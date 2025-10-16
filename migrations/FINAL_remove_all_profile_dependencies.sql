-- ============================================================================
-- FINAL: Remove ALL Profile/User Dependencies (Complete Decoupling)
-- Purpose: Remove ALL foreign key constraints to profiles/users tables
-- Date: 2025-10-16
-- Author: System Migration
-- ============================================================================
-- TABLES AFFECTED:
-- 1. biomarkers
-- 2. scores
-- 3. archetype_analysis_tracking
-- 4. plan_items
-- 5. task_checkins
-- 6. daily_journals
-- 7. time_blocks (if exists)
-- 8. calendar_selections
-- ============================================================================

\echo '=========================================================================='
\echo 'FINAL MIGRATION: Remove ALL Profile/User Table Dependencies'
\echo '=========================================================================='
\echo ''

-- ============================================================================
-- STEP 1: Document ALL existing constraints
-- ============================================================================

\echo '=== STEP 1: Documenting all existing FK constraints to profiles/users ==='
\echo ''

SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name as references_table,
    rc.delete_rule,
    '⚠️ Will be removed' as status
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_name IN ('profiles', 'users')
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name;

-- ============================================================================
-- STEP 2: Remove FK constraints from biomarkers
-- ============================================================================

\echo ''
\echo '=== STEP 2: Removing biomarkers FK constraints ==='

ALTER TABLE biomarkers DROP CONSTRAINT IF EXISTS biomarkers_profile_id_fkey CASCADE;
ALTER TABLE biomarkers DROP CONSTRAINT IF EXISTS fk_biomarkers_profile CASCADE;
ALTER TABLE biomarkers DROP CONSTRAINT IF EXISTS fk_biomarkers_user CASCADE;

\echo '✅ biomarkers: All FK constraints dropped'

-- ============================================================================
-- STEP 3: Remove FK constraints from scores
-- ============================================================================

\echo ''
\echo '=== STEP 3: Removing scores FK constraints ==='

ALTER TABLE scores DROP CONSTRAINT IF EXISTS scores_profile_id_fkey CASCADE;
ALTER TABLE scores DROP CONSTRAINT IF EXISTS fk_scores_profile CASCADE;
ALTER TABLE scores DROP CONSTRAINT IF EXISTS fk_scores_user CASCADE;

\echo '✅ scores: All FK constraints dropped'

-- ============================================================================
-- STEP 4: Remove FK constraints from archetype_analysis_tracking
-- ============================================================================

\echo ''
\echo '=== STEP 4: Removing archetype_analysis_tracking FK constraints ==='

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
        EXECUTE format('ALTER TABLE archetype_analysis_tracking DROP CONSTRAINT IF EXISTS %I CASCADE', constraint_record.constraint_name);
        RAISE NOTICE 'Dropped: %', constraint_record.constraint_name;
    END LOOP;
END $$;

\echo '✅ archetype_analysis_tracking: All FK constraints dropped'

-- ============================================================================
-- STEP 5: Remove FK constraints from plan_items
-- ============================================================================

\echo ''
\echo '=== STEP 5: Removing plan_items FK constraints ==='

ALTER TABLE plan_items DROP CONSTRAINT IF EXISTS fk_plan_items_profile CASCADE;
ALTER TABLE plan_items DROP CONSTRAINT IF EXISTS plan_items_profile_id_fkey CASCADE;

\echo '✅ plan_items: All FK constraints dropped'

-- ============================================================================
-- STEP 6: Remove FK constraints from task_checkins
-- ============================================================================

\echo ''
\echo '=== STEP 6: Removing task_checkins FK constraints ==='

ALTER TABLE task_checkins DROP CONSTRAINT IF EXISTS fk_task_checkins_profile CASCADE;
ALTER TABLE task_checkins DROP CONSTRAINT IF EXISTS task_checkins_profile_id_fkey CASCADE;

\echo '✅ task_checkins: All FK constraints dropped'

-- ============================================================================
-- STEP 7: Remove FK constraints from daily_journals
-- ============================================================================

\echo ''
\echo '=== STEP 7: Removing daily_journals FK constraints ==='

ALTER TABLE daily_journals DROP CONSTRAINT IF EXISTS fk_daily_journals_profile CASCADE;
ALTER TABLE daily_journals DROP CONSTRAINT IF EXISTS daily_journals_profile_id_fkey CASCADE;

\echo '✅ daily_journals: All FK constraints dropped'

-- ============================================================================
-- STEP 8: Remove FK constraints from time_blocks (if exists)
-- ============================================================================

