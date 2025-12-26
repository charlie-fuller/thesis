-- Migration 018: Add provider column to oauth_states table
-- Supports multiple OAuth providers (Google Drive, Notion, etc.)

ALTER TABLE oauth_states
ADD COLUMN IF NOT EXISTS provider VARCHAR(50);

-- Add index for provider lookups
CREATE INDEX IF NOT EXISTS idx_oauth_states_provider ON oauth_states(provider);

-- Add comment
COMMENT ON COLUMN oauth_states.provider IS 'OAuth provider name (e.g., google-drive, notion)';
