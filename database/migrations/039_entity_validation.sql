-- Migration: 039_entity_validation.sql
-- Entity Validation System for correcting transcription errors
-- Created: 2026-01-23

-- =============================================================================
-- ORGANIZATION REGISTRY
-- Ground truth for company/organization names with known aliases
-- =============================================================================
CREATE TABLE IF NOT EXISTS organization_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    canonical_name TEXT NOT NULL,
    aliases TEXT[] DEFAULT '{}',
    domain TEXT,
    industry TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, canonical_name)
);

CREATE INDEX idx_org_registry_client ON organization_registry(client_id);
CREATE INDEX idx_org_registry_canonical ON organization_registry(canonical_name);
CREATE INDEX idx_org_registry_aliases ON organization_registry USING GIN(aliases);

-- =============================================================================
-- PERSON NAME REGISTRY
-- Known person names with phonetic codes for sound-alike matching
-- =============================================================================
CREATE TABLE IF NOT EXISTS person_name_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    canonical_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    aliases TEXT[] DEFAULT '{}',
    metaphone_first TEXT,
    metaphone_last TEXT,
    stakeholder_id UUID REFERENCES stakeholders(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, canonical_name)
);

CREATE INDEX idx_person_registry_client ON person_name_registry(client_id);
CREATE INDEX idx_person_registry_canonical ON person_name_registry(canonical_name);
CREATE INDEX idx_person_registry_aliases ON person_name_registry USING GIN(aliases);
CREATE INDEX idx_person_registry_metaphone ON person_name_registry(metaphone_first, metaphone_last);
CREATE INDEX idx_person_registry_stakeholder ON person_name_registry(stakeholder_id);

-- =============================================================================
-- ENTITY CORRECTIONS
-- History of user corrections for learning
-- =============================================================================
CREATE TABLE IF NOT EXISTS entity_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('person', 'organization')),
    original_value TEXT NOT NULL,
    corrected_value TEXT NOT NULL,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    source_candidate_id UUID,
    corrected_by UUID REFERENCES users(id) ON DELETE SET NULL,
    correction_context TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_corrections_client ON entity_corrections(client_id);
CREATE INDEX idx_corrections_type ON entity_corrections(entity_type);
CREATE INDEX idx_corrections_original ON entity_corrections(original_value);
CREATE INDEX idx_corrections_created ON entity_corrections(created_at DESC);

-- =============================================================================
-- ENTITY VALIDATION RESULTS
-- Audit trail of validation decisions
-- =============================================================================
CREATE TABLE IF NOT EXISTS entity_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('person', 'organization')),
    original_value TEXT NOT NULL,
    validation_status TEXT NOT NULL CHECK (validation_status IN (
        'exact_match', 'alias_match', 'fuzzy_match', 'phonetic_match',
        'new_entity', 'potential_error'
    )),
    suggested_value TEXT,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    match_reason TEXT,
    registry_entry_id UUID,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_validation_client ON entity_validation_results(client_id);
CREATE INDEX idx_validation_status ON entity_validation_results(validation_status);
CREATE INDEX idx_validation_created ON entity_validation_results(created_at DESC);

-- =============================================================================
-- EXTEND STAKEHOLDER_CANDIDATES WITH VALIDATION FIELDS
-- =============================================================================
ALTER TABLE stakeholder_candidates
    ADD COLUMN IF NOT EXISTS name_validation_status TEXT CHECK (name_validation_status IN (
        'validated', 'suggested_correction', 'new', 'potential_error'
    )),
    ADD COLUMN IF NOT EXISTS name_suggested_correction TEXT,
    ADD COLUMN IF NOT EXISTS name_validation_confidence FLOAT CHECK (
        name_validation_confidence IS NULL OR
        (name_validation_confidence >= 0 AND name_validation_confidence <= 1)
    ),
    ADD COLUMN IF NOT EXISTS org_validation_status TEXT CHECK (org_validation_status IN (
        'validated', 'suggested_correction', 'new', 'potential_error'
    )),
    ADD COLUMN IF NOT EXISTS org_suggested_correction TEXT,
    ADD COLUMN IF NOT EXISTS org_validation_confidence FLOAT CHECK (
        org_validation_confidence IS NULL OR
        (org_validation_confidence >= 0 AND org_validation_confidence <= 1)
    );

