-- Migration: 048_disco_synthesis.sql
-- Description: Add DISCo Synthesis stage tables for initiative bundles
-- Created: 2026-01-25

-- ============================================================================
-- disco_bundles: Initiative bundles proposed by Synthesis stage
-- ============================================================================

CREATE TABLE IF NOT EXISTS disco_bundles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiative_id UUID NOT NULL REFERENCES purdy_initiatives(id) ON DELETE CASCADE,

    -- Bundle definition
    name TEXT NOT NULL,
    description TEXT,

    -- Status workflow: proposed -> approved/rejected
    status TEXT NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed', 'approved', 'rejected', 'merged')),

    -- Scoring (from Synthesis agent)
    impact_score TEXT CHECK (impact_score IN ('HIGH', 'MEDIUM', 'LOW')),
    impact_rationale TEXT,
    feasibility_score TEXT CHECK (feasibility_score IN ('HIGH', 'MEDIUM', 'LOW')),
    feasibility_rationale TEXT,
    urgency_score TEXT CHECK (urgency_score IN ('HIGH', 'MEDIUM', 'LOW')),
    urgency_rationale TEXT,

    -- Complexity tier
    complexity_tier TEXT CHECK (complexity_tier IN ('Light', 'Medium', 'Heavy')),
    complexity_rationale TEXT,

    -- Bundle contents (references to insights)
    included_items JSONB DEFAULT '[]'::jsonb,
    -- Format: [{"type": "pain_point", "description": "...", "source": "..."}]

    -- Affected stakeholders
    stakeholders JSONB DEFAULT '[]'::jsonb,
    -- Format: [{"name": "...", "stake": "..."}]

    -- Dependencies
    dependencies JSONB DEFAULT '{}'::jsonb,
    -- Format: {"blocks": ["uuid"], "requires": ["uuid"], "conflicts": ["uuid"]}

    -- Rationale for bundling
    bundling_rationale TEXT,

    -- Output reference (which synthesis run created this)
    source_output_id UUID REFERENCES purdy_outputs(id) ON DELETE SET NULL,

    -- Tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES auth.users(id)
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_disco_bundles_initiative ON disco_bundles(initiative_id);
CREATE INDEX IF NOT EXISTS idx_disco_bundles_status ON disco_bundles(status);
CREATE INDEX IF NOT EXISTS idx_disco_bundles_created ON disco_bundles(created_at DESC);

-- ============================================================================
-- disco_bundle_feedback: Human feedback/edits on bundles
-- ============================================================================

CREATE TABLE IF NOT EXISTS disco_bundle_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_id UUID NOT NULL REFERENCES disco_bundles(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id),

    -- Action type
    action TEXT NOT NULL CHECK (action IN (
        'approve', 'reject', 'edit', 'split', 'merge',
        'adjust_score', 'add_item', 'remove_item', 'comment'
    )),

    -- Feedback content
    feedback TEXT,

    -- For edits: what changed
    changes JSONB,
    -- Format: {"field": "name", "old_value": "...", "new_value": "..."}

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for feedback queries
CREATE INDEX IF NOT EXISTS idx_disco_bundle_feedback_bundle ON disco_bundle_feedback(bundle_id);
CREATE INDEX IF NOT EXISTS idx_disco_bundle_feedback_user ON disco_bundle_feedback(user_id);

-- ============================================================================
-- disco_prds: Generated PRDs from approved bundles (for Phase 3)
-- ============================================================================

CREATE TABLE IF NOT EXISTS disco_prds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_id UUID NOT NULL REFERENCES disco_bundles(id) ON DELETE CASCADE,
    initiative_id UUID NOT NULL REFERENCES purdy_initiatives(id) ON DELETE CASCADE,

    -- PRD content
    title TEXT NOT NULL,
    content_markdown TEXT NOT NULL,
    content_structured JSONB,

    -- Status
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'review', 'approved', 'exported')),

    -- Version tracking
    version INTEGER NOT NULL DEFAULT 1,

    -- Output reference
    source_output_id UUID REFERENCES purdy_outputs(id) ON DELETE SET NULL,

    -- Tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES auth.users(id)
);

