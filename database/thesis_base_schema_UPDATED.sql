-- ============================================================================
-- THESIS COMPLETE DATABASE SCHEMA (UPDATED)
-- Run this once on a fresh Supabase project OR run on existing database
-- This version includes all tables from migrations and uses DROP POLICY IF EXISTS
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Clients (tenants)
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    assistant_name VARCHAR(100) DEFAULT 'Thesis',
    organization TEXT,
    system_instructions TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default client
INSERT INTO clients (id, name, assistant_name)
VALUES ('00000000-0000-0000-0000-000000000001', 'Default Organization', 'Thesis')
ON CONFLICT (id) DO NOTHING;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    client_id UUID REFERENCES clients(id) DEFAULT '00000000-0000-0000-0000-000000000001',
    avatar_url TEXT,
    storage_quota BIGINT DEFAULT 524288000, -- 500MB default
    storage_used BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    title VARCHAR(500) DEFAULT 'New Conversation',
    archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMPTZ,
    in_knowledge_base BOOLEAN DEFAULT FALSE,
    added_to_kb_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(100),
    mime_type VARCHAR(100),
    file_size BIGINT DEFAULT 0,
    storage_url TEXT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error TEXT,
    chunk_count INTEGER DEFAULT 0,
    access_count INTEGER DEFAULT 0,
    is_core_document BOOLEAN DEFAULT FALSE,
    source_platform VARCHAR(50) DEFAULT 'upload',
    external_url TEXT,
    google_drive_file_id VARCHAR(255),
    notion_page_id VARCHAR(255),
    sync_cadence VARCHAR(50) DEFAULT 'manual',
    last_synced_at TIMESTAMPTZ,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document chunks (for RAG)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024), -- Voyage AI embeddings
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- USER FEATURES
-- ============================================================================

-- Quick prompts
CREATE TABLE IF NOT EXISTS user_quick_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    prompt_text TEXT NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_auto_generated BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INTEGRATIONS
-- ============================================================================

-- OAuth states (for Google Drive, Notion)
CREATE TABLE IF NOT EXISTS oauth_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) DEFAULT 'google',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '10 minutes')
);

-- Google Drive tokens
CREATE TABLE IF NOT EXISTS google_drive_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT NOT NULL,
    token_expiry TIMESTAMPTZ,
    email VARCHAR(255),
    folder_id VARCHAR(255),
    folder_name VARCHAR(255),
    sync_cadence VARCHAR(50) DEFAULT 'manual',
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notion tokens
CREATE TABLE IF NOT EXISTS notion_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_access_token TEXT NOT NULL,
    workspace_id VARCHAR(255),
    workspace_name VARCHAR(255),
    bot_id VARCHAR(255),
    sync_cadence VARCHAR(50) DEFAULT 'manual',
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Google Drive sync log
CREATE TABLE IF NOT EXISTS google_drive_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    folder_id VARCHAR(255),
    folder_name VARCHAR(255),
    sync_type VARCHAR(50) DEFAULT 'full',
    documents_added INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_skipped INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER
);

-- Notion sync log
CREATE TABLE IF NOT EXISTS notion_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    page_id VARCHAR(255),
    page_name VARCHAR(255),
    sync_type VARCHAR(50) DEFAULT 'full',
    documents_added INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_skipped INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER
);

-- ============================================================================
-- ADMIN FEATURES
-- ============================================================================

-- Interview sessions (for voice interview pipeline)
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL UNIQUE,
    session_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata JSONB
);

-- Interview extractions (structured data from voice interviews)
CREATE TABLE IF NOT EXISTS interview_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    transcript TEXT NOT NULL,
    extraction_json JSONB,
    audio_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending_solomon',
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    review_reason TEXT,
    completeness_score INTEGER,
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Extractions (system instruction configurations and function selections)
CREATE TABLE IF NOT EXISTS extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    extraction_json JSONB NOT NULL,
    deployment_status TEXT NOT NULL DEFAULT 'draft',
    deployed_at TIMESTAMPTZ,
    deployed_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Solomon reviews (human review queue for AI-generated system instructions)
CREATE TABLE IF NOT EXISTS solomon_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extraction_id UUID REFERENCES interview_extractions(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    generated_instructions TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES users(id),
    deployment_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- System instruction document mappings
CREATE TABLE IF NOT EXISTS system_instruction_document_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    placeholder_key VARCHAR(100) NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, placeholder_key)
);

-- API usage logs
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    tokens_used INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10, 6) DEFAULT 0,
    operation TEXT,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Theme settings
