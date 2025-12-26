-- Add help_type column to help_conversations
-- Tracks whether the conversation was started from admin or user help context

ALTER TABLE help_conversations
ADD COLUMN IF NOT EXISTS help_type TEXT DEFAULT 'user' CHECK (help_type IN ('admin', 'user'));

-- Add index for filtering by help_type
CREATE INDEX IF NOT EXISTS help_conversations_help_type_idx ON help_conversations(help_type);

COMMENT ON COLUMN help_conversations.help_type IS 'Whether this help conversation was in admin or user context';
