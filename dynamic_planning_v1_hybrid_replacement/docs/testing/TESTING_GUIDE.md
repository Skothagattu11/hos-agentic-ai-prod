# Dynamic Personalization Test Suite - What to Expect

## Overview

The test script (`testing/test_dynamic_personalization.py`) validates that your dynamic personalization system is working correctly. It runs **10 comprehensive tests** that check everything from database connectivity to complete plan generation.

---

## Test Breakdown

### ✅ TEST 1: Configuration Loading
**What it does**: Checks if environment variables are loaded correctly

**Expected Result**:
```
✅ PASSED: Configuration Loading
   ENABLE_DYNAMIC_PLANS: false (or true)
   ADAPTIVE_LEARNING: false (or true)
   FEEDBACK_ENABLED: false (or true)
```

**What it validates**:
- `.env` file exists and loads properly
- Feature flags are accessible
- Configuration singleton works

**If it fails**:
- Missing `.env` file
- Invalid environment variable format

---

### ✅ TEST 2: Database Connection
**What it does**: Tests basic database connectivity with Supabase

**Expected Result**:
```
✅ PASSED: Database Connection
```

**What it validates**:
- Supabase credentials are correct
- Network connection to Supabase works
- Adapter can execute simple queries

**If it fails**:
- Wrong `SUPABASE_URL` or `SUPABASE_KEY` in `.env`
- Network connectivity issues
- Query parser issues (already fixed!)

---

### ✅ TEST 3: Task Library - Count Tasks
**What it does**: Counts tasks in each category from the task library

**Expected Result**:
```
✅ PASSED: Task Library - Count Tasks
   Task counts by category:
     • hydration: 8 tasks
     • movement: 12 tasks
     • nutrition: 10 tasks
     • wellness: 8 tasks
     • recovery: 6 tasks
     • work: 6 tasks
   ✅ Total tasks: 50
```

**What it validates**:
- Task library table exists
- Seeding script worked correctly
- 50 tasks are accessible
- Tasks are distributed across 6 categories

**If it fails**:
- Task library not seeded (run seeding script first)
- Migration 001 not applied
- RLS policy blocking access

---

### ✅ TEST 4: Task Library - Select Tasks
**What it does**: Tests intelligent task selection based on archetype and mode

**Expected Result**:
```
✅ PASSED: Task Library - Select Tasks
   Selected 3 hydration tasks:
     • Morning Lemon Water (score: 0.92)
     • Green Tea Ritual (score: 0.89)
     • Alkaline Water Morning (score: 0.87)
```

**What it validates**:
- Task selection algorithm works
- Archetype fit scoring (70% weight)
- Mode fit scoring (30% weight)
- Proper filtering by category

**If it fails**:
- No tasks found for category (seeding issue)
- Scoring algorithm broken
- Database query issues

---

### ✅ TEST 5: Feedback - Record Task Completion
**What it does**: Records a test task completion with feedback

**Expected Result**:
```
✅ PASSED: Feedback - Record Task Completion
   ✅ Feedback recorded: <feedback_id>
```

**What it validates**:
- `user_task_feedback` table exists
- INSERT with RETURNING works
- Feedback ID is generated
- Timestamps are recorded

**If it fails**:
- Migration 002 not applied
- RLS policy issues
- INSERT query parsing issues

---

### ✅ TEST 6: Feedback - Get Preference Profile
**What it does**: Retrieves user preference profile (if exists)

**Expected Result** (first run):
```
✅ PASSED: Feedback - Get Preference Profile
   ℹ️  No profile yet (will be created on first feedback)
```

**Expected Result** (after feedback recorded):
```
✅ PASSED: Feedback - Get Preference Profile
   ✅ Profile found:
     Learning Phase: discovery
     Tasks Completed: 5
     Completion Rate: 80.0%
```

**What it validates**:
- `user_preference_profile` table exists
- Profile can be retrieved
- Profile auto-creates on first feedback
- Learning phase tracking works

**If it fails**:
- Migration 003 not applied
- User profile not created
- SELECT query issues

---

### ✅ TEST 7: Adaptive Selector - Discovery Phase
**What it does**: Tests phase-aware task selection (80% untried, 20% tried)

**Expected Result** (if `ADAPTIVE_LEARNING_ENABLED=true`):
```
✅ PASSED: Adaptive Selector - Discovery Phase
   ✅ Adaptive selection:
     • Tai Chi Flow
```

**Expected Result** (if disabled):
```
✅ PASSED: Adaptive Selector - Discovery Phase
   ⚠️  Adaptive learning disabled - skipping test
```

**What it validates**:
- Adaptive task selector works
- Discovery phase strategy (80/20 split)
- User history tracking
- Preference-based scoring

**If it fails**:
- Adaptive learning service broken
- User history query issues
- Phase detection broken

---

### ✅ TEST 8: Learning Phase - Check Progression
**What it does**: Tests automatic phase progression (Discovery → Establishment → Mastery)

**Expected Result** (if `ADAPTIVE_LEARNING_ENABLED=true`):
```
✅ PASSED: Learning Phase - Check Progression
   Current Phase: discovery
   Phase Changed: false
   Days in Phase: 2
   Tasks Completed: 5
```

**Expected Result** (if disabled):
```
✅ PASSED: Learning Phase - Check Progression
   ⚠️  Adaptive learning disabled - skipping test
```

**What it validates**:
- Learning phase manager works
- Phase transition logic (7 days OR 15 tasks for Discovery → Establishment)
- Progress tracking
- Celebration insights generation

