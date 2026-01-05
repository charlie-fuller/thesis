-- ============================================================================
-- CONTENTFUL STAKEHOLDER PROFILES - COMPLETE SQL
-- ============================================================================
-- Client UUID: 00000000-0000-0000-0000-000000000001 (Default Organization)
-- Created: January 2025
--
-- This script creates/updates stakeholder profiles for Contentful interview
-- contacts with rich psychological profiles, communication preferences, and
-- strategic intelligence for use by Thesis agents.
-- ============================================================================

-- ============================================================================
-- STEP 1: INSERT CEO (Karthik Rao)
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
    'Karthik Rao',
    NULL,
    'Chief Executive Officer',
    'executive',
    'Contentful',
    'champion',
    0.95,
    0.8,
    '["Company-wide AI adoption velocity", "ROI on AI investments", "Competitive positioning"]'::JSONB,
    '["AI-native strategy", "Operational efficiency", "Market leadership"]'::JSONB,
    '{"preferred_channel": "executive briefings", "style": "results-focused"}'::JSONB,
    'Started April 2025. Driving company-wide AI initiative as strategic priority. Mandated hiring of 4 AI Practitioners across departments after Champions program underperformed. Provides political backing for AI transformation.',
    '{"personality_archetype": "Transformational Leader", "motivations": ["Market leadership", "Operational excellence", "AI-native company positioning"], "decision_style": "Strategic, results-oriented, willing to mandate change", "influence_on_ai_adoption": "Executive sponsor - sets strategic direction, provides air cover, mandated AI Practitioner hiring", "tenure_at_contentful": "Started April 2025"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 2: INSERT Raul Rivera III - Finance
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
    'Raul Rivera III',
    NULL,
    'Senior Director, Global Controller',
    'finance',
    'Contentful',
    'supporter',
    0.75,
    0.6,
    '["SOX compliance", "Audit readiness", "Data accuracy", "Close cycle speed", "System reliability during month-end"]'::JSONB,
    '["Process optimization", "Automation ROI", "Pre-IPO financial rigor", "Team capacity building"]'::JSONB,
    '{"preferred_channel": "structured meetings with data", "style": "numbers-driven, show-me-the-ROI", "avoid": "vague promises without metrics"}'::JSONB,
    'CPA, MBA (UW Foster Executive). Finance leader focused on continuous optimization and cross-functional collaboration. Leads global Accounting, AP, Tax, Treasury, Payroll, and Procurement. Promoted to Senior Director May 2024. Background: Stripe (8 months), Expedia (5+ years). Highest-ROI stakeholder for AI.',
    '{"personality_archetype": "The Scaling Specialist", "motivations": ["Close cycle acceleration", "Audit-ready processes", "Team efficiency without headcount scaling", "IPO readiness"], "concerns": ["Data integrity and audit trails", "System reliability during close", "Black box solutions", "Compliance gaps"], "decision_style": "Show me the numbers - baseline metrics, target metrics, ROI calculation. Risk mitigation first. Proof before scale.", "what_success_looks_like": "Close cycle cut by 40%, AP processing time halved, team positioned as strategic partners", "relationship_builders": ["Use finance terminology correctly", "Offer to shadow his team", "Frame AI as freeing finance to be strategic partners"], "relationship_killers": ["Overselling", "Ignoring accounting standards", "Skipping IT partnership"], "credentials": "CPA, Executive MBA (UW Foster)", "tenure_at_contentful": "3+ years (Nov 2022 - present)"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 3: INSERT Danny Leal - IT/Governance
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
    'Danny Leal',
    NULL,
    'Director of IT',
    'it',
    'Contentful',
    'supporter',
    0.7,
    0.5,
    '["Shadow IT proliferation", "Security risks", "SOC 2/ISO 27001 compliance", "Team overload", "Maintenance burden from new tools"]'::JSONB,
    '["Secure enablement", "Reducing help desk tickets", "Scalable systems", "Clean audits", "Team not overwhelmed"]'::JSONB,
    '{"preferred_channel": "concise written (Slack/email with bullets)", "style": "data-driven, no surprises", "meetings": "agendas in advance", "bad_news": "wants it early with options"}'::JSONB,
    'Leads internal IT team including systems engineering, IT services, compliance, people tech. Denver-based (Arvada). 4.5 years at Contentful. Key stakeholder for security, SOC 2/ISO 27001 compliance, and technical integration decisions.',
    '{"personality_archetype": "The Pragmatic Enabler", "primary_identity": "Calm, systematic problem-solver who values order, predictability, and scalable systems", "motivations": ["Team not overwhelmed", "Clean audit reports", "IT made that surprisingly easy", "Eliminating repetitive tasks"], "concerns": ["Shadow IT creation", "Security surprises", "Solutions becoming maintenance nightmare", "Tool proliferation"], "underlying_fear": "Introducing solutions that create more work, security risks, or technical debt", "decision_style": "Tool agnostic, outcome focused. Elegant simplicity wins over complex cleverness.", "communication_decoder": {"help_me_understand_architecture": "Im concerned about how this fits", "interesting_approach": "I have concerns but want to hear you out"}, "what_success_looks_like": "Reduced help desk tickets, clean audits, solutions that make existing systems smarter", "relationship_builders": ["Acknowledge his teams burden", "Document everything", "Involve IT early", "Build on approved platforms"], "relationship_killers": ["Dismissing compliance concerns", "Surprises", "Lack of follow-through"], "tech_stack": "Okta, Jira Service Management, Google Workspace", "tenure_at_contentful": "4.5 years"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 4: INSERT Chad Meek - People/HR
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
    'Chad Meek',
    NULL,
    'VP, Talent Acquisition, Community, and People Data',
    'hr',
    'Contentful',
    'supporter',
    0.75,
    0.6,
    '["Employee adoption anxiety", "Change fatigue", "Failed AI Champions program", "Sustainable adoption without burnout", "Measuring people impact"]'::JSONB,
    '["Community building at scale", "Data-driven people decisions", "Talent development", "Employee engagement", "AI fluency as employer brand"]'::JSONB,
    '{"preferred_channel": "professional but warm", "style": "interested in both metrics and stories", "approach": "thoughtful questions, partnership mindset"}'::JSONB,
    'People leader with passion for building. Started April 2021 as VP TA, role expanded March 2023 to include Community and People Data. Amazon background (data-driven, bias for action). Active in ONE Campaign and Economic Development Committee.',
    '{"personality_archetype": "People Leader with Passion for Building", "self_description": "People leader not talent leader or HR leader - holistic view of humans beyond job functions", "motivations": ["Human-centered AI transformation", "Building community and belonging", "Data-driven people decisions", "Strategic talent development"], "concerns": ["AI Practitioners failing like Champions did", "Employee burnout", "Adoption without support structures", "Measuring soft outcomes"], "amazon_background": ["Data-driven decision making", "Bias for action", "Customer obsession (employees are his customers)"], "champions_failure_context": "Part-time commitment, liked learning but not sharing, no dedicated support", "decision_style": "Both metrics and stories matter. Partnership mindset. Looking for cultural alignment.", "what_success_looks_like": "AI Practitioners succeed where Champions failed. Adoption up, satisfaction high, retention improved.", "relationship_builders": ["Lead with community", "Show scale experience", "Demonstrate people-first values", "Connect to employer brand"], "relationship_killers": ["Technology-first framing", "Ignoring emotional journey", "Creating burnout"], "tenure_at_contentful": "Since April 2021"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 5: INSERT Jon Eakin - Recruiter
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
    'Jon Eakin',
    'jonathan.eakin@contentful.com',
    'Recruiter',
    'hr',
    'Contentful',
    'neutral',
    0.5,
    0.5,
    '[]'::JSONB,
    '["Finding great candidates", "Smooth interview processes"]'::JSONB,
    '{"preferred_channel": "email", "style": "professional, transparent"}'::JSONB,
    'Initial recruiting contact for AI Solutions Partner role. Reports within Chad Meek People organization. 3+ years at Contentful.',
    '{"personality_archetype": "Supportive Coordinator", "motivations": ["Successful placements", "Candidate experience"], "influence_on_ai_adoption": "Low - recruiting function", "tenure_at_contentful": "3+ years"}'::JSONB
)
ON CONFLICT (client_id, name) DO UPDATE SET
    role = EXCLUDED.role,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- ============================================================================
