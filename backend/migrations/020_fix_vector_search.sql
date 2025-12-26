-- Migration 020: Fix Vector Search and Add Missing RPC Function
-- Date: 2025-11-16
-- Purpose: Create missing match_document_chunks function and fix vector dimensions
--
-- ISSUE: Vector search fails because match_document_chunks() PostgreSQL function doesn't exist
--        Also, vector dimensions may be inconsistent (1536 vs 1024)
--
-- SOLUTION:
-- 1. Enable pgvector extension
-- 2. Fix embedding column to use correct dimensions (1024 for Voyage AI)
-- 3. Create match_document_chunks() RPC function for vector similarity search
-- 4. Add proper indexes for vector search performance

-- ============================================================================
-- STEP 1: ENABLE PGVECTOR EXTENSION
-- ============================================================================

-- Enable pgvector extension (required for vector operations)
CREATE EXTENSION IF NOT EXISTS vector;

COMMENT ON EXTENSION vector IS 'Vector similarity search extension for embeddings';


-- ============================================================================
-- STEP 2: FIX EMBEDDING COLUMN DIMENSIONS
-- ============================================================================

-- Check if embedding column exists and update its dimensions
-- Voyage AI (voyage-3) generates 1024-dimensional vectors, not 1536
-- Note: This operation may fail if there's existing data with wrong dimensions
-- In that case, you'll need to regenerate embeddings

DO $$
DECLARE
    current_dimension int;
    chunk_count int;
BEGIN
    -- Check if the column exists and get its current dimension
    BEGIN
        SELECT atttypmod - 4 INTO current_dimension
        FROM pg_attribute
        WHERE attrelid = 'public.document_chunks'::regclass
        AND attname = 'embedding'
        AND NOT attisdropped;

        IF current_dimension IS NULL THEN
            -- Column doesn't exist, create it
            ALTER TABLE public.document_chunks
            ADD COLUMN IF NOT EXISTS embedding vector(1024);
            RAISE NOTICE 'Created new embedding column as vector(1024)';
        ELSIF current_dimension = 1024 THEN
            -- Already correct dimension
            RAISE NOTICE 'Embedding column already has correct dimension (1024)';
        ELSE
            -- Different dimension, check if there's data
            SELECT COUNT(*) INTO chunk_count
            FROM public.document_chunks
            WHERE embedding IS NOT NULL;

            IF chunk_count = 0 THEN
                -- No data, safe to change
                ALTER TABLE public.document_chunks
                ALTER COLUMN embedding TYPE vector(1024);
                RAISE NOTICE 'Updated embedding column from vector(%) to vector(1024)', current_dimension;
            ELSE
                -- Has data, risky to change
                RAISE WARNING 'Cannot change embedding dimension from % to 1024: % chunks exist. You need to delete chunks and regenerate embeddings.', current_dimension, chunk_count;
                RAISE WARNING 'Run: DELETE FROM document_chunks WHERE embedding IS NOT NULL;';
            END IF;
        END IF;
    EXCEPTION
        WHEN undefined_table THEN
            RAISE EXCEPTION 'Table document_chunks does not exist. Run earlier migrations first.';
        WHEN OTHERS THEN
            RAISE WARNING 'Could not check/alter embedding column: %', SQLERRM;
    END;
END $$;

COMMENT ON COLUMN public.document_chunks.embedding IS '1024-dimensional vector embedding from Voyage AI (voyage-3 model)';


-- ============================================================================
-- STEP 3: CREATE VECTOR SIMILARITY SEARCH INDEXES
-- ============================================================================

-- Create HNSW index for fast vector similarity search
-- Using cosine distance operator (<=>) which is what the code uses
-- Note: This will only succeed if the embedding column has correct type
DO $$
BEGIN
    -- Try to create HNSW index
    CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_cosine
    ON public.document_chunks
    USING hnsw (embedding vector_cosine_ops);

    RAISE NOTICE 'Created HNSW index for vector similarity search';
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Could not create HNSW index: %. This is expected if embedding column needs dimension change.', SQLERRM;
        RAISE WARNING 'You can create the index manually after fixing embeddings with: CREATE INDEX idx_document_chunks_embedding_cosine ON document_chunks USING hnsw (embedding vector_cosine_ops);';
END $$;

-- Alternative: IVFFlat index (more memory efficient but slower)
-- Uncomment and use this if HNSW doesn't work or you have limited memory:
-- CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_ivfflat
-- ON public.document_chunks
-- USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create index on client_id for filtering
CREATE INDEX IF NOT EXISTS idx_document_chunks_client_id
ON public.document_chunks(client_id);


-- ============================================================================
-- STEP 4: CREATE MATCH_DOCUMENT_CHUNKS RPC FUNCTION
-- ============================================================================

-- This is the CRITICAL missing function that the backend code calls
-- Location: backend/document_processor.py:457

-- First, drop any existing versions of this function (with any signature)
-- This handles functions with different vector dimensions (1024, 1536, etc.)
DO $$
DECLARE
    func_record RECORD;
