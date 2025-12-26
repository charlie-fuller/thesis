-- Fix match_help_chunks to allow admin to see all chunks
-- Previously admin could only see chunks with role_access containing 'admin'
-- Now admin can see all chunks (admin + user docs)

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
        -- Admin can see all content, users only see content marked for their role
        user_role = 'admin' OR user_role = ANY(hc.role_access)
    ORDER BY hc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_help_chunks IS 'Vector similarity search for help documentation. Admin sees all content, users see role-appropriate content.';
