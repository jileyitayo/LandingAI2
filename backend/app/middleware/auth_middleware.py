"""Authentication middleware for protecting routes."""

from typing import Callable, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.auth import verify_token


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect routes that require authentication.
    
    This middleware checks for valid authentication tokens on protected routes
    and adds user information to the request state.
    
    Args:
        excluded_paths: List of path prefixes that don't require authentication
    """
    
    def __init__(
        self,
        app,
        excluded_paths: List[str] = None,
    ):
        super().__init__(app)
        # Default paths that don't require authentication
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/auth/signup",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/previews/builds",
            "/assets",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process the request and check authentication if required.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response from the route handler or error response
        """
        # Check if path is excluded from authentication
        path = request.url.path
        
        if path == "/" or any(path.startswith(excluded) for excluded in self.excluded_paths):
            # Skip authentication for excluded paths
            return await call_next(request)
        
        # Allow OPTIONS requests to pass through for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify Bearer token format
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authorization header format"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token and extract user information
        try:
            user_info = await verify_token(token)
            # Add user info to request state for use in route handlers
            request.state.user = user_info
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers or {},
            )
        
        # Continue to route handler
        response = await call_next(request)
        return response


def get_user_from_request(request: Request) -> dict:
    """
    Helper function to get user information from request state.
    
    This is useful when using the AuthenticationMiddleware.
    The middleware adds user info to request.state.user.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: User information
        
    Raises:
        HTTPException: If user information is not found in request state
        
    Example:
        ```python
        @app.get("/protected")
        async def protected_route(request: Request):
            user = get_user_from_request(request)
            return {"message": f"Hello {user['email']}"}
        ```
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User information not found in request",
        )
    
    return request.state.user