-- =============================================================================
-- RPC FUNCTION: Search organization registry with fuzzy matching
-- =============================================================================
CREATE OR REPLACE FUNCTION search_organization_registry(
    p_client_id UUID,
    p_search_term TEXT,
    p_limit INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    canonical_name TEXT,
    aliases TEXT[],
    match_type TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.canonical_name,
        o.aliases,
        CASE
            WHEN LOWER(o.canonical_name) = LOWER(p_search_term) THEN 'exact'
            WHEN LOWER(p_search_term) = ANY(SELECT LOWER(unnest(o.aliases))) THEN 'alias'
            ELSE 'fuzzy'
        END AS match_type,
        similarity(LOWER(o.canonical_name), LOWER(p_search_term)) AS similarity
    FROM organization_registry o
    WHERE o.client_id = p_client_id
        AND (
            LOWER(o.canonical_name) = LOWER(p_search_term)
            OR LOWER(p_search_term) = ANY(SELECT LOWER(unnest(o.aliases)))
            OR similarity(LOWER(o.canonical_name), LOWER(p_search_term)) > 0.3
        )
    ORDER BY
        CASE WHEN LOWER(o.canonical_name) = LOWER(p_search_term) THEN 0
             WHEN LOWER(p_search_term) = ANY(SELECT LOWER(unnest(o.aliases))) THEN 1
             ELSE 2 END,
        similarity(LOWER(o.canonical_name), LOWER(p_search_term)) DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- RPC FUNCTION: Search person name registry with phonetic matching
-- =============================================================================
CREATE OR REPLACE FUNCTION search_person_registry(
    p_client_id UUID,
    p_search_term TEXT,
    p_metaphone_first TEXT DEFAULT NULL,
    p_metaphone_last TEXT DEFAULT NULL,
    p_limit INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    canonical_name TEXT,
    aliases TEXT[],
    stakeholder_id UUID,
    match_type TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.canonical_name,
        p.aliases,
        p.stakeholder_id,
        CASE
            WHEN LOWER(p.canonical_name) = LOWER(p_search_term) THEN 'exact'
            WHEN LOWER(p_search_term) = ANY(SELECT LOWER(unnest(p.aliases))) THEN 'alias'
            WHEN p_metaphone_first IS NOT NULL
                AND p.metaphone_first = p_metaphone_first
                AND (p_metaphone_last IS NULL OR p.metaphone_last = p_metaphone_last) THEN 'phonetic'
            ELSE 'fuzzy'
        END AS match_type,
        similarity(LOWER(p.canonical_name), LOWER(p_search_term)) AS similarity
    FROM person_name_registry p
    WHERE p.client_id = p_client_id
        AND (
            LOWER(p.canonical_name) = LOWER(p_search_term)
            OR LOWER(p_search_term) = ANY(SELECT LOWER(unnest(p.aliases)))
            OR (p_metaphone_first IS NOT NULL
                AND p.metaphone_first = p_metaphone_first
                AND (p_metaphone_last IS NULL OR p.metaphone_last = p_metaphone_last))
            OR similarity(LOWER(p.canonical_name), LOWER(p_search_term)) > 0.3
        )
    ORDER BY
        CASE WHEN LOWER(p.canonical_name) = LOWER(p_search_term) THEN 0
             WHEN LOWER(p_search_term) = ANY(SELECT LOWER(unnest(p.aliases))) THEN 1
             WHEN p_metaphone_first IS NOT NULL AND p.metaphone_first = p_metaphone_first THEN 2
             ELSE 3 END,
        similarity(LOWER(p.canonical_name), LOWER(p_search_term)) DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- RPC FUNCTION: Add alias to organization
-- =============================================================================
CREATE OR REPLACE FUNCTION add_organization_alias(
    p_org_id UUID,
    p_alias TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE organization_registry
    SET
        aliases = array_append(
            array_remove(aliases, p_alias),  -- Remove if exists (dedup)
            p_alias
        ),
        updated_at = NOW()
    WHERE id = p_org_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- RPC FUNCTION: Add alias to person name
-- =============================================================================
CREATE OR REPLACE FUNCTION add_person_alias(
    p_person_id UUID,
    p_alias TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE person_name_registry
    SET
        aliases = array_append(
            array_remove(aliases, p_alias),  -- Remove if exists (dedup)
            p_alias
        ),
        updated_at = NOW()
    WHERE id = p_person_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ENABLE pg_trgm EXTENSION (for similarity function)
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =============================================================================
-- ROW LEVEL SECURITY
-- =============================================================================
ALTER TABLE organization_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE person_name_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE entity_corrections ENABLE ROW LEVEL SECURITY;
ALTER TABLE entity_validation_results ENABLE ROW LEVEL SECURITY;

-- Policies for organization_registry
CREATE POLICY "Users can view their client's organization registry"
    ON organization_registry FOR SELECT
    USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can insert into their client's organization registry"
    ON organization_registry FOR INSERT
    WITH CHECK (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can update their client's organization registry"
    ON organization_registry FOR UPDATE
    USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

-- Policies for person_name_registry
CREATE POLICY "Users can view their client's person registry"
    ON person_name_registry FOR SELECT
    USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can insert into their client's person registry"
    ON person_name_registry FOR INSERT
    WITH CHECK (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can update their client's person registry"
    ON person_name_registry FOR UPDATE
    USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

-- Policies for entity_corrections
CREATE POLICY "Users can view their client's corrections"
    ON entity_corrections FOR SELECT
    USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can insert corrections"
    ON entity_corrections FOR INSERT
    WITH CHECK (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

-- Policies for entity_validation_results
CREATE POLICY "Users can view their client's validation results"
    ON entity_validation_results FOR SELECT
    USING (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can insert validation results"
    ON entity_validation_results FOR INSERT
    WITH CHECK (client_id IN (SELECT client_id FROM users WHERE id = auth.uid()));

-- Service role bypass for all tables
CREATE POLICY "Service role has full access to organization_registry"
    ON organization_registry FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to person_name_registry"
    ON person_name_registry FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to entity_corrections"
    ON entity_corrections FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to entity_validation_results"
    ON entity_validation_results FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
