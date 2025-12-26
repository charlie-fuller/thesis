-- ============================================================================
-- MIGRATION: System Instruction Versioning
-- Description: Add versioning support for global system instructions
-- Author: Claude
-- Date: 2025-12-24
-- ============================================================================

-- ============================================================================
-- STEP 1: Create system_instruction_versions table
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_instruction_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_number VARCHAR(20) NOT NULL UNIQUE,
    content TEXT NOT NULL,
    storage_path TEXT,
    file_size BIGINT DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_active BOOLEAN DEFAULT FALSE,
    version_notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    activated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',

    CONSTRAINT version_number_format CHECK (version_number ~ '^[0-9]+\.[0-9]+(-.+)?$')
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_system_instruction_versions_status
    ON system_instruction_versions(status);
CREATE INDEX IF NOT EXISTS idx_system_instruction_versions_is_active
    ON system_instruction_versions(is_active);
CREATE INDEX IF NOT EXISTS idx_system_instruction_versions_created_at
    ON system_instruction_versions(created_at DESC);

-- Ensure only one active version at a time
-- This partial unique index guarantees that only one row can have is_active = TRUE
CREATE UNIQUE INDEX IF NOT EXISTS idx_only_one_active_version
    ON system_instruction_versions(is_active)
    WHERE is_active = TRUE;

-- ============================================================================
-- STEP 2: Add system_instruction_version_id to conversations table
-- ============================================================================

ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS system_instruction_version_id UUID
    REFERENCES system_instruction_versions(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_si_version_id
    ON conversations(system_instruction_version_id);

-- ============================================================================
-- STEP 3: Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on the new table
ALTER TABLE system_instruction_versions ENABLE ROW LEVEL SECURITY;

-- Policy: Admins can do everything
CREATE POLICY admin_all_access ON system_instruction_versions
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'admin'
        )
    );

-- Policy: All authenticated users can read active version
CREATE POLICY users_read_active ON system_instruction_versions
    FOR SELECT
    TO authenticated
    USING (is_active = TRUE);

-- ============================================================================
-- STEP 4: Helper function to update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_system_instruction_versions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_system_instruction_versions_updated_at
    BEFORE UPDATE ON system_instruction_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_system_instruction_versions_updated_at();

-- ============================================================================
-- STEP 5: Grant permissions for service role (backend)
-- ============================================================================

-- The service role (used by backend) should have full access
GRANT ALL ON system_instruction_versions TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Note: The initial version (1.3) will be seeded via a separate script or
-- through the admin UI after this migration runs. This keeps the DDL migration
-- clean and allows for manual verification before seeding data.
