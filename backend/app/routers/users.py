"""User profile management endpoints."""

import uuid
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Depends, Query
from fastapi.responses import JSONResponse
from app.utils.auth import get_current_user, get_current_user_optional
from app.utils.rate_limiter import RateLimiter
import logging

logger = logging.getLogger(__name__)

from app.models.auth import (
    ProfileUpdateRequest,
    ProfileResponse,
    AvatarUploadResponse,
)
from app.models.users import (
    UsageAnalyticsResponse,
    AnalyticsDataPoint,
)
from app.middleware.auth_middleware import get_user_from_request
from app.utils.supabase_client import supabase
from app.utils.action_logger import log_action

router = APIRouter()


# Allowed image types for avatar upload
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
}

# Maximum file size: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024



@router.get("/profile")
@log_action(action_type='READ', target_resource_type='user_profile')
async def get_current_user_profile(request: Request):
    """
    Get current user profile.

    Returns the authenticated user's profile information including
    personal details, subscription status, and usage statistics.

    Args:
        request: FastAPI request object (contains user info from middleware)

    Returns:
        ProfileResponse: User profile data

    Raises:
        HTTPException: If user not found or database error occurs
    """
    try:
        # Get user info from request (set by authentication middleware)
        user_info = get_user_from_request(request)
        user_id = user_info.get("sub") or user_info.get("id")

        # Fetch user profile with subscription details (join with user_subscriptions and subscription_tiers)
        response = supabase.table("users")\
            .select(
                "*, "
                "user_subscriptions("
                "id, status, current_period_start, current_period_end, "
                "cancel_at_period_end, cancelled_at, trial_start, trial_end, "
                "subscription_tiers("
                "id, tier_name, display_name, description, "
                "daily_generation_limit, per_minute_limit, "
                "price_monthly, price_yearly, features, is_active"
                ")"
                ")"
            )\
            .eq("id", user_id)\
            .execute()

        # Check if a user profile was found
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )
        user_data = response.data[0]

        # Count actual projects for this user (excluding soft-deleted)
        project_count_response = supabase.table("projects")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .is_("deleted_at", "null")\
            .execute()

        # Get the actual project count
        actual_project_count = project_count_response.count if project_count_response.count is not None else 0

        # Build subscription details object
        subscription_data = None
        user_subscription = user_data.get("user_subscriptions")

        if user_subscription and user_subscription.get("subscription_tiers"):
            tier = user_subscription["subscription_tiers"]
            subscription_data = {
                "id": user_subscription["id"],
                "status": user_subscription["status"],
                "tier": {
                    "id": tier["id"],
                    "tier_name": tier["tier_name"],
                    "display_name": tier["display_name"],
                    "description": tier.get("description"),
                    "daily_generation_limit": tier["daily_generation_limit"],
                    "per_minute_limit": tier["per_minute_limit"],
                    "price_monthly": float(tier["price_monthly"]) if tier["price_monthly"] else 0,
                    "price_yearly": float(tier["price_yearly"]) if tier["price_yearly"] else 0,
                    "features": tier.get("features", []),
                    "is_active": tier["is_active"]
                },
                "current_period_start": user_subscription.get("current_period_start"),
                "current_period_end": user_subscription.get("current_period_end"),
                "cancel_at_period_end": user_subscription.get("cancel_at_period_end", False),
                "cancelled_at": user_subscription.get("cancelled_at"),
                "trial_start": user_subscription.get("trial_start"),
                "trial_end": user_subscription.get("trial_end")
            }

        # Return profile response
        return ProfileResponse(
            id=user_data["id"],
            email=user_data["email"],
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            avatar_url=user_data.get("avatar_url"),
            subscription_tier=user_data["subscription_tier"],
            generation_count=actual_project_count,
            current_period_generations=user_data["current_period_generations"],
            email_verified=user_data["email_verified"],
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"],
            subscription=subscription_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetche user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user profile: {str(e)}",
        )


@router.patch("/profile", response_model=ProfileResponse)
@log_action(action_type='UPDATE', target_resource_type='user_profile')
async def update_current_user_profile(
    request: Request,
    profile_update: ProfileUpdateRequest,
):
    """
    Update current user profile.

    Updates the authenticated user's profile information such as
    first name and last name.

    Args:
        request: FastAPI request object (contains user info from middleware)
        profile_update: Profile update data

    Returns:
        ProfileResponse: Updated user profile data

    Raises:
        HTTPException: If user not found, validation fails, or database error occurs
    """
    try:
        # Get user info from request
        user_info = get_user_from_request(request)
        user_id = user_info.get("sub") or user_info.get("id")

        # Prepare update data (only include non-None values)
        update_data = {}
        if profile_update.first_name is not None:
            update_data["first_name"] = profile_update.first_name
        if profile_update.last_name is not None:
            update_data["last_name"] = profile_update.last_name

        # If no fields to update, return current profile
        if not update_data:
            response = supabase.table("users").select("*").eq("id", user_id).execute()
            user_data = response.data
        else:
            # Update user profile
            response = (
                supabase.table("users")
                .update(update_data)
                .eq("id", user_id)
                .execute()
            )

     

        if not response.data:
            pass
            # print("User profile not found")

        user_data = response.data[0]    

        # Return updated profile
        return ProfileResponse(
            id=user_data["id"],
            email=user_data["email"],
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            avatar_url=user_data.get("avatar_url"),
            subscription_tier=user_data["subscription_tier"],
            generation_count=user_data["generation_count"],
            current_period_generations=user_data["current_period_generations"],
            email_verified=user_data["email_verified"],
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}",
        )


