-- ============================================================================
-- FIX: Archetype Analysis Tracking Table
-- Run this in Supabase SQL Editor to fix the missing schema
-- ============================================================================

-- Step 1: Create table if it doesn't exist (with all required columns)
CREATE TABLE IF NOT EXISTS archetype_analysis_tracking (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    archetype TEXT NOT NULL,
    analysis_type TEXT NOT NULL DEFAULT 'behavior_analysis',
    last_analysis_at TIMESTAMPTZ NOT NULL,
    analysis_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 2: Add analysis_type column if table exists but column is missing
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
        RAISE NOTICE 'Added analysis_type column';
    END IF;
END $$;

-- Step 3: Drop old constraint if exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_name = 'archetype_analysis_tracking'
        AND constraint_name = 'unique_user_archetype'
    ) THEN
        ALTER TABLE archetype_analysis_tracking DROP CONSTRAINT unique_user_archetype;
        RAISE NOTICE 'Dropped old constraint';
    END IF;
END $$;

-- Step 4: Add new unique constraint with analysis_type
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
        RAISE NOTICE 'Added new unique constraint';
    END IF;
END $$;

-- Step 5: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_archetype
ON archetype_analysis_tracking(user_id, archetype);

CREATE INDEX IF NOT EXISTS idx_archetype_tracking_last_analysis
ON archetype_analysis_tracking(user_id, last_analysis_at DESC);

CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_archetype_type
ON archetype_analysis_tracking(user_id, archetype, analysis_type);

-- Step 6: Add archetype validation constraint
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
        RAISE NOTICE 'Added archetype validation';
    END IF;
END $$;

-- Step 7: Enable Row Level Security
ALTER TABLE archetype_analysis_tracking ENABLE ROW LEVEL SECURITY;

-- Step 8: Drop existing policies if they exist
DROP POLICY IF EXISTS archetype_tracking_service_full_access ON public.archetype_analysis_tracking;
DROP POLICY IF EXISTS archetype_tracking_anon_access ON public.archetype_analysis_tracking;
DROP POLICY IF EXISTS archetype_tracking_user_access ON public.archetype_analysis_tracking;

-- Step 9: Create RLS policies
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

-- Step 10: Grant permissions
GRANT ALL ON public.archetype_analysis_tracking TO service_role;
GRANT ALL ON public.archetype_analysis_tracking TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.archetype_analysis_tracking TO authenticated;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE archetype_analysis_tracking_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE archetype_analysis_tracking_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE archetype_analysis_tracking_id_seq TO authenticated;

-- Step 11: Verify schema
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
ORDER BY ordinal_position;

-- Step 12: Show current data
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
-- DONE! Your archetype_analysis_tracking table is now properly configured.
-- ============================================================================
