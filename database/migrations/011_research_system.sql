-- Migration: 011_research_system.sql
-- Description: Atlas Proactive Research System tables
-- Created: 2025-12-27

-- ============================================================================
-- RESEARCH TASKS TABLE
-- Tracks individual research tasks (scheduled or manual)
-- ============================================================================

CREATE TABLE IF NOT EXISTS research_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,

    -- Research definition
    topic VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    focus_area VARCHAR(100),  -- strategic_planning, finance_roi, governance_compliance, etc.
    research_type VARCHAR(50) DEFAULT 'scheduled',  -- scheduled, manual, gap_fill, anticipatory

    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),

    -- Context that drove this research
    context JSONB DEFAULT '{}',  -- stakeholders, concerns, opportunities, agent_gaps

    -- Results
    result_content TEXT,  -- The research output content
    result_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    result_summary TEXT,  -- Brief summary for quick reference

    -- Web search metadata
    web_sources JSONB DEFAULT '[]',  -- URLs and credibility tiers used

    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Indexes for research_tasks
CREATE INDEX IF NOT EXISTS idx_research_tasks_status ON research_tasks(status);
CREATE INDEX IF NOT EXISTS idx_research_tasks_client ON research_tasks(client_id);
CREATE INDEX IF NOT EXISTS idx_research_tasks_focus_area ON research_tasks(focus_area);
CREATE INDEX IF NOT EXISTS idx_research_tasks_created ON research_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_research_tasks_type ON research_tasks(research_type);

-- ============================================================================
-- RESEARCH SCHEDULE TABLE
-- Configures what research runs on which days
-- ============================================================================

CREATE TABLE IF NOT EXISTS research_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,  -- NULL = global schedule

    -- Schedule definition
    day_of_week INTEGER CHECK (day_of_week >= 0 AND day_of_week <= 6),  -- 0=Sunday, 1=Monday, etc.
    hour_utc INTEGER DEFAULT 6 CHECK (hour_utc >= 0 AND hour_utc <= 23),  -- Hour to run (UTC)

    -- Research focus
    focus_area VARCHAR(100) NOT NULL,
    description TEXT,

    -- Query template (can include placeholders like {industry}, {department})
    query_template TEXT,

    -- Control
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 5,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one focus area per day per client (or global)
    UNIQUE(client_id, day_of_week, focus_area)
);

-- Index for schedule lookups
CREATE INDEX IF NOT EXISTS idx_research_schedule_active ON research_schedule(is_active, day_of_week);
CREATE INDEX IF NOT EXISTS idx_research_schedule_client ON research_schedule(client_id);

-- ============================================================================
-- RESEARCH SOURCES TABLE
-- Tracks credibility of web sources for research
-- ============================================================================

CREATE TABLE IF NOT EXISTS research_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source identification
    domain VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),

    -- Credibility scoring
    credibility_tier INTEGER DEFAULT 3 CHECK (credibility_tier >= 1 AND credibility_tier <= 4),
    -- Tier 1: McKinsey, BCG, Gartner, HBR, MIT Sloan (cite directly)
    -- Tier 2: Big 4, major tech, academic (cite directly)
    -- Tier 3: Industry pubs, reputable news (verify claims)
    -- Tier 4: Blogs, vendor marketing (signals only)

    -- Categorization
    source_type VARCHAR(50),  -- consulting, academic, news, vendor, blog
    topics TEXT[],  -- Array of topic tags this source is good for

    -- Usage tracking
    times_cited INTEGER DEFAULT 0,
    last_cited_at TIMESTAMPTZ,

    -- Control
    is_blocked BOOLEAN DEFAULT FALSE,  -- Block unreliable sources
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for source lookups
CREATE INDEX IF NOT EXISTS idx_research_sources_domain ON research_sources(domain);
CREATE INDEX IF NOT EXISTS idx_research_sources_tier ON research_sources(credibility_tier);

