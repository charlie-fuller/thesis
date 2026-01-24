-- Migration: 045_output_source_tracking
-- Description: Track which previous outputs were used as input for each output
-- Date: 2026-01-24

-- Add source_outputs column to track input dependencies
ALTER TABLE purdy_outputs
ADD COLUMN IF NOT EXISTS source_outputs JSONB;

-- Add comment for documentation
COMMENT ON COLUMN purdy_outputs.source_outputs IS 'Array of previous outputs used as input: [{agent_type, version, id}]';
