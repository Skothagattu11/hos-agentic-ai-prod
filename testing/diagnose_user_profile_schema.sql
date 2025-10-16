-- ============================================================================
-- Database Schema Diagnosis: User and Profile Relationships
-- Purpose: Identify all foreign key constraints and dependencies
-- Date: 2025-10-16
-- ============================================================================

-- ============================================================================
-- STEP 1: Check if users and profiles tables exist
-- ============================================================================

SELECT 'STEP 1: Table Existence Check' as step;

SELECT
    table_name,
    table_schema,
    table_type
FROM information_schema.tables
WHERE table_name IN ('users', 'profiles', 'user_profiles', 'user_accounts')
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_name;

-- ============================================================================
-- STEP 2: Examine profiles table structure
-- ============================================================================

SELECT 'STEP 2: Profiles Table Structure' as step;

SELECT
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'profiles'
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY ordinal_position;

-- ============================================================================
-- STEP 3: Examine users table structure (if exists)
-- ============================================================================

SELECT 'STEP 3: Users Table Structure (if exists)' as step;

SELECT
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'users'
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY ordinal_position;

-- ============================================================================
-- STEP 4: Find all foreign key constraints referencing profiles
-- ============================================================================

SELECT 'STEP 4: Foreign Keys Referencing Profiles' as step;

SELECT
    tc.constraint_name,
    tc.table_name as referencing_table,
    kcu.column_name as referencing_column,
    ccu.table_name as referenced_table,
    ccu.column_name as referenced_column,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
    AND rc.constraint_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_name = 'profiles'
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY tc.table_name, tc.constraint_name;

-- ============================================================================
-- STEP 5: Find all foreign key constraints FROM profiles to other tables
-- ============================================================================

SELECT 'STEP 5: Foreign Keys FROM Profiles to Other Tables' as step;

SELECT
    tc.constraint_name,
    tc.table_name as referencing_table,
    kcu.column_name as referencing_column,
    ccu.table_name as referenced_table,
    ccu.column_name as referenced_column,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
    AND rc.constraint_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'profiles'
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY tc.constraint_name;

-- ============================================================================
-- STEP 6: Find relationships between users and profiles
-- ============================================================================

SELECT 'STEP 6: User-Profile Relationship Analysis' as step;

-- Check if profiles.id references users
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name as profile_column,
    ccu.table_name as references_table,
    ccu.column_name as references_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'profiles'
  AND (kcu.column_name = 'id' OR kcu.column_name = 'user_id')
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema');

-- ============================================================================
-- STEP 7: Check for tables that depend on BOTH users AND profiles
-- ============================================================================

SELECT 'STEP 7: Tables Dependent on Both Users and Profiles' as step;

WITH profile_deps AS (
    SELECT DISTINCT tc.table_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_name = 'profiles'
),
user_deps AS (
    SELECT DISTINCT tc.table_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_name = 'users'
)
SELECT
    pd.table_name,
    'Depends on both users and profiles' as note
FROM profile_deps pd
INNER JOIN user_deps ud ON pd.table_name = ud.table_name
ORDER BY pd.table_name;

-- ============================================================================
-- STEP 8: Find all tables that use profile_id column
-- ============================================================================

SELECT 'STEP 8: Tables with profile_id Column' as step;

SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE column_name = 'profile_id'
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_name;

-- ============================================================================
-- STEP 9: Check biomarkers and scores table constraints
-- ============================================================================

SELECT 'STEP 9: Biomarkers Table Foreign Keys' as step;

SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name as references_table,
    ccu.column_name as references_column,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'biomarkers'
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema');

SELECT 'STEP 9b: Scores Table Foreign Keys' as step;

SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name as references_table,
    ccu.column_name as references_column,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'scores'
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema');

-- ============================================================================
-- STEP 10: Check archetype_analysis_tracking constraints
-- ============================================================================

SELECT 'STEP 10: Archetype Analysis Tracking Foreign Keys' as step;

SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name as references_table,
    ccu.column_name as references_column,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'archetype_analysis_tracking'
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema');

-- ============================================================================
-- STEP 11: Summary of findings
-- ============================================================================

SELECT 'STEP 11: Summary' as step;

SELECT
    'Total foreign keys to profiles' as metric,
    COUNT(*) as count
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_name = 'profiles'

UNION ALL

SELECT
    'Total foreign keys from profiles' as metric,
    COUNT(*) as count
FROM information_schema.table_constraints tc
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'profiles'

UNION ALL

SELECT
    'Tables with profile_id column' as metric,
    COUNT(DISTINCT table_name) as count
FROM information_schema.columns
WHERE column_name = 'profile_id'
  AND table_schema NOT IN ('pg_catalog', 'information_schema');

-- ============================================================================
-- STEP 12: Check if user_id can be used independently
-- ============================================================================

SELECT 'STEP 12: Tables Using user_id Column' as step;

SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE column_name = 'user_id'
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_name;

-- ============================================================================
-- END OF DIAGNOSIS
-- ============================================================================

SELECT '✅ Diagnosis Complete!' as status,
       'Review results above to understand user-profile dependencies' as next_step;
