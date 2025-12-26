-- =====================================================
-- Migration 014: Add Sync Cadence to Documents
-- =====================================================
-- Description: Adds sync_cadence column to documents table for per-document sync settings
-- Author: Claude
-- Date: 2025-11-10
-- =====================================================

-- Add sync_cadence column to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS
  sync_cadence VARCHAR DEFAULT 'manual'; -- 'manual', 'daily', 'weekly', 'monthly'

-- Add comment
COMMENT ON COLUMN documents.sync_cadence IS
  'Automatic sync cadence for Google Drive documents: manual, daily, weekly, or monthly';

-- Create index for efficient querying by sync cadence
CREATE INDEX IF NOT EXISTS idx_documents_sync_cadence
  ON documents(sync_cadence) WHERE source_platform = 'google_drive';

-- =====================================================
-- Migration Complete
-- =====================================================
