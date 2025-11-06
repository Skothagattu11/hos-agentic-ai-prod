-- =====================================================
-- MIGRATION: Calendar Anchoring System
-- =====================================================
-- Date: November 6, 2025
-- Phase: 1 (Foundation)
-- Purpose: Add calendar anchoring support to plan_items and create results tracking table
--
-- Changes:
-- 1. Add anchoring columns to plan_items table
-- 2. Create calendar_anchoring_results table for metadata
-- 3. Add indexes for query performance
--
-- Compatibility: Does NOT break existing friction-reduction system (Phase 5.0)
-- =====================================================

-- =====================================================
-- Step 1: Add Anchoring Columns to plan_items
-- =====================================================

-- Add is_anchored flag (default false to not affect existing rows)
ALTER TABLE plan_items
ADD COLUMN IF NOT EXISTS is_anchored BOOLEAN DEFAULT false;

-- Add anchored_at timestamp (when anchoring was performed)
ALTER TABLE plan_items
ADD COLUMN IF NOT EXISTS anchored_at TIMESTAMP WITH TIME ZONE;

-- Add anchoring_metadata JSONB (stores anchoring algorithm results)
ALTER TABLE plan_items
ADD COLUMN IF NOT EXISTS anchoring_metadata JSONB;

-- Add confidence_score (how confident the anchoring algorithm is about placement)
ALTER TABLE plan_items
ADD COLUMN IF NOT EXISTS confidence_score FLOAT;

-- Add index on is_anchored for filtering
CREATE INDEX IF NOT EXISTS idx_plan_items_anchored
ON plan_items(is_anchored);

-- Add index on anchored_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_plan_items_anchored_at
ON plan_items(anchored_at);

COMMENT ON COLUMN plan_items.is_anchored IS 'Whether this task has been anchored to calendar events';
COMMENT ON COLUMN plan_items.anchored_at IS 'Timestamp when task was anchored to calendar';
COMMENT ON COLUMN plan_items.anchoring_metadata IS 'JSON metadata from anchoring algorithm (slot_id, scores, reasoning, etc.)';
COMMENT ON COLUMN plan_items.confidence_score IS 'Confidence score (0-1) from anchoring algorithm';

-- =====================================================
-- Step 2: Create calendar_anchoring_results Table
-- =====================================================

CREATE TABLE IF NOT EXISTS calendar_anchoring_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Links to plan generation
    analysis_result_id UUID NOT NULL,
    profile_id TEXT NOT NULL,
    target_date DATE NOT NULL,

    -- Calendar data used
    calendar_events_count INTEGER DEFAULT 0,
    calendar_provider VARCHAR(50) DEFAULT 'google',  -- 'google', 'mock', 'none'

    -- Anchoring results summary
    total_tasks INTEGER DEFAULT 0,
    tasks_anchored INTEGER DEFAULT 0,
    tasks_rescheduled INTEGER DEFAULT 0,
    tasks_kept_original_time INTEGER DEFAULT 0,
    average_confidence_score FLOAT DEFAULT 0.0,

    -- Rich metadata (JSONB)
    anchoring_summary JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_time_ms INTEGER,

    -- Ensure one anchoring result per plan per date
    CONSTRAINT unique_anchoring_per_plan UNIQUE(analysis_result_id, target_date),

    -- Foreign key to profiles table
    CONSTRAINT fk_anchoring_results_profile
        FOREIGN KEY (profile_id)
        REFERENCES profiles(id)
        ON DELETE CASCADE

    -- Note: analysis_result_id references holistic_analysis_results
    -- Foreign key handled at application level (different database in some deployments)
);

-- Indexes for calendar_anchoring_results
CREATE INDEX IF NOT EXISTS idx_anchoring_results_profile
ON calendar_anchoring_results(profile_id);

CREATE INDEX IF NOT EXISTS idx_anchoring_results_date
ON calendar_anchoring_results(target_date);

CREATE INDEX IF NOT EXISTS idx_anchoring_results_analysis
ON calendar_anchoring_results(analysis_result_id);

