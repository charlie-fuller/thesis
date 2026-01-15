-- Migration: Project Triage Integration
-- Date: 2026-01-15
-- Description: Adds AI opportunity scoring, stakeholder metrics validation,
--              and meeting prep support for project-triage integration.
--
-- New Tables:
--   - ai_opportunities: 4-dimension scoring model with auto-computed tiers
--   - stakeholder_metrics: Per-stakeholder KPIs with validation status
--   - opportunity_stakeholder_link: Many-to-many relationships
--
-- Stakeholder Extensions:
--   - priority_level, ai_priorities, pain_points, win_conditions
--   - communication_style, relationship_status, open_questions, last_contact

-- ============================================================================
-- AI OPPORTUNITIES TABLE
-- ============================================================================
-- Primary opportunity tracking with 4-dimension scoring model
-- Scoring: ROI Potential + Implementation Effort + Strategic Alignment + Stakeholder Readiness
-- Each dimension is 1-5, total max 20, auto-tiered

CREATE TABLE IF NOT EXISTS ai_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Identification
    opportunity_code VARCHAR(10) NOT NULL,  -- e.g., F01, L02, H03, S04
    title VARCHAR(255) NOT NULL,
    description TEXT,
    department VARCHAR(100),  -- finance, legal, hr, it, revops, marketing, sales

    -- Owner/Champion
    owner_stakeholder_id UUID REFERENCES stakeholders(id) ON DELETE SET NULL,

    -- Current/Desired State
    current_state TEXT,
    desired_state TEXT,

    -- 4-Dimension Scoring (1-5 scale each)
    roi_potential INTEGER CHECK (roi_potential IS NULL OR roi_potential BETWEEN 1 AND 5),
    implementation_effort INTEGER CHECK (implementation_effort IS NULL OR implementation_effort BETWEEN 1 AND 5),
    strategic_alignment INTEGER CHECK (strategic_alignment IS NULL OR strategic_alignment BETWEEN 1 AND 5),
    stakeholder_readiness INTEGER CHECK (stakeholder_readiness IS NULL OR stakeholder_readiness BETWEEN 1 AND 5),

    -- Computed total score (max 20)
    total_score INTEGER GENERATED ALWAYS AS (
        COALESCE(roi_potential, 0) +
        COALESCE(implementation_effort, 0) +
        COALESCE(strategic_alignment, 0) +
        COALESCE(stakeholder_readiness, 0)
    ) STORED,

    -- Computed tier based on total score
    -- Tier 1: 17-20 (Immediate Priority)
    -- Tier 2: 14-16 (Near-Term Priority)
    -- Tier 3: 11-13 (Medium-Term)
    -- Tier 4: 8-10 or lower (Backlog)
    tier INTEGER GENERATED ALWAYS AS (
        CASE
            WHEN (COALESCE(roi_potential, 0) + COALESCE(implementation_effort, 0) +
                  COALESCE(strategic_alignment, 0) + COALESCE(stakeholder_readiness, 0)) >= 17 THEN 1
            WHEN (COALESCE(roi_potential, 0) + COALESCE(implementation_effort, 0) +
                  COALESCE(strategic_alignment, 0) + COALESCE(stakeholder_readiness, 0)) >= 14 THEN 2
            WHEN (COALESCE(roi_potential, 0) + COALESCE(implementation_effort, 0) +
                  COALESCE(strategic_alignment, 0) + COALESCE(stakeholder_readiness, 0)) >= 11 THEN 3
            ELSE 4
        END
    ) STORED,

    -- Status Tracking
    status VARCHAR(50) DEFAULT 'identified',  -- identified, scoping, pilot, scaling, completed, blocked
    next_step TEXT,
    blockers TEXT[],
    follow_up_questions TEXT[],

    -- ROI Indicators (flexible JSONB)
    roi_indicators JSONB DEFAULT '{}',
    -- Example: {
    --   "time_savings_percent": 80,
    --   "cost_savings_annual": "$80-140K",
    --   "payback_months": 3,
    --   "hours_saved_weekly": 40
    -- }

    -- Source Tracking
    source_type VARCHAR(50),  -- transcript, research, manual, meeting
    source_id UUID,
    source_notes TEXT,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint on code within client
    UNIQUE(client_id, opportunity_code)
);

