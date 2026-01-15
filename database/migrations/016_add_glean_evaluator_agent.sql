-- Migration: Add Glean Evaluator Agent ("Can We Glean This?") and Connector Registry
-- Version: 016
-- Date: 2025-01-15
-- Description:
--   Adds the Glean Evaluator internal enablement agent for assessing
--   whether Glean is the appropriate tool for a given PRD, discussion,
--   or application request. Evaluates integration requirements, data
--   access, scale fit, and alternative recommendations.
--
--   Also creates connector registry tables for tracking:
--   - Out-of-box Glean connectors (reference data)
--   - Custom connectors built by Contentful
--   - Connector requests/gaps for prioritization

-- ============================================================================
-- STEP 1: Insert Glean Evaluator agent
-- ============================================================================
INSERT INTO agents (name, display_name, description, is_active, capabilities, config)
VALUES (
    'glean_evaluator',
    'Can We Glean This?',
    'Glean platform fit assessment agent. Analyzes PRDs, discussions, and application requests to determine if Glean is the appropriate solution. Evaluates integration requirements, data access patterns, scale fit, security needs, and recommends alternatives when Glean is not ideal.',
    true,
    ARRAY[
        'glean_fit_assessment',
        'integration_analysis',
        'build_vs_buy_evaluation',
        'alternative_recommendations',
        'cost_benefit_analysis',
        'security_requirements_mapping',
        'data_source_compatibility'
    ],
    jsonb_build_object(
        'agent_type', 'internal_enablement',
        'domain', 'platform_evaluation',
        'kb_access', 'all',
        'responds_to', ARRAY['glean', 'can we', 'should we use', 'platform fit', 'build or buy'],
        'handoffs', ARRAY['architect', 'guardian', 'capital']
    )
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    capabilities = EXCLUDED.capabilities,
    config = agents.config || EXCLUDED.config;

-- ============================================================================
-- STEP 2: Create initial instruction version for Glean Evaluator
-- ============================================================================
INSERT INTO agent_instruction_versions (
    agent_id,
    version_number,
    instructions,
    description,
    is_active
)
SELECT
    id,
    '1',
    '-- Glean Evaluator instructions loaded from XML file: backend/system_instructions/agents/glean_evaluator.xml',
    'Initial Glean Evaluator agent creation - platform fit assessment for Glean',
    true
FROM agents
WHERE name = 'glean_evaluator'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- STEP 3: Create Glean Connector Registry
-- ============================================================================

-- Connector types: oob (out-of-box), custom (we built), requested (gap/wish)
CREATE TYPE glean_connector_type AS ENUM ('oob', 'custom', 'requested');

-- Connector status for custom/requested connectors
CREATE TYPE glean_connector_status AS ENUM (
    'available',        -- Ready to use
    'in_development',   -- Currently being built
    'planned',          -- On roadmap
    'requested',        -- Gap identified, not yet planned
    'not_feasible'      -- Evaluated and determined not possible
);

-- Main connector registry table
CREATE TABLE IF NOT EXISTS glean_connectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    connector_type glean_connector_type NOT NULL,
    status glean_connector_status NOT NULL DEFAULT 'available',
    category VARCHAR(100), -- e.g., 'productivity', 'engineering', 'hr', 'sales'
    description TEXT,
    documentation_url TEXT,
    -- For custom connectors: who built it, when
    developed_by VARCHAR(200),
    development_date DATE,
    -- For OOB connectors: Glean's tier/complexity
    glean_tier VARCHAR(50), -- 'standard', 'premium', 'enterprise'
    setup_complexity VARCHAR(50), -- 'simple', 'moderate', 'complex'
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, connector_type)
);

