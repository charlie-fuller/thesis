-- Migration: Task Candidate Rich Context
-- Date: 2026-01-20
-- Description: Adds rich context fields to task_candidates for better task descriptions
--              including meeting context, team, stakeholder, value proposition, etc.

-- ============================================================================
-- ADD RICH CONTEXT COLUMNS
-- ============================================================================

-- Context about the meeting/document where this task was found
ALTER TABLE task_candidates
ADD COLUMN IF NOT EXISTS meeting_context TEXT;  -- Summary of the meeting/document context

-- Team or department involved
ALTER TABLE task_candidates
ADD COLUMN IF NOT EXISTS team VARCHAR(255);

-- Stakeholder or individual who owns/requested this
ALTER TABLE task_candidates
ADD COLUMN IF NOT EXISTS stakeholder_name VARCHAR(255);

-- Value proposition or business impact
ALTER TABLE task_candidates
ADD COLUMN IF NOT EXISTS value_proposition TEXT;

-- Document date (when the source meeting/document occurred)
ALTER TABLE task_candidates
ADD COLUMN IF NOT EXISTS document_date DATE;

-- Full description with rich context (LLM-generated)
ALTER TABLE task_candidates
ADD COLUMN IF NOT EXISTS description TEXT;

-- Related topics or tags
ALTER TABLE task_candidates
ADD COLUMN IF NOT EXISTS topics TEXT[];  -- Array of related topics

-- ============================================================================
-- DONE!
-- ============================================================================
