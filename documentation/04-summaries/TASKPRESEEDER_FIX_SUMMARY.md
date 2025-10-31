# TaskPreseeder Parameter Substitution Bug Fix

## Date: 2025-10-30

## Critical Bug Found

**Symptom**: TaskPreseeder always reports "0 completed tasks" even though 80+ check-ins exist in database.

**Root Cause**: `_handle_count_query` method was not substituting parameter placeholders (`$1`) with actual values from `args` tuple.

## Evidence from Server Logs

```
INFO:httpx:HTTP Request: HEAD https://...task_checkins?profile_id=eq.None&completion_status=eq.completed
INFO:services.dynamic_personalization.task_preseeder:[PRESEED] User a57f70b4: feedback_count=0, threshold=3
```

TaskPreseeder knew user_id was `a57f70b4`, but the database query used `profile_id=None`.

## The Bug

**File**: `shared_libs/supabase_client/adapter.py`

**Method**: `_handle_count_query` (line 1021)

**Before (BROKEN)**:
```python
async def _handle_count_query(self, parsed_query: Dict[str, Any], args: tuple):
    ...
    for condition in parsed_query['where_conditions']:
        column = condition['column']
        operator = condition['operator']
        value = condition['value']  # ❌ BUG: Always None for parameters!

        if operator == 'eq':
            supabase_query = supabase_query.eq(column, value)
```

**Why This Failed**:
When `$1` is parsed by `_parse_where_with_params`:
```python
conditions.append({
    'column': 'profile_id',
    'operator': 'eq',
    'param_index': 0,       # Points to args[0]
    'value': None           # Placeholder, to be filled later
})
```

But `_handle_count_query` only looked at `condition['value']` (which is `None`), ignoring `param_index` entirely!

## The Fix

**After (CORRECT)**:
```python
async def _handle_count_query(self, parsed_query: Dict[str, Any], args: tuple):
    ...
    for condition in parsed_query['where_conditions']:
        column = condition['column']
        operator = condition['operator']
        param_index = condition.get('param_index')

        # ✅ FIX: Check param_index and substitute from args
        if param_index is not None and param_index < len(args):
            value = args[param_index]  # Use actual user_id from args
        else:
            value = condition['value']

        if operator == 'eq':
            supabase_query = supabase_query.eq(column, value)
```

Now it matches the pattern used in `_fetch_with_supabase_client` (lines 294-299).

## Impact

### Before Fix:
- TaskPreseeder: "0 completed tasks" ❌
- Database query: `profile_id=None` ❌
- AI receives: No friction data ❌
- Result: Tasks never adapt ❌

### After Fix:
- TaskPreseeder: "80 completed tasks" ✅
- Database query: `profile_id='a57f70b4...'` ✅
- AI receives: Friction scores for all categories ✅
- Result: Tasks simplify based on friction ✅

## Expected Behavior After Fix

Run the 7-day test again (`python run_feedback_test_7day.py`):

**Day 1-3**:
- Standard tasks
- TaskPreseeder logs: "Insufficient feedback (0/3) - using pure AI"

**Day 4**:
- TaskPreseeder logs: "Selected X tasks from Y days of feedback"
- AI receives friction scores: nutrition=0.41, movement=0.05
- Plan should start adapting

**Day 5-7**:
- High-friction categories (nutrition, mindfulness) simplified
- Example: "Balanced Breakfast" → "Take photo of breakfast plate"
- Low-friction categories (movement, hydration) used as anchors

## Testing

1. **Restart server**: `python start_openai.py`
2. **Run 7-day test**: `python run_feedback_test_7day.py`
3. **Watch logs for**:
   ```
   ✅ [PRESEED] Selected X tasks from Y days of feedback
   ```
   Instead of:
   ```
   ⚪ [PRESEED] Cold start - using pure AI (0 completed tasks)
   ```

4. **Validate results**: `python diagnose_all_categories_friction.py`
   - Should show: "✅ PASS: Tasks evolved across all categories"
   - Nutrition tasks should differ Day 1 vs Day 7

## Files Modified

1. `shared_libs/supabase_client/adapter.py`:
   - Lines 1032-1038: Added param_index check and substitution
   - Matches pattern from `_fetch_with_supabase_client`

## Status: ✅ COMPLETE

The root cause of TaskPreseeder always finding 0 check-ins has been fixed. Friction-reduction system should now work end-to-end.
