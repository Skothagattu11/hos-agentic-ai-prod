-- Diagnostic Queries for Threshold System Debugging
-- Run these queries to understand what's happening with your analysis tracking

-- ============================================================================
-- QUERY 1: Check archetype_analysis_tracking structure
-- ============================================================================
-- Verify the analysis_type column exists and has correct constraint
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'archetype_analysis_tracking'
ORDER BY ordinal_position;

-- Expected columns:
-- user_id, archetype, analysis_type, last_analysis_at, analysis_count, created_at, updated_at

-- ============================================================================
-- QUERY 2: Check tracking entries for your test user
-- ============================================================================
SELECT
    user_id,
    archetype,
    analysis_type,
    last_analysis_at,
    analysis_count,
    created_at,
    updated_at,
    EXTRACT(EPOCH FROM (NOW() - last_analysis_at))/60 AS minutes_since_last_analysis
FROM archetype_analysis_tracking
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
ORDER BY last_analysis_at DESC;

-- Expected: Should see separate entries for behavior_analysis and circadian_analysis

-- ============================================================================
-- QUERY 3: Check holistic_analysis_results entries
-- ============================================================================
SELECT
    id,
    user_id,
    analysis_type,
    archetype,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 AS minutes_ago
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
AND analysis_type = 'circadian_analysis'
ORDER BY created_at DESC
LIMIT 10;

-- Expected: Number of entries should match expected test runs

-- ============================================================================
-- QUERY 4: Compare tracking count vs actual analysis count
-- ============================================================================
SELECT
    tracking.archetype,
    tracking.analysis_type,
    tracking.analysis_count AS tracking_says,
    COUNT(results.id) AS actual_analyses,
    tracking.analysis_count - COUNT(results.id) AS mismatch
FROM archetype_analysis_tracking tracking
LEFT JOIN holistic_analysis_results results
    ON results.user_id = tracking.user_id
    AND results.archetype = tracking.archetype
    AND results.analysis_type = tracking.analysis_type
WHERE tracking.user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
GROUP BY tracking.archetype, tracking.analysis_type, tracking.analysis_count
ORDER BY tracking.analysis_type;

-- Expected: mismatch should be 0 (tracking_says should equal actual_analyses)

-- ============================================================================
-- QUERY 5: Check if there are duplicate entries (should be impossible)
-- ============================================================================
SELECT
    user_id,
    archetype,
    analysis_type,
    COUNT(*) as entry_count
FROM archetype_analysis_tracking
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
GROUP BY user_id, archetype, analysis_type
HAVING COUNT(*) > 1;

-- Expected: NO ROWS (unique constraint should prevent duplicates)

-- ============================================================================
-- QUERY 6: Check timing of last 5 circadian analyses
-- ============================================================================
SELECT
    created_at,
    LAG(created_at) OVER (ORDER BY created_at) AS previous_created_at,
    EXTRACT(EPOCH FROM (created_at - LAG(created_at) OVER (ORDER BY created_at)))/60 AS minutes_since_previous
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
AND analysis_type = 'circadian_analysis'
ORDER BY created_at DESC
LIMIT 5;

-- Expected: First run should show 2 analyses close together (force_refresh=true/false)
-- Second run should show only 1 analysis (force_refresh=true only, threshold should skip the false one)

-- ============================================================================
-- QUERY 7: Check unique constraint exists
-- ============================================================================
SELECT
    tc.constraint_name,
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_name = 'archetype_analysis_tracking'
AND tc.constraint_type = 'UNIQUE'
ORDER BY kcu.ordinal_position;

-- Expected: Should show constraint on (user_id, archetype, analysis_type)

-- ============================================================================
-- QUERY 8: Clear test data (OPTIONAL - use to reset for clean test)
-- ============================================================================
-- UNCOMMENT TO RUN (be careful!)
-- DELETE FROM archetype_analysis_tracking
-- WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
-- AND analysis_type = 'circadian_analysis';

-- DELETE FROM holistic_analysis_results
-- WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
-- AND analysis_type = 'circadian_analysis';

-- ============================================================================
-- QUERY 9: Get recent scores/biomarkers count (for threshold calculation)
-- ============================================================================
SELECT
    'scores' as data_type,
    COUNT(*) as total_count,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as last_hour,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h
FROM scores
WHERE profile_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'

UNION ALL

SELECT
    'biomarkers' as data_type,
    COUNT(*) as total_count,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as last_hour,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h
FROM biomarkers
WHERE profile_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2';

-- This helps understand if there's enough data for threshold to be met

-- ============================================================================
-- QUERY 10: Full diagnostic for latest test run
-- ============================================================================
WITH latest_tracking AS (
    SELECT
        analysis_type,
        last_analysis_at,
        analysis_count,
        EXTRACT(EPOCH FROM (NOW() - last_analysis_at))/60 AS minutes_ago
    FROM archetype_analysis_tracking
    WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
    AND archetype = 'Foundation Builder'
),
latest_results AS (
    SELECT
        analysis_type,
        COUNT(*) as result_count,
        MAX(created_at) as last_result_at
    FROM holistic_analysis_results
    WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
    AND archetype = 'Foundation Builder'
    GROUP BY analysis_type
)
SELECT
    COALESCE(t.analysis_type, r.analysis_type) as analysis_type,
    t.last_analysis_at,
    t.analysis_count,
    t.minutes_ago,
    r.result_count,
    r.last_result_at,
    CASE
        WHEN t.analysis_count = r.result_count THEN '✅ Match'
        WHEN t.analysis_count > r.result_count THEN '⚠️  Tracking > Results'
        ELSE '❌ Results > Tracking'
    END as status
FROM latest_tracking t
FULL OUTER JOIN latest_results r ON t.analysis_type = r.analysis_type
ORDER BY analysis_type;

-- This gives you a complete picture of tracking vs actual results
