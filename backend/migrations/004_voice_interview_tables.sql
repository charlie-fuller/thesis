-- Migration: Voice Interview System Tables
-- Date: 2025-11-04
-- Description: Adds tables for ElevenLabs voice interview pipeline and Solomon processing

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
-- UPDATE INTERVIEW_EXTRACTIONS TABLE
-- Add tracking fields for Solomon Stage 1 processing
-- ============================================================================
ALTER TABLE interview_extractions
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS error_message TEXT,
ADD COLUMN IF NOT EXISTS review_reason TEXT,
ADD COLUMN IF NOT EXISTS completeness_score INTEGER;

-- Add index for status queries
CREATE INDEX IF NOT EXISTS idx_interview_extractions_status ON interview_extractions(status);

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
ALTER TABLE clients
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';
-- Status values: pending_interview, interview_scheduled, interview_complete,
--                extraction_complete, configuration_pending, active

-- ============================================================================
-- SOLOMON REVIEWS TABLE
-- Stores Stage 2 configuration generation for human review
-- ============================================================================
-- This table should already exist from previous migrations, but add columns if needed
ALTER TABLE solomon_reviews
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES users(id),
ADD COLUMN IF NOT EXISTS deployment_notes TEXT;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE interview_sessions IS 'Voice interview sessions created via ElevenLabs Conversational AI';
COMMENT ON COLUMN interview_sessions.agent_id IS 'ElevenLabs agent ID for this interview';
COMMENT ON COLUMN interview_sessions.session_id IS 'Unique session ID from ElevenLabs';
COMMENT ON COLUMN interview_sessions.session_url IS 'Interview URL shared with client';
COMMENT ON COLUMN interview_sessions.status IS 'Current status: scheduled, in_progress, completed, failed';

COMMENT ON TABLE api_usage_logs IS 'Tracks Claude API usage for cost monitoring and optimization';
COMMENT ON COLUMN api_usage_logs.operation IS 'Type of operation: extraction, generation, chat, etc.';
COMMENT ON COLUMN api_usage_logs.cost_usd IS 'Calculated cost in USD based on token usage and model pricing';

COMMENT ON COLUMN interview_extractions.completeness_score IS 'Percentage (0-100) of required data extracted from interview';
COMMENT ON COLUMN interview_extractions.review_reason IS 'Reason flagged for human review (e.g., low completeness)';
