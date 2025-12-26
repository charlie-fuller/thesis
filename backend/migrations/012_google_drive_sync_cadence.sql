-- =====================================================
-- Migration 012: Google Drive Sync Cadence
-- =====================================================
-- Description: Adds automatic sync scheduling to Google Drive integration
-- Author: Claude
-- Date: 2025-11-09
-- =====================================================

-- Add sync cadence columns to google_drive_tokens table
ALTER TABLE google_drive_tokens ADD COLUMN IF NOT EXISTS
  sync_frequency VARCHAR DEFAULT 'manual'; -- 'manual', 'daily', 'weekly', 'monthly'

ALTER TABLE google_drive_tokens ADD COLUMN IF NOT EXISTS
  last_auto_sync TIMESTAMPTZ; -- Last time automated sync ran

ALTER TABLE google_drive_tokens ADD COLUMN IF NOT EXISTS
  next_sync_scheduled TIMESTAMPTZ; -- Next scheduled sync time

ALTER TABLE google_drive_tokens ADD COLUMN IF NOT EXISTS
  default_folder_id VARCHAR; -- Default Google Drive folder ID to sync

ALTER TABLE google_drive_tokens ADD COLUMN IF NOT EXISTS
  default_folder_name VARCHAR; -- Default folder name for display

-- Create index for scheduled syncs query
CREATE INDEX IF NOT EXISTS idx_google_tokens_next_sync
  ON google_drive_tokens(next_sync_scheduled)
  WHERE next_sync_scheduled IS NOT NULL
  AND is_active = TRUE
  AND sync_frequency != 'manual';

-- Add helpful comments
COMMENT ON COLUMN google_drive_tokens.sync_frequency IS
  'Automatic sync frequency: manual, daily, weekly, or monthly';

COMMENT ON COLUMN google_drive_tokens.last_auto_sync IS
  'Timestamp of last automated sync execution';

COMMENT ON COLUMN google_drive_tokens.next_sync_scheduled IS
  'Timestamp when next automatic sync should run';

COMMENT ON COLUMN google_drive_tokens.default_folder_id IS
  'Default Google Drive folder ID for automatic syncs';

COMMENT ON COLUMN google_drive_tokens.default_folder_name IS
  'Human-readable name of default sync folder';

-- =====================================================
-- Migration Complete
-- =====================================================
