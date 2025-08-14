-- Add last_analysis_at column to profiles table for simplified incremental sync
-- This replaces complex memory table approach with single field tracking

ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS last_analysis_at TIMESTAMPTZ;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_profiles_last_analysis 
ON profiles(last_analysis_at);

-- Optional: Add analysis metadata for future expansion
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS analysis_metadata JSONB DEFAULT '{}';

COMMENT ON COLUMN profiles.last_analysis_at IS 'Timestamp of last analysis for incremental data fetching';
COMMENT ON COLUMN profiles.analysis_metadata IS 'Optional metadata: analysis_count, data_volume, etc';
