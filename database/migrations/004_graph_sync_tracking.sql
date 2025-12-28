-- ============================================================================
-- GRAPH SYNC TRACKING
-- Tracks synchronization state between Supabase and Neo4j
-- ============================================================================

-- Table to log sync operations
CREATE TABLE IF NOT EXISTS graph_sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    sync_type TEXT NOT NULL CHECK (sync_type IN ('full', 'incremental', 'entity')),
    entity_type TEXT NOT NULL,
    entity_id UUID,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    sync_status TEXT NOT NULL CHECK (sync_status IN ('started', 'completed', 'failed')),
    details JSONB DEFAULT '{}',
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for efficient queries
CREATE INDEX IF NOT EXISTS idx_graph_sync_log_client
    ON graph_sync_log(client_id, synced_at DESC);

CREATE INDEX IF NOT EXISTS idx_graph_sync_log_entity
    ON graph_sync_log(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_graph_sync_log_status
    ON graph_sync_log(sync_status, synced_at DESC);

-- Table to track last sync time per entity type
CREATE TABLE IF NOT EXISTS graph_sync_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    last_synced_at TIMESTAMPTZ,
    last_sync_status TEXT,
    record_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, entity_type)
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_graph_sync_state_client
    ON graph_sync_state(client_id);

-- Function to update sync state
CREATE OR REPLACE FUNCTION update_graph_sync_state()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO graph_sync_state (client_id, entity_type, last_synced_at, last_sync_status)
    VALUES (NEW.client_id, NEW.entity_type, NEW.synced_at, NEW.sync_status)
    ON CONFLICT (client_id, entity_type)
    DO UPDATE SET
        last_synced_at = EXCLUDED.last_synced_at,
        last_sync_status = EXCLUDED.last_sync_status,
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update sync state
DROP TRIGGER IF EXISTS trg_update_graph_sync_state ON graph_sync_log;
CREATE TRIGGER trg_update_graph_sync_state
    AFTER INSERT ON graph_sync_log
    FOR EACH ROW
    WHEN (NEW.sync_status = 'completed')
    EXECUTE FUNCTION update_graph_sync_state();

-- Enable RLS
ALTER TABLE graph_sync_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE graph_sync_state ENABLE ROW LEVEL SECURITY;

-- RLS policies (users can only see their client's sync data)
DROP POLICY IF EXISTS "Users can view own client sync logs" ON graph_sync_log;
CREATE POLICY "Users can view own client sync logs"
    ON graph_sync_log FOR SELECT
    USING (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can view own client sync state" ON graph_sync_state;
CREATE POLICY "Users can view own client sync state"
    ON graph_sync_state FOR SELECT
    USING (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

-- Service role can do everything
DROP POLICY IF EXISTS "Service role full access to sync logs" ON graph_sync_log;
CREATE POLICY "Service role full access to sync logs"
    ON graph_sync_log FOR ALL
    USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role full access to sync state" ON graph_sync_state;
CREATE POLICY "Service role full access to sync state"
    ON graph_sync_state FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================================================
-- DONE!
-- ============================================================================
