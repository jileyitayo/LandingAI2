-- =====================================================
-- Add design_tokens column to projects table
-- Version: 1.0
-- Created: 2025-11-05
-- Description: Adds JSONB column to store extracted design tokens (colors, fonts, spacing)
--              for the click-to-edit visual editing system
-- =====================================================

-- Add design_tokens column to projects table
ALTER TABLE public.projects
ADD COLUMN IF NOT EXISTS design_tokens JSONB DEFAULT NULL;

-- Create index for design_tokens queries
CREATE INDEX IF NOT EXISTS idx_projects_design_tokens 
ON public.projects USING GIN (design_tokens) 
WHERE design_tokens IS NOT NULL;

-- Add comment to explain the design_tokens column
COMMENT ON COLUMN public.projects.design_tokens IS 'Extracted design system tokens (colors, fonts, spacing, etc.) for visual editing';

-- Example of what design_tokens might contain:
-- {
--   "colors": {
--     "primary": "#3b82f6",
--     "secondary": "#6366f1",
--     "background": "#ffffff",
--     "text": "#1f2937"
--   },
--   "fonts": {
--     "heading": "Inter",
--     "body": "Roboto"
--   },
--   "spacing": {
--     "base": "1rem",
--     "small": "0.5rem",
--     "large": "2rem"
--   },
--   "borderRadius": {
--     "small": "0.25rem",
--     "medium": "0.5rem",
--     "large": "1rem"
--   },
--   "shadows": {
--     "small": "0 1px 2px rgba(0, 0, 0, 0.05)",
--     "medium": "0 4px 6px rgba(0, 0, 0, 0.1)",
--     "large": "0 10px 15px rgba(0, 0, 0, 0.1)"
--   }
-- }