-- Track connector requests/gaps from assessments
CREATE TABLE IF NOT EXISTS glean_connector_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_name VARCHAR(200) NOT NULL,
    requested_by VARCHAR(200),
    request_source TEXT, -- PRD name, meeting room ID, or description
    use_case TEXT NOT NULL,
    business_justification TEXT,
    priority VARCHAR(50) DEFAULT 'medium', -- 'critical', 'high', 'medium', 'low'
    request_count INTEGER DEFAULT 1, -- Increment when same connector requested again
    status glean_connector_status DEFAULT 'requested',
    -- Link to connector if it gets built
    connector_id UUID REFERENCES glean_connectors(id),
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_glean_connectors_type ON glean_connectors(connector_type);
CREATE INDEX IF NOT EXISTS idx_glean_connectors_category ON glean_connectors(category);
CREATE INDEX IF NOT EXISTS idx_glean_connector_requests_status ON glean_connector_requests(status);
CREATE INDEX IF NOT EXISTS idx_glean_connector_requests_priority ON glean_connector_requests(priority);

-- ============================================================================
-- STEP 4: Seed Out-of-Box Glean Connectors
-- ============================================================================

INSERT INTO glean_connectors (name, display_name, connector_type, status, category, glean_tier, setup_complexity) VALUES
-- ============================================================================
-- PRODUCTIVITY & COMMUNICATION (Core collaboration tools)
-- ============================================================================
('google_workspace_sso', 'Google Workspace SSO', 'oob', 'available', 'sso', 'standard', 'simple'),
('slack', 'Slack', 'oob', 'available', 'communication', 'standard', 'simple'),
('microsoft_teams', 'Microsoft Teams', 'oob', 'available', 'communication', 'standard', 'simple'),
('microsoft_365', 'Microsoft 365', 'oob', 'available', 'productivity', 'standard', 'simple'),
('zoom', 'Zoom', 'oob', 'available', 'communication', 'standard', 'moderate'),
('gmail', 'Gmail', 'oob', 'available', 'communication', 'standard', 'simple'),
('microsoft_outlook', 'Microsoft Outlook', 'oob', 'available', 'communication', 'standard', 'simple'),
('google_chat', 'Google Chat', 'oob', 'available', 'communication', 'standard', 'simple'),
('google_calendar', 'Google Calendar', 'oob', 'available', 'productivity', 'standard', 'simple'),
('facebook_workplace', 'Facebook Workplace', 'oob', 'available', 'communication', 'standard', 'moderate'),
('pingboard', 'Pingboard', 'oob', 'available', 'communication', 'standard', 'simple'),
('lumapps', 'LumApps', 'oob', 'available', 'communication', 'standard', 'moderate'),
('interact', 'Interact', 'oob', 'available', 'communication', 'standard', 'moderate'),
('fellow', 'Fellow', 'oob', 'available', 'productivity', 'standard', 'simple'),

-- ============================================================================
-- KNOWLEDGE MANAGEMENT & DOCUMENTATION
-- ============================================================================
('confluence', 'Confluence', 'oob', 'available', 'knowledge', 'standard', 'simple'),
('notion', 'Notion', 'oob', 'available', 'knowledge', 'standard', 'simple'),
('microsoft_sharepoint', 'Microsoft SharePoint', 'oob', 'available', 'knowledge', 'standard', 'moderate'),
('microsoft_onenote', 'Microsoft OneNote', 'oob', 'available', 'knowledge', 'standard', 'simple'),
('coda', 'Coda', 'oob', 'available', 'knowledge', 'standard', 'simple'),
('quip', 'Quip', 'oob', 'available', 'knowledge', 'standard', 'simple'),
('airtable', 'Airtable', 'oob', 'available', 'knowledge', 'standard', 'simple'),
('google_sites', 'Google Sites', 'oob', 'available', 'knowledge', 'standard', 'simple'),
('evernote', 'Evernote', 'oob', 'available', 'knowledge', 'standard', 'simple'),
('guru', 'Guru', 'oob', 'available', 'knowledge', 'standard', 'simple'),
('haystack', 'Haystack', 'oob', 'available', 'knowledge', 'standard', 'moderate'),
('mindtouch', 'Mindtouch', 'oob', 'available', 'knowledge', 'standard', 'moderate'),
('screenssteps', 'ScreenSteps', 'oob', 'available', 'knowledge', 'standard', 'simple'),

