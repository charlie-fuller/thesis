-- DISCo Checkpoints: Human-in-the-loop approval gates between consolidated agents
-- Migration: 061_disco_checkpoints.sql
-- Date: 2026-02-02

-- Create disco_checkpoints table
CREATE TABLE IF NOT EXISTS disco_checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    initiative_id UUID NOT NULL REFERENCES disco_initiatives(id) ON DELETE CASCADE,
    checkpoint_number INTEGER NOT NULL CHECK (checkpoint_number BETWEEN 1 AND 4),
    status TEXT NOT NULL DEFAULT 'locked' CHECK (status IN ('locked', 'needs_review', 'approved', 'stale')),
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES auth.users(id),
    notes TEXT,
    checklist_items JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Each initiative can have only one checkpoint per number
    UNIQUE(initiative_id, checkpoint_number)
);

-- Create index for efficient lookup
CREATE INDEX IF NOT EXISTS idx_disco_checkpoints_initiative
ON disco_checkpoints(initiative_id);

CREATE INDEX IF NOT EXISTS idx_disco_checkpoints_status
ON disco_checkpoints(status);

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_disco_checkpoint_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS disco_checkpoints_updated_at ON disco_checkpoints;
CREATE TRIGGER disco_checkpoints_updated_at
    BEFORE UPDATE ON disco_checkpoints
    FOR EACH ROW
    EXECUTE FUNCTION update_disco_checkpoint_timestamp();

-- RLS Policies
ALTER TABLE disco_checkpoints ENABLE ROW LEVEL SECURITY;

-- Users can view checkpoints for initiatives they have access to
CREATE POLICY "Users can view checkpoints for their initiatives"
ON disco_checkpoints FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM disco_initiatives
        WHERE disco_initiatives.id = disco_checkpoints.initiative_id
        AND disco_initiatives.created_by = auth.uid()
    )
);

-- Users can insert checkpoints for initiatives they own
CREATE POLICY "Users can insert checkpoints for their initiatives"
ON disco_checkpoints FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM disco_initiatives
        WHERE disco_initiatives.id = disco_checkpoints.initiative_id
        AND disco_initiatives.created_by = auth.uid()
    )
);

-- Users can update checkpoints for initiatives they own
CREATE POLICY "Users can update checkpoints for their initiatives"
ON disco_checkpoints FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM disco_initiatives
        WHERE disco_initiatives.id = disco_checkpoints.initiative_id
        AND disco_initiatives.created_by = auth.uid()
    )
);

-- Users can delete checkpoints for initiatives they own
CREATE POLICY "Users can delete checkpoints for their initiatives"
ON disco_checkpoints FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM disco_initiatives
        WHERE disco_initiatives.id = disco_checkpoints.initiative_id
        AND disco_initiatives.created_by = auth.uid()
    )
);

-- Add last_run_at to disco_outputs for staleness tracking
-- This tracks when each agent type was last run for an initiative
ALTER TABLE disco_outputs
ADD COLUMN IF NOT EXISTS last_run_at TIMESTAMPTZ DEFAULT NOW();

-- Create index for staleness checks
CREATE INDEX IF NOT EXISTS idx_disco_outputs_last_run
ON disco_outputs(initiative_id, agent_type, last_run_at DESC);

-- Function to initialize checkpoints for an initiative
CREATE OR REPLACE FUNCTION initialize_disco_checkpoints(p_initiative_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Insert all 4 checkpoints in locked state if they don't exist
    INSERT INTO disco_checkpoints (initiative_id, checkpoint_number, status)
    VALUES
        (p_initiative_id, 1, 'locked'),
        (p_initiative_id, 2, 'locked'),
        (p_initiative_id, 3, 'locked'),
        (p_initiative_id, 4, 'locked')
    ON CONFLICT (initiative_id, checkpoint_number) DO NOTHING;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update checkpoint status based on agent completion
CREATE OR REPLACE FUNCTION update_checkpoint_on_agent_complete()
RETURNS TRIGGER AS $$
DECLARE
    checkpoint_num INTEGER;
BEGIN
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

-- Trigger to update checkpoints when outputs are created
DROP TRIGGER IF EXISTS disco_output_checkpoint_trigger ON disco_outputs;
CREATE TRIGGER disco_output_checkpoint_trigger
    AFTER INSERT ON disco_outputs
    FOR EACH ROW
    EXECUTE FUNCTION update_checkpoint_on_agent_complete();

-- Comment on checkpoint purposes
COMMENT ON TABLE disco_checkpoints IS 'Human-in-the-loop approval gates between DISCo consolidated agents';
COMMENT ON COLUMN disco_checkpoints.checkpoint_number IS '1=After Discovery Guide, 2=After Insight Analyst, 3=After Initiative Builder, 4=After Requirements Generator';
COMMENT ON COLUMN disco_checkpoints.status IS 'locked=waiting for previous agent, needs_review=awaiting approval, approved=passed, stale=new docs since approval';
COMMENT ON COLUMN disco_checkpoints.checklist_items IS 'JSON array of checklist items with completed status';