-- STEP 6: UPDATE Ashley Adams with full profile
-- ============================================================================
UPDATE stakeholders
SET
    key_concerns = '["AI hallucinations and accuracy", "Bias in AI systems", "Data privacy and confidential info leakage", "Regulatory compliance (EU AI Act, state laws)", "Shadow AI proliferation", "Team overwhelm"]'::JSONB,
    interests = '["Governance as strategic advantage", "People-first transformation", "Cross-functional partnership", "Legal as innovation enabler", "Team development and recognition"]'::JSONB,
    communication_preferences = '{"preferred_channel": "structured meetings", "style": "vision + execution clarity + metrics", "approach": "strategic framing with evidence"}'::JSONB,
    notes = 'Director of Legal Operations. 15+ years across legal ops, HR, talent management, organizational transformation. Doctorate in Leadership & Organizational Culture (2025). Enneagram 3 ENFJ - driven by achievement AND team success. Wants legal positioned as strategic partner enabling responsible innovation.',
    metadata = '{"personality_archetype": "Enneagram 3 ENFJ - The Achiever Protagonist", "core_philosophy": "Focusing on people first is the key to success", "combined_profile": "Wants to build something that WORKS AND looks successful. Thinks in VISION AND metrics. Competitive but COLLABORATIVE.", "motivations": ["Position legal as strategic partner", "Team development and career advancement", "Being recognized as leader who made AI work", "Governance as competitive advantage"], "concerns": ["AI hallucinations (missed clauses = millions in liability)", "Bias in AI systems", "Data privacy leakage", "Regulatory fragmentation", "Team overwhelm"], "governance_position": {"data_privacy": "Requires vendor agreements on data ownership, residency, deletion", "accuracy": "Rigorous validation, human-in-the-loop, threshold-based deployment", "compliance": "Governance committee with legal representation, risk-based classification"}, "decision_style": "Vision + Execution clarity required. Show metrics AND team impact.", "what_success_looks_like": "Legal positioned as strategic governance leader. Team advances careers. Measurable impact AND recognition.", "relationship_builders": ["Lead with vision + execution", "Emphasize team growth AND recognition", "Frame governance as strategic advantage"], "relationship_killers": ["Vague about execution", "Focus only on risk without opportunity", "Forgetting team visibility"], "credentials": "Doctorate in Leadership (2025), Masters in Org Leadership, SHRM-CP", "tenure_at_contentful": "Since ~2024"}'::JSONB,
    updated_at = NOW()
