# Component Library Service

## Quick Start

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

## Available Components

- **Header** (2 variations): `centered-logo`, `logo-left`
- **Hero** (3 variations): `centered`, `split`, `full-width`
- **Services** (3 variations): `three-column`, `two-column`, `list`
- **About** (2 variations): `two-column`, `centered`
- **CTA** (2 variations): `banner`, `centered`
- **Contact** (2 variations): `form-only`, `split-info`
- **Testimonials** (2 variations): `cards`, `simple`
- **Footer** (2 variations): `simple`, `columns`

## Documentation

See `/docs/COMPONENT_LIBRARY.md` for complete documentation.