CREATE TABLE IF NOT EXISTS theme_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    color_primary VARCHAR(7) DEFAULT '#6366f1',
    color_primary_hover VARCHAR(7) DEFAULT '#4f46e5',
    color_secondary VARCHAR(7) DEFAULT '#8b5cf6',
    color_bg_page VARCHAR(7) DEFAULT '#0a0a0a',
    color_bg_card VARCHAR(7) DEFAULT '#111111',
    color_bg_hover VARCHAR(7) DEFAULT '#1a1a1a',
    color_text_primary VARCHAR(7) DEFAULT '#ffffff',
    color_text_secondary VARCHAR(7) DEFAULT '#a1a1aa',
    color_text_muted VARCHAR(7) DEFAULT '#71717a',
    color_border VARCHAR(7) DEFAULT '#27272a',
    color_border_focus VARCHAR(7) DEFAULT '#6366f1',
    color_success VARCHAR(7) DEFAULT '#22c55e',
    color_warning VARCHAR(7) DEFAULT '#f59e0b',
    color_error VARCHAR(7) DEFAULT '#ef4444',
    font_family_heading VARCHAR(100) DEFAULT 'Inter, system-ui, sans-serif',
    font_family_body VARCHAR(100) DEFAULT 'Inter, system-ui, sans-serif',
    font_size_base VARCHAR(10) DEFAULT '16px',
    border_radius_sm VARCHAR(10) DEFAULT '0.25rem',
    border_radius_md VARCHAR(10) DEFAULT '0.5rem',
    border_radius_lg VARCHAR(10) DEFAULT '0.75rem',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id)
);

