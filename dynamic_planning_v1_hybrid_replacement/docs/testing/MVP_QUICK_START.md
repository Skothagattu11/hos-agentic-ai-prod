# Quick Alpha MVP - Setup & Testing Guide

## Current Status: Ready for Testing ✅

**What's Complete:**
- ✅ Phase 1-3: Core hybrid system implemented
- ✅ Feature switch integrated
- ✅ E2E test script created
- ✅ Database migration ready

**What's Needed:**
1. Apply database migration
2. Start API server
3. Run E2E tests
4. Enable for alpha user

---

## Step 1: Apply Database Migration (1 minute)

The migration adds plan caching columns to `user_preference_profile` table.

### Option A: Via Supabase Dashboard (Recommended)

1. Go to https://supabase.com/dashboard
2. Select your project
3. Navigate to **SQL Editor**
4. Copy contents of `supabase/migrations/006_add_plan_caching.sql`
5. Paste and click **Run**

**Expected Output:**
```
Success. No rows returned
```

### Option B: Via SQL (if you have direct access)

```bash
# From project root
psql $DATABASE_URL < supabase/migrations/006_add_plan_caching.sql
```

### Verify Migration:

Run this in SQL Editor:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'user_preference_profile'
  AND column_name IN ('last_shuffle_date', 'cached_ai_plan');
```

**Expected:** 2 rows showing the new columns

---

## Step 2: Configure Feature Switch (30 seconds)

### Current State (Safe Default):
```env
ENABLE_DYNAMIC_TASK_SELECTION=false  # Hybrid OFF - uses AI only
```

### For Testing (Enable Hybrid):
```env
ENABLE_DYNAMIC_TASK_SELECTION=true   # Hybrid ON - replaces AI tasks
```

**Where:** `.env` file (lines 73-74)

**Decision:**
- Keep `false` initially to test server starts correctly
- Change to `true` when ready to test hybrid system

---

## Step 3: Start API Server (30 seconds)

### Terminal 1: Start Server

```bash
# From project root
./venv/Scripts/python.exe start_openai.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8002
```

**Important:** Server must be running on port **8002** for tests to work

### Verify Server Health:

Open browser or curl:
```bash
curl http://localhost:8002/api/health
```

**Expected:** `{"status": "healthy"}`

---

## Step 4: Run E2E Tests (2-3 minutes)

### Terminal 2: Run Tests

```bash
# From project root
./venv/Scripts/python.exe testing/test_hybrid_mvp_e2e.py
```

### What the Test Does:

**Test 1: Multi-Day Journey**
- Generates plans for: Today, Tomorrow, +3 days, +7 days
- Validates API responses
- Checks hybrid system activation
- Measures replacement rate

**Test 2: Mode Switching**
- Tests: brain_power, productivity, recovery modes
- Verifies mode parameter works
- Compares replacement rates

### Expected Results (Hybrid OFF):

```
✅ Total Successful: 7/7
🤖 Hybrid System: NOT ACTIVE (all AI-only plans)
   Note: Check ENABLE_DYNAMIC_TASK_SELECTION in .env

MVP SUCCESS CRITERIA:
   ✅ API generates plans without crashing (7/7)
   ❌ Hybrid system activated (0 plans)
   ✅ Plans can be generated for future dates
```

**This is GOOD!** It proves:
- API works
- No breaking changes from Phase 3 code
- Future date generation works

### Expected Results (Hybrid ON):

```
✅ Total Successful: 7/7
🔀 Hybrid System: ACTIVE (7 hybrid plans generated)
📊 Average Replacement Rate: 45.2%

MVP SUCCESS CRITERIA:
   ✅ API generates plans without crashing (7/7)
   ✅ Hybrid system activated (7 plans)
   ✅ Plans can be generated for future dates

🎉 MVP TEST SUITE PASSED - Ready for alpha user testing!
```

**This is PERFECT!** Ready for alpha user.

---

## Step 5: Troubleshooting Common Issues

### Issue 1: Server Won't Start

**Error:** `Address already in use: 8002`

**Fix:**
```bash
# Windows
netstat -ano | findstr :8002
taskkill /PID <PID> /F

# Stop and restart
./venv/Scripts/python.exe start_openai.py
```

### Issue 2: Test Can't Connect to Server

**Error:** `API server not running at http://localhost:8002`

**Fix:**
1. Check server is running (Terminal 1)
2. Verify port 8002 is accessible
3. Check firewall settings

### Issue 3: Low Replacement Rate (<30%)

**Possible Causes:**
1. **SQL parsing issues** - Library queries failing
2. **Task library empty** - Need to seed tasks
3. **Category mapping gaps** - AI tasks don't match categories

**Debug:**
```bash
# Check task library count
./venv/Scripts/python.exe -c "
import asyncio
from services.dynamic_personalization.task_library_service import TaskLibraryService

async def check():
    service = TaskLibraryService()
    await service.initialize()
    counts = await service.get_task_count_by_category()
    print(f'Task Library: {counts}')
    await service.close()

asyncio.run(check())
"
```

**Expected:** Should show ~50 tasks across categories

**Fix if empty:**
```bash
./venv/Scripts/python.exe services/seeding/task_library_seed.py
```

### Issue 4: Plans Generate But No Hybrid Flag

**Symptom:** Plans work but `is_dynamic_hybrid: false`

**Cause:** Feature switch still OFF

**Fix:**
```bash
# Edit .env
ENABLE_DYNAMIC_TASK_SELECTION=true

# Restart server (Ctrl+C in Terminal 1, then restart)
./venv/Scripts/python.exe start_openai.py
```

### Issue 5: SQL Parsing Errors in Logs

