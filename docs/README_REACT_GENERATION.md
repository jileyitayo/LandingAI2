# React Website Generation System

## Overview

The React Website Generation system creates complete, production-ready React/TypeScript websites from simple text prompts. It analyzes business requirements and generates a full project structure with components, routing, and styling.

## Architecture

### Core Components

1. **BusinessAnalyzer** (`business_analyzer.py`)
   - Analyzes user prompts to extract business requirements
   - Determines business type, industry, target audience
   - Identifies key pages and features needed
   - Defines design direction (tone, style, colors)

2. **ReactWebsiteGenerator** (`react_website_generator.py`)
   - Main orchestrator for React website generation
   - Converts business analysis into website structure
   - Generates React components and pages
   - Creates complete project files

3. **Generation Router** (`generation.py`)
   - API endpoints for triggering generation
   - Background task management
   - Rate limiting and authentication

## Generation Flow

```
User Prompt
    ↓
Business Analysis
    ↓
Website Structure Generation
    ↓
Component Generation
    ↓
File Creation
    ↓
Complete React Project
```

### Step-by-Step Process

#### 1. Business Analysis
```python
# Input: User prompt
"Create a website for a modern coffee shop called 'Bean & Brew'"

# Output: BusinessAnalysis
{
  "business_type": "Coffee Shop",
  "industry": "Food & Beverage",
  "site_purpose": "Informational with Menu Display",
  "target_audience": "Coffee enthusiasts and local residents",
  "key_pages": ["Home", "Menu", "About", "Contact"],
  "tone": "Friendly and Warm",
  "style_keywords": ["Modern", "Cozy", "Inviting"],
  "primary_colors": ["Brown", "Cream", "Green"],
  "must_have_features": ["Menu Display", "Contact Form", "Location Map"],
  "primary_cta": "Visit Us Today"
}
```

#### 2. Website Structure Generation
```python
# Converts analysis into page structures
{
  "name": "Bean & Brew",
  "tagline": "Your Daily Coffee Ritual",
  "pages": [
    {
      "name": "Home",
      "path": "/",
      "components": [
        {"name": "Hero", "type": "hero"},
        {"name": "Features", "type": "features"},
        {"name": "Cta", "type": "cta"}
      ]
    },
    {
      "name": "Menu",
      "path": "/menu",
      "components": [
        {"name": "Menu", "type": "features"}
      ]
    }
  ]
}
```

#### 3. Component Generation

Creates reusable React components:
- **Hero**: Main landing section with CTA
- **Features**: Grid layout for services/products
- **About**: Company story and mission
- **Contact**: Contact form and information
- **Testimonials**: Customer reviews
- **CTA**: Call-to-action sections
- **Stats**: Statistics and numbers

#### 4. File Generation

Generates complete project structure:

```
project/
├── package.json          # Dependencies and scripts
├── tsconfig.json        # TypeScript config
├── vite.config.ts       # Vite config
├── tailwind.config.js   # Tailwind config
├── index.html           # HTML entry point
└── src/
    ├── main.tsx         # React entry point
    ├── App.tsx          # Main app with routing
    ├── index.css        # Global styles
    ├── pages/
    │   ├── home.tsx
    │   ├── menu.tsx
    │   ├── about.tsx
    │   └── contact.tsx
    ├── components/
    │   ├── hero.tsx
    │   ├── features.tsx
    │   ├── contact.tsx
    │   └── ui/
    │       ├── button.tsx
    │       ├── card.tsx
    │       └── input.tsx
    └── lib/
        └── utils.ts
```

## API Usage

### Generate React Website

**Endpoint:** `POST /api/v1/generation/generate_react_website`

**Request:**
```json
{
  "prompt": "Create a website for my photography studio specializing in wedding photography",
  "project_name": "Photo Studio Website"
}
```

**Response:**
```json
{
  "project_id": "uuid-here",
  "status": "generating",
  "message": "React website generation started...",
  "website_structure": null,
  "business_analysis": null,
  "files_count": null
}
```

### Get Generated Website

