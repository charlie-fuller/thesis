-- ============================================================================
-- MIGRATION: Add document_type filtering to vector search
-- Description: Creates a new RPC function that can filter/boost by document_type
--              for smarter RAG retrieval based on query intent
-- Author: Claude
-- Date: 2026-01-20
-- ============================================================================

-- New function that supports document_type filtering
CREATE OR REPLACE FUNCTION match_document_chunks_by_type(
    query_embedding vector(1024),
    match_count int DEFAULT 5,
    match_threshold float DEFAULT 0.0,
    p_client_id uuid DEFAULT NULL,
    p_user_id uuid DEFAULT NULL,
    p_document_types text[] DEFAULT NULL  -- Filter to specific document types
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    conversation_id uuid,
    client_id uuid,
    content text,
    embedding vector(1024),
    similarity float,
    metadata jsonb,
    source_type text,
    chunk_index int,
    created_at timestamptz,
    document_type text,
    primary_use_case text
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
        (1 - (dc.embedding <=> query_embedding))::float AS similarity,
        dc.metadata,
        dc.source_type,
        dc.chunk_index,
        dc.created_at,
        d.document_type::text,
        d.primary_use_case::text
    FROM public.document_chunks dc
    LEFT JOIN public.documents d ON dc.document_id = d.id
    WHERE
        -- Filter by client_id if provided
        (p_client_id IS NULL OR dc.client_id = p_client_id)
        -- Filter by user_id if provided
        AND (p_user_id IS NULL OR d.uploaded_by = p_user_id)
        -- Filter by document_type if provided
        AND (p_document_types IS NULL OR d.document_type::text = ANY(p_document_types))
        -- Only return chunks that have embeddings
        AND dc.embedding IS NOT NULL
        -- Apply similarity threshold
        AND (1 - (dc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY
        dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_document_chunks_by_type IS
'Vector similarity search with document_type filtering. Use p_document_types to filter to specific types like transcript, article, etc.';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Usage example:
-- SELECT * FROM match_document_chunks_by_type(
--     query_embedding := <embedding>,
--     match_count := 10,
--     match_threshold := 0.1,
--     p_client_id := 'uuid',
--     p_document_types := ARRAY['transcript', 'notes']
-- );
