-- Migration: 049_disco_rename.sql
-- Description: Rename all purdy_* tables, indexes, functions, policies to disco_*
-- Date: 2026-01-25
-- IMPORTANT: This is a breaking change requiring coordinated deployment

-- ============================================================================
-- PHASE 1: DROP DEPENDENT OBJECTS (Views, Triggers, Policies, Functions)
-- ============================================================================

-- Drop view (depends on tables)
DROP VIEW IF EXISTS purdy_outcome_metrics;

-- Drop triggers (depends on tables and functions)
DROP TRIGGER IF EXISTS purdy_initiatives_updated_at_trigger ON purdy_initiatives;

-- ============================================================================
-- PHASE 2: DROP ALL RLS POLICIES
-- (Must be done before table renames since policies are bound to table names)
-- ============================================================================

-- purdy_initiatives policies
DROP POLICY IF EXISTS purdy_initiatives_select ON purdy_initiatives;
DROP POLICY IF EXISTS purdy_initiatives_insert ON purdy_initiatives;
DROP POLICY IF EXISTS purdy_initiatives_update ON purdy_initiatives;
DROP POLICY IF EXISTS purdy_initiatives_delete ON purdy_initiatives;

-- purdy_initiative_members policies
DROP POLICY IF EXISTS purdy_members_select ON purdy_initiative_members;

-- purdy_documents policies
DROP POLICY IF EXISTS purdy_documents_select ON purdy_documents;
DROP POLICY IF EXISTS purdy_documents_insert ON purdy_documents;

-- purdy_document_chunks policies
DROP POLICY IF EXISTS purdy_chunks_select ON purdy_document_chunks;

-- purdy_runs policies
DROP POLICY IF EXISTS purdy_runs_select ON purdy_runs;
DROP POLICY IF EXISTS purdy_runs_insert ON purdy_runs;
DROP POLICY IF EXISTS purdy_runs_update ON purdy_runs;

-- purdy_run_documents policies
DROP POLICY IF EXISTS purdy_run_documents_select ON purdy_run_documents;
DROP POLICY IF EXISTS purdy_run_documents_insert ON purdy_run_documents;

-- purdy_outputs policies
DROP POLICY IF EXISTS purdy_outputs_select ON purdy_outputs;
DROP POLICY IF EXISTS purdy_outputs_insert ON purdy_outputs;
DROP POLICY IF EXISTS purdy_outputs_update ON purdy_outputs;
DROP POLICY IF EXISTS purdy_outputs_delete ON purdy_outputs;

-- purdy_conversations policies
DROP POLICY IF EXISTS purdy_conversations_select ON purdy_conversations;
DROP POLICY IF EXISTS purdy_conversations_insert ON purdy_conversations;

-- purdy_messages policies
DROP POLICY IF EXISTS purdy_messages_select ON purdy_messages;
DROP POLICY IF EXISTS purdy_messages_insert ON purdy_messages;

-- purdy_system_kb policies
DROP POLICY IF EXISTS purdy_system_kb_select ON purdy_system_kb;
DROP POLICY IF EXISTS purdy_system_kb_chunks_select ON purdy_system_kb_chunks;

-- ============================================================================
-- PHASE 3: DROP FUNCTIONS (Must be done before recreating with new table refs)
-- ============================================================================

DROP FUNCTION IF EXISTS update_purdy_initiatives_updated_at();
DROP FUNCTION IF EXISTS match_purdy_document_chunks(VECTOR(1024), INT, FLOAT, UUID);
DROP FUNCTION IF EXISTS match_purdy_system_kb_chunks(VECTOR(1024), INT, FLOAT);
DROP FUNCTION IF EXISTS match_purdy_all_chunks(VECTOR(1024), INT, FLOAT, UUID);

-- ============================================================================
-- PHASE 4: RENAME TABLES
-- ============================================================================

