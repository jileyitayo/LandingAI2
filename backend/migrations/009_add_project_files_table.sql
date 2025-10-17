-- Migration: Add project_files table for React file storage
-- Description: Store individual React project files for better scalability
-- Date: 2025-10-14

-- =====================================================
-- Create project_files table
-- =====================================================

CREATE TABLE IF NOT EXISTS public.project_files (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    
    -- File information
    file_path TEXT NOT NULL, -- e.g., 'src/components/Hero.tsx'
    file_content TEXT NOT NULL, -- The actual file content
    file_type VARCHAR(50), -- 'component', 'page', 'config', 'style', etc.
    file_size INTEGER, -- Size in bytes for monitoring
    
    -- Metadata
    content_hash VARCHAR(64), -- SHA-256 hash for change detection
    is_generated BOOLEAN DEFAULT true, -- vs user-edited
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Unique constraint: one file path per project
    UNIQUE(project_id, file_path)
);

-- =====================================================
-- Indexes for performance
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_project_files_project_id 
    ON public.project_files(project_id);

CREATE INDEX IF NOT EXISTS idx_project_files_file_type 
    ON public.project_files(file_type) WHERE file_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_project_files_file_path 
    ON public.project_files(project_id, file_path);

-- =====================================================
-- Add columns to projects table
-- =====================================================

ALTER TABLE public.projects
ADD COLUMN IF NOT EXISTS project_type VARCHAR(20) DEFAULT 'html' CHECK (project_type IN ('html', 'react')),
ADD COLUMN IF NOT EXISTS files_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS website_structure JSONB,
ADD COLUMN IF NOT EXISTS business_analysis JSONB,
ADD COLUMN IF NOT EXISTS validation_result JSONB,
ADD COLUMN IF NOT EXISTS generation_metadata JSONB;

-- Add index on project_type
CREATE INDEX IF NOT EXISTS idx_projects_project_type 
    ON public.projects(project_type);
-- Add GIN indexes for JSONB columns (enables fast JSON queries)
CREATE INDEX IF NOT EXISTS idx_projects_website_structure 
    ON public.projects USING GIN (website_structure) WHERE website_structure IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_projects_business_analysis 
    ON public.projects USING GIN (business_analysis) WHERE business_analysis IS NOT NULL;

-- =====================================================
-- Triggers
-- =====================================================

-- Trigger for updated_at on project_files
CREATE TRIGGER update_project_files_updated_at
    BEFORE UPDATE ON public.project_files
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Function to update files_count in projects table
CREATE OR REPLACE FUNCTION update_project_files_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the files_count in projects table
    UPDATE public.projects
    SET files_count = (
        SELECT COUNT(*) 
        FROM public.project_files 
        WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
    )
    WHERE id = COALESCE(NEW.project_id, OLD.project_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger to update files_count on insert/update/delete
CREATE TRIGGER update_files_count_on_insert
    AFTER INSERT ON public.project_files
    FOR EACH ROW
    EXECUTE FUNCTION update_project_files_count();

CREATE TRIGGER update_files_count_on_delete
    AFTER DELETE ON public.project_files
    FOR EACH ROW
    EXECUTE FUNCTION update_project_files_count();

-- =====================================================
-- RLS Policies
-- =====================================================

ALTER TABLE public.project_files ENABLE ROW LEVEL SECURITY;

-- Users can view files for their own projects
CREATE POLICY "Users can view own project files"
ON public.project_files FOR SELECT
USING (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- Users can insert files for their own projects
CREATE POLICY "Users can insert own project files"
ON public.project_files FOR INSERT
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- Users can update files for their own projects
CREATE POLICY "Users can update own project files"
ON public.project_files FOR UPDATE
USING (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- Users can delete files for their own projects
CREATE POLICY "Users can delete own project files"
ON public.project_files FOR DELETE
USING (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- =====================================================
-- Grants
-- =====================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_files TO authenticated;

-- =====================================================
-- Comments
-- =====================================================

COMMENT ON TABLE public.project_files IS 'Individual files for React/website projects';
COMMENT ON COLUMN public.project_files.file_path IS 'Relative path within project (e.g., src/App.tsx)';
COMMENT ON COLUMN public.project_files.content_hash IS 'SHA-256 hash for detecting changes';
COMMENT ON COLUMN public.projects.website_structure IS 'Website structure metadata (pages, components, navigation) for React projects';
COMMENT ON COLUMN public.projects.business_analysis IS 'AI-generated business analysis (business type, target audience, etc.)';
COMMENT ON COLUMN public.projects.validation_result IS 'Code validation and build test results';
COMMENT ON COLUMN public.projects.generation_metadata IS 'Additional generation metadata (retry_count, fixed_errors, generation_time, etc.)';