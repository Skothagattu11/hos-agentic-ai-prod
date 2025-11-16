-- =========================================================================
-- Add Manual Plan Support to Database Schema
-- =========================================================================
--
-- This migration adds 'manual' to the allowed analysis_type values
-- in the holistic_analysis_results table to support manual plan creation.
--
-- Run this in your Supabase database BEFORE testing manual plan creation.
-- =========================================================================

-- Add 'manual' to the CHECK constraint for analysis_type
ALTER TABLE holistic_analysis_results
DROP CONSTRAINT IF EXISTS holistic_analysis_results_analysis_type_check;

ALTER TABLE holistic_analysis_results
ADD CONSTRAINT holistic_analysis_results_analysis_type_check
CHECK (analysis_type IN (
    'behavior_analysis',
    'nutrition_plan',
    'routine_plan',
    'complete_analysis',
    'circadian_analysis',
    'manual'  -- NEW: Support for manual plan creation
));

-- Add index for manual analysis queries (optional performance optimization)
CREATE INDEX IF NOT EXISTS idx_analysis_results_manual
ON holistic_analysis_results(user_id, analysis_type)
WHERE analysis_type = 'manual';

-- Verify the change
DO $$
BEGIN
    RAISE NOTICE 'Manual Plan Database Support Added Successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes made:';
    RAISE NOTICE '  ✅ Added ''manual'' to analysis_type constraint';
    RAISE NOTICE '  ✅ Added performance index for manual plan queries';
    RAISE NOTICE '';
    RAISE NOTICE 'The holistic_analysis_results table now supports:';
    RAISE NOTICE '  • behavior_analysis';
    RAISE NOTICE '  • nutrition_plan';
    RAISE NOTICE '  • routine_plan';
    RAISE NOTICE '  • complete_analysis';
    RAISE NOTICE '  • circadian_analysis';
    RAISE NOTICE '  • manual (NEW)';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Manual plan creation is now ready to use!';
END $$;
