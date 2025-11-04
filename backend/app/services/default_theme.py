"""
Default Theme Configuration
Provides fallback theme for index.css when AI generation fails or is unavailable.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ThemeColors(BaseModel):
    """CSS variable color values in HSL format (without hsl() wrapper)"""

    # Core colors
    background: str = Field(..., description="Main background color (HSL format: '0 0% 100%')")
    foreground: str = Field(..., description="Main text color")

    # Card colors
    card: str = Field(..., description="Card background color")
    card_foreground: str = Field(..., description="Card text color")

    # Popover colors
    popover: str = Field(..., description="Popover/dropdown background")
    popover_foreground: str = Field(..., description="Popover/dropdown text")

    # Primary brand colors
    primary: str = Field(..., description="Primary brand color")
    primary_foreground: str = Field(..., description="Text on primary color")

    # Secondary colors
    secondary: str = Field(..., description="Secondary accent color")
    secondary_foreground: str = Field(..., description="Text on secondary color")

    # Muted/subtle colors
    muted: str = Field(..., description="Muted background color")
    muted_foreground: str = Field(..., description="Muted text color")

    # Accent colors
    accent: str = Field(..., description="Accent/highlight color")
    accent_foreground: str = Field(..., description="Text on accent color")

    # Destructive/error colors
    destructive: str = Field(..., description="Error/danger color")
    destructive_foreground: str = Field(..., description="Text on destructive color")

    # UI element colors
    border: str = Field(..., description="Border color")
    input: str = Field(..., description="Input border color")
    ring: str = Field(..., description="Focus ring color")

    # Border radius
    radius: str = Field(default="0.5rem", description="Border radius value")


# Professional Blue Theme - Works well for most business types
DEFAULT_THEME = ThemeColors(
    background="0 0% 100%",
    foreground="222.2 84% 4.9%",
    card="0 0% 100%",
    card_foreground="222.2 84% 4.9%",
    popover="0 0% 100%",
    popover_foreground="222.2 84% 4.9%",
    primary="221.2 83.2% 53.3%",  # Professional blue
    primary_foreground="210 40% 98%",
    secondary="210 40% 96.1%",
    secondary_foreground="222.2 47.4% 11.2%",
    muted="210 40% 96.1%",
    muted_foreground="215.4 16.3% 46.9%",
    accent="210 40% 96.1%",
    accent_foreground="222.2 47.4% 11.2%",
    destructive="0 84.2% 60.2%",
    destructive_foreground="210 40% 98%",
    border="214.3 31.8% 91.4%",
    input="214.3 31.8% 91.4%",
    ring="221.2 83.2% 53.3%",
    radius="0.5rem"
)


# Theme variants for different color schemes (fallback when structure.color_scheme is provided)
THEME_VARIANTS = {
    "blue": ThemeColors(
        background="0 0% 100%",
        foreground="222.2 84% 4.9%",
        card="0 0% 100%",
        card_foreground="222.2 84% 4.9%",
        popover="0 0% 100%",
        popover_foreground="222.2 84% 4.9%",
        primary="221.2 83.2% 53.3%",  # Blue
        primary_foreground="210 40% 98%",
        secondary="210 40% 96.1%",
        secondary_foreground="222.2 47.4% 11.2%",
        muted="210 40% 96.1%",
        muted_foreground="215.4 16.3% 46.9%",
        accent="210 40% 96.1%",
        accent_foreground="222.2 47.4% 11.2%",
        destructive="0 84.2% 60.2%",
        destructive_foreground="210 40% 98%",
        border="214.3 31.8% 91.4%",
        input="214.3 31.8% 91.4%",
        ring="221.2 83.2% 53.3%",
        radius="0.5rem"
    ),
    "indigo": ThemeColors(
        background="0 0% 100%",
        foreground="222.2 84% 4.9%",
        card="0 0% 100%",
        card_foreground="222.2 84% 4.9%",
        popover="0 0% 100%",
        popover_foreground="222.2 84% 4.9%",
        primary="239 84% 67%",  # Indigo
        primary_foreground="210 40% 98%",
        secondary="210 40% 96.1%",
        secondary_foreground="222.2 47.4% 11.2%",
        muted="210 40% 96.1%",
        muted_foreground="215.4 16.3% 46.9%",
        accent="210 40% 96.1%",
        accent_foreground="222.2 47.4% 11.2%",
        destructive="0 84.2% 60.2%",
        destructive_foreground="210 40% 98%",
        border="214.3 31.8% 91.4%",
        input="214.3 31.8% 91.4%",
        ring="239 84% 67%",
        radius="0.5rem"
    ),
    "green": ThemeColors(
        background="0 0% 100%",
        foreground="222.2 84% 4.9%",
        card="0 0% 100%",
        card_foreground="222.2 84% 4.9%",
        popover="0 0% 100%",
        popover_foreground="222.2 84% 4.9%",
        primary="142.1 76.2% 36.3%",  # Green
        primary_foreground="210 40% 98%",
        secondary="210 40% 96.1%",
        secondary_foreground="222.2 47.4% 11.2%",
        muted="210 40% 96.1%",
        muted_foreground="215.4 16.3% 46.9%",
        accent="210 40% 96.1%",
        accent_foreground="222.2 47.4% 11.2%",
        destructive="0 84.2% 60.2%",
        destructive_foreground="210 40% 98%",
        border="214.3 31.8% 91.4%",
        input="214.3 31.8% 91.4%",
        ring="142.1 76.2% 36.3%",
        radius="0.5rem"
    ),
    "emerald": ThemeColors(
        background="0 0% 100%",
        foreground="222.2 84% 4.9%",
        card="0 0% 100%",
        card_foreground="222.2 84% 4.9%",
        popover="0 0% 100%",
        popover_foreground="222.2 84% 4.9%",
        primary="142.1 76.2% 36.3%",  # Emerald
        primary_foreground="210 40% 98%",
        secondary="210 40% 96.1%",
        secondary_foreground="222.2 47.4% 11.2%",
        muted="210 40% 96.1%",
        muted_foreground="215.4 16.3% 46.9%",
        accent="210 40% 96.1%",
        accent_foreground="222.2 47.4% 11.2%",
        destructive="0 84.2% 60.2%",
        destructive_foreground="210 40% 98%",
        border="214.3 31.8% 91.4%",
        input="214.3 31.8% 91.4%",
        ring="142.1 76.2% 36.3%",
        radius="0.5rem"
    ),
    "purple": ThemeColors(
        background="0 0% 100%",
        foreground="222.2 84% 4.9%",
        card="0 0% 100%",
        card_foreground="222.2 84% 4.9%",
        popover="0 0% 100%",
        popover_foreground="222.2 84% 4.9%",
        primary="262.1 83.3% 57.8%",  # Purple
        primary_foreground="210 40% 98%",
        secondary="210 40% 96.1%",
        secondary_foreground="222.2 47.4% 11.2%",
        muted="210 40% 96.1%",
        muted_foreground="215.4 16.3% 46.9%",
        accent="210 40% 96.1%",
        accent_foreground="222.2 47.4% 11.2%",
        destructive="0 84.2% 60.2%",
        destructive_foreground="210 40% 98%",
        border="214.3 31.8% 91.4%",
        input="214.3 31.8% 91.4%",
        ring="262.1 83.3% 57.8%",
        radius="0.5rem"
    ),
    "pink": ThemeColors(
        background="0 0% 100%",
        foreground="222.2 84% 4.9%",
        card="0 0% 100%",
        card_foreground="222.2 84% 4.9%",
        popover="0 0% 100%",
        popover_foreground="222.2 84% 4.9%",
        primary="330 81% 60%",  # Pink
        primary_foreground="210 40% 98%",
        secondary="210 40% 96.1%",
        secondary_foreground="222.2 47.4% 11.2%",
        muted="210 40% 96.1%",
        muted_foreground="215.4 16.3% 46.9%",
        accent="210 40% 96.1%",
        accent_foreground="222.2 47.4% 11.2%",
        destructive="0 84.2% 60.2%",
        destructive_foreground="210 40% 98%",
        border="214.3 31.8% 91.4%",
        input="214.3 31.8% 91.4%",
        ring="330 81% 60%",
        radius="0.5rem"
    ),
    "red": ThemeColors(
        background="0 0% 100%",
        foreground="222.2 84% 4.9%",
        card="0 0% 100%",
        card_foreground="222.2 84% 4.9%",
        popover="0 0% 100%",
        popover_foreground="222.2 84% 4.9%",
        primary="0 72% 51%",  # Red
        primary_foreground="210 40% 98%",
        secondary="210 40% 96.1%",
        secondary_foreground="222.2 47.4% 11.2%",
        muted="210 40% 96.1%",
        muted_foreground="215.4 16.3% 46.9%",
        accent="210 40% 96.1%",
        accent_foreground="222.2 47.4% 11.2%",
        destructive="0 84.2% 60.2%",
        destructive_foreground="210 40% 98%",
        border="214.3 31.8% 91.4%",
        input="214.3 31.8% 91.4%",
        ring="0 72% 51%",
        radius="0.5rem"
    ),
    "orange": ThemeColors(
        background="0 0% 100%",
        foreground="222.2 84% 4.9%",
        card="0 0% 100%",
        card_foreground="222.2 84% 4.9%",
        popover="0 0% 100%",
        popover_foreground="222.2 84% 4.9%",
        primary="24.6 95% 53.1%",  # Orange
        primary_foreground="210 40% 98%",
        secondary="210 40% 96.1%",
        secondary_foreground="222.2 47.4% 11.2%",
        muted="210 40% 96.1%",
        muted_foreground="215.4 16.3% 46.9%",
        accent="210 40% 96.1%",
        accent_foreground="222.2 47.4% 11.2%",
        destructive="0 84.2% 60.2%",
        destructive_foreground="210 40% 98%",
        border="214.3 31.8% 91.4%",
        input="214.3 31.8% 91.4%",
        ring="24.6 95% 53.1%",
        radius="0.5rem"
    ),
}


def get_default_theme() -> ThemeColors:
    """Get the default fallback theme"""
    return DEFAULT_THEME


def get_theme_variant(color_scheme: Optional[str] = None) -> ThemeColors:
    """
    Get a theme variant based on color scheme

    Args:
        color_scheme: Color scheme name (e.g., 'blue', 'green', 'purple')

    Returns:
        ThemeColors object for the requested scheme, or default if not found
    """
    if not color_scheme:
        return DEFAULT_THEME

    color_key = color_scheme.lower().strip()
    return THEME_VARIANTS.get(color_key, DEFAULT_THEME)
