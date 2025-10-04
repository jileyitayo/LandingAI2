# Component Library Documentation

## Overview

The Component Library is a core feature of SiteSmith that provides reusable, validated, and customizable components for website generation. This system enables AI-powered template generation while maintaining consistency, quality, and flexibility.

### Key Features

- **8 Core Component Types** with 2-3 variations each
- **Flexible Content Bindings** with type validation
- **CSS Variable Theming** for easy customization
- **Mobile-Responsive Design** by default
- **African Market Optimization** (WhatsApp integration, data-friendly)
- **Type-Safe** with full TypeScript support

---

## Architecture

The component library follows a three-layer architecture:

```
┌─────────────────────────────────────────────┐
│          Frontend (Next.js)                 │
│  - TypeScript types                         │
│  - Validation schemas (Zod)                 │
│  - ComponentPreview component               │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│          Backend (FastAPI)                  │
│  - Component definitions                    │
│  - Validation functions                     │
│  - Rendering utilities                      │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│          Database (Supabase)                │
│  - Template storage (sections_config)       │
│  - Content schema definitions               │
└─────────────────────────────────────────────┘
```

---

## Component Types

### 1. Header Components

Header sections with logo and navigation.

#### Variations

##### `centered-logo`
- **Description**: Header with centered logo and navigation menu below
- **Best For**: Simple sites, portfolios, landing pages
- **Layout**: Centered logo, horizontal menu below
- **Mobile**: Stacks vertically

**Content Bindings:**
- `logo_url` (image, required) - Logo image URL
- `business_name` (text, required) - Business name for alt text
- `nav_items` (array, required) - Navigation menu items
  - `label` (string) - Menu item text
  - `url` (string) - Link URL

**Config Options:**
- `sticky` (boolean) - Sticky header on scroll
- `showBorder` (boolean) - Show bottom border

**Example Usage:**
```json
{
  "type": "header",
  "variation": "centered-logo",
  "content": {
    "logo_url": "https://example.com/logo.png",
    "business_name": "Acme Corp",
    "nav_items": [
      {"label": "Home", "url": "#home"},
      {"label": "Services", "url": "#services"},
      {"label": "Contact", "url": "#contact"}
    ]
  }
}
```

##### `logo-left`
- **Description**: Header with logo on left and right-aligned navigation
- **Best For**: Professional sites, e-commerce, corporate
- **Layout**: Logo left, horizontal menu right
- **Mobile**: Logo left, collapsible menu

**Content Bindings:** Same as `centered-logo`

---

### 2. Hero Components

Large, prominent sections typically at the top of pages.

#### Variations

##### `centered`
- **Description**: Full-width hero with centered content
- **Best For**: Landing pages, marketing sites
- **Features**: Background image/color/gradient support, overlay options
- **Layout**: Centered text and CTAs

**Content Bindings:**
- `headline` (text, required) - Main headline
- `subheadline` (text, required) - Supporting text
- `cta_text` (text, required, default: "Get Started") - Primary CTA button text
- `cta_url` (url, optional, default: "#contact") - Primary CTA link
- `secondary_cta_text` (text, optional) - Secondary CTA text
- `secondary_cta_url` (url, optional) - Secondary CTA link
- `background_image` (image, optional) - Background image
- `background_style` (text, optional) - CSS background style

**Config Options:**
- `background.type` - "image" | "color" | "gradient" | "video"
- `background.overlay` (boolean) - Show dark overlay
- `background.overlayOpacity` (0-1) - Overlay opacity
- `contentAlignment` - "center"
- `verticalAlignment` - "center"
- `minHeight` - "100vh" | "75vh" | "50vh"
- `textColor` - "light" | "dark"

**Example:**
```json
{
  "type": "hero",
  "variation": "centered",
  "content": {
    "headline": "Transform Your Business Online",
    "subheadline": "Create stunning websites in minutes with AI",
    "cta_text": "Start Free Trial",
    "cta_url": "#signup",
    "background_style": "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
  },
  "config": {
    "minHeight": "100vh",
    "textColor": "light"
  }
}
```

##### `split`
- **Description**: Hero with content on left and image on right
- **Best For**: Product pages, service descriptions
- **Features**: Side-by-side layout with image
- **Layout**: 50/50 split on desktop, stacks on mobile

**Content Bindings:**
- `headline` (text, required)
- `subheadline` (text, required)
- `cta_text` (text, required)
- `cta_url` (url, optional)
- `hero_image` (image, required) - Feature image
- `hero_image_alt` (text, optional)

