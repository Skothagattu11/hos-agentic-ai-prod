-- Migration: Add archetype to unique constraint for holistic_analysis_results
-- Purpose: Ensure users can have different behavior analyses for different archetypes on the same day
-- Date: 2025-08-19

-- Step 1: Drop the existing constraint that doesn't include archetype
ALTER TABLE holistic_analysis_results 
DROP CONSTRAINT IF EXISTS unique_analysis_per_user_type_date;

-- Step 2: Create new constraint that includes archetype
-- This allows users to have different analyses for different archetypes on the same day
ALTER TABLE holistic_analysis_results 
ADD CONSTRAINT unique_analysis_per_user_type_date_archetype 
UNIQUE (user_id, analysis_type, analysis_date, archetype);

-- Step 3: Create index for faster archetype-specific queries
CREATE INDEX IF NOT EXISTS idx_analysis_results_archetype 
ON holistic_analysis_results(user_id, archetype, analysis_type, analysis_date DESC);

-- Step 4: Add comment to document the change
COMMENT ON CONSTRAINT unique_analysis_per_user_type_date_archetype ON holistic_analysis_results IS 
'Ensures unique analysis per user, type, date, and archetype combination. Allows different archetypes to have separate analyses on the same day.';