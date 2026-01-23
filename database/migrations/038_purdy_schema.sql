-- Migration: 038_purdy_schema
-- Description: Add PuRDy (Product Requirements Discovery) integration
-- Date: 2026-01-23

-- ============================================================================
-- EXTEND USERS TABLE
-- ============================================================================

-- Add app_access column to users for role-based feature access
-- Values: 'thesis', 'purdy', 'all'
ALTER TABLE users ADD COLUMN IF NOT EXISTS
    app_access TEXT[] DEFAULT ARRAY['thesis'];

COMMENT ON COLUMN users.app_access IS 'Array of application access rights: thesis, purdy, all';

-- ============================================================================
-- PURDY INITIATIVES
-- ============================================================================

-- Initiative container - the central entity for a PuRDy discovery effort
CREATE TABLE IF NOT EXISTS purdy_initiatives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',
    -- Statuses: draft, triaged, in_discovery, synthesized, evaluated, archived
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE purdy_initiatives IS 'PuRDy initiative containers for discovery efforts';
COMMENT ON COLUMN purdy_initiatives.status IS 'Workflow status: draft, triaged, in_discovery, synthesized, evaluated, archived';

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_purdy_initiatives_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER purdy_initiatives_updated_at_trigger
    BEFORE UPDATE ON purdy_initiatives
    FOR EACH ROW
    EXECUTE FUNCTION update_purdy_initiatives_updated_at();

-- ============================================================================
-- PURDY INITIATIVE MEMBERS (Sharing)
-- ============================================================================

-- Initiative sharing for multi-user collaboration
CREATE TABLE IF NOT EXISTS purdy_initiative_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiative_id UUID REFERENCES purdy_initiatives(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'viewer',  -- owner, editor, viewer
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(initiative_id, user_id)
);

COMMENT ON TABLE purdy_initiative_members IS 'PuRDy initiative sharing and permissions';
COMMENT ON COLUMN purdy_initiative_members.role IS 'Permission level: owner, editor, viewer';

-- ============================================================================
-- PURDY DOCUMENTS
-- ============================================================================

