-- Fix Database Function GROUP BY Error
-- Date: 2025-09-03

-- ===================================================================
-- 1. Fix the get_complete_routine_plan function GROUP BY clause
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
        GROUP BY 
            tb.id, 
            tb.block_title, 
            tb.time_range, 
            tb.purpose, 
            tb.why_it_matters, 
            tb.connection_to_insights, 
            tb.health_data_integration, 
            tb.block_order, 
            tb.archetype, 
            tb.profile_id
    ) tb;
    
    RETURN result;
END;
$$;

-- ===================================================================
-- 2. Fix the get_user_routine_dashboard function GROUP BY clause
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
-- 3. Add a simple test function to verify the fix
-- ===================================================================

CREATE OR REPLACE FUNCTION test_routine_functions()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    test_result JSON;
    analysis_id UUID := '1e5c8d71-6f69-46be-8728-74fc7952e66a';
    profile_id TEXT := '35pDPUIfAoRl2Y700bFkxPKYjjf2';
BEGIN
    -- Test the complete routine plan function
    SELECT get_complete_routine_plan(analysis_id, profile_id) INTO test_result;
    
    RETURN json_build_object(
        'status', 'success',
        'test_analysis_id', analysis_id,
        'test_profile_id', profile_id,
        'result_sample', json_build_object(
            'has_time_blocks', test_result ? 'time_blocks',
            'time_blocks_count', json_array_length(test_result -> 'time_blocks')
        )
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'status', 'error',
            'error_message', SQLERRM,
            'error_code', SQLSTATE
        );
END;
$$;

COMMENT ON FUNCTION get_complete_routine_plan(UUID, TEXT) IS 'Fixed version - retrieves complete routine plan with proper GROUP BY clause';
COMMENT ON FUNCTION get_user_routine_dashboard(TEXT, DATE) IS 'Fixed version - gets user routine dashboard with proper GROUP BY clause';
COMMENT ON FUNCTION test_routine_functions() IS 'Test function to verify database function fixes';