-- ============================================================================
-- STORAGE & FILES
-- ============================================================================
('box', 'Box', 'oob', 'available', 'storage', 'standard', 'simple'),
('dropbox', 'Dropbox', 'oob', 'available', 'storage', 'standard', 'simple'),
('google_drive', 'Google Drive', 'oob', 'available', 'storage', 'standard', 'simple'),
('microsoft_onedrive', 'Microsoft OneDrive', 'oob', 'available', 'storage', 'standard', 'simple'),
('egnyte', 'Egnyte', 'oob', 'available', 'storage', 'standard', 'moderate'),
('amazon_s3', 'Amazon S3', 'oob', 'available', 'storage', 'standard', 'moderate'),
('google_cloud_storage', 'Google Cloud Storage', 'oob', 'available', 'storage', 'standard', 'moderate'),
('azure_file_share', 'Azure File Share', 'oob', 'available', 'storage', 'standard', 'moderate'),
('file_upload', 'File Upload', 'oob', 'available', 'storage', 'standard', 'simple'),

-- ============================================================================
-- ENGINEERING & DEVOPS
-- ============================================================================
('github', 'GitHub', 'oob', 'available', 'engineering', 'standard', 'simple'),
('gitlab', 'GitLab', 'oob', 'available', 'engineering', 'standard', 'simple'),
('bitbucket', 'Bitbucket', 'oob', 'available', 'engineering', 'standard', 'simple'),
('azure_devops', 'Azure DevOps', 'oob', 'available', 'engineering', 'standard', 'moderate'),
('jira', 'Jira', 'oob', 'available', 'engineering', 'standard', 'simple'),
('linear', 'Linear', 'oob', 'available', 'engineering', 'standard', 'simple'),
('phabricator', 'Phabricator', 'oob', 'available', 'engineering', 'standard', 'moderate'),
('jenkins', 'Jenkins', 'oob', 'available', 'engineering', 'standard', 'moderate'),
('jfrog', 'JFrog', 'oob', 'available', 'engineering', 'standard', 'moderate'),
('datadog', 'Datadog', 'oob', 'available', 'engineering', 'standard', 'moderate'),
('pagerduty', 'PagerDuty', 'oob', 'available', 'engineering', 'standard', 'simple'),
('opsgenie', 'Opsgenie', 'oob', 'available', 'engineering', 'standard', 'simple'),
('rootly', 'Rootly', 'oob', 'available', 'engineering', 'standard', 'simple'),
('google_cloud_platform', 'Google Cloud Platform', 'oob', 'available', 'engineering', 'enterprise', 'complex'),

-- ============================================================================
-- PROJECT MANAGEMENT
-- ============================================================================
('asana', 'Asana', 'oob', 'available', 'project_management', 'standard', 'simple'),
('monday', 'Monday.com', 'oob', 'available', 'project_management', 'standard', 'simple'),
('aha', 'Aha!', 'oob', 'available', 'project_management', 'standard', 'moderate'),
('procore', 'Procore', 'oob', 'available', 'project_management', 'enterprise', 'complex'),
('harvest', 'Harvest', 'oob', 'available', 'project_management', 'standard', 'simple'),
('ironclad', 'Ironclad', 'oob', 'available', 'project_management', 'standard', 'moderate'),

-- ============================================================================
-- SALES & CRM
-- ============================================================================
('salesforce', 'Salesforce', 'oob', 'available', 'sales', 'standard', 'moderate'),
('hubspot', 'HubSpot', 'oob', 'available', 'sales', 'standard', 'simple'),
('gong', 'Gong', 'oob', 'available', 'sales', 'premium', 'moderate'),
('microsoft_dynamics_365', 'Microsoft Dynamics 365', 'oob', 'available', 'sales', 'enterprise', 'complex'),
('netsuite', 'NetSuite', 'oob', 'available', 'sales', 'enterprise', 'complex'),
('affinity', 'Affinity', 'oob', 'available', 'sales', 'standard', 'simple'),

