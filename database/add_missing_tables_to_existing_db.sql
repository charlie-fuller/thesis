-- ============================================================================
-- Add Missing Tables to Existing Database
-- Safe to run on production - only adds tables/columns that don't exist
-- ============================================================================

-- Google Drive sync log
CREATE TABLE IF NOT EXISTS google_drive_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    folder_id VARCHAR(255),
    folder_name VARCHAR(255),
    sync_type VARCHAR(50) DEFAULT 'full',
    documents_added INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_skipped INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER
);

-- Notion sync log
CREATE TABLE IF NOT EXISTS notion_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    page_id VARCHAR(255),
    page_name VARCHAR(255),
    sync_type VARCHAR(50) DEFAULT 'full',
    documents_added INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_skipped INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER
);

-- Interview sessions
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL UNIQUE,
    session_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata JSONB
);

-- Interview extractions
CREATE TABLE IF NOT EXISTS interview_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    transcript TEXT NOT NULL,
    extraction_json JSONB,
    audio_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending_solomon',
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    review_reason TEXT,
    completeness_score INTEGER,
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Solomon reviews
CREATE TABLE IF NOT EXISTS solomon_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extraction_id UUID REFERENCES interview_extractions(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    generated_instructions TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES users(id),
    deployment_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Add missing columns to clients table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'clients' AND column_name = 'organization'
    ) THEN
        ALTER TABLE clients ADD COLUMN organization TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'clients' AND column_name = 'system_instructions'
    ) THEN
        ALTER TABLE clients ADD COLUMN system_instructions TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'clients' AND column_name = 'status'
    ) THEN
        ALTER TABLE clients ADD COLUMN status TEXT DEFAULT 'active';
    END IF;
END $$;

-- Add missing columns to api_usage_logs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'operation'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN operation TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'model'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN model TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'input_tokens'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN input_tokens INTEGER;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'output_tokens'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN output_tokens INTEGER;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'cost_usd'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN cost_usd DECIMAL(10, 6);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN metadata JSONB;
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_google_drive_sync_log_user_id ON google_drive_sync_log(user_id);
CREATE INDEX IF NOT EXISTS idx_google_drive_sync_log_status ON google_drive_sync_log(status);
CREATE INDEX IF NOT EXISTS idx_notion_sync_log_user_id ON notion_sync_log(user_id);
CREATE INDEX IF NOT EXISTS idx_notion_sync_log_status ON notion_sync_log(status);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_client_id ON interview_sessions(client_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interview_extractions_client_id ON interview_extractions(client_id);
CREATE INDEX IF NOT EXISTS idx_interview_extractions_user_id ON interview_extractions(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_extractions_status ON interview_extractions(status);
CREATE INDEX IF NOT EXISTS idx_solomon_reviews_extraction_id ON solomon_reviews(extraction_id);
CREATE INDEX IF NOT EXISTS idx_solomon_reviews_client_id ON solomon_reviews(client_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_operation ON api_usage_logs(operation);

-- Enable RLS on new tables
ALTER TABLE google_drive_sync_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE notion_sync_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE solomon_reviews ENABLE ROW LEVEL SECURITY;

-- Sync log policies
DROP POLICY IF EXISTS "Users can view own sync logs" ON google_drive_sync_log;
DROP POLICY IF EXISTS "Users can insert own sync logs" ON google_drive_sync_log;
DROP POLICY IF EXISTS "Users can update own sync logs" ON google_drive_sync_log;
CREATE POLICY "Users can view own sync logs" ON google_drive_sync_log FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own sync logs" ON google_drive_sync_log FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own sync logs" ON google_drive_sync_log FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view own Notion sync logs" ON notion_sync_log;
DROP POLICY IF EXISTS "Users can insert own Notion sync logs" ON notion_sync_log;
DROP POLICY IF EXISTS "Users can update own Notion sync logs" ON notion_sync_log;
CREATE POLICY "Users can view own Notion sync logs" ON notion_sync_log FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own Notion sync logs" ON notion_sync_log FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own Notion sync logs" ON notion_sync_log FOR UPDATE USING (auth.uid() = user_id);

-- ============================================================================
-- DONE!
-- ============================================================================
