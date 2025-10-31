-- =====================================================
-- Add key_insights Column to holistic_analysis_results
-- =====================================================
-- Purpose: Store 4 key insights extracted from behavior and circadian analysis
-- Date: 2025-10-30
-- Author: HolisticOS Team

-- Add key_insights JSONB column
ALTER TABLE holistic_analysis_results
ADD COLUMN IF NOT EXISTS key_insights JSONB DEFAULT '[]'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN holistic_analysis_results.key_insights IS
'Array of 4 key insights extracted from behavior and circadian analysis for UI display.
Format: ["insight 1", "insight 2", "insight 3", "insight 4"]';

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_holistic_analysis_results_key_insights
ON holistic_analysis_results USING gin (key_insights);

-- Verification query
SELECT
    table_name,
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'holistic_analysis_results'
AND column_name = 'key_insights';

-- Example query to verify structure
-- SELECT
--     id,
--     profile_id,
--     analysis_type,
--     key_insights,
--     created_at
-- FROM holistic_analysis_results
-- WHERE key_insights IS NOT NULL
-- ORDER BY created_at DESC
-- LIMIT 5;
