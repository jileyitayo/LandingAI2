"""
React Website Generator Models
Pydantic models for React website generation
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Union, Any

class PropItem(BaseModel):
    """A single prop key-value pair"""
    key: str = Field(..., description="Component's Property key")
    value: Union[str, int, float, bool, List[Dict[str, Any]], Dict[str, Any], None] = Field(..., description="Component's Property value")

class PageComponent(BaseModel):
    """Represents a component/section within a page"""
    name: str = Field(..., description="Component name (e.g., Hero, Services, Contact, etc.)")
    type: str = Field(..., description="Component type (hero, features, testimonials, contact, about, etc.)")
    props: List[PropItem] = Field(default=[], description="Component props/contentas key-value pairs")


class PageStructure(BaseModel):
    """Represents a complete page structure"""
    name: str = Field(..., description="Page name (e.g., Home, About, Services, etc.)")
    path: str = Field(..., description="Route path (e.g., /, /about, /services, etc.)")
    title: str = Field(..., description="Page title for SEO")
    description: str = Field(..., description="Page description for SEO")
    components: List[PageComponent] = Field(..., description="List of components/sections on this page")

class NavItem(BaseModel):
    """Navigation menu item"""
    label: str = Field(..., description=f"Header Navigation label")
    path: str = Field(..., description="Header Navigation path")

class WebsiteStructure(BaseModel):
    """Complete website structure"""
    name: str = Field(..., description="Website/business name")
    tagline: str = Field(..., description="Main tagline/slogan")
    description: str = Field(..., description="Business description")
    color_scheme: str = Field(..., description="Primary color (e.g., blue, indigo, emerald)")
    pages: List[PageStructure] = Field(..., description="List of all pages")
    navigation: List[NavItem] = Field(..., description="Header Navigation menu items")

class ComponentFile(BaseModel):
    """Represents a generated component file"""
    path: str = Field(..., description="Relative file path (e.g., src/components/Hero.tsx or src/components/ui/badge.tsx)")
    content: str = Field(..., description="Complete file content including imports and exports")
    component_type: str = Field(..., description="Type: 'section' for page components, 'ui' for UI primitives")

class PageGenerationResponse(BaseModel):
    """Response from LLM for page generation"""
    page_content: str = Field(..., description="Complete page component code with all imports and exports")
    new_components: List[ComponentFile] = Field(default=[], description="List of new components that need to be created")

