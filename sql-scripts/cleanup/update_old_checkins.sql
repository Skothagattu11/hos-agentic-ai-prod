-- Update old check-ins with default values for new simplified columns
-- This makes them compatible with the new feedback system

-- Update experience_rating based on satisfaction_rating (if it exists)
UPDATE task_checkins
SET experience_rating = CASE
    WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating
    ELSE 3  -- Default to "OK" (neutral) if no rating exists
END
WHERE experience_rating IS NULL;

-- Set continue_preference to 'maybe' for old records (neutral default)
UPDATE task_checkins
SET continue_preference = 'maybe'
WHERE continue_preference IS NULL;

-- Verify the update
SELECT 
    COUNT(*) as total_checkins,
    COUNT(experience_rating) as has_experience_rating,
    COUNT(continue_preference) as has_continue_preference,
    AVG(experience_rating) as avg_experience,
    COUNT(CASE WHEN continue_preference = 'yes' THEN 1 END) as continue_yes,
    COUNT(CASE WHEN continue_preference = 'maybe' THEN 1 END) as continue_maybe,
    COUNT(CASE WHEN continue_preference = 'no' THEN 1 END) as continue_no
FROM task_checkins
WHERE profile_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869';
