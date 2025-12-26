-- Fix IVFFlat index to use more probes for better recall
-- The default of 1 probe can miss results for certain query embeddings
-- Increasing probes improves accuracy at a small performance cost

-- Option 1: Set probes at session level in the function
CREATE OR REPLACE FUNCTION match_help_chunks(
    query_embedding VECTOR(1536),
    match_count INT,
    user_role TEXT DEFAULT 'user'
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    heading_context TEXT,
    document_id UUID,
    document_title TEXT,
    file_path TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Increase probes for better recall with IVFFlat index
    -- Default is 1, we use 10 for much better accuracy
    SET LOCAL ivfflat.probes = 10;

    RETURN QUERY
    SELECT
        hc.id,
        hc.content,
        hc.heading_context,
        hc.document_id,
        hd.title AS document_title,
        hd.file_path,
        1 - (hc.embedding <=> query_embedding) AS similarity
    FROM help_chunks hc
    JOIN help_documents hd ON hd.id = hc.document_id
    WHERE
        user_role = 'admin' OR user_role = ANY(hc.role_access)
    ORDER BY hc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_help_chunks IS 'Vector similarity search for help documentation with increased IVFFlat probes for better recall.';