ALTER TABLE IF EXISTS purdy_initiatives RENAME TO disco_initiatives;
ALTER TABLE IF EXISTS purdy_initiative_members RENAME TO disco_initiative_members;
ALTER TABLE IF EXISTS purdy_documents RENAME TO disco_documents;
ALTER TABLE IF EXISTS purdy_document_chunks RENAME TO disco_document_chunks;
ALTER TABLE IF EXISTS purdy_runs RENAME TO disco_runs;
ALTER TABLE IF EXISTS purdy_run_documents RENAME TO disco_run_documents;
ALTER TABLE IF EXISTS purdy_outputs RENAME TO disco_outputs;
ALTER TABLE IF EXISTS purdy_conversations RENAME TO disco_conversations;
ALTER TABLE IF EXISTS purdy_messages RENAME TO disco_messages;
ALTER TABLE IF EXISTS purdy_system_kb RENAME TO disco_system_kb;
ALTER TABLE IF EXISTS purdy_system_kb_chunks RENAME TO disco_system_kb_chunks;

-- ============================================================================
-- PHASE 5: RENAME INDEXES
-- ============================================================================

ALTER INDEX IF EXISTS idx_purdy_chunks_initiative RENAME TO idx_disco_chunks_initiative;
ALTER INDEX IF EXISTS idx_purdy_chunks_embedding RENAME TO idx_disco_chunks_embedding;
ALTER INDEX IF EXISTS idx_purdy_system_kb_embedding RENAME TO idx_disco_system_kb_embedding;
ALTER INDEX IF EXISTS idx_purdy_docs_initiative RENAME TO idx_disco_docs_initiative;
ALTER INDEX IF EXISTS idx_purdy_outputs_initiative RENAME TO idx_disco_outputs_initiative;
ALTER INDEX IF EXISTS idx_purdy_runs_initiative RENAME TO idx_disco_runs_initiative;
ALTER INDEX IF EXISTS idx_purdy_members_initiative RENAME TO idx_disco_members_initiative;
ALTER INDEX IF EXISTS idx_purdy_members_user RENAME TO idx_disco_members_user;
ALTER INDEX IF EXISTS idx_purdy_initiatives_decided_at RENAME TO idx_disco_initiatives_decided_at;
ALTER INDEX IF EXISTS idx_purdy_initiatives_status_dates RENAME TO idx_disco_initiatives_status_dates;
ALTER INDEX IF EXISTS idx_purdy_outputs_stakeholder_rating RENAME TO idx_disco_outputs_stakeholder_rating;

-- ============================================================================
-- PHASE 6: UPDATE FOREIGN KEY REFERENCES IN disco_bundles AND disco_prds
-- ============================================================================

-- disco_bundles: Update FK to disco_initiatives
ALTER TABLE disco_bundles DROP CONSTRAINT IF EXISTS disco_bundles_initiative_id_fkey;
ALTER TABLE disco_bundles ADD CONSTRAINT disco_bundles_initiative_id_fkey
    FOREIGN KEY (initiative_id) REFERENCES disco_initiatives(id) ON DELETE CASCADE;

-- disco_bundles: Update FK to disco_outputs
ALTER TABLE disco_bundles DROP CONSTRAINT IF EXISTS disco_bundles_source_output_id_fkey;
ALTER TABLE disco_bundles ADD CONSTRAINT disco_bundles_source_output_id_fkey
    FOREIGN KEY (source_output_id) REFERENCES disco_outputs(id) ON DELETE SET NULL;

-- disco_prds: Update FK to disco_initiatives
ALTER TABLE disco_prds DROP CONSTRAINT IF EXISTS disco_prds_initiative_id_fkey;
ALTER TABLE disco_prds ADD CONSTRAINT disco_prds_initiative_id_fkey
    FOREIGN KEY (initiative_id) REFERENCES disco_initiatives(id) ON DELETE CASCADE;

-- disco_prds: Update FK to disco_outputs
ALTER TABLE disco_prds DROP CONSTRAINT IF EXISTS disco_prds_source_output_id_fkey;
ALTER TABLE disco_prds ADD CONSTRAINT disco_prds_source_output_id_fkey
    FOREIGN KEY (source_output_id) REFERENCES disco_outputs(id) ON DELETE SET NULL;

-- ============================================================================
-- PHASE 7: RECREATE FUNCTIONS WITH NEW TABLE REFERENCES
-- ============================================================================

