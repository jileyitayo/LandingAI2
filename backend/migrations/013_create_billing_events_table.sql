-- =====================================================
-- Create Billing Events Table
-- Version: 1.0
-- Created: 2025-10-24
-- Description: Create billing_events table for audit trail of subscription events
-- =====================================================

-- =====================================================
-- SECTION 1: CREATE TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.billing_events (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign key
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Event information
    event_type TEXT NOT NULL CHECK (event_type IN (
        'subscription_created',
        'subscription_updated',
        'subscription_cancelled',
        'subscription_deleted',
        'payment_succeeded',
        'payment_failed',
        'payment_refunded',
        'trial_started',
        'trial_ended',
        'invoice_created',
        'invoice_paid',
        'invoice_payment_failed'
    )),

    -- Stripe integration
    stripe_event_id TEXT UNIQUE, -- Prevents duplicate webhook processing

    -- Financial information
    amount DECIMAL(10, 2),
    currency TEXT DEFAULT 'USD',

    -- Details
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb, -- Additional event data

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- SECTION 2: CREATE INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_billing_events_user_id ON public.billing_events(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_events_event_type ON public.billing_events(event_type);
CREATE INDEX IF NOT EXISTS idx_billing_events_stripe_event_id ON public.billing_events(stripe_event_id) WHERE stripe_event_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_billing_events_created_at ON public.billing_events(created_at DESC);

-- =====================================================
-- SECTION 3: ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

ALTER TABLE public.billing_events ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own billing events
CREATE POLICY "Users can view own billing events"
ON public.billing_events FOR SELECT
USING (auth.uid() = user_id);

-- Note: Only service role can INSERT billing events (via webhook handler)

-- =====================================================
-- SECTION 4: GRANTS AND PERMISSIONS
-- =====================================================

-- Grant SELECT to authenticated users
GRANT SELECT ON public.billing_events TO authenticated;

-- =====================================================
-- SECTION 5: ADD COMMENTS
-- =====================================================

COMMENT ON TABLE public.billing_events IS 'Audit trail of subscription and billing events from Stripe';
COMMENT ON COLUMN public.billing_events.stripe_event_id IS 'Unique Stripe event ID to prevent duplicate webhook processing';
COMMENT ON COLUMN public.billing_events.metadata IS 'JSONB field for storing additional event data from Stripe';

-- =====================================================
-- MIGRATION COMPLETE
-- Created: billing_events table
-- =====================================================
