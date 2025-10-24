"""
Template Renderer Service
Renders website templates by merging template structure with generated content.
"""

from typing import Dict, Any, List, Optional
import json
import re
import logging
from app.services.components_library import component_library, ComponentType

logger = logging.getLogger(__name__)


class TemplateRenderError(Exception):
    """Custom exception for template rendering errors"""
    pass


class TemplateRenderer:
    """Main template renderer class"""
    
    def __init__(self):
        """Initialize the template renderer"""
        pass
    
    # TODO: RENDER with just template and content, no components library
    def render_template_with_content(
        self,
        template: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Render a complete website by merging template with content.
        """
        return None
    

    def render_template(
        self,
        template: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Render a complete website by merging template with content.
        
        Args:
            template: Template structure from database (sections_config, style_config, etc.)
            content: Generated content matching content_schema
        
        Returns:
            Dictionary containing rendered HTML, CSS, and JS
        
        Raises:
            TemplateRenderError: If rendering fails
        """
        try:
            logger.info("[RENDER 1/7] Starting template rendering")
            
            # Extract template parts
            sections_config = template.get("sections_config", {})
            style_config = template.get("style_config", {})
            base_css = template.get("base_css", "")
            base_js = template.get("base_js", "")
            
            sections = sections_config
            logger.info(f"Template has {len(sections)} sections")
            
            # Sort sections by order
            logger.info("[RENDER 2/7] Sorting sections by order")
            sorted_sections = sorted(sections, key=lambda s: s.get("order", 0))
            
            # Render each section
            logger.info("[RENDER 3/7] Rendering individual sections")
            rendered_sections = []
            section_css_parts = []
            section_js_parts = []
            
            for idx, section in enumerate(sorted_sections):
                logger.info(f"  Rendering section {idx + 1}/{len(sorted_sections)}: {section['component_type']}")
                
                rendered = self._render_section(section, content, style_config)
                rendered_sections.append(rendered["html"])
                
                if rendered.get("css"):
                    section_css_parts.append(rendered["css"])
                if rendered.get("js"):
                    section_js_parts.append(rendered["js"])
            
            # Build complete HTML structure
            logger.info("[RENDER 4/7] Building complete HTML structure")
            html = self._build_html_structure(
                rendered_sections,
                style_config,
                template.get("name", "Generated Website")
            )
            
            # Build complete CSS
            logger.info("[RENDER 5/7] Building complete CSS")
            css = self._build_complete_css(
                base_css,
                section_css_parts,
                style_config
            )
            
            # Build complete JS
            logger.info("[RENDER 6/7] Building complete JavaScript")
            js = self._build_complete_js(
                base_js,
                section_js_parts,
                content
            )
            
            # Apply optimizations
            logger.info("[RENDER 7/7] Applying optimizations")
            html = self._optimize_html(html)
            css = self._minify_css(css)
            js = self._minify_js(js)
            
            logger.info("✓ Template rendering completed successfully")
            logger.info(f"  HTML: {len(html)} characters")
            logger.info(f"  CSS: {len(css)} characters")
            logger.info(f"  JS: {len(js)} characters")
            
            return {
                "html_content": html,
                "css_content": css,
                "js_content": js,
                "metadata": {
                    "sections_count": len(sections),
                    "has_custom_js": bool(js.strip()),
                    "mobile_optimized": True
                }
            }
            
        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}")
            raise TemplateRenderError(f"Template rendering failed: {str(e)}")
    
    def _render_section(
        self,
        section: Dict[str, Any],
        content: Dict[str, Any],
        style_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render a single section with content"""
        component_type = section.get("component_type")
        variation = section.get("variation")
        config = section.get("config", {})
        
        # Get component from library
        try:
            component = component_library.get_component(
                ComponentType(component_type),
                variation
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Component {component_type}:{variation} not found, using fallback")
            component = self._create_fallback_component(component_type)
        
        if not component:
            logger.warning(f"Using fallback for {component_type}:{variation}")
            component = self._create_fallback_component(component_type)
        
        # Get component HTML and CSS
        html_template = component.get("html", "")
        css_template = component.get("css", "")
        
        # Replace content placeholders
        html = self._replace_placeholders(html_template, content, config)
        css = self._replace_style_variables(css_template, style_config)
        
        return {
            "html": html,
            "css": css,
            "js": ""  # Component-specific JS could be added here
        }
    
    def _replace_placeholders(
        self,
        template: str,
        content: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """Replace {{placeholder}} with actual content"""
        result = template
        
        # Replace simple placeholders
        for key, value in content.items():
            placeholder = f"{{{{{key}}}}}"
            
            # Handle different content types
            if isinstance(value, str):
                result = result.replace(placeholder, self._escape_html(value))
            elif isinstance(value, (int, float)):
                result = result.replace(placeholder, str(value))
            elif isinstance(value, list):
                # For arrays, we need more complex handling
                result = self._replace_array_placeholder(result, key, value)
            elif isinstance(value, dict):
                # Handle nested objects
                for sub_key, sub_value in value.items():
                    nested_placeholder = f"{{{{{key}.{sub_key}}}}}"
                    if isinstance(sub_value, str):
                        result = result.replace(nested_placeholder, self._escape_html(sub_value))
        
        # Replace config placeholders
        for key, value in config.items():
            placeholder = f"{{{{config.{key}}}}}"
            if isinstance(value, str):
                result = result.replace(placeholder, value)
        
        # Remove any remaining placeholders (replace with empty string)
        result = re.sub(r'\{\{[^}]+\}\}', '', result)
        
        return result
    
    def _replace_array_placeholder(
        self,
        template: str,
        key: str,
        items: List[Any]
    ) -> str:
        """Replace array placeholders with repeated elements"""
        # Look for array loop patterns like {{#services}}...{{/services}}
        loop_pattern = f"{{{{#{key}}}}}(.*?){{{{/{key}}}}}"
        match = re.search(loop_pattern, template, re.DOTALL)
        
        if match:
            loop_template = match.group(1)
            rendered_items = []
            
            for item in items:
                rendered_item = loop_template
                if isinstance(item, dict):
                    for item_key, item_value in item.items():
                        item_placeholder = f"{{{{{item_key}}}}}"
                        if isinstance(item_value, str):
                            rendered_item = rendered_item.replace(
                                item_placeholder,
                                self._escape_html(item_value)
                            )
                elif isinstance(item, str):
                    rendered_item = rendered_item.replace("{{item}}", self._escape_html(item))
                
                rendered_items.append(rendered_item)
            
            # Replace the loop with rendered items
            result = template.replace(match.group(0), "".join(rendered_items))
            return result
        
        return template
    
    def _replace_style_variables(
        self,
        css: str,
        style_config: Dict[str, Any]
    ) -> str:
        """Replace CSS variables with actual style values"""
        result = css
        
        # Replace color variables
        colors = style_config.get("colors", {})
        for color_name, color_value in colors.items():
            result = result.replace(f"var(--color-{color_name})", color_value)
            result = result.replace(f"{{{{colors.{color_name}}}}}", color_value)
        
        # Replace typography variables
        typography = style_config.get("typography", {})
        for typo_name, typo_value in typography.items():
            result = result.replace(f"var(--{typo_name})", typo_value)
            result = result.replace(f"{{{{typography.{typo_name}}}}}", typo_value)
        
        # Replace spacing variables
        spacing = style_config.get("spacing", {})
        for spacing_name, spacing_value in spacing.items():
            result = result.replace(f"var(--spacing-{spacing_name})", spacing_value)
            result = result.replace(f"{{{{spacing.{spacing_name}}}}}", spacing_value)
        
        return result
    
    def _build_html_structure(
        self,
        rendered_sections: List[str],
        style_config: Dict[str, Any],
        title: str
    ) -> str:
        """Build complete HTML document structure"""
        
        # Extract style variables for CSS
        colors = style_config.get("colors", {})
        typography = style_config.get("typography", {})
        
        # Build meta tags for mobile optimization
        meta_tags = """
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
"""
        
        # Build CSS variables
        css_vars = self._build_css_variables(style_config)
        
        # Build complete HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{meta_tags}
    <title>{self._escape_html(title)}</title>
    
    <!-- CSS Variables -->
    <style>
        :root {{
{css_vars}
        }}
    </style>
    
    <!-- Link to external CSS -->
    <link rel="stylesheet" href="styles.css">
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
</head>
<body>
{chr(10).join(rendered_sections)}

    <!-- JavaScript -->
    <script src="script.js"></script>
</body>
</html>"""
        
        return html
    
    def _build_css_variables(self, style_config: Dict[str, Any]) -> str:
        """Build CSS custom properties from style config"""
        variables = []
        
        # Colors
        colors = style_config.get("colors", {})
        for key, value in colors.items():
            variables.append(f"            --color-{key}: {value};")
        
        # Typography
        typography = style_config.get("typography", {})
        for key, value in typography.items():
            var_key = re.sub(r'(?<!^)(?=[A-Z])', '-', key).lower()
            variables.append(f"            --{var_key}: {value};")
        
        # Spacing
        spacing = style_config.get("spacing", {})
        for key, value in spacing.items():
            variables.append(f"            --spacing-{key}: {value};")
        
        return "\n".join(variables)
    
    def _build_complete_css(
        self,
        base_css: str,
        section_css_parts: List[str],
        style_config: Dict[str, Any]
    ) -> str:
        """Build complete CSS file"""
        
        # Base reset and utilities
        reset_css = """
/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    font-size: 16px;
    -webkit-text-size-adjust: 100%;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

body {
    font-family: var(--font-family, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif);
    font-size: var(--font-size, 16px);
    line-height: var(--line-height, 1.6);
    color: var(--color-text, #333);
    background-color: var(--color-background, #fff);
}

img {
    max-width: 100%;
    height: auto;
    display: block;
}

a {
    color: var(--color-primary, #007bff);
    text-decoration: none;
    transition: color 0.3s ease;
}

a:hover {
    color: var(--color-secondary, #0056b3);
}

/* Container */
.container {
    width: 100%;
    max-width: var(--spacing-containerMaxWidth, 1200px);
    margin: 0 auto;
    padding: 0 1rem;
}

/* Mobile Optimization */
@media (max-width: 768px) {
    html {
        font-size: 14px;
    }
    
    .container {
        padding: 0 0.75rem;
    }
}

/* WhatsApp Button (African Market Optimization) */
.whatsapp-float {
    position: fixed;
    width: 60px;
    height: 60px;
    bottom: 40px;
    right: 40px;
    background-color: #25d366;
    color: #FFF;
    border-radius: 50px;
    text-align: center;
    font-size: 30px;
    box-shadow: 2px 2px 3px #999;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}

.whatsapp-float:hover {
    background-color: #128c7e;
    transform: scale(1.1);
}

@media (max-width: 768px) {
    .whatsapp-float {
        width: 50px;
        height: 50px;
        bottom: 20px;
        right: 20px;
    }
}
"""
        
        # Combine all CSS parts
        css_parts = [reset_css]
        
        if base_css:
            css_parts.append("\n/* Base Template CSS */")
            css_parts.append(base_css)
        
        if section_css_parts:
            css_parts.append("\n/* Component Styles */")
            css_parts.extend(section_css_parts)
        
        return "\n\n".join(css_parts)
    
    def _build_complete_js(
        self,
        base_js: str,
        section_js_parts: List[str],
        content: Dict[str, Any]
    ) -> str:
        """Build complete JavaScript file"""
        
        # Base JS utilities
        base_utilities = """
// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu functionality
    const mobileMenuBtn = document.querySelector('[data-mobile-menu-toggle]');
    const mobileMenu = document.querySelector('[data-mobile-menu]');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // Lazy load images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
});
"""
        
        # Combine all JS parts
        js_parts = [base_utilities]
        
        if base_js:
            js_parts.append("\n// Base Template JavaScript")
            js_parts.append(base_js)
        
        if section_js_parts:
            js_parts.append("\n// Component Scripts")
            js_parts.extend(section_js_parts)
        
        return "\n\n".join(js_parts)
    
    def _create_fallback_component(self, component_type: str) -> Dict[str, str]:
        """Create a fallback component when component is not found"""
        return {
            "html": f'<div class="fallback-section" data-type="{component_type}"><p>Section: {component_type}</p></div>',
            "css": ".fallback-section { padding: 2rem; background: #f5f5f5; text-align: center; }",
            "config": {},
            "content_bindings": {}
        }
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not isinstance(text, str):
            return str(text)
        
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))
    
    def _optimize_html(self, html: str) -> str:
        """Optimize HTML for performance"""
        # Remove excessive whitespace
        html = re.sub(r'\n\s*\n', '\n', html)
        html = re.sub(r'  +', ' ', html)
        return html.strip()
    
    def _minify_css(self, css: str) -> str:
        """Minify CSS (basic minification)"""
        # Remove comments
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
        # Remove excessive whitespace
        css = re.sub(r'\s+', ' ', css)
        css = re.sub(r'\s*([{}:;,])\s*', r'\1', css)
        return css.strip()
    
    def _minify_js(self, js: str) -> str:
        """Minify JavaScript (basic minification)"""
        # Remove single-line comments
        js = re.sub(r'//.*?$', '', js, flags=re.MULTILINE)
        # Remove multi-line comments
        js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
        # Remove excessive whitespace (basic)
        js = re.sub(r'\n\s*\n', '\n', js)
        return js.strip()


# Export singleton instance
template_renderer = TemplateRenderer()

