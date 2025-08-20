-- Archetype-Specific Threshold Analysis Script
-- Compares old global vs new archetype-specific threshold logic
-- Run this to see how data points are calculated with archetype tracking

WITH user_archetype_analysis AS (
  -- Get archetype-specific last analysis dates
  SELECT
    user_id,
    archetype,
    last_analysis_at,
    analysis_count
  FROM archetype_analysis_tracking
  WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
  
  UNION ALL
  
  -- Add a row for testing new archetype (no previous analysis)
  SELECT 
    '35pDPUIfAoRl2Y700bFkxPKYjjf2' as user_id,
    'Transformation Seeker' as archetype,
    NULL as last_analysis_at,
    0 as analysis_count
),
user_global_analysis AS (
  -- Get global last analysis date for comparison
  SELECT
    id as user_id,
    last_analysis_at as global_last_analysis_at
  FROM profiles
  WHERE id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
),
archetype_new_scores AS (
  -- Calculate new scores since archetype-specific last analysis
  SELECT
    ua.archetype,
    COUNT(s.*) as new_scores_count,
    MIN(s.created_at) as earliest_score,
    MAX(s.created_at) as latest_score
  FROM user_archetype_analysis ua
  LEFT JOIN scores s ON s.profile_id = ua.user_id
    AND (ua.last_analysis_at IS NULL OR s.created_at > ua.last_analysis_at)
  GROUP BY ua.archetype
),
archetype_new_biomarkers AS (
  -- Calculate new biomarkers since archetype-specific last analysis
  SELECT
    ua.archetype,
    COUNT(b.*) as new_biomarkers_count,
    MIN(b.created_at) as earliest_biomarker,
    MAX(b.created_at) as latest_biomarker
  FROM user_archetype_analysis ua
  LEFT JOIN biomarkers b ON b.profile_id = ua.user_id
    AND (ua.last_analysis_at IS NULL OR b.created_at > ua.last_analysis_at)
  GROUP BY ua.archetype
),
global_new_scores AS (
  -- Calculate new scores since global last analysis (for comparison)
  SELECT
    COUNT(*) as global_new_scores_count
  FROM scores s
  CROSS JOIN user_global_analysis u
  WHERE s.profile_id = u.user_id
    AND (u.global_last_analysis_at IS NULL OR s.created_at > u.global_last_analysis_at)
),
global_new_biomarkers AS (
  -- Calculate new biomarkers since global last analysis (for comparison) 
  SELECT
    COUNT(*) as global_new_biomarkers_count
  FROM biomarkers b
  CROSS JOIN user_global_analysis u
  WHERE b.profile_id = u.user_id
    AND (u.global_last_analysis_at IS NULL OR b.created_at > u.global_last_analysis_at)
)
SELECT
  ua.user_id,
  ua.archetype,
  ua.last_analysis_at as archetype_last_analysis_at,
  ua.analysis_count as archetype_analysis_count,
  ug.global_last_analysis_at,
  
  -- Archetype-specific data points
  COALESCE(s.new_scores_count, 0) as archetype_new_scores,
  COALESCE(b.new_biomarkers_count, 0) as archetype_new_biomarkers,
  (COALESCE(s.new_scores_count, 0) + COALESCE(b.new_biomarkers_count, 0)) as archetype_total_new_data,
  
  -- Global data points (for comparison)
  COALESCE(gs.global_new_scores_count, 0) as global_new_scores,
  COALESCE(gb.global_new_biomarkers_count, 0) as global_new_biomarkers,
  (COALESCE(gs.global_new_scores_count, 0) + COALESCE(gb.global_new_biomarkers_count, 0)) as global_total_new_data,
  
  -- Threshold analysis (50-point threshold)
  CASE
    WHEN (COALESCE(s.new_scores_count, 0) + COALESCE(b.new_biomarkers_count, 0)) >= 50
    THEN '✅ ARCHETYPE THRESHOLD MET - Fresh analysis should trigger'
    WHEN ua.last_analysis_at IS NULL
    THEN '🆕 NEW ARCHETYPE - Fresh analysis (7-day baseline)'
    ELSE '❌ Below archetype threshold - Should use cache or fallback'
  END as archetype_threshold_status,
  
  CASE
    WHEN (COALESCE(gs.global_new_scores_count, 0) + COALESCE(gb.global_new_biomarkers_count, 0)) >= 50
    THEN '✅ GLOBAL THRESHOLD MET (old logic)'
    ELSE '❌ Below global threshold (old logic)'
  END as global_threshold_status,
  
  -- Data freshness
  s.latest_score as latest_score_date,
  b.latest_biomarker as latest_biomarker_date,
  
  -- Analysis mode determination
  CASE
    WHEN ua.last_analysis_at IS NULL THEN 'INITIAL (7-day baseline)'
    WHEN ua.last_analysis_at < NOW() - INTERVAL '7 days' THEN 'STALE (force refresh)'
    WHEN (COALESCE(s.new_scores_count, 0) + COALESCE(b.new_biomarkers_count, 0)) >= 50 THEN 'FRESH_ANALYSIS'
    ELSE 'CACHE/FALLBACK'
  END as recommended_analysis_mode

FROM user_archetype_analysis ua
LEFT JOIN user_global_analysis ug ON ua.user_id = ug.user_id
LEFT JOIN archetype_new_scores s ON ua.archetype = s.archetype
LEFT JOIN archetype_new_biomarkers b ON ua.archetype = b.archetype
CROSS JOIN global_new_scores gs
CROSS JOIN global_new_biomarkers gb
ORDER BY 
  CASE WHEN ua.last_analysis_at IS NULL THEN 0 ELSE 1 END,  -- New archetypes first
  ua.last_analysis_at DESC NULLS FIRST;

-- Additional summary query
SELECT 
  '📊 ARCHETYPE TRACKING SUMMARY' as section,
  COUNT(*) as total_archetypes_tracked,
  COUNT(*) FILTER (WHERE last_analysis_at IS NOT NULL) as archetypes_with_history,
  COUNT(*) FILTER (WHERE last_analysis_at IS NULL) as new_archetypes,
  MAX(last_analysis_at) as most_recent_archetype_analysis,
  MIN(last_analysis_at) as oldest_archetype_analysis
FROM archetype_analysis_tracking
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2';

-- Memory quality assessment based on archetype history
SELECT 
  '🧠 MEMORY QUALITY ASSESSMENT' as section,
  user_id,
  COUNT(*) as total_archetype_experiences,
  SUM(analysis_count) as total_analyses_across_archetypes,
  AVG(analysis_count) as avg_analyses_per_archetype,
  MAX(analysis_count) as max_analyses_single_archetype,
  CASE
    WHEN COUNT(*) >= 3 AND SUM(analysis_count) >= 10 THEN 'RICH (multiple archetypes, high usage)'
    WHEN COUNT(*) >= 2 OR SUM(analysis_count) >= 5 THEN 'DEVELOPING (some experience)' 
    ELSE 'SPARSE (limited archetype experience)'
  END as memory_quality_level
FROM archetype_analysis_tracking
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
GROUP BY user_id;