-- ============================================================================
-- THESIS SCHEMA EXTENSIONS
-- Run this after thesis_base_schema.sql
-- Adds agent registry, stakeholders, transcripts, and ROI tracking
-- ============================================================================

-- ============================================================================
-- AGENT REGISTRY
-- ============================================================================

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,  -- "atlas", "fortuna", "guardian", "counselor", "oracle"
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    system_instruction TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed the core agents
INSERT INTO agents (name, display_name, description, is_active) VALUES
    ('atlas', 'Atlas', 'Research agent - tracks GenAI research, consulting approaches, case studies, and thought leadership', TRUE),
    ('fortuna', 'Fortuna', 'Finance agent - ROI analysis, budget justification, Finance stakeholder support', TRUE),
    ('guardian', 'Guardian', 'IT/Governance agent - navigates governance, security, and infrastructure considerations', TRUE),
    ('counselor', 'Counselor', 'Legal agent - legal considerations, contracts, and compliance', TRUE),
    ('oracle', 'Oracle', 'Transcript analyzer - extracts stakeholder sentiment from meeting transcripts', TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- Agent instruction versions (extends base system for multi-agent)
CREATE TABLE IF NOT EXISTS agent_instruction_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL,
    instructions TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    UNIQUE(agent_id, version_number)
);

-- ============================================================================
-- STAKEHOLDER TRACKING (Full CRM-style)
-- ============================================================================

CREATE TABLE IF NOT EXISTS stakeholders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Basic Info
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(255),
    department VARCHAR(100),  -- finance, it, legal, governance, hr, marketing, etc.
    organization VARCHAR(255) DEFAULT 'Contentful',

    -- Sentiment & Engagement
    sentiment_score FLOAT DEFAULT 0.0,  -- -1 to 1
    sentiment_trend VARCHAR(20) DEFAULT 'stable',  -- improving, stable, declining
    engagement_level VARCHAR(50) DEFAULT 'neutral',  -- champion, supporter, neutral, skeptic, blocker
    alignment_score FLOAT DEFAULT 0.5,  -- 0 to 1, alignment with AI initiatives

    -- Interaction History
    first_interaction DATE,
    last_interaction TIMESTAMPTZ,
    total_interactions INTEGER DEFAULT 0,

    -- Preferences & Notes
    communication_preferences JSONB DEFAULT '{}',  -- {preferred_channel, best_times, etc.}
    key_concerns JSONB DEFAULT '[]',  -- Array of active concerns
    interests JSONB DEFAULT '[]',  -- What they care about
    notes TEXT,

    -- Relationships
    reports_to UUID REFERENCES stakeholders(id) ON DELETE SET NULL,
    influences JSONB DEFAULT '[]',  -- Array of stakeholder IDs they influence

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stakeholder Insights (extracted from transcripts)
CREATE TABLE IF NOT EXISTS stakeholder_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stakeholder_id UUID NOT NULL REFERENCES stakeholders(id) ON DELETE CASCADE,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    meeting_transcript_id UUID,  -- Will reference meeting_transcripts

    insight_type VARCHAR(50) NOT NULL,  -- concern, enthusiasm, question, commitment, objection, support
    content TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.8,

    -- Context
    extracted_quote TEXT,  -- Direct quote from transcript
    context TEXT,  -- Surrounding context

    -- Status
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- MEETING TRANSCRIPTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS meeting_transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Meeting Info
    title VARCHAR(500),
    meeting_date DATE,
    meeting_type VARCHAR(100),  -- discovery, planning, review, standup, etc.

    -- Parsed Content
    raw_text TEXT,
    attendees JSONB DEFAULT '[]',  -- [{name, role, organization, stakeholder_id}]

    -- Analysis Results
    summary TEXT,
    key_topics JSONB DEFAULT '[]',
    sentiment_summary JSONB DEFAULT '{}',  -- {overall, by_speaker}
    action_items JSONB DEFAULT '[]',  -- [{description, owner, due_date, status}]
    decisions JSONB DEFAULT '[]',
    open_questions JSONB DEFAULT '[]',

    -- Processing Status
    processing_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    processing_error TEXT,
    processed_at TIMESTAMPTZ,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add foreign key for stakeholder_insights (only if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_meeting_transcript'
    ) THEN
        ALTER TABLE stakeholder_insights
            ADD CONSTRAINT fk_meeting_transcript
            FOREIGN KEY (meeting_transcript_id)
            REFERENCES meeting_transcripts(id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- ROI OPPORTUNITIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS roi_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Opportunity Details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    department VARCHAR(100),

    -- Valuation
    estimated_value_usd DECIMAL(12, 2),
    estimated_hours_saved DECIMAL(10, 2),
    confidence_level VARCHAR(50) DEFAULT 'medium',  -- low, medium, high

    -- Status Tracking
    status VARCHAR(50) DEFAULT 'identified',  -- identified, validated, in_progress, completed, rejected
    priority VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, critical

    -- Stakeholder Alignment
    stakeholder_alignment JSONB DEFAULT '[]',  -- [{stakeholder_id, support_level, notes}]

    -- Source
    source_type VARCHAR(50),  -- transcript, research, manual
    source_id UUID,  -- Reference to transcript or document

    -- Outcome Tracking
    actual_value_usd DECIMAL(12, 2),
    actual_hours_saved DECIMAL(10, 2),
    completed_at TIMESTAMPTZ,
    outcome_notes TEXT,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- AGENT HANDOFFS
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_handoffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    from_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    to_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

    -- Handoff Details
    reason TEXT,
    context JSONB DEFAULT '{}',  -- Preserved context for receiving agent

    -- Tracking
    initiated_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'initiated'  -- initiated, accepted, completed, rejected
);