COMMENT ON TABLE ai_opportunities IS 'AI implementation opportunities with 4-dimension scoring and auto-tiering';
COMMENT ON COLUMN ai_opportunities.opportunity_code IS 'Short identifier like F01 (Finance #1), L02 (Legal #2)';
COMMENT ON COLUMN ai_opportunities.roi_potential IS 'Score 1-5: Revenue/cost/time impact potential';
COMMENT ON COLUMN ai_opportunities.implementation_effort IS 'Score 1-5: Ease of implementation (5=easy)';
COMMENT ON COLUMN ai_opportunities.strategic_alignment IS 'Score 1-5: Alignment with North Star goals';
COMMENT ON COLUMN ai_opportunities.stakeholder_readiness IS 'Score 1-5: Champion identified, data ready, team eager';
COMMENT ON COLUMN ai_opportunities.total_score IS 'Auto-computed sum of 4 dimensions (max 20)';
COMMENT ON COLUMN ai_opportunities.tier IS 'Auto-computed tier: 1 (17-20), 2 (14-16), 3 (11-13), 4 (<11)';

-- ============================================================================
-- STAKEHOLDER METRICS TABLE
-- ============================================================================
-- Per-stakeholder KPI tracking with validation status (red/yellow/green)

CREATE TABLE IF NOT EXISTS stakeholder_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stakeholder_id UUID NOT NULL REFERENCES stakeholders(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Metric Definition
    metric_name VARCHAR(255) NOT NULL,
    metric_category VARCHAR(100) DEFAULT 'primary',  -- primary, secondary, operational
    unit VARCHAR(50),  -- days, hours, %, $, count, etc.

    -- Values
    current_value VARCHAR(255),
    target_value VARCHAR(255),

    -- Validation Status
    -- red = needs validation (estimated, unconfirmed)
    -- yellow = partially validated (directionally correct)
    -- green = confirmed (stakeholder verified)
    validation_status VARCHAR(20) DEFAULT 'red' CHECK (validation_status IN ('red', 'yellow', 'green')),

    -- Source Tracking
    source VARCHAR(255),  -- "Finance transcript 2026-01-07", "Raul verbal"
    source_date DATE,

    -- Notes
    notes TEXT,
    questions_to_confirm TEXT[],  -- Specific questions to ask to validate

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- One metric per name per stakeholder
    UNIQUE(stakeholder_id, metric_name)
);

COMMENT ON TABLE stakeholder_metrics IS 'Stakeholder KPIs with validation tracking (red/yellow/green status)';
COMMENT ON COLUMN stakeholder_metrics.validation_status IS 'red=needs validation, yellow=partial, green=confirmed';
COMMENT ON COLUMN stakeholder_metrics.questions_to_confirm IS 'Questions to ask stakeholder to validate this metric';

-- ============================================================================
-- OPPORTUNITY-STAKEHOLDER LINK TABLE
-- ============================================================================
-- Many-to-many relationship between opportunities and stakeholders

CREATE TABLE IF NOT EXISTS opportunity_stakeholder_link (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID NOT NULL REFERENCES ai_opportunities(id) ON DELETE CASCADE,
    stakeholder_id UUID NOT NULL REFERENCES stakeholders(id) ON DELETE CASCADE,

    -- Role in this opportunity
    role VARCHAR(50) DEFAULT 'involved',  -- owner, champion, involved, blocker, approver
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- One link per opportunity-stakeholder pair
    UNIQUE(opportunity_id, stakeholder_id)
);

COMMENT ON TABLE opportunity_stakeholder_link IS 'Links stakeholders to opportunities with role designation';
COMMENT ON COLUMN opportunity_stakeholder_link.role IS 'Stakeholder role: owner, champion, involved, blocker, approver';

-- ============================================================================
-- STAKEHOLDER TABLE EXTENSIONS
-- ============================================================================
-- Add project-triage fields to existing stakeholders table

