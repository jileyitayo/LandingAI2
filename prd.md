# Product Requirements Document (PRD)
# AI Website Builder - "SiteSmith"

## 1. Overview

### 1.1 Product Vision
SiteSmith is a no-code AI website builder that enables users to create professional websites through natural language prompts. Similar to Lovable, but focused on simplicity and speed for non-technical users who want a website without any coding knowledge. It is also aimed at the SME businesses in Africa to help build their business website for a low cost.

### 1.2 Target Users
- Small business owners
- Freelancers and creators
- Non-technical entrepreneurs
- Anyone needing a quick web presence without coding

### 1.3 Core Value Proposition
**Primary CVP (The "What"):** "SiteSmith empowers African entrepreneurs to launch a professional, mobile-friendly website in minutes using simple English. No code, no high costs, no complications."

**Value Prop 1:** 
Affordability & Speed

**Statement:** 
"Get your business online today, not next month. Stop waiting for expensive developers. Build your own website for less than the cost of a loaf of bread and start attracting customers now."

Features to back this up: Low-cost subscription tier, AI generation in under a minute.

**Value Prop 2:** 
Mobile-First & Data-Friendly

**Statement:** 
"Reach every customer, on any device. SiteSmith automatically creates lightning-fast websites that look perfect on mobile phones and use less data, so you never lose a visitor due to a slow connection."

Features to back this up: Performant Next.js frontend, image optimization, lightweight templates.


**Value Prop 3:** 
Built for Commerce in Africa

**Statement:** 
"Connect with your customers where they are. Add a 'Chat on WhatsApp' button with one click and get ready for a future with integrated local payment options. We built SiteSmith for the way you do business."

Features to back this up: Easy WhatsApp integration (MVP), roadmap for Paystack/Flutterwave (Post-MVP).


**Value Prop 4:**
Simplicity & Empowerment

**Statement:** 
"If you can describe your business, you can build your website. SiteSmith's AI handles all the technical details, so you can focus on what you do best: running your business."

Features to back this up: Natural language prompts, no-code editor, one-click publishing.


### 1.4 Pain point
- Hiring a developer or agency is too expensive. Subscription services like Wix or Squarespace can also be costly when priced in USD.
- Technical Barrier: Lack of coding skills or understanding of web hosting, domains, and SSL certificates.
- Customers are often wary of online businesses. A professional website needs to build trust quickly.
- Email is not the primary communication tool. Business happens on WhatsApp.
- Receiving online payments can be complex. Credit card penetration is low; mobile money and local payment systems are dominant.

### 1.5 Key Feature: AI Template Generation (v1.1)
SiteSmith now supports **AI-powered template generation**, allowing users to create custom, reusable website templates based on their specific design preferences and business needs. This feature provides:

**What it does:**
- Users can describe their desired website design (e.g., "modern business layout with blue tones and professional feel")
- AI generates a complete, reusable template with flexible HTML/CSS structure
- Templates can be saved, edited, and reused across multiple projects
- Users can build a personal library of custom templates alongside system-provided templates

**Why it matters:**
- **Consistency:** Businesses with multiple websites or pages can maintain brand consistency
- **Efficiency:** Create one template, use it multiple times with different content
- **Flexibility:** More control than pre-built templates, easier than coding from scratch
- **Cost savings:** Reduce dependency on expensive template purchases or designer fees
- **Customization:** Templates tailored to African business aesthetics and needs

**User Flow:**
1. User enters a template generation prompt (e.g., "Create a restaurant template with warm colors")
2. AI generates template structure with CSS variables for easy theming
3. User previews the template
4. User can save, edit, or regenerate
5. Template becomes available for use when creating new websites

This feature bridges the gap between rigid pre-built templates and complex custom coding, giving users more creative control while maintaining simplicity.

---

## 2. Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js + Tailwind CSS |
| Backend | FastAPI |
| Database | Supabase (PostgreSQL) |
| Authentication | Supabase Auth |
| Payments | Stripe |
| Email | Supabase |
| Hosting | Vercel |
| Domain Management | Vercel |
| Monitoring | Vercel Analytics |
| Logging | Vercel |
| Error Tracking | Vercel |

---

## 3. MVP Scope

### 3.1 Core Functionality (Must-Have)
1. **User Authentication** - Sign up, login, logout
2. **AI Website Generation** - Generate website from text prompt
3. **AI Template Generation** - Generate custom templates from user prompts
4. **Website Preview** - Live preview of generated website
5. **Basic Editing** - Simple text and image editing
6. **Website Publishing** - Deploy to a subdomain
7. **Template Selection** - 3-5 basic templates/styles + user-generated templates
8. **WhatsApp Click-to-Chat** - Users should be able to chat with your business

### 3.2 Out of Scope for MVP
- Custom domain support (post-MVP)
- Advanced editing/drag-and-drop
- Multi-page websites (MVP: single-page only)
- Team collaboration
- Analytics dashboard
- SEO tools
- A/B testing

---

## 4. Features Breakdown

### Feature 1: User Management & Authentication
**Description:** Complete user authentication flow with email verification and profile management.

**User Stories:**
- As a user, I want to sign up with email/password
- As a user, I want to log in and out securely
- As a user, I want to reset my password if forgotten
- As a user, I want to view and edit my profile

**Technical Requirements:**
- Supabase Auth integration
- JWT-based authentication
- Protected routes in Next.js
- Session management

---

### Feature 2: AI Website Generation Engine
**Description:** Core AI functionality that converts user prompts into complete website code, with the ability to generate custom templates or use existing ones.

**User Stories:**
- As a user, I want to describe my website needs in plain English
- As a user, I want to see my website generated within 30 seconds
- As a user, I want to regenerate with refined prompts
- As a user, I want to choose a style/template before generation
- As a user, I want to generate a custom template based on my business type and design preferences
- As a user, I want to save generated templates for reuse across projects

**Technical Requirements:**
- Integration with OpenAI API (GPT-4) or similar
- Prompt engineering for website generation
- Prompt engineering for template generation (layout, color schemes, typography)
- Template system for consistent outputs (system + user-generated)
- Real-time generation status updates
- Template validation and storage
- Template preview generation

---

### Feature 3: Website Preview & Editor
**Description:** Live preview and basic editing capabilities for generated websites.

**User Stories:**
- As a user, I want to see a live preview of my website
- As a user, I want to edit text content inline
- As a user, I want to change images
- As a user, I want to adjust colors/theme

**Technical Requirements:**
- iframe-based preview system
- Simple WYSIWYG text editor
- Image upload and management
- Color picker integration

---

### Feature 4: Website Storage & Management
**Description:** Database storage for generated websites and user projects.

**User Stories:**
- As a user, I want to save multiple website projects
- As a user, I want to view all my projects in a dashboard
- As a user, I want to delete old projects
- As a user, I want to duplicate projects

**Technical Requirements:**
- PostgreSQL schema via Supabase
- CRUD operations for projects
- File storage for assets (Supabase Storage)
- Project versioning (basic)

---

