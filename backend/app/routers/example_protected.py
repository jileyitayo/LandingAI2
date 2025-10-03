"""Example of protected routes using authentication."""

from typing import Optional
from fastapi import APIRouter, Depends, Request
from app.utils.auth import get_current_user, get_current_user_optional
from app.middleware.auth_middleware import get_user_from_request

router = APIRouter()


@router.get("/protected-dependency")
async def protected_with_dependency(current_user: dict = Depends(get_current_user)):
    """
    Example of a protected route using the get_current_user dependency.
    
    This is the recommended approach for most protected endpoints.
    Requires: Authorization: Bearer <token> header
    """
    return {
        "message": f"Hello {current_user['email']}!",
        "user_id": current_user["user_id"],
        "user_email": current_user["email"],
    }


@router.get("/optional-auth")
async def optional_auth_route(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Example of a route with optional authentication.
    
    Returns different content for authenticated vs anonymous users.
    Works with or without: Authorization: Bearer <token> header
    """
    if current_user:
        return {
            "message": f"Welcome back, {current_user['email']}!",
            "authenticated": True,
            "user_id": current_user["user_id"],
        }
    return {
        "message": "Welcome, guest user!",
        "authenticated": False,
    }


@router.get("/protected-middleware")
async def protected_with_middleware(request: Request):
    """
    Example of a protected route using the AuthenticationMiddleware.
    
    When AuthenticationMiddleware is enabled, user info is automatically
    added to request.state.user for protected routes.
    
    Requires: Authorization: Bearer <token> header
    Note: Only works if AuthenticationMiddleware is enabled in main.py
    """
    user = get_user_from_request(request)
    return {
        "message": f"Hello {user['email']}!",
        "user_id": user["user_id"],
        "via": "middleware",
    }


@router.get("/user-profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Example: Get detailed user profile.
    
    Shows how to access full user object from Supabase.
    """
    user = current_user["user"]
    
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "user_metadata": user.user_metadata,
        "app_metadata": user.app_metadata,
    }