##### `full-width`
- **Description**: Minimalist hero with large typography
- **Best For**: Bold statements, minimal designs
- **Features**: Maximalist typography, clean layout
- **Layout**: Centered, full-width

---

### 3. Services Components

Display services, features, or offerings.

#### Variations

##### `three-column`
- **Description**: Service cards in a 3-column grid
- **Best For**: 3-6 services, feature highlights
- **Layout**: Grid layout, cards with icons

**Content Bindings:**
- `section_title` (text, required, default: "Our Services")
- `section_description` (text, optional)
- `services` (array, required) - Service items
  - `icon` (string) - Icon (emoji or HTML entity)
  - `title` (string) - Service name
  - `description` (string) - Service description

**Config Options:**
- `columns` - 3
- `cardStyle` - "elevated" | "bordered" | "flat"
- `iconStyle` - "outlined" | "solid"

**Example:**
```json
{
  "type": "services",
  "variation": "three-column",
  "content": {
    "section_title": "What We Offer",
    "services": [
      {
        "icon": "🎨",
        "title": "Web Design",
        "description": "Beautiful, modern designs that convert"
      },
      {
        "icon": "⚡",
        "title": "Fast Delivery",
        "description": "Get your site live in under 5 minutes"
      },
      {
        "icon": "📱",
        "title": "Mobile First",
        "description": "Optimized for all devices"
      }
    ]
  }
}
```

##### `two-column`
- **Description**: Larger service cards in 2 columns
- **Best For**: Detailed services, 2-4 offerings
- **Layout**: 2-column grid with more content space

##### `list`
- **Description**: Vertical list of services
- **Best For**: Many services, simple layout
- **Layout**: Stacked list with icons

---

### 4. About Components

Tell your story or share company information.

#### Variations

##### `two-column`
- **Description**: About section with image and content side-by-side
- **Best For**: Company stories, team introductions
- **Features**: Image gallery, stats/highlights

**Content Bindings:**
- `section_title` (text, required)
- `about_text` (text, required)
- `about_image` (image, required)
- `about_image_alt` (text, optional)
- `highlights` (array, optional) - Key metrics
  - `value` (string) - Metric value (e.g., "10+")
  - `label` (string) - Metric label (e.g., "Years")

##### `centered`
- **Description**: Centered about section
- **Best For**: Mission statements, simple stories
- **Layout**: Centered text with optional feature icons

---

### 5. CTA (Call-to-Action) Components

Prompt visitors to take action.

#### Variations

##### `banner`
- **Description**: Full-width banner CTA
- **Best For**: High-impact conversions
- **Features**: Gradient background, centered content

**Content Bindings:**
- `cta_title` (text, required)
- `cta_text` (text, required)
- `cta_button_text` (text, required)
- `cta_url` (url, optional)

##### `centered`
- **Description**: Boxed CTA section
- **Best For**: Mid-page conversions
- **Features**: White box, primary and secondary CTAs

---

### 6. Contact Components

Enable visitors to reach out.

#### Variations

##### `form-only`
- **Description**: Simple centered contact form
- **Best For**: Basic contact needs
- **Fields**: Name, email, message

**Content Bindings:**
- `section_title` (text, required)
- `section_description` (text, optional)
- `submit_button_text` (text, required)
- `form_action` (url, optional)

##### `split-info`
- **Description**: Contact form with business info
- **Best For**: Complete contact section
- **Features**: Form + email/phone/WhatsApp info

**Content Bindings:**
- All from `form-only` plus:
- `business_email` (email, required)
- `business_phone` (phone, optional)
- `whatsapp_number` (phone, optional) - African market feature

**Example with WhatsApp:**
```json
{
  "type": "contact",
  "variation": "split-info",
  "content": {
    "section_title": "Get in Touch",
    "business_email": "hello@example.com",
    "business_phone": "+234 812 345 6789",
    "whatsapp_number": "2348123456789",
    "submit_button_text": "Send Message"
  },
  "config": {
    "showWhatsApp": true
  }
}
```

---

### 7. Testimonials Components

Display customer feedback.

#### Variations

##### `cards`
- **Description**: Grid of testimonial cards
- **Best For**: Multiple testimonials, social proof
- **Layout**: Card grid with quotes

**Content Bindings:**
- `section_title` (text, required)
- `section_description` (text, optional)
- `testimonials` (array, required)
  - `quote` (string) - Testimonial text
  - `author_name` (string) - Customer name
  - `author_title` (string) - Customer title/company

