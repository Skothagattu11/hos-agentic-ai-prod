# Schedule Anchoring Test Script

## Overview

This test script validates the complete schedule anchoring integration:
1. Creates a realistic test schedule with tasks (e.g., "Morning Routine")
2. Creates/fetches a wellness plan for today
3. Calls the `/api/v1/anchor/generate` endpoint
4. Displays anchored tasks vs standalone tasks with visual timeline
5. Offers cleanup of test data

## Prerequisites

1. **Backend Running**: Make sure the FastAPI server is running
   ```bash
   cd /Users/kothagattu/Desktop/OG/hos-agentic-ai-prod
   python start_openai.py
   ```

2. **Environment Variables**: Ensure `.env` file has database credentials
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   DATABASE_URL=postgresql://...
   ```

3. **Database Tables**: Ensure these tables exist in Supabase:
   - `saved_schedules`
   - `scheduled_tasks`
   - `holistic_analysis_results`
   - `plan_items`

## Quick Start

### Option 1: Using the Shell Script (Easiest)

```bash
cd /Users/kothagattu/Desktop/OG/hos-agentic-ai-prod

# Generate a random test user ID
./run_schedule_anchoring_test.sh $(uuidgen)

# Or use a specific user ID
./run_schedule_anchoring_test.sh test-user-123
```

### Option 2: Direct Python Execution

```bash
cd /Users/kothagattu/Desktop/OG/hos-agentic-ai-prod

# With a specific user ID
python testing/test_schedule_anchoring.py test-user-123

# Or generate a random UUID
python testing/test_schedule_anchoring.py $(python -c "import uuid; print(str(uuid.uuid4()))")
```

## What the Test Does

### Step 1: Create Test Schedule
Creates a "Test Morning Routine" schedule with 7 tasks:
- 06:00-06:20: Morning Shower
- 06:30-07:00: Breakfast
- 07:30-08:00: Commute to Work
- 09:00-09:30: Morning Meeting
- 12:00-13:00: Lunch Break
- 15:00-15:15: Afternoon Coffee
- 17:00-17:30: Commute Home

### Step 2: Create/Fetch Test Plan
Creates a wellness plan with 7 health tasks:
- 06:15: Morning Hydration (5min)
- 06:45: Protein-Rich Breakfast (20min)
- 07:10: 10-Minute Morning Walk (10min)
- 08:45: Mindful Breathing (5min)
- 12:15: Healthy Lunch (30min)
- 15:30: Afternoon Stretch (5min)
- 18:00: Evening Reflection (10min)

### Step 3: Call Anchoring Endpoint
Sends HTTP POST request to `http://localhost:8002/api/v1/anchor/generate`:
```json
{
  "user_id": "test-user-123",
  "date": "2025-11-09",
  "schedule_id": "schedule-uuid",
  "include_google_calendar": false,
  "confidence_threshold": 0.7
}
```

### Step 4: Display Results
Shows:
- ✅ **Anchored Tasks**: Tasks matched to schedule events with confidence >= 0.7
- 📍 **Standalone Tasks**: Tasks that didn't find good matches
- 📊 **Statistics**: Anchoring success rate, average confidence

### Step 5: Cleanup (Optional)
Asks if you want to delete the test data from the database.

## Expected Output

