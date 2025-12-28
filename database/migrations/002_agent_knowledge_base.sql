-- ============================================================================
-- AGENT KNOWLEDGE BASE LINKING
-- Links documents to specific agents for agent-specific RAG retrieval
-- ============================================================================

-- Agent-Document linking table
CREATE TABLE IF NOT EXISTS agent_knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Linking metadata
    added_by UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    priority INTEGER DEFAULT 0,  -- Higher priority docs are weighted more heavily

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicate agent-document links
    UNIQUE(agent_id, document_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agent_kb_agent_id ON agent_knowledge_base(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_kb_document_id ON agent_knowledge_base(document_id);
CREATE INDEX IF NOT EXISTS idx_agent_kb_priority ON agent_knowledge_base(agent_id, priority DESC);

-- RLS
ALTER TABLE agent_knowledge_base ENABLE ROW LEVEL SECURITY;

-- All authenticated users can view agent KB links
DROP POLICY IF EXISTS "Users can view agent knowledge base" ON agent_knowledge_base;
CREATE POLICY "Users can view agent knowledge base" ON agent_knowledge_base
    FOR SELECT USING (true);

-- Only admins can manage agent KB links
DROP POLICY IF EXISTS "Admins can manage agent knowledge base" ON agent_knowledge_base;
CREATE POLICY "Admins can manage agent knowledge base" ON agent_knowledge_base
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'admin'
        )
    );

-- ============================================================================
-- DONE!
-- ============================================================================
