-- Migration: Add Custom Extraction Prompt Support
-- Date: 2025-11-05
-- Description: Adds extraction_prompt column to interview_sessions for custom agent instructions

-- Add extraction_prompt column to interview_sessions
ALTER TABLE interview_sessions
ADD COLUMN IF NOT EXISTS extraction_prompt TEXT;

COMMENT ON COLUMN interview_sessions.extraction_prompt IS 'Custom system instructions/prompt for transcript extraction. If NULL, uses default Solomon Stage 1 prompt. Must include {transcript} placeholder.';
