-- Migration: Engagement Level History
-- Date: 2025-01-05
-- Description: Creates engagement_level_history table for tracking automatic engagement
--              level calculations and adds last_engagement_calculated to stakeholders

-- ============================================================================
-- ENGAGEMENT LEVEL HISTORY TABLE
-- ============================================================================
-- Tracks all engagement level calculations for trend analytics

CREATE TABLE IF NOT EXISTS engagement_level_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stakeholder_id UUID NOT NULL REFERENCES stakeholders(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Level tracking
    engagement_level VARCHAR(50) NOT NULL,  -- champion, supporter, neutral, skeptic, blocker
    previous_level VARCHAR(50),             -- Level before this change (NULL for first calculation)

    -- Calculation details
    calculation_reason TEXT,                 -- Human-readable explanation of why this level
    signals JSONB DEFAULT '{}',              -- Captured signals at time of calculation
    -- Example signals:
    -- {
    --   "total_interactions": 5,
    --   "days_since_contact": 7,
    --   "enthusiasm_count": 3,
    --   "support_count": 2,
    --   "commitment_count": 1,
    --   "concern_count": 1,
    --   "objection_count": 0,
    --   "unresolved_concern_count": 0,
    --   "unresolved_objection_count": 0,
    --   "positive_ratio": 0.83
    -- }

    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    calculation_type VARCHAR(50) DEFAULT 'scheduled',  -- 'scheduled', 'manual', 'trigger'

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ADD COLUMN TO STAKEHOLDERS
-- ============================================================================

ALTER TABLE stakeholders
    ADD COLUMN IF NOT EXISTS last_engagement_calculated TIMESTAMPTZ;

COMMENT ON COLUMN stakeholders.last_engagement_calculated IS 'Timestamp of last automatic engagement level calculation';

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_engagement_history_stakeholder
    ON engagement_level_history(stakeholder_id);

CREATE INDEX IF NOT EXISTS idx_engagement_history_client
    ON engagement_level_history(client_id);

CREATE INDEX IF NOT EXISTS idx_engagement_history_calculated_at
    ON engagement_level_history(calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_engagement_history_level
    ON engagement_level_history(engagement_level);

-- Composite index for trend queries (client + time range)
CREATE INDEX IF NOT EXISTS idx_engagement_history_client_time
    ON engagement_level_history(client_id, calculated_at DESC);

-- Index for finding level changes
CREATE INDEX IF NOT EXISTS idx_engagement_history_level_change
    ON engagement_level_history(client_id, calculated_at DESC)
    WHERE previous_level IS DISTINCT FROM engagement_level;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE engagement_level_history ENABLE ROW LEVEL SECURITY;

-- Users can view engagement history for their client
DROP POLICY IF EXISTS "Users can view engagement history in their client" ON engagement_level_history;
CREATE POLICY "Users can view engagement history in their client" ON engagement_level_history
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

-- Service role has full access (for scheduled jobs)
DROP POLICY IF EXISTS "Service role has full access to engagement_level_history" ON engagement_level_history;
CREATE POLICY "Service role has full access to engagement_level_history" ON engagement_level_history
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE engagement_level_history IS 'Tracks stakeholder engagement level calculations over time for trend analytics';
COMMENT ON COLUMN engagement_level_history.engagement_level IS 'Calculated level: champion, supporter, neutral, skeptic, blocker';
COMMENT ON COLUMN engagement_level_history.previous_level IS 'Level before this calculation (NULL for first calculation)';
COMMENT ON COLUMN engagement_level_history.calculation_reason IS 'Human-readable explanation of the level assignment';
COMMENT ON COLUMN engagement_level_history.signals IS 'JSON object containing all signals used in calculation';
COMMENT ON COLUMN engagement_level_history.calculation_type IS 'How calculation was triggered: scheduled (weekly job), manual (admin), trigger (real-time)';
