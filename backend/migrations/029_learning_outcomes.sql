-- Migration: Add learning outcomes tracking
-- This enables users to track expected vs actual outcomes for their training projects

-- Create learning_outcomes table
CREATE TABLE IF NOT EXISTS learning_outcomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Outcome identification
    title VARCHAR(500) NOT NULL,
    description TEXT,
    metric_type VARCHAR(100) NOT NULL, -- e.g., 'completion_rate', 'assessment_score', 'performance_improvement', 'roi', 'custom'

    -- Target values
    baseline_value DECIMAL(12, 4),  -- starting point
    target_value DECIMAL(12, 4),    -- goal
    actual_value DECIMAL(12, 4),    -- measured result
    unit VARCHAR(50),               -- e.g., '%', 'points', '$', 'hours'

    -- Tracking metadata
    target_date DATE,               -- when we expect to achieve this
    measured_at TIMESTAMPTZ,        -- when actual was measured
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, achieved, missed, partial

    -- Notes and context
    notes TEXT,
    data_source VARCHAR(500),       -- where the measurement comes from

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_learning_outcomes_project ON learning_outcomes(project_id);
CREATE INDEX IF NOT EXISTS idx_learning_outcomes_user ON learning_outcomes(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_outcomes_status ON learning_outcomes(status);
CREATE INDEX IF NOT EXISTS idx_learning_outcomes_metric_type ON learning_outcomes(metric_type);

-- Add constraint for valid metric types
ALTER TABLE learning_outcomes
    ADD CONSTRAINT check_learning_outcome_metric_type
    CHECK (metric_type IN (
        'completion_rate',
        'assessment_score',
        'performance_improvement',
        'time_to_competency',
        'learner_satisfaction',
        'knowledge_retention',
        'behavior_change',
        'business_impact',
        'roi',
        'custom'
    ));

-- Add constraint for valid status values
ALTER TABLE learning_outcomes
    ADD CONSTRAINT check_learning_outcome_status
    CHECK (status IN ('pending', 'in_progress', 'achieved', 'missed', 'partial'));

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_learning_outcomes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_learning_outcomes_updated_at ON learning_outcomes;
CREATE TRIGGER trigger_learning_outcomes_updated_at
    BEFORE UPDATE ON learning_outcomes
    FOR EACH ROW
    EXECUTE FUNCTION update_learning_outcomes_updated_at();

-- Add expected_roi field to projects table for quick ROI tracking
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS expected_roi_percentage DECIMAL(8, 2),
    ADD COLUMN IF NOT EXISTS actual_roi_percentage DECIMAL(8, 2),
    ADD COLUMN IF NOT EXISTS roi_notes TEXT;
