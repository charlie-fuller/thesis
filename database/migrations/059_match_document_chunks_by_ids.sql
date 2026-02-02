-- Migration: 059_match_document_chunks_by_ids
-- Description: Add function to search document_chunks by specific document IDs
-- Used by DISCo chat to search linked KB documents

-- ============================================================================
-- Function: match_document_chunks_by_ids
-- Vector search within document_chunks table filtered by specific document IDs
-- ============================================================================

CREATE OR REPLACE FUNCTION match_document_chunks_by_ids(
    query_embedding VECTOR(1024),
    match_count INT,
    match_threshold FLOAT,
    p_document_ids UUID[]
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    chunk_index INT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.chunk_index,
        dc.content,
        dc.metadata,
        (1 - (dc.embedding <=> query_embedding))::FLOAT AS similarity
    FROM document_chunks dc
    WHERE dc.document_id = ANY(p_document_ids)
        AND (1 - (dc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_document_chunks_by_ids IS
    'Vector search within document_chunks filtered by specific document IDs. Used by DISCo chat to search linked KB documents.';
