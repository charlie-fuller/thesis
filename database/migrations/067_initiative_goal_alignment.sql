-- Migration 067: Add goal alignment columns to disco_initiatives
-- Enables IS FY27 strategic goal alignment analysis at the initiative level

ALTER TABLE disco_initiatives
  ADD COLUMN IF NOT EXISTS goal_alignment_score INTEGER,
  ADD COLUMN IF NOT EXISTS goal_alignment_details JSONB;

-- Index for future dashboard queries (e.g. sorting initiatives by alignment)
CREATE INDEX IF NOT EXISTS idx_disco_initiatives_goal_alignment_score
  ON disco_initiatives (goal_alignment_score)
  WHERE goal_alignment_score IS NOT NULL;

-- Add a check constraint for valid score range
ALTER TABLE disco_initiatives
  ADD CONSTRAINT chk_initiative_goal_alignment_score
  CHECK (goal_alignment_score IS NULL OR (goal_alignment_score >= 0 AND goal_alignment_score <= 100));
