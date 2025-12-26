-- Migration: Add message_documents table to link messages with attached documents
-- Purpose: Maintain explicit relationships between chat messages and uploaded files
-- Date: 2025-12-15

-- Create the message_documents junction table
CREATE TABLE IF NOT EXISTS message_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure a document is only linked once per message
    UNIQUE(message_id, document_id)
);

-- Add index for efficient lookup by message_id
CREATE INDEX IF NOT EXISTS idx_message_documents_message_id
ON message_documents(message_id);

-- Add index for efficient lookup by document_id
CREATE INDEX IF NOT EXISTS idx_message_documents_document_id
ON message_documents(document_id);

-- Add index for efficient lookup by creation time
CREATE INDEX IF NOT EXISTS idx_message_documents_created_at
ON message_documents(created_at DESC);

-- Enable Row Level Security
ALTER TABLE message_documents ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see message-document links for their own messages
CREATE POLICY message_documents_select_policy ON message_documents
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE m.id = message_documents.message_id
            AND c.user_id = auth.uid()
        )
    );

-- RLS Policy: Users can only insert message-document links for their own messages
CREATE POLICY message_documents_insert_policy ON message_documents
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE m.id = message_documents.message_id
            AND c.user_id = auth.uid()
        )
    );

-- RLS Policy: Users can only delete message-document links for their own messages
CREATE POLICY message_documents_delete_policy ON message_documents
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE m.id = message_documents.message_id
            AND c.user_id = auth.uid()
        )
    );

-- Add comment for documentation
COMMENT ON TABLE message_documents IS 'Junction table linking chat messages to uploaded documents, maintaining file context throughout conversations';
COMMENT ON COLUMN message_documents.message_id IS 'Reference to the message that has the document attached';
COMMENT ON COLUMN message_documents.document_id IS 'Reference to the uploaded document';
