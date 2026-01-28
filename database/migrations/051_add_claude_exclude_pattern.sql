-- Migration: Add .claude/** and preserved-context patterns to vault config exclude patterns
-- This prevents Claude Code's internal files (compact-context, etc.) from being synced

-- Update all vault configs to include the Claude-related exclude patterns
-- Uses jsonb_set to append to the existing array if not already present

-- Add .claude/**
UPDATE obsidian_vault_configs
SET sync_options = jsonb_set(
    sync_options,
    '{exclude_patterns}',
    (
        SELECT jsonb_agg(DISTINCT elem)
        FROM (
            SELECT jsonb_array_elements(
                COALESCE(sync_options->'exclude_patterns', '[]'::jsonb)
            ) AS elem
            UNION
            SELECT '".claude/**"'::jsonb
        ) sub
    )
)
WHERE sync_options IS NOT NULL
  AND NOT (sync_options->'exclude_patterns' @> '".claude/**"'::jsonb);

-- Add **/.claude/** (for nested .claude folders like backend/.claude)
UPDATE obsidian_vault_configs
SET sync_options = jsonb_set(
    sync_options,
    '{exclude_patterns}',
    (
        SELECT jsonb_agg(DISTINCT elem)
        FROM (
            SELECT jsonb_array_elements(
                COALESCE(sync_options->'exclude_patterns', '[]'::jsonb)
            ) AS elem
            UNION
            SELECT '"**/.claude/**"'::jsonb
        ) sub
    )
)
WHERE sync_options IS NOT NULL
  AND NOT (sync_options->'exclude_patterns' @> '"**/.claude/**"'::jsonb);

-- Add **/preserved-context/** (catch-all for context files in any location)
UPDATE obsidian_vault_configs
SET sync_options = jsonb_set(
    sync_options,
    '{exclude_patterns}',
    (
        SELECT jsonb_agg(DISTINCT elem)
        FROM (
            SELECT jsonb_array_elements(
                COALESCE(sync_options->'exclude_patterns', '[]'::jsonb)
            ) AS elem
            UNION
            SELECT '"**/preserved-context/**"'::jsonb
        ) sub
    )
)
WHERE sync_options IS NOT NULL
  AND NOT (sync_options->'exclude_patterns' @> '"**/preserved-context/**"'::jsonb);

-- Report what was updated
DO $$
BEGIN
    RAISE NOTICE 'Added Claude exclude patterns (.claude/**, **/.claude/**, **/preserved-context/**) to vault configs';
END $$;
