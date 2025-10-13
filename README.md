# SiteSmith - AI Website Builder

AI Website Builder for African Entrepreneurs. Create professional websites in minutes using natural language.

## 🏗️ Project Structure

```
LandingV2/
├── frontend/          # Next.js 15 frontend application
├── backend/           # FastAPI backend API
├── prd.md            # Product Requirements Document
└── README.md         # This file
```

## 🚀 Tech Stack

### Frontend
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Deployment:** Vercel

### Backend
- **Framework:** FastAPI (Python 3.12+)
- **Database:** Supabase (PostgreSQL)
- **Authentication:** Supabase Auth
- **Payments:** Stripe
- **Package Manager:** uv (fast Python package installer)

## 📋 Prerequisites

- Node.js 20.x or higher
- Python 3.12 or higher
- uv (Python package installer)
- Docker (optional)
- npm or yarn

## 🛠️ Quick Start

### Frontend Development

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your credentials
npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000)

### Backend Development

```bash
cd backend
uv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend API will be available at [http://localhost:8000](http://localhost:8000)

## 🐳 Docker Setup

```bash
# Build and run all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop all services
docker-compose down
```

## 📖 Documentation

- [Frontend README](./frontend/README.md) - Frontend setup and development
- [Product Requirements](./prd.md) - Complete product specification
- [Backend README](./backend/README.md) - Backend setup and API docs
- [Services Documentation](./backend/app/services/README.md) - Detailed service documentation

## 🏗️ Backend Services Architecture

The backend is organized into specialized services handling different aspects of website generation and deployment:

### Core Generation Services

#### 🧠 Business Analyzer (`business_analyzer.py`)
Analyzes user prompts to extract structured business requirements for website generation.
- Identifies business type, industry, and user intent
- Determines site purpose and target audience
- Generates design direction (tone, style, colors)
- Extracts key features and content strategy
- Outputs: `BusinessAnalysis` model with 15+ structured fields

#### 🎨 Template Generator (`template_generator.py`)
Generates complete website templates using OpenAI and component library.
- Creates sections configuration with component types and variations
- Builds style configuration (colors, fonts, spacing)
- Defines content schema for all required fields
- Generates preview HTML for template visualization
- Uses: Business analysis, component library, and AI

#### 📝 Content Generator (`content_generator.py`)
Generates website content based on templates and business descriptions.
- Fetches template structure from database
- Generates localized content for African markets
- Fills all required schema fields with AI-generated content
- Validates content against template schema
- Supports WhatsApp integration and local payment methods

#### 🎭 Template Renderer (`template_renderer.py`)
Renders complete websites by merging templates with generated content.
- Replaces content placeholders in HTML/CSS/JS
- Handles array content (services, testimonials, etc.)
- Applies style variables and configurations
- Builds optimized HTML structure with SEO
- Outputs: Complete website files ready for deployment

### React Generation Services

#### ⚛️ React Website Generator (`react_website_generator.py`)
Generates modern React/TypeScript/Tailwind websites from user prompts.
- Analyzes business requirements
- Generates multi-page website structure
- Creates React components with TypeScript
- Uses shadcn/ui components for UI primitives
- Outputs: Complete Vite + React project

#### 📦 React File Manager (`react_file_manager.py`)
Manages generation of all React project files and configurations.
- Generates config files (vite.config, tsconfig, tailwind.config)
- Creates 15+ reusable UI components (Button, Card, Badge, etc.)
- Builds page components with proper routing
- Generates App.tsx and style files
- 1200+ lines of component templates

#### 🔧 React Models (`react_models.py`)
Pydantic models for React website structure and generation.
- `WebsiteStructure`: Complete site configuration
- `PageStructure`: Individual page definitions
- `PageComponent`: Component/section structure
- `ComponentFile`: Generated file representation
- Type-safe generation with validation

### Component & Validation Services

#### 📚 Component Library (`components_library.py`)
Comprehensive library of validated, reusable website components.
- **8 component types**: Header, Hero, Services, About, CTA, Contact, Testimonials, Footer
- **20+ variations**: Multiple designs per component type
- HTML/CSS templates with content bindings
- Validation and rendering utilities
- 2400+ lines of production-ready components

#### ✅ Code Validator (`code_validator.py`)
Validates generated React/TypeScript code for common errors.
- Validates lucide-react icon imports
- Checks for duplicate/conflicting exports
- Validates TypeScript syntax (braces, parens)
- Cross-file import/export validation
- Auto-fixes invalid icons with safe alternatives

#### 🎯 Icon Validator (`icon_validator.py`)
Ensures only valid lucide-react icons are used in generated code.
- 136+ verified safe icons categorized by purpose
- Navigation, Communication, Location, People, Media, etc.
- Suggests alternatives for invalid icons
- Prevents import errors in generated code
- Formats icon lists for LLM prompts

#### 🔍 Template Validator (`template_validator.py`)
Validates template structure, sections, styles, and content schemas.
- Validates required template fields
- Checks sections configuration
- Validates style configuration (colors, fonts, spacing)
- Ensures content schema completeness
- Cross-validates content bindings

### Deployment & Utility Services

#### 🚀 Deployment Service (`deployment.py`)
Handles deployment of websites to Vercel using Vercel API v2.
- Creates/manages Vercel projects
- Generates static files (HTML/CSS/JS)
- Deploys to production with public access
- Monitors deployment status
- Updates database with deployment URLs

#### 🤖 Prompt OpenAI (`prompt_open_ai.py`)
Centralized OpenAI API client with structured output support.
- Supports GPT-4o-mini, GPT-4o, GPT-5, o3-mini, o4-mini models
- Structured output with Pydantic models
- Automatic retry logic (3 attempts)
- Token usage tracking and logging
- Configurable temperature and max tokens

#### 🎨 UI Components Extended (`ui_components_extended.py`)
Extended set of advanced UI components for React generation.
- Accordion, Tabs, Tooltip, Popover
- Dropdown Menu, Toggle, Radio Group
- Table, Toast notifications
- Full TypeScript implementations
- Consistent with shadcn/ui patterns

### Service Architecture Flow

```
User Prompt
    ↓
Business Analyzer → BusinessAnalysis
    ↓
Template Generator → Template Structure
    ↓
Content Generator → Generated Content
    ↓
Template Renderer → Complete Website (HTML/CSS/JS)
    ↓
Deployment Service → Live Website (Vercel)
```

**OR** (React Flow)

```
User Prompt
    ↓
Business Analyzer → BusinessAnalysis
    ↓
React Website Generator
    ├→ React File Manager → Config Files
    ├→ UI Components → Component Files
    └→ Page Generator → Page Files
    ↓
Complete React Project
```

For detailed API documentation and usage examples, see [Services README](./backend/app/services/README.md).

## 🎯 MVP Features

- ✅ User authentication (Supabase)
- ✅ AI website generation (OpenAI)
- ✅ Live preview system
- ✅ Basic content editing
- ✅ One-click publishing
- ✅ Subscription management (Stripe)
- ✅ WhatsApp integration


See [prd.md](./prd.md) for complete development roadmap.

## 🤝 Contributing

This is a private project. For questions or contributions, contact the development team.

## 📄 License

This project is private and proprietary.

---

Built with ❤️ for African Entrepreneurs
