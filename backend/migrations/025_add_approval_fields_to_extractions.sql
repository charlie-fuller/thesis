-- Migration: Add approval fields to interview_extractions
-- Date: 2025-11-21
-- Description: Adds approved_at and approved_by columns to track extraction approval

-- Add approval tracking columns to interview_extractions
DO $$
BEGIN
    ALTER TABLE interview_extractions ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;
    ALTER TABLE interview_extractions ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES users(id);
EXCEPTION
    WHEN duplicate_column THEN NULL;
END $$;

-- Add index for approved_at queries
CREATE INDEX IF NOT EXISTS idx_interview_extractions_approved_at ON interview_extractions(approved_at);
CREATE INDEX IF NOT EXISTS idx_interview_extractions_approved_by ON interview_extractions(approved_by);

-- Add comments
COMMENT ON COLUMN interview_extractions.approved_at IS 'Timestamp when extraction was approved by an admin';
COMMENT ON COLUMN interview_extractions.approved_by IS 'User ID of the admin who approved the extraction';
