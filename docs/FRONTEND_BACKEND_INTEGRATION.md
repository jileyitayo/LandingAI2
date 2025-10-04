# Frontend-Backend Authentication Integration Guide

This document explains how the Next.js frontend connects to the FastAPI backend with Supabase authentication.

## Architecture Overview

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Next.js       │      │   Supabase       │      │   FastAPI       │
│   Frontend      │◄────►│   Auth Service   │◄────►│   Backend       │
└─────────────────┘      └──────────────────┘      └─────────────────┘
        │                                                    │
        │  1. Login/Signup (Supabase JS SDK)                │
        │───────────────────────────────────►               │
        │                                                    │
        │  2. Get access_token from session                 │
        │                                                    │
        │  3. API request with Authorization header         │
        │───────────────────────────────────────────────────►│
        │                                                    │
        │                     4. Verify token with Supabase │
        │                                    ◄───────────────│
        │                                                    │
        │  5. Return user data                              │
        │◄───────────────────────────────────────────────────│
```

## Why Backend Auth is Needed

Even though the frontend manages the Supabase session, the backend still needs to verify authentication because:

1. **Security**: Never trust client-provided data - the backend must independently verify tokens
2. **Defense-in-depth**: Client can be compromised; backend is the source of truth
3. **Multi-client support**: Mobile apps, webhooks, server-to-server calls need the same API
4. **Centralized authorization**: Backend enforces permissions and returns proper 401/403 responses
5. **Stateless API**: Each request must be authenticated independently

## Authentication Flow

### 1. Frontend Login (Supabase)

```tsx
// User logs in via frontend
import { createClient } from "@/lib/supabase/client";

const supabase = createClient();
const { data, error } = await supabase.auth.signInWithPassword({
  email: "user@example.com",
  password: "password123",
});

// Supabase stores the session (access_token + refresh_token) in browser
```

### 2. Frontend Calls Backend API

```tsx
// API client automatically includes Authorization header
import { api } from "@/lib/api";

try {
  // This internally:
  // 1. Gets access_token from Supabase session
  // 2. Adds header: Authorization: Bearer <access_token>
  // 3. Makes request to backend
  const user = await api.auth.getUser();
  console.log(user);
} catch (err) {
  if (err.status === 401) {
    // Token expired or invalid - redirect to login
  }
}
```

### 3. Backend Verifies Token

```python
# Backend receives request with Authorization header
# app/utils/auth.py

async def verify_token(token: str) -> dict:
    # Verify token with Supabase
    response = supabase.auth.get_user(token)
    
    if not response.user:
        raise HTTPException(status_code=401)
    
    return {
        "user_id": response.user.id,
        "email": response.user.email,
        "user": response.user,
    }

# app/routers/auth.py
@router.get("/user")
async def get_user(current_user: dict = Depends(get_current_user)):
    # current_user is automatically injected after token verification
    return UserResponse(
        id=current_user["user"].id,
        email=current_user["user"].email,
        # ... other fields
    )
```

## Key Files

### Frontend

- **`src/lib/api.ts`**: API client that automatically includes Authorization headers
- **`src/lib/supabase/client.ts`**: Supabase client for browser/client components
- **`src/lib/supabase/server.ts`**: Supabase client for server components
- **`src/hooks/useAuth.ts`**: React hook for managing auth state
- **`src/components/UserProfileCard.tsx`**: Example component using backend API

### Backend

- **`app/utils/auth.py`**: Token verification and `get_current_user` dependency
- **`app/routers/auth.py`**: Auth endpoints (login, signup, logout, etc.)
- **`app/middleware/auth_middleware.py`**: Optional middleware for global auth
- **`app/utils/supabase_client.py`**: Backend Supabase client

## Usage Examples

### Client Component (CSR)

```tsx
"use client";

import { api } from "@/lib/api";
import { useEffect, useState } from "react";

export function MyComponent() {
  const [data, setData] = useState(null);

  useEffect(() => {
    async function fetchData() {
      // Automatically includes Authorization header
      const result = await api.auth.getUser();
      setData(result);
    }
    fetchData();
  }, []);

  return <div>{data?.email}</div>;
}
```

### Server Component (RSC)

```tsx
import { createServerClient } from "@/lib/supabase";
import { serverApiRequest } from "@/lib/api";

