-- Migration: Entity Deduplication Enhancement
-- Date: 2026-01-28
-- Description: Add match tracking fields and embeddings to all candidate tables
--              to support unified deduplication across tasks, opportunities, and stakeholders.
--
--              Key features:
--              - task_candidates: Add matched_task_id, matched_candidate_id, match_confidence, match_reason, embedding
--              - opportunity_candidates: Add matched_candidate_id (already has matched_opportunity_id)
--              - stakeholder_candidates: Add matched_candidate_id, match_reason (already has potential_match_stakeholder_id)
--              - project_tasks: Add embedding for semantic matching

-- ============================================================================
-- TASK CANDIDATES - Add missing dedup fields
-- ============================================================================

-- Match tracking fields
ALTER TABLE task_candidates
  ADD COLUMN IF NOT EXISTS matched_task_id UUID REFERENCES project_tasks(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS matched_candidate_id UUID REFERENCES task_candidates(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS match_confidence FLOAT,
  ADD COLUMN IF NOT EXISTS match_reason TEXT;

-- Embedding fields for semantic matching
ALTER TABLE task_candidates
  ADD COLUMN IF NOT EXISTS embedding VECTOR(1024),
  ADD COLUMN IF NOT EXISTS embedding_status VARCHAR(20) DEFAULT 'pending';

-- ============================================================================
-- PROJECT TASKS - Add embedding for semantic matching
-- ============================================================================

ALTER TABLE project_tasks
  ADD COLUMN IF NOT EXISTS embedding VECTOR(1024);

-- ============================================================================
-- OPPORTUNITY CANDIDATES - Add within-batch dedup field
-- (already has matched_opportunity_id, match_confidence, match_reason)
-- ============================================================================

ALTER TABLE opportunity_candidates
  ADD COLUMN IF NOT EXISTS matched_candidate_id UUID REFERENCES opportunity_candidates(id) ON DELETE SET NULL;

-- ============================================================================
-- STAKEHOLDER CANDIDATES - Add match_reason and matched_candidate_id
-- (already has potential_match_stakeholder_id, match_confidence)
-- ============================================================================

ALTER TABLE stakeholder_candidates
  ADD COLUMN IF NOT EXISTS matched_candidate_id UUID REFERENCES stakeholder_candidates(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS match_reason TEXT;

-- ============================================================================
-- INDEXES for deduplication queries
-- ============================================================================

-- Task candidates: match tracking
CREATE INDEX IF NOT EXISTS idx_task_candidates_matched_task
  ON task_candidates(matched_task_id)
  WHERE matched_task_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_task_candidates_matched_candidate
  ON task_candidates(matched_candidate_id)
  WHERE matched_candidate_id IS NOT NULL;

-- Opportunity candidates: match tracking
CREATE INDEX IF NOT EXISTS idx_opportunity_candidates_matched_candidate
  ON opportunity_candidates(matched_candidate_id)
  WHERE matched_candidate_id IS NOT NULL;

-- Stakeholder candidates: match tracking
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_matched_candidate
  ON stakeholder_candidates(matched_candidate_id)
  WHERE matched_candidate_id IS NOT NULL;

-- ============================================================================
-- VECTOR INDEXES for semantic matching
-- Note: These indexes use ivfflat for approximate nearest neighbor search
-- ============================================================================

-- Task candidates embedding index
CREATE INDEX IF NOT EXISTS idx_task_candidates_embedding
  ON task_candidates USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
  WHERE embedding IS NOT NULL;

-- Project tasks embedding index
CREATE INDEX IF NOT EXISTS idx_project_tasks_embedding
  ON project_tasks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
  WHERE embedding IS NOT NULL;

-- ============================================================================
-- RPC FUNCTIONS for semantic matching
-- ============================================================================

-- Match task candidates against other pending candidates
CREATE OR REPLACE FUNCTION match_task_candidates(
    query_embedding VECTOR(1024),
    p_client_id UUID,
    match_threshold FLOAT DEFAULT 0.75,
    match_count INT DEFAULT 5,
    exclude_id UUID DEFAULT NULL
) RETURNS TABLE (id UUID, title TEXT, status TEXT, similarity FLOAT)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT tc.id, tc.title, tc.status,
           1 - (tc.embedding <=> query_embedding) AS similarity
    FROM task_candidates tc
    WHERE tc.client_id = p_client_id
      AND tc.embedding IS NOT NULL
      AND (exclude_id IS NULL OR tc.id != exclude_id)
      AND 1 - (tc.embedding <=> query_embedding) > match_threshold
    ORDER BY tc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Match against existing project_tasks
CREATE OR REPLACE FUNCTION match_existing_tasks(
    query_embedding VECTOR(1024),
    p_client_id UUID,
    match_threshold FLOAT DEFAULT 0.75,
    match_count INT DEFAULT 5
) RETURNS TABLE (id UUID, title TEXT, status TEXT, similarity FLOAT)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT pt.id, pt.title, pt.status,
           1 - (pt.embedding <=> query_embedding) AS similarity
    FROM project_tasks pt
    WHERE pt.client_id = p_client_id
      AND pt.embedding IS NOT NULL
      AND pt.status != 'completed'
      AND 1 - (pt.embedding <=> query_embedding) > match_threshold
    ORDER BY pt.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Match opportunity candidates against other pending candidates
CREATE OR REPLACE FUNCTION match_opportunity_candidates(
    query_embedding VECTOR(1024),
    p_client_id UUID,
    match_threshold FLOAT DEFAULT 0.75,
    match_count INT DEFAULT 5,
    exclude_id UUID DEFAULT NULL
) RETURNS TABLE (id UUID, title TEXT, status TEXT, similarity FLOAT)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT oc.id, oc.title, oc.status,
           1 - (oc.embedding <=> query_embedding) AS similarity
    FROM opportunity_candidates oc
    WHERE oc.client_id = p_client_id
      AND oc.embedding IS NOT NULL
      AND (exclude_id IS NULL OR oc.id != exclude_id)
      AND 1 - (oc.embedding <=> query_embedding) > match_threshold
    ORDER BY oc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN task_candidates.matched_task_id IS 'Existing project_task this candidate matches (for linking instead of creating)';
COMMENT ON COLUMN task_candidates.matched_candidate_id IS 'Other pending candidate this matches (within-batch dedup)';
COMMENT ON COLUMN task_candidates.match_confidence IS 'Confidence score (0-1) of the match';
COMMENT ON COLUMN task_candidates.match_reason IS 'Human-readable explanation of why match was detected';
COMMENT ON COLUMN task_candidates.embedding IS 'Vector embedding for semantic similarity search (1024 dims, voyage-3)';
COMMENT ON COLUMN task_candidates.embedding_status IS 'Status of embedding generation: pending, completed, failed';

COMMENT ON COLUMN project_tasks.embedding IS 'Vector embedding for semantic similarity search (1024 dims, voyage-3)';

COMMENT ON COLUMN opportunity_candidates.matched_candidate_id IS 'Other pending candidate this matches (within-batch dedup)';

COMMENT ON COLUMN stakeholder_candidates.matched_candidate_id IS 'Other pending candidate this matches (within-batch dedup)';
COMMENT ON COLUMN stakeholder_candidates.match_reason IS 'Human-readable explanation of why match was detected';

-- ============================================================================
-- DONE!
-- ============================================================================
