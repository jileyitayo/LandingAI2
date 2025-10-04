-- =====================================================
-- Migration: Add created_by column to templates table
-- Version: 006
-- Created: 2025-01-27
-- Description: Adds created_by column to templates table for tracking template creator
-- =====================================================

-- Add created_by column to templates table
ALTER TABLE public.templates 
ADD COLUMN IF NOT EXISTS created_by TEXT;

-- Add comment to the new column
COMMENT ON COLUMN public.templates.created_by IS 'User ID or identifier of who created this template (for system templates, this could be "system" or admin user ID)';

-- Create index for created_by column for better query performance
CREATE INDEX IF NOT EXISTS idx_templates_created_by ON public.templates(created_by) WHERE created_by IS NOT NULL;

-- =====================================================
-- MIGRATION COMPLETE
-- Schema Version: 006
-- Changes: Added created_by column to templates table
-- =====================================================
