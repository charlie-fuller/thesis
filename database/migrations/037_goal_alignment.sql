-- Migration: 037_goal_alignment
-- Description: Add goal alignment score and details for IS team FY27 strategic goals
-- Date: 2026-01-23

-- Add goal_alignment_score: 0-100 percentage indicating alignment with IS strategic goals
ALTER TABLE ai_opportunities
ADD COLUMN IF NOT EXISTS goal_alignment_score INTEGER CHECK (goal_alignment_score >= 0 AND goal_alignment_score <= 100);

-- Add goal_alignment_details: JSONB containing pillar scores, KPI impacts, and summary
-- Structure:
-- {
--   "pillar_scores": {
--     "decision_ready_journey": { "score": 0-25, "rationale": "..." },
--     "maximize_systems_ai": { "score": 0-25, "rationale": "..." },
--     "data_first_workforce": { "score": 0-25, "rationale": "..." },
--     "high_trust_culture": { "score": 0-25, "rationale": "..." }
--   },
--   "kpi_impacts": ["AI Agent Success Rate", "Production Agents"],
--   "summary": "Overall alignment summary",
--   "analyzed_at": "2026-01-23T..."
-- }
ALTER TABLE ai_opportunities
ADD COLUMN IF NOT EXISTS goal_alignment_details JSONB DEFAULT '{}'::jsonb;

-- Add comments for documentation
COMMENT ON COLUMN ai_opportunities.goal_alignment_score IS 'Alignment percentage (0-100) with IS team FY27 strategic goals across 4 pillars';
COMMENT ON COLUMN ai_opportunities.goal_alignment_details IS 'JSONB with pillar scores, rationales, KPI impacts, and summary';

-- Create index for filtering/sorting by alignment score
CREATE INDEX IF NOT EXISTS idx_ai_opportunities_goal_alignment
ON ai_opportunities(client_id, goal_alignment_score)
WHERE goal_alignment_score IS NOT NULL;
