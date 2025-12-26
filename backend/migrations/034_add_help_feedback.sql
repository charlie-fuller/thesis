-- Add feedback tracking to help messages
-- Allows admins to rate responses with thumbs up/down

ALTER TABLE help_messages
ADD COLUMN feedback INTEGER CHECK (feedback IN (-1, 1)),
ADD COLUMN feedback_timestamp TIMESTAMPTZ;

-- Index for analytics queries
CREATE INDEX idx_help_messages_feedback ON help_messages(feedback) WHERE feedback IS NOT NULL;

-- Add comment
COMMENT ON COLUMN help_messages.feedback IS 'User feedback: 1 for thumbs up, -1 for thumbs down, NULL for no feedback';
COMMENT ON COLUMN help_messages.feedback_timestamp IS 'When the feedback was given';