### Feature 5: Website Publishing & Deployment
**Description:** One-click deployment to a live subdomain.

**User Stories:**
- As a user, I want to publish my website with one click
- As a user, I want a unique subdomain (e.g., mysite.SiteSmith.app)
- As a user, I want to unpublish my website
- As a user, I want to see my published URL

**Technical Requirements:**
- Vercel API integration for deployment
- Subdomain management
- Deployment status tracking
- Rollback capability

---

### Feature 6: Template Management & Generation
**Description:** System for managing both system-provided and user-generated templates, with AI-powered template creation.

**User Stories:**
- As a user, I want to browse available templates (system and my custom ones)
- As a user, I want to generate a custom template by describing my design preferences
- As a user, I want to preview templates before using them
- As a user, I want to save generated templates for future use
- As a user, I want to edit and customize my saved templates
- As a user, I want to delete templates I no longer need

**Technical Requirements:**
- Template CRUD operations (Create, Read, Update, Delete)
- AI template generation service with GPT-4
- Template preview rendering system
- Template categorization and tagging
- Template ownership and access control (RLS)
- Template validation (ensure valid HTML/CSS structure)

---

### Feature 7: Subscription & Payments
**Description:** Stripe integration for subscription management.

**User Stories:**
- As a user, I want a free tier (1 website)
- As a user, I want to upgrade to paid plan (unlimited websites)
- As a user, I want to manage my subscription
- As a user, I want to cancel my subscription

**Technical Requirements:**
- Stripe Checkout integration
- Webhook handling for payment events
- Subscription tier enforcement
- Billing portal access

---

## 5. Milestones & Implementation Plan

### **Phase 1: Foundation & Setup**

#### Milestone 1.1: Project Setup & Configuration
**Goal:** Initialize both frontend and backend projects with proper structure.

**LLM Prompt:**
```
Create a new Next.js 14 frontend project  with TypeScript and Tailwind CSS. Set up the following:
1. App router structure with src/ directory
2. Configure Tailwind with custom theme colors (primary: #6366f1, secondary: #8b5cf6)
3. Set up ESLint and Prettier
4. Create a basic folder structure: components/, app/, lib/, types/, hooks/
5. Add .env.local with placeholder environment variables for Supabase and Stripe
6. Create a README.md with setup instructions
7. Add docker support
```

**LLM Prompt:**
```
Create a FastAPI backend project with the following structure:
1. Use Python 3.12+ with virtual environment
2. Set up FastAPI with CORS middleware
3. Create folder structure: app/, app/routers/, app/models/, app/services/, app/utils/
4. Add requirements.txt with: fastapi, uvicorn, supabase, stripe, openai, python-dotenv, pydantic
5. Create main.py with basic health check endpoint
6. Set up .env with placeholder variables
7. Add Docker support
```

**LLM Prompt:**
```
Initialize a git repo for this project
```

**Acceptance Criteria:**
- [ ] Both projects run successfully
- [ ] Environment variables properly configured
- [ ] Git repository initialized with .gitignore
- [ ] Git repository created 
- [ ] Basic documentation in README

---

#### Milestone 1.2: Supabase Setup & Configuration
**Goal:** Set up Supabase project with database schema and authentication.

**LLM Prompt:**
```
Set up Supabase integration for the Next.js frontend:
1. Install @supabase/supabase-js and @supabase/auth-helpers-nextjs
2. Create lib/supabase/client.ts for client-side Supabase client
3. Create lib/supabase/server.ts for server-side Supabase client
4. Configure environment variables (NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY)
5. Add TypeScript types for Supabase tables
```

**LLM Prompt:**
```
Create the following database schema in Supabase (provide SQL):

1. users table (extends Supabase auth.users):
   - id (uuid, primary key, references auth.users)
   - email (text, not null, unique)
   - full_name (text, nullable)
   - avatar_url (text, nullable)
   - subscription_tier (text, default: 'free') -- 'free' | 'pro'
   - payment_customer_id (text) # for stripe -  Stripe customer ID
   - generation_count (integer, default: 0) -- Total generations ever
   - current_period_generations (integer, default: 0) -- Resets monthly
   - current_period_start (date, default: CURRENT_DATE) -- For rate limiting
   - onboarding_completed (boolean, default: false)
   - email_verified (boolean, default: false)
   - last_login_at (timestamp, nullable)
   - created_at (timestamp, default: NOW())
   - updated_at (timestamp, default: NOW())


2. projects table:
   - id (uuid, primary key, default: uuid_generate_v4())
   - user_id (uuid, foreign key to users.id, not null)
   - name (text, not null)
   - description (text, nullable)
   - prompt (text, nullable)
   - template_id (text)
   - html_content (text)
   - css_content (text)
   - js_content (text)
   - published (boolean, default: false)
   - subdomain (text, unique)
   - deployment_url (text)
   - deployment_id (text, nullable) -- Vercel deployment ID
   - theme_settings (jsonb, nullable) -- {primaryColor, secondaryColor, fontFamily}
   - whatsapp_number (varchar(20), nullable) -- African market feature
   - favicon_url (text, nullable)
   - generation_status (varchar(20), default: 'idle') -- 'idle' | 'generating' | 'completed' | 'failed'
   - generation_error (text, nullable)
   - last_generated_at (timestamp, nullable)
   - last_deployed_at (timestamp, nullable)
   - deleted_at (timestamp, nullable) -- Soft delete
   - created_at (timestamp)
   - updated_at (timestamp)


3. templates table:
   - id (uuid, primary key, default: uuid_generate_v4())
   - user_id (uuid, foreign key to users.id, nullable) -- NULL for system templates, user ID for user-generated
   - name (text, not null)
   - description (text, nullable)
   - preview_image (text, nullable) -- URL to preview image
   - preview_html (text, nullable) -- Generated preview for thumbnail
   - category (text, nullable) -- 'business' | 'portfolio' | 'restaurant' | 'services' | 'custom'
   - base_html (text, nullable) -- Stores the generated html (Potentially could be generated and during deployment)
   - base_css (text, nullable) -- Global CSS, component styles in sections_config
   - base_js (text, nullable) -- Optional JavaScript for template
   - is_system_template (boolean, default: false) -- True for built-in templates
   - is_active (boolean, default: true) -- Can be disabled without deleting
   - is_public (boolean, default: false) -- For future template marketplace
   - generation_prompt (text, nullable) -- Original prompt used to generate template
   - style_config (jsonb, nullable) -- {colorScheme: {primary, secondary, accent}, typography: {headingFont, bodyFont}, spacing: 'comfortable' | 'compact' | 'spacious'}
   - sections_config (jsonb, not null) -- Component-based structure: {sections: [{id, type, order, variation, html, css, content_bindings, config}]}
   - content_schema (jsonb, nullable) -- Defines required fields: {required_fields: {business_name: 'string', services: 'array', etc.}}
   - tags (text[], nullable) -- ['african', 'modern', 'minimal', etc.]
   - use_count (integer, default: 0) -- Track popularity
   - generation_status (varchar(20), default: 'completed') -- 'generating' | 'completed' | 'failed'
   - generation_error (text, nullable)
   - created_at (timestamp, default: NOW())
   - updated_at (timestamp, default: NOW())


Add Row Level Security (RLS) policies for all tables:

**RLS Policies for templates table:**
```sql
-- Enable RLS
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can view system templates
CREATE POLICY "System templates are viewable by everyone" 
ON templates FOR SELECT 
USING (is_system_template = true);

