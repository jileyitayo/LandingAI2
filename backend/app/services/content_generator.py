"""
Content Generator Service
Generates website content using OpenAI API based on template structure and user prompt.
"""

from typing import Dict, Any, Optional, List
import json
import logging
from openai import OpenAI, OpenAIError
from app.config import settings
from app.utils.supabase_client import get_supabase_client
from app.services.prompt_open_ai import PromptOpenAI
logger = logging.getLogger(__name__)


class ContentGenerationError(Exception):
    """Custom exception for content generation errors"""
    pass


class ContentGenerator:
    """Main content generator class using OpenAI API"""
    
    def __init__(self):
        """Initialize the content generator"""
        if not settings.openai_api_key:
            raise ContentGenerationError("OpenAI API key not configured")
        
        self.prompt_open_ai = PromptOpenAI()
        self.model = self.prompt_open_ai.model
        self.max_retries = self.prompt_open_ai.max_retries
    
    async def generate_content(
        self,
        prompt: str,
        template_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate website content based on user prompt and template structure.
        
        Args:
            prompt: User's business description
            template_id: ID of the template to use
            user_id: ID of the user generating content
        
        Returns:
            Dictionary containing generated content matching content_schema
        
        Raises:
            ContentGenerationError: If generation fails
        """
        try:
            test_response = None
            if settings.training_wheels:
                from app.data.response_sample import content_generator_response_sample
                test_response = content_generator_response_sample()

            logger.info(f"[CONTENT GEN 1/6] Starting content generation for user {user_id}")
            logger.info(f"Template: {template_id}")
            logger.info(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # Fetch template from database
            logger.info("[CONTENT GEN 2/6] Fetching template structure from database")
            template = await self._fetch_template(template_id)
            
            if not template:
                raise ContentGenerationError(f"Template {template_id} not found")
            
            # Extract template configuration
            sections_config = template.get("sections_config", {})
            content_schema = template.get("content_schema", {})
            style_config = template.get("style_config", {})
            
            logger.info(f"Template loaded: {template.get('name', 'Unnamed')}")
            logger.info(f"Sections: {len(sections_config)}")
            logger.info(f"Content fields required: {len(content_schema)}")
            
            # Build system prompt for content generation
            logger.info("[CONTENT GEN 3/6] Building content generation prompt")
            system_prompt = self._build_system_prompt(
                sections_config,
                content_schema,
                style_config
            )
            # print(f"OPENAI CONTENT GENERATION SYSTEM PROMPT: \n{system_prompt}")
            # Build user prompt
            user_prompt = self._build_user_prompt(prompt)
            # print(f"OPENAI CONTENT GENERATION USER PROMPT: \n{user_prompt}")
            if not test_response:
                # Call OpenAI API
                logger.info(f"[CONTENT GEN 4/6] Calling OpenAI API (model: {self.model})")
                response = self._call_openai_api(system_prompt, user_prompt)
                logger.info(f"Received response from OpenAI ({len(response)} characters)")
            else:
                logger.info("Skipping STEP 4")
                response = test_response
            
            # Parse and validate response
            print(f"OPENAI CONTENT GENERATION RESPONSE: \n{response}")
            logger.info("[CONTENT GEN 5/6] Parsing and validating content")
            content_data = self._parse_openai_response(response)
            
            # Validate against content schema
            logger.info("[CONTENT GEN 6/6] Validating content against schema")
            self._validate_content(content_data, content_schema)
            
            logger.info("✓ Content generation completed successfully")
            return {
                "content": content_data.get("content", {}),
                "metadata": {
                    "template_id": template_id,
                    "generated_for": user_id,
                    "business_type": content_data.get("metadata", {}).get("business_type"),
                    "tone": content_data.get("metadata", {}).get("tone")
                }
            }
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise ContentGenerationError(f"AI generation failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise ContentGenerationError("Failed to parse AI response")
        except Exception as e:
            logger.error(f"Content generation error: {str(e)}")
            raise ContentGenerationError(f"Content generation failed: {str(e)}")
    
    async def _fetch_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Fetch template from database"""
        try:
            supabase = get_supabase_client()
            response = supabase.table("templates")\
                .select("*")\
                .eq("id", template_id)\
                .eq("is_active", True)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching template: {str(e)}")
            raise ContentGenerationError(f"Failed to fetch template: {str(e)}")
    
    def _build_system_prompt(
        self,
        sections_config: List[Any],
        content_schema: List[Any],
        style_config: Dict[str, Any]
    ) -> str:
        """Build the system prompt for content generation"""
        
        # Extract sections for context
        section_types = [s["component_type"] for s in sections_config]
        
        return f"""You are an expert content writer specializing in website copy for African businesses.
Your task is to generate compelling, localized content for a business website based on a template structure.

TEMPLATE STRUCTURE:
The website has the following sections: {', '.join(section_types)}

SECTIONS CONFIGURATION:
{json.dumps({"sections": sections_config}, indent=2)}

CONTENT SCHEMA (Required Fields):
{json.dumps({"content_schema": content_schema}, indent=2)}

STYLE CONFIGURATION:
{json.dumps(style_config, indent=2)}

YOUR RESPONSIBILITIES:

1. **Extract Business Information**:
   - Business name and type
   - Products/services offered
   - Target audience
   - Unique selling propositions
   - Contact information

2. **Generate Content for Each Field**:
   - Fill ALL required fields in the content schema
   - Match the field type (text, array, image, etc.)
   - Use appropriate length for each field (headlines short, descriptions longer)
   - Ensure consistency across all content

3. **Localization for African Market**:
   - Use language that resonates with African audiences
   - Include WhatsApp as primary contact method when applicable
   - Consider mobile-first content (shorter, scannable)
   - Use culturally appropriate examples and references
   - Include local payment methods when relevant

4. **Tone and Style**:
   - Match tone to business type (professional for corporate, friendly for retail)
   - Keep content concise and web-friendly
   - Use action-oriented language
   - Create compelling CTAs

5. **Content Best Practices**:
   - Headlines: 5-10 words, attention-grabbing
   - Subheadlines: 10-20 words, benefit-focused
   - Body text: Clear, scannable, value-driven
   - CTAs: Action verbs, urgency, clear value
   - Lists/Arrays: 3-6 items, parallel structure

6. **Required Content Types**:
   - text: String content (headlines, paragraphs)
   - array: Lists of items (services, features, testimonials)
   - image: Image URLs (use placeholder URLs if not provided)
   - email: Valid email format
   - phone: Local phone format (e.g., +234 for Nigeria)
   - url: Valid URLs (use # for placeholders)

PRE-GENERATION CHECKLIST:
1. Read through ALL fields in content_schema and sections_config
2. Identify which fields have "required": true
3. Plan content for each required field
4. Ensure you have content for: logo_url, submit_button_text, and all others
5. Only then proceed to generate the JSON response
Below is a sample output format but ensure to generate the right content for the content_schema and sections_config fields.
SAMPLE OUTPUT FORMAT (JSON):
{{
  "content": {{
    "business_name": "The business name",
    "logo_url": "https://images.unsplash.com/photo-...", // REQUIRED | Generate a related image url using images.unsplash.com
    "sections": [ // REQUIRED | Generate the right content for the sections_config fields
        {{
        "component_type": "header", // can be found in the sections_config fields for header
            "nav_items": [
            {{
                "label": "Home",
                "url": "#home"
            }}
            ],
        }},
      {{
        "component_type": "hero", // can be found in the sections_config fields for hero
        "title": "Compelling headline goes here",
        "subheadline": "Supporting subheadline goes here",
        "description": "description value goes here",
        "image": "image url goes here",
        "cta_text": "cta text value goes here",
        "cta_url": "#cta",
      }}
    ],
    "services": [
      {{
        "title": "Service name",
        "description": "Service description",
        "icon": "icon-name"
      }}
    ],
    "testimonials": [
      {{
        "quote": "Testimonial quote",
        "author_name": "Testimonial author name",
        "author_title": "Testimonial author title"
      }}
    ],
    "about": [
      {{
        "title": "About title",
        "description": "About description",
        "image": "https://images.unsplash.com/photo-..,"
      }}
    ],
    "contact": [
      {{
        "title": "Contact title",
        "description": "Contact description",
        "image": "https://images.unsplash.com/photo-..,"
        "business_email": "contact@business.com",
        "business_phone": "+234 XXX XXX XXXX",
        "whatsapp_number": "+234XXXXXXXXXX",
        "submit_button_text": "Send Message",
        "section_title": "Contact Us",
        "section_description": "We'd love to hear from you",
        "form_action": "#contact",
        "form_fields": [
          {{
            "type": "text",
            "label": "Name",
            "placeholder": "Your name"
          }}
          {{
            "type": "email",
            "label": "Email",
            "placeholder": "Your email"
          }}
          {{
        ]
      }}
    ],
    "cta": [
      {{
        "title": "CTA title",
        "description": "CTA description",
        "image": "https://images.unsplash.com/photo-..,"
      }}
    ],
    ...,
    "footer": [
      {{
        "title": "Footer title",
        "description": "Footer description",
        "image": "https://images.unsplash.com/photo-..,"
      }}
    ]
  }},
  "metadata": {{
    "business_type": "restaurant|consultancy|retail|service|portfolio",
    "tone": "professional|friendly|casual|luxury",
    "target_audience": "Brief description"
  }}
}}

FIELD COMPLETION CHECKLIST:
Before finalizing your response, verify you have included:
- logo_url: Business logo image URL (required for header)
- submit_button_text: Contact form button text (required for contact form)
- All other fields marked as "required": true in content_schema
- Use placeholder images: https://images.unsplash.com/photo-... for missing images | Generate a related image url using images.unsplash.com
- Use default values from schema when available

CRITICAL RULES:
- Generate content in English (can include local language greetings)
- ALL required fields from content_schema MUST be present - NO EXCEPTIONS
- Double-check: logo_url, submit_button_text, and ALL fields with "required": true
- Arrays should have at least the minimum number of items specified
- Phone numbers should use local format
- WhatsApp numbers should be in international format without spaces (+234XXXXXXXXXX)
- Placeholder images should use https://images.unsplash.com/photo-... format | Generate using images.unsplash.com
- Keep content authentic and professional
- Avoid generic corporate speak
- Make CTAs specific and actionable
- FINAL CHECK: Count all required fields in your response before submitting

Generate engaging, conversion-focused content that represents the business authentically."""
    
    def _build_user_prompt(self, prompt: str) -> str:
        """Build the user prompt with business description"""
        return f"""BUSINESS DESCRIPTION:
{prompt}

Please generate complete website content based on this business description.
Ensure all required content fields are filled with appropriate, high-quality content.
Make the content specific to this business, not generic templates.
Use appropriate African localization (WhatsApp, local payment methods, cultural references)."""
    
    def _call_openai_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API with retry logic"""
        return self.prompt_open_ai.call_openai_api(system_prompt, user_prompt)
        
    def _parse_openai_response(self, response: str) -> Dict[str, Any]:
        """Parse and clean OpenAI response"""
        data = json.loads(response)
        
        # Validate required top-level fields
        if "content" not in data:
            raise ValueError("Missing required field: content")
        
        if not isinstance(data["content"], dict):
            raise ValueError("content must be a dictionary")
        
        logger.info(f"Parsed content with {len(data['content'])} fields")
        
        return data
    
    def _validate_content(
        self,
        content_data: Dict[str, Any],
        content_schema: Dict[str, Any]
    ) -> None:
        """Validate generated content against schema"""
        content = content_data.get("content", {})
        missing_fields = []
        
        # Check all required fields are present and add defaults for missing ones
        for field_name, field_config in content_schema.items():
            if isinstance(field_config, dict) and field_config.get("required", False):
                if field_name not in content:
                    missing_fields.append(field_name)
                    # Add default value for missing required fields
                    default_value = field_config.get("default")
                    if default_value is not None:
                        content[field_name] = default_value
                        logger.warning(f"Missing required field '{field_name}', using default: {default_value}")
                    else:
                        # Generate appropriate default based on field type
                        field_type = field_config.get("type", "text")
                        if field_type == "image":
                            content[field_name] = "https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0"
                        elif field_type == "text":
                            content[field_name] = field_config.get("placeholder", "Default text")
                        elif field_type == "email":
                            content[field_name] = "contact@business.com"
                        elif field_type == "phone":
                            content[field_name] = "+234 xxx xxx xxxx"
                        elif field_type == "url":
                            content[field_name] = "#"
                        else:
                            content[field_name] = "Default value"
                        logger.warning(f"Missing required field '{field_name}', generated default based on type: {field_type}")
        
        # Update the content_data with the filled defaults
        content_data["content"] = content
        
        if missing_fields:
            logger.warning(f"Missing required fields were filled with defaults: {', '.join(missing_fields)}")
        
        # Validate field types
        for field_name, field_value in content.items():
            if field_name in content_schema:
                field_config = content_schema[field_name]
                if isinstance(field_config, dict):
                    field_type = field_config.get("type", "text")
                    
                    # Type validation
                    if field_type == "array" and not isinstance(field_value, list):
                        raise ValueError(f"Field {field_name} should be array, got {type(field_value)}")
                    elif field_type == "text" and not isinstance(field_value, str):
                        raise ValueError(f"Field {field_name} should be text, got {type(field_value)}")
        
        logger.info("✓ Content validation passed")

    def parse_openai_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI response"""
        logger.info("[CONTENT GEN 5/6] Parsing and validating content")
        content_data = self._parse_openai_response(response)
        
        return content_data

    def validate_content(self, content_data: Dict[str, Any], content_schema: Dict[str, Any]) -> None:
        """Validate content against schema"""
        logger.info("[CONTENT GEN 6/6] Validating content against schema")
        self._validate_content(content_data, content_schema)
        

# Export singleton instance
content_generator = ContentGenerator()

