-- Migration 022: Fix UUID Type Cast in match_document_chunks
-- Date: 2025-11-16
-- Purpose: Fix "operator does not exist: uuid = text" error in match_document_chunks function
--
-- ISSUE: The match_document_chunks function has filter_client_id parameter as TEXT,
--        but document_chunks.client_id is UUID. This causes type mismatch errors when
--        comparing them on line 178 of migration 020.
--
-- ERROR: operator does not exist: uuid = text
-- HINT: No operator matches the given name and argument types. You might need to add explicit type casts.
--
-- SOLUTION: Change filter_client_id parameter from TEXT to UUID to match the column type

-- ============================================================================
-- DROP AND RECREATE match_document_chunks WITH CORRECT TYPE
-- ============================================================================

-- Drop the existing function with wrong signature
DROP FUNCTION IF EXISTS match_document_chunks(vector(1024), int, text);

-- Recreate with correct UUID type for filter_client_id
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding vector(1024),
    match_count int DEFAULT 5,
    filter_client_id uuid DEFAULT NULL  -- Changed from 'text' to 'uuid'
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    conversation_id uuid,
    client_id uuid,  -- This is also UUID, not text
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
        dc.client_id,  -- Now properly typed as UUID
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
        -- Filter by client_id if provided (UUID = UUID comparison)
        (filter_client_id IS NULL OR dc.client_id = filter_client_id)
        -- Only return chunks that have embeddings
        AND dc.embedding IS NOT NULL
    ORDER BY
        -- Order by similarity (most similar first)
        dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_document_chunks IS 'Vector similarity search for document chunks using cosine distance. Returns chunks ordered by similarity to query_embedding. Fixed to use UUID type for client_id filter.';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check the function signature
SELECT
    proname as function_name,
    pg_get_function_arguments(oid) as arguments,
    pg_get_function_result(oid) as return_type
FROM pg_proc
WHERE proname = 'match_document_chunks';

-- ============================================================================
-- NOTES
-- ============================================================================
--
-- WHAT THIS FIXES:
-- - Changes filter_client_id parameter from TEXT to UUID
-- - Changes client_id return column from TEXT to UUID
-- - Ensures type consistency between function parameters and table columns
-- - Eliminates "operator does not exist: uuid = text" errors
--
-- NO BACKEND CHANGES NEEDED:
-- - Python code already passes client_id as-is from user object
-- - Supabase client handles type conversions automatically
-- - This is purely a database-level fix
--
-- ============================================================================
