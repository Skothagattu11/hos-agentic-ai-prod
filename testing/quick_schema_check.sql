-- ============================================================================
-- Quick Schema Check - Key User/Profile Relationships
-- Run this first to get a quick overview
-- ============================================================================

-- 1. Do these tables exist?
\echo '=== TABLE EXISTENCE ==='
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('users', 'profiles', 'biomarkers', 'scores', 'archetype_analysis_tracking')
AND table_schema = 'public';

-- 2. What columns does profiles table have?
\echo '\n=== PROFILES TABLE COLUMNS ==='
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'profiles' AND table_schema = 'public'
ORDER BY ordinal_position;

-- 3. What foreign keys constrain the profiles table?
\echo '\n=== FOREIGN KEYS ON PROFILES ==='
SELECT
    tc.constraint_name,
    kcu.column_name as profile_column,
    ccu.table_name as references,
    ccu.column_name as references_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'profiles'
  AND tc.table_schema = 'public';

-- 4. What tables reference the profiles table?
\echo '\n=== TABLES REFERENCING PROFILES ==='
SELECT
    tc.table_name,
    kcu.column_name,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_name = 'profiles'
  AND tc.table_schema = 'public';

-- 5. Can we use user_id without creating a profile first?
\echo '\n=== CRITICAL: Check if biomarkers/scores need profiles ==='
SELECT
    'biomarkers' as table_name,
    constraint_name,
    'profile_id -> profiles.id' as constraint
FROM information_schema.table_constraints
WHERE table_name = 'biomarkers'
  AND constraint_type = 'FOREIGN KEY'
  AND constraint_name LIKE '%profile%'

UNION ALL

SELECT
    'scores' as table_name,
    constraint_name,
    'profile_id -> profiles.id' as constraint
FROM information_schema.table_constraints
WHERE table_name = 'scores'
  AND constraint_type = 'FOREIGN KEY'
  AND constraint_name LIKE '%profile%';

\echo '\n=== ✅ Quick check complete! ==='
\echo 'If biomarkers/scores have FK to profiles, you need to remove them for direct user_id usage.'