-- Policy: Users can view their own templates
CREATE POLICY "Users can view own templates" 
ON templates FOR SELECT 
USING (auth.uid() = user_id);

-- Policy: Users can insert their own templates
CREATE POLICY "Users can insert own templates" 
ON templates FOR INSERT 
WITH CHECK (auth.uid() = user_id AND is_system_template = false);

-- Policy: Users can update their own templates
CREATE POLICY "Users can update own templates" 
ON templates FOR UPDATE 
USING (auth.uid() = user_id AND is_system_template = false);

-- Policy: Users can delete their own templates
CREATE POLICY "Users can delete own templates" 
ON templates FOR DELETE 
USING (auth.uid() = user_id AND is_system_template = false);

-- Policy: Public templates are viewable by everyone (for future marketplace)
CREATE POLICY "Public templates are viewable by everyone" 
ON templates FOR SELECT 
USING (is_public = true);
```

**Indexes for performance:**
```sql
-- Index for user templates lookup
CREATE INDEX idx_templates_user_id ON templates(user_id) WHERE user_id IS NOT NULL;

-- Index for system templates lookup
CREATE INDEX idx_templates_system ON templates(is_system_template) WHERE is_system_template = true;

-- Index for category filtering
CREATE INDEX idx_templates_category ON templates(category);

-- Index for tag searching
CREATE INDEX idx_templates_tags ON templates USING GIN(tags);

-- Index for active templates
CREATE INDEX idx_templates_active ON templates(is_active) WHERE is_active = true;
```

**Component Library Structure:**

Templates use a component-based JSON structure for flexible, reusable sections:

```json
{
  "sections": [
    {
      "id": "hero-1",
      "type": "hero",
      "order": 1,
      "variation": "full-width-centered",
      "html": "<section class='hero'>...</section>",
      "css": ".hero { ... }",
      "config": {
        "background": {
          "type": "image",  // 'image' | 'color' | 'gradient' | 'video'
          "value": "{{background_image}}",  // URL binding or color value
          "overlay": true,  // Dark overlay for text readability
          "overlayOpacity": 0.4
        },
        "contentAlignment": "center",  // 'left' | 'center' | 'right'
        "minHeight": "100vh",
        "padding": "comfortable"
      },
      "content_bindings": {
        "headline": {
          "type": "text",
          "required": true,
          "placeholder": "Your Business Name"
        },
        "subheadline": {
          "type": "text",
          "required": false,
          "placeholder": "A compelling tagline"
        },
        "cta_text": {
          "type": "text",
          "required": true,
          "default": "Get Started"
        },
        "cta_url": {
          "type": "url",
          "required": false,
          "default": "#contact"
        },
        "hero_image": {
          "type": "image",
          "required": false,
          "placeholder": null
        },
        "hero_video": {
          "type": "video",
          "required": false,
          "placeholder": null
        },
        "background_image": {
          "type": "image",
          "required": false,
          "placeholder": null
        }
      }
    },
    {
      "id": "services-1",
      "type": "services",
      "order": 2,
      "variation": "three-column-grid",
      "html": "...",
      "css": "...",
      "config": {
        "columns": 3,
        "iconStyle": "outlined",
        "cardStyle": "elevated"
      },
      "content_bindings": {
        "section_title": {
          "type": "text",
          "required": true,
          "default": "Our Services"
        },
        "services": {
          "type": "array",
          "required": true,
          "itemSchema": {
            "title": "string",
            "description": "string",
            "icon": "string",
            "image": "url"
          }
        }
      }
    },
    {
      "id": "contact-1",
      "type": "contact",
      "order": 3,
      "variation": "split-form-info",
      "html": "...",
      "css": "...",
      "config": {
        "showMap": false,
        "showWhatsApp": true,
        "formFields": ["name", "email", "message"]
      },
      "content_bindings": {
        "business_phone": {"type": "phone", "required": false},
        "whatsapp_number": {"type": "phone", "required": false},
        "business_email": {"type": "email", "required": true},
        "business_address": {"type": "text", "required": false}
      }
    }
  ]
}
```

**Supported Component Types (MVP):**
- All sections should have a header and a footer
- `header` - Header sections with multiple variations (centered-logo, logo-left-right-aligned-menu)
- `hero` - Hero sections with multiple variations (centered, split, video background)
- `about` - About/story sections (two-column, centered, timeline)
- `services` - Service/feature grids (2-col, 3-col, 4-col, carousel)
- `portfolio` - Work/product showcase (grid, masonry, carousel)
- `testimonials` - Customer reviews (cards, carousel, wall)
- `cta` - Call-to-action sections (banner, centered, split)
- `contact` - Contact sections (form, info, map)
- `footer` - Footer sections (simple, columns, social)

**Hero Section Configuration Options:**
```json
{
  "background": {
    "type": "image | color | gradient | video",
    "value": "url or color value",
    "overlay": true,
    "overlayOpacity": 0.4,
    "parallax": false
  },
  "contentAlignment": "left | center | right",
  "verticalAlignment": "top | center | bottom",
  "minHeight": "50vh | 75vh | 100vh | auto",
  "textColor": "auto | light | dark",
  "showScrollIndicator": true
}
```

**Acceptance Criteria:**
- [ ] Supabase project created
- [ ] Database schema deployed
- [ ] RLS policies active for all tables
- [ ] Indexes created for performance
- [ ] Connection from both frontend and backend verified
- [ ] Template RLS policies tested (users can only access system + own templates)
- [ ] Component library structure documented and validated

---

### **Phase 2: Authentication**

#### Milestone 2.1: Frontend Authentication UI
**Goal:** Build complete authentication UI with all flows.

**LLM Prompt:**
```
Create authentication pages and components in Next.js:

1. app/auth/login/page.tsx - Login page with email/password
2. app/auth/signup/page.tsx - Sign up page with email/password
3. app/auth/forgot-password/page.tsx - Password reset request
4. app/auth/reset-password/page.tsx - Password reset form
5. components/AuthForm.tsx - Reusable form component
6. hooks/useAuth.ts - Custom hook for auth state

Requirements:
- Use Tailwind CSS for styling (modern, clean design)
- Form validation with react-hook-form and zod
- Loading states and error handling
- Redirect authenticated users from auth pages
- Email verification flow
```

**Acceptance Criteria:**
- [ ] All auth pages functional
- [ ] Form validation working
- [ ] Error messages displayed properly
- [ ] Responsive design

---

#### Milestone 2.2: Backend Authentication Integration
**Goal:** Set up FastAPI endpoints for authentication and user management.

**LLM Prompt:**
```
Create FastAPI authentication endpoints:

