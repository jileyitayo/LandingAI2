-- Migration: Add deploy progress tracking + favicon to projects
-- Description: Async publish with staged progress (queued/uploading/building/ready/error)
--              polled by the frontend, plus favicon_url for the settings page.
-- Date: 2026-07-03

ALTER TABLE public.projects
    ADD COLUMN IF NOT EXISTS deploy_status VARCHAR(20) DEFAULT 'idle'
        CHECK (deploy_status IN ('idle', 'queued', 'uploading', 'building', 'ready', 'error')),
    ADD COLUMN IF NOT EXISTS deploy_stage_detail TEXT,
    ADD COLUMN IF NOT EXISTS deploy_error TEXT,
    ADD COLUMN IF NOT EXISTS favicon_url TEXT;

COMMENT ON COLUMN public.projects.deploy_status IS 'Async deploy progress: idle|queued|uploading|building|ready|error';
COMMENT ON COLUMN public.projects.deploy_error IS 'Last deploy failure message (cleared on next deploy)';
COMMENT ON COLUMN public.projects.favicon_url IS 'Uploaded favicon public URL (project-media bucket)';

-- Verification:
-- SELECT column_name FROM information_schema.columns WHERE table_name='projects' AND column_name LIKE 'deploy%';
