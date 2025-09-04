-- Migration: Add Time Blocks Normalization
-- Purpose: Separate time block metadata from individual tasks for better data organization
-- Date: 2025-09-03

-- ===================================================================
-- 1. Create time_blocks table
-- ===================================================================

CREATE TABLE IF NOT EXISTS time_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Links to the original analysis
    analysis_result_id UUID NOT NULL,
    profile_id TEXT NOT NULL,
    
    -- Time block identification
    block_title VARCHAR(255) NOT NULL,
    time_range VARCHAR(100),  -- e.g., "6:00-7:00 AM"
    purpose TEXT,  -- e.g., "Foundation Setting and Energy Building"
    
    -- Rich contextual metadata
    why_it_matters TEXT,
    connection_to_insights TEXT,
    health_data_integration TEXT,
    
    -- Organization
    block_order INTEGER NOT NULL DEFAULT 1,
    
    -- Archetype and plan info
    archetype VARCHAR(100),
    plan_type VARCHAR(50) DEFAULT 'routine',
    
    -- Timestamps
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fk_time_blocks_analysis 
        FOREIGN KEY (analysis_result_id) 
        REFERENCES holistic_analysis_results(id) 
        ON DELETE CASCADE,
    
    -- Ensure unique time blocks per analysis
    CONSTRAINT unique_time_block_per_analysis 
        UNIQUE (analysis_result_id, block_title)
);

-- ===================================================================
-- 2. Add time_block_id foreign key to plan_items
-- ===================================================================

-- Add the foreign key column
ALTER TABLE plan_items 
ADD COLUMN IF NOT EXISTS time_block_id UUID REFERENCES time_blocks(id) ON DELETE SET NULL;

-- ===================================================================
-- 3. Create indexes for performance
-- ===================================================================

-- Index for time block queries
CREATE INDEX IF NOT EXISTS idx_time_blocks_analysis_result 
    ON time_blocks(analysis_result_id);

CREATE INDEX IF NOT EXISTS idx_time_blocks_profile 
    ON time_blocks(profile_id);

CREATE INDEX IF NOT EXISTS idx_time_blocks_order 
    ON time_blocks(analysis_result_id, block_order);

-- Index for plan_items to time_blocks relationship
CREATE INDEX IF NOT EXISTS idx_plan_items_time_block 
    ON plan_items(time_block_id);

-- Combined index for efficient dashboard queries
CREATE INDEX IF NOT EXISTS idx_plan_items_time_block_order 
    ON plan_items(time_block_id, task_order_in_block);

-- ===================================================================
-- 4. Create database function for complete routine retrieval
-- ===================================================================

CREATE OR REPLACE FUNCTION get_complete_routine_plan(
    p_analysis_result_id UUID,
    p_profile_id TEXT DEFAULT NULL
)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    result JSON;
BEGIN
    -- Build the complete routine plan with time blocks and tasks
    SELECT json_build_object(
        'analysis_id', p_analysis_result_id,
        'profile_id', COALESCE(p_profile_id, tb.profile_id),
        'archetype', tb.archetype,
        'time_blocks', json_agg(
            json_build_object(
                'id', tb.id,
                'title', tb.block_title,
                'time_range', tb.time_range,
                'purpose', tb.purpose,
                'why_it_matters', tb.why_it_matters,
                'connection_to_insights', tb.connection_to_insights,
                'health_data_integration', tb.health_data_integration,
                'block_order', tb.block_order,
                'tasks', tb.tasks
            ) ORDER BY tb.block_order
        )
    ) INTO result
    FROM (
        SELECT 
            tb.id,
            tb.block_title,
            tb.time_range,
            tb.purpose,
            tb.why_it_matters,
            tb.connection_to_insights,
            tb.health_data_integration,
            tb.block_order,
            tb.archetype,
            tb.profile_id,
            tb.analysis_result_id,
            tb.plan_type,
            tb.extracted_at,
            tb.created_at,
            tb.updated_at,
            COALESCE(
                json_agg(
                    json_build_object(
                        'id', pi.id,
                        'item_id', pi.item_id,
                        'title', pi.title,
                        'description', pi.description,
                        'scheduled_time', pi.scheduled_time,
                        'scheduled_end_time', pi.scheduled_end_time,
                        'estimated_duration_minutes', pi.estimated_duration_minutes,
                        'task_type', pi.task_type,
                        'priority_level', pi.priority_level,
                        'is_trackable', pi.is_trackable,
                        'task_order', pi.task_order_in_block
                    ) ORDER BY pi.task_order_in_block
                ) FILTER (WHERE pi.id IS NOT NULL),
                '[]'::json
            ) as tasks
        FROM time_blocks tb
        LEFT JOIN plan_items pi ON tb.id = pi.time_block_id
        WHERE tb.analysis_result_id = p_analysis_result_id
        AND (p_profile_id IS NULL OR tb.profile_id = p_profile_id)
        GROUP BY tb.id, tb.block_title, tb.time_range, tb.purpose, 
                 tb.why_it_matters, tb.connection_to_insights, 
                 tb.health_data_integration, tb.block_order, tb.archetype, 
                 tb.profile_id, tb.analysis_result_id, tb.plan_type, 
                 tb.extracted_at, tb.created_at, tb.updated_at
    ) tb;
    
    RETURN result;
