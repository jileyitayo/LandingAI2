-- Migration: Add project media storage
-- Description: Table + storage bucket for user-uploaded media (images now, video later)
--              used as chat attachments, site assets, and favicons.
-- Date: 2026-07-03

-- =====================================================
-- Create project_media table
-- =====================================================

CREATE TABLE IF NOT EXISTS public.project_media (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- Nullable: dashboard uploads happen before a project exists;
    -- linked to the project after generation creates the row.
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Media info
    media_type VARCHAR(20) NOT NULL DEFAULT 'image' CHECK (media_type IN ('image', 'video')),
    storage_path TEXT NOT NULL,           -- {user_id}/{uuid}.{ext} in the project-media bucket
    public_url TEXT NOT NULL,
    original_filename TEXT,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,

    -- Advisory purpose tag: 'attachment' | 'favicon' | ...
    purpose VARCHAR(30) DEFAULT 'attachment',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- Indexes
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_project_media_project_id
    ON public.project_media(project_id);

CREATE INDEX IF NOT EXISTS idx_project_media_user_id
    ON public.project_media(user_id);

CREATE INDEX IF NOT EXISTS idx_project_media_created_at
    ON public.project_media(user_id, created_at DESC);

-- =====================================================
-- RLS Policies
-- =====================================================

ALTER TABLE public.project_media ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own media"
ON public.project_media FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY "Users can insert own media"
ON public.project_media FOR INSERT
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own media"
ON public.project_media FOR UPDATE
USING (user_id = auth.uid());

CREATE POLICY "Users can delete own media"
ON public.project_media FOR DELETE
USING (user_id = auth.uid());

GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_media TO authenticated;

-- =====================================================
-- Storage bucket: project-media
-- Public: generated sites and Vercel deployments hot-link these URLs.
-- =====================================================

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'project-media',
    'project-media',
    true,
    10485760,  -- 10MB
    ARRAY['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS (belt-and-braces; backend uses the service-role client)
CREATE POLICY "Users can upload their own project media"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'project-media' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can update their own project media"
ON storage.objects FOR UPDATE
TO authenticated
USING (
    bucket_id = 'project-media' AND
    auth.uid()::text = (storage.foldername(name))[1]
)
WITH CHECK (
    bucket_id = 'project-media' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can delete their own project media"
ON storage.objects FOR DELETE
TO authenticated
USING (
    bucket_id = 'project-media' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Anyone can view project media"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'project-media');

-- =====================================================
-- Comments
-- =====================================================

COMMENT ON TABLE public.project_media IS 'User-uploaded media (chat attachments, site assets, favicons)';
COMMENT ON COLUMN public.project_media.project_id IS 'NULL until linked to a project (dashboard uploads happen pre-generation)';
COMMENT ON COLUMN public.project_media.purpose IS 'Advisory tag: attachment, favicon, ...';

-- =====================================================
-- Verification
-- =====================================================
-- SELECT * FROM storage.buckets WHERE id = 'project-media';
-- SELECT * FROM pg_policies WHERE tablename = 'project_media';
