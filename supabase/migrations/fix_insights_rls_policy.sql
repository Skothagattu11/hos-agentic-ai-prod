-- Fix RLS policies for holistic_insights table
-- Issue: Service operations are blocked by auth.uid() requirement
-- Solution: Add policy that allows service_role and anon operations

-- Drop existing restrictive policies
DROP POLICY IF EXISTS insights_user_isolation ON public.holistic_insights;
DROP POLICY IF EXISTS insights_service_role ON public.holistic_insights;

-- Create more permissive policies for MVP

-- Policy 1: Allow all operations for service_role (for backend services)
CREATE POLICY insights_service_full_access ON public.holistic_insights
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy 2: Allow all operations for anon role (for development/testing)
CREATE POLICY insights_anon_access ON public.holistic_insights
    FOR ALL TO anon
    USING (true) 
    WITH CHECK (true);

-- Policy 3: Allow authenticated users to access their own insights
CREATE POLICY insights_user_access ON public.holistic_insights
    FOR ALL TO authenticated
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

-- Ensure proper grants are in place
GRANT ALL ON public.holistic_insights TO service_role;
GRANT ALL ON public.holistic_insights TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.holistic_insights TO authenticated;

-- Also fix the view permissions
GRANT SELECT ON public.active_insights TO anon;
GRANT SELECT ON public.active_insights TO service_role;
GRANT SELECT ON public.active_insights TO authenticated;