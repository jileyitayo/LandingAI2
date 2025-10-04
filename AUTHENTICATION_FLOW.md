# Authentication Flow Documentation

## Overview
This document explains how the authentication flow works between the frontend (Next.js) and backend (FastAPI) using Supabase as the authentication provider.

## Complete Authentication Flow

### 1. User Login (Frontend)
```typescript
// frontend/src/hooks/useAuth.ts
const signIn = async ({ email, password }) => {
  // User signs in with Supabase
  const { data } = await supabase.auth.signInWithPassword({
    email,
    password,
  });
  // Supabase stores the session (including access_token) in localStorage
}
```

### 2. Making Authenticated Requests (Frontend)
```typescript
// frontend/src/lib/api.ts

// Step 1: Get the access token from Supabase session
async function getAccessToken(): Promise<string | null> {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;  // This is the JWT token
}

// Step 2: Add token to Authorization header
async function apiRequest<T>(endpoint: string, options: RequestInit = {}) {
  const token = await getAccessToken();
  
  headers["Authorization"] = `Bearer ${token}`;  // Send as Bearer token
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  return response.json();
}

// Example: Get user profile
api.users.getProfile(); // Automatically includes Authorization header
```

### 3. Middleware Intercepts Request (Backend)
```python
# backend/app/middleware/auth_middleware.py

class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Step 1: Extract Authorization header
        auth_header = request.headers.get("Authorization")
        # Example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        
        # Step 2: Parse the Bearer token
        scheme, token = auth_header.split()  # scheme="Bearer", token="eyJh..."
        
        # Step 3: Verify token with Supabase
        user_info = await verify_token(token)
        
        # Step 4: Store user info in request state
        request.state.user = user_info
        # Now contains: { id, sub, user_id, email, user }
        
        # Step 5: Continue to route handler
        return await call_next(request)
```

### 4. Token Verification (Backend)
```python
# backend/app/utils/auth.py

async def verify_token(token: str) -> dict:
    # Verify token with Supabase
    response = supabase.auth.get_user(token)
    
    if not response.user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Return standardized user info
    return {
        "id": response.user.id,           # User UUID
        "sub": response.user.id,          # JWT standard (subject)
        "user_id": response.user.id,      # Alias
        "email": response.user.email,      # User's email
        "user": response.user,            # Full Supabase user object
    }
```

### 5. Route Handler Accesses User Info (Backend)
```python
# backend/app/routers/users.py

@router.get("/me")
async def get_current_user_profile(request: Request):
    # Step 1: Get user info from request state (set by middleware)
    user_info = get_user_from_request(request)
    
    # Step 2: Extract user ID
    user_id = user_info.get("sub") or user_info.get("id")
    
    # Step 3: Fetch user profile from database
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    
    # Step 4: Return profile
    return ProfileResponse(**response.data)
```

### 6. Helper Function (Backend)
```python
# backend/app/middleware/auth_middleware.py

def get_user_from_request(request: Request) -> dict:
    """
    Extract user info from request state.
    This is set by AuthenticationMiddleware.
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return request.state.user
```

## Key Components

### Frontend Components
1. **`useAuth` hook** - Manages Supabase authentication (login/logout)
2. **`createClient`** - Creates Supabase client with session management
3. **`api.ts`** - API client that automatically adds Authorization headers

### Backend Components
1. **`AuthenticationMiddleware`** - Intercepts requests and validates tokens
2. **`verify_token()`** - Verifies JWT token with Supabase
3. **`get_user_from_request()`** - Helper to extract user from request

## Session Storage

The Supabase session (including the access token) is automatically stored in:
- **Browser**: localStorage (key: `sb-<project-ref>-auth-token`)
- **Token Lifespan**: 1 hour (automatically refreshed by Supabase)

## Security Notes

1. **Token is httpOnly**: Not accessible via JavaScript (managed by Supabase)
2. **Automatic Refresh**: Supabase automatically refreshes expired tokens
3. **CORS**: Backend allows credentials from frontend origin
4. **HTTPS**: Use HTTPS in production for secure token transmission

## Testing the Flow

### 1. Check if user is logged in (Frontend)
```typescript
const supabase = createClient();
const { data: { session } } = await supabase.auth.getSession();
console.log("Token:", session?.access_token);
```

### 2. Test API call (Frontend)
```typescript
try {
  const profile = await api.users.getProfile();
  console.log("Profile:", profile);
} catch (error) {
  console.error("Error:", error);
}
```

### 3. Check middleware (Backend logs)
```
# You should see:
🔑 Request to /api/v1/users/me
✅ User authenticated: user_id=xxx, email=user@example.com
```

## Troubleshooting

### Error: "Missing authentication credentials"
- **Cause**: User not logged in or session expired
- **Fix**: Redirect to login page

### Error: "Invalid authentication credentials"
- **Cause**: Token is invalid or expired
- **Fix**: Refresh session or re-login

### Error: "User information not found in request"
- **Cause**: Middleware not registered or route not protected
- **Fix**: Ensure `AuthenticationMiddleware` is added to FastAPI app

## Summary

The authentication flow is simple:
1. ✅ User logs in → Supabase stores JWT token
2. ✅ Frontend gets token → Adds to Authorization header
3. ✅ Middleware intercepts → Verifies token with Supabase
4. ✅ Route handler → Accesses user info from request state
5. ✅ Returns data → Frontend displays profile

Everything is already connected! Just restart your backend server.

