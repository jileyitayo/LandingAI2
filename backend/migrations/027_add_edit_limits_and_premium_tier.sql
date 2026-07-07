-- =====================================================
-- Add Edit Rate Limits + Premium Tier
-- Version: 1.0
-- Created: 2026-07-05
-- Description: Separate edit quota from generation quota.
--   - Adds daily_edit_limit / per_minute_edit_limit to subscription_tiers
--   - Seeds edit limits: free 10/day + 2/min, pro 30/day + 5/min
--   - Seeds premium tier (placeholder pricing, no Stripe IDs):
--     100 generations/day + 5/min, 10000 edits/day + 20/min
--   - Adds index for per-user per-call-type counting on ai_call_logs
-- =====================================================

-- =====================================================
-- SECTION 1: ADD EDIT LIMIT COLUMNS
-- =====================================================

ALTER TABLE public.subscription_tiers
    ADD COLUMN IF NOT EXISTS daily_edit_limit INTEGER NOT NULL DEFAULT 10,
    ADD COLUMN IF NOT EXISTS per_minute_edit_limit INTEGER NOT NULL DEFAULT 2;

COMMENT ON COLUMN public.subscription_tiers.daily_edit_limit IS 'Max LLM edits per rolling 24h window (separate from daily_generation_limit)';
COMMENT ON COLUMN public.subscription_tiers.per_minute_edit_limit IS 'Max LLM edits per sliding 60s window (separate from per_minute_limit)';

-- =====================================================
-- SECTION 2: SEED EDIT LIMITS ON EXISTING TIERS
-- =====================================================

UPDATE public.subscription_tiers
SET daily_edit_limit = 10,
    per_minute_edit_limit = 2,
    updated_at = NOW()
WHERE tier_name = 'free';

UPDATE public.subscription_tiers
SET daily_edit_limit = 30,
    per_minute_edit_limit = 5,
    updated_at = NOW()
WHERE tier_name = 'pro';

-- =====================================================
-- SECTION 3: SEED PREMIUM TIER
-- =====================================================

INSERT INTO public.subscription_tiers (
    tier_name,
    display_name,
    description,
    daily_generation_limit,
    per_minute_limit,
    daily_edit_limit,
    per_minute_edit_limit,
    price_monthly,
    price_yearly,
    stripe_price_id_monthly,
    stripe_price_id_yearly,
    stripe_product_id,
    features,
    is_active
) VALUES (
    'premium',
    'Premium Plan',
    'For power users and agencies who need high-volume generation and unlimited editing',
    100,   -- 100 generations per day
    5,     -- 5 generations per minute
    10000, -- effectively unlimited edits per day
    20,    -- 20 edits per minute
    0.00,  -- TODO: placeholder — set real pricing when billing is wired up
    0.00,  -- TODO: placeholder — set real pricing when billing is wired up
    NULL,  -- TODO: Replace with actual Stripe price ID after creating product in Stripe
    NULL,  -- TODO: Replace with actual Stripe price ID for yearly
    NULL,  -- TODO: Replace with actual Stripe product ID
    '["100 website generations per day", "5 generations per minute", "Unlimited edits (10000/day)", "20 edits per minute", "All premium templates", "Priority support", "Custom domain support", "Advanced customization"]'::jsonb,
    true
) ON CONFLICT (tier_name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    daily_generation_limit = EXCLUDED.daily_generation_limit,
    per_minute_limit = EXCLUDED.per_minute_limit,
    daily_edit_limit = EXCLUDED.daily_edit_limit,
    per_minute_edit_limit = EXCLUDED.per_minute_edit_limit,
    features = EXCLUDED.features,
    updated_at = NOW();

-- =====================================================
-- SECTION 4: INDEX FOR EDIT-SCOPED COUNTING
-- =====================================================

-- check_rate_limit(call_type='edit') counts ai_call_logs by
-- (user_id, call_type) over 60s and 24h windows
CREATE INDEX IF NOT EXISTS idx_ai_call_logs_user_type_created
    ON public.ai_call_logs (user_id, call_type, created_at DESC);

-- =====================================================
-- SECTION 5: VERIFY
-- =====================================================

DO $$
DECLARE
    tier_count INTEGER;
    rec RECORD;
BEGIN
    SELECT COUNT(*) INTO tier_count FROM public.subscription_tiers WHERE is_active = true;
    IF tier_count < 3 THEN
        RAISE EXCEPTION 'Expected at least 3 active tiers (free, pro, premium), found %', tier_count;
    END IF;
    RAISE NOTICE 'Active subscription tiers: %', tier_count;
    FOR rec IN
        SELECT tier_name, daily_generation_limit, per_minute_limit, daily_edit_limit, per_minute_edit_limit
        FROM public.subscription_tiers WHERE is_active = true ORDER BY tier_name
    LOOP
        RAISE NOTICE 'Tier %: % gen/day, % gen/min, % edits/day, % edits/min',
            rec.tier_name, rec.daily_generation_limit, rec.per_minute_limit,
            rec.daily_edit_limit, rec.per_minute_edit_limit;
    END LOOP;
END $$;

-- =====================================================
-- MIGRATION COMPLETE
-- Edit limits: free 10/day + 2/min, pro 30/day + 5/min, premium 10000/day + 20/min
-- Premium generation limits: 100/day + 5/min (placeholder $0 pricing)
--
-- NEXT STEPS:
-- 1. Apply manually via Supabase Dashboard -> SQL Editor
-- 2. Set real premium pricing + Stripe IDs when billing is ready
-- =====================================================
