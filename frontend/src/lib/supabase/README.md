# Supabase Integration Guide

This directory contains the Supabase client configuration for the SiteSmith application.

## Setup

### Environment Variables

Create a `.env.local` file in the frontend root with the following variables:

```env
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url-here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key-here
```

You can find these values in your Supabase project settings under **API**.

## Usage

### Client Components (Browser)

Use the client-side Supabase client in React Client Components:

```typescript
'use client'

import { createClient } from '@/lib/supabase/client'
import { useEffect, useState } from 'react'

export default function MyComponent() {
  const [user, setUser] = useState(null)
  const supabase = createClient()

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
    }
    getUser()
  }, [])

  return <div>User: {user?.email}</div>
}
```

### Server Components

Use the server-side Supabase client in React Server Components:

```typescript
import { createClient } from '@/lib/supabase/server'

export default async function MyServerComponent() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  return <div>User: {user?.email}</div>
}
```

### Server Actions

Use the server-side client in Server Actions:

```typescript
"use server";

import { createClient } from "@/lib/supabase/server";

export async function myServerAction() {
  const supabase = await createClient();

  const { data, error } = await supabase.from("projects").select("*");

  if (error) throw error;
  return data;
}
```

### Route Handlers (API Routes)

Use the server-side client in Route Handlers:

```typescript
import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function GET() {
  const supabase = await createClient();

  const { data, error } = await supabase.from("projects").select("*");

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}
```

## TypeScript Types

TypeScript types for database tables are available in `/src/types/database.types.ts`:

```typescript
import type { User, Project, Template } from "@/types/database.types";

// Use these types throughout your application for type safety
const user: User = {
  id: "uuid",
  email: "user@example.com",
  // ... other fields
};
```

## Database Schema

The application uses the following tables:

- **users**: User profile information and subscription data
- **projects**: Website projects with HTML/CSS/JS content
- **templates**: Base templates for website generation

See the PRD for detailed schema information.

## Security

- Always use Row Level Security (RLS) policies on all tables
- The anon key is safe to use in the browser (it's rate-limited and respects RLS)
- Never expose the service role key in frontend code
- All database operations respect RLS policies based on the authenticated user

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Auth with Next.js](https://supabase.com/docs/guides/auth/auth-helpers/nextjs)
- [Supabase SSR Package](https://supabase.com/docs/guides/auth/server-side/nextjs)
