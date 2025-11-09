# Quick Start: Run Schedule Anchoring Test

## 1. Start the Backend (Terminal 1)

```bash
cd /Users/kothagattu/Desktop/OG/hos-agentic-ai-prod
python start_openai.py
```

Wait for: `✅ Server running on http://0.0.0.0:8002`

## 2. Run the Test (Terminal 2)

### Option A: Direct Python (Recommended)
```bash
cd /Users/kothagattu/Desktop/OG/hos-agentic-ai-prod
python testing/test_schedule_anchoring.py a57f70b4-d0a4-4aef-b721-a4b526f64869
```

**Interactive Cleanup**: After the test completes, you'll be asked:
```
🗑️  Do you want to DELETE this test data? (y/N):
```
- Type `y` + Enter to delete the test data
- Type `N` or just Enter to keep the data for inspection

### Option B: Shell Script (Auto-cleanup)
```bash
cd /Users/kothagattu/Desktop/OG/hos-agentic-ai-prod
echo "y" | python testing/test_schedule_anchoring.py a57f70b4-d0a4-4aef-b721-a4b526f64869
```

## What to Expect

The test will:
1. ✅ Create a "Morning Routine" schedule with 7 tasks
2. ✅ Create a wellness plan with 7 health tasks
3. ✅ Call the anchoring endpoint
4. ✅ Show which tasks were anchored and which are standalone
5. ✅ Ask if you want to clean up test data

## Success Looks Like:

```
================================================================================
 ANCHORING RESULTS
================================================================================

  ✅ Anchored Tasks (Matched to Schedule)

Total: 3 tasks successfully anchored

  ⚓ 06:15  Morning Hydration
     → Anchored to: Morning Shower
     → Confidence: 0.82

  ⚓ 06:45  Protein-Rich Breakfast
     → Anchored to: Breakfast
     → Confidence: 0.95

  📊 Summary Statistics
  Total Tasks: 7
  Anchored: 3 (42.9%)
  Standalone: 4 (57.1%)

================================================================================
 TEST COMPLETE ✅
================================================================================
```

## If It Fails

### Foreign Key Constraint Error

If you see: `violates foreign key constraint "fk_saved_schedules_user"`

**Quick Fix**: Run this SQL in Supabase SQL Editor to allow any user_id:
```sql
ALTER TABLE saved_schedules DROP CONSTRAINT IF EXISTS fk_saved_schedules_user;
```

Or run: `database/migrations/remove_fk_constraint_saved_schedules.sql`

### Other Common Issues

1. **Check backend is running**: Look for port 8002 in logs
2. **Check database tables exist**: Run the migration SQL in Supabase
3. **Check environment variables**: Verify `.env` has correct DATABASE_URL
4. **Invalid UUID error**: Run the SQL above to remove foreign key constraint

## Full Documentation

See `testing/SCHEDULE_ANCHORING_TEST_README.md` for complete details.
