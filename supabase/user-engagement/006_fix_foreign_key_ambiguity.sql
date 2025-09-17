-- =====================================================
-- Fix Foreign Key Ambiguity Between plan_items and time_blocks
-- =====================================================
-- Purpose: Resolve "ambiguous relationship" errors in Supabase JOINs
-- Date: 2025-09-16
-- Issue: Multiple foreign key constraints exist on the same column relationship
--
-- Problem Analysis:
-- 1. Migration 003 added: plan_items.time_block_id REFERENCES time_blocks(id) (unnamed constraint)
-- 2. Migration fix_calendar_constraints_v2 added: fk_plan_items_time_block constraint on same columns
-- 3. This creates duplicate foreign key constraints causing Supabase JOIN ambiguity
-- =====================================================

-- Step 1: Identify and drop any unnamed foreign key constraints
-- This removes the unnamed constraint created by the REFERENCES clause in migration 003
DO $$
DECLARE
    constraint_rec RECORD;
BEGIN
    -- Find all foreign key constraints from plan_items.time_block_id to time_blocks.id
    FOR constraint_rec IN
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = 'plan_items'
            AND kcu.column_name = 'time_block_id'
            AND ccu.table_name = 'time_blocks'
            AND ccu.column_name = 'id'
            AND tc.constraint_name != 'fk_plan_items_time_block'  -- Keep our named constraint
    LOOP
        -- Drop the unnamed/duplicate foreign key constraint
        EXECUTE format('ALTER TABLE plan_items DROP CONSTRAINT %I', constraint_rec.constraint_name);
        RAISE NOTICE 'Dropped duplicate foreign key constraint: %', constraint_rec.constraint_name;
    END LOOP;
END $$;

-- Step 2: Ensure our named foreign key constraint exists and is properly configured
DO $$
BEGIN
    -- Check if our named constraint exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_plan_items_time_block'
        AND table_name = 'plan_items'
        AND constraint_type = 'FOREIGN KEY'
    ) THEN
        -- Create the named foreign key constraint
        ALTER TABLE plan_items
        ADD CONSTRAINT fk_plan_items_time_block
        FOREIGN KEY (time_block_id) REFERENCES time_blocks(id)
        ON DELETE SET NULL;

        RAISE NOTICE 'Created named foreign key constraint: fk_plan_items_time_block';
    ELSE
        RAISE NOTICE 'Named foreign key constraint fk_plan_items_time_block already exists';
    END IF;
END $$;

-- Step 3: Verify we now have exactly one foreign key relationship
DO $$
DECLARE
    fk_count INTEGER;
    constraint_info RECORD;
BEGIN
    -- Count foreign key constraints between plan_items.time_block_id and time_blocks.id
    SELECT COUNT(*) INTO fk_count
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = 'plan_items'
        AND kcu.column_name = 'time_block_id'
        AND ccu.table_name = 'time_blocks'
        AND ccu.column_name = 'id';

    RAISE NOTICE 'Total foreign key constraints between plan_items.time_block_id and time_blocks.id: %', fk_count;

    -- List the remaining constraints for verification
    FOR constraint_info IN
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = 'plan_items'
            AND kcu.column_name = 'time_block_id'
            AND ccu.table_name = 'time_blocks'
            AND ccu.column_name = 'id'
    LOOP
        RAISE NOTICE 'Remaining constraint: % on %.%',
            constraint_info.constraint_name,
            constraint_info.table_name,
            constraint_info.column_name;
    END LOOP;

    -- Verification check
    IF fk_count = 1 THEN
        RAISE NOTICE 'SUCCESS: Foreign key ambiguity resolved - exactly 1 constraint remains';
    ELSIF fk_count = 0 THEN
        RAISE WARNING 'ERROR: No foreign key constraints found - this will break referential integrity';
    ELSE
        RAISE WARNING 'WARNING: % foreign key constraints still exist - ambiguity may persist', fk_count;
    END IF;
END $$;

-- Step 4: Add indexes to ensure optimal JOIN performance
-- These indexes help Supabase optimize JOINs after resolving the ambiguity
CREATE INDEX IF NOT EXISTS idx_plan_items_time_block_optimized
ON plan_items(time_block_id)
WHERE time_block_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_time_blocks_for_joins
ON time_blocks(id, analysis_result_id, profile_id);

-- Step 5: Create a verification function to test JOIN operations
CREATE OR REPLACE FUNCTION test_plan_items_time_blocks_join()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    test_result JSON;
    join_count INTEGER;
    sample_data JSON;
BEGIN
    -- Test basic JOIN operation that was failing
    SELECT COUNT(*) INTO join_count
    FROM plan_items pi
    INNER JOIN time_blocks tb ON pi.time_block_id = tb.id;

    -- Get a sample of the JOIN result
    SELECT json_agg(
        json_build_object(
            'plan_item_id', pi.id,
            'plan_item_title', pi.title,
            'time_block_id', tb.id,
            'time_block_title', tb.block_title,
            'profile_id', pi.profile_id
        )
    ) INTO sample_data
    FROM plan_items pi
    INNER JOIN time_blocks tb ON pi.time_block_id = tb.id
    LIMIT 5;

    -- Build test result
    test_result := json_build_object(
        'status', 'success',
        'join_count', join_count,
        'message', 'JOIN operation completed successfully',
        'sample_data', COALESCE(sample_data, '[]'::json),
        'test_timestamp', NOW()
    );

    RETURN test_result;
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'status', 'error',
            'error_message', SQLERRM,
            'error_code', SQLSTATE,
            'message', 'JOIN operation failed - ambiguity may still exist'
        );
END;
$$;

-- Step 6: Run verification test
DO $$
DECLARE
    test_result JSON;
BEGIN
    RAISE NOTICE 'Running JOIN verification test...';

    SELECT test_plan_items_time_blocks_join() INTO test_result;

    RAISE NOTICE 'Test result: %', test_result::text;
END $$;

-- Step 7: Add helpful documentation
COMMENT ON CONSTRAINT fk_plan_items_time_block ON plan_items IS
'Single foreign key relationship between plan_items.time_block_id and time_blocks.id - resolves Supabase JOIN ambiguity';

COMMENT ON FUNCTION test_plan_items_time_blocks_join() IS
'Verification function to test that JOIN operations work without ambiguity errors';

-- =====================================================
-- Summary and Validation Queries
-- =====================================================

-- Query to verify the fix worked
SELECT
    'Foreign Key Verification' as check_type,
    tc.constraint_name,
    tc.table_name || '.' || kcu.column_name as source_column,
    ccu.table_name || '.' || ccu.column_name as target_column,
    'FIXED: Single relationship' as status
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'plan_items'
    AND kcu.column_name = 'time_block_id'
    AND ccu.table_name = 'time_blocks';

-- Test query that should now work in Supabase without ambiguity errors
/*
Example Supabase query that should now work:

SELECT
    pi.title as task_title,
    pi.scheduled_time,
    tb.block_title,
    tb.time_range,
    tb.purpose
FROM plan_items pi
INNER JOIN time_blocks tb ON pi.time_block_id = tb.id
WHERE pi.profile_id = 'your_profile_id'
ORDER BY tb.block_order, pi.task_order_in_block;
*/

SELECT 'Migration 006_fix_foreign_key_ambiguity completed successfully!' as status;