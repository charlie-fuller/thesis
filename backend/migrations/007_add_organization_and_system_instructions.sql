-- Migration: Add organization and system_instructions to clients table
-- Date: 2025-11-06
-- Purpose: Support Solomon Stage 2 system instructions generation

-- Add organization column (optional, for customizing instructions)
ALTER TABLE clients
ADD COLUMN IF NOT EXISTS organization TEXT;

-- Add system_instructions column (stores generated instructions)
ALTER TABLE clients
ADD COLUMN IF NOT EXISTS system_instructions TEXT;

-- Add comment for documentation
COMMENT ON COLUMN clients.organization IS 'Client organization name, used for customizing system instructions';
COMMENT ON COLUMN clients.system_instructions IS 'Generated system instructions from Solomon Stage 2';