-- Per-initiative document repository
CREATE TABLE IF NOT EXISTS purdy_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiative_id UUID REFERENCES purdy_initiatives(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    document_type TEXT DEFAULT 'uploaded',
    -- Types: uploaded, triage_output, prd_output, tech_eval_output
    version INT DEFAULT 1,
    source_run_id UUID,  -- If auto-created from a run output
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE purdy_documents IS 'PuRDy initiative documents - uploaded and generated';
COMMENT ON COLUMN purdy_documents.document_type IS 'Document source: uploaded, triage_output, prd_output, tech_eval_output';
COMMENT ON COLUMN purdy_documents.source_run_id IS 'Reference to agent run that generated this document';

-- ============================================================================
-- PURDY DOCUMENT CHUNKS (Vector Search)
-- ============================================================================

-- Chunked and embedded documents for RAG (scoped to initiative)
CREATE TABLE IF NOT EXISTS purdy_document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES purdy_documents(id) ON DELETE CASCADE,
    initiative_id UUID NOT NULL,  -- Denormalized for fast queries
    chunk_index INT,
    content TEXT,
    embedding VECTOR(1024),
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE purdy_document_chunks IS 'PuRDy document chunks with embeddings for RAG';
COMMENT ON COLUMN purdy_document_chunks.initiative_id IS 'Denormalized initiative_id for fast vector search scoping';

-- ============================================================================
-- PURDY RUNS
-- ============================================================================

-- Each agent run (triage, discovery, synthesis, etc.)
CREATE TABLE IF NOT EXISTS purdy_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiative_id UUID REFERENCES purdy_initiatives(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL,
    -- Agent types: triage, discovery_planner, coverage_tracker, synthesizer, tech_evaluation
    run_by UUID REFERENCES auth.users(id),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running',  -- running, completed, failed
    error_message TEXT,
    token_usage JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE purdy_runs IS 'PuRDy agent run history and tracking';
COMMENT ON COLUMN purdy_runs.agent_type IS 'Agent: triage, discovery_planner, coverage_tracker, synthesizer, tech_evaluation';
COMMENT ON COLUMN purdy_runs.status IS 'Run status: running, completed, failed';

-- ============================================================================
-- PURDY RUN DOCUMENTS (Junction Table)
-- ============================================================================

-- Track which documents were used in each run
CREATE TABLE IF NOT EXISTS purdy_run_documents (
    run_id UUID REFERENCES purdy_runs(id) ON DELETE CASCADE,
    document_id UUID REFERENCES purdy_documents(id) ON DELETE CASCADE,
    PRIMARY KEY (run_id, document_id)
);

COMMENT ON TABLE purdy_run_documents IS 'Junction table tracking documents used in each PuRDy run';

-- ============================================================================
-- PURDY OUTPUTS
-- ============================================================================

-- Versioned outputs (structured + exportable)
CREATE TABLE IF NOT EXISTS purdy_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES purdy_runs(id) ON DELETE CASCADE,
    initiative_id UUID NOT NULL,
    agent_type TEXT NOT NULL,
    version INT DEFAULT 1,

    -- Structured fields (queryable)
    title TEXT,
    recommendation TEXT,        -- GO/NO-GO for triage
    tier_routing TEXT,          -- ELT/Solutions/Self-Serve
    confidence_level TEXT,      -- HIGH/MEDIUM/LOW
    executive_summary TEXT,

    -- Full content
    content_markdown TEXT NOT NULL,
    content_structured JSONB,   -- Parsed sections

    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE purdy_outputs IS 'PuRDy versioned agent outputs with structured fields';
COMMENT ON COLUMN purdy_outputs.recommendation IS 'GO/NO-GO recommendation for triage agent';
COMMENT ON COLUMN purdy_outputs.tier_routing IS 'Routing tier: ELT, Solutions, Self-Serve';
COMMENT ON COLUMN purdy_outputs.confidence_level IS 'Confidence level: HIGH, MEDIUM, LOW';

-- ============================================================================
-- PURDY CONVERSATIONS (RAG Chat)
-- ============================================================================

-- Initiative chat (RAG against initiative docs)
CREATE TABLE IF NOT EXISTS purdy_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiative_id UUID REFERENCES purdy_initiatives(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE purdy_conversations IS 'PuRDy initiative chat conversations for RAG';

-- ============================================================================
-- PURDY MESSAGES
-- ============================================================================

CREATE TABLE IF NOT EXISTS purdy_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES purdy_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,  -- user, assistant
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE purdy_messages IS 'PuRDy chat messages with source citations';
COMMENT ON COLUMN purdy_messages.role IS 'Message role: user, assistant';
COMMENT ON COLUMN purdy_messages.sources IS 'Array of source document references';

-- ============================================================================
-- PURDY SYSTEM KB (Global Knowledge Base)
-- ============================================================================

-- Global System KB (shared across all initiatives)
CREATE TABLE IF NOT EXISTS purdy_system_kb (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    category TEXT,  -- methodology, analysis, risk, decision, internal
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE purdy_system_kb IS 'PuRDy global system knowledge base files';
COMMENT ON COLUMN purdy_system_kb.category IS 'KB category: methodology, analysis, risk, decision, internal';

-- System KB chunks with embeddings
CREATE TABLE IF NOT EXISTS purdy_system_kb_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id UUID REFERENCES purdy_system_kb(id) ON DELETE CASCADE,
    chunk_index INT,
    content TEXT,
    embedding VECTOR(1024),
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE purdy_system_kb_chunks IS 'PuRDy system KB chunks with embeddings for RAG';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Document chunks initiative index (for scoped queries)
CREATE INDEX IF NOT EXISTS idx_purdy_chunks_initiative
    ON purdy_document_chunks(initiative_id);

-- Document chunks embedding index (for vector similarity search)
CREATE INDEX IF NOT EXISTS idx_purdy_chunks_embedding
    ON purdy_document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- System KB chunks embedding index
CREATE INDEX IF NOT EXISTS idx_purdy_system_kb_embedding
    ON purdy_system_kb_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Documents by initiative
CREATE INDEX IF NOT EXISTS idx_purdy_docs_initiative
    ON purdy_documents(initiative_id);

-- Outputs by initiative and agent type
CREATE INDEX IF NOT EXISTS idx_purdy_outputs_initiative
    ON purdy_outputs(initiative_id, agent_type);

-- Runs by initiative
CREATE INDEX IF NOT EXISTS idx_purdy_runs_initiative
    ON purdy_runs(initiative_id);

-- Members by initiative
CREATE INDEX IF NOT EXISTS idx_purdy_members_initiative
    ON purdy_initiative_members(initiative_id);

-- Members by user
CREATE INDEX IF NOT EXISTS idx_purdy_members_user
    ON purdy_initiative_members(user_id);

-- ============================================================================
-- VECTOR SEARCH FUNCTIONS
-- ============================================================================

-- Match document chunks within an initiative (scoped vector search)
CREATE OR REPLACE FUNCTION match_purdy_document_chunks(
    query_embedding VECTOR(1024),
    match_count INT,
    match_threshold FLOAT,
    p_initiative_id UUID
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    initiative_id UUID,
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
        pdc.id,
        pdc.document_id,
        pdc.initiative_id,
        pdc.chunk_index,
        pdc.content,
        pdc.metadata,
        (1 - (pdc.embedding <=> query_embedding))::FLOAT AS similarity
    FROM purdy_document_chunks pdc
    WHERE pdc.initiative_id = p_initiative_id
        AND (1 - (pdc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY pdc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_purdy_document_chunks IS 'Vector similarity search for PuRDy document chunks scoped to initiative';

-- Match system KB chunks (global search)
CREATE OR REPLACE FUNCTION match_purdy_system_kb_chunks(
    query_embedding VECTOR(1024),
    match_count INT,
    match_threshold FLOAT
)
RETURNS TABLE (
    id UUID,
    kb_id UUID,
    chunk_index INT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    filename TEXT,
    category TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        pskc.id,
        pskc.kb_id,
        pskc.chunk_index,
        pskc.content,
        pskc.metadata,
        (1 - (pskc.embedding <=> query_embedding))::FLOAT AS similarity,
        psk.filename,
        psk.category
    FROM purdy_system_kb_chunks pskc
    JOIN purdy_system_kb psk ON pskc.kb_id = psk.id
    WHERE (1 - (pskc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY pskc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_purdy_system_kb_chunks IS 'Vector similarity search for PuRDy global system KB chunks';

-- Combined search: initiative docs + system KB
CREATE OR REPLACE FUNCTION match_purdy_all_chunks(
    query_embedding VECTOR(1024),
    match_count INT,
    match_threshold FLOAT,
    p_initiative_id UUID
)
RETURNS TABLE (
    id UUID,
    source_type TEXT,  -- 'document' or 'system_kb'
    source_id UUID,    -- document_id or kb_id
    chunk_index INT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    filename TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    -- Initiative documents
    SELECT
        pdc.id,
        'document'::TEXT AS source_type,
        pdc.document_id AS source_id,
        pdc.chunk_index,
        pdc.content,
        pdc.metadata,
        (1 - (pdc.embedding <=> query_embedding))::FLOAT AS similarity,
        pd.filename
    FROM purdy_document_chunks pdc
    JOIN purdy_documents pd ON pdc.document_id = pd.id
    WHERE pdc.initiative_id = p_initiative_id
        AND (1 - (pdc.embedding <=> query_embedding)) >= match_threshold

    UNION ALL

    -- System KB
    SELECT
        pskc.id,
        'system_kb'::TEXT AS source_type,
        pskc.kb_id AS source_id,
        pskc.chunk_index,
        pskc.content,
        pskc.metadata,
        (1 - (pskc.embedding <=> query_embedding))::FLOAT AS similarity,
        psk.filename
    FROM purdy_system_kb_chunks pskc
    JOIN purdy_system_kb psk ON pskc.kb_id = psk.id
    WHERE (1 - (pskc.embedding <=> query_embedding)) >= match_threshold

    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_purdy_all_chunks IS 'Combined vector search across initiative docs and system KB';

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all PuRDy tables
ALTER TABLE purdy_initiatives ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_initiative_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_run_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_system_kb ENABLE ROW LEVEL SECURITY;
ALTER TABLE purdy_system_kb_chunks ENABLE ROW LEVEL SECURITY;

-- Initiatives: Users can see initiatives they created or are members of
CREATE POLICY purdy_initiatives_select ON purdy_initiatives FOR SELECT
    USING (
        created_by = auth.uid()
        OR EXISTS (
            SELECT 1 FROM purdy_initiative_members
            WHERE initiative_id = purdy_initiatives.id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY purdy_initiatives_insert ON purdy_initiatives FOR INSERT
    WITH CHECK (created_by = auth.uid());

CREATE POLICY purdy_initiatives_update ON purdy_initiatives FOR UPDATE
    USING (
        created_by = auth.uid()
        OR EXISTS (
            SELECT 1 FROM purdy_initiative_members
            WHERE initiative_id = purdy_initiatives.id
            AND user_id = auth.uid()
            AND role IN ('owner', 'editor')
        )
    );

CREATE POLICY purdy_initiatives_delete ON purdy_initiatives FOR DELETE
    USING (created_by = auth.uid());

-- Members: Users can see members of initiatives they have access to
CREATE POLICY purdy_members_select ON purdy_initiative_members FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_initiative_members.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members m
                    WHERE m.initiative_id = purdy_initiatives.id
                    AND m.user_id = auth.uid()
                )
            )
        )
    );

-- Documents: Users can access documents of initiatives they have access to
CREATE POLICY purdy_documents_select ON purdy_documents FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_documents.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = purdy_initiatives.id
                    AND user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY purdy_documents_insert ON purdy_documents FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_documents.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = purdy_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- Document chunks inherit document permissions
CREATE POLICY purdy_chunks_select ON purdy_document_chunks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM purdy_documents pd
            JOIN purdy_initiatives pi ON pd.initiative_id = pi.id
            WHERE pd.id = purdy_document_chunks.document_id
            AND (
                pi.created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = pi.id
                    AND user_id = auth.uid()
                )
            )
        )
    );

-- Runs: Users can access runs of initiatives they have access to
CREATE POLICY purdy_runs_select ON purdy_runs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_runs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = purdy_initiatives.id
                    AND user_id = auth.uid()
                )
            )
        )
    );

-- Outputs: Users can access outputs of initiatives they have access to
CREATE POLICY purdy_outputs_select ON purdy_outputs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_outputs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = purdy_initiatives.id
                    AND user_id = auth.uid()
                )
            )
        )
    );

-- Conversations: Users can access conversations they created
CREATE POLICY purdy_conversations_select ON purdy_conversations FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY purdy_conversations_insert ON purdy_conversations FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Messages: Users can access messages in their conversations
CREATE POLICY purdy_messages_select ON purdy_messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM purdy_conversations
            WHERE id = purdy_messages.conversation_id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY purdy_messages_insert ON purdy_messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM purdy_conversations
            WHERE id = purdy_messages.conversation_id
            AND user_id = auth.uid()
        )
    );

-- System KB: Read-only for all authenticated users
CREATE POLICY purdy_system_kb_select ON purdy_system_kb FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY purdy_system_kb_chunks_select ON purdy_system_kb_chunks FOR SELECT
    TO authenticated
    USING (true);
