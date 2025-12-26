-- Help System Tables
-- Stores help documentation for the AI-powered help chat

-- Help documents table
-- Tracks original help markdown files
CREATE TABLE IF NOT EXISTS help_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,  -- Path relative to docs/help/
    category TEXT NOT NULL,           -- 'admin', 'system', 'user', 'technical'
    role_access TEXT[] DEFAULT ARRAY['admin', 'user'],  -- Who can access this doc
    content TEXT NOT NULL,            -- Full markdown content
    word_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Help chunks table with embeddings
-- Stores searchable chunks of help documentation
CREATE TABLE IF NOT EXISTS help_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES help_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- Voyage AI embeddings
    chunk_index INTEGER NOT NULL,  -- Position in original document
    heading_context TEXT,  -- Section heading for this chunk
    role_access TEXT[] DEFAULT ARRAY['admin', 'user'],  -- Inherited from document
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Help conversations table
-- Tracks help chat history (separate from main conversations)
CREATE TABLE IF NOT EXISTS help_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    title TEXT DEFAULT 'Help Chat',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Help messages table
CREATE TABLE IF NOT EXISTS help_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES help_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB,  -- Referenced help documents/chunks
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS help_chunks_embedding_idx ON help_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS help_chunks_document_id_idx ON help_chunks(document_id);
CREATE INDEX IF NOT EXISTS help_chunks_role_access_idx ON help_chunks USING GIN(role_access);
CREATE INDEX IF NOT EXISTS help_messages_conversation_id_idx ON help_messages(conversation_id);
CREATE INDEX IF NOT EXISTS help_conversations_user_id_idx ON help_conversations(user_id);

-- Function to search help chunks (similar to match_document_chunks)
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
    WHERE user_role = ANY(hc.role_access)
    ORDER BY hc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant permissions (adjust based on your RLS setup)
ALTER TABLE help_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE help_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE help_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE help_messages ENABLE ROW LEVEL SECURITY;

-- Policy: Admins can see all help content
CREATE POLICY "Admins see all help content" ON help_documents
    FOR SELECT
    USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

CREATE POLICY "Admins see all help chunks" ON help_chunks
    FOR SELECT
    USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

-- Policy: Users can see content appropriate for their role
CREATE POLICY "Users see role-appropriate help content" ON help_documents
    FOR SELECT
    USING ((SELECT role FROM users WHERE id = auth.uid()) = ANY(role_access));

CREATE POLICY "Users see role-appropriate help chunks" ON help_chunks
    FOR SELECT
    USING ((SELECT role FROM users WHERE id = auth.uid()) = ANY(role_access));

-- Policy: Users can only see their own help conversations
CREATE POLICY "Users see own help conversations" ON help_conversations
    FOR ALL
    USING (user_id = auth.uid());

CREATE POLICY "Users see own help messages" ON help_messages
    FOR ALL
    USING (
        conversation_id IN (
            SELECT id FROM help_conversations WHERE user_id = auth.uid()
        )
    );

-- Comments for documentation
COMMENT ON TABLE help_documents IS 'Original help documentation files from docs/help/ directory';
COMMENT ON TABLE help_chunks IS 'Searchable chunks of help documentation with embeddings for RAG';
COMMENT ON TABLE help_conversations IS 'Help chat conversation history (separate from main conversations)';
COMMENT ON TABLE help_messages IS 'Messages in help chat conversations';
COMMENT ON FUNCTION match_help_chunks IS 'Vector similarity search for help documentation based on user role';
