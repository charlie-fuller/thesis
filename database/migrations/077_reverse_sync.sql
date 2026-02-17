-- Migration 077: Add reverse sync support
-- Allows documents created in the app (e.g. from DISCO chat) to sync back to local Obsidian vault

-- Flag to indicate a document needs to be pulled down to the local vault
ALTER TABLE documents ADD COLUMN IF NOT EXISTS needs_reverse_sync BOOLEAN DEFAULT false;

-- Timestamp of when the document was last reverse-synced to the local vault
ALTER TABLE documents ADD COLUMN IF NOT EXISTS reverse_synced_at TIMESTAMPTZ;

-- Index for efficient querying of documents pending reverse sync
CREATE INDEX IF NOT EXISTS idx_documents_needs_reverse_sync
  ON documents (needs_reverse_sync)
  WHERE needs_reverse_sync = true;

COMMENT ON COLUMN documents.needs_reverse_sync IS 'True when document was created in-app and needs to be synced to local Obsidian vault';
COMMENT ON COLUMN documents.reverse_synced_at IS 'Timestamp of last successful reverse sync to local vault';