-- ============================================================================
-- MARKETING & CONTENT
-- ============================================================================
('marketo', 'Marketo', 'oob', 'available', 'marketing', 'premium', 'complex'),
('seismic', 'Seismic', 'oob', 'available', 'marketing', 'premium', 'moderate'),
('highspot', 'Highspot', 'oob', 'available', 'marketing', 'premium', 'moderate'),
('bynder', 'Bynder', 'oob', 'available', 'marketing', 'standard', 'moderate'),
('loopio', 'Loopio', 'oob', 'available', 'marketing', 'standard', 'moderate'),
('klue', 'Klue', 'oob', 'available', 'marketing', 'standard', 'moderate'),

-- ============================================================================
-- HR & PEOPLE
-- ============================================================================
('workday', 'Workday', 'oob', 'available', 'hr', 'enterprise', 'complex'),
('bamboohr', 'BambooHR', 'oob', 'available', 'hr', 'standard', 'simple'),
('greenhouse', 'Greenhouse', 'oob', 'available', 'hr', 'standard', 'simple'),
('fifteen_five', '15Five', 'oob', 'available', 'hr', 'standard', 'simple'),

-- ============================================================================
-- SUPPORT & SERVICE
-- ============================================================================
('zendesk', 'Zendesk', 'oob', 'available', 'support', 'standard', 'simple'),
('servicenow', 'ServiceNow', 'oob', 'available', 'support', 'enterprise', 'complex'),
('freshservice', 'Freshservice', 'oob', 'available', 'support', 'standard', 'simple'),
('nice_cxone', 'Nice CXone', 'oob', 'available', 'support', 'enterprise', 'complex'),
('insided', 'InSided', 'oob', 'available', 'support', 'standard', 'moderate'),

-- ============================================================================
-- LEARNING & ENABLEMENT
-- ============================================================================
('docebo', 'Docebo', 'oob', 'available', 'learning', 'standard', 'moderate'),
('lessonly', 'Lessonly', 'oob', 'available', 'learning', 'standard', 'simple'),
('panopto', 'Panopto', 'oob', 'available', 'learning', 'standard', 'moderate'),
('saleshood', 'SalesHood', 'oob', 'available', 'learning', 'standard', 'moderate'),
('guidde', 'Guidde', 'oob', 'available', 'learning', 'standard', 'simple'),
('plusplus', 'PlusPlus', 'oob', 'available', 'learning', 'standard', 'simple'),
('mindtickle', 'Mindtickle', 'oob', 'available', 'learning', 'premium', 'moderate'),

-- ============================================================================
-- DATA & ANALYTICS
-- ============================================================================
('databricks', 'Databricks', 'oob', 'available', 'data', 'enterprise', 'complex'),
('datastax', 'Datastax', 'oob', 'available', 'data', 'enterprise', 'complex'),
('looker_studio', 'Looker Studio', 'oob', 'available', 'data', 'premium', 'moderate'),

-- ============================================================================
-- DESIGN & COLLABORATION
-- ============================================================================
('miro', 'Miro', 'oob', 'available', 'design', 'standard', 'simple'),
('invision', 'InVision', 'oob', 'available', 'design', 'standard', 'simple'),

-- ============================================================================
-- PROCUREMENT & LEGAL
-- ============================================================================
('ariba', 'Ariba', 'oob', 'available', 'procurement', 'enterprise', 'complex'),
('coupa', 'Coupa', 'oob', 'available', 'procurement', 'enterprise', 'complex'),
('docusign', 'DocuSign', 'oob', 'available', 'legal', 'standard', 'moderate'),
('onetrust', 'OneTrust', 'oob', 'available', 'legal', 'enterprise', 'complex'),

-- ============================================================================
-- LIFE SCIENCES / SPECIALIZED
-- ============================================================================
('benchling', 'Benchling', 'oob', 'available', 'life_sciences', 'enterprise', 'complex'),
('adobe_experience_manager', 'Adobe Experience Manager', 'oob', 'available', 'content', 'enterprise', 'complex'),

