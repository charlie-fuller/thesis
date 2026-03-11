-- Migration 052: Add project_id to disco_runs and disco_outputs
-- Purpose: Enable project-scoped DISCO agent runs (not just initiative-scoped)
-- The backend code already references these columns but they were never created.

-- Add project_id to disco_runs
ALTER TABLE disco_runs
  ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES ai_projects(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_disco_runs_project_id ON disco_runs(project_id);

-- Add project_id to disco_outputs
ALTER TABLE disco_outputs
  ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES ai_projects(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_disco_outputs_project_id ON disco_outputs(project_id);
CREATE INDEX IF NOT EXISTS idx_disco_outputs_project_agent ON disco_outputs(project_id, agent_type);
