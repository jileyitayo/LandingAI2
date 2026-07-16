-- Migration: Add custom domain support to projects (Pro tier feature)
-- Date: 2026-07-13
-- Run manually in the Supabase SQL editor.

ALTER TABLE public.projects
    ADD COLUMN IF NOT EXISTS custom_domain TEXT,
    ADD COLUMN IF NOT EXISTS custom_domain_status VARCHAR(20)
        CHECK (custom_domain_status IN ('pending_dns', 'verified', 'error')),
    ADD COLUMN IF NOT EXISTS custom_domain_error TEXT,
    ADD COLUMN IF NOT EXISTS custom_domain_updated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS vercel_project_id TEXT;

-- Global uniqueness, case-insensitive (NULLs exempt)
CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_custom_domain_unique
    ON public.projects (lower(custom_domain))
    WHERE custom_domain IS NOT NULL;

COMMENT ON COLUMN public.projects.custom_domain IS 'User-entered custom domain (lowercase, no scheme). The www/apex counterpart is auto-managed on Vercel, not stored.';
COMMENT ON COLUMN public.projects.custom_domain_status IS 'pending_dns|verified|error (cached; live-checked by GET /api/v1/projects/{id}/domain)';
COMMENT ON COLUMN public.projects.custom_domain_error IS 'Last hard failure message for the custom domain, if any';
COMMENT ON COLUMN public.projects.vercel_project_id IS 'Vercel projectId captured at deploy time; required for Vercel domain API calls';
