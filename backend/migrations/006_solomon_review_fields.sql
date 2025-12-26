-- Migration: Solomon Review Dashboard Fields
-- Date: 2025-11-05
-- Description: Adds missing extraction_json field and enhances review workflow

-- ============================================================================
-- ADD MISSING EXTRACTION_JSON TO INTERVIEW_EXTRACTIONS
-- This column is used by solomon_stage1.py but was missing from migration 004
-- ============================================================================
DO $$
BEGIN
    ALTER TABLE interview_extractions ADD COLUMN IF NOT EXISTS extraction_json JSONB;
    ALTER TABLE interview_extractions ADD COLUMN IF NOT EXISTS interview_session_id UUID REFERENCES interview_sessions(id) ON DELETE SET NULL;
EXCEPTION
    WHEN duplicate_column THEN NULL;
END $$;

-- Add index for extraction_json queries
CREATE INDEX IF NOT EXISTS idx_interview_extractions_extraction_json ON interview_extractions USING GIN (extraction_json);

-- Add index for interview session lookups
CREATE INDEX IF NOT EXISTS idx_interview_extractions_session_id ON interview_extractions(interview_session_id);

-- ============================================================================
-- ENHANCE SOLOMON_REVIEWS TABLE FOR REVIEW DASHBOARD
-- Add deployed_at timestamp for tracking when instructions go live
-- ============================================================================
DO $$
BEGIN
    ALTER TABLE solomon_reviews ADD COLUMN IF NOT EXISTS deployed_at TIMESTAMPTZ;
EXCEPTION
    WHEN duplicate_column THEN NULL;
END $$;

-- Add index for deployed reviews
CREATE INDEX IF NOT EXISTS idx_solomon_reviews_deployed_at ON solomon_reviews(deployed_at);

-- ============================================================================
-- UPDATE COMMENTS
-- ============================================================================
COMMENT ON COLUMN interview_extractions.extraction_json IS 'Structured JSON data extracted from interview transcript by Solomon Stage 1';
COMMENT ON COLUMN interview_extractions.interview_session_id IS 'Reference to the original ElevenLabs interview session';
COMMENT ON COLUMN solomon_reviews.deployed_at IS 'Timestamp when system instructions were deployed to production (clients.system_instructions updated)';
COMMENT ON COLUMN solomon_reviews.status IS 'Review workflow status: pending (awaiting review), approved (ready to deploy), rejected (needs revision), needs_revision (edits required)';