1. app/routers/auth.py with routes:
   - POST /auth/signup - Create new user
   - POST /auth/login - Login user
   - POST /auth/logout - Logout user
   - POST /auth/refresh - Refresh token
   - GET /auth/user - Get current user

2. app/utils/auth.py with helper functions:
   - verify_token() - Verify Supabase JWT
   - get_current_user() - FastAPI dependency for protected routes

3. Middleware for authentication on protected routes

Use Supabase client for all auth operations.
```

**Acceptance Criteria:**
- [ ] All auth endpoints working
- [ ] JWT verification functional
- [ ] Protected routes enforced
- [ ] Integration with frontend complete

---

#### Milestone 2.3: User Profile Management
**Goal:** Allow users to view and edit their profiles.

**LLM Prompt:**
```
Create user profile functionality:

Frontend (Next.js):
1. app/dashboard/profile/page.tsx - Profile page
2. components/ProfileForm.tsx - Edit profile form
3. Avatar upload with Supabase Storage

Backend (FastAPI):
1. GET /users/profile - Get current user profile
2. PATCH /users/profile - Update user profile
3. POST /users/avatar - Upload avatar

Include error handling and loading states.
```

**Acceptance Criteria:**
- [ ] Users can view their profile
- [ ] Users can update name and email
- [ ] Avatar upload working
- [ ] Changes persist in database

---

### **Phase 3: AI Website Generation**

#### Milestone 3.1: Prompt Interface & Template Selection
**Goal:** Build the UI for users to input prompts and select or generate templates.

**User Stories:**
- As a user, I want to easily input my website idea into a text box.
- As a user, I want to see a selection of professional templates to choose from before I generate my site.
- As a user, I want to generate a custom template based on my business description.
- As a small business owner in Africa, I want to see website templates relevant to my business (e.g., local artisan, tourism service), so that I can find a design that fits my needs and feel the product is made for me.

**LLM Prompt:**
```
Create the website generation interface:

1. app/dashboard/new/page.tsx - New project page with:
   - Large textarea for prompt input
   - Template selector (grid of 3-5 system templates with previews)
   - "Generate Custom Template" button/option
   - "Generate Website" button
   - Tab/toggle to switch between "Use Template" and "Generate Template" modes
   - Character count and helpful prompt examples

2. components/TemplateCard.tsx - Template preview card with:
   - Template thumbnail
   - Template name and description
   - Category badge
   - "Use Template" action
   - "System" or "Custom" indicator

3. components/PromptInput.tsx - Enhanced textarea with suggestions
4. Add sample templates to Supabase templates table

Design should be inspiring and easy to use. Include helpful prompt examples like:
- "A landing page for a yoga studio with calming colors"
- "A portfolio website for a photographer with gallery"
- "A restaurant website with menu and reservations"
- "A modern business template with blue tones and professional layout"
```

**Acceptance Criteria:**
- [ ] Prompt input functional
- [ ] Template selection working
- [ ] UI is intuitive and attractive
- [ ] Sample templates available
- [ ] At least two templates tailored for African SMEs are available and functional
- [ ] Option to generate custom template is visible and accessible
---

#### Milestone 3.2: Component Library Setup
**Goal:** Create the foundational component library with sample components for AI generation.

**User Stories:**
- As a developer, I want a library of pre-validated component samples
- As a user, I want consistent, professional-looking sections in my templates
- As a developer, I want components that are reusable and customizable

**LLM Prompt:**
```
Create the component library system:

Backend (FastAPI):
1. app/services/components_library.py with:
   - Define 5-7 core component types with variations
   - COMPONENT_SAMPLES dictionary with HTML/CSS samples
   - Component validation functions
   - Component rendering utilities
   
   Core components to create:
   - Header (2 variations: centered-logo, logo-left-right-aligned-menu)
   - Hero (3 variations: centered, split, full-width)
   - Services (3 variations: 2-col, 3-col, carousel)
   - About (2 variations: two-column, centered)
   - CTA (2 variations: banner, centered)
   - Contact (2 variations: form-only, split-info)
   - Testimonials (2 variations: cards, carousel)
   - Footer (2 variations: simple, columns)

2. Each component should include:
   - Multiple variations (e.g., hero-centered, hero-split)
   - HTML structure with content binding placeholders {{variable}}
   - CSS using CSS variables for theming
   - Config object defining customization options
   - Content bindings schema with types and validation

3. Hero component specifications:
   - Support background image, color, gradient, or video
   - Content alignment: left, center, right
   - Vertical alignment: top, center, bottom
   - Optional overlay for readability
   - Optional hero image/video as content
   - Responsive design
   - Min height options (50vh, 75vh, 100vh)

4. app/data/component_samples.json - Store component samples:
   ```json
   {
     "hero": {
       "centered": {
         "html": "...",
         "css": "...",
         "config": {...},
         "content_bindings": {...}
       }
     }
   }


Frontend (Next.js):
1. lib/components/types.ts - TypeScript types for component structure
2. lib/components/schema.ts - Validation schemas for components
3. components/ComponentPreview.tsx - Preview individual components

Documentation:
- Create docs/COMPONENT_LIBRARY.md documenting all components
- Include examples and usage patterns
```

**Acceptance Criteria:**
- [ ] 5-7 component types defined with 2-3 variations each
- [ ] Hero component supports all specified options (background types, alignment)
- [ ] All components use CSS variables for theming
- [ ] Content bindings properly typed and validated
- [ ] Components are mobile-responsive
- [ ] Component library documented
- [ ] TypeScript types created

---

#### Milestone 3.3: AI Template Generation Service
**Goal:** Implement AI-powered template generation using component library.

**User Stories:**
- As a user, I want to generate a custom template by describing my design preferences
- As a user, I want the AI to select appropriate sections for my business type
- As a user, I want templates that follow professional design patterns

