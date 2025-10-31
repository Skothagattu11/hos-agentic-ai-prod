-- ============================================================================
-- FIX: Archetype Analysis Tracking Table - Add Missing Columns
-- Run this in Supabase SQL Editor to fix the schema
-- Version 2: Adds missing columns to existing table
-- ============================================================================

-- Step 1: Show current schema
SELECT 'Current table schema:' as status;
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
ORDER BY ordinal_position;

-- Step 2: Add last_analysis_at column if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'archetype_analysis_tracking'
        AND column_name = 'last_analysis_at'
    ) THEN
        -- Add the column as nullable first
        ALTER TABLE archetype_analysis_tracking
        ADD COLUMN last_analysis_at TIMESTAMPTZ;

        -- Set a default value for existing rows (use created_at or NOW())
        UPDATE archetype_analysis_tracking
        SET last_analysis_at = COALESCE(created_at, NOW())
        WHERE last_analysis_at IS NULL;

        -- Make it NOT NULL now that all rows have values
        ALTER TABLE archetype_analysis_tracking
        ALTER COLUMN last_analysis_at SET NOT NULL;

        RAISE NOTICE '✅ Added last_analysis_at column';
    ELSE
        RAISE NOTICE '✓ last_analysis_at column already exists';
    END IF;
END $$;

-- Step 3: Add analysis_type column if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'archetype_analysis_tracking'
        AND column_name = 'analysis_type'
    ) THEN
        ALTER TABLE archetype_analysis_tracking ADD COLUMN analysis_type TEXT;
        UPDATE archetype_analysis_tracking SET analysis_type = 'behavior_analysis' WHERE analysis_type IS NULL;
        ALTER TABLE archetype_analysis_tracking ALTER COLUMN analysis_type SET NOT NULL;
        RAISE NOTICE '✅ Added analysis_type column';
    ELSE
        RAISE NOTICE '✓ analysis_type column already exists';
    END IF;
END $$;

-- Step 4: Drop old constraint if exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_name = 'archetype_analysis_tracking'
        AND constraint_name = 'unique_user_archetype'
    ) THEN
        ALTER TABLE archetype_analysis_tracking DROP CONSTRAINT unique_user_archetype;
        RAISE NOTICE '✅ Dropped old constraint';
    ELSE
        RAISE NOTICE '✓ Old constraint does not exist';
    END IF;
END $$;

-- Step 5: Add new unique constraint with analysis_type
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_name = 'archetype_analysis_tracking'
        AND constraint_name = 'archetype_analysis_tracking_user_archetype_type_key'
    ) THEN
        ALTER TABLE archetype_analysis_tracking
        ADD CONSTRAINT archetype_analysis_tracking_user_archetype_type_key
        UNIQUE (user_id, archetype, analysis_type);
        RAISE NOTICE '✅ Added new unique constraint';
    ELSE
        RAISE NOTICE '✓ Unique constraint already exists';
    END IF;
END $$;

-- Step 6: Create indexes for performance (now that columns exist)
CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_archetype
ON archetype_analysis_tracking(user_id, archetype);

CREATE INDEX IF NOT EXISTS idx_archetype_tracking_last_analysis
ON archetype_analysis_tracking(user_id, last_analysis_at DESC);

CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_archetype_type
ON archetype_analysis_tracking(user_id, archetype, analysis_type);

SELECT '✅ Created indexes' as status;

-- Step 7: Add archetype validation constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_name = 'archetype_analysis_tracking'
        AND constraint_name = 'valid_archetype'
    ) THEN
        ALTER TABLE archetype_analysis_tracking
        ADD CONSTRAINT valid_archetype CHECK (
            archetype IN (
                'Foundation Builder',
                'Peak Performer',
                'Systematic Improver',
                'Transformation Seeker',
                'Resilience Rebuilder',
                'Connected Explorer'
            )
        );
        RAISE NOTICE '✅ Added archetype validation';
    ELSE
        RAISE NOTICE '✓ Archetype validation already exists';
    END IF;
END $$;

-- Step 8: Enable Row Level Security
ALTER TABLE archetype_analysis_tracking ENABLE ROW LEVEL SECURITY;

-- Step 9: Drop existing policies if they exist
DROP POLICY IF EXISTS archetype_tracking_service_full_access ON public.archetype_analysis_tracking;
DROP POLICY IF EXISTS archetype_tracking_anon_access ON public.archetype_analysis_tracking;
DROP POLICY IF EXISTS archetype_tracking_user_access ON public.archetype_analysis_tracking;

-- Step 10: Create RLS policies
CREATE POLICY archetype_tracking_service_full_access ON public.archetype_analysis_tracking
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY archetype_tracking_anon_access ON public.archetype_analysis_tracking
    FOR ALL TO anon
    USING (true)
    WITH CHECK (true);

CREATE POLICY archetype_tracking_user_access ON public.archetype_analysis_tracking
    FOR ALL TO authenticated
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

SELECT '✅ RLS policies configured' as status;

-- Step 11: Grant permissions
GRANT ALL ON public.archetype_analysis_tracking TO service_role;
GRANT ALL ON public.archetype_analysis_tracking TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.archetype_analysis_tracking TO authenticated;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE archetype_analysis_tracking_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE archetype_analysis_tracking_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE archetype_analysis_tracking_id_seq TO authenticated;

SELECT '✅ Permissions granted' as status;

-- Step 12: Verify final schema
SELECT '📋 Final schema:' as status;
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
ORDER BY ordinal_position;

-- Step 13: Show current data
SELECT '📊 Current data (top 10 rows):' as status;
SELECT
    user_id,
    archetype,
    analysis_type,
    last_analysis_at,
    analysis_count,
    created_at
FROM archetype_analysis_tracking
ORDER BY last_analysis_at DESC
LIMIT 10;

-- ============================================================================
-- ✅ DONE! Your archetype_analysis_tracking table is now properly configured.
-- ============================================================================
