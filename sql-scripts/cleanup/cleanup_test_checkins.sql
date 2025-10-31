-- Delete old test check-ins for the test user
-- This allows the test to create fresh check-ins with the new simplified columns

DELETE FROM task_checkins 
WHERE profile_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869'
AND planned_date >= '2025-10-29'::date;

-- Verify deletion
SELECT 
    COUNT(*) as remaining_checkins,
    MIN(planned_date) as earliest_date,
    MAX(planned_date) as latest_date
FROM task_checkins 
WHERE profile_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869';