BEGIN
    -- Find and drop all functions named 'match_document_chunks'
    FOR func_record IN
        SELECT oid::regprocedure AS func_signature
        FROM pg_proc
        WHERE proname = 'match_document_chunks'
    LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS ' || func_record.func_signature || ' CASCADE';
        RAISE NOTICE 'Dropped existing function: %', func_record.func_signature;
    END LOOP;
END $$;

-- Now create the function with the correct signature
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding vector(1024),
    match_count int DEFAULT 5,
    filter_client_id text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    conversation_id uuid,
    client_id text,
    content text,
    embedding vector(1024),
    similarity float,
    metadata jsonb,
    source_type text,
    chunk_index int,
    created_at timestamptz
)
LANGUAGE plpgsql STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.conversation_id,
        dc.client_id,
        dc.content,
        dc.embedding,
        -- Calculate similarity score (1 - cosine distance = cosine similarity)
        -- Higher score = more similar (range 0-1)
        (1 - (dc.embedding <=> query_embedding))::float AS similarity,
        dc.metadata,
        dc.source_type,
        dc.chunk_index,
        dc.created_at
    FROM public.document_chunks dc
    WHERE
        -- Filter by client_id if provided
        (filter_client_id IS NULL OR dc.client_id = filter_client_id)
        -- Only return chunks that have embeddings
        AND dc.embedding IS NOT NULL
    ORDER BY
        -- Order by similarity (most similar first)
        dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_document_chunks IS 'Vector similarity search for document chunks using cosine distance. Returns chunks ordered by similarity to query_embedding.';


-- ============================================================================
-- STEP 5: CREATE HELPER FUNCTION TO CHECK EMBEDDING QUALITY
-- ============================================================================

-- Utility function to check if embeddings are valid (not all zeros)
CREATE OR REPLACE FUNCTION is_valid_embedding(emb vector(1024))
RETURNS boolean
LANGUAGE plpgsql IMMUTABLE
AS $$
DECLARE
    magnitude float;
BEGIN
    -- Calculate vector magnitude (L2 norm)
    -- Note: <#> operator is NEGATIVE inner product, so we negate it
    -- L2 norm = sqrt(v · v) = sqrt(-(v <#> v))
    -- If magnitude is 0 or very close to 0, embedding is invalid
    magnitude := sqrt((-(emb <#> emb))::float);
    RETURN magnitude > 0.0001;
END;
$$;

COMMENT ON FUNCTION is_valid_embedding IS 'Checks if a vector embedding is valid (non-zero magnitude)';


-- ============================================================================
-- STEP 6: ADD STATISTICS FOR QUERY OPTIMIZATION
-- ============================================================================

-- Analyze the table to update statistics for better query planning
ANALYZE public.document_chunks;


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check pgvector extension is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check embedding column definition
SELECT
    column_name,
    data_type,
    udt_name,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'document_chunks'
AND column_name = 'embedding';

-- Check indexes on document_chunks
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'document_chunks'
ORDER BY indexname;

-- Check function exists
SELECT
    proname as function_name,
    pg_get_functiondef(oid) as definition
FROM pg_proc
WHERE proname = 'match_document_chunks';

-- Count chunks with valid embeddings
SELECT
    COUNT(*) as total_chunks,
    COUNT(embedding) as chunks_with_embeddings,
    COUNT(CASE WHEN is_valid_embedding(embedding) THEN 1 END) as valid_embeddings
FROM public.document_chunks
WHERE embedding IS NOT NULL;

-- Test the function (replace with actual values)
-- SELECT * FROM match_document_chunks(
--     query_embedding := (SELECT embedding FROM document_chunks LIMIT 1),
--     match_count := 5,
--     filter_client_id := 'your-client-id-here'
-- );


-- ============================================================================
-- NOTES FOR DEPLOYMENT
-- ============================================================================
--
-- BEFORE RUNNING THIS MIGRATION:
-- ✓ Backup your database
-- ✓ Check if you have existing embeddings
-- ✓ Verify Supabase supports pgvector extension
--
-- AFTER RUNNING THIS MIGRATION:
-- 1. If embedding column dimension change fails:
--    - You may need to delete existing chunks and regenerate embeddings
--    - Run: DELETE FROM document_chunks; (WARNING: Destructive!)
--    - Then reprocess all documents via /api/documents/{id}/process
--
-- 2. Test the vector search:
--    - Upload a text file to KB
--    - Process it to generate embeddings
--    - Try querying via chat - should now work!
--
-- 3. Monitor performance:
--    - HNSW index is fast but uses more memory
--    - If you have millions of chunks, consider IVFFlat instead
--
-- 4. Regenerate embeddings if needed:
--    - Any documents processed before this migration may have wrong dimensions
--    - Use the /api/documents/{id}/process endpoint to reprocess
--
-- TROUBLESHOOTING:
-- - If "pgvector extension not available": Contact Supabase support
-- - If "invalid vector dimension": Clear chunks and regenerate
-- - If searches are slow: Check index creation with \d+ document_chunks
--
-- ============================================================================
