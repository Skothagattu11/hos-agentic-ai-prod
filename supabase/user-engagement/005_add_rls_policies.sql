-- RLS Policies for Calendar and Engagement Tables
-- Date: 2025-09-03
-- Purpose: Enable Row Level Security for calendar_selections, task_checkins, and daily_journals

-- ===================================================================
-- 1. Calendar Selections RLS Policies
-- ===================================================================

-- Enable RLS on calendar_selections table
ALTER TABLE calendar_selections ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own calendar selections
CREATE POLICY "Users can access own calendar selections" ON calendar_selections
    FOR ALL 
    USING (profile_id = auth.jwt() ->> 'sub' OR profile_id = current_user);

-- Policy: Service role can access all calendar selections
CREATE POLICY "Service role can access all calendar selections" ON calendar_selections
    FOR ALL 
    TO service_role
    USING (true);

-- ===================================================================
-- 2. Task Check-ins RLS Policies  
-- ===================================================================

-- Enable RLS on task_checkins table
ALTER TABLE task_checkins ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own task check-ins
CREATE POLICY "Users can access own task checkins" ON task_checkins
    FOR ALL 
    USING (profile_id = auth.jwt() ->> 'sub' OR profile_id = current_user);

-- Policy: Service role can access all task check-ins
CREATE POLICY "Service role can access all task checkins" ON task_checkins
    FOR ALL 
    TO service_role
    USING (true);

-- ===================================================================
-- 3. Daily Journals RLS Policies
-- ===================================================================

-- Enable RLS on daily_journals table  
ALTER TABLE daily_journals ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own daily journals
CREATE POLICY "Users can access own daily journals" ON daily_journals
    FOR ALL 
    USING (profile_id = auth.jwt() ->> 'sub' OR profile_id = current_user);

-- Policy: Service role can access all daily journals
CREATE POLICY "Service role can access all daily journals" ON daily_journals
    FOR ALL 
    TO service_role
    USING (true);

-- ===================================================================
-- 4. Plan Items RLS Policies (if not already set)
-- ===================================================================

-- Enable RLS on plan_items table
ALTER TABLE plan_items ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own plan items
CREATE POLICY "Users can access own plan items" ON plan_items
    FOR ALL 
    USING (profile_id = auth.jwt() ->> 'sub' OR profile_id = current_user);

-- Policy: Service role can access all plan items
CREATE POLICY "Service role can access all plan items" ON plan_items
    FOR ALL 
    TO service_role
    USING (true);

-- ===================================================================
-- 5. Holistic Analysis Results RLS Policies (if not already set)
-- ===================================================================

-- Enable RLS on holistic_analysis_results table
ALTER TABLE holistic_analysis_results ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own analysis results
CREATE POLICY "Users can access own analysis results" ON holistic_analysis_results
    FOR ALL 
    USING (user_id = auth.jwt() ->> 'sub' OR user_id = current_user);

-- Policy: Service role can access all analysis results
CREATE POLICY "Service role can access all analysis results" ON holistic_analysis_results
    FOR ALL 
    TO service_role
    USING (true);

-- ===================================================================
-- 6. Grant necessary permissions to authenticated users
-- ===================================================================

-- Grant SELECT, INSERT, UPDATE, DELETE to authenticated users on their own data
GRANT ALL ON calendar_selections TO authenticated;
GRANT ALL ON task_checkins TO authenticated;  
GRANT ALL ON daily_journals TO authenticated;
GRANT ALL ON plan_items TO authenticated;
GRANT ALL ON time_blocks TO authenticated;
GRANT ALL ON holistic_analysis_results TO authenticated;

-- Grant usage on sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- ===================================================================
-- 7. Test RLS policies (optional verification queries)
-- ===================================================================

/*
-- Test queries to verify RLS is working (run after applying policies):

-- This should work (service role access)
SELECT COUNT(*) FROM calendar_selections;

-- Test user-specific access (replace with actual user ID)  
SET request.jwt.claims TO '{"sub": "35pDPUIfAoRl2Y700bFkxPKYjjf2"}';
SELECT COUNT(*) FROM calendar_selections WHERE profile_id = '35pDPUIfAoRl2Y700bFkxPKYjjf2';

-- Reset
RESET request.jwt.claims;
*/

-- ===================================================================
-- 8. Add helpful comments
-- ===================================================================

COMMENT ON POLICY "Users can access own calendar selections" ON calendar_selections 
    IS 'Users can only see and modify their own calendar selections';

COMMENT ON POLICY "Service role can access all calendar selections" ON calendar_selections 
    IS 'Service role has full access for admin operations and API calls';

COMMENT ON POLICY "Users can access own task checkins" ON task_checkins 
    IS 'Users can only see and modify their own task check-ins';

COMMENT ON POLICY "Service role can access all task checkins" ON task_checkins 
    IS 'Service role has full access for admin operations and API calls';

COMMENT ON POLICY "Users can access own daily journals" ON daily_journals 
    IS 'Users can only see and modify their own daily journal entries';

COMMENT ON POLICY "Service role can access all daily journals" ON daily_journals 
    IS 'Service role has full access for admin operations and API calls';

-- ===================================================================
-- 9. Verification: Check that all policies are applied
-- ===================================================================

-- Query to verify all RLS policies are in place
SELECT 
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename IN ('calendar_selections', 'task_checkins', 'daily_journals', 'plan_items', 'time_blocks', 'holistic_analysis_results')
ORDER BY tablename, policyname;