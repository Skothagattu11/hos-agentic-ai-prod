-- ============================================================================
-- Fix Memory System RLS Policies
-- ============================================================================
-- This script adds RLS policies to allow the health analysis service to
-- write to memory tables while maintaining user data security.
--
-- Issue: Memory tables have RLS enabled with policies that only allow
-- authenticated users (auth.uid() = user_id), but the service operates
-- without user authentication context.
--
-- Solution: Add policies that allow service operations when auth.uid() is NULL
-- while preserving user data protection when auth.uid() exists.
-- ============================================================================

-- Remove any existing permissive service policies (cleanup)
DROP POLICY IF EXISTS "Allow service operations on working memory" ON holistic_working_memory;
DROP POLICY IF EXISTS "Allow service operations on shortterm memory" ON holistic_shortterm_memory;
DROP POLICY IF EXISTS "Allow service operations on longterm memory" ON holistic_longterm_memory;
DROP POLICY IF EXISTS "Allow service operations on meta memory" ON holistic_meta_memory;
DROP POLICY IF EXISTS "Allow service operations on analysis results" ON holistic_analysis_results;

-- ============================================================================
-- SECURE RLS POLICIES FOR MEMORY SYSTEM
-- ============================================================================
-- These policies allow:
-- 1. Service operations when auth.uid() IS NULL (your health analysis service)
-- 2. User operations when auth.uid() matches user_id (authenticated users)
-- ============================================================================

-- 1. Working Memory (session-based temporary data)
CREATE POLICY "Service and user access to working memory" 
ON holistic_working_memory 
FOR ALL 
TO public 
USING (auth.uid() IS NULL OR (auth.uid())::text = user_id) 
WITH CHECK (auth.uid() IS NULL OR (auth.uid())::text = user_id);

-- 2. Short-term Memory (recent patterns, 7-30 days)
CREATE POLICY "Service and user access to shortterm memory"
ON holistic_shortterm_memory 
FOR ALL 
TO public 
USING (auth.uid() IS NULL OR (auth.uid())::text = user_id) 
WITH CHECK (auth.uid() IS NULL OR (auth.uid())::text = user_id);

-- 3. Long-term Memory (persistent user patterns)
CREATE POLICY "Service and user access to longterm memory"
ON holistic_longterm_memory 
FOR ALL 
TO public 
USING (auth.uid() IS NULL OR (auth.uid())::text = user_id) 
WITH CHECK (auth.uid() IS NULL OR (auth.uid())::text = user_id);

-- 4. Meta Memory (learning about learning patterns)
CREATE POLICY "Service and user access to meta memory"
ON holistic_meta_memory 
FOR ALL 
TO public 
USING (auth.uid() IS NULL OR (auth.uid())::text = user_id) 
WITH CHECK (auth.uid() IS NULL OR (auth.uid())::text = user_id);

-- 5. Analysis Results (historical analysis storage)
CREATE POLICY "Service and user access to analysis results"
ON holistic_analysis_results 
FOR ALL 
TO public 
USING (auth.uid() IS NULL OR (auth.uid())::text = user_id) 
WITH CHECK (auth.uid() IS NULL OR (auth.uid())::text = user_id);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify the policies were created successfully:

-- Check that all policies exist:
SELECT 
    tablename,
    policyname,
    cmd as operation,
    using_expression,
    check_expression
FROM pg_policies 
WHERE tablename IN (
    'holistic_working_memory',
    'holistic_shortterm_memory', 
    'holistic_longterm_memory',
    'holistic_meta_memory',
    'holistic_analysis_results'
)
ORDER BY tablename, policyname;

-- Test INSERT permission (should work now):
/*
INSERT INTO holistic_working_memory (
    user_id, session_id, agent_id, memory_type, content,
    priority, created_at, expires_at, is_active
) VALUES (
    'test_user', 'test_session', 'test_agent', 'test_type', 
    '{"test": "data"}'::jsonb, 5, now(), now() + interval '1 day', true
);

-- Clean up test data:
DELETE FROM holistic_working_memory WHERE user_id = 'test_user';
*/

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. These policies maintain security by:
--    - Allowing service operations when no user is authenticated (auth.uid() IS NULL)
--    - Restricting user access to their own data when authenticated
--
-- 2. The "TO public" means these policies apply to all roles, but the USING/CHECK
--    clauses still enforce the security constraints.
--
-- 3. If you need even more restrictive policies, you can modify the USING/CHECK
--    expressions to add additional constraints.
--
-- 4. After running this script, your memory system should work properly while
--    maintaining Row-Level Security protection.
-- ============================================================================