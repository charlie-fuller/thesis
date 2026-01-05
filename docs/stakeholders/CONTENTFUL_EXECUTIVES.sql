-- ============================================================================
-- CONTENTFUL C-SUITE EXECUTIVES - ADDITIONAL STAKEHOLDERS
-- ============================================================================
-- Client UUID: 00000000-0000-0000-0000-000000000001 (Default Organization)
-- Created: January 2025
--
-- This script adds C-suite executives identified from official Contentful
-- leadership page and updates reporting relationships for existing stakeholders.
--
-- NOTE: Run this AFTER creating the unique constraint if it doesn't exist:
-- CREATE UNIQUE INDEX IF NOT EXISTS stakeholders_client_name_idx
--   ON stakeholders (client_id, name);
-- ============================================================================

-- ============================================================================
-- STEP 0: ADD UNIQUE CONSTRAINT IF MISSING
-- ============================================================================
CREATE UNIQUE INDEX IF NOT EXISTS stakeholders_client_name_idx
  ON stakeholders (client_id, name);

-- ============================================================================
-- STEP 1: FIX CEO NAME (Karthik Rau, not Rao)
-- ============================================================================
UPDATE stakeholders
SET name = 'Karthik Rau',
    notes = 'Started April 2025. Driving company-wide AI initiative as strategic priority. Mandated hiring of 4 AI Practitioners across departments after Champions program underperformed. Provides political backing for AI transformation. Previously CEO at SignalFx.',
    metadata = metadata || '{"background": "Former CEO at SignalFx (acquired by Splunk)"}'::jsonb,
    updated_at = NOW()