**LLM Prompt:**
```
Create the AI template generation system:

Backend (FastAPI):
1. app/services/template_generator.py with:
   - generate_template(prompt: str, user_id: str, style_preferences: dict) -> dict
   - Few-shot learning using component samples from components_library
   - System prompt that instructs AI to:
     * Analyze business type from prompt
     * Select appropriate component types
     * Choose variations that fit the style
     * Generate sections_config JSON structure
     * Create content_schema defining required fields
     * Extract style_config (colors, fonts, spacing)
   
   - Integration with OpenAI API (gpt-4)
   - Structured output validation (ensure valid JSON)
   - Component-based generation (not raw HTML)
   - Generate preview HTML for thumbnail

2. System prompt template:
   
   You are a UI/UX expert generating website templates using a component library.
   
   AVAILABLE COMPONENTS:
   {component_samples}
   
   USER REQUEST: {user_prompt}
   
   INSTRUCTIONS:
   1. Analyze the business type and requirements
   2. Select 4-6 appropriate sections from the component library
   3. Choose variations that match the desired style
   4. Customize colors, fonts, and spacing
   5. Define content bindings for dynamic content
   6. Output structured JSON (not raw HTML)
   
   OUTPUT FORMAT:
   {
     "sections": [...],
     "style_config": {...},
     "content_schema": {...},
     "meta": {
       "category": "...",
       "tags": [...]
     }
   }
   

3. app/routers/templates.py with:
   - POST /templates/generate - Generate new template from prompt
   - GET /templates - List templates (system + user's templates)
   - GET /templates/{id} - Get specific template
   - PATCH /templates/{id} - Update user template
   - DELETE /templates/{id} - Delete user template
   - GET /templates/{id}/status - Check generation status

4. Template generation flow:
   - Validate user prompt
   - Check rate limits (max 3 generations/hour for free tier)
   - Call OpenAI with component samples as few-shot examples
   - Parse and validate JSON response
   - Validate component structure
   - Generate preview HTML
   - Store in templates table
   - Return template ID and status

5. app/services/template_validator.py:
   - validate_sections_config(sections_config: dict) -> bool
   - validate_content_schema(content_schema: dict) -> bool
   - Ensure all referenced components exist
   - Validate content binding types

Frontend (Next.js):
1. components/TemplateGenerationModal.tsx - Modal for template generation:
   - Template prompt input with examples
   - Style preferences selector
   - Business category dropdown
   - Progress indicator with stages
   - Preview of generated template
   - Save/edit/regenerate options

2. hooks/useTemplateGeneration.ts - Custom hook:
   - Handle generation API calls
   - Poll for status updates
   - Error handling with retry logic
   - Success/failure states

3. Prompt examples:
   - "Modern restaurant with warm colors, menu showcase, and online ordering"
   - "Professional consultancy with trust-building elements"
   - "Creative portfolio with large image galleries"
   - "Local artisan shop with product showcase and WhatsApp ordering"
```

**Acceptance Criteria:**
- [ ] AI generates component-based JSON structures (not raw HTML)
- [ ] Templates use components from the library
- [ ] Style config properly extracted and applied
- [ ] Content schema accurately defines required fields
- [ ] Validation ensures structural integrity
- [ ] Rate limiting enforced (3 templates/hour)
- [ ] Generation takes < 30 seconds
- [ ] Preview HTML generated for thumbnails
- [ ] Structured output validated before storage
---

#### Milestone 3.4: AI Website Content Generation Service
**Goal:** Implement content generation that fills template components with actual business content.

**User Stories:**
- As a user, I want to generate website content from a simple business description
- As a user, I want content that fits my selected template structure
- As a user, I want the content to be customized for my specific business

**LLM Prompt:**
```
Create the AI website content generation service in FastAPI:

1. app/services/content_generator.py with:
   - generate_content(prompt: str, template_id: str, user_id: str) -> dict
   - Fetch template's sections_config and content_schema
   - System prompt engineering for content generation
   - Integration with OpenAI API (gpt-4o-mini)
   - Generate content that matches content_schema
   - Fill all required content bindings
   - Apply template's style_config
   
   System prompt structure:
   
   You are generating website content for a business.
   
   BUSINESS DESCRIPTION: {user_prompt}
   
   TEMPLATE STRUCTURE: {sections_config}
   
   CONTENT SCHEMA: {content_schema}
   
   INSTRUCTIONS:
   1. Extract business details from the description
   2. Generate content for each section based on bindings
   3. Ensure all required fields are filled
   4. Match the tone and style to the business type
   5. Keep content concise and web-friendly
   6. Use appropriate CTAs for African market (e.g., WhatsApp)
   
   OUTPUT FORMAT:
   {
     "content": {
       "headline": "...",
       "services": [...],
       "business_phone": "...",
       // ... all content bindings
     }
   }
   

2. app/services/template_renderer.py:
   - render_template(template: dict, content: dict) -> dict
   - Merge template sections_config with generated content
   - Replace all {{placeholders}} with actual content
   - Apply style_config (colors, fonts, spacing)
   - Generate final HTML/CSS/JS
   - Minify output for performance
   - Optimize for mobile (African market)

3. app/routers/generation.py with:
   - POST /generate - Generate website from prompt + template_id
   - GET /generation/{id}/status - Check generation status
   - Process flow:
     * Validate template_id exists
     * Check user rate limits (5 generations/hour for free tier)
     * Fetch template structure
     * Generate content using content_generator
     * Render final website using template_renderer
     * Store in projects table with template reference
     * Return project_id and status

4. app/services/ai_generator.py (legacy support):
   - Keep for backwards compatibility
   - Refactor to use content_generator + template_renderer
   - Add migration path for old-style templates

5. Implement rate limiting:
   - Check current_period_generations in users table
   - Free tier: max 5 website generations per hour
   - Pro tier: unlimited (or higher limit)

The system should generate:
- Content that matches template's content_schema
- Properly filled content bindings
- Semantic, accessible content
- Mobile-optimized output
- WhatsApp integration for African market
```

**Acceptance Criteria:**
- [ ] Content generation fills template structure correctly
- [ ] All required content bindings populated
- [ ] Optional bindings handled gracefully (null/empty)
- [ ] Template styles applied consistently
- [ ] Generated HTML is valid and semantic
- [ ] Output is mobile-responsive
- [ ] Rate limiting enforced (5 generations/hour)
- [ ] Generation takes < 30 seconds
- [ ] Content matches business description
- [ ] Error handling for missing templates

---

#### Milestone 3.5: Template Management UI
**Goal:** Build comprehensive template management interface for users.

**User Stories:**
- As a user, I want to view all my custom templates in one place
- As a user, I want to edit my saved templates
- As a user, I want to delete templates I no longer need
- As a user, I want to preview templates before using them

**LLM Prompt:**
```
Create template management interface:

1. app/dashboard/templates/page.tsx - Template library page:
   - Tabbed interface: "System Templates" | "My Templates"
   - Grid layout showing template cards
   - Search and filter by category
   - Sort by: newest, most used, name
   - "Generate New Template" button
   - Empty state for users with no custom templates

2. components/TemplateLibrary.tsx - Template grid component:
   - Display system and user templates
   - Template card with hover preview
   - Quick actions: Use, Edit, Delete, Duplicate
   - Visual distinction between system and user templates

3. app/dashboard/templates/[id]/page.tsx - Template detail/edit page:
   - Full preview of template
   - Edit template metadata (name, description, category)
   - Edit template HTML/CSS (code editor)
   - Save changes button
   - Delete template option
   - "Use Template" CTA

4. components/TemplateEditor.tsx - Template code editor:
   - Syntax-highlighted code editor for HTML/CSS
   - Live preview pane
   - Split view (code | preview)
   - Validation feedback

5. Backend endpoints (already in Milestone 3.2):
   - GET /templates - List all templates
   - GET /templates/{id} - Get template details
   - PATCH /templates/{id} - Update template
   - DELETE /templates/{id} - Delete template
   - POST /templates/{id}/duplicate - Duplicate template
```