WHERE name = 'Ashley Adams' AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- ============================================================================
-- STEP 7: UPDATE Chris Baumgartner with full profile
-- ============================================================================
UPDATE stakeholders
SET
    role = 'Staff Program Manager, AI',
    key_concerns = '["Organizational ADHD", "AI Champions program failure", "Sustainable adoption without burnout", "Measurable outcomes", "Cross-functional complexity"]'::JSONB,
    interests = '["Lean principles", "Value stream mapping", "Process improvement", "Human-centered AI", "Metrics and OKRs"]'::JSONB,
    communication_preferences = '{"preferred_channel": "structured STAR-format conversations", "style": "data-driven, Lean terminology", "approach": "waste reduction, iterative improvement"}'::JSONB,
    notes = 'Staff Program Manager of AI for all of Contentful. AI Solutions Partner reports directly to him. Lean transformation background. Reports through IS Organization. Hired to drive AI adoption and literacy company-wide.',
    metadata = '{"personality_archetype": "Practical Philosopher / Lean Transformation Specialist", "background": {"lean_experience": "Done lean transformations before - big picture organizational change", "self_assessment": "By no means an AI expert - learning as I go"}, "orb_of_light_concept": "Organizations need constant awareness through Metrics, OKRs, KPIs. The orb of light is institutional will to continually revisit metrics.", "motivations": ["Fighting organizational ADHD with data", "Human-centered process improvement", "Measurable adoption rates and business impact"], "concerns": ["Champions failed (part-time, liked learning not sharing)", "Solutions without metrics", "Adoption without change management"], "ai_champions_failure": {"why_failed": "Part-time gig, liked learning but not homework of sharing", "ceo_response": "Mandated hiring 4 dedicated AI Practitioners"}, "four_practitioners": {"prod_dev": "Job open", "field": "Dragging feet", "gna": "Direct report to Chris", "marketing": "Already hired"}, "ga_terrain": {"people_hr": "Most open but HIGH bias/compliance risk", "finance": "Moderate readiness, numbers-driven, easy ROI", "legal": "Lowest readiness but highest long-term value"}, "five_nonnegotiables": ["Diagnose independently", "Build hands-on", "Drive adoption through change management", "Show measurable impact", "Human-in-the-loop solutions"], "interview_style": {"format": "Behavioral STAR method", "what_he_listens_for": "You specifically, not we"}, "decision_style": "Data-driven, Lean principles, proof of execution not just ideas", "what_success_looks_like": "Measurable adoption rates, quantified feedback, real business impact", "relationship_builders": ["Shadow teams", "Show workflow changes", "Demonstrate coaching", "Use STAR format", "Know Lean terminology"], "relationship_killers": ["Strategy without execution", "No metrics", "Saying we did instead of I did"], "tenure_at_contentful": "Since April 2025"}'::JSONB,
    updated_at = NOW()
