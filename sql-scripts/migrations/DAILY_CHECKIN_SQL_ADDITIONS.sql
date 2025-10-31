-- =====================================================
-- Daily Check-in System - SQL Additions
-- =====================================================
-- This script adds minimal fields to support the daily check-in flow
-- Leverages existing task_checkins and daily_journals tables

-- =====================================================
-- 1. Add check-in preference fields to task_checkins
-- =====================================================
-- These fields capture the "Continue tomorrow?" and "Did you enjoy this?" questions

ALTER TABLE task_checkins
ADD COLUMN IF NOT EXISTS continue_preference VARCHAR(10) CHECK (continue_preference IN ('yes', 'no', 'maybe')),
ADD COLUMN IF NOT EXISTS enjoyed BOOLEAN,
ADD COLUMN IF NOT EXISTS timing_feedback VARCHAR(10) CHECK (timing_feedback IN ('perfect', 'early', 'late'));

COMMENT ON COLUMN task_checkins.continue_preference IS 'User preference for including this task tomorrow (yes/no/maybe)';
COMMENT ON COLUMN task_checkins.enjoyed IS 'Whether user enjoyed this task (true/false)';
COMMENT ON COLUMN task_checkins.timing_feedback IS 'How the timing worked for the user (perfect/early/late)';

-- =====================================================
-- 2. Add check-in completion tracking to daily_journals
-- =====================================================
-- Track when user completed their end-of-day check-in

ALTER TABLE daily_journals
ADD COLUMN IF NOT EXISTS checkin_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS checkin_reminder_sent BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS checkin_reminder_sent_at TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN daily_journals.checkin_completed IS 'Whether user completed end-of-day check-in';
COMMENT ON COLUMN daily_journals.checkin_reminder_sent IS 'Whether 6PM reminder was sent';
COMMENT ON COLUMN daily_journals.checkin_reminder_sent_at IS 'When the reminder was sent';

-- =====================================================
-- 3. Add plan_date to plan_items (if not already exists)
-- =====================================================
-- This helps query tasks for a specific date's check-in

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plan_items' AND column_name = 'plan_date'
    ) THEN
        ALTER TABLE plan_items ADD COLUMN plan_date DATE;

        -- Backfill plan_date from extracted_at for existing records
        UPDATE plan_items
        SET plan_date = DATE(extracted_at)
        WHERE plan_date IS NULL;

        COMMENT ON COLUMN plan_items.plan_date IS 'The date this plan is for (not extraction date)';
    END IF;
END $$;

-- Create index for fast date-based queries
CREATE INDEX IF NOT EXISTS idx_plan_items_date
    ON plan_items (profile_id, plan_date DESC);

-- =====================================================
-- 4. Create view for daily check-in status
-- =====================================================
-- Useful view to quickly check if user has completed check-in for a date

CREATE OR REPLACE VIEW daily_checkin_status AS
SELECT
    dj.profile_id,
    dj.journal_date,
    dj.checkin_completed,
    dj.completed_at as journal_completed_at,
    COUNT(tc.id) as total_tasks_checked_in,
    COUNT(CASE WHEN tc.completion_status = 'completed' THEN 1 END) as tasks_completed,
    COUNT(CASE WHEN tc.continue_preference = 'yes' THEN 1 END) as tasks_to_continue,
    COUNT(CASE WHEN tc.continue_preference = 'no' THEN 1 END) as tasks_to_exclude,
    COUNT(CASE WHEN tc.enjoyed = true THEN 1 END) as tasks_enjoyed
FROM daily_journals dj
LEFT JOIN task_checkins tc ON
    tc.profile_id = dj.profile_id
    AND tc.planned_date = dj.journal_date
GROUP BY dj.profile_id, dj.journal_date, dj.checkin_completed, dj.completed_at;

COMMENT ON VIEW daily_checkin_status IS 'Summary of daily check-in completion status and task preferences';

-- =====================================================
-- 5. Add function to get tasks needing check-in feedback
-- =====================================================
-- Returns tasks that were completed but haven't received check-in feedback

CREATE OR REPLACE FUNCTION get_tasks_needing_checkin(
    p_profile_id TEXT,
    p_date DATE
)
RETURNS TABLE (
    plan_item_id UUID,
    title TEXT,
    description TEXT,
    scheduled_time TIME,
    completion_status VARCHAR(20),
    completed_at TIMESTAMP WITH TIME ZONE,
    has_feedback BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pi.id as plan_item_id,
        pi.title,
        pi.description,
        pi.scheduled_time,
        tc.completion_status,
        tc.completed_at,
        (tc.continue_preference IS NOT NULL OR tc.enjoyed IS NOT NULL) as has_feedback
    FROM plan_items pi
    LEFT JOIN task_checkins tc ON
        tc.plan_item_id = pi.id
        AND tc.planned_date = p_date
    WHERE
        pi.profile_id = p_profile_id
        AND pi.plan_date = p_date
        AND pi.is_trackable = true
        AND (tc.completion_status IN ('completed', 'partial') OR tc.completion_status IS NULL)
    ORDER BY pi.time_block_order, pi.task_order_in_block;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_tasks_needing_checkin IS 'Returns tasks for a date that need check-in feedback';

-- =====================================================
-- 6. Add function to check if regeneration is available
-- =====================================================
-- Determines if user can regenerate plan (missed check-in)

CREATE OR REPLACE FUNCTION can_regenerate_plan(
    p_profile_id TEXT,
    p_date DATE
)
RETURNS BOOLEAN AS $$
DECLARE
    v_journal_exists BOOLEAN;
    v_checkin_completed BOOLEAN;
BEGIN
    -- Check if journal exists for the date
    SELECT
        CASE WHEN dj.id IS NOT NULL THEN true ELSE false END,
        COALESCE(dj.checkin_completed, false)
    INTO v_journal_exists, v_checkin_completed
    FROM daily_journals dj
    WHERE dj.profile_id = p_profile_id
    AND dj.journal_date = p_date;

    -- Can regenerate if: no journal OR journal exists but check-in not completed
    RETURN (NOT v_journal_exists) OR (v_journal_exists AND NOT v_checkin_completed);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION can_regenerate_plan IS 'Returns true if user can regenerate plan for a date (missed check-in)';

-- =====================================================
-- 7. Create indexes for performance
-- =====================================================

-- Index for checking feedback completion
CREATE INDEX IF NOT EXISTS idx_task_checkins_feedback
    ON task_checkins (profile_id, planned_date, continue_preference)
    WHERE continue_preference IS NOT NULL;

-- Index for journal check-in status
CREATE INDEX IF NOT EXISTS idx_daily_journals_checkin
    ON daily_journals (profile_id, journal_date, checkin_completed);

-- =====================================================
-- 8. Grant necessary permissions
-- =====================================================

-- Grant execute permissions on functions to authenticated users
GRANT EXECUTE ON FUNCTION get_tasks_needing_checkin TO authenticated;
GRANT EXECUTE ON FUNCTION can_regenerate_plan TO authenticated;

-- Grant select on view
GRANT SELECT ON daily_checkin_status TO authenticated;

-- =====================================================
-- DONE! Schema ready for daily check-in system
-- =====================================================

-- To run this migration:
-- 1. psql -U postgres -d your_database -f DAILY_CHECKIN_SQL_ADDITIONS.sql
-- OR
-- 2. Copy/paste into Supabase SQL Editor and run
