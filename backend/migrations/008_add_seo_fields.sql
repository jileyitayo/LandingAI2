-- Migration: Add SEO fields to projects table
-- Description: Add seo_title and seo_description fields for better SEO control
-- Date: 2025-10-05

-- Add SEO fields to projects table
ALTER TABLE public.projects
ADD COLUMN IF NOT EXISTS seo_title VARCHAR(60),
ADD COLUMN IF NOT EXISTS seo_description VARCHAR(160);

-- Add comments for clarity
COMMENT ON COLUMN public.projects.seo_title IS 'SEO-optimized page title (max 60 chars for search engines)';
COMMENT ON COLUMN public.projects.seo_description IS 'SEO-optimized meta description (max 160 chars for search engines)';

-- Optional: Set default values based on existing data
UPDATE public.projects
SET seo_title = LEFT(name, 60)
WHERE seo_title IS NULL AND name IS NOT NULL;

UPDATE public.projects
SET seo_description = LEFT(description, 160)
WHERE seo_description IS NULL AND description IS NOT NULL;

