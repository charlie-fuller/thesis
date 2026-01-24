-- Migration: 044_multi_pass_synthesis
-- Description: Add multi-pass synthesis support to PuRDy outputs
-- Date: 2026-01-24

-- Add synthesis_mode column to track single vs multi-pass
ALTER TABLE purdy_outputs
ADD COLUMN IF NOT EXISTS synthesis_mode TEXT DEFAULT 'single';

-- Add intermediate_outputs column to store the 3 pass outputs for multi-pass
ALTER TABLE purdy_outputs
ADD COLUMN IF NOT EXISTS intermediate_outputs JSONB;

-- Add comments for documentation
COMMENT ON COLUMN purdy_outputs.synthesis_mode IS 'single or multi_pass - indicates synthesis approach used';
COMMENT ON COLUMN purdy_outputs.intermediate_outputs IS 'For multi_pass mode, stores the 3 intermediate pass outputs with their temperatures and labels';

-- Create index for filtering by synthesis mode if needed
CREATE INDEX IF NOT EXISTS idx_purdy_outputs_synthesis_mode ON purdy_outputs(synthesis_mode);
