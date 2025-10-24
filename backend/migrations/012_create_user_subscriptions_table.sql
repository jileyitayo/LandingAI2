-- =====================================================
-- Create User Subscriptions Table
-- Version: 1.0
-- Created: 2025-10-24
-- Description: Create user_subscriptions table to track active subscriptions
-- =====================================================

-- =====================================================
-- SECTION 1: CREATE TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign keys
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    tier_id UUID NOT NULL REFERENCES public.subscription_tiers(id) ON DELETE RESTRICT,

    -- Subscription status
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'past_due', 'trialing')),

    -- Stripe integration
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT,

    -- Billing period
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,

    -- Cancellation
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
    cancelled_at TIMESTAMPTZ,

    -- Trial period (optional)
    trial_start TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- SECTION 2: CREATE INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON public.user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_tier_id ON public.user_subscriptions(tier_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON public.user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_stripe_subscription_id ON public.user_subscriptions(stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_stripe_customer_id ON public.user_subscriptions(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_created_at ON public.user_subscriptions(created_at DESC);

-- =====================================================
-- SECTION 3: ADD TRIGGER FOR UPDATED_AT
-- =====================================================

CREATE TRIGGER update_user_subscriptions_updated_at
    BEFORE UPDATE ON public.user_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- =====================================================
-- SECTION 4: ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own subscription
CREATE POLICY "Users can view own subscription"
ON public.user_subscriptions FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can update their own subscription (for cancellation)
CREATE POLICY "Users can update own subscription"
ON public.user_subscriptions FOR UPDATE
USING (auth.uid() = user_id);

-- Note: INSERT and DELETE operations are restricted to service role only

-- =====================================================
-- SECTION 5: GRANTS AND PERMISSIONS
-- =====================================================

-- Grant SELECT and UPDATE to authenticated users (for viewing and cancelling)
GRANT SELECT, UPDATE ON public.user_subscriptions TO authenticated;

-- =====================================================
-- SECTION 6: ADD COMMENTS
-- =====================================================

COMMENT ON TABLE public.user_subscriptions IS 'User subscription records linking users to their active subscription tier';
COMMENT ON COLUMN public.user_subscriptions.user_id IS 'UNIQUE constraint ensures one subscription per user';
COMMENT ON COLUMN public.user_subscriptions.status IS 'Subscription status: active, cancelled, expired, past_due, trialing';
COMMENT ON COLUMN public.user_subscriptions.cancel_at_period_end IS 'If true, subscription will cancel at end of current period';

-- =====================================================
-- MIGRATION COMPLETE
-- Created: user_subscriptions table
-- =====================================================