WHERE name = 'Karthik Rao'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- ============================================================================
-- STEP 2: INSERT CFO - Carla Cooper
-- ============================================================================
INSERT INTO stakeholders (
    client_id,
    name,
    email,
    role,
    department,
    organization,
    engagement_level,
    alignment_score,
    sentiment_score,
    key_concerns,
    interests,
    communication_preferences,
    notes,
    metadata
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Carla Cooper',
    NULL,
    'Chief Financial Officer',
    'finance',
    'Contentful',
    'neutral',
    0.7,
    0.65,
    '["AI ROI justification", "Budget allocation for AI initiatives", "Pre-IPO financial discipline"]'::JSONB,
    '["Cost efficiency", "Revenue impact", "Operational leverage"]'::JSONB,
    '{"preferred_channel": "executive briefings", "style": "data-driven, bottom-line focused"}'::JSONB,
    'CFO overseeing all finance functions. Previously held finance roles at Salesforce, Mulesoft, and Responsys. Key decision maker for AI investment approvals.',
    '{"personality_archetype": "Financial Steward", "motivations": ["Financial discipline", "Shareholder value", "Operational efficiency"], "decision_style": "ROI-focused, risk-aware, needs clear business case", "influence_on_ai_adoption": "Budget holder - approves AI investments, needs ROI demonstration", "background": "Salesforce, Mulesoft, Responsys"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 3: INSERT CPO - Karl Rumelhart
-- ============================================================================
INSERT INTO stakeholders (
    client_id,
    name,
    email,
    role,
    department,
    organization,
    engagement_level,
    alignment_score,
    sentiment_score,
    key_concerns,
    interests,
    communication_preferences,
    notes,
    metadata
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Karl Rumelhart',
    NULL,
    'Chief Product Officer',
    'product',
    'Contentful',
    'champion',
    0.9,
    0.8,
    '["AI product integration", "Product velocity", "Customer AI adoption"]'::JSONB,
    '["AI-powered product features", "Customer success", "Product innovation"]'::JSONB,
    '{"preferred_channel": "product reviews", "style": "strategic, customer-focused"}'::JSONB,
    'CPO responsible for product strategy at Contentful. Previously CPO at Gainsight. Direct manager of Chris Baumgartner (AI Program) and Michael Stratton (VP Product).',
    '{"personality_archetype": "Product Visionary", "motivations": ["Product excellence", "AI-native capabilities", "Customer outcomes"], "decision_style": "Strategic product thinker, balances innovation with execution", "influence_on_ai_adoption": "Owns AI program through Chris Baumgartner - key sponsor for internal AI initiatives", "background": "Former CPO at Gainsight"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 4: INSERT Chief People Officer - Ray Martinelli
-- ============================================================================
INSERT INTO stakeholders (
    client_id,
    name,
    email,
    role,
    department,
    organization,
    engagement_level,
    alignment_score,
    sentiment_score,
    key_concerns,
    interests,
    communication_preferences,
    notes,
    metadata
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Ray Martinelli',
    NULL,
    'Chief People Officer',
    'hr',
    'Contentful',
    'supporter',
    0.75,
    0.7,
    '["AI impact on workforce", "Change management at scale", "Employee AI anxiety"]'::JSONB,
    '["Workforce development", "AI upskilling", "Culture transformation"]'::JSONB,
    '{"preferred_channel": "leadership meetings", "style": "people-centered, strategic"}'::JSONB,
    'Chief People Officer with 20+ years HR leadership experience. Previously at Apple and Juniper Networks. Direct manager of Chad Meek (VP Talent).',
    '{"personality_archetype": "People Champion", "motivations": ["Employee development", "Culture preservation", "Workforce readiness"], "decision_style": "People-first, change-aware, collaborative", "influence_on_ai_adoption": "Key stakeholder for change management and AI adoption culture", "background": "Apple, Juniper Networks"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 5: INSERT CTO - Paolo Negri
-- ============================================================================
INSERT INTO stakeholders (
    client_id,
    name,
    email,
    role,
    department,
    organization,
    engagement_level,
    alignment_score,
    sentiment_score,
    key_concerns,
    interests,
    communication_preferences,
    notes,
    metadata
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Paolo Negri',
    NULL,
    'Chief Technology Officer',
    'it',
    'Contentful',
    'champion',
    0.85,
    0.75,
    '["Technical infrastructure for AI", "Engineering velocity", "Platform scalability"]'::JSONB,
    '["AI/ML infrastructure", "Developer experience", "Technical excellence"]'::JSONB,
    '{"preferred_channel": "technical reviews", "style": "engineering-focused, detail-oriented"}'::JSONB,
    'Co-founder & CTO. Engineering leader focused on scaling technology. Danny Leal (IT Director) likely reports here or has dotted line.',
    '{"personality_archetype": "Technical Visionary", "motivations": ["Technical excellence", "Platform innovation", "Engineering culture"], "decision_style": "Engineering-first, data-driven, pragmatic", "influence_on_ai_adoption": "Sets technical direction for AI infrastructure and integration", "background": "Contentful Co-founder"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 6: INSERT CLO - Margo M. Smith
-- ============================================================================
INSERT INTO stakeholders (
    client_id,
    name,
    email,
    role,
    department,
    organization,
    engagement_level,
    alignment_score,
    sentiment_score,
    key_concerns,
    interests,
    communication_preferences,
    notes,
    metadata
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Margo M. Smith',
    NULL,
    'Chief Legal Officer',
    'legal',
    'Contentful',
    'neutral',
    0.65,
    0.6,
    '["AI liability and risk", "Data privacy compliance", "Vendor contracts for AI tools"]'::JSONB,
    '["AI governance frameworks", "Risk mitigation", "Regulatory compliance"]'::JSONB,
    '{"preferred_channel": "legal briefings", "style": "risk-focused, thorough"}'::JSONB,
    'Recently joined Contentful from Snowflake Inc. to lead global legal strategy. Direct manager of Ashley Adams (Legal Operations).',
    '{"personality_archetype": "Risk Guardian", "motivations": ["Legal risk mitigation", "Compliance excellence", "Corporate governance"], "decision_style": "Risk-aware, thorough, precedent-conscious", "influence_on_ai_adoption": "Gatekeeper for AI vendor contracts and compliance requirements", "background": "Snowflake Inc."}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 7: INSERT CMO - Elizabeth Maxson
-- ============================================================================
INSERT INTO stakeholders (
    client_id,
    name,
    email,
    role,
    department,
    organization,
    engagement_level,
    alignment_score,
    sentiment_score,
    key_concerns,
    interests,
    communication_preferences,
    notes,
    metadata
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Elizabeth Maxson',
    NULL,
    'Chief Marketing Officer',
    'marketing',
    'Contentful',
    'champion',
    0.85,
    0.75,
    '["AI in marketing operations", "Content personalization at scale", "Brand consistency with AI"]'::JSONB,
    '["AI-powered marketing", "Personalization", "Marketing automation"]'::JSONB,
    '{"preferred_channel": "marketing reviews", "style": "creative, data-informed"}'::JSONB,
    'Former CMO at Tableau (Salesforce). Focused on AI and personalization in marketing. Potential champion for marketing AI use cases.',
    '{"personality_archetype": "Marketing Innovator", "motivations": ["Marketing excellence", "AI-driven personalization", "Brand leadership"], "decision_style": "Creative yet data-informed, customer-centric", "influence_on_ai_adoption": "Champion for AI in marketing - potential early adopter for content AI", "background": "Tableau (Salesforce)"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 8: UPDATE REPORTING RELATIONSHIPS
-- ============================================================================

-- Chris Baumgartner reports to Karl Rumelhart (CPO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Karl Rumelhart'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Chris Baumgartner'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Michael Stratton reports to Karl Rumelhart (CPO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Karl Rumelhart'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Michael Stratton'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Raul Rivera III reports to Carla Cooper (CFO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Carla Cooper'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Raul Rivera III'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Danny Leal reports to Paolo Negri (CTO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Paolo Negri'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Danny Leal'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Ashley Adams reports to Margo M. Smith (CLO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Margo M. Smith'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Ashley Adams'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Chad Meek reports to Ray Martinelli (Chief People Officer)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Ray Martinelli'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Chad Meek'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Karl Rumelhart (CPO) reports to Karthik Rau (CEO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Karthik Rau'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Karl Rumelhart'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Carla Cooper (CFO) reports to Karthik Rau (CEO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Karthik Rau'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Carla Cooper'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Ray Martinelli (Chief People Officer) reports to Karthik Rau (CEO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Karthik Rau'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Ray Martinelli'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Paolo Negri (CTO) reports to Karthik Rau (CEO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Karthik Rau'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Paolo Negri'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Margo M. Smith (CLO) reports to Karthik Rau (CEO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Karthik Rau'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Margo M. Smith'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- Elizabeth Maxson (CMO) reports to Karthik Rau (CEO)
UPDATE stakeholders
SET reports_to = (
    SELECT id FROM stakeholders
    WHERE name = 'Karthik Rau'
    AND client_id = '00000000-0000-0000-0000-000000000001'::UUID
    LIMIT 1
)
WHERE name = 'Elizabeth Maxson'
  AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Run this to verify the org structure:
SELECT
    s.name,
    s.role,
    s.department,
    m.name as reports_to
FROM stakeholders s
LEFT JOIN stakeholders m ON s.reports_to = m.id
WHERE s.client_id = '00000000-0000-0000-0000-000000000001'::UUID
ORDER BY
    CASE WHEN m.name IS NULL THEN 0 ELSE 1 END,
    m.name,
    s.name;
