-- Migration: Add Sahha sync tracking columns to archetype_analysis_tracking
-- Purpose: Track Sahha data archival status per analysis (incremental sync implementation)
-- Date: 2025-10-16
-- Phase: Direct Sahha Integration - Phase 1
-- Version: 2 (with duplicate cleanup)

-- ============================================
-- STEP 1: Add sync tracking columns
-- ============================================

-- Add columns to track Sahha data sync status
-- All default to false so existing analyses don't appear as synced
ALTER TABLE archetype_analysis_tracking
ADD COLUMN IF NOT EXISTS sahha_data_synced BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS biomarkers_synced BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS scores_synced BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS archetypes_synced BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS sync_completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS sync_error TEXT;

-- Add helpful comments
COMMENT ON COLUMN archetype_analysis_tracking.sahha_data_synced IS
'Tracks if Sahha data has been successfully archived to Supabase for this analysis';

COMMENT ON COLUMN archetype_analysis_tracking.biomarkers_synced IS
'Tracks if biomarkers specifically have been synced to Supabase';

COMMENT ON COLUMN archetype_analysis_tracking.scores_synced IS
'Tracks if scores specifically have been synced to Supabase';

COMMENT ON COLUMN archetype_analysis_tracking.archetypes_synced IS
'Tracks if archetypes data has been synced to Supabase';

COMMENT ON COLUMN archetype_analysis_tracking.sync_completed_at IS
'Timestamp when background archival job completed successfully';

COMMENT ON COLUMN archetype_analysis_tracking.sync_error IS
'Error message if sync failed (for debugging and retry logic)';

-- ============================================
-- STEP 2: Rename last_analysis_at to analysis_timestamp (watermark)
-- ============================================

-- Check if column exists with old name before renaming
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'archetype_analysis_tracking'
        AND column_name = 'last_analysis_at'
    ) THEN
        ALTER TABLE archetype_analysis_tracking
        RENAME COLUMN last_analysis_at TO analysis_timestamp;

        RAISE NOTICE 'Renamed last_analysis_at to analysis_timestamp';
    ELSE
        RAISE NOTICE 'Column last_analysis_at does not exist (already renamed or different schema)';
    END IF;
END $$;

-- Update comment to reflect watermark usage
COMMENT ON COLUMN archetype_analysis_tracking.analysis_timestamp IS
'Timestamp of analysis - ALSO serves as watermark for incremental Sahha data fetching';

-- ============================================
-- STEP 3: Clean up duplicate biomarkers BEFORE adding constraint
-- ============================================

-- Find and log duplicate biomarkers
DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT profile_id, type, start_date_time, end_date_time, COUNT(*) as cnt
        FROM biomarkers
        GROUP BY profile_id, type, start_date_time, end_date_time
        HAVING COUNT(*) > 1
    ) duplicates;

    RAISE NOTICE 'Found % duplicate biomarker groups', duplicate_count;
END $$;

-- Keep the most recent biomarker entry, delete older duplicates
-- This preserves data while removing duplicates
DELETE FROM biomarkers
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY profile_id, type, start_date_time, end_date_time
                   ORDER BY created_at DESC, id DESC
               ) as rn
        FROM biomarkers
    ) ranked
    WHERE rn > 1
);

-- Log how many duplicates were removed
DO $$
DECLARE
    deleted_count INTEGER;
BEGIN
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % duplicate biomarker entries', deleted_count;
END $$;

-- Now add the unique constraint (safe now)
ALTER TABLE biomarkers
DROP CONSTRAINT IF EXISTS unique_biomarker_entry;

ALTER TABLE biomarkers
ADD CONSTRAINT unique_biomarker_entry
UNIQUE (profile_id, type, start_date_time, end_date_time);

COMMENT ON CONSTRAINT unique_biomarker_entry ON biomarkers IS
'Prevents duplicate biomarker entries - enables safe UPSERT during incremental sync';

-- ============================================
-- STEP 4: Clean up duplicate scores BEFORE adding constraint
-- ============================================

-- Find and log duplicate scores
DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT profile_id, type, score_date_time, COUNT(*) as cnt
        FROM scores
        GROUP BY profile_id, type, score_date_time
        HAVING COUNT(*) > 1
    ) duplicates;

    RAISE NOTICE 'Found % duplicate score groups', duplicate_count;
END $$;

-- Keep the most recent score entry, delete older duplicates
DELETE FROM scores
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY profile_id, type, score_date_time
                   ORDER BY created_at DESC, id DESC
               ) as rn
        FROM scores
    ) ranked
    WHERE rn > 1
);

-- Log how many duplicates were removed
DO $$
DECLARE
    deleted_count INTEGER;
BEGIN
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % duplicate score entries', deleted_count;
END $$;

-- Now add the unique constraint (safe now)
ALTER TABLE scores
DROP CONSTRAINT IF EXISTS unique_score_entry;

ALTER TABLE scores
ADD CONSTRAINT unique_score_entry
UNIQUE (profile_id, type, score_date_time);

COMMENT ON CONSTRAINT unique_score_entry ON scores IS
'Prevents duplicate score entries - enables safe UPSERT during incremental sync';

-- ============================================
-- STEP 5: Create indexes for performance
-- ============================================

-- Index for filtering by sync status (useful for retry logic)
CREATE INDEX IF NOT EXISTS idx_archetype_tracking_sync_status
ON archetype_analysis_tracking(user_id, archetype, sahha_data_synced)
WHERE sahha_data_synced = false;

-- Index for finding failed syncs that need retry
CREATE INDEX IF NOT EXISTS idx_archetype_tracking_sync_errors
ON archetype_analysis_tracking(user_id, sync_error)
WHERE sync_error IS NOT NULL;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Verify schema changes
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
  AND column_name IN ('sahha_data_synced', 'biomarkers_synced', 'scores_synced',
                      'archetypes_synced', 'sync_completed_at', 'sync_error', 'analysis_timestamp')
ORDER BY ordinal_position;

-- Verify unique constraints on biomarkers
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'biomarkers'
  AND constraint_type = 'UNIQUE';

-- Verify unique constraints on scores
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'scores'
  AND constraint_type = 'UNIQUE';

-- Verify no duplicates remain in biomarkers
SELECT COUNT(*) as remaining_biomarker_duplicates
FROM (
    SELECT profile_id, type, start_date_time, end_date_time, COUNT(*) as cnt
    FROM biomarkers
    GROUP BY profile_id, type, start_date_time, end_date_time
    HAVING COUNT(*) > 1
) duplicates;

-- Verify no duplicates remain in scores
SELECT COUNT(*) as remaining_score_duplicates
FROM (
    SELECT profile_id, type, score_date_time, COUNT(*) as cnt
    FROM scores
    GROUP BY profile_id, type, score_date_time
    HAVING COUNT(*) > 1
) duplicates;

-- Show sample of updated schema
SELECT
    user_id,
    archetype,
    analysis_type,
    analysis_timestamp,
    sahha_data_synced,
    biomarkers_synced,
    scores_synced,
    sync_completed_at,
    sync_error
FROM archetype_analysis_tracking
ORDER BY analysis_timestamp DESC
LIMIT 5;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================

SELECT 'Migration 001_add_sahha_sync_tracking_v2.sql completed successfully!' AS status,
       'Duplicate data cleaned up and unique constraints added' AS details;
