-- Migration: Add Duplicate Prevention Constraints (Fixed Version 2)
-- Purpose: Prevent duplicate analysis entries - fixes all errors
-- Date: 2025-08-15

-- 1. holistic_analysis_results: Add analysis_hash column for content deduplication
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'holistic_analysis_results' 
        AND column_name = 'analysis_hash'
    ) THEN
        ALTER TABLE public.holistic_analysis_results
        ADD COLUMN analysis_hash TEXT;
    END IF;
END $$;

-- Add duplicate tracking columns if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'holistic_analysis_results' 
        AND column_name = 'data_source_hash'
    ) THEN
        ALTER TABLE public.holistic_analysis_results
        ADD COLUMN data_source_hash TEXT,
        ADD COLUMN is_duplicate BOOLEAN DEFAULT FALSE,
        ADD COLUMN original_analysis_id UUID REFERENCES public.holistic_analysis_results(id);
    END IF;
END $$;

-- Create function to generate analysis hash
CREATE OR REPLACE FUNCTION generate_analysis_hash(analysis_result JSONB)
RETURNS TEXT AS $$
BEGIN
    RETURN MD5(analysis_result::TEXT);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create trigger to auto-generate analysis_hash
CREATE OR REPLACE FUNCTION set_analysis_hash()
RETURNS TRIGGER AS $$
BEGIN
    NEW.analysis_hash = generate_analysis_hash(NEW.analysis_result);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists and create new one
DROP TRIGGER IF EXISTS trigger_set_analysis_hash ON public.holistic_analysis_results;
CREATE TRIGGER trigger_set_analysis_hash
    BEFORE INSERT OR UPDATE OF analysis_result ON public.holistic_analysis_results
    FOR EACH ROW
    EXECUTE FUNCTION set_analysis_hash();

-- Add unique constraint to prevent duplicate analysis per user/type/date (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'unique_analysis_per_user_type_date'
        AND table_name = 'holistic_analysis_results'
    ) THEN
        ALTER TABLE public.holistic_analysis_results 
        ADD CONSTRAINT unique_analysis_per_user_type_date 
        UNIQUE (user_id, analysis_type, analysis_date, archetype);
    END IF;
EXCEPTION
    WHEN duplicate_table THEN
        -- Constraint already exists, continue
        NULL;
    WHEN unique_violation THEN
        -- Existing duplicates prevent constraint, we'll handle this below
        RAISE NOTICE 'Cannot add unique constraint due to existing duplicates. Run cleanup first.';
END $$;

-- Create index on analysis_hash for fast duplicate detection
CREATE INDEX IF NOT EXISTS idx_analysis_hash 
ON public.holistic_analysis_results (user_id, analysis_hash);

-- 2. holistic_shortterm_memory: Add content_hash for duplicate detection
-- Note: We cannot use GENERATED columns with timezone conversion, so we'll use a regular column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'holistic_shortterm_memory' 
        AND column_name = 'created_date'
    ) THEN
        -- Add created_date as a regular column
        ALTER TABLE public.holistic_shortterm_memory 
        ADD COLUMN created_date DATE;
        
        -- Update existing rows with the date portion of created_at
        UPDATE public.holistic_shortterm_memory 
        SET created_date = created_at::DATE
        WHERE created_date IS NULL;
        
        -- Create trigger to automatically set created_date
        CREATE OR REPLACE FUNCTION set_created_date()
        RETURNS TRIGGER AS $_$
        BEGIN
            NEW.created_date = NEW.created_at::DATE;
            RETURN NEW;
        END;
        $_$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trigger_set_created_date
            BEFORE INSERT OR UPDATE OF created_at ON public.holistic_shortterm_memory
            FOR EACH ROW
            EXECUTE FUNCTION set_created_date();
        
        -- Create index for performance
        CREATE INDEX idx_shortterm_memory_created_date 
        ON public.holistic_shortterm_memory (user_id, memory_category, created_date);
    END IF;
END $$;