\echo ''
\echo '=== STEP 8: Removing time_blocks FK constraints (if table exists) ==='

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'time_blocks' AND table_schema = 'public') THEN
        EXECUTE 'ALTER TABLE time_blocks DROP CONSTRAINT IF EXISTS fk_time_blocks_profile CASCADE';
        EXECUTE 'ALTER TABLE time_blocks DROP CONSTRAINT IF EXISTS time_blocks_profile_id_fkey CASCADE';
        RAISE NOTICE '✅ time_blocks: All FK constraints dropped';
    ELSE
        RAISE NOTICE 'ℹ️  time_blocks table does not exist, skipping';
    END IF;
END $$;

-- ============================================================================
-- STEP 9: Remove FK constraints from calendar_selections
-- ============================================================================

\echo ''
\echo '=== STEP 9: Removing calendar_selections FK constraints ==='

ALTER TABLE calendar_selections DROP CONSTRAINT IF EXISTS fk_calendar_selections_profile CASCADE;
ALTER TABLE calendar_selections DROP CONSTRAINT IF EXISTS calendar_selections_profile_id_fkey CASCADE;

\echo '✅ calendar_selections: All FK constraints dropped'

-- ============================================================================
-- STEP 10: Remove ANY remaining FK constraints to profiles/users
-- ============================================================================

\echo ''
\echo '=== STEP 10: Removing any remaining FK constraints to profiles/users ==='

DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    FOR constraint_record IN
        SELECT DISTINCT
            tc.table_name,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_name IN ('profiles', 'users')
          AND tc.table_schema = 'public'
    LOOP
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I CASCADE',
            constraint_record.table_name,
            constraint_record.constraint_name);
        RAISE NOTICE 'Dropped: %.%', constraint_record.table_name, constraint_record.constraint_name;
    END LOOP;
END $$;

\echo '✅ All remaining FK constraints dropped'

-- ============================================================================
-- STEP 11: Verify ALL constraints removed
-- ============================================================================

\echo ''
\echo '=== STEP 11: Verifying NO FK constraints remain to profiles/users ==='
\echo ''

DO $$
DECLARE
    remaining_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO remaining_count
    FROM information_schema.table_constraints tc
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_name IN ('profiles', 'users')
      AND tc.table_schema = 'public';

    IF remaining_count > 0 THEN
        RAISE EXCEPTION '⚠️ ERROR: % FK constraints still exist to profiles/users!', remaining_count;
    ELSE
        RAISE NOTICE '✅ SUCCESS: NO FK constraints remain to profiles/users';
    END IF;
END $$;

-- ============================================================================
-- STEP 12: Add performance indexes (since FKs are gone)
-- ============================================================================

\echo ''
\echo '=== STEP 12: Adding performance indexes for all tables ==='
\echo ''

