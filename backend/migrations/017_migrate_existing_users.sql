-- =====================================================
-- Migrate Existing Users to New Subscription System
-- Version: 1.0
-- Created: 2025-10-24
-- Description: Create user_subscriptions for all existing users and link them to appropriate tiers
-- =====================================================

-- =====================================================
-- SECTION 1: GET TIER IDs
-- =====================================================

DO $$
DECLARE
    free_tier_id UUID;
    pro_tier_id UUID;
    users_migrated INTEGER := 0;
    subscriptions_created INTEGER := 0;
    tier_record RECORD;
BEGIN
    -- Get the free and pro tier IDs
    SELECT id INTO free_tier_id FROM public.subscription_tiers WHERE tier_name = 'free';
    SELECT id INTO pro_tier_id FROM public.subscription_tiers WHERE tier_name = 'pro';

    IF free_tier_id IS NULL OR pro_tier_id IS NULL THEN
        RAISE EXCEPTION 'Subscription tiers not found. Please run migration 015_seed_subscription_tiers.sql first.';
    END IF;

    RAISE NOTICE 'Free tier ID: %', free_tier_id;
    RAISE NOTICE 'Pro tier ID: %', pro_tier_id;

    -- =====================================================
    -- SECTION 2: UPDATE USERS.CURRENT_TIER_ID
    -- =====================================================

    -- Update users who have 'pro' in subscription_tier column to pro tier
    UPDATE public.users
    SET current_tier_id = pro_tier_id
    WHERE subscription_tier = 'pro'
    AND current_tier_id IS NULL;

    GET DIAGNOSTICS users_migrated = ROW_COUNT;
    RAISE NOTICE 'Updated % existing pro users with pro tier ID', users_migrated;

    -- Update all other users to free tier
    UPDATE public.users
    SET current_tier_id = free_tier_id
    WHERE current_tier_id IS NULL;

    GET DIAGNOSTICS users_migrated = ROW_COUNT;
    RAISE NOTICE 'Updated % existing free users with free tier ID', users_migrated;

    -- =====================================================
    -- SECTION 3: CREATE USER_SUBSCRIPTIONS
    -- =====================================================

    -- Create user_subscriptions for pro users
    INSERT INTO public.user_subscriptions (
        user_id,
        tier_id,
        status,
        current_period_start,
        current_period_end,
        created_at,
        updated_at
    )
    SELECT
        id,
        pro_tier_id,
        'active',
        NOW(),
        NOW() + INTERVAL '30 days', -- Set 30-day period for existing pro users
        created_at,
        NOW()
    FROM public.users
    WHERE current_tier_id = pro_tier_id
    ON CONFLICT (user_id) DO NOTHING; -- Skip if subscription already exists

    GET DIAGNOSTICS subscriptions_created = ROW_COUNT;
    RAISE NOTICE 'Created % subscriptions for pro users', subscriptions_created;

    -- Create user_subscriptions for free users
    INSERT INTO public.user_subscriptions (
        user_id,
        tier_id,
        status,
        current_period_start,
        current_period_end,
        created_at,
        updated_at
    )
    SELECT
        id,
        free_tier_id,
        'active',
        NOW(),
        NULL, -- Free tier doesn't have end date
        created_at,
        NOW()
    FROM public.users
    WHERE current_tier_id = free_tier_id
    ON CONFLICT (user_id) DO NOTHING; -- Skip if subscription already exists

    GET DIAGNOSTICS subscriptions_created = ROW_COUNT;
    RAISE NOTICE 'Created % subscriptions for free users', subscriptions_created;

    -- =====================================================
    -- SECTION 4: VERIFY MIGRATION
    -- =====================================================

    -- Count users with subscriptions
    SELECT COUNT(*) INTO users_migrated
    FROM public.users u
    INNER JOIN public.user_subscriptions us ON u.id = us.user_id;

    RAISE NOTICE 'Total users with subscriptions: %', users_migrated;

    -- Show tier distribution
    RAISE NOTICE 'Subscription Distribution:';
    FOR tier_record IN
        SELECT st.tier_name, COUNT(us.user_id) as user_count
        FROM public.subscription_tiers st
        LEFT JOIN public.user_subscriptions us ON st.id = us.tier_id
        GROUP BY st.tier_name
    LOOP
        RAISE NOTICE '  %: % users', tier_record.tier_name, tier_record.user_count;
    END LOOP;

END $$;

-- =====================================================
-- SECTION 5: CREATE FUNCTION TO AUTO-ASSIGN TIER TO NEW USERS
-- =====================================================

CREATE OR REPLACE FUNCTION public.assign_default_tier_to_new_user()
RETURNS TRIGGER AS $$
DECLARE
    free_tier_id UUID;
BEGIN
    -- Get free tier ID
    SELECT id INTO free_tier_id
    FROM public.subscription_tiers
    WHERE tier_name = 'free'
    LIMIT 1;

    IF free_tier_id IS NULL THEN
        RAISE WARNING 'Free tier not found, cannot assign tier to new user';
        RETURN NEW;
    END IF;

    -- Update the newly created user with free tier
    UPDATE public.users
    SET current_tier_id = free_tier_id
    WHERE id = NEW.id AND current_tier_id IS NULL;

    -- Create user_subscription for the new user
    INSERT INTO public.user_subscriptions (
        user_id,
        tier_id,
        status,
        current_period_start
    ) VALUES (
        NEW.id,
        free_tier_id,
        'active',
        NOW()
    ) ON CONFLICT (user_id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- SECTION 6: CREATE TRIGGER FOR NEW USERS
-- =====================================================

-- Drop trigger if it exists
DROP TRIGGER IF EXISTS assign_tier_to_new_user ON public.users;

-- Create trigger that runs AFTER a new user is inserted
CREATE TRIGGER assign_tier_to_new_user
    AFTER INSERT ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.assign_default_tier_to_new_user();

COMMENT ON FUNCTION public.assign_default_tier_to_new_user IS 'Automatically assigns free tier to newly created users';
COMMENT ON TRIGGER assign_tier_to_new_user ON public.users IS 'Trigger that assigns free tier to new users on signup';

-- =====================================================
-- MIGRATION COMPLETE
-- - Updated all existing users with appropriate tier_id
-- - Created user_subscriptions for all users
-- - Created trigger to auto-assign free tier to new users
-- - Verified migration success
-- =====================================================
