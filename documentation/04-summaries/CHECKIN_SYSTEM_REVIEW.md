# Daily Check-in System Review & SQL Requirements

## ✅ Existing System (Already Implemented)

### Tables You Already Have

#### 1. **`task_checkins`** ✅
**Status**: Fully functional, just needs 3 small additions

**Current Fields**:
- `completion_status` - completed/partial/skipped
- `satisfaction_rating` - 1-5 scale
- `planned_date`, `planned_time`, `actual_completion_time`
- `user_notes` - Free text feedback

**What It Does**: Tracks individual task completions with ratings

#### 2. **`daily_journals`** ✅
**Status**: Excellent! Already has most of what you need

**Current Fields**:
- **Wellbeing Scales** (1-5): energy_level, mood_rating, sleep_quality, stress_level
- **Nutrition**: nutrition_satisfaction, hydration_glasses, meal_timing_satisfaction
- **Habits**: breathing_exercises, sunlight_exposure, mindfulness_practice
- **Reflection**: what_went_well, what_was_challenging, tomorrow_intentions
- **Gratitude**: gratitude_notes (array)
- **Voice**: voice_note_url, voice_note_duration_seconds

**What It Does**: End-of-day holistic reflection

#### 3. **`plan_items`** ✅
**Status**: Fully functional

**Key Fields**:
- Extracted tasks from AI-generated plans
- Links to `holistic_analysis_results`
- Tracks scheduled times and durations
- Has `is_trackable` flag

#### 4. **`time_blocks`** ✅
**Status**: Fully functional

**Key Fields**:
- Block structure for daily plans
- Links to analysis results
- Has context and purpose

### APIs You Already Have ✅

Located in: `services/api_gateway/engagement_endpoints.py`

**Task Check-in APIs**:
- `POST /api/v1/engagement/task-checkin` - Individual task check-in
- `POST /api/v1/engagement/batch-checkin` - Multiple tasks at once
- `GET /api/v1/engagement/tasks/{profile_id}` - Get tasks with status
- `GET /api/v1/engagement/checkins/status/{profile_id}` - Check-in status

**Daily Journal APIs**:
- `POST /api/v1/engagement/journal` - Submit daily journal
- `GET /api/v1/engagement/journal/{profile_id}` - Get journal

**Analytics APIs**:
- `GET /api/v1/engagement/analytics/{profile_id}/completion-summary`
- `GET /api/v1/engagement/engagement-context/{profile_id}`

---

## 🔧 What You Need to Add (SQL Changes Only)

### Minimal SQL Additions Required

I've created `DAILY_CHECKIN_SQL_ADDITIONS.sql` with these changes:

#### 1. Add 3 Columns to `task_checkins` Table

```sql
ALTER TABLE task_checkins
ADD COLUMN continue_preference VARCHAR(10),  -- yes/no/maybe
ADD COLUMN enjoyed BOOLEAN,                   -- true/false
ADD COLUMN timing_feedback VARCHAR(10);       -- perfect/early/late
```

**Why**: Captures the daily check-in questions:
- "Would you like this task tomorrow?" → `continue_preference`
- "Did you enjoy this?" → `enjoyed`
- "How was the timing?" → `timing_feedback`

#### 2. Add 3 Columns to `daily_journals` Table

```sql
ALTER TABLE daily_journals
ADD COLUMN checkin_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN checkin_reminder_sent BOOLEAN DEFAULT FALSE,
ADD COLUMN checkin_reminder_sent_at TIMESTAMP WITH TIME ZONE;
```

**Why**: Tracks check-in completion and notification status

#### 3. Add `plan_date` to `plan_items` (if not exists)

```sql
ALTER TABLE plan_items ADD COLUMN plan_date DATE;
```

**Why**: Makes it easy to query "What tasks are for today?" for check-in screen

#### 4. Create Helper View: `daily_checkin_status`

```sql
CREATE VIEW daily_checkin_status AS ...
```

**Why**: Quick summary of check-in completion for a date

#### 5. Create Helper Functions

Two PostgreSQL functions to make queries easier:

**Function 1**: `get_tasks_needing_checkin(profile_id, date)`
- Returns tasks that need feedback
- Used by check-in screen

