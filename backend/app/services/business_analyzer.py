from pydantic import BaseModel, Field
from typing import List

from app.services.prompt_open_ai import PromptOpenAI
from app.config import settings

class BusinessAnalysis(BaseModel):
    """Minimal business analysis for accurate website template and content generation"""
    
    # Intent & Context
    prompt: str = Field(..., description="The comprehensive summary of the original user prompt used to generate the business analysis")
    user_intent: str = Field(..., description="What user wants: build_new_website, redesign_existing, add_features, get_ideas")
    business_type: str = Field(..., description="What the business does (e.g., Coffee Shop, Law Firm, Photography Studio)")
    industry: str = Field(..., description="Industry category (e.g., Food & Beverage, Legal Services, Creative Services)")
    
    # Core Requirements
    site_purpose: str = Field(..., description="Primary goal: E-commerce, Lead Generation, Portfolio, Informational, Booking")
    target_audience: str = Field(..., description="Who will use this site (single concise description)")
    key_pages: List[str] = Field(..., description="Essential pages needed (e.g., Home, About, Services, Contact) - between 1 (single page) and 4 depending on the business type. Always make it simple")
    
    # Content & Design Direction
    tone: str = Field(..., description="Content tone: Professional, Friendly, Luxury, Playful, Technical, etc.")
    style_keywords: List[str] = Field(..., description="3-5 design keywords (e.g., Modern, Clean, Bold, Minimalist, Elegant)")
    primary_colors: List[str] = Field(..., description="2-4 color suggestions (e.g., Navy Blue, White, Gold)")
    
    # Key Features & CTAs
    must_have_features: List[str] = Field(..., description="Critical features for this site type (e.g., Contact Form, Menu Display, Booking System)")
    primary_cta: str = Field(..., description="Main call-to-action (e.g., Book Now, Contact Us, Shop Now, Get Quote)")
    
    # Content Hints
    value_propositions: List[str] = Field(..., description="3-5 key selling points or benefits to highlight")
    content_sections: List[str] = Field(..., description="Main content sections for each of the key_pages (e.g., Home: [Hero, Services, Testimonials, Contact], About: [About, Team, Stats]... etc). Include Header and Footer in the content_sections if needed")

"""
# TODO
Inspirations online 
Design inspiration: MIT Media Lab, Stanford AI Lab - clean, scientific aesthetic with modern gradients and professional typography.


Detailed Features:

Hero section with lab introduction
Projects showcase grid
Blog posts section
Smooth navigation and animations
Fully responsive design

Design approach:

Deep blue to purple gradient theme (scientific/tech feel)
Clean card-based layouts
Smooth fade-in animations
Professional typography with good contrast
Modern glassmorphism effects
"""


