-- =====================================================
-- Create Subscription Tiers Table
-- Version: 1.0
-- Created: 2025-10-24
-- Description: Create subscription_tiers table for managing subscription plans
-- =====================================================

-- =====================================================
-- SECTION 1: CREATE TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.subscription_tiers (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Tier information
    tier_name TEXT NOT NULL UNIQUE CHECK (tier_name IN ('free', 'pro', 'premium', 'enterprise')),
    display_name TEXT NOT NULL,
    description TEXT,

    -- Rate limits (configurable from database)
    daily_generation_limit INTEGER NOT NULL DEFAULT 5,
    per_minute_limit INTEGER NOT NULL DEFAULT 1,

    -- Pricing
    price_monthly DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    price_yearly DECIMAL(10, 2) NOT NULL DEFAULT 0.00,

    -- Stripe integration
    stripe_price_id_monthly TEXT,
    stripe_price_id_yearly TEXT,
    stripe_product_id TEXT,

    -- Features
    features JSONB NOT NULL DEFAULT '[]'::jsonb, -- ['unlimited_templates', 'priority_support', etc.]

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- SECTION 2: CREATE INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_subscription_tiers_tier_name ON public.subscription_tiers(tier_name);
CREATE INDEX IF NOT EXISTS idx_subscription_tiers_is_active ON public.subscription_tiers(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_subscription_tiers_created_at ON public.subscription_tiers(created_at DESC);

-- =====================================================
-- SECTION 3: ADD TRIGGER FOR UPDATED_AT
-- =====================================================

CREATE TRIGGER update_subscription_tiers_updated_at
    BEFORE UPDATE ON public.subscription_tiers
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- =====================================================
-- SECTION 4: ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

ALTER TABLE public.subscription_tiers ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone (authenticated and anon) can view active tiers
CREATE POLICY "Active subscription tiers are viewable by everyone"
ON public.subscription_tiers FOR SELECT
USING (is_active = true);

-- Policy: Only service role can insert/update/delete (done via backend)
-- No policies for INSERT/UPDATE/DELETE means only service role can do these operations

-- =====================================================
-- SECTION 5: GRANTS AND PERMISSIONS
-- =====================================================

-- Grant SELECT to authenticated and anon users
GRANT SELECT ON public.subscription_tiers TO authenticated, anon;

-- =====================================================
-- SECTION 6: ADD COMMENTS
-- =====================================================

COMMENT ON TABLE public.subscription_tiers IS 'Subscription tier definitions with configurable rate limits and pricing';
COMMENT ON COLUMN public.subscription_tiers.daily_generation_limit IS 'Maximum AI generations allowed per day (resets at midnight UTC)';
COMMENT ON COLUMN public.subscription_tiers.per_minute_limit IS 'Maximum AI calls allowed per minute (sliding window)';
COMMENT ON COLUMN public.subscription_tiers.features IS 'JSONB array of feature identifiers for this tier';

-- =====================================================
-- MIGRATION COMPLETE
-- Created: subscription_tiers table
-- =====================================================
