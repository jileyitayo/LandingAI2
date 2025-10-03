# Database Migrations

This directory contains SQL migration files for the SiteSmith database schema.

## How to Apply Migrations

### Option 1: Supabase Dashboard (Recommended for MVP)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy the contents of `001_initial_schema.sql`
5. Paste into the SQL editor
6. Click **Run** to execute the migration

### Option 2: Supabase CLI (For Production)

```bash
# Login to Supabase
supabase login

# Link your project
supabase link --project-ref your-project-ref

# Apply migration
supabase db push
```

### Option 3: Direct SQL Execution

```bash
# Using psql
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres" \
  -f migrations/001_initial_schema.sql
```

## Migration Files

### 001_initial_schema.sql

**Version:** 1.0  
**Status:** ✅ Ready to Apply  
**Description:** Initial database schema including:

- **users table** - User profiles with subscription and rate limiting
- **templates table** - Website templates (system and user-generated)
- **projects table** - User website projects
- **RLS Policies** - 14 security policies
- **Triggers** - Auto-update timestamps and user profile creation
- **Indexes** - Performance optimization

## Database Schema Overview

### Users Table
Extends Supabase `auth.users` with application-specific data.

**Key Features:**
- User profile (first_name, last_name, avatar)
- Subscription management (free/pro tiers)
- Rate limiting (generation counts, period tracking)
- Onboarding state
- Stripe integration (payment_customer_id)

### Templates Table
Stores website templates for AI generation.

**Key Features:**
- System templates (built-in, read-only)
- User-generated templates (custom)
- Public templates (future marketplace)
- Component-based structure (sections_config)
- Style configuration (colors, fonts, spacing)
- Usage analytics (use_count)

### Projects Table
User website projects with full content.

**Key Features:**
- Website content (HTML, CSS, JS)
- Deployment tracking (Vercel integration)
- Generation status tracking
- WhatsApp integration (African market feature)
- Theme customization
- Soft delete support

## Row Level Security (RLS)

All tables have RLS enabled with appropriate policies:

### Users
- Users can view/update their own profile
- Auto-created on signup via trigger

### Templates
- System templates visible to all
- Public templates visible to all
- Users can CRUD their own templates
- System templates are read-only

### Projects
- Users can CRUD their own projects
- Published projects are publicly viewable
- Soft-deleted projects remain accessible to owner

## Indexes

Performance indexes are created for:
- Foreign keys (user_id references)
- Lookup fields (email, subdomain, payment_customer_id)
- Filter fields (subscription_tier, published, is_active)
- Sort fields (created_at, use_count)
- Array fields (tags using GIN index)

## Triggers

### Auto-Update Timestamps
All tables have triggers that automatically update `updated_at` on modifications.

### User Profile Creation
New users in `auth.users` automatically get a profile in `public.users`.

## Seed Data

System templates and sample data will be added in a separate migration (`002_seed_templates.sql`) to keep schema migrations clean.

## Rollback

To rollback this migration, run:

```sql
-- Drop tables in reverse order (respects foreign keys)
DROP TABLE IF EXISTS public.projects CASCADE;
DROP TABLE IF EXISTS public.templates CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- Drop triggers
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS update_projects_updated_at ON public.projects;
DROP TRIGGER IF EXISTS update_templates_updated_at ON public.templates;
DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;

-- Drop functions
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS public.update_updated_at_column();
```

## Verification

After applying the migration, verify:

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'projects', 'templates');

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Check policies exist
SELECT tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public';

-- Check indexes
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;
```

## Next Steps

After applying this migration:

1. ✅ Update frontend `.env.local` with Supabase credentials
2. ✅ Verify TypeScript types match schema
3. ⏭️ Apply `002_seed_templates.sql` (coming next)
4. ⏭️ Test authentication flow
5. ⏭️ Test RLS policies

## Troubleshooting

### Error: "extension uuid-ossp does not exist"
The extension is created in the migration. If you see this error, ensure you have proper permissions.

### Error: "relation auth.users does not exist"
This shouldn't happen in Supabase. Ensure you're running in a Supabase project, not a plain PostgreSQL database.

### Error: "permission denied for schema public"
Ensure you're connected as the database owner or have proper grants.

## Support

For issues or questions:
- Check [Supabase Documentation](https://supabase.com/docs)
- Review the [PRD](../../prd.md) for schema specifications
- Check TypeScript types in `frontend/src/types/database.types.ts`

