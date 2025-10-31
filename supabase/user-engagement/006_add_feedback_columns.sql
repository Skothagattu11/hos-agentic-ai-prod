-- =====================================================
-- Add Feedback Columns to task_checkins Table
-- =====================================================
-- Purpose: Add columns required for friction-reduction feedback system
-- Author: HolisticOS Team
-- Date: 2025-10-31
--
-- These columns enable the FeedbackService to analyze user preferences
-- and adapt plans using Atomic Habits principles.

-- Add continue_preference column
ALTER TABLE task_checkins
ADD COLUMN IF NOT EXISTS continue_preference VARCHAR(10)
CHECK (continue_preference IN ('yes', 'no', 'maybe'));

-- Add enjoyed column
ALTER TABLE task_checkins
ADD COLUMN IF NOT EXISTS enjoyed BOOLEAN;

-- Add timing_feedback column
ALTER TABLE task_checkins
ADD COLUMN IF NOT EXISTS timing_feedback VARCHAR(10)
CHECK (timing_feedback IN ('early', 'perfect', 'late'));

-- Add composite index for feedback queries
CREATE INDEX IF NOT EXISTS idx_task_checkins_feedback
ON task_checkins (profile_id, planned_date DESC)
WHERE continue_preference IS NOT NULL;

-- Add comment
COMMENT ON COLUMN task_checkins.continue_preference IS
'User preference to continue this task (yes/no/maybe) - used for friction analysis';

COMMENT ON COLUMN task_checkins.enjoyed IS
'Whether user enjoyed the task - used for friction analysis';

COMMENT ON COLUMN task_checkins.timing_feedback IS
'User feedback on task timing (early/perfect/late) - used for schedule adjustment';

-- Verify columns were added
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'task_checkins'
AND column_name IN ('continue_preference', 'enjoyed', 'timing_feedback')
ORDER BY column_name;
