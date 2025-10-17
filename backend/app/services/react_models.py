"""
React Website Generator Models
Pydantic models for React website generation
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Union, Any, Optional

class PropItem(BaseModel):
    """A single prop key-value pair"""
    key: str = Field(..., description="Component's Property key")
    value: Union[str, int, float, bool, List[Dict[str, Any]], Dict[str, Any], None] = Field(..., description="Component's Property value. Must not be empty. Use real values.")

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


class ValidationError(BaseModel):
    """Represents a validation error"""
    file_path: str = Field(..., description="Path to file with error")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    severity: str = Field(default="error", description="Error severity: error or warning")


class ValidationResult(BaseModel):
    """Result of code validation"""
    passed: bool = Field(..., description="Whether validation passed")
    errors: List[ValidationError] = Field(default=[], description="List of validation errors")
    warnings: List[ValidationError] = Field(default=[], description="List of validation warnings")
    total_files_validated: int = Field(..., description="Number of files validated")


class BuildTestResult(BaseModel):
    """Result of build test"""
    success: bool = Field(..., description="Whether build succeeded")
    errors: List[ValidationError] = Field(default=[], description="List of build errors")
    warnings: List[str] = Field(default=[], description="List of build warnings")
    duration: float = Field(..., description="Build duration in seconds")
    build_output: str = Field(default="", description="Full build output")


class GenerationResult(BaseModel):
    """Complete generation result with validation info"""
    success: bool = Field(..., description="Whether generation was successful")
    website_structure: Dict[str, Any] = Field(..., description="Generated website structure")
    business_analysis: Dict[str, Any] = Field(..., description="Business analysis")
    files: Dict[str, str] = Field(..., description="Generated files")
    validation: ValidationResult = Field(..., description="Validation results")
    build_test: Union[BuildTestResult, None] = Field(default=None, description="Build test results (if enabled)")
    retry_count: int = Field(default=0, description="Number of retry attempts made")
    fixed_errors: List[str] = Field(default=[], description="List of errors that were auto-fixed")
    generation_time: float = Field(..., description="Total generation time in seconds")

