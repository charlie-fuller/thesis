-- Migration: 072_disco_restructure
-- Description: Add value alignment, sponsor/stakeholder, resolution annotation columns
-- to disco_initiatives and source tracking to project_tasks.
-- Date: 2026-02-12

-- Value alignment (flexible, not rigid hierarchy)
ALTER TABLE disco_initiatives ADD COLUMN IF NOT EXISTS target_department VARCHAR(100);
ALTER TABLE disco_initiatives ADD COLUMN IF NOT EXISTS value_alignment JSONB DEFAULT NULL;
-- Structure: { kpis: ["Time to fill", "Cost per hire"],
--              department_goals: ["Eliminate manual recruiting overhead"],
--              company_priority: "Cost-Efficient GTM Growth",
--              strategic_pillar: "operationalize",
--              notes: "Discovered during kickoff with Bella" }
-- All fields optional - populated as they become known during discovery

-- Sponsors and stakeholders
ALTER TABLE disco_initiatives ADD COLUMN IF NOT EXISTS sponsor_stakeholder_id UUID REFERENCES stakeholders(id);
ALTER TABLE disco_initiatives ADD COLUMN IF NOT EXISTS stakeholder_ids UUID[] DEFAULT '{}';

-- Resolution annotations (for feedback loop)
ALTER TABLE disco_initiatives ADD COLUMN IF NOT EXISTS resolution_annotations JSONB DEFAULT NULL;
-- Structure: { hypothesis_overrides: { "h-1": { status: "refuted", note: "Disproved in Q1 review" } },
--              gap_overrides: { "g-2": { status: "addressed", note: "Resolved with new tool" } } }

-- Triage suggestions (framing extraction from documents)
ALTER TABLE disco_outputs ADD COLUMN IF NOT EXISTS triage_suggestions JSONB DEFAULT NULL;
-- Structure: { problem_statements: [...], hypotheses: [...], gaps: [...], kpis: [...],
--              stakeholders: [...], value_alignment_notes: "..." }

-- Task source tracking back to DISCO
ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS source_initiative_id UUID REFERENCES disco_initiatives(id);
ALTER TABLE project_tasks ADD COLUMN IF NOT EXISTS source_disco_output_id UUID REFERENCES disco_outputs(id);

-- Add documentation comments
COMMENT ON COLUMN disco_initiatives.target_department IS 'Target department for this discovery (e.g., People, Engineering)';
COMMENT ON COLUMN disco_initiatives.value_alignment IS 'Flexible value alignment: kpis, department_goals, company_priority, strategic_pillar, notes';
COMMENT ON COLUMN disco_initiatives.sponsor_stakeholder_id IS 'Executive sponsor from stakeholders table';
COMMENT ON COLUMN disco_initiatives.stakeholder_ids IS 'Array of stakeholder UUIDs involved in this discovery';
COMMENT ON COLUMN disco_initiatives.resolution_annotations IS 'User annotations on hypothesis/gap resolutions: overrides and notes';
COMMENT ON COLUMN project_tasks.source_initiative_id IS 'DISCO initiative that generated this task';
COMMENT ON COLUMN project_tasks.source_disco_output_id IS 'DISCO output (convergence run) that generated this task';
