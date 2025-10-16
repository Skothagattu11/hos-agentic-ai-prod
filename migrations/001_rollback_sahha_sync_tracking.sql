-- Rollback: Remove Sahha sync tracking columns from archetype_analysis_tracking
-- Purpose: Rollback migration 001_add_sahha_sync_tracking.sql if needed
-- Date: 2025-10-16

-- ============================================
-- STEP 1: Remove unique constraints from scores
-- ============================================

ALTER TABLE scores
DROP CONSTRAINT IF EXISTS unique_score_entry;

-- ============================================
-- STEP 2: Remove unique constraints from biomarkers
-- ============================================

ALTER TABLE biomarkers
DROP CONSTRAINT IF EXISTS unique_biomarker_entry;

-- ============================================
-- STEP 3: Drop indexes
-- ============================================

DROP INDEX IF EXISTS idx_archetype_tracking_sync_status;
DROP INDEX IF EXISTS idx_archetype_tracking_sync_errors;

-- ============================================
-- STEP 4: Rename analysis_timestamp back to last_analysis_at
-- ============================================

ALTER TABLE archetype_analysis_tracking
RENAME COLUMN analysis_timestamp TO last_analysis_at;

-- ============================================
-- STEP 5: Remove sync tracking columns
-- ============================================

ALTER TABLE archetype_analysis_tracking
DROP COLUMN IF EXISTS sahha_data_synced,
DROP COLUMN IF EXISTS biomarkers_synced,
DROP COLUMN IF EXISTS scores_synced,
DROP COLUMN IF EXISTS archetypes_synced,
DROP COLUMN IF EXISTS sync_completed_at,
DROP COLUMN IF EXISTS sync_error;

-- ============================================
-- VERIFICATION
-- ============================================

SELECT 'Rollback 001_rollback_sahha_sync_tracking.sql completed successfully!' AS status;

-- Verify columns removed
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
ORDER BY ordinal_position;