-- Add content_hash column for better duplicate detection
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'holistic_shortterm_memory' 
        AND column_name = 'content_hash'
    ) THEN
        ALTER TABLE public.holistic_shortterm_memory
        ADD COLUMN content_hash TEXT;
        
        -- Create function to generate content hash
        CREATE OR REPLACE FUNCTION generate_content_hash(content JSONB)
        RETURNS TEXT AS $_$
        BEGIN
            RETURN MD5(content::TEXT);
        END;
        $_$ LANGUAGE plpgsql IMMUTABLE;
        
        -- Create trigger to auto-generate content_hash
        CREATE OR REPLACE FUNCTION set_content_hash()
        RETURNS TRIGGER AS $_$
        BEGIN
            NEW.content_hash = generate_content_hash(NEW.content);
            RETURN NEW;
        END;
        $_$ LANGUAGE plpgsql;
        
        DROP TRIGGER IF EXISTS trigger_set_content_hash ON public.holistic_shortterm_memory;
        CREATE TRIGGER trigger_set_content_hash
            BEFORE INSERT OR UPDATE OF content ON public.holistic_shortterm_memory
            FOR EACH ROW
            EXECUTE FUNCTION set_content_hash();
        
        -- Update existing rows with content_hash
        UPDATE public.holistic_shortterm_memory
        SET content_hash = generate_content_hash(content)
        WHERE content_hash IS NULL;
    END IF;
END $$;

-- Add unique constraint using content_hash (only if columns exist)
DO $$
BEGIN
    -- First check if all required columns exist
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'holistic_shortterm_memory' 
        AND column_name = 'created_date'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'holistic_shortterm_memory' 
        AND column_name = 'content_hash'
    ) THEN
        -- Check if constraint doesn't already exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'unique_analysis_result_per_day'
            AND table_name = 'holistic_shortterm_memory'
        ) THEN
            -- Try to add constraint
            BEGIN
                ALTER TABLE public.holistic_shortterm_memory
                ADD CONSTRAINT unique_analysis_result_per_day
                UNIQUE (user_id, memory_category, created_date, content_hash);
            EXCEPTION
                WHEN unique_violation THEN
                    RAISE NOTICE 'Cannot add unique constraint to shortterm_memory due to existing duplicates. Run cleanup first.';
            END;
        END IF;
    END IF;
END $$;

-- 3. holistic_working_memory: Fix the partial unique constraint syntax
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'unique_analysis_context_per_session'
        AND table_name = 'holistic_working_memory'
    ) THEN
        -- Create a partial unique index instead of constraint with WHERE clause
        CREATE UNIQUE INDEX unique_analysis_context_per_session
        ON public.holistic_working_memory (user_id, session_id, memory_type)
        WHERE memory_type = 'analysis_context';
    END IF;
EXCEPTION
    WHEN duplicate_table THEN
        NULL;
END $$;

-- 4. Create function to detect and mark duplicates in holistic_analysis_results
CREATE OR REPLACE FUNCTION mark_analysis_duplicates()
RETURNS INTEGER AS $$
DECLARE
    duplicate_count INTEGER := 0;
    rec RECORD;
BEGIN
    -- Update analysis_hash for existing records that don't have it
    UPDATE public.holistic_analysis_results 
    SET analysis_hash = generate_analysis_hash(analysis_result)
    WHERE analysis_hash IS NULL;
    
    -- Find and mark duplicates based on analysis_hash
    FOR rec IN 
        SELECT user_id, analysis_hash, array_agg(id ORDER BY created_at) as ids
        FROM public.holistic_analysis_results 
        WHERE analysis_hash IS NOT NULL
        GROUP BY user_id, analysis_hash 
        HAVING COUNT(*) > 1
    LOOP
        -- Keep the first (oldest) record, mark others as duplicates
        UPDATE public.holistic_analysis_results 
        SET is_duplicate = TRUE,
            original_analysis_id = rec.ids[1]
        WHERE id = ANY(rec.ids[2:]);
        
        duplicate_count := duplicate_count + array_length(rec.ids, 1) - 1;
    END LOOP;
    
    RETURN duplicate_count;