**Function 2**: `can_regenerate_plan(profile_id, date)`
- Returns true/false if user can regenerate plan
- Used to show "Regenerate Plan" button

---

## 📋 What You Need to Do Now

### Step 1: Run SQL Migration

**Option A - Supabase Dashboard**:
1. Go to Supabase SQL Editor
2. Copy contents of `DAILY_CHECKIN_SQL_ADDITIONS.sql`
3. Run the script

**Option B - Command Line**:
```bash
psql -U postgres -d your_database -f DAILY_CHECKIN_SQL_ADDITIONS.sql
```

### Step 2: Verify Schema Changes

Run this query to verify all columns exist:

```sql
-- Verify task_checkins columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'task_checkins'
AND column_name IN ('continue_preference', 'enjoyed', 'timing_feedback');

-- Verify daily_journals columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'daily_journals'
AND column_name IN ('checkin_completed', 'checkin_reminder_sent');

-- Verify plan_items column
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'plan_items'
AND column_name = 'plan_date';

-- Verify functions exist
SELECT proname, pg_get_function_identity_arguments(oid)
FROM pg_proc
WHERE proname IN ('get_tasks_needing_checkin', 'can_regenerate_plan');

-- Verify view exists
SELECT table_name, view_definition
FROM information_schema.views
WHERE table_name = 'daily_checkin_status';
```

**Expected Output**:
- 3 columns in task_checkins
- 3 columns in daily_journals
- 1 column in plan_items (or already exists)
- 2 functions
- 1 view

---

## 🎯 How Your Check-in Flow Will Work

### Flow 1: User Completes Task Throughout Day

**Existing API** (no changes needed):
```
POST /api/v1/engagement/task-checkin
{
  "profile_id": "user123",
  "plan_item_id": "task-uuid",
  "completion_status": "completed",
  "satisfaction_rating": 5
}
```

### Flow 2: User Gets 6 PM Notification

