-- =====================================================
-- Migration 019: Notion Sync Cadence
-- =====================================================
-- Description: Adds automatic sync scheduling to Notion integration
-- Author: Claude
-- Date: 2025-11-13
-- =====================================================

-- Add sync cadence columns to notion_tokens table
ALTER TABLE notion_tokens ADD COLUMN IF NOT EXISTS
  sync_frequency VARCHAR DEFAULT 'manual'; -- 'manual', 'daily', 'weekly', 'monthly'

ALTER TABLE notion_tokens ADD COLUMN IF NOT EXISTS
  last_auto_sync TIMESTAMPTZ; -- Last time automated sync ran

ALTER TABLE notion_tokens ADD COLUMN IF NOT EXISTS
  next_sync_scheduled TIMESTAMPTZ; -- Next scheduled sync time

ALTER TABLE notion_tokens ADD COLUMN IF NOT EXISTS
  default_page_ids TEXT[]; -- Default Notion page IDs to sync (stored as array)

-- Create index for scheduled syncs query
CREATE INDEX IF NOT EXISTS idx_notion_tokens_next_sync
  ON notion_tokens(next_sync_scheduled)
  WHERE next_sync_scheduled IS NOT NULL
  AND is_active = TRUE
  AND sync_frequency != 'manual';

-- Add helpful comments
COMMENT ON COLUMN notion_tokens.sync_frequency IS
  'Automatic sync frequency: manual, daily, weekly, or monthly';

COMMENT ON COLUMN notion_tokens.last_auto_sync IS
  'Timestamp of last automated sync execution';

COMMENT ON COLUMN notion_tokens.next_sync_scheduled IS
  'Timestamp when next automatic sync should run';

COMMENT ON COLUMN notion_tokens.default_page_ids IS
  'Default Notion page IDs for automatic syncs (stored as array)';

-- =====================================================
-- Migration Complete
-- =====================================================
