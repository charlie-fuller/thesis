-- Migration: 035_opportunity_scoring_confidence
-- Description: Add scoring confidence percentage and confidence-raising questions to opportunities
-- Date: 2026-01-21

-- Add scoring_confidence: 0-100 percentage indicating confidence in the 4-dimension scores
ALTER TABLE ai_opportunities
ADD COLUMN IF NOT EXISTS scoring_confidence INTEGER CHECK (scoring_confidence BETWEEN 0 AND 100);

-- Add confidence_questions: array of questions that, if answered, would raise confidence
ALTER TABLE ai_opportunities
ADD COLUMN IF NOT EXISTS confidence_questions TEXT[] DEFAULT '{}';

-- Add comments for documentation
COMMENT ON COLUMN ai_opportunities.scoring_confidence IS 'Confidence percentage (0-100) in the accuracy of the 4-dimension scoring';
COMMENT ON COLUMN ai_opportunities.confidence_questions IS 'List of questions that, if answered, would increase scoring confidence';

-- Create index for filtering by confidence level
CREATE INDEX IF NOT EXISTS idx_ai_opportunities_scoring_confidence
ON ai_opportunities(scoring_confidence)
WHERE scoring_confidence IS NOT NULL;