-- Biomarkers indexes
CREATE INDEX IF NOT EXISTS idx_biomarkers_profile_id ON biomarkers(profile_id) WHERE profile_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_biomarkers_user_id ON biomarkers(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_biomarkers_profile_created ON biomarkers(profile_id, created_at DESC) WHERE profile_id IS NOT NULL;
\echo '✅ biomarkers indexes created'

-- Scores indexes
CREATE INDEX IF NOT EXISTS idx_scores_profile_id ON scores(profile_id) WHERE profile_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_scores_user_id ON scores(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_scores_profile_created ON scores(profile_id, created_at DESC) WHERE profile_id IS NOT NULL;
\echo '✅ scores indexes created'

-- Archetype tracking indexes
CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_id ON archetype_analysis_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_archetype ON archetype_analysis_tracking(user_id, archetype);
\echo '✅ archetype_analysis_tracking indexes created'

-- Plan items indexes
CREATE INDEX IF NOT EXISTS idx_plan_items_profile_id ON plan_items(profile_id) WHERE profile_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_plan_items_profile_date ON plan_items(profile_id, plan_date DESC) WHERE profile_id IS NOT NULL;
\echo '✅ plan_items indexes created'

-- Task checkins indexes
CREATE INDEX IF NOT EXISTS idx_task_checkins_profile_id ON task_checkins(profile_id) WHERE profile_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_task_checkins_profile_date ON task_checkins(profile_id, planned_date DESC) WHERE profile_id IS NOT NULL;
\echo '✅ task_checkins indexes created'

-- Daily journals indexes
CREATE INDEX IF NOT EXISTS idx_daily_journals_profile_id ON daily_journals(profile_id) WHERE profile_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_daily_journals_profile_date ON daily_journals(profile_id, journal_date DESC) WHERE profile_id IS NOT NULL;
\echo '✅ daily_journals indexes created'

-- Time blocks indexes (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'time_blocks' AND table_schema = 'public') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_time_blocks_profile_id ON time_blocks(profile_id) WHERE profile_id IS NOT NULL';
        RAISE NOTICE '✅ time_blocks indexes created';
    END IF;
END $$;

-- Calendar selections indexes
CREATE INDEX IF NOT EXISTS idx_calendar_selections_profile_id ON calendar_selections(profile_id) WHERE profile_id IS NOT NULL;
\echo '✅ calendar_selections indexes created'

-- ============================================================================
-- STEP 13: Test insertion with non-existent profile_id (will rollback)
-- ============================================================================

\echo ''
\echo '=== STEP 13: Testing insertions with non-existent profile_id ==='
\echo ''

BEGIN;

-- Test 1: biomarker insert
INSERT INTO biomarkers (profile_id, user_id, type, data, start_date_time, end_date_time, created_at)
VALUES ('test_user_999', 'a0000000-0000-0000-0000-000000000999'::uuid, 'heart_rate', '{"value": 72}', NOW(), NOW(), NOW());
\echo '✅ Test 1: biomarker inserted without profile validation'

-- Test 2: score insert
INSERT INTO scores (profile_id, user_id, type, score, score_date_time, created_at)
VALUES ('test_user_999', 'a0000000-0000-0000-0000-000000000999'::uuid, 'sleep', 85.5, NOW(), NOW());
\echo '✅ Test 2: score inserted without profile validation'

-- Test 3: plan_item insert
INSERT INTO plan_items (analysis_result_id, item_id, profile_id, title, description, scheduled_time, task_type, plan_date, time_block, is_trackable, created_at, updated_at)
VALUES ('00000000-0000-0000-0000-000000000999'::uuid, 'test-task-1', 'test_user_999', 'Test Task', 'Testing', '09:00', 'work', CURRENT_DATE, 'Morning', true, NOW(), NOW());
\echo '✅ Test 3: plan_item inserted without profile validation'

-- Test 4: task_checkin insert
INSERT INTO task_checkins (profile_id, plan_item_id, analysis_result_id, completion_status, planned_date, created_at)
VALUES ('test_user_999', '00000000-0000-0000-0000-000000000998'::uuid, '00000000-0000-0000-0000-000000000999'::uuid, 'completed', CURRENT_DATE, NOW());
\echo '✅ Test 4: task_checkin inserted without profile validation'

-- Test 5: daily_journal insert
INSERT INTO daily_journals (profile_id, journal_date, energy_level, mood_rating, completed_at)
VALUES ('test_user_999', CURRENT_DATE, 4, 4, NOW());
\echo '✅ Test 5: daily_journal inserted without profile validation'

ROLLBACK;

\echo ''
\echo 'All test inserts rolled back (not saved)'

-- ============================================================================
-- SUCCESS SUMMARY
-- ============================================================================

\echo ''
\echo '=========================================================================='
\echo '✅ MIGRATION COMPLETE - ALL PROFILE/USER DEPENDENCIES REMOVED'
\echo '=========================================================================='
\echo ''
\echo 'TABLES DECOUPLED:'
\echo '  ✅ biomarkers'
\echo '  ✅ scores'
\echo '  ✅ archetype_analysis_tracking'
\echo '  ✅ plan_items'
\echo '  ✅ task_checkins'
\echo '  ✅ daily_journals'
\echo '  ✅ time_blocks (if exists)'
\echo '  ✅ calendar_selections'
\echo ''
\echo 'CHANGES MADE:'
\echo '  ✅ All foreign key constraints to profiles/users removed'
\echo '  ✅ Performance indexes added for all profile_id/user_id columns'
\echo '  ✅ Test insertions successful (rolled back)'
\echo ''
\echo 'YOU CAN NOW:'
\echo '  1. Use ANY user_id/profile_id from your external auth system'
\echo '  2. Insert data without creating profiles first'
\echo '  3. Sahha external_id can be used directly as profile_id'
\echo '  4. No validation against profiles/users tables'
\echo ''
\echo 'IMPORTANT NOTES:'
\echo '  - profiles and users tables still exist (not dropped)'
\echo '  - Your application is now responsible for data consistency'
\echo '  - Consider dropping profiles/users tables if no longer needed'
\echo ''
\echo 'NEXT STEPS:'
\echo '  1. Run your test scripts to verify everything works'
\echo '  2. Check for any application code that assumes FK constraints exist'
\echo '  3. Update documentation to reflect new architecture'
\echo ''
\echo '=========================================================================='
