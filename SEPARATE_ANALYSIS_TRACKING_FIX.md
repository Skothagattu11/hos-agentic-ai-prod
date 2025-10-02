# Separate Analysis Type Tracking - Implementation Guide

## 🎯 Problem Solved

**Before Fix:**
```
User calls: POST /circadian/analyze at 12:00
  → Updates archetype_analysis_tracking.last_analysis_at = 12:00

User calls: POST /behavior/analyze at 12:05
  → Checks archetype_analysis_tracking.last_analysis_at
  → Sees 12:00 (only 5 minutes ago)
  → ❌ SKIPS behavior analysis (thinks it's too recent)
  → User gets CIRCADIAN data when they wanted BEHAVIOR data
```

**After Fix:**
```
User calls: POST /circadian/analyze at 12:00
  → Updates archetype_analysis_tracking:
    - analysis_type = "circadian_analysis"
    - last_analysis_at = 12:00

User calls: POST /behavior/analyze at 12:05
  → Checks archetype_analysis_tracking:
    - analysis_type = "behavior_analysis"
    - No recent entry found!
  → ✅ Runs FRESH behavior analysis
  → User gets BEHAVIOR data as expected
```

---

## 📋 Changes Made

### 1. Database Migration
**File**: `migrations/add_analysis_type_to_tracking.sql`

Adds `analysis_type` column to track behavior vs circadian separately:
- Adds column with default value 'behavior_analysis'
- Updates unique constraint to include analysis_type
- Creates index for faster queries

### 2. ArchetypeAnalysisTracker Service
**File**: `services/archetype_analysis_tracker.py`

**Changes**:
- `get_last_analysis_date()`: Added `analysis_type` parameter (default: "behavior_analysis")
- `update_last_analysis_date()`: Added `analysis_type` parameter
- `get_last_analysis_date_with_fallback()`: Added `analysis_type` parameter

### 3. Circadian Analysis Integration
**File**: `services/api_gateway/openai_main.py` (line 3533)

**Changes**:
```python
tracking_success = await tracker.update_last_analysis_date(
    user_id=user_id,
    archetype=archetype,
    analysis_date=datetime.now(timezone.utc),
    analysis_type="circadian_analysis"  # ← NEW: Track separately
)
```

---

## 🚀 Deployment Steps

### Step 1: Run Database Migration

```bash
# Connect to Supabase SQL Editor and run:
cat migrations/add_analysis_type_to_tracking.sql

# Or use psql:
psql $DATABASE_URL -f migrations/add_analysis_type_to_tracking.sql
```

**Verify migration:**
```sql
-- Check column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking';

-- Should show:
-- user_id, archetype, analysis_type, last_analysis_at, analysis_count, etc.
```

### Step 2: Restart Server

```bash
# Kill old server
# Start new server
python start_openai.py
```

### Step 3: Test Separation

**Test Script 1: Circadian First**
```bash
# Test circadian analysis
python test_circadian_api.py

# Immediately test behavior analysis
curl -X POST http://localhost:8002/api/user/35pDPUIfAoRl2Y700bFkxPKYjjf2/behavior/analyze \
  -H "X-API-Key: hosa_flutter_app_2024" \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder", "force_refresh": false}'
```

**Expected Result**: Both should run fresh analyses (not skip due to threshold).

**Test Script 2: Behavior First**
```bash
# Test behavior analysis
curl -X POST http://localhost:8002/api/user/35pDPUIfAoRl2Y700bFkxPKYjjf2/behavior/analyze \
  -H "X-API-Key: hosa_flutter_app_2024" \
  -H "Content-Type: application/json" \
  -d '{"archetype": "Foundation Builder", "force_refresh": false}'

# Immediately test circadian analysis
python test_circadian_api.py
```

**Expected Result**: Both should run fresh analyses (not skip due to threshold).

---

## 🧪 Verification Queries

### Check Tracking Records