```
================================================================================
 SCHEDULE ANCHORING INTEGRATION TEST
================================================================================

User ID: test-user-123
Target Date: 2025-11-09

--------------------------------------------------------------------------------
  Step 1: Creating Test Schedule
--------------------------------------------------------------------------------
✅ Created schedule: Test Morning Routine (ID: a1b2c3d4...)
   Days: Monday-Friday

📋 Creating schedule tasks:
   ✓ 06:00 - 06:20  Morning Shower
   ✓ 06:30 - 07:00  Breakfast
   ✓ 07:30 - 08:00  Commute to Work
   ✓ 09:00 - 09:30  Morning Meeting
   ✓ 12:00 - 13:00  Lunch Break
   ✓ 15:00 - 15:15  Afternoon Coffee
   ✓ 17:00 - 17:30  Commute Home

✅ Created 7 schedule tasks

--------------------------------------------------------------------------------
  Step 2: Getting/Creating Test Plan
--------------------------------------------------------------------------------
⚠️  No existing plan found. Creating test plan...
✅ Created plan: xyz789ab...

📋 Creating test plan items:
   ✓ 06:15  Morning Hydration (5min)
   ✓ 06:45  Protein-Rich Breakfast (20min)
   ✓ 07:10  10-Minute Morning Walk (10min)
   ✓ 08:45  Mindful Breathing (5min)
   ✓ 12:15  Healthy Lunch (30min)
   ✓ 15:30  Afternoon Stretch (5min)
   ✓ 18:00  Evening Reflection (10min)

✅ Created 7 plan items

--------------------------------------------------------------------------------
  Step 3: Calling Anchoring Endpoint
--------------------------------------------------------------------------------
📤 Sending request to: http://localhost:8002/api/v1/anchor/generate
   User ID: test-user-123
   Date: 2025-11-09
   Schedule ID: a1b2c3d4...
   Confidence Threshold: 0.7

✅ Response received successfully
   Anchored tasks: 3
   Standalone tasks: 4

================================================================================
 ANCHORING RESULTS
================================================================================

--------------------------------------------------------------------------------
  ✅ Anchored Tasks (Matched to Schedule)
--------------------------------------------------------------------------------

Total: 3 tasks successfully anchored

  ⚓ 06:15  Morning Hydration
     → Anchored to: Morning Shower
     → Confidence: 0.82
     → Duration: 5 minutes
     → Category: hydration

  ⚓ 06:45  Protein-Rich Breakfast
     → Anchored to: Breakfast
     → Confidence: 0.95
     → Duration: 20 minutes
     → Category: nutrition

  ⚓ 12:15  Healthy Lunch
     → Anchored to: Lunch Break
     → Confidence: 0.88
     → Duration: 30 minutes
     → Category: nutrition

--------------------------------------------------------------------------------
  📍 Standalone Tasks (No Good Match)
--------------------------------------------------------------------------------

Total: 4 tasks remain standalone

  📌 07:10 - 07:20  10-Minute Morning Walk
     → Duration: 10 minutes

  📌 08:45 - 08:50  Mindful Breathing
     → Duration: 5 minutes

  📌 15:30 - 15:35  Afternoon Stretch
     → Duration: 5 minutes

  📌 18:00 - 18:10  Evening Reflection
     → Duration: 10 minutes

--------------------------------------------------------------------------------
  📊 Summary Statistics
--------------------------------------------------------------------------------

  Total Tasks: 7
  Anchored: 3 (42.9%)
  Standalone: 4 (57.1%)
  Average Confidence: 0.88

================================================================================
 TEST COMPLETE ✅
================================================================================

The anchoring endpoint is working correctly!
You can now use this feature in the Flutter app.
```

## Cleanup

The test offers to clean up test data at the end:
```
Do you want to clean up test data? (y/N):
```

- Enter `y` to delete the test schedule and plan
- Enter `N` (or anything else) to keep the data for inspection

## Troubleshooting

### Error: "No module named 'httpx'"
```bash
pip install httpx
```

### Error: "Connection refused"
Make sure the backend is running:
```bash
python start_openai.py
# Should show: Server running on http://0.0.0.0:8002
```

### Error: "Table not found"
Run the database migration:
```bash
# In Supabase SQL Editor, run:
# HolisticOS-app/database/migrations/create_saved_schedules_tables.sql
```

### Error: "API returned 500"
Check backend logs:
```bash
# Backend terminal should show error details
# Look for [ANCHORING] error messages
```

## Advanced Usage

### Test with Existing User Data

If you have a real user ID with existing plans:

```bash
python testing/test_schedule_anchoring.py your-real-user-uuid
```

The script will:
- Create a test schedule for that user
- Use their existing plan if one exists for today
- Run anchoring with real data

### Test Different Confidence Thresholds

Edit the script to test different thresholds:

```python
# In test_schedule_anchoring.py, line 367:
result = await call_anchoring_endpoint(
    user_id=user_id,
    target_date=target_date,
    schedule_id=schedule_id,
    confidence_threshold=0.5  # Changed from 0.7 to 0.5
)
```

Lower threshold = more tasks anchored (but with lower confidence)

### Keep Test Data for Manual Inspection

When prompted for cleanup, choose `N`:
```
Do you want to clean up test data? (y/N): N
```

Then inspect in Supabase:
```sql
-- View test schedule
SELECT * FROM saved_schedules WHERE name = 'Test Morning Routine';

-- View schedule tasks
SELECT * FROM scheduled_tasks WHERE schedule_id = 'your-schedule-id';

-- View plan items
SELECT * FROM plan_items WHERE analysis_id = 'your-analysis-id';
```

## Integration with Flutter App

After running this test successfully, the Flutter app's "Generate Anchors" button will work!

The frontend sends the exact same request format that this test uses.

## Files Created by This Test

- `testing/test_schedule_anchoring.py` - Main test script
- `run_schedule_anchoring_test.sh` - Convenience runner script
- `testing/SCHEDULE_ANCHORING_TEST_README.md` - This documentation

## Next Steps

1. ✅ Run this test to verify backend works
2. ✅ Open Flutter app and create a real schedule
3. ✅ Click "Generate Anchors" and see it work!
4. 🎉 Celebrate successful integration!
