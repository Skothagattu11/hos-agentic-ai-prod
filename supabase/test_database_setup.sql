-- Database Setup Verification Test Suite
-- Purpose: Verify all tables, constraints, and duplicate prevention are working correctly
-- Date: 2025-08-15

-- ============================================
-- 1. VERIFY TABLE STRUCTURE
-- ============================================
SELECT '===== 1. TABLE STRUCTURE CHECK =====' as test_section;

-- Check if all required tables exist
SELECT 
    table_name,
    CASE 
        WHEN table_name IN ('holistic_analysis_results', 'holistic_insights', 
                           'holistic_shortterm_memory', 'holistic_working_memory', 
                           'holistic_longterm_memory', 'holistic_meta_memory')
        THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END as status
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'holistic_%'
ORDER BY table_name;

-- ============================================
-- 2. CHECK NEW COLUMNS WERE ADDED
-- ============================================
SELECT '===== 2. NEW COLUMNS CHECK =====' as test_section;

-- Check holistic_analysis_results columns
SELECT 
    'holistic_analysis_results' as table_name,
    column_name,
    data_type,
    CASE 
        WHEN column_name IN ('analysis_hash', 'data_source_hash', 'is_duplicate', 'original_analysis_id')
        THEN '✅ NEW COLUMN'
        ELSE '📝 EXISTING'
    END as column_status
FROM information_schema.columns
WHERE table_name = 'holistic_analysis_results'
AND column_name IN ('analysis_hash', 'data_source_hash', 'is_duplicate', 'original_analysis_id', 'id', 'user_id')
ORDER BY column_name;

-- Check holistic_shortterm_memory columns
SELECT 
    'holistic_shortterm_memory' as table_name,
    column_name,
    data_type,
    CASE 
        WHEN column_name IN ('content_hash', 'created_date')
        THEN '✅ NEW COLUMN'
        ELSE '📝 EXISTING'
    END as column_status
FROM information_schema.columns
WHERE table_name = 'holistic_shortterm_memory'
AND column_name IN ('content_hash', 'created_date', 'id', 'user_id')
ORDER BY column_name;

-- ============================================
-- 3. CHECK CONSTRAINTS AND INDEXES
-- ============================================
SELECT '===== 3. CONSTRAINTS & INDEXES CHECK =====' as test_section;

-- Check unique constraints
SELECT 
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    '✅ ACTIVE' as status
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'public'
AND tc.table_name LIKE 'holistic_%'
AND tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY', 'FOREIGN KEY')
ORDER BY tc.table_name, tc.constraint_type;

-- Check indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    CASE 
        WHEN indexname LIKE '%unique%' THEN '🔑 UNIQUE INDEX'
        ELSE '📍 REGULAR INDEX'
    END as index_type
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename LIKE 'holistic_%'
ORDER BY tablename, indexname;

-- ============================================
-- 4. CHECK TRIGGERS
-- ============================================
SELECT '===== 4. TRIGGERS CHECK =====' as test_section;

SELECT 
    trigger_name,
    event_object_table as table_name,
    event_manipulation as trigger_event,
    '✅ ACTIVE' as status
FROM information_schema.triggers
WHERE trigger_schema = 'public'
AND event_object_table LIKE 'holistic_%'
ORDER BY event_object_table, trigger_name;

-- ============================================
-- 5. CHECK FOR EXISTING DUPLICATES
-- ============================================
SELECT '===== 5. DUPLICATE DATA CHECK =====' as test_section;

-- Check for duplicates in holistic_analysis_results
WITH duplicate_check AS (
    SELECT 
        user_id,
        analysis_type,
        analysis_date,
        archetype,
        COUNT(*) as duplicate_count
    FROM holistic_analysis_results
    GROUP BY user_id, analysis_type, analysis_date, archetype
    HAVING COUNT(*) > 1
)
SELECT 
    COALESCE(COUNT(*), 0) as tables_with_duplicates,
    COALESCE(SUM(duplicate_count), 0) as total_duplicates,
    CASE 
        WHEN COALESCE(COUNT(*), 0) = 0 THEN '✅ NO DUPLICATES'
        ELSE '⚠️ DUPLICATES FOUND'
    END as status
FROM duplicate_check;

-- Detailed duplicate analysis
SELECT 
    'holistic_analysis_results' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT analysis_hash) as unique_hashes,
    COUNT(*) - COUNT(DISTINCT analysis_hash) as potential_duplicates,
    COUNT(*) FILTER (WHERE is_duplicate = true) as marked_duplicates
FROM holistic_analysis_results;

-- Check shortterm memory duplicates
SELECT 
    'holistic_shortterm_memory' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT content_hash) as unique_hashes,
    COUNT(*) FILTER (WHERE memory_category = 'analysis_results') as analysis_results_count
FROM holistic_shortterm_memory;

