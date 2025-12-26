-- Migration 027: Add ADDIE Phase Tracking to Conversations
-- Purpose: Track current ADDIE phase for each conversation
-- Created: December 18, 2025

-- Add phase tracking columns to conversations
ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS addie_phase VARCHAR(50),
  ADD COLUMN IF NOT EXISTS phase_updated_at TIMESTAMPTZ;

-- Add index for efficient phase filtering
CREATE INDEX IF NOT EXISTS idx_conversations_addie_phase ON conversations(addie_phase);

-- Add check constraint for valid ADDIE phases
ALTER TABLE conversations
  ADD CONSTRAINT check_conversation_addie_phase
  CHECK (addie_phase IS NULL OR addie_phase IN ('Analysis', 'Design', 'Development', 'Implementation', 'Evaluation', 'General'));

-- Comment on new columns
COMMENT ON COLUMN conversations.addie_phase IS 'Current detected ADDIE phase for this conversation';
COMMENT ON COLUMN conversations.phase_updated_at IS 'Timestamp when the phase was last updated/detected';
