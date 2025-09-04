-- =====================================================================
-- Admin API SQL Queries for Testing
-- Test these queries with your actual data before implementing APIs
-- Replace user_id and dates with your actual values
-- =====================================================================

-- =====================================================================
-- QUERY 1: User List for Dashboard Homepage
-- Used by: GET /api/admin/users
-- =====================================================================
WITH latest_analyses AS (
    SELECT DISTINCT ON (user_id) 
        user_id,
        archetype,
        created_at as last_analysis_date,
        analysis_type
    FROM holistic_analysis_results 
    ORDER BY user_id, created_at DESC
),
analysis_counts AS (
    SELECT 
        user_id,
        COUNT(*) as total_analyses
    FROM holistic_analysis_results
    GROUP BY user_id
)
SELECT 
    p.id,
    p.data->>'name' as name,
    (p.data->>'age')::integer as age,
    la.archetype as latest_archetype,
    la.last_analysis_date,
    COALESCE(ac.total_analyses, 0) as total_analyses,
    p.created_at as profile_created
FROM profiles p
LEFT JOIN latest_analyses la ON p.id = la.user_id
LEFT JOIN analysis_counts ac ON p.id = ac.user_id
ORDER BY la.last_analysis_date DESC NULLS LAST
LIMIT 50 OFFSET 0;

-- =====================================================================
-- QUERY 2A: User Profile Basic Info
-- Used by: GET /api/admin/user/{user_id}/overview
-- Replace '35pDPUIfAoRl2Y700bFkxPKYjjf2' with your user_id
-- =====================================================================
SELECT 
    id,
    data->>'name' as name,
    (data->>'age')::integer as age,
    created_at,
    updated_at,
    last_analysis_at,
    data -- Full profile data
FROM profiles 
WHERE id = '35pDPUIfAoRl2Y700bFkxPKYjjf2';

-- =====================================================================
-- QUERY 2B: User Analysis Summary
-- Used by: GET /api/admin/user/{user_id}/overview
-- Replace '35pDPUIfAoRl2Y700bFkxPKYjjf2' with your user_id
-- =====================================================================
SELECT 
    COUNT(*) as total_analyses,
    COUNT(CASE WHEN analysis_type = 'behavior_analysis' THEN 1 END) as behavior_analyses,
    COUNT(CASE WHEN analysis_type = 'nutrition_plan' THEN 1 END) as nutrition_analyses,
    COUNT(CASE WHEN analysis_type = 'routine_plan' THEN 1 END) as routine_analyses,
    COUNT(CASE WHEN analysis_type = 'complete_analysis' THEN 1 END) as complete_analyses,
    MAX(created_at) as last_analysis_date,
    (SELECT archetype FROM holistic_analysis_results 
     WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2' 
     ORDER BY created_at DESC LIMIT 1) as latest_archetype
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2';

-- =====================================================================
-- QUERY 3: Analysis Data for Specific Date
-- Used by: GET /api/admin/user/{user_id}/analysis-data?date={date}
-- Replace user_id and date with your values
-- =====================================================================
SELECT 
    id as analysis_id,
    analysis_date,
    analysis_type,
    archetype,
    analysis_result,
    input_summary,
    confidence_score,
    completeness_score,
    created_at,
    analysis_trigger
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2' 
AND DATE(analysis_date) = '2025-08-19'
ORDER BY created_at DESC
LIMIT 10;

-- =====================================================================
-- QUERY 4: Check Analysis Result Structure (IMPORTANT)
-- This shows the structure of your analysis_result JSON
-- =====================================================================
SELECT 
    id,
    analysis_type,
    archetype,
    jsonb_pretty(analysis_result) as formatted_result
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
LIMIT 1;

