-- =========================================================================
-- HolisticOS Memory System Tables
-- =========================================================================
-- 
-- This file contains SQL commands to create the memory system tables
-- for the HolisticOS MVP implementation.
--
-- These tables support the 4-layer hierarchical memory system:
-- 1. Working Memory (temporary, session-based)
-- 2. Short-term Memory (recent patterns and context)
-- 3. Long-term Memory (persistent user patterns and preferences)
-- 4. Meta-memory (learning about learning patterns)
--
-- IMPORTANT: Run these commands in your existing Supabase database
-- =========================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -------------------------------------------------------------------------
-- 1. WORKING MEMORY TABLE
-- -------------------------------------------------------------------------
-- Stores temporary session data, active analysis context, and workflow state
-- TTL: Usually 1-24 hours, cleaned up automatically

CREATE TABLE IF NOT EXISTS holistic_working_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL, -- Which agent stored this memory
    memory_type TEXT NOT NULL CHECK (memory_type IN (
        'analysis_context',
        'workflow_state', 
        'user_goals',
        'session_preferences',
        'active_insights',
        'temporary_patterns'
    )),
    content JSONB NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    -- Indexes for performance
    CONSTRAINT unique_session_memory UNIQUE(user_id, session_id, memory_type, agent_id)
);

-- Indexes for working memory
CREATE INDEX idx_working_memory_user_session ON holistic_working_memory(user_id, session_id);
CREATE INDEX idx_working_memory_expiry ON holistic_working_memory(expires_at) WHERE is_active = true;
CREATE INDEX idx_working_memory_type ON holistic_working_memory(memory_type);

-- -------------------------------------------------------------------------
-- 2. SHORT-TERM MEMORY TABLE  
-- -------------------------------------------------------------------------
-- Stores recent patterns, analysis results, and contextual information
-- TTL: Usually 7-30 days, represents recent behavioral patterns

CREATE TABLE IF NOT EXISTS holistic_shortterm_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    memory_category TEXT NOT NULL CHECK (memory_category IN (
        'recent_behaviors',
        'analysis_results',
        'goal_progress',
        'preference_changes',
        'interaction_patterns',
        'adaptation_responses'
    )),
    content JSONB NOT NULL,
    confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    recency_weight FLOAT DEFAULT 1.0 CHECK (recency_weight >= 0.0 AND recency_weight <= 2.0),
    source_agent TEXT NOT NULL, -- Agent that created this memory
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 1,
    
    -- Relevance and importance scores
    relevance_score FLOAT DEFAULT 0.5 CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0.0 AND importance_score <= 1.0)
);

-- Indexes for short-term memory
CREATE INDEX idx_shortterm_memory_user ON holistic_shortterm_memory(user_id);
CREATE INDEX idx_shortterm_memory_category ON holistic_shortterm_memory(memory_category);
CREATE INDEX idx_shortterm_memory_confidence ON holistic_shortterm_memory(confidence_score DESC);
CREATE INDEX idx_shortterm_memory_recency ON holistic_shortterm_memory(created_at DESC);

-- -------------------------------------------------------------------------
-- 3. LONG-TERM MEMORY TABLE
-- -------------------------------------------------------------------------
-- Stores persistent user patterns, stable preferences, and learned behaviors
-- TTL: Permanent or very long-term (months/years)

CREATE TABLE IF NOT EXISTS holistic_longterm_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    memory_category TEXT NOT NULL CHECK (memory_category IN (
        'behavioral_patterns',
        'health_preferences',
        'goal_history',
        'successful_strategies',
        'archetype_evolution',
        'interaction_preferences',
        'learning_patterns',
        'personality_traits',
        'motivation_drivers',
        'barrier_patterns'
    )),
    memory_data JSONB NOT NULL,
    
    -- Confidence and stability metrics
    confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    stability_score FLOAT DEFAULT 0.5 CHECK (stability_score >= 0.0 AND stability_score <= 1.0),
    evidence_count INTEGER DEFAULT 1,
    
    -- Versioning and evolution tracking
    version INTEGER DEFAULT 1,
    previous_version_id UUID REFERENCES holistic_longterm_memory(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_validated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Source tracking
    contributing_agents TEXT[] DEFAULT '{}',
    update_source TEXT NOT NULL,
    
    -- Memory consolidation status
    is_consolidated BOOLEAN DEFAULT false,
    consolidation_date TIMESTAMP WITH TIME ZONE,
    
    -- Unique constraint for category per user
    CONSTRAINT unique_user_memory_category UNIQUE(user_id, memory_category)
);

-- Indexes for long-term memory
CREATE INDEX idx_longterm_memory_user ON holistic_longterm_memory(user_id);
CREATE INDEX idx_longterm_memory_category ON holistic_longterm_memory(memory_category);
CREATE INDEX idx_longterm_memory_confidence ON holistic_longterm_memory(confidence_score DESC);
CREATE INDEX idx_longterm_memory_stability ON holistic_longterm_memory(stability_score DESC);
CREATE INDEX idx_longterm_memory_consolidated ON holistic_longterm_memory(is_consolidated);

-- -------------------------------------------------------------------------
-- 4. META-MEMORY TABLE
-- -------------------------------------------------------------------------
-- Stores learning about learning - how the user responds to different approaches,
-- what adaptation strategies work, and system performance patterns

