-- =========================================================================
-- Add analysis_result_id Column to planner_goals Table
-- =========================================================================
--
-- This migration adds a column to link planner goals to their corresponding
-- holistic_analysis_results entries (plans). This is needed for manual plan
-- creation where a goal is created alongside a plan.
--
-- Run this in your Supabase database.
-- =========================================================================

-- Add analysis_result_id column to planner_goals
ALTER TABLE planner_goals
ADD COLUMN IF NOT EXISTS analysis_result_id UUID DEFAULT NULL;

-- Add comment explaining the column
COMMENT ON COLUMN planner_goals.analysis_result_id IS 'Foreign key reference to holistic_analysis_results table. Used to link a goal to its corresponding plan (especially for manual plans).';

-- Create index for queries filtering by analysis_result_id
CREATE INDEX IF NOT EXISTS idx_planner_goals_analysis_result_id
ON planner_goals(analysis_result_id);

-- Verify the change
DO $$
BEGIN
    RAISE NOTICE 'Analysis Result ID Column Added to planner_goals!';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes made:';
    RAISE NOTICE '  ✅ Added analysis_result_id column (UUID)';
    RAISE NOTICE '  ✅ Added index for query performance';
    RAISE NOTICE '';
    RAISE NOTICE 'This column links goals to their plans:';
    RAISE NOTICE '  • Manual plans: One goal per plan (1:1 relationship)';
    RAISE NOTICE '  • AI plans: Existing goals linked to generated plans';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Goals can now be linked to analysis results!';
END $$;
