-- =====================================================
-- Add SIMPLIFIED Feedback Columns to task_checkins
-- =====================================================
-- Purpose: Minimize user friction with just 2 questions per task
-- Author: HolisticOS Team
-- Date: 2025-10-31
--
-- Design Philosophy:
--   - Question 1: "How did this go?" (1-5 rating)
--   - Question 2: "Keep this task?" (yes/maybe/no)
--   - Derive friction from these 2 inputs
--   - Time per task: ~3 seconds (vs 15-20 with 5 questions)

-- Question 1: Overall experience rating (replaces: enjoyed + satisfaction_rating)
-- Combines "did you enjoy it?" and "how satisfied?" into one slider
ALTER TABLE task_checkins
ADD COLUMN IF NOT EXISTS experience_rating INTEGER
CHECK (experience_rating BETWEEN 1 AND 5);

COMMENT ON COLUMN task_checkins.experience_rating IS
'Single rating (1-5) combining enjoyment and satisfaction. 1=Hated it, 5=Loved it. Used for friction analysis.';

-- Question 2: Continuation preference (keep existing for backward compatibility)
ALTER TABLE task_checkins
ADD COLUMN IF NOT EXISTS continue_preference VARCHAR(10)
CHECK (continue_preference IN ('yes', 'no', 'maybe'));

COMMENT ON COLUMN task_checkins.continue_preference IS
'Simple 3-option choice: Keep this task tomorrow? (yes/maybe/no). Used for friction analysis.';

-- OPTIONAL: Add these only if you want timing insights (recommended to keep it simple)
-- Uncomment if you want to track timing issues
-- ALTER TABLE task_checkins
-- ADD COLUMN IF NOT EXISTS timing_issue BOOLEAN DEFAULT FALSE;
--
-- COMMENT ON COLUMN task_checkins.timing_issue IS
-- 'Optional: Flag if user reports timing was off (too early/too late). Simplified from early/perfect/late.';

-- Add index for fast feedback queries
CREATE INDEX IF NOT EXISTS idx_task_checkins_feedback_simple
ON task_checkins (profile_id, planned_date DESC, experience_rating)
WHERE experience_rating IS NOT NULL AND continue_preference IS NOT NULL;

-- Add index for friction analysis by category (requires JOIN with plan_items)
CREATE INDEX IF NOT EXISTS idx_task_checkins_profile_completed
ON task_checkins (profile_id, completion_status, planned_date DESC)
WHERE completion_status = 'completed';

-- Verify columns were added
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'task_checkins'
AND column_name IN ('experience_rating', 'continue_preference')
ORDER BY column_name;

-- Show example query for friction analysis
COMMENT ON TABLE task_checkins IS
'Tracks task completions with SIMPLIFIED 2-question feedback:
1. experience_rating (1-5): How did this go?
2. continue_preference (yes/no/maybe): Keep this task?
Friction derived from: low rating + no continuation = high friction';
