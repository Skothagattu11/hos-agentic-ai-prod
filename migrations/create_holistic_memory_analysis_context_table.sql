-- Migration: Create holistic_memory_analysis_context table for AI Context Generation Service
-- This table stores AI-generated context summaries that replace the complex 4-layer memory system

-- Create the main context table
CREATE TABLE IF NOT EXISTS holistic_memory_analysis_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    context_summary TEXT NOT NULL,  -- AI-generated context summary
    source_data JSONB,              -- Raw data used to generate context
    archetype TEXT,                 -- User archetype when context was generated
    engagement_data_included BOOLEAN DEFAULT FALSE,  -- Whether engagement data was used
    data_period_days INTEGER DEFAULT 30,            -- Number of days analyzed
    generation_method VARCHAR(50) DEFAULT 'ai_raw_data',  -- How context was generated
    created_at TIMESTAMP DEFAULT NOW()

    -- Note: Uniqueness per user per day handled by application logic and cleanup processes
);

-- Enable Row Level Security
ALTER TABLE holistic_memory_analysis_context ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Policy for users to access their own context data
CREATE POLICY "Users can view their own analysis context"
ON holistic_memory_analysis_context
FOR SELECT
USING (auth.uid()::text = user_id);

-- Policy for users to insert their own context data
CREATE POLICY "Users can insert their own analysis context"
ON holistic_memory_analysis_context
FOR INSERT
WITH CHECK (auth.uid()::text = user_id);

-- Policy for users to update their own context data
CREATE POLICY "Users can update their own analysis context"
ON holistic_memory_analysis_context
FOR UPDATE
USING (auth.uid()::text = user_id)
WITH CHECK (auth.uid()::text = user_id);

-- Policy for service role to manage all context data (for admin/system operations)
CREATE POLICY "Service role can manage all analysis context"
ON holistic_memory_analysis_context
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_holistic_memory_analysis_context_user_date
ON holistic_memory_analysis_context (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_holistic_memory_analysis_context_archetype
ON holistic_memory_analysis_context (user_id, archetype, created_at DESC);

-- Add helpful comments
COMMENT ON TABLE holistic_memory_analysis_context IS 'AI-generated context summaries for personalized behavior and circadian analysis';
COMMENT ON COLUMN holistic_memory_analysis_context.context_summary IS 'AI-generated summary of user patterns, preferences, and insights';
COMMENT ON COLUMN holistic_memory_analysis_context.source_data IS 'Metadata about the raw data used (engagement metrics, calendar data, etc.)';
COMMENT ON COLUMN holistic_memory_analysis_context.engagement_data_included IS 'Whether this context includes engagement/calendar data analysis';
COMMENT ON COLUMN holistic_memory_analysis_context.generation_method IS 'Method used: ai_raw_data, manual, or legacy_memory';

-- Grant necessary permissions for authenticated users
GRANT SELECT, INSERT, UPDATE ON holistic_memory_analysis_context TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON holistic_memory_analysis_context TO service_role;