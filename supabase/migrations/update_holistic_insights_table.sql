-- Migration: Update Existing Holistic Insights Table
-- Purpose: Add foreign key reference to holistic_analysis_results
-- Date: 2025-08-15

-- Option 1: If you want to DROP and RECREATE (will lose any existing data)
-- Uncomment the line below if you want to drop the table
-- DROP TABLE IF EXISTS public.holistic_insights CASCADE;

-- Option 2: ALTER existing table to add the foreign key (RECOMMENDED)
-- This preserves any existing data

-- Check if foreign key constraint already exists
DO $$
BEGIN
    -- Add foreign key constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'holistic_insights_source_analysis_id_fkey'
        AND table_name = 'holistic_insights'
    ) THEN
        ALTER TABLE public.holistic_insights
        ADD CONSTRAINT holistic_insights_source_analysis_id_fkey 
        FOREIGN KEY (source_analysis_id) 
        REFERENCES public.holistic_analysis_results(id)
        ON DELETE SET NULL;
    END IF;
END $$;

-- Verify the table structure
-- This will show you the current structure including the new foreign key
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'holistic_insights'
ORDER BY ordinal_position;

-- Show all constraints on the table
SELECT 
    con.conname AS constraint_name,
    con.contype AS constraint_type,
    CASE 
        WHEN con.contype = 'f' THEN 'FOREIGN KEY'
        WHEN con.contype = 'p' THEN 'PRIMARY KEY'
        WHEN con.contype = 'u' THEN 'UNIQUE'
        WHEN con.contype = 'c' THEN 'CHECK'
    END AS type_description
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
WHERE rel.relname = 'holistic_insights';

-- If you need to check if there's any data in the table
SELECT COUNT(*) as record_count FROM public.holistic_insights;