-- Trigger function for updated_at
CREATE OR REPLACE FUNCTION update_disco_initiatives_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Vector search: document chunks within initiative
CREATE OR REPLACE FUNCTION match_disco_document_chunks(
    query_embedding VECTOR(1024),
    match_count INT,
    match_threshold FLOAT,
    p_initiative_id UUID
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    initiative_id UUID,
    chunk_index INT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ddc.id,
        ddc.document_id,
        ddc.initiative_id,
        ddc.chunk_index,
        ddc.content,
        ddc.metadata,
        (1 - (ddc.embedding <=> query_embedding))::FLOAT AS similarity
    FROM disco_document_chunks ddc
    WHERE ddc.initiative_id = p_initiative_id
        AND (1 - (ddc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY ddc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_disco_document_chunks IS 'Vector similarity search for DISCo document chunks scoped to initiative';

-- Vector search: system KB chunks
CREATE OR REPLACE FUNCTION match_disco_system_kb_chunks(
    query_embedding VECTOR(1024),
    match_count INT,
    match_threshold FLOAT
)
RETURNS TABLE (
    id UUID,
    kb_id UUID,
    chunk_index INT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    filename TEXT,
    category TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dskc.id,
        dskc.kb_id,
        dskc.chunk_index,
        dskc.content,
        dskc.metadata,
        (1 - (dskc.embedding <=> query_embedding))::FLOAT AS similarity,
        dsk.filename,
        dsk.category
    FROM disco_system_kb_chunks dskc
    JOIN disco_system_kb dsk ON dskc.kb_id = dsk.id
    WHERE (1 - (dskc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY dskc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_disco_system_kb_chunks IS 'Vector similarity search for DISCo global system KB chunks';

-- Combined search: initiative docs + system KB
CREATE OR REPLACE FUNCTION match_disco_all_chunks(
    query_embedding VECTOR(1024),
    match_count INT,
    match_threshold FLOAT,
    p_initiative_id UUID
)
RETURNS TABLE (
    id UUID,
    source_type TEXT,
    source_id UUID,
    chunk_index INT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    filename TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    -- Initiative documents
    SELECT
        ddc.id,
        'document'::TEXT AS source_type,
        ddc.document_id AS source_id,
        ddc.chunk_index,
        ddc.content,
        ddc.metadata,
        (1 - (ddc.embedding <=> query_embedding))::FLOAT AS similarity,
        dd.filename
    FROM disco_document_chunks ddc
    JOIN disco_documents dd ON ddc.document_id = dd.id
    WHERE ddc.initiative_id = p_initiative_id
        AND (1 - (ddc.embedding <=> query_embedding)) >= match_threshold

    UNION ALL

    -- System KB
    SELECT
        dskc.id,
        'system_kb'::TEXT AS source_type,
        dskc.kb_id AS source_id,
        dskc.chunk_index,
        dskc.content,
        dskc.metadata,
        (1 - (dskc.embedding <=> query_embedding))::FLOAT AS similarity,
        dsk.filename
    FROM disco_system_kb_chunks dskc
    JOIN disco_system_kb dsk ON dskc.kb_id = dsk.id
    WHERE (1 - (dskc.embedding <=> query_embedding)) >= match_threshold

    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_disco_all_chunks IS 'Combined vector search across initiative docs and system KB';

-- ============================================================================
-- PHASE 8: RECREATE TRIGGER
-- ============================================================================

CREATE TRIGGER disco_initiatives_updated_at_trigger
    BEFORE UPDATE ON disco_initiatives
    FOR EACH ROW
    EXECUTE FUNCTION update_disco_initiatives_updated_at();

-- ============================================================================
-- PHASE 9: RECREATE VIEW WITH NEW TABLE REFERENCES
-- ============================================================================

CREATE OR REPLACE VIEW disco_outcome_metrics AS
SELECT
  i.id,
  i.name,
  i.status,
  i.created_at,
  i.decided_at,
  i.launched_at,
  i.completed_at,
  i.abandoned_at,
  i.decision_velocity_days,
  CASE
    WHEN i.decided_at IS NOT NULL AND i.decision_velocity_days <= 7 THEN 'fast'
    WHEN i.decided_at IS NOT NULL AND i.decision_velocity_days <= 14 THEN 'moderate'
    WHEN i.decided_at IS NOT NULL THEN 'slow'
    ELSE 'pending'
  END as velocity_category,
  (SELECT AVG(stakeholder_rating) FROM disco_outputs WHERE initiative_id = i.id AND stakeholder_rating IS NOT NULL) as avg_stakeholder_rating,
  (SELECT COUNT(*) FROM disco_outputs WHERE initiative_id = i.id AND stakeholder_rating IS NOT NULL) as ratings_count,
  (SELECT COUNT(*) FROM disco_outputs WHERE initiative_id = i.id) as total_outputs
FROM disco_initiatives i;

-- ============================================================================
-- PHASE 10: RECREATE RLS POLICIES
-- ============================================================================

-- Enable RLS (should already be enabled, but ensure)
ALTER TABLE disco_initiatives ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_initiative_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_run_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_system_kb ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_system_kb_chunks ENABLE ROW LEVEL SECURITY;

-- disco_initiatives policies
CREATE POLICY disco_initiatives_select ON disco_initiatives FOR SELECT
    USING (
        created_by = auth.uid()
        OR EXISTS (
            SELECT 1 FROM disco_initiative_members
            WHERE initiative_id = disco_initiatives.id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY disco_initiatives_insert ON disco_initiatives FOR INSERT
    WITH CHECK (created_by = auth.uid());

CREATE POLICY disco_initiatives_update ON disco_initiatives FOR UPDATE
    USING (
        created_by = auth.uid()
        OR EXISTS (
            SELECT 1 FROM disco_initiative_members
            WHERE initiative_id = disco_initiatives.id
            AND user_id = auth.uid()
            AND role IN ('owner', 'editor')
        )
    );

CREATE POLICY disco_initiatives_delete ON disco_initiatives FOR DELETE
    USING (created_by = auth.uid());

-- disco_initiative_members policies
CREATE POLICY disco_members_select ON disco_initiative_members FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_initiative_members.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members m
                    WHERE m.initiative_id = disco_initiatives.id
                    AND m.user_id = auth.uid()
                )
            )
        )
    );

-- disco_documents policies
CREATE POLICY disco_documents_select ON disco_documents FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_documents.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = disco_initiatives.id
                    AND user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY disco_documents_insert ON disco_documents FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_documents.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = disco_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- disco_document_chunks policies
CREATE POLICY disco_chunks_select ON disco_document_chunks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM disco_documents dd
            JOIN disco_initiatives di ON dd.initiative_id = di.id
            WHERE dd.id = disco_document_chunks.document_id
            AND (
                di.created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = di.id
                    AND user_id = auth.uid()
                )
            )
        )
    );

-- disco_runs policies
CREATE POLICY disco_runs_select ON disco_runs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_runs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = disco_initiatives.id
                    AND user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY disco_runs_insert ON disco_runs FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_runs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = disco_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

CREATE POLICY disco_runs_update ON disco_runs FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_runs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = disco_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- disco_run_documents policies
CREATE POLICY disco_run_documents_select ON disco_run_documents FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM disco_runs r
            JOIN disco_initiatives i ON i.id = r.initiative_id
            WHERE r.id = disco_run_documents.run_id
            AND (
                i.created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = i.id
                    AND user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY disco_run_documents_insert ON disco_run_documents FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM disco_runs r
            JOIN disco_initiatives i ON i.id = r.initiative_id
            WHERE r.id = disco_run_documents.run_id
            AND (
                i.created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = i.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- disco_outputs policies
CREATE POLICY disco_outputs_select ON disco_outputs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_outputs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = disco_initiatives.id
                    AND user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY disco_outputs_insert ON disco_outputs FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_outputs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = disco_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

CREATE POLICY disco_outputs_update ON disco_outputs FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_outputs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = disco_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

CREATE POLICY disco_outputs_delete ON disco_outputs FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM disco_initiatives
            WHERE id = disco_outputs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM disco_initiative_members
                    WHERE initiative_id = disco_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- disco_conversations policies
CREATE POLICY disco_conversations_select ON disco_conversations FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY disco_conversations_insert ON disco_conversations FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- disco_messages policies
CREATE POLICY disco_messages_select ON disco_messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM disco_conversations
            WHERE id = disco_messages.conversation_id
            AND user_id = auth.uid()
        )
    );

CREATE POLICY disco_messages_insert ON disco_messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM disco_conversations
            WHERE id = disco_messages.conversation_id
            AND user_id = auth.uid()
        )
    );

