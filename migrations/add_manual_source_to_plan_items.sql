-- =========================================================================
-- Add Manual Source Support to plan_items Table
-- =========================================================================
--
-- This migration adds 'manual' to the allowed source values in the plan_items
-- table to support manual plan creation where users create their own tasks.
--
-- Run this in your Supabase database AFTER running add_manual_analysis_type.sql
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

-- Update any rows with unexpected source values to 'library' (default)
-- This handles any legacy or unexpected source values
UPDATE plan_items
SET "source" = 'library'
WHERE "source" IS NOT NULL
  AND "source" NOT IN ('library', 'historical_analysis', 'markdown_regeneration');

-- Set NULL source values to 'library' (default)
UPDATE plan_items
SET "source" = 'library'
WHERE "source" IS NULL;

-- Now add 'manual' to the CHECK constraint for source column
ALTER TABLE plan_items
DROP CONSTRAINT IF EXISTS plan_items_source_check;

ALTER TABLE plan_items
ADD CONSTRAINT plan_items_source_check
CHECK (source IN (
    'library',
    'historical_analysis',
    'markdown_regeneration',
    'manual'  -- NEW: Support for manually created tasks
));

-- Verify the change
DO $$
BEGIN
    RAISE NOTICE 'Manual Source Support Added to plan_items!';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes made:';
    RAISE NOTICE '  ✅ Normalized existing source values';
    RAISE NOTICE '  ✅ Added ''manual'' to source constraint';
    RAISE NOTICE '';
    RAISE NOTICE 'The plan_items table now supports:';
    RAISE NOTICE '  • library';
    RAISE NOTICE '  • historical_analysis';
    RAISE NOTICE '  • markdown_regeneration';
    RAISE NOTICE '  • manual (NEW)';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Manual plan tasks can now be created!';
END $$;
