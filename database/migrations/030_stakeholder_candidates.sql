-- Migration: Stakeholder Candidates Table
-- Date: 2026-01-21
-- Description: Stores potential stakeholders extracted from meeting documents for user review.
--              Stakeholders are extracted on manual scan (via "Scan for Stakeholders" button),
--              then users can accept/reject/merge them.

-- ============================================================================
-- STAKEHOLDER CANDIDATES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS stakeholder_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Extracted info
    name TEXT NOT NULL,
    role TEXT,
    department TEXT,
    organization TEXT,
    email TEXT,

    -- Context from extraction
    key_concerns JSONB DEFAULT '[]',      -- ["budget", "timeline"]
    interests JSONB DEFAULT '[]',          -- ["AI automation", "efficiency"]
    initial_sentiment TEXT,                -- positive/neutral/negative
    influence_level TEXT,                  -- high/medium/low

    -- Source tracking
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    source_document_name TEXT,
    source_text TEXT,                      -- Evidence quote
    extraction_context TEXT,               -- Meeting context

    -- Related entities found
    related_opportunity_ids UUID[] DEFAULT '{}',
    related_task_ids UUID[] DEFAULT '{}',

    -- Review status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'merged')),
    confidence TEXT DEFAULT 'medium' CHECK (confidence IN ('high', 'medium', 'low')),

    -- Deduplication
    potential_match_stakeholder_id UUID REFERENCES stakeholders(id) ON DELETE SET NULL,
    match_confidence FLOAT,

    -- Resolution
    accepted_at TIMESTAMPTZ,
    accepted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_stakeholder_id UUID REFERENCES stakeholders(id) ON DELETE SET NULL,
    merged_into_stakeholder_id UUID REFERENCES stakeholders(id) ON DELETE SET NULL,
    rejection_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- DOCUMENT SCAN TRACKING
-- ============================================================================

-- Add column to track when document was scanned for stakeholders
ALTER TABLE documents ADD COLUMN IF NOT EXISTS stakeholders_scanned_at TIMESTAMPTZ;

-- ============================================================================
-- INDEXES
-- ============================================================================

-- For fetching pending candidates by client
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_pending
ON stakeholder_candidates(client_id, status, created_at DESC)
WHERE status = 'pending';

-- For finding candidates from a specific document
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_document
ON stakeholder_candidates(source_document_id);

-- For cleanup queries (old rejected/accepted)
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_status_date
ON stakeholder_candidates(status, created_at);

-- For deduplication queries
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_match
ON stakeholder_candidates(potential_match_stakeholder_id)
WHERE potential_match_stakeholder_id IS NOT NULL;

-- For querying unscanned documents
CREATE INDEX IF NOT EXISTS idx_documents_stakeholders_scanned_at
ON documents(stakeholders_scanned_at)
WHERE stakeholders_scanned_at IS NULL;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE stakeholder_candidates ENABLE ROW LEVEL SECURITY;

-- Users can see candidates in their client
CREATE POLICY "Users can view stakeholder candidates in their client"
ON stakeholder_candidates
FOR SELECT
USING (
    client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    )
);

-- Users can update candidates (accept/reject/merge)
CREATE POLICY "Users can update stakeholder candidates in their client"
ON stakeholder_candidates
FOR UPDATE
USING (
    client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    )
);

-- Service role can insert (from document processing)
CREATE POLICY "Service role can insert stakeholder candidates"
ON stakeholder_candidates
FOR INSERT
WITH CHECK (true);

-- Service role can delete (cleanup)
CREATE POLICY "Service role can delete stakeholder candidates"
ON stakeholder_candidates
FOR DELETE
USING (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE stakeholder_candidates IS 'Potential stakeholders extracted from meeting documents, pending user review';
COMMENT ON COLUMN stakeholder_candidates.source_text IS 'Evidence quote from the document that mentions this stakeholder';
COMMENT ON COLUMN stakeholder_candidates.extraction_context IS 'Summary of the meeting/document context where stakeholder was mentioned';
COMMENT ON COLUMN stakeholder_candidates.potential_match_stakeholder_id IS 'Existing stakeholder this might be a duplicate of';
COMMENT ON COLUMN stakeholder_candidates.match_confidence IS 'Confidence score (0-1) that this is a match with potential_match_stakeholder_id';
COMMENT ON COLUMN documents.stakeholders_scanned_at IS 'When this document was last scanned for stakeholder extraction (NULL = never scanned)';

-- ============================================================================
-- DONE!
-- ============================================================================
