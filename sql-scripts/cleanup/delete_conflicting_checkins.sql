-- Delete only the check-ins that conflict with the test
-- (same plan_item_ids and dates that the test will try to create)

DELETE FROM task_checkins
WHERE profile_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869'
AND plan_item_id IN (
    'c4f527a1-4dd4-4086-9bee-0318a946d282',
    '6f9ad297-4c57-49ec-b18a-f7742d3c4328',
    'fa034fbd-973f-4b37-8bc8-581205bd3c9d',
    '758a80e5-4112-4df4-9017-bd147dd2849e',
    '279dbc2c-7c0b-4be1-b5fc-13ca3d9a7387',
    '9349f0fa-e1c0-4174-90d5-0fe85704c4ca',
    '1a72b9eb-4ba4-4d9d-b734-ef366b233de5',
    '4a71b960-a317-4766-b7b4-8e8be125495c',
    '84509da2-2e2a-40fb-811d-b55c4dc7d254',
    '84404c60-5a2b-4c29-bbc5-9433319e3b97',
    '372e4673-aef2-45a6-9dfd-19c3bdf1ead1',
    '56b7f2a1-dc9a-48ef-961b-e6c6b82513f1'
)
AND planned_date = '2025-10-29';

-- Show what remains
SELECT COUNT(*) as remaining_checkins FROM task_checkins
WHERE profile_id = 'a57f70b4-d0a4-4aef-b721-a4b526f64869';
