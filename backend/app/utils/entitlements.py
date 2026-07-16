"""Subscription tier lookup used to gate paid-only features."""

import logging

from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def get_user_tier_name(user_id: str, supabase_client=None) -> str:
    """
    Resolve a user's subscription tier name via
    users -> user_subscriptions -> subscription_tiers.

    Returns 'free' when the user has no subscription or on any lookup error
    (callers gate paid features with `!= 'free'`, so errors fail closed for
    paid features).
    """
    try:
        supabase = supabase_client or get_supabase_client()
        response = supabase.table("users")\
            .select("id, user_subscriptions(id, status, subscription_tiers(tier_name))")\
            .eq("id", user_id)\
            .single()\
            .execute()

        if not response.data:
            return "free"

        subscription = response.data.get("user_subscriptions")
        if not subscription or not subscription.get("subscription_tiers"):
            return "free"

        return subscription["subscription_tiers"]["tier_name"] or "free"
    except Exception as e:
        logger.error(f"Error resolving tier for user {user_id}: {e}")
        return "free"
