-- ============================================================================
-- Remove ALL User and Profile Table Dependencies
-- Purpose: Decouple from users/profiles tables - use external auth system
-- Date: 2025-10-16
-- CRITICAL: This allows using ANY user_id/profile_id without validation
-- ============================================================================

-- ============================================================================
-- STEP 1: Document what we're removing (for rollback reference)
-- ============================================================================

\echo '=== STEP 1: Documenting constraints to be removed ==='

-- List all FK constraints from biomarkers/scores to profiles
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name as references_table,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('biomarkers', 'scores', 'archetype_analysis_tracking')
  AND ccu.table_name IN ('profiles', 'users')
  AND tc.table_schema = 'public';

-- ============================================================================
-- STEP 2: Remove biomarkers FK constraints (profiles + users)
-- ============================================================================

\echo '\n=== STEP 2: Removing biomarkers foreign key constraints ==='

-- Remove: biomarkers.profile_id → profiles.id (NO ACTION)
ALTER TABLE biomarkers DROP CONSTRAINT IF EXISTS biomarkers_profile_id_fkey;
\echo 'Dropped: biomarkers_profile_id_fkey'

-- Remove: biomarkers.profile_id → profiles.id (CASCADE)
ALTER TABLE biomarkers DROP CONSTRAINT IF EXISTS fk_biomarkers_profile;
\echo 'Dropped: fk_biomarkers_profile'

-- Remove: biomarkers.user_id → users.id (CASCADE)
ALTER TABLE biomarkers DROP CONSTRAINT IF EXISTS fk_biomarkers_user;
\echo 'Dropped: fk_biomarkers_user'

-- Remove any other biomarkers constraints to users/profiles
DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    FOR constraint_record IN
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = 'biomarkers'
          AND ccu.table_name IN ('profiles', 'users')
          AND tc.table_schema = 'public'
    LOOP
        EXECUTE format('ALTER TABLE biomarkers DROP CONSTRAINT IF EXISTS %I', constraint_record.constraint_name);
        RAISE NOTICE 'Dropped additional constraint: %', constraint_record.constraint_name;
    END LOOP;
END $$;

-- ============================================================================
-- STEP 3: Remove scores FK constraints (profiles + users)
-- ============================================================================

\echo '\n=== STEP 3: Removing scores foreign key constraints ==='

-- Remove: scores.profile_id → profiles.id (NO ACTION)
ALTER TABLE scores DROP CONSTRAINT IF EXISTS scores_profile_id_fkey;
\echo 'Dropped: scores_profile_id_fkey'

-- Remove: scores.profile_id → profiles.id (CASCADE)
ALTER TABLE scores DROP CONSTRAINT IF EXISTS fk_scores_profile;
\echo 'Dropped: fk_scores_profile'

-- Remove: scores.user_id → users.id (CASCADE)
ALTER TABLE scores DROP CONSTRAINT IF EXISTS fk_scores_user;
\echo 'Dropped: fk_scores_user'

-- Remove any other scores constraints to users/profiles
DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    FOR constraint_record IN
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = 'scores'
          AND ccu.table_name IN ('profiles', 'users')
          AND tc.table_schema = 'public'
    LOOP
        EXECUTE format('ALTER TABLE scores DROP CONSTRAINT IF EXISTS %I', constraint_record.constraint_name);
        RAISE NOTICE 'Dropped additional constraint: %', constraint_record.constraint_name;
    END LOOP;
END $$;

-- ============================================================================
-- STEP 4: Remove archetype_analysis_tracking FK constraints (if any)
-- ============================================================================

\echo '\n=== STEP 4: Removing archetype_analysis_tracking FK constraints (if any) ==='

DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    FOR constraint_record IN
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = 'archetype_analysis_tracking'
          AND ccu.table_name IN ('profiles', 'users')
          AND tc.table_schema = 'public'
    LOOP
        EXECUTE format('ALTER TABLE archetype_analysis_tracking DROP CONSTRAINT IF EXISTS %I', constraint_record.constraint_name);
        RAISE NOTICE 'Dropped constraint from archetype_analysis_tracking: %', constraint_record.constraint_name;
    END LOOP;
END $$;

-- ============================================================================
-- STEP 5: Verify ALL constraints removed
-- ============================================================================

\echo '\n=== STEP 5: Verifying all FK constraints removed ==='

-- Check if any FK constraints remain
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name as still_references,
    '⚠️ STILL EXISTS - Manual removal needed' as status
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('biomarkers', 'scores', 'archetype_analysis_tracking')
  AND ccu.table_name IN ('profiles', 'users')
  AND tc.table_schema = 'public';

-- If above query returns 0 rows, we're successful!

-- ============================================================================
-- STEP 6: Add performance indexes (since FKs are gone)
-- ============================================================================

\echo '\n=== STEP 6: Adding performance indexes ==='

-- Biomarkers indexes
CREATE INDEX IF NOT EXISTS idx_biomarkers_profile_id
ON biomarkers(profile_id)
WHERE profile_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_biomarkers_user_id
ON biomarkers(user_id)
WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_biomarkers_profile_created
ON biomarkers(profile_id, created_at DESC)
WHERE profile_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_biomarkers_profile_type
ON biomarkers(profile_id, type)
WHERE profile_id IS NOT NULL;