CREATE INDEX IF NOT EXISTS idx_anchoring_results_created
ON calendar_anchoring_results(created_at DESC);

-- Add table comment
COMMENT ON TABLE calendar_anchoring_results IS 'Stores metadata about calendar anchoring operations';

-- Add column comments
COMMENT ON COLUMN calendar_anchoring_results.analysis_result_id IS 'Links to holistic_analysis_results.id';
COMMENT ON COLUMN calendar_anchoring_results.calendar_provider IS 'Source of calendar events: google, mock, or none';
COMMENT ON COLUMN calendar_anchoring_results.anchoring_summary IS 'JSON with algorithm details (gaps found, AI models used, fallbacks, etc.)';
COMMENT ON COLUMN calendar_anchoring_results.processing_time_ms IS 'Time taken to perform anchoring (milliseconds)';

-- =====================================================
-- Step 3: Sample anchoring_metadata Structure
-- =====================================================

-- Example of what gets stored in plan_items.anchoring_metadata:
/*
{
  "original_time": "09:00:00",
  "anchored_time": "06:20:00",
  "time_adjustment_minutes": -160,
  "slot_id": "slot_001",
  "slot_type": "morning_start",
  "slot_size": "large",
  "habit_stack": {
    "anchor_event": "Morning coffee",
    "anchor_time": "06:10:00",
    "reliability": 0.98,
    "phrase": "After coffee, do 15-min stretch"
  },
  "scoring_breakdown": {
    "base_score": 15,
    "pattern_score": 10,
    "habit_score": 10,
    "goal_score": 8,
    "context_score": 2,
    "total": 45
  },
  "ai_reasoning": "Excellent placement. Morning coffee (98% reliability) is strongest anchor...",
  "calendar_gap_used": {
    "gap_start": "06:00:00",
    "gap_end": "09:30:00",
    "gap_type": "morning_start",
    "before_event": null,
    "after_event": "Team Standup"
  }
}
*/

-- =====================================================
-- Step 4: Sample anchoring_summary Structure
-- =====================================================

-- Example of what gets stored in calendar_anchoring_results.anchoring_summary:
/*
{
  "calendar_gaps_found": 8,
  "total_available_minutes": 870,
  "algorithm_version": "hybrid_v1.0",
  "ai_models_used": ["gpt-4", "gpt-4o-mini"],
  "pattern_analysis_used": true,
  "habit_stacking_applied": 7,
  "conflicts_detected": 0,
  "fallback_placements": 1,
  "calendar_fetch_source": "well-planned-api",
  "calendar_fetch_success": true,
  "error_message": null
}
*/

-- =====================================================
-- Rollback Script (if needed)
-- =====================================================

-- To rollback this migration:
/*
-- Drop calendar_anchoring_results table
DROP TABLE IF EXISTS calendar_anchoring_results CASCADE;

-- Remove indexes from plan_items
DROP INDEX IF EXISTS idx_plan_items_anchored;
DROP INDEX IF EXISTS idx_plan_items_anchored_at;

-- Remove columns from plan_items
ALTER TABLE plan_items DROP COLUMN IF EXISTS is_anchored;
ALTER TABLE plan_items DROP COLUMN IF EXISTS anchored_at;
ALTER TABLE plan_items DROP COLUMN IF EXISTS anchoring_metadata;
ALTER TABLE plan_items DROP COLUMN IF EXISTS confidence_score;
*/

-- =====================================================
-- Verification Queries
-- =====================================================

-- Check that columns were added
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'plan_items'
-- AND column_name IN ('is_anchored', 'anchored_at', 'anchoring_metadata', 'confidence_score');

-- Check that table was created
-- SELECT table_name
-- FROM information_schema.tables
-- WHERE table_name = 'calendar_anchoring_results';

-- Check indexes
-- SELECT indexname, tablename
-- FROM pg_indexes
-- WHERE tablename IN ('plan_items', 'calendar_anchoring_results')
-- AND indexname LIKE '%anchor%';

-- =====================================================
-- Migration Complete
-- =====================================================
