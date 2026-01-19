-- Migration: Obsidian Vault Sync
-- Date: 2026-01-15
-- Description: Adds tables for syncing markdown files from local Obsidian vaults
--              to the Thesis Knowledge Base with file watching and state tracking.
--
-- New Tables:
--   - obsidian_vault_configs: User vault configuration with sync options
--   - obsidian_sync_state: Per-file sync state for incremental syncing
--   - obsidian_sync_log: Sync operation history and error tracking

-- ============================================================================
-- OBSIDIAN VAULT CONFIGS TABLE
-- ============================================================================
-- Stores user's Obsidian vault configuration and sync preferences

CREATE TABLE IF NOT EXISTS obsidian_vault_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id UUID DEFAULT '00000000-0000-0000-0000-000000000001' REFERENCES clients(id) ON DELETE CASCADE,

    -- Vault Configuration
    vault_path TEXT NOT NULL,
    vault_name VARCHAR(255),  -- Display name, derived from folder name if not set

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMPTZ,
    last_error TEXT,

    -- Sync Options (JSONB for flexibility)
    sync_options JSONB DEFAULT '{
        "include_patterns": ["**/*.md"],
        "exclude_patterns": [".obsidian/**", ".trash/**", ".git/**"],
        "auto_classify": true,
        "sync_on_delete": false,
        "parse_frontmatter": true,
        "convert_wikilinks": true,
        "max_file_size_mb": 10,
        "debounce_ms": 500
    }'::JSONB,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- One active config per user (can have inactive/archived configs)
    UNIQUE(user_id, vault_path)
);

COMMENT ON TABLE obsidian_vault_configs IS 'User Obsidian vault configurations for file sync';
COMMENT ON COLUMN obsidian_vault_configs.vault_path IS 'Absolute path to the Obsidian vault directory';
COMMENT ON COLUMN obsidian_vault_configs.sync_options IS 'JSON config: include/exclude patterns, auto-classify, delete sync, frontmatter parsing';
COMMENT ON COLUMN obsidian_vault_configs.is_active IS 'Whether sync is currently active for this vault';

-- ============================================================================
-- OBSIDIAN SYNC STATE TABLE
-- ============================================================================
-- Tracks per-file sync state for incremental synchronization

CREATE TABLE IF NOT EXISTS obsidian_sync_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id UUID NOT NULL REFERENCES obsidian_vault_configs(id) ON DELETE CASCADE,

    -- File Identification (relative path from vault root)
    file_path TEXT NOT NULL,

    -- Link to synced document
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Change Detection
    file_mtime TIMESTAMPTZ,
    file_hash TEXT,  -- MD5 hash for content change detection
    file_size INTEGER,

    -- Sync Status
    sync_status VARCHAR(50) DEFAULT 'pending',  -- pending, synced, failed, deleted
    last_synced_at TIMESTAMPTZ,
    sync_error TEXT,

    -- Frontmatter Cache (parsed from file)
    frontmatter JSONB DEFAULT '{}',
    -- Example: {
    --   "title": "My Note",
    --   "tags": ["project", "thesis"],
    --   "thesis-agents": ["atlas", "capital"],
    --   "aliases": ["alias1", "alias2"]
    -- }

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- One entry per file per config
    UNIQUE(config_id, file_path)
);

COMMENT ON TABLE obsidian_sync_state IS 'Per-file sync state for Obsidian vault incremental sync';
COMMENT ON COLUMN obsidian_sync_state.file_path IS 'Relative path from vault root (e.g., "notes/project.md")';
COMMENT ON COLUMN obsidian_sync_state.file_hash IS 'MD5 hash of file content for change detection';
COMMENT ON COLUMN obsidian_sync_state.frontmatter IS 'Cached YAML frontmatter parsed from file';
COMMENT ON COLUMN obsidian_sync_state.sync_status IS 'Current sync status: pending, synced, failed, deleted';

-- ============================================================================
-- OBSIDIAN SYNC LOG TABLE
-- ============================================================================
-- Track sync operations for debugging and user visibility

