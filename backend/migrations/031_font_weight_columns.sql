-- Migration: Add Font Weight Columns to Theme Settings
-- Allows customization of heading and body font weights

-- Add heading font weight
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS font_weight_heading VARCHAR(10) DEFAULT '600';

-- Add body font weight
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS font_weight_body VARCHAR(10) DEFAULT '400';

-- Add comments
COMMENT ON COLUMN theme_settings.font_weight_heading IS 'Font weight for headings (e.g., 400, 500, 600, 700)';
COMMENT ON COLUMN theme_settings.font_weight_body IS 'Font weight for body text (e.g., 400, 500, 600, 700)';
