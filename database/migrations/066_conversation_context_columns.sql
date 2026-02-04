-- Migration: Add project and initiative context to conversations and meeting rooms
-- This enables unified chat interface where all chats can be filtered by project/initiative

-- Add context columns to conversations table
ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES ai_projects(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS initiative_id UUID REFERENCES disco_initiatives(id) ON DELETE SET NULL;

-- Create partial indexes for efficient filtering (only index non-null values)
CREATE INDEX IF NOT EXISTS idx_conversations_project_id
  ON conversations(project_id)
  WHERE project_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_initiative_id
  ON conversations(initiative_id)
  WHERE initiative_id IS NOT NULL;

-- Composite indexes for common query patterns (client + context + ordering)
CREATE INDEX IF NOT EXISTS idx_conversations_client_project
  ON conversations(client_id, project_id, updated_at DESC)
  WHERE project_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_client_initiative
  ON conversations(client_id, initiative_id, updated_at DESC)
  WHERE initiative_id IS NOT NULL;

-- Add context columns to meeting_rooms table
ALTER TABLE meeting_rooms
  ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES ai_projects(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS initiative_id UUID REFERENCES disco_initiatives(id) ON DELETE SET NULL;

-- Create partial indexes for meeting rooms
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_project_id
  ON meeting_rooms(project_id)
  WHERE project_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_meeting_rooms_initiative_id
  ON meeting_rooms(initiative_id)
  WHERE initiative_id IS NOT NULL;

-- Comment on new columns
COMMENT ON COLUMN conversations.project_id IS 'Links conversation to a specific project for context-aware chat';
COMMENT ON COLUMN conversations.initiative_id IS 'Links conversation to a specific DISCo initiative for context-aware chat';
COMMENT ON COLUMN meeting_rooms.project_id IS 'Links meeting room to a specific project';
COMMENT ON COLUMN meeting_rooms.initiative_id IS 'Links meeting room to a specific DISCo initiative';
