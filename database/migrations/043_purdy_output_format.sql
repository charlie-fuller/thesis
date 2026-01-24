-- Add output_format column to track format used for PuRDy outputs
-- Values: comprehensive (default), executive, brief

-- Add output_format column to purdy_outputs
ALTER TABLE purdy_outputs
ADD COLUMN IF NOT EXISTS output_format TEXT DEFAULT 'comprehensive';

-- Add index for filtering by format
CREATE INDEX IF NOT EXISTS idx_purdy_outputs_format
ON purdy_outputs(initiative_id, output_format);

-- Add comment for documentation
COMMENT ON COLUMN purdy_outputs.output_format IS 'Output format used: comprehensive, executive, or brief';
