-- Migration: Add last_edited_at to projects table
-- Stamped whenever an edit (AI component edit or property edit) is saved.
-- Compared against last_deployed_at to show the "Unpublished changes" badge.

-- Add last_edited_at column to projects table
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS last_edited_at TIMESTAMPTZ;

-- Add comment
COMMENT ON COLUMN projects.last_edited_at IS 'Timestamp of the most recent saved edit to the project files';
