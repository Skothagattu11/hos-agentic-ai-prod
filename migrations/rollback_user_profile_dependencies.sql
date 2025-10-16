-- ============================================================================
-- ROLLBACK: Restore User and Profile Table Dependencies
-- Purpose: Restore FK constraints if needed (emergency rollback)
-- Date: 2025-10-16
-- WARNING: This will fail if you have data with non-existent users/profiles!
-- ============================================================================

\echo '=== ⚠️  ROLLBACK SCRIPT - Restoring FK Constraints ==='
\echo 'WARNING: This will fail if data references non-existent users/profiles!'
\echo ''

-- ============================================================================
-- STEP 1: Check for orphaned data
-- ============================================================================

\echo '=== STEP 1: Checking for orphaned data ==='

-- Check biomarkers with non-existent profiles
SELECT COUNT(*) as orphaned_biomarkers_count
FROM biomarkers b
LEFT JOIN profiles p ON b.profile_id = p.id
WHERE b.profile_id IS NOT NULL
  AND p.id IS NULL;

-- Check scores with non-existent profiles
SELECT COUNT(*) as orphaned_scores_count
FROM scores s
LEFT JOIN profiles p ON s.profile_id = p.id
WHERE s.profile_id IS NOT NULL
  AND p.id IS NULL;

\echo 'If counts above are > 0, you have orphaned data and CANNOT restore FKs!'

-- ============================================================================
-- STEP 2: Drop indexes created during migration
-- ============================================================================

\echo '\n=== STEP 2: Dropping indexes created during decoupling ==='

DROP INDEX IF EXISTS idx_biomarkers_profile_id;
DROP INDEX IF EXISTS idx_biomarkers_user_id;
DROP INDEX IF EXISTS idx_biomarkers_profile_created;
DROP INDEX IF EXISTS idx_biomarkers_profile_type;
\echo 'Dropped biomarkers indexes'

DROP INDEX IF EXISTS idx_scores_profile_id;
DROP INDEX IF EXISTS idx_scores_user_id;
DROP INDEX IF EXISTS idx_scores_profile_created;
DROP INDEX IF EXISTS idx_scores_profile_type;
\echo 'Dropped scores indexes'

DROP INDEX IF EXISTS idx_archetype_tracking_user_id;
DROP INDEX IF EXISTS idx_archetype_tracking_user_archetype;
DROP INDEX IF EXISTS idx_archetype_tracking_user_type;
\echo 'Dropped archetype_analysis_tracking indexes'

-- ============================================================================
-- STEP 3: Restore biomarkers FK constraints
-- ============================================================================

\echo '\n=== STEP 3: Restoring biomarkers foreign key constraints ==='

-- Restore: biomarkers.profile_id → profiles.id (NO ACTION)
ALTER TABLE biomarkers
ADD CONSTRAINT biomarkers_profile_id_fkey
FOREIGN KEY (profile_id) REFERENCES profiles(id)
ON UPDATE NO ACTION ON DELETE NO ACTION;
\echo 'Restored: biomarkers_profile_id_fkey'

-- Restore: biomarkers.profile_id → profiles.id (CASCADE)
ALTER TABLE biomarkers
ADD CONSTRAINT fk_biomarkers_profile
FOREIGN KEY (profile_id) REFERENCES profiles(id)
ON UPDATE NO ACTION ON DELETE CASCADE;
\echo 'Restored: fk_biomarkers_profile'

-- Restore: biomarkers.user_id → users.id (CASCADE)
ALTER TABLE biomarkers
ADD CONSTRAINT fk_biomarkers_user
FOREIGN KEY (user_id) REFERENCES users(id)
ON UPDATE NO ACTION ON DELETE CASCADE;
\echo 'Restored: fk_biomarkers_user'

-- ============================================================================
-- STEP 4: Restore scores FK constraints
-- ============================================================================

\echo '\n=== STEP 4: Restoring scores foreign key constraints ==='

-- Restore: scores.profile_id → profiles.id (NO ACTION)
ALTER TABLE scores
ADD CONSTRAINT scores_profile_id_fkey
FOREIGN KEY (profile_id) REFERENCES profiles(id)
ON UPDATE NO ACTION ON DELETE NO ACTION;
\echo 'Restored: scores_profile_id_fkey'

-- Restore: scores.profile_id → profiles.id (CASCADE)
ALTER TABLE scores
ADD CONSTRAINT fk_scores_profile
FOREIGN KEY (profile_id) REFERENCES profiles(id)
ON UPDATE NO ACTION ON DELETE CASCADE;
\echo 'Restored: fk_scores_profile'

-- Restore: scores.user_id → users.id (CASCADE)
ALTER TABLE scores
ADD CONSTRAINT fk_scores_user
FOREIGN KEY (user_id) REFERENCES users(id)
ON UPDATE NO ACTION ON DELETE CASCADE;
\echo 'Restored: fk_scores_user'

-- ============================================================================
-- STEP 5: Verify constraints restored
-- ============================================================================

\echo '\n=== STEP 5: Verifying FK constraints restored ==='

SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name as references_table,
    rc.delete_rule,
    '✅ RESTORED' as status
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('biomarkers', 'scores')
  AND ccu.table_name IN ('profiles', 'users')
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name;

-- ============================================================================
-- SUCCESS!
-- ============================================================================

\echo '\n=== ✅ Rollback Complete! ==='
\echo ''
\echo 'SUMMARY:'
\echo '✅ biomarkers: FK constraints restored to profiles and users'
\echo '✅ scores: FK constraints restored to profiles and users'
\echo '✅ System back to original state'
\echo ''
\echo 'IMPORTANT:'
\echo '- You MUST create profiles before inserting biomarkers/scores'
\echo '- Sahha integration will require profile creation step'
\echo '- Database will enforce referential integrity again'
