-- Migration: Create archetype-specific analysis tracking table
-- Purpose: Enable each user archetype to have independent analysis timestamps
-- Date: 2025-08-19
-- Phase: MVP Implementation Phase 1

-- Create the archetype analysis tracking table
CREATE TABLE IF NOT EXISTS archetype_analysis_tracking (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    archetype TEXT NOT NULL,
    last_analysis_at TIMESTAMPTZ NOT NULL,
    analysis_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure one record per user-archetype combination
    CONSTRAINT unique_user_archetype UNIQUE(user_id, archetype)
);

-- Performance indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_archetype_tracking_user_archetype 
ON archetype_analysis_tracking(user_id, archetype);

CREATE INDEX IF NOT EXISTS idx_archetype_tracking_last_analysis 
ON archetype_analysis_tracking(user_id, last_analysis_at DESC);

-- Add helpful comments
COMMENT ON TABLE archetype_analysis_tracking IS 
'Tracks last analysis date for each user-archetype combination to enable archetype-specific data windows';

COMMENT ON COLUMN archetype_analysis_tracking.user_id IS 
'User identifier - references profiles.id';

COMMENT ON COLUMN archetype_analysis_tracking.archetype IS 
'Archetype name (Peak Performer, Foundation Builder, etc.)';

COMMENT ON COLUMN archetype_analysis_tracking.last_analysis_at IS 
'Timestamp of most recent behavior analysis for this user-archetype combination';

COMMENT ON COLUMN archetype_analysis_tracking.analysis_count IS 
'Total number of analyses performed for this user-archetype combination';

-- Validation: Check that expected archetypes are used
ALTER TABLE archetype_analysis_tracking 
ADD CONSTRAINT valid_archetype CHECK (
    archetype IN (
        'Foundation Builder',
        'Peak Performer', 
        'Systematic Improver',
        'Transformation Seeker',
        'Resilience Rebuilder',
        'Connected Explorer'
    )
);

-- ============================================
-- ROW LEVEL SECURITY (RLS) SETUP
-- ============================================

-- Enable RLS on the table
ALTER TABLE archetype_analysis_tracking ENABLE ROW LEVEL SECURITY;

-- Drop any existing policies (in case of re-run)
DROP POLICY IF EXISTS archetype_tracking_service_full_access ON public.archetype_analysis_tracking;
DROP POLICY IF EXISTS archetype_tracking_anon_access ON public.archetype_analysis_tracking;
DROP POLICY IF EXISTS archetype_tracking_user_access ON public.archetype_analysis_tracking;

-- Policy 1: Allow all operations for service_role (for backend services)
CREATE POLICY archetype_tracking_service_full_access ON public.archetype_analysis_tracking
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy 2: Allow all operations for anon role (for development/testing)
CREATE POLICY archetype_tracking_anon_access ON public.archetype_analysis_tracking
    FOR ALL TO anon
    USING (true) 
    WITH CHECK (true);

-- Policy 3: Allow authenticated users to access their own archetype tracking data
CREATE POLICY archetype_tracking_user_access ON public.archetype_analysis_tracking
    FOR ALL TO authenticated
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

-- Ensure proper grants are in place
GRANT ALL ON public.archetype_analysis_tracking TO service_role;
GRANT ALL ON public.archetype_analysis_tracking TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.archetype_analysis_tracking TO authenticated;

-- Grant sequence permissions for SERIAL id column
GRANT USAGE, SELECT ON SEQUENCE archetype_analysis_tracking_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE archetype_analysis_tracking_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE archetype_analysis_tracking_id_seq TO authenticated;