**Acceptance Criteria:**
- [ ] Users can view all system and custom templates
- [ ] Template search and filtering works
- [ ] Users can edit custom template metadata
- [ ] Users can edit custom template code
- [ ] Users can delete their templates
- [ ] Preview updates in real-time during editing
- [ ] Confirmation dialog for destructive actions
---

#### Milestone 3.6: Real-time Generation Status
**Goal:** Show users real-time progress during website and template generation.

**LLM Prompt:**
```
Implement real-time generation status updates:

Frontend:
1. Create a loading state component with progress indicator
2. Use polling or Server-Sent Events to check generation status
3. Show stages for website generation: "Analyzing prompt..." → "Generating layout..." → "Creating content..." → "Done!"
4. Show stages for template generation: "Analyzing design preferences..." → "Creating layout..." → "Generating styles..." → "Done!"
5. components/GenerationProgress.tsx
6. components/TemplateGenerationProgress.tsx

Backend:
1. Store generation status in database (projects and templates tables)
2. Update status at different stages
3. Return status in GET /generation/{id}/status endpoint
4. Return status in GET /templates/{id}/status endpoint

Make the loading experience delightful with smooth animations.
```

**Acceptance Criteria:**
- [ ] Users see generation progress for both websites and templates
- [ ] Status updates in real-time
- [ ] Smooth UX during waiting
- [ ] Clear error states
- [ ] Different progress messages for templates vs websites

---

### **Phase 4: Preview & Editing**

#### Milestone 4.1: Website Preview System
**Goal:** Display generated website in a safe, isolated preview.

**LLM Prompt:**
```
Create a website preview system:

1. components/WebsitePreview.tsx - iframe-based preview
   - Sandboxed iframe for security
   - Desktop/tablet/mobile responsive toggle
   - Full-screen mode
   - Refresh capability

2. app/dashboard/projects/[id]/page.tsx - Project editor page
   - Split view: editor on left, preview on right
   - Real-time preview updates

3. Handle iframe security (sandbox attributes)
4. Inject HTML/CSS/JS into iframe safely

Use Tailwind for the editor UI with a clean, VS Code-inspired design.
```

**Acceptance Criteria:**
- [ ] Preview renders correctly
- [ ] Responsive view toggle works
- [ ] Preview is secure (sandboxed)
- [ ] Updates reflect in real-time

---

#### Milestone 4.2: Basic Content Editor
**Goal:** Allow users to edit text and images in their generated website.

**LLM Prompt:**
```
Create a basic WYSIWYG editor:

1. components/ContentEditor.tsx - Simple text editor
   - Click-to-edit functionality
   - Rich text editing (bold, italic, links)
   - Use a library like TipTap or Slate.js
   - Save changes to database

2. components/ImageUploader.tsx - Image management
   - Upload images to Supabase Storage
   - Replace images in website
   - Image optimization

3. app/routers/projects.py - Backend endpoints:
   - PATCH /projects/{id}/content - Update HTML content
   - POST /projects/{id}/images - Upload image

Keep it simple - just essential editing for MVP.
```

**Acceptance Criteria:**
- [ ] Users can edit text content
- [ ] Users can upload and replace images
- [ ] Changes save automatically
- [ ] Preview updates immediately

---

#### Milestone 4.3: Theme Customization
**Goal:** Allow basic color and font customization.

**LLM Prompt:**
```
Add theme customization features:

1. components/ThemeCustomizer.tsx - Side panel with:
   - Color picker for primary/secondary colors
   - Font family selector (3-5 Google Fonts)
   - Button to apply changes

2. CSS variable injection system:
   - Parse CSS and inject CSS variables
   - Update preview in real-time
   - Save theme settings to database

3. Backend: Add theme_settings JSONB column to projects table

Keep it simple - focus on colors and fonts only for MVP.
```

**Acceptance Criteria:**
- [ ] Users can change colors
- [ ] Users can change fonts
- [ ] Changes apply in real-time
- [ ] Settings persist

---

### **Phase 5: Project Management**

#### Milestone 5.1: Projects Dashboard
**Goal:** Display all user projects in an organized dashboard.

**LLM Prompt:**
```
Create a projects dashboard:

1. app/dashboard/page.tsx - Main dashboard with:
   - Grid of project cards
   - Create new project button
   - Search and filter functionality
   - Empty state for new users

2. components/ProjectCard.tsx - Project card showing:
   - Thumbnail preview
   - Project name
   - Created/updated date
   - Published status
   - Quick actions (edit, delete, duplicate)

3. Backend endpoints:
   - GET /projects - List all user projects
   - DELETE /projects/{id} - Delete project
   - POST /projects/{id}/duplicate - Duplicate project

Use a modern card-based layout with hover effects.
```

**Acceptance Criteria:**
- [ ] All projects displayed
- [ ] CRUD operations working
- [ ] Responsive grid layout
- [ ] Search/filter functional

---

#### Milestone 5.2: Project Settings
**Goal:** Allow users to configure project settings.

**LLM Prompt:**
```
Create project settings page:

1. app/dashboard/projects/[id]/settings/page.tsx with:
   - Project name editing
   - Subdomain configuration (alphanumeric only)
   - Delete project (with confirmation)
   - SEO settings (title, description) - nice to have

2. Backend validation:
   - Ensure subdomain uniqueness
   - Validate subdomain format
   - Update projects table

3. Add optimistic UI updates
```

**Acceptance Criteria:**
- [ ] Users can rename projects
- [ ] Subdomain validation works
- [ ] Delete confirmation prevents accidents
- [ ] All changes persist

---

### **Phase 6: Publishing & Deployment**

#### Milestone 6.1: Vercel Integration
**Goal:** Set up Vercel API integration for deployments.

**LLM Prompt:**
```
Create Vercel deployment integration:

1. app/services/deployment.py with:
   - deploy_website(project_id: str) -> str (returns URL)
   - delete_deployment(deployment_id: str)
   - Use Vercel API v2
   - Handle authentication with Vercel token

2. Generate static HTML files from project content
3. Deploy to Vercel with unique subdomain
4. Store deployment URL in database

5. app/routers/deployment.py:
   - POST /projects/{id}/deploy
   - DELETE /projects/{id}/deploy
   - GET /projects/{id}/deployment-status

Handle deployment errors gracefully.
```

**Acceptance Criteria:**
- [ ] Deployment to Vercel successful
- [ ] Unique subdomain assigned
- [ ] Deployment URL stored
- [ ] Error handling robust
- [ ] Generated websites (using SSG or SSR) are extremely lightweight e.g make use of minimal JS, optimized images (image compression for large images)

---

#### Milestone 6.2: Publish/Unpublish UI
**Goal:** Add one-click publish functionality to the UI.

**LLM Prompt:**
```
Create publishing interface:

1. components/PublishButton.tsx - Smart button with states:
   - "Publish" (unpublished state)
   - "Publishing..." (loading)
   - "Published" with URL (published state)
   - "Unpublish" option

2. components/PublishModal.tsx - Success modal showing:
   - Deployed URL
   - Preview button
   - Share buttons (copy link, social)

3. Update project editor to show publish status
4. Add deployment history (nice to have)

Make the publish moment feel celebratory!
```

