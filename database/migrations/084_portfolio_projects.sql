-- 084_portfolio_projects.sql
-- AI Project Portfolio dashboard - lightweight project registry

CREATE TABLE IF NOT EXISTS portfolio_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(100) NOT NULL,
    owner VARCHAR(255),
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'in_progress', 'completed')),
    start_date DATE,
    effort VARCHAR(10) CHECK (effort IN ('low', 'medium', 'high')),
    investment VARCHAR(20) CHECK (investment IN ('0-1k', '1k-5k', '5k-15k', '15k-25k', '25k+')),
    business_value VARCHAR(20) CHECK (business_value IN ('low', 'medium', 'high', 'critical')),
    tools_platform TEXT,
    category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_projects_client_id ON portfolio_projects(client_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_projects_department ON portfolio_projects(department);
CREATE INDEX IF NOT EXISTS idx_portfolio_projects_status ON portfolio_projects(status);

-- RLS
ALTER TABLE portfolio_projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their client portfolio projects"
    ON portfolio_projects FOR SELECT
    USING (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can insert portfolio projects for their client"
    ON portfolio_projects FOR INSERT
    WITH CHECK (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can update their client portfolio projects"
    ON portfolio_projects FOR UPDATE
    USING (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Users can delete their client portfolio projects"
    ON portfolio_projects FOR DELETE
    USING (client_id IN (
        SELECT client_id FROM users WHERE id = auth.uid()
    ));

-- Service role bypass
CREATE POLICY "Service role full access to portfolio_projects"
    ON portfolio_projects FOR ALL
    USING (auth.role() = 'service_role');

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_portfolio_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_portfolio_projects_updated_at
    BEFORE UPDATE ON portfolio_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_portfolio_projects_updated_at();
