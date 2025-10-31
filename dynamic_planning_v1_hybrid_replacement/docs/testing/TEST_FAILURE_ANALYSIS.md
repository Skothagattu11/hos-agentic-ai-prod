# Test Failure Analysis - Day 2 Issues

## 🎯 Summary

Test failed on Day 2 with **THREE separate issues**:

1. ❌ **SQL syntax error** → Dynamic task selection completely failed (0% replacement)
2. ❌ **Same analysis_id for both days** → Test mode not working correctly
3. ❌ **Task replacement error** → String/dict type mismatch

---

## 🔴 Issue 1: SQL Syntax Error (BLOCKING)

### Error Message
```
'column task_library.(time_of_day_preference does not exist'
```

### Root Cause

The system is in **DEVELOPMENT mode**, which uses Supabase REST API instead of PostgreSQL.

The query being generated has a malformed filter:
```
%22%28time_of_day_preference%22=eq.morning
```

Decoded:
```
"(time_of_day_preference"=eq.morning   ← Extra "( before column name!
```

### Why This Happens

**Location**: `shared_libs/supabase_client/adapter.py`

When `ENVIRONMENT=development`, the adapter uses Supabase REST API. The REST API query builder is incorrectly adding quotes around the column name in the filter.

### Fix Option 1: Disable Dynamic Task Selection for Now

```bash
# In .env
ENABLE_DYNAMIC_TASK_SELECTION=false
```

This will skip the task library entirely and use pure AI generation.

### Fix Option 2: Switch to Production Mode (Uses PostgreSQL)

```bash
# In .env
ENVIRONMENT=production
```

This will use direct PostgreSQL queries which work correctly.

**Trade-off**: Production mode uses connection pooling which may have issues in WSL2.

### Fix Option 3: Fix the REST API Query (Requires Code Change)

Need to fix how `SupabaseAsyncPGAdapter` builds REST API queries when falling back from PostgreSQL.

---

## 🔴 Issue 2: Test Mode Not Working (Same Analysis ID)

### What Happened

```
Day 1: Analysis ID: b72bc322-9db3-47e7-8a15-c52dd0dc532f  ✅ Created
Day 2: Analysis ID: b72bc322-9db3-47e7-8a15-c52dd0dc532f  ❌ SAME ID!
Day 2: Retrieved 0 plan items  ❌ No tasks found
```

### Why Test Mode Didn't Work

Looking at the code change we made:

```python
# Line 476-494 in ai_context_integration_service.py
if test_mode:
    # Extract plan_date from analysis_result
    plan_date = None
    if isinstance(analysis_result, dict):
        if 'date' in analysis_result:
            plan_date = analysis_result['date']  ← FOUND IT!
        elif 'content' in analysis_result:
            ...
```

**The problem**: `analysis_result` DOES contain `'date'`, so it extracts the correct plan_date.

But then:
```python
# Line 503-510
existing_result = supabase.table('holistic_analysis_results')\
    .select('id')\
    .eq('user_id', user_id)\
    .eq('analysis_type', analysis_type)\
    .eq('archetype', archetype or 'unknown')\
    .eq('analysis_date', plan_date)\  ← Checks for existing plan with this date
    .limit(1)\
    .execute()
```

**What's happening**:
1. Day 1: `plan_date = "2025-10-27"` → No existing plan → **INSERT** new
2. Day 2: `plan_date = "2025-10-28"` → Should find no existing plan → But it DOES find one!

### The Real Problem

The issue is that when Day 2 UPDATES the plan, it changes `analysis_date` from "2025-10-27" to "2025-10-28", but keeps the same `id`.

Then `plan_extraction_service.py` deletes the old plan_items and inserts new ones with the SAME `analysis_result_id`.

So Day 1's plan_items are GONE.

### Why This Breaks Testing

