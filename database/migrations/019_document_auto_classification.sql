-- ============================================================================
-- DOCUMENT AUTO-CLASSIFICATION
-- Adds relevance scoring and classification tracking for agent-document routing
-- ============================================================================

-- Add relevance scoring to agent_knowledge_base
ALTER TABLE agent_knowledge_base
ADD COLUMN IF NOT EXISTS relevance_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS classification_source VARCHAR(50) DEFAULT 'manual',
ADD COLUMN IF NOT EXISTS classification_confidence FLOAT,
ADD COLUMN IF NOT EXISTS classification_reason TEXT,
ADD COLUMN IF NOT EXISTS user_confirmed BOOLEAN DEFAULT FALSE;

-- Add index for filtering by relevance (if not exists, may overlap with existing priority index)
CREATE INDEX IF NOT EXISTS idx_agent_kb_relevance
ON agent_knowledge_base(agent_id, relevance_score DESC);

-- Comments for documentation
COMMENT ON COLUMN agent_knowledge_base.relevance_score IS
    'LLM-assigned relevance score 0.0-1.0 for agent-document match';
COMMENT ON COLUMN agent_knowledge_base.classification_source IS
    'How classification was determined: manual, auto_keyword, auto_llm, auto_hybrid';
COMMENT ON COLUMN agent_knowledge_base.classification_confidence IS
    'Confidence score from classification algorithm';
COMMENT ON COLUMN agent_knowledge_base.classification_reason IS
    'Human-readable explanation of why this classification was made';
COMMENT ON COLUMN agent_knowledge_base.user_confirmed IS
    'Whether user explicitly confirmed/modified the classification';

-- ============================================================================
-- CLASSIFICATION HISTORY TABLE
-- Track classification results and pending reviews
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_classifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Classification results
    detected_type VARCHAR(100),
    classification_method VARCHAR(50) NOT NULL, -- 'keyword', 'llm', 'hybrid'
    model_used VARCHAR(100), -- e.g., 'claude-3-5-haiku-20241022'
    tokens_used INTEGER,
    processing_time_ms INTEGER,

    -- Raw results (all agent scores)
    raw_scores JSONB DEFAULT '{}',
    sample_chunks_used INTEGER DEFAULT 3,

    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'completed', 'needs_review', 'reviewed'
    requires_user_review BOOLEAN DEFAULT FALSE,
    review_reason TEXT,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES users(id),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_doc_class_document_id ON document_classifications(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_class_status ON document_classifications(status);
CREATE INDEX IF NOT EXISTS idx_doc_class_needs_review ON document_classifications(requires_user_review)
WHERE requires_user_review = TRUE;

-- RLS
ALTER TABLE document_classifications ENABLE ROW LEVEL SECURITY;

-- Users can view classifications for documents in their client
DROP POLICY IF EXISTS "Users can view document classifications" ON document_classifications;
CREATE POLICY "Users can view document classifications" ON document_classifications
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM documents d
            JOIN users u ON d.client_id = u.client_id
            WHERE d.id = document_id
            AND u.id = auth.uid()
        )
    );

-- Users can update classifications they need to review (confirm/modify)
DROP POLICY IF EXISTS "Users can update document classifications" ON document_classifications;
CREATE POLICY "Users can update document classifications" ON document_classifications
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM documents d
            JOIN users u ON d.client_id = u.client_id
            WHERE d.id = document_id
            AND u.id = auth.uid()
        )
    );

-- Service role can insert (via backend)
DROP POLICY IF EXISTS "Service can insert classifications" ON document_classifications;
CREATE POLICY "Service can insert classifications" ON document_classifications
    FOR INSERT WITH CHECK (true);

-- ============================================================================
-- AGENT-FILTERED CHUNK MATCHING RPC
-- New function with agent filtering and fallback behavior
-- ============================================================================

CREATE OR REPLACE FUNCTION match_document_chunks_with_agent_filter(
    query_embedding VECTOR(1024),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 5,
    p_client_id UUID DEFAULT NULL,
    p_user_id UUID DEFAULT NULL,
    p_agent_ids UUID[] DEFAULT NULL,
    p_fallback_threshold INT DEFAULT 3
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB,
    agent_relevance_score FLOAT,
    used_fallback BOOLEAN
)
LANGUAGE plpgsql
AS $$
DECLARE
    agent_filtered_count INT;
    use_fallback BOOLEAN := FALSE;
BEGIN
    -- First, count results with agent filter to decide on fallback
    IF p_agent_ids IS NOT NULL AND array_length(p_agent_ids, 1) > 0 THEN
        SELECT COUNT(*) INTO agent_filtered_count
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        LEFT JOIN agent_knowledge_base akb ON d.id = akb.document_id
        WHERE
            (p_client_id IS NULL OR d.client_id = p_client_id)
            AND (p_user_id IS NULL OR d.uploaded_by = p_user_id)
            AND d.processing_status = 'completed'
            AND 1 - (dc.embedding <=> query_embedding) > match_threshold
            AND (
                akb.agent_id = ANY(p_agent_ids)
                OR NOT EXISTS (
                    SELECT 1 FROM agent_knowledge_base akb2
                    WHERE akb2.document_id = d.id
                )
            );

        -- If enough results with agent filter, use filtered search
        IF agent_filtered_count >= p_fallback_threshold THEN
            RETURN QUERY
            SELECT
                dc.id,
                dc.document_id,
                dc.content,
                1 - (dc.embedding <=> query_embedding) as similarity,
                dc.metadata,
                COALESCE(MAX(akb.relevance_score), 0.5) as agent_relevance_score,
                FALSE as used_fallback
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            LEFT JOIN agent_knowledge_base akb ON d.id = akb.document_id AND akb.agent_id = ANY(p_agent_ids)
            WHERE
                (p_client_id IS NULL OR d.client_id = p_client_id)
                AND (p_user_id IS NULL OR d.uploaded_by = p_user_id)
                AND d.processing_status = 'completed'
                AND 1 - (dc.embedding <=> query_embedding) > match_threshold
                AND (
                    akb.agent_id = ANY(p_agent_ids)
                    OR NOT EXISTS (
                        SELECT 1 FROM agent_knowledge_base akb2
                        WHERE akb2.document_id = d.id
                    )
                )
            GROUP BY dc.id, dc.document_id, dc.content, dc.embedding, dc.metadata
            ORDER BY
                MAX(akb.relevance_score) DESC NULLS LAST,
                dc.embedding <=> query_embedding
            LIMIT match_count;
            RETURN;
        END IF;

        use_fallback := TRUE;
    END IF;

    -- Fallback: search all documents (no agent filter)
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity,
        dc.metadata,
        0.5::FLOAT as agent_relevance_score,
        use_fallback as used_fallback
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE
        (p_client_id IS NULL OR d.client_id = p_client_id)
        AND (p_user_id IS NULL OR d.uploaded_by = p_user_id)
        AND d.processing_status = 'completed'
        AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- UPDATE BASE SCHEMA COMMENT
-- ============================================================================
COMMENT ON FUNCTION match_document_chunks_with_agent_filter IS
    'Vector search with agent filtering and fallback. Prioritizes documents tagged for specified agents, falls back to all docs if insufficient results.';

-- ============================================================================
-- DONE!
-- ============================================================================