class BusinessAnalyzer():
    def __init__(self):
        self.client = PromptOpenAI()
        self.google_client = PromptOpenAI(is_google=True)


    def generate_business_analysis(self, user_prompt: str, cost_tracker=None) -> BusinessAnalysis:
        """
        Generate extensive and complete business analysis for website template generation.
        
        Args:
            user_prompt: User's prompt describing their business/website needs
            cost_tracker: Optional CostTracker instance to track AI costs
        
        Returns:
            BusinessAnalysis object
        """
        system_prompt_old = """You are a website strategy expert. Analyze user requests and extract ONLY the essential information needed for an LLM to generate accurate website templates and content.

    Focus on:
    1. INTENT: What does the user want to accomplish?
    2. BUSINESS CONTEXT: What type of business and industry?
    3. SITE PURPOSE: What should the website achieve?
    4. AUDIENCE: Who is it for?
    5. STRUCTURE: What pages are essential? 
    6. DESIGN DIRECTION: What aesthetic fits this business?
    7. FEATURES: What functionality is critical?, max 3 features
    8. CONTENT STRATEGY: What messages matter most?
    9. ORIGINAL PROMPT: Comprehensive summary of the original user prompt. Do not include any other information in this field.

    Be specific and actionable. Think: "What does an LLM need to know to build this site accurately?"

    For each field:
    - business_type: Specific (e.g., "Italian Restaurant", not just "Restaurant")
    - key_pages: Only essential pages, typically 3-5
    - style_keywords: Descriptive aesthetic terms that guide design
    - must_have_features: Critical functionality, not nice-to-haves
    - value_propositions: Actual benefits to communicate, not generic
    - content_sections: Logical flow of homepage sections
    - original_prompt: Comprehensive summary of the original user prompt.
    Infer intelligently from minimal prompts based on industry standards."""
        # self.client.set_max_completion_tokens(6000)
        # self.business_analysis, usage = self.client.call_openai_api_structured(system_prompt, user_prompt, BusinessAnalysis)

        # Optimized system prompt
        system_prompt = """
        You are a website strategy expert. Your task is to analyze user requests and extract only the essential information required for a language model to generate accurate website templates and content. Focus on providing specific, actionable details to inform site creation. Always consider: "What must an LLM know to build this site correctly?"
        Begin with a concise checklist (3-7 bullets) of what you will do; keep items conceptual, not implementation-level.
        Extract and return the following fields:
        1. **intent**: What is the user's primary goal for the website? (string)
        2. **business_context**: What is the specific business type and industry? (string)
        3. **site_purpose**: What should the website accomplish? (string)
        4. **audience**: Who is the main audience? (string)
        5. **key_pages**: List 3-5 essential pages. (array of strings)
        6. **style_keywords**: Up to 5 descriptive terms for the site's desired look/feel. (array of strings)
        7. **must_have_features**: Up to 3 crucial features (array of up to 3 strings). If more are listed, select only the most essential; if fewer or none, infer from industry standards or leave as null if insufficient information.
        8. **value_propositions**: Core benefits or messaging to communicate (avoid generalities). (array of strings)
        9. **content_sections**: Ordered list of homepage section names to define homepage flow. (array of strings)
        10. **original_prompt**: Direct summary of the user's original prompt. Do not add or embellish; retain ambiguity if information is missing or unclear.
        If a field cannot be confidently determined or inferred from the user input, return null for that field.
        Infer intelligently from minimal prompts using industry common practices when possible.
        After extracting each field, briefly validate that your extraction matches the user's intent and correct if necessary before finalizing your output.
        """

        self.google_client.set_max_completion_tokens(6000)
        self.business_analysis, usage = self.google_client.call_openai_api_structured(system_prompt, user_prompt, BusinessAnalysis, model="gemini-2.5-flash")
        print(f"Usage for business analysis: {usage}")
        
        # Track cost if cost_tracker is provided
        if cost_tracker:
            cost_tracker.track_call(
                service_name="business_analysis",
                model_name="gemini-2.5-flash",
                usage=usage
            )
        
        return self.business_analysis


    def print_analysis(self):
        """Display the streamlined analysis"""
        print("\n" + "="*70)
        print("BUSINESS ANALYSIS FOR WEBSITE GENERATION")
        print("="*70)
        analysis = self.business_analysis
        print(f"\n🎯 INTENT & CONTEXT")
        print(f"   Intent: {analysis.user_intent}")
        print(f"   Business: {analysis.business_type}")
        print(f"   Industry: {analysis.industry}")
        
        print(f"\n🎨 DESIGN DIRECTION")
        print(f"   Tone: {analysis.tone}")
        print(f"   Style: {', '.join(analysis.style_keywords)}")
        print(f"   Colors: {', '.join(analysis.primary_colors)}")
        
        print(f"\n📄 SITE STRUCTURE")
        print(f"   Purpose: {analysis.site_purpose}")
        print(f"   Audience: {analysis.target_audience}")
        print(f"   Pages: {', '.join(analysis.key_pages)}")
        
        print(f"\n⚡ KEY FEATURES")
        print(f"   Must-Have: {', '.join(analysis.must_have_features)}")
        print(f"   Primary CTA: {analysis.primary_cta}")
        
        print(f"\n💡 CONTENT STRATEGY")
        print(f"   Sections: {', '.join(analysis.content_sections)}")
        print(f"   Value Props:")
        for vp in analysis.value_propositions:
            print(f"      • {vp}")
        
        print("\n" + "="*70)


    def create_generation_prompt(self) -> str:
        """
        Convert analysis into a prompt for website template/content generation.
        This is what you'd pass to your next LLM.
        """
        analysis = self.business_analysis
        prompt = f"""Generate a complete website for a {analysis.business_type} in the {analysis.industry} industry.

    BUSINESS CONTEXT:
    - Purpose: {analysis.site_purpose}
    - Target Audience: {analysis.target_audience}
    - User Intent: {analysis.user_intent}

    DESIGN REQUIREMENTS:
    - Tone: {analysis.tone}
    - Style: {', '.join(analysis.style_keywords)}
    - Colors: {', '.join(analysis.primary_colors)}

    SITE STRUCTURE:
    Create these pages: {', '.join(analysis.key_pages)}

    FEATURES TO INCLUDE:
    {chr(10).join(f"- {feature}" for feature in analysis.must_have_features)}

    CONTENT DIRECTION:
    Main sections: {', '.join(analysis.content_sections)}

    Key value propositions to highlight:
    {chr(10).join(f"- {vp}" for vp in analysis.value_propositions)}

    Primary call-to-action: {analysis.primary_cta}

    Generate appropriate content and design that matches this business type and achieves the stated purpose."""
        
        return prompt


