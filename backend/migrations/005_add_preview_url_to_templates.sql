-- =====================================================
-- Migration: Add preview_url column to templates table
-- Version: 005
-- Created: 2025-01-27
-- Description: Adds preview_url column to templates table for storing preview URLs
-- =====================================================

-- Add preview_url column to templates table
ALTER TABLE public.templates 
ADD COLUMN IF NOT EXISTS preview_url TEXT;

-- Add comment to the new column
COMMENT ON COLUMN public.templates.preview_url IS 'URL to preview the template (e.g., hosted preview URL)';

-- Create index for preview_url column for better query performance
CREATE INDEX IF NOT EXISTS idx_templates_preview_url ON public.templates(preview_url) WHERE preview_url IS NOT NULL;

-- =====================================================
-- MIGRATION COMPLETE
-- Schema Version: 005
-- Changes: Added preview_url column to templates table
-- =====================================================
