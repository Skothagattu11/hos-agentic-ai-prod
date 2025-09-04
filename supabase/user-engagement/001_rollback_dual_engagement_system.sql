-- =====================================================
-- Dual Engagement System Rollback Script
-- =====================================================
-- This script safely removes all components of the dual engagement system
-- Use this if you need to completely roll back the implementation

-- =====================================================
-- Drop RLS Policies First
-- =====================================================

-- Drop task_checkins policies
DROP POLICY IF EXISTS "Users can access own task check-ins" ON task_checkins;
DROP POLICY IF EXISTS "Service role full access task check-ins" ON task_checkins;

-- Drop daily_journals policies
DROP POLICY IF EXISTS "Users can access own journal data" ON daily_journals;
DROP POLICY IF EXISTS "Service role full access daily journals" ON daily_journals;

-- Drop plan_items policies
DROP POLICY IF EXISTS "Users can access own plan items" ON plan_items;
DROP POLICY IF EXISTS "Service role full access plan items" ON plan_items;

-- Drop routine_templates policies
DROP POLICY IF EXISTS "Users can read routine templates" ON routine_templates;
DROP POLICY IF EXISTS "Service role full access templates" ON routine_templates;

-- =====================================================
-- Drop Tables (in reverse dependency order)
-- =====================================================

-- Drop task_checkins first (references plan_items)
DROP TABLE IF EXISTS task_checkins CASCADE;

-- Drop daily_journals (standalone table)
DROP TABLE IF EXISTS daily_journals CASCADE;

-- Drop plan_items (references profiles but no other engagement tables)
DROP TABLE IF EXISTS plan_items CASCADE;

-- Drop routine_templates (standalone table)
DROP TABLE IF EXISTS routine_templates CASCADE;

-- =====================================================
-- Drop Functions
-- =====================================================

DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- =====================================================
-- Verify Cleanup
-- =====================================================

-- Check if tables still exist (should return empty)
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('task_checkins', 'daily_journals', 'plan_items', 'routine_templates');
    
    IF table_count > 0 THEN
        RAISE NOTICE 'Warning: % engagement tables still exist after rollback', table_count;
    ELSE
        RAISE NOTICE 'Rollback completed successfully - all engagement tables removed';
    END IF;
END $$;