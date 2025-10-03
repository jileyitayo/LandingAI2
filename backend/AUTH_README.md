# FastAPI Authentication with Supabase

This documentation explains how to use the authentication system integrated with Supabase.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication Endpoints](#authentication-endpoints)
3. [Protecting Routes](#protecting-routes)
4. [Using Authentication Middleware](#using-authentication-middleware)
5. [Testing with cURL](#testing-with-curl)
6. [Common Use Cases](#common-use-cases)
7. [Error Handling](#error-handling)

---

## Quick Start

### 1. Environment Setup

Make sure you have Supabase credentials configured in your `.env` file:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

### 2. Start the Server

```bash
cd backend
uvicorn app.main:app --reload
```

### 3. Access API Documentation

Visit: `http://localhost:8000/docs`

You'll see all authentication endpoints with interactive testing.

---

## Authentication Endpoints

### POST `/api/v1/auth/signup`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "created_at": "2025-10-03T12:00:00Z"
  }
}
```

### POST `/api/v1/auth/login`

Login with existing credentials.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** Same as signup

### POST `/api/v1/auth/logout`

Logout the current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### POST `/api/v1/auth/refresh`

Get a new access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** Same as login

### GET `/api/v1/auth/user`

Get current user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2025-10-03T12:00:00Z",
  "updated_at": "2025-10-03T12:00:00Z"
}
```

---

## Protecting Routes

### Method 1: Using Dependency Injection (Recommended)

This is the most flexible and recommended approach:

```python
from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user

router = APIRouter()

@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """This route requires authentication."""
    return {
        "message": f"Hello {current_user['email']}",
        "user_id": current_user["user_id"]
    }
```

**User Object Structure:**
```python
current_user = {
    "user_id": "123e4567-...",
    "email": "user@example.com",
    "user": <Supabase User Object>
}
```

### Method 2: Optional Authentication

Allow both authenticated and anonymous users:

```python
from typing import Optional
from fastapi import Depends
from app.utils.auth import get_current_user_optional

@router.get("/optional-auth")
async def optional_route(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Works with or without authentication."""
    if current_user:
        return {"message": f"Hello {current_user['email']}"}
    return {"message": "Hello guest"}
```

### Method 3: Using Middleware

Enable middleware in `main.py`:

```python
from app.middleware import AuthenticationMiddleware

# Add after CORS middleware
app.add_middleware(
    AuthenticationMiddleware,
    excluded_paths=[
        "/docs",
        "/redoc",
        "/openapi.json",
        "/",
        "/api/v1/health",
        "/api/v1/auth/signup",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    ]
)
```

Then access user from request:

```python
from fastapi import Request
from app.middleware.auth_middleware import get_user_from_request

@router.get("/protected")
async def protected_route(request: Request):
    """Middleware handles authentication automatically."""
    user = get_user_from_request(request)
    return {"message": f"Hello {user['email']}"}
```

**Note:** Middleware approach protects ALL routes by default (except excluded paths). Use dependency injection for more granular control.

---

## Testing with cURL

### 1. Sign Up

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepass123",
    "full_name": "Test User"
  }'
```

Save the `access_token` from the response.

### 2. Access Protected Route

```bash
curl -X GET http://localhost:8000/api/v1/auth/user \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Refresh Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### 4. Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Common Use Cases

### 1. User-Specific Data Access

```python
from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.utils.supabase_client import supabase

router = APIRouter()

@router.get("/my-projects")
async def get_user_projects(current_user: dict = Depends(get_current_user)):
    """Get projects belonging to the current user."""
    user_id = current_user["user_id"]
    
    response = supabase.table("projects")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    return {"projects": response.data}
```

### 2. Role-Based Access Control

```python
from fastapi import HTTPException, status

async def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency that requires admin role."""
    user = current_user["user"]
    
    # Check if user has admin role in metadata
    if not user.app_metadata.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """Admin-only endpoint."""
    # Delete user logic here
    pass
```

### 3. Creating Resources with User Association

```python
from pydantic import BaseModel

class CreateProjectRequest(BaseModel):
    name: str
    description: str

@router.post("/projects")
async def create_project(
    project: CreateProjectRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new project associated with the user."""
    user_id = current_user["user_id"]
    
    response = supabase.table("projects").insert({
        "name": project.name,
        "description": project.description,
        "user_id": user_id,
    }).execute()
    
    return {"project": response.data[0]}
```

---

## Error Handling

### Common Authentication Errors

#### 401 Unauthorized

```json
{
  "detail": "Invalid authentication credentials"
}
```

**Causes:**
- Invalid token
- Expired token
- Missing Authorization header
- Malformed token

**Solution:** Login again to get a new token.

#### 403 Forbidden

```json
{
  "detail": "Admin access required"
}
```

**Causes:**
- User doesn't have required permissions
- Insufficient role/privileges

**Solution:** Contact administrator for access.

#### 409 Conflict

```json
{
  "detail": "An account with this email already exists"
}
```

**Causes:**
- Email already registered during signup

**Solution:** Use login instead or recover password.

### Handling Expired Tokens

Tokens expire after 1 hour by default. Use refresh tokens to get new access tokens:

```python
import httpx

async def refresh_access_token(refresh_token: str) -> str:
    """Refresh the access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        
        # Refresh token expired, need to login again
        raise Exception("Session expired, please login again")
```

---

## Best Practices

### 1. Token Storage (Frontend)

**Do:**
- Store access tokens in memory (state management)
- Store refresh tokens in httpOnly cookies (if using SSR)
- Use environment variables for API URLs

**Don't:**
- Store tokens in localStorage (XSS vulnerability)
- Expose service_role key in frontend
- Hardcode API credentials

### 2. Security Headers

Already configured in the application:
- CORS properly configured
- Bearer token authentication
- Proper HTTP status codes

### 3. Password Requirements

Enforce strong passwords:
- Minimum 8 characters (configured in models)
- Consider adding complexity requirements in production
- Use Supabase password reset flow for password changes

### 4. Error Messages

Don't expose sensitive information:

```python
# ❌ Bad - Exposes implementation details
raise HTTPException(detail=f"Database error: {str(e)}")

# ✅ Good - Generic but helpful
raise HTTPException(detail="Authentication failed")
```

---

## Integration with Frontend

### Next.js Example

```typescript
// lib/api/auth.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function login(email: string, password: string) {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  
  if (!response.ok) {
    throw new Error('Login failed');
  }
  
  return response.json();
}

export async function fetchProtectedData(token: string) {
  const response = await fetch(`${API_URL}/api/v1/protected`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch data');
  }
  
  return response.json();
}
```

---

## Troubleshooting

### Issue: "Could not validate credentials"

**Check:**
1. Token is being sent in Authorization header
2. Format is: `Bearer <token>` (with space)
3. Token hasn't expired (< 1 hour old)
4. Supabase URL and keys are correctly configured

### Issue: "Failed to create user account"

**Check:**
1. Supabase project is running
2. Environment variables are loaded
3. Email is valid format
4. Password meets minimum requirements (8 chars)
5. Database migration has been applied

### Issue: Middleware not protecting routes

**Check:**
1. Middleware is added to app in `main.py`
2. Route path is not in `excluded_paths`
3. Middleware is added before route handlers

---

## Next Steps

- **Add password reset:** Implement forgot password flow
- **Email verification:** Enable email confirmation in Supabase
- **OAuth providers:** Add Google, GitHub login
- **Rate limiting:** Protect against brute force attacks
- **Logging:** Add authentication event logging
- **Monitoring:** Track failed login attempts

---

## Support

For more information:
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)

---

**Last Updated:** October 3, 2025  
**Version:** 1.0


