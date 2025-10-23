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
        Uses component hierarchy from enhanced selector script.

        Args:
            selected_element: Element data from selector (with component hierarchy)
            components: Dictionary of available project files

        Returns:
            Component file path or None if not found
        """
        try:
            # Get component hierarchy from new selector structure
            component_info = selected_element.get('component', {})
            component_file = component_info.get('componentFile')
            component_name = component_info.get('componentName')

            # PRIORITY 1: Use data-file attribute directly (most reliable)
            if component_file:
                if component_file in components:
                    logger.info(f"[COMPONENT EDITOR] ✓ Found component from data-file: {component_file}")
                    return component_file
                else:
                    logger.warning(f"[COMPONENT EDITOR] data-file '{component_file}' not found in project files")

            # PRIORITY 2: Use data-component attribute to construct path
            if component_name:
                logger.info(f"[COMPONENT EDITOR] Trying to find component: {component_name}")
                # Check common component locations
                possible_paths = [
                    f"src/components/{component_name}.tsx",
                    f"src/components/{component_name}.jsx",
                    f"src/components/sections/{component_name}.tsx",
                    f"src/components/sections/{component_name}.jsx"
                ]

                for path in possible_paths:
                    if path in components:
                        logger.info(f"[COMPONENT EDITOR] ✓ Found component file for {component_name}: {path}")
                        return path

                logger.warning(f"[COMPONENT EDITOR] Component '{component_name}' not found in expected locations")

            # FALLBACK: Try legacy attributes (for backward compatibility)
            legacy_data_file = selected_element.get('attributes', {}).get('data-file')
            if legacy_data_file and legacy_data_file in components:
                logger.info(f"[COMPONENT EDITOR] ✓ Found component from legacy data-file: {legacy_data_file}")
                return legacy_data_file

            legacy_data_component = selected_element.get('attributes', {}).get('data-component')
            if legacy_data_component:
                possible_paths = [
                    f"src/components/{legacy_data_component}.tsx",
                    f"src/components/{legacy_data_component}.jsx",
                ]
                for path in possible_paths:
                    if path in components:
                        logger.info(f"[COMPONENT EDITOR] ✓ Found component from legacy data-component: {path}")
                        return path
            
            # PRIORITY 3: Simplified heuristic fallback (last resort)
            logger.warning("[COMPONENT EDITOR] ⚠ No data attributes found, using heuristic detection (unreliable)")

            # Get element path for context
            path_str = ' '.join(selected_element.get('path', [])).lower()
            available_components = set(components.keys())

            # Helper function to find matching component
            def find_component_like(pattern: str) -> Optional[str]:
                """Find component that matches pattern (case-insensitive)"""
                pattern_lower = pattern.lower()
                matches = [c for c in available_components if pattern_lower in c.lower()]
                return min(matches, key=len) if matches else None

            # Simple pattern matching based on DOM structure
            component = None

            # Try to match by path structure
            if 'header' in path_str or 'nav' in path_str:
                component = find_component_like("header")
                logger.info(f"[COMPONENT EDITOR] Heuristic: Detected header/nav in path → {component}")
            elif 'footer' in path_str:
                component = find_component_like("footer")
                logger.info(f"[COMPONENT EDITOR] Heuristic: Detected footer in path → {component}")
            elif 'main' in path_str or 'section' in path_str:
                # Try common section names
                component = (find_component_like("hero") or
                           find_component_like("about") or
                           find_component_like("services") or
                           find_component_like("home"))
                logger.info(f"[COMPONENT EDITOR] Heuristic: Detected main/section → {component}")

            if component:
                return component

            # Final fallback: Use first available page/component
            fallback = (find_component_like("home") or
                       find_component_like("page") or
                       list(available_components)[0] if available_components else None)

            if fallback:
                logger.warning(f"[COMPONENT EDITOR] ⚠ Using absolute fallback: {fallback}")
                return fallback

            logger.error("[COMPONENT EDITOR] ✗ No components found in project")
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
            element_info: Selected element information (with component hierarchy)

        Returns:
            Analysis of the edit request
        """
        instruction_lower = instruction.lower()

        # Determine edit type
        edit_type = "unknown"
        if any(word in instruction_lower for word in ['color', 'background', 'text', 'font', 'size', 'padding', 'margin', 'border', 'style']):
            edit_type = "style"
        elif any(word in instruction_lower for word in ['text', 'content', 'title', 'heading', 'button', 'label', 'change', 'wording']):
            edit_type = "content"
        elif any(word in instruction_lower for word in ['add', 'remove', 'delete', 'create', 'insert']):
            edit_type = "structure"

        # Extract target element info from new structure
        component_info = element_info.get('component', {})
        target_element = component_info.get('elementName') or element_info.get('attributes', {}).get('data-element', 'unknown')
        component_name = component_info.get('componentName') or element_info.get('attributes', {}).get('data-component', 'Unknown')

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
