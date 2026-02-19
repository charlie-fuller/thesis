-- =============================================================
-- Migration 081: Project-Level DISCO Agents
-- Extends disco_outputs and disco_runs to support project-scoped
-- agent runs alongside initiative-scoped ones.
-- =============================================================

BEGIN;

-- =============================================================
-- SECTION 1: Add project_id columns
-- =============================================================

-- Add nullable project_id to disco_outputs
ALTER TABLE disco_outputs
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES ai_projects(id) ON DELETE CASCADE;

-- Add nullable project_id to disco_runs
ALTER TABLE disco_runs
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES ai_projects(id) ON DELETE CASCADE;

-- =============================================================
-- SECTION 2: Make initiative_id nullable
-- =============================================================

-- disco_outputs: drop NOT NULL on initiative_id
ALTER TABLE disco_outputs ALTER COLUMN initiative_id DROP NOT NULL;

-- disco_runs: drop NOT NULL on initiative_id
ALTER TABLE disco_runs ALTER COLUMN initiative_id DROP NOT NULL;

-- =============================================================
-- SECTION 3: XOR check constraint (exactly one must be set)
-- =============================================================

ALTER TABLE disco_outputs
ADD CONSTRAINT disco_outputs_scope_xor
CHECK (
    (initiative_id IS NOT NULL AND project_id IS NULL) OR
    (initiative_id IS NULL AND project_id IS NOT NULL)
);

ALTER TABLE disco_runs
ADD CONSTRAINT disco_runs_scope_xor
CHECK (
    (initiative_id IS NOT NULL AND project_id IS NULL) OR
    (initiative_id IS NULL AND project_id IS NOT NULL)
);

-- =============================================================
-- SECTION 4: Indexes for project-scoped queries
-- =============================================================

CREATE INDEX IF NOT EXISTS idx_disco_outputs_project
ON disco_outputs(project_id) WHERE project_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_disco_outputs_project_agent
ON disco_outputs(project_id, agent_type, created_at DESC) WHERE project_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_disco_runs_project
ON disco_runs(project_id) WHERE project_id IS NOT NULL;

-- =============================================================
-- SECTION 5: RLS policies for project-scoped rows
-- =============================================================

-- disco_outputs: allow SELECT for project-scoped rows
CREATE POLICY disco_outputs_project_select ON disco_outputs FOR SELECT
USING (
    project_id IS NOT NULL AND
    EXISTS (
        SELECT 1 FROM ai_projects
        WHERE ai_projects.id = disco_outputs.project_id
        AND ai_projects.client_id = (
            SELECT client_id FROM users WHERE id = (SELECT auth.uid())
        )
    )
);

-- disco_outputs: allow INSERT for project-scoped rows
CREATE POLICY disco_outputs_project_insert ON disco_outputs FOR INSERT
WITH CHECK (
    project_id IS NOT NULL AND
    EXISTS (
        SELECT 1 FROM ai_projects
        WHERE ai_projects.id = disco_outputs.project_id
        AND ai_projects.client_id = (
            SELECT client_id FROM users WHERE id = (SELECT auth.uid())
        )
    )
);

-- disco_outputs: allow UPDATE for project-scoped rows
CREATE POLICY disco_outputs_project_update ON disco_outputs FOR UPDATE
USING (
    project_id IS NOT NULL AND
    EXISTS (
        SELECT 1 FROM ai_projects
        WHERE ai_projects.id = disco_outputs.project_id
        AND ai_projects.client_id = (
            SELECT client_id FROM users WHERE id = (SELECT auth.uid())
        )
    )
);

-- disco_runs: allow SELECT for project-scoped rows
CREATE POLICY disco_runs_project_select ON disco_runs FOR SELECT
USING (
    project_id IS NOT NULL AND
    EXISTS (
        SELECT 1 FROM ai_projects
        WHERE ai_projects.id = disco_runs.project_id
        AND ai_projects.client_id = (
            SELECT client_id FROM users WHERE id = (SELECT auth.uid())
        )
    )
);

-- disco_runs: allow INSERT for project-scoped rows
CREATE POLICY disco_runs_project_insert ON disco_runs FOR INSERT
WITH CHECK (
    project_id IS NOT NULL AND
    EXISTS (
        SELECT 1 FROM ai_projects
        WHERE ai_projects.id = disco_runs.project_id
        AND ai_projects.client_id = (
            SELECT client_id FROM users WHERE id = (SELECT auth.uid())
        )
    )
);

-- disco_runs: allow UPDATE for project-scoped rows
CREATE POLICY disco_runs_project_update ON disco_runs FOR UPDATE
USING (
    project_id IS NOT NULL AND
    EXISTS (
        SELECT 1 FROM ai_projects
        WHERE ai_projects.id = disco_runs.project_id
        AND ai_projects.client_id = (
            SELECT client_id FROM users WHERE id = (SELECT auth.uid())
        )
    )
);

-- =============================================================
-- SECTION 6: Guard checkpoint trigger for project-scoped outputs
-- =============================================================

-- Replace the checkpoint trigger function to skip when initiative_id is NULL
CREATE OR REPLACE FUNCTION update_checkpoint_on_agent_complete()
RETURNS TRIGGER AS $$
DECLARE
    checkpoint_num INTEGER;
BEGIN
    -- Skip checkpoint updates for project-scoped outputs (no initiative)
    IF NEW.initiative_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Map agent types to checkpoint numbers
    checkpoint_num := CASE NEW.agent_type
        WHEN 'discovery_guide' THEN 1
        WHEN 'insight_analyst' THEN 2
        WHEN 'initiative_builder' THEN 3
        WHEN 'requirements_generator' THEN 4
        ELSE NULL
    END;

    IF checkpoint_num IS NOT NULL THEN
        -- Ensure checkpoints exist
        PERFORM initialize_disco_checkpoints(NEW.initiative_id);

        -- Update checkpoint to needs_review when agent completes
        UPDATE disco_checkpoints
        SET status = 'needs_review',
            updated_at = NOW()
        WHERE initiative_id = NEW.initiative_id
          AND checkpoint_number = checkpoint_num
          AND status IN ('locked', 'stale');
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================
-- SECTION 7: Comments
-- =============================================================

COMMENT ON COLUMN disco_outputs.project_id IS 'Project scope for project-level agent runs (XOR with initiative_id)';
COMMENT ON COLUMN disco_runs.project_id IS 'Project scope for project-level agent runs (XOR with initiative_id)';

-- Trigger PostgREST schema reload
NOTIFY pgrst, 'reload schema';

COMMIT;
