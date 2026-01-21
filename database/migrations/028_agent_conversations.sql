-- Migration 028: Add agent_id to conversations for agent-specific chat history
-- Description: Allows tracking conversations with specific agents for the agent chat tab feature

-- Add agent_id column (optional - NULL for auto/coordinator routed conversations)
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES agents(id) ON DELETE SET NULL;

-- Add index for efficient querying by agent
CREATE INDEX IF NOT EXISTS idx_conversations_agent_id ON conversations(agent_id);

-- Composite index for common query: get conversations for an agent, newest first
CREATE INDEX IF NOT EXISTS idx_conversations_agent_updated
    ON conversations(agent_id, updated_at DESC);

-- Comment on column
COMMENT ON COLUMN conversations.agent_id IS 'Optional: links conversation to a specific agent for agent-focused chat';
