-- Migration 053: Department KPIs table for Strategy dashboard
-- Replaces hardcoded MOCK_KPIS in StrategyContent.tsx with database-backed KPIs

-- ============================================================================
-- TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS department_kpis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    department VARCHAR(100) NOT NULL,
    kpi_name VARCHAR(255) NOT NULL,
    description TEXT,
    current_value NUMERIC,
    target_value NUMERIC NOT NULL,
    unit VARCHAR(50) NOT NULL,
    trend VARCHAR(10) DEFAULT 'flat' CHECK (trend IN ('up', 'down', 'flat')),
    trend_percentage NUMERIC DEFAULT 0,
    status VARCHAR(10) DEFAULT 'yellow' CHECK (status IN ('green', 'yellow', 'red')),
    linked_objective_id VARCHAR(50),
    fiscal_year VARCHAR(10) DEFAULT 'FY27',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_dept_kpis_client ON department_kpis(client_id);
CREATE INDEX idx_dept_kpis_department ON department_kpis(department);
CREATE INDEX idx_dept_kpis_fy ON department_kpis(fiscal_year);

-- ============================================================================
-- UPDATED_AT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION update_department_kpis_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS department_kpis_updated_at_trigger ON department_kpis;
CREATE TRIGGER department_kpis_updated_at_trigger
    BEFORE UPDATE ON department_kpis
    FOR EACH ROW
    EXECUTE FUNCTION update_department_kpis_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE department_kpis ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their client KPIs"
    ON department_kpis FOR SELECT
    USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can manage their client KPIs"
    ON department_kpis FOR ALL
    USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

-- ============================================================================
-- SEED DATA (matches existing MOCK_KPIS for seamless transition)
-- Uses the default client_id from clients table
-- ============================================================================

DO $$
DECLARE
    default_client UUID;
BEGIN
    SELECT id INTO default_client FROM clients LIMIT 1;

    IF default_client IS NULL THEN
        RAISE NOTICE 'No client found, skipping seed data';
        RETURN;
    END IF;

    -- Legal
    INSERT INTO department_kpis (client_id, department, kpi_name, description, current_value, target_value, unit, trend, trend_percentage, status, linked_objective_id, fiscal_year, sort_order)
    VALUES
    (default_client, 'Legal', 'Contract Review Cycle Time', 'Days from contract submission to completion (target: 90% reduction).', 19, 2, 'days', 'down', 10, 'red', '2', 'FY27', 1),
    (default_client, 'Legal', 'Attorney Strategic Work Time', 'Time on high-value strategic work vs. admin.', 20, 40, '%', 'up', 5, 'yellow', '3', 'FY27', 2),

    -- Finance
    (default_client, 'Finance', 'Monthly Close Cycle', 'Days to complete monthly financial close.', 15, 8, 'days', 'down', 10, 'yellow', '2', 'FY27', 1),
    (default_client, 'Finance', 'Invoice Processing Time', 'Minutes per invoice via AI OCR.', 15, 3, 'min/invoice', 'down', 15, 'yellow', '3', 'FY27', 2),

    -- People
    (default_client, 'People', 'Employee Retention Rate', 'Annual employee retention (target: 98%).', 92, 98, '%', 'up', 2, 'yellow', '4', 'FY27', 1),
    (default_client, 'People', 'People Ticket Deflection', 'Questions resolved via AI chatbot.', 10, 40, '%', 'up', 5, 'yellow', '3', 'FY27', 2),

    -- IT
    (default_client, 'IT', 'AI Agent Success Rate', 'Built agents reaching production.', 4, 80, '%', 'up', 5, 'red', '3', 'FY27', 1),
    (default_client, 'IT', 'Production Agents', 'AI agents deployed to production.', 15, 50, 'agents', 'up', 10, 'yellow', '3', 'FY27', 2),

    -- Revenue Ops
    (default_client, 'Revenue Ops', 'Ticket Escalation Rate', 'Sales questions requiring human escalation.', 75, 25, '%', 'down', 5, 'red', '2', 'FY27', 1),
    (default_client, 'Revenue Ops', 'MEDDIC Field Completion', 'Opportunities with complete MEDDIC data.', 60, 90, '%', 'up', 10, 'yellow', '1', 'FY27', 2);

    RAISE NOTICE 'Seeded 10 department KPIs for client %', default_client;
END $$;
