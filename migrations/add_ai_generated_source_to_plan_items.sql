-- =========================================================================
-- Add AI-Generated Source Support to plan_items Table
-- =========================================================================
--
-- This migration adds 'routine_plan' and 'nutrition_plan' to the allowed
-- source values in the plan_items table to support AI-generated plans.
--
-- Run this in your Supabase database
-- =========================================================================

-- First, check what source values currently exist in the table
DO $$
DECLARE
    source_values TEXT;
BEGIN
    SELECT string_agg(DISTINCT "source", ', ' ORDER BY "source")
    INTO source_values
    FROM plan_items
    WHERE "source" IS NOT NULL;

    RAISE NOTICE 'Current source values in plan_items table: %', COALESCE(source_values, 'NULL');
END $$;

-- Now update the CHECK constraint for source column
ALTER TABLE plan_items
DROP CONSTRAINT IF EXISTS plan_items_source_check;

ALTER TABLE plan_items
ADD CONSTRAINT plan_items_source_check
CHECK (source IN (
    'library',
    'historical_analysis',
    'markdown_regeneration',
    'manual',
    'ai',               -- Backward compatible: Generic AI-generated tasks
    'routine_plan',     -- NEW: Specific AI-generated routine plans
    'nutrition_plan'    -- NEW: Specific AI-generated nutrition plans
));

-- Verify the change
DO $$
BEGIN
    RAISE NOTICE 'AI-Generated Source Support Added to plan_items!';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes made:';
    RAISE NOTICE '  ✅ Added ''ai'', ''routine_plan'', and ''nutrition_plan'' to source constraint';
    RAISE NOTICE '';
    RAISE NOTICE 'The plan_items table now supports:';
    RAISE NOTICE '  • library';
    RAISE NOTICE '  • historical_analysis';
    RAISE NOTICE '  • markdown_regeneration';
    RAISE NOTICE '  • manual';
    RAISE NOTICE '  • ai (backward compatible)';
    RAISE NOTICE '  • routine_plan (NEW)';
    RAISE NOTICE '  • nutrition_plan (NEW)';
    RAISE NOTICE '';
    RAISE NOTICE '✅ AI-generated plans can now be stored with proper source tracking!';
END $$;
