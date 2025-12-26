-- =====================================================
-- Migration 015: Notion Integration
-- =====================================================
-- Description: Adds tables and columns to support Notion integration
-- Author: Claude
-- Date: 2025-11-11
-- =====================================================

-- Update source_platform to support 'notion'
-- (Already exists, just documenting that it now supports: 'manual', 'google_drive', 'notion')

-- Add Notion-specific columns to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS
  notion_page_id VARCHAR; -- Notion page ID

ALTER TABLE documents ADD COLUMN IF NOT EXISTS
  notion_database_id VARCHAR; -- Notion database ID (if from a database)

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_documents_notion_page_id
  ON documents(notion_page_id) WHERE notion_page_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_documents_notion_database_id
  ON documents(notion_database_id) WHERE notion_database_id IS NOT NULL;

-- =====================================================
-- Notion Sync Log Table
-- =====================================================
-- Tracks each sync job from Notion
CREATE TABLE IF NOT EXISTS notion_sync_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) NOT NULL,
  page_id VARCHAR, -- Notion page/database ID
  page_name VARCHAR, -- Human-readable page name
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

CREATE INDEX IF NOT EXISTS idx_notion_sync_log_user
  ON notion_sync_log(user_id);

CREATE INDEX IF NOT EXISTS idx_notion_sync_log_status
  ON notion_sync_log(status);

-- =====================================================
-- Notion OAuth Tokens Table
-- =====================================================
-- Stores encrypted OAuth tokens for Notion access
CREATE TABLE IF NOT EXISTS notion_tokens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) UNIQUE NOT NULL,

  -- OAuth tokens (encrypted at application layer)
  access_token_encrypted TEXT NOT NULL,

  -- Notion tokens don't expire unless revoked
  -- Metadata
  workspace_name VARCHAR,
  workspace_icon VARCHAR,
  bot_id VARCHAR,
  connected_at TIMESTAMPTZ DEFAULT NOW(),

  -- Status
  is_active BOOLEAN DEFAULT TRUE,
  revoked_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notion_tokens_user
  ON notion_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_notion_tokens_active
  ON notion_tokens(is_active) WHERE is_active = TRUE;

-- =====================================================
-- Add helpful comments
-- =====================================================
COMMENT ON TABLE notion_sync_log IS
  'Tracks each sync job from Notion';

COMMENT ON TABLE notion_tokens IS
  'Stores encrypted OAuth tokens for Notion access';

COMMENT ON COLUMN documents.notion_page_id IS
  'Notion page ID for synced documents';

COMMENT ON COLUMN documents.notion_database_id IS
  'Notion database ID if document comes from a Notion database';

-- =====================================================
-- Row Level Security (RLS) Policies
-- =====================================================
-- Ensure users can only access their own sync logs and tokens

ALTER TABLE notion_sync_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE notion_tokens ENABLE ROW LEVEL SECURITY;

-- Sync log policies
CREATE POLICY "Users can view their own Notion sync logs"
  ON notion_sync_log
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own Notion sync logs"
  ON notion_sync_log
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own Notion sync logs"
  ON notion_sync_log
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Token policies
CREATE POLICY "Users can view their own Notion tokens"
  ON notion_tokens
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own Notion tokens"
  ON notion_tokens
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own Notion tokens"
  ON notion_tokens
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own Notion tokens"
  ON notion_tokens
  FOR DELETE
  USING (auth.uid() = user_id);

-- =====================================================
-- Migration Complete
-- =====================================================