**Acceptance Criteria:**
- [ ] One-click publish works
- [ ] Published URL accessible
- [ ] Unpublish functionality works
- [ ] Success state delightful

---

### **Phase 7: Payments & Subscriptions**

#### Milestone 7.1: Stripe Integration Setup
**Goal:** Set up Stripe for subscription management.

**LLM Prompt:**
```
Set up Stripe integration:

1. Backend (FastAPI):
   - app/services/stripe_service.py with:
     - create_customer(user_id, email)
     - create_checkout_session(customer_id, price_id)
     - handle_webhook(event)
   
2. app/routers/billing.py:
   - POST /billing/checkout - Create checkout session
   - POST /billing/portal - Create customer portal session
   - POST /billing/webhook - Handle Stripe webhooks

3. Set up two products in Stripe:
   - Free tier: 1 website
   - Pro tier: Unlimited websites ($10/month)

4. Webhook handling for:
   - checkout.session.completed
   - customer.subscription.updated
   - customer.subscription.deleted
```

**Acceptance Criteria:**
- [ ] Stripe account configured
- [ ] Products created
- [ ] Webhooks receiving events
- [ ] Customer creation working

---

#### Milestone 7.2: Subscription UI & Upgrade Flow
**Goal:** Build subscription management UI.

**LLM Prompt:**
```
Create subscription and billing UI:

1. app/dashboard/billing/page.tsx - Billing page with:
   - Current plan display
   - Usage stats (projects created vs limit)
   - Upgrade/downgrade buttons
   - Manage subscription button (links to Stripe portal)

2. components/PricingTable.tsx - Pricing comparison:
   - Free: 1 website
   - Pro: Unlimited websites, priority support
   - Highlight differences
   - Call-to-action buttons

3. Enforce limits:
   - Block project creation if limit reached
   - Show upgrade prompt
   - Graceful degradation for downgraded users

4. Success/cancel redirect handling after Stripe checkout
```

**Acceptance Criteria:**
- [ ] Pricing page attractive
- [ ] Upgrade flow seamless
- [ ] Limits enforced correctly
- [ ] Portal link working

---

#### Milestone 7.3: Subscription Enforcement
**Goal:** Enforce subscription limits throughout the app.

**LLM Prompt:**
```
Implement subscription tier enforcement:

1. Create middleware/hooks:
   - hooks/useSubscription.ts - Check user tier and limits
   - Middleware to check limits on project creation

2. Update backend:
   - Add subscription checks to POST /generate endpoint
   - Return 403 if limit exceeded
   - Include upgrade URL in error response

3. Update UI:
   - Show upgrade prompt when limit reached
   - Display tier badge on dashboard
   - Conditional features based on tier

4. Add grace period for downgraded users (7 days to choose which project to keep)
```

**Acceptance Criteria:**
- [ ] Free users limited to 1 project
- [ ] Pro users have unlimited projects
- [ ] Clear messaging about limits
- [ ] Upgrade prompts contextual

---

### **Phase 8: Polish & Launch**

#### Milestone 8.1: Landing Page
**Goal:** Create a compelling landing page for the product.

**LLM Prompt:**
```
Create a beautiful landing page:

1. app/page.tsx - Landing page with sections:
   - Hero: Bold headline, demo video/gif, CTA
   - Features: 3-column grid of key features
   - How it works: 3-step process
   - Pricing: Pricing table
   - FAQ: Common questions
   - Footer: Links, social, legal

2. Use Tailwind CSS with:
   - Gradient backgrounds
   - Smooth animations (framer-motion)
   - Modern, clean design
   - Mobile-first approach

3. Add SEO metadata and Open Graph tags

Make it conversion-focused and visually stunning.
```

**Acceptance Criteria:**
- [ ] Landing page live
- [ ] Responsive design
- [ ] Fast loading
- [ ] SEO optimized

---

#### Milestone 8.2: Onboarding Flow
**Goal:** Create a smooth onboarding experience for new users.

**LLM Prompt:**
```
Build an onboarding flow:

1. components/OnboardingModal.tsx - Multi-step modal:
   - Step 1: Welcome message
   - Step 2: Quick tutorial (how to use)
   - Step 3: Choose template or start from scratch
   - Skip option

2. Show onboarding once per user (store in database)
3. Add helpful tooltips on first project creation
4. Create a quick-start template/example

Use progressive disclosure - don't overwhelm users.
```

**Acceptance Criteria:**
- [ ] Onboarding shown to new users
- [ ] Can be skipped
- [ ] Only shows once
- [ ] Helpful and concise

---

#### Milestone 8.3: Error Handling & Edge Cases
**Goal:** Handle all error states gracefully.

**LLM Prompt:**
```
Implement comprehensive error handling:

1. Create error boundary components:
   - components/ErrorBoundary.tsx
   - app/error.tsx
   - app/not-found.tsx

2. Add error states for:
   - Network failures
   - API errors
   - Authentication errors
   - Rate limit errors
   - Deployment failures

3. Add logging:
   - Client-side error logging to console
   - Backend logging with structured logs
   - Error tracking setup (Vercel)

4. Add retry logic for transient failures
5. User-friendly error messages (no technical jargon)

Make errors informative but not scary.
```

**Acceptance Criteria:**
- [ ] All error states handled
- [ ] Error messages user-friendly
- [ ] Logging functional
- [ ] Retry logic working

---

#### Milestone 8.4: Performance Optimization
**Goal:** Optimize for speed and user experience.

**LLM Prompt:**
```
Optimize application performance:

1. Frontend optimizations:
   - Implement code splitting
   - Add loading skeletons
   - Optimize images (next/image)
   - Lazy load components
   - Minimize bundle size

2. Backend optimizations:
   - Add database indexes
   - Implement caching (Redis optional)
   - Optimize API response times
   - Connection pooling

3. Add performance monitoring:
   - Vercel Analytics
   - Web Vitals tracking
   - API response time monitoring

4. Run Lighthouse audit and address issues

Target: Lighthouse score > 90 for all metrics.
```

**Acceptance Criteria:**
- [ ] Page load < 2 seconds
- [ ] Time to interactive < 3 seconds
- [ ] Lighthouse score > 90
- [ ] No unnecessary re-renders

---

#### Milestone 8.5: Security & Compliance
**Goal:** Ensure the application is secure and compliant.

**LLM Prompt:**
```
Implement security best practices:

1. Frontend security:
   - Sanitize all user inputs
   - Implement CSP headers
   - Secure iframe sandboxing
   - XSS prevention

2. Backend security:
   - Input validation with Pydantic
   - Rate limiting on all endpoints
   - SQL injection prevention (use Supabase safely)
   - API key protection

3. Add legal pages:
   - app/privacy/page.tsx - Privacy policy
   - app/terms/page.tsx - Terms of service
   - Cookie consent banner

4. GDPR compliance:
   - Data export capability
   - Account deletion
   - Clear data usage explanation

Also ensure 
Nigeria's NDPR and South Africa's POPIA Compliance
 
Run security audit with tools like npm audit.
```

