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


    def _search_text_in_jsx_props(self, component_name: str, text_content: str, file_content: str) -> bool:
        """
        Search for text content in JSX props when using a component.

        Args:
            component_name: Name of the component (e.g., "HeroSection")
            text_content: The text to search for
            file_content: Content of the file to search in

        Returns:
            True if text is found in component props, False otherwise
        """
        # Escape special regex characters in text
        escaped_text = re.escape(text_content)

        # Pattern to match component usage with the text in any prop
        # Matches: <ComponentName ...prop="...text..."... >
        # Handles multiline, single/double quotes, and various prop formats
        patterns = [
            # Double quotes: prop="text"
            rf'<{component_name}[^>]*\s+\w+\s*=\s*"[^"]*{escaped_text}[^"]*"[^>]*>',
            # Single quotes: prop='text'
            rf"<{component_name}[^>]*\s+\w+\s*=\s*'[^']*{escaped_text}[^']*'[^>]*>",
            # Template literals or JSX expressions: prop={`text`} or prop={"text"}
            rf'<{component_name}[^>]*\s+\w+\s*=\s*{{[^}}]*{escaped_text}[^}}]*}}[^>]*>',
        ]

        for pattern in patterns:
            if re.search(pattern, file_content, re.DOTALL | re.MULTILINE):
                return True

        # Also check for text in children: <Component>text</Component>
        children_pattern = rf'<{component_name}[^>]*>.*?{escaped_text}.*?</{component_name}>'
        if re.search(children_pattern, file_content, re.DOTALL):
            return True

        return False

    async def _find_parent_component_using_prop(
        self,
        component_file: str,
        component_name: Optional[str],
        text_content: str,
        all_files: Dict[str, str]
    ) -> Optional[str]:
        """
        Find the parent component/page that uses a component with specific prop text.

        This is the core of prop tracing - it identifies when selected text is passed
        as a prop to a component, rather than being hardcoded in the component itself.

        Args:
            component_file: Path to the component file (e.g., "src/components/HeroSection.tsx")
            component_name: Name of the component (e.g., "HeroSection")
            text_content: The text content selected by user
            all_files: Dictionary of all project files

        Returns:
            File path of parent component/page that passes the prop, or None
        """
        try:
            # First, check if text is hardcoded in the component itself
            component_code = all_files.get(component_file, '')
            if text_content in component_code:
                # Text is hardcoded in component, not a prop - edit the component
                logger.info(f"[PROP TRACE] Text is hardcoded in {component_file}, not a prop")
                return None

            logger.info(f"[PROP TRACE] Text not found in component, searching for parent that passes it as prop...")

            if not component_name:
                # Extract component name from file path
                component_name = component_file.split('/')[-1].replace('.tsx', '').replace('.jsx', '')

            # Search through all files for usage of this component with the text
            parent_candidates = []

            for file_path, file_content in all_files.items():
                # Skip the component file itself
                if file_path == component_file:
                    continue

                # Skip non-tsx/jsx files
                if not (file_path.endswith('.tsx') or file_path.endswith('.jsx')):
                    continue

                # Check if this file imports and uses the component
                if component_name in file_content:
                    # Check if the text appears in props when using the component
                    if self._search_text_in_jsx_props(component_name, text_content, file_content):
                        logger.info(f"[PROP TRACE] Found text in {file_path} props for {component_name}")
                        parent_candidates.append(file_path)

            if not parent_candidates:
                logger.info(f"[PROP TRACE] No parent components found using {component_name} with this text")
                return None

            # Prioritize pages over components
            page_files = [f for f in parent_candidates if '/pages/' in f]
            if page_files:
                logger.info(f"[PROP TRACE] ✓ Found parent page: {page_files[0]}")
                return page_files[0]

            # Return first component found
            logger.info(f"[PROP TRACE] ✓ Found parent component: {parent_candidates[0]}")
            return parent_candidates[0]

        except Exception as e:
            logger.error(f"[PROP TRACE] Error tracing prop: {str(e)}")
            return None

    async def identify_component(self, selected_element: Dict[str, Any], components: Dict[str, str]) -> Optional[str]:
        """
        Identify which component file to edit based on selected element data.
        Uses component hierarchy from enhanced selector script.

        NEW: Implements prop tracing - if selected text is a prop value (not hardcoded),
        finds and returns the parent page/component that passes that prop.

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
            selected_text = selected_element.get('textContent', '').strip()

            # PRIORITY 1: Use data-file attribute directly (most reliable)
            if component_file:
                if component_file in components:
                    logger.info(f"[COMPONENT EDITOR] ✓ Found component from data-file: {component_file}")

                    # NEW: Check if selected text is a prop value or hardcoded
                    if selected_text and len(selected_text) > 10:  # Only trace meaningful text
                        parent_file = await self._find_parent_component_using_prop(
                            component_file, component_name, selected_text, components
                        )
                        if parent_file:
                            logger.info(f"[COMPONENT EDITOR] ✓ Text is prop value, editing parent: {parent_file}")
                            return parent_file

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

                        # NEW: Check if selected text is a prop value or hardcoded
                        if selected_text and len(selected_text) > 10:
                            parent_file = await self._find_parent_component_using_prop(
                                path, component_name, selected_text, components
                            )
                            if parent_file:
                                logger.info(f"[COMPONENT EDITOR] ✓ Text is prop value, editing parent: {parent_file}")
                                return parent_file

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
    ) -> Tuple[bool, str, str, Optional[str]]:
        """
        Use AI to modify component code based on user instruction.

        Args:
            file_path: Path to the component file
            instruction: User's natural language instruction
            element_context: Context about the selected element
            project_id: Project ID for loading current code

        Returns:
            Tuple of (success, old_code, modified_code, error_message)
        """
        try:
            # Load current component code
            files = await project_file_manager.get_project_files(project_id)
            current_code = files.get(file_path)

            if not current_code:
                return False, "", "", f"Component file {file_path} not found in project"

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
                return False, current_code, "", "AI did not return any code"

            # Extract code from response (handle markdown code blocks)
            modified_code = self._extract_code_from_response(response)

            if not modified_code:
                return False, current_code, "", "Could not extract valid code from AI response"

            # Basic validation
            if not self._validate_component_code(modified_code):
                return False, current_code, "", "Generated code appears to be invalid"

            logger.info(f"[COMPONENT EDITOR] Successfully modified {file_path}")
            return True, current_code, modified_code, None

        except Exception as e:
            logger.error(f"[COMPONENT EDITOR] Error modifying component: {str(e)}")
            return False, "", "", f"Error modifying component: {str(e)}"

    async def generate_edit_description(
        self,
        instruction: str,
        element_context: Dict[str, Any],
        file_path: str
    ) -> str:
        """
        Generate a human-readable description of the edit that was made.

        Args:
            instruction: Original user instruction
            element_context: Context about the selected element
            file_path: Path to the component file that was edited

        Returns:
            A brief description of what was changed
        """
        try:
            component_info = element_context.get('component', {})
            component_name = component_info.get('componentName')
            element_name = component_info.get('elementName')
            selected_text = element_context.get('textContent', '').strip()
            tag_name = element_context.get('tagName', '')

            # Extract file name from path for display
            file_name = file_path.split('/')[-1].replace('.tsx', '').replace('.jsx', '')

            # Determine if this was a prop edit or component edit based on file path
            is_page_edit = '/pages/' in file_path
            is_prop_edit = is_page_edit or (component_name and component_name not in file_path)

            # Build a clear, informative description
            description_parts = []

            # Part 1: What was edited
            if is_prop_edit and component_name:
                # Editing props in a parent component/page
                description_parts.append(f"Edited {component_name} component")

                # Try to infer which prop was edited based on selected text
                if selected_text and len(selected_text) > 10:
                    # Truncate long text for readability
                    text_preview = selected_text[:40] + "..." if len(selected_text) > 40 else selected_text
                    description_parts.append(f'updated prop with text "{text_preview}"')

                description_parts.append(f"in {file_name} page")
            else:
                # Editing component internals
                if element_name:
                    description_parts.append(f"Edited {element_name}")
                elif tag_name:
                    description_parts.append(f"Edited {tag_name} element")
                elif selected_text and len(selected_text) > 10:
                    text_preview = selected_text[:40] + "..." if len(selected_text) > 40 else selected_text
                    description_parts.append(f'Edited element with text "{text_preview}"')
                else:
                    description_parts.append("Edited component")

                if component_name:
                    description_parts.append(f"in {component_name}")
                else:
                    description_parts.append(f"in {file_name}")

            # Combine parts
            description = " ".join(description_parts)

            # Part 2: What kind of change based on instruction
            instruction_lower = instruction.lower()
            change_type = None

            if 'color' in instruction_lower or 'background' in instruction_lower:
                change_type = "Modified colors/styling"
            elif 'text' in instruction_lower or 'content' in instruction_lower or 'change' in instruction_lower or 'update' in instruction_lower:
                change_type = "Changed text content"
            elif 'size' in instruction_lower or 'font' in instruction_lower:
                change_type = "Adjusted sizing/typography"
            elif 'add' in instruction_lower or 'create' in instruction_lower:
                change_type = "Added new elements"
            elif 'remove' in instruction_lower or 'delete' in instruction_lower:
                change_type = "Removed elements"

            if change_type:
                description = f"{description}. {change_type}."
            else:
                # Include the instruction as context
                instruction_excerpt = instruction[:60] + "..." if len(instruction) > 60 else instruction
                description = f"{description}. {instruction_excerpt}"

            logger.info(f"[COMPONENT EDITOR] Generated description: {description}")
            return description

        except Exception as e:
            logger.error(f"[COMPONENT EDITOR] Error generating description: {str(e)}", exc_info=True)
            # Fallback to a basic but informative description
            file_name = file_path.split('/')[-1].replace('.tsx', '').replace('.jsx', '')
            return f"Updated {file_name}. {instruction[:60]}"

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
        selected_text = element_context.get('textContent', '').strip()

        # Determine if we're editing a prop value or component internals
        is_prop_edit = False
        component_info = element_context.get('component', {})
        actual_component_name = component_info.get('componentName')

        # Check if selected text appears in prop context
        if actual_component_name and selected_text and len(selected_text) > 10:
            # Simple heuristic: if component name appears in code with the selected text nearby, likely a prop
            if f'<{actual_component_name}' in current_code and selected_text in current_code:
                # Text appears in a component usage context
                is_prop_edit = True

        # Build context-aware prompt
        if is_prop_edit:
            context_note = f"""
