-- Migration: 071_initiative_throughline
-- Description: Add throughline (structured input framing) and throughline_resolution columns
-- Date: 2026-02-12

-- Add throughline JSONB column to disco_initiatives
-- Stores structured input framing: problem_statements, hypotheses, gaps, desired_outcome_state
ALTER TABLE disco_initiatives
ADD COLUMN IF NOT EXISTS throughline JSONB DEFAULT NULL;

-- Add throughline_resolution JSONB column to disco_outputs
-- Stores convergence resolution: hypothesis_resolutions, gap_statuses, state_changes, so_what
ALTER TABLE disco_outputs
ADD COLUMN IF NOT EXISTS throughline_resolution JSONB DEFAULT NULL;

-- Add comments for documentation
COMMENT ON COLUMN disco_initiatives.throughline IS 'Structured input framing: problem_statements, hypotheses, gaps, desired_outcome_state';
COMMENT ON COLUMN disco_outputs.throughline_resolution IS 'Convergence resolution: hypothesis_resolutions, gap_statuses, state_changes, so_what';