**Acceptance Criteria:**
- [ ] Security headers configured
- [ ] No critical vulnerabilities
- [ ] Legal pages published
- [ ] GDPR-compliant features

---

#### Milestone 8.6: Testing & QA
**Goal:** Write tests for critical functionality.

**LLM Prompt:**
```
Add testing coverage:

1. Frontend tests (Jest + React Testing Library):
   - components/__tests__/AuthForm.test.tsx
   - components/__tests__/ProjectCard.test.tsx
   - app/__tests__/page.test.tsx
   - Test user interactions and edge cases

2. Backend tests (pytest):
   - tests/test_auth.py
   - tests/test_generation.py
   - tests/test_projects.py
   - Test API endpoints and business logic

3. E2E tests (Playwright - optional):
   - tests/e2e/auth.spec.ts
   - tests/e2e/generation.spec.ts
   - Critical user flows

4. Set up CI/CD with GitHub Actions

Aim for >70% code coverage on critical paths.
```

**Acceptance Criteria:**
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests cover critical flows
- [ ] CI/CD pipeline working

---

## 6. Success Metrics

### Primary KPIs
- **User Sign-ups:** 100+ users in first month
- **Website Generations:** 500+ generations
- **Template Generations:** 150+ custom template generations
- **Paid Conversions:** 5% conversion rate from free to paid
- **User Retention:** 40% 7-day retention
- **Percentage of sign-ups from target African countries:** 250+ sign-ups from Nigeria

### Secondary Metrics
- Average time to first website: < 5 minutes
- Generation success rate: > 95% (websites and templates)
- Template reuse rate: 30% of users reuse at least one custom template
- Page load time: < 2 seconds
- Customer satisfaction: > 4.5/5
- Activation rate of WhatsApp widget on generated sites: 4/5
- Template generation to website creation ratio: 1:3 (1 template used for 3 websites)

### Template-Specific Metrics
- Custom template generation success rate: > 90%
- Average templates per user: 2-3 custom templates
- Template edit rate: 40% of custom templates are edited after generation
- System vs custom template usage: Track adoption of AI-generated templates vs pre-built ones

---

## 7. Timeline Estimate

| Phase | Duration | Milestone Count |
|-------|----------|-----------------|
| Phase 1: Foundation | 3-4 days | 2 |
| Phase 2: Authentication | 3-4 days | 3 |
| Phase 3: AI Generation & Templates | 10-14 days | 6 |
| Phase 4: Preview & Editing | 5-7 days | 3 |
| Phase 5: Project Management | 3-4 days | 2 |
| Phase 6: Publishing | 4-5 days | 2 |
| Phase 7: Payments | 4-5 days | 3 |
| Phase 8: Polish & Launch | 5-7 days | 6 |
| **Total** | **37-54 days** | **27 milestones** |

*Note: Timeline assumes one developer using LLM assistance (Cursor). Can be parallelized with multiple developers.*

---

## 8. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI generation quality inconsistent | High | Component-based generation with pre-validated samples, few-shot learning, structured output validation |
| Component library becomes too complex | Medium | Start with 5-7 core components, add more based on user feedback, clear documentation |
| AI selects inappropriate components | Medium | Strong system prompts with business-type analysis, validation layer, allow user override |
| Vercel API changes/limits | Medium | Abstract deployment layer, consider alternatives |
| High OpenAI API costs | Medium | Component reuse reduces token usage, strict rate limiting, cache template structures, separate template from content generation |
| Security vulnerabilities in generated code | High | Pre-validated component samples, sanitize content only, sandbox previews, security audits |
| Slow generation times | Medium | Component-based approach is faster, async processing, progress updates, cache components |
| Template generation produces invalid JSON | High | Structured output enforcement, validation layer, retry logic with corrections |
| Users generate too many low-quality templates | Low | Rate limiting (3/hour), storage limits, option to archive/delete templates |
| Content doesn't fit template structure | Medium | Clear content_schema definitions, graceful fallbacks, allow manual editing |

---

## 9. Future Enhancements (Post-MVP)

1. **Multi-page websites** - Support for multiple pages
2. **Custom domains** - Allow users to connect their own domains
3. **Advanced editor** - Drag-and-drop visual editor
4. **Component library** - Pre-built sections to add
5. **Team collaboration** - Share and collaborate on projects
6. **Analytics integration** - Built-in website analytics
7. **SEO tools** - Meta tags, sitemap generation
8. **More AI features** - Regenerate sections, AI copywriting
9. **Template marketplace** - User-submitted templates that can be shared publicly or sold
10. **Template versioning** - Track changes to templates over time
11. **Advanced component library** - Expand to 20+ component types with more variations
12. **Component marketplace** - Users can create and sell individual components
13. **AI template refinement** - Iteratively improve templates with AI suggestions
14. **Template analytics** - Track which templates perform best for different business types
15. **Visual component editor** - Drag-and-drop interface for building custom components
16. **Component A/B testing** - Test different component variations
17. **Dynamic component loading** - Load components on-demand for performance
18. **Component animations** - Pre-built animation libraries for components
19. **White-label solution** - Enterprise offering
20. **Integration with African Payment Gateways** - Paystack, Flutterwave
21. **Direct WhatsApp Integration** - Beyond a simple link, this could include automated messaging or order notifications
22. **SMS Notification** - For user account actions or customer inquiries
23. **Offline-First Capabilities** - For generated websites using service workers, which would be a game-changer in areas with spotty connectivity
24. **Template collaboration** - Share templates with team members
25. **Optional (Future Use)** - Google Analytics tracking ID, Sentry DSN for error tracking, App URL for production deployments





---

## 10. Appendix

### Environment Variables Required

**Frontend (.env.local):**
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
```

**Backend (.env):**
```
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
OPENAI_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
VERCEL_API_TOKEN=
VERCEL_TEAM_ID=
```

### Useful Resources
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Stripe Documentation](https://stripe.com/docs)
- [Vercel API Documentation](https://vercel.com/docs/rest-api)

---

**Document Version:** 1.2  
**Last Updated:** October 3, 2025  
**Status:** Ready for Development  
**Changelog:**
- v1.2: Updated to component-based architecture
  - Added component library structure with 5-7 core components
  - Enhanced hero section with background options (image/color/video) and alignment controls
  - Separated template generation (structure) from content generation (data)
  - Added Milestone 3.2: Component Library Setup
  - Renamed milestones for clarity (3.3→3.4, 3.4→3.5, 3.5→3.6)
  - Updated database schema with sections_config and content_schema
  - Enhanced template generation with few-shot learning approach
  - Updated timeline: 37-54 days, 27 milestones
  - Added component-specific risks and future enhancements
- v1.1: Added AI Template Generation feature with custom template creation, management, and reuse capabilities
- v1.0: Initial PRD release

