-- Migration: Voice Interview System Tables
-- Date: 2025-11-04
-- Description: Adds tables for ElevenLabs voice interview pipeline and Solomon processing
-- FIXED VERSION: Creates interview_extractions table before altering it

-- ============================================================================
-- INTERVIEW SESSIONS TABLE
-- Tracks voice interview sessions created via ElevenLabs
-- ============================================================================
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL UNIQUE,
    session_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',
    -- Status values: scheduled, in_progress, completed, failed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata JSONB
);

-- Indexes for interview_sessions
CREATE INDEX IF NOT EXISTS idx_interview_sessions_client_id ON interview_sessions(client_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_session_id ON interview_sessions(session_id);

-- ============================================================================
-- INTERVIEW EXTRACTIONS TABLE
-- Create the base table first, then add enhancement columns
-- ============================================================================
CREATE TABLE IF NOT EXISTS interview_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    transcript TEXT NOT NULL,
    audio_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending_solomon',
    -- Status values: pending_solomon, extracting, extracted, generating, complete, failed, needs_review
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Now add enhancement columns (safe to run if columns already exist)
DO $$
BEGIN
    ALTER TABLE interview_extractions ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;
    ALTER TABLE interview_extractions ADD COLUMN IF NOT EXISTS error_message TEXT;
    ALTER TABLE interview_extractions ADD COLUMN IF NOT EXISTS review_reason TEXT;
    ALTER TABLE interview_extractions ADD COLUMN IF NOT EXISTS completeness_score INTEGER;
EXCEPTION
    WHEN duplicate_column THEN NULL;
END $$;

-- Add index for status queries
CREATE INDEX IF NOT EXISTS idx_interview_extractions_status ON interview_extractions(status);
CREATE INDEX IF NOT EXISTS idx_interview_extractions_client_id ON interview_extractions(client_id);

-- ============================================================================
-- API USAGE LOGS TABLE
-- Tracks Claude API usage for cost monitoring
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id),
    operation TEXT NOT NULL,
    -- Operation types: solomon_stage1_extraction, solomon_stage2_generation, chat_message, etc.
    model TEXT NOT NULL,
    -- Model used: claude-3-5-sonnet-20241022, claude-3-opus-20240229, etc.
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Indexes for api_usage_logs
CREATE INDEX IF NOT EXISTS idx_api_usage_client ON api_usage_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_operation ON api_usage_logs(operation);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage_logs(created_at DESC);

-- ============================================================================
-- UPDATE CLIENTS TABLE
-- Add status field to track onboarding stage
-- ============================================================================
DO $$
BEGIN
    ALTER TABLE clients ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';
EXCEPTION
    WHEN duplicate_column THEN NULL;
END $$;
-- Status values: pending_interview, interview_scheduled, interview_complete,
--                extraction_complete, configuration_pending, active

-- ============================================================================
-- SOLOMON REVIEWS TABLE
-- Create if doesn't exist, then add review tracking columns
-- ============================================================================
CREATE TABLE IF NOT EXISTS solomon_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extraction_id UUID REFERENCES interview_extractions(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    -- Status values: pending, approved, rejected, needs_revision
    generated_instructions TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Add enhancement columns
DO $$
BEGIN
    ALTER TABLE solomon_reviews ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;
    ALTER TABLE solomon_reviews ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES users(id);
    ALTER TABLE solomon_reviews ADD COLUMN IF NOT EXISTS deployment_notes TEXT;
EXCEPTION
    WHEN duplicate_column THEN NULL;
END $$;

-- Index for solomon_reviews
CREATE INDEX IF NOT EXISTS idx_solomon_reviews_extraction_id ON solomon_reviews(extraction_id);
CREATE INDEX IF NOT EXISTS idx_solomon_reviews_client_id ON solomon_reviews(client_id);
CREATE INDEX IF NOT EXISTS idx_solomon_reviews_status ON solomon_reviews(status);

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE interview_sessions IS 'Voice interview sessions created via ElevenLabs Conversational AI';
COMMENT ON COLUMN interview_sessions.agent_id IS 'ElevenLabs agent ID for this interview';
COMMENT ON COLUMN interview_sessions.session_id IS 'Unique session ID from ElevenLabs';
COMMENT ON COLUMN interview_sessions.session_url IS 'Interview URL shared with client';
COMMENT ON COLUMN interview_sessions.status IS 'Current status: scheduled, in_progress, completed, failed';

COMMENT ON TABLE interview_extractions IS 'Structured data extracted from voice interviews via Solomon Stage 1';
COMMENT ON COLUMN interview_extractions.status IS 'Processing status through Solomon pipeline';
COMMENT ON COLUMN interview_extractions.completeness_score IS 'Percentage (0-100) of required data extracted from interview';
COMMENT ON COLUMN interview_extractions.review_reason IS 'Reason flagged for human review (e.g., low completeness)';

COMMENT ON TABLE api_usage_logs IS 'Tracks Claude API usage for cost monitoring and optimization';
COMMENT ON COLUMN api_usage_logs.operation IS 'Type of operation: extraction, generation, chat, etc.';
COMMENT ON COLUMN api_usage_logs.cost_usd IS 'Calculated cost in USD based on token usage and model pricing';

COMMENT ON TABLE solomon_reviews IS 'Human review queue for AI-generated system instructions';
