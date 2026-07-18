-- Migration: Store the LLM-polished generation prompt alongside the raw one
-- Date: 2026-07-18
-- Run manually in the Supabase SQL editor.

ALTER TABLE public.projects
    ADD COLUMN IF NOT EXISTS polished_prompt TEXT;

COMMENT ON COLUMN public.projects.polished_prompt IS 'Detailed build spec produced by the intent-preflight polisher (analysis_model) from the raw prompt; what generation actually consumed. NULL when the polish failed or preflight was disabled. Internal-only, not surfaced in the UI.';
