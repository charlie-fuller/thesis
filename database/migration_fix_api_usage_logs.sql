-- ============================================================================
-- Migration: Fix api_usage_logs table schema
-- Description: Adds missing columns from migration 004 to api_usage_logs
-- Safe to run multiple times
-- ============================================================================

-- Add missing columns if they don't exist
DO $$
BEGIN
    -- Add operation column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'operation'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN operation TEXT;
    END IF;

    -- Add model column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'model'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN model TEXT;
    END IF;

    -- Add input_tokens column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'input_tokens'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN input_tokens INTEGER;
    END IF;

    -- Add output_tokens column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'output_tokens'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN output_tokens INTEGER;
    END IF;

    -- Add cost_usd column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'cost_usd'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN cost_usd DECIMAL(10, 6);
    END IF;

    -- Add metadata column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'api_usage_logs' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE api_usage_logs ADD COLUMN metadata JSONB;
    END IF;
END $$;

-- Recreate index if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_api_usage_operation ON api_usage_logs(operation);

-- Add comments
COMMENT ON TABLE api_usage_logs IS 'Tracks API usage for cost monitoring and optimization';
COMMENT ON COLUMN api_usage_logs.operation IS 'Type of operation: extraction, generation, chat, etc.';
COMMENT ON COLUMN api_usage_logs.cost_usd IS 'Calculated cost in USD based on token usage and model pricing';