-- Insert default theme
INSERT INTO theme_settings (client_id)
VALUES ('00000000-0000-0000-0000-000000000001')
ON CONFLICT (client_id) DO NOTHING;

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_client_id ON users(client_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_client_id ON conversations(client_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_client_id ON documents(client_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_user_quick_prompts_user_id ON user_quick_prompts(user_id);
CREATE INDEX IF NOT EXISTS idx_theme_settings_client_id ON theme_settings(client_id);
CREATE INDEX IF NOT EXISTS idx_google_drive_sync_log_user_id ON google_drive_sync_log(user_id);
CREATE INDEX IF NOT EXISTS idx_google_drive_sync_log_status ON google_drive_sync_log(status);
CREATE INDEX IF NOT EXISTS idx_notion_sync_log_user_id ON notion_sync_log(user_id);
CREATE INDEX IF NOT EXISTS idx_notion_sync_log_status ON notion_sync_log(status);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_client_id ON interview_sessions(client_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interview_extractions_client_id ON interview_extractions(client_id);
CREATE INDEX IF NOT EXISTS idx_interview_extractions_user_id ON interview_extractions(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_extractions_status ON interview_extractions(status);
CREATE INDEX IF NOT EXISTS idx_extractions_client_id ON extractions(client_id);
CREATE INDEX IF NOT EXISTS idx_extractions_user_id ON extractions(user_id);
CREATE INDEX IF NOT EXISTS idx_extractions_deployment_status ON extractions(deployment_status);
CREATE INDEX IF NOT EXISTS idx_extractions_created_at ON extractions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_solomon_reviews_extraction_id ON solomon_reviews(extraction_id);
CREATE INDEX IF NOT EXISTS idx_solomon_reviews_client_id ON solomon_reviews(client_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_client ON api_usage_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_operation ON api_usage_logs(operation);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage_logs(created_at DESC);

-- Vector similarity search index (HNSW for fast approximate nearest neighbor)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks
USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_quick_prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_drive_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE notion_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE theme_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_instruction_document_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_drive_sync_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE notion_sync_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE solomon_reviews ENABLE ROW LEVEL SECURITY;

-- Users policies
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

-- Conversations policies
DROP POLICY IF EXISTS "Users can view own conversations" ON conversations;
DROP POLICY IF EXISTS "Users can create conversations" ON conversations;
DROP POLICY IF EXISTS "Users can update own conversations" ON conversations;
DROP POLICY IF EXISTS "Users can delete own conversations" ON conversations;
CREATE POLICY "Users can view own conversations" ON conversations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create conversations" ON conversations FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own conversations" ON conversations FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own conversations" ON conversations FOR DELETE USING (auth.uid() = user_id);

-- Messages policies
DROP POLICY IF EXISTS "Users can view messages in own conversations" ON messages;
DROP POLICY IF EXISTS "Users can create messages in own conversations" ON messages;
CREATE POLICY "Users can view messages in own conversations" ON messages FOR SELECT
USING (EXISTS (SELECT 1 FROM conversations WHERE conversations.id = messages.conversation_id AND conversations.user_id = auth.uid()));
CREATE POLICY "Users can create messages in own conversations" ON messages FOR INSERT
WITH CHECK (EXISTS (SELECT 1 FROM conversations WHERE conversations.id = messages.conversation_id AND conversations.user_id = auth.uid()));

-- Documents policies
DROP POLICY IF EXISTS "Users can view own documents" ON documents;
DROP POLICY IF EXISTS "Users can upload documents" ON documents;
DROP POLICY IF EXISTS "Users can update own documents" ON documents;
DROP POLICY IF EXISTS "Users can delete own documents" ON documents;
CREATE POLICY "Users can view own documents" ON documents FOR SELECT USING (uploaded_by = auth.uid());
CREATE POLICY "Users can upload documents" ON documents FOR INSERT WITH CHECK (uploaded_by = auth.uid());
CREATE POLICY "Users can update own documents" ON documents FOR UPDATE USING (uploaded_by = auth.uid());
CREATE POLICY "Users can delete own documents" ON documents FOR DELETE USING (uploaded_by = auth.uid());

-- Document chunks policies
DROP POLICY IF EXISTS "Users can view chunks of own documents" ON document_chunks;
CREATE POLICY "Users can view chunks of own documents" ON document_chunks FOR SELECT
USING (EXISTS (SELECT 1 FROM documents WHERE documents.id = document_chunks.document_id AND documents.uploaded_by = auth.uid()));

-- Quick prompts policies
DROP POLICY IF EXISTS "Users can view own prompts" ON user_quick_prompts;
DROP POLICY IF EXISTS "Users can manage own prompts" ON user_quick_prompts;
CREATE POLICY "Users can view own prompts" ON user_quick_prompts FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can manage own prompts" ON user_quick_prompts FOR ALL USING (user_id = auth.uid());

-- OAuth tokens policies
DROP POLICY IF EXISTS "Users can manage own Google Drive tokens" ON google_drive_tokens;
DROP POLICY IF EXISTS "Users can manage own Notion tokens" ON notion_tokens;
DROP POLICY IF EXISTS "Users can manage own OAuth states" ON oauth_states;
CREATE POLICY "Users can manage own Google Drive tokens" ON google_drive_tokens FOR ALL USING (user_id = auth.uid());
CREATE POLICY "Users can manage own Notion tokens" ON notion_tokens FOR ALL USING (user_id = auth.uid());
CREATE POLICY "Users can manage own OAuth states" ON oauth_states FOR ALL USING (user_id = auth.uid());

-- Theme settings policies
DROP POLICY IF EXISTS "Users can read theme settings" ON theme_settings;
DROP POLICY IF EXISTS "Admins can manage theme settings" ON theme_settings;
CREATE POLICY "Users can read theme settings" ON theme_settings FOR SELECT
USING (EXISTS (SELECT 1 FROM users WHERE users.id = auth.uid() AND users.client_id = theme_settings.client_id));
CREATE POLICY "Admins can manage theme settings" ON theme_settings FOR ALL
USING (EXISTS (SELECT 1 FROM users WHERE users.id = auth.uid() AND users.role = 'admin' AND users.client_id = theme_settings.client_id));

-- Sync log policies
DROP POLICY IF EXISTS "Users can view own sync logs" ON google_drive_sync_log;
DROP POLICY IF EXISTS "Users can insert own sync logs" ON google_drive_sync_log;
DROP POLICY IF EXISTS "Users can update own sync logs" ON google_drive_sync_log;
CREATE POLICY "Users can view own sync logs" ON google_drive_sync_log FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own sync logs" ON google_drive_sync_log FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own sync logs" ON google_drive_sync_log FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view own Notion sync logs" ON notion_sync_log;
DROP POLICY IF EXISTS "Users can insert own Notion sync logs" ON notion_sync_log;
DROP POLICY IF EXISTS "Users can update own Notion sync logs" ON notion_sync_log;
CREATE POLICY "Users can view own Notion sync logs" ON notion_sync_log FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own Notion sync logs" ON notion_sync_log FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own Notion sync logs" ON notion_sync_log FOR UPDATE USING (auth.uid() = user_id);

-- Extractions policies
DROP POLICY IF EXISTS "Users can view own extractions" ON extractions;
DROP POLICY IF EXISTS "Users can create own extractions" ON extractions;
DROP POLICY IF EXISTS "Users can update own extractions" ON extractions;
DROP POLICY IF EXISTS "Admins can manage all extractions" ON extractions;
CREATE POLICY "Users can view own extractions" ON extractions FOR SELECT
USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));
CREATE POLICY "Users can create own extractions" ON extractions FOR INSERT
WITH CHECK (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));
CREATE POLICY "Users can update own extractions" ON extractions FOR UPDATE
USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));
CREATE POLICY "Admins can manage all extractions" ON extractions FOR ALL
USING (EXISTS (SELECT 1 FROM users WHERE users.id = auth.uid() AND users.role = 'admin'));

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to match document chunks by embedding similarity
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding VECTOR(1024),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 5,
    p_client_id UUID DEFAULT NULL,
    p_user_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity,
        dc.metadata
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE
        (p_client_id IS NULL OR d.client_id = p_client_id)
        AND (p_user_id IS NULL OR d.uploaded_by = p_user_id)
        AND d.processing_status = 'completed'
        AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, name, role, client_id)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        'user',
        '00000000-0000-0000-0000-000000000001'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create user profile on auth signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- DONE!
-- ============================================================================