-- =====================================================================
-- QUERY 5: Check What Keys Exist in analysis_result (FIXED for STRING type)
-- This tells us how your data is structured
-- =====================================================================
SELECT 
    id,
    analysis_type,
    archetype,
    -- Parse the JSON string and check for keys
    (analysis_result::jsonb) ? 'behavioral_signature' as has_behavioral_signature,
    (analysis_result::jsonb) ? 'sophistication_assessment' as has_sophistication,
    (analysis_result::jsonb) ? 'primary_goal' as has_primary_goal,
    (analysis_result::jsonb) ? 'personalized_strategy' as has_strategy,
    (analysis_result::jsonb) ? 'recommendations' as has_recommendations,
    (analysis_result::jsonb) ? 'content' as has_content,
    (analysis_result::jsonb) ? 'date' as has_date,
    -- Get all top level keys from the parsed JSON
    (SELECT array_agg(key) FROM jsonb_object_keys(analysis_result::jsonb) key) as all_keys,
    -- Show length of the JSON string
    length(analysis_result) as result_length
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
ORDER BY created_at DESC
LIMIT 3;

-- =====================================================================
-- QUERY 6: Get All Available Dates for User
-- Shows what dates have data for the date picker
-- =====================================================================
SELECT 
    DATE(analysis_date) as date,
    COUNT(*) as analysis_count,
    array_agg(DISTINCT analysis_type ORDER BY analysis_type) as analysis_types,
    array_agg(DISTINCT archetype) as archetypes_used,
    MIN(created_at) as first_analysis_time,
    MAX(created_at) as last_analysis_time
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
GROUP BY DATE(analysis_date)
ORDER BY date DESC
LIMIT 30;

-- =====================================================================
-- QUERY 7: Get Insights for User (FIXED column names)
-- If you want to show insights in the dashboard
-- =====================================================================
SELECT 
    id,
    insight_type,
    insight_title,
    insight_content,
    confidence_score,
    priority,
    actionability_score,
    created_at,
    source_analysis_id
FROM holistic_insights
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
AND DATE(created_at) = '2025-08-20'
ORDER BY created_at DESC
LIMIT 10;

-- =====================================================================
-- QUERY 8: Combined Dashboard Query (FIXED)
-- Gets everything needed for a user's dashboard in one query
-- =====================================================================
WITH user_analyses AS (
    SELECT 
        id,
        analysis_date,
        analysis_type,
        archetype,
        analysis_result::jsonb as parsed_result,
        confidence_score,
        completeness_score,
        created_at
    FROM holistic_analysis_results
    WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2' 
    AND DATE(analysis_date) = '2025-08-20'
),
user_insights AS (
    SELECT 
        insight_type,
        insight_title,
        insight_content,
        confidence_score,
        created_at
    FROM holistic_insights
    WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
    AND DATE(created_at) = '2025-08-20'
)
SELECT 
    (SELECT json_agg(ua.*) FROM user_analyses ua) as analyses,
    (SELECT json_agg(ui.*) FROM user_insights ui) as insights;

-- =====================================================================
-- QUERY 9: Check Analysis Types and Content Structure
-- This helps understand the relationship between analysis_type and content
-- =====================================================================
SELECT 
    id,
    analysis_type,
    archetype,
    CASE 
        WHEN analysis_type = 'complete_analysis' THEN 'Complete Analysis (all components)'
        WHEN analysis_type = 'behavior_analysis' THEN 'Behavior Analysis Only'
        WHEN analysis_type = 'routine_plan' THEN 'Routine Plan Only'
        WHEN analysis_type = 'nutrition_plan' THEN 'Nutrition Plan Only'
        ELSE 'Unknown Type'
    END as analysis_category,
    -- Check what content is actually present
    analysis_result ? 'behavior_analysis' as has_behavior_content,
    analysis_result ? 'routine_plan' as has_routine_content,
    analysis_result ? 'nutrition_plan' as has_nutrition_content,
    jsonb_typeof(analysis_result) as result_type,
    created_at
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
ORDER BY created_at DESC
LIMIT 10;