END;
$$;

-- ===================================================================
-- 5. Create function for dashboard routine queries
-- ===================================================================

CREATE OR REPLACE FUNCTION get_user_routine_dashboard(
    p_profile_id TEXT,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    latest_analysis_id UUID;
    result JSON;
BEGIN
    -- Get the latest routine plan analysis for the user
    SELECT id INTO latest_analysis_id
    FROM holistic_analysis_results
    WHERE user_id = p_profile_id 
    AND analysis_type = 'routine_plan'
    ORDER BY created_at DESC
    LIMIT 1;
    
    IF latest_analysis_id IS NULL THEN
        RETURN json_build_object(
            'error', 'No routine plan found',
            'profile_id', p_profile_id,
            'date', p_date
        );
    END IF;
    
    -- Get the complete routine plan
    SELECT get_complete_routine_plan(latest_analysis_id, p_profile_id) INTO result;
    
    -- Add calendar selection status for the date
    result := result || json_build_object(
        'date', p_date,
        'calendar_selections', (
            SELECT COALESCE(json_agg(
                json_build_object(
                    'plan_item_id', cs.plan_item_id,
                    'selected_for_calendar', cs.selected_for_calendar,
                    'selection_timestamp', cs.selection_timestamp,
                    'calendar_notes', cs.calendar_notes
                )
            ), '[]'::json)
            FROM calendar_selections cs
            JOIN plan_items pi ON cs.plan_item_id = pi.id
            WHERE pi.analysis_result_id = latest_analysis_id
            AND cs.profile_id = p_profile_id
            AND DATE(cs.selection_timestamp) = p_date
        )
    );
    
    RETURN result;
END;
$$;

-- ===================================================================
-- 6. Add RLS (Row Level Security) policies
-- ===================================================================

-- Enable RLS on time_blocks table
ALTER TABLE time_blocks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own time blocks
CREATE POLICY "Users can access own time blocks" ON time_blocks
    FOR ALL 
    USING (profile_id = auth.jwt() ->> 'sub' OR profile_id = current_user);

-- Policy: Service role can access all time blocks
CREATE POLICY "Service role can access all time blocks" ON time_blocks
    FOR ALL 
    TO service_role
    USING (true);

-- ===================================================================
-- 7. Add helpful comments
-- ===================================================================

COMMENT ON TABLE time_blocks IS 'Stores time block metadata with rich contextual information from routine plans';
COMMENT ON COLUMN time_blocks.why_it_matters IS 'Explanation of why this time block is important for the user';
COMMENT ON COLUMN time_blocks.connection_to_insights IS 'How this time block connects to user health insights and data';
COMMENT ON COLUMN time_blocks.health_data_integration IS 'Specific health metrics and data this time block targets';

COMMENT ON FUNCTION get_complete_routine_plan(UUID, TEXT) IS 'Retrieves a complete routine plan with time blocks and associated tasks';
COMMENT ON FUNCTION get_user_routine_dashboard(TEXT, DATE) IS 'Gets user routine for dashboard with calendar selection status';

-- ===================================================================
-- 8. Sample query examples (for reference)
-- ===================================================================

/*
-- Get complete routine plan for user
SELECT get_user_routine_dashboard('35pDPUIfAoRl2Y700bFkxPKYjjf2', '2025-09-02');

-- Get time blocks with tasks for specific analysis
SELECT 
    tb.block_title,
    tb.time_range,
    tb.why_it_matters,
    json_agg(
        json_build_object(
            'title', pi.title,
            'scheduled_time', pi.scheduled_time,
            'task_type', pi.task_type
        ) ORDER BY pi.task_order_in_block
    ) as tasks
FROM time_blocks tb
LEFT JOIN plan_items pi ON tb.id = pi.time_block_id
WHERE tb.analysis_result_id = '1e5c8d71-6f69-46be-8728-74fc7952e66a'
GROUP BY tb.id, tb.block_title, tb.time_range, tb.why_it_matters, tb.block_order
ORDER BY tb.block_order;

-- Check migration success
SELECT 
    'time_blocks' as table_name,
    COUNT(*) as row_count
FROM time_blocks
UNION ALL
SELECT 
    'plan_items_with_time_block_id' as table_name,
    COUNT(*) as row_count  
FROM plan_items 
WHERE time_block_id IS NOT NULL;
*/