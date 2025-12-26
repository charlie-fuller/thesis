-- ============================================================================
-- Migration: Create extractions table
-- Description: Creates the extractions table for storing system instruction
--              configuration data and function selections
-- Safe to run multiple times
-- ============================================================================

-- Create extractions table
CREATE TABLE IF NOT EXISTS extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    extraction_json JSONB NOT NULL,
    deployment_status TEXT NOT NULL DEFAULT 'draft',
    -- Status values: draft, pending_review, approved, deployed, archived
    deployed_at TIMESTAMPTZ,
    deployed_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_extractions_client_id ON extractions(client_id);
CREATE INDEX IF NOT EXISTS idx_extractions_user_id ON extractions(user_id);
CREATE INDEX IF NOT EXISTS idx_extractions_deployment_status ON extractions(deployment_status);
CREATE INDEX IF NOT EXISTS idx_extractions_created_at ON extractions(created_at DESC);

-- Enable RLS
ALTER TABLE extractions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Users can view own extractions" ON extractions;
DROP POLICY IF EXISTS "Users can create own extractions" ON extractions;
DROP POLICY IF EXISTS "Users can update own extractions" ON extractions;
DROP POLICY IF EXISTS "Admins can manage all extractions" ON extractions;

CREATE POLICY "Users can view own extractions" ON extractions
FOR SELECT
USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can create own extractions" ON extractions
FOR INSERT
WITH CHECK (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can update own extractions" ON extractions
FOR UPDATE
USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Admins can manage all extractions" ON extractions
FOR ALL
USING (EXISTS (
    SELECT 1 FROM users
    WHERE users.id = auth.uid()
    AND users.role = 'admin'
));

-- Add helpful comments
COMMENT ON TABLE extractions IS 'Stores system instruction configurations and function selections for clients';
COMMENT ON COLUMN extractions.extraction_json IS 'JSON data containing selected functions and configuration details';
COMMENT ON COLUMN extractions.deployment_status IS 'Current status: draft, pending_review, approved, deployed, archived';
COMMENT ON COLUMN extractions.deployed_at IS 'Timestamp when configuration was deployed to production';
COMMENT ON COLUMN extractions.deployed_by IS 'User who deployed this configuration';

-- ============================================================================
-- DONE!
-- ============================================================================
