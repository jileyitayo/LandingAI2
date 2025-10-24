# SiteSmith Services

This directory contains core services for the SiteSmith AI Website Builder.

## Services Overview

### 1. Component Library (`components_library.py`)

Manages the library of reusable website components.

```python
from app.services.components_library import component_library, ComponentType

# Get a component
hero = component_library.get_component(ComponentType.HERO, "centered")

# List all component types
types = component_library.list_component_types()

# Get all variations of a type
hero_variations = component_library.get_all_variations(ComponentType.HERO)

# Validate component
is_valid, error = component_library.validate_component_structure(hero)

# Render with content
content = {
    "headline": "Welcome",
    "subheadline": "Get started today",
    "cta_text": "Learn More"
}
rendered = component_library.render_component(hero, content)
```

### 2. Content Generator (`content_generator.py`)

Generates website content using OpenAI based on business descriptions.

```python
from app.services.content_generator import content_generator

# Generate content for a template
result = await content_generator.generate_content(
    prompt="Small bakery in Lagos selling fresh bread and pastries",
    template_id="restaurant-template-uuid",
    user_id="user-uuid"
)

print(result["content"])  # Generated content matching schema
print(result["metadata"])  # Business type, tone, etc.
```

### 3. Template Renderer (`template_renderer.py`)

Renders complete websites by merging templates with content.

```python
from app.services.templates.template_renderer import template_renderer

# Render template with content
result = template_renderer.render_template(
    template=template_data,  # From database
    content=generated_content  # From content_generator
)

print(result["html_content"])  # Complete HTML
print(result["css_content"])   # Complete CSS
print(result["js_content"])    # Complete JS
```

### 4. AI Generator (`ai_generator.py`)

Unified interface for content generation (new and legacy flows).

```python
from app.services.ai_generator import ai_generator

# New flow: Template-based generation
result = await ai_generator.generate_website(
    prompt="Fashion boutique in Nairobi",
    template_id="boutique-template-uuid",
    user_id="user-uuid"
)

# Legacy flow: Generate template from scratch
result = await ai_generator.generate_website(
    prompt="Create a modern restaurant website",
    template_id=None,  # Triggers legacy flow
    user_id="user-uuid",
    style_preferences={"colors": {...}}
)
```

### 5. Template Generator (`template_generator.py`)

Generates complete template structures using OpenAI (legacy).

```python
from app.services.templates.template_generator import template_generator

# Generate new template from scratch
template = template_generator.generate_template(
    prompt="Modern restaurant website with gallery",
    user_id="user-uuid",
    style_preferences={"colors": {"primary": "#ff6b6b"}}
)

print(template["sections_config"])  # Component structure
print(template["style_config"])     # Style configuration
print(template["content_schema"])   # Required content fields
```

### 6. Template Validator (`template_validator.py`)

Validates template structures and configurations.

```python
from app.services.validators.template_validator import validate_template_structure

# Validate template
is_valid, error = validate_template_structure(template_data)

if not is_valid:
    print(f"Validation error: {error}")
```

## Available Components

- **Header** (2 variations): `centered-logo`, `logo-left`
- **Hero** (3 variations): `centered`, `split`, `full-width`
- **Services** (3 variations): `three-column`, `two-column`, `list`
- **About** (2 variations): `two-column`, `centered`
- **CTA** (2 variations): `banner`, `centered`
- **Contact** (2 variations): `form-only`, `split-info`
- **Testimonials** (2 variations): `cards`, `simple`
- **Footer** (2 variations): `simple`, `columns`

## Service Dependencies

```
ai_generator
    ├── content_generator
    │   └── supabase_client
    ├── template_renderer
    │   └── components_library
    └── template_generator (legacy)
        ├── components_library
        └── template_validator
```

## Documentation

- **Component Library**: `/docs/COMPONENT_LIBRARY.md`
- **Content Generation**: `/docs/AI_CONTENT_GENERATION_SYSTEM.md`
- **Template Generation**: `/docs/AI_TEMPLATE_GENERATION_SYSTEM.md`

## Usage Recommendations

### For New Projects

Use the **new flow** (template-based):

```python
from app.services.ai_generator import ai_generator

result = await ai_generator.generate_website(
    prompt="Your business description here",
    template_id="selected-template-uuid",
    user_id="user-uuid"
)
```

### For Creating New Templates

Use the **legacy flow**:

```python
from app.services.templates.template_generator import template_generator

template = template_generator.generate_template(
    prompt="Template description",
    user_id="user-uuid"
)

# Save template to database for reuse
```

### For Direct Content Generation

```python
from app.services.content_generator import content_generator

content = await content_generator.generate_content(
    prompt="Business description",
    template_id="template-uuid",
    user_id="user-uuid"
)
```

### For Manual Rendering

```python
from app.services.templates.template_renderer import template_renderer

website = template_renderer.render_template(
    template=template_data,
    content=content_data
)
```