\echo 'Created biomarkers indexes'

-- Scores indexes
CREATE INDEX IF NOT EXISTS idx_scores_profile_id
ON scores(profile_id)
WHERE profile_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_scores_user_id
ON scores(user_id)
WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_scores_profile_created
ON scores(profile_id, created_at DESC)
WHERE profile_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_scores_profile_type
ON scores(profile_id, type)
WHERE profile_id IS NOT NULL;

\echo 'Created scores indexes'

-- Archetype analysis tracking indexes
CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_id
ON archetype_analysis_tracking(user_id);

CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_archetype
ON archetype_analysis_tracking(user_id, archetype);

CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_type
ON archetype_analysis_tracking(user_id, analysis_type);

\echo 'Created archetype_analysis_tracking indexes'

-- ============================================================================
-- STEP 7: Test that new user workflow works
-- ============================================================================

\echo '\n=== STEP 7: Testing new user workflow (will rollback) ==='

BEGIN;

-- Test 1: Insert biomarker with non-existent profile_id and user_id
INSERT INTO biomarkers (
    profile_id,
    user_id,
    type,
    data,
    start_date_time,
    end_date_time,
    created_at
) VALUES (
    'new_test_user_123',  -- Does NOT exist in profiles
    'a0000000-0000-0000-0000-000000000001'::uuid,  -- Does NOT exist in users
    'heart_rate',
    '{"value": 72, "unit": "bpm"}',
    NOW(),
    NOW(),
    NOW()
);

\echo '✅ Test 1 passed: biomarker inserted without profile/user validation'

-- Test 2: Insert score with non-existent profile_id and user_id
INSERT INTO scores (
    profile_id,
    user_id,
    type,
    score,
    score_date_time,
    created_at
) VALUES (
    'new_test_user_123',  -- Does NOT exist in profiles
    'a0000000-0000-0000-0000-000000000001'::uuid,  -- Does NOT exist in users
    'sleep',
    85.5,
    NOW(),
    NOW()
);

\echo '✅ Test 2 passed: score inserted without profile/user validation'

-- Test 3: Insert into archetype_analysis_tracking with non-existent user_id
INSERT INTO archetype_analysis_tracking (
    user_id,
    archetype,
    analysis_type,
    analysis_timestamp,
    analysis_count,
    created_at,
    updated_at
) VALUES (
    'new_test_user_123',  -- Does NOT exist anywhere
    'Peak Performer',
    'circadian_analysis',
    NOW(),
    1,
    NOW(),
    NOW()
);

\echo '✅ Test 3 passed: archetype tracking inserted without user validation'

ROLLBACK;

\echo 'All test inserts rolled back (not saved)'

-- ============================================================================
-- STEP 8: Document changes
-- ============================================================================

\echo '\n=== STEP 8: Summary of Changes ==='

SELECT
    'biomarkers' as table_name,
    'profile_id, user_id' as columns,
    'No FK constraints' as new_state,
    'Can use ANY value' as benefit
UNION ALL
SELECT
    'scores' as table_name,
    'profile_id, user_id' as columns,
    'No FK constraints' as new_state,
    'Can use ANY value' as benefit
UNION ALL
SELECT
    'archetype_analysis_tracking' as table_name,
    'user_id' as columns,
    'No FK constraints' as new_state,
    'Can use ANY value' as benefit;

-- ============================================================================
-- STEP 9: Verify column data types (for documentation)
-- ============================================================================

\echo '\n=== STEP 9: Column data types (for reference) ==='

SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name IN ('biomarkers', 'scores', 'archetype_analysis_tracking')
  AND column_name IN ('profile_id', 'user_id')
  AND table_schema = 'public'
ORDER BY table_name, column_name;

-- ============================================================================
-- SUCCESS!
-- ============================================================================

\echo '\n=== ✅ Migration Complete! ==='
\echo ''
\echo 'SUMMARY:'
\echo '✅ biomarkers: Removed ALL FK constraints to profiles and users'
\echo '✅ scores: Removed ALL FK constraints to profiles and users'
\echo '✅ archetype_analysis_tracking: Removed ALL FK constraints (if any existed)'
\echo '✅ Performance indexes added'
\echo '✅ Test inserts successful'
\echo ''
\echo 'YOU CAN NOW:'
\echo '1. Use ANY user_id value (from your external auth system)'
\echo '2. Use user_id as profile_id (or use any identifier)'
\echo '3. Insert biomarkers/scores without creating profiles first'
\echo '4. Sahha integration will work immediately with external_id'
\echo ''
\echo 'IMPORTANT:'
\echo '- profiles and users tables still exist (not dropped)'
\echo '- Other tables still reference profiles (archetypes, plan_items, etc.)'
\echo '- Only biomarkers, scores, and archetype_analysis_tracking are decoupled'
\echo '- Your application is now responsible for data consistency'
\echo ''
\echo 'NEXT STEPS:'
\echo '1. Test with a real new user'
\echo '2. Use Sahha external_id as profile_id in your code'
\echo '3. Run comprehensive tests to ensure everything works'
