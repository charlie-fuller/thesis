-- =====================================================
-- Migration 011: Google Drive Integration
-- =====================================================
-- Description: Adds tables and columns to support Google Drive integration
-- Author: Claude
-- Date: 2025-11-09
-- =====================================================

-- Add Google Drive columns to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS
  source_platform VARCHAR DEFAULT 'manual'; -- 'manual' or 'google_drive'

ALTER TABLE documents ADD COLUMN IF NOT EXISTS
  external_id VARCHAR; -- Google Drive file ID

ALTER TABLE documents ADD COLUMN IF NOT EXISTS
  external_url TEXT; -- Link to view in Google Drive

ALTER TABLE documents ADD COLUMN IF NOT EXISTS
  google_drive_file_id VARCHAR; -- Specific to Google Drive

ALTER TABLE documents ADD COLUMN IF NOT EXISTS
  last_synced_at TIMESTAMPTZ; -- Last time this doc was synced

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_documents_external_id
  ON documents(external_id) WHERE external_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_documents_source_platform
  ON documents(source_platform);

CREATE INDEX IF NOT EXISTS idx_documents_google_drive_file_id
  ON documents(google_drive_file_id) WHERE google_drive_file_id IS NOT NULL;

-- =====================================================
-- Google Drive Sync Log Table
-- =====================================================
-- Tracks each sync job from Google Drive
CREATE TABLE IF NOT EXISTS google_drive_sync_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) NOT NULL,
  folder_id VARCHAR, -- Google Drive folder ID (NULL = root)
  folder_name VARCHAR, -- Human-readable folder name
  sync_type VARCHAR DEFAULT 'full', -- 'full' or 'incremental'

  -- Results
  documents_added INTEGER DEFAULT 0,
  documents_updated INTEGER DEFAULT 0,
  documents_skipped INTEGER DEFAULT 0,
  status VARCHAR DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'

  -- Error tracking
  error_message TEXT,

  -- Timing
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  duration_seconds INTEGER
);

CREATE INDEX IF NOT EXISTS idx_sync_log_user
  ON google_drive_sync_log(user_id);

CREATE INDEX IF NOT EXISTS idx_sync_log_status
  ON google_drive_sync_log(status);

-- =====================================================
-- Google Drive OAuth Tokens Table
-- =====================================================
-- Stores encrypted OAuth tokens for Google Drive access
CREATE TABLE IF NOT EXISTS google_drive_tokens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) UNIQUE NOT NULL,

  -- OAuth tokens (encrypted at application layer)
  access_token_encrypted TEXT NOT NULL,
  refresh_token_encrypted TEXT NOT NULL,
  token_expires_at TIMESTAMPTZ NOT NULL,

  -- Metadata
  scopes TEXT[], -- OAuth scopes granted
  connected_at TIMESTAMPTZ DEFAULT NOW(),
  last_refreshed_at TIMESTAMPTZ,

  -- Status
  is_active BOOLEAN DEFAULT TRUE,
  revoked_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_google_tokens_user
  ON google_drive_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_google_tokens_active
  ON google_drive_tokens(is_active) WHERE is_active = TRUE;

-- =====================================================
-- Add helpful comments
-- =====================================================
COMMENT ON TABLE google_drive_sync_log IS
  'Tracks each sync job from Google Drive';

COMMENT ON TABLE google_drive_tokens IS
  'Stores encrypted OAuth tokens for Google Drive access';

COMMENT ON COLUMN documents.source_platform IS
  'Source of document: manual upload or google_drive';

COMMENT ON COLUMN documents.google_drive_file_id IS
  'Google Drive file ID for synced documents';

COMMENT ON COLUMN documents.external_id IS
  'External platform file ID (Google Drive, SharePoint, etc.)';

COMMENT ON COLUMN documents.external_url IS
  'URL to view document in external platform';

COMMENT ON COLUMN documents.last_synced_at IS
  'Last time this document was synced from external platform';

-- =====================================================
-- Row Level Security (RLS) Policies
-- =====================================================
-- Ensure users can only access their own sync logs and tokens

ALTER TABLE google_drive_sync_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_drive_tokens ENABLE ROW LEVEL SECURITY;

-- Sync log policies
CREATE POLICY "Users can view their own sync logs"
  ON google_drive_sync_log
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sync logs"
  ON google_drive_sync_log
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sync logs"
  ON google_drive_sync_log
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Token policies
CREATE POLICY "Users can view their own tokens"
  ON google_drive_tokens
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own tokens"
  ON google_drive_tokens
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tokens"
  ON google_drive_tokens
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tokens"
  ON google_drive_tokens
  FOR DELETE
  USING (auth.uid() = user_id);

-- =====================================================
-- Migration Complete
-- =====================================================
