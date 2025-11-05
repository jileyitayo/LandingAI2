-- Migration: Add preview_id to projects table for fast HMR updates
-- This allows us to track which preview build belongs to each project
-- so we can update existing previews instead of creating new ones

-- Add preview_id column to projects table
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS preview_id TEXT;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_projects_preview_id ON projects(preview_id);

-- Add comment
COMMENT ON COLUMN projects.preview_id IS 'UUID of the active Vite preview build for this project';

