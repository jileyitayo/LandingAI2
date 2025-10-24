-- =====================================================
-- Seed Subscription Tiers
-- Version: 1.0
-- Created: 2025-10-24
-- Description: Insert default subscription tiers (free and pro)
-- =====================================================

-- =====================================================
-- SECTION 1: INSERT FREE TIER
-- =====================================================

INSERT INTO public.subscription_tiers (
    tier_name,
    display_name,
    description,
    daily_generation_limit,
    per_minute_limit,
    price_monthly,
    price_yearly,
    stripe_price_id_monthly,
    stripe_price_id_yearly,
    stripe_product_id,
    features,
    is_active
) VALUES (
    'free',
    'Free Plan',
    'Perfect for trying out SiteSmith with basic features',
    5,  -- 5 generations per day
    1,  -- 1 generation per minute
    0.00,
    0.00,
    NULL,  -- No Stripe price ID for free tier
    NULL,
    NULL,
    '["5 website generations per day", "1 generation per minute", "Basic templates", "Community support"]'::jsonb,
    true
) ON CONFLICT (tier_name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    daily_generation_limit = EXCLUDED.daily_generation_limit,
    per_minute_limit = EXCLUDED.per_minute_limit,
    features = EXCLUDED.features,
    updated_at = NOW();

-- =====================================================
-- SECTION 2: INSERT PRO TIER
-- =====================================================

INSERT INTO public.subscription_tiers (
    tier_name,
    display_name,
    description,
    daily_generation_limit,
    per_minute_limit,
    price_monthly,
    price_yearly,
    stripe_price_id_monthly,
    stripe_price_id_yearly,
    stripe_product_id,
    features,
    is_active
) VALUES (
    'pro',
    'Pro Plan',
    'For professionals who need more generations and priority support',
    30,  -- 30 generations per day
    2,   -- 2 generations per minute
    19.99,  -- $19.99/month (adjust as needed)
    199.99, -- $199.99/year (adjust as needed)
    NULL,  -- TODO: Replace with actual Stripe price ID after creating product in Stripe
    NULL,  -- TODO: Replace with actual Stripe price ID for yearly
    NULL,  -- TODO: Replace with actual Stripe product ID
    '["30 website generations per day", "2 generations per minute", "All premium templates", "Priority support", "Custom domain support", "Advanced customization"]'::jsonb,
    true
) ON CONFLICT (tier_name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    daily_generation_limit = EXCLUDED.daily_generation_limit,
    per_minute_limit = EXCLUDED.per_minute_limit,
    price_monthly = EXCLUDED.price_monthly,
    price_yearly = EXCLUDED.price_yearly,
    features = EXCLUDED.features,
    updated_at = NOW();

-- =====================================================
-- SECTION 3: VERIFY INSERTED DATA
-- =====================================================

-- Display inserted tiers for verification
DO $$
DECLARE
    tier_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO tier_count FROM public.subscription_tiers WHERE is_active = true;
    RAISE NOTICE 'Successfully seeded % active subscription tiers', tier_count;
END $$;

-- =====================================================
-- SECTION 4: ADD COMMENTS
-- =====================================================

COMMENT ON COLUMN public.subscription_tiers.stripe_price_id_monthly IS 'TODO: Update with actual Stripe price ID after creating product in Stripe Dashboard';
COMMENT ON COLUMN public.subscription_tiers.stripe_price_id_yearly IS 'TODO: Update with actual Stripe price ID for yearly billing';
COMMENT ON COLUMN public.subscription_tiers.stripe_product_id IS 'TODO: Update with actual Stripe product ID';

-- =====================================================
-- MIGRATION COMPLETE
-- Seeded: free (1/min, 5/day) and pro (2/min, 30/day) tiers
--
-- NEXT STEPS:
-- 1. Create Stripe product and pricing in Stripe Dashboard
-- 2. Update stripe_price_id_monthly, stripe_price_id_yearly, stripe_product_id
--    with actual values from Stripe
-- 3. Update environment variables with Stripe keys
-- =====================================================
