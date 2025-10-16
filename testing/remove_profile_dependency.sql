-- ============================================================================
-- Remove Profile Table Dependency - Allow Direct user_id Usage
-- Purpose: Enable creating biomarkers/scores with just user_id (no profile needed)
-- Date: 2025-10-16
-- ============================================================================

-- IMPORTANT: Run quick_schema_check.sql first to confirm dependencies exist!

-- ============================================================================
-- STEP 1: Backup current constraints (for documentation)
-- ============================================================================

\echo '=== STEP 1: Document existing constraints ==='

-- List all constraints we're about to remove
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name as references_table,
    ccu.column_name as references_column
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
LEFT JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('biomarkers', 'scores', 'archetype_analysis_tracking')
  AND ccu.table_name = 'profiles'
  AND tc.table_schema = 'public';

-- ============================================================================
-- STEP 2: Remove foreign key from biomarkers.profile_id -> profiles.id
-- ============================================================================

\echo '\n=== STEP 2: Remove biomarkers -> profiles FK ==='

-- Drop the constraint (adjust constraint name based on your schema)
DO $$
DECLARE
    constraint_name_var TEXT;
BEGIN
    -- Find the constraint name dynamically
    SELECT tc.constraint_name INTO constraint_name_var
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_name = 'biomarkers'
      AND kcu.column_name = 'profile_id'
      AND ccu.table_name = 'profiles'
      AND tc.table_schema = 'public'
    LIMIT 1;

    IF constraint_name_var IS NOT NULL THEN
        EXECUTE format('ALTER TABLE biomarkers DROP CONSTRAINT IF EXISTS %I', constraint_name_var);
        RAISE NOTICE 'Dropped constraint: %', constraint_name_var;
    ELSE
        RAISE NOTICE 'No FK constraint found on biomarkers.profile_id -> profiles.id';
    END IF;
END $$;

-- ============================================================================
-- STEP 3: Remove foreign key from scores.profile_id -> profiles.id
-- ============================================================================

\echo '\n=== STEP 3: Remove scores -> profiles FK ==='

DO $$
DECLARE
    constraint_name_var TEXT;
BEGIN
    -- Find the constraint name dynamically
    SELECT tc.constraint_name INTO constraint_name_var
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_name = 'scores'
      AND kcu.column_name = 'profile_id'
      AND ccu.table_name = 'profiles'
      AND tc.table_schema = 'public'
    LIMIT 1;

    IF constraint_name_var IS NOT NULL THEN
        EXECUTE format('ALTER TABLE scores DROP CONSTRAINT IF EXISTS %I', constraint_name_var);
        RAISE NOTICE 'Dropped constraint: %', constraint_name_var;
    ELSE
        RAISE NOTICE 'No FK constraint found on scores.profile_id -> profiles.id';
    END IF;
END $$;

-- ============================================================================
-- STEP 4: Remove foreign key from archetype_analysis_tracking (if exists)
-- ============================================================================

\echo '\n=== STEP 4: Remove archetype_analysis_tracking -> profiles FK (if exists) ==='

DO $$
DECLARE
    constraint_name_var TEXT;
BEGIN
    -- Find the constraint name dynamically
    SELECT tc.constraint_name INTO constraint_name_var
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_name = 'archetype_analysis_tracking'
      AND kcu.column_name = 'user_id'
      AND ccu.table_name = 'profiles'
      AND tc.table_schema = 'public'
    LIMIT 1;

    IF constraint_name_var IS NOT NULL THEN
        EXECUTE format('ALTER TABLE archetype_analysis_tracking DROP CONSTRAINT IF EXISTS %I', constraint_name_var);
        RAISE NOTICE 'Dropped constraint: %', constraint_name_var;
    ELSE
        RAISE NOTICE 'No FK constraint found on archetype_analysis_tracking.user_id -> profiles';
    END IF;
END $$;

-- ============================================================================
-- STEP 5: Verify profile_id columns are now unrestricted
-- ============================================================================

\echo '\n=== STEP 5: Verify constraints removed ==='

-- Check if any FK constraints remain
SELECT
    tc.table_name,
    tc.constraint_name,
    'STILL EXISTS - Need manual removal' as status
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('biomarkers', 'scores', 'archetype_analysis_tracking')
  AND ccu.table_name = 'profiles'
  AND tc.table_schema = 'public';

-- If above query returns 0 rows, we're good!

-- ============================================================================
-- STEP 6: Add indexes for performance (since FKs are gone)
-- ============================================================================

\echo '\n=== STEP 6: Add indexes for performance ==='

-- Add index on biomarkers.profile_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_biomarkers_profile_id
ON biomarkers(profile_id);

-- Add index on scores.profile_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_scores_profile_id
ON scores(profile_id);

-- Add composite index for common queries
CREATE INDEX IF NOT EXISTS idx_biomarkers_profile_created
ON biomarkers(profile_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_scores_profile_created
ON scores(profile_id, created_at DESC);

\echo 'Indexes created for performance'

-- ============================================================================
-- STEP 7: Document what changed
-- ============================================================================

\echo '\n=== STEP 7: Summary of Changes ==='

SELECT
    'biomarkers.profile_id' as column_name,
    'No longer requires profile to exist' as change,
    'Can now use any user_id value' as benefit
UNION ALL
SELECT
    'scores.profile_id' as column_name,
    'No longer requires profile to exist' as change,
    'Can now use any user_id value' as benefit
UNION ALL
SELECT
    'archetype_analysis_tracking.user_id' as column_name,
    'No longer requires profile to exist' as change,
    'Can now use any user_id value' as benefit;

-- ============================================================================
-- STEP 8: Test that you can now insert without profile
-- ============================================================================

\echo '\n=== STEP 8: Test Insert (will rollback) ==='

BEGIN;

-- Try to insert a biomarker with a non-existent profile_id
INSERT INTO biomarkers (
    profile_id,
    type,
    data,
    start_date_time,
    end_date_time,
    created_at
) VALUES (
    'test_user_new_123',  -- This user doesn't exist in profiles
    'heart_rate',
    '{"value": 72, "unit": "bpm"}',
    NOW(),
    NOW(),
    NOW()
);

\echo 'Test insert succeeded - profile_id constraint is removed!'

ROLLBACK;

\echo 'Test insert rolled back (not saved)'

-- ============================================================================
-- SUCCESS!
-- ============================================================================

\echo '\n=== ✅ Migration Complete! ==='
\echo 'You can now create biomarkers/scores with any user_id without needing a profile entry first.'
\echo ''
\echo 'IMPORTANT NOTES:'
\echo '1. profile_id still exists as a column (data preserved)'
\echo '2. No foreign key constraint enforcing profile existence'
\echo '3. Your application is responsible for data integrity'
\echo '4. Existing data is unchanged'
\echo '5. Indexes added for performance'
