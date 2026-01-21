-- Migration: 027_compass_improvement_actions
-- Description: Add improvement_actions column to career status reports
-- Created: 2026-01-20

-- Add improvement_actions column for concrete, actionable improvement steps per dimension
-- Using DO block to handle case where column already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'compass_status_reports'
        AND column_name = 'improvement_actions'
    ) THEN
        ALTER TABLE compass_status_reports
        ADD COLUMN improvement_actions JSONB DEFAULT '{}';
    END IF;
END $$;

-- Comment (will update even if column exists)
COMMENT ON COLUMN compass_status_reports.improvement_actions IS 'Concrete actionable improvement steps per dimension, keyed by dimension name';