CREATE TABLE IF NOT EXISTS obsidian_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id UUID NOT NULL REFERENCES obsidian_vault_configs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Operation Details
    sync_type VARCHAR(50) NOT NULL,  -- full, incremental, watch
    status VARCHAR(50) NOT NULL,  -- running, completed, failed
    trigger_source VARCHAR(50),  -- manual, watcher, scheduled

    -- Results
    files_scanned INTEGER DEFAULT 0,
    files_added INTEGER DEFAULT 0,
    files_updated INTEGER DEFAULT 0,
    files_deleted INTEGER DEFAULT 0,
    files_skipped INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,

    -- Error Tracking
    error_message TEXT,
    error_details JSONB DEFAULT '[]',  -- Array of {file_path, error} objects

    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER
);

COMMENT ON TABLE obsidian_sync_log IS 'History of Obsidian sync operations with results';
COMMENT ON COLUMN obsidian_sync_log.sync_type IS 'Type of sync: full (all files), incremental (changed only), watch (single file from watcher)';
COMMENT ON COLUMN obsidian_sync_log.trigger_source IS 'What triggered this sync: manual, watcher, scheduled';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Obsidian Vault Configs indexes
CREATE INDEX IF NOT EXISTS idx_obsidian_vault_configs_user_id
    ON obsidian_vault_configs(user_id);

CREATE INDEX IF NOT EXISTS idx_obsidian_vault_configs_client_id
    ON obsidian_vault_configs(client_id);

CREATE INDEX IF NOT EXISTS idx_obsidian_vault_configs_active
    ON obsidian_vault_configs(is_active)
    WHERE is_active = TRUE;

-- Obsidian Sync State indexes
CREATE INDEX IF NOT EXISTS idx_obsidian_sync_state_config_id
    ON obsidian_sync_state(config_id);

CREATE INDEX IF NOT EXISTS idx_obsidian_sync_state_document_id
    ON obsidian_sync_state(document_id);

CREATE INDEX IF NOT EXISTS idx_obsidian_sync_state_status
    ON obsidian_sync_state(sync_status);

-- Find pending/failed files quickly
CREATE INDEX IF NOT EXISTS idx_obsidian_sync_state_needs_sync
    ON obsidian_sync_state(config_id, sync_status)
    WHERE sync_status IN ('pending', 'failed');

-- Obsidian Sync Log indexes
CREATE INDEX IF NOT EXISTS idx_obsidian_sync_log_config_id
    ON obsidian_sync_log(config_id);

CREATE INDEX IF NOT EXISTS idx_obsidian_sync_log_user_id
    ON obsidian_sync_log(user_id);

