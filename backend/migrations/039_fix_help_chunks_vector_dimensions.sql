-- Migration: Fix help_chunks embedding dimensions
-- The help system was originally created with 1536-dimension vectors (OpenAI)
-- but Thesis uses Voyage AI voyage-3 which outputs 1024 dimensions

-- Drop the index first (required before altering column type)
DROP INDEX IF EXISTS help_chunks_embedding_idx;

-- Alter the embedding column to use 1024 dimensions
ALTER TABLE help_chunks
ALTER COLUMN embedding TYPE VECTOR(1024);

-- Recreate the index with correct dimensions
CREATE INDEX help_chunks_embedding_idx ON help_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Update the match function to use correct dimensions
DROP FUNCTION IF EXISTS match_help_chunks(VECTOR(1536), INT, TEXT);

CREATE OR REPLACE FUNCTION match_help_chunks(
    query_embedding VECTOR(1024),
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
    WHERE user_role = ANY(hc.role_access)
    ORDER BY hc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_help_chunks IS 'Vector similarity search for help documentation (1024 dims for Voyage AI voyage-3)';
