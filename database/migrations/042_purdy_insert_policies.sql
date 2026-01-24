-- Migration: 042_purdy_insert_policies
-- Description: Add missing INSERT/UPDATE policies for PuRDy tables
-- The original migration only had SELECT policies, blocking writes even with service role
-- Date: 2026-01-24

-- ============================================================================
-- PURDY_OUTPUTS INSERT POLICY
-- ============================================================================

-- Allow inserting outputs for initiatives user has access to
CREATE POLICY IF NOT EXISTS purdy_outputs_insert ON purdy_outputs FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_outputs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = purdy_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- Allow updating outputs for initiatives user has access to
CREATE POLICY IF NOT EXISTS purdy_outputs_update ON purdy_outputs FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_outputs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = purdy_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- Allow deleting outputs for initiatives user has access to
CREATE POLICY IF NOT EXISTS purdy_outputs_delete ON purdy_outputs FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_outputs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = purdy_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- ============================================================================
-- PURDY_RUNS INSERT POLICY
-- ============================================================================

-- Allow inserting runs for initiatives user has access to
CREATE POLICY IF NOT EXISTS purdy_runs_insert ON purdy_runs FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_runs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = purdy_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- Allow updating runs (for status updates)
CREATE POLICY IF NOT EXISTS purdy_runs_update ON purdy_runs FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM purdy_initiatives
            WHERE id = purdy_runs.initiative_id
            AND (
                created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = purdy_initiatives.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );

-- ============================================================================
-- PURDY_RUN_DOCUMENTS INSERT POLICY
-- ============================================================================

-- Allow inserting run documents
CREATE POLICY IF NOT EXISTS purdy_run_documents_insert ON purdy_run_documents FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM purdy_runs r
            JOIN purdy_initiatives i ON i.id = r.initiative_id
            WHERE r.id = purdy_run_documents.run_id
            AND (
                i.created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM purdy_initiative_members
                    WHERE initiative_id = i.id
                    AND user_id = auth.uid()
                    AND role IN ('owner', 'editor')
                )
            )
        )
    );
