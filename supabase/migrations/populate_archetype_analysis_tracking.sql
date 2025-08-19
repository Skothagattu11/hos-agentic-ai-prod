-- Migration: Populate archetype_analysis_tracking with existing data
-- Purpose: Migrate existing analysis data to support archetype-specific timestamps
-- Date: 2025-08-19
-- Phase: MVP Implementation - Data Migration

-- Step 1: Populate from existing holistic_analysis_results (behavior analyses only)
INSERT INTO archetype_analysis_tracking (user_id, archetype, last_analysis_at, analysis_count, created_at, updated_at)
SELECT 
    user_id,
    COALESCE(archetype, 'Foundation Builder') as archetype,  -- Default archetype if null
    MAX(created_at) as last_analysis_at,
    COUNT(*) as analysis_count,
    MIN(created_at) as created_at,
    MAX(created_at) as updated_at
FROM holistic_analysis_results 
WHERE analysis_type = 'behavior_analysis'
  AND created_at >= NOW() - INTERVAL '90 days'  -- Only migrate recent data
GROUP BY user_id, COALESCE(archetype, 'Foundation Builder')
ON CONFLICT (user_id, archetype) DO UPDATE SET
    last_analysis_at = GREATEST(
        archetype_analysis_tracking.last_analysis_at, 
        EXCLUDED.last_analysis_at
    ),
    analysis_count = archetype_analysis_tracking.analysis_count + EXCLUDED.analysis_count,
    updated_at = NOW();

-- Step 2: Validate migration results
SELECT 
    'Migration Complete' as status,
    COUNT(*) as total_tracking_records,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT archetype) as unique_archetypes,
    MIN(last_analysis_at) as earliest_analysis,
    MAX(last_analysis_at) as latest_analysis
FROM archetype_analysis_tracking;

-- Step 3: Show archetype distribution
SELECT 
    archetype,
    COUNT(*) as user_count,
    AVG(analysis_count) as avg_analyses_per_user,
    MAX(analysis_count) as max_analyses,
    MIN(last_analysis_at) as earliest,
    MAX(last_analysis_at) as latest
FROM archetype_analysis_tracking
GROUP BY archetype
ORDER BY user_count DESC;

-- Step 4: Show sample data for verification
SELECT 
    user_id,
    archetype,
    last_analysis_at,
    analysis_count,
    created_at,
    updated_at
FROM archetype_analysis_tracking
ORDER BY updated_at DESC
LIMIT 10;

-- Step 5: Verify against original data
WITH source_data AS (
    SELECT 
        user_id,
        COALESCE(archetype, 'Foundation Builder') as archetype,
        COUNT(*) as original_count,
        MAX(created_at) as original_latest
    FROM holistic_analysis_results 
    WHERE analysis_type = 'behavior_analysis'
      AND created_at >= NOW() - INTERVAL '90 days'
    GROUP BY user_id, COALESCE(archetype, 'Foundation Builder')
),
tracking_data AS (
    SELECT 
        user_id,
        archetype,
        analysis_count as tracking_count,
        last_analysis_at as tracking_latest
    FROM archetype_analysis_tracking
)
SELECT 
    'Data Integrity Check' as check_type,
    COUNT(*) as total_comparisons,
    COUNT(*) FILTER (WHERE s.original_count = t.tracking_count) as count_matches,
    COUNT(*) FILTER (WHERE s.original_latest = t.tracking_latest) as timestamp_matches,
    ROUND(
        COUNT(*) FILTER (WHERE s.original_count = t.tracking_count) * 100.0 / COUNT(*), 
        2
    ) as count_match_percentage,
    ROUND(
        COUNT(*) FILTER (WHERE s.original_latest = t.tracking_latest) * 100.0 / COUNT(*), 
        2
    ) as timestamp_match_percentage
FROM source_data s
JOIN tracking_data t ON s.user_id = t.user_id AND s.archetype = t.archetype;

-- Final summary
SELECT 
    '✅ ARCHETYPE TRACKING MIGRATION COMPLETE' as status,
    'Check the results above to verify data integrity' as next_step;