-- Index for PRD queries
CREATE INDEX IF NOT EXISTS idx_disco_prds_bundle ON disco_prds(bundle_id);
CREATE INDEX IF NOT EXISTS idx_disco_prds_initiative ON disco_prds(initiative_id);
CREATE INDEX IF NOT EXISTS idx_disco_prds_status ON disco_prds(status);

-- ============================================================================
-- RLS Policies
-- ============================================================================

-- Enable RLS
ALTER TABLE disco_bundles ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_bundle_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE disco_prds ENABLE ROW LEVEL SECURITY;

-- disco_bundles policies
CREATE POLICY "disco_bundles_select_policy" ON disco_bundles
    FOR SELECT USING (
        initiative_id IN (
            SELECT initiative_id FROM purdy_initiative_members WHERE user_id = auth.uid()
        )
        OR initiative_id IN (
            SELECT id FROM purdy_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_bundles_insert_policy" ON disco_bundles
    FOR INSERT WITH CHECK (
        initiative_id IN (
            SELECT initiative_id FROM purdy_initiative_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'editor')
        )
        OR initiative_id IN (
            SELECT id FROM purdy_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_bundles_update_policy" ON disco_bundles
    FOR UPDATE USING (
        initiative_id IN (
            SELECT initiative_id FROM purdy_initiative_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'editor')
        )
        OR initiative_id IN (
            SELECT id FROM purdy_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_bundles_delete_policy" ON disco_bundles
    FOR DELETE USING (
        initiative_id IN (
            SELECT initiative_id FROM purdy_initiative_members
            WHERE user_id = auth.uid() AND role = 'owner'
        )
        OR initiative_id IN (
            SELECT id FROM purdy_initiatives WHERE created_by = auth.uid()
        )
    );

-- disco_bundle_feedback policies
CREATE POLICY "disco_bundle_feedback_select_policy" ON disco_bundle_feedback
    FOR SELECT USING (
        bundle_id IN (
            SELECT b.id FROM disco_bundles b
            JOIN purdy_initiative_members m ON b.initiative_id = m.initiative_id
            WHERE m.user_id = auth.uid()
        )
        OR bundle_id IN (
            SELECT b.id FROM disco_bundles b
            JOIN purdy_initiatives i ON b.initiative_id = i.id
            WHERE i.created_by = auth.uid()
        )
    );

CREATE POLICY "disco_bundle_feedback_insert_policy" ON disco_bundle_feedback
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- disco_prds policies
CREATE POLICY "disco_prds_select_policy" ON disco_prds
    FOR SELECT USING (
        initiative_id IN (
            SELECT initiative_id FROM purdy_initiative_members WHERE user_id = auth.uid()
        )
        OR initiative_id IN (
            SELECT id FROM purdy_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_prds_insert_policy" ON disco_prds
    FOR INSERT WITH CHECK (
        initiative_id IN (
            SELECT initiative_id FROM purdy_initiative_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'editor')
        )
        OR initiative_id IN (
            SELECT id FROM purdy_initiatives WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "disco_prds_update_policy" ON disco_prds
    FOR UPDATE USING (
        initiative_id IN (
            SELECT initiative_id FROM purdy_initiative_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'editor')
        )
        OR initiative_id IN (
            SELECT id FROM purdy_initiatives WHERE created_by = auth.uid()
        )
    );

-- ============================================================================
-- Triggers for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_disco_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER disco_bundles_updated_at
    BEFORE UPDATE ON disco_bundles
    FOR EACH ROW
    EXECUTE FUNCTION update_disco_updated_at();

CREATE TRIGGER disco_prds_updated_at
    BEFORE UPDATE ON disco_prds
    FOR EACH ROW
    EXECUTE FUNCTION update_disco_updated_at();