# # Example usage
# if __name__ == "__main__":
#     test_prompts = [
#         "build a website for my bakery",
#         "I need a portfolio site for my photography business",
#         "create a website for a law firm specializing in family law",
#         "online store for handmade jewelry",
#         "website for a yoga studio"
#     ]
    
#     test_prompt = test_prompts[1]
    
#     print("="*70)
#     print("STREAMLINED WEBSITE ANALYSIS")
#     print("="*70)
#     print(f"\n💬 User Prompt: \"{test_prompt}\"")
#     print("\n🔍 Generating analysis...")
    
#     try:
        
#         # Generate streamlined analysis
#         business_analyzer = BusinessAnalyzer()
#         analysis = business_analyzer.generate_business_analysis(test_prompt)
        
#         # Display
#         business_analyzer.print_analysis()
        
#         # Save JSON
#         output_file = "streamlined_analysis.json"
#         with open(output_file, "w") as f:
#             f.write(analysis.model_dump_json(indent=2))
#         print(f"\n💾 Saved to '{output_file}'")
        
#         # Show generation prompt
#         print("\n" + "="*70)
#         print("PROMPT FOR WEBSITE GENERATOR LLM")
#         print("="*70)
#         generation_prompt = business_analyzer.create_generation_prompt()
#         print(generation_prompt)
        
#         # Show usage pattern
#         print("\n" + "="*70)
#         print("USAGE IN YOUR PIPELINE")
#         print("="*70)
#         print("""
# # Step 1: Analyze user request
# analysis = business_analyzer.generate_business_analysis(user_prompt)

# # Step 2: Pass to template generator
# template_prompt = business_analyzer.create_generation_prompt()
# website = your_llm.generate(template_prompt)

# # Or use the structured data directly
# website = business_analyzer.generate_website(
#     business_type=analysis.business_type,
#     pages=analysis.key_pages,
#     style=analysis.style_keywords,
#     features=analysis.must_have_features,
#     tone=analysis.tone
# )
#         """)
        
#         # Show field count
#         print(f"\nTotal fields: {len(analysis.model_dump())}")
#         print("Each field is essential for accurate generation! ✓")
        
#     except ValueError as e:
#         print(f"\n❌ Error: {e}")
#     except Exception as e:
#         print(f"\n❌ Error: {str(e)}")