-- Migration: Opportunity Conversations
-- Date: 2026-01-16
-- Description: Adds table to store Q&A conversations about opportunities
--
-- New Tables:
--   - opportunity_conversations: Stores user questions and AI responses linked to opportunities

-- ============================================================================
-- OPPORTUNITY CONVERSATIONS TABLE
-- ============================================================================
-- Stores Q&A history for each opportunity, allowing users to ask questions
-- and get AI-generated responses with relevant document context

CREATE TABLE IF NOT EXISTS opportunity_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID NOT NULL REFERENCES ai_opportunities(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Q&A Content
    question TEXT NOT NULL,
    response TEXT NOT NULL,

    -- Source documents used to generate response
    -- Array of: { document_id, document_name, snippet, relevance_score }
    source_documents JSONB DEFAULT '[]',

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE opportunity_conversations IS 'Q&A history for opportunities - stores user questions and AI responses';
COMMENT ON COLUMN opportunity_conversations.source_documents IS 'JSONB array of documents used as context for the response';

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_opp_conversations_opportunity_id
    ON opportunity_conversations(opportunity_id);

CREATE INDEX IF NOT EXISTS idx_opp_conversations_client_id
    ON opportunity_conversations(client_id);

CREATE INDEX IF NOT EXISTS idx_opp_conversations_user_id
    ON opportunity_conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_opp_conversations_created_at
    ON opportunity_conversations(created_at DESC);

-- Composite index for common query: get conversations for an opportunity, newest first
CREATE INDEX IF NOT EXISTS idx_opp_conversations_opp_created
    ON opportunity_conversations(opportunity_id, created_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE opportunity_conversations ENABLE ROW LEVEL SECURITY;

-- Users can view conversations in their client
DROP POLICY IF EXISTS "Users can view conversations in their client" ON opportunity_conversations;
CREATE POLICY "Users can view conversations in their client" ON opportunity_conversations
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

-- Users can create conversations in their client
DROP POLICY IF EXISTS "Users can create conversations in their client" ON opportunity_conversations;
CREATE POLICY "Users can create conversations in their client" ON opportunity_conversations
    FOR INSERT WITH CHECK (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

-- Service role has full access
DROP POLICY IF EXISTS "Service role has full access to opportunity_conversations" ON opportunity_conversations;
CREATE POLICY "Service role has full access to opportunity_conversations" ON opportunity_conversations
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- DONE!
-- ============================================================================
