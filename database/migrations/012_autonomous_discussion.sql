-- Migration: 012_autonomous_discussion.sql
-- Description: Autonomous Discussion Mode for Meeting Rooms + Vector Embeddings
-- Created: 2025-12-27

-- ============================================================================
-- PART 1: AUTONOMOUS DISCUSSION COLUMNS
-- Add columns to track autonomous discussion context in messages
-- ============================================================================

-- Add discussion round tracking to messages
ALTER TABLE meeting_room_messages
ADD COLUMN IF NOT EXISTS discussion_round INTEGER DEFAULT NULL;

-- Track which agent a message is responding to (for agent-to-agent discourse)
ALTER TABLE meeting_room_messages
ADD COLUMN IF NOT EXISTS responding_to_agent VARCHAR(100) DEFAULT NULL;

-- Add pending interjection flag for detecting user messages during autonomous mode
ALTER TABLE meeting_room_messages
ADD COLUMN IF NOT EXISTS pending_interjection BOOLEAN DEFAULT FALSE;

-- Index for querying messages by round
CREATE INDEX IF NOT EXISTS idx_meeting_room_messages_discussion_round
ON meeting_room_messages(meeting_room_id, discussion_round)
WHERE discussion_round IS NOT NULL;

-- ============================================================================
-- PART 2: VECTOR EMBEDDINGS FOR MEETING ROOM MESSAGES
-- Enable RAG search across meeting room conversations
-- ============================================================================

-- Add embedding column for vector search
ALTER TABLE meeting_room_messages
ADD COLUMN IF NOT EXISTS embedding VECTOR(1024) DEFAULT NULL;

-- Add embedding status tracking
ALTER TABLE meeting_room_messages
ADD COLUMN IF NOT EXISTS embedding_status VARCHAR(50) DEFAULT 'pending';
-- Status: pending, processing, completed, failed

-- Index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_meeting_room_messages_embedding
ON meeting_room_messages USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100)
WHERE embedding IS NOT NULL;

-- Index for finding messages needing embedding
CREATE INDEX IF NOT EXISTS idx_meeting_room_messages_embedding_status
ON meeting_room_messages(embedding_status)
WHERE embedding_status = 'pending';

-- ============================================================================
-- PART 3: VECTOR SEARCH FUNCTION FOR MEETING ROOM MESSAGES
-- Similar to match_document_chunks but for meeting room conversations
-- ============================================================================

CREATE OR REPLACE FUNCTION match_meeting_room_messages(
    query_embedding VECTOR(1024),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10,
    p_client_id UUID DEFAULT NULL,
    p_user_id UUID DEFAULT NULL,
    p_meeting_room_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    meeting_room_id UUID,
    role VARCHAR(50),
    agent_name VARCHAR(100),
    agent_display_name VARCHAR(200),
    content TEXT,
    discussion_round INTEGER,
    created_at TIMESTAMPTZ,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        mrm.id,
        mrm.meeting_room_id,
        mrm.role,
        mrm.agent_name,
        mrm.agent_display_name,
        mrm.content,
        mrm.discussion_round,
        mrm.created_at,
        1 - (mrm.embedding <=> query_embedding) AS similarity
    FROM meeting_room_messages mrm
    JOIN meeting_rooms mr ON mrm.meeting_room_id = mr.id
    WHERE mrm.embedding IS NOT NULL
      AND mrm.embedding_status = 'completed'
      AND (p_client_id IS NULL OR mr.client_id = p_client_id)
      AND (p_user_id IS NULL OR mr.user_id = p_user_id)
      AND (p_meeting_room_id IS NULL OR mrm.meeting_room_id = p_meeting_room_id)
      AND 1 - (mrm.embedding <=> query_embedding) > match_threshold
    ORDER BY mrm.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- PART 4: NEO4J SYNC TRACKING FOR MEETING ROOM MESSAGES
-- Track which messages have been synced to the graph
-- ============================================================================

-- Add graph sync timestamp (NULL = never synced, timestamp = last sync)
ALTER TABLE meeting_room_messages
ADD COLUMN IF NOT EXISTS graph_synced_at TIMESTAMPTZ DEFAULT NULL;

-- Index for finding messages needing graph sync
CREATE INDEX IF NOT EXISTS idx_meeting_room_messages_graph_sync
ON meeting_room_messages(graph_synced_at NULLS FIRST)
WHERE graph_synced_at IS NULL;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN meeting_room_messages.discussion_round IS
'Round number during autonomous discussion mode (1, 2, 3, etc.). NULL for user-directed messages.';

COMMENT ON COLUMN meeting_room_messages.responding_to_agent IS
'Agent name this message is responding to during autonomous discussion. Enables agent-to-agent discourse tracking.';

COMMENT ON COLUMN meeting_room_messages.pending_interjection IS
'Flag for user messages sent during autonomous discussion that should pause the discussion.';

COMMENT ON COLUMN meeting_room_messages.embedding IS
'Voyage AI embedding (1024 dimensions) for vector similarity search.';

COMMENT ON COLUMN meeting_room_messages.embedding_status IS
'Status of embedding generation: pending, processing, completed, failed.';

COMMENT ON COLUMN meeting_room_messages.graph_synced_at IS
'Timestamp of last sync to Neo4j graph. NULL means never synced.';

COMMENT ON FUNCTION match_meeting_room_messages IS
'Vector similarity search for meeting room messages. Returns messages similar to the query embedding.';

-- ============================================================================
-- NOTE: Autonomous discussion config is stored in meeting_rooms.config JSONB
--
-- Expected config structure:
-- {
--   "autonomous": {
--     "is_active": false,
--     "topic": null,
--     "total_rounds": 3,
--     "current_round": 0,
--     "speaking_order": "priority",
--     "is_paused": false,
--     "agents_spoken_this_round": []
--   }
-- }
-- ============================================================================
