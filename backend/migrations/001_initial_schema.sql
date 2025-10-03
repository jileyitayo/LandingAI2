-- =====================================================
-- SiteSmith Database Schema - Initial Migration
-- Version: 1.0
-- Created: 2025-10-03
-- Description: Core database schema for SiteSmith AI Website Builder
-- =====================================================

-- =====================================================
-- SECTION 1: EXTENSIONS
-- Enable required PostgreSQL extensions
-- =====================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for fuzzy text search (useful for search features)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- END SECTION 1: EXTENSIONS
-- =====================================================


-- =====================================================
-- SECTION 2: USERS TABLE
-- Extends Supabase auth.users with application-specific data
-- =====================================================

CREATE TABLE IF NOT EXISTS public.users (
    -- Primary identification
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    
    -- Profile information
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    
    -- Subscription management
    subscription_tier TEXT NOT NULL DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro')),
    payment_customer_id TEXT, -- Stripe customer ID
    
    -- Rate limiting and usage tracking
    generation_count INTEGER NOT NULL DEFAULT 0, -- Total generations ever
    current_period_generations INTEGER NOT NULL DEFAULT 0, -- Resets monthly
    current_period_start DATE NOT NULL DEFAULT CURRENT_DATE, -- For rate limiting
    
    -- User state
    onboarding_completed BOOLEAN NOT NULL DEFAULT false,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON public.users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_payment_customer_id ON public.users(payment_customer_id) WHERE payment_customer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at DESC);

-- Add comment to users table
COMMENT ON TABLE public.users IS 'User profiles and subscription data extending Supabase auth.users';

-- =====================================================
-- END SECTION 2: USERS TABLE
-- =====================================================


-- =====================================================
-- SECTION 3: TEMPLATES TABLE
-- Stores website templates (system and user-generated)
-- =====================================================