WHERE name = 'Chris Baumgartner' AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- ============================================================================
-- STEP 8: UPDATE Michael Stratton with full profile
-- ============================================================================
UPDATE stakeholders
SET
    role = 'VP of Product',
    department = 'product',
    engagement_level = 'neutral',
    alignment_score = 0.6,
    sentiment_score = 0.5,
    key_concerns = '["Resource distraction from product roadmap", "Reputational and security risk from internal AI", "Internal technical debt", "Missed learning opportunities from siloed work"]'::JSONB,
    interests = '["Platform maturity and extensibility", "Developer experience (DX)", "User adoption and activation", "Competitive differentiation", "Cross-functional alignment"]'::JSONB,
    communication_preferences = '{"preferred_channel": "quarterly briefings via Chris", "style": "business outcomes not tech details", "format": "time saved, cost avoidance, risk mitigation metrics"}'::JSONB,
    notes = 'VP of Product. Not direct stakeholder for G&A AI work, but influential senior leader. Views internal AI through two lenses: (1) Internal Force Multiplier - does G&A AI boost Product bandwidth? (2) Strategic Risk & Culture Agent - do internal AI experiments set good governance precedents?',
    metadata = '{"personality_archetype": "Strategic Product Leader", "relationship_to_role": {"direct_stakeholder": false, "influence_level": "High - senior leader whose perception matters", "update_cadence": "Quarterly briefs via Chris"}, "two_lenses": {"force_multiplier": "Does G&A AI make supporting functions faster/cheaper?", "risk_culture_agent": "Do internal AI experiments set good governance precedents?"}, "interests_relevance": {"platform_maturity": "Low direct relevance", "developer_experience": "High indirect - your pioneering informs future DX", "user_adoption": "Medium - internal adoption is live case study", "cross_functional": "CRITICAL - you must navigate legal/security/finance/HR"}, "concerns": ["Distraction from product roadmap", "Security/reputational risk", "Creating internal debt", "Siloed learning"], "what_he_wants_to_hear": {"business_outcomes": "Time saved, cost avoidance, cycle time reduction", "risk_mitigation": "Guardrails, audit trails, data governance", "product_connection": "How G&A AI frees up engineering support"}, "communication_strategy": {"report_through_chris": true, "focus_on": "Business outcomes not tech", "offer": "Internal AI Playbook Product could adapt"}, "how_to_build_relationship": ["Quarterly share-outs", "Position as internal beta tester", "Create one-page case studies"], "influence_on_ai_adoption": "Indirect but significant. Senior leader shaping executive perception.", "north_star": "Frame success by organizational velocity, friction reduction, de-risking AI adoption"}'::JSONB,
    updated_at = NOW()
WHERE name = 'Michael Stratton' AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- ============================================================================
-- STEP 9: Set up reporting relationships
-- ============================================================================
UPDATE stakeholders
SET reports_to = (SELECT id FROM stakeholders WHERE name = 'Chad Meek' AND client_id = '00000000-0000-0000-0000-000000000001'::UUID LIMIT 1)
WHERE name = 'Jon Eakin' AND client_id = '00000000-0000-0000-0000-000000000001'::UUID;

-- ============================================================================
-- VERIFICATION
-- ============================================================================
SELECT name, role, department, engagement_level, alignment_score
FROM stakeholders
WHERE client_id = '00000000-0000-0000-0000-000000000001'::UUID
ORDER BY department, name;
