"""
Rate Limiter with Dual Rate Limiting (Per-Minute + Daily)

This module implements rate limiting with:
1. Per-minute limit (sliding window) - e.g., 1 request/min for free, 2/min for pro
2. Daily limit - e.g., 5 requests/day for free, 30/day for pro

All limits are configurable from the database (subscription_tiers table).
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with per-minute (sliding window) and daily limits"""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def check_rate_limit(self, user_id: str, call_type: str = "generation") -> Tuple[bool, Dict[str, Any]]:
        """
        Check if user has exceeded either per-minute or daily rate limit.

        Args:
            user_id: User ID to check
            call_type: 'generation' (default) uses the shared generation quota
                (per_minute_limit + daily_generation_limit / current_period_generations).
                'edit' uses the separate edit quota (per_minute_edit_limit +
                daily_edit_limit), counted from ai_call_logs rows with
                call_type='edit' over sliding 60s / rolling 24h windows.

        Returns:
            Tuple of (is_allowed, rate_limit_info)
            - is_allowed: True if request is allowed, False if rate limited
            - rate_limit_info: Dictionary with limit details and error info (if rate limited)
        """
        try:
            now = datetime.utcnow()

            # =====================================================
            # STEP 1: Fetch user + subscription + tier info
            # =====================================================
            user_response = self.supabase.table("users")\
                .select(
                    "id, email, current_period_generations, current_period_start, "
                    "last_ai_call_at, user_subscriptions(tier_id, subscription_tiers(*))"
                )\
                .eq("id", user_id)\
                .single()\
                .execute()

            if not user_response.data:
                logger.error(f"User {user_id} not found")
                # Allow request but log the error
                return True, {"error": "user_not_found"}

            user = user_response.data

            # Get tier information
            subscription = user.get("user_subscriptions")
            if not subscription or not subscription.get("subscription_tiers"):
                logger.warning(f"User {user_id} has no subscription or tier. Applying default free tier limits.")
                # Fallback to free tier limits if subscription not found
                tier = {
                    "tier_name": "free",
                    "per_minute_limit": 1,
                    "daily_generation_limit": 5,
                    "per_minute_edit_limit": 2,
                    "daily_edit_limit": 10
                }
            else:
                tier = subscription["subscription_tiers"]

            tier_name = tier["tier_name"]
            per_minute_limit = tier["per_minute_limit"]
            daily_limit = tier["daily_generation_limit"]

            if call_type == "edit":
                return await self._check_edit_rate_limit(user_id, tier, now)

            # =====================================================
            # STEP 2: Check Per-Minute Limit (Sliding Window)
            # =====================================================

            # Count calls in the last 60 seconds from ai_call_logs
            sixty_seconds_ago = now - timedelta(seconds=60)

            recent_calls_response = self.supabase.table("ai_call_logs")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", sixty_seconds_ago.isoformat())\
                .execute()

            calls_in_last_minute = recent_calls_response.count or 0

            # Check if per-minute limit is exceeded
            if calls_in_last_minute >= per_minute_limit:
                # Calculate retry_after: time until oldest call in the window expires
                oldest_call_response = self.supabase.table("ai_call_logs")\
                    .select("created_at")\
                    .eq("user_id", user_id)\
                    .gte("created_at", sixty_seconds_ago.isoformat())\
                    .order("created_at", desc=False)\
                    .limit(1)\
                    .execute()

                if oldest_call_response.data:
                    oldest_call_time = datetime.fromisoformat(
                        oldest_call_response.data[0]["created_at"].replace('Z', '+00:00')
                    )
                    # Calculate seconds until the oldest call expires (60 seconds from its time)
                    retry_after = 60 - (now - oldest_call_time.replace(tzinfo=None)).total_seconds()
                    retry_after = max(1, int(retry_after) + 1)  # At least 1 second
                else:
                    retry_after = 60

                return False, {
                    "limit_type": "per_minute",
                    "tier": tier_name,
                    "per_minute_limit": per_minute_limit,
                    "calls_in_last_minute": calls_in_last_minute,
                    "retry_after_seconds": retry_after,
                    "message": f"Rate limit exceeded. Please wait {retry_after} seconds.",
                    "countdown_message": f"You can make your next request in {retry_after} seconds",
                    "upgrade_suggestion": "Upgrade to Pro for 2 requests per minute and 30 requests per day" if tier_name == "free" else None
                }

            # =====================================================
            # STEP 3: Check Daily Limit
            # =====================================================

            current_count = user.get("current_period_generations", 0)
            period_start = user.get("current_period_start")

            # Check if we need to reset daily counter (past 24 hours)
            if period_start:
                period_start_dt = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
                if (now - period_start_dt.replace(tzinfo=None)) > timedelta(days=1):
                    # Reset the counter
                    self.supabase.table("users")\
                        .update({
                            "current_period_generations": 0,
                            "current_period_start": now.isoformat()
                        })\
                        .eq("id", user_id)\
                        .execute()
                    current_count = 0
                    period_start_dt = now
            else:
                # Initialize period start if not set
                period_start_dt = now
                self.supabase.table("users")\
                    .update({"current_period_start": now.isoformat()})\
                    .eq("id", user_id)\
                    .execute()

            # Check if daily limit is exceeded
            if current_count >= daily_limit:
                # Calculate time until next reset (midnight UTC of next day)
                tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                retry_after = int((tomorrow - now).total_seconds())
                hours_until_reset = int(retry_after / 3600)
                minutes_until_reset = int((retry_after % 3600) / 60)

                return False, {
                    "limit_type": "daily",
                    "tier": tier_name,
                    "daily_limit": daily_limit,
                    "used_today": current_count,
                    "retry_after_seconds": retry_after,
                    "resets_at": tomorrow.isoformat(),
                    "message": f"Daily limit reached. Resets in {hours_until_reset}h {minutes_until_reset}m.",
                    "countdown_message": f"Your daily limit will reset in {hours_until_reset} hours and {minutes_until_reset} minutes",
                    "upgrade_suggestion": "Upgrade to Pro for 30 requests per day" if tier_name == "free" else None
                }

            # =====================================================
            # STEP 4: All Checks Passed - Return Success Info
            # =====================================================

            return True, {
                "tier": tier_name,
                "per_minute_limit": per_minute_limit,
                "daily_limit": daily_limit,
                "calls_in_last_minute": calls_in_last_minute,
                "used_today": current_count,
                "remaining_today": daily_limit - current_count
            }

        except Exception as e:
            logger.error(f"Error checking rate limit for user {user_id}: {str(e)}", exc_info=True)
            # On error, allow the request but log it
            return True, {"error": str(e)}

    async def _check_edit_rate_limit(self, user_id: str, tier: Dict[str, Any], now: datetime) -> Tuple[bool, Dict[str, Any]]:
        """
        Check the edit-specific quota: sliding 60s window + rolling 24h window,
        both counted from ai_call_logs rows with call_type='edit'.

        Edits do NOT touch users.current_period_generations — the two quotas
        are fully independent. Uses .get() defaults so this degrades to free-tier
        edit limits until migration 027 adds the columns.
        """
        tier_name = tier["tier_name"]
        per_minute_limit = tier.get("per_minute_edit_limit", 2)
        daily_limit = tier.get("daily_edit_limit", 10)

        def count_edits_since(since: datetime) -> int:
            response = self.supabase.table("ai_call_logs")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("call_type", "edit")\
                .gte("created_at", since.isoformat())\
                .execute()
            return response.count or 0

        def oldest_edit_since(since: datetime) -> Optional[datetime]:
            response = self.supabase.table("ai_call_logs")\
                .select("created_at")\
                .eq("user_id", user_id)\
                .eq("call_type", "edit")\
                .gte("created_at", since.isoformat())\
                .order("created_at", desc=False)\
                .limit(1)\
                .execute()
            if response.data:
                return datetime.fromisoformat(
                    response.data[0]["created_at"].replace('Z', '+00:00')
                ).replace(tzinfo=None)
            return None

        # Per-minute limit (sliding 60s window)
        sixty_seconds_ago = now - timedelta(seconds=60)
        edits_in_last_minute = count_edits_since(sixty_seconds_ago)

        if edits_in_last_minute >= per_minute_limit:
            oldest = oldest_edit_since(sixty_seconds_ago)
            retry_after = max(1, int(60 - (now - oldest).total_seconds()) + 1) if oldest else 60

            return False, {
                "limit_type": "per_minute",
                "quota": "edit",
                "tier": tier_name,
                "per_minute_limit": per_minute_limit,
                "calls_in_last_minute": edits_in_last_minute,
                "retry_after_seconds": retry_after,
                "message": f"Edit rate limit exceeded. Please wait {retry_after} seconds.",
                "countdown_message": f"You can make your next edit in {retry_after} seconds",
                "upgrade_suggestion": "Upgrade to Pro for 5 edits per minute and 30 edits per day" if tier_name == "free" else None
            }

        # Daily limit (rolling 24h window)
        twenty_four_hours_ago = now - timedelta(hours=24)
        edits_in_last_day = count_edits_since(twenty_four_hours_ago)

        if edits_in_last_day >= daily_limit:
            oldest = oldest_edit_since(twenty_four_hours_ago)
            if oldest:
                retry_after = max(1, int((oldest + timedelta(hours=24) - now).total_seconds()) + 1)
            else:
                retry_after = 24 * 3600
            resets_at = now + timedelta(seconds=retry_after)
            hours_until_reset = int(retry_after / 3600)
            minutes_until_reset = int((retry_after % 3600) / 60)

            return False, {
                "limit_type": "daily",
                "quota": "edit",
                "tier": tier_name,
                "daily_limit": daily_limit,
                "used_today": edits_in_last_day,
                "retry_after_seconds": retry_after,
                "resets_at": resets_at.isoformat(),
                "message": f"Daily edit limit reached. Resets in {hours_until_reset}h {minutes_until_reset}m.",
                "countdown_message": f"Your daily edit limit will reset in {hours_until_reset} hours and {minutes_until_reset} minutes",
                "upgrade_suggestion": "Upgrade to Pro for 30 edits per day" if tier_name == "free" else None
            }

        return True, {
            "quota": "edit",
            "tier": tier_name,
            "per_minute_limit": per_minute_limit,
            "daily_limit": daily_limit,
            "calls_in_last_minute": edits_in_last_minute,
            "used_today": edits_in_last_day,
            "remaining_today": daily_limit - edits_in_last_day
        }

    async def log_ai_call(
        self,
        user_id: str,
        call_type: str,
        project_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> None:
        """
        Log an AI call for rate limiting tracking.

        This function:
        1. Inserts a record into ai_call_logs table (for per-minute tracking)
        2. Updates user's last_ai_call_at timestamp
        3. Increments user's current_period_generations (daily counter) —
           only for call_type='generation'; edits have their own quota
           counted directly from ai_call_logs

        Args:
            user_id: User ID making the call
            call_type: Type of AI call ('generation', 'edit', 'question')
            project_id: Optional project ID associated with the call
            endpoint: Optional endpoint path for debugging
        """
        try:
            now = datetime.utcnow()

            # Insert into ai_call_logs for per-minute tracking
            self.supabase.table("ai_call_logs").insert({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "call_type": call_type,
                "project_id": project_id,
                "endpoint": endpoint,
                "created_at": now.isoformat()
            }).execute()

            if call_type != "generation":
                # Edits/questions don't consume the generation quota
                self.supabase.table("users")\
                    .update({"last_ai_call_at": now.isoformat()})\
                    .eq("id", user_id)\
                    .execute()
                logger.info(f"Logged AI call for user {user_id}: {call_type}")
                return

            # Update user's last_ai_call_at and increment daily counter
            # First, get current count
            user_response = self.supabase.table("users")\
                .select("current_period_generations")\
                .eq("id", user_id)\
                .single()\
                .execute()

            if user_response.data:
                current_count = user_response.data.get("current_period_generations", 0)

                self.supabase.table("users")\
                    .update({
                        "last_ai_call_at": now.isoformat(),
                        "current_period_generations": current_count + 1
                    })\
                    .eq("id", user_id)\
                    .execute()

                logger.info(f"Logged AI call for user {user_id}: {call_type} (daily count: {current_count + 1})")

        except Exception as e:
            logger.error(f"Failed to log AI call for user {user_id}: {str(e)}", exc_info=True)
            # Don't raise exception - logging failure shouldn't break the main flow

    async def get_current_usage(self, user_id: str) -> Dict[str, Any]:
        """
        Get current usage statistics for a user.

        Returns:
            Dictionary with daily and per-minute usage info
        """
        try:
            now = datetime.utcnow()

            # Fetch user + subscription + tier info
            user_response = self.supabase.table("users")\
                .select(
                    "id, current_period_generations, current_period_start, "
                    "last_ai_call_at, user_subscriptions(tier_id, subscription_tiers(*))"
                )\
                .eq("id", user_id)\
                .single()\
                .execute()

            if not user_response.data:
                return {"error": "user_not_found"}

            user = user_response.data
            subscription = user.get("user_subscriptions")

            if not subscription or not subscription.get("subscription_tiers"):
                tier = {
                    "tier_name": "free",
                    "display_name": "Free Plan",
                    "per_minute_limit": 1,
                    "daily_generation_limit": 5
                }
            else:
                tier = subscription["subscription_tiers"]

            tier_name = tier["tier_name"]
            tier_display_name = tier.get("display_name", tier_name.title())
            per_minute_limit = tier["per_minute_limit"]
            daily_limit = tier["daily_generation_limit"]

            # Calculate daily usage
            current_count = user.get("current_period_generations", 0)
            period_start = user.get("current_period_start")

            if period_start:
                period_start_dt = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
            else:
                period_start_dt = now

            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            resets_in_seconds = int((tomorrow - now).total_seconds())

            # Calculate per-minute usage
            sixty_seconds_ago = now - timedelta(seconds=60)
            recent_calls_response = self.supabase.table("ai_call_logs")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", sixty_seconds_ago.isoformat())\
                .execute()

            calls_in_last_minute = recent_calls_response.count or 0
            can_call_now = calls_in_last_minute < per_minute_limit

            # Calculate retry_after for per-minute
            retry_after = 0
            if not can_call_now:
                oldest_call_response = self.supabase.table("ai_call_logs")\
                    .select("created_at")\
                    .eq("user_id", user_id)\
                    .gte("created_at", sixty_seconds_ago.isoformat())\
                    .order("created_at", desc=False)\
                    .limit(1)\
                    .execute()

                if oldest_call_response.data:
                    oldest_call_time = datetime.fromisoformat(
                        oldest_call_response.data[0]["created_at"].replace('Z', '+00:00')
                    )
                    retry_after = max(1, int(60 - (now - oldest_call_time.replace(tzinfo=None)).total_seconds()) + 1)

            # Edit quota usage (rolling 24h, counted from ai_call_logs)
            daily_edit_limit = tier.get("daily_edit_limit", 10)
            per_minute_edit_limit = tier.get("per_minute_edit_limit", 2)
            twenty_four_hours_ago = now - timedelta(hours=24)
            edits_response = self.supabase.table("ai_call_logs")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("call_type", "edit")\
                .gte("created_at", twenty_four_hours_ago.isoformat())\
                .execute()
            edits_in_last_day = edits_response.count or 0

            return {
                "tier": tier_name,
                "tier_display_name": tier_display_name,
                "daily": {
                    "limit": daily_limit,
                    "used": current_count,
                    "remaining": max(0, daily_limit - current_count),
                    "resets_at": tomorrow.isoformat(),
                    "resets_in_seconds": resets_in_seconds
                },
                "per_minute": {
                    "limit": per_minute_limit,
                    "calls_in_last_minute": calls_in_last_minute,
                    "can_call_now": can_call_now,
                    "retry_after_seconds": retry_after
                },
                "edits": {
                    "limit": daily_edit_limit,
                    "per_minute_limit": per_minute_edit_limit,
                    "used": edits_in_last_day,
                    "remaining": max(0, daily_edit_limit - edits_in_last_day)
                }
            }

        except Exception as e:
            logger.error(f"Error getting current usage for user {user_id}: {str(e)}", exc_info=True)
            return {"error": str(e)}
