-- =====================================================
-- Avatar Storage Setup Migration
-- Version: 1.1
-- Created: 2025-10-03
-- Description: Set up Supabase Storage for user avatars
-- =====================================================

-- =====================================================
-- SECTION 1: CREATE STORAGE BUCKET
-- =====================================================

-- Create public avatars bucket
-- Note: If bucket already exists, this will fail gracefully
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'avatars',
    'avatars',
    true,  -- Public bucket for avatars
    5242880,  -- 5MB limit
    ARRAY['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- END SECTION 1: CREATE STORAGE BUCKET
-- =====================================================


-- =====================================================
-- SECTION 2: STORAGE RLS POLICIES
-- =====================================================

-- Enable RLS on storage.objects
-- ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy: Users can upload their own avatars
-- Files must be in a folder named with their user ID
CREATE POLICY "Users can upload their own avatar"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'avatars' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy: Users can update their own avatars
CREATE POLICY "Users can update their own avatar"
ON storage.objects FOR UPDATE
TO authenticated
USING (
    bucket_id = 'avatars' AND
    auth.uid()::text = (storage.foldername(name))[1]
)
WITH CHECK (
    bucket_id = 'avatars' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy: Users can delete their own avatars
CREATE POLICY "Users can delete their own avatar"
ON storage.objects FOR DELETE
TO authenticated
USING (
    bucket_id = 'avatars' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy: Anyone can view avatars (public bucket)
CREATE POLICY "Anyone can view avatars"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'avatars');

-- =====================================================
-- END SECTION 2: STORAGE RLS POLICIES
-- =====================================================


-- =====================================================
-- SECTION 3: CLEANUP FUNCTION (OPTIONAL)
-- =====================================================

-- Function to clean up old avatar files when a new one is uploaded
-- This prevents accumulation of unused avatar files
CREATE OR REPLACE FUNCTION public.cleanup_old_avatars()
RETURNS TRIGGER AS $$
BEGIN
    -- When avatar_url is updated, delete the old file from storage
    IF OLD.avatar_url IS NOT NULL AND NEW.avatar_url IS DISTINCT FROM OLD.avatar_url THEN
        -- Extract the file path from the old avatar URL
        -- This is a best-effort cleanup; errors are ignored
        BEGIN
            -- Note: This requires the storage API to be accessible from database functions
            -- In practice, you might want to handle cleanup in the application layer
            NULL; -- Placeholder for cleanup logic
        EXCEPTION WHEN OTHERS THEN
            -- Ignore errors during cleanup
            NULL;
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to cleanup old avatars on update
-- Note: Commented out by default as cleanup is handled in application code
-- CREATE TRIGGER cleanup_old_avatars_trigger
--     BEFORE UPDATE OF avatar_url ON public.users
--     FOR EACH ROW
--     EXECUTE FUNCTION public.cleanup_old_avatars();

-- =====================================================
-- END SECTION 3: CLEANUP FUNCTION
-- =====================================================


-- =====================================================
-- MIGRATION COMPLETE
-- Storage Setup Version: 1.1
-- Bucket Created: avatars
-- Total Policies: 4
-- =====================================================

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify bucket was created
-- SELECT * FROM storage.buckets WHERE id = 'avatars';

-- Verify policies were created
-- SELECT * FROM pg_policies WHERE tablename = 'objects' AND policyname LIKE '%avatar%';

-- Test upload permission (as authenticated user)
-- Should return true for your own user_id folder
-- SELECT auth.uid()::text = (storage.foldername('USER_ID/test.jpg'))[1];

-- =====================================================

