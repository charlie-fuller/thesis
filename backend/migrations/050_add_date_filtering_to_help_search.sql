-- Add date filtering capability to help chunk search
-- Allows filtering results by creation date for recency queries like "this week's docs"

-- Drop and recreate the function with new parameter
CREATE OR REPLACE FUNCTION match_help_chunks(
    query_embedding VECTOR(1536),
    match_count INT,
    user_role TEXT DEFAULT 'user',
    min_date TIMESTAMPTZ DEFAULT NULL,
    min_similarity FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    heading_context TEXT,
    document_id UUID,
    document_title TEXT,
    file_path TEXT,
    similarity FLOAT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Increase probes for better recall with IVFFlat index
    SET LOCAL ivfflat.probes = 10;

    RETURN QUERY
    SELECT
        hc.id,
        hc.content,
        hc.heading_context,
        hc.document_id,
        hd.title AS document_title,
        hd.file_path,
        1 - (hc.embedding <=> query_embedding) AS similarity,
        hc.created_at
    FROM help_chunks hc
    JOIN help_documents hd ON hd.id = hc.document_id
    WHERE
        (user_role = 'admin' OR user_role = ANY(hc.role_access))
        AND (min_date IS NULL OR hc.created_at >= min_date)
        AND (1 - (hc.embedding <=> query_embedding)) >= min_similarity
    ORDER BY hc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_help_chunks IS 'Vector similarity search for help documentation with date filtering, minimum similarity threshold, and increased IVFFlat probes for better recall.';

-- Add index on created_at for faster date filtering if not exists
CREATE INDEX IF NOT EXISTS idx_help_chunks_created_at ON help_chunks(created_at);
CREATE INDEX IF NOT EXISTS idx_help_documents_created_at ON help_documents(created_at);
