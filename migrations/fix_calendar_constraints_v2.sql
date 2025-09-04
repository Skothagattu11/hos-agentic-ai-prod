-- Fix Calendar System - Corrected Database Constraints (v2)
-- This migration adds proper foreign keys, unique constraints, and validation rules

-- 1. Add unique constraint to prevent duplicate calendar selections
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'unique_calendar_selection'
    ) THEN
        ALTER TABLE calendar_selections 
        ADD CONSTRAINT unique_calendar_selection 
        UNIQUE (profile_id, plan_item_id);
    END IF;
END $$;

-- 2. Add foreign key constraint: calendar_selections.plan_item_id → plan_items.id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_calendar_selections_plan_item'
    ) THEN
        ALTER TABLE calendar_selections 
        ADD CONSTRAINT fk_calendar_selections_plan_item 
        FOREIGN KEY (plan_item_id) REFERENCES plan_items(id) 
        ON DELETE CASCADE;
    END IF;
END $$;

-- 3. Add foreign key constraint: plan_items.time_block_id → time_blocks.id  
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_plan_items_time_block'
    ) THEN
        ALTER TABLE plan_items 
        ADD CONSTRAINT fk_plan_items_time_block 
        FOREIGN KEY (time_block_id) REFERENCES time_blocks(id) 
        ON DELETE SET NULL;
    END IF;
END $$;

-- 4. Create indexes for better performance on calendar queries
CREATE INDEX IF NOT EXISTS idx_calendar_selections_profile_selected 
ON calendar_selections(profile_id, selected_for_calendar) 
WHERE selected_for_calendar = true;

CREATE INDEX IF NOT EXISTS idx_plan_items_time_block_lookup 
ON plan_items(profile_id, analysis_result_id, time_block_id);

CREATE INDEX IF NOT EXISTS idx_time_blocks_profile_analysis 
ON time_blocks(profile_id, analysis_result_id);

-- 5. Create validation function for time_block consistency
CREATE OR REPLACE FUNCTION validate_time_block_belongs_to_analysis(
    p_time_block_id UUID,
    p_profile_id TEXT,
    p_analysis_result_id UUID
) RETURNS BOOLEAN AS $$
BEGIN
    -- If time_block_id is NULL, it's valid
    IF p_time_block_id IS NULL THEN
        RETURN TRUE;
    END IF;
    
    -- Check if time_block belongs to the same profile and analysis
    RETURN EXISTS (
        SELECT 1 FROM time_blocks 
        WHERE id = p_time_block_id 
        AND profile_id = p_profile_id 
        AND analysis_result_id = p_analysis_result_id
    );
END;
$$ LANGUAGE plpgsql;

-- 6. Create trigger function to validate time_block assignments
CREATE OR REPLACE FUNCTION validate_time_block_assignment()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate time_block_id belongs to same profile and analysis
    IF NOT validate_time_block_belongs_to_analysis(
        NEW.time_block_id, 
        NEW.profile_id, 
        NEW.analysis_result_id
    ) THEN
        RAISE EXCEPTION 'time_block_id % does not belong to profile % and analysis %', 
            NEW.time_block_id, NEW.profile_id, NEW.analysis_result_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 7. Create the trigger (drop first if exists)
DROP TRIGGER IF EXISTS validate_plan_item_time_block ON plan_items;
CREATE TRIGGER validate_plan_item_time_block
    BEFORE INSERT OR UPDATE ON plan_items
    FOR EACH ROW
    EXECUTE FUNCTION validate_time_block_assignment();

-- 8. Function to fix orphaned time_block_ids with smart matching
CREATE OR REPLACE FUNCTION fix_orphaned_time_block_ids_smart()
RETURNS TABLE(plan_item_id UUID, old_time_block_id UUID, new_time_block_id UUID, item_title TEXT) AS $$
DECLARE
    rec RECORD;
    fixed_count INTEGER := 0;
