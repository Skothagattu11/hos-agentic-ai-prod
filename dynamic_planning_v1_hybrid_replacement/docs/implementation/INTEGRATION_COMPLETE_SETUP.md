# Task Library Integration - Complete Setup Guide

## Overview
This guide walks you through integrating the dynamic task library system with your existing engagement tracking system (`task_checkins` and `plan_items`).

**Key Benefit**: Uses your existing production tables instead of creating duplicate feedback tables.

---

## Step 1: Run Database Migration

Execute the migration to add task library columns to existing tables:

```bash
# Connect to your Supabase database and run:
psql -h db.YOUR_PROJECT.supabase.co -U postgres -d postgres -f supabase/user-engagement/006_add_task_library_integration.sql
```

**Or via Supabase Dashboard**:
1. Go to SQL Editor
2. Open `supabase/user-engagement/006_add_task_library_integration.sql`
3. Run the migration

**What It Does**:
- Adds `task_library_id`, `source`, `category`, `subcategory`, `variation_group` to `plan_items`
- Adds `user_mode`, `user_archetype`, `day_of_week` to `task_checkins`
- Creates views for easy querying (`task_feedback_complete`, `library_task_performance`, `user_preference_summary`)
- Creates indexes for performance

---

## Step 2: Verify Migration Success

```sql
-- Check if columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'plan_items'
  AND column_name IN ('task_library_id', 'source', 'category', 'subcategory', 'variation_group');

-- Check views were created
SELECT * FROM task_feedback_complete LIMIT 1;
SELECT * FROM library_task_performance LIMIT 1;
SELECT * FROM user_preference_summary LIMIT 1;
```

---

## Step 3: Code Changes (Already Done)

The following files have been updated:

### ✅ Plan Extraction Service
- **File**: `services/plan_extraction_service.py`
- **Changes**:
  - Added fields to `ExtractedTask` dataclass
  - Modified `_store_plan_items_with_time_blocks` to store new fields

### ✅ Dynamic Task Selector
- **File**: `services/dynamic_personalization/dynamic_task_selector.py`
- **Changes**:
  - `_create_replaced_task` now includes `source`, `category`, `subcategory`
  - `_mark_as_ai_task` now marks source as 'ai'

### 🔄 Next: Update Feedback Services
- Need to update `FeedbackAnalyzerService` to query `task_checkins`
- Need to update `AdaptiveTaskSelector` to use new views
- Need to update test script to use `/api/v1/engagement/task-checkin`

---

## Step 4: Test the Integration

### Run the 4-Day Journey Test
```bash
cd /mnt/c/dev_skoth/hos/hos-agentic-ai-prod
python testing/test_realistic_user_journey.py
```

**What It Tests**:
1. Generates 4 days of plans with hybrid system
2. Simulates user completing 60-80% of tasks
3. Posts feedback to `/api/v1/engagement/task-checkin`
4. Verifies adaptive learning works

---

## Step 5: Monitor the System

### Check Library Task Performance
```sql
SELECT * FROM library_task_performance
WHERE total_assignments > 0
ORDER BY avg_satisfaction DESC, completed_count DESC
LIMIT 10;
```

### Check User Preferences
```sql
SELECT * FROM user_preference_summary
WHERE profile_id = 'YOUR_USER_ID'
ORDER BY avg_satisfaction DESC;
```

### Check Task Sources
```sql
SELECT
    source,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN source = 'library' THEN 1 END) as library_tasks,
    ROUND(100.0 * COUNT(CASE WHEN source = 'library' THEN 1 END) / COUNT(*), 2) as library_percentage
FROM plan_items
WHERE profile_id = 'YOUR_USER_ID'
GROUP BY source;
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     PLAN GENERATION                          │
├─────────────────────────────────────────────────────────────┤
│  AI Generates Plan → Dynamic Selector Replaces Tasks        │
│         ↓                        ↓                           │
│  holistic_analysis_results   time_blocks                     │
│         ↓                        ↓                           │
│              plan_items                                      │
│         (task_library_id, source, category)                  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    USER ENGAGEMENT                           │
├─────────────────────────────────────────────────────────────┤
│  Flutter App → POST /api/v1/engagement/task-checkin         │
│         ↓                                                    │
│    task_checkins                                             │
│  (completion_status, satisfaction_rating, user_mode)         │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  ADAPTIVE LEARNING                           │
├─────────────────────────────────────────────────────────────┤
│  Query: task_feedback_complete VIEW                          │
│         ↓                                                    │
│  AdaptiveTaskSelector → Learns user preferences              │
│         ↓                                                    │
│  Next Plan → More library tasks based on favorites           │
└─────────────────────────────────────────────────────────────┘
```

---

## Benefits of This Integration

### ✅ No Duplicate Data
- Single source of truth: `task_checkins`
- No sync issues between tables

### ✅ Production Ready
- Flutter app already using engagement endpoints
- No mobile app changes needed
- Working RLS policies

### ✅ Better Data Model
- `completion_status` enum > boolean
- Full plan lineage tracking
- Richer feedback data

### ✅ Easy Queries
- Views pre-calculate metrics
- JOIN complexity hidden
- Fast performance with indexes

---

## Cleanup (After Testing)

Once integration is verified working, you can remove unused tables:

```sql
-- OPTIONAL: Remove old feedback tables (after confirming not used)
DROP TABLE IF EXISTS user_task_feedback CASCADE;
DROP TABLE IF EXISTS user_preference_profile CASCADE;
DROP TABLE IF EXISTS task_rotation_state CASCADE;

-- OPTIONAL: Remove old feedback endpoints
-- Delete services/api_gateway/feedback_endpoints.py
-- Remove registration in services/api_gateway/openai_main.py
```

---

## Troubleshooting

### Migration Failed
- Check if columns already exist
- Check Supabase connection
- Run migration manually via SQL Editor

### Plan Items Missing task_library_id
- Check DynamicTaskSelector is marking tasks correctly
- Check PlanExtractionService is extracting fields
- Verify `ENABLE_DYNAMIC_TASK_SELECTION=true` in `.env`

### Test Script Failing
- Verify server is running on port 8002
- Check `/api/v1/engagement/task-checkin` endpoint exists
- Confirm API key is correct

---

## Next Steps

1. ✅ Run migration
2. 🔄 Update remaining services (FeedbackAnalyzerService, AdaptiveTaskSelector)
3. 🔄 Update test script to use engagement endpoint
4. ⏳ Run 4-day journey test
5. ⏳ Enable for alpha user
6. ⏳ Monitor real-world usage

---

## Contact

For issues or questions:
- Check logs in `logs/agent_handoffs/`
- Review API docs at `http://localhost:8002/docs`
- Test with `curl` commands

