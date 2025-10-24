-- =====================================================
-- Create AI Call Logs Table
-- Version: 1.0
-- Created: 2025-10-24
-- Description: Create ai_call_logs table for per-minute rate limiting (sliding window)
-- =====================================================

-- =====================================================
-- SECTION 1: CREATE TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.ai_call_logs (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign keys
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,

    -- Call information
    call_type TEXT NOT NULL CHECK (call_type IN ('generation', 'edit', 'question')),

    -- Optional metadata
    endpoint TEXT, -- e.g., '/generate_website', '/edit/project/{id}'
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamp (critical for sliding window)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- SECTION 2: CREATE INDEXES
-- =====================================================

-- Critical index for sliding window queries: (user_id, created_at DESC)
-- This index enables fast queries like: WHERE user_id = X AND created_at >= NOW() - INTERVAL '60 seconds'
CREATE INDEX IF NOT EXISTS idx_ai_call_logs_user_created ON public.ai_call_logs(user_id, created_at DESC);

-- Additional indexes
CREATE INDEX IF NOT EXISTS idx_ai_call_logs_project_id ON public.ai_call_logs(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ai_call_logs_call_type ON public.ai_call_logs(call_type);
CREATE INDEX IF NOT EXISTS idx_ai_call_logs_created_at ON public.ai_call_logs(created_at DESC);

-- =====================================================
-- SECTION 3: ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

ALTER TABLE public.ai_call_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own AI call logs
CREATE POLICY "Users can view own AI call logs"
ON public.ai_call_logs FOR SELECT
USING (auth.uid() = user_id);

-- Note: Only service role can INSERT call logs (via rate limiter)

-- =====================================================
-- SECTION 4: GRANTS AND PERMISSIONS
-- =====================================================

-- Grant SELECT to authenticated users (for usage tracking)
GRANT SELECT ON public.ai_call_logs TO authenticated;

-- =====================================================
-- SECTION 5: CREATE CLEANUP FUNCTION (OPTIONAL)
-- =====================================================

-- Function to clean up old AI call logs (older than 7 days)
-- This prevents the table from growing indefinitely
CREATE OR REPLACE FUNCTION public.cleanup_old_ai_call_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM public.ai_call_logs
    WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.cleanup_old_ai_call_logs IS 'Deletes AI call logs older than 7 days. Can be run via cron job or pg_cron extension.';

-- Optional: Schedule automatic cleanup using pg_cron (if extension is enabled)
-- SELECT cron.schedule('cleanup-ai-call-logs', '0 2 * * *', 'SELECT public.cleanup_old_ai_call_logs()');

-- =====================================================
-- SECTION 6: ADD COMMENTS
-- =====================================================

COMMENT ON TABLE public.ai_call_logs IS 'Logs all AI calls for per-minute rate limiting using sliding window approach';
COMMENT ON COLUMN public.ai_call_logs.call_type IS 'Type of AI call: generation (new website), edit (component modification), question (chat)';
COMMENT ON COLUMN public.ai_call_logs.created_at IS 'Timestamp used for sliding window rate limiting (last 60 seconds)';
COMMENT ON INDEX idx_ai_call_logs_user_created IS 'Critical index for fast sliding window queries in rate limiting';

-- =====================================================
-- MIGRATION COMPLETE
-- Created: ai_call_logs table with sliding window support
-- =====================================================