-- ============================================================================
-- KNOWLEDGE GAPS TABLE
-- Tracks questions agents couldn't fully answer
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,

    -- Gap identification
    topic VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,  -- The original question or topic
    source_agent VARCHAR(50),  -- Which agent encountered this gap
    source_conversation_id UUID,  -- Reference to the conversation

    -- Gap analysis
    uncertainty_signals TEXT[],  -- Phrases that indicated uncertainty
    gap_type VARCHAR(50),  -- missing_data, outdated_info, no_benchmarks, etc.

    -- Resolution
    status VARCHAR(50) DEFAULT 'open',  -- open, researching, resolved, wont_fix
    resolution_task_id UUID REFERENCES research_tasks(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,

    -- Priority
    occurrence_count INTEGER DEFAULT 1,  -- How many times this gap was encountered
    priority INTEGER DEFAULT 5,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for knowledge gaps
CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_status ON knowledge_gaps(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_client ON knowledge_gaps(client_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_agent ON knowledge_gaps(source_agent);
CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_priority ON knowledge_gaps(priority DESC, occurrence_count DESC);

-- ============================================================================
-- AGENT TOPIC MAPPING TABLE
-- Defines which topics are relevant to which agents
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_topic_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    topic_keyword VARCHAR(100) NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    relevance_score FLOAT DEFAULT 1.0 CHECK (relevance_score >= 0 AND relevance_score <= 1),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(topic_keyword, agent_name)
);

-- Index for topic lookups
CREATE INDEX IF NOT EXISTS idx_agent_topic_mapping_topic ON agent_topic_mapping(topic_keyword);
CREATE INDEX IF NOT EXISTS idx_agent_topic_mapping_agent ON agent_topic_mapping(agent_name);

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Default global research schedule (NULL client_id = applies to all)
INSERT INTO research_schedule (client_id, day_of_week, focus_area, description, query_template, priority) VALUES
(NULL, 1, 'strategic_planning', 'Monday: C-suite engagement and governance patterns',
 'What are the latest best practices for C-suite AI governance and strategic planning? Include recent case studies from Fortune 500 companies.', 8),
(NULL, 2, 'finance_roi', 'Tuesday: Finance use cases and ROI benchmarks',
 'What are proven ROI benchmarks for AI implementation in Finance departments? Include specific metrics, payback periods, and case studies.', 8),
(NULL, 3, 'governance_compliance', 'Wednesday: IT governance and compliance frameworks',
 'What are current best practices for AI governance and compliance? Include regulatory updates, security frameworks, and vendor evaluation criteria.', 8),
(NULL, 4, 'change_management', 'Thursday: Change management and adoption patterns',
 'What does research say about successful AI adoption and change management? Include failure patterns, champion program best practices, and cultural change strategies.', 8),
(NULL, 5, 'weekly_synthesis', 'Friday: Weekly synthesis and emerging trends',
 'Synthesize the key GenAI developments from this week. Include major announcements, research publications, and emerging trends.', 7)
ON CONFLICT (client_id, day_of_week, focus_area) DO NOTHING;

-- Seed credible research sources (Tier 1 & 2)
INSERT INTO research_sources (domain, name, credibility_tier, source_type, topics) VALUES
-- Tier 1: Consulting firms and top research
('mckinsey.com', 'McKinsey & Company', 1, 'consulting', ARRAY['strategy', 'transformation', 'roi', 'adoption']),
('bcg.com', 'Boston Consulting Group', 1, 'consulting', ARRAY['strategy', 'transformation', 'innovation']),
('bain.com', 'Bain & Company', 1, 'consulting', ARRAY['strategy', 'operations', 'transformation']),
('gartner.com', 'Gartner', 1, 'research', ARRAY['technology', 'trends', 'vendors', 'governance']),
('forrester.com', 'Forrester Research', 1, 'research', ARRAY['technology', 'customer', 'digital']),
('hbr.org', 'Harvard Business Review', 1, 'academic', ARRAY['strategy', 'leadership', 'management', 'innovation']),
('sloanreview.mit.edu', 'MIT Sloan Management Review', 1, 'academic', ARRAY['strategy', 'technology', 'innovation', 'ai']),

-- Tier 2: Big 4 and major tech
('deloitte.com', 'Deloitte', 2, 'consulting', ARRAY['audit', 'tax', 'consulting', 'technology']),
('pwc.com', 'PwC', 2, 'consulting', ARRAY['audit', 'tax', 'consulting', 'transformation']),
('ey.com', 'Ernst & Young', 2, 'consulting', ARRAY['audit', 'tax', 'consulting', 'technology']),
('kpmg.com', 'KPMG', 2, 'consulting', ARRAY['audit', 'tax', 'consulting', 'technology']),
('accenture.com', 'Accenture', 2, 'consulting', ARRAY['technology', 'consulting', 'digital', 'operations']),
('anthropic.com', 'Anthropic', 2, 'vendor', ARRAY['ai', 'safety', 'claude', 'enterprise']),
('openai.com', 'OpenAI', 2, 'vendor', ARRAY['ai', 'gpt', 'enterprise', 'api']),
('microsoft.com', 'Microsoft', 2, 'vendor', ARRAY['ai', 'azure', 'copilot', 'enterprise']),
('google.com', 'Google', 2, 'vendor', ARRAY['ai', 'cloud', 'gemini', 'enterprise']),

-- Tier 3: Industry publications and news
('wsj.com', 'Wall Street Journal', 3, 'news', ARRAY['business', 'technology', 'finance']),
('ft.com', 'Financial Times', 3, 'news', ARRAY['business', 'technology', 'finance']),
('reuters.com', 'Reuters', 3, 'news', ARRAY['business', 'technology', 'finance']),
('techcrunch.com', 'TechCrunch', 3, 'news', ARRAY['technology', 'startups', 'ai']),
('wired.com', 'Wired', 3, 'news', ARRAY['technology', 'ai', 'culture']),
('venturebeat.com', 'VentureBeat', 3, 'news', ARRAY['ai', 'technology', 'enterprise'])
ON CONFLICT (domain) DO NOTHING;

-- Seed agent topic mapping
INSERT INTO agent_topic_mapping (topic_keyword, agent_name, relevance_score) VALUES
-- ROI and Finance topics
('roi', 'fortuna', 1.0),
('roi', 'strategist', 0.8),
('finance', 'fortuna', 1.0),
('budget', 'fortuna', 1.0),
('cost', 'fortuna', 0.9),
('payback', 'fortuna', 1.0),
('sox', 'fortuna', 0.9),
('sox', 'guardian', 0.7),

-- Compliance and Governance topics
('compliance', 'guardian', 1.0),
('compliance', 'counselor', 0.8),
('governance', 'guardian', 1.0),
('governance', 'strategist', 0.7),
('security', 'guardian', 1.0),
('security', 'architect', 0.8),
('audit', 'guardian', 0.9),
('audit', 'fortuna', 0.7),

-- Legal topics
('contract', 'counselor', 1.0),
('liability', 'counselor', 1.0),
('ip', 'counselor', 1.0),
('privacy', 'counselor', 1.0),
('privacy', 'guardian', 0.7),
('gdpr', 'counselor', 0.9),
('gdpr', 'guardian', 0.8),

-- Change Management topics
('change_management', 'sage', 1.0),
('change_management', 'catalyst', 0.9),
('adoption', 'sage', 1.0),
('adoption', 'scholar', 0.8),
('training', 'scholar', 1.0),
('training', 'sage', 0.7),
('culture', 'sage', 0.9),
('culture', 'catalyst', 0.8),
('resistance', 'sage', 1.0),
('champion', 'sage', 0.9),
('champion', 'scholar', 0.8),

-- Architecture and Technical topics
('architecture', 'architect', 1.0),
('architecture', 'guardian', 0.6),
('integration', 'architect', 1.0),
('integration', 'operator', 0.7),
('mlops', 'architect', 1.0),
('api', 'architect', 0.9),
('rag', 'architect', 1.0),

-- Operations topics
('process', 'operator', 1.0),
('automation', 'operator', 1.0),
('automation', 'architect', 0.7),
('workflow', 'operator', 0.9),
('metrics', 'operator', 0.8),
('metrics', 'fortuna', 0.7),

-- Innovation topics
('innovation', 'pioneer', 1.0),
('emerging', 'pioneer', 1.0),
('trend', 'pioneer', 0.9),
('trend', 'atlas', 0.8),
('hype', 'pioneer', 0.9),

-- Strategy topics
('strategy', 'strategist', 1.0),
('executive', 'strategist', 1.0),
('stakeholder', 'strategist', 0.9),
('politics', 'strategist', 0.8),

-- Communication topics
('communication', 'catalyst', 1.0),
('messaging', 'catalyst', 1.0),
('messaging', 'echo', 0.8),
('voice', 'echo', 1.0),
('brand', 'echo', 1.0),

-- Systems thinking topics
('systems', 'nexus', 1.0),
('interconnection', 'nexus', 1.0),
('feedback', 'nexus', 0.9),
('unintended', 'nexus', 1.0)
ON CONFLICT (topic_keyword, agent_name) DO NOTHING;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE research_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_gaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_topic_mapping ENABLE ROW LEVEL SECURITY;

-- Research tasks: users can see tasks for their clients (via users.client_id)
CREATE POLICY "Users can view research tasks for their clients" ON research_tasks
    FOR SELECT USING (
        client_id IN (
            SELECT users.client_id FROM users
            WHERE users.id = auth.uid()
        )
        OR client_id IS NULL  -- Global tasks visible to all
    );

-- Research schedule: users can view schedules for their clients + global
CREATE POLICY "Users can view research schedules" ON research_schedule
    FOR SELECT USING (
        client_id IN (
            SELECT users.client_id FROM users
            WHERE users.id = auth.uid()
        )
        OR client_id IS NULL  -- Global schedule visible to all
    );

-- Research sources: all users can view (reference data)
CREATE POLICY "All users can view research sources" ON research_sources
    FOR SELECT USING (true);

-- Knowledge gaps: users can see gaps for their clients
CREATE POLICY "Users can view knowledge gaps for their clients" ON knowledge_gaps
    FOR SELECT USING (
        client_id IN (
            SELECT users.client_id FROM users
            WHERE users.id = auth.uid()
        )
        OR client_id IS NULL  -- Allow null client_id gaps to be visible
    );

-- Agent topic mapping: all users can view (reference data)
CREATE POLICY "All users can view agent topic mapping" ON agent_topic_mapping
    FOR SELECT USING (true);

-- Service role policies for backend operations
CREATE POLICY "Service role full access to research_tasks" ON research_tasks
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to research_schedule" ON research_schedule
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to research_sources" ON research_sources
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to knowledge_gaps" ON knowledge_gaps
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to agent_topic_mapping" ON agent_topic_mapping
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to get today's scheduled research topics
CREATE OR REPLACE FUNCTION get_todays_research_schedule(p_client_id UUID DEFAULT NULL)
RETURNS TABLE (
    schedule_id UUID,
    focus_area VARCHAR(100),
    description TEXT,
    query_template TEXT,
    priority INTEGER,
    is_global BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        rs.id as schedule_id,
        rs.focus_area,
        rs.description,
        rs.query_template,
        rs.priority,
        (rs.client_id IS NULL) as is_global
    FROM research_schedule rs
    WHERE rs.is_active = TRUE
      AND rs.day_of_week = EXTRACT(DOW FROM NOW())
      AND (rs.client_id = p_client_id OR rs.client_id IS NULL)
    ORDER BY rs.priority DESC, rs.client_id NULLS LAST;
END;
$$ LANGUAGE plpgsql;

-- Function to get agents relevant to a topic
CREATE OR REPLACE FUNCTION get_agents_for_topic(p_topic VARCHAR)
RETURNS TABLE (
    agent_name VARCHAR(50),
    relevance_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        atm.agent_name,
        atm.relevance_score
    FROM agent_topic_mapping atm
    WHERE atm.topic_keyword = LOWER(p_topic)
    ORDER BY atm.relevance_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to increment gap occurrence count
CREATE OR REPLACE FUNCTION increment_gap_occurrence(p_gap_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE knowledge_gaps
    SET occurrence_count = occurrence_count + 1,
        updated_at = NOW()
    WHERE id = p_gap_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get open knowledge gaps by priority
CREATE OR REPLACE FUNCTION get_priority_knowledge_gaps(p_client_id UUID, p_limit INTEGER DEFAULT 10)
RETURNS TABLE (
    gap_id UUID,
    topic VARCHAR(255),
    question TEXT,
    source_agent VARCHAR(50),
    occurrence_count INTEGER,
    priority INTEGER,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        kg.id as gap_id,
        kg.topic,
        kg.question,
        kg.source_agent,
        kg.occurrence_count,
        kg.priority,
        kg.created_at
    FROM knowledge_gaps kg
    WHERE kg.client_id = p_client_id
      AND kg.status = 'open'
    ORDER BY kg.priority DESC, kg.occurrence_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE research_tasks IS 'Tracks individual research tasks executed by Atlas';
COMMENT ON TABLE research_schedule IS 'Configures daily/weekly research schedule';
COMMENT ON TABLE research_sources IS 'Credibility ratings for web sources';
COMMENT ON TABLE knowledge_gaps IS 'Questions that agents could not fully answer';
COMMENT ON TABLE agent_topic_mapping IS 'Maps topics to relevant agents for knowledge distribution';
