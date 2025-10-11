"""
Component Library Service
Provides reusable, validated component samples for website generation.

This module contains:
- Component definitions with multiple variations
- Validation functions for component structure
- Rendering utilities for template generation
- Helper functions for component manipulation
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
import re
from pydantic import BaseModel, Field, validator


class ComponentType(str, Enum):
    """Supported component types"""
    HEADER = "header"
    HERO = "hero"
    SERVICES = "services"
    ABOUT = "about"
    CTA = "cta"
    CONTACT = "contact"
    TESTIMONIALS = "testimonials"
    FOOTER = "footer"
    # New advanced types
    # NAVIGATION = "navigation"
    # TESTIMONIALS = "testimonials"
    # GALLERY = "gallery"
    # PRICING = "pricing"
    # FAQ = "faq"
    # BLOG = "blog"
    # NEWSLETTER = "newsletter"
    # STATS = "stats"
    # TEAM = "team"
    # PORTFOLIO = "portfolio"
    # TIMELINE = "timeline"
    # MAP = "map"
    # CHAT = "chat"
    # BOOKING = "booking"
    # PAYMENT = "payment"
    # REVIEWS = "reviews"
    # SOCIAL_PROOF = "social_proof"
    # BREADCRUMBS = "breadcrumbs"
    # SEARCH = "search"
    # FILTER = "filter"
    # COMPARISON = "comparison"
    # CALCULATOR = "calculator"
    # FORM_BUILDER = "form_builder"
    # VIDEO_PLAYER = "video_player"
    # IMAGE_CAROUSEL = "image_carousel"
    # ACCORDION = "accordion"
    # TABS = "tabs"
    # MODAL = "modal"
    # TOOLTIP = "tooltip"
    # PROGRESS_BAR = "progress_bar"
    # COUNTER = "counter"
    # ANIMATION = "animation"
    # PARALLAX = "parallax"
    # INTERACTIVE = "interactive"


class ContentBindingType(str, Enum):
    """Types for content bindings"""
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    IMAGE = "image"
    VIDEO = "video"
    ARRAY = "array"
    COLOR = "color"


class ContentBinding(BaseModel):
    """Schema for content binding definition"""
    type: ContentBindingType
    required: bool = False
    default: Optional[Union[str, list, dict]] = None
    placeholder: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


class ComponentConfig(BaseModel):
    """Configuration options for a component"""
    background: Optional[Dict[str, Any]] = None
    alignment: Optional[str] = None
    columns: Optional[int] = None
    layout: Optional[str] = None
    spacing: Optional[str] = "normal"
    animation: Optional[bool] = False


class ComponentVariation(BaseModel):
    """Represents a single variation of a component"""
    name: str
    description: str
    html: str
    css: str
    config: Dict[str, Any]
    content_bindings: Dict[str, Dict[str, Any]]
    preview_image: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @validator('html')
    def validate_html(cls, v):
        """Ensure HTML contains proper structure"""
        if not v or len(v.strip()) == 0:
            raise ValueError("HTML cannot be empty")
        return v

    @validator('content_bindings')
    def validate_bindings(cls, v):
        """Ensure all content bindings in HTML are defined"""
        # This is a basic check - production would be more thorough
        return v


class ComponentLibrary:
    """Main component library class"""
    
    def __init__(self):
        self._components = self._initialize_components()
    
    def get_component(
        self, 
        component_type: ComponentType, 
        variation: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific component variation"""
        if component_type.value not in self._components:
            return None
        
        variations = self._components[component_type.value]
        return variations.get(variation)
    
    def get_all_variations(
        self, 
        component_type: ComponentType
    ) -> Dict[str, Dict[str, Any]]:
        """Get all variations of a component type"""
        return self._components.get(component_type.value, {})
    
    def list_component_types(self) -> List[str]:
        """List all available component types"""
        return list(self._components.keys())
    
    def validate_component_structure(
        self, 
        component: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate component structure"""
        required_fields = ['html', 'css', 'config', 'content_bindings']
        
        for field in required_fields:
            if field not in component:
                return False, f"Missing required field: {field}"
        
        # Validate HTML placeholders match content_bindings
        html = component['html']
        bindings = component['content_bindings']
        
        placeholders = re.findall(r'\{\{(\w+)\}\}', html)
        for placeholder in placeholders:
            if placeholder not in bindings:
                return False, f"Placeholder {{{{ {placeholder} }}}} not defined in content_bindings"
        
        return True, None
    
    def render_component(
        self, 
        component: Dict[str, Any], 
        content: Dict[str, Any]
    ) -> str:
        """Render a component with actual content"""
        html = component['html']
        
        # Replace placeholders with content
        for key, value in content.items():
            if isinstance(value, str):
                html = html.replace(f"{{{{{key}}}}}", value)
            elif isinstance(value, list):
                # Handle array content (e.g., services, testimonials)
                html = self._render_array_content(html, key, value)
        
        return html
    
    def _render_array_content(
        self, 
        html: str, 
        key: str, 
        items: List[Dict[str, Any]]
    ) -> str:
        """Render array content like services or testimonials"""
        # Find the repeated element pattern
        pattern = rf'<!-- {key}_item_start -->(.*?)<!-- {key}_item_end -->'
        match = re.search(pattern, html, re.DOTALL)
        
        if not match:
            return html
        
        template = match.group(1)
        rendered_items = []
        
        for item in items:
            item_html = template
            for item_key, item_value in item.items():
                item_html = item_html.replace(f"{{{{{key}.{item_key}}}}}", str(item_value))
            rendered_items.append(item_html)
        
        # Replace the entire section with rendered items
        return re.sub(pattern, ''.join(rendered_items), html, flags=re.DOTALL)
    
    def _initialize_components(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the component library with all definitions"""
        return {
            ComponentType.HEADER.value: self._create_header_components(),
            ComponentType.HERO.value: self._create_hero_components(),
            ComponentType.SERVICES.value: self._create_services_components(),
            ComponentType.ABOUT.value: self._create_about_components(),
            ComponentType.CTA.value: self._create_cta_components(),
            ComponentType.CONTACT.value: self._create_contact_components(),
            ComponentType.TESTIMONIALS.value: self._create_testimonials_components(),
            ComponentType.FOOTER.value: self._create_footer_components(),
        }
    
    def _create_header_components(self) -> Dict[str, Dict[str, Any]]:
        """Create header component variations"""
        return {
            "centered-logo": {
                "name": "Centered Logo Header",
                "description": "Header with centered logo and navigation menu below",
                "html": """<header class="header header--centered">
    <div class="header__container">
        <div class="header__logo-wrapper">
            <a href="/" class="header__logo">
                <img src="{{logo_url}}" alt="{{business_name}}" class="header__logo-img" />
            </a>
        </div>
        <nav class="header__nav" role="navigation">
            <ul class="header__nav-list">
                <!-- nav_item_start -->
                <li class="header__nav-item">
                    <a href="{{nav_items.url}}" class="header__nav-link">{{nav_items.label}}</a>
                </li>
                <!-- nav_item_end -->
            </ul>
        </nav>
    </div>
</header>""",
                "css": """.header {
    background: var(--color-background, #ffffff);
    border-bottom: 1px solid var(--color-border, #e5e7eb);
    padding: var(--spacing-md, 1.5rem) 0;
    position: sticky;
    top: 0;
    z-index: 1000;
}

.header__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
}

.header--centered .header__logo-wrapper {
    text-align: center;
    margin-bottom: var(--spacing-sm, 1rem);
}

.header__logo {
    display: inline-block;
    text-decoration: none;
}

.header__logo-img {
    height: 40px;
    width: auto;
}

.header__nav {
    text-align: center;
}

.header__nav-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    justify-content: center;
    gap: var(--spacing-md, 1.5rem);
    flex-wrap: wrap;
}

.header__nav-link {
    color: var(--color-text, #1f2937);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s ease;
}

.header__nav-link:hover {
    color: var(--color-primary, #6366f1);
}

@media (max-width: 768px) {
    .header__nav-list {
        gap: var(--spacing-sm, 1rem);
    }
}""",
                "config": {
                    "sticky": True,
                    "alignment": "center",
                    "showBorder": True
                },
                "content_bindings": {
                    "logo_url": {
                        "type": "image",
                        "required": True,
                        "placeholder": "Logo URL"
                    },
                    "business_name": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Business Name"
                    },
                    "nav_items": {
                        "type": "array",
                        "required": True,
                        "itemSchema": {
                            "label": "string",
                            "url": "string"
                        },
                        "default": [
                            {"label": "Home", "url": "#home"},
                            {"label": "Services", "url": "#services"},
                            {"label": "About", "url": "#about"},
                            {"label": "Contact", "url": "#contact"}
                        ]
                    }
                },
                "tags": ["header", "centered", "navigation"]
            },
            "logo-left": {
                "name": "Logo Left Header",
                "description": "Header with logo on left and right-aligned navigation menu",
                "html": """<header class="header header--logo-left">
    <div class="header__container">
        <a href="/" class="header__logo">
            <img src="{{logo_url}}" alt="{{business_name}}" class="header__logo-img" />
        </a>
        <nav class="header__nav" role="navigation">
            <ul class="header__nav-list">
                <!-- nav_item_start -->
                <li class="header__nav-item">
                    <a href="{{nav_items.url}}" class="header__nav-link">{{nav_items.label}}</a>
                </li>
                <!-- nav_item_end -->
            </ul>
        </nav>
    </div>
</header>""",
                "css": """.header {
    background: var(--color-background, #ffffff);
    border-bottom: 1px solid var(--color-border, #e5e7eb);
    padding: var(--spacing-md, 1.5rem) 0;
    position: sticky;
    top: 0;
    z-index: 1000;
}

.header__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.header__logo {
    text-decoration: none;
    flex-shrink: 0;
}

.header__logo-img {
    height: 40px;
    width: auto;
}

.header__nav-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    gap: var(--spacing-lg, 2rem);
    align-items: center;
}

.header__nav-link {
    color: var(--color-text, #1f2937);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s ease;
    white-space: nowrap;
}

.header__nav-link:hover {
    color: var(--color-primary, #6366f1);
}

@media (max-width: 768px) {
    .header__nav-list {
        gap: var(--spacing-md, 1.5rem);
    }
}""",
                "config": {
                    "sticky": True,
                    "alignment": "left",
                    "showBorder": True
                },
                "content_bindings": {
                    "logo_url": {
                        "type": "image",
                        "required": True,
                        "placeholder": "Logo URL"
                    },
                    "business_name": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Business Name"
                    },
                    "nav_items": {
                        "type": "array",
                        "required": True,
                        "itemSchema": {
                            "label": "string",
                            "url": "string"
                        },
                        "default": [
                            {"label": "Home", "url": "#home"},
                            {"label": "Services", "url": "#services"},
                            {"label": "About", "url": "#about"},
                            {"label": "Contact", "url": "#contact"}
                        ]
                    }
                },
                "tags": ["header", "left-aligned", "navigation"]
            }
        }
    
    def _create_hero_components(self) -> Dict[str, Dict[str, Any]]:
        """Create hero component variations"""
        return {
            "centered": {
                "name": "Centered Hero",
                "description": "Full-width hero with centered content and optional background",
                "html": """<section class="hero hero--centered" style="{{background_style}}">
    <div class="hero__overlay"></div>
    <div class="hero__container">
        <div class="hero__content">
            <h1 class="hero__headline">{{headline}}</h1>
            <p class="hero__subheadline">{{subheadline}}</p>
            <div class="hero__cta-group">
                <a href="{{cta_url}}" class="hero__cta hero__cta--primary">{{cta_text}}</a>
                <a href="{{secondary_cta_url}}" class="hero__cta hero__cta--secondary">{{secondary_cta_text}}</a>
            </div>
        </div>
    </div>
</section>""",
                "css": """.hero {
    position: relative;
    min-height: var(--hero-min-height, 100vh);
    display: flex;
    align-items: center;
    justify-content: center;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

.hero__overlay {
    position: absolute;
    inset: 0;
    background: var(--hero-overlay-color, rgba(0, 0, 0, 0.4));
    opacity: var(--hero-overlay-opacity, 1);
}

.hero__container {
    position: relative;
    z-index: 1;
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: var(--spacing-xl, 3rem) var(--spacing-md, 1.5rem);
    width: 100%;
}

.hero--centered .hero__content {
    text-align: center;
    max-width: 800px;
    margin: 0 auto;
}

.hero__headline {
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 700;
    line-height: 1.2;
    color: var(--hero-text-color, #ffffff);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.hero__subheadline {
    font-size: clamp(1.125rem, 2vw, 1.5rem);
    line-height: 1.6;
    color: var(--hero-text-color, #ffffff);
    opacity: 0.95;
    margin: 0 0 var(--spacing-lg, 2rem);
}

.hero__cta-group {
    display: flex;
    gap: var(--spacing-md, 1.5rem);
    justify-content: center;
    flex-wrap: wrap;
}

.hero__cta {
    display: inline-block;
    padding: 1rem 2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
}

.hero__cta--primary {
    background: var(--color-primary, #6366f1);
    color: #ffffff;
}

.hero__cta--primary:hover {
    background: var(--color-primary-dark, #4f46e5);
    transform: translateY(-2px);
}

.hero__cta--secondary {
    background: transparent;
    color: var(--hero-text-color, #ffffff);
    border: 2px solid currentColor;
}

.hero__cta--secondary:hover {
    background: rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
    .hero {
        min-height: 80vh;
    }
    
    .hero__cta-group {
        flex-direction: column;
        align-items: center;
    }
    
    .hero__cta {
        width: 100%;
        max-width: 300px;
        text-align: center;
    }
}""",
                "config": {
                    "background": {
                        "type": "image",
                        "overlay": True,
                        "overlayOpacity": 0.4
                    },
                    "contentAlignment": "center",
                    "verticalAlignment": "center",
                    "minHeight": "100vh",
                    "textColor": "light"
                },
                "content_bindings": {
                    "headline": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Your Compelling Headline"
                    },
                    "subheadline": {
                        "type": "text",
                        "required": True,
                        "placeholder": "A brief description of what you offer"
                    },
                    "cta_text": {
                        "type": "text",
                        "required": True,
                        "default": "Get Started"
                    },
                    "cta_url": {
                        "type": "url",
                        "required": False,
                        "default": "#contact"
                    },
                    "secondary_cta_text": {
                        "type": "text",
                        "required": False,
                        "default": "Learn More"
                    },
                    "secondary_cta_url": {
                        "type": "url",
                        "required": False,
                        "default": "#services"
                    },
                    "background_image": {
                        "type": "image",
                        "required": False
                    },
                    "background_style": {
                        "type": "text",
                        "required": False,
                        "default": "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
                    }
                },
                "tags": ["hero", "centered", "full-width"]
            },
            "split": {
                "name": "Split Hero",
                "description": "Hero with content on left and image/media on right",
                "html": """<section class="hero hero--split">
    <div class="hero__container">
        <div class="hero__content">
            <h1 class="hero__headline">{{headline}}</h1>
            <p class="hero__subheadline">{{subheadline}}</p>
            <div class="hero__cta-group">
                <a href="{{cta_url}}" class="hero__cta hero__cta--primary">{{cta_text}}</a>
            </div>
        </div>
        <div class="hero__media">
            <img src="{{hero_image}}" alt="{{hero_image_alt}}" class="hero__image" />
        </div>
    </div>
</section>""",
                "css": """.hero {
    padding: var(--spacing-xl, 3rem) 0;
    background: var(--color-background, #ffffff);
}

.hero__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-xl, 3rem);
    align-items: center;
    min-height: 600px;
}

.hero__content {
    padding: var(--spacing-lg, 2rem) 0;
}

.hero__headline {
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.hero__subheadline {
    font-size: clamp(1rem, 2vw, 1.25rem);
    line-height: 1.6;
    color: var(--color-text, #6b7280);
    margin: 0 0 var(--spacing-lg, 2rem);
}

.hero__cta-group {
    display: flex;
    gap: var(--spacing-md, 1.5rem);
    flex-wrap: wrap;
}

.hero__cta {
    display: inline-block;
    padding: 1rem 2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
}

.hero__cta--primary {
    background: var(--color-primary, #6366f1);
    color: #ffffff;
}

.hero__cta--primary:hover {
    background: var(--color-primary-dark, #4f46e5);
    transform: translateY(-2px);
}

.hero__media {
    position: relative;
    width: 100%;
    height: 100%;
}

.hero__image {
    width: 100%;
    height: auto;
    border-radius: 1rem;
    object-fit: cover;
}

@media (max-width: 768px) {
    .hero__container {
        grid-template-columns: 1fr;
        gap: var(--spacing-lg, 2rem);
        min-height: auto;
    }
    
    .hero__media {
        order: -1;
    }
}""",
                "config": {
                    "layout": "split",
                    "contentAlignment": "left",
                    "imagePosition": "right"
                },
                "content_bindings": {
                    "headline": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Your Business Headline"
                    },
                    "subheadline": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Describe what makes you unique"
                    },
                    "cta_text": {
                        "type": "text",
                        "required": True,
                        "default": "Get Started"
                    },
                    "cta_url": {
                        "type": "url",
                        "required": False,
                        "default": "#contact"
                    },
                    "hero_image": {
                        "type": "image",
                        "required": True,
                        "placeholder": "Hero image URL"
                    },
                    "hero_image_alt": {
                        "type": "text",
                        "required": False,
                        "default": "Hero image"
                    }
                },
                "tags": ["hero", "split", "two-column"]
            },
            "full-width": {
                "name": "Full Width Hero",
                "description": "Minimalist full-width hero with large typography",
                "html": """<section class="hero hero--full-width">
    <div class="hero__container">
        <h1 class="hero__headline">{{headline}}</h1>
        <p class="hero__subheadline">{{subheadline}}</p>
        <a href="{{cta_url}}" class="hero__cta">{{cta_text}}</a>
    </div>
</section>""",
                "css": """.hero {
    min-height: var(--hero-min-height, 75vh);
    background: var(--color-background, #f9fafb);
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.hero__container {
    max-width: 900px;
    margin: 0 auto;
    padding: var(--spacing-xl, 3rem) var(--spacing-md, 1.5rem);
}

.hero__headline {
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    font-weight: 800;
    line-height: 1.1;
    color: var(--color-heading, #111827);
    margin: 0 0 var(--spacing-lg, 2rem);
    letter-spacing: -0.02em;
}

.hero__subheadline {
    font-size: clamp(1.125rem, 2vw, 1.5rem);
    line-height: 1.6;
    color: var(--color-text, #6b7280);
    margin: 0 0 var(--spacing-xl, 3rem);
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
}

.hero__cta {
    display: inline-block;
    padding: 1.25rem 3rem;
    background: var(--color-primary, #6366f1);
    color: #ffffff;
    border-radius: 0.75rem;
    font-size: 1.125rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
    box-shadow: 0 4px 6px rgba(99, 102, 241, 0.2);
}

.hero__cta:hover {
    background: var(--color-primary-dark, #4f46e5);
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(99, 102, 241, 0.3);
}

@media (max-width: 768px) {
    .hero {
        min-height: 60vh;
    }
}""",
                "config": {
                    "layout": "full-width",
                    "contentAlignment": "center",
                    "minHeight": "75vh",
                    "style": "minimalist"
                },
                "content_bindings": {
                    "headline": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Make it bold and memorable"
                    },
                    "subheadline": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Supporting text that adds context"
                    },
                    "cta_text": {
                        "type": "text",
                        "required": True,
                        "default": "Start Now"
                    },
                    "cta_url": {
                        "type": "url",
                        "required": False,
                        "default": "#contact"
                    }
                },
                "tags": ["hero", "full-width", "minimalist"]
            }
        }
    
    def _create_services_components(self) -> Dict[str, Dict[str, Any]]:
        """Create services component variations"""
        return {
            "three-column": {
                "name": "Three Column Services",
                "description": "Service cards in a 3-column grid layout",
                "html": """<section class="services">
    <div class="services__container">
        <div class="services__header">
            <h2 class="services__title">{{section_title}}</h2>
            <p class="services__description">{{section_description}}</p>
        </div>
        <div class="services__grid">
            <!-- services_item_start -->
            <div class="services__card">
                <div class="services__icon">{{services.icon}}</div>
                <h3 class="services__card-title">{{services.title}}</h3>
                <p class="services__card-description">{{services.description}}</p>
            </div>
            <!-- services_item_end -->
        </div>
    </div>
</section>""",
                "css": """.services {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #ffffff);
}

.services__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
}

.services__header {
    text-align: center;
    margin-bottom: var(--spacing-xl, 3rem);
}

.services__title {
    font-size: clamp(2rem, 4vw, 2.5rem);
    font-weight: 700;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.services__description {
    font-size: 1.125rem;
    color: var(--color-text, #6b7280);
    max-width: 600px;
    margin: 0 auto;
}

.services__grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--spacing-lg, 2rem);
}

.services__card {
    padding: var(--spacing-lg, 2rem);
    background: var(--color-card-background, #f9fafb);
    border-radius: 1rem;
    transition: all 0.3s ease;
}

.services__card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.services__icon {
    font-size: 2.5rem;
    margin-bottom: var(--spacing-md, 1.5rem);
}

.services__card-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-sm, 1rem);
}

.services__card-description {
    font-size: 1rem;
    line-height: 1.6;
    color: var(--color-text, #6b7280);
    margin: 0;
}

@media (max-width: 768px) {
    .services__grid {
        grid-template-columns: 1fr;
    }
}""",
                "config": {
                    "columns": 3,
                    "cardStyle": "elevated",
                    "iconStyle": "outlined"
                },
                "content_bindings": {
                    "section_title": {
                        "type": "text",
                        "required": True,
                        "default": "Our Services"
                    },
                    "section_description": {
                        "type": "text",
                        "required": False,
                        "placeholder": "What we offer"
                    },
                    "services": {
                        "type": "array",
                        "required": True,
                        "itemSchema": {
                            "icon": "string",
                            "title": "string",
                            "description": "string"
                        },
                        "default": []
                    }
                },
                "tags": ["services", "grid", "three-column"]
            },
            "two-column": {
                "name": "Two Column Services",
                "description": "Service cards in a 2-column grid with larger cards",
                "html": """<section class="services services--two-col">
    <div class="services__container">
        <div class="services__header">
            <h2 class="services__title">{{section_title}}</h2>
            <p class="services__description">{{section_description}}</p>
        </div>
        <div class="services__grid services__grid--two-col">
            <!-- services_item_start -->
            <div class="services__card">
                <div class="services__icon">{{services.icon}}</div>
                <h3 class="services__card-title">{{services.title}}</h3>
                <p class="services__card-description">{{services.description}}</p>
            </div>
            <!-- services_item_end -->
        </div>
    </div>
</section>""",
                "css": """.services {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #f9fafb);
}

.services__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
}

.services__header {
    text-align: center;
    margin-bottom: var(--spacing-xl, 3rem);
}

.services__title {
    font-size: clamp(2rem, 4vw, 2.5rem);
    font-weight: 700;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.services__description {
    font-size: 1.125rem;
    color: var(--color-text, #6b7280);
    max-width: 600px;
    margin: 0 auto;
}

.services__grid--two-col {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: var(--spacing-xl, 3rem);
}

.services__card {
    padding: var(--spacing-xl, 3rem);
    background: var(--color-card-background, #ffffff);
    border-radius: 1rem;
    border: 1px solid var(--color-border, #e5e7eb);
    transition: all 0.3s ease;
}

.services__card:hover {
    border-color: var(--color-primary, #6366f1);
    box-shadow: 0 8px 16px rgba(99, 102, 241, 0.1);
}

.services__icon {
    font-size: 3rem;
    margin-bottom: var(--spacing-md, 1.5rem);
    color: var(--color-primary, #6366f1);
}

.services__card-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.services__card-description {
    font-size: 1.0625rem;
    line-height: 1.7;
    color: var(--color-text, #6b7280);
    margin: 0;
}

@media (max-width: 768px) {
    .services__grid--two-col {
        grid-template-columns: 1fr;
    }
}""",
                "config": {
                    "columns": 2,
                    "cardStyle": "bordered",
                    "iconStyle": "solid"
                },
                "content_bindings": {
                    "section_title": {
                        "type": "text",
                        "required": True,
                        "default": "What We Do"
                    },
                    "section_description": {
                        "type": "text",
                        "required": False,
                        "placeholder": "Our expertise"
                    },
                    "services": {
                        "type": "array",
                        "required": True,
                        "itemSchema": {
                            "icon": "string",
                            "title": "string",
                            "description": "string"
                        }
                    }
                },
                "tags": ["services", "grid", "two-column"]
            },
            "list": {
                "name": "Services List",
                "description": "Simple list layout for services",
                "html": """<section class="services services--list">
    <div class="services__container">
        <h2 class="services__title">{{section_title}}</h2>
        <div class="services__list">
            <!-- services_item_start -->
            <div class="services__item">
                <div class="services__item-icon">{{services.icon}}</div>
                <div class="services__item-content">
                    <h3 class="services__item-title">{{services.title}}</h3>
                    <p class="services__item-description">{{services.description}}</p>
                </div>
            </div>
            <!-- services_item_end -->
        </div>
    </div>
</section>""",
                "css": """.services {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #ffffff);
}

.services__container {
    max-width: var(--container-max-width, 900px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
}

.services__title {
    font-size: clamp(2rem, 4vw, 2.5rem);
    font-weight: 700;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-xl, 3rem);
    text-align: center;
}

.services__list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg, 2rem);
}

.services__item {
    display: flex;
    gap: var(--spacing-md, 1.5rem);
    padding: var(--spacing-lg, 2rem);
    background: var(--color-card-background, #f9fafb);
    border-radius: 0.75rem;
}

.services__item-icon {
    font-size: 2rem;
    color: var(--color-primary, #6366f1);
    flex-shrink: 0;
}

.services__item-content {
    flex: 1;
}

.services__item-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-sm, 1rem);
}

.services__item-description {
    font-size: 1rem;
    line-height: 1.6;
    color: var(--color-text, #6b7280);
    margin: 0;
}

@media (max-width: 768px) {
    .services__item {
        flex-direction: column;
    }
}""",
                "config": {
                    "layout": "list",
                    "iconPosition": "left"
                },
                "content_bindings": {
                    "section_title": {
                        "type": "text",
                        "required": True,
                        "default": "Services"
                    },
                    "services": {
                        "type": "array",
                        "required": True,
                        "itemSchema": {
                            "icon": "string",
                            "title": "string",
                            "description": "string"
                        }
                    }
                },
                "tags": ["services", "list", "vertical"]
            }
        }
    
    def _create_about_components(self) -> Dict[str, Dict[str, Any]]:
        """Create about section component variations"""
        return {
            "two-column": {
                "name": "Two Column About",
                "description": "About section with image on one side and content on the other",
                "html": """<section class="about">
    <div class="about__container">
        <div class="about__image-wrapper">
            <img src="{{about_image}}" alt="{{about_image_alt}}" class="about__image" />
        </div>
        <div class="about__content">
            <h2 class="about__title">{{section_title}}</h2>
            <p class="about__text">{{about_text}}</p>
            <div class="about__highlights">
                <!-- highlights_item_start -->
                <div class="about__highlight">
                    <div class="about__highlight-value">{{highlights.value}}</div>
                    <div class="about__highlight-label">{{highlights.label}}</div>
                </div>
                <!-- highlights_item_end -->
            </div>
        </div>
    </div>
</section>""",
                "css": """.about {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #ffffff);
}

.about__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-xl, 3rem);
    align-items: center;
}

.about__image-wrapper {
    position: relative;
    width: 100%;
    height: 500px;
}

.about__image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 1rem;
}

.about__title {
    font-size: clamp(2rem, 4vw, 2.5rem);
    font-weight: 700;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.about__text {
    font-size: 1.0625rem;
    line-height: 1.7;
    color: var(--color-text, #6b7280);
    margin: 0 0 var(--spacing-lg, 2rem);
}

.about__highlights {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: var(--spacing-md, 1.5rem);
}

.about__highlight {
    text-align: center;
    padding: var(--spacing-md, 1.5rem);
    background: var(--color-card-background, #f9fafb);
    border-radius: 0.5rem;
}

.about__highlight-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-primary, #6366f1);
    margin-bottom: var(--spacing-sm, 0.5rem);
}

.about__highlight-label {
    font-size: 0.875rem;
    color: var(--color-text, #6b7280);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

@media (max-width: 768px) {
    .about__container {
        grid-template-columns: 1fr;
    }
    
    .about__image-wrapper {
        height: 300px;
    }
}""",
                "config": {
                    "layout": "two-column",
                    "imagePosition": "left"
                },
                "content_bindings": {
                    "section_title": {
                        "type": "text",
                        "required": True,
                        "default": "About Us"
                    },
                    "about_text": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Tell your story"
                    },
                    "about_image": {
                        "type": "image",
                        "required": True,
                        "placeholder": "About image URL"
                    },
                    "about_image_alt": {
                        "type": "text",
                        "required": False,
                        "default": "About"
                    },
                    "highlights": {
                        "type": "array",
                        "required": False,
                        "itemSchema": {
                            "value": "string",
                            "label": "string"
                        }
                    }
                },
                "tags": ["about", "two-column", "stats"]
            },
            "centered": {
                "name": "Centered About",
                "description": "Centered about section with focused content",
                "html": """<section class="about about--centered">
    <div class="about__container">
        <h2 class="about__title">{{section_title}}</h2>
        <p class="about__text">{{about_text}}</p>
        <div class="about__features">
            <!-- features_item_start -->
            <div class="about__feature">
                <div class="about__feature-icon">{{features.icon}}</div>
                <h3 class="about__feature-title">{{features.title}}</h3>
                <p class="about__feature-description">{{features.description}}</p>
            </div>
            <!-- features_item_end -->
        </div>
    </div>
</section>""",
                "css": """.about {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #f9fafb);
}

.about__container {
    max-width: 900px;
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
    text-align: center;
}

.about__title {
    font-size: clamp(2rem, 4vw, 2.5rem);
    font-weight: 700;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.about__text {
    font-size: 1.125rem;
    line-height: 1.7;
    color: var(--color-text, #6b7280);
    margin: 0 0 var(--spacing-xl, 3rem);
}

.about__features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-lg, 2rem);
    text-align: center;
}

.about__feature-icon {
    font-size: 2rem;
    margin-bottom: var(--spacing-md, 1.5rem);
}

.about__feature-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-sm, 1rem);
}

.about__feature-description {
    font-size: 0.9375rem;
    line-height: 1.6;
    color: var(--color-text, #6b7280);
    margin: 0;
}""",
                "config": {
                    "layout": "centered",
                    "textAlign": "center"
                },
                "content_bindings": {
                    "section_title": {
                        "type": "text",
                        "required": True,
                        "default": "Our Story"
                    },
                    "about_text": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Share your journey"
                    },
                    "features": {
                        "type": "array",
                        "required": False,
                        "itemSchema": {
                            "icon": "string",
                            "title": "string",
                            "description": "string"
                        }
                    }
                },
                "tags": ["about", "centered", "features"]
            }
        }
    
    def _create_cta_components(self) -> Dict[str, Dict[str, Any]]:
        """Create CTA component variations"""
        return {
            "banner": {
                "name": "CTA Banner",
                "description": "Full-width banner call-to-action",
                "html": """<section class="cta cta--banner">
    <div class="cta__container">
        <h2 class="cta__title">{{cta_title}}</h2>
        <p class="cta__text">{{cta_text}}</p>
        <a href="{{cta_url}}" class="cta__button">{{cta_button_text}}</a>
    </div>
</section>""",
                "css": """.cta {
    padding: var(--spacing-2xl, 5rem) 0;
    background: linear-gradient(135deg, var(--color-primary, #6366f1) 0%, var(--color-primary-dark, #4f46e5) 100%);
    color: #ffffff;
}

.cta__container {
    max-width: var(--container-max-width, 800px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
    text-align: center;
}

.cta__title {
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 700;
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.cta__text {
    font-size: 1.25rem;
    line-height: 1.6;
    margin: 0 0 var(--spacing-lg, 2rem);
    opacity: 0.95;
}

.cta__button {
    display: inline-block;
    padding: 1rem 2.5rem;
    background: #ffffff;
    color: var(--color-primary, #6366f1);
    border-radius: 0.5rem;
    font-size: 1.125rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
}

.cta__button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}""",
                "config": {
                    "style": "banner",
                    "background": "gradient"
                },
                "content_bindings": {
                    "cta_title": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Ready to get started?"
                    },
                    "cta_text": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Join thousands of satisfied customers"
                    },
                    "cta_button_text": {
                        "type": "text",
                        "required": True,
                        "default": "Get Started Today"
                    },
                    "cta_url": {
                        "type": "url",
                        "required": False,
                        "default": "#contact"
                    }
                },
                "tags": ["cta", "banner", "full-width"]
            },
            "centered": {
                "name": "Centered CTA",
                "description": "Simple centered call-to-action box",
                "html": """<section class="cta cta--centered">
    <div class="cta__container">
        <div class="cta__box">
            <h2 class="cta__title">{{cta_title}}</h2>
            <p class="cta__text">{{cta_text}}</p>
            <div class="cta__buttons">
                <a href="{{cta_url}}" class="cta__button cta__button--primary">{{cta_button_text}}</a>
                <a href="{{secondary_cta_url}}" class="cta__button cta__button--secondary">{{secondary_cta_text}}</a>
            </div>
        </div>
    </div>
</section>""",
                "css": """.cta {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #f9fafb);
}

.cta__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
}

.cta__box {
    max-width: 700px;
    margin: 0 auto;
    padding: var(--spacing-xl, 3rem);
    background: #ffffff;
    border-radius: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    text-align: center;
}

.cta__title {
    font-size: clamp(1.75rem, 4vw, 2.25rem);
    font-weight: 700;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.cta__text {
    font-size: 1.125rem;
    line-height: 1.6;
    color: var(--color-text, #6b7280);
    margin: 0 0 var(--spacing-lg, 2rem);
}

.cta__buttons {
    display: flex;
    gap: var(--spacing-md, 1.5rem);
    justify-content: center;
    flex-wrap: wrap;
}

.cta__button {
    display: inline-block;
    padding: 1rem 2rem;
    border-radius: 0.5rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
}

.cta__button--primary {
    background: var(--color-primary, #6366f1);
    color: #ffffff;
}

.cta__button--primary:hover {
    background: var(--color-primary-dark, #4f46e5);
}

.cta__button--secondary {
    background: transparent;
    color: var(--color-primary, #6366f1);
    border: 2px solid currentColor;
}

.cta__button--secondary:hover {
    background: var(--color-primary, #6366f1);
    color: #ffffff;
}""",
                "config": {
                    "style": "centered",
                    "background": "light"
                },
                "content_bindings": {
                    "cta_title": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Take the next step"
                    },
                    "cta_text": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Let's work together"
                    },
                    "cta_button_text": {
                        "type": "text",
                        "required": True,
                        "default": "Contact Us"
                    },
                    "cta_url": {
                        "type": "url",
                        "required": False,
                        "default": "#contact"
                    },
                    "secondary_cta_text": {
                        "type": "text",
                        "required": False,
                        "default": "Learn More"
                    },
                    "secondary_cta_url": {
                        "type": "url",
                        "required": False,
                        "default": "#about"
                    }
                },
                "tags": ["cta", "centered", "boxed"]
            }
        }
    
    def _create_contact_components(self) -> Dict[str, Dict[str, Any]]:
        """Create contact section component variations"""
        return {
            "form-only": {
                "name": "Contact Form Only",
                "description": "Simple contact form centered on page",
                "html": """<section class="contact">
    <div class="contact__container">
        <div class="contact__header">
            <h2 class="contact__title">{{section_title}}</h2>
            <p class="contact__description">{{section_description}}</p>
        </div>
        <form class="contact__form" action="{{form_action}}" method="POST">
            <div class="contact__form-group">
                <label for="name" class="contact__label">Name</label>
                <input type="text" id="name" name="name" class="contact__input" required />
            </div>
            <div class="contact__form-group">
                <label for="email" class="contact__label">Email</label>
                <input type="email" id="email" name="email" class="contact__input" required />
            </div>
            <div class="contact__form-group">
                <label for="message" class="contact__label">Message</label>
                <textarea id="message" name="message" rows="5" class="contact__textarea" required></textarea>
            </div>
            <button type="submit" class="contact__submit">{{submit_button_text}}</button>
        </form>
    </div>
</section>""",
                "css": """.contact {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #ffffff);
}

.contact__container {
    max-width: 600px;
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
}

.contact__header {
    text-align: center;
    margin-bottom: var(--spacing-xl, 3rem);
}

.contact__title {
    font-size: clamp(2rem, 4vw, 2.5rem);
    font-weight: 700;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.contact__description {
    font-size: 1.125rem;
    color: var(--color-text, #6b7280);
}

.contact__form {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 1.5rem);
}

.contact__form-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm, 0.5rem);
}

.contact__label {
    font-weight: 500;
    color: var(--color-heading, #1f2937);
}

.contact__input,
.contact__textarea {
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-border, #d1d5db);
    border-radius: 0.5rem;
    font-size: 1rem;
    font-family: inherit;
    transition: border-color 0.2s ease;
}

.contact__input:focus,
.contact__textarea:focus {
    outline: none;
    border-color: var(--color-primary, #6366f1);
}

.contact__submit {
    padding: 1rem 2rem;
    background: var(--color-primary, #6366f1);
    color: #ffffff;
    border: none;
    border-radius: 0.5rem;
    font-size: 1.125rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.contact__submit:hover {
    background: var(--color-primary-dark, #4f46e5);
    transform: translateY(-2px);
}""",
                "config": {
                    "layout": "form-only",
                    "formFields": ["name", "email", "message"]
                },
                "content_bindings": {
                    "section_title": {
                        "type": "text",
                        "required": True,
                        "default": "Get in Touch"
                    },
                    "section_description": {
                        "type": "text",
                        "required": False,
                        "placeholder": "We'd love to hear from you"
                    },
                    "submit_button_text": {
                        "type": "text",
                        "required": True,
                        "default": "Send Message"
                    },
                    "form_action": {
                        "type": "url",
                        "required": False,
                        "default": "/api/contact"
                    }
                },
                "tags": ["contact", "form", "simple"]
            },
            "split-info": {
                "name": "Split Contact with Info",
                "description": "Contact form on one side, contact information on the other",
                "html": """<section class="contact contact--split">
    <div class="contact__container">
        <div class="contact__info">
            <h2 class="contact__title">{{section_title}}</h2>
            <p class="contact__description">{{section_description}}</p>
            <div class="contact__details">
                <div class="contact__detail">
                    <div class="contact__detail-icon">📧</div>
                    <div class="contact__detail-content">
                        <div class="contact__detail-label">Email</div>
                        <a href="mailto:{{business_email}}" class="contact__detail-value">{{business_email}}</a>
                    </div>
                </div>
                <div class="contact__detail">
                    <div class="contact__detail-icon">📱</div>
                    <div class="contact__detail-content">
                        <div class="contact__detail-label">Phone</div>
                        <a href="tel:{{business_phone}}" class="contact__detail-value">{{business_phone}}</a>
                    </div>
                </div>
                <div class="contact__detail">
                    <div class="contact__detail-icon">💬</div>
                    <div class="contact__detail-content">
                        <div class="contact__detail-label">WhatsApp</div>
                        <a href="https://wa.me/{{whatsapp_number}}" class="contact__detail-value" target="_blank">Chat on WhatsApp</a>
                    </div>
                </div>
            </div>
        </div>
        <form class="contact__form" action="{{form_action}}" method="POST">
            <div class="contact__form-group">
                <label for="name" class="contact__label">Name</label>
                <input type="text" id="name" name="name" class="contact__input" required />
            </div>
            <div class="contact__form-group">
                <label for="email" class="contact__label">Email</label>
                <input type="email" id="email" name="email" class="contact__input" required />
            </div>
            <div class="contact__form-group">
                <label for="message" class="contact__label">Message</label>
                <textarea id="message" name="message" rows="5" class="contact__textarea" required></textarea>
            </div>
            <button type="submit" class="contact__submit">{{submit_button_text}}</button>
        </form>
    </div>
</section>""",
                "css": """.contact {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #f9fafb);
}

.contact__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-xl, 3rem);
}

.contact__info {
    padding: var(--spacing-xl, 3rem);
    background: var(--color-primary, #6366f1);
    color: #ffffff;
    border-radius: 1rem;
}

.contact__title {
    font-size: clamp(2rem, 4vw, 2.5rem);
    font-weight: 700;
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.contact__description {
    font-size: 1.125rem;
    line-height: 1.6;
    margin: 0 0 var(--spacing-xl, 3rem);
    opacity: 0.95;
}

.contact__details {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg, 2rem);
}

.contact__detail {
    display: flex;
    gap: var(--spacing-md, 1.5rem);
    align-items: flex-start;
}

.contact__detail-icon {
    font-size: 1.5rem;
}

.contact__detail-label {
    font-size: 0.875rem;
    opacity: 0.8;
    margin-bottom: var(--spacing-xs, 0.25rem);
}

.contact__detail-value {
    color: #ffffff;
    text-decoration: none;
    font-weight: 500;
}

.contact__detail-value:hover {
    text-decoration: underline;
}

.contact__form {
    background: #ffffff;
    padding: var(--spacing-xl, 3rem);
    border-radius: 1rem;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 1.5rem);
}

.contact__form-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm, 0.5rem);
}

.contact__label {
    font-weight: 500;
    color: var(--color-heading, #1f2937);
}

.contact__input,
.contact__textarea {
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-border, #d1d5db);
    border-radius: 0.5rem;
    font-size: 1rem;
    font-family: inherit;
    transition: border-color 0.2s ease;
}

.contact__input:focus,
.contact__textarea:focus {
    outline: none;
    border-color: var(--color-primary, #6366f1);
}

.contact__submit {
    padding: 1rem 2rem;
    background: var(--color-primary, #6366f1);
    color: #ffffff;
    border: none;
    border-radius: 0.5rem;
    font-size: 1.125rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.contact__submit:hover {
    background: var(--color-primary-dark, #4f46e5);
}

@media (max-width: 768px) {
    .contact__container {
        grid-template-columns: 1fr;
    }
}""",
                "config": {
                    "layout": "split",
                    "showWhatsApp": True,
                    "formFields": ["name", "email", "message"]
                },
                "content_bindings": {
                    "section_title": {
                        "type": "text",
                        "required": True,
                        "default": "Contact Us"
                    },
                    "section_description": {
                        "type": "text",
                        "required": False,
                        "placeholder": "Reach out to us"
                    },
                    "business_email": {
                        "type": "email",
                        "required": True,
                        "placeholder": "your@email.com"
                    },
                    "business_phone": {
                        "type": "phone",
                        "required": False,
                        "placeholder": "+234 xxx xxx xxxx"
                    },
                    "whatsapp_number": {
                        "type": "phone",
                        "required": False,
                        "placeholder": "234xxxxxxxxxx"
                    },
                    "submit_button_text": {
                        "type": "text",
                        "required": True,
                        "default": "Send Message"
                    },
                    "form_action": {
                        "type": "url",
                        "required": False,
                        "default": "/api/contact"
                    }
                },
                "tags": ["contact", "split", "info", "whatsapp"]
            }
        }
    
    def _create_testimonials_components(self) -> Dict[str, Dict[str, Any]]:
        """Create testimonials component variations"""
        return {
            "cards": {
                "name": "Testimonial Cards",
                "description": "Grid of testimonial cards",
                "html": """<section class="testimonials">
    <div class="testimonials__container">
        <div class="testimonials__header">
            <h2 class="testimonials__title">{{section_title}}</h2>
            <p class="testimonials__description">{{section_description}}</p>
        </div>
        <div class="testimonials__grid">
            <!-- testimonials_item_start -->
            <div class="testimonials__card">
                <div class="testimonials__quote">{{testimonials.quote}}</div>
                <div class="testimonials__author">
                    <div class="testimonials__author-name">{{testimonials.author_name}}</div>
                    <div class="testimonials__author-title">{{testimonials.author_title}}</div>
                </div>
            </div>
            <!-- testimonials_item_end -->
        </div>
    </div>
</section>""",
                "css": """.testimonials {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #f9fafb);
}

.testimonials__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
}

.testimonials__header {
    text-align: center;
    margin-bottom: var(--spacing-xl, 3rem);
}

.testimonials__title {
    font-size: clamp(2rem, 4vw, 2.5rem);
    font-weight: 700;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.testimonials__description {
    font-size: 1.125rem;
    color: var(--color-text, #6b7280);
}

.testimonials__grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-lg, 2rem);
}

.testimonials__card {
    padding: var(--spacing-xl, 3rem);
    background: #ffffff;
    border-radius: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.testimonials__quote {
    font-size: 1.0625rem;
    line-height: 1.7;
    color: var(--color-text, #6b7280);
    margin-bottom: var(--spacing-lg, 2rem);
    font-style: italic;
}

.testimonials__quote::before {
    content: '"';
    font-size: 3rem;
    line-height: 0;
    color: var(--color-primary, #6366f1);
    opacity: 0.3;
}

.testimonials__author-name {
    font-weight: 600;
    color: var(--color-heading, #1f2937);
    margin-bottom: var(--spacing-xs, 0.25rem);
}

.testimonials__author-title {
    font-size: 0.875rem;
    color: var(--color-text, #6b7280);
}

@media (max-width: 768px) {
    .testimonials__grid {
        grid-template-columns: 1fr;
    }
}""",
                "config": {
                    "layout": "grid",
                    "cardStyle": "elevated"
                },
                "content_bindings": {
                    "section_title": {
                        "type": "text",
                        "required": True,
                        "default": "What Our Customers Say"
                    },
                    "section_description": {
                        "type": "text",
                        "required": False,
                        "placeholder": "Testimonials description"
                    },
                    "testimonials": {
                        "type": "array",
                        "required": True,
                        "itemSchema": {
                            "quote": "string",
                            "author_name": "string",
                            "author_title": "string"
                        }
                    }
                },
                "tags": ["testimonials", "cards", "grid"]
            },
            "simple": {
                "name": "Simple Testimonials",
                "description": "Minimal testimonial list",
                "html": """<section class="testimonials testimonials--simple">
    <div class="testimonials__container">
        <h2 class="testimonials__title">{{section_title}}</h2>
        <div class="testimonials__list">
            <!-- testimonials_item_start -->
            <div class="testimonials__item">
                <p class="testimonials__quote">{{testimonials.quote}}</p>
                <div class="testimonials__author">
                    <strong>{{testimonials.author_name}}</strong>, {{testimonials.author_title}}
                </div>
            </div>
            <!-- testimonials_item_end -->
        </div>
    </div>
</section>""",
                "css": """.testimonials {
    padding: var(--spacing-2xl, 5rem) 0;
    background: var(--color-background, #ffffff);
}

.testimonials__container {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
}

.testimonials__title {
    font-size: clamp(2rem, 4vw, 2.5rem);
    font-weight: 700;
    color: var(--color-heading, #1f2937);
    margin: 0 0 var(--spacing-xl, 3rem);
    text-align: center;
}

.testimonials__list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl, 3rem);
}

.testimonials__item {
    padding: var(--spacing-lg, 2rem);
    border-left: 4px solid var(--color-primary, #6366f1);
    background: var(--color-card-background, #f9fafb);
}

.testimonials__quote {
    font-size: 1.125rem;
    line-height: 1.7;
    color: var(--color-text, #374151);
    margin: 0 0 var(--spacing-md, 1.5rem);
    font-style: italic;
}

.testimonials__author {
    font-size: 0.9375rem;
    color: var(--color-text, #6b7280);
}""",
                "config": {
                    "layout": "list",
                    "style": "minimal"
                },
                "content_bindings": {
                    "section_title": {
                        "type": "text",
                        "required": True,
                        "default": "Testimonials"
                    },
                    "testimonials": {
                        "type": "array",
                        "required": True,
                        "itemSchema": {
                            "quote": "string",
                            "author_name": "string",
                            "author_title": "string"
                        }
                    }
                },
                "tags": ["testimonials", "simple", "list"]
            }
        }
    
    def _create_footer_components(self) -> Dict[str, Dict[str, Any]]:
        """Create footer component variations"""
        return {
            "simple": {
                "name": "Simple Footer",
                "description": "Simple centered footer with copyright and links",
                "html": """<footer class="footer footer--simple">
    <div class="footer__container">
        <div class="footer__links">
            <!-- footer_links_item_start -->
            <a href="{{footer_links.url}}" class="footer__link">{{footer_links.label}}</a>
            <!-- footer_links_item_end -->
        </div>
        <p class="footer__copyright">{{copyright_text}}</p>
    </div>
</footer>""",
                "css": """.footer {
    padding: var(--spacing-xl, 3rem) 0;
    background: var(--color-footer-background, #1f2937);
    color: var(--color-footer-text, #9ca3af);
}

.footer__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
    text-align: center;
}

.footer__links {
    display: flex;
    justify-content: center;
    gap: var(--spacing-lg, 2rem);
    flex-wrap: wrap;
    margin-bottom: var(--spacing-md, 1.5rem);
}

.footer__link {
    color: var(--color-footer-text, #9ca3af);
    text-decoration: none;
    transition: color 0.2s ease;
}

.footer__link:hover {
    color: var(--color-footer-text-hover, #ffffff);
}

.footer__copyright {
    font-size: 0.875rem;
    margin: 0;
}""",
                "config": {
                    "style": "simple",
                    "alignment": "center"
                },
                "content_bindings": {
                    "copyright_text": {
                        "type": "text",
                        "required": True,
                        "default": "© 2025 Your Business. All rights reserved."
                    },
                    "footer_links": {
                        "type": "array",
                        "required": False,
                        "itemSchema": {
                            "label": "string",
                            "url": "string"
                        },
                        "default": [
                            {"label": "Privacy Policy", "url": "/privacy"},
                            {"label": "Terms of Service", "url": "/terms"}
                        ]
                    }
                },
                "tags": ["footer", "simple", "centered"]
            },
            "columns": {
                "name": "Column Footer",
                "description": "Multi-column footer with detailed information",
                "html": """<footer class="footer footer--columns">
    <div class="footer__container">
        <div class="footer__grid">
            <div class="footer__column">
                <h3 class="footer__column-title">{{business_name}}</h3>
                <p class="footer__description">{{business_description}}</p>
            </div>
            <div class="footer__column">
                <h4 class="footer__column-title">Quick Links</h4>
                <ul class="footer__list">
                    <!-- footer_links_item_start -->
                    <li class="footer__list-item">
                        <a href="{{footer_links.url}}" class="footer__link">{{footer_links.label}}</a>
                    </li>
                    <!-- footer_links_item_end -->
                </ul>
            </div>
            <div class="footer__column">
                <h4 class="footer__column-title">Contact</h4>
                <ul class="footer__list">
                    <li class="footer__list-item">{{business_email}}</li>
                    <li class="footer__list-item">{{business_phone}}</li>
                </ul>
            </div>
        </div>
        <div class="footer__bottom">
            <p class="footer__copyright">{{copyright_text}}</p>
        </div>
    </div>
</footer>""",
                "css": """.footer {
    padding: var(--spacing-2xl, 5rem) 0 var(--spacing-lg, 2rem);
    background: var(--color-footer-background, #1f2937);
    color: var(--color-footer-text, #9ca3af);
}

.footer__container {
    max-width: var(--container-max-width, 1200px);
    margin: 0 auto;
    padding: 0 var(--spacing-md, 1.5rem);
}

.footer__grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-xl, 3rem);
    margin-bottom: var(--spacing-xl, 3rem);
}

.footer__column-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-footer-text-light, #ffffff);
    margin: 0 0 var(--spacing-md, 1.5rem);
}

.footer__description {
    line-height: 1.6;
    margin: 0;
}

.footer__list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm, 1rem);
}

.footer__link {
    color: var(--color-footer-text, #9ca3af);
    text-decoration: none;
    transition: color 0.2s ease;
}

.footer__link:hover {
    color: var(--color-footer-text-hover, #ffffff);
}

.footer__bottom {
    padding-top: var(--spacing-lg, 2rem);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    text-align: center;
}

.footer__copyright {
    font-size: 0.875rem;
    margin: 0;
}

@media (max-width: 768px) {
    .footer__grid {
        grid-template-columns: 1fr;
    }
}""",
                "config": {
                    "style": "columns",
                    "columns": 3
                },
                "content_bindings": {
                    "business_name": {
                        "type": "text",
                        "required": True,
                        "placeholder": "Business Name"
                    },
                    "business_description": {
                        "type": "text",
                        "required": False,
                        "placeholder": "Brief description"
                    },
                    "business_email": {
                        "type": "email",
                        "required": False,
                        "placeholder": "email@business.com"
                    },
                    "business_phone": {
                        "type": "phone",
                        "required": False,
                        "placeholder": "+234 xxx xxx xxxx"
                    },
                    "copyright_text": {
                        "type": "text",
                        "required": True,
                        "default": "© 2025 Your Business. All rights reserved."
                    },
                    "footer_links": {
                        "type": "array",
                        "required": False,
                        "itemSchema": {
                            "label": "string",
                            "url": "string"
                        },
                        "default": [
                            {"label": "Home", "url": "#home"},
                            {"label": "Services", "url": "#services"},
                            {"label": "About", "url": "#about"},
                            {"label": "Contact", "url": "#contact"}
                        ]
                    }
                },
                "tags": ["footer", "columns", "detailed"]
            }
        }


# Export singleton instance
component_library = ComponentLibrary()

