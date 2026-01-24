-- Migration: 046_synthesis_notes_column
-- Description: Store multi-pass synthesis notes separately from main content
-- Date: 2026-01-24

-- Add synthesis_notes column for the multi-pass explainability report
ALTER TABLE purdy_outputs
ADD COLUMN IF NOT EXISTS synthesis_notes TEXT;

-- Add comment for documentation
COMMENT ON COLUMN purdy_outputs.synthesis_notes IS 'For multi-pass mode: detailed attribution of which pass contributed what and why (separate from main PRD content)';