CONTEXT: This is a PAGE/PARENT COMPONENT that uses the <{actual_component_name}> component.
You are editing the PROP VALUES passed to {actual_component_name}, not the component itself.

SPECIFIC GUIDANCE:
- Find where <{actual_component_name}> is used in this code
- Modify the prop value that contains: "{selected_text}"
- Do NOT modify the component definition or import
- Only change the specific prop value as instructed
"""
        else:
            context_note = f"""
CONTEXT: This is the component definition itself.
You are editing the component's internal structure and content.

SPECIFIC GUIDANCE:
- Modify the element/text: "{selected_text}"
- Keep the component's prop interface unchanged unless necessary
- Maintain the component's export and structure
"""

        prompt = f"""You are a React component editor. Modify the following code based on the user's instruction.

{context_note}

CODE TO EDIT:
```tsx
{current_code}
```

USER INSTRUCTION:
"{instruction}"

TARGET INFORMATION:
- Element: {target_element}
- Tag: {element_context.get('tagName', '')}
- Text: "{selected_text}"
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
9. Maintain all data attributes (data-component, data-file, data-element)

IMPORTANT:
- Return ONLY the complete modified code
- Do not include explanations or markdown formatting
- The code should be ready to use as-is
- Keep all existing imports and structure intact

Return the complete modified code:"""

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
