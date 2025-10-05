"""
Template Generator Service
Generates website templates using OpenAI API and component library.
"""

from typing import Dict, Any, Optional, List
import json
import re
from datetime import datetime
from openai import OpenAI, OpenAIError
from app.config import settings
from app.services.components_library import component_library, ComponentType
from app.services.template_validator import validate_template_structure
import logging
import sys
from app.config import settings

logger = logging.getLogger(__name__)


class TemplateGenerationError(Exception):
    """Custom exception for template generation errors"""
    pass


class TemplateGenerator:
    """Main template generator class using OpenAI API"""
    
    def __init__(self):
        """Initialize the template generator"""
        if not settings.openai_api_key:
            raise TemplateGenerationError("OpenAI API key not configured")
        
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"
        # self.model = "gpt-4-turbo-preview"
        self.max_retries = 3
    
    def _normalize_category(self, category: str) -> str:
        """
        Normalize AI-generated category to match database constraints.
        Valid categories: 'business', 'portfolio', 'restaurant', 'services', 'general'
        """
        if not category:
            return 'general'
        
        category = category.lower().strip()
        
        # Category mapping
        category_map = {
            'service': 'services',
            'consultancy': 'services',
            'consulting': 'services',
            'retail': 'business',
            'shop': 'business',
            'store': 'business',
            'ecommerce': 'business',
            'corporate': 'business',
            'startup': 'business',
            'saas': 'business',
            'tech': 'business',
            'technology': 'business',
            'agency': 'services',
            'photography': 'portfolio',
            'creative': 'portfolio',
            'artist': 'portfolio',
            'designer': 'portfolio',
            'food': 'restaurant',
            'cafe': 'restaurant',
            'bar': 'restaurant',
            'restaurant': 'restaurant',
            'business': 'business',
            'services': 'services',
            'portfolio': 'portfolio',
            'general': 'general'
        }
        
        # Return mapped category or 'general' as fallback
        normalized = category_map.get(category, 'general')
        logger.info(f"Category normalized: '{category}' -> '{normalized}'")
        return normalized
    
    def generate_template(
        self,
        prompt: str,
        user_id: str,
        style_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a website template based on user prompt.
        
        Args:
            prompt: User's description of desired website
            user_id: ID of the user generating the template
            style_preferences: Optional style preferences (colors, fonts, etc.)
        
        Returns:
            Dictionary containing generated template data
        
        Raises:
            TemplateGenerationError: If generation fails
        """
        try:
            test_response = None
            if settings.training_wheels:
                from app.data.response_sample import open_ai_response_sample
                test_response = open_ai_response_sample()

            logger.info(f"[STEP 1/8] Starting template generation for user {user_id}")
            logger.info(f"User prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            
            # Prepare component samples for few-shot learning
            logger.info("[STEP 2/8] Preparing component samples from library")
            component_samples = self._prepare_component_samples()
            logger.info(f"Loaded {len(component_samples)} component types with variations")
            
            # Build system prompt with instructions
            logger.info("[STEP 3/8] Building system prompt with component library")
            system_prompt = self._build_system_prompt(component_samples)
            print(f"OPENAI TEMPLATE GENERATION SYSTEM PROMPT: \n{system_prompt}")
            logger.info(f"System prompt prepared ({len(system_prompt)} characters)")
        
            # Build user prompt with preferences
            logger.info("[STEP 4/8] Building user prompt with preferences")
            user_prompt = self._build_user_prompt(prompt, style_preferences)
            print(f"OPENAI TEMPLATE GENERATION USER PROMPT: \n{user_prompt}")
            if style_preferences:
                logger.info(f"Applied style preferences: {list(style_preferences.keys())}")
                
            if not test_response:
                # Call OpenAI API
                logger.info(f"[STEP 5/8] Calling OpenAI API (model: {self.model})")
                response = self._call_openai_api(system_prompt, user_prompt)
                logger.info(f"Received response from OpenAI ({len(response)} characters)")

                logger.info(f"OpenAI response: {response}")
            else:
                logger.info("Skipping STEP 5")
                response = test_response
            # Parse and validate response
            print(f"OPENAI TEMPLATE GENERATION RESPONSE: \n{response}")
            logger.info("[STEP 6/8] Parsing and validating OpenAI response")
            template_data = self._parse_openai_response(response)
            logger.info(f"Parsed template with {len(template_data.get('sections', []))} sections")

            # Auto-fix missing content bindings
            template_data = self._auto_fix_content_schema(template_data)

            # Validate template structure
            logger.info("[STEP 7/8] Validating template structure")
            is_valid, error_msg = validate_template_structure(template_data)
            if not is_valid:
                logger.error(f"Template validation failed: {error_msg}")
                raise TemplateGenerationError(f"Invalid template structure: {error_msg}")
            logger.info("Template structure validation passed")
            
            # Generate preview HTML
            logger.info("[STEP 8/8] Generating preview HTML")
            preview_html = self._generate_preview_html(template_data)
            logger.info(f"Generated preview HTML ({len(preview_html)} characters)")
            
            # Build complete template object
            raw_category = template_data.get("meta", {}).get("category", "general")
            normalized_category = self._normalize_category(raw_category)
            
            template = {
                "name": template_data.get("name", "Generated Template"),
                "description": template_data.get("description", prompt[:200]),
                "sections_config": template_data["sections"],
                "style_config": template_data["style_config"],
                "content_schema": template_data["content_schema"],
                "preview_html": preview_html,
                "category": normalized_category,
                "tags": template_data.get("meta", {}).get("tags", []),
                "is_public": False,
                "created_by": user_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✓ Template '{template['name']}' generated successfully for user {user_id}")
            logger.info(f"  - Category: {template['category']} (from: {raw_category})")
            logger.info(f"  - Sections: {len(template['sections_config'])}")
            logger.info(f"  - Tags: {', '.join(template['tags']) if template['tags'] else 'none'}")
            return template
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise TemplateGenerationError(f"AI generation failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise TemplateGenerationError("Failed to parse AI response")
        except Exception as e:
            logger.error(f"Template generation error: {str(e)}")
            raise TemplateGenerationError(f"Template generation failed: {str(e)}")
    
    def _prepare_component_samples(self) -> Dict[str, Any]:
        """Prepare component samples for the AI prompt"""
        samples = {}
        for component_type in ComponentType:
            variations = component_library.get_all_variations(component_type)
            samples[component_type.value] = {
                var_name: {
                    "name": var_data["name"],
                    "description": var_data["description"],
                    "tags": var_data.get("tags", []),
                    "config": var_data["config"],
                    "content_bindings": var_data["content_bindings"]
                }
                for var_name, var_data in variations.items()
            }
        return samples
    
    def _build_system_prompt(self, component_samples: Dict[str, Any]) -> str:
        """Build the system prompt with instructions and examples"""
        return f"""You are a professional UI/UX expert and web designer. Your task is to generate website templates using a predefined component library.

AVAILABLE COMPONENTS:
{json.dumps(component_samples, indent=2)}

YOUR TASK:
1. Analyze the user's business description and requirements
2. Select 4-7 appropriate sections from the component library
3. Choose component variations that match the desired style and business type
4. Customize colors, fonts, and spacing for brand consistency based on the business type
5. CRITICAL: For each selected component in the content_schema, examine its content_bindings and include ALL bindings that have "required": true in your content_schema
6. Generate a cohesive, professional website structure

SECTION SELECTION GUIDELINES:
- Always include: header, hero, footer (required for every website)
- Business-specific sections: services, about, contact, testimonials, cta
- Choose variations based on content density and style preferences based on the business type
- Consider the business type when selecting components

CONTENT BINDING RULES (CRITICAL):
- Examine the "content_bindings" section of EACH component you select
- For EVERY binding that has "required": true, you MUST include it in your content_schema. Do not exclude any required bindings.
- Copy the exact binding name, type, and placeholder
- Include all required bindings or the template will fail validation
- Example: If you select header "logo-left", you MUST include: logo_url, business_name, nav_items
- Example: If you select cta "banner", you MUST include: cta_title, cta_text, cta_button_text, cta_url
- Example: If you select contact "split-info", you MUST include: business_email, business_phone, whatsapp_number

STYLE CONFIGURATION:
- Primary color: Main brand color (hex code)
- Secondary color: Accent color (hex code)
- Text color: Main text color (hex code)
- Heading color: Heading text color (hex code)
- Background color: Main background (hex code)
- Font family: Primary font (web-safe or Google Fonts)
- Spacing: Consistent spacing scale (sm, md, lg, xl, 2xl)

OUTPUT FORMAT (JSON):
{{
  "name": "Template Name",
  "description": "Brief description of the template",
  "sections": [
    {{
      "component_type": "header",
      "variation": "logo-left",
      "order": 0,
      "config": {{}}
    }},
    ...
  ],
  "style_config": {{
    "colors": {{
      "primary": "#6366f1",
      "secondary": "#8b5cf6",
      "text": "#1f2937",
      "heading": "#111827",
      "background": "#ffffff",
      "border": "#e5e7eb"
    }},
    "typography": {{
      "fontFamily": "'Inter', sans-serif",
      "headingFontFamily": "'Inter', sans-serif",
      "fontSize": "16px",
      "lineHeight": "1.5"
    }},
    "spacing": {{
      "containerMaxWidth": "1200px",
      "sm": "1rem",
      "md": "1.5rem",
      "lg": "2rem",
      "xl": "3rem",
      "2xl": "5rem"
    }}
  }},
  "content_schema": {{
    "business_name": {{
      "type": "text", // ✅ Valid type
      "required": true,
      "placeholder": "Your Business Name"
    }},
    "logo_url": {{
      "type": "image",
      "required": true,
      "placeholder": "Logo URL"
    }},
    "business_email": {{
      "type": "email", // ✅ Valid type
      "required": true,
      "placeholder": "your@email.com"   
    }},
    "services": {{
      "type": "array", // ✅ Valid type
      "required": true,
      "itemSchema": {{
        "title": "string",
        "description": "string"
      }}
    }},
    "submit_button_text": {{
      "type": "text", // ✅ Valid type
      "required": true,
      "default": "Send Message"
    }}
    ...
  }},
  "meta": {{
    "category": "business|portfolio|restaurant|services|general",
    "tags": ["modern", "professional", "warm"]
  }}
}}

FIELD TYPE CONSTRAINTS:
When creating content_schema fields, the "type" field MUST be one of these exact values:
- "text" - for string content (headlines, descriptions, etc.)
- "email" - for email addresses
- "phone" - for phone numbers
- "url" - for web links
- "image" - for image URLs
- "video" - for video URLs
- "array" - for lists of items (services, testimonials, etc.)
- "color" - for color values (hex codes)
DO NOT use any other type values. If unsure, use "text" as the default.

IMPORTANT RULES:
- Only use components and variations that exist in the component library
- CRITICAL: Ensure content_schema includes ALL required bindings from selected components (check "required": true in content_bindings)
- CRITICAL: content_schema field "type" must be one of: "text", "email", "phone", "url", "image", "video", "array", "color" - NO OTHER TYPES ALLOWED
- Style colors must be valid hex codes
- Section order must be sequential (0, 1, 2, ...)
- Don't generate raw HTML - use component references only
- Ensure the design is cohesive and professional

FINAL VALIDATION CHECKLIST:
Before submitting your response:
1. Verify all content_schema field types are from the allowed list
2. Check that no field uses invalid types like "string", "number", "boolean", etc.
3. Ensure array fields have proper itemSchema structure
4. Confirm all required fields from component bindings are included
"""
    

    def _build_user_prompt(
        self,
        prompt: str,
        style_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the user prompt with request details"""
        user_prompt = f"USER REQUEST:\n{prompt}\n"
        
        if style_preferences:
            user_prompt += f"\nSTYLE PREFERENCES:\n{json.dumps(style_preferences, indent=2)}\n"
        
        user_prompt += "\nPlease generate a website template that matches this description."
        return user_prompt
    
    def _call_openai_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API with retry logic"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to OpenAI (attempt {attempt + 1}/{self.max_retries})")
                if self.model == "gpt-5-mini" or self.model == "gpt-5":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_completion_tokens=4000,
                        response_format={"type": "json_object"}
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4000,
                        response_format={"type": "json_object"}
                    )
                
                logger.info(f"OpenAI API call successful (tokens used: ~{len(response.choices[0].message.content) // 4})")
                return response.choices[0].message.content
                
            except OpenAIError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠ OpenAI API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    logger.info(f"Retrying in next attempt...")
                    continue
                logger.error(f"✗ All retry attempts exhausted. Final error: {str(e)}")
                raise
    
    def _parse_openai_response(self, response: str) -> Dict[str, Any]:
        """Parse and clean OpenAI response"""
        # Parse JSON response
        data = json.loads(response)
        
        # Validate required fields
        required_fields = ["sections", "style_config", "content_schema"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Ensure sections is a list
        if not isinstance(data["sections"], list):
            raise ValueError("sections must be a list")
        
        logger.info(f"Template structure contains {len(data['sections'])} sections:")
        
        # Validate each section has required fields
        for i, section in enumerate(data["sections"]):
            required_section_fields = ["component_type", "variation"]
            for field in required_section_fields:
                if field not in section:
                    raise ValueError(f"Section {i} missing required field: {field}")
            
            # Ensure order is set
            if "order" not in section:
                section["order"] = i
            
            # Ensure config is a dict
            if "config" not in section:
                section["config"] = {}
            
            # Log section details
            logger.info(f"  [{i}] {section['component_type']}:{section['variation']}")
        
        # Log style configuration
        if "colors" in data.get("style_config", {}):
            primary_color = data["style_config"]["colors"].get("primary", "N/A")
            logger.info(f"Primary color: {primary_color}")
        
        return data
    
    def _auto_fix_content_schema(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-fix missing required content bindings in content_schema"""
        content_schema = template_data.get("content_schema", {})
        sections = template_data.get("sections", [])
        
        # Collect all required bindings from components
        for section in sections:
            component_type = section.get("component_type")
            variation = section.get("variation")
            
            component = component_library.get_component(
                ComponentType(component_type),
                variation
            )
            
            if component:
                content_bindings = component.get("content_bindings", {})
                for binding_name, binding_config in content_bindings.items():
                    # If binding is required and not in schema, add it
                    if isinstance(binding_config, dict) and binding_config.get("required", False):
                        if binding_name not in content_schema:
                            logger.warning(f"Auto-adding missing required binding: {binding_name}")
                            content_schema[binding_name] = {
                                "type": binding_config.get("type", "text"),
                                "required": True,
                                "placeholder": binding_config.get("placeholder", f"Enter {binding_name}"),
                                "default": binding_config.get("default")
                            }
        
        template_data["content_schema"] = content_schema
        return template_data
    
    def _generate_preview_html(self, template_data: Dict[str, Any]) -> str:
        """Generate preview HTML for the template"""
        sections = template_data.get("sections", [])
        style_config = template_data.get("style_config", {})
        
        logger.info(f"Generating preview HTML for {len(sections)} sections")
        
        # Build CSS variables from style config
        css_vars = self._build_css_variables(style_config)
        logger.info(f"Built CSS variables from style configuration")
        
        # Start HTML
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "<style>",
            ":root {",
            css_vars,
            "}",
            "* { margin: 0; padding: 0; box-sizing: border-box; }",
            "body { font-family: var(--font-family); font-size: var(--font-size); line-height: var(--line-height); color: var(--color-text); }",
            "</style>",
            "</head>",
            "<body>"
        ]
        
        # Add simplified component previews
        components_added = 0
        for section in sorted(sections, key=lambda s: s.get("order", 0)):
            component_type = section.get("component_type")
            variation = section.get("variation")
            
            # Get component from library
            component = component_library.get_component(
                ComponentType(component_type),
                variation
            )
            
            if component:
                # Add component CSS
                html_parts.append(f"<style>{component['css']}</style>")
                
                # Add simplified HTML preview
                html_preview = self._create_preview_section(component_type, variation)
                html_parts.append(html_preview)
                components_added += 1
                logger.info(f"  Added {component_type}:{variation} to preview")
            else:
                logger.warning(f"  Component {component_type}:{variation} not found in library")
        
        html_parts.extend(["</body>", "</html>"])
        
        logger.info(f"Preview HTML generation complete ({components_added}/{len(sections)} components added)")
        return "\n".join(html_parts)
    
    def _build_css_variables(self, style_config: Dict[str, Any]) -> str:
        """Build CSS variables from style config"""
        variables = []
        
        # Colors
        colors = style_config.get("colors", {})
        for key, value in colors.items():
            variables.append(f"  --color-{key}: {value};")
        
        # Typography
        typography = style_config.get("typography", {})
        if "fontFamily" in typography:
            variables.append(f"  --font-family: {typography['fontFamily']};")
        if "fontSize" in typography:
            variables.append(f"  --font-size: {typography['fontSize']};")
        if "lineHeight" in typography:
            variables.append(f"  --line-height: {typography['lineHeight']};")
        
        # Spacing
        spacing = style_config.get("spacing", {})
        for key, value in spacing.items():
            var_key = key.replace('_', '-')
            variables.append(f"  --spacing-{var_key}: {value};")
        
        return "\n".join(variables)
    
    def _create_preview_section(self, component_type: str, variation: str) -> str:
        """Create a simplified preview section"""
        # Simplified preview representations
        previews = {
            "header": f"<div style='padding: 1rem; background: var(--color-background); border-bottom: 1px solid var(--color-border);'><strong>Header ({variation})</strong></div>",
            "hero": f"<div style='padding: 4rem 2rem; background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%); color: white; text-align: center;'><h1>Hero Section ({variation})</h1></div>",
            "services": f"<div style='padding: 3rem 2rem; background: var(--color-background);'><h2>Services ({variation})</h2><p>Service cards will appear here</p></div>",
            "about": f"<div style='padding: 3rem 2rem;'><h2>About Section ({variation})</h2></div>",
            "testimonials": f"<div style='padding: 3rem 2rem; background: var(--color-background);'><h2>Testimonials ({variation})</h2></div>",
            "cta": f"<div style='padding: 3rem 2rem; background: var(--color-primary); color: white; text-align: center;'><h2>Call to Action ({variation})</h2></div>",
            "contact": f"<div style='padding: 3rem 2rem;'><h2>Contact ({variation})</h2></div>",
            "footer": f"<div style='padding: 2rem; background: var(--color-heading); color: white; text-align: center;'><strong>Footer ({variation})</strong></div>"
        }
        
        return previews.get(component_type, f"<div>{component_type} - {variation}</div>")

    def parse_openai_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI response"""
        template_data = self._parse_openai_response(response)
        return template_data

# Export singleton instance
template_generator = TemplateGenerator()