**Backend** (you'll implement):
- Cron job or scheduled function at 6 PM
- Check if user has completed tasks today
- If yes, send push notification: "Check in on your day"

### Flow 3: User Opens Check-in Screen

**Frontend Query** (use new function):
```sql
SELECT * FROM get_tasks_needing_checkin('user123', '2025-10-31');
```

Returns all tasks user completed today that need feedback.

### Flow 4: User Answers Check-in Questions

**New API Call** (minor modification to existing endpoint):
```
POST /api/v1/engagement/task-checkin
{
  "profile_id": "user123",
  "plan_item_id": "task-uuid",
  "completion_status": "completed",
  "satisfaction_rating": 5,
  "continue_preference": "yes",     // NEW
  "enjoyed": true,                  // NEW
  "timing_feedback": "perfect"      // NEW
}
```

### Flow 5: User Submits Daily Journal

**Existing API** (just add one field):
```
POST /api/v1/engagement/journal
{
  "profile_id": "user123",
  "journal_date": "2025-10-31",
  "energy_level": 4,
  "mood_rating": 5,
  "what_went_well": "Great productivity",
  "checkin_completed": true          // NEW
}
```

### Flow 6: Next Day Plan Generation

**Your Manual Trigger**:
```
POST /api/v1/plan/generate-manual
{
  "user_id": "user123",
  "date": "2025-11-01"
}
```

**Backend Fetches Check-in Data**:
```sql
-- Get yesterday's check-in feedback
SELECT
    tc.plan_item_id,
    pi.title,
    pi.task_type,
    pi.category,
    tc.continue_preference,
    tc.enjoyed,
    tc.timing_feedback,
    tc.satisfaction_rating
FROM task_checkins tc
JOIN plan_items pi ON pi.id = tc.plan_item_id
WHERE tc.profile_id = 'user123'
AND tc.planned_date = '2025-10-31'  -- Yesterday
AND tc.continue_preference IS NOT NULL;
```

**TaskPreseeder Uses This Data**:
- Tasks with `continue_preference = 'yes'` → Boost score 20%
- Tasks with `continue_preference = 'no'` → Exclude
- Tasks with `enjoyed = true` → Boost score 10%
- Tasks with `timing_feedback = 'late'` → Schedule later
- Tasks with `timing_feedback = 'early'` → Schedule earlier

### Flow 7: User Missed Check-in (Regenerate)

**Check if Regeneration Available**:
```sql
SELECT can_regenerate_plan('user123', '2025-10-31');
```

If returns `true`, show "Regenerate Plan" button.

**When User Clicks Regenerate**:
1. Show same check-in screen
2. Submit late check-in responses
3. Immediately trigger plan regeneration
4. Show updated plan

---

## 🚀 Next Steps for Full Day 2+ Flow

You mentioned wanting **full behavior + circadian analysis from Day 2** with **key insights displayed as bullet points** on UI.

### What This Means for Backend

#### On Plan Generation (Day 2+):

1. **Run Behavior Analysis**:
   ```
   POST /api/user/{user_id}/behavior/analyze
   ```
   - Analyzes task completion patterns
   - Identifies optimal times for categories
   - Detects energy patterns

2. **Run Circadian Analysis** (if available):
   - Uses sleep data, activity patterns
   - Personalizes time blocks

3. **Generate Plan with Full Context**:
   ```python
   routine_result = await run_routine_planning_4o(
       system_prompt=...,
       user_context=...,
       behavior_analysis=behavior_data,    # NEW
       circadian_analysis=circadian_data,  # NEW
       archetype=archetype,
       preselected_tasks=preselected_tasks
   )
   ```

4. **Extract Key Insights as Bullet Points**:

   Add this to your plan generation flow:
   ```python
   insights = {
       "key_patterns": [
           "You complete movement tasks best between 7-9 AM",
           "Afternoon energy dips around 2-3 PM - lighter tasks scheduled",
           "Hydration tasks consistently skipped - reduced frequency"
       ],
       "optimizations": [
           "Moved meditation to evening based on completion patterns",
           "Added buffer time before meetings based on stress data"
       ],
       "recommendations": [
           "Consider earlier bedtime - sleep quality below target",
           "Strong adherence to morning routine - continuing structure"
       ]
   }
   ```

5. **Save Insights to `holistic_analysis_results`**:
   ```json
   {
       "analysis_type": "routine_plan",
       "analysis_result": {
           /* full plan */
       },
       "insights_summary": {
           "key_patterns": [...],
           "optimizations": [...],
           "recommendations": [...]
       }
   }
   ```

#### UI Display

On Planner screen, show:

```
📊 Today's Plan Insights

Key Patterns:
• You complete movement tasks best between 7-9 AM
• Afternoon energy dips around 2-3 PM

Optimizations:
• Moved meditation to evening based on your feedback
• Added buffer time before meetings

Recommendations:
• Consider earlier bedtime - sleep quality below target
```

---

## Summary: What You Need to Do

### Immediate (This Week):

✅ **Run SQL Migration**:
```bash
# Run DAILY_CHECKIN_SQL_ADDITIONS.sql
```

✅ **Verify Schema**:
```sql
# Run verification queries above
```

✅ **Test Existing APIs**:
```bash
# Test task check-in API with new fields
# Test journal API with checkin_completed field
```

### Soon (Next Week):

🔧 **Modify TaskPreseeder**:
- Add logic to use check-in feedback for scoring

🔧 **Add Manual Generation Endpoint**:
- Create endpoint to trigger plan generation

🔧 **Add Notification Service**:
- Schedule 6 PM check-in reminders

🔧 **Build Flutter Check-in Screen**:
- Use existing APIs + new fields

### Later (For Day 2+ Full Analysis):

🔬 **Add Insights Extraction**:
- After behavior + circadian analysis
- Extract bullet point insights from analysis
- Save to database
- Display in UI

---

## Files Reference

**SQL Migration**:
- `DAILY_CHECKIN_SQL_ADDITIONS.sql` ← Run this first!

**Existing Schema**:
- `supabase/user-engagement/001_create_dual_engagement_system.sql`

**Existing APIs**:
- `services/api_gateway/engagement_endpoints.py`

**Documentation**:
- `documentation/02-implementation/features/CALENDAR_CHECKIN_IMPLEMENTATION_GUIDE.md`

---

**Your system is 90% ready! Just need the SQL additions and minor API tweaks.** 🎉
