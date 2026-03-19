-- 083_strategic_goals.sql
-- Strategic Goals table + department_kpis linked_goal_id + seed data

-- 1. Create strategic_goals table
CREATE TABLE IF NOT EXISTS strategic_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL CHECK (level IN ('company', 'team')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    department VARCHAR(100),
    owner VARCHAR(255),
    target_metric VARCHAR(255),
    current_value NUMERIC,
    target_value NUMERIC,
    unit VARCHAR(50),
    status VARCHAR(20) DEFAULT 'on_track' CHECK (status IN ('on_track', 'at_risk', 'behind', 'achieved')),
    priority INTEGER DEFAULT 0,
    parent_goal_id UUID REFERENCES strategic_goals(id) ON DELETE SET NULL,
    fiscal_year VARCHAR(10) DEFAULT 'FY27',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_strategic_goals_client_id ON strategic_goals(client_id);
CREATE INDEX IF NOT EXISTS idx_strategic_goals_level ON strategic_goals(level);
CREATE INDEX IF NOT EXISTS idx_strategic_goals_fiscal_year ON strategic_goals(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_strategic_goals_parent ON strategic_goals(parent_goal_id);

-- RLS
ALTER TABLE strategic_goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their client goals"
    ON strategic_goals FOR SELECT
    USING (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can insert goals for their client"
    ON strategic_goals FOR INSERT
    WITH CHECK (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can update their client goals"
    ON strategic_goals FOR UPDATE
    USING (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can delete their client goals"
    ON strategic_goals FOR DELETE
    USING (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

-- Service role bypass
CREATE POLICY "Service role full access to strategic_goals"
    ON strategic_goals FOR ALL
    USING (auth.role() = 'service_role');

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_strategic_goals_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_strategic_goals_updated_at
    BEFORE UPDATE ON strategic_goals
    FOR EACH ROW
    EXECUTE FUNCTION update_strategic_goals_updated_at();

-- 2. Add linked_goal_id to department_kpis
ALTER TABLE department_kpis
    ADD COLUMN IF NOT EXISTS linked_goal_id UUID REFERENCES strategic_goals(id) ON DELETE SET NULL;

-- 3. Seed FY26 + FY27 company objectives and backfill KPI links
DO $$
DECLARE
    v_client_id UUID := '00000000-0000-0000-0000-000000000001';
    v_fy26_1 UUID; v_fy26_2 UUID; v_fy26_3 UUID; v_fy26_4 UUID;
    v_fy27_1 UUID; v_fy27_2 UUID; v_fy27_3 UUID; v_fy27_4 UUID;
BEGIN
    -- FY26 Goals
    INSERT INTO strategic_goals (client_id, level, title, description, target_metric, current_value, target_value, unit, status, priority, fiscal_year)
    VALUES (v_client_id, 'company', 'Market Positioning',
        'Re-establish Contentful as a thought leader and disruptor in the broader DXP category, with a compelling near-term value proposition, and an expansive vision around content operations that co-opts the GenAI value proposition.',
        'DXP category leadership', NULL, 100, '%', 'on_track', 1, 'FY26')
    RETURNING id INTO v_fy26_1;

    INSERT INTO strategic_goals (client_id, level, title, description, target_metric, current_value, target_value, unit, status, priority, fiscal_year)
    VALUES (v_client_id, 'company', 'Sales Productivity',
        'Accelerate sales productivity to approach industry benchmarks, exceed pipeline and bookings targets, and support increased S&M investment in H2 to re-accelerate revenue growth in FY27 and FY28.',
        'Pipeline vs target', 113, 100, '%', 'achieved', 2, 'FY26')
    RETURNING id INTO v_fy26_2;

    INSERT INTO strategic_goals (client_id, level, title, description, target_metric, current_value, target_value, unit, status, priority, fiscal_year)
    VALUES (v_client_id, 'company', 'Product Innovation',
        'Accelerate velocity of new product and feature introductions that reinforce platform/ecosystem leadership, provide differentiated expansion into DXP category, and capture net new spend categories through GenAI capabilities.',
        'EXO/GenAI milestones', 5, 8, 'milestones', 'on_track', 3, 'FY26')
    RETURNING id INTO v_fy26_3;

    INSERT INTO strategic_goals (client_id, level, title, description, target_metric, current_value, target_value, unit, status, priority, fiscal_year)
    VALUES (v_client_id, 'company', 'Culture',
        'Create a winning culture based on transparency, empowerment, risk taking and performance. Values: Relentless Customer Focus, Own It, Be Bold, Win Together.',
        'Employee retention', 92, 98, '%', 'on_track', 4, 'FY26')
    RETURNING id INTO v_fy26_4;

    -- FY27 Goals
    INSERT INTO strategic_goals (client_id, level, title, description, target_metric, current_value, target_value, unit, status, priority, fiscal_year)
    VALUES (v_client_id, 'company', 'Market Leadership',
        'Transform perceptions of Contentful from a technical CMS tool for developers into a strategic solution partner for CMOs and CTOs. Create a differentiated narrative around our product vision that capitalizes on emerging AI disruptions and creates an aura of industry leadership.',
        'CMO/CTO perception shift', NULL, 100, '%', 'on_track', 1, 'FY27')
    RETURNING id INTO v_fy27_1;

    INSERT INTO strategic_goals (client_id, level, title, description, target_metric, current_value, target_value, unit, status, priority, fiscal_year)
    VALUES (v_client_id, 'company', 'Cost-Efficient GTM Growth',
        'Build upon FY26 productivity improvements to exceed all FY top line targets, achieve a cost-to-book ratio under 2.0, and improve FY26 gross retention metrics.',
        'Cost-to-book ratio', NULL, 2.0, 'ratio', 'on_track', 2, 'FY27')
    RETURNING id INTO v_fy27_2;

    INSERT INTO strategic_goals (client_id, level, title, description, target_metric, current_value, target_value, unit, status, priority, fiscal_year)
    VALUES (v_client_id, 'company', 'Product Innovation',
        'Introduce new platform and AI-powered experience orchestration capabilities that leapfrog the market. Democratize the value of experimentation, p13n, and content analytics. Develop a clear product strategy behind the agentic web.',
        'EXO/Agentic Web milestones', NULL, 8, 'milestones', 'on_track', 3, 'FY27')
    RETURNING id INTO v_fy27_3;

    INSERT INTO strategic_goals (client_id, level, title, description, target_metric, current_value, target_value, unit, status, priority, fiscal_year)
    VALUES (v_client_id, 'company', 'Culture',
        'Create a winning culture based on transparency, empowerment, risk taking and performance. Target: 98% employee retention.',
        'Employee retention', NULL, 98, '%', 'on_track', 4, 'FY27')
    RETURNING id INTO v_fy27_4;

    -- 4. Backfill linked_goal_id on department_kpis
    UPDATE department_kpis SET linked_goal_id = v_fy27_1
    WHERE client_id = v_client_id AND linked_objective_id = '1';

    UPDATE department_kpis SET linked_goal_id = v_fy27_2
    WHERE client_id = v_client_id AND linked_objective_id = '2';

    UPDATE department_kpis SET linked_goal_id = v_fy27_3
    WHERE client_id = v_client_id AND linked_objective_id = '3';

    UPDATE department_kpis SET linked_goal_id = v_fy27_4
    WHERE client_id = v_client_id AND linked_objective_id = '4';
END;
$$;