-- =====================================================================
-- QUERY 10: Get Sample of Each Analysis Type
-- Shows structure of different analysis types
-- =====================================================================
SELECT DISTINCT ON (analysis_type)
    analysis_type,
    archetype,
    confidence_score,
    completeness_score,
    jsonb_pretty(analysis_result) as sample_structure,
    created_at
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
ORDER BY analysis_type, created_at DESC;

-- =====================================================================
-- NEW QUERY 11: Test JSON String Parsing
-- This verifies we can parse the analysis_result string as JSON
-- =====================================================================
SELECT 
    id,
    analysis_type,
    archetype,
    -- Parse the JSON string and extract specific fields
    (analysis_result::jsonb)->>'model_used' as model_used,
    (analysis_result::jsonb)->>'analysis_type' as internal_analysis_type,
    -- For behavior_analysis
    (analysis_result::jsonb)->'behavioral_signature'->>'signature' as behavior_signature,
    (analysis_result::jsonb)->'primary_goal'->>'goal' as primary_goal,
    -- For routine_plan  
    (analysis_result::jsonb)->>'content' as routine_content_preview,
    substring((analysis_result::jsonb)->>'content', 1, 200) as content_preview,
    created_at
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
ORDER BY created_at DESC
LIMIT 3;

-- =====================================================================
-- NEW QUERY 12: Get Profile Data Structure
-- This shows how to extract user info from profiles.data
-- =====================================================================
SELECT 
    id,
    -- Extract profile info from the nested JSON
    data->'profileInfo'->>'externalId' as external_id,
    data->'profileInfo'->>'accountId' as account_id,
    data->'profileInfo'->>'createdAtUtc' as sahha_created_at,
    data->'profileInfo'->>'dataLastReceivedAtUtc' as last_data_received,
    data->'profileInfo'->>'isSampleProfile' as is_sample,
    -- Check if there are other data fields we could use for name/age
    jsonb_object_keys(data) as top_level_keys,
    created_at,
    updated_at
FROM profiles 
WHERE id = '35pDPUIfAoRl2Y700bFkxPKYjjf2';

-- =====================================================================
-- DEBUG QUERY 13: Diagnose JSON Parsing Issue
-- This helps us understand why JSON parsing is failing
-- =====================================================================
SELECT 
    id,
    analysis_type,
    -- Show first 500 characters of the analysis_result string
    substring(analysis_result, 1, 500) as result_preview,
    -- Check if it starts and ends with quotes
    left(analysis_result, 10) as starts_with,
    right(analysis_result, 10) as ends_with,
    -- Try different parsing approaches
    CASE 
        WHEN analysis_result::text ~ '^".*"$' THEN 'Quoted JSON string'
        WHEN analysis_result::text ~ '^{.*}$' THEN 'Direct JSON object'
        ELSE 'Unknown format'
    END as format_type,
    length(analysis_result) as total_length
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
AND analysis_type = 'behavior_analysis'
ORDER BY created_at DESC
LIMIT 1;

-- =====================================================================
-- DEBUG QUERY 14: Try Alternative JSON Parsing
-- Test different ways to parse the JSON
-- =====================================================================
SELECT 
    id,
    analysis_type,
    (trim(analysis_result, '"')::jsonb)->>'model_used' as model_via_trim,
    (analysis_result::jsonb)->>'model_used' as model_direct,
    length(replace(analysis_result, '\\', '')) as length_without_escapes,
    length(analysis_result) as original_length
FROM holistic_analysis_results
WHERE user_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2'
ORDER BY created_at DESC
LIMIT 1;

-- =====================================================================
-- INSTRUCTIONS:
-- 1. Replace '35pDPUIfAoRl2Y700bFkxPKYjjf2' with your actual user_id
-- 2. Run DEBUG QUERY 13 and 14 to understand the JSON format
-- 3. Share the results so I can fix the parsing logic
-- 4. Note: I also see the datetime format differences - will handle those too
-- =====================================================================