```sql
-- Day 1 creates:
holistic_analysis_results: id=abc123, analysis_date='2025-10-27'
plan_items: 11 rows with analysis_result_id=abc123, plan_date='2025-10-27'

-- Day 2 UPDATES:
holistic_analysis_results: id=abc123, analysis_date='2025-10-28' (UPDATED!)
plan_items: DELETED old rows, INSERTED 0 rows (extraction failed due to Issue #1)

-- Test queries for Day 2:
SELECT * FROM plan_items WHERE analysis_result_id=abc123 AND plan_date='2025-10-28'
→ Returns 0 rows (no plan_items were created due to dynamic task selection failure)
```

### Real Fix Needed

The test mode logic needs to check if a plan exists for the SPECIFIC DATE before deciding to update:

```python
if test_mode:
    # Extract plan_date
    plan_date = analysis_result.get('date') or datetime.now(timezone.utc).date().isoformat()

    # ALWAYS INSERT in test mode (don't check for existing)
    # This allows multiple plans for different dates
    existing_result = None  # Force INSERT
else:
    # Production: use today and check for existing
    plan_date = datetime.now(timezone.utc).date().isoformat()
    existing_result = supabase.table('holistic_analysis_results')...
```

---

## 🔴 Issue 3: Task Replacement Error

### Error Message
```
[HYBRID] Task replacement failed: string indices must be integers, not 'str'
```

### Root Cause

`DynamicTaskSelector` is receiving plan data in wrong format (string instead of dict).

### Where It Fails

`services/dynamic_personalization/dynamic_task_selector.py` expects plan to be a dict/list, but it's receiving a string.

This happens because plan extraction may be returning JSON-encoded strings instead of parsed dicts.

---

## ✅ Recommended Quick Fix (For Testing)

Since all 3 issues are interconnected and fixing them properly requires significant code changes, here's the QUICKEST path to get testing working:

### Step 1: Disable Dynamic Task Selection

```bash
# .env
ENABLE_DYNAMIC_TASK_SELECTION=false
```

This eliminates Issue #1 and Issue #3.

### Step 2: Fix Test Mode to Always INSERT

```python
# ai_context_integration_service.py line 489
if test_mode:
    plan_date = analysis_result.get('date') or datetime.now(timezone.utc).date().isoformat()
    logger.debug(f"[TEST_MODE] Using plan_date={plan_date}, forcing INSERT")

    # FORCE INSERT - don't check for existing in test mode
    existing_result = type('obj', (object,), {'data': None})()  # Empty result
else:
    # Production mode
    plan_date = datetime.now(timezone.utc).date().isoformat()
    existing_result = supabase.table('holistic_analysis_results')...
```

### Step 3: Run Test Again

```bash
python testing/test_realistic_user_journey_v2.py
```

Expected outcome:
- ✅ 4 different `analysis_id` values (one per day)
- ✅ Each day has plan_items in database
- ✅ No dynamic task selection (0% replacement) but test completes
- ✅ Feedback submissions succeed

---

## 📊 Alternative: Proper Fix (More Time)

If you want dynamic task selection working:

1. Fix SupabaseAsyncPGAdapter REST API query building
2. Or switch to `ENVIRONMENT=production`
3. Fix test mode to force INSERT
4. Fix DynamicTaskSelector string/dict handling

**Time estimate**: 2-3 hours

**Recommendation**: Use quick fix for now, do proper fix after initial testing proves the concept works.

---

## 🎯 What To Do Next

**Option A: Quick Fix (Recommended for NOW)**
1. Set `ENABLE_DYNAMIC_TASK_SELECTION=false`
2. Fix test mode to force INSERT
3. Run test → Verify 4 plans created
4. Come back to fix dynamic selection later

**Option B: Full Fix (Better Long-term)**
1. Set `ENVIRONMENT=production`
2. Fix test mode to force INSERT
3. Debug and fix dynamic task selection
4. Run test → Verify everything works

**Which do you prefer?**
