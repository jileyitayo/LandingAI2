# API Client Usage Examples

This document shows how to use the API client (`src/lib/api.ts`) to communicate with the FastAPI backend.

## Client-Side (Client Components)

### Basic Usage

```tsx
"use client";

import { api, ApiError } from "@/lib/api";
import { useEffect, useState } from "react";

export function UserProfile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchUser() {
      try {
        const userData = await api.auth.getUser();
        setUser(userData);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
          // Handle specific error codes
          if (err.status === 401) {
            // Redirect to login or refresh token
          }
        }
      } finally {
        setLoading(false);
      }
    }

    fetchUser();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return null;

  return (
    <div>
      <h2>{user.email}</h2>
      <p>Name: {user.first_name} {user.last_name}</p>
    </div>
  );
}
```

### With Error Handling

```tsx
"use client";

import { api, ApiError } from "@/lib/api";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function LogoutButton() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogout = async () => {
    setLoading(true);
    
    try {
      // Call backend logout endpoint
      await api.auth.logout();
      
      // Also sign out from Supabase client
      const supabase = createClient();
      await supabase.auth.signOut();
      
      // Redirect to login
      router.push("/auth/login");
    } catch (err) {
      if (err instanceof ApiError) {
        console.error("Logout failed:", err.message);
        // Still try to sign out locally
        const supabase = createClient();
        await supabase.auth.signOut();
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleLogout} disabled={loading}>
      {loading ? "Logging out..." : "Logout"}
    </button>
  );
}
```

### In a Server Action

```tsx
"use server";

import { createServerClient } from "@/lib/supabase";
import { serverApiRequest } from "@/lib/api";

export async function getUserFromBackend() {
  // Get session from Supabase (server-side)
  const supabase = await createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    throw new Error("Not authenticated");
  }

  // Call backend with token
  const user = await serverApiRequest<{
    id: string;
    email: string;
    first_name?: string;
    last_name?: string;
  }>("/api/v1/auth/user", session.access_token);

  return user;
}
```

### In a Server Component

```tsx
import { createServerClient } from "@/lib/supabase";
import { serverApiRequest } from "@/lib/api";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const supabase = await createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/auth/login");
  }

  // Fetch user from backend
  const user = await serverApiRequest<{
    id: string;
    email: string;
    first_name?: string;
    last_name?: string;
  }>("/api/v1/auth/user", session.access_token);

  return (
    <div>
      <h1>Welcome, {user.first_name || user.email}!</h1>
      <p>User ID: {user.id}</p>
    </div>
  );
}
```

### In a Route Handler

```tsx
// app/api/user/route.ts
import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase/server";
import { serverApiRequest } from "@/lib/api";

export async function GET(request: NextRequest) {
  const supabase = await createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const user = await serverApiRequest(
      "/api/v1/auth/user",
      session.access_token
    );
    return NextResponse.json(user);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch user" },
      { status: 500 }
    );
  }
}
```

## Authentication Flow

### Option 1: Using Supabase Directly (Recommended for Auth)

For signup, login, and logout, it's recommended to use Supabase directly from the frontend:

```tsx
"use client";

import { createClient } from "@/lib/supabase/client";

// Sign up
const supabase = createClient();
const { data, error } = await supabase.auth.signUp({
  email: "user@example.com",
  password: "password123",
  options: {
    data: {
      first_name: "John",
      last_name: "Doe",
    },
  },
});

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: "user@example.com",
  password: "password123",
});

// Sign out
await supabase.auth.signOut();
```

### Option 2: Using Backend API

If you need to use the backend API for authentication:

```tsx
"use client";

import { api } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

// Sign up via backend
const response = await api.auth.signup({
  email: "user@example.com",
  password: "password123",
  first_name: "John",
  last_name: "Doe",
});

// Set the session in Supabase client
const supabase = createClient();
await supabase.auth.setSession({
  access_token: response.access_token,
  refresh_token: response.refresh_token,
});
```

## Adding New Endpoints

When you add new endpoints to the backend, update the API client:

```tsx
// In src/lib/api.ts

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
    
    update: (id: string, data: UpdateProjectData) =>
      apiRequest<Project>(`/api/v1/projects/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    
    delete: (id: string) =>
      apiRequest<void>(`/api/v1/projects/${id}`, {
        method: "DELETE",
      }),
  },
};
```

## Environment Variables

Make sure you have the following environment variables set:

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

## Error Handling

The API client throws `ApiError` for failed requests:

```tsx
try {
  const user = await api.auth.getUser();
} catch (err) {
  if (err instanceof ApiError) {
    // Access status code
    console.error("Status:", err.status);
    
    // Access error message
    console.error("Message:", err.message);
    
    // Access full error details
    console.error("Details:", err.detail);
    
    // Handle specific errors
    if (err.status === 401) {
      // Unauthorized - redirect to login
      router.push("/auth/login");
    } else if (err.status === 403) {
      // Forbidden - show error message
      setError("You don't have permission to access this resource");
    }
  }
}
```

## Key Points

1. **Client-Side**: Use `api.*` methods in Client Components - they automatically get the token from Supabase
2. **Server-Side**: Use `serverApiRequest()` in Server Components/Actions - you must pass the token explicitly
3. **Authentication**: Prefer using Supabase directly for auth flows (signup/login/logout)
4. **Protected Routes**: The backend verifies the token on every request - no trust in client state
5. **Error Handling**: Always catch `ApiError` and handle 401 (redirect to login) and 403 (show error) appropriately