##### `simple`
- **Description**: Minimal list of testimonials
- **Best For**: Few testimonials, clean design
- **Layout**: Vertical list

---

### 8. Footer Components

Website footer with links and info.

#### Variations

##### `simple`
- **Description**: Simple centered footer
- **Best For**: Landing pages, minimal sites
- **Layout**: Centered links and copyright

**Content Bindings:**
- `copyright_text` (text, required)
- `footer_links` (array, optional)
  - `label` (string)
  - `url` (string)

##### `columns`
- **Description**: Multi-column footer with details
- **Best For**: Full websites, lots of links
- **Layout**: 3-column grid with business info

**Content Bindings:**
- `business_name` (text, required)
- `business_description` (text, optional)
- `business_email` (email, optional)
- `business_phone` (phone, optional)
- `copyright_text` (text, required)
- `footer_links` (array, optional)

---

## CSS Theming System

All components use CSS variables for easy theming:

### Core Variables

```css
/* Colors */
--color-primary: #6366f1;
--color-primary-dark: #4f46e5;
--color-secondary: #8b5cf6;
--color-background: #ffffff;
--color-card-background: #f9fafb;
--color-text: #6b7280;
--color-heading: #1f2937;
--color-border: #e5e7eb;

/* Spacing */
--spacing-xs: 0.25rem;
--spacing-sm: 1rem;
--spacing-md: 1.5rem;
--spacing-lg: 2rem;
--spacing-xl: 3rem;
--spacing-2xl: 5rem;

/* Layout */
--container-max-width: 1200px;

/* Typography */
--font-heading: 'Inter', sans-serif;
--font-body: 'Inter', sans-serif;
```

### Customization Example

```json
{
  "style_config": {
    "colorScheme": {
      "primary": "#10b981",
      "secondary": "#3b82f6",
      "background": "#ffffff",
      "text": "#374151",
      "heading": "#111827"
    },
    "typography": {
      "headingFont": "'Poppins', sans-serif",
      "bodyFont": "'Inter', sans-serif"
    },
    "spacing": "comfortable"
  }
}
```

---

## Usage Examples

### Backend: Creating a Template with Components

```python
from app.services.components_library import component_library, ComponentType

# Get a hero component
hero = component_library.get_component(ComponentType.HERO, "centered")

# Create a template section
section = {
    "id": "hero-1",
    "type": "hero",
    "order": 1,
    "variation": "centered",
    "html": hero["html"],
    "css": hero["css"],
    "config": hero["config"],
    "content_bindings": hero["content_bindings"]
}

# Validate component
is_valid, error = component_library.validate_component_structure(hero)
if not is_valid:
    print(f"Validation error: {error}")
```

### Backend: Rendering a Component with Content

```python
# Define content
content = {
    "headline": "Welcome to My Business",
    "subheadline": "We provide excellent services",
    "cta_text": "Contact Us",
    "cta_url": "#contact"
}

# Render component
rendered_html = component_library.render_component(hero, content)
```

### Frontend: Previewing a Component

```tsx
import ComponentPreview from '@/components/ComponentPreview';
import { ComponentVariation } from '@/lib/components/types';

function MyComponentPreview() {
  const component: ComponentVariation = {
    name: "Centered Hero",
    description: "Full-width hero with centered content",
    html: "...",
    css: "...",
    config: {},
    content_bindings: {},
    tags: ["hero", "centered"]
  };

  const content = {
    headline: "My Business",
    subheadline: "Quality services",
    cta_text: "Learn More",
    cta_url: "#about"
  };

  return (
    <ComponentPreview 
      component={component}
      content={content}
      showControls={true}
    />
  );
}
```

### Frontend: Validating Template Data

```typescript
import { validateTemplate, validateTemplateContent } from '@/lib/components/schema';

// Validate template structure
const templateValidation = validateTemplate(templateData);
if (!templateValidation.valid) {
  console.error('Template errors:', templateValidation.errors);
}

// Validate content against schema
const contentValidation = validateTemplateContent(
  contentData,
  template.content_schema
);
if (!contentValidation.valid) {
  console.error('Content errors:', contentValidation.errors);
}
if (contentValidation.warnings.length > 0) {
  console.warn('Content warnings:', contentValidation.warnings);
}
```

---

## AI Integration

### Template Generation Prompt Structure

When AI generates templates, it uses the component library:

