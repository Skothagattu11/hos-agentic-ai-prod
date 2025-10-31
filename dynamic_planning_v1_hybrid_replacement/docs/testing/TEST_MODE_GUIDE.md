# Test Mode Guide - Future Date Testing

## 🎯 Purpose

This test mode allows testing the dynamic task selection system with **future dates** for multi-day journey simulations.

**IMPORTANT**: This is a **temporary testing feature** only. After testing is complete, you must disable it to restore production behavior.

---

## 🔧 What Was Changed

**File**: `services/ai_context_integration_service.py` (lines 471-498)

**Change**: Added `ENABLE_TEST_MODE` environment variable that controls how `analysis_date` is determined when storing routine plans.

### Production Behavior (DEFAULT)

```python
# ENABLE_TEST_MODE=false (or not set)
analysis_date = datetime.now(timezone.utc).date().isoformat()  # Always TODAY
```

**Result**: Same user + same archetype + same day → **UPDATE** existing plan (correct for production!)

### Test Mode Behavior

```python
# ENABLE_TEST_MODE=true
analysis_date = analysis_result.get('date') or today  # Use plan's date
```

**Result**: Different dates → **CREATE** new plans (enables multi-day testing)

---

## ✅ How to Enable Test Mode

### Step 1: Add to `.env` File

```bash
# Open .env file
nano .env

# Add this line (or set to 'true' if it already exists)
ENABLE_TEST_MODE=true

# Save and exit
```

### Step 2: Restart the Server

```bash
# Stop the server (Ctrl+C)

# Start it again
python start_openai.py
```

### Step 3: Verify Test Mode is Active

Look for this log message when server starts or plan is generated:
```
[TEST_MODE] Using analysis_date=2025-10-27 from plan (test mode enabled)
```

---

## 🧪 Running Tests with Test Mode

### Test Script to Use

**Use**: `testing/test_realistic_user_journey_v2.py`

This script:
- ✅ Queries `plan_items` from database (real UUIDs)
- ✅ Uses correct engagement endpoint schema
- ✅ Tests 4-day journey with feedback loop
- ✅ Verifies task library integration

### Run the Test

```bash
# Make sure test mode is enabled in .env
# ENABLE_TEST_MODE=true

# Make sure server is running
python start_openai.py

# In another terminal, run the test
python testing/test_realistic_user_journey_v2.py
```

### Expected Behavior with Test Mode

```
Day 1 (2025-10-27) → Creates NEW analysis_id="abc123"
Day 2 (2025-10-28) → Creates NEW analysis_id="def456"
Day 3 (2025-10-29) → Creates NEW analysis_id="ghi789"
Day 4 (2025-10-30) → Creates NEW analysis_id="jkl012"
```

**Result**: 4 separate entries in `holistic_analysis_results` table ✅

### Expected Behavior WITHOUT Test Mode (Production)

```
Day 1 (today) → Creates analysis_id="abc123"
Day 2 (today) → UPDATES analysis_id="abc123"
Day 3 (today) → UPDATES analysis_id="abc123"
Day 4 (today) → UPDATES analysis_id="abc123"
```

**Result**: 1 entry in `holistic_analysis_results` that gets updated ✅

---

## 🔴 How to Disable Test Mode (CRITICAL)

### After Testing is Complete

**Step 1: Update `.env` File**

```bash
# Open .env file
nano .env

# Change ENABLE_TEST_MODE to false (or remove the line entirely)
ENABLE_TEST_MODE=false

# OR just comment it out
# ENABLE_TEST_MODE=true

# Save and exit
```

**Step 2: Restart the Server**

```bash
# Stop the server (Ctrl+C)

# Start it again
python start_openai.py
```

**Step 3: Verify Production Mode is Active**

Look for this log message:
```
[PRODUCTION] Using analysis_date=2025-01-27 (today)
```

---

## 📊 Verification Queries

### Check How Many Plans Were Created

```sql
-- With test mode: Should see 4 plans for different dates
SELECT
    id,
    analysis_date,
    archetype,
    created_at
FROM holistic_analysis_results
WHERE user_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869'
  AND analysis_type = 'routine_plan'
ORDER BY analysis_date DESC;
```

### Expected Results

**With Test Mode ON**:
```
id (different)    | analysis_date | archetype      | created_at
------------------|---------------|----------------|-------------------
jkl012...         | 2025-10-30   | Peak Performer | 2025-01-27 14:03:00
ghi789...         | 2025-10-29   | Peak Performer | 2025-01-27 14:02:00
def456...         | 2025-10-28   | Peak Performer | 2025-01-27 14:01:00
abc123...         | 2025-10-27   | Peak Performer | 2025-01-27 14:00:00
```