CREATE INDEX IF NOT EXISTS idx_obsidian_sync_log_started_at
    ON obsidian_sync_log(started_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Obsidian Vault Configs RLS
ALTER TABLE obsidian_vault_configs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own vault configs" ON obsidian_vault_configs;
CREATE POLICY "Users can view their own vault configs" ON obsidian_vault_configs
    FOR SELECT USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can manage their own vault configs" ON obsidian_vault_configs;
CREATE POLICY "Users can manage their own vault configs" ON obsidian_vault_configs
    FOR ALL USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Service role has full access to obsidian_vault_configs" ON obsidian_vault_configs;
CREATE POLICY "Service role has full access to obsidian_vault_configs" ON obsidian_vault_configs
    FOR ALL USING (auth.role() = 'service_role');

-- Obsidian Sync State RLS
ALTER TABLE obsidian_sync_state ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view sync state for their configs" ON obsidian_sync_state;
CREATE POLICY "Users can view sync state for their configs" ON obsidian_sync_state
    FOR SELECT USING (
        config_id IN (
            SELECT id FROM obsidian_vault_configs WHERE user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can manage sync state for their configs" ON obsidian_sync_state;
CREATE POLICY "Users can manage sync state for their configs" ON obsidian_sync_state
    FOR ALL USING (
        config_id IN (
            SELECT id FROM obsidian_vault_configs WHERE user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Service role has full access to obsidian_sync_state" ON obsidian_sync_state;
CREATE POLICY "Service role has full access to obsidian_sync_state" ON obsidian_sync_state
    FOR ALL USING (auth.role() = 'service_role');

-- Obsidian Sync Log RLS
ALTER TABLE obsidian_sync_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own sync logs" ON obsidian_sync_log;
CREATE POLICY "Users can view their own sync logs" ON obsidian_sync_log
    FOR SELECT USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can manage their own sync logs" ON obsidian_sync_log;
CREATE POLICY "Users can manage their own sync logs" ON obsidian_sync_log
    FOR ALL USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Service role has full access to obsidian_sync_log" ON obsidian_sync_log;
CREATE POLICY "Service role has full access to obsidian_sync_log" ON obsidian_sync_log
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update vault config timestamp on changes
CREATE OR REPLACE FUNCTION update_obsidian_vault_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_obsidian_vault_config_timestamp ON obsidian_vault_configs;
CREATE TRIGGER trigger_update_obsidian_vault_config_timestamp
BEFORE UPDATE ON obsidian_vault_configs
FOR EACH ROW
EXECUTE FUNCTION update_obsidian_vault_config_timestamp();

-- Function to update sync state timestamp on changes
CREATE OR REPLACE FUNCTION update_obsidian_sync_state_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_obsidian_sync_state_timestamp ON obsidian_sync_state;
CREATE TRIGGER trigger_update_obsidian_sync_state_timestamp
BEFORE UPDATE ON obsidian_sync_state
FOR EACH ROW
EXECUTE FUNCTION update_obsidian_sync_state_timestamp();

-- Function to compute sync log duration when completed
CREATE OR REPLACE FUNCTION compute_obsidian_sync_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_ms = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)) * 1000;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_compute_obsidian_sync_duration ON obsidian_sync_log;
CREATE TRIGGER trigger_compute_obsidian_sync_duration
BEFORE UPDATE ON obsidian_sync_log
FOR EACH ROW
EXECUTE FUNCTION compute_obsidian_sync_duration();

-- ============================================================================
-- ADD SOURCE PLATFORM SUPPORT TO DOCUMENTS
-- ============================================================================
-- Ensure documents table can track Obsidian as a source

-- Add obsidian-specific columns if they don't exist
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS obsidian_vault_path TEXT,
    ADD COLUMN IF NOT EXISTS obsidian_file_path TEXT;

COMMENT ON COLUMN documents.obsidian_vault_path IS 'Source vault path for Obsidian-synced documents';
COMMENT ON COLUMN documents.obsidian_file_path IS 'Relative file path within the Obsidian vault';

-- Index for finding documents by Obsidian source
CREATE INDEX IF NOT EXISTS idx_documents_obsidian_source
    ON documents(obsidian_vault_path)
    WHERE obsidian_vault_path IS NOT NULL;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Vault configs with sync stats
CREATE OR REPLACE VIEW v_obsidian_vault_status AS
SELECT
    ovc.*,
    COUNT(oss.id) as total_files,
    COUNT(oss.id) FILTER (WHERE oss.sync_status = 'synced') as synced_files,
    COUNT(oss.id) FILTER (WHERE oss.sync_status = 'pending') as pending_files,
    COUNT(oss.id) FILTER (WHERE oss.sync_status = 'failed') as failed_files,
    MAX(oss.last_synced_at) as latest_file_sync
FROM obsidian_vault_configs ovc
LEFT JOIN obsidian_sync_state oss ON ovc.id = oss.config_id
GROUP BY ovc.id;

-- View: Recent sync operations
CREATE OR REPLACE VIEW v_obsidian_recent_syncs AS
SELECT
    osl.*,
    ovc.vault_path,
    ovc.vault_name
FROM obsidian_sync_log osl
JOIN obsidian_vault_configs ovc ON osl.config_id = ovc.id
ORDER BY osl.started_at DESC;

-- ============================================================================
-- DONE!
-- ============================================================================
