-- Migration: Add project thumbnail URL
-- Description: Stores the public URL of the dashboard preview screenshot
--              captured after each successful deploy (ScreenshotOne -> project-media bucket).
-- Date: 2026-07-13

ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;

COMMENT ON COLUMN public.projects.thumbnail_url IS 'Public URL of the dashboard preview screenshot (project-media bucket, cache-busted with ?v=timestamp)';

-- =====================================================
-- Verification
-- =====================================================
-- SELECT column_name FROM information_schema.columns
--   WHERE table_name = 'projects' AND column_name = 'thumbnail_url';
