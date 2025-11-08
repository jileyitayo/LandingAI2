-- =====================================================
-- Add SYSTEM to action_type enum
-- Version: 1.0
-- Created: 2025-11-08
-- =====================================================

-- Add SYSTEM to the action_type enum
DO $$
BEGIN
    -- Check if SYSTEM already exists in the enum
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_enum 
        WHERE enumlabel = 'SYSTEM' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'action_type')
    ) THEN
        -- Add SYSTEM to the enum
        ALTER TYPE public.action_type ADD VALUE 'SYSTEM';
    END IF;
END $$;

-- Comments
COMMENT ON TYPE public.action_type IS 'Action types: CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, AUTHENTICATION, AUTHORIZATION, OTHER, SYSTEM';