CREATE TABLE IF NOT EXISTS public.templates (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL, -- NULL for system templates
    
    -- Basic information
    name TEXT NOT NULL,
    description TEXT,
    
    -- Visual preview
    preview_image TEXT, -- URL to preview image
    preview_html TEXT, -- Generated preview for thumbnail
    
    -- Categorization
    category TEXT CHECK (category IN ('business', 'portfolio', 'restaurant', 'services', 'custom')),
    tags TEXT[], -- ['african', 'modern', 'minimal', etc.]
    
    -- Template content
    base_html TEXT, -- Base HTML structure
    base_css TEXT, -- Global CSS
    base_js TEXT, -- Optional JavaScript
    
    -- Template configuration
    generation_prompt TEXT, -- Original prompt used to generate template
    style_config JSONB, -- {colorScheme: {primary, secondary, accent}, typography: {headingFont, bodyFont}, spacing: 'comfortable' | 'compact' | 'spacious'}
    sections_config JSONB NOT NULL, -- Component-based structure: {sections: [{id, type, order, variation, html, css, content_bindings, config}]}
    content_schema JSONB, -- Defines required fields: {required_fields: {business_name: 'string', services: 'array', etc.}}
    
    -- Template status
    is_system_template BOOLEAN NOT NULL DEFAULT false, -- True for built-in templates
    is_active BOOLEAN NOT NULL DEFAULT true, -- Can be disabled without deleting
    is_public BOOLEAN NOT NULL DEFAULT false, -- For future template marketplace
    
    -- Generation tracking
    generation_status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (generation_status IN ('generating', 'completed', 'failed')),
    generation_error TEXT,
    
    -- Analytics
    use_count INTEGER NOT NULL DEFAULT 0, -- Track popularity
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for templates table
CREATE INDEX IF NOT EXISTS idx_templates_user_id ON public.templates(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_templates_category ON public.templates(category) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_templates_is_system ON public.templates(is_system_template) WHERE is_system_template = true;
CREATE INDEX IF NOT EXISTS idx_templates_is_public ON public.templates(is_public) WHERE is_public = true;
CREATE INDEX IF NOT EXISTS idx_templates_is_active ON public.templates(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_templates_tags ON public.templates USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_templates_use_count ON public.templates(use_count DESC);
CREATE INDEX IF NOT EXISTS idx_templates_created_at ON public.templates(created_at DESC);

-- Add comment to templates table
COMMENT ON TABLE public.templates IS 'Website templates for AI generation - includes system templates and user-created templates';

-- =====================================================
-- END SECTION 3: TEMPLATES TABLE
-- =====================================================


-- =====================================================
-- SECTION 4: PROJECTS TABLE
-- Stores user website projects
-- =====================================================

CREATE TABLE IF NOT EXISTS public.projects (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Project information
    name TEXT NOT NULL,
    description TEXT,
    prompt TEXT, -- Original user prompt
    template_id TEXT, -- Reference to template used (can be UUID or string)
    
    -- Website content
    html_content TEXT,
    css_content TEXT,
    js_content TEXT,
    
    -- Deployment information
    published BOOLEAN NOT NULL DEFAULT false,
    subdomain TEXT UNIQUE, -- Unique subdomain (e.g., 'mysite' for mysite.sitesmith.app)
    deployment_url TEXT, -- Full deployment URL
    deployment_id TEXT, -- Vercel deployment ID
    
    -- Customization
    theme_settings JSONB, -- {primaryColor, secondaryColor, fontFamily}
    whatsapp_number VARCHAR(20), -- African market feature - Click-to-chat WhatsApp
    favicon_url TEXT,
    
    -- Generation tracking
    generation_status VARCHAR(20) NOT NULL DEFAULT 'idle' CHECK (generation_status IN ('idle', 'generating', 'completed', 'failed')),
    generation_error TEXT,
    last_generated_at TIMESTAMPTZ,
    
    -- Deployment tracking
    last_deployed_at TIMESTAMPTZ,
    
    -- Soft delete
    deleted_at TIMESTAMPTZ, -- NULL means not deleted
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for projects table
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_subdomain ON public.projects(subdomain) WHERE subdomain IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_projects_published ON public.projects(published) WHERE published = true;
CREATE INDEX IF NOT EXISTS idx_projects_template_id ON public.projects(template_id) WHERE template_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_projects_deleted_at ON public.projects(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON public.projects(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_generation_status ON public.projects(generation_status);

-- Add comment to projects table
COMMENT ON TABLE public.projects IS 'User website projects with content, deployment info, and generation tracking';

-- =====================================================
-- END SECTION 4: PROJECTS TABLE
-- =====================================================


-- =====================================================
-- SECTION 5: FUNCTIONS AND TRIGGERS
-- Automatic timestamp updates and utility functions
-- =====================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger for templates table
CREATE TRIGGER update_templates_updated_at
    BEFORE UPDATE ON public.templates
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger for projects table
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Function to create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, email_verified)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.email_confirmed_at IS NOT NULL
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create user profile when auth user is created
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- =====================================================
-- END SECTION 5: FUNCTIONS AND TRIGGERS
-- =====================================================


-- =====================================================
-- SECTION 6: ROW LEVEL SECURITY (RLS) POLICIES
-- Security policies for all tables
-- =====================================================

-- =====================================
-- 6.1: Users Table RLS Policies
-- =====================================

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own profile
CREATE POLICY "Users can view own profile"
ON public.users FOR SELECT
USING (auth.uid() = id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
ON public.users FOR UPDATE
USING (auth.uid() = id);

-- Policy: Users can insert their own profile (handled by trigger, but allows manual inserts)
CREATE POLICY "Users can insert own profile"
ON public.users FOR INSERT
WITH CHECK (auth.uid() = id);

-- =====================================
-- 6.2: Templates Table RLS Policies
-- =====================================

ALTER TABLE public.templates ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can view system templates
CREATE POLICY "System templates are viewable by everyone"
ON public.templates FOR SELECT
USING (is_system_template = true AND is_active = true);

-- Policy: Users can view their own templates
CREATE POLICY "Users can view own templates"
ON public.templates FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Public templates are viewable by everyone (for future marketplace)
CREATE POLICY "Public templates are viewable by everyone"
ON public.templates FOR SELECT
USING (is_public = true AND is_active = true);

-- Policy: Users can insert their own templates
CREATE POLICY "Users can insert own templates"
ON public.templates FOR INSERT
WITH CHECK (auth.uid() = user_id AND is_system_template = false);

-- Policy: Users can update their own templates
CREATE POLICY "Users can update own templates"
ON public.templates FOR UPDATE
USING (auth.uid() = user_id AND is_system_template = false);

-- Policy: Users can delete their own templates
CREATE POLICY "Users can delete own templates"
ON public.templates FOR DELETE
USING (auth.uid() = user_id AND is_system_template = false);

-- =====================================
-- 6.3: Projects Table RLS Policies
-- =====================================

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own projects (including soft-deleted ones)
CREATE POLICY "Users can view own projects"
ON public.projects FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can insert their own projects
CREATE POLICY "Users can insert own projects"
ON public.projects FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own projects
CREATE POLICY "Users can update own projects"
ON public.projects FOR UPDATE
USING (auth.uid() = user_id);

-- Policy: Users can delete their own projects
CREATE POLICY "Users can delete own projects"
ON public.projects FOR DELETE
USING (auth.uid() = user_id);

-- Policy: Published projects are viewable by everyone (for public preview)
CREATE POLICY "Published projects are publicly viewable"
ON public.projects FOR SELECT
USING (published = true AND deleted_at IS NULL);

-- =====================================================
-- END SECTION 6: ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================


-- =====================================================
-- SECTION 7: SEED DATA
-- Initial system templates and sample data
-- =====================================================

-- Insert default system templates will be added in a separate migration
-- This keeps the schema migration clean and allows easy template updates

-- =====================================================
-- END SECTION 7: SEED DATA
-- =====================================================


-- =====================================================
-- SECTION 8: GRANTS AND PERMISSIONS
-- Ensure proper permissions for application access
-- =====================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.users TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.projects TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.templates TO authenticated;

-- Allow anon to view public templates and published projects
GRANT SELECT ON public.templates TO anon;
GRANT SELECT ON public.projects TO anon;

-- =====================================================
-- END SECTION 8: GRANTS AND PERMISSIONS
-- =====================================================


-- =====================================================
-- MIGRATION COMPLETE
-- Schema Version: 1.0
-- Tables Created: users, templates, projects
-- Total Policies: 14
-- =====================================================

