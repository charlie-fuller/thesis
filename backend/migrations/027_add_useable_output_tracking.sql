-- Migration: Add useable output tracking
-- Date: 2025-11-23
-- Purpose: Track when conversations achieve "useable output" for Correction Loop KPI

-- Add useable output tracking to conversations
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS useable_output_message_id UUID REFERENCES messages(id),
ADD COLUMN IF NOT EXISTS turns_to_useable_output INTEGER,
ADD COLUMN IF NOT EXISTS useable_output_method TEXT,
ADD COLUMN IF NOT EXISTS useable_output_detected_at TIMESTAMP WITH TIME ZONE;

-- Add index for efficient querying
CREATE INDEX IF NOT EXISTS idx_conversations_useable_output
ON conversations(useable_output_message_id)
WHERE useable_output_message_id IS NOT NULL;

-- Add comments
COMMENT ON COLUMN conversations.useable_output_message_id IS 'The assistant message that provided useable output';
COMMENT ON COLUMN conversations.turns_to_useable_output IS 'Number of user turns required to reach useable output';
COMMENT ON COLUMN conversations.useable_output_method IS 'How useable output was detected: user_marked, copy_event, keyword_detected, function_complete, conversation_ended';
COMMENT ON COLUMN conversations.useable_output_detected_at IS 'When useable output was detected/marked';

-- Valid detection methods:
-- - user_marked: User explicitly marked message as useable
-- - copy_event: User copied substantial content from message
-- - keyword_detected: Positive sentiment/confirmation keywords detected in user response
-- - function_complete: AI function reached completion state
-- - conversation_ended: Conversation ended naturally (fallback)
