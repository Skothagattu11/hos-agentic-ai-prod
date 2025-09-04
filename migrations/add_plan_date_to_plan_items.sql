-- Add plan_date column to plan_items table for proper date tracking
-- This ensures tasks are associated with their plan generation date, not action timestamps

-- Add the plan_date column
ALTER TABLE plan_items 
ADD COLUMN plan_date DATE;

-- Create an index for efficient querying by plan_date
CREATE INDEX idx_plan_items_plan_date ON plan_items(plan_date);

-- Backfill existing records with plan_date from holistic_analysis_results
UPDATE plan_items 
SET plan_date = har.analysis_date
FROM holistic_analysis_results har 
WHERE plan_items.analysis_result_id = har.id;

-- Add a comment explaining the column
COMMENT ON COLUMN plan_items.plan_date IS 'Date the plan was generated for (copied from holistic_analysis_results.analysis_date)';

-- Make the column NOT NULL after backfill
ALTER TABLE plan_items 
ALTER COLUMN plan_date SET NOT NULL;