-- disco_system_kb policies (read-only for authenticated)
CREATE POLICY disco_system_kb_select ON disco_system_kb FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY disco_system_kb_chunks_select ON disco_system_kb_chunks FOR SELECT
    TO authenticated
    USING (true);

-- ============================================================================
-- PHASE 11: UPDATE RLS POLICIES FOR disco_bundles AND disco_prds
-- (These reference the renamed tables)
-- ============================================================================

-- Drop old policies that reference purdy_* tables
DROP POLICY IF EXISTS "disco_bundles_select_policy" ON disco_bundles;
DROP POLICY IF EXISTS "disco_bundles_insert_policy" ON disco_bundles;
DROP POLICY IF EXISTS "disco_bundles_update_policy" ON disco_bundles;
DROP POLICY IF EXISTS "disco_bundles_delete_policy" ON disco_bundles;
DROP POLICY IF EXISTS "disco_bundle_feedback_select_policy" ON disco_bundle_feedback;
DROP POLICY IF EXISTS "disco_bundle_feedback_insert_policy" ON disco_bundle_feedback;
DROP POLICY IF EXISTS "disco_prds_select_policy" ON disco_prds;
DROP POLICY IF EXISTS "disco_prds_insert_policy" ON disco_prds;
DROP POLICY IF EXISTS "disco_prds_update_policy" ON disco_prds;

