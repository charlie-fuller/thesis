-- Migration: Add Panel Edge Styling to Theme Settings
-- Allows customization of panel/card border thickness, color, and shadow

-- Add panel border width (e.g., '1px', '2px')
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS panel_border_width VARCHAR(10) DEFAULT '1px';

-- Add panel border color (hex color)
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS panel_border_color VARCHAR(7) DEFAULT '#27272a';

-- Add panel shadow size for depth effect (e.g., '0px', '4px', '8px')
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS panel_shadow_size VARCHAR(10) DEFAULT '1px';

-- Add panel shadow color (hex color)
ALTER TABLE theme_settings
ADD COLUMN IF NOT EXISTS panel_shadow_color VARCHAR(9) DEFAULT '#000000';

-- Add comment
COMMENT ON COLUMN theme_settings.panel_border_width IS 'Border thickness for cards/panels (e.g., 1px, 2px)';
COMMENT ON COLUMN theme_settings.panel_border_color IS 'Border color for cards/panels (hex)';
COMMENT ON COLUMN theme_settings.panel_shadow_size IS 'Shadow blur radius for depth effect (e.g., 0px, 4px, 8px)';
COMMENT ON COLUMN theme_settings.panel_shadow_color IS 'Shadow color for depth effect (hex)';
