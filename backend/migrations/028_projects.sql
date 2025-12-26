-- Migration 028: Add Projects Table for Conversation Grouping
-- Purpose: Group related conversations into projects with shared context
-- Created: December 18, 2025

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    current_phase VARCHAR(50) DEFAULT 'Analysis',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add project_id to conversations table
ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL;

-- Add indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_client_id ON projects(client_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);

-- Add check constraint for valid project phases
ALTER TABLE projects
  ADD CONSTRAINT check_project_phase
  CHECK (current_phase IS NULL OR current_phase IN ('Analysis', 'Design', 'Development', 'Implementation', 'Evaluation', 'Complete'));

-- Add check constraint for valid project status
ALTER TABLE projects
  ADD CONSTRAINT check_project_status
  CHECK (status IN ('active', 'archived', 'complete'));

-- Add trigger to update updated_at on projects
CREATE OR REPLACE FUNCTION update_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS projects_updated_at_trigger ON projects;
CREATE TRIGGER projects_updated_at_trigger
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_projects_updated_at();

-- Comments
COMMENT ON TABLE projects IS 'Groups related conversations into learning design projects';
COMMENT ON COLUMN projects.current_phase IS 'Current ADDIE phase of the project';
COMMENT ON COLUMN projects.status IS 'Project status: active, archived, or complete';
COMMENT ON COLUMN conversations.project_id IS 'Optional link to parent project';
