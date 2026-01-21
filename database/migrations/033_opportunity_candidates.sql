-- Migration: Opportunity Candidates Table
-- Date: 2026-01-21
-- Description: Stores potential AI opportunities extracted from meeting documents for user review.
--              Opportunities are extracted by Granola scanner when documents are processed,
--              then users can accept/reject them before they become real opportunities.
--              Includes deduplication support to detect matches with existing opportunities.

-- ============================================================================
-- OPPORTUNITY CANDIDATES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS opportunity_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Extracted info
    title VARCHAR(255) NOT NULL,
    description TEXT,
    department VARCHAR(100),

    -- Source tracking
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    source_document_name TEXT,
    source_text TEXT,  -- Evidence quote from document

    -- Suggested scores (1-5 scale each)
    suggested_roi_potential INTEGER CHECK (suggested_roi_potential IS NULL OR suggested_roi_potential BETWEEN 1 AND 5),
    suggested_effort INTEGER CHECK (suggested_effort IS NULL OR suggested_effort BETWEEN 1 AND 5),
    suggested_alignment INTEGER CHECK (suggested_alignment IS NULL OR suggested_alignment BETWEEN 1 AND 5),
    suggested_readiness INTEGER CHECK (suggested_readiness IS NULL OR suggested_readiness BETWEEN 1 AND 5),

    -- Context
    potential_impact TEXT,
    related_stakeholder_names TEXT[],

    -- Review status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    confidence TEXT DEFAULT 'medium' CHECK (confidence IN ('high', 'medium', 'low')),

    -- Deduplication
    matched_opportunity_id UUID REFERENCES ai_opportunities(id) ON DELETE SET NULL,
    match_confidence FLOAT,
    match_reason TEXT,

    -- Resolution
    accepted_at TIMESTAMPTZ,
    accepted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_opportunity_id UUID REFERENCES ai_opportunities(id) ON DELETE SET NULL,
    rejected_at TIMESTAMPTZ,
    rejected_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    rejection_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- DOCUMENT SCAN TRACKING
-- ============================================================================

-- Add column to track when document was scanned for opportunities
ALTER TABLE documents ADD COLUMN IF NOT EXISTS opportunities_scanned_at TIMESTAMPTZ;

-- ============================================================================
-- INDEXES
-- ============================================================================

-- For fetching pending candidates by client
CREATE INDEX IF NOT EXISTS idx_opportunity_candidates_pending
ON opportunity_candidates(client_id, status, created_at DESC)
WHERE status = 'pending';

-- For finding candidates from a specific document
CREATE INDEX IF NOT EXISTS idx_opportunity_candidates_document
ON opportunity_candidates(source_document_id);

-- For cleanup queries (old rejected/accepted)
CREATE INDEX IF NOT EXISTS idx_opportunity_candidates_status_date
ON opportunity_candidates(status, created_at);

-- For deduplication queries
CREATE INDEX IF NOT EXISTS idx_opportunity_candidates_match
ON opportunity_candidates(matched_opportunity_id)
WHERE matched_opportunity_id IS NOT NULL;

-- For querying unscanned documents
CREATE INDEX IF NOT EXISTS idx_documents_opportunities_scanned_at
ON documents(opportunities_scanned_at)
WHERE opportunities_scanned_at IS NULL;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE opportunity_candidates ENABLE ROW LEVEL SECURITY;

-- Users can see candidates in their client
CREATE POLICY "Users can view opportunity candidates in their client"
ON opportunity_candidates
FOR SELECT
USING (
    client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    )
);

-- Users can update candidates (accept/reject)
CREATE POLICY "Users can update opportunity candidates in their client"
ON opportunity_candidates
FOR UPDATE
USING (
    client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    )
);

-- Service role can insert (from document processing)
CREATE POLICY "Service role can insert opportunity candidates"
ON opportunity_candidates
FOR INSERT
WITH CHECK (true);

-- Service role can delete (cleanup)
CREATE POLICY "Service role can delete opportunity candidates"
ON opportunity_candidates
FOR DELETE
USING (true);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_opportunity_candidate_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_opportunity_candidate_timestamp ON opportunity_candidates;
CREATE TRIGGER trigger_update_opportunity_candidate_timestamp
BEFORE UPDATE ON opportunity_candidates
FOR EACH ROW
EXECUTE FUNCTION update_opportunity_candidate_timestamp();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE opportunity_candidates IS 'Potential AI opportunities extracted from meeting documents, pending user review';
COMMENT ON COLUMN opportunity_candidates.source_text IS 'Evidence quote from the document that mentions this opportunity';
COMMENT ON COLUMN opportunity_candidates.matched_opportunity_id IS 'Existing opportunity this might be a duplicate of';
COMMENT ON COLUMN opportunity_candidates.match_confidence IS 'Confidence score (0-1) that this is a match with matched_opportunity_id';
COMMENT ON COLUMN opportunity_candidates.match_reason IS 'Explanation of why this was flagged as a potential match';
COMMENT ON COLUMN documents.opportunities_scanned_at IS 'When this document was last scanned for opportunity extraction (NULL = never scanned)';

-- ============================================================================
-- DONE!
-- ============================================================================