-- Priority level (tier_1 = most important, tier_3 = least)
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS priority_level VARCHAR(20) DEFAULT 'tier_3';

-- AI priorities - what they want from AI
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS ai_priorities TEXT[];

-- Pain points - what frustrates them
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS pain_points TEXT[];

-- Win conditions - what makes them a champion
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS win_conditions TEXT[];

-- Communication style - how to engage them
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS communication_style TEXT;

-- Relationship status - current state of relationship
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS relationship_status VARCHAR(50) DEFAULT 'new';

-- Open questions - what to ask next
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS open_questions TEXT[];

-- Last contact date (different from last_interaction which is auto-updated)
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS last_contact DATE;

-- Reports to name (denormalized for display)
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS reports_to_name VARCHAR(255);

-- Team size
ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS team_size INTEGER;

COMMENT ON COLUMN stakeholders.priority_level IS 'Stakeholder priority: tier_1 (critical), tier_2 (important), tier_3 (standard)';
COMMENT ON COLUMN stakeholders.ai_priorities IS 'Array of AI-related priorities and goals';
COMMENT ON COLUMN stakeholders.pain_points IS 'Array of frustrations and challenges';
COMMENT ON COLUMN stakeholders.win_conditions IS 'Array of conditions that would make them an AI champion';
COMMENT ON COLUMN stakeholders.communication_style IS 'Preferred engagement approach and style';
COMMENT ON COLUMN stakeholders.relationship_status IS 'Current relationship: strong, building, new, strained';
COMMENT ON COLUMN stakeholders.open_questions IS 'Array of questions to ask in next meeting';
COMMENT ON COLUMN stakeholders.last_contact IS 'Manual last contact date (for meeting prep)';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- AI Opportunities indexes
CREATE INDEX IF NOT EXISTS idx_ai_opportunities_client_id
    ON ai_opportunities(client_id);

CREATE INDEX IF NOT EXISTS idx_ai_opportunities_code
    ON ai_opportunities(opportunity_code);

CREATE INDEX IF NOT EXISTS idx_ai_opportunities_department
    ON ai_opportunities(department);

CREATE INDEX IF NOT EXISTS idx_ai_opportunities_tier
    ON ai_opportunities(tier);

CREATE INDEX IF NOT EXISTS idx_ai_opportunities_status
    ON ai_opportunities(status);

CREATE INDEX IF NOT EXISTS idx_ai_opportunities_owner
    ON ai_opportunities(owner_stakeholder_id);

-- Composite index for common queries (tier + status within client)
CREATE INDEX IF NOT EXISTS idx_ai_opportunities_client_tier_status
    ON ai_opportunities(client_id, tier, status);

-- Stakeholder Metrics indexes
CREATE INDEX IF NOT EXISTS idx_stakeholder_metrics_stakeholder_id
    ON stakeholder_metrics(stakeholder_id);

CREATE INDEX IF NOT EXISTS idx_stakeholder_metrics_client_id
    ON stakeholder_metrics(client_id);

CREATE INDEX IF NOT EXISTS idx_stakeholder_metrics_validation
    ON stakeholder_metrics(validation_status);

-- Find unvalidated metrics quickly
CREATE INDEX IF NOT EXISTS idx_stakeholder_metrics_needs_validation
    ON stakeholder_metrics(client_id, validation_status)
    WHERE validation_status IN ('red', 'yellow');

-- Opportunity-Stakeholder Link indexes
CREATE INDEX IF NOT EXISTS idx_opp_stakeholder_link_opportunity
    ON opportunity_stakeholder_link(opportunity_id);

CREATE INDEX IF NOT EXISTS idx_opp_stakeholder_link_stakeholder
    ON opportunity_stakeholder_link(stakeholder_id);

CREATE INDEX IF NOT EXISTS idx_opp_stakeholder_link_role
    ON opportunity_stakeholder_link(role);

-- Stakeholder extensions indexes
CREATE INDEX IF NOT EXISTS idx_stakeholders_priority_level
    ON stakeholders(priority_level);

CREATE INDEX IF NOT EXISTS idx_stakeholders_relationship_status
    ON stakeholders(relationship_status);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- AI Opportunities RLS
