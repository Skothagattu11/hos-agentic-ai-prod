-- =====================================================
-- Dual Engagement System Database Schema
-- =====================================================
-- This script creates the database schema for the dual engagement system:
-- 1. plan_items - Extracts trackable tasks from existing holistic_analysis_results
-- 2. task_checkins - Tracks individual task completions
-- 3. daily_journals - Holistic daily reflection entries
-- 4. routine_templates - Template structures for plan generation

-- =====================================================
-- Plan Items Table - Extract Tasks from Existing Plans
-- =====================================================
-- This table extracts individual trackable tasks from the existing 
-- holistic_analysis_results table, making them available for check-ins
CREATE TABLE IF NOT EXISTS plan_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Reference to existing plan in holistic_analysis_results (health-agent-main DB)
    analysis_result_id UUID NOT NULL, -- References holistic_analysis_results.id
    profile_id TEXT NOT NULL, -- Denormalized for performance (references profiles.id)
    
    -- Item Identification (extracted from analysis_result JSON)
    item_id VARCHAR(100) NOT NULL, -- e.g., "morning_wake_up_hrv_check", "focus_block_work"
    time_block VARCHAR(100) NOT NULL, -- e.g., "Morning Wake-up (6:00-7:00 AM)"
    
    -- Item Details (parsed from plan content)
    title TEXT NOT NULL, -- e.g., "3-Minute HRV/Readiness Check"
    description TEXT, -- Full task description from plan
    scheduled_time TIME, -- e.g., "06:00:00"
    scheduled_end_time TIME, -- e.g., "06:03:00"
    estimated_duration_minutes INTEGER,
    
    -- Task Properties
    task_type VARCHAR(50), -- "assessment", "exercise", "nutrition", "mindfulness", "preparation"
    is_trackable BOOLEAN DEFAULT TRUE, -- Whether this appears in task check-ins
    priority_level VARCHAR(10) DEFAULT 'medium' CHECK (priority_level IN ('low', 'medium', 'high', 'critical')),
    
    -- Order within plan (for display)
    time_block_order INTEGER DEFAULT 0, -- Order of time blocks in plan
    task_order_in_block INTEGER DEFAULT 0, -- Order of tasks within time block
    
    -- Metadata
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to profiles table
    CONSTRAINT fk_plan_items_profile 
        FOREIGN KEY (profile_id) 
        REFERENCES profiles(id) 
        ON DELETE CASCADE,
    
    -- Unique task per analysis result
    CONSTRAINT unique_item_per_analysis 
        UNIQUE (analysis_result_id, item_id)
);

-- =====================================================
-- Task Check-ins Table - Granular Completion Tracking
-- =====================================================
-- This table tracks individual task completions with satisfaction ratings
CREATE TABLE IF NOT EXISTS task_checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id TEXT NOT NULL,
    
    -- Task Reference (links to plan_items table)
    plan_item_id UUID NOT NULL, -- References plan_items.id
    analysis_result_id UUID NOT NULL, -- References holistic_analysis_results.id for easier queries
    
    -- Completion Data
    completion_status VARCHAR(20) NOT NULL CHECK (completion_status IN ('completed', 'partial', 'skipped')),
    completed_at TIMESTAMP WITH TIME ZONE,
    satisfaction_rating INTEGER CHECK (satisfaction_rating BETWEEN 1 AND 5),
    
    -- Timing Analysis
    planned_date DATE NOT NULL,
    planned_time TIME,
    actual_completion_time TIMESTAMP WITH TIME ZONE,
    
    -- Optional user notes
    user_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints
    CONSTRAINT fk_task_checkins_profile 
        FOREIGN KEY (profile_id) 
        REFERENCES profiles(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_task_checkins_plan_item 
        FOREIGN KEY (plan_item_id) 
        REFERENCES plan_items(id) 
        ON DELETE CASCADE,
    
    -- Note: analysis_result_id references holistic_analysis_results in health-agent-main DB
    -- Foreign key constraint handled at application level due to cross-database reference
    
    -- One check-in per plan item per day
    CONSTRAINT unique_task_checkin_per_day 
        UNIQUE (profile_id, plan_item_id, planned_date)
);

