-- Migration: 027_compass_improvement_actions
-- Description: Add improvement_actions column to career status reports
-- Created: 2026-01-20

-- Add improvement_actions column for concrete, actionable improvement steps per dimension
ALTER TABLE compass_status_reports
ADD COLUMN IF NOT EXISTS improvement_actions JSONB DEFAULT '{}';

-- Comment
COMMENT ON COLUMN compass_status_reports.improvement_actions IS 'Concrete actionable improvement steps per dimension, keyed by dimension name';