```
You are a UI/UX expert generating website templates using a component library.

AVAILABLE COMPONENTS:
- Header: centered-logo, logo-left
- Hero: centered, split, full-width
- Services: three-column, two-column, list
- About: two-column, centered
- CTA: banner, centered
- Contact: form-only, split-info
- Testimonials: cards, simple
- Footer: simple, columns

USER REQUEST: "Create a modern restaurant website with warm colors"

INSTRUCTIONS:
1. Select appropriate components (header, hero, services, contact, footer)
2. Choose variations that match the style (e.g., "split" hero for restaurant)
3. Define color scheme (warm colors: oranges, reds)
4. Specify content bindings (menu items, contact info)

OUTPUT: JSON with sections_config
```

### Content Generation

After template is created, AI fills it with business content:

```
TEMPLATE STRUCTURE: [sections with content_bindings]
BUSINESS DESCRIPTION: "Italian restaurant in Lagos"

Generate content for:
- headline: [business name]
- services: [menu categories]
- whatsapp_number: [for orders]
```

---

## Best Practices

### Component Design

1. **Mobile-First**: All components responsive by default
2. **Semantic HTML**: Use proper HTML5 elements
3. **Accessibility**: ARIA labels, keyboard navigation
4. **Performance**: Minimal CSS, no heavy libraries
5. **African Market**: WhatsApp integration, data-efficient

### Content Bindings

1. **Required vs Optional**: Mark appropriately
2. **Defaults**: Provide sensible defaults
3. **Validation**: Use proper types (email, phone, url)
4. **Placeholders**: Clear, helpful placeholders

### CSS Variables

1. **Consistent Naming**: Follow `--component-property` pattern
2. **Fallbacks**: Always provide fallback values
3. **Responsive**: Use clamp() for fluid typography
4. **Theme-able**: Use variables for all colors

---

## Testing

### Component Validation

```python
# Test component structure
def test_hero_component():
    hero = component_library.get_component(ComponentType.HERO, "centered")
    is_valid, error = component_library.validate_component_structure(hero)
    assert is_valid, f"Hero validation failed: {error}"
```

### Rendering Tests

```python
def test_hero_rendering():
    hero = component_library.get_component(ComponentType.HERO, "centered")
    content = {
        "headline": "Test Headline",
        "subheadline": "Test Subheadline",
        "cta_text": "Test CTA"
    }
    rendered = component_library.render_component(hero, content)
    assert "Test Headline" in rendered
    assert "Test CTA" in rendered
```

---

## Troubleshooting

### Common Issues

**Issue**: Placeholder not replaced in rendered HTML
- **Solution**: Ensure placeholder is defined in content_bindings
- **Check**: Placeholder format is `{{variable}}`

**Issue**: Array content not rendering
- **Solution**: Use `<!-- key_item_start -->` and `<!-- key_item_end -->` comments
- **Check**: Content key matches the loop key

**Issue**: CSS not applying
- **Solution**: Verify CSS variables are defined
- **Check**: No conflicting styles

**Issue**: Validation errors
- **Solution**: Check required fields in content_bindings
- **Check**: Content types match binding types

---

## Future Enhancements

### Planned Features

1. **More Components**: Blog, pricing, FAQ, team sections
2. **Component Marketplace**: User-submitted components
3. **Advanced Variations**: More layout options per component
4. **Animation Library**: Pre-built animations
5. **A/B Testing**: Component variation testing
6. **Version Control**: Track component changes
7. **Visual Editor**: Drag-and-drop component builder
8. **Dark Mode**: Built-in dark mode support

---

## API Reference

### Backend Endpoints

```
GET  /api/components                    # List all components
GET  /api/components/{type}             # Get components by type
GET  /api/components/{type}/{variation} # Get specific component
POST /api/components/validate           # Validate component structure
POST /api/components/render             # Render component with content
```

### Component Library Methods

```python
ComponentLibrary.get_component(type, variation)
ComponentLibrary.get_all_variations(type)
ComponentLibrary.list_component_types()
ComponentLibrary.validate_component_structure(component)
ComponentLibrary.render_component(component, content)
```

---

## Support

For questions or issues:
- Check this documentation first
- Review code examples in `/backend/app/services/components_library.py`
- Check type definitions in `/frontend/src/lib/components/types.ts`
- Refer to the PRD for overall architecture

---

## Changelog

### v1.0.0 (Current)
- Initial release with 8 component types
- 20 total component variations
- Full TypeScript support
- Validation schemas
- ComponentPreview component
- Complete documentation

---

**Last Updated**: October 4, 2025  
**Maintained By**: SiteSmith Development Team

