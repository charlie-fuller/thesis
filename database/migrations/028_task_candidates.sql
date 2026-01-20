-- Migration: Task Candidates Table
-- Date: 2026-01-20
-- Description: Stores potential tasks extracted from documents for user review.
--              Tasks are auto-extracted by Taskmaster when documents are uploaded,
--              then users can accept/reject them before they become real tasks.

-- ============================================================================
-- TASK CANDIDATES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- Source document info
    source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    source_document_name VARCHAR(500),
    source_text TEXT,  -- The original text that led to extraction

    -- Extracted task info
    title VARCHAR(500) NOT NULL,
    suggested_priority INTEGER DEFAULT 3 CHECK (suggested_priority BETWEEN 1 AND 5),
    suggested_due_date DATE,
    due_date_text VARCHAR(100),  -- Original text like "by Friday"
    assignee_name VARCHAR(255),

    -- Extraction metadata
    confidence VARCHAR(20) DEFAULT 'medium',  -- 'high' or 'medium'
    extraction_pattern VARCHAR(100),  -- Which pattern matched

    -- Review status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    accepted_at TIMESTAMPTZ,
    accepted_by UUID REFERENCES auth.users(id),
    created_task_id UUID REFERENCES project_tasks(id),
    rejected_at TIMESTAMPTZ,
    rejected_by UUID REFERENCES auth.users(id),
    rejection_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- For fetching pending candidates by user/client
CREATE INDEX IF NOT EXISTS idx_task_candidates_pending
ON task_candidates(client_id, status, created_at DESC)
WHERE status = 'pending';

-- For finding candidates from a specific document
CREATE INDEX IF NOT EXISTS idx_task_candidates_document
ON task_candidates(source_document_id);

-- For cleanup queries (old rejected/accepted)
CREATE INDEX IF NOT EXISTS idx_task_candidates_status_date
ON task_candidates(status, created_at);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE task_candidates ENABLE ROW LEVEL SECURITY;

-- Users can see candidates in their client
CREATE POLICY "Users can view task candidates in their client"
ON task_candidates
FOR SELECT
USING (
    client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    )
);

-- Users can update candidates (accept/reject)
CREATE POLICY "Users can update task candidates in their client"
ON task_candidates
FOR UPDATE
USING (
    client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    )
);

-- Service role can insert (from document processing)
CREATE POLICY "Service role can insert task candidates"
ON task_candidates
FOR INSERT
WITH CHECK (true);

-- ============================================================================
-- DONE!
-- ============================================================================