@router.post("/avatar", response_model=AvatarUploadResponse)
@log_action(action_type='UPDATE', target_resource_type='user_profile_avatar')
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Upload user avatar image.

    Uploads an avatar image to Supabase Storage and updates the user's
    profile with the avatar URL. Only image files are allowed.

    Args:
        request: FastAPI request object (contains user info from middleware)
        file: Uploaded image file

    Returns:
        AvatarUploadResponse: Avatar URL and success message

    Raises:
        HTTPException: If file validation fails, upload fails, or database error occurs
    """
    try:
        # Get user info from request
        user_info = get_user_from_request(request)
        user_id = user_info.get("sub") or user_info.get("id")

        # Validate file type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}",
            )

        # Read file content
        file_content = await file.read()

        # Validate file size
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024)}MB",
            )

        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{user_id}/{uuid.uuid4()}.{file_extension}"

        # Upload to Supabase Storage
        # Create bucket if it doesn't exist (avatars bucket)
        try:
            storage_response = supabase.storage.from_("avatars").upload(
                path=unique_filename,
                file=file_content,
                file_options={"content-type": file.content_type},
            )
        except Exception as upload_error:
            # If upload fails, it might be because the bucket doesn't exist
            # or the file already exists - try to update instead
            try:
                storage_response = supabase.storage.from_("avatars").update(
                    path=unique_filename,
                    file=file_content,
                    file_options={"content-type": file.content_type},
                )
            except Exception:
                logger.error(f"Failed to upload avatar: {str(upload_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload avatar: {str(upload_error)}",
                )

        # Get public URL for the uploaded file
        avatar_url = supabase.storage.from_("avatars").get_public_url(unique_filename)

        # Update user profile with avatar URL
        update_response = (
            supabase.table("users")
            .update({"avatar_url": avatar_url})
            .eq("id", user_id)
            .execute()
        )

        if not update_response.data:
            # If update fails, delete the uploaded file to avoid orphaned files
            try:
                supabase.storage.from_("avatars").remove([unique_filename])
            except Exception:
                pass  # Ignore cleanup errors
            logger.error(f"Failed to update user profile with avatar URL")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile with avatar URL",
            )

        return AvatarUploadResponse(
            avatar_url=avatar_url,
            message="Avatar uploaded successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}",
        )


@router.get("/usage/current")
@log_action(action_type='READ', target_resource_type='user_usage_stats')
async def get_current_usage(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get current usage statistics for the authenticated user.

    Returns detailed information about:
    - Current subscription tier
    - Daily usage (limit, used, remaining, reset time)
    - Per-minute usage (limit, calls in last minute, whether can call now)

    This endpoint helps users understand their usage and when they can make their next AI call.

    Args:
        request: FastAPI request object
        current_user: Authenticated user from dependency

    Returns:
        Dictionary with usage statistics:
        {
            "tier": "free",
            "tier_display_name": "Free Plan",
            "daily": {
                "limit": 5,
                "used": 3,
                "remaining": 2,
                "resets_at": "2025-10-25T00:00:00Z",
                "resets_in_seconds": 43200
            },
            "per_minute": {
                "limit": 1,
                "calls_in_last_minute": 0,
                "can_call_now": true,
                "retry_after_seconds": 0
            }
        }

    Raises:
        HTTPException: If error occurs while fetching usage data
    """
    try:
        user_id = current_user.get("id")

        # Use rate limiter to get usage stats
        rate_limiter = RateLimiter(supabase)
        usage_data = await rate_limiter.get_current_usage(user_id)

        if "error" in usage_data:
            logger.error(f"Error getting usage for user {user_id}: {usage_data['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch usage data: {usage_data['error']}"
            )

        return usage_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch usage data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch usage data: {str(e)}",
        )


