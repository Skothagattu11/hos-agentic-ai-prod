-- Migration: Create Holistic Insights Table
-- Purpose: Centralized storage for all insights with deduplication and referencing
-- Date: 2025-08-15

-- Create holistic_insights table (updated for actual schema compatibility)
CREATE TABLE IF NOT EXISTS public.holistic_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    insight_type VARCHAR(50) NOT NULL, -- 'behavioral', 'nutritional', 'routine', 'adaptive', 'general'
    source_analysis_id UUID REFERENCES public.holistic_analysis_results(id), -- Reference to the analysis that generated this insight
    source_analysis_type VARCHAR(50), -- 'behavior_analysis', 'routine_plan', 'nutrition_plan', 'follow_up'
    archetype VARCHAR(50) NOT NULL,
    
    -- Core insight content
    insight_title VARCHAR(255) NOT NULL,
    insight_content TEXT NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10), -- 1=highest, 10=lowest
    actionability_score DECIMAL(3,2) CHECK (actionability_score >= 0 AND actionability_score <= 1), -- 0-1 how actionable
    
    -- Context and metadata
    data_context JSONB, -- Context about what data drove this insight
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    supporting_metrics TEXT[], -- Array of metric names that support this insight
    tags TEXT[] DEFAULT '{}', -- Searchable tags for categorization
    
    -- Lifecycle management
    is_active BOOLEAN DEFAULT true,
    user_acknowledged BOOLEAN DEFAULT false,
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5), -- User feedback 1-5 stars
    user_feedback TEXT,
    
    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- Optional expiry for time-sensitive insights
    last_surfaced_at TIMESTAMP WITH TIME ZONE, -- When was this last shown to user
    
    -- Deduplication fields
    content_hash TEXT, -- Hash of insight_content for duplicate detection
    context_signature TEXT, -- Hash of key context elements for similar insights
    
    -- Performance indexes
    CONSTRAINT unique_content_per_user UNIQUE (user_id, content_hash),
    CONSTRAINT unique_context_per_user UNIQUE (user_id, insight_type, context_signature)
);

-- Create indexes for performance
CREATE INDEX idx_insights_user_active ON public.holistic_insights (user_id, is_active, created_at DESC);
CREATE INDEX idx_insights_type_priority ON public.holistic_insights (insight_type, priority, created_at DESC);
CREATE INDEX idx_insights_archetype ON public.holistic_insights (archetype, user_id);
CREATE INDEX idx_insights_source_analysis ON public.holistic_insights (source_analysis_id, source_analysis_type);
CREATE INDEX idx_insights_actionability ON public.holistic_insights (actionability_score DESC, priority ASC);
CREATE INDEX idx_insights_tags ON public.holistic_insights USING GIN (tags);
CREATE INDEX idx_insights_content_hash ON public.holistic_insights (content_hash);
CREATE INDEX idx_insights_context_signature ON public.holistic_insights (context_signature);

-- Create function to update updated_at automatically
CREATE OR REPLACE FUNCTION update_insights_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER trigger_insights_updated_at
    BEFORE UPDATE ON public.holistic_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_insights_updated_at();

-- Add RLS policies (Row Level Security)
ALTER TABLE public.holistic_insights ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own insights
CREATE POLICY insights_user_isolation ON public.holistic_insights
    FOR ALL USING (auth.uid()::text = user_id);

-- Policy: Service role can access all insights (for admin/system operations)
CREATE POLICY insights_service_role ON public.holistic_insights
    FOR ALL USING (auth.role() = 'service_role');

-- Grant permissions
GRANT ALL ON public.holistic_insights TO postgres;
GRANT ALL ON public.holistic_insights TO service_role;
GRANT SELECT, INSERT, UPDATE ON public.holistic_insights TO authenticated;

-- Create view for active insights with computed fields
CREATE OR REPLACE VIEW public.active_insights AS
SELECT 
    *,
    CASE 
        WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN false
        ELSE is_active 
    END as is_currently_active,
    EXTRACT(EPOCH FROM (NOW() - created_at))::INTEGER as age_seconds,
    CASE 
        WHEN last_surfaced_at IS NULL THEN true
        ELSE EXTRACT(EPOCH FROM (NOW() - last_surfaced_at)) > 86400 -- 24 hours
    END as ready_to_surface
FROM public.holistic_insights
WHERE is_active = true;

GRANT SELECT ON public.active_insights TO authenticated;
GRANT SELECT ON public.active_insights TO service_role;

-- Add comments for documentation
COMMENT ON TABLE public.holistic_insights IS 'Centralized storage for all health insights with deduplication and lifecycle management';
COMMENT ON COLUMN public.holistic_insights.insight_type IS 'Type of insight: behavioral, nutritional, routine, adaptive, general';
COMMENT ON COLUMN public.holistic_insights.source_analysis_id IS 'References the analysis that generated this insight (from holistic_analysis_results)';
COMMENT ON COLUMN public.holistic_insights.actionability_score IS 'How actionable this insight is (0=theoretical, 1=immediately actionable)';
COMMENT ON COLUMN public.holistic_insights.content_hash IS 'MD5 hash of insight_content for duplicate prevention';
COMMENT ON COLUMN public.holistic_insights.context_signature IS 'Hash of key context elements to prevent similar insights';
COMMENT ON VIEW public.active_insights IS 'View showing only active, non-expired insights with computed status fields';