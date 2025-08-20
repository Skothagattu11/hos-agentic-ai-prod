-- Simple Archetype-Specific Threshold Check
-- Shows data point counts since last archetype analysis vs global analysis

WITH user_archetype_analysis AS (
  SELECT
    user_id,
    archetype,
    last_analysis_at
  FROM archetype_analysis_tracking
  WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
),
user_global_analysis AS (
  SELECT
    id as user_id,
    last_analysis_at as global_last_analysis_at
  FROM profiles
  WHERE id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
),
archetype_new_scores AS (
  SELECT
    ua.archetype,
    COUNT(*) as new_scores_count
  FROM user_archetype_analysis ua
  CROSS JOIN scores s
  WHERE s.profile_id = ua.user_id
    AND (ua.last_analysis_at IS NULL OR s.created_at > ua.last_analysis_at)
  GROUP BY ua.archetype
),
archetype_new_biomarkers AS (
  SELECT
    ua.archetype,
    COUNT(*) as new_biomarkers_count
  FROM user_archetype_analysis ua
  CROSS JOIN biomarkers b
  WHERE b.profile_id = ua.user_id
    AND (ua.last_analysis_at IS NULL OR b.created_at > ua.last_analysis_at)
  GROUP BY ua.archetype
),
global_new_scores AS (
  SELECT
    COUNT(*) as global_new_scores_count
  FROM scores s
  CROSS JOIN user_global_analysis u
  WHERE s.profile_id = u.user_id
    AND (u.global_last_analysis_at IS NULL OR s.created_at > u.global_last_analysis_at)
),
global_new_biomarkers AS (
  SELECT
    COUNT(*) as global_new_biomarkers_count
  FROM biomarkers b
  CROSS JOIN user_global_analysis u
  WHERE b.profile_id = u.user_id
    AND (u.global_last_analysis_at IS NULL OR b.created_at > u.global_last_analysis_at)
)
SELECT
  ua.archetype,
  ua.last_analysis_at as archetype_last_analysis_at,
  ug.global_last_analysis_at,
  
  -- Data point counts since archetype-specific analysis
  COALESCE(s.new_scores_count, 0) as new_scores_count,
  COALESCE(b.new_biomarkers_count, 0) as new_biomarkers_count,
  (COALESCE(s.new_scores_count, 0) + COALESCE(b.new_biomarkers_count, 0)) as total_new_data_points,
  
  -- Data point counts since global analysis (for comparison)
  gs.global_new_scores_count,
  gb.global_new_biomarkers_count,
  (gs.global_new_scores_count + gb.global_new_biomarkers_count) as global_total_new_data_points,
  
  -- Threshold status
  CASE
    WHEN (COALESCE(s.new_scores_count, 0) + COALESCE(b.new_biomarkers_count, 0)) >= 50
    THEN '✅ THRESHOLD MET - Fresh analysis should trigger'
    WHEN ua.last_analysis_at IS NULL
    THEN '🆕 NEW ARCHETYPE - Fresh analysis (7-day baseline)'
    ELSE '❌ Below threshold - Cached analysis expected'
  END as threshold_status

FROM user_archetype_analysis ua
LEFT JOIN user_global_analysis ug ON ua.user_id = ug.user_id
LEFT JOIN archetype_new_scores s ON ua.archetype = s.archetype
LEFT JOIN archetype_new_biomarkers b ON ua.archetype = b.archetype
CROSS JOIN global_new_scores gs
CROSS JOIN global_new_biomarkers gb
ORDER BY ua.last_analysis_at DESC NULLS FIRST;