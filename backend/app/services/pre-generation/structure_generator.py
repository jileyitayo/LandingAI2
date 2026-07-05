"""
Structure Generator Service
Generates website structure from business analysis.
"""

import logging
from app.config import settings
from app.services.business_analyzer import BusinessAnalysis
from app.services.react_models import WebsiteStructure
from app.services.prompt_open_ai import PromptOpenAI

logger = logging.getLogger(__name__)


class StructureGenerator:
    """Generates website structure from business analysis"""

    def __init__(self):
        """Initialize the structure generator with Google AI client"""
        self.google_client = PromptOpenAI(is_google=True)

    def generate_structure(self, analysis: BusinessAnalysis, cost_tracker=None) -> WebsiteStructure:
        """
        Convert business analysis into website structure
        
        Args:
            analysis: Business analysis data
            cost_tracker: Optional CostTracker instance to track AI costs
        
        Returns:
            WebsiteStructure object
        """
        
        system_prompt = f"""You are a website architect. Based on a business analysis, generate a comprehensive website structure.
Begin with a concise checklist (3-7 bullets) of what steps you will perform to generate the site structure; keep items high-level and conceptual.
        
Your task:
1. Create page structures for each key page - {', '.join(analysis.key_pages)}
2. Define components/sections for each page based on content_sections - {', '.join(analysis.content_sections)}
3. Map business requirements to appropriate React components
4. Ensure logical flow and user experience
5. Determing if its a single page website (ONLY 1 page) or multiple pages website (more than 1 page).
6. If its a single page website, ensure the page is named Home and the path is "/" not "", with header navigation urls pointing to the sections in the page with #menu for menu for example

CRITICAL: Navigation and Pages MUST Match Exactly
7. For EVERY navigation item you create, there MUST be a corresponding page with the EXACT same path
8. For EVERY page you create, there MUST be a corresponding navigation item (except utility pages like 404, privacy)
9. Navigation item path MUST exactly match page path. except for "home" page which must be "/", not "". 
   Example: 
    Navigation: {{label: "About", path: "/about"}}
    Page: {{name: "About", path: "/about"}}
   Example 2 (Always use this pattern for the home/main/entry page):
    Navigation: {{label: "Home", path: "/"}}
    Page: {{name: "Home", path: "/"}}
   There must be a one to one mapping between navigation items and pages
   NEVER do this: 
   - Navigation: {{label: "HomePage", path: "/homePage"}} Page: {{name: "HomePage", path: "/#home"}}
10. Do NOT create navigation items without creating the page
11. Do NOT create pages without adding them to navigation (unless utility pages)
12. ENSURE that all values in the "props" are generated with appropriate values, not just empty strings or numbers. And make use of href for links, not just url.
sample data might look like this for example:
{{
    id: 'linkedin',
    label: 'LinkedIn',
    href: 'https://linkedin.com/in/aureliaphoto', // not "url: ''"
    icon: <ExternalLink className="h-5 w-5" aria-hidden />
}}

CRITICAL: 
- Home path must be /
- Page and component names must be joined without spaces, not hyphens. Example: Home, About, ProjectDetail, etc.

Available Component Types:
- header: Header section with logo, navigation, and call-to-action
- hero: Main hero section with CTA
- features: Grid of features/services
- about: About section with story/mission
- testimonials: Customer testimonials
- contact: Contact form and information
- cta: Call-to-action section with CTA
- stats: Statistics/numbers section
- team: Team members grid
- pricing: Pricing tables
- gallery: Image gallery
- faq: Frequently asked questions
- footer: Footer section

Return a complete website structure with all pages and their components."""

        user_prompt = f"""Based on this business analysis, create a complete website structure:

Business Type: {analysis.business_type}
Industry: {analysis.industry}
Site Purpose: {analysis.site_purpose}
Target Audience: {analysis.target_audience}

These pages must be created: {', '.join(analysis.key_pages)}
These content sections must be created: {', '.join(analysis.content_sections)}
These must-have features must be created: {', '.join(analysis.must_have_features)}
Primary CTA: {analysis.primary_cta}

Tone: {analysis.tone}
Style: {', '.join(analysis.style_keywords)}
Colors: {', '.join(analysis.primary_colors)}

Value Propositions:
{chr(10).join(f"- {vp}" for vp in analysis.value_propositions)}

Create a website structure with appropriate pages and components for each page."""
        
        self.google_client.set_max_completion_tokens(8000)
        response, usage = self.google_client.call_openai_api_structured(
            system_prompt,
            user_prompt,
            WebsiteStructure,
            model=settings.analysis_model
        )

        print(f"Usage for structure generation: {usage}")
        
        # Track cost if cost_tracker is provided
        if cost_tracker:
            cost_tracker.track_call(
                service_name="structure_generation",
                model_name=settings.analysis_model,
                usage=usage
            )
        
        return response

