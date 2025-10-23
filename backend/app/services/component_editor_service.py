"""
Component Editor Service
Handles AI-powered component modification for visual editing
"""

import logging
import re
from typing import Dict, Any, Optional, Tuple
from app.services.project_file_manager import project_file_manager
from app.services.prompt_open_ai import PromptOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class ComponentEditorService:
    """Service for AI-powered component editing"""
    
    def __init__(self):
        self.prompt_service = PromptOpenAI(api_key=settings.google_api_key, url="https://generativelanguage.googleapis.com/v1beta/openai/")

    
    async def identify_component(self, selected_element: Dict[str, Any], components: Dict[str, str]) -> Optional[str]:
        """
        Identify which component file to edit based on selected element data.
        Uses a stable hierarchical approach based on DOM structure and file existence.
        
        Args:
            selected_element: Element data from selector
            components: Dictionary of available project files
            
        Returns:
            Component file path or None if not found
        """
        try:
            # First try to get from data-file attribute (most reliable)
            data_file = selected_element.get('attributes', {}).get('data-file')
            if data_file and data_file in components:
                logger.info(f"[COMPONENT EDITOR] Found component file from data-file: {data_file}")
                return data_file
            
            # Second: try to match by data-component attribute
            data_component = selected_element.get('attributes', {}).get('data-component')
            if data_component:
                # Check if component exists in project
                possible_paths = [
                    f"src/components/{data_component}.tsx",
                    f"src/components/{data_component}.jsx",
                    f"src/components/sections/{data_component}.tsx",
                    f"src/components/sections/{data_component}.jsx"
                ]
                
                for path in possible_paths:
                    if path in components:
                        logger.info(f"[COMPONENT EDITOR] Found component file for {data_component}: {path}")
                        return path
            
            # Fallback: Stable hierarchical detection based on DOM structure
            logger.info("[COMPONENT EDITOR] No data attributes found, using stable hierarchical detection")
            
            tag_name = selected_element.get('tagName', '').lower()
            path = selected_element.get('path', [])
            text_content = selected_element.get('textContent', '').strip()
            classes = selected_element.get('classList', [])
            selector = selected_element.get('selector', '').lower()
            
            # Convert path to string for easier matching
            path_str = ' '.join(path).lower()
            classes_str = ' '.join(classes).lower()
            
            # Get available components
            available_components = set(components.keys())
            logger.info(f"[COMPONENT EDITOR] Available components: {len(available_components)} files")
            
            # Helper function to find best matching component
            def find_component_like(pattern: str) -> Optional[str]:
                """Find component that matches pattern (case-insensitive)"""
                pattern_lower = pattern.lower()
                matches = []
                for component_path in available_components:
                    if pattern_lower in component_path.lower():
                        matches.append(component_path)
                
                if matches:
                    # Return the most specific match (shortest path)
                    return min(matches, key=len)
                return None
            

            # STABLE HIERARCHICAL DETECTION - Based on DOM structure and file existence
            
            # 1. HEADER DETECTION - Most specific, based on DOM position
            if (tag_name in ['nav', 'header', 'a', 'button'] and 
                ('header' in path_str or 'nav' in path_str or 'navigation' in path_str)):
                logger.info(f"[COMPONENT EDITOR] Detected Header/Navigation element (tag: {tag_name})")
                header_component = find_component_like("header")
                if header_component:
                    logger.info(f"[COMPONENT EDITOR] Found Header component: {header_component}")
                    return header_component
                else:
                    logger.warning("[COMPONENT EDITOR] Header component not found, will use fallback")
            
            # 2. FOOTER DETECTION - Most specific, based on DOM position  
            elif (tag_name in ['footer', 'p', 'a', 'div'] and 'footer' in path_str):
                logger.info(f"[COMPONENT EDITOR] Detected Footer element (tag: {tag_name})")
                footer_component = find_component_like("footer")
                if footer_component:
                    logger.info(f"[COMPONENT EDITOR] Found Footer component: {footer_component}")
                    return footer_component
                else:
                    logger.warning("[COMPONENT EDITOR] Footer component not found, will use fallback")
            
            # 3. HERO SECTION DETECTION - Based on content and position
            elif (tag_name in ['h1', 'h2', 'button', 'p'] and 
                  ('section' in path_str or 'main' in path_str) and
                  any(keyword in text_content.lower() for keyword in ['welcome', 'hero', 'artistry', 'discover', 'get started', 'learn more', 'welcome to', 'introducing'])):
                logger.info(f"[COMPONENT EDITOR] Detected Hero section (tag: {tag_name}, text: '{text_content[:30]}...')")
                hero_component = find_component_like("hero")
                if hero_component:
                    logger.info(f"[COMPONENT EDITOR] Found Hero component: {hero_component}")
                    return hero_component
                else:
                    logger.warning("[COMPONENT EDITOR] Hero component not found, will use fallback")
            
            # 4. SECTION-BASED DETECTION - Based on content keywords
            elif any(keyword in text_content.lower() for keyword in ['about', 'our story', 'who we are', 'mission', 'vision', 'about us']):
                logger.info(f"[COMPONENT EDITOR] Detected About section (text: '{text_content[:30]}...')")
                about_component = find_component_like("about")
                if about_component:
                    logger.info(f"[COMPONENT EDITOR] Found About component: {about_component}")
                    return about_component
                else:
                    logger.warning("[COMPONENT EDITOR] About component not found, will use fallback")
            
            elif any(keyword in text_content.lower() for keyword in ['service', 'feature', 'what we offer', 'our services', 'services']):
                logger.info(f"[COMPONENT EDITOR] Detected Services section (text: '{text_content[:30]}...')")
                services_component = find_component_like("service")
                if services_component:
                    logger.info(f"[COMPONENT EDITOR] Found Services component: {services_component}")
                    return services_component
                else:
                    logger.warning("[COMPONENT EDITOR] Services component not found, will use fallback")
            
            elif any(keyword in text_content.lower() for keyword in ['contact', 'get in touch', 'reach us', 'email', 'phone', 'contact us']):
                logger.info(f"[COMPONENT EDITOR] Detected Contact section (text: '{text_content[:30]}...')")
                contact_component = find_component_like("contact")
                if contact_component:
                    logger.info(f"[COMPONENT EDITOR] Found Contact component: {contact_component}")
                    return contact_component
                else:
                    logger.warning("[COMPONENT EDITOR] Contact component not found, will use fallback")
            
            elif any(keyword in text_content.lower() for keyword in ['testimonial', 'review', 'what people say', 'customer', 'client']):
                logger.info(f"[COMPONENT EDITOR] Detected Testimonials section (text: '{text_content[:30]}...')")
                testimonials_component = find_component_like("testimonial")
                if testimonials_component:
                    logger.info(f"[COMPONENT EDITOR] Found Testimonials component: {testimonials_component}")
                    return testimonials_component
                else:
                    logger.warning("[COMPONENT EDITOR] Testimonials component not found, will use fallback")
            
            # 5. GENERIC SECTION DETECTION
            elif tag_name == 'section':
                logger.info(f"[COMPONENT EDITOR] Generic section tag detected")
                section_component = find_component_like("section")
                if section_component:
                    logger.info(f"[COMPONENT EDITOR] Found section component: {section_component}")
                    return section_component
                else:
                    logger.warning("[COMPONENT EDITOR] No section component found, will use fallback")
            
            # 6. MAIN PAGE DETECTION - If within main tag
            elif 'main' in path_str:
                logger.info(f"[COMPONENT EDITOR] Element is within main tag, targeting main page")
                main_component = find_component_like("home") or find_component_like("main") or find_component_like("index")
                if main_component:
                    logger.info(f"[COMPONENT EDITOR] Found main page component: {main_component}")
                    return main_component
                else:
                    logger.warning("[COMPONENT EDITOR] No main page component found, will use fallback")
            
            # 7. FINAL FALLBACK - Find any page or component
            logger.warning(f"[COMPONENT EDITOR] Could not identify specific component, using final fallback (tag: {tag_name})")
            
            # Try to find any page component first
            page_component = find_component_like("page") or find_component_like("home") or find_component_like("main") or find_component_like("index")
            if page_component:
                logger.info(f"[COMPONENT EDITOR] Found page component as fallback: {page_component}")
                return page_component
            
            # If no page found, try to find any component
            if available_components:
                # Get the first available component as absolute fallback
                fallback_component = list(available_components)[0]
                logger.warning(f"[COMPONENT EDITOR] Using first available component as fallback: {fallback_component}")
                return fallback_component
            
            # Ultimate fallback
            logger.error("[COMPONENT EDITOR] No components found in project")
            return None
            
        except Exception as e:
            logger.error(f"[COMPONENT EDITOR] Error identifying component: {str(e)}")
            # On error, default to Home page as safe fallback
            return "src/pages/Home.tsx"
    
    def analyze_edit_request(self, instruction: str, element_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the edit request to determine what type of changes are needed.
        
        Args:
            instruction: User's natural language instruction
            element_info: Selected element information
            
        Returns:
            Analysis of the edit request
        """
        instruction_lower = instruction.lower()
        
        # Determine edit type
        edit_type = "unknown"
        if any(word in instruction_lower for word in ['color', 'background', 'text', 'font', 'size', 'padding', 'margin', 'border', 'style']):
            edit_type = "style"
        elif any(word in instruction_lower for word in ['text', 'content', 'title', 'heading', 'button', 'label', 'change']):
            edit_type = "content"
        elif any(word in instruction_lower for word in ['add', 'remove', 'delete', 'create', 'insert']):
            edit_type = "structure"
        
        # Extract target element info
        target_element = element_info.get('attributes', {}).get('data-element', 'unknown')
        component_name = element_info.get('attributes', {}).get('data-component', 'Unknown')
        
        return {
            "edit_type": edit_type,
            "target_element": target_element,
            "component_name": component_name,
            "instruction": instruction,
            "element_tag": element_info.get('tagName', ''),
            "element_text": element_info.get('textContent', ''),
            "element_classes": element_info.get('classList', [])
        }
    
    async def modify_component_code(
        self, 
        file_path: str, 
        instruction: str, 
        element_context: Dict[str, Any],
        project_id: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Use AI to modify component code based on user instruction.
        
        Args:
            file_path: Path to the component file
            instruction: User's natural language instruction
            element_context: Context about the selected element
            project_id: Project ID for loading current code
            
        Returns:
            Tuple of (success, modified_code, error_message)
        """
        try:
            # Load current component code
            files = await project_file_manager.get_project_files(project_id)
            current_code = files.get(file_path)
            
            if not current_code:
                return False, "", f"Component file {file_path} not found in project"
            
            # Analyze the edit request
            analysis = self.analyze_edit_request(instruction, element_context)
            
            # Build AI prompt
            prompt = self._build_edit_prompt(current_code, instruction, element_context, analysis)
            
            # Call AI service
            logger.info(f"[COMPONENT EDITOR] Calling AI to modify {file_path}")
            response, usage = self.prompt_service.call_openai_api(
                system_prompt="",
                user_prompt=prompt,
                model="gemini-2.5-flash"
            )
            logger.info(f"[COMPONENT EDITOR] Response from AI: {response}")
            logger.info(f"[COMPONENT EDITOR] Usage for component edit: {usage}")
            if not response or not response.strip():
                return False, "", "AI did not return any code"
            
            # Extract code from response (handle markdown code blocks)
            modified_code = self._extract_code_from_response(response)
            
            if not modified_code:
                return False, "", "Could not extract valid code from AI response"
            
            # Basic validation
            if not self._validate_component_code(modified_code):
                return False, "", "Generated code appears to be invalid"
            
            logger.info(f"[COMPONENT EDITOR] Successfully modified {file_path}")
            return True, modified_code, None
            
        except Exception as e:
            logger.error(f"[COMPONENT EDITOR] Error modifying component: {str(e)}")
            return False, "", f"Error modifying component: {str(e)}"
    
    def _build_edit_prompt(
        self, 
        current_code: str, 
        instruction: str, 
        element_context: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """Build the AI prompt for component editing"""
        
        target_element = analysis.get('target_element', 'unknown')
        component_name = analysis.get('component_name', 'Unknown')
        edit_type = analysis.get('edit_type', 'unknown')
        
        prompt = f"""You are a React component editor. Modify the following component based on the user's instruction.

COMPONENT CODE:
```tsx
{current_code}
```

USER INSTRUCTION:
"{instruction}"

TARGET ELEMENT:
- Element: {target_element}
- Tag: {element_context.get('tagName', '')}
- Text: "{element_context.get('textContent', '')}"
- Classes: {', '.join(element_context.get('classList', []))}
- Component: {component_name}

EDIT TYPE: {edit_type}

REQUIREMENTS:
1. Make ONLY the requested changes - do not modify other parts
2. Preserve all existing functionality and structure
3. Keep the same export style (default or named)
4. Maintain TypeScript types and interfaces
5. Use Tailwind CSS classes for styling
6. Keep the same component name and file structure
7. Ensure the modified element is still accessible and semantic
8. Do not add unnecessary imports or dependencies

IMPORTANT:
- Return ONLY the complete modified component code
- Do not include explanations or markdown formatting
- The code should be ready to use as-is
- Maintain all data attributes (data-component, data-file, data-element)

Return the complete modified component:"""

        return prompt
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from AI response, handling markdown code blocks"""
        # Remove markdown code block markers
        response = re.sub(r'^```(?:tsx|ts|jsx|js)?\n?', '', response, flags=re.MULTILINE)
        response = re.sub(r'\n?```$', '', response, flags=re.MULTILINE)
        
        # Clean up the response
        response = response.strip()
        
        return response
    
    def _validate_component_code(self, code: str) -> bool:
        """Basic validation of component code"""
        if not code or len(code.strip()) < 50:
            return False
        
        # Check for basic React component structure
        if 'export' not in code or 'return' not in code:
            return False
        
        # Check for balanced braces (basic syntax check)
        open_braces = code.count('{')
        close_braces = code.count('}')
        if open_braces != close_braces:
            return False
        
        return True
    
    async def apply_component_edit(
        self, 
        project_id: str, 
        file_path: str, 
        new_code: str
    ) -> Tuple[bool, str]:
        """
        Save the modified component code to the project.
        
        Args:
            project_id: Project ID
            file_path: Path to the component file
            new_code: Modified component code
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Save the updated file
            await project_file_manager.save_project_file(
                project_id=project_id,
                file_path=file_path,
                file_content=new_code
            )
            
            logger.info(f"[COMPONENT EDITOR] Successfully saved {file_path}")
            return True, f"Component {file_path} updated successfully"
            
        except Exception as e:
            logger.error(f"[COMPONENT EDITOR] Error saving component: {str(e)}")
            return False, f"Error saving component: {str(e)}"


# Create singleton instance
component_editor_service = ComponentEditorService()
