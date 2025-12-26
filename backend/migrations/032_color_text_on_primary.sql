-- Migration: Add button text color columns
-- Allows customizing button text colors for proper contrast

-- Primary button text color (colored buttons)
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS color_text_on_primary VARCHAR(7) DEFAULT '#ffffff';

-- Secondary button text color (outline/light buttons)
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS color_text_on_secondary VARCHAR(7) DEFAULT '#ffffff';

-- Add comments for documentation
COMMENT ON COLUMN theme_settings.color_text_on_primary IS 'Text color for primary buttons (should contrast with color_primary)';
COMMENT ON COLUMN theme_settings.color_text_on_secondary IS 'Text color for secondary/outline buttons (should contrast with color_bg_card)';
