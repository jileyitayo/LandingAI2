"""
Component Editor Service
Handles AI-powered component modification for visual editing
"""

import difflib
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from app.services.project_file_manager import project_file_manager
from app.services.prompt_open_ai import PromptOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class ComponentEditorService:
    """Service for AI-powered component editing"""
    
    def __init__(self):
        self.prompt_service = PromptOpenAI(is_google=True)

    def _is_multi_element_selection(self, text_content: str) -> bool:
        """
        Detect if the selected text spans multiple elements.

        Multi-element selections typically:
        - Contain multiple newlines (indicating different elements)
        - Are very long (>200 chars, suggesting multiple text nodes)
        - Contain patterns suggesting multiple distinct pieces (e.g., title + description + list)

        Args:
            text_content: The selected text content

        Returns:
            True if this appears to be a multi-element selection
        """
        if not text_content:
            return False

        # Clean up the text
        cleaned = text_content.strip()

        # Check for multiple newlines (strong indicator)
        newline_count = cleaned.count('\n')
        if newline_count >= 2:
            logger.info(f"[MULTI-ELEMENT] Detected {newline_count} newlines - multi-element selection")
            return True

        # Check for very long selections (likely multiple elements)
        if len(cleaned) > 200:
            logger.info(f"[MULTI-ELEMENT] Text length {len(cleaned)} > 200 - likely multi-element")
            return True

        # Check for patterns suggesting multiple distinct sections
        # (e.g., sentence ending followed by new sentence, suggesting separate elements)
        sentences = [s.strip() for s in cleaned.split('.') if s.strip()]
        if len(sentences) >= 3:
            logger.info(f"[MULTI-ELEMENT] Found {len(sentences)} sentences - likely multi-element")
            return True

        return False

    def _split_selection_into_parts(self, text_content: str) -> list:
        """
        Split a multi-element selection into individual text parts.

        This helps identify which parts are props vs hardcoded.

        Args:
            text_content: The full selected text

        Returns:
            List of text parts (individual strings that might be separate elements)
        """
        if not text_content:
            return []

        # Split by newlines and filter out empty strings
        parts = [part.strip() for part in text_content.split('\n') if part.strip()]

        # If no newlines, try splitting by sentence boundaries for long text
        if len(parts) <= 1 and len(text_content) > 100:
            # Split by periods followed by space and capital letter (sentence boundaries)
            parts = [s.strip() + '.' for s in text_content.split('.') if s.strip()]
            # Remove trailing period from last item if it didn't have one
            if parts and not text_content.endswith('.'):
                parts[-1] = parts[-1].rstrip('.')

        logger.info(f"[MULTI-ELEMENT] Split selection into {len(parts)} parts")
        return parts


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

        Enhanced to handle multi-element selections - if ANY part of the selection is
        found as a prop, it returns the parent component.

        Args:
            component_file: Path to the component file (e.g., "src/components/HeroSection.tsx")
            component_name: Name of the component (e.g., "HeroSection")
            text_content: The text content selected by user (may span multiple elements)
            all_files: Dictionary of all project files

        Returns:
            File path of parent component/page that passes the prop, or None
        """
        try:
            # Check if this is a multi-element selection
            is_multi_element = self._is_multi_element_selection(text_content)

            if is_multi_element:
                logger.info(f"[PROP TRACE] Multi-element selection detected, will check individual parts")
                text_parts = self._split_selection_into_parts(text_content)
            else:
                text_parts = [text_content]

            # First, check if ALL text parts are hardcoded in the component itself
            component_code = all_files.get(component_file, '')
            hardcoded_parts = [part for part in text_parts if part in component_code]
            prop_parts = [part for part in text_parts if part not in component_code]

            logger.info(f"[PROP TRACE] Found {len(hardcoded_parts)} hardcoded parts and {len(prop_parts)} potential prop parts")

            # If ALL parts are hardcoded, edit the component itself
            if len(prop_parts) == 0:
                logger.info(f"[PROP TRACE] All text is hardcoded in {component_file}, not props")
                return None

            # If ANY part is a prop, find the parent component
            logger.info(f"[PROP TRACE] Some text not found in component, searching for parent that passes it as prop...")

            if not component_name:
                # Extract component name from file path
                component_name = component_file.split('/')[-1].replace('.tsx', '').replace('.jsx', '')

            # Search through all files for usage of this component with ANY of the text parts
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
                    # Check if ANY of the text parts appears in props when using the component
                    found_in_props = False
                    for part in prop_parts:
                        if self._search_text_in_jsx_props(component_name, part, file_content):
                            logger.info(f"[PROP TRACE] Found text part '{part[:50]}...' in {file_path} props for {component_name}")
                            found_in_props = True
                            break

                    if found_in_props:
                        parent_candidates.append(file_path)

            if not parent_candidates:
                logger.info(f"[PROP TRACE] No parent components found using {component_name} with this text")
                # If we have both hardcoded and prop parts, but no parent found, edit the component itself
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
    
    async def analyze_edit_request(self, instruction: str, element_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advanced AI-powered analysis of edit requests to determine what type of changes are needed.

        Provides accurate detection of edit types (structure, content, style) with support for
        multi-category edits and confidence scoring.

        Enhanced to detect multi-element selections and adjust scope accordingly.

        Args:
            instruction: User's natural language instruction
            element_info: Selected element information (with component hierarchy)

        Returns:
            Comprehensive analysis including:
            - edit_categories: List of applicable categories (structure/content/style)
            - primary_edit_type: The main category of edit
            - confidence: Confidence score (0-1) for the analysis
            - target_element: Element being edited
            - component_name: Component containing the element
            - specific_changes: Detailed breakdown of requested changes
            - element_context: Full context about the element
            - is_multi_element: Whether this is a multi-element selection
            - text_parts: List of text parts if multi-element
        """
        instruction_lower = instruction.lower()

        # Extract target element info from new structure
        component_info = element_info.get('component', {})
        target_element = component_info.get('elementName') or element_info.get('attributes', {}).get('data-element', 'unknown')
        component_name = component_info.get('componentName') or element_info.get('attributes', {}).get('data-component', 'Unknown')
        element_tag = element_info.get('tagName', '')
        element_text = element_info.get('textContent', '').strip()
        element_classes = element_info.get('classList', [])

        # Detect multi-element selection
        is_multi_element = self._is_multi_element_selection(element_text)
        text_parts = []
        if is_multi_element:
            text_parts = self._split_selection_into_parts(element_text)
            logger.info(f"[ANALYSIS] Multi-element selection detected with {len(text_parts)} parts")

        logger.info(f"[COMPONENT EDITOR] Analyzing instruction: {instruction}")
        logger.info(f"[COMPONENT EDITOR] Target element: {target_element}, Component: {component_name}")

        # Build comprehensive context for AI analysis
        element_context = {
            "tag": element_tag,
            "text": element_text[:100] if element_text else "",  # Truncate for prompt
            "classes": element_classes[:5] if element_classes else [],  # Top 5 classes
            "element_name": target_element,
            "component": component_name
        }

        if settings.cost_savings_mode:
            logger.info(f"[COMPONENT EDITOR] Cost savings mode enabled, using fallback analysis")
            return self._fallback_analysis(instruction, instruction_lower,
                                       target_element, component_name, element_tag,
                                       element_text, element_classes, is_multi_element, text_parts)
        
        # Call AI for advanced analysis
        analysis_prompt = self._build_analysis_prompt(instruction, element_context)
        
        try:
            response, usage = self.prompt_service.call_openai_api(
                system_prompt="You are an expert at analyzing UI edit requests. Provide precise JSON responses.",
                user_prompt=analysis_prompt,
                model=settings.edit_model
            )

            logger.info(f"[COMPONENT EDITOR] AI analysis usage: {usage}")

            # Parse AI response
            ai_analysis = self._parse_analysis_response(response)

            if ai_analysis:
                logger.info(f"[COMPONENT EDITOR] AI analysis result: {ai_analysis}")

                # Adjust scope if multi-element
                scope = ai_analysis.get("scope", "element")
                if is_multi_element and scope == "element":
                    scope = "multiple"

                return {
                    "edit_categories": ai_analysis.get("categories", ["content"]),
                    "primary_edit_type": ai_analysis.get("primary_type", "content"),
                    "confidence": ai_analysis.get("confidence", 0.8),
                    "target_element": target_element,
                    "component_name": component_name,
                    "instruction": instruction,
                    "specific_changes": ai_analysis.get("specific_changes", {}),
                    "element_context": {
                        "tag": element_tag,
                        "text": element_text,
                        "classes": element_classes
                    },
                    "change_scope": scope,
                    "requires_new_elements": ai_analysis.get("requires_new_elements", False),
                    "affects_layout": ai_analysis.get("affects_layout", False),
                    "is_multi_element": is_multi_element,
                    "text_parts": text_parts
                }

        except Exception as e:
            logger.warning(f"[COMPONENT EDITOR] AI analysis failed, using fallback: {str(e)}")

        # Fallback to enhanced heuristic analysis if AI fails
        return self._fallback_analysis(instruction, instruction_lower,
                                       target_element, component_name, element_tag,
                                       element_text, element_classes, is_multi_element, text_parts)

    def _build_analysis_prompt(self, instruction: str, element_context: Dict[str, Any]) -> str:
        """Build prompt for AI-powered edit analysis"""
        return f"""Analyze this UI edit request and return a JSON response.

INSTRUCTION: "{instruction}"

SELECTED ELEMENT:
- Tag: {element_context.get('tag', 'unknown')}
- Text content: "{element_context.get('text', '')}"
- CSS classes: {', '.join(element_context.get('classes', []))}
- Element name: {element_context.get('element_name', 'unknown')}
- Component: {element_context.get('component', 'Unknown')}

Analyze what changes are needed and respond with ONLY a valid JSON object (no markdown, no explanation):

{{
  "categories": ["structure" | "content" | "style"],  // All applicable categories
  "primary_type": "structure" | "content" | "style",  // Main category
  "confidence": 0.0-1.0,  // Your confidence in this analysis
  "specific_changes": {{
    "structure": {{
      "add_elements": ["element types to add"],
      "remove_elements": ["element types to remove"],
      "reorder": false,
      "change_hierarchy": false
    }},
    "content": {{
      "text_changes": ["description of text changes"],
      "replace_text": "new text if specified",
      "modify_attributes": ["attributes to change"]
    }},
    "style": {{
      "colors": ["color properties to change"],
      "typography": ["font/text properties to change"],
      "layout": ["spacing/positioning properties to change"],
      "visual_effects": ["effects like borders, shadows, etc."]
    }}
  }},
  "scope": "element" | "component" | "multiple",  // How many things affected
  "requires_new_elements": true | false,
  "affects_layout": true | false
}}

EXAMPLES:

Instruction: "make the text red"
Response: {{"categories": ["style"], "primary_type": "style", "confidence": 0.95, "specific_changes": {{"style": {{"colors": ["text color to red"]}}}}, "scope": "element", "requires_new_elements": false, "affects_layout": false}}

Instruction: "change this to say 'Welcome'"
Response: {{"categories": ["content"], "primary_type": "content", "confidence": 0.98, "specific_changes": {{"content": {{"text_changes": ["change text to Welcome"], "replace_text": "Welcome"}}}}, "scope": "element", "requires_new_elements": false, "affects_layout": false}}

Instruction: "add a button below this"
Response: {{"categories": ["structure"], "primary_type": "structure", "confidence": 0.9, "specific_changes": {{"structure": {{"add_elements": ["button"]}}}}, "scope": "component", "requires_new_elements": true, "affects_layout": true}}

Instruction: "make this heading larger and bold with a blue color"
Response: {{"categories": ["style", "content"], "primary_type": "style", "confidence": 0.92, "specific_changes": {{"style": {{"typography": ["increase size", "make bold"], "colors": ["text color to blue"]}}}}, "scope": "element", "requires_new_elements": false, "affects_layout": false}}

Respond with ONLY the JSON object for the given instruction:"""

    def _parse_analysis_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse and validate AI analysis response"""
        try:
            import json

            # Clean response
            response = response.strip()

            # Remove markdown code blocks if present
            if response.startswith('```'):
                response = re.sub(r'^```(?:json)?\n?', '', response, flags=re.MULTILINE)
                response = re.sub(r'\n?```$', '', response, flags=re.MULTILINE)
                response = response.strip()

            # Parse JSON
            analysis = json.loads(response)

            # Validate required fields
            required_fields = ['categories', 'primary_type', 'confidence']
            if not all(field in analysis for field in required_fields):
                logger.warning("[COMPONENT EDITOR] AI response missing required fields")
                return None

            # Validate categories
            valid_categories = {'structure', 'content', 'style'}
            if not all(cat in valid_categories for cat in analysis['categories']):
                logger.warning("[COMPONENT EDITOR] Invalid categories in AI response")
                return None

            # Validate primary type
            if analysis['primary_type'] not in valid_categories:
                logger.warning("[COMPONENT EDITOR] Invalid primary_type in AI response")
                return None

            # Validate confidence
            if not (0 <= analysis['confidence'] <= 1):
                logger.warning("[COMPONENT EDITOR] Invalid confidence score")
                analysis['confidence'] = 0.7  # Default

            return analysis

        except json.JSONDecodeError as e:
            logger.warning(f"[COMPONENT EDITOR] Failed to parse AI response as JSON: {str(e)}")
            return None
        except Exception as e:
            logger.warning(f"[COMPONENT EDITOR] Error parsing analysis response: {str(e)}")
            return None

    def _fallback_analysis(
        self,
        instruction: str,
        instruction_lower: str,
        target_element: str,
        component_name: str,
        element_tag: str,
        element_text: str,
        element_classes: list,
        is_multi_element: bool = False,
        text_parts: list = None
    ) -> Dict[str, Any]:
        """Enhanced fallback heuristic analysis when AI is unavailable"""
        if text_parts is None:
            text_parts = []

        # Enhanced keyword detection with context
        style_keywords = {
            'color', 'background', 'font', 'size', 'padding', 'margin', 'border',
            'style', 'width', 'height', 'spacing', 'bold', 'italic', 'underline',
            'shadow', 'rounded', 'opacity', 'larger', 'smaller', 'bigger'
        }

        content_keywords = {
            'text', 'content', 'title', 'heading', 'label', 'wording',
            'say', 'change to', 'rename', 'update text', 'write', 'modify'
        }

        structure_keywords = {
            'add', 'remove', 'delete', 'create', 'insert', 'place',
            'move', 'reorder', 'organize', 'section', 'new'
        }

        # Detect all applicable categories
        categories = []
        scores = {
            'style': 0,
            'content': 0,
            'structure': 0
        }

        # Score each category
        words = instruction_lower.split()
        for word in words:
            if any(kw in word for kw in style_keywords):
                scores['style'] += 1
            if any(kw in word for kw in content_keywords):
                scores['content'] += 1
            if any(kw in word for kw in structure_keywords):
                scores['structure'] += 1

        # Determine categories based on scores
        max_score = max(scores.values())
        if max_score > 0:
            for category, score in scores.items():
                if score > 0:
                    categories.append(category)
            primary_type = max(scores.items(), key=lambda x: x[1])[0]
        else:
            # Default to content if unclear
            categories = ['content']
            primary_type = 'content'

        # Analyze specific changes
        specific_changes = {
            'structure': {
                'add_elements': [],
                'remove_elements': [],
                'reorder': 'move' in instruction_lower or 'reorder' in instruction_lower,
                'change_hierarchy': False
            },
            'content': {
                'text_changes': [],
                'replace_text': None,
                'modify_attributes': []
            },
            'style': {
                'colors': [],
                'typography': [],
                'layout': [],
                'visual_effects': []
            }
        }

        # Detect specific structure changes
        if 'structure' in categories:
            if any(word in instruction_lower for word in ['add', 'create', 'insert']):
                # Try to detect what to add
                for element_type in ['button', 'input', 'section', 'div', 'image', 'link']:
                    if element_type in instruction_lower:
                        specific_changes['structure']['add_elements'].append(element_type)

            if any(word in instruction_lower for word in ['remove', 'delete']):
                specific_changes['structure']['remove_elements'].append(element_tag or 'element')

        # Detect specific content changes
        if 'content' in categories:
            # Check for text replacement patterns
            replace_patterns = [
                r'change.*to\s+"([^"]+)"',
                r'change.*to\s+\'([^\']+)\'',
                r'say\s+"([^"]+)"',
                r'say\s+\'([^\']+)\'',
                r'make.*say\s+"([^"]+)"',
            ]

            for pattern in replace_patterns:
                match = re.search(pattern, instruction_lower)
                if match:
                    specific_changes['content']['replace_text'] = match.group(1)
                    specific_changes['content']['text_changes'].append(f"Replace text with: {match.group(1)}")
                    break

            if not specific_changes['content']['text_changes']:
                specific_changes['content']['text_changes'].append("Modify text content")

        # Detect specific style changes
        if 'style' in categories:
            # Color changes
            color_words = ['color', 'red', 'blue', 'green', 'yellow', 'black', 'white', 'background']
            if any(word in instruction_lower for word in color_words):
                specific_changes['style']['colors'].append("Change color properties")

            # Typography changes
            typo_words = ['font', 'size', 'bold', 'italic', 'larger', 'smaller', 'bigger']
            if any(word in instruction_lower for word in typo_words):
                specific_changes['style']['typography'].append("Adjust typography")

            # Layout changes
            layout_words = ['padding', 'margin', 'spacing', 'width', 'height', 'position']
            if any(word in instruction_lower for word in layout_words):
                specific_changes['style']['layout'].append("Modify layout/spacing")

            # Visual effects
            effect_words = ['border', 'shadow', 'rounded', 'opacity']
            if any(word in instruction_lower for word in effect_words):
                specific_changes['style']['visual_effects'].append("Add/modify visual effects")

        # Determine scope and impact
        scope = 'element'
        if is_multi_element:
            # Multi-element selection automatically means multiple scope
            scope = 'multiple'
        elif any(word in instruction_lower for word in ['all', 'every', 'multiple', 'section']):
            scope = 'multiple'
        elif any(word in instruction_lower for word in ['component', 'entire', 'whole']):
            scope = 'component'

        requires_new_elements = 'structure' in categories and any(
            word in instruction_lower for word in ['add', 'create', 'insert', 'new']
        )

        affects_layout = 'structure' in categories or (
            'style' in categories and any(
                word in instruction_lower for word in ['padding', 'margin', 'width', 'height', 'position', 'layout']
            )
        )

        # Calculate confidence based on keyword matches
        confidence = min(0.9, 0.5 + (max_score * 0.1))

        logger.info(f"[COMPONENT EDITOR] Fallback analysis - Categories: {categories}, Primary: {primary_type}, Confidence: {confidence}, Multi-element: {is_multi_element}")

        return {
            "edit_categories": categories,
            "primary_edit_type": primary_type,
            "confidence": confidence,
            "target_element": target_element,
            "component_name": component_name,
            "instruction": instruction,
            "specific_changes": specific_changes,
            "element_context": {
                "tag": element_tag,
                "text": element_text,
                "classes": element_classes
            },
            "change_scope": scope,
            "requires_new_elements": requires_new_elements,
            "affects_layout": affects_layout,
            "is_multi_element": is_multi_element,
            "text_parts": text_parts
        }
    
    async def modify_component_code(
        self,
        file_path: str,
        instruction: str,
        element_context: Dict[str, Any],
        project_id: str,
        files: Dict[str, str],
        business_context: Optional[Dict[str, Any]] = None,
        additional_contexts: Optional[List[Dict[str, Any]]] = None,
        scope: str = "element",
        strict_note: Optional[str] = None
    ) -> Tuple[bool, str, str, Optional[str]]:
        """
        Use AI to modify component code based on user instruction.

        Args:
            file_path: Path to the component file
            instruction: User's natural language instruction
            element_context: Context about the selected element
            project_id: Project ID for loading current code
            files: Dictionary of all project files
            business_context: Business analysis data for context (optional)
            additional_contexts: Other selected elements in this same file (multi-select)
            scope: Edit scope — "element" (only selected elements), "section" (whole component), "page"
            strict_note: Extra constraint appended on containment-violation retries

        Returns:
            Tuple of (success, old_code, modified_code, error_message)
        """
        try:
            # Load current component code
            current_code = files.get(file_path)

            if not current_code:
                return False, "", "", f"Component file {file_path} not found in project"

            # Analyze the edit request (now async)
            analysis = await self.analyze_edit_request(instruction, element_context)

            # Build AI prompt with business context
            prompt = self._build_edit_prompt(
                current_code, instruction, element_context, analysis, business_context,
                additional_contexts=additional_contexts, scope=scope, strict_note=strict_note
            )
            logger.info(f"[COMPONENT EDITOR] Enhanced prompt built with analysis and business context")

            # Call AI service
            logger.info(f"[COMPONENT EDITOR] Calling AI to modify {file_path}")
            response, usage = self.prompt_service.call_openai_api(
                system_prompt="",
                user_prompt=prompt,
                model=settings.edit_model
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

    def check_edit_containment(
        self,
        old_code: str,
        new_code: str,
        element_contexts: List[Dict[str, Any]],
        tolerance: int = 12
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify that an element-scoped edit only changed code near the selected element(s).

        Anchors are located in the original code via each element's data-element name
        and text content; every diff hunk must fall within `tolerance` lines of an anchor.

        Returns:
            Tuple of (is_contained, violation_description)
        """
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()

        # Collect anchor line numbers for all selected elements
        anchors: set = set()
        for ctx in element_contexts:
            keys = []
            component_info = ctx.get('component', {}) or {}
            element_name = component_info.get('elementName') or ctx.get('elementSelector')
            if element_name:
                keys.append(f'data-element="{element_name}"')
            text = (ctx.get('textContent', '') or '').strip()
            if text:
                # Use a leading chunk of the text — JSX often wraps long strings
                keys.append(text[:60])
            for i, line in enumerate(old_lines):
                if any(k in line for k in keys if k):
                    anchors.add(i)

        if not anchors:
            # Cannot locate the selection in source — skip the check rather than block valid edits
            logger.warning("[COMPONENT EDITOR] Containment check skipped: no anchors found for selection")
            return True, None

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            changed_range = range(i1, max(i2, i1 + 1))
            near_anchor = any(
                abs(line_no - anchor) <= tolerance
                for anchor in anchors
                for line_no in changed_range
            )
            if not near_anchor:
                snippet_lines = old_lines[i1:i2] or new_lines[j1:j2]
                snippet = ' / '.join(l.strip() for l in snippet_lines[:2])[:160]
                violation = f"lines {i1 + 1}-{max(i2, i1 + 1)} changed outside the selected element region: {snippet}"
                logger.warning(f"[COMPONENT EDITOR] Containment violation: {violation}")
                return False, violation

        return True, None

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
        analysis: Dict[str, Any],
        business_context: Optional[Dict[str, Any]] = None,
        additional_contexts: Optional[List[Dict[str, Any]]] = None,
        scope: str = "element",
        strict_note: Optional[str] = None
    ) -> str:
        """Build the AI prompt for component editing using enhanced analysis and business context"""

        target_element = analysis.get('target_element', 'unknown')
        component_name = analysis.get('component_name', 'Unknown')
        edit_categories = analysis.get('edit_categories', ['content'])
        primary_edit_type = analysis.get('primary_edit_type', 'content')
        specific_changes = analysis.get('specific_changes', {})
        confidence = analysis.get('confidence', 0.7)
        change_scope = analysis.get('change_scope', 'element')
        requires_new_elements = analysis.get('requires_new_elements', False)
        affects_layout = analysis.get('affects_layout', False)

        selected_text = element_context.get('textContent', '').strip()

        # Detect multi-element selection
        is_multi_element = self._is_multi_element_selection(selected_text)
        text_parts = []
        if is_multi_element:
            text_parts = self._split_selection_into_parts(selected_text)
            logger.info(f"[EDIT PROMPT] Multi-element selection with {len(text_parts)} parts")

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
            if is_multi_element:
                # Multi-element prop edit
                text_parts_preview = '\n'.join([f'  - "{part[:60]}..."' if len(part) > 60 else f'  - "{part}"' for part in text_parts[:5]])
                context_note = f"""
CONTEXT: This is a PAGE/PARENT COMPONENT that uses the <{actual_component_name}> component.
You are editing the PROP VALUES passed to {actual_component_name}, not the component itself.

⚠️ MULTI-ELEMENT SELECTION DETECTED ⚠️
The user selected text that spans MULTIPLE elements/props. This means you need to modify
MULTIPLE prop values in the <{actual_component_name}> usage, not just one.

SELECTED TEXT PARTS ({len(text_parts)} parts):
{text_parts_preview}

SPECIFIC GUIDANCE:
- Find where <{actual_component_name}> is used in this code
- Identify which props contain any of the text parts above
- Modify ALL relevant prop values according to the instruction
- The instruction applies to ALL selected text, not just one prop
- Do NOT modify the component definition or import
- Make sure all changes are consistent with the user's instruction
"""
            else:
                # Single element prop edit
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
            if is_multi_element:
                # Multi-element component edit
                text_parts_preview = '\n'.join([f'  - "{part[:60]}..."' if len(part) > 60 else f'  - "{part}"' for part in text_parts[:5]])
                context_note = f"""
CONTEXT: This is the component definition itself.
You are editing the component's internal structure and content.

⚠️ MULTI-ELEMENT SELECTION DETECTED ⚠️
The user selected text that spans MULTIPLE elements in the component. This means you need to
modify MULTIPLE pieces of text/elements, not just one.

SELECTED TEXT PARTS ({len(text_parts)} parts):
{text_parts_preview}

SPECIFIC GUIDANCE:
- Find ALL occurrences of the text parts above in the component
- Modify ALL of them according to the instruction (the instruction applies to ALL selected text)
- Keep the component's prop interface unchanged unless necessary
- Maintain the component's export and structure
- Ensure changes are consistent across all modified elements
"""
            else:
                # Single element component edit
                context_note = f"""
CONTEXT: This is the component definition itself.
You are editing the component's internal structure and content.

SPECIFIC GUIDANCE:
- Modify the element/text: "{selected_text}"
- Keep the component's prop interface unchanged unless necessary
- Maintain the component's export and structure
"""

        # Build detailed change instructions based on analysis
        change_details = self._build_change_details(specific_changes, edit_categories)

        # Scope guidance
        scope_guidance = ""
        if change_scope == "multiple":
            scope_guidance = "\n⚠️ SCOPE: This change affects MULTIPLE elements. Make sure to apply the change consistently across all relevant elements."
        elif change_scope == "component":
            scope_guidance = "\n⚠️ SCOPE: This change affects the ENTIRE component. Consider the impact on the component's overall structure."

        # Layout warning
        layout_warning = ""
        if affects_layout:
            layout_warning = "\n⚠️ LAYOUT IMPACT: This change may affect the layout. Ensure spacing, positioning, and responsive behavior remain intact."

        # New elements guidance
        new_elements_guidance = ""
        if requires_new_elements:
            new_elements_guidance = "\n⚠️ NEW ELEMENTS: This change requires adding new elements. Make sure they follow the existing code style and maintain semantic HTML."

        # Build business context section
        business_context_note = ""
        if business_context:
            # Extract key business information
            business_name = business_context.get('business_name', '')
            business_description = business_context.get('business_description', '')
            target_audience = business_context.get('target_audience', '')
            key_offerings = business_context.get('key_offerings', [])
            value_proposition = business_context.get('value_proposition', '')
            brand_personality = business_context.get('brand_personality', '')

            business_context_note = f"""
BUSINESS CONTEXT (use this to inform your edits with relevant, specific content):
- Business Name: {business_name}
- Description: {business_description}
- Target Audience: {target_audience}
- Value Proposition: {value_proposition}
- Brand Personality: {brand_personality}
- Key Offerings: {', '.join(key_offerings[:5]) if key_offerings else 'N/A'}

IMPORTANT: When the user's instruction lacks specific replacement text (e.g., "update this text", "change the title"),
use the business context above to generate relevant, meaningful content that aligns with the business's brand and offerings.
DO NOT use generic placeholders like "New Title Placeholder" - instead, create actual content based on the business context.
"""

        # Enumerate additional multi-select targets in this file
        additional_targets_note = ""
        if additional_contexts:
            target_lines = []
            for idx, ctx in enumerate(additional_contexts, start=2):
                ctx_component = ctx.get('component', {}) or {}
                ctx_text = (ctx.get('textContent', '') or '').strip()
                target_lines.append(
                    f"  {idx}. <{ctx.get('tagName', '?')}> "
                    f"data-element=\"{ctx_component.get('elementName') or ctx.get('elementSelector') or 'unknown'}\" "
                    f"text=\"{ctx_text[:80]}{'...' if len(ctx_text) > 80 else ''}\""
                )
            additional_targets_note = f"""
ADDITIONAL SELECTED TARGETS (the user multi-selected {len(additional_contexts) + 1} elements in this file —
the instruction applies to ALL of them, including the primary target above):
{chr(10).join(target_lines)}
"""

        # Scope enforcement — element scope must not touch anything outside the selection
        if scope == "element":
            scope_enforcement = """
STRICT SCOPE ENFORCEMENT:
- Change ONLY the selected element(s) enumerated in the target information.
- Reproduce every other line of the file EXACTLY as it appears in the original — byte-for-byte.
- Do NOT reformat, reorder imports, rename variables, adjust whitespace, or "improve" unrelated code.
- If the instruction seems to imply broader changes, still restrict your changes to the selected element(s) only."""
        elif scope == "section":
            scope_enforcement = """
SCOPE: The user selected this entire section/component. You may change anything within this file
that the instruction requires, but keep unrelated parts of the file untouched."""
        else:
            scope_enforcement = ""

        strict_retry_note = f"\nPREVIOUS ATTEMPT REJECTED: {strict_note}\n" if strict_note else ""

        prompt = f"""You are a React component editor. Modify the following code based on the user's instruction.

{context_note}
{business_context_note}

CODE TO EDIT:
```tsx
{current_code}
```

USER INSTRUCTION:
"{instruction}"

TARGET INFORMATION:
- Element: {target_element}
- Tag: {element_context.get('tagName', '')}
- Text: "{selected_text[:100]}{'...' if len(selected_text) > 100 else ''}"
- Classes: {', '.join(element_context.get('classList', [])[:5])}
- Component: {component_name}
- Multi-element: {'YES - ' + str(len(text_parts)) + ' parts' if is_multi_element else 'NO'}
{additional_targets_note}{scope_enforcement}{strict_retry_note}

ANALYSIS (Confidence: {confidence:.0%}):
- Edit Categories: {', '.join(edit_categories)}
- Primary Type: {primary_edit_type}
- Scope: {change_scope}
{scope_guidance}{layout_warning}{new_elements_guidance}

SPECIFIC CHANGES REQUIRED:
{change_details}

REQUIREMENTS:
1. Make ONLY the requested changes - do not modify other parts
2. Preserve all existing functionality and structure
3. Keep the same export style (default or named)
4. Maintain TypeScript types and interfaces
5. Use Tailwind CSS classes for styling (do not add inline styles)
6. Keep the same component name and file structure
7. Ensure the modified element is still accessible and semantic
8. Do not add unnecessary imports or dependencies
9. Maintain all data attributes (data-component, data-file, data-element)
10. Follow React best practices and hooks rules

IMPORTANT:
- Return ONLY the complete modified code
- Do not include explanations or markdown formatting
- The code should be ready to use as-is
- Keep all existing imports and structure intact
- Make precise, targeted changes based on the analysis above

Return the complete modified code:"""

        return prompt

    def _build_change_details(self, specific_changes: Dict[str, Any], categories: list) -> str:
        """Build detailed change instructions from analysis"""
        details = []

        # Structure changes
        if 'structure' in categories and 'structure' in specific_changes:
            structure = specific_changes['structure']
            if structure.get('add_elements'):
                details.append(f"  • ADD ELEMENTS: {', '.join(structure['add_elements'])}")
            if structure.get('remove_elements'):
                details.append(f"  • REMOVE ELEMENTS: {', '.join(structure['remove_elements'])}")
            if structure.get('reorder'):
                details.append("  • REORDER: Rearrange element positions")
            if structure.get('change_hierarchy'):
                details.append("  • HIERARCHY: Modify DOM structure/nesting")

        # Content changes
        if 'content' in categories and 'content' in specific_changes:
            content = specific_changes['content']
            if content.get('replace_text'):
                details.append(f"  • REPLACE TEXT: Change to \"{content['replace_text']}\"")
            elif content.get('text_changes'):
                for change in content['text_changes']:
                    details.append(f"  • TEXT CHANGE: {change}")
            if content.get('modify_attributes'):
                details.append(f"  • ATTRIBUTES: Modify {', '.join(content['modify_attributes'])}")

        # Style changes
        if 'style' in categories and 'style' in specific_changes:
            style = specific_changes['style']
            if style.get('colors'):
                details.append(f"  • COLORS: {', '.join(style['colors'])}")
            if style.get('typography'):
                details.append(f"  • TYPOGRAPHY: {', '.join(style['typography'])}")
            if style.get('layout'):
                details.append(f"  • LAYOUT: {', '.join(style['layout'])}")
            if style.get('visual_effects'):
                details.append(f"  • EFFECTS: {', '.join(style['visual_effects'])}")

        return "\n".join(details) if details else "  • Make the changes as described in the instruction"
    
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
