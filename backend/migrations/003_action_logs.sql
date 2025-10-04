-- =====================================================
-- Action Logs Table - Auditing and Observability
-- Version: 1.0
-- Created: 2025-10-03
-- =====================================================

-- Enum for action types
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'action_type') THEN
        CREATE TYPE public.action_type AS ENUM (
            'CREATE',
            'READ',
            'UPDATE',
            'DELETE',
            'LOGIN',
            'LOGOUT',
            'AUTHENTICATION',
            'AUTHORIZATION',
            'OTHER'
        );
    END IF;
END $$;

-- Action logs table
CREATE TABLE IF NOT EXISTS public.action_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id UUID,
    action_name TEXT NOT NULL,
    action_type public.action_type,
    success BOOLEAN NOT NULL,
    duration_ms INTEGER,
    ip_address INET,
    user_agent TEXT,
    http_method VARCHAR(10),
    path TEXT,
    status_code INTEGER,
    request_payload JSONB,
    response_payload JSONB,
    error_message TEXT,
    error_details JSONB,
    target_resource_type TEXT,
    target_resource_id TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_action_logs_timestamp ON public.action_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_action_logs_user_id ON public.action_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_action_logs_action_name ON public.action_logs(action_name);
CREATE INDEX IF NOT EXISTS idx_action_logs_action_type ON public.action_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_action_logs_path ON public.action_logs(path);

-- Comments
COMMENT ON TABLE public.action_logs IS 'Stores logs of actions performed by users and system processes.';
COMMENT ON COLUMN public.action_logs.user_id IS 'The user who performed the action. Nullable for anonymous/system.';
COMMENT ON COLUMN public.action_logs.request_payload IS 'Sanitized request snapshot. Avoid sensitive data.';
COMMENT ON COLUMN public.action_logs.response_payload IS 'Sanitized response snapshot. Avoid sensitive data.';
COMMENT ON COLUMN public.action_logs.target_resource_type IS 'Type of resource acted upon (e.g., user_profile).';
COMMENT ON COLUMN public.action_logs.target_resource_id IS 'Identifier of the resource acted upon.';


