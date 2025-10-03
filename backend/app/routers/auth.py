"""Authentication routes for user signup, login, logout, and token management."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.auth import (
    SignupRequest,
    LoginRequest,
    RefreshTokenRequest,
    AuthResponse,
    UserResponse,
    MessageResponse,
)
from app.utils.auth import get_current_user
from app.utils.supabase_client import supabase


router = APIRouter()


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user account",
    description="Register a new user with email and password. Returns authentication tokens.",
)
async def signup(request: SignupRequest) -> AuthResponse:
    """
    Create a new user account.
    
    Args:
        request: Signup request containing email, password, and optional first_name and last_name
        
    Returns:
        AuthResponse: Authentication tokens and user information
        
    Raises:
        HTTPException: If signup fails (e.g., email already exists)
    """
    try:
        # Create user with Supabase Auth
        response = supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
                "options": {
                    "data": {
                        "first_name": request.first_name,
                        "last_name": request.last_name,
                    }
                },
            }
        )
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account",
            )
        
        # Return authentication response
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_in=response.session.expires_in or 3600,
            token_type="bearer",
            user={
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at,
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        
        # Handle common Supabase errors
        if "already registered" in error_message.lower() or "already exists" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {error_message}",
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login user",
    description="Authenticate user with email and password. Returns authentication tokens.",
)
async def login(request: LoginRequest) -> AuthResponse:
    """
    Login user with email and password.
    
    Args:
        request: Login request containing email and password
        
    Returns:
        AuthResponse: Authentication tokens and user information
        
    Raises:
        HTTPException: If login fails (invalid credentials)
    """
    try:
        # Authenticate with Supabase
        response = supabase.auth.sign_in_with_password(
            {
                "email": request.email,
                "password": request.password,
            }
        )
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Return authentication response
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_in=response.session.expires_in or 3600,
            token_type="bearer",
            user={
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at,
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Invalidate the current user session. Requires authentication.",
)
async def logout(current_user: dict = Depends(get_current_user)) -> MessageResponse:
    """
    Logout the current user by invalidating their session.
    
    Args:
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        MessageResponse: Confirmation message
        
    Raises:
        HTTPException: If logout fails
    """
    try:
        # Sign out from Supabase
        supabase.auth.sign_out()
        
        return MessageResponse(message="Successfully logged out")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}",
        )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh access token",
    description="Get a new access token using a refresh token.",
)
async def refresh_token(request: RefreshTokenRequest) -> AuthResponse:
    """
    Refresh the access token using a refresh token.
    
    Args:
        request: Refresh token request
        
    Returns:
        AuthResponse: New authentication tokens and user information
        
    Raises:
        HTTPException: If refresh fails (invalid or expired refresh token)
    """
    try:
        # Refresh session with Supabase
        response = supabase.auth.refresh_session(request.refresh_token)
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        
        # Return new authentication response
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_in=response.session.expires_in or 3600,
            token_type="bearer",
            user={
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at,
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.get(
    "/user",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user. Requires authentication.",
)
async def get_user(current_user: dict = Depends(get_current_user)) -> UserResponse:
    """
    Get the current authenticated user's information.
    
    Args:
        current_user: Current authenticated user (injected by dependency)
        
    Returns:
        UserResponse: Current user information
        
    Raises:
        HTTPException: If user retrieval fails
    """
    try:
        user = current_user["user"]
        
        # Return user information
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.user_metadata.get("first_name"),
            last_name=user.user_metadata.get("last_name"),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user information: {str(e)}",
        )

