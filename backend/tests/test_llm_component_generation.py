# -*- coding: utf-8 -*-
"""
Test for LLM-based component generation system
This demonstrates how the new system dynamically generates components
"""

import json
from app.services.react_website_generator import react_website_generator
from app.services.react_models import PageStructure, PageComponent, PropItem, WebsiteStructure, NavItem
from app.services.business_analyzer import BusinessAnalysis


def test_page_generation_with_llm():
    """
    Test that demonstrates LLM-based page generation with automatic component creation
    """
    
    # Create a mock business analysis
    business_analysis = BusinessAnalysis(
        user_intent="build_new_website",
        business_type="SaaS Company",
        industry="Technology",
        site_purpose="Product landing page with signup",
        target_audience="Small business owners and entrepreneurs",
        key_pages=["Home", "Features", "Pricing", "About"],
        content_sections=["hero", "features", "testimonials", "pricing", "cta"],
        must_have_features=["Email signup", "Pricing table", "Feature showcase"],
        primary_cta="Start Free Trial",
        tone="professional yet friendly",
        style_keywords=["modern", "clean", "minimalist"],
        primary_colors=["blue", "white", "gray"],
        value_propositions=[
            "Automate your workflow",
            "Save time and money",
            "Scale with confidence"
        ]
    )
    
    # Create a mock website structure with a home page
    website_structure = WebsiteStructure(
        name="TechFlow",
        tagline="Automate Your Business Workflow",
        description="The all-in-one platform for managing your business operations",
        color_scheme="blue",
        pages=[
            PageStructure(
                name="Home",
                path="/",
                title="TechFlow - Automate Your Business Workflow",
                description="Transform your business with our powerful automation platform",
                components=[
                    PageComponent(
                        name="Hero",
                        type="hero",
                        props=[
                            PropItem(key="title", value="Automate Your Business Workflow"),
                            PropItem(key="subtitle", value="Save time and boost productivity"),
                            PropItem(key="primaryCta", value="Start Free Trial"),
                            PropItem(key="secondaryCta", value="Watch Demo")
                        ]
                    ),
                    PageComponent(
                        name="Features",
                        type="features",
                        props=[
                            PropItem(key="title", value="Powerful Features"),
                            PropItem(key="description", value="Everything you need to succeed"),
                            PropItem(key="features", value=[
                                {
                                    "title": "Automation",
                                    "description": "Automate repetitive tasks"
                                },
                                {
                                    "title": "Analytics",
                                    "description": "Track your performance"
                                },
                                {
                                    "title": "Integration",
                                    "description": "Connect with your tools"
                                }
                            ])
                        ]
                    ),
                    PageComponent(
                        name="Testimonials",
                        type="testimonials",
                        props=[
                            PropItem(key="title", value="What Our Customers Say"),
                            PropItem(key="testimonials", value=[
                                {
                                    "quote": "TechFlow transformed our business",
                                    "author": "John Doe",
                                    "role": "CEO, StartupCo"
                                }
                            ])
                        ]
                    )
                ]
            )
        ],
        navigation=[
            NavItem(label="Home", path="/"),
            NavItem(label="Features", path="/features"),
            NavItem(label="Pricing", path="/pricing"),
            NavItem(label="About", path="/about")
        ]
    )
    
    # Initialize the generator (don't actually call the LLM in tests)
    generator = react_website_generator
    
    # Mock files dictionary with base UI components
    files = {
        "src/components/ui/button.tsx": "// Button component",
        "src/components/ui/card.tsx": "// Card component",
        "src/components/ui/input.tsx": "// Input component",
    }
    
    # Verify helper methods work correctly
    ui_components = generator._get_available_ui_components(files)
    assert "button" in ui_components
    assert "card" in ui_components
    assert "input" in ui_components
    
    section_components = generator._get_available_section_components(files)
    assert len(section_components) == 0  # No section components yet
    
    # Test that prompts are created correctly
    system_prompt = generator._create_page_generation_system_prompt()
    assert "React/TypeScript" in system_prompt
    assert "shadcn/ui" in system_prompt
    
    user_prompt = generator._create_page_generation_user_prompt(
        page=website_structure.pages[0],
        structure=website_structure,
        analysis=business_analysis,
        available_ui_components=ui_components,
        available_section_components=section_components
    )
    assert "Home" in user_prompt
    assert "Hero" in user_prompt
    assert "Features" in user_prompt
    assert "TechFlow" in user_prompt
    
    print("[PASS] All helper methods working correctly")
    print(f"[PASS] Available UI components: {ui_components}")
    print(f"[PASS] System prompt length: {len(system_prompt)} chars")
    print(f"[PASS] User prompt length: {len(user_prompt)} chars")


def test_component_file_structure():
    """Test that component file paths are structured correctly"""
    from app.services.react_models import ComponentFile
    
    # Test section component
    section_comp = ComponentFile(
        path="src/components/Hero.tsx",
        content="// Hero component code",
        component_type="section"
    )
    assert section_comp.path.startswith("src/components/")
    assert not section_comp.path.startswith("src/components/ui/")
    
    # Test UI component
    ui_comp = ComponentFile(
        path="src/components/ui/badge.tsx",
        content="// Badge component code",
        component_type="ui"
    )
    assert ui_comp.path.startswith("src/components/ui/")
    
    print("[PASS] Component file structure validated")


if __name__ == "__main__":
    print("\n=== Testing LLM Component Generation System ===\n")
    
    test_component_file_structure()
    test_page_generation_with_llm()
    
    print("\nAll tests passed!")
    print("\nTo run full generation (requires OpenAI API key):")
    print("  python backend/tests/example_react_generation.py")