@router.get("/analytics", response_model=UsageAnalyticsResponse)
@log_action(action_type='READ', target_resource_type='user_analytics')
async def get_usage_analytics(
    request: Request,
    current_user: dict = Depends(get_current_user),
    period: str = Query("7d", regex="^(24h|7d|30d|all)$", description="Time period: 24h, 7d, 30d, or all"),
    granularity: str = Query("daily", regex="^(hourly|daily)$", description="Data granularity: hourly or daily")
):
    """
    Get usage analytics for the authenticated user.

    Returns time-series data showing AI call patterns over time, with configurable
    time period and granularity. Useful for visualizing usage trends.

    Args:
        request: FastAPI request object
        current_user: Authenticated user from dependency
        period: Time period to analyze (24h, 7d, 30d, all)
        granularity: Data granularity (hourly for 24h period, daily otherwise)

    Returns:
        UsageAnalyticsResponse with:
        - Time-series data points
        - Total calls in period
        - Peak RPM (requests per minute)
        - Average RPD (requests per day)
        - Breakdown by call type

    Raises:
        HTTPException: If error occurs while fetching analytics data
    """
    try:
        user_id = current_user.get("id")
        now = datetime.utcnow()

        # Calculate date range based on period
        if period == "24h":
            start_date = now - timedelta(hours=24)
            granularity = "hourly"  # Force hourly for 24h period
        elif period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        else:  # "all"
            start_date = None

        # Build query for ai_call_logs
        query = supabase.table("ai_call_logs")\
            .select("created_at, call_type")\
            .eq("user_id", user_id)\
            .order("created_at", desc=False)

        if start_date:
            query = query.gte("created_at", start_date.isoformat())

        calls_response = query.execute()
        all_calls = calls_response.data or []

        # Process data into time buckets
        data_points = []
        breakdown_by_type = {}
        total_calls = len(all_calls)

        if granularity == "hourly":
            # Group by hour
            buckets = {}
            for call in all_calls:
                created_at = datetime.fromisoformat(call["created_at"].replace('Z', '+00:00'))
                bucket_time = created_at.replace(minute=0, second=0, microsecond=0, tzinfo=None)
                bucket_key = bucket_time.isoformat()

                if bucket_key not in buckets:
                    buckets[bucket_key] = {"count": 0, "call_types": {}}

                buckets[bucket_key]["count"] += 1
                call_type = call["call_type"]
                buckets[bucket_key]["call_types"][call_type] = buckets[bucket_key]["call_types"].get(call_type, 0) + 1

                # Update overall breakdown
                breakdown_by_type[call_type] = breakdown_by_type.get(call_type, 0) + 1

            # Convert to data points
            for timestamp, data in sorted(buckets.items()):
                data_points.append(AnalyticsDataPoint(
                    timestamp=timestamp + "Z",
                    count=data["count"],
                    call_types=data["call_types"]
                ))

        else:  # daily
            # Group by day
            buckets = {}
            for call in all_calls:
                created_at = datetime.fromisoformat(call["created_at"].replace('Z', '+00:00'))
                bucket_time = created_at.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                bucket_key = bucket_time.isoformat()

                if bucket_key not in buckets:
                    buckets[bucket_key] = {"count": 0, "call_types": {}}

                buckets[bucket_key]["count"] += 1
                call_type = call["call_type"]
                buckets[bucket_key]["call_types"][call_type] = buckets[bucket_key]["call_types"].get(call_type, 0) + 1

                # Update overall breakdown
                breakdown_by_type[call_type] = breakdown_by_type.get(call_type, 0) + 1

            # Convert to data points
            for timestamp, data in sorted(buckets.items()):
                data_points.append(AnalyticsDataPoint(
                    timestamp=timestamp + "Z",
                    count=data["count"],
                    call_types=data["call_types"]
                ))

        # Calculate RPM peak and RPD average
        rpm_peak = 0
        if all_calls:
            # Calculate peak RPM by looking at 1-minute windows
            minute_buckets = {}
            for call in all_calls:
                created_at = datetime.fromisoformat(call["created_at"].replace('Z', '+00:00'))
                minute_key = created_at.replace(second=0, microsecond=0, tzinfo=None).isoformat()
                minute_buckets[minute_key] = minute_buckets.get(minute_key, 0) + 1

            rpm_peak = max(minute_buckets.values()) if minute_buckets else 0

        # Calculate RPD average
        if period == "24h":
            days_in_period = 1
        elif period == "7d":
            days_in_period = 7
        elif period == "30d":
            days_in_period = 30
        else:
            # For "all", calculate actual days
            if all_calls:
                first_call = datetime.fromisoformat(all_calls[0]["created_at"].replace('Z', '+00:00'))
                last_call = datetime.fromisoformat(all_calls[-1]["created_at"].replace('Z', '+00:00'))
                days_in_period = max(1, (last_call - first_call).days + 1)
            else:
                days_in_period = 1

        rpd_average = round(total_calls / days_in_period, 2) if days_in_period > 0 else 0.0

        return UsageAnalyticsResponse(
            period=period,
            granularity=granularity,
            data_points=data_points,
            total_calls=total_calls,
            rpm_peak=rpm_peak,
            rpd_average=rpd_average,
            breakdown_by_type=breakdown_by_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch analytics data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics data: {str(e)}",
        )

