"""
Direct Code Editor Service

This service handles direct code manipulation for property editing without using AI.
It parses React/TypeScript components and modifies specific properties like:
- Tailwind CSS classes (className attribute)
- Inline styles (style attribute)
- Text content
- Image sources
- Link hrefs

Implementation uses regex-based code manipulation for reliable, fast edits.
For complex AST-based operations, consider extending with @babel/parser.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from html import escape, unescape
from pathlib import Path

logger = logging.getLogger(__name__)


# Tailwind class mappings for property editing
TAILWIND_PROPERTY_MAP = {
    # Colors
    'color': r'text-(?:\w+)-(?:\d+)',
    'backgroundColor': r'bg-(?:\w+)-(?:\d+)',
    'borderColor': r'border-(?:\w+)-(?:\d+)',
    
    # Typography
    'fontSize': r'text-(?:xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)',
    'fontWeight': r'font-(?:thin|extralight|light|normal|medium|semibold|bold|extrabold|black)',
    'fontFamily': r'font-(?:sans|serif|mono)',
    'lineHeight': r'leading-(?:none|tight|snug|normal|relaxed|loose|\d+)',
    'textAlign': r'text-(?:left|center|right|justify)',
    'textTransform': r'(?:uppercase|lowercase|capitalize|normal-case)',
    
    # Spacing
    'padding': r'p-(?:\d+(?:\.\d+)?)',
    'paddingTop': r'pt-(?:\d+(?:\.\d+)?)',
    'paddingRight': r'pr-(?:\d+(?:\.\d+)?)',
    'paddingBottom': r'pb-(?:\d+(?:\.\d+)?)',
    'paddingLeft': r'pl-(?:\d+(?:\.\d+)?)',
    'margin': r'm-(?:\d+(?:\.\d+)?)',
    'marginTop': r'mt-(?:\d+(?:\.\d+)?)',
    'marginRight': r'mr-(?:\d+(?:\.\d+)?)',
    'marginBottom': r'mb-(?:\d+(?:\.\d+)?)',
    'marginLeft': r'ml-(?:\d+(?:\.\d+)?)',
    'gap': r'gap-(?:\d+(?:\.\d+)?)',
    
    # Border
    'borderWidth': r'border-(?:\d+)?',
    'borderRadius': r'rounded-(?:none|sm|md|lg|xl|2xl|3xl|full)?',
    
    # Layout
    'display': r'(?:block|inline-block|inline|flex|inline-flex|grid|inline-grid|hidden)',
    'position': r'(?:static|fixed|absolute|relative|sticky)',
    'justifyContent': r'justify-(?:start|end|center|between|around|evenly)',
    'alignItems': r'items-(?:start|end|center|baseline|stretch)',
    'flexDirection': r'flex-(?:row|row-reverse|col|col-reverse)',
    'flexWrap': r'flex-(?:wrap|wrap-reverse|nowrap)',
    
    # Sizing
    'width': r'w-(?:\d+(?:\.\d+)?|full|screen|min|max|fit|auto)',
    'height': r'h-(?:\d+(?:\.\d+)?|full|screen|min|max|fit|auto)',
    'minWidth': r'min-w-(?:\d+|full|min|max|fit)',
    'maxWidth': r'max-w-(?:xs|sm|md|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|full|min|max|fit|prose|screen-sm|screen-md|screen-lg|screen-xl|screen-2xl)',
    'minHeight': r'min-h-(?:\d+|full|screen|min|max|fit)',
    'maxHeight': r'max-h-(?:\d+|full|screen|min|max|fit)',
    
    # Effects
    'boxShadow': r'shadow-(?:sm|md|lg|xl|2xl|inner|none)?',
    'opacity': r'opacity-(?:\d+)',
    'zIndex': r'z-(?:\d+|auto)',
}


class DirectCodeEditor:
    """Service for direct code manipulation without AI"""
    
    def __init__(self):
        pass
    
    def validate_property_value(self, property_name: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate property value before applying.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            value_str = str(value)
            
            # Validate URL properties
            if property_name in ['src', 'href']:
                if not value_str.strip():
                    return (False, f"{property_name} cannot be empty")
                # Basic URL validation
                if not (value_str.startswith('http') or value_str.startswith('/') or value_str.startswith('.')):
                    return (False, f"Invalid URL format for {property_name}")
            
            # Validate text content
            elif property_name == 'text':
                if len(value_str) > 10000:
                    return (False, "Text content too long (max 10,000 characters)")
            
            # Validate Tailwind classes
            elif property_name in TAILWIND_PROPERTY_MAP:
                if not value_str.strip():
                    return (False, f"{property_name} value cannot be empty")
                # Check if it looks like a valid Tailwind class
                if not re.match(r'^[\w-]+$', value_str):
                    return (False, f"Invalid Tailwind class format: {value_str}")
            
            return (True, None)
            
        except Exception as e:
            return (False, f"Validation error: {str(e)}")
        
    def edit_properties(
        self,
        code: str,
        element_selector: str,
        properties: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """
        Edit component properties directly with validation and error handling.

        Args:
            code: Original component code
            element_selector: data-element value to identify the element
            properties: List of property changes to apply

        Returns:
            Tuple of (success, new_code, error_message, prop_edit_metadata)
            - success: True if changes applied, False otherwise
            - new_code: Modified code if successful, None otherwise
            - error_message: Error description if failed, None otherwise
            - prop_edit_metadata: Dict with prop edit info if prop update needed, None otherwise
        """
        try:
            # Input validation
            if not code or not code.strip():
                return (False, None, "Code cannot be empty", None)

            if not element_selector or not element_selector.strip():
                return (False, None, "Element selector cannot be empty", None)

            if not properties or len(properties) == 0:
                return (False, None, "No properties to edit", None)

            logger.info(f"[DIRECT EDIT] Editing element '{element_selector}' with {len(properties)} properties")

            # Verify element exists before attempting any changes
            if not self._find_element_tag(code, element_selector):
                return (False, None, f"Element with data-element='{element_selector}' not found in code", None)
            
            new_code = code
            changes_applied = []
            failed_changes = []
            
            for prop in properties:
                property_name = prop.get('property')
                property_value = prop.get('value')
                
                if not property_name:
                    failed_changes.append(("unknown", "Property name is missing"))
                    continue
                
                # Validate property value
                is_valid, validation_error = self.validate_property_value(property_name, property_value)
                if not is_valid:
                    failed_changes.append((property_name, validation_error))
                    logger.warning(f"[DIRECT EDIT] Validation failed for {property_name}: {validation_error}")
                    continue
                
                logger.info(f"[DIRECT EDIT] Applying {property_name} = {property_value}")
                
                # Store previous code for rollback
                previous_code = new_code
                
                # Route to appropriate editor method
                result = None
                try:
                    if property_name == 'text':
                        result = self._edit_text_content(new_code, element_selector, str(property_value))

                        # Check if result is a prop edit metadata dict
                        if isinstance(result, dict) and result.get('type') == 'prop_edit':
                            logger.info(f"[DIRECT EDIT] Prop edit detected for '{result['prop_name']}'")
                            # Return early with prop edit info for caller to handle
                            return (False, None, None, result)

                    elif property_name == 'src':
                        result = self._edit_attribute(new_code, element_selector, 'src', str(property_value))
                    elif property_name == 'href':
                        result = self._edit_attribute(new_code, element_selector, 'href', str(property_value))
                    elif property_name == 'alt':
                        result = self._edit_attribute(new_code, element_selector, 'alt', str(property_value))
                    elif property_name in TAILWIND_PROPERTY_MAP:
                        result = self._edit_tailwind_class(new_code, element_selector, property_name, str(property_value))
                    else:
                        failed_changes.append((property_name, "Property type not supported"))
                        logger.warning(f"[DIRECT EDIT] Property type '{property_name}' not yet implemented")
                        continue

                    if result and result != previous_code:
                        # Verify the change didn't break the code structure
                        logger.info(f"[DIRECT EDIT] Verifying code structure after {property_name} change...")
                        logger.info(f"[DIRECT EDIT] Code length: {len(previous_code)} -> {len(result)}")

                        if self._verify_code_structure(result):
                            new_code = result
                            changes_applied.append(property_name)
                            logger.info(f"[DIRECT EDIT] ✓ Successfully applied {property_name}")
                        else:
                            failed_changes.append((property_name, "Code structure validation failed"))
                            logger.error(f"[DIRECT EDIT] Code structure validation failed for {property_name}")
                            logger.error(f"[DIRECT EDIT] Original code snippet (first 500 chars):\n{previous_code[:500]}")
                            logger.error(f"[DIRECT EDIT] Modified code snippet (first 500 chars):\n{result[:500]}")
                            new_code = previous_code
                    else:
                        failed_changes.append((property_name, "No changes made - element may not support this property"))
                        logger.warning(f"[DIRECT EDIT] Failed to apply {property_name}")
                        
                except Exception as edit_error:
                    failed_changes.append((property_name, str(edit_error)))
                    logger.error(f"[DIRECT EDIT] Exception while applying {property_name}: {str(edit_error)}")
                    new_code = previous_code  # Rollback on error
            
            # Build result message
            if changes_applied:
                success_msg = f"Successfully applied: {', '.join(changes_applied)}"
                if failed_changes:
                    failed_msg = "; ".join([f"{prop}: {err}" for prop, err in failed_changes])
                    success_msg += f". Failed: {failed_msg}"

                logger.info(f"[DIRECT EDIT] {success_msg}")
                return (True, new_code, None, None)
            else:
                error_msg = "No changes could be applied"
                if failed_changes:
                    error_msg += f": {'; '.join([f'{prop} ({err})' for prop, err in failed_changes])}"
                logger.error(f"[DIRECT EDIT] {error_msg}")
                return (False, None, error_msg, None)

        except Exception as e:
            logger.error(f"[DIRECT EDIT] Unexpected error: {str(e)}", exc_info=True)
            return (False, None, f"Unexpected error: {str(e)}", None)

    def update_prop_at_source(
        self,
        files: Dict[str, str],
        component_file: str,
        prop_name: str,
        new_value: str,
        component_tracker
    ) -> Tuple[bool, Optional[Dict[str, str]], Optional[str]]:
        """
        Update a prop value at its source (parent component) instead of hardcoding.

        This method traces a prop back to where it's passed from a parent component
        and updates the value there, preserving the component's dynamic nature.

        Args:
            files: All project files (dict of file_path -> content)
            component_file: Path to the component file being edited (e.g., "src/components/HeroSection.tsx")
            prop_name: Name of the prop to update (e.g., "title")
            new_value: New value for the prop
            component_tracker: ComponentRelationshipTracker instance

        Returns:
            Tuple of (success, updated_files, error_message)
            - success: True if prop updated at source, False otherwise
            - updated_files: Dict of updated files if successful, None otherwise
            - error_message: Error description if failed, None otherwise
        """
        try:
            logger.info(f"[PROP UPDATE] Updating prop '{prop_name}' at source for component: {component_file}")

            # Extract component name from file path
            component_name = Path(component_file).stem
            logger.info(f"[PROP UPDATE] Component name: {component_name}")

            # Find where this prop is passed from
            prop_source = component_tracker.find_prop_source(component_file, prop_name)

            if not prop_source:
                error_msg = f"Could not find source for prop '{prop_name}' in component '{component_name}'"
                logger.warning(f"[PROP UPDATE] {error_msg}")
                return (False, None, error_msg)

            parent_file, old_prop_value, usage = prop_source
            logger.info(f"[PROP UPDATE] Found prop source in: {parent_file}")
            logger.info(f"[PROP UPDATE] Old prop value: '{old_prop_value}'")
            logger.info(f"[PROP UPDATE] New prop value: '{new_value}'")

            # Get parent file content
            if parent_file not in files:
                error_msg = f"Parent file '{parent_file}' not found in project files"
                logger.error(f"[PROP UPDATE] {error_msg}")
                return (False, None, error_msg)

            parent_code = files[parent_file]

            # Find and update the component usage in parent
            updated_parent_code = self._update_prop_in_jsx(
                code=parent_code,
                component_name=component_name,
                prop_name=prop_name,
                new_value=new_value,
                old_value=old_prop_value
            )

            if not updated_parent_code or updated_parent_code == parent_code:
                error_msg = f"Failed to update prop in parent component"
                logger.error(f"[PROP UPDATE] {error_msg}")
                return (False, None, error_msg)

            # Verify the updated code structure
            if not self._verify_code_structure(updated_parent_code):
                error_msg = "Updated parent code failed structure validation"
                logger.error(f"[PROP UPDATE] {error_msg}")
                return (False, None, error_msg)

            # Create updated files dict
            updated_files = files.copy()
            updated_files[parent_file] = updated_parent_code

            logger.info(f"[PROP UPDATE] Successfully updated prop '{prop_name}' in {parent_file}")
            return (True, updated_files, None)

        except Exception as e:
            error_msg = f"Unexpected error updating prop at source: {str(e)}"
            logger.error(f"[PROP UPDATE] {error_msg}", exc_info=True)
            return (False, None, error_msg)

    def _update_prop_in_jsx(
        self,
        code: str,
        component_name: str,
        prop_name: str,
        new_value: str,
        old_value: str
    ) -> Optional[str]:
        """
        Update a specific prop value in a component usage.

        Args:
            code: Parent component code
            component_name: Name of the child component (e.g., "HeroSection")
            prop_name: Prop to update (e.g., "title")
            new_value: New prop value
            old_value: Old prop value (for verification)

        Returns:
            Updated code or None if update failed
        """
        logger.info(f"[PROP UPDATE] Updating {component_name} prop '{prop_name}' from '{old_value}' to '{new_value}'")

        # Pattern to find component usage
        # Matches: <ComponentName ...props... />  OR  <ComponentName ...props...>
        component_pattern = rf'<{component_name}\s+([^>]*?)(/?>)'

        match = re.search(component_pattern, code, re.DOTALL)
        if not match:
            logger.error(f"[PROP UPDATE] Could not find <{component_name}> usage in code")
            return None

        props_section = match.group(1)
        component_end = match.group(2)
        match_start = match.start()
        match_end = match.end()

        logger.info(f"[PROP UPDATE] Found component at position {match_start}-{match_end}")
        logger.debug(f"[PROP UPDATE] Props section: {props_section[:100]}...")

        # Find and update the specific prop
        # Handle both string props: title="value" and expression props: title={value}

        # Try string prop first: prop_name="old_value"
        string_prop_pattern = rf'{prop_name}="([^"]*)"'
        string_match = re.search(string_prop_pattern, props_section)

        if string_match:
            logger.info(f"[PROP UPDATE] Found string prop: {prop_name}=\"{string_match.group(1)}\"")
            # Replace the prop value
            old_prop_full = string_match.group(0)  # e.g., title="old value"
            new_prop_full = f'{prop_name}="{new_value}"'

            updated_props = props_section.replace(old_prop_full, new_prop_full, 1)
            updated_component_tag = f"<{component_name} {updated_props}{component_end}"

            # Replace in code
            new_code = code[:match_start] + updated_component_tag + code[match_end:]

            logger.info(f"[PROP UPDATE] Successfully updated string prop")
            return new_code

        # Try expression prop: prop_name={value}
        expr_prop_pattern = rf'{prop_name}=\{{([^}}]*)\}}'
        expr_match = re.search(expr_prop_pattern, props_section)

        if expr_match:
            logger.info(f"[PROP UPDATE] Found expression prop: {prop_name}={{{expr_match.group(1)}}}")
            # For expression props, convert to string prop
            old_prop_full = expr_match.group(0)
            new_prop_full = f'{prop_name}="{new_value}"'

            updated_props = props_section.replace(old_prop_full, new_prop_full, 1)
            updated_component_tag = f"<{component_name} {updated_props}{component_end}"

            # Replace in code
            new_code = code[:match_start] + updated_component_tag + code[match_end:]

            logger.info(f"[PROP UPDATE] Successfully updated expression prop")
            return new_code

        logger.warning(f"[PROP UPDATE] Prop '{prop_name}' not found in component usage")
        return None

    def _verify_code_structure(self, code: str) -> bool:
        """
        Verify that code structure is still valid after changes.
        Basic checks for common issues.
        """
        try:
            # Check for balanced braces
            brace_open = code.count('{')
            brace_close = code.count('}')
            if brace_open != brace_close:
                logger.warning(f"[VERIFY] Unbalanced braces detected: {brace_open} open, {brace_close} close")
                return False

            # Check for balanced parentheses
            paren_open = code.count('(')
            paren_close = code.count(')')
            if paren_open != paren_close:
                logger.warning(f"[VERIFY] Unbalanced parentheses detected: {paren_open} open, {paren_close} close")
                return False

            # Check for balanced angle brackets (basic JSX check)
            # Support tags with dots (e.g., motion.div, styled.button)
            open_tags = len(re.findall(r'<\w+(?:\.\w+)?[^<>]*(?<!/)>', code))
            close_tags = len(re.findall(r'</\w+(?:\.\w+)?>', code))
            self_closing_tags = len(re.findall(r'<\w+(?:\.\w+)?[^>]*/>', code))

            # open_tags should equal close_tags (self-closing don't count)
            if open_tags != close_tags:
                logger.warning(f"[VERIFY] Unbalanced JSX tags: {open_tags} open, {close_tags} close, {self_closing_tags} self-closing")
                logger.warning(f"[VERIFY] First 200 chars of code: {code[:200]}")
                return False

            logger.info(f"[VERIFY] Code structure OK - braces: {brace_open}, parens: {paren_open}, tags: {open_tags}/{close_tags}")
            return True

        except Exception as e:
            logger.error(f"[VERIFY] Verification error: {str(e)}")
            return False
    
    def _find_element_tag(self, code: str, selector: str) -> Optional[Tuple[int, int, str]]:
        """
        Find element opening tag by data-element attribute.
        Returns (start_pos, end_pos, tag_content) of the opening tag.

        Supports both:
        - Static attributes: data-element="service-item-title-1"
        - JSX expressions: data-element={`service-item-title-${index}`}
        """
        # First, try to match static string attributes
        # Matches: <tagname ... data-element="selector" ... >
        # Supports tags with dots like motion.div, styled.button, etc.
        pattern = rf'<(\w+(?:\.\w+)?)([^>]*data-element=["\']{ re.escape(selector)}["\'][^>]*)>'
        match = re.search(pattern, code, re.DOTALL)

        if match:
            logger.info(f"[DIRECT EDIT] Found element with static data-element='{selector}'")
            return (match.start(), match.end(), match.group(0))

        # Second, try to match JSX template expressions
        # For selector like "service-item-title-1", extract the pattern and number
        # Pattern: data-element={`service-item-title-${index}`}

        # Try to extract pattern and index from selector
        # Common patterns: "prefix-0", "prefix-1", "prefix-suffix-2", etc.
        match_parts = re.match(r'^(.+?)-(\d+)$', selector)

        if match_parts:
            prefix = match_parts.group(1)
            index_value = match_parts.group(2)

            logger.info(f"[DIRECT EDIT] Trying JSX expression pattern: prefix='{prefix}', index={index_value}")

            # Pattern to match JSX template expression
            # Matches: data-element={`prefix-${variable}`}
            jsx_pattern = rf'<(\w+(?:\.\w+)?)([^>]*data-element=\{{`{re.escape(prefix)}-\$\{{[^}}]+\}}`\}}[^>]*)>'
            jsx_match = re.search(jsx_pattern, code, re.DOTALL)

            if jsx_match:
                logger.info(f"[DIRECT EDIT] Found element with JSX expression data-element={{`{prefix}-${{...}}`}}")
                return (jsx_match.start(), jsx_match.end(), jsx_match.group(0))

        logger.warning(f"[DIRECT EDIT] Element with data-element='{selector}' not found (tried both static and JSX patterns)")
        return None
    
    def _find_element_content(self, code: str, selector: str) -> Optional[Tuple[int, int, int, int, str, str]]:
        """
        Find element with its content by data-element attribute.
        Returns (tag_start, tag_end, content_end, closing_tag_end, tag_name, content) or None.

        Where:
        - tag_start: Start of opening tag
        - tag_end: End of opening tag (where content begins)
        - content_end: End of content (where closing tag begins)
        - closing_tag_end: End of closing tag
        - tag_name: Name of the tag
        - content: Text content between tags
        """
        # First find the opening tag
        tag_match = self._find_element_tag(code, selector)
        if not tag_match:
            return None

        tag_start, tag_end, tag_content = tag_match

        # Extract tag name (supports tags with dots like motion.div, styled.button)
        tag_name_match = re.match(r'<(\w+(?:\.\w+)?)', tag_content)
        if not tag_name_match:
            return None
        tag_name = tag_name_match.group(1)

        # Check if it's a self-closing tag
        if tag_content.rstrip().endswith('/>'):
            return (tag_start, tag_end, tag_end, tag_end, tag_name, '')

        # Find the closing tag
        # Pattern to match closing tag, handling nested tags
        closing_pattern = rf'</{tag_name}>'

        # Simple approach: find the next closing tag of the same type
        # (Limitations: doesn't handle nested same-type tags correctly)
        search_start = tag_end
        closing_match = re.search(closing_pattern, code[search_start:])

        if closing_match:
            content_start = tag_end
            content_end = search_start + closing_match.start()
            closing_tag_end = search_start + closing_match.end()
            content = code[content_start:content_end]
            return (tag_start, tag_end, content_end, closing_tag_end, tag_name, content)

        logger.warning(f"[DIRECT EDIT] Closing tag for <{tag_name}> not found")
        return None
    
    def _edit_text_content(self, code: str, selector: str, new_text: str) -> Optional[str | Dict[str, Any]]:
        """
        Edit text content of an element.
        Works for elements with direct text children (headings, paragraphs, buttons, etc.)

        Returns:
            - New code string if direct edit is performed
            - Dict with prop edit metadata if content is a prop expression
            - None if element not found
        """
        logger.info(f"[DIRECT EDIT] Changing text content to: '{new_text}'")

        element_data = self._find_element_content(code, selector)
        if not element_data:
            logger.error(f"[DIRECT EDIT] Could not find element with selector: {selector}")
            return None

        tag_start, tag_end, content_end, closing_tag_end, tag_name, old_content = element_data

        logger.info(f"[DIRECT EDIT] Tag name: {tag_name}")
        logger.info(f"[DIRECT EDIT] Old content: '{old_content}' (length: {len(old_content)})")
        logger.info(f"[DIRECT EDIT] New content: '{new_text}' (length: {len(new_text)})")
        logger.info(f"[DIRECT EDIT] Positions - tag_start: {tag_start}, tag_end: {tag_end}, content_end: {content_end}, closing_tag_end: {closing_tag_end}")

        # Check if content is a JSX prop expression like {title} or {subtitle}
        prop_match = re.match(r'^\s*\{(\w+)\}\s*$', old_content)
        if prop_match:
            prop_name = prop_match.group(1)

            # Verify it's actually a component prop (not a local variable)
            if self._is_component_prop(code, prop_name):
                logger.info(f"[DIRECT EDIT] Content is a prop expression: {{{prop_name}}}")
                logger.info(f"[DIRECT EDIT] Returning prop edit metadata for parent component update")

                # Return metadata indicating prop edit is needed
                return {
                    'type': 'prop_edit',
                    'prop_name': prop_name,
                    'old_value': old_content,  # {propName}
                    'new_value': new_text,
                    'requires_parent_update': True,
                    'element_selector': selector,
                    'tag_name': tag_name
                }
            else:
                logger.info(f"[DIRECT EDIT] {{{prop_name}}} appears to be a local variable, not a prop")

        # Check if content is an object property access like {service.title}
        object_prop_match = re.match(r'^\s*\{(\w+)\.(\w+)\}\s*$', old_content)
        if object_prop_match:
            object_name = object_prop_match.group(1)  # e.g., "service"
            property_name = object_prop_match.group(2)  # e.g., "title"

            logger.info(f"[DIRECT EDIT] Content is an object property access: {{{object_name}.{property_name}}}")

            # Try to extract array index from selector (e.g., "service-item-title-1" -> 1)
            array_index = self._extract_array_index_from_selector(selector)

            if array_index is not None:
                logger.info(f"[DIRECT EDIT] Extracted array index: {array_index}")

                # Try to find and update the array definition
                updated_code = self._update_array_item_property(
                    code=code,
                    object_name=object_name,
                    array_index=array_index,
                    property_name=property_name,
                    new_value=new_text
                )

                if updated_code and updated_code != code:
                    logger.info(f"[DIRECT EDIT] Successfully updated array item at index {array_index}")
                    return updated_code
                else:
                    logger.warning(f"[DIRECT EDIT] Failed to update array, falling back to hardcoding")

        # Check if content has JSX expressions or nested elements
        if '<' in old_content or '{' in old_content:
            logger.warning(f"[DIRECT EDIT] Complex content detected (has JSX/HTML), simple replacement may not work")
            # For now, still attempt replacement but log a warning

        # Build new code by replacing only the content between tags
        # Structure: [everything before content][new_text][closing tag and everything after]
        new_code = code[:tag_end] + new_text + code[content_end:]

        logger.info(f"[DIRECT EDIT] Text content replacement successful")
        logger.info(f"[DIRECT EDIT] Original code length: {len(code)}, New code length: {len(new_code)}")
        logger.info(f"[DIRECT EDIT] Content replaced: '{old_content}' -> '{new_text}'")

        return new_code

    def _is_component_prop(self, code: str, name: str) -> bool:
        """
        Check if a name is a component prop (appears in props destructuring).

        Args:
            code: Component code
            name: Variable name to check

        Returns:
            True if name appears in component props, False otherwise
        """
        # Pattern to match function component props destructuring
        # Matches:
        # - function Component({ title, subtitle }: Props)
        # - export function Component({ title }: Props)
        # - const Component = ({ title }: Props) =>
        # - export default function Component({ title }: Props)

        patterns = [
            # Function declarations
            rf'function\s+\w+\s*\(\s*\{{[^}}]*\b{name}\b[^}}]*\}}',
            # Arrow functions
            rf'=\s*\(\s*\{{[^}}]*\b{name}\b[^}}]*\}}',
            # With TypeScript types
            rf'\(\s*\{{[^}}]*\b{name}\b[^}}]*\}}\s*:\s*\w+',
        ]

        for pattern in patterns:
            if re.search(pattern, code):
                logger.debug(f"[PROP CHECK] '{name}' found in component props")
                return True

        logger.debug(f"[PROP CHECK] '{name}' not found in component props")
        return False

    def _extract_array_index_from_selector(self, selector: str) -> Optional[int]:
        """
        Extract array index from a selector like "service-item-title-1" -> 1

        Args:
            selector: Element selector with index suffix

        Returns:
            Integer index or None if not found
        """
        match = re.search(r'-(\d+)$', selector)
        if match:
            return int(match.group(1))
        return None

    def _update_array_item_property(
        self,
        code: str,
        object_name: str,
        array_index: int,
        property_name: str,
        new_value: str
    ) -> Optional[str]:
        """
        Update a property in an array item definition.

        For example, updating services[1].title in:
        const services = [
          { title: "First", description: "..." },
          { title: "Second", description: "..." }
        ]

        Args:
            code: Component code
            object_name: Name of the object variable (e.g., "service")
            array_index: Index of the item to update (0-based)
            property_name: Property to update (e.g., "title")
            new_value: New value for the property

        Returns:
            Updated code or None if update failed
        """
        logger.info(f"[ARRAY UPDATE] Looking for array definition for object '{object_name}'")

        # Strategy 1: Find the array name from the .map() call
        # Pattern: {arrayName}.map((objectName, index) => ...)
        map_pattern = rf'(\w+)\.map\s*\(\s*\(\s*{re.escape(object_name)}\s*,\s*\w+\s*\)\s*=>'
        map_match = re.search(map_pattern, code)

        possible_array_names = []

        if map_match:
            actual_array_name = map_match.group(1)
            logger.info(f"[ARRAY UPDATE] Found array name from .map() call: '{actual_array_name}'")
            possible_array_names.append(actual_array_name)

        # Strategy 2: Try common pluralization patterns as fallback
        possible_array_names.extend([
            f"{object_name}s",  # service -> services
            f"{object_name}es",  # hero -> heroes
            f"{object_name}ies",  # category -> categories
            object_name,  # sometimes it's the same
        ])

        logger.info(f"[ARRAY UPDATE] Trying array names in order: {possible_array_names}")

        for array_name in possible_array_names:
            # Pattern to match array definition: const arrayName = [...]
            # Supports various declaration styles: const, let, var, export const, etc.
            array_pattern = rf'(?:const|let|var|export\s+const)\s+{re.escape(array_name)}\s*=\s*\['

            match = re.search(array_pattern, code)
            if not match:
                continue

            logger.info(f"[ARRAY UPDATE] Found array definition for '{array_name}' at position {match.start()}")

            # Find the complete array definition (from [ to ])
            array_start = match.end() - 1  # Position of '['
            array_content, _ = self._extract_balanced_brackets(code, array_start)

            if array_content is None:
                logger.warning(f"[ARRAY UPDATE] Could not extract complete array definition")
                continue

            logger.info(f"[ARRAY UPDATE] Array content length: {len(array_content)} characters")

            # Parse the array to find individual items
            array_items = self._parse_array_items(array_content)

            if array_index >= len(array_items):
                logger.warning(f"[ARRAY UPDATE] Index {array_index} out of bounds (array has {len(array_items)} items)")
                continue

            logger.info(f"[ARRAY UPDATE] Found {len(array_items)} items in array")
            logger.info(f"[ARRAY UPDATE] Updating item at index {array_index}")

            # Get the item to update
            item_start, item_end, item_content = array_items[array_index]

            # Update the property in the item
            updated_item = self._update_object_property(item_content, property_name, new_value)

            if updated_item:
                # Reconstruct the code with the updated item
                # Calculate absolute positions
                abs_item_start = array_start + 1 + item_start
                abs_item_end = array_start + 1 + item_end

                new_code = code[:abs_item_start] + updated_item + code[abs_item_end:]

                logger.info(f"[ARRAY UPDATE] Successfully updated {property_name} in item {array_index}")
                return new_code
            else:
                logger.warning(f"[ARRAY UPDATE] Failed to update property in item")

        logger.warning(f"[ARRAY UPDATE] Could not find array definition for '{object_name}'")
        return None

    def _extract_balanced_brackets(self, code: str, start_pos: int) -> tuple[Optional[str], Optional[int]]:
        """
        Extract content between balanced brackets starting at start_pos.

        Args:
            code: Source code
            start_pos: Position of opening bracket

        Returns:
            Tuple of (content, end_position) or (None, None) if not found
        """
        if start_pos >= len(code) or code[start_pos] not in '[{':
            return None, None

        open_bracket = code[start_pos]
        close_bracket = ']' if open_bracket == '[' else '}'

        depth = 0
        i = start_pos

        while i < len(code):
            char = code[i]

            # Skip strings to avoid counting brackets inside strings
            if char in ['"', "'", '`']:
                # Find the end of the string
                quote = char
                i += 1
                while i < len(code):
                    if code[i] == quote and code[i-1] != '\\':
                        break
                    i += 1

            elif char == open_bracket:
                depth += 1
            elif char == close_bracket:
                depth -= 1
                if depth == 0:
                    # Found the closing bracket
                    content = code[start_pos + 1:i]
                    return content, i + 1

            i += 1

        return None, None

    def _parse_array_items(self, array_content: str) -> list[tuple[int, int, str]]:
        """
        Parse array items from array content.

        Returns list of (start_pos, end_pos, item_content) tuples.
        Each tuple represents one item in the array.

        Args:
            array_content: Content between [ and ]

        Returns:
            List of (start_pos, end_pos, item_content) tuples
        """
        items = []
        i = 0
        item_start = 0

        depth = 0
        in_string = False
        string_char = None

        while i < len(array_content):
            char = array_content[i]

            # Handle strings
            if char in ['"', "'", '`'] and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string and array_content[i-1] != '\\':
                in_string = False
                string_char = None

            # Only count brackets outside of strings
            if not in_string:
                if char in ['{', '[']:
                    depth += 1
                elif char in ['}', ']']:
                    depth -= 1
                elif char == ',' and depth == 0:
                    # Found item separator at top level
                    item_content = array_content[item_start:i].strip()
                    if item_content:
                        items.append((item_start, i, item_content))
                    item_start = i + 1

            i += 1

        # Don't forget the last item
        item_content = array_content[item_start:].strip()
        if item_content:
            items.append((item_start, len(array_content), item_content))

        return items

    def _update_object_property(self, object_content: str, property_name: str, new_value: str) -> Optional[str]:
        """
        Update a property in an object literal.

        Example:
            Input: '{ title: "Old", description: "..." }'
            property_name: 'title'
            new_value: 'New'
            Output: '{ title: "New", description: "..." }'

        Args:
            object_content: Object literal content
            property_name: Property to update
            new_value: New value (will be properly quoted)

        Returns:
            Updated object content or None if property not found
        """
        # Pattern to match property: key followed by : and value
        # Handles various formats: title: "value", title:"value", title: 'value'

        # Try to find the property with quoted string value
        pattern = rf'{re.escape(property_name)}\s*:\s*(["\'])((?:[^"\'\\]|\\.)*)(["\'])'
        match = re.search(pattern, object_content)

        if match:
            old_prop = match.group(0)
            # Preserve the quote style used in the original
            quote = match.group(1)
            # Escape the new value if needed
            escaped_value = new_value.replace('\\', '\\\\').replace(quote, f'\\{quote}')
            new_prop = f'{property_name}: {quote}{escaped_value}{quote}'

            updated_content = object_content.replace(old_prop, new_prop, 1)
            logger.info(f"[OBJECT UPDATE] Updated property '{property_name}'")
            logger.debug(f"[OBJECT UPDATE] Old: {old_prop}")
            logger.debug(f"[OBJECT UPDATE] New: {new_prop}")
            return updated_content

        logger.warning(f"[OBJECT UPDATE] Property '{property_name}' not found in object")
        return None

    def _edit_attribute(self, code: str, selector: str, attr_name: str, new_value: str) -> Optional[str]:
        """
        Edit an HTML attribute (src, href, alt, etc.)
        """
        logger.info(f"[DIRECT EDIT] Changing {attr_name} to: '{new_value}'")
        
        tag_match = self._find_element_tag(code, selector)
        if not tag_match:
            return None
        
        tag_start, tag_end, tag_content = tag_match
        
        # Check if attribute already exists
        attr_pattern = rf'{attr_name}=["\'](.*?)["\']'
        attr_match = re.search(attr_pattern, tag_content)
        
        if attr_match:
            # Replace existing attribute
            old_attr = attr_match.group(0)
            new_attr = f'{attr_name}="{new_value}"'
            new_tag_content = tag_content.replace(old_attr, new_attr, 1)
        else:
            # Add new attribute (insert before closing >)
            new_attr = f'{attr_name}="{new_value}"'
            if tag_content.endswith('/>'):
                # Self-closing tag
                new_tag_content = tag_content[:-2] + f' {new_attr} />'
            else:
                # Regular tag
                new_tag_content = tag_content[:-1] + f' {new_attr}>'
        
        # Replace in code
        new_code = code[:tag_start] + new_tag_content + code[tag_end:]
        
        return new_code
    
    def _edit_tailwind_class(self, code: str, selector: str, property_name: str, new_class: str) -> Optional[str]:
        """
        Edit a Tailwind CSS class in the className attribute.
        
        Args:
            code: Component code
            selector: Element selector (data-element value)
            property_name: Property name (e.g., 'color', 'fontSize', 'padding')
            new_class: New Tailwind class to apply
        """
        logger.info(f"[DIRECT EDIT] Changing Tailwind class for {property_name} to: '{new_class}'")
        
        tag_match = self._find_element_tag(code, selector)
        if not tag_match:
            return None
        
        tag_start, tag_end, tag_content = tag_match
        
        # Find className attribute
        # Handle both: className="..." and className={"..."}
        class_pattern = r'className=(?:["\'](.*?)["\']|\{["\'](.*?)["\']\})'
        class_match = re.search(class_pattern, tag_content)
        
        if not class_match:
            # No className attribute, add one
            new_attr = f'className="{new_class}"'
            if tag_content.endswith('/>'):
                new_tag_content = tag_content[:-2] + f' {new_attr} />'
            else:
                new_tag_content = tag_content[:-1] + f' {new_attr}>'
            
            new_code = code[:tag_start] + new_tag_content + code[tag_end:]
            return new_code
        
        # Get current className value
        old_classes = class_match.group(1) or class_match.group(2) or ''
        
        # Remove old classes matching the pattern for this property
        old_pattern = TAILWIND_PROPERTY_MAP.get(property_name, '')
        if old_pattern:
            # Remove classes matching the pattern
            classes = old_classes.split()
            filtered_classes = [c for c in classes if not re.match(old_pattern, c)]
            
            # Add new class
            filtered_classes.append(new_class)
            new_classes = ' '.join(filtered_classes)
        else:
            # Just add the new class
            new_classes = f"{old_classes} {new_class}".strip()
        
        # Replace className in tag
        old_class_attr = class_match.group(0)
        new_class_attr = f'className="{new_classes}"'
        new_tag_content = tag_content.replace(old_class_attr, new_class_attr, 1)
        
        # Replace in code
        new_code = code[:tag_start] + new_tag_content + code[tag_end:]
        
        return new_code


# Create singleton instance
direct_code_editor = DirectCodeEditor()