```sql
-- Should see SEPARATE entries for behavior and circadian
SELECT user_id, archetype, analysis_type, last_analysis_at, analysis_count
FROM archetype_analysis_tracking
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
AND archetype = 'Foundation Builder'
ORDER BY last_analysis_at DESC;

-- Expected output:
-- user_id | archetype | analysis_type | last_analysis_at | analysis_count
-- 35pD... | Foundation Builder | circadian_analysis | 2025-10-02 12:00:00 | 1
-- 35pD... | Foundation Builder | behavior_analysis  | 2025-10-02 12:05:00 | 1
```

### Check Analysis Results

```sql
-- Should see BOTH circadian and behavior results
SELECT id, user_id, analysis_type, archetype, created_at
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
AND archetype = 'Foundation Builder'
ORDER BY created_at DESC
LIMIT 10;

-- Expected output:
-- Both "circadian_analysis" and "behavior_analysis" entries
```

---

## 🎯 Testing Checklist

### Scenario 1: Circadian → Behavior (Immediate)
- [ ] Call `/circadian/analyze`
- [ ] Verify `archetype_analysis_tracking` has `analysis_type='circadian_analysis'`
- [ ] Immediately call `/behavior/analyze` (< 5 minutes)
- [ ] Verify it runs FRESH analysis (not skipped)
- [ ] Verify `archetype_analysis_tracking` has BOTH entries

### Scenario 2: Behavior → Circadian (Immediate)
- [ ] Call `/behavior/analyze`
- [ ] Verify `archetype_analysis_tracking` has `analysis_type='behavior_analysis'`
- [ ] Immediately call `/circadian/analyze` (< 5 minutes)
- [ ] Verify it runs FRESH analysis (not skipped)
- [ ] Verify `archetype_analysis_tracking` has BOTH entries

### Scenario 3: Routine Generation (Agentic Flow)
- [ ] Call `/routine/generate`
- [ ] Verify it runs PARALLEL behavior + circadian analyses
- [ ] Verify BOTH tracking entries are updated
- [ ] Verify routine uses BOTH behavior AND circadian data

### Scenario 4: Threshold Logic (Same Type)
- [ ] Call `/circadian/analyze`
- [ ] Wait 2 minutes
- [ ] Call `/circadian/analyze` again (same archetype)
- [ ] Verify it SKIPS (threshold not met)
- [ ] Call `/behavior/analyze`
- [ ] Verify it RUNS FRESH (different analysis type)

---

## 🔧 Troubleshooting

### Issue: Migration Fails with "Column already exists"

**Solution**: The column might already exist. Check manually:
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
AND column_name = 'analysis_type';
```

If it exists but has no unique constraint:
```sql
ALTER TABLE archetype_analysis_tracking
ADD CONSTRAINT archetype_analysis_tracking_user_archetype_type_key
UNIQUE (user_id, archetype, analysis_type);
```

### Issue: Old tracking entries without analysis_type

**Solution**: The migration sets default value 'behavior_analysis' for existing rows.

To verify:
```sql
SELECT analysis_type, COUNT(*)
FROM archetype_analysis_tracking
GROUP BY analysis_type;

-- Should show:
-- behavior_analysis | 5
-- circadian_analysis | 0  (until first circadian analysis runs)
```

### Issue: Behavior analysis still skips after circadian

**Cause**: Migration not run or server not restarted.

**Solution**:
1. Run migration SQL
2. Restart server: `pkill -f start_openai && python start_openai.py`
3. Test again

---

## 📊 Success Metrics

After deployment, you should see:

✅ **Separate tracking entries** for behavior vs circadian
✅ **No false threshold skips** when switching analysis types
✅ **Routine generation works** with parallel analyses
✅ **Cost savings** from proper threshold enforcement (no duplicate analyses of SAME type)
✅ **Better logs** showing analysis_type in tracking messages

---

## 🎯 Summary

This fix ensures that:
1. **Circadian analysis** tracks separately from **behavior analysis**
2. Running circadian **does NOT** prevent behavior from running
3. Running behavior **does NOT** prevent circadian from running
4. **Same-type analyses** still respect threshold (prevents duplicates)
5. **Agentic flow** (routine generation) works perfectly with parallel analyses

**Result**: Users get the RIGHT analysis type when they request it, and the system still saves costs by preventing duplicate analyses of the SAME type.