-- Recreate disco_bundles policies with disco_* references
CREATE POLICY "disco_bundles_select_policy" ON disco_bundles
    FOR SELECT USING (
        initiative_id IN (
            SELECT initiative_id FROM disco_initiative_members WHERE user_id = auth.uid()
        )
        OR initiative_id IN (
            SELECT id FROM disco_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_bundles_insert_policy" ON disco_bundles
    FOR INSERT WITH CHECK (
        initiative_id IN (
            SELECT initiative_id FROM disco_initiative_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'editor')
        )
        OR initiative_id IN (
            SELECT id FROM disco_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_bundles_update_policy" ON disco_bundles
    FOR UPDATE USING (
        initiative_id IN (
            SELECT initiative_id FROM disco_initiative_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'editor')
        )
        OR initiative_id IN (
            SELECT id FROM disco_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_bundles_delete_policy" ON disco_bundles
    FOR DELETE USING (
        initiative_id IN (
            SELECT initiative_id FROM disco_initiative_members
            WHERE user_id = auth.uid() AND role = 'owner'
        )
        OR initiative_id IN (
            SELECT id FROM disco_initiatives WHERE created_by = auth.uid()
        )
    );

-- Recreate disco_bundle_feedback policies
CREATE POLICY "disco_bundle_feedback_select_policy" ON disco_bundle_feedback
    FOR SELECT USING (
        bundle_id IN (
            SELECT b.id FROM disco_bundles b
            JOIN disco_initiative_members m ON b.initiative_id = m.initiative_id
            WHERE m.user_id = auth.uid()
        )
        OR bundle_id IN (
            SELECT b.id FROM disco_bundles b
            JOIN disco_initiatives i ON b.initiative_id = i.id
            WHERE i.created_by = auth.uid()
        )
    );

CREATE POLICY "disco_bundle_feedback_insert_policy" ON disco_bundle_feedback
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- Recreate disco_prds policies
CREATE POLICY "disco_prds_select_policy" ON disco_prds
    FOR SELECT USING (
        initiative_id IN (
            SELECT initiative_id FROM disco_initiative_members WHERE user_id = auth.uid()
        )
        OR initiative_id IN (
            SELECT id FROM disco_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_prds_insert_policy" ON disco_prds
    FOR INSERT WITH CHECK (
        initiative_id IN (
            SELECT initiative_id FROM disco_initiative_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'editor')
        )
        OR initiative_id IN (
            SELECT id FROM disco_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_prds_update_policy" ON disco_prds
    FOR UPDATE USING (
        initiative_id IN (
            SELECT initiative_id FROM disco_initiative_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'editor')
        )
        OR initiative_id IN (
            SELECT id FROM disco_initiatives WHERE created_by = auth.uid()
        )
    );

-- ============================================================================
-- PHASE 12: UPDATE TABLE AND COLUMN COMMENTS
-- ============================================================================

COMMENT ON TABLE disco_initiatives IS 'DISCo initiative containers for discovery efforts';
COMMENT ON COLUMN disco_initiatives.status IS 'Workflow status: draft, triaged, in_discovery, synthesized, evaluated, archived';
COMMENT ON COLUMN disco_initiatives.decided_at IS 'When stakeholders made a decision based on synthesis output';
COMMENT ON COLUMN disco_initiatives.launched_at IS 'When the initiative transitioned from decision to implementation';
COMMENT ON COLUMN disco_initiatives.completed_at IS 'When the initiative achieved its goals';
COMMENT ON COLUMN disco_initiatives.abandoned_at IS 'When the initiative was abandoned (alternative to completed_at)';
COMMENT ON COLUMN disco_initiatives.decision_velocity_days IS 'Days from initiative creation to decision (auto-calculated)';

COMMENT ON TABLE disco_initiative_members IS 'DISCo initiative sharing and permissions';
COMMENT ON COLUMN disco_initiative_members.role IS 'Permission level: owner, editor, viewer';

COMMENT ON TABLE disco_documents IS 'DISCo initiative documents - uploaded and generated';
COMMENT ON COLUMN disco_documents.document_type IS 'Document source: uploaded, triage_output, prd_output, tech_eval_output';
COMMENT ON COLUMN disco_documents.source_run_id IS 'Reference to agent run that generated this document';

COMMENT ON TABLE disco_document_chunks IS 'DISCo document chunks with embeddings for RAG';
COMMENT ON COLUMN disco_document_chunks.initiative_id IS 'Denormalized initiative_id for fast vector search scoping';

COMMENT ON TABLE disco_runs IS 'DISCo agent run history and tracking';
COMMENT ON COLUMN disco_runs.agent_type IS 'Agent: triage, discovery_planner, coverage_tracker, synthesizer, tech_evaluation';
COMMENT ON COLUMN disco_runs.status IS 'Run status: running, completed, failed';

COMMENT ON TABLE disco_run_documents IS 'Junction table tracking documents used in each DISCo run';

COMMENT ON TABLE disco_outputs IS 'DISCo versioned agent outputs with structured fields';
COMMENT ON COLUMN disco_outputs.recommendation IS 'GO/NO-GO recommendation for triage agent';
COMMENT ON COLUMN disco_outputs.tier_routing IS 'Routing tier: ELT, Solutions, Self-Serve';
COMMENT ON COLUMN disco_outputs.confidence_level IS 'Confidence level: HIGH, MEDIUM, LOW';
COMMENT ON COLUMN disco_outputs.stakeholder_rating IS 'Stakeholder conviction rating 1-5: "I know what to do"';
COMMENT ON COLUMN disco_outputs.stakeholder_feedback IS 'Optional freeform feedback from stakeholder';

COMMENT ON TABLE disco_conversations IS 'DISCo initiative chat conversations for RAG';

COMMENT ON TABLE disco_messages IS 'DISCo chat messages with source citations';
COMMENT ON COLUMN disco_messages.role IS 'Message role: user, assistant';
COMMENT ON COLUMN disco_messages.sources IS 'Array of source document references';

COMMENT ON TABLE disco_system_kb IS 'DISCo global system knowledge base files';
COMMENT ON COLUMN disco_system_kb.category IS 'KB category: methodology, analysis, risk, decision, internal';

COMMENT ON TABLE disco_system_kb_chunks IS 'DISCo system KB chunks with embeddings for RAG';

-- ============================================================================
-- PHASE 13: RENAME CONSTRAINTS (Primary Keys, Foreign Keys, Check Constraints)
-- ============================================================================

-- Primary key constraints
ALTER TABLE disco_initiatives RENAME CONSTRAINT purdy_initiatives_pkey TO disco_initiatives_pkey;
ALTER TABLE disco_initiative_members RENAME CONSTRAINT purdy_initiative_members_pkey TO disco_initiative_members_pkey;
ALTER TABLE disco_initiative_members RENAME CONSTRAINT purdy_initiative_members_initiative_id_user_id_key TO disco_initiative_members_initiative_id_user_id_key;
ALTER TABLE disco_documents RENAME CONSTRAINT purdy_documents_pkey TO disco_documents_pkey;
ALTER TABLE disco_document_chunks RENAME CONSTRAINT purdy_document_chunks_pkey TO disco_document_chunks_pkey;
ALTER TABLE disco_runs RENAME CONSTRAINT purdy_runs_pkey TO disco_runs_pkey;
ALTER TABLE disco_run_documents RENAME CONSTRAINT purdy_run_documents_pkey TO disco_run_documents_pkey;
ALTER TABLE disco_outputs RENAME CONSTRAINT purdy_outputs_pkey TO disco_outputs_pkey;
ALTER TABLE disco_conversations RENAME CONSTRAINT purdy_conversations_pkey TO disco_conversations_pkey;
ALTER TABLE disco_messages RENAME CONSTRAINT purdy_messages_pkey TO disco_messages_pkey;
ALTER TABLE disco_system_kb RENAME CONSTRAINT purdy_system_kb_pkey TO disco_system_kb_pkey;
ALTER TABLE disco_system_kb RENAME CONSTRAINT purdy_system_kb_filename_key TO disco_system_kb_filename_key;
ALTER TABLE disco_system_kb_chunks RENAME CONSTRAINT purdy_system_kb_chunks_pkey TO disco_system_kb_chunks_pkey;

-- Foreign key constraints
ALTER TABLE disco_initiatives RENAME CONSTRAINT purdy_initiatives_created_by_fkey TO disco_initiatives_created_by_fkey;
ALTER TABLE disco_initiative_members RENAME CONSTRAINT purdy_initiative_members_initiative_id_fkey TO disco_initiative_members_initiative_id_fkey;
ALTER TABLE disco_initiative_members RENAME CONSTRAINT purdy_initiative_members_user_id_fkey TO disco_initiative_members_user_id_fkey;
ALTER TABLE disco_documents RENAME CONSTRAINT purdy_documents_initiative_id_fkey TO disco_documents_initiative_id_fkey;
ALTER TABLE disco_document_chunks RENAME CONSTRAINT purdy_document_chunks_document_id_fkey TO disco_document_chunks_document_id_fkey;
ALTER TABLE disco_runs RENAME CONSTRAINT purdy_runs_initiative_id_fkey TO disco_runs_initiative_id_fkey;
ALTER TABLE disco_runs RENAME CONSTRAINT purdy_runs_run_by_fkey TO disco_runs_run_by_fkey;
ALTER TABLE disco_run_documents RENAME CONSTRAINT purdy_run_documents_run_id_fkey TO disco_run_documents_run_id_fkey;
ALTER TABLE disco_run_documents RENAME CONSTRAINT purdy_run_documents_document_id_fkey TO disco_run_documents_document_id_fkey;
ALTER TABLE disco_outputs RENAME CONSTRAINT purdy_outputs_run_id_fkey TO disco_outputs_run_id_fkey;
ALTER TABLE disco_outputs RENAME CONSTRAINT purdy_outputs_stakeholder_rating_check TO disco_outputs_stakeholder_rating_check;
ALTER TABLE disco_conversations RENAME CONSTRAINT purdy_conversations_initiative_id_fkey TO disco_conversations_initiative_id_fkey;
ALTER TABLE disco_conversations RENAME CONSTRAINT purdy_conversations_user_id_fkey TO disco_conversations_user_id_fkey;
ALTER TABLE disco_messages RENAME CONSTRAINT purdy_messages_conversation_id_fkey TO disco_messages_conversation_id_fkey;
ALTER TABLE disco_system_kb_chunks RENAME CONSTRAINT purdy_system_kb_chunks_kb_id_fkey TO disco_system_kb_chunks_kb_id_fkey;

-- Additional indexes that may have been missed
ALTER INDEX IF EXISTS idx_purdy_outputs_synthesis_mode RENAME TO idx_disco_outputs_synthesis_mode;
ALTER INDEX IF EXISTS idx_purdy_outputs_format RENAME TO idx_disco_outputs_format;

-- Trigger PostgREST schema reload
NOTIFY pgrst, 'reload schema';

-- ============================================================================
-- VERIFICATION QUERIES (Run these after migration to confirm success)
-- ============================================================================

-- Uncomment to verify:
-- \dt disco_*
-- \di idx_disco_*
-- \df match_disco_*
-- SELECT count(*) FROM disco_initiatives;
-- SELECT count(*) FROM disco_documents;
-- SELECT count(*) FROM disco_outputs;
-- SELECT conname FROM pg_constraint WHERE conname LIKE 'purdy%';  -- Should return 0 rows
