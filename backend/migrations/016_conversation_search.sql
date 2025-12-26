-- Migration: Add full-text search to conversations and messages
-- Date: 2025-11-11
-- Description: Add full-text search indexes for conversation search functionality

-- Create GIN index for full-text search on conversation titles
CREATE INDEX IF NOT EXISTS idx_conversations_title_search
ON conversations USING GIN (to_tsvector('english', title));

-- Create GIN index for full-text search on message content
CREATE INDEX IF NOT EXISTS idx_messages_content_search
ON messages USING GIN (to_tsvector('english', content));

-- Create composite index for efficient date range queries
CREATE INDEX IF NOT EXISTS idx_conversations_created_updated
ON conversations(created_at DESC, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_timestamp
ON messages(timestamp DESC);

COMMENT ON INDEX idx_conversations_title_search IS 'Full-text search index for conversation titles';
COMMENT ON INDEX idx_messages_content_search IS 'Full-text search index for message content';
