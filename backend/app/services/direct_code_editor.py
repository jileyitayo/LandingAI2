"""
Direct Code Editor Service

This service handles direct code manipulation for property editing without using AI.
It parses React/TypeScript components and modifies specific properties like:
- Tailwind CSS classes (className attribute)
- Inline styles (style attribute)
- Text content
- Image sources (src, alt attributes)
- Link properties (href, target, rel attributes)

For prop-based values and array items, the service detects these patterns and
updates them at their source (parent component) instead of hardcoding values.

Smart link handling:
- Automatically converts <a> tags to <Link> components for internal links
- Automatically converts <Link> components to <a> tags for external links
- Manages React Router imports (adds "import { Link } from 'react-router-dom'")
- Handles attribute conversion (href ↔ to)
- Supports asChild pattern (Radix UI/shadcn): automatically redirects edits to child elements

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
    'textAlign': r'text-(?:left|center|right|justify)',
    'textTransform': r'(?:uppercase|lowercase|capitalize|normal-case)',
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
            if property_name == 'src':
                if not value_str.strip():
                    return (False, "src cannot be empty")
                # Basic URL validation for src
                if not (value_str.startswith('http') or value_str.startswith('/') or value_str.startswith('.')):
                    return (False, "Invalid URL format for src")

            # Validate href (allow empty for "no link")
            elif property_name == 'href':
                if value_str.strip():  # Only validate if not empty
                    # Basic URL validation
                    if not (value_str.startswith('http') or value_str.startswith('/') or
                            value_str.startswith('.') or value_str.startswith('#') or
                            value_str.startswith('mailto:') or value_str.startswith('tel:')):
                        return (False, "Invalid URL format for href")
            
            # Validate text content
            elif property_name == 'text':
                if len(value_str) > 10000:
                    return (False, "Text content too long (max 10,000 characters)")
            
            # Validate Tailwind classes
            elif property_name in TAILWIND_PROPERTY_MAP:
                if not value_str.strip():
                    return (False, f"{property_name} value cannot be empty")
                # Allow hex colors for color properties
                if property_name in ['color', 'backgroundColor', 'borderColor']:
                    # Allow either Tailwind classes or hex colors
                    is_hex = re.match(r'^#[0-9A-Fa-f]{6}$', value_str)
                    is_tailwind = re.match(r'^[\w-]+$', value_str)
                    if not (is_hex or is_tailwind):
                        return (False, f"Invalid color format: {value_str} (must be Tailwind class or hex color)")
                else:
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
        properties: List[Dict[str, Any]],
        files: Optional[Dict[str, str]] = None,
        component_tracker = None
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """
        Edit component properties directly with validation and error handling.

        Args:
            code: Original component code
            element_selector: data-element value to identify the element
            properties: List of property changes to apply
            files: All project files (optional, needed for prop-based arrays)
            component_tracker: ComponentRelationshipTracker instance (optional, needed for prop-based arrays)

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
            logger.info(f"[DIRECT EDIT] Properties to edit: {properties}")
            logger.info(f"[DIRECT EDIT] Code length: {len(code)} chars")

            # Verify element exists before attempting any changes
            if not self._find_element_tag(code, element_selector):
                logger.error(f"[DIRECT EDIT] Element with data-element='{element_selector}' not found in code")
                logger.error(f"[DIRECT EDIT] Code snippet (first 500 chars):\n{code[:500]}")
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
                        result = self._edit_attribute(new_code, element_selector, 'src', str(property_value), files, component_tracker)
                        # Check if result is array prop edit metadata
                        if isinstance(result, dict) and result.get('type') == 'array_prop_edit':
                            logger.info(f"[DIRECT EDIT] Array prop edit detected for '{result['prop_name']}'")
                            # Return early with array prop edit info for caller to handle
                            return (False, None, None, result)
                    elif property_name == 'href':
                        result = self._edit_attribute(new_code, element_selector, 'href', str(property_value), files, component_tracker)
                        # Check if result is prop edit or array prop edit metadata
                        if isinstance(result, dict) and result.get('type') in ['prop_edit', 'array_prop_edit']:
                            logger.info(f"[DIRECT EDIT] {result.get('type')} detected for href")
                            # Return early with prop edit info for caller to handle
                            return (False, None, None, result)
                    elif property_name == 'target':
                        result = self._edit_attribute(new_code, element_selector, 'target', str(property_value), files, component_tracker)
                        # Check if result is prop edit or array prop edit metadata
                        if isinstance(result, dict) and result.get('type') in ['prop_edit', 'array_prop_edit']:
                            logger.info(f"[DIRECT EDIT] {result.get('type')} detected for target")
                            return (False, None, None, result)
                    elif property_name == 'rel':
                        result = self._edit_attribute(new_code, element_selector, 'rel', str(property_value), files, component_tracker)
                        # Check if result is prop edit or array prop edit metadata
                        if isinstance(result, dict) and result.get('type') in ['prop_edit', 'array_prop_edit']:
                            logger.info(f"[DIRECT EDIT] {result.get('type')} detected for rel")
                            return (False, None, None, result)
                    elif property_name == 'alt':
                        result = self._edit_attribute(new_code, element_selector, 'alt', str(property_value), files, component_tracker)
                        # Check if result is array prop edit metadata
                        if isinstance(result, dict) and result.get('type') == 'array_prop_edit':
                            logger.info(f"[DIRECT EDIT] Array prop edit detected for '{result['prop_name']}'")
                            # Return early with array prop edit info for caller to handle
                            return (False, None, None, result)
                    elif property_name in TAILWIND_PROPERTY_MAP:
                        # Check if it's a custom hex color
                        if property_name in ['color', 'backgroundColor', 'borderColor'] and str(property_value).startswith('#'):
                            # Handle custom hex colors with inline styles
                            style_prop_map = {
                                'color': 'color',
                                'backgroundColor': 'backgroundColor',
                                'borderColor': 'borderColor'
                            }
                            logger.info(f"[DIRECT EDIT] Applying inline style for {property_name}: {property_value}")
                            result = self._edit_inline_style(new_code, element_selector, style_prop_map[property_name], str(property_value))
                            if not result:
                                logger.error(f"[DIRECT EDIT] _edit_inline_style returned None for selector: {element_selector}")
                        else:
                            # Handle regular Tailwind classes
                            logger.info(f"[DIRECT EDIT] Applying Tailwind class for {property_name}: {property_value}")
                            result = self._edit_tailwind_class(new_code, element_selector, property_name, str(property_value))
                            if not result:
                                logger.error(f"[DIRECT EDIT] _edit_tailwind_class returned None for selector: {element_selector}")
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

    def update_array_prop_at_source(
        self,
        files: Dict[str, str],
        component_file: str,
        prop_name: str,
        array_index: int,
        property_path: str,
        new_value: str,
        object_name: str,
        component_tracker
    ) -> Tuple[bool, Optional[Dict[str, str]], Optional[str]]:
        """
        Update an array item property at its source (parent component) instead of hardcoding.
        
        For example, when editing images[7].src in FullPortfolioGallery component where
        images comes from props, this updates portfolioImages[7].src in the parent page.

        Args:
            files: All project files (dict of file_path -> content)
            component_file: Path to the component file being edited (e.g., "src/components/FullPortfolioGallery.tsx")
            prop_name: Name of the prop that contains the array (e.g., "images")
            array_index: Index of the array item to update (0-based)
            property_path: Property path to update (e.g., "src", "alt")
            new_value: New value for the property
            object_name: Object name from child component's map call (e.g., "image" from images.map((image, index) => ...))
            component_tracker: ComponentRelationshipTracker instance

        Returns:
            Tuple of (success, updated_files, error_message)
            - success: True if array item updated at source, False otherwise
            - updated_files: Dict of updated files if successful, None otherwise
            - error_message: Error description if failed, None otherwise
        """
        try:
            logger.info(f"[ARRAY PROP UPDATE] Updating array prop '{prop_name}[{array_index}].{property_path}' at source")
            logger.info(f"[ARRAY PROP UPDATE] Component: {component_file}")

            # Extract component name from file path
            component_name = Path(component_file).stem
            logger.info(f"[ARRAY PROP UPDATE] Component name: {component_name}")

            # Find where this prop is passed from
            prop_source = component_tracker.find_prop_source(component_file, prop_name)

            if not prop_source:
                error_msg = f"Could not find source for prop '{prop_name}' in component '{component_name}'"
                logger.warning(f"[ARRAY PROP UPDATE] {error_msg}")
                return (False, None, error_msg)

            parent_file, prop_value, usage = prop_source
            logger.info(f"[ARRAY PROP UPDATE] Found prop source in: {parent_file}")
            logger.info(f"[ARRAY PROP UPDATE] Prop value: '{prop_value}'")

            # Extract array variable name from prop value
            # prop_value might be: "{portfolioImages}" or "portfolioImages"
            # Remove JSX expression braces if present
            array_var_name = prop_value.strip()
            if array_var_name.startswith('{') and array_var_name.endswith('}'):
                array_var_name = array_var_name[1:-1].strip()
            
            logger.info(f"[ARRAY PROP UPDATE] Array variable name: '{array_var_name}'")

            # Get parent file content
            if parent_file not in files:
                error_msg = f"Parent file '{parent_file}' not found in project files"
                logger.error(f"[ARRAY PROP UPDATE] {error_msg}")
                return (False, None, error_msg)

            parent_code = files[parent_file]

            # Find the object name used in the map call
            # Since the map call is in the CHILD component (not parent), we use the object_name
            # from the metadata (extracted from child component's map call)
            # The object_name comes from: images.map((image, index) => ...) -> "image"
            found_object_name = None
            
            # Try to find map call in parent (in case parent also uses this array)
            map_pattern = rf'{re.escape(array_var_name)}\.map\s*\(\s*\(\s*(\w+)'
            map_match = re.search(map_pattern, parent_code)
            
            if map_match:
                found_object_name = map_match.group(1)
                logger.info(f"[ARRAY PROP UPDATE] Found object name '{found_object_name}' from map call in parent")
            else:
                # Use object_name from metadata (extracted from child component)
                # This is the object name used in the child: images.map((image, index) => ...)
                found_object_name = object_name  # Use the parameter passed in
                if not found_object_name:
                    # Fallback: infer from array name (remove 's' or use common patterns)
                    found_object_name = array_var_name.rstrip('s') if array_var_name.endswith('s') else array_var_name
                    # Handle special cases: portfolioImages -> portfolioImage -> image
                    if 'Image' in found_object_name:
                        found_object_name = 'image'
                    elif 'Item' in found_object_name:
                        found_object_name = 'item'
                logger.info(f"[ARRAY PROP UPDATE] Using object name '{found_object_name}' (from child component or inferred)")

            # Update the array item in the parent file
            # Use array_var_name directly since we know it from the prop value
            updated_parent_code = self._update_array_item_attribute(
                code=parent_code,
                object_name=found_object_name,
                array_index=array_index,
                property_path=property_path,
                new_value=new_value,
                array_name_override=array_var_name  # Use the known array name from prop
            )

            # Check if update succeeded
            # Note: updated_parent_code could be a dict (metadata) or a string (updated code)
            if isinstance(updated_parent_code, dict):
                # This shouldn't happen when array_name_override is provided, but handle it
                error_msg = f"Unexpected metadata return when updating array '{array_var_name}'"
                logger.error(f"[ARRAY PROP UPDATE] {error_msg}")
                return (False, None, error_msg)
            
            if not updated_parent_code:
                error_msg = f"Failed to update array item '{array_var_name}[{array_index}].{property_path}' in parent component"
                logger.error(f"[ARRAY PROP UPDATE] {error_msg}")
                logger.error(f"[ARRAY PROP UPDATE] Array '{array_var_name}' may not exist or have different structure")
                logger.error(f"[ARRAY PROP UPDATE] Parent file content snippet: {parent_code[:500]}...")
                return (False, None, error_msg)
            
            # Log success - the update method already logged success internally
            logger.info(f"[ARRAY PROP UPDATE] Successfully updated array item via _update_array_item_attribute")
            
            # Check if code actually changed (if value was already the same, code might be identical)
            code_changed = updated_parent_code != parent_code
            if not code_changed:
                logger.info(f"[ARRAY PROP UPDATE] Code unchanged (value may already be '{new_value}'), but update succeeded")
                # Still consider this a success - the value is already correct

            # Verify the updated code structure
            if not self._verify_code_structure(updated_parent_code):
                error_msg = "Updated parent code failed structure validation"
                logger.error(f"[ARRAY PROP UPDATE] {error_msg}")
                return (False, None, error_msg)

            # Create updated files dict
            updated_files = files.copy()
            updated_files[parent_file] = updated_parent_code

            logger.info(f"[ARRAY PROP UPDATE] Successfully updated '{array_var_name}[{array_index}].{property_path}' in {parent_file}")
            return (True, updated_files, None)

        except Exception as e:
            error_msg = f"Unexpected error updating array prop at source: {str(e)}"
            logger.error(f"[ARRAY PROP UPDATE] {error_msg}", exc_info=True)
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

    def _update_array_item_attribute(
        self,
        code: str,
        object_name: str,
        array_index: int,
        property_path: str,
        new_value: str,
        files: Optional[Dict[str, str]] = None,
        component_tracker = None,
        array_name_override: Optional[str] = None
    ) -> Optional[str | Dict[str, Any]]:
        """
        Update a property in an array item definition for attributes (src, alt, etc.).

        For example, updating images[0].src in:
        const images = [
          { src: "old-url", alt: "..." },
          { src: "...", alt: "..." }
        ]

        Also handles nested properties like images[0].media.url
        If array is a prop, returns metadata dict for parent update.

        Args:
            code: Component code
            object_name: Name of the object variable (e.g., "image")
            array_index: Index of the item to update (0-based)
            property_path: Property path to update (e.g., "src", "url", "media.url")
            new_value: New value for the property
            files: All project files (needed for prop-based arrays)
            component_tracker: ComponentRelationshipTracker instance (needed for prop-based arrays)
            array_name_override: Optional array name to use directly (skips map call detection)

        Returns:
            Updated code if successful, metadata dict if prop-based array, or None if failed
        """
        logger.info(f"[ARRAY ATTR UPDATE] Looking for array definition for object '{object_name}'")
        logger.info(f"[ARRAY ATTR UPDATE] Updating property '{property_path}' at index {array_index}")

        possible_array_names = []
        
        # If array_name_override is provided, use it directly
        if array_name_override:
            possible_array_names = [array_name_override]
            logger.info(f"[ARRAY ATTR UPDATE] Using provided array name: '{array_name_override}'")
        else:
            # Strategy 1: Find the array name from the .map() call
            # Pattern: {arrayName}.map((objectName, index) => ...)
            map_pattern = rf'(\w+)\.map\s*\(\s*\(\s*{re.escape(object_name)}\s*,\s*\w+\s*\)\s*=>'
            map_match = re.search(map_pattern, code)

            if map_match:
                actual_array_name = map_match.group(1)
                logger.info(f"[ARRAY ATTR UPDATE] Found array name from .map() call: '{actual_array_name}'")
                possible_array_names.append(actual_array_name)

            # Strategy 2: Try common pluralization patterns as fallback
            possible_array_names.extend([
                f"{object_name}s",  # image -> images
                f"{object_name}es",  # hero -> heroes
                f"{object_name}ies",  # category -> categories
                object_name,  # sometimes it's the same
            ])

        logger.info(f"[ARRAY ATTR UPDATE] Trying array names in order: {possible_array_names}")

        for array_name in possible_array_names:
            # Skip prop check if array_name_override is provided (we know it's a local array)
            if array_name_override and array_name != array_name_override:
                # When override is provided, only process that specific array name
                continue
                
            if array_name_override:
                is_prop = False  # When override is provided, it's always a local array
                logger.info(f"[ARRAY ATTR UPDATE] Using array_name_override '{array_name_override}', skipping prop check")
            else:
                # Check if array comes from props FIRST (before looking for local definition)
                is_prop = self._is_component_prop(code, array_name)
                logger.info(f"[ARRAY ATTR UPDATE] Checking array '{array_name}': is_prop={is_prop}")
            
            # Pattern to match array definition: const arrayName = [...]
            # Supports various declaration styles: const, let, var, export const, etc.
            array_pattern = rf'(?:const|let|var|export\s+const)\s+{re.escape(array_name)}\s*=\s*\['

            match = re.search(array_pattern, code)
            if not match:
                # If not found as hardcoded, and it's a prop, return metadata for parent update
                if is_prop and not array_name_override:  # Don't return metadata if using override
                    logger.info(f"[ARRAY ATTR UPDATE] Array '{array_name}' is a prop but not found locally")
                    if files is not None and component_tracker is not None:
                        logger.info(f"[ARRAY ATTR UPDATE] Returning metadata for parent update")
                        return {
                            'type': 'array_prop_edit',
                            'prop_name': array_name,
                            'array_index': array_index,
                            'property_path': property_path,
                            'new_value': new_value,
                            'object_name': object_name
                        }
                    else:
                        logger.warning(f"[ARRAY ATTR UPDATE] Array '{array_name}' is a prop but files/component_tracker not provided")
                continue

            # Found array definition locally - update it
            logger.info(f"[ARRAY ATTR UPDATE] Found array definition for '{array_name}' at position {match.start()}")

            # Find the complete array definition (from [ to ])
            array_start = match.end() - 1  # Position of '['
            array_content, _ = self._extract_balanced_brackets(code, array_start)

            if array_content is None:
                logger.warning(f"[ARRAY ATTR UPDATE] Could not extract complete array definition")
                continue

            logger.info(f"[ARRAY ATTR UPDATE] Array content length: {len(array_content)} characters")

            # Parse the array to find individual items
            array_items = self._parse_array_items(array_content)

            if array_index >= len(array_items):
                logger.warning(f"[ARRAY ATTR UPDATE] Index {array_index} out of bounds (array has {len(array_items)} items)")
                continue

            logger.info(f"[ARRAY ATTR UPDATE] Found {len(array_items)} items in array")
            logger.info(f"[ARRAY ATTR UPDATE] Updating item at index {array_index}")

            # Get the item to update
            item_start, item_end, item_content = array_items[array_index]
            
            logger.info(f"[ARRAY ATTR UPDATE] Item content at index {array_index}: {item_content[:200]}...")

            # Update the property in the item (handles nested properties)
            updated_item = self._update_object_property_path(item_content, property_path, new_value)

            if updated_item:
                # Reconstruct the code with the updated item
                # Calculate absolute positions
                abs_item_start = array_start + 1 + item_start
                abs_item_end = array_start + 1 + item_end

                new_code = code[:abs_item_start] + updated_item + code[abs_item_end:]

                logger.info(f"[ARRAY ATTR UPDATE] Successfully updated {property_path} in item {array_index}")
                if is_prop:
                    logger.info(f"[ARRAY ATTR UPDATE] Note: Array '{array_name}' is a prop - consider updating at parent component")
                return new_code
            else:
                logger.warning(f"[ARRAY ATTR UPDATE] Failed to update property '{property_path}' in item at index {array_index}")
                logger.warning(f"[ARRAY ATTR UPDATE] Item content: {item_content}")
                logger.warning(f"[ARRAY ATTR UPDATE] Property path: {property_path}, New value: {new_value}")

        logger.warning(f"[ARRAY ATTR UPDATE] Could not find array definition for '{object_name}'")
        logger.warning(f"[ARRAY ATTR UPDATE] Tried array names: {possible_array_names}")
        return None

    def _update_object_property_path(self, object_content: str, property_path: str, new_value: str) -> Optional[str]:
        """
        Update a property in an object literal, supporting nested properties.

        Examples:
        - property_path='src' -> updates { src: "..." }
        - property_path='media.url' -> updates { media: { url: "..." } }

        Args:
            object_content: Object literal content
            property_path: Property path (e.g., 'src', 'media.url')
            new_value: New value (will be properly quoted)

        Returns:
            Updated object content or None if property not found
        """
        # Handle nested properties
        if '.' in property_path:
            parts = property_path.split('.')
            main_prop = parts[0]
            nested_path = '.'.join(parts[1:])
            
            # Find the main property object
            # Pattern: mainProp: { ... }
            main_pattern = rf'{re.escape(main_prop)}\s*:\s*\{{'
            main_match = re.search(main_pattern, object_content)
            
            if main_match:
                # Find the nested object
                nested_start = main_match.end() - 1  # Position of '{'
                nested_content, nested_end_pos = self._extract_balanced_brackets(object_content, nested_start)
                
                if nested_content:
                    # Recursively update nested property
                    updated_nested = self._update_object_property_path(nested_content, nested_path, new_value)
                    
                    if updated_nested:
                        # Replace the nested object in the main object
                        abs_nested_start = nested_start + 1
                        abs_nested_end = nested_end_pos - 1
                        updated_object = (
                            object_content[:abs_nested_start] + 
                            updated_nested + 
                            object_content[abs_nested_end:]
                        )
                        logger.info(f"[OBJECT UPDATE] Updated nested property '{property_path}'")
                        return updated_object
            
            logger.warning(f"[OBJECT UPDATE] Could not find nested property '{property_path}'")
            return None
        else:
            # Simple property update (non-nested)
            return self._update_object_property(object_content, property_path, new_value)

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
        logger.info(f"[OBJECT UPDATE] Updating property '{property_name}' with value '{new_value}'")
        logger.debug(f"[OBJECT UPDATE] Object content: {object_content[:200]}...")
        
        # Pattern to match property: key followed by : and value
        # Handles various formats: title: "value", title:"value", title: 'value'
        # Also handles: alt: 'value' or alt: "value"

        # Try to find the property with quoted string value
        # Match: propertyName: "value" or propertyName: 'value'
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

        # Try without quotes (for numeric or boolean values, or template literals)
        # Pattern: propertyName: value (no quotes)
        pattern_no_quotes = rf'{re.escape(property_name)}\s*:\s*([^,}}]+)'
        match_no_quotes = re.search(pattern_no_quotes, object_content)
        
        if match_no_quotes:
            old_prop = match_no_quotes.group(0)
            # For string values, add quotes
            new_prop = f'{property_name}: "{new_value}"'
            updated_content = object_content.replace(old_prop, new_prop, 1)
            logger.info(f"[OBJECT UPDATE] Updated property '{property_name}' (was unquoted)")
            return updated_content

        logger.warning(f"[OBJECT UPDATE] Property '{property_name}' not found in object")
        logger.warning(f"[OBJECT UPDATE] Object content: {object_content}")
        return None

    def _has_import(self, code: str, module_name: str, import_name: str) -> bool:
        """
        Check if a specific import exists in the code.

        Args:
            code: Component code
            module_name: Module to import from (e.g., 'react-router-dom')
            import_name: Name to import (e.g., 'Link')

        Returns:
            True if import exists, False otherwise
        """
        # Pattern to match: import { Link } from 'react-router-dom';
        # Also handles: import { Link, Route } from 'react-router-dom';
        # And: import { Route, Link } from 'react-router-dom';
        pattern = rf'import\s+\{{[^}}]*\b{re.escape(import_name)}\b[^}}]*\}}\s+from\s+["\'{re.escape(module_name)}"\']'

        if re.search(pattern, code):
            logger.debug(f"[IMPORT CHECK] Found import {{ {import_name} }} from '{module_name}'")
            return True

        logger.debug(f"[IMPORT CHECK] Import {{ {import_name} }} from '{module_name}' not found")
        return False

    def _add_import(self, code: str, module_name: str, import_name: str) -> str:
        """
        Add an import statement to the code if it doesn't already exist.

        Args:
            code: Component code
            module_name: Module to import from (e.g., 'react-router-dom')
            import_name: Name to import (e.g., 'Link')

        Returns:
            Updated code with import added
        """
        # Check if import already exists
        if self._has_import(code, module_name, import_name):
            logger.info(f"[IMPORT] Import {{ {import_name} }} from '{module_name}' already exists")
            return code

        logger.info(f"[IMPORT] Adding import {{ {import_name} }} from '{module_name}'")

        # Check if there's an existing import from the same module
        # Pattern: import { ... } from 'module-name';
        existing_import_pattern = rf'(import\s+\{{)([^}}]*)\}}\s+from\s+["\'{re.escape(module_name)}"\']'
        existing_match = re.search(existing_import_pattern, code)

        if existing_match:
            # Add to existing import
            logger.info(f"[IMPORT] Adding to existing import from '{module_name}'")
            existing_imports = existing_match.group(2).strip()
            # Add the new import to the list
            new_imports = f"{existing_imports}, {import_name}"
            new_import_statement = f"import {{ {new_imports} }} from '{module_name}';"

            # Replace the old import statement
            old_import_statement = existing_match.group(0)
            code = code.replace(old_import_statement, new_import_statement, 1)
        else:
            # Add new import statement
            logger.info(f"[IMPORT] Adding new import statement for '{module_name}'")
            new_import = f"import {{ {import_name} }} from '{module_name}';\n"

            # Find where to insert the import (after other imports or at the beginning)
            # Look for the last import statement
            import_pattern = r'import\s+.*?from\s+["\'].*?["\'];?\s*\n'
            import_matches = list(re.finditer(import_pattern, code))

            if import_matches:
                # Insert after the last import
                last_import = import_matches[-1]
                insert_pos = last_import.end()
                code = code[:insert_pos] + new_import + code[insert_pos:]
            else:
                # No imports found, add at the beginning
                code = new_import + code

        return code

    def _is_internal_link(self, url: str) -> bool:
        """
        Check if a URL is an internal link (should use React Router <Link>).

        Args:
            url: The URL to check

        Returns:
            True if internal (relative path or hash), False if external
        """
        if not url or not url.strip():
            return False

        url = url.strip()

        # Internal links:
        # - Start with / (e.g., /about, /contact)
        # - Start with # (e.g., #section)
        # External links:
        # - Start with http:// or https://
        # - mailto: or tel: links

        is_internal = url.startswith('/') or url.startswith('#')
        is_external = (url.startswith('http://') or url.startswith('https://') or
                      url.startswith('mailto:') or url.startswith('tel:'))

        # If it starts with ./ or ../ it's also internal (relative)
        if url.startswith('./') or url.startswith('../'):
            is_internal = True

        return is_internal and not is_external

    def _has_as_child_prop(self, tag_content: str) -> bool:
        """
        Check if a tag has the asChild prop (used in Radix UI/shadcn patterns).

        Args:
            tag_content: The tag content to check

        Returns:
            True if asChild prop is present, False otherwise
        """
        # Pattern to match: asChild or asChild={true}
        # Also handles: asChild={true}, asChild={false} (though false means it's not actually asChild)
        if re.search(r'\basChild\s*(?:=\{true\})?(?:\s|>|/)', tag_content):
            logger.debug(f"[ASCHILD] Found asChild prop in tag")
            return True
        return False

    def _extract_child_element_selector(self, code: str, parent_selector: str) -> Optional[str]:
        """
        Extract the data-element selector of the child element within an asChild parent.

        For example:
        <Button asChild data-element="parent">
          <Link to="/contact" data-element="child">Text</Link>
        </Button>

        Given parent_selector="parent", returns "child"

        Args:
            code: Component code
            parent_selector: The selector of the parent element

        Returns:
            Child element's selector or None if not found
        """
        logger.info(f"[ASCHILD] Extracting child element from parent with selector '{parent_selector}'")

        # Find the parent element
        element_data = self._find_element_content(code, parent_selector)
        if not element_data:
            logger.warning(f"[ASCHILD] Could not find parent element with selector '{parent_selector}'")
            return None

        tag_start, tag_end, content_end, closing_tag_end, tag_name, content = element_data

        logger.debug(f"[ASCHILD] Parent content: {content[:200]}...")

        # Find the first child element with data-element attribute
        # Pattern to match: <AnyTag ... data-element="value" ... >
        child_pattern = r'<(\w+(?:\.\w+)?)[^>]*data-element=["\']([^"\']+)["\']'
        child_match = re.search(child_pattern, content)

        if child_match:
            child_selector = child_match.group(2)
            child_tag = child_match.group(1)
            logger.info(f"[ASCHILD] Found child element: <{child_tag}> with selector '{child_selector}'")
            return child_selector

        # If no child has data-element, we need to add one to the first child element
        # Find the first opening tag in content
        first_child_pattern = r'<(\w+(?:\.\w+)?)'
        first_child_match = re.search(first_child_pattern, content)

        if first_child_match:
            logger.warning(f"[ASCHILD] Child element has no data-element attribute")
            logger.info(f"[ASCHILD] Will add data-element to child automatically")
            # Generate a child selector based on parent selector
            child_selector_candidate = f"{parent_selector}-child"
            return child_selector_candidate

        logger.warning(f"[ASCHILD] No child element found in parent content")
        return None

    def _add_data_element_to_child(self, code: str, parent_selector: str, child_selector: str) -> Optional[str]:
        """
        Add data-element attribute to the child element of an asChild parent.

        Args:
            code: Component code
            parent_selector: Parent element's selector
            child_selector: Selector to add to child

        Returns:
            Updated code with data-element added to child, or None if failed
        """
        logger.info(f"[ASCHILD] Adding data-element='{child_selector}' to child of '{parent_selector}'")

        # Find the parent element
        element_data = self._find_element_content(code, parent_selector)
        if not element_data:
            return None

        tag_start, tag_end, content_end, closing_tag_end, tag_name, content = element_data

        # Find the first child element opening tag
        first_child_pattern = r'<(\w+(?:\.\w+)?)([^>]*?)(/?>)'
        first_child_match = re.search(first_child_pattern, content)

        if not first_child_match:
            logger.warning(f"[ASCHILD] No child element found to add data-element to")
            return None

        child_tag_name = first_child_match.group(1)
        child_attrs = first_child_match.group(2)
        child_closing = first_child_match.group(3)

        # Add data-element attribute
        new_child_tag = f'<{child_tag_name}{child_attrs} data-element="{child_selector}"{child_closing}'

        # Replace in content
        new_content = content.replace(first_child_match.group(0), new_child_tag, 1)

        # Reconstruct code
        new_code = (
            code[:tag_end] +
            new_content +
            code[content_end:]
        )

        logger.info(f"[ASCHILD] Successfully added data-element to child")
        return new_code

    def _convert_tag_type(self, code: str, selector: str, from_tag: str, to_tag: str, attr_conversions: Dict[str, str] = None) -> Optional[str]:
        """
        Convert a tag from one type to another (e.g., <a> to <Link>).

        Args:
            code: Component code
            selector: Element selector (data-element value)
            from_tag: Source tag name (e.g., 'a')
            to_tag: Target tag name (e.g., 'Link')
            attr_conversions: Optional dict mapping old attribute names to new ones (e.g., {'href': 'to'})

        Returns:
            Updated code with tag converted, or None if failed
        """
        logger.info(f"[TAG CONVERT] Converting <{from_tag}> to <{to_tag}> for selector '{selector}'")

        # Find the opening and closing tags
        element_data = self._find_element_content(code, selector)
        if not element_data:
            logger.error(f"[TAG CONVERT] Could not find element with selector: {selector}")
            return None

        tag_start, tag_end, content_end, closing_tag_end, tag_name, content = element_data

        if tag_name != from_tag:
            logger.warning(f"[TAG CONVERT] Expected <{from_tag}> but found <{tag_name}>")
            return None

        # Extract the opening tag
        opening_tag = code[tag_start:tag_end]

        # Replace tag name in opening tag
        new_opening_tag = re.sub(rf'^<{re.escape(from_tag)}\b', f'<{to_tag}', opening_tag)

        # Apply attribute conversions if specified
        if attr_conversions:
            for old_attr, new_attr in attr_conversions.items():
                # Pattern to match attribute: oldAttr="value" or oldAttr={value}
                attr_pattern = rf'{re.escape(old_attr)}=(["\'{{])'
                if re.search(attr_pattern, new_opening_tag):
                    new_opening_tag = re.sub(
                        rf'\b{re.escape(old_attr)}=',
                        f'{new_attr}=',
                        new_opening_tag
                    )
                    logger.info(f"[TAG CONVERT] Converted attribute '{old_attr}' to '{new_attr}'")

        # Replace closing tag
        closing_tag = code[content_end:closing_tag_end]
        new_closing_tag = closing_tag.replace(f'</{from_tag}>', f'</{to_tag}>')

        # Build new code
        new_code = (
            code[:tag_start] +
            new_opening_tag +
            content +
            new_closing_tag +
            code[closing_tag_end:]
        )

        logger.info(f"[TAG CONVERT] Successfully converted <{from_tag}> to <{to_tag}>")
        return new_code

    def _extract_simple_prop_expression(self, tag_content: str, attr_name: str) -> Optional[str]:
        """
        Extract a simple prop name from an attribute expression like {propName}.

        Examples:
        - href={link} -> 'link'
        - target={linkTarget} -> 'linkTarget'
        - href={url} -> 'url'

        Args:
            tag_content: The HTML tag content containing the attribute
            attr_name: The attribute name (e.g., 'href', 'target', 'rel')

        Returns:
            Prop name or None if not a simple prop expression
        """
        # Pattern to match JSX expression attributes: attrName={expression}
        expr_pattern = rf'{re.escape(attr_name)}=\{{([^}}]+)\}}'
        expr_match = re.search(expr_pattern, tag_content)

        if not expr_match:
            return None

        expression = expr_match.group(1).strip()

        # Check if it's a simple identifier (no dots, no complex expressions)
        # Matches: link, url, linkTarget, etc.
        # Does NOT match: item.link, navItem.href, etc.
        if re.match(r'^\w+$', expression):
            logger.debug(f"[SIMPLE PROP] Found simple prop expression: {{{expression}}}")
            return expression

        logger.debug(f"[SIMPLE PROP] Expression '{expression}' is not a simple prop")
        return None

    def _extract_attribute_expression(self, tag_content: str, attr_name: str) -> Optional[tuple[str, str]]:
        """
        Extract the object name and property path from an attribute expression.

        Examples:
        - src={image.src} -> ('image', 'src')
        - src={image.url} -> ('image', 'url')
        - src={image.media.url} -> ('image', 'media.url')
        - alt={item.alt} -> ('item', 'alt')
        - href={navItem.href} -> ('navItem', 'href')

        Args:
            tag_content: The HTML tag content containing the attribute
            attr_name: The attribute name (e.g., 'src', 'alt', 'href')

        Returns:
            Tuple of (object_name, property_path) or None if not found
        """
        # Pattern to match JSX expression attributes: attrName={expression}
        # Handles: src={image.src}, src={image.url}, src={image.media.url}
        expr_pattern = rf'{re.escape(attr_name)}=\{{([^}}]+)\}}'
        expr_match = re.search(expr_pattern, tag_content)

        if not expr_match:
            return None

        expression = expr_match.group(1).strip()

        # Pattern to match object property access: objectName.property or objectName.nested.property
        # Matches: image.src, image.url, image.media.url, item.alt, navItem.href
        prop_pattern = r'^(\w+)(?:\.(\w+(?:\.\w+)*))?$'
        prop_match = re.match(prop_pattern, expression)

        if prop_match:
            object_name = prop_match.group(1)
            property_path = prop_match.group(2) if prop_match.group(2) else attr_name  # Default to attr_name if no property specified

            # Handle fallback patterns like image.url || image.src
            # Use the first property found
            fallback_match = re.search(r'(\w+)\.(\w+)', expression)
            if fallback_match and fallback_match.group(1) == object_name:
                property_path = fallback_match.group(2)

            logger.info(f"[ATTR EXPR] Extracted: object='{object_name}', property='{property_path}' from expression '{expression}'")
            return (object_name, property_path)

        logger.debug(f"[ATTR EXPR] Could not extract property from expression: '{expression}'")
        return None

    def _edit_attribute(self, code: str, selector: str, attr_name: str, new_value: str, files: Optional[Dict[str, str]] = None, component_tracker = None) -> Optional[str | Dict[str, Any]]:
        """
        Edit an HTML attribute (src, href, alt, target, rel, etc.)

        For link attributes (href), intelligently handles:
        - <Link to="/about"> for internal links
        - <a href="https://..."> for external links

        For asChild pattern (Radix UI/shadcn components):
        - Automatically detects asChild prop on parent
        - Redirects all operations to the child element
        - Adds data-element to child if needed

        For array items (detected via selector pattern), attempts to update
        the array item property instead of hardcoding the attribute.

        For prop expressions, returns metadata for parent component update.

        Returns:
            Updated code, metadata dict for prop-based arrays/props, or None if failed
        """
        logger.info(f"[DIRECT EDIT] Changing {attr_name} to: '{new_value}'")

        tag_match = self._find_element_tag(code, selector)
        if not tag_match:
            return None

        tag_start, tag_end, tag_content = tag_match

        # Extract tag name to determine if it's a Link component or a tag
        tag_name_match = re.match(r'<(\w+(?:\.\w+)?)', tag_content)
        tag_name = tag_name_match.group(1) if tag_name_match else None
        logger.info(f"[DIRECT EDIT] Tag name: {tag_name}")

        # Handle asChild pattern (Radix UI/shadcn components)
        # If parent has asChild prop, redirect operations to the child element
        if self._has_as_child_prop(tag_content):
            logger.info(f"[DIRECT EDIT] Detected asChild prop on element '{selector}'")

            # Extract or create child element selector
            child_selector = self._extract_child_element_selector(code, selector)

            if child_selector:
                # Check if child already has data-element
                child_has_selector = self._find_element_tag(code, child_selector) is not None

                if not child_has_selector:
                    # Add data-element to child
                    logger.info(f"[DIRECT EDIT] Adding data-element to child: '{child_selector}'")
                    code = self._add_data_element_to_child(code, selector, child_selector)
                    if not code:
                        logger.error(f"[DIRECT EDIT] Failed to add data-element to child")
                        return None

                # Redirect to child element
                logger.info(f"[DIRECT EDIT] Redirecting edit to child element: '{child_selector}'")
                return self._edit_attribute(code, child_selector, attr_name, new_value, files, component_tracker)
            else:
                logger.warning(f"[DIRECT EDIT] Could not extract child from asChild parent, continuing with parent")

        # For href attribute, determine the correct attribute name based on tag and link type
        actual_attr_name = attr_name
        if attr_name == 'href':
            is_internal = self._is_internal_link(new_value)
            logger.info(f"[DIRECT EDIT] Link type: {'internal' if is_internal else 'external'}")

            if tag_name == 'Link' and is_internal:
                # Use 'to' attribute for internal links in Link component
                actual_attr_name = 'to'
                logger.info(f"[DIRECT EDIT] Using 'to' attribute for Link component with internal link")
            elif tag_name == 'Link' and not is_internal:
                # External link with Link component - warn but still use href
                # (Link components typically shouldn't be used for external links)
                logger.warning(f"[DIRECT EDIT] External link detected in Link component - consider using <a> tag")
                actual_attr_name = 'href'
            elif tag_name == 'a' and is_internal:
                # Internal link with a tag - use href (though Link would be better)
                actual_attr_name = 'href'
                logger.info(f"[DIRECT EDIT] Using 'href' for <a> tag with internal link")
            else:
                # External link with a tag - use href (correct)
                actual_attr_name = 'href'

        logger.info(f"[DIRECT EDIT] Using attribute: {actual_attr_name}")

        # Handle tag conversion when link type changes (e.g., <a> to <Link> or vice versa)
        tag_was_converted = False
        if attr_name == 'href':
            is_internal = self._is_internal_link(new_value)

            # Convert <a> to <Link> for internal links
            if tag_name == 'a' and is_internal:
                logger.info(f"[DIRECT EDIT] Converting <a> to <Link> for internal link")
                # Add Link import
                code = self._add_import(code, 'react-router-dom', 'Link')
                # Convert tag (this will convert href to to)
                converted_code = self._convert_tag_type(code, selector, 'a', 'Link', {'href': 'to'})
                if converted_code:
                    code = converted_code
                    tag_was_converted = True
                    actual_attr_name = 'to'  # Update to reflect the converted attribute
                    # Re-find the tag after conversion to update tag_content
                    tag_match = self._find_element_tag(code, selector)
                    if tag_match:
                        tag_start, tag_end, tag_content = tag_match
                    logger.info(f"[DIRECT EDIT] Successfully converted <a> to <Link>")
                else:
                    logger.warning(f"[DIRECT EDIT] Failed to convert <a> to <Link>, continuing with <a> tag")

            # Convert <Link> to <a> for external links
            elif tag_name == 'Link' and not is_internal and new_value.strip():  # Only if not empty
                logger.info(f"[DIRECT EDIT] Converting <Link> to <a> for external link")
                # Convert tag (this will convert to to href)
                converted_code = self._convert_tag_type(code, selector, 'Link', 'a', {'to': 'href'})
                if converted_code:
                    code = converted_code
                    tag_was_converted = True
                    actual_attr_name = 'href'  # Update to reflect the converted attribute
                    # Re-find the tag after conversion to update tag_content
                    tag_match = self._find_element_tag(code, selector)
                    if tag_match:
                        tag_start, tag_end, tag_content = tag_match
                    logger.info(f"[DIRECT EDIT] Successfully converted <Link> to <a>")
                else:
                    logger.warning(f"[DIRECT EDIT] Failed to convert <Link> to <a>, continuing with <Link> tag")

        # Note: After tag conversion, we still need to update the attribute value below
        # The conversion only changes the attribute NAME (href ↔ to), not the VALUE

        # First check if attribute is a simple prop expression like {propName}
        # This is common for link hrefs: <a href={link}> or <Link to={link}>
        # Check both the original attr_name and actual_attr_name
        simple_prop_match = (self._extract_simple_prop_expression(tag_content, actual_attr_name) or
                            self._extract_simple_prop_expression(tag_content, attr_name))
        if simple_prop_match:
            prop_name = simple_prop_match

            # Verify it's actually a component prop
            if self._is_component_prop(code, prop_name):
                logger.info(f"[DIRECT EDIT] Attribute {actual_attr_name} is a simple prop expression: {{{prop_name}}}")
                logger.info(f"[DIRECT EDIT] Returning prop edit metadata for parent component update")

                # Return metadata indicating prop edit is needed
                return {
                    'type': 'prop_edit',
                    'prop_name': prop_name,
                    'old_value': f'{{{prop_name}}}',
                    'new_value': new_value,
                    'requires_parent_update': True,
                    'element_selector': selector,
                    'attribute_name': actual_attr_name
                }

        # Check if this is an array item (selector contains index like "nav-item-0", "portfolio-image-0")
        # Handle for src, alt, href, to, target, rel attributes
        if attr_name in ['src', 'alt', 'href', 'to', 'target', 'rel'] or actual_attr_name in ['src', 'alt', 'href', 'to', 'target', 'rel']:
            array_index = self._extract_array_index_from_selector(selector)

            if array_index is not None:
                logger.info(f"[DIRECT EDIT] Detected array item at index {array_index} for attribute {actual_attr_name}")

                # Extract which property is actually used in the attribute expression
                # Try both actual_attr_name and attr_name
                attr_expr = (self._extract_attribute_expression(tag_content, actual_attr_name) or
                            self._extract_attribute_expression(tag_content, attr_name))

                if attr_expr:
                    object_name, property_path = attr_expr
                    logger.info(f"[DIRECT EDIT] Attempting to update array item: object='{object_name}', property='{property_path}'")

                    # Try to update the array item property
                    updated_code = self._update_array_item_attribute(
                        code=code,
                        object_name=object_name,
                        array_index=array_index,
                        property_path=property_path,
                        new_value=new_value,
                        files=files,
                        component_tracker=component_tracker
                    )

                    # Check if result is metadata dict (prop-based array)
                    if isinstance(updated_code, dict):
                        logger.info(f"[DIRECT EDIT] Array prop edit detected, returning metadata")
                        return updated_code

                    if updated_code and updated_code != code:
                        logger.info(f"[DIRECT EDIT] Successfully updated array item property '{property_path}' at index {array_index}")
                        return updated_code
                    else:
                        logger.warning(f"[DIRECT EDIT] Failed to update array item, falling back to direct attribute update")
                else:
                    logger.debug(f"[DIRECT EDIT] Could not extract attribute expression, falling back to direct update")

        # Fallback to direct attribute update
        # Check if attribute already exists (use actual_attr_name)
        attr_pattern = rf'{re.escape(actual_attr_name)}=["\'](.*?)["\']'
        attr_match = re.search(attr_pattern, tag_content)
        
        if attr_match:
            # Replace existing attribute
            old_attr = attr_match.group(0)
            new_attr = f'{actual_attr_name}="{new_value}"'
            new_tag_content = tag_content.replace(old_attr, new_attr, 1)
        else:
            # Attribute doesn't exist - add new attribute (insert before closing >)
            # But first, if we're switching from href to to (or vice versa), remove the old one
            if attr_name == 'href' and actual_attr_name != attr_name:
                # We're changing from href to to or vice versa
                # Try to find and remove the old attribute
                old_attr_pattern = rf'{re.escape(attr_name)}=["\'](.*?)["\']'
                old_attr_match = re.search(old_attr_pattern, tag_content)
                if old_attr_match:
                    # Remove old attribute
                    logger.info(f"[DIRECT EDIT] Removing old attribute '{attr_name}' before adding '{actual_attr_name}'")
                    tag_content = tag_content.replace(old_attr_match.group(0), '', 1)
                    # Clean up extra whitespace
                    tag_content = re.sub(r'\s+', ' ', tag_content)

            new_attr = f'{actual_attr_name}="{new_value}"'
            if tag_content.endswith('/>'):
                # Self-closing tag
                new_tag_content = tag_content[:-2] + f' {new_attr} />'
            else:
                # Regular tag
                new_tag_content = tag_content[:-1] + f' {new_attr}>'

        # Replace in code
        new_code = code[:tag_start] + new_tag_content + code[tag_end:]

        return new_code
    
    def _edit_inline_style(self, code: str, selector: str, style_property: str, value: str) -> Optional[str]:
        """
        Edit an inline style property in the style attribute.
        Used for custom hex colors and other inline styles.
        
        When applying a custom color via inline style, this method also removes
        conflicting Tailwind color classes from the className to avoid redundancy.
        
        Args:
            code: Component code
            selector: Element selector (data-element value)
            style_property: CSS property name (e.g., 'color', 'backgroundColor')
            value: CSS value (e.g., '#FF5733')
        """
        logger.info(f"[DIRECT EDIT] Setting inline style {style_property} to: '{value}' for selector: '{selector}'")
        logger.info(f"[DIRECT EDIT] Code length: {len(code)} chars")
        
        tag_match = self._find_element_tag(code, selector)
        if not tag_match:
            logger.error(f"[DIRECT EDIT] _find_element_tag returned None for selector: '{selector}'")
            # Log first 500 chars of code to help debug
            logger.error(f"[DIRECT EDIT] Code snippet (first 500 chars):\n{code[:500]}")
            return None
        
        tag_start, tag_end, tag_content = tag_match
        
        logger.info(f"[DIRECT EDIT] Tag content (first 200 chars): {tag_content[:200]}")
        
        # Find existing style attribute
        # React inline styles use objects: style={{ property: 'value' }}
        style_pattern = r'style=\{\{([^}]*)\}\}'
        style_match = re.search(style_pattern, tag_content)
        
        logger.info(f"[DIRECT EDIT] Style pattern match: {bool(style_match)}")
        
        if style_match:
            # Has existing style attribute
            old_style = style_match.group(1).strip()
            
            # Parse existing styles (React object notation)
            style_dict = {}
            if old_style:
                # Split by commas that aren't inside quotes
                parts = []
                current = []
                in_quotes = False
                for char in old_style:
                    if char in ['"', "'"]:
                        in_quotes = not in_quotes
                    if char == ',' and not in_quotes:
                        parts.append(''.join(current))
                        current = []
                    else:
                        current.append(char)
                if current:
                    parts.append(''.join(current))
                
                for part in parts:
                    part = part.strip()
                    if ':' in part:
                        prop, val = part.split(':', 1)
                        prop = prop.strip()
                        val = val.strip().strip(',')
                        style_dict[prop] = val
            
            # Update or add the property (use camelCase for React)
            style_dict[style_property] = f"'{value}'"
            
            # Rebuild style object
            style_entries = [f"{k}: {v}" for k, v in style_dict.items()]
            new_style = '{{ ' + ', '.join(style_entries) + ' }}'
            
            # Replace in tag
            old_attr = style_match.group(0)
            new_attr = f'style={new_style}'
            new_tag_content = tag_content.replace(old_attr, new_attr, 1)
            logger.info(f"[DIRECT EDIT] Updated existing style attribute")
            logger.info(f"[DIRECT EDIT] Old attr: {old_attr}")
            logger.info(f"[DIRECT EDIT] New attr: {new_attr}")
        else:
            # No style attribute, add one (React object notation with camelCase)
            new_attr = f"style={{{{ {style_property}: '{value}' }}}}"
            logger.info(f"[DIRECT EDIT] Adding new style attribute: {new_attr}")
            if tag_content.endswith('/>'):
                new_tag_content = tag_content[:-2] + f' {new_attr} />'
            else:
                new_tag_content = tag_content[:-1] + f' {new_attr}>'
        
        # Remove conflicting Tailwind color classes from className
        # Map style properties to their Tailwind class prefixes
        property_to_tailwind_prefix = {
            'color': 'text',
            'backgroundColor': 'bg',
            'borderColor': 'border'
        }
        
        if style_property in property_to_tailwind_prefix:
            prefix = property_to_tailwind_prefix[style_property]
            logger.info(f"[DIRECT EDIT] Removing conflicting {prefix}-* color classes from className")
            new_tag_content = self._remove_conflicting_color_classes(new_tag_content, prefix)
        
        # Replace in code
        new_code = code[:tag_start] + new_tag_content + code[tag_end:]
        
        logger.info(f"[DIRECT EDIT] Code changed: {new_code != code}")
        logger.info(f"[DIRECT EDIT] New tag content (first 200 chars): {new_tag_content[:200]}")
        
        return new_code
    
    def _remove_conflicting_color_classes(self, tag_content: str, prefix: str) -> str:
        """
        Remove Tailwind color classes with the given prefix from className attribute.
        
        This removes classes like:
        - text-{color}-{shade} (e.g., text-slate-50, text-blue-600)
        - text-white, text-black, text-transparent
        - bg-{color}-{shade}, bg-white, bg-black, bg-transparent
        - border-{color}-{shade}, border-white, border-black, border-transparent
        
        Args:
            tag_content: The tag content containing className
            prefix: The Tailwind prefix ('text', 'bg', 'border')
            
        Returns:
            Updated tag content with color classes removed
        """
        # Find className attribute
        class_pattern = r'className=(?:["\'](.*?)["\']|\{["\'](.*?)["\']\})'
        class_match = re.search(class_pattern, tag_content)
        
        if not class_match:
            # No className attribute found
            return tag_content
        
        # Get current className value
        old_classes = class_match.group(1) or class_match.group(2) or ''
        
        # Split into individual classes
        classes = old_classes.split()
        
        # Filter out color classes with the given prefix
        # Matches: text-{color}-{shade}, text-white, text-black, text-transparent, etc.
        color_class_patterns = [
            rf'^{prefix}-\w+-\d+$',  # e.g., text-slate-50, bg-blue-600
            rf'^{prefix}-white$',     # e.g., text-white
            rf'^{prefix}-black$',     # e.g., text-black
            rf'^{prefix}-transparent$', # e.g., bg-transparent
            rf'^{prefix}-current$',   # e.g., text-current
        ]
        
        filtered_classes = []
        removed_classes = []
        
        for cls in classes:
            should_remove = False
            for pattern in color_class_patterns:
                if re.match(pattern, cls):
                    should_remove = True
                    removed_classes.append(cls)
                    break
            
            if not should_remove:
                filtered_classes.append(cls)
        
        if removed_classes:
            logger.info(f"[DIRECT EDIT] Removed conflicting classes: {', '.join(removed_classes)}")
        
        # Build new className string
        new_classes = ' '.join(filtered_classes)
        
        # Replace className in tag
        old_class_attr = class_match.group(0)
        new_class_attr = f'className="{new_classes}"'
        new_tag_content = tag_content.replace(old_class_attr, new_class_attr, 1)
        
        return new_tag_content
    
    def _remove_inline_style_property(self, tag_content: str, style_property: str) -> str:
        """
        Remove a specific property from inline style attribute.
        
        For example, removes 'color' from style={{ color: '#FFFFFF', fontSize: '20px' }}
        to become style={{ fontSize: '20px' }}
        
        If the style object becomes empty after removal, removes the entire style attribute.
        
        Args:
            tag_content: The tag content containing style attribute
            style_property: The CSS property to remove (e.g., 'color', 'backgroundColor')
            
        Returns:
            Updated tag content with the style property removed
        """
        # Find existing style attribute
        style_pattern = r'style=\{\{([^}]*)\}\}'
        style_match = re.search(style_pattern, tag_content)
        
        if not style_match:
            # No style attribute found
            return tag_content
        
        old_style = style_match.group(1).strip()
        
        # Parse existing styles (React object notation)
        style_dict = {}
        if old_style:
            # Split by commas that aren't inside quotes
            parts = []
            current = []
            in_quotes = False
            for char in old_style:
                if char in ['"', "'"]:
                    in_quotes = not in_quotes
                if char == ',' and not in_quotes:
                    parts.append(''.join(current))
                    current = []
                else:
                    current.append(char)
            if current:
                parts.append(''.join(current))
            
            for part in parts:
                part = part.strip()
                if ':' in part:
                    prop, val = part.split(':', 1)
                    prop = prop.strip()
                    val = val.strip().strip(',')
                    style_dict[prop] = val
        
        # Remove the specified property
        if style_property in style_dict:
            del style_dict[style_property]
            logger.info(f"[DIRECT EDIT] Removed inline style property: {style_property}")
        else:
            # Property not found, return unchanged
            return tag_content
        
        # If no styles remain, remove the entire style attribute
        if not style_dict:
            logger.info(f"[DIRECT EDIT] Style object empty, removing entire style attribute")
            old_attr = style_match.group(0)
            # Remove the style attribute and any extra whitespace
            new_tag_content = tag_content.replace(old_attr, '', 1)
            # Clean up double spaces
            new_tag_content = re.sub(r'\s+', ' ', new_tag_content)
            return new_tag_content
        
        # Rebuild style object with remaining properties
        style_entries = [f"{k}: {v}" for k, v in style_dict.items()]
        new_style = '{{ ' + ', '.join(style_entries) + ' }}'
        
        # Replace in tag
        old_attr = style_match.group(0)
        new_attr = f'style={new_style}'
        new_tag_content = tag_content.replace(old_attr, new_attr, 1)
        
        logger.info(f"[DIRECT EDIT] Updated style attribute")
        logger.info(f"[DIRECT EDIT] Old: {old_attr}")
        logger.info(f"[DIRECT EDIT] New: {new_attr}")
        
        return new_tag_content
    
    def _edit_tailwind_class(self, code: str, selector: str, property_name: str, new_class: str) -> Optional[str]:
        """
        Edit a Tailwind CSS class in the className attribute.
        
        When applying a Tailwind color class, also removes any conflicting inline styles
        to ensure clean, consistent styling (no mixing of Tailwind and inline styles).
        
        Args:
            code: Component code
            selector: Element selector (data-element value)
            property_name: Property name (e.g., 'color', 'fontSize', 'padding')
            new_class: New Tailwind class to apply
        """
        logger.info(f"[DIRECT EDIT] Changing Tailwind class for {property_name} to: '{new_class}' for selector: '{selector}'")
        logger.info(f"[DIRECT EDIT] Code length: {len(code)} chars")
        
        tag_match = self._find_element_tag(code, selector)
        if not tag_match:
            logger.error(f"[DIRECT EDIT] _find_element_tag returned None for selector: '{selector}'")
            # Log first 500 chars of code to help debug
            logger.error(f"[DIRECT EDIT] Code snippet (first 500 chars):\n{code[:500]}")
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
        
        # Remove conflicting inline styles for color properties
        # Map property names to their inline style equivalents
        property_to_style_name = {
            'color': 'color',
            'backgroundColor': 'backgroundColor',
            'borderColor': 'borderColor'
        }
        
        if property_name in property_to_style_name:
            style_name = property_to_style_name[property_name]
            logger.info(f"[DIRECT EDIT] Removing conflicting inline style '{style_name}' from style attribute")
            new_tag_content = self._remove_inline_style_property(new_tag_content, style_name)
        
        # Replace in code
        new_code = code[:tag_start] + new_tag_content + code[tag_end:]
        
        return new_code


# Create singleton instance
direct_code_editor = DirectCodeEditor()