-- ============================================
-- 6. CHECK HOLISTIC_INSIGHTS TABLE
-- ============================================
SELECT '===== 6. INSIGHTS TABLE CHECK =====' as test_section;

-- Check insights table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default IS NOT NULL as has_default
FROM information_schema.columns
WHERE table_name = 'holistic_insights'
AND column_name IN ('id', 'user_id', 'insight_type', 'source_analysis_id', 
                    'content_hash', 'context_signature', 'priority', 'actionability_score')
ORDER BY ordinal_position;

-- Check foreign key relationships
SELECT 
    conname as constraint_name,
    conrelid::regclass as table_name,
    confrelid::regclass as references_table,
    '✅ FOREIGN KEY' as relationship_status
FROM pg_constraint
WHERE contype = 'f'
AND conrelid::regclass::text LIKE 'holistic_%';

-- ============================================
-- 7. DATA INTEGRITY CHECK
-- ============================================
SELECT '===== 7. DATA INTEGRITY CHECK =====' as test_section;

-- Check for orphaned references
SELECT 
    'Orphaned insights (no source analysis)' as check_type,
    COUNT(*) as count,
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ CLEAN'
        ELSE '⚠️ ORPHANS FOUND'
    END as status
FROM holistic_insights hi
LEFT JOIN holistic_analysis_results har ON hi.source_analysis_id = har.id
WHERE hi.source_analysis_id IS NOT NULL
AND har.id IS NULL;

-- Check for data in each memory table
SELECT 
    'holistic_working_memory' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions
FROM holistic_working_memory
UNION ALL
SELECT 
    'holistic_shortterm_memory',
    COUNT(*),
    COUNT(DISTINCT user_id),
    0
FROM holistic_shortterm_memory
UNION ALL
SELECT 
    'holistic_longterm_memory',
    COUNT(*),
    COUNT(DISTINCT user_id),
    0
FROM holistic_longterm_memory
UNION ALL
SELECT 
    'holistic_meta_memory',
    COUNT(*),
    COUNT(DISTINCT user_id),
    0
FROM holistic_meta_memory
ORDER BY table_name;

-- ============================================
-- 8. FUNCTION AVAILABILITY CHECK
-- ============================================
SELECT '===== 8. FUNCTIONS CHECK =====' as test_section;

SELECT 
    proname as function_name,
    CASE 
        WHEN proname IN ('mark_analysis_duplicates', 'cleanup_shortterm_memory_duplicates', 
                        'generate_analysis_hash', 'generate_content_hash')
        THEN '✅ AVAILABLE'
        ELSE '📝 OTHER'
    END as status
FROM pg_proc
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
AND proname IN ('mark_analysis_duplicates', 'cleanup_shortterm_memory_duplicates', 
                'generate_analysis_hash', 'generate_content_hash', 
                'set_analysis_hash', 'set_content_hash', 'set_created_date')
ORDER BY proname;

-- ============================================
-- 9. SAMPLE DATA CHECK
-- ============================================
SELECT '===== 9. SAMPLE DATA CHECK =====' as test_section;

-- Show sample of recent analysis with hash
SELECT 
    id,
    user_id,
    analysis_type,
    archetype,
    analysis_date,
    LEFT(analysis_hash, 10) || '...' as hash_preview,
    is_duplicate,
    created_at
FROM holistic_analysis_results
ORDER BY created_at DESC
LIMIT 5;

-- ============================================
-- 10. SUMMARY REPORT
-- ============================================
SELECT '===== 10. SUMMARY REPORT =====' as test_section;

WITH summary AS (
    SELECT 
        (SELECT COUNT(*) FROM holistic_analysis_results) as analysis_count,
        (SELECT COUNT(*) FROM holistic_insights) as insights_count,
        (SELECT COUNT(*) FROM holistic_shortterm_memory) as shortterm_count,
        (SELECT COUNT(*) FROM holistic_working_memory) as working_count,
        (SELECT COUNT(*) FILTER (WHERE is_duplicate = true) FROM holistic_analysis_results) as duplicates_marked,
        (SELECT COUNT(DISTINCT user_id) FROM holistic_analysis_results) as unique_users
)
SELECT 
    'Total Analysis Records' as metric,
    analysis_count as value
FROM summary
UNION ALL
SELECT 'Total Insights', insights_count FROM summary
UNION ALL
SELECT 'Shortterm Memory Items', shortterm_count FROM summary
UNION ALL
SELECT 'Working Memory Items', working_count FROM summary
UNION ALL
SELECT 'Duplicates Marked', duplicates_marked FROM summary
UNION ALL
SELECT 'Unique Users', unique_users FROM summary
ORDER BY metric;

-- Final status
SELECT 
    '🎯 DATABASE SETUP VERIFICATION COMPLETE' as status,
    'Review the results above to confirm all components are properly configured' as message;