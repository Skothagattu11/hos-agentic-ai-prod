# Phase 4 Integration Test - README

## Overview

This test validates the complete **Option B (Feedback-Driven Pre-seeding)** integration by testing the second half of the system:

1. **Routine Planning Agent** (with preselected library tasks)
2. **Plan Extraction Service** (with source tracking)

The test uses **REAL DATA** and interacts with the **REAL DATABASE** to replicate the actual production flow.

---

## What This Test Does

### Test Flow

```
1. Load Real Data
   ↓
   - Circadian Analysis (from holistic_analysis_results_rows.json)
   - Behavior Analysis (from holistic_analysis_results_rows.json)
   - User ID: a57f70b4-d0a4-4aef-b721-a4b526f64869
   - Archetype: Peak Performer

2. Fetch Real Library Tasks
   ↓
   - Queries task_library table
   - Fetches 6 tasks matching Peak Performer archetype
   - Includes: id, name, category, variation_group, etc.

3. Build Mock Preselected Tasks
   ↓
   - Simulates TaskPreseeder output
   - Uses real library task data
   - Adds selection metadata (learning phase, feedback count)

4. Call Routine Planning Agent
   ↓
   - Calls run_routine_planning_4o() from openai_main.py
   - Passes preselected_tasks parameter (Option B integration)
   - AI generates plan including library tasks

5. Save Plan to Database
   ↓
   - Inserts into holistic_analysis_results table
   - Generates unique analysis_result_id
   - Stores complete plan JSON

6. Call Plan Extraction Service
   ↓
   - Calls extract_and_store_plan_items() from plan_extraction_service.py
   - Passes preselected_tasks parameter (Option B integration)
   - Matches tasks to library tasks
   - Tags with source='library' or source='ai'

7. Verify Results
   ↓
   - Counts library vs AI tasks
   - Verifies task_library_id linkage
   - Validates source tracking
   - Checks category, variation_group population
```

---

## Running the Test

### Prerequisites

1. **Environment Variables**: Ensure `.env` file has:
   - `OPENAI_API_KEY` - Required for routine planning
   - `SUPABASE_URL` - Database connection
   - `SUPABASE_KEY` - Database authentication
   - `DATABASE_URL` - PostgreSQL connection string

2. **Database Setup**: Ensure tables exist:
   - `task_library` (with at least 6 tasks)
   - `holistic_analysis_results`
   - `plan_items`
   - `time_blocks`

3. **Data File**: Ensure `holistic_analysis_results_rows.json` exists in project root

### Execute Test

```bash
# Option 1: Direct execution
python testing/test_phase4_routine_extraction_real.py

# Option 2: Quick runner
python run_phase4_test.py
```

---

## Expected Output

### Success Output Example

```
================================================================================
PHASE 4 INTEGRATION TEST: Routine Planning + Extraction
================================================================================

🔧 Initializing database connections...
✅ Database connections established

📂 Loading real analysis data from holistic_analysis_results_rows.json...
   ✅ Loaded circadian analysis (ID: afae788e-03d4-40cc-8461-61eedc004e2c)
      - Energy timeline: 96 slots
      - Peak windows: 1
   ✅ Loaded behavior analysis (ID: 5f867282-2ef4-461c-8e91-7cf8abdedeb4)
      - Sophistication level: advanced
      - Consistency score: 0.75

📚 Fetching 6 real library tasks from database...
   ✅ Fetched 6 library tasks:
      - Morning Hydration (hydration, 5min, morning)
      - Protein-Rich Breakfast (nutrition, 20min, morning)
      - Mid-Morning Movement (movement, 15min, any)
      - Afternoon Energy Boost (nutrition, 10min, afternoon)
      - Evening Wind-Down (mindfulness, 10min, evening)
      - Sleep Hygiene Routine (sleep, 15min, evening)

🎭 Building mock preselected_tasks result...
   ✅ Mock preselected_tasks created:
      - Learning phase: establishment
      - Total selected: 6
      - Categories: hydration, nutrition, movement, mindfulness, sleep

🤖 Testing Routine Planning Agent...
================================================================================

📋 Calling run_routine_planning_4o()...
   - Archetype: Peak Performer
   - Preselected tasks: 6 tasks
   - User timezone: America/New_York

✅ Routine planning completed!
   - Status: success
   - Plan length: 15234 characters

💾 Saving plan to holistic_analysis_results table...
   ✅ Plan saved to database
      - Analysis Result ID: 3c7e9b2a-4f1d-4a8e-9c5b-2e8d7f6a3b9c
      - Table: holistic_analysis_results

🔍 Testing Plan Extraction Service...
================================================================================

📋 Calling extract_and_store_plan_items()...
   - Analysis Result ID: 3c7e9b2a-4f1d-4a8e-9c5b-2e8d7f6a3b9c
   - Profile ID: a57f70b4-d0a4-4aef-b721-a4b526f64869
   - Preselected tasks: 6 tasks

✅ Plan extraction completed!
   - Total items extracted: 11

🔬 Verifying Option B Integration Results...
================================================================================

📊 Task Distribution:
   - Total tasks: 11
   - Library tasks: 6
   - AI-generated tasks: 5

📚 Library Task Verification:
   ✅ 'Morning Hydration'
      - Source: library
      - Task Library ID: 8b3c1a5e-2f9d-4c7b-8e6a-1d3f5b7c9e2a
      - Category: hydration
      - Variation Group: hydration_basic
      - ✅ Correctly matched to preselected task

   ✅ 'Protein-Rich Breakfast'
      - Source: library
      - Task Library ID: 2a5c8d1e-9f3b-4e7a-6c8d-5f1b3e7a9c2d
      - Category: nutrition
      - Variation Group: nutrition_breakfast
      - ✅ Correctly matched to preselected task

   ... (4 more library tasks)

🤖 AI-Generated Task Verification:
   🤖 'Focus Block: Deep Work Session'
      - Source: ai
      - Task Library ID: None (should be None)
      - Category: None (should be None)

   🤖 'Lunch Break: Mindful Eating'
      - Source: ai
      - Task Library ID: None (should be None)
      - Category: None (should be None)

   ... (3 more AI tasks)

✅ SUCCESS CRITERIA:
   - Library tasks found: 6 (expected: 6)
   - Library tasks have task_library_id: True
   - AI tasks have source='ai': True
   - AI tasks have task_library_id=None: True

================================================================================
✅ PHASE 4 INTEGRATION TEST COMPLETED SUCCESSFULLY!
================================================================================
```

