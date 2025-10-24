-- =====================================================
-- Update Users Table for Subscription System
-- Version: 1.0
-- Created: 2025-10-24
-- Description: Modify users table to support new subscription system
-- =====================================================

-- =====================================================
-- SECTION 1: ALTER USERS TABLE
-- =====================================================

-- Add new column for linking to subscription tier
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS current_tier_id UUID REFERENCES public.subscription_tiers(id) ON DELETE RESTRICT;

-- Add column to track last AI call for per-minute rate limiting
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS last_ai_call_at TIMESTAMPTZ;

-- Change current_period_start from DATE to TIMESTAMPTZ for precise time tracking
-- First, create a new column
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS current_period_start_tz TIMESTAMPTZ;

-- Migrate existing DATE values to TIMESTAMPTZ (set to midnight UTC)
UPDATE public.users
SET current_period_start_tz = current_period_start::timestamp AT TIME ZONE 'UTC'
WHERE current_period_start IS NOT NULL AND current_period_start_tz IS NULL;

-- Set default for new rows
UPDATE public.users
SET current_period_start_tz = NOW()
WHERE current_period_start_tz IS NULL;

-- Drop the old DATE column
ALTER TABLE public.users
DROP COLUMN IF EXISTS current_period_start;

-- Rename the new TIMESTAMPTZ column to current_period_start
ALTER TABLE public.users
RENAME COLUMN current_period_start_tz TO current_period_start;

-- Set NOT NULL constraint and default
ALTER TABLE public.users
ALTER COLUMN current_period_start SET NOT NULL,
ALTER COLUMN current_period_start SET DEFAULT NOW();

-- =====================================================
-- SECTION 2: CREATE INDEXES
-- =====================================================

-- Index for quickly looking up users by tier
CREATE INDEX IF NOT EXISTS idx_users_current_tier_id ON public.users(current_tier_id) WHERE current_tier_id IS NOT NULL;

-- Index for checking last AI call times (for per-minute rate limiting)
CREATE INDEX IF NOT EXISTS idx_users_last_ai_call_at ON public.users(last_ai_call_at DESC) WHERE last_ai_call_at IS NOT NULL;

-- =====================================================
-- SECTION 3: ADD COMMENTS
-- =====================================================

COMMENT ON COLUMN public.users.current_tier_id IS 'Foreign key to subscription_tiers - users current active tier';
COMMENT ON COLUMN public.users.last_ai_call_at IS 'Timestamp of last AI call - used for per-minute rate limiting (sliding window)';
COMMENT ON COLUMN public.users.current_period_start IS 'Start of current daily rate limit period (TIMESTAMPTZ for precise tracking)';
COMMENT ON COLUMN public.users.subscription_tier IS 'DEPRECATED: Use current_tier_id instead. Kept for backward compatibility.';

-- =====================================================
-- SECTION 4: VERIFY CHANGES
-- =====================================================

DO $$
DECLARE
    tier_id_col_exists BOOLEAN;
    last_call_col_exists BOOLEAN;
    period_start_type TEXT;
BEGIN
    -- Check if current_tier_id column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'current_tier_id'
    ) INTO tier_id_col_exists;

    -- Check if last_ai_call_at column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'last_ai_call_at'
    ) INTO last_call_col_exists;

    -- Check type of current_period_start
    SELECT data_type INTO period_start_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'users'
    AND column_name = 'current_period_start';

    RAISE NOTICE 'current_tier_id column exists: %', tier_id_col_exists;
    RAISE NOTICE 'last_ai_call_at column exists: %', last_call_col_exists;
    RAISE NOTICE 'current_period_start type: %', period_start_type;

    IF tier_id_col_exists AND last_call_col_exists AND period_start_type = 'timestamp with time zone' THEN
        RAISE NOTICE 'Users table successfully updated for subscription system';
    ELSE
        RAISE WARNING 'Some columns may not have been created properly';
    END IF;
END $$;

-- =====================================================
-- MIGRATION COMPLETE
-- Updated: users table with current_tier_id, last_ai_call_at, and current_period_start (TIMESTAMPTZ)
-- =====================================================
