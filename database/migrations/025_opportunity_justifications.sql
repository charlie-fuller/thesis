-- Migration: Opportunity Justifications
-- Date: 2026-01-18
-- Description: Adds text justification fields for opportunity description and
--              each of the four scoring dimensions (ROI, effort, alignment, readiness).
--              These provide 3-4 sentence explanations for each score.

-- ============================================================================
-- ADD JUSTIFICATION COLUMNS TO AI_OPPORTUNITIES
-- ============================================================================

-- Opportunity summary - 3-4 sentence description of what this opportunity is
ALTER TABLE ai_opportunities
    ADD COLUMN IF NOT EXISTS opportunity_summary TEXT;

-- ROI Potential justification - why this score was given
ALTER TABLE ai_opportunities
    ADD COLUMN IF NOT EXISTS roi_justification TEXT;

-- Implementation Effort justification - why this score was given
ALTER TABLE ai_opportunities
    ADD COLUMN IF NOT EXISTS effort_justification TEXT;

-- Strategic Alignment justification - why this score was given
ALTER TABLE ai_opportunities
    ADD COLUMN IF NOT EXISTS alignment_justification TEXT;

-- Stakeholder Readiness justification - why this score was given
ALTER TABLE ai_opportunities
    ADD COLUMN IF NOT EXISTS readiness_justification TEXT;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN ai_opportunities.opportunity_summary IS '3-4 sentence summary describing what this opportunity is and its potential impact';
COMMENT ON COLUMN ai_opportunities.roi_justification IS '3-4 sentence explanation of why this ROI potential score was assigned';
COMMENT ON COLUMN ai_opportunities.effort_justification IS '3-4 sentence explanation of why this implementation effort score was assigned';
COMMENT ON COLUMN ai_opportunities.alignment_justification IS '3-4 sentence explanation of why this strategic alignment score was assigned';
COMMENT ON COLUMN ai_opportunities.readiness_justification IS '3-4 sentence explanation of why this stakeholder readiness score was assigned';

-- ============================================================================
-- DONE!
-- ============================================================================
