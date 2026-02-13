-- Migration: 073_solution_type_and_verdicts
-- Description: Add solution_type to bundles and initiative verdict support
-- for non-build outcomes in the DISCO pipeline.
-- Date: 2026-02-13

-- Solution type on bundles (extends beyond build/buy)
ALTER TABLE disco_bundles ADD COLUMN IF NOT EXISTS solution_type VARCHAR(20) DEFAULT NULL;
-- Valid values: build, buy, govern, coordinate, train, restructure, document, defer, accept
-- NULL means not yet assessed (backwards compatible)

-- Initiative verdict support (extends resolution_annotations)
-- These fields are added to resolution_annotations JSONB (no new column needed),
-- but we document the extended structure here:
-- resolution_annotations: {
--   hypothesis_overrides: { "h-1": { status, note } },
--   gap_overrides: { "g-2": { status, note } },
--   initiative_verdict: "proceed" | "defer" | "accept" | "no_action",
--   defer_until: "2026-Q3" or ISO date,
--   accept_rationale: "Cost of solving exceeds value; current workarounds adequate"
-- }

-- Document new initiative status values
-- Existing: draft, discovery, insights, synthesis, convergence, completed
-- New: deferred (conscious delay), accepted (acknowledged, no action), assessed (non-build outcome generated)
-- These are soft statuses stored in the existing status VARCHAR column

-- Add documentation comments
COMMENT ON COLUMN disco_bundles.solution_type IS 'Solution type taxonomy: build, buy, govern, coordinate, train, restructure, document, defer, accept';

-- Notify PostgREST to reload schema cache
SELECT pg_notify('pgrst', 'reload schema');