**Endpoint:** `GET /api/v1/generation/react_website/{project_id}`

**Response:**
```json
{
  "project_id": "uuid-here",
  "status": "completed",
  "website_structure": { ... },
  "business_analysis": { ... },
  "files": {
    "package.json": "{ ... }",
    "src/App.tsx": "import ...",
    "src/pages/home.tsx": "...",
    ...
  },
  "files_count": 25,
  "created_at": "2025-10-11T...",
  "completed_at": "2025-10-11T..."
}
```

## Component Templates

### Hero Component
```tsx
<Hero
  title="Welcome to Bean & Brew"
  subtitle="Artisan Coffee & Pastries"
  description="Experience the perfect blend..."
  primaryCta="Visit Us"
  secondaryCta="View Menu"
/>
```

### Features Component
```tsx
<Features
  title="Our Services"
  description="What makes us special"
  features={[
    {
      title: "Premium Coffee",
      description: "Sourced from the finest beans"
    },
    {
      title: "Fresh Pastries",
      description: "Baked daily on-site"
    }
  ]}
/>
```

### Contact Component
```tsx
<Contact
  title="Get In Touch"
  description="We'd love to hear from you"
  email="hello@beanandbrew.com"
  phone="+1 (555) 123-4567"
  address="123 Main St, City"
/>
```

## Customization

### Colors
The system automatically selects appropriate colors based on business type:
- **Blue**: Professional, Corporate
- **Green/Emerald**: Health, Environment
- **Purple**: Creative, Luxury
- **Orange**: Food, Energy
- **Pink**: Beauty, Fashion

### Component Types
Available component types:
- `hero`: Landing section with CTA
- `features`: Grid of features/services
- `about`: About section
- `contact`: Contact form
- `testimonials`: Customer reviews
- `cta`: Call-to-action
- `stats`: Statistics display
- `team`: Team member profiles
- `pricing`: Pricing tables
- `gallery`: Image gallery
- `faq`: FAQ section

## Database Schema

Projects table needs these fields:
```sql
ALTER TABLE projects ADD COLUMN project_type VARCHAR;
ALTER TABLE projects ADD COLUMN react_files JSONB;
ALTER TABLE projects ADD COLUMN website_structure JSONB;
ALTER TABLE projects ADD COLUMN business_analysis JSONB;
```

## Rate Limits

- **Free Tier**: 5 generations per hour
- **Pro Tier**: 100 generations per hour

## Error Handling

The system handles various error scenarios:
- Invalid prompts (too short, empty)
- Rate limit exceeded
- Generation failures
- Invalid template types

## Testing

Run tests:
```bash
pytest backend/tests/test_react_generation.py -v
```

## Example Prompts

### Simple
```
"Create a website for my bakery"
```

### Detailed
```
"I need a professional website for my law firm specializing in family law.
We offer divorce consultation, child custody, and estate planning services.
The site should be professional and trustworthy."
```

### Specific
```
"Build a portfolio website for a freelance photographer.
Include a gallery, about page, contact form, and testimonials.
Modern, minimalist design with a focus on showcasing work."
```

## Technical Stack

- **Frontend**: React 19 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui inspired
- **Routing**: React Router v6
- **State Management**: React Query

## Future Enhancements

- [ ] Additional component types (FAQ, Pricing, Gallery)
- [ ] Custom theme generation
- [ ] Advanced animations
- [ ] SEO optimization
- [ ] Accessibility improvements
- [ ] Multi-language support
- [ ] Dark mode support
- [ ] Export as ZIP file
- [ ] Deploy to Vercel integration

## Support

For issues or questions:
- Check the test files for examples
- Review the component templates
- Contact the development team

---

✅ Simple: "Create a website for my bakery"
✅ Detailed: "Professional website for a law firm specializing in family law with team profiles and testimonials"
✅ Specific: "Modern portfolio for a wedding photographer with gallery and booking system"
All files are ready to use! The system is fully integrated with your existing authentication, rate limiting, and database infrastructure. 🎉

**Last Updated:** October 2025

