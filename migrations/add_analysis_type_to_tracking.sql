-- Migration: Add analysis_type column to archetype_analysis_tracking
-- Purpose: Track behavior_analysis and circadian_analysis separately
-- Date: 2025-10-02

-- Step 1: Add analysis_type column (nullable for now)
ALTER TABLE archetype_analysis_tracking
ADD COLUMN IF NOT EXISTS analysis_type TEXT;

-- Step 2: Set default value for existing rows (assume behavior_analysis)
UPDATE archetype_analysis_tracking
SET analysis_type = 'behavior_analysis'
WHERE analysis_type IS NULL;

-- Step 3: Make column NOT NULL now that all rows have values
ALTER TABLE archetype_analysis_tracking
ALTER COLUMN analysis_type SET NOT NULL;

-- Step 4: Update the unique constraint to include analysis_type
-- Drop old constraint
ALTER TABLE archetype_analysis_tracking
DROP CONSTRAINT IF EXISTS archetype_analysis_tracking_user_id_archetype_key;

-- Add new constraint with analysis_type
ALTER TABLE archetype_analysis_tracking
ADD CONSTRAINT archetype_analysis_tracking_user_archetype_type_key
UNIQUE (user_id, archetype, analysis_type);

-- Step 5: Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_archetype_type
ON archetype_analysis_tracking(user_id, archetype, analysis_type);

-- Verify the schema
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
ORDER BY ordinal_position;

-- Show sample data
SELECT user_id, archetype, analysis_type, last_analysis_at, analysis_count
FROM archetype_analysis_tracking
ORDER BY last_analysis_at DESC
LIMIT 5;