-- =====================================================
-- Daily Journals Table - Holistic Daily Reflection
-- =====================================================
-- This table captures end-of-day holistic reflection and wellbeing data
CREATE TABLE IF NOT EXISTS daily_journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id TEXT NOT NULL,
    journal_date DATE NOT NULL,
    
    -- Overall Day Assessment (1-5 scales)
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 5),
    mood_rating INTEGER CHECK (mood_rating BETWEEN 1 AND 5),
    sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 5),
    stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 5),
    
    -- Nutrition Summary
    nutrition_satisfaction INTEGER CHECK (nutrition_satisfaction BETWEEN 1 AND 5),
    hydration_glasses INTEGER DEFAULT 0 CHECK (hydration_glasses >= 0),
    meal_timing_satisfaction INTEGER CHECK (meal_timing_satisfaction BETWEEN 1 AND 5),
    
    -- Habit Completions (general habits not tied to specific plan items)
    breathing_exercises_completed BOOLEAN DEFAULT FALSE,
    sunlight_exposure_completed BOOLEAN DEFAULT FALSE,
    mindfulness_practice_completed BOOLEAN DEFAULT FALSE,
    
    -- Reflection Fields
    what_went_well TEXT,
    what_was_challenging TEXT,
    tomorrow_intentions TEXT,
    gratitude_notes TEXT[], -- Array of gratitude items
    
    -- Voice Notes
    voice_note_url TEXT,
    voice_note_duration_seconds INTEGER CHECK (voice_note_duration_seconds > 0),
    
    -- Completion Metadata
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    time_to_complete_seconds INTEGER CHECK (time_to_complete_seconds > 0), -- Track journal efficiency
    
    -- Foreign key constraints
    CONSTRAINT fk_daily_journals_profile 
        FOREIGN KEY (profile_id) 
        REFERENCES profiles(id) 
        ON DELETE CASCADE,
    
    -- One journal per user per day
    CONSTRAINT unique_journal_per_day 
        UNIQUE (profile_id, journal_date)
);

-- =====================================================
-- Routine Templates Table - Plan Generation Templates
-- =====================================================
-- This table stores template structures used by AI agents for plan generation
CREATE TABLE IF NOT EXISTS routine_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    archetype VARCHAR(50) NOT NULL, -- 'foundation', 'peak', 'systematic', etc.
    
    -- Template structure for plan generation (used by AI agents)
    template_structure JSONB, -- Template structure used by AI agents for plan generation
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique archetype templates
    CONSTRAINT unique_archetype_template 
        UNIQUE (archetype)
);

-- =====================================================
-- Performance Indexes
-- =====================================================

-- Task check-ins indexes
CREATE INDEX idx_task_checkins_profile_date 
    ON task_checkins (profile_id, planned_date DESC);
    
CREATE INDEX idx_task_checkins_completion_status 
    ON task_checkins (profile_id, completion_status) 
    WHERE completion_status != 'skipped';

CREATE INDEX idx_task_checkins_plan_item 
    ON task_checkins (plan_item_id, planned_date DESC);

CREATE INDEX idx_task_checkins_analysis 
    ON task_checkins (analysis_result_id, planned_date DESC);
    
-- Daily journals indexes
CREATE INDEX idx_daily_journals_profile_date 
    ON daily_journals (profile_id, journal_date DESC);
    
CREATE INDEX idx_daily_journals_completion_time 
    ON daily_journals (completed_at);

-- Plan items indexes
CREATE INDEX idx_plan_items_analysis_trackable 
    ON plan_items (analysis_result_id, is_trackable) 
    WHERE is_trackable = true;

CREATE INDEX idx_plan_items_profile_date 
    ON plan_items (profile_id, extracted_at DESC);

CREATE INDEX idx_plan_items_time_order 
    ON plan_items (analysis_result_id, time_block_order, task_order_in_block);

-- Routine templates indexes
CREATE INDEX idx_routine_templates_archetype 
    ON routine_templates (archetype);

-- =====================================================
-- Row Level Security (RLS) Policies
-- =====================================================

-- RLS Policies for task_checkins
ALTER TABLE task_checkins ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own task check-ins
CREATE POLICY "Users can access own task check-ins" 
    ON task_checkins
    FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = task_checkins.profile_id 
            AND profiles.user_id::uuid = auth.uid()
        )
    );

-- Policy: Service role has full access
CREATE POLICY "Service role full access task check-ins" 
    ON task_checkins
    FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');

-- RLS Policies for daily_journals
ALTER TABLE daily_journals ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own journal data
CREATE POLICY "Users can access own journal data" 
    ON daily_journals
    FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = daily_journals.profile_id 
            AND profiles.user_id::uuid = auth.uid()
        )
    );

-- Policy: Service role has full access
CREATE POLICY "Service role full access daily journals" 
    ON daily_journals
    FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');

-- RLS Policies for plan_items
ALTER TABLE plan_items ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own plan items
CREATE POLICY "Users can access own plan items" 
    ON plan_items
    FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = plan_items.profile_id 
            AND profiles.user_id::uuid = auth.uid()
        )
    );

-- Policy: Service role has full access
CREATE POLICY "Service role full access plan items" 
    ON plan_items
    FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');

-- RLS Policies for routine_templates (read-only for users)
ALTER TABLE routine_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read routine templates" 
    ON routine_templates
    FOR SELECT 
    USING (true); -- All users can read templates

CREATE POLICY "Service role full access templates" 
    ON routine_templates
    FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');

-- =====================================================
-- Comments and Documentation
-- =====================================================

COMMENT ON TABLE plan_items IS 'Extracts individual trackable tasks from holistic_analysis_results for granular completion tracking';
COMMENT ON TABLE task_checkins IS 'Tracks individual task completions with satisfaction ratings for personalization';
COMMENT ON TABLE daily_journals IS 'Captures holistic daily reflection and wellbeing data for comprehensive behavior analysis';
COMMENT ON TABLE routine_templates IS 'Stores template structures used by AI agents for plan generation';

-- =====================================================
-- Trigger Functions for Updated Timestamps
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Note: Add updated_at triggers to any tables that need them in future migrations