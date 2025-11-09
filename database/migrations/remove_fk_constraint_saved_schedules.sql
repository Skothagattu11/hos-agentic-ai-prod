-- Temporarily remove foreign key constraint for testing
-- This allows testing with any user_id without requiring auth.users entry

-- Drop the foreign key constraint
ALTER TABLE IF EXISTS saved_schedules
DROP CONSTRAINT IF EXISTS fk_saved_schedules_user;

-- Add a comment explaining this is for flexible testing
COMMENT ON TABLE saved_schedules IS 'Schedule storage table - FK constraint removed to support Firebase Auth IDs';

-- Note: If you want to re-add the constraint later, use:
-- ALTER TABLE saved_schedules
-- ADD CONSTRAINT fk_saved_schedules_user
-- FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
