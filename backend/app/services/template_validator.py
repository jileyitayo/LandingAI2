"""
Template Validator Service
Validates generated template structures and content schemas.
"""

from typing import Dict, Any, Tuple, Optional, List
from app.services.components_library import component_library, ComponentType


def validate_template_structure(template_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate the overall template structure.
    
    Args:
        template_data: Template data dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required top-level fields
    required_fields = ["sections", "style_config", "content_schema"]
    for field in required_fields:
        if field not in template_data:
            return False, f"Missing required field: {field}"
    
    # Validate sections
    is_valid, error = validate_sections_config(template_data["sections"])
    if not is_valid:
        return False, error
    
    # Validate style config
    is_valid, error = validate_style_config(template_data["style_config"])
    if not is_valid:
        return False, error
    
    # Validate content schema
    is_valid, error = validate_content_schema(template_data["content_schema"])
    if not is_valid:
        return False, error
    
    # Cross-validate: ensure content schema includes all required bindings
    is_valid, error = validate_content_bindings(
        template_data["sections"],
        template_data["content_schema"]
    )
    if not is_valid:
        return False, error
    
    return True, None


def validate_sections_config(sections: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Validate sections configuration.
    
    Args:
        sections: List of section configurations
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(sections, list):
        return False, "sections must be a list"
    
    if len(sections) == 0:
        return False, "sections cannot be empty"
    
    if len(sections) > 12:
        return False, "Too many sections (maximum 12)"
    
    # Required sections
    component_types = [s.get("component_type") for s in sections]
    required_types = ["header", "hero", "footer"]
    
    for required_type in required_types:
        if required_type not in component_types:
            return False, f"Missing required section: {required_type}"
    
    # Validate each section
    for i, section in enumerate(sections):
        # Check required fields
        if "component_type" not in section:
            return False, f"Section {i}: missing component_type"
        
        if "variation" not in section:
            return False, f"Section {i}: missing variation"
        
        # Validate component_type exists
        component_type = section["component_type"]
        try:
            ComponentType(component_type)
        except ValueError:
            return False, f"Section {i}: invalid component_type '{component_type}'"
        
        # Validate variation exists
        variation = section["variation"]
        component = component_library.get_component(
            ComponentType(component_type),
            variation
        )
        if not component:
            return False, f"Section {i}: variation '{variation}' not found for component '{component_type}'"
        
        # Validate order if present
        if "order" in section:
            order = section["order"]
            if not isinstance(order, int) or order < 0:
                return False, f"Section {i}: order must be a non-negative integer"
        
        # Validate config if present
        if "config" in section:
            if not isinstance(section["config"], dict):
                return False, f"Section {i}: config must be a dictionary"
    
    # Check for duplicate orders
    orders = [s.get("order", i) for i, s in enumerate(sections)]
    if len(orders) != len(set(orders)):
        return False, "Duplicate section orders found"
    
    return True, None


def validate_style_config(style_config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate style configuration.
    
    Args:
        style_config: Style configuration dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(style_config, dict):
        return False, "style_config must be a dictionary"
    
    # Validate colors
    if "colors" in style_config:
        colors = style_config["colors"]
        if not isinstance(colors, dict):
            return False, "style_config.colors must be a dictionary"
        
        # Check for required colors
        required_colors = ["primary", "text", "background"]
        for color_name in required_colors:
            if color_name not in colors:
                return False, f"Missing required color: {color_name}"
            
            # Validate hex color format
            color_value = colors[color_name]
            if not isinstance(color_value, str):
                return False, f"Color {color_name} must be a string"
            
            if not _is_valid_hex_color(color_value) and not _is_valid_color_name(color_value):
                return False, f"Invalid color format for {color_name}: {color_value}"
    
    # Validate typography
    if "typography" in style_config:
        typography = style_config["typography"]
        if not isinstance(typography, dict):
            return False, "style_config.typography must be a dictionary"
    
    # Validate spacing
    if "spacing" in style_config:
        spacing = style_config["spacing"]
        if not isinstance(spacing, dict):
            return False, "style_config.spacing must be a dictionary"
    
    return True, None


def validate_content_schema(content_schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate content schema.
    
    Args:
        content_schema: Content schema dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(content_schema, dict):
        return False, "content_schema must be a dictionary"
    
    if len(content_schema) == 0:
        return False, "content_schema cannot be empty"
    
    # Valid content binding types
    valid_types = ["text", "email", "phone", "url", "image", "video", "array", "color"]
    
    # Validate each content field
    for field_name, field_config in content_schema.items():
        if not isinstance(field_config, dict):
            return False, f"Content field '{field_name}' config must be a dictionary"
        
        # Check type
        if "type" not in field_config:
            return False, f"Content field '{field_name}' missing type"
        
        field_type = field_config["type"]
        if field_type not in valid_types:
            return False, f"Content field '{field_name}' has invalid type: {field_type}"
        
        # Validate array type
        if field_type == "array":
            if "itemSchema" in field_config:
                item_schema = field_config["itemSchema"]
                if not isinstance(item_schema, dict):
                    return False, f"Content field '{field_name}' itemSchema must be a dictionary"
    
    return True, None


def validate_content_bindings(
    sections: List[Dict[str, Any]],
    content_schema: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Validate that content schema includes all required bindings from sections.
    
    Args:
        sections: List of section configurations
        content_schema: Content schema dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_bindings = set()
    
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
                # If binding is required, add to required set
                if isinstance(binding_config, dict) and binding_config.get("required", False):
                    required_bindings.add(binding_name)
    
    # Check that all required bindings are in content schema
    missing_bindings = required_bindings - set(content_schema.keys())
    if missing_bindings:
        return False, f"Missing required content bindings: {', '.join(missing_bindings)}"
    
    return True, None


def _is_valid_hex_color(color: str) -> bool:
    """Check if a string is a valid hex color"""
    import re
    pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, color))


def _is_valid_color_name(color: str) -> bool:
    """Check if a string is a valid CSS color name"""
    # Basic CSS color names (could be extended)
    valid_colors = {
        'white', 'black', 'red', 'green', 'blue', 'yellow', 'purple', 'orange',
        'pink', 'gray', 'grey', 'cyan', 'magenta', 'lime', 'indigo', 'teal',
        'navy', 'maroon', 'olive', 'aqua', 'silver', 'fuchsia'
    }
    return color.lower() in valid_colors or color.startswith('rgb') or color.startswith('hsl')

