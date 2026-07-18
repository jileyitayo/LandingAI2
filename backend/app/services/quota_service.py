"""
Quota Service
Rate limiting, AI-call logging, and project-limit checks shared across routers.
"""

import logging
from typing import Dict, Any, Tuple

from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import log_action
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


# ============================================================================
# Rate Limiting Functions - NEW DUAL RATE LIMITING
# ============================================================================
@log_action(action_type='READ', target_resource_type='rate_limit_check')
async def check_user_rate_limit(user_id: str, supabase_client, call_type: str = "generation") -> tuple[bool, Dict[str, Any]]:
    """
    Check if user has exceeded rate limit (per-minute OR daily).

    Uses new dual rate limiting:
    - call_type='generation': per-minute (Free=1/min, Pro=2/min) + daily
      (Free=5/day, Pro=30/day) via the shared generation counter
    - call_type='edit': separate edit quota (Free=10/day+2/min, Pro=30/day+5/min,
      Premium=10000/day+20/min) counted from ai_call_logs

    Returns:
        Tuple of (is_allowed, rate_limit_info)
    """
    rate_limiter = RateLimiter(supabase_client)
    return await rate_limiter.check_rate_limit(user_id, call_type=call_type)


async def log_ai_call(
    user_id: str,
    call_type: str,
    project_id: str = None,
    endpoint: str = None,
    supabase_client = None
) -> None:
    """
    Log AI call for rate limiting tracking.

    Args:
        user_id: User ID making the call
        call_type: 'generation', 'edit', or 'question'
        project_id: Optional project ID
        endpoint: Optional endpoint path
        supabase_client: Supabase client instance
    """
    if supabase_client is None:
        supabase_client = get_supabase_client()

    rate_limiter = RateLimiter(supabase_client)
    await rate_limiter.log_ai_call(user_id, call_type, project_id, endpoint)


# ============================================================================
# Helper Functions
# ============================================================================

async def check_project_limit(user_id: str, supabase_client) -> Tuple[bool, dict]:
    """
    Check if user has reached their project limit based on subscription tier.
    Free users are limited to 3 projects maximum.

    Returns:
        tuple: (is_allowed: bool, info: dict)
    """
    limit = 3
    try:
        # Get user's subscription tier
        user_response = supabase_client.table("users")\
            .select("*, user_subscriptions(id, status, subscription_tiers(tier_name))")\
            .eq("id", user_id)\
            .single()\
            .execute()

        if not user_response.data:
            logger.error(f"User {user_id} not found")
            return True, {"error": "user_not_found"}

        user = user_response.data

        # Get tier information
        subscription = user.get("user_subscriptions")
        if not subscription or not subscription.get("subscription_tiers"):
            # Default to free tier if no subscription
            tier_name = "free"
        else:
            tier_name = subscription["subscription_tiers"]["tier_name"]

        # Only check project limit for free tier users
        if tier_name != "free":
            return True, {"tier": tier_name}

        # Count user's existing projects (excluding soft-deleted ones)
        projects_response = supabase_client.table("projects")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .is_("deleted_at", "null")\
            .execute()

        project_count = projects_response.count or 0

        # Free users are limited to 5 projects
        if project_count >= limit:
            return False, {
                "tier": tier_name,
                "project_count": project_count,
                "project_limit": limit,
                "message": f"Free tier users are limited to 3 projects. You currently have {project_count} projects. Please delete some projects or upgrade to Pro for unlimited projects.",
                "upgrade_suggestion": "Upgrade to Pro for unlimited projects and higher generation limits"
            }

        return True, {
            "tier": tier_name,
            "project_count": project_count,
            "project_limit": limit
        }

    except Exception as e:
        logger.error(f"Error checking project limit: {str(e)}")
        # Allow request on error to avoid blocking users
        return True, {"error": str(e)}

