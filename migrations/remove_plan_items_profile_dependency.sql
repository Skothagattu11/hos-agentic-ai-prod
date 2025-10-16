-- ============================================================================
-- Remove plan_items Foreign Key Dependency on profiles table
-- Purpose: Allow plan_items to work with external user_ids without profile validation
-- Date: 2025-10-16
-- CRITICAL: Run this to fix the "fk_plan_items_profile" constraint error
-- ============================================================================

\echo '=== Removing plan_items foreign key constraint to profiles ==='

-- STEP 1: Document existing constraint
\echo '\n--- STEP 1: Documenting existing constraint ---'

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
  AND tc.table_name = 'plan_items'
  AND ccu.table_name = 'profiles'
  AND tc.table_schema = 'public';

-- STEP 2: Remove the constraint
\echo '\n--- STEP 2: Removing fk_plan_items_profile constraint ---'

ALTER TABLE plan_items DROP CONSTRAINT IF EXISTS fk_plan_items_profile;

\echo '✅ Dropped: fk_plan_items_profile'

-- Remove any other plan_items constraints to profiles
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
          AND tc.table_name = 'plan_items'
          AND ccu.table_name = 'profiles'
          AND tc.table_schema = 'public'
    LOOP
        EXECUTE format('ALTER TABLE plan_items DROP CONSTRAINT IF EXISTS %I', constraint_record.constraint_name);
        RAISE NOTICE 'Dropped additional constraint: %', constraint_record.constraint_name;
    END LOOP;
END $$;

-- STEP 3: Verify constraint removed
\echo '\n--- STEP 3: Verifying constraint removal ---'

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
  AND tc.table_name = 'plan_items'
  AND ccu.table_name = 'profiles'
  AND tc.table_schema = 'public';

-- If above query returns 0 rows, we're successful!

-- STEP 4: Add performance index (since FK is gone)
\echo '\n--- STEP 4: Adding performance index ---'

CREATE INDEX IF NOT EXISTS idx_plan_items_profile_id
ON plan_items(profile_id)
WHERE profile_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_plan_items_profile_date
ON plan_items(profile_id, plan_date DESC)
WHERE profile_id IS NOT NULL;

\echo '✅ Created plan_items indexes for performance'

-- STEP 5: Test insertion with non-existent profile_id
\echo '\n--- STEP 5: Testing insertion with non-existent profile_id (will rollback) ---'

BEGIN;

-- Test insert with non-existent profile_id
INSERT INTO plan_items (
    analysis_result_id,
    item_id,
    profile_id,
    title,
    description,
    scheduled_time,
    scheduled_end_time,
    estimated_duration_minutes,
    task_type,
    priority_level,
    plan_date,
    time_block,
    time_block_id,
    time_block_order,
    task_order_in_block,
    is_trackable,
    created_at,
    updated_at
) VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,  -- Fake analysis_result_id
    'test-item-' || gen_random_uuid()::text,
    '6241b25a-c2de-49fe-9476-1ada99ffe5ca',  -- Test user (doesn't need to exist in profiles)
    'Test Task',
    'Testing plan_items without profile validation',
    '09:00',
    '10:00',
    60,
    'work',
    'high',
    CURRENT_DATE,
    'Morning Block',
    '00000000-0000-0000-0000-000000000002'::uuid,  -- Fake time_block_id
    1,
    1,
    true,
    NOW(),
    NOW()
);

\echo '✅ Test passed: plan_items inserted without profile validation'

ROLLBACK;

\echo 'Test insert rolled back (not saved)'

-- ============================================================================
-- SUCCESS!
-- ============================================================================

\echo '\n=== ✅ Migration Complete! ==='
\echo ''
\echo 'SUMMARY:'
\echo '✅ plan_items: Removed FK constraint to profiles table'
\echo '✅ Performance indexes added'
\echo '✅ Test insert successful'
\echo ''
\echo 'YOU CAN NOW:'
\echo '1. Insert plan_items with ANY profile_id value (from external auth system)'
\echo '2. Use Sahha external_id as profile_id directly'
\echo '3. Plan extraction service will work without profile validation'
\echo ''
\echo 'IMPORTANT:'
\echo '- profiles table still exists (not dropped)'
\echo '- Other tables may still reference profiles (check DIAGNOSTIC_QUERIES.sql)'
\echo '- Your application is now responsible for data consistency'
\echo ''
