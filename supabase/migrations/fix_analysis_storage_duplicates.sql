-- Migration: Fix Analysis Storage & Duplicate Issues
-- Date: 2025-08-20
-- Purpose: Allow threshold-exceeded analyses + prevent duplicates
-- Addresses: Missing behavior analysis storage when threshold exceeded

BEGIN;

-- Step 1: Add analysis_trigger column to distinguish analysis types
ALTER TABLE holistic_analysis_results 
ADD COLUMN IF NOT EXISTS analysis_trigger VARCHAR(50);

-- Step 2: Update existing records with default trigger
UPDATE holistic_analysis_results 
SET analysis_trigger = 'scheduled' 
WHERE analysis_trigger IS NULL;

-- Step 3: Make column NOT NULL with default
ALTER TABLE holistic_analysis_results 
ALTER COLUMN analysis_trigger SET NOT NULL,
ALTER COLUMN analysis_trigger SET DEFAULT 'scheduled';

-- Step 4: Drop the problematic constraint that blocks same-day analyses
ALTER TABLE holistic_analysis_results 
DROP CONSTRAINT IF EXISTS unique_analysis_per_user_type_date_archetype;

-- Step 5: Add new constraint allowing multiple analyses per day with different triggers
ALTER TABLE holistic_analysis_results 
ADD CONSTRAINT unique_analysis_per_user_type_date_archetype_trigger 
UNIQUE (user_id, analysis_type, analysis_date, archetype, analysis_trigger);

-- Step 6: Add performance indexes for fast trigger-based queries
CREATE INDEX IF NOT EXISTS idx_analysis_trigger_lookup 
ON holistic_analysis_results (user_id, archetype, analysis_trigger, created_at DESC);

-- Step 7: Add index for admin analytics and monitoring
CREATE INDEX IF NOT EXISTS idx_analysis_trigger_stats
ON holistic_analysis_results (analysis_trigger, created_at DESC);

-- Step 8: Add comment to document the change
COMMENT ON COLUMN holistic_analysis_results.analysis_trigger IS 
'Distinguishes analysis types: scheduled, threshold_exceeded, archetype_switch, manual_refresh, stale_refresh';

COMMIT;

-- Validation: Check migration success
SELECT 
    '✅ MIGRATION COMPLETED' as status,
    COUNT(*) as total_analyses,
    COUNT(DISTINCT analysis_trigger) as trigger_types,
    COUNT(*) FILTER (WHERE analysis_trigger = 'scheduled') as scheduled_count,
    COUNT(*) FILTER (WHERE analysis_trigger IS NULL) as null_triggers
FROM holistic_analysis_results;

-- Show analysis trigger distribution
SELECT 
    analysis_trigger,
    COUNT(*) as count,
    MIN(created_at) as earliest_date,
    MAX(created_at) as latest_date
FROM holistic_analysis_results
GROUP BY analysis_trigger
ORDER BY count DESC;

-- Check constraint is working (should allow multiple triggers per day)
SELECT 
    user_id,
    analysis_date,
    archetype,
    analysis_trigger,
    COUNT(*) as analyses_per_trigger
FROM holistic_analysis_results
WHERE analysis_date >= CURRENT_DATE - 7
GROUP BY user_id, analysis_date, archetype, analysis_trigger
HAVING COUNT(*) > 1
ORDER BY analysis_date DESC
LIMIT 10;

-- Final validation query for specific test user
SELECT 
    '📊 TEST USER ANALYSIS SUMMARY' as summary,
    user_id,
    COUNT(*) as total_analyses,
    COUNT(DISTINCT archetype) as archetypes_used,
    COUNT(DISTINCT analysis_trigger) as trigger_types_used,
    MAX(created_at) as latest_analysis
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
GROUP BY user_id;