CREATE TABLE IF NOT EXISTS holistic_meta_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    
    -- Learning patterns about the user
    adaptation_patterns JSONB NOT NULL, -- How user responds to different strategies
    learning_velocity JSONB NOT NULL,   -- How quickly user adopts new patterns
    success_predictors JSONB NOT NULL,  -- What factors predict success for this user
    failure_patterns JSONB NOT NULL,    -- What consistently doesn't work
    
    -- System performance metrics
    agent_effectiveness JSONB NOT NULL, -- Which agents work best for this user
    archetype_evolution JSONB NOT NULL, -- How user's archetype has changed
    engagement_patterns JSONB NOT NULL, -- User interaction and engagement data
    
    -- Meta-learning scores
    adaptability_score FLOAT DEFAULT 0.5 CHECK (adaptability_score >= 0.0 AND adaptability_score <= 1.0),
    consistency_score FLOAT DEFAULT 0.5 CHECK (consistency_score >= 0.0 AND consistency_score <= 1.0),
    complexity_tolerance FLOAT DEFAULT 0.5 CHECK (complexity_tolerance >= 0.0 AND complexity_tolerance <= 1.0),
    
    -- Timestamps and versioning
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analysis_window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    analysis_window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Source and confidence
    confidence_level FLOAT DEFAULT 0.5 CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0),
    sample_size INTEGER DEFAULT 0,
    
    -- Unique per user (only one meta-memory record per user, updated over time)
    CONSTRAINT unique_user_meta_memory UNIQUE(user_id)
);

-- Indexes for meta-memory
CREATE INDEX idx_meta_memory_user ON holistic_meta_memory(user_id);
CREATE INDEX idx_meta_memory_adaptability ON holistic_meta_memory(adaptability_score DESC);
CREATE INDEX idx_meta_memory_updated ON holistic_meta_memory(last_updated DESC);

-- -------------------------------------------------------------------------
-- 5. ANALYSIS RESULTS STORAGE TABLE
-- -------------------------------------------------------------------------
-- Stores complete analysis results for historical tracking and comparison

CREATE TABLE IF NOT EXISTS holistic_analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL CHECK (analysis_type IN (
        'behavior_analysis',
        'nutrition_plan', 
        'routine_plan',
        'complete_analysis'
    )),
    archetype TEXT,
    
    -- Analysis data
    analysis_result JSONB NOT NULL,
    input_summary JSONB NOT NULL, -- Summary of input data used
    
    -- Analysis metadata
    agent_id TEXT NOT NULL,
    analysis_version TEXT DEFAULT '1.0',
    system_prompt_version TEXT,
    
    -- Quality metrics
    confidence_score FLOAT DEFAULT 0.0,
    completeness_score FLOAT DEFAULT 0.0,
    processing_time_ms INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analysis_date DATE DEFAULT CURRENT_DATE,
    
    -- User feedback and outcomes
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    implementation_success BOOLEAN,
    follow_up_date DATE
);

-- Indexes for analysis results
CREATE INDEX idx_analysis_results_user ON holistic_analysis_results(user_id);
CREATE INDEX idx_analysis_results_type ON holistic_analysis_results(analysis_type);
CREATE INDEX idx_analysis_results_date ON holistic_analysis_results(analysis_date DESC);
CREATE INDEX idx_analysis_results_archetype ON holistic_analysis_results(archetype);

-- -------------------------------------------------------------------------
-- 6. MEMORY CLEANUP AND MAINTENANCE
-- -------------------------------------------------------------------------

-- Function to clean up expired working memory
CREATE OR REPLACE FUNCTION cleanup_expired_working_memory()
RETURNS void AS $$
BEGIN
    DELETE FROM holistic_working_memory 
    WHERE expires_at < NOW() AND is_active = true;
END;
$$ LANGUAGE plpgsql;

-- Function to update access patterns
CREATE OR REPLACE FUNCTION update_memory_access(memory_table TEXT, memory_id UUID)
RETURNS void AS $$
BEGIN
    IF memory_table = 'shortterm' THEN
        UPDATE holistic_shortterm_memory 
        SET last_accessed = NOW(), access_count = access_count + 1
        WHERE id = memory_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- -------------------------------------------------------------------------
-- 7. ROW LEVEL SECURITY (Optional - for multi-tenant setup)
-- -------------------------------------------------------------------------

-- Enable RLS on all memory tables
ALTER TABLE holistic_working_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE holistic_shortterm_memory ENABLE ROW LEVEL SECURITY;  
ALTER TABLE holistic_longterm_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE holistic_meta_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE holistic_analysis_results ENABLE ROW LEVEL SECURITY;

-- Create policies (users can only access their own memories)
CREATE POLICY "Users can only access their own working memory" ON holistic_working_memory
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own short-term memory" ON holistic_shortterm_memory
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own long-term memory" ON holistic_longterm_memory  
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own meta-memory" ON holistic_meta_memory
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own analysis results" ON holistic_analysis_results
    FOR ALL USING (auth.uid()::text = user_id);

-- -------------------------------------------------------------------------
-- 8. SAMPLE DATA AND VERIFICATION QUERIES
-- -------------------------------------------------------------------------

-- Verify tables were created successfully
DO $$
BEGIN
    RAISE NOTICE 'HolisticOS Memory System Tables Created Successfully!';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - holistic_working_memory';
    RAISE NOTICE '  - holistic_shortterm_memory'; 
    RAISE NOTICE '  - holistic_longterm_memory';
    RAISE NOTICE '  - holistic_meta_memory';
    RAISE NOTICE '  - holistic_analysis_results';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Update your .env file with DATABASE_URL';
    RAISE NOTICE '  2. Test the connection from your HolisticOS agents';
    RAISE NOTICE '  3. Run initial memory population scripts';
END $$;

-- Sample verification query (run this to test)
-- SELECT 
--     schemaname, 
--     tablename, 
--     tableowner 
-- FROM pg_tables 
-- WHERE tablename LIKE 'holistic_%' 
-- ORDER BY tablename;