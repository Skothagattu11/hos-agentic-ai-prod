-- ============================================================================
-- QUICK FIX: Rename analysis_timestamp back to last_analysis_at
-- The code expects last_analysis_at but someone renamed it to analysis_timestamp
-- ============================================================================

-- Step 1: Check current column name
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
AND column_name IN ('analysis_timestamp', 'last_analysis_at')
ORDER BY column_name;

-- Step 2: Rename the column back
DO $$
BEGIN
    -- Check if analysis_timestamp exists
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'archetype_analysis_tracking'
        AND column_name = 'analysis_timestamp'
    ) THEN
        -- Rename it back to last_analysis_at
        ALTER TABLE archetype_analysis_tracking
        RENAME COLUMN analysis_timestamp TO last_analysis_at;

        RAISE NOTICE '✅ Renamed analysis_timestamp to last_analysis_at';
    ELSE
        RAISE NOTICE '✓ Column is already named last_analysis_at (or missing)';
    END IF;
END $$;

-- Step 3: Add the column if it doesn't exist at all
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'archetype_analysis_tracking'
        AND column_name = 'last_analysis_at'
    ) THEN
        -- Add the column
        ALTER TABLE archetype_analysis_tracking
        ADD COLUMN last_analysis_at TIMESTAMPTZ;

        -- Set a default value for existing rows
        UPDATE archetype_analysis_tracking
        SET last_analysis_at = COALESCE(created_at, NOW())
        WHERE last_analysis_at IS NULL;

        -- Make it NOT NULL
        ALTER TABLE archetype_analysis_tracking
        ALTER COLUMN last_analysis_at SET NOT NULL;

        RAISE NOTICE '✅ Added last_analysis_at column';
    END IF;
END $$;

-- Step 4: Verify the fix
SELECT '✅ Final schema:' as status;
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
ORDER BY ordinal_position;

-- ============================================================================
-- ✅ DONE! Column renamed to match code expectations
-- ============================================================================
