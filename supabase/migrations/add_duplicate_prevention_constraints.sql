-- Migration: Add Duplicate Prevention Constraints to Analysis Tables
-- Purpose: Prevent duplicate analysis entries and clean up existing data structure
-- Date: 2025-08-15

-- Add unique constraints to prevent duplicate analyses
-- Note: These constraints will help identify and prevent future duplicates

-- 1. holistic_analysis_results: Prevent duplicate analysis per user/type/date
ALTER TABLE public.holistic_analysis_results 
ADD CONSTRAINT unique_analysis_per_user_type_date 
UNIQUE (user_id, analysis_type, analysis_date, archetype);

-- 2. holistic_shortterm_memory: Add created_date for better duplicate detection  
ALTER TABLE public.holistic_shortterm_memory 
ADD COLUMN IF NOT EXISTS created_date DATE GENERATED ALWAYS AS (created_at::DATE) STORED;

-- Create index for performance on the generated column
CREATE INDEX IF NOT EXISTS idx_shortterm_memory_created_date 
ON public.holistic_shortterm_memory (user_id, memory_category, created_date);

-- 3. Add unique constraint to shortterm memory to prevent duplicate analysis results per day
ALTER TABLE public.holistic_shortterm_memory
ADD CONSTRAINT unique_analysis_result_per_day
UNIQUE (user_id, memory_category, created_date, content) 
DEFERRABLE INITIALLY DEFERRED;

-- 4. holistic_working_memory: Prevent duplicate analysis_context per session
ALTER TABLE public.holistic_working_memory
ADD CONSTRAINT unique_analysis_context_per_session
UNIQUE (user_id, session_id, memory_type)
WHERE memory_type = 'analysis_context';

-- 5. Add analysis_hash column to holistic_analysis_results for content deduplication
ALTER TABLE public.holistic_analysis_results
ADD COLUMN IF NOT EXISTS analysis_hash TEXT;

-- Create function to generate analysis hash
CREATE OR REPLACE FUNCTION generate_analysis_hash(analysis_result TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN MD5(analysis_result);
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

-- Apply trigger to holistic_analysis_results
CREATE TRIGGER trigger_set_analysis_hash
    BEFORE INSERT OR UPDATE OF analysis_result ON public.holistic_analysis_results
    FOR EACH ROW
    EXECUTE FUNCTION set_analysis_hash();

-- Create index on analysis_hash for fast duplicate detection
CREATE INDEX IF NOT EXISTS idx_analysis_hash 
ON public.holistic_analysis_results (user_id, analysis_hash);

-- 6. Add metadata columns for better tracking
ALTER TABLE public.holistic_analysis_results
ADD COLUMN IF NOT EXISTS data_source_hash TEXT, -- Hash of input data used
ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS original_analysis_id UUID REFERENCES public.holistic_analysis_results(id);

-- Create function to detect and mark duplicates
CREATE OR REPLACE FUNCTION mark_analysis_duplicates()
RETURNS INTEGER AS $$
DECLARE
    duplicate_count INTEGER := 0;
    rec RECORD;
BEGIN
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

-- 7. Create view for clean analysis results (excluding duplicates)
CREATE OR REPLACE VIEW public.clean_analysis_results AS
SELECT * FROM public.holistic_analysis_results 
WHERE is_duplicate IS FALSE OR is_duplicate IS NULL;

GRANT SELECT ON public.clean_analysis_results TO authenticated;
GRANT SELECT ON public.clean_analysis_results TO service_role;

-- 8. Add function to clean up shortterm memory duplicates
CREATE OR REPLACE FUNCTION cleanup_shortterm_memory_duplicates()
RETURNS INTEGER AS $$
DECLARE
    cleanup_count INTEGER := 0;
BEGIN
    -- Remove duplicate analysis_results entries, keeping the most recent
    WITH duplicates AS (
        SELECT id, ROW_NUMBER() OVER (
            PARTITION BY user_id, memory_category, created_date, 
            MD5(content::TEXT) 
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

-- 9. Add comments for documentation
COMMENT ON CONSTRAINT unique_analysis_per_user_type_date ON public.holistic_analysis_results 
IS 'Prevents duplicate analysis results for same user/type/date/archetype combination';

COMMENT ON CONSTRAINT unique_analysis_result_per_day ON public.holistic_shortterm_memory 
IS 'Prevents duplicate analysis results in shortterm memory per day';

COMMENT ON CONSTRAINT unique_analysis_context_per_session ON public.holistic_working_memory 
IS 'Ensures only one analysis_context per session in working memory';

COMMENT ON COLUMN public.holistic_analysis_results.analysis_hash 
IS 'MD5 hash of analysis_result content for duplicate detection';

COMMENT ON COLUMN public.holistic_analysis_results.is_duplicate 
IS 'Marks entries that are duplicates of earlier analyses';

COMMENT ON VIEW public.clean_analysis_results 
IS 'View of analysis results excluding duplicates';

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION mark_analysis_duplicates() TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_shortterm_memory_duplicates() TO service_role;
GRANT EXECUTE ON FUNCTION generate_analysis_hash(TEXT) TO service_role;

-- Note: To apply these constraints to existing data, run:
-- SELECT mark_analysis_duplicates();
-- SELECT cleanup_shortterm_memory_duplicates();