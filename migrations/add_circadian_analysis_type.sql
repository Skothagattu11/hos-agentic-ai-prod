-- =========================================================================
-- Add Circadian Analysis Support to Database Schema
-- =========================================================================
--
-- This migration adds 'circadian_analysis' to the allowed analysis_type values
-- in the holistic_analysis_results table to support the new circadian rhythm
-- analysis agent.
--
-- Run this in your Supabase database BEFORE testing circadian analysis.
-- =========================================================================

-- Add circadian_analysis to the CHECK constraint for analysis_type
ALTER TABLE holistic_analysis_results
DROP CONSTRAINT IF EXISTS holistic_analysis_results_analysis_type_check;

ALTER TABLE holistic_analysis_results
ADD CONSTRAINT holistic_analysis_results_analysis_type_check
CHECK (analysis_type IN (
    'behavior_analysis',
    'nutrition_plan',
    'routine_plan',
    'complete_analysis',
    'circadian_analysis'  -- NEW: Support for circadian rhythm analysis
));

-- Add index for circadian analysis queries (optional performance optimization)
CREATE INDEX IF NOT EXISTS idx_analysis_results_circadian
ON holistic_analysis_results(user_id, analysis_type)
WHERE analysis_type = 'circadian_analysis';

-- Verify the change
DO $$
BEGIN
    RAISE NOTICE 'Circadian Analysis Database Support Added Successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes made:';
    RAISE NOTICE '  ✅ Added ''circadian_analysis'' to analysis_type constraint';
    RAISE NOTICE '  ✅ Added performance index for circadian queries';
    RAISE NOTICE '';
    RAISE NOTICE 'The holistic_analysis_results table now supports:';
    RAISE NOTICE '  • behavior_analysis';
    RAISE NOTICE '  • nutrition_plan';
    RAISE NOTICE '  • routine_plan';
    RAISE NOTICE '  • complete_analysis';
    RAISE NOTICE '  • circadian_analysis (NEW)';
    RAISE NOTICE '';
    RAISE NOTICE '🕐 Your circadian rhythm agent is now ready to use!';
END $$;

-- Optional: Test the constraint works
-- INSERT INTO holistic_analysis_results (
--     user_id,
--     analysis_type,
--     analysis_result,
--     input_summary,
--     agent_id
-- ) VALUES (
--     'test_user',
--     'circadian_analysis',
--     '{"test": "data"}',
--     '{"test": "input"}',
--     'circadian_energy_agent'
-- );
--
-- -- Clean up test data
-- DELETE FROM holistic_analysis_results WHERE user_id = 'test_user';