-- ============================================================================
-- SINGLE SIGN-ON (SSO) PROVIDERS
-- ============================================================================
('azure_sso', 'Azure SSO', 'oob', 'available', 'sso', 'standard', 'simple'),
('okta', 'Okta', 'oob', 'available', 'sso', 'standard', 'simple'),
('microsoft_entra_id', 'Microsoft Entra ID', 'oob', 'available', 'sso', 'standard', 'simple'),
('onelogin', 'OneLogin', 'oob', 'available', 'sso', 'standard', 'simple'),
('jumpcloud', 'Jumpcloud', 'oob', 'available', 'sso', 'standard', 'simple'),
('keycloak', 'Keycloak', 'oob', 'available', 'sso', 'standard', 'moderate'),
('ping_identity', 'Ping Identity', 'oob', 'available', 'sso', 'standard', 'moderate'),
('iap_sso', 'IAP SSO', 'oob', 'available', 'sso', 'standard', 'moderate')
ON CONFLICT (name, connector_type) DO NOTHING;

-- ============================================================================
-- STEP 5: Function to log connector requests from assessments
-- ============================================================================

CREATE OR REPLACE FUNCTION log_connector_request(
    p_connector_name VARCHAR(200),
    p_requested_by VARCHAR(200),
    p_request_source TEXT,
    p_use_case TEXT,
    p_business_justification TEXT DEFAULT NULL,
    p_priority VARCHAR(50) DEFAULT 'medium'
) RETURNS UUID AS $$
DECLARE
    v_existing_id UUID;
    v_result_id UUID;
BEGIN
    -- Check if this connector was already requested
    SELECT id INTO v_existing_id
    FROM glean_connector_requests
    WHERE connector_name = p_connector_name
    AND status = 'requested'
    LIMIT 1;

    IF v_existing_id IS NOT NULL THEN
        -- Increment request count and update
        UPDATE glean_connector_requests
        SET request_count = request_count + 1,
            updated_at = NOW(),
            -- Escalate priority if requested again
            priority = CASE
                WHEN priority = 'low' AND p_priority IN ('medium', 'high', 'critical') THEN p_priority
                WHEN priority = 'medium' AND p_priority IN ('high', 'critical') THEN p_priority
                WHEN priority = 'high' AND p_priority = 'critical' THEN p_priority
                ELSE priority
            END
        WHERE id = v_existing_id
        RETURNING id INTO v_result_id;
    ELSE
        -- Create new request
        INSERT INTO glean_connector_requests (
            connector_name, requested_by, request_source,
            use_case, business_justification, priority
        ) VALUES (
            p_connector_name, p_requested_by, p_request_source,
            p_use_case, p_business_justification, p_priority
        ) RETURNING id INTO v_result_id;
    END IF;

    RETURN v_result_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 6: View for connector gap analysis
-- ============================================================================

CREATE OR REPLACE VIEW glean_connector_gaps AS
SELECT
    cr.connector_name,
    cr.request_count,
    cr.priority,
    cr.status,
    STRING_AGG(DISTINCT cr.use_case, '; ') as use_cases,
    STRING_AGG(DISTINCT cr.requested_by, ', ') as requesters,
    MIN(cr.created_at) as first_requested,
    MAX(cr.updated_at) as last_requested
FROM glean_connector_requests cr
WHERE cr.status IN ('requested', 'planned')
GROUP BY cr.connector_name, cr.request_count, cr.priority, cr.status
ORDER BY
    CASE cr.priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    cr.request_count DESC;

-- ============================================================================
-- STEP 7: Documentation note
-- ============================================================================
-- Note: Update CLAUDE.md to reflect 18 agents (was 17):
--   - 15 domain specialists
--   - 2 meta-agents (Facilitator + Reporter)
--   - 1 internal enablement agent (Glean Evaluator)
--
-- Agent details:
--   Name: glean_evaluator
--   Display: "Can We Glean This?"
--   Category: Internal Enablement
--   Purpose: Evaluate if Glean is the right tool for a given request
--   Handoffs: Architect (technical deep-dive), Guardian (security), Capital (cost analysis)
--
-- New tables:
--   - glean_connectors: Registry of OOB, custom, and requested connectors
--   - glean_connector_requests: Gap tracking for connector prioritization
--   - glean_connector_gaps (view): Prioritized view of requested connectors
