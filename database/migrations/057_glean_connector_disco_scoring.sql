-- Migration: Glean Connector Registry with DISCO Scoring Matrix
-- Version: 057
-- Date: 2026-01-29
-- Description:
--   Replaces glean_connectors table with authoritative data from:
--   AWC-Glean Data Source Connector Tracking-290126.pdf
--
--   Creates scoring matrix for DISCO project feasibility assessment.

-- ============================================================================
-- STEP 1: Add Contentful deployment status enum (if not exists)
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE glean_contentful_status AS ENUM (
        'enabled',           -- Fully deployed and working at Contentful
        'testing',           -- Indexed/testing phase
        'approved',          -- Approved for deployment, TBD date
        'in_progress',       -- Approved and actively being built
        'pending_approval',  -- Requested, needs approval
        'not_requested'      -- Available in Glean but not requested at Contentful
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- STEP 2: Add new columns to glean_connectors (if not exist)
-- ============================================================================

ALTER TABLE glean_connectors
ADD COLUMN IF NOT EXISTS contentful_status glean_contentful_status DEFAULT 'not_requested',
ADD COLUMN IF NOT EXISTS contentful_enabled_date DATE,
ADD COLUMN IF NOT EXISTS connector_subtype VARCHAR(50),
ADD COLUMN IF NOT EXISTS disco_score INTEGER DEFAULT 0;

-- ============================================================================
-- STEP 3: Clear existing data and replace with PDF source of truth
-- ============================================================================

TRUNCATE TABLE glean_connectors CASCADE;

-- ============================================================================
-- STEP 4: Insert All Available Native Glean Connectors (85 from PDF pages 1-3)
-- ============================================================================

INSERT INTO glean_connectors (name, display_name, connector_type, status, connector_subtype, contentful_status, disco_score) VALUES
-- Row 1-30 from PDF page 1
('15five', '15Five', 'oob', 'available', 'native', 'not_requested', 1),
('adobe_experience_manager', 'Adobe Experience Manager', 'oob', 'available', 'native', 'not_requested', 1),
('affinity', 'Affinity', 'oob', 'available', 'native', 'not_requested', 1),
('aha', 'Aha!', 'oob', 'available', 'native', 'not_requested', 1),
('airtable', 'Airtable', 'oob', 'available', 'native', 'not_requested', 1),
('amazon_s3', 'Amazon S3 (beta)', 'oob', 'available', 'native', 'not_requested', 1),
('ariba', 'Ariba', 'oob', 'available', 'native', 'not_requested', 1),
('azure', 'Azure', 'oob', 'available', 'native', 'not_requested', 1),
('azure_devops', 'Azure DevOps (Beta)', 'oob', 'available', 'native', 'not_requested', 1),
('azure_file_share', 'Azure File Share', 'oob', 'available', 'native', 'not_requested', 1),
('bamboohr', 'BambooHR', 'oob', 'available', 'native', 'not_requested', 1),
('benchling', 'Benchling', 'oob', 'available', 'native', 'not_requested', 1),
('bitbucket', 'Bitbucket', 'oob', 'available', 'native', 'not_requested', 1),
('box', 'Box', 'oob', 'available', 'native', 'not_requested', 1),
('brightspot', 'Brightspot', 'oob', 'available', 'native', 'not_requested', 1),
('bynder_native', 'Bynder', 'oob', 'available', 'native', 'not_requested', 1),
('coda', 'Coda', 'oob', 'available', 'native', 'not_requested', 1),
('confluence_on_premise', 'Confluence On Premise', 'oob', 'available', 'native', 'not_requested', 1),
('databricks', 'Databricks', 'oob', 'available', 'native', 'not_requested', 1),
('datadog', 'Datadog', 'oob', 'available', 'native', 'not_requested', 1),
('datastax', 'Datastax', 'oob', 'available', 'native', 'not_requested', 1),
('docebo', 'Docebo', 'oob', 'available', 'native', 'not_requested', 1),
('dropbox', 'Dropbox', 'oob', 'available', 'native', 'not_requested', 1),
('egnyte', 'Egnyte', 'oob', 'available', 'native', 'not_requested', 1),
('evernote', 'Evernote', 'oob', 'available', 'native', 'not_requested', 1),
('fellow', 'Fellow', 'oob', 'available', 'partner_built', 'not_requested', 1),
('freshservice', 'Freshservice', 'oob', 'available', 'native', 'not_requested', 1),
('gitlab', 'GitLab', 'oob', 'available', 'native', 'not_requested', 1),
('gong', 'Gong', 'oob', 'available', 'native', 'not_requested', 1),
('greenhouse_native', 'Greenhouse', 'oob', 'available', 'native', 'not_requested', 1),

-- Row 31-67 from PDF page 2
('guidde', 'Guidde', 'oob', 'available', 'partner_built', 'not_requested', 1),
('guru', 'Guru', 'oob', 'available', 'native', 'not_requested', 1),
('haystack', 'Haystack', 'oob', 'available', 'partner_built', 'not_requested', 1),
('highspot', 'Highspot', 'oob', 'available', 'native', 'not_requested', 1),
('hubspot', 'Hubspot (Beta)', 'oob', 'available', 'native', 'not_requested', 1),
('iap_sso', 'IAP SSO', 'oob', 'available', 'native', 'not_requested', 1),
('insided', 'InSided', 'oob', 'available', 'native', 'not_requested', 1),
('invision', 'InVision', 'oob', 'available', 'native', 'not_requested', 1),
('interact', 'Interact', 'oob', 'available', 'native', 'not_requested', 1),
('jfrog', 'JFrog', 'oob', 'available', 'native', 'not_requested', 1),
('jenkins', 'Jenkins', 'oob', 'available', 'native', 'not_requested', 1),
('jumpcloud', 'Jumpcloud', 'oob', 'available', 'native', 'not_requested', 1),
('keycloak', 'Keycloak', 'oob', 'available', 'native', 'not_requested', 1),
('lessonly', 'Lessonly', 'oob', 'available', 'native', 'not_requested', 1),
('lever', 'Lever (beta)', 'oob', 'available', 'native', 'not_requested', 1),
('linear', 'Linear (beta)', 'oob', 'available', 'native', 'not_requested', 1),
('looker_studio', 'Looker Studio', 'oob', 'available', 'native', 'not_requested', 1),
('lumapps', 'LumApps', 'oob', 'available', 'native', 'not_requested', 1),
('marketo', 'Marketo', 'oob', 'available', 'native', 'not_requested', 1),
('microsoft_entra_id', 'Microsoft Entra ID', 'oob', 'available', 'native', 'not_requested', 1),
('microsoft_teams', 'Microsoft Teams', 'oob', 'available', 'native', 'not_requested', 1),
('mindtouch', 'Mindtouch', 'oob', 'available', 'native', 'not_requested', 1),
('monday', 'Monday', 'oob', 'available', 'native', 'not_requested', 1),
('nice_cxone', 'Nice CXone', 'oob', 'available', 'native', 'not_requested', 1),
('notion', 'Notion', 'oob', 'available', 'native', 'not_requested', 1),
('onedrive', 'OneDrive', 'oob', 'available', 'native', 'not_requested', 1),
('onelogin', 'OneLogin', 'oob', 'available', 'native', 'not_requested', 1),
('onetrust', 'OneTrust', 'oob', 'available', 'native', 'not_requested', 1),
('opsgenie', 'Opsgenie', 'oob', 'available', 'native', 'not_requested', 1),
('outlook', 'Outlook', 'oob', 'available', 'native', 'not_requested', 1),
('pagerduty', 'PagerDuty', 'oob', 'available', 'native', 'not_requested', 1),
('panopto', 'Panopto', 'oob', 'available', 'native', 'not_requested', 1),
('phabricator', 'Phabricator', 'oob', 'available', 'native', 'not_requested', 1),
('ping_identity', 'Ping Identity', 'oob', 'available', 'native', 'not_requested', 1),
('pingboard', 'Pingboard', 'oob', 'available', 'native', 'not_requested', 1),
('plusplus', 'PlusPlus', 'oob', 'available', 'partner_built', 'not_requested', 1),
('quip', 'Quip', 'oob', 'available', 'native', 'not_requested', 1),

-- Row 68-85 from PDF page 3
('saleshood', 'SalesHood', 'oob', 'available', 'native', 'not_requested', 1),
('screensteps', 'ScreenSteps', 'oob', 'available', 'partner_built', 'not_requested', 1),
('seismic', 'Seismic', 'oob', 'available', 'native', 'not_requested', 1),
('servicenow', 'ServiceNow', 'oob', 'available', 'native', 'not_requested', 1),
('sharepoint', 'SharePoint', 'oob', 'available', 'native', 'not_requested', 1),
('shortcut', 'Shortcut', 'oob', 'available', 'native', 'not_requested', 1),
('simpplr', 'Simpplr', 'oob', 'available', 'native', 'not_requested', 1),
('slab', 'Slab', 'oob', 'available', 'native', 'not_requested', 1),
('smartsheet', 'Smartsheet', 'oob', 'available', 'native', 'not_requested', 1),
('stack_overflow_teams', 'Stack Overflow for Teams', 'oob', 'available', 'native', 'not_requested', 1),
('swagger', 'Swagger', 'oob', 'available', 'native', 'not_requested', 1),
('trello', 'Trello', 'oob', 'available', 'native', 'not_requested', 1),
('unily', 'Unily', 'oob', 'available', 'native', 'not_requested', 1),
('workramp', 'Workramp', 'oob', 'available', 'native', 'not_requested', 1),
('workday', 'Workday', 'oob', 'available', 'native', 'not_requested', 1),
('workplace_from_meta', 'Workplace from Meta', 'oob', 'available', 'native', 'not_requested', 1),
('zeplin', 'Zeplin', 'oob', 'available', 'native', 'not_requested', 1),
('zulip', 'Zulip', 'oob', 'available', 'native', 'not_requested', 1);

-- ============================================================================
-- STEP 5: Insert Contentful's Deployed/Requested Connectors (from PDF table)
-- ============================================================================

-- ENABLED connectors (May 19, 2025 - Initial deployment)
INSERT INTO glean_connectors (name, display_name, connector_type, status, connector_subtype, contentful_status, contentful_enabled_date, disco_score) VALUES
('confluence', 'Confluence', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),
('jira', 'Jira', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),
('google_drive', 'Google Drive', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),
('google_mail', 'Google Mail', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),
('miro', 'Miro', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),
('salesforce', 'Salesforce', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),
('slack', 'Slack', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),
('asana', 'Asana', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),
('zendesk', 'Zendesk', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),
('zoom', 'Zoom', 'oob', 'available', 'native', 'enabled', '2025-05-19', 5),

-- ENABLED - Custom connector
('chorus', 'Chorus', 'custom', 'available', 'custom', 'enabled', '2025-11-21', 5),

-- ENABLED - Later dates
('google_calendar', 'Google Calendar', 'oob', 'available', 'native', 'enabled', '2025-08-18', 5),
('github', 'Github', 'oob', 'available', 'native', 'enabled', '2025-10-23', 5),

-- ENABLED - Public connectors
('contentful_com', 'Contentful.com', 'custom', 'available', 'public', 'enabled', '2025-07-14', 5),
('dev_docs', 'Dev Docs', 'custom', 'available', 'public', 'enabled', '2025-07-14', 5),

-- INDEXED/TESTING
('tableau', 'Tableau', 'oob', 'available', 'native', 'testing', '2025-07-18', 4);

-- APPROVED connectors (TBD dates)
INSERT INTO glean_connectors (name, display_name, connector_type, status, connector_subtype, contentful_status, disco_score) VALUES
('pagerduty_approved', 'PagerDuty', 'oob', 'available', 'native', 'approved', 3),
('loopio', 'Loopio', 'oob', 'available', 'native', 'approved', 3),
('docusign', 'Docusign', 'oob', 'available', 'native', 'approved', 3),
('coupa', 'Coupa', 'custom', 'available', 'custom', 'approved', 3);

-- APPROVED / IN PROGRESS (custom connectors being built)
INSERT INTO glean_connectors (name, display_name, connector_type, status, connector_subtype, contentful_status, disco_score) VALUES
('gainsight', 'Gainsight', 'custom', 'in_development', 'custom', 'in_progress', 2),
('outreach', 'Outreach', 'custom', 'in_development', 'custom', 'in_progress', 2);

-- NEEDS APPROVAL connectors
INSERT INTO glean_connectors (name, display_name, connector_type, status, connector_subtype, contentful_status, disco_score) VALUES
('linkedin_sales_nav', 'LinkedIn Sales Nav', 'custom', 'requested', 'custom', 'pending_approval', 1),
('klue', 'Klue', 'oob', 'available', 'native', 'pending_approval', 1),
('thought_industries', 'Thought Industries', 'custom', 'requested', 'custom', 'pending_approval', 1),
('backstage_roadie', 'Backstage/Roadie', 'custom', 'requested', 'custom', 'pending_approval', 1),
('arphie', 'Arphie', 'custom', 'requested', 'custom', 'pending_approval', 1),
('momentum', 'Momentum', 'custom', 'requested', 'custom', 'pending_approval', 1),
('wistia', 'Wistia', 'custom', 'requested', 'custom', 'pending_approval', 1),
('figma', 'Figma', 'custom', 'requested', 'custom', 'pending_approval', 1),
('dovetail', 'Dovetail', 'custom', 'requested', 'custom', 'pending_approval', 1),
('bynder_custom', 'Bynder', 'custom', 'requested', 'custom', 'pending_approval', 1),
('wappalyzer_builtwith', 'Wappalyzer/BuiltWith', 'custom', 'requested', 'custom', 'pending_approval', 1),
('certinia', 'Certinia', 'custom', 'requested', 'custom', 'pending_approval', 1),
('truvoice', 'TruVoice', 'custom', 'requested', 'custom', 'pending_approval', 1),
('crossbeam', 'Crossbeam', 'custom', 'requested', 'custom', 'pending_approval', 1),
('allego', 'Allego', 'custom', 'requested', 'custom', 'pending_approval', 1),
('allbound', 'Allbound', 'custom', 'requested', 'custom', 'pending_approval', 1),
('greenhouse_custom', 'Greenhouse', 'custom', 'requested', 'custom', 'pending_approval', 1);

-- ============================================================================
-- STEP 6: Create indexes for efficient DISCO queries
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_glean_connectors_disco_score ON glean_connectors(disco_score DESC);
CREATE INDEX IF NOT EXISTS idx_glean_connectors_contentful_status ON glean_connectors(contentful_status);

-- ============================================================================
-- STEP 7: Create DISCO Integration Scoring Function
-- ============================================================================

CREATE OR REPLACE FUNCTION check_disco_integration_feasibility(
    p_integration_names TEXT[]
) RETURNS TABLE (
    integration_name TEXT,
    connector_found BOOLEAN,
    connector_name VARCHAR(100),
    display_name VARCHAR(200),
    connector_type glean_connector_type,
    contentful_status glean_contentful_status,
    disco_score INTEGER,
    feasibility_rating TEXT,
    is_blocker BOOLEAN,
    notes TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH requested AS (
        SELECT UNNEST(p_integration_names) AS req_name
    )
    SELECT
        r.req_name::TEXT AS integration_name,
        (c.id IS NOT NULL) AS connector_found,
        c.name AS connector_name,
        c.display_name,
        c.connector_type,
        c.contentful_status,
        COALESCE(c.disco_score, 0) AS disco_score,
        CASE
            WHEN c.disco_score >= 5 THEN 'READY'
            WHEN c.disco_score >= 4 THEN 'NEARLY_READY'
            WHEN c.disco_score >= 3 THEN 'PLANNED'
            WHEN c.disco_score >= 2 THEN 'IN_PROGRESS'
            WHEN c.disco_score >= 1 THEN 'REQUIRES_PROCESS'
            ELSE 'BLOCKER'
        END AS feasibility_rating,
        (COALESCE(c.disco_score, 0) = 0) AS is_blocker,
        CASE
            WHEN c.disco_score >= 5 THEN 'Ready to use - connector enabled at Contentful'
            WHEN c.disco_score >= 4 THEN 'Nearly ready - connector in testing phase'
            WHEN c.disco_score >= 3 THEN 'On roadmap - connector approved, awaiting deployment'
            WHEN c.disco_score >= 2 THEN 'In development - custom connector being built'
            WHEN c.disco_score >= 1 THEN 'Available - needs approval process to enable'
            ELSE 'BLOCKER: No connector exists - escalate to IT for custom connector request'
        END AS notes
    FROM requested r
    LEFT JOIN glean_connectors c ON (
        LOWER(c.name) = LOWER(REPLACE(REPLACE(r.req_name, ' ', '_'), '-', '_'))
        OR LOWER(c.display_name) ILIKE '%' || LOWER(r.req_name) || '%'
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 8: Create View for DISCO Integration Matrix
-- ============================================================================

DROP VIEW IF EXISTS glean_disco_integration_matrix;
CREATE VIEW glean_disco_integration_matrix AS
SELECT
    name,
    display_name,
    connector_type,
    connector_subtype,
    contentful_status,
    contentful_enabled_date,
    disco_score,
    CASE disco_score
        WHEN 5 THEN 'READY - Fully enabled at Contentful'
        WHEN 4 THEN 'TESTING - In indexing/testing phase'
        WHEN 3 THEN 'APPROVED - Approved, pending deployment'
        WHEN 2 THEN 'BUILDING - Custom connector in development'
        WHEN 1 THEN 'AVAILABLE - Needs approval process'
        ELSE 'CUSTOM - Requires custom build'
    END AS disco_rating
FROM glean_connectors
ORDER BY disco_score DESC, display_name;

-- ============================================================================
-- STEP 9: Summary view by status
-- ============================================================================

DROP VIEW IF EXISTS glean_connector_summary;
CREATE VIEW glean_connector_summary AS
SELECT
    contentful_status,
    disco_score,
    COUNT(*) as connector_count,
    STRING_AGG(display_name, ', ' ORDER BY display_name) as connectors
FROM glean_connectors
GROUP BY contentful_status, disco_score
ORDER BY disco_score DESC;

-- ============================================================================
-- STEP 10: Overall DISCO feasibility scoring function
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_disco_integration_score(
    p_integration_names TEXT[]
) RETURNS JSONB AS $$
DECLARE
    v_results JSONB;
    v_total_score INTEGER := 0;
    v_max_score INTEGER := 0;
    v_integration_count INTEGER := 0;
    v_ready_count INTEGER := 0;
    v_blockers_count INTEGER := 0;
    v_blocker_names TEXT[];
BEGIN
    SELECT jsonb_agg(row_to_json(r.*))
    INTO v_results
    FROM check_disco_integration_feasibility(p_integration_names) r;

    SELECT
        COALESCE(SUM(disco_score), 0),
        COUNT(*) * 5,
        COUNT(*),
        COUNT(*) FILTER (WHERE disco_score >= 5),
        COUNT(*) FILTER (WHERE disco_score = 0),
        ARRAY_AGG(integration_name) FILTER (WHERE disco_score = 0)
    INTO v_total_score, v_max_score, v_integration_count, v_ready_count, v_blockers_count, v_blocker_names
    FROM check_disco_integration_feasibility(p_integration_names);

    RETURN jsonb_build_object(
        'integrations', v_results,
        'summary', jsonb_build_object(
            'total_integrations', v_integration_count,
            'ready_integrations', v_ready_count,
            'blockers', v_blockers_count,
            'blocker_names', COALESCE(v_blocker_names, ARRAY[]::TEXT[]),
            'score', v_total_score,
            'max_score', v_max_score,
            'percentage', CASE WHEN v_max_score > 0 THEN ROUND((v_total_score::DECIMAL / v_max_score) * 100, 1) ELSE 0 END,
            'overall_feasibility', CASE
                WHEN v_blockers_count > 0 THEN 'BLOCKED'
                WHEN v_total_score = v_max_score THEN 'FULLY_READY'
                WHEN v_total_score >= v_max_score * 0.8 THEN 'MOSTLY_READY'
                WHEN v_total_score >= v_max_score * 0.5 THEN 'PARTIAL'
                ELSE 'SIGNIFICANT_GAPS'
            END,
            'action_required', CASE
                WHEN v_blockers_count > 0 THEN 'Escalate to IT: ' || ARRAY_TO_STRING(COALESCE(v_blocker_names, ARRAY[]::TEXT[]), ', ') || ' require custom connector development'
                WHEN v_total_score < v_max_score THEN 'Some integrations need approval or are in progress'
                ELSE 'All integrations ready'
            END
        ),
        'data_source', jsonb_build_object(
            'source', 'AWC-Glean Data Source Connector Tracking',
            'last_updated', '2026-01-29',
            'note', 'Connector availability may have changed. Check with IT/AWC team for latest status before finalizing project plans.'
        )
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Documentation
-- ============================================================================
--
-- DISCO Integration Scoring:
--   5 = READY: Integration enabled and working at Contentful
--   4 = TESTING: Integration in indexing/testing phase
--   3 = APPROVED: Integration approved, awaiting deployment
--   2 = BUILDING: Custom connector being developed
--   1 = AVAILABLE: Glean has connector OR needs approval at Contentful
--   0 = CUSTOM: No connector exists, would need custom build
--
-- Usage Examples:
--   SELECT * FROM check_disco_integration_feasibility(ARRAY['Salesforce', 'Gainsight', 'Figma']);
--   SELECT calculate_disco_integration_score(ARRAY['Slack', 'Jira', 'Notion']);
--   SELECT * FROM glean_disco_integration_matrix WHERE disco_score >= 3;
--   SELECT * FROM glean_connector_summary;
--
-- Source: AWC-Glean Data Source Connector Tracking-290126.pdf
-- Last Updated: 2026-01-29