export default async function Page() {
  const supabase = await createServerClient();
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    redirect("/auth/login");
  }

  // Call backend with explicit token
  const user = await serverApiRequest(
    "/api/v1/auth/user",
    session.access_token
  );

  return <div>Hello {user.email}</div>;
}
```

### Server Action

```tsx
"use server";

import { createServerClient } from "@/lib/supabase";
import { serverApiRequest } from "@/lib/api";

export async function updateProfile(formData: FormData) {
  const supabase = await createServerClient();
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    throw new Error("Not authenticated");
  }

  await serverApiRequest(
    "/api/v1/user/profile",
    session.access_token,
    {
      method: "PUT",
      body: JSON.stringify({
        first_name: formData.get("first_name"),
        last_name: formData.get("last_name"),
      }),
    }
  );
}
```

## Adding New Protected Endpoints

### 1. Create Backend Route

```python
# backend/app/routers/projects.py
from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user

router = APIRouter()

@router.get("/projects")
async def list_projects(current_user: dict = Depends(get_current_user)):
    """Protected endpoint - requires authentication"""
    user_id = current_user["user_id"]
    # Fetch user's projects
    return {"projects": []}
```

### 2. Register Router

```python
# backend/app/main.py
from app.routers import projects

app.include_router(
    projects.router,
    prefix="/api/v1/projects",
    tags=["Projects"]
)
```

### 3. Add to Frontend API Client

```tsx
// frontend/src/lib/api.ts
export const api = {
  // ... existing endpoints

  projects: {
    list: () => apiRequest<Project[]>("/api/v1/projects"),
    
    get: (id: string) => 
      apiRequest<Project>(`/api/v1/projects/${id}`),
    
    create: (data: CreateProjectData) =>
      apiRequest<Project>("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
};
```

### 4. Use in Frontend Component

```tsx
"use client";

import { api } from "@/lib/api";

export function ProjectList() {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    api.projects.list().then(setProjects);
  }, []);

  return <div>{/* render projects */}</div>;
}
```

## Environment Variables

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### Backend (.env)

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

## Error Handling

The API client throws `ApiError` for failed requests:

```tsx
import { api, ApiError } from "@/lib/api";

try {
  const user = await api.auth.getUser();
} catch (err) {
  if (err instanceof ApiError) {
    if (err.status === 401) {
      // Unauthorized - token expired or invalid
      router.push("/auth/login");
    } else if (err.status === 403) {
      // Forbidden - user doesn't have permission
      alert("Access denied");
    } else {
      // Other errors
      console.error(err.message);
    }
  }
}
```

## Token Refresh

Supabase automatically refreshes tokens before they expire. The frontend API client always gets the latest token from the session:

```tsx
async function getAccessToken(): Promise<string | null> {
  const supabase = createClient();
  
  // Supabase SDK handles token refresh automatically
  const { data: { session } } = await supabase.auth.getSession();
  
  return session?.access_token ?? null;
}
```

## Security Best Practices

1. **Never store tokens manually** - let Supabase SDK handle it
2. **Always use HTTPS** in production
3. **Set proper CORS origins** in backend (don't use `*`)
4. **Validate all inputs** on the backend, never trust client data
5. **Use environment variables** for secrets
6. **Implement rate limiting** on sensitive endpoints
7. **Log authentication failures** for security monitoring

## Testing

### Test Backend Auth

```bash
# Get a token from Supabase
# Then test the backend endpoint

curl http://localhost:8000/api/v1/auth/user \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test Frontend Integration

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Sign up/login at http://localhost:3000/auth/login
4. Visit http://localhost:3000/dashboard
5. See both frontend session and backend-verified user data

## Common Issues

### 401 Unauthorized

- **Cause**: Token expired, invalid, or missing
- **Fix**: User should re-login; frontend should redirect to `/auth/login`

### 403 Forbidden

- **Cause**: User doesn't have permission for the resource
- **Fix**: Check user roles/permissions on backend

### CORS Errors

- **Cause**: Backend CORS settings don't allow frontend origin
- **Fix**: Update `settings.cors_origins` in `backend/app/config.py`

### Token Not Sent

- **Cause**: User not logged in or session expired
- **Fix**: Check if `supabase.auth.getSession()` returns a session

## Next Steps

1. Add more protected endpoints as your app grows
2. Implement role-based access control (RBAC) on backend
3. Add request/response logging for debugging
4. Set up monitoring and error tracking (Sentry, etc.)
5. Implement API rate limiting
6. Add integration tests for auth flows

## Reference Documentation

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Authentication](https://nextjs.org/docs/authentication)
