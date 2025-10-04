"""User profile management endpoints."""

import uuid
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from app.utils.auth import get_current_user, get_current_user_optional


from app.models.auth import (
    ProfileUpdateRequest,
    ProfileResponse,
    AvatarUploadResponse,
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
        # Fetch user profile from database
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        # Check if a user profile was found
        # Since we queried by a unique ID, we can safely take the first result
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )
        user_data = response.data[0]
            
        # Return profile response
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