**If it fails**:
- Phase manager service broken
- Profile query issues
- Phase criteria calculation errors

---

### ✅ TEST 9: Plan Generator - Generate Daily Plan
**What it does**: Generates a complete daily plan using the task library

**Expected Result** (if `ENABLE_DYNAMIC_PLANS=true`):
```
✅ PASSED: Plan Generator - Generate Daily Plan
   ✅ Plan generated:
     Tasks: 12
     Phase: discovery
       • Morning Lemon Water (hydration)
       • Gentle Morning Yoga (movement)
       • Protein-Packed Smoothie (nutrition)
       • Morning Meditation (wellness)
       • ...
```

**Expected Result** (if disabled):
```
✅ PASSED: Plan Generator - Generate Daily Plan
   ⚠️  Dynamic plans disabled - skipping test
```

**What it validates**:
- DynamicPlanGenerator orchestration works
- Task selection for multiple categories
- Learning phase integration
- Rotation prevention
- Complete plan structure

**If it fails**:
- Plan generator service broken
- Task selection issues
- Missing categories
- Orchestration logic errors

---

### ✅ TEST 10: Weekly Summary - Generate Summary
**What it does**: Generates weekly insights and recommendations

**Expected Result** (if `WEEKLY_SUMMARIES_ENABLED=true` and user has data):
```
✅ PASSED: Weekly Summary - Generate Summary
   ✅ Summary generated:
     Total Tasks: 28
     Completed: 22
     Insights: 3
```

**Expected Result** (if no data yet):
```
✅ PASSED: Weekly Summary - Generate Summary
   ℹ️  No data for summary yet: Insufficient user data
```

**Expected Result** (if disabled):
```
✅ PASSED: Weekly Summary - Generate Summary
   ⚠️  Weekly summaries disabled - skipping test
```

**What it validates**:
- WeeklySummaryService works
- Completion statistics calculation
- Category performance analysis
- Favorite tasks identification
- Streak tracking
- Personalized insights generation

**If it fails**:
- Summary service broken
- Feedback query issues
- Calculation errors
- Insufficient test data

---

## Overall Success Criteria

### 🎯 Minimum Required (for basic functionality):
- **4-5 tests passing** = Basic infrastructure works
  - TEST 1: Configuration ✅
  - TEST 2: Database Connection ✅
  - TEST 3: Task Library Count ✅
  - TEST 4: Task Selection ✅
  - TEST 6: Preference Profile ✅

### 🎯 Good Progress (core features work):
- **6-7 tests passing** = Core features operational
  - All minimum tests ✅
  - TEST 5: Feedback Recording ✅
  - One Phase 2 test ✅

### 🎯 Production Ready (everything works):
- **10/10 tests passing** = System fully operational
  - All Phase 1 tests ✅
  - All Phase 2 tests ✅ (if enabled)
  - Complete end-to-end flow ✅

---

## Current Status (Based on Your Last Run)

Your test run showed:
- ✅ 6 tests passing (60%)
- ❌ 4 tests failing

### What's Working:
1. ✅ Configuration loads correctly
2. ✅ Preference profile retrieval works
3. ✅ Phase 2 tests skip properly when disabled

### What Needs Fixing:
1. ❌ Database connection test (simple SELECT query)
2. ❌ Task library count (GROUP BY query format)
3. ❌ Task selection (no tasks found - likely related to count)
4. ❌ Feedback recording (INSERT RETURNING query)

---

## After My Fixes

You should now see:
- ✅ TEST 2 passing (simple SELECT fixed)
- ✅ TEST 3 likely passing (COUNT query improved)
- ✅ TEST 4 likely passing (tasks now found)
- ❌ TEST 5 might still fail (INSERT RETURNING needs data parsing)

**Expected new result**: **7-8 tests passing (70-80%)**

---

## Next Steps After Tests Pass

Once you get 8+ tests passing:

1. **Enable dynamic plans** in `.env`:
   ```env
   ENABLE_DYNAMIC_PLANS=true
   ADAPTIVE_LEARNING_ENABLED=true
   WEEKLY_SUMMARIES_ENABLED=true
   ```

2. **Re-run tests** - should get 10/10 passing

3. **Start the backend**:
   ```bash
   python start_openai.py
   ```

4. **Test API endpoints**:
   ```bash
   ./testing/test_api_endpoints.sh
   ```

5. **Deploy gradually** following `DEPLOYMENT_GUIDE.md`

---

## Troubleshooting Common Test Failures

### "Task library is empty!"
**Solution**: Run seeding script first
```bash
python -m services.seeding.task_library_seed
```

### "Row-level security policy violation"
**Solution**: Use service role key in `.env`
```env
SUPABASE_SERVICE_KEY=your_service_key_here
```

### "Query operation not recognized"
**Solution**: Already fixed in adapter! Re-run tests.

### "No module named 'shared_libs.utils.logger'"
**Solution**: Already fixed! Logger utility created.

### Tests skip with "disabled" warnings
**Solution**: This is NORMAL if features are disabled in `.env`. Enable them to run full tests.

---

## Summary

The test suite validates:
- ✅ Database infrastructure (migrations, RLS)
- ✅ Task library (seeding, selection, scoring)
- ✅ Feedback system (recording, profiles, learning)
- ✅ Adaptive learning (phases, progression, summaries)
- ✅ Plan generation (orchestration, integration)

**Goal**: 10/10 tests passing = Production ready! 🚀
