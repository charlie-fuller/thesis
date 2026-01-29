-- Migration: Add sync_progress column to obsidian_vault_configs
-- Purpose: Track live sync progress (total files, files processed, current file)

-- Add sync_progress JSONB column
ALTER TABLE obsidian_vault_configs
ADD COLUMN IF NOT EXISTS sync_progress JSONB;

-- Add comment explaining the column
COMMENT ON COLUMN obsidian_vault_configs.sync_progress IS 'Live sync progress: {is_syncing, total_files, files_processed, current_file, updated_at}';
