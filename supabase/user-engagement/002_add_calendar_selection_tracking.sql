-- =====================================================================================
-- Calendar Selection Tracking Enhancement for Sprint 1 Engagement System
-- =====================================================================================
-- Purpose: Track user's calendar selection workflow:
--   1. AI generates 7 plan items
--   2. User selects subset for calendar (e.g., 3 out of 7)
--   3. User checks in on selected calendar items
--   4. Daily journal for reflection
-- =====================================================================================

-- Add calendar tracking columns to existing plan_items table
ALTER TABLE plan_items 
ADD COLUMN added_to_calendar BOOLEAN DEFAULT FALSE,
ADD COLUMN calendar_added_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN calendar_notes TEXT;

-- Create calendar_selections table for detailed tracking
CREATE TABLE calendar_selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id TEXT NOT NULL,
    plan_item_id UUID NOT NULL REFERENCES plan_items(id) ON DELETE CASCADE,
    selected_for_calendar BOOLEAN NOT NULL DEFAULT TRUE,
    selection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    calendar_notes TEXT,
    selection_metadata JSONB DEFAULT '{}',
    
    -- Constraints
    UNIQUE(profile_id, plan_item_id),  -- One selection per user per plan item
    
    -- Indexes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX idx_calendar_selections_profile_id ON calendar_selections(profile_id);
CREATE INDEX idx_calendar_selections_plan_item_id ON calendar_selections(plan_item_id);
CREATE INDEX idx_calendar_selections_timestamp ON calendar_selections(selection_timestamp);
CREATE INDEX idx_calendar_selections_profile_date ON calendar_selections(profile_id, DATE(selection_timestamp));

-- Create calendar selection summary view for analytics
CREATE VIEW calendar_selection_summary AS
SELECT 
    cs.profile_id,
    DATE(cs.selection_timestamp) as selection_date,
    COUNT(pi.id) as total_plan_items,
    COUNT(cs.id) as items_selected_for_calendar,
    COUNT(tc.id) as items_checked_in,
    ROUND(
        (COUNT(cs.id)::DECIMAL / NULLIF(COUNT(pi.id), 0)) * 100, 2
    ) as calendar_selection_rate,
    ROUND(
        (COUNT(tc.id)::DECIMAL / NULLIF(COUNT(cs.id), 0)) * 100, 2
    ) as calendar_completion_rate
FROM plan_items pi
LEFT JOIN calendar_selections cs ON pi.id = cs.plan_item_id
LEFT JOIN task_checkins tc ON pi.id = tc.plan_item_id 
    AND DATE(cs.selection_timestamp) = tc.planned_date
WHERE DATE(pi.extracted_at) = DATE(cs.selection_timestamp)
GROUP BY cs.profile_id, DATE(cs.selection_timestamp);

-- Create function to automatically update plan_items when calendar selection is made
CREATE OR REPLACE FUNCTION update_plan_item_calendar_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the plan_items table when a calendar selection is made
    UPDATE plan_items 
    SET 
        added_to_calendar = NEW.selected_for_calendar,
        calendar_added_at = NEW.selection_timestamp,
        calendar_notes = NEW.calendar_notes
    WHERE id = NEW.plan_item_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically sync calendar selections with plan_items
CREATE TRIGGER trigger_update_plan_item_calendar
    AFTER INSERT OR UPDATE ON calendar_selections
    FOR EACH ROW
    EXECUTE FUNCTION update_plan_item_calendar_status();

-- Add RLS (Row Level Security) policies for calendar_selections
ALTER TABLE calendar_selections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own calendar selections" ON calendar_selections
    FOR SELECT USING (profile_id = auth.uid()::text);

CREATE POLICY "Users can insert their own calendar selections" ON calendar_selections
    FOR INSERT WITH CHECK (profile_id = auth.uid()::text);

CREATE POLICY "Users can update their own calendar selections" ON calendar_selections
    FOR UPDATE USING (profile_id = auth.uid()::text);

CREATE POLICY "Users can delete their own calendar selections" ON calendar_selections
    FOR DELETE USING (profile_id = auth.uid()::text);

