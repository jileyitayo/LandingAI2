"""
Theme Generator Service
Generates custom CSS themes based on business analysis using AI.
"""

import logging
from typing import Optional

from app.services.business_analyzer import BusinessAnalysis
from app.services.prompt_open_ai import PromptOpenAI
from app.services.default_theme import ThemeColors, get_default_theme, get_theme_variant

logger = logging.getLogger(__name__)


class ThemeGenerator:
    """Generates AI-powered color themes based on business analysis"""

    def __init__(self):
        self.google_client = PromptOpenAI(is_google=True)

    def generate_theme(self, business_analysis: BusinessAnalysis) -> ThemeColors:
        """
        Generate a custom theme based on business analysis

        Args:
            business_analysis: Business analysis data

        Returns:
            ThemeColors object with AI-generated or fallback theme
        """
        try:
            logger.info(f"[THEME GEN] Generating theme for {business_analysis.business_type}")

            # Create system prompt for theme generation
            system_prompt = self._create_theme_system_prompt()

            # Create user prompt with business context
            user_prompt = self._create_theme_user_prompt(business_analysis)

            # Call AI to generate theme
            self.google_client.set_max_completion_tokens(4000)
            theme, usage = self.google_client.call_openai_api_structured(
                system_prompt,
                user_prompt,
                ThemeColors,
                model="gemini-2.5-flash"
            )

            logger.info(f"[THEME GEN] ✓ AI theme generated successfully")
            logger.info(f"[THEME GEN] Usage: {usage}")
            logger.info(f"[THEME GEN] Primary color: hsl({theme.primary})")

            return theme

        except Exception as e:
            logger.error(f"[THEME GEN] ✗ AI theme generation failed: {str(e)}")
            logger.info(f"[THEME GEN] Falling back to default theme")
            return get_default_theme()

    def _create_theme_system_prompt(self) -> str:
        """Create system prompt for theme generation"""
        return """You are an expert UI/UX designer and color theorist specializing in brand identity and web design.

Your task is to generate a professional, accessible color theme for a website based on business analysis.

CRITICAL REQUIREMENTS:
1. **HSL Format Only**: All colors MUST be in HSL format WITHOUT the hsl() wrapper
   - ✅ CORRECT: "221.2 83.2% 53.3%"
   - ❌ WRONG: "hsl(221.2, 83.2%, 53.3%)"
   - ❌ WRONG: "221.2deg 83.2% 53.3%"

2. **WCAG Accessibility**: Ensure proper contrast ratios
   - Background vs Foreground: minimum 4.5:1
   - Primary vs Primary Foreground: minimum 4.5:1
   - All text must be readable on its background

3. **Color Psychology**: Match colors to business type and industry
   - Law firms, Finance: Professional blues, navy, charcoal
   - Healthcare: Trustworthy blues, calming greens
   - Food/Restaurants: Warm oranges, browns, appetizing reds
   - Tech/Startups: Modern blues, purples, teals
   - Creative: Bold, vibrant, unique palettes
   - Luxury: Deep purples, golds, blacks
   - Environmental: Natural greens, earth tones

4. **Tone Alignment**: Reflect the business tone
   - Professional: Conservative, muted colors
   - Friendly: Warm, approachable colors
   - Playful: Bright, energetic colors
   - Luxury: Rich, sophisticated colors
   - Technical: Cool, modern colors

5. **Cohesive Palette**: All colors must work together harmoniously
   - Primary should be the dominant brand color
   - Secondary should complement primary
   - Accent should provide visual interest
   - Muted colors should be subtle variants

6. **Standard Structure**: Use light backgrounds and dark text (light mode only)
   - background: white or very light color
   - foreground: dark text color for readability
   - card/popover: similar to background
   - borders/inputs: subtle gray tones

7. **Border Radius**: Set appropriate roundness
   - Modern/Tech: 0.5rem - 0.75rem
   - Traditional: 0.25rem - 0.5rem
   - Playful: 0.75rem - 1rem

OUTPUT FORMAT:
Return a JSON object with ALL required CSS variable values in HSL format (no hsl() wrapper).

Example output structure:
{
  "background": "0 0% 100%",
  "foreground": "222.2 84% 4.9%",
  "card": "0 0% 100%",
  "card_foreground": "222.2 84% 4.9%",
  "popover": "0 0% 100%",
  "popover_foreground": "222.2 84% 4.9%",
  "primary": "221.2 83.2% 53.3%",
  "primary_foreground": "210 40% 98%",
  "secondary": "210 40% 96.1%",
  "secondary_foreground": "222.2 47.4% 11.2%",
  "muted": "210 40% 96.1%",
  "muted_foreground": "215.4 16.3% 46.9%",
  "accent": "210 40% 96.1%",
  "accent_foreground": "222.2 47.4% 11.2%",
  "destructive": "0 84.2% 60.2%",
  "destructive_foreground": "210 40% 98%",
  "border": "214.3 31.8% 91.4%",
  "input": "214.3 31.8% 91.4%",
  "ring": "221.2 83.2% 53.3%",
  "radius": "0.5rem"
}

IMPORTANT:
- Ring color should match primary color for consistency
- Destructive colors should be red-based for errors/warnings
- All HSL values must be space-separated (not comma-separated)
- No units in HSL values except for radius"""

    def _create_theme_user_prompt(self, analysis: BusinessAnalysis) -> str:
        """Create user prompt with business context"""
        return f"""Generate a professional, accessible color theme for this website:

BUSINESS CONTEXT:
- Type: {analysis.business_type}
- Industry: {analysis.industry}
- Purpose: {analysis.site_purpose}
- Target Audience: {analysis.target_audience}

DESIGN DIRECTION:
- Tone: {analysis.tone}
- Style Keywords: {', '.join(analysis.style_keywords)}
- Suggested Colors: {', '.join(analysis.primary_colors)}

REQUIREMENTS:
1. Create a cohesive color palette that:
   - Reflects the business type and industry standards
   - Matches the tone ({analysis.tone})
   - Incorporates inspiration from: {', '.join(analysis.primary_colors)}
   - Appeals to the target audience: {analysis.target_audience}

2. Ensure excellent contrast and accessibility (WCAG AA minimum)

3. The primary color should be bold enough for CTAs and buttons

4. Keep backgrounds light (white or near-white) for readability

5. Use the suggested colors as inspiration, but adjust for:
   - Proper contrast ratios
   - Professional appearance
   - Visual harmony

Generate the theme now in the exact JSON format specified, with all HSL values in space-separated format (e.g., "221.2 83.2% 53.3%")."""

    def generate_theme_with_fallback(
        self,
        business_analysis: Optional[BusinessAnalysis] = None,
        color_scheme: Optional[str] = None
    ) -> ThemeColors:
        """
        Generate theme with multiple fallback levels

        Args:
            business_analysis: Business analysis for AI generation
            color_scheme: Fallback color scheme name

        Returns:
            ThemeColors object (AI-generated, variant, or default)
        """
        # Level 1: Try AI generation
        if business_analysis:
            try:
                return self.generate_theme(business_analysis)
            except Exception as e:
                logger.warning(f"[THEME GEN] AI generation failed, trying fallback: {str(e)}")

        # Level 2: Try theme variant based on color_scheme
        if color_scheme:
            logger.info(f"[THEME GEN] Using theme variant: {color_scheme}")
            return get_theme_variant(color_scheme)

        # Level 3: Use default theme
        logger.info(f"[THEME GEN] Using default theme")
        return get_default_theme()


# Create singleton instance
theme_generator = ThemeGenerator()
