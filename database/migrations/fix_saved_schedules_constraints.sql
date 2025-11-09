-- ============================================================================
-- Fix saved_schedules Foreign Key Constraints
-- This script checks and removes ALL foreign key constraints on user_id
-- ============================================================================

-- Step 1: Check existing constraints
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'saved_schedules'::regclass;

-- Step 2: Drop ALL foreign key constraints on saved_schedules
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'saved_schedules'::regclass
        AND contype = 'f'  -- 'f' = foreign key
    ) LOOP
        EXECUTE 'ALTER TABLE saved_schedules DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname) || ' CASCADE';
        RAISE NOTICE 'Dropped constraint: %', r.conname;
    END LOOP;
END $$;

-- Step 3: Explicitly drop the specific constraint (in case it has a different name)
ALTER TABLE saved_schedules DROP CONSTRAINT IF EXISTS fk_saved_schedules_user CASCADE;
ALTER TABLE saved_schedules DROP CONSTRAINT IF EXISTS saved_schedules_user_id_fkey CASCADE;

-- Step 4: Verify constraints are removed
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'saved_schedules'::regclass
AND contype = 'f';

-- Should return no rows if all foreign keys are removed

-- Step 5: Add a helpful comment
COMMENT ON TABLE saved_schedules IS 'Schedule storage table - FK constraints removed to support Firebase Auth IDs and flexible testing';

-- ============================================================================
-- Verification Complete
-- ============================================================================
-- If you see "Dropped constraint: ..." messages, the constraints were removed
-- If you see no foreign key constraints in the final SELECT, you are good to go!
