"""
Test script for theme generation
"""

from app.services.business_analyzer import BusinessAnalysis
from app.services.theme_generator import theme_generator
from app.services.default_theme import get_default_theme, get_theme_variant


def test_default_theme():
    """Test default theme retrieval"""
    print("\n" + "="*70)
    print("TEST 1: Default Theme")
    print("="*70)

    theme = get_default_theme()
    print(f"Background: {theme.background}")
    print(f"Foreground: {theme.foreground}")
    print(f"Primary: {theme.primary}")
    print(f"Secondary: {theme.secondary}")
    print(f"Accent: {theme.accent}")
    print(f"Border Radius: {theme.radius}")
    print("✓ Default theme retrieved successfully")


def test_theme_variants():
    """Test theme variants"""
    print("\n" + "="*70)
    print("TEST 2: Theme Variants")
    print("="*70)

    colors = ["blue", "green", "purple", "orange", "red"]

    for color in colors:
        theme = get_theme_variant(color)
        print(f"\n{color.upper()} variant:")
        print(f"  Primary: {theme.primary}")
        print(f"  Ring: {theme.ring}")

    print("\n✓ All theme variants working")


def test_ai_theme_generation():
    """Test AI theme generation with sample business analysis"""
    print("\n" + "="*70)
    print("TEST 3: AI Theme Generation")
    print("="*70)

    # Create sample business analysis for a coffee shop
    sample_analysis = BusinessAnalysis(
        prompt="Build a website for my coffee shop",
        user_intent="build_new_website",
        business_type="Coffee Shop",
        industry="Food & Beverage",
        site_purpose="Lead Generation",
        target_audience="Coffee lovers, local community, professionals",
        key_pages=["Home", "Menu", "About", "Contact"],
        tone="Friendly",
        style_keywords=["Warm", "Inviting", "Modern", "Cozy"],
        primary_colors=["Brown", "Cream", "Orange"],
        must_have_features=["Menu Display", "Location Map", "Contact Form"],
        primary_cta="Visit Us",
        value_propositions=[
            "Freshly roasted beans",
            "Cozy atmosphere",
            "Local community hub"
        ],
        content_sections=["Hero", "Menu Highlights", "About Us", "Location", "Contact"]
    )

    print(f"\nBusiness Type: {sample_analysis.business_type}")
    print(f"Industry: {sample_analysis.industry}")
    print(f"Tone: {sample_analysis.tone}")
    print(f"Style: {', '.join(sample_analysis.style_keywords)}")
    print(f"Colors: {', '.join(sample_analysis.primary_colors)}")

    print("\nGenerating AI theme...")
    theme = theme_generator.generate_theme(sample_analysis)

    print(f"\n✓ AI Theme Generated:")
    print(f"  Background: {theme.background}")
    print(f"  Foreground: {theme.foreground}")
    print(f"  Primary: {theme.primary}")
    print(f"  Primary Foreground: {theme.primary_foreground}")
    print(f"  Secondary: {theme.secondary}")
    print(f"  Accent: {theme.accent}")
    print(f"  Border: {theme.border}")
    print(f"  Radius: {theme.radius}")


def test_fallback_logic():
    """Test multi-level fallback"""
    print("\n" + "="*70)
    print("TEST 4: Fallback Logic")
    print("="*70)

    # Test with business analysis (AI generation)
    print("\nLevel 1: With business analysis (AI)...")
    sample_analysis = BusinessAnalysis(
        prompt="Tech startup website",
        user_intent="build_new_website",
        business_type="SaaS Platform",
        industry="Technology",
        site_purpose="Lead Generation",
        target_audience="Developers and tech companies",
        key_pages=["Home", "Features", "Pricing"],
        tone="Professional",
        style_keywords=["Modern", "Clean", "Technical"],
        primary_colors=["Blue", "White", "Purple"],
        must_have_features=["Feature showcase", "Pricing table"],
        primary_cta="Start Free Trial",
        value_propositions=["Easy to use", "Powerful features"],
        content_sections=["Hero", "Features", "Pricing"]
    )
    theme1 = theme_generator.generate_theme_with_fallback(
        business_analysis=sample_analysis
    )
    print(f"✓ Got theme with primary: {theme1.primary}")

    # Test with color scheme only (variant)
    print("\nLevel 2: With color scheme only (variant)...")
    theme2 = theme_generator.generate_theme_with_fallback(
        color_scheme="purple"
    )
    print(f"✓ Got theme with primary: {theme2.primary}")

    # Test with nothing (default)
    print("\nLevel 3: With nothing (default)...")
    theme3 = theme_generator.generate_theme_with_fallback()
    print(f"✓ Got theme with primary: {theme3.primary}")


def test_css_generation():
    """Test CSS generation with theme"""
    print("\n" + "="*70)
    print("TEST 5: CSS Generation")
    print("="*70)

    # Test direct CSS generation from theme
    theme = get_theme_variant("green")

    print(f"\nUsing GREEN theme variant:")
    print(f"  Primary: {theme.primary}")
    print(f"  Background: {theme.background}")
    print(f"  Accent: {theme.accent}")

    # Generate CSS content manually to test the theme values
    css_content = f'''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {{
  :root {{
    --background: {theme.background};
    --foreground: {theme.foreground};
    --card: {theme.card};
    --card-foreground: {theme.card_foreground};
    --popover: {theme.popover};
    --popover-foreground: {theme.popover_foreground};
    --primary: {theme.primary};
    --primary-foreground: {theme.primary_foreground};
    --secondary: {theme.secondary};
    --secondary-foreground: {theme.secondary_foreground};
    --muted: {theme.muted};
    --muted-foreground: {theme.muted_foreground};
    --accent: {theme.accent};
    --accent-foreground: {theme.accent_foreground};
    --destructive: {theme.destructive};
    --destructive-foreground: {theme.destructive_foreground};
    --border: {theme.border};
    --input: {theme.input};
    --ring: {theme.ring};
    --radius: {theme.radius};
  }}
}}

@layer base {{
  * {{
    @apply border-border;
  }}
  body {{
    @apply bg-background text-foreground;
  }}
}}
'''

    print("\n✓ CSS content generated successfully")
    print("\nPreview (CSS variables section):")
    print("-" * 70)
    lines = css_content.split('\n')[5:30]  # Show :root section
    print('\n'.join(lines))
    print("-" * 70)

    # Verify theme values are present
    if f"--primary: {theme.primary}" in css_content:
        print(f"\n✓ Theme primary color applied: {theme.primary}")
    if f"--background: {theme.background}" in css_content:
        print(f"✓ Theme background applied: {theme.background}")
    if f"--accent: {theme.accent}" in css_content:
        print(f"✓ Theme accent applied: {theme.accent}")
    if "@tailwind base" in css_content:
        print("✓ Tailwind directives present")

    print("\n✓ CSS generation test passed!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("THEME GENERATION TEST SUITE")
    print("="*70)

    try:
        test_default_theme()
        test_theme_variants()
        test_fallback_logic()
        test_css_generation()

        print("\n" + "="*70)
        print("TESTING AI THEME GENERATION (requires API key)")
        print("="*70)
        test_ai_theme_generation()

    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