END;
$$ LANGUAGE plpgsql;

-- 5. Create function to clean up shortterm memory duplicates
CREATE OR REPLACE FUNCTION cleanup_shortterm_memory_duplicates()
RETURNS INTEGER AS $$
DECLARE
    cleanup_count INTEGER := 0;
BEGIN
    -- Update content_hash for existing records that don't have it
    UPDATE public.holistic_shortterm_memory 
    SET content_hash = generate_content_hash(content)
    WHERE content_hash IS NULL;
    
    -- Update created_date for existing records that don't have it
    UPDATE public.holistic_shortterm_memory 
    SET created_date = created_at::DATE
    WHERE created_date IS NULL;
    
    -- Remove duplicate analysis_results entries, keeping the most recent
    WITH duplicates AS (
        SELECT id, ROW_NUMBER() OVER (
            PARTITION BY user_id, memory_category, 
            COALESCE(created_date, created_at::DATE), 
            content_hash
            ORDER BY created_at DESC
        ) as rn
        FROM public.holistic_shortterm_memory
        WHERE memory_category = 'analysis_results'
    )
    DELETE FROM public.holistic_shortterm_memory 
    WHERE id IN (
        SELECT id FROM duplicates WHERE rn > 1
    );
    
    GET DIAGNOSTICS cleanup_count = ROW_COUNT;
    RETURN cleanup_count;
END;
$$ LANGUAGE plpgsql;

-- 6. Create view for clean analysis results (excluding duplicates)
DROP VIEW IF EXISTS public.clean_analysis_results;
CREATE VIEW public.clean_analysis_results AS
SELECT * FROM public.holistic_analysis_results 
WHERE COALESCE(is_duplicate, FALSE) = FALSE;

-- Grant permissions
GRANT SELECT ON public.clean_analysis_results TO authenticated;
GRANT SELECT ON public.clean_analysis_results TO service_role;
GRANT EXECUTE ON FUNCTION mark_analysis_duplicates() TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_shortterm_memory_duplicates() TO service_role;
GRANT EXECUTE ON FUNCTION generate_analysis_hash(JSONB) TO service_role;

-- Also grant on generate_content_hash if it was created
DO $$
BEGIN
    GRANT EXECUTE ON FUNCTION generate_content_hash(JSONB) TO service_role;
EXCEPTION
    WHEN undefined_function THEN
        NULL;
END $$;

-- 7. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_holistic_analysis_user_type_date 
ON public.holistic_analysis_results (user_id, analysis_type, analysis_date);

CREATE INDEX IF NOT EXISTS idx_holistic_shortterm_content_hash 
ON public.holistic_shortterm_memory (user_id, content_hash)
WHERE content_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_holistic_working_session_type 
ON public.holistic_working_memory (user_id, session_id, memory_type);

-- 8. Add comments for documentation
COMMENT ON COLUMN public.holistic_analysis_results.analysis_hash 
IS 'MD5 hash of analysis_result content for duplicate detection';

COMMENT ON COLUMN public.holistic_analysis_results.is_duplicate 
IS 'Marks entries that are duplicates of earlier analyses';

-- Add comments only if columns exist
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'holistic_shortterm_memory' 
        AND column_name = 'content_hash'
    ) THEN
        COMMENT ON COLUMN public.holistic_shortterm_memory.content_hash 
        IS 'MD5 hash of content for duplicate detection';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'holistic_shortterm_memory' 
        AND column_name = 'created_date'
    ) THEN
        COMMENT ON COLUMN public.holistic_shortterm_memory.created_date 
        IS 'Date portion of created_at for daily deduplication';
    END IF;
END $$;

COMMENT ON VIEW public.clean_analysis_results 
IS 'View of analysis results excluding duplicates';

-- Summary of what to run after this migration:
-- 1. Mark existing duplicates: SELECT mark_analysis_duplicates();
-- 2. Clean shortterm memory: SELECT cleanup_shortterm_memory_duplicates();
-- 3. Verify: SELECT COUNT(*) FROM clean_analysis_results;