**With Test Mode OFF (Production)**:
```
id (same)         | analysis_date | archetype      | created_at
------------------|---------------|----------------|-------------------
abc123...         | 2025-01-27   | Peak Performer | 2025-01-27 14:03:00
(Only 1 row - updated 4 times)
```

### Check Plan Items

```sql
-- Verify plan_items were created for each plan
SELECT
    analysis_result_id,
    plan_date,
    COUNT(*) as task_count
FROM plan_items
WHERE profile_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869'
GROUP BY analysis_result_id, plan_date
ORDER BY plan_date DESC;
```

### Check Feedback Submissions

```sql
-- Verify task check-ins were recorded
SELECT
    analysis_result_id,
    planned_date,
    COUNT(*) as checkin_count,
    AVG(satisfaction_rating) as avg_satisfaction
FROM task_checkins
WHERE profile_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869'
GROUP BY analysis_result_id, planned_date
ORDER BY planned_date DESC;
```

---

## 🚨 Important Reminders

### ⚠️ DO NOT Leave Test Mode Enabled in Production

**Why?**
- Users regenerating today's plan will create duplicates
- Each regeneration creates a NEW plan instead of updating
- Database will fill with duplicate plans for the same day
- Flutter app may show multiple plans for the same day

### ✅ Production Behavior is CORRECT

The default behavior (test mode OFF) is intentionally designed for production:
- User generates plan for today → Creates plan
- User regenerates plan for today → **UPDATES** the same plan
- This prevents duplicate plans for the same day ✅

### 🧪 Test Mode is ONLY for Multi-Day Testing

Test mode allows testing future dates:
- Day 1: Generate plan for 2025-10-27 → Creates new plan
- Day 2: Generate plan for 2025-10-28 → Creates new plan
- This enables testing 4-day journeys, feedback loops, adaptive learning

---

## 📝 Quick Reference

### Enable Test Mode
```bash
# .env file
ENABLE_TEST_MODE=true

# Restart server
python start_openai.py
```

### Disable Test Mode
```bash
# .env file
ENABLE_TEST_MODE=false
# OR remove the line entirely

# Restart server
python start_openai.py
```

### Check Current Mode
```bash
# Look for log messages when server runs:
# "[TEST_MODE] Using analysis_date=..." → Test mode ON
# "[PRODUCTION] Using analysis_date=..." → Test mode OFF
```

---

## 🎯 Testing Checklist

Before testing:
- [ ] Set `ENABLE_TEST_MODE=true` in `.env`
- [ ] Restart server
- [ ] Verify test mode log message appears

During testing:
- [ ] Run `testing/test_realistic_user_journey_v2.py`
- [ ] Verify 4 different `analysis_id` values in output
- [ ] Verify feedback submissions succeed (no UUID errors)
- [ ] Check database: 4 plans with different `analysis_date` values

After testing:
- [ ] Set `ENABLE_TEST_MODE=false` in `.env`
- [ ] Restart server
- [ ] Verify production mode log message appears
- [ ] Test production behavior: regenerate today's plan → should UPDATE not INSERT

---

## 🔧 Troubleshooting

### Issue: Test mode not working (still updating same plan)

**Check**:
1. `.env` file has `ENABLE_TEST_MODE=true`
2. Server was restarted after changing `.env`
3. Log shows `[TEST_MODE]` message (not `[PRODUCTION]`)

### Issue: Feedback submissions still failing with UUID errors

**Check**:
1. Using `test_realistic_user_journey_v2.py` (not v1)
2. Script queries `plan_items` from database
3. Script uses `plan_item_id` (not `task_id`)

### Issue: Can't find `ENABLE_TEST_MODE` in code

**Location**: `services/ai_context_integration_service.py:474`

```python
test_mode = os.getenv('ENABLE_TEST_MODE', 'false').lower() == 'true'
```

---

## 📞 Support

If you encounter issues:
1. Check server logs for `[TEST_MODE]` or `[PRODUCTION]` messages
2. Verify `.env` file syntax (no spaces around `=`)
3. Ensure server was restarted after `.env` changes
4. Check `holistic_analysis_results` table with verification queries above

---

## ✅ Summary

**Test Mode**: Enables multi-day testing by using plan's date (not today)
**Production Mode**: Uses today's date for same-day plan updates (default)

**To Enable**: Set `ENABLE_TEST_MODE=true` in `.env` and restart server
**To Disable**: Set `ENABLE_TEST_MODE=false` in `.env` and restart server

**CRITICAL**: Always disable test mode after testing is complete!