BEGIN
    -- Find and fix plan items with orphaned time_block_ids
    FOR rec IN 
        SELECT 
            pi.id as plan_item_id,
            pi.time_block_id as old_time_block_id,
            pi.title,
            pi.time_block as time_block_name,
            pi.profile_id,
            pi.analysis_result_id,
            tb_correct.id as new_time_block_id,
            tb_correct.block_title
        FROM plan_items pi
        LEFT JOIN time_blocks tb_current ON (
            pi.time_block_id = tb_current.id 
            AND pi.profile_id = tb_current.profile_id 
            AND pi.analysis_result_id = tb_current.analysis_result_id
        )
        LEFT JOIN time_blocks tb_correct ON (
            tb_correct.profile_id = pi.profile_id 
            AND tb_correct.analysis_result_id = pi.analysis_result_id
            AND (
                -- Smart matching based on time_block name patterns
                LOWER(pi.time_block) LIKE '%morning%' AND LOWER(tb_correct.block_title) LIKE '%morning%'
                OR LOWER(pi.time_block) LIKE '%focus%' AND LOWER(tb_correct.block_title) LIKE '%focus%'
                OR LOWER(pi.time_block) LIKE '%afternoon%' AND LOWER(tb_correct.block_title) LIKE '%afternoon%'
                OR LOWER(pi.time_block) LIKE '%evening%' AND LOWER(tb_correct.block_title) LIKE '%evening%'
                OR LOWER(pi.time_block) LIKE '%wind%' AND LOWER(tb_correct.block_title) LIKE '%wind%'
            )
        )
        WHERE tb_current.id IS NULL  -- time_block is orphaned
        AND tb_correct.id IS NOT NULL -- we found a matching block
        ORDER BY pi.id
    LOOP
        -- Update the plan item with correct time_block_id
        UPDATE plan_items 
        SET time_block_id = rec.new_time_block_id
        WHERE id = rec.plan_item_id;
        
        -- Return the fix details
        plan_item_id := rec.plan_item_id;
        old_time_block_id := rec.old_time_block_id;
        new_time_block_id := rec.new_time_block_id;
        item_title := rec.title;
        
        RETURN NEXT;
        
        fixed_count := fixed_count + 1;
    END LOOP;
    
    RAISE NOTICE 'Fixed % orphaned plan items', fixed_count;
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- 9. Run the smart fix function to clean up existing data
DO $$
DECLARE
    fix_result RECORD;
    total_fixed INTEGER := 0;
BEGIN
    RAISE NOTICE 'Running smart orphaned time_block_id fixes...';
    
    FOR fix_result IN SELECT * FROM fix_orphaned_time_block_ids_smart() LOOP
        total_fixed := total_fixed + 1;
        RAISE NOTICE 'Fixed: % (%) - % → %', 
            fix_result.item_title, 
            fix_result.plan_item_id, 
            fix_result.old_time_block_id, 
            fix_result.new_time_block_id;
    END LOOP;
    
    RAISE NOTICE 'Total items fixed: %', total_fixed;
END $$;

-- 10. Add helpful comments
COMMENT ON CONSTRAINT unique_calendar_selection ON calendar_selections IS 
'Prevents duplicate calendar selections for the same user and plan item';

COMMENT ON CONSTRAINT fk_calendar_selections_plan_item ON calendar_selections IS 
'Ensures calendar selections reference valid plan items, cascades delete';

COMMENT ON CONSTRAINT fk_plan_items_time_block ON plan_items IS 
'Ensures plan items reference valid time blocks, sets NULL on delete';

COMMENT ON FUNCTION validate_time_block_belongs_to_analysis(UUID, TEXT, UUID) IS 
'Validates that a time_block_id belongs to the specified profile and analysis';

COMMENT ON FUNCTION validate_time_block_assignment() IS 
'Trigger function to prevent orphaned time_block_id assignments';

COMMENT ON FUNCTION fix_orphaned_time_block_ids_smart() IS 
'Smart function to fix existing orphaned time_block_id assignments using pattern matching';