**Example:** `column user_task_feedback.DISTINCTtask_library_id does not exist`

**Impact:** Library queries fail, fallback to AI tasks works

**Status:** Known issue from Phase 1, doesn't block MVP

**Fix:** Will address if replacement rate too low

---

## Step 6: Enable for Alpha User (5 minutes)

Once E2E tests pass with hybrid ON:

### 6.1 Verify Configuration

```bash
# Check .env
grep "ENABLE_DYNAMIC_TASK_SELECTION" .env

# Should show:
ENABLE_DYNAMIC_TASK_SELECTION=true
```

### 6.2 Restart Server (if needed)

```bash
# Terminal 1: Ctrl+C to stop
# Then restart:
./venv/Scripts/python.exe start_openai.py
```

### 6.3 Test with Flutter App

**From Flutter app:**
1. Navigate to plan generation screen
2. Request new routine plan
3. Observe tasks in the plan

**What to Look For:**
- Mix of different task variations
- Tasks you haven't seen before
- Variety across days

**What to Monitor:**
- Server logs (Terminal 1)
- Look for `[HYBRID]` messages
- Check replacement stats

### 6.4 Monitor Logs

**Look for these messages:**
```
🔀 [HYBRID] Dynamic task selection enabled - replacing AI tasks with library selections
✅ [HYBRID] Replaced 5/12 tasks with library selections
```

**If you see:**
```
⚠️ [HYBRID] Task replacement failed: ...
   Continuing with AI-only plan
```

→ Check error message, may need fixes

---

## Step 7: 2-3 Day Monitoring Period

### Daily Checklist:

**Day 1:**
- [ ] Generate plan from Flutter app
- [ ] Check server logs for errors
- [ ] Note replacement rate in logs
- [ ] Complete some tasks
- [ ] Observe if tasks feel different

**Day 2:**
- [ ] Generate another plan
- [ ] Compare with Day 1 tasks
- [ ] Check for variety
- [ ] Note any issues
- [ ] Check replacement rate improving

**Day 3:**
- [ ] Generate plan
- [ ] Assess overall experience
- [ ] Collect feedback notes
- [ ] Decide: Continue or iterate?

### Success Indicators:

✅ **Good Signs:**
- Plans generate consistently
- See task variety across days
- Replacement rate > 30%
- No crashes or errors
- User completes tasks

⚠️ **Warning Signs:**
- Replacement rate < 20%
- Frequent errors in logs
- User dislikes tasks
- Server instability

❌ **Stop and Fix:**
- Plans fail to generate
- Server crashes
- Data loss or corruption
- User can't use app

---

## Quick Command Reference

```bash
# 1. Apply migration (Supabase Dashboard - see Step 1)

# 2. Start server
./venv/Scripts/python.exe start_openai.py

# 3. Run E2E tests (new terminal)
./venv/Scripts/python.exe testing/test_hybrid_mvp_e2e.py

# 4. Check task library
./venv/Scripts/python.exe -c "
import asyncio
from services.dynamic_personalization.task_library_service import TaskLibraryService
async def check():
    s = TaskLibraryService()
    await s.initialize()
    print(await s.get_task_count_by_category())
    await s.close()
asyncio.run(check())
"

# 5. Check config
grep "ENABLE_DYNAMIC_TASK_SELECTION" .env

# 6. View server logs (in server terminal)
# Just watch Terminal 1 output
```

---

## Next Steps After MVP Testing

### If Successful (Replacement rate > 30%, stable):
1. ✅ Expand to 2-3 more users
2. ✅ Collect structured feedback
3. ✅ Plan Phase 4 (Mode Support) or Phase 5 (Caching)

### If Issues Found:
1. 🔧 Fix critical bugs
2. 🔧 Improve category mapping
3. 🔧 Address SQL parsing if blocking
4. 🔄 Re-test before expanding

### If Replacement Rate Too Low (<20%):
1. 🔍 Review AI task titles (add to category mapper)
2. 🔍 Check task library coverage
3. 🔍 Fix SQL queries if failing
4. 🔍 Consider expanding task library

---

## Support & Debugging

### View Server Logs:
- Watch Terminal 1 (where server is running)
- Look for `[HYBRID]`, `[ERROR]`, `[WARNING]` tags

### Check Database:
```sql
-- Supabase SQL Editor

-- Verify migration applied
SELECT column_name FROM information_schema.columns
WHERE table_name = 'user_preference_profile'
  AND column_name IN ('last_shuffle_date', 'cached_ai_plan');

-- Check task library
SELECT category, COUNT(*)
FROM task_library
WHERE is_active = true
GROUP BY category;

-- Check user preferences
SELECT * FROM user_preference_profile
WHERE user_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869';
```

### Common Log Messages:

**Normal Operation:**
```
🔀 [HYBRID] Dynamic task selection enabled - replacing AI tasks
✅ [HYBRID] Replaced X/Y tasks with library selections
```

**Warnings (Non-Critical):**
```
⚠️ [HYBRID] No library task found for 'Task Title' - keeping AI task
⚠️ [HYBRID] Unexpected routine_plan structure - skipping task replacement
```

**Errors (Needs Fix):**
```
❌ [HYBRID] Task replacement failed: <error>
   Continuing with AI-only plan
```

---

## Questions?

If you encounter issues:

1. **Check this guide first** - Most issues covered here
2. **Review server logs** - Error messages are descriptive
3. **Run diagnostic commands** - Check task library, config, etc.
4. **Try with hybrid OFF** - Verify base system works
5. **Ask for help** - Provide error messages and context

---

**Ready to start?** → Go to **Step 1: Apply Database Migration**
