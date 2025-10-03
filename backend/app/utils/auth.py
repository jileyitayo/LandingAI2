"""Authentication utilities and dependencies."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings
from app.utils.supabase_client import supabase


# HTTP Bearer token scheme
security = HTTPBearer()


async def verify_token(token: str) -> dict:
    """
    Verify and decode a Supabase JWT token.
    
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Get Supabase JWT from user
        response = supabase.auth.get_user(token)
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": response.user.id,
            "email": response.user.email,
            "user": response.user,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    FastAPI dependency to get the current authenticated user.
    
    This dependency can be used in route handlers to protect endpoints
    and access user information.
        
    Example:
        ```python
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"message": f"Hello {user['email']}"}
        ```
    """
    token = credentials.credentials
    return await verify_token(token)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    FastAPI dependency to optionally get the current authenticated user.
    
    Unlike get_current_user, this dependency doesn't raise an error if
    no authentication is provided. Useful for endpoints that have different
    behavior for authenticated vs anonymous users.

    Example:
        ```python
        @app.get("/optional-auth")
        async def optional_route(user: Optional[dict] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user['email']}"}
            return {"message": "Hello anonymous user"}
        ```
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        return await verify_token(token)
    except HTTPException:
        return None