-- Create helper function for calendar workflow analytics
CREATE OR REPLACE FUNCTION get_calendar_workflow_stats(
    p_profile_id TEXT,
    p_date DATE DEFAULT CURRENT_DATE
) RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'profile_id', p_profile_id,
        'date', p_date,
        'total_plan_items', COUNT(pi.id),
        'calendar_selected', COUNT(cs.id) FILTER (WHERE cs.selected_for_calendar = true),
        'calendar_not_selected', COUNT(pi.id) - COUNT(cs.id) FILTER (WHERE cs.selected_for_calendar = true),
        'checked_in', COUNT(tc.id),
        'calendar_but_no_checkin', 
            COUNT(cs.id) FILTER (WHERE cs.selected_for_calendar = true) - COUNT(tc.id),
        'selection_rate_percent', 
            ROUND((COUNT(cs.id) FILTER (WHERE cs.selected_for_calendar = true)::DECIMAL / 
                   NULLIF(COUNT(pi.id), 0)) * 100, 1),
        'completion_rate_percent',
            ROUND((COUNT(tc.id)::DECIMAL / 
                   NULLIF(COUNT(cs.id) FILTER (WHERE cs.selected_for_calendar = true), 0)) * 100, 1)
    ) INTO result
    FROM plan_items pi
    LEFT JOIN calendar_selections cs ON pi.id = cs.plan_item_id
    LEFT JOIN task_checkins tc ON pi.id = tc.plan_item_id AND tc.planned_date = p_date
    WHERE pi.profile_id = p_profile_id 
      AND DATE(pi.extracted_at) = p_date;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Insert some sample data to demonstrate the workflow
DO $$
DECLARE
    sample_profile_id TEXT := 'demo-user-calendar-workflow';
    sample_analysis_id UUID := gen_random_uuid();
    sample_plan_item_1 UUID;
    sample_plan_item_2 UUID;
    sample_plan_item_3 UUID;
BEGIN
    -- Create sample plan items (AI generates 7 tasks)
    INSERT INTO plan_items (analysis_result_id, profile_id, item_id, title, description, time_block, scheduled_time, estimated_duration_minutes)
    VALUES 
        (sample_analysis_id, sample_profile_id, 'morning_hrv_check', '3-Minute HRV Check', 'Check readiness with HRV app', 'Morning Wake-up', '06:00:00', 3),
        (sample_analysis_id, sample_profile_id, 'morning_visualization', '5-Minute Visualization', 'Visualize daily goals', 'Morning Wake-up', '06:03:00', 5),
        (sample_analysis_id, sample_profile_id, 'outdoor_light', 'Outdoor Light Exposure', '10 minutes natural light', 'Morning Wake-up', '06:10:00', 10),
        (sample_analysis_id, sample_profile_id, 'focused_work', 'Focused Work Session', 'High-priority tasks', 'Focus Block', '09:00:00', 90),
        (sample_analysis_id, sample_profile_id, 'movement_break', 'Movement Break', 'Stretch or walk', 'Focus Block', '10:30:00', 10),
        (sample_analysis_id, sample_profile_id, 'screen_off', 'Screen-Off Time', 'No screens, light stretching', 'Evening Wind-down', '20:30:00', 15),
        (sample_analysis_id, sample_profile_id, 'breathwork', 'Mindfulness Breathwork', '10 minutes breathwork', 'Evening Wind-down', '20:45:00', 10)
    RETURNING id INTO sample_plan_item_1;

    -- Get the plan item IDs for calendar selection
    SELECT id INTO sample_plan_item_1 FROM plan_items WHERE profile_id = sample_profile_id AND item_id = 'morning_hrv_check';
    SELECT id INTO sample_plan_item_2 FROM plan_items WHERE profile_id = sample_profile_id AND item_id = 'focused_work';
    SELECT id INTO sample_plan_item_3 FROM plan_items WHERE profile_id = sample_profile_id AND item_id = 'breathwork';

    -- User selects 3 out of 7 tasks for calendar
    INSERT INTO calendar_selections (profile_id, plan_item_id, selected_for_calendar, calendar_notes)
    VALUES 
        (sample_profile_id, sample_plan_item_1, true, 'Added to morning routine'),
        (sample_profile_id, sample_plan_item_2, true, 'Important work block'),
        (sample_profile_id, sample_plan_item_3, true, 'Evening wind-down essential');

    -- User checks in on 2 out of 3 calendar items
    INSERT INTO task_checkins (profile_id, plan_item_id, completion_status, satisfaction_rating, planned_date, user_notes)
    VALUES 
        (sample_profile_id, sample_plan_item_1, 'completed', 4, CURRENT_DATE, 'HRV looked good today'),
        (sample_profile_id, sample_plan_item_2, 'partial', 3, CURRENT_DATE, 'Got distracted but made progress');
    -- Note: sample_plan_item_3 (breathwork) was added to calendar but user forgot to check in

END $$;

-- Add helpful comments
COMMENT ON TABLE calendar_selections IS 'Tracks which plan items users select to add to their calendar';
COMMENT ON COLUMN calendar_selections.selected_for_calendar IS 'TRUE if user added this task to calendar, FALSE if explicitly not selected';
COMMENT ON COLUMN calendar_selections.selection_metadata IS 'JSON field for additional selection context (calendar app used, priority set, etc.)';
COMMENT ON VIEW calendar_selection_summary IS 'Analytics view showing calendar selection and completion rates by user and date';
COMMENT ON FUNCTION get_calendar_workflow_stats IS 'Helper function to get complete calendar workflow statistics for a user and date';

-- Migration complete
SELECT 'Calendar selection tracking system created successfully!' as status;