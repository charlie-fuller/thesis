-- Migration: Add Conversation to Knowledge Base Feature
-- Date: 2025-11-07
-- Purpose: Allow users to add conversations to their knowledge base

-- ============================================================================
-- ADD KNOWLEDGE BASE TRACKING TO CONVERSATIONS
-- ============================================================================

-- Add flag to track if conversation is in knowledge base
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS in_knowledge_base BOOLEAN DEFAULT FALSE;

-- Add timestamp for when conversation was added to KB
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS added_to_kb_at TIMESTAMPTZ;

-- Add index for filtering conversations in KB
CREATE INDEX IF NOT EXISTS idx_conversations_in_kb
ON conversations(in_knowledge_base, user_id);

-- ============================================================================
-- ADD SOURCE TYPE TO DOCUMENT CHUNKS FOR DISTINCTION
-- ============================================================================

-- Add source type to distinguish document chunks from conversation chunks
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'document';

-- Add conversation_id for conversation chunks
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE;

-- Add constraint to ensure valid source types
ALTER TABLE document_chunks
ADD CONSTRAINT valid_source_type
CHECK (source_type IN ('document', 'conversation'));

-- Add index for conversation chunks
CREATE INDEX IF NOT EXISTS idx_chunks_by_conversation
ON document_chunks(conversation_id)
WHERE conversation_id IS NOT NULL;

-- Add index for source type
CREATE INDEX IF NOT EXISTS idx_chunks_by_source_type
ON document_chunks(source_type);

-- ============================================================================
-- UPDATE RLS POLICIES FOR CONVERSATION CHUNKS
-- ============================================================================

-- Users can view their own conversation chunks
CREATE POLICY "users_view_own_conversation_chunks"
ON document_chunks
FOR SELECT
TO authenticated
USING (
    source_type = 'conversation'
    AND conversation_id IN (
        SELECT id FROM conversations WHERE user_id = auth.uid()
    )
);

-- ============================================================================
-- ADD COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON COLUMN conversations.in_knowledge_base IS 'Whether this conversation has been added to the user knowledge base for RAG';
COMMENT ON COLUMN conversations.added_to_kb_at IS 'Timestamp when conversation was added to knowledge base';
COMMENT ON COLUMN document_chunks.source_type IS 'Source of the chunk: document (uploaded file) or conversation (chat history)';
COMMENT ON COLUMN document_chunks.conversation_id IS 'Reference to conversation if source_type is conversation';
