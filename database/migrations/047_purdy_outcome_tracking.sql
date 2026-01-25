-- Migration 047: PuRDy Outcome Tracking
-- Adds columns to track initiative outcomes for continuous improvement
-- Part of v3.0 rubric redesign: measuring decision velocity and stakeholder conviction

-- Add outcome tracking columns to purdy_initiatives
ALTER TABLE purdy_initiatives
ADD COLUMN IF NOT EXISTS decided_at TIMESTAMPTZ DEFAULT NULL,
ADD COLUMN IF NOT EXISTS launched_at TIMESTAMPTZ DEFAULT NULL,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ DEFAULT NULL,
ADD COLUMN IF NOT EXISTS abandoned_at TIMESTAMPTZ DEFAULT NULL,
ADD COLUMN IF NOT EXISTS decision_velocity_days INTEGER GENERATED ALWAYS AS (
  CASE
    WHEN decided_at IS NOT NULL AND created_at IS NOT NULL
    THEN EXTRACT(DAY FROM (decided_at - created_at))::INTEGER
    ELSE NULL
  END
) STORED;

-- Add stakeholder feedback to purdy_outputs
ALTER TABLE purdy_outputs
ADD COLUMN IF NOT EXISTS stakeholder_rating INTEGER DEFAULT NULL CHECK (stakeholder_rating BETWEEN 1 AND 5),
ADD COLUMN IF NOT EXISTS stakeholder_feedback TEXT DEFAULT NULL;

-- Create outcome metrics view for continuous improvement
CREATE OR REPLACE VIEW purdy_outcome_metrics AS
SELECT
  i.id,
  i.name,
  i.status,
  i.created_at,
  i.decided_at,
  i.launched_at,
  i.completed_at,
  i.abandoned_at,
  i.decision_velocity_days,
  CASE
    WHEN i.decided_at IS NOT NULL AND i.decision_velocity_days <= 7 THEN 'fast'
    WHEN i.decided_at IS NOT NULL AND i.decision_velocity_days <= 14 THEN 'moderate'
    WHEN i.decided_at IS NOT NULL THEN 'slow'
    ELSE 'pending'
  END as velocity_category,
  (SELECT AVG(stakeholder_rating) FROM purdy_outputs WHERE initiative_id = i.id AND stakeholder_rating IS NOT NULL) as avg_stakeholder_rating,
  (SELECT COUNT(*) FROM purdy_outputs WHERE initiative_id = i.id AND stakeholder_rating IS NOT NULL) as ratings_count,
  (SELECT COUNT(*) FROM purdy_outputs WHERE initiative_id = i.id) as total_outputs
FROM purdy_initiatives i;

-- Index for faster outcome queries
CREATE INDEX IF NOT EXISTS idx_purdy_initiatives_decided_at ON purdy_initiatives(decided_at) WHERE decided_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_purdy_initiatives_status_dates ON purdy_initiatives(status, decided_at, launched_at);
CREATE INDEX IF NOT EXISTS idx_purdy_outputs_stakeholder_rating ON purdy_outputs(initiative_id, stakeholder_rating) WHERE stakeholder_rating IS NOT NULL;

-- Comment for documentation
COMMENT ON COLUMN purdy_initiatives.decided_at IS 'When stakeholders made a decision based on synthesis output';
COMMENT ON COLUMN purdy_initiatives.launched_at IS 'When the initiative transitioned from decision to implementation';
COMMENT ON COLUMN purdy_initiatives.completed_at IS 'When the initiative achieved its goals';
COMMENT ON COLUMN purdy_initiatives.abandoned_at IS 'When the initiative was abandoned (alternative to completed_at)';
COMMENT ON COLUMN purdy_initiatives.decision_velocity_days IS 'Days from initiative creation to decision (auto-calculated)';
COMMENT ON COLUMN purdy_outputs.stakeholder_rating IS 'Stakeholder conviction rating 1-5: "I know what to do"';
COMMENT ON COLUMN purdy_outputs.stakeholder_feedback IS 'Optional freeform feedback from stakeholder';