---

## What Gets Verified

### 1. Routine Planning Integration (Phase 3)
- ✅ Preselected tasks passed to `run_routine_planning_4o()`
- ✅ AI prompt enhanced with library task section
- ✅ Warm start mode activated (learning phase shown)
- ✅ Plan generated successfully

### 2. Plan Extraction Integration (Phase 4)
- ✅ Preselected tasks passed to `extract_and_store_plan_items()`
- ✅ Task matching logic executed (case-insensitive)
- ✅ Library tasks matched correctly
- ✅ Source tracking applied ('library' vs 'ai')

### 3. Database Storage
- ✅ Plan saved to `holistic_analysis_results`
- ✅ Plan items saved to `plan_items` table
- ✅ Time blocks saved to `time_blocks` table
- ✅ New Option B columns populated:
  - `source` (library/ai)
  - `task_library_id` (UUID or null)
  - `category` (from library or null)
  - `subcategory` (from library or null)
  - `variation_group` (from library or null)

---

## Troubleshooting

### Error: "No library tasks found"
**Cause**: `task_library` table is empty or has no Peak Performer tasks

**Solution**:
```sql
-- Check if task_library has data
SELECT COUNT(*) FROM task_library;

-- Check if Peak Performer tasks exist
SELECT * FROM task_library WHERE archetype_fit ? 'Peak Performer' LIMIT 5;
```

If empty, you need to populate the `task_library` table with tasks.

---

### Error: "Failed to save plan"
**Cause**: Missing columns in `holistic_analysis_results` table

**Solution**: Ensure table has all required columns (id, user_id, analysis_type, archetype, analysis_result, etc.)

---

### Error: "OPENAI_API_KEY not found"
**Cause**: Missing OpenAI API key in environment

**Solution**:
```bash
# Add to .env file
OPENAI_API_KEY=sk-...your-key-here...
```

---

### Error: Database connection timeout
**Cause**: Invalid `DATABASE_URL` or Supabase credentials

**Solution**: Verify connection strings in `.env`:
```bash
DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=your-anon-key
```

---

## Success Criteria

The test is **SUCCESSFUL** if:

1. ✅ **Routine planning completes** without errors
2. ✅ **Plan saved to database** with valid analysis_result_id
3. ✅ **Extraction completes** without errors
4. ✅ **Library tasks matched** (count matches preselected count)
5. ✅ **Library tasks linked** (all have task_library_id populated)
6. ✅ **AI tasks tagged** (all have source='ai' and task_library_id=None)
7. ✅ **Categories populated** for library tasks
8. ✅ **Variation groups populated** for library tasks

---

## What This Test Does NOT Cover

This test focuses on **Phase 3-4 integration only**. It does NOT test:

- ❌ TaskPreseeder service (we mock its output)
- ❌ Behavior Analysis Agent
- ❌ Memory Management Agent
- ❌ Full orchestration flow
- ❌ Task rotation logic (variation_group usage)
- ❌ Feedback recording
- ❌ Learning phase transitions

For complete system testing, see:
- `testing/test_user_journey_simple.py` (full end-to-end flow)
- `testing/test_phase2_task_preseeder.py` (TaskPreseeder testing)

---

## Next Steps

After successful test:

1. **Verify Database**: Check `plan_items` table to see source tracking in action
2. **Test Rotation**: Run test multiple times to verify variation_group prevents duplicates
3. **Test Cold Start**: Modify mock to set `has_sufficient_feedback=False` and verify pure AI mode
4. **Production Testing**: Deploy and monitor real user plans

---

## Files Modified/Used

### Test Files (New)
- `testing/test_phase4_routine_extraction_real.py` - Main test script
- `run_phase4_test.py` - Quick runner
- `testing/PHASE4_TEST_README.md` - This file

### Production Code (Tested)
- `services/api_gateway/openai_main.py` - Routine planning with Option B
- `services/plan_extraction_service.py` - Extraction with source tracking

### Data Files (Read)
- `holistic_analysis_results_rows.json` - Real circadian/behavior analysis

### Database Tables (Read/Write)
- `task_library` (READ) - Fetch real library tasks
- `holistic_analysis_results` (WRITE) - Save plan
- `plan_items` (WRITE) - Store extracted tasks
- `time_blocks` (WRITE) - Store time blocks

---

## Questions?

If the test fails or you need help:
1. Check the error message carefully
2. Review the Troubleshooting section above
3. Verify all prerequisites are met
4. Check database connectivity
5. Ensure OpenAI API key is valid

**Good luck testing!** 🚀
