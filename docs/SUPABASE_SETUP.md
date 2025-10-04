# Supabase Setup Guide for SiteSmith

This guide walks you through setting up Supabase for the SiteSmith project.

## Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in
3. Click **New Project**
4. Fill in project details:
   - **Name:** SiteSmith (or your preferred name)
   - **Database Password:** Create a strong password (save this!)
   - **Region:** Choose closest to your users (e.g., `eu-west-1` for Europe, `us-east-1` for US)
   - **Pricing Plan:** Free tier is fine for development
5. Click **Create new project**
6. Wait 2-3 minutes for project to initialize

## Step 2: Get API Credentials

1. In your Supabase project dashboard, go to **Settings** (gear icon)
2. Click **API** in the sidebar
3. Copy the following values:
   - **Project URL** - (looks like `https://xxxxx.supabase.co`)
   - **anon public** key - (long JWT token starting with `eyJ...`)

## Step 3: Update Environment Variables

### Frontend (.env.local)

Update `/frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=your-stripe-key-here
```

### Backend (.env)

Update `/backend/.env`:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
OPENAI_API_KEY=your-openai-key-here
STRIPE_SECRET_KEY=your-stripe-secret-key-here
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret-here
VERCEL_API_TOKEN=your-vercel-token-here
VERCEL_TEAM_ID=your-vercel-team-id-here
```

**Note:** The **service_role** key (for backend) is found in the same API settings page under "service_role" - this has admin access, so keep it secret!

## Step 4: Apply Database Migration

### Method A: Using Supabase Dashboard (Recommended for First Time)

1. In your Supabase dashboard, click **SQL Editor** (icon in sidebar)
2. Click **New Query**
3. Open `/backend/migrations/001_initial_schema.sql`
4. Copy ALL the contents
5. Paste into the SQL Editor
6. Click **Run** (or press Cmd/Ctrl + Enter)
7. You should see "Success. No rows returned" - this is good!

### Method B: Using Supabase CLI (For Advanced Users)

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Apply migration
cd backend
supabase db push
```

## Step 5: Verify Migration

1. In SQL Editor, run the verification script:
   ```sql
   -- Paste contents of migrations/verify_migration.sql
   ```
2. Check that all sections show ✓ PASS or ✓ EXISTS
3. Expected results:
   - ✅ 3 tables created (users, projects, templates)
   - ✅ 14+ RLS policies
   - ✅ 15+ indexes
   - ✅ 4 triggers

### Quick Verification Query

```sql
-- Check tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Should show: users, projects, templates
```

## Step 6: Enable Email Authentication

1. Go to **Authentication** → **Providers** in Supabase dashboard
2. **Email** provider should be enabled by default
3. Configure email settings:
   - **Enable email confirmations:** Toggle ON (for production)
   - **Confirm email:** Can leave OFF for development
4. (Optional) Configure custom email templates under **Email Templates**

## Step 7: Test Connection from Frontend

Create a test page in your Next.js app:

```typescript
// app/test/page.tsx
import { createClient } from '@/lib/supabase/server'

export default async function TestPage() {
  const supabase = await createClient()
  
  // Try to fetch templates (should be empty but should not error)
  const { data, error } = await supabase
    .from('templates')
    .select('*')
    .limit(5)
  
  if (error) {
    return <div>❌ Error: {error.message}</div>
  }
  
  return (
    <div>
      <h1>✅ Supabase Connected!</h1>
      <p>Templates count: {data?.length || 0}</p>
    </div>
  )
}
```

Visit `http://localhost:3000/test` and you should see "✅ Supabase Connected!"

## Step 8: Test Authentication Flow

Try signing up a test user:

### Option A: Using Supabase Dashboard

1. Go to **Authentication** → **Users**
2. Click **Add User** → **Create new user**
3. Enter email and password
4. Click **Create user**
5. Check that user appears in both:
   - `auth.users` table (Authentication section)
   - `public.users` table (Table Editor section)

### Option B: Using Frontend (Once auth pages are built)

After you build the auth UI in Phase 2, test:
1. Sign up with email/password
2. Check Supabase dashboard that user was created
3. Verify profile created in `public.users`

## Troubleshooting

### Error: "extension uuid-ossp does not exist"
**Solution:** Already handled in migration. If you see this, ensure you're running in Supabase, not plain PostgreSQL.

### Error: "permission denied for schema public"
**Solution:** You need to run the SQL as the database owner. In Supabase dashboard, you're automatically the owner.

### Error: "relation auth.users does not exist"
**Solution:** You're not in a Supabase database. Supabase provides auth.users automatically.

### Tables created but RLS not working
**Solution:** Run this to enable RLS:
```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
```

### Can't see public.users data in dashboard
**Solution:** By default, you're viewing as an anon user. Switch to viewing as "service_role" in Table Editor settings.

## Security Checklist

Before going to production:

- ✅ Enable email confirmations
- ✅ Set up custom email templates with your branding
- ✅ Verify RLS policies are working (test with anon vs authenticated users)
- ✅ Never commit `.env.local` or `.env` files
- ✅ Use service_role key only in backend, never in frontend
- ✅ Set up Supabase Auth redirect URLs in production

## Next Steps

After Supabase is set up:

1. ✅ **Milestone 1.2 Complete!**
2. ⏭️ Move to **Milestone 2.1:** Build authentication UI
3. ⏭️ Move to **Milestone 2.2:** Backend auth integration
4. ⏭️ Create seed data migration (002_seed_templates.sql)

## Useful Supabase Dashboard Links

- **Table Editor:** View and edit data directly
- **SQL Editor:** Run queries and migrations
- **Authentication:** Manage users and auth settings
- **API Docs:** Auto-generated API documentation
- **Logs:** View real-time logs (auth, database, etc.)
- **Database → Replication:** For backups and replication

## Support Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Discord](https://discord.supabase.com)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Next.js Integration Guide](https://supabase.com/docs/guides/auth/server-side/nextjs)

---

**Last Updated:** October 3, 2025  
**Schema Version:** 1.0