-- Track which agent version was used for each conversation
ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES agents(id),
    ADD COLUMN IF NOT EXISTS agent_instruction_version_id UUID REFERENCES agent_instruction_versions(id);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Agents
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
CREATE INDEX IF NOT EXISTS idx_agents_is_active ON agents(is_active);

-- Agent Instruction Versions
CREATE INDEX IF NOT EXISTS idx_agent_instructions_agent_id ON agent_instruction_versions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_instructions_is_active ON agent_instruction_versions(is_active);

-- Stakeholders
CREATE INDEX IF NOT EXISTS idx_stakeholders_client_id ON stakeholders(client_id);
CREATE INDEX IF NOT EXISTS idx_stakeholders_department ON stakeholders(department);
CREATE INDEX IF NOT EXISTS idx_stakeholders_engagement_level ON stakeholders(engagement_level);
CREATE INDEX IF NOT EXISTS idx_stakeholders_last_interaction ON stakeholders(last_interaction);
CREATE INDEX IF NOT EXISTS idx_stakeholders_name ON stakeholders(name);

-- Stakeholder Insights
CREATE INDEX IF NOT EXISTS idx_stakeholder_insights_stakeholder_id ON stakeholder_insights(stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_insights_type ON stakeholder_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_stakeholder_insights_is_resolved ON stakeholder_insights(is_resolved);
CREATE INDEX IF NOT EXISTS idx_stakeholder_insights_transcript_id ON stakeholder_insights(meeting_transcript_id);

-- Meeting Transcripts
CREATE INDEX IF NOT EXISTS idx_meeting_transcripts_client_id ON meeting_transcripts(client_id);
CREATE INDEX IF NOT EXISTS idx_meeting_transcripts_user_id ON meeting_transcripts(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_transcripts_meeting_date ON meeting_transcripts(meeting_date);
CREATE INDEX IF NOT EXISTS idx_meeting_transcripts_status ON meeting_transcripts(processing_status);

-- ROI Opportunities
CREATE INDEX IF NOT EXISTS idx_roi_opportunities_client_id ON roi_opportunities(client_id);
CREATE INDEX IF NOT EXISTS idx_roi_opportunities_status ON roi_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_roi_opportunities_department ON roi_opportunities(department);

-- Agent Handoffs
CREATE INDEX IF NOT EXISTS idx_agent_handoffs_conversation_id ON agent_handoffs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_handoffs_from_agent ON agent_handoffs(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_handoffs_to_agent ON agent_handoffs(to_agent_id);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_instruction_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE stakeholders ENABLE ROW LEVEL SECURITY;
ALTER TABLE stakeholder_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE roi_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_handoffs ENABLE ROW LEVEL SECURITY;

-- Agents are readable by all authenticated users
DROP POLICY IF EXISTS "Users can view active agents" ON agents;
CREATE POLICY "Users can view active agents" ON agents
    FOR SELECT USING (is_active = TRUE);

-- Agent instructions - admins can manage, users can view active
DROP POLICY IF EXISTS "Users can view active agent instructions" ON agent_instruction_versions;
CREATE POLICY "Users can view active agent instructions" ON agent_instruction_versions
    FOR SELECT USING (is_active = TRUE);

DROP POLICY IF EXISTS "Admins can manage agent instructions" ON agent_instruction_versions;
CREATE POLICY "Admins can manage agent instructions" ON agent_instruction_versions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'admin'
        )
    );

-- Stakeholders - users can view/manage within their client
DROP POLICY IF EXISTS "Users can view stakeholders in their client" ON stakeholders;
CREATE POLICY "Users can view stakeholders in their client" ON stakeholders
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can manage stakeholders in their client" ON stakeholders;
CREATE POLICY "Users can manage stakeholders in their client" ON stakeholders
    FOR ALL USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

-- Stakeholder Insights - via stakeholder access
DROP POLICY IF EXISTS "Users can view insights for their stakeholders" ON stakeholder_insights;
CREATE POLICY "Users can view insights for their stakeholders" ON stakeholder_insights
    FOR SELECT USING (
        stakeholder_id IN (
            SELECT s.id FROM stakeholders s
            JOIN users u ON s.client_id = u.client_id
            WHERE u.id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can manage insights for their stakeholders" ON stakeholder_insights;
CREATE POLICY "Users can manage insights for their stakeholders" ON stakeholder_insights
    FOR ALL USING (
        stakeholder_id IN (
            SELECT s.id FROM stakeholders s
            JOIN users u ON s.client_id = u.client_id
            WHERE u.id = auth.uid()
        )
    );

-- Meeting Transcripts - users can manage their own
DROP POLICY IF EXISTS "Users can view their transcripts" ON meeting_transcripts;
CREATE POLICY "Users can view their transcripts" ON meeting_transcripts
    FOR SELECT USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can manage their transcripts" ON meeting_transcripts;
CREATE POLICY "Users can manage their transcripts" ON meeting_transcripts
    FOR ALL USING (user_id = auth.uid());

-- ROI Opportunities - client-level access
DROP POLICY IF EXISTS "Users can view ROI opportunities in their client" ON roi_opportunities;
CREATE POLICY "Users can view ROI opportunities in their client" ON roi_opportunities
    FOR SELECT USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can manage ROI opportunities in their client" ON roi_opportunities;
CREATE POLICY "Users can manage ROI opportunities in their client" ON roi_opportunities
    FOR ALL USING (
        client_id IN (
            SELECT client_id FROM users WHERE id = auth.uid()
        )
    );

-- Agent Handoffs - via conversation access
DROP POLICY IF EXISTS "Users can view handoffs in their conversations" ON agent_handoffs;
CREATE POLICY "Users can view handoffs in their conversations" ON agent_handoffs
    FOR SELECT USING (
        conversation_id IN (
            SELECT id FROM conversations WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update stakeholder sentiment after new insight
CREATE OR REPLACE FUNCTION update_stakeholder_sentiment()
RETURNS TRIGGER AS $$
DECLARE
    avg_sentiment FLOAT;
    concern_count INTEGER;
    enthusiasm_count INTEGER;
BEGIN
    -- Calculate average sentiment based on recent insights
    SELECT
        COUNT(*) FILTER (WHERE insight_type = 'concern'),
        COUNT(*) FILTER (WHERE insight_type IN ('enthusiasm', 'support'))
    INTO concern_count, enthusiasm_count
    FROM stakeholder_insights
    WHERE stakeholder_id = NEW.stakeholder_id
    AND created_at > NOW() - INTERVAL '30 days';

    -- Simple sentiment calculation
    IF (concern_count + enthusiasm_count) > 0 THEN
        avg_sentiment := (enthusiasm_count::FLOAT - concern_count::FLOAT) / (concern_count + enthusiasm_count);
    ELSE
        avg_sentiment := 0;
    END IF;

    -- Update stakeholder
    UPDATE stakeholders
    SET
        sentiment_score = avg_sentiment,
        updated_at = NOW()
    WHERE id = NEW.stakeholder_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_stakeholder_sentiment ON stakeholder_insights;
CREATE TRIGGER trigger_update_stakeholder_sentiment
AFTER INSERT ON stakeholder_insights
FOR EACH ROW
EXECUTE FUNCTION update_stakeholder_sentiment();

-- Function to update stakeholder interaction stats
CREATE OR REPLACE FUNCTION update_stakeholder_interactions()
RETURNS TRIGGER AS $$
BEGIN
    -- Update interaction stats for each attendee
    UPDATE stakeholders s
    SET
        last_interaction = NEW.meeting_date,
        total_interactions = total_interactions + 1,
        first_interaction = COALESCE(first_interaction, NEW.meeting_date),
        updated_at = NOW()
    FROM (
        SELECT (jsonb_array_elements(NEW.attendees)->>'stakeholder_id')::UUID as sid
    ) attendee_ids
    WHERE s.id = attendee_ids.sid;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_stakeholder_interactions ON meeting_transcripts;
CREATE TRIGGER trigger_update_stakeholder_interactions
AFTER INSERT ON meeting_transcripts
FOR EACH ROW
WHEN (NEW.attendees IS NOT NULL AND jsonb_array_length(NEW.attendees) > 0)
EXECUTE FUNCTION update_stakeholder_interactions();

-- ============================================================================
-- DONE!
-- ============================================================================