ALTER TABLE ai_opportunities ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view opportunities in their client" ON ai_opportunities;
CREATE POLICY "Users can view opportunities in their client" ON ai_opportunities
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can manage opportunities in their client" ON ai_opportunities;
CREATE POLICY "Users can manage opportunities in their client" ON ai_opportunities
    FOR ALL USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Service role has full access to ai_opportunities" ON ai_opportunities;
CREATE POLICY "Service role has full access to ai_opportunities" ON ai_opportunities
    FOR ALL USING (auth.role() = 'service_role');

-- Stakeholder Metrics RLS
ALTER TABLE stakeholder_metrics ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view metrics in their client" ON stakeholder_metrics;
CREATE POLICY "Users can view metrics in their client" ON stakeholder_metrics
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can manage metrics in their client" ON stakeholder_metrics;
CREATE POLICY "Users can manage metrics in their client" ON stakeholder_metrics
    FOR ALL USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Service role has full access to stakeholder_metrics" ON stakeholder_metrics;
CREATE POLICY "Service role has full access to stakeholder_metrics" ON stakeholder_metrics
    FOR ALL USING (auth.role() = 'service_role');

-- Opportunity-Stakeholder Link RLS
ALTER TABLE opportunity_stakeholder_link ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view links via opportunity access" ON opportunity_stakeholder_link;
CREATE POLICY "Users can view links via opportunity access" ON opportunity_stakeholder_link
    FOR SELECT USING (
        opportunity_id IN (
            SELECT id FROM ai_opportunities
            WHERE client_id IN (
                SELECT client_id FROM users WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Users can manage links via opportunity access" ON opportunity_stakeholder_link;
CREATE POLICY "Users can manage links via opportunity access" ON opportunity_stakeholder_link
    FOR ALL USING (
        opportunity_id IN (
            SELECT id FROM ai_opportunities
            WHERE client_id IN (
                SELECT client_id FROM users WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Service role has full access to opportunity_stakeholder_link" ON opportunity_stakeholder_link;
CREATE POLICY "Service role has full access to opportunity_stakeholder_link" ON opportunity_stakeholder_link
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update opportunity timestamp on changes
CREATE OR REPLACE FUNCTION update_opportunity_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_opportunity_timestamp ON ai_opportunities;
CREATE TRIGGER trigger_update_opportunity_timestamp
BEFORE UPDATE ON ai_opportunities
FOR EACH ROW
EXECUTE FUNCTION update_opportunity_timestamp();

-- Function to update stakeholder_metrics timestamp on changes
CREATE OR REPLACE FUNCTION update_stakeholder_metrics_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_stakeholder_metrics_timestamp ON stakeholder_metrics;
CREATE TRIGGER trigger_update_stakeholder_metrics_timestamp
BEFORE UPDATE ON stakeholder_metrics
FOR EACH ROW
EXECUTE FUNCTION update_stakeholder_metrics_timestamp();

-- ============================================================================
-- VIEWS (Optional convenience views)
-- ============================================================================

-- View: Opportunities with owner name joined
CREATE OR REPLACE VIEW v_opportunities_with_owner AS
SELECT
    o.*,
    s.name as owner_name,
    s.email as owner_email,
    s.department as owner_department
FROM ai_opportunities o
LEFT JOIN stakeholders s ON o.owner_stakeholder_id = s.id;

-- View: Stakeholders with metrics summary
CREATE OR REPLACE VIEW v_stakeholders_with_metrics AS
SELECT
    s.*,
    COUNT(sm.id) as total_metrics,
    COUNT(sm.id) FILTER (WHERE sm.validation_status = 'green') as validated_metrics,
    COUNT(sm.id) FILTER (WHERE sm.validation_status = 'red') as unvalidated_metrics,
    COUNT(osl.id) as linked_opportunities
FROM stakeholders s
LEFT JOIN stakeholder_metrics sm ON s.id = sm.stakeholder_id
LEFT JOIN opportunity_stakeholder_link osl ON s.id = osl.stakeholder_id
GROUP BY s.id;

-- ============================================================================
-- DONE!
-- ============================================================================
