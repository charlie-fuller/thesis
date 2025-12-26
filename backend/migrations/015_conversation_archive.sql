-- Migration: Add archive functionality to conversations
-- Date: 2025-11-11
-- Description: Add archived and archived_at columns to conversations table

-- Add archive columns to conversations table
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ DEFAULT NULL;

-- Create index for faster filtering of archived conversations
CREATE INDEX IF NOT EXISTS idx_conversations_archived ON conversations(archived);

-- Create index for date range queries on archived_at
CREATE INDEX IF NOT EXISTS idx_conversations_archived_at ON conversations(archived_at);

-- Update RLS policies to include archived conversations in user queries
-- (archived conversations should still be accessible to their owners)

COMMENT ON COLUMN conversations.archived IS 'Whether the conversation has been archived';
COMMENT ON COLUMN conversations.archived_at IS 'Timestamp when the conversation was archived';
