"""
Code Validator Service
Validates generated React/TypeScript code for common errors.
"""

import re
import logging
from typing import Dict, List, Tuple, Set, Any
from app.services.validators.icon_validator import is_valid_icon, validate_and_fix_icon

logger = logging.getLogger(__name__)

# Import for type hints
try:
    from app.services.react_models import WebsiteStructure
except ImportError:
    WebsiteStructure = Any  # Fallback if import fails


class CodeValidationError:
    """Represents a validation error"""
    def __init__(self, file_path: str, error_type: str, message: str, severity: str = "error"):
        self.file_path = file_path
        self.error_type = error_type
        self.message = message
        self.severity = severity  # "error" or "warning"
    
    def __repr__(self):
        return f"[{self.severity.upper()}] {self.file_path}: {self.error_type} - {self.message}"


class CodeValidator:
    """Validates generated React/TypeScript code"""
    
    def __init__(self):
        self.errors: List[CodeValidationError] = []
        self.warnings: List[CodeValidationError] = []
    
    def validate_all_files(self, files: Dict[str, str]) -> Tuple[List[CodeValidationError], List[CodeValidationError]]:
        """
        Validate all generated files
        
        Args:
            files: Dictionary mapping file paths to file contents
            
        Returns:
            Tuple of (errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        logger.info(f"[CODE VALIDATOR] Validating {len(files)} files...")
        
        # Validate each file individually
        for file_path, content in files.items():
            if file_path.endswith('.tsx') or file_path.endswith('.ts'):
                self._validate_typescript_file(file_path, content)
        
        # Cross-file validation
        self._validate_imports_exports(files)
        self._validate_no_duplicates(files)
        self._validate_component_props(files)
        self._validate_unused_imports(files)
        self._validate_undefined_variables(files)
        
        logger.info(f"[CODE VALIDATOR] Found {len(self.errors)} errors and {len(self.warnings)} warnings")
        
        return self.errors, self.warnings

    def _validate_and_inject_data_attributes(self, file_path: str, content: str) -> tuple[str, bool]:
        """
        Validate that component has data-component and data-file attributes on root element.
        If missing, attempt to inject them.

        Args:
            file_path: Path to the component file (e.g., "src/components/Hero.tsx")
            content: Component file content

        Returns:
            Tuple of (modified_content, was_modified)
        """
        # Only process component files, not pages
        if not file_path.startswith("src/components/") or "/ui/" in file_path:
            return content, False

        # Extract component name from file path
        component_name = file_path.split("/")[-1].replace(".tsx", "").replace(".jsx", "")

        # Check if data attributes already exist
        has_data_component = 'data-component=' in content
        has_data_file = 'data-file=' in content

        if has_data_component and has_data_file:
            logger.info(f"[VALIDATION] ✓ {file_path} already has data attributes")
            return content, False

        logger.warning(f"[VALIDATION] ⚠ {file_path} missing data attributes - attempting injection")

        # Find the root element (first JSX element in return statement)
        # Pattern: return ( ... <tagName ...> or return <tagName ...>
        # We want to inject into the first opening tag after 'return'

        # Pattern to find first JSX element after return
        # Matches: <section, <div, <header, etc. but not self-closing or closing tags
        pattern = r'(return\s*\(?[\s\n]*<)([a-zA-Z][a-zA-Z0-9]*)([\s\n]+|>)'

        def inject_attributes(match):
            before_tag = match.group(1)  # "return (<" or "return <"
            tag_name = match.group(2)     # "section", "div", etc.
            after_tag = match.group(3)    # space or ">"

            # Build the data attributes
            data_attrs = []
            if not has_data_component:
                data_attrs.append(f'data-component="{component_name}"')
            if not has_data_file:
                data_attrs.append(f'data-file="{file_path}"')

            # If after_tag is just ">", we need to insert a space
            if after_tag == ">":
                return f'{before_tag}{tag_name} {" ".join(data_attrs)}>'
            else:
                # There's already whitespace
                return f'{before_tag}{tag_name} {" ".join(data_attrs)}{after_tag}'

        modified_content = re.sub(pattern, inject_attributes, content, count=1)

        if modified_content != content:
            logger.info(f"[VALIDATION] ✓ Injected data attributes into {file_path}")
            return modified_content, True
        else:
            logger.warning(f"[VALIDATION] ⚠ Could not inject data attributes into {file_path} - pattern not found")
            return content, False
    
    def _validate_typescript_file(self, file_path: str, content: str):
        """Validate a single TypeScript/React file"""
        
        # Validate lucide-react icons
        self._validate_lucide_icons(file_path, content)
        
        # Validate exports
        self._validate_exports(file_path, content)
        
        # Validate basic TypeScript syntax
        self._validate_typescript_syntax(file_path, content)
    
    def _validate_lucide_icons(self, file_path: str, content: str):
        """Check that all lucide-react icons are valid"""
        
        # Find all lucide-react imports
        icon_import_pattern = r"import\s+\{([^}]+)\}\s+from\s+['\"]lucide-react['\"]"
        matches = re.finditer(icon_import_pattern, content)
        
        for match in matches:
            imported_icons = match.group(1)
            # Split by comma and clean up
            icons = [icon.strip() for icon in imported_icons.split(',') if icon.strip()]

            for icon in icons:
                if icon and not is_valid_icon(icon):
                    alternative, _ = validate_and_fix_icon(icon)
                    self.errors.append(CodeValidationError(
                        file_path,
                        "invalid_icon",
                        f"Invalid lucide-react icon '{icon}'. Use '{alternative}' instead."
                    ))
    
    def _validate_exports(self, file_path: str, content: str):
        """Check for duplicate or conflicting exports"""
        
        # Find all export statements
        export_patterns = [
            r"export\s+default\s+",
            r"export\s+function\s+(\w+)",
            r"export\s+const\s+(\w+)",
            r"export\s+\{([^}]+)\}",
        ]
        
        exports = []
        has_default = False
        
        for pattern in export_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if "default" in match.group(0):
                    if has_default:
                        self.errors.append(CodeValidationError(
                            file_path,
                            "duplicate_default_export",
                            "File has multiple default exports"
                        ))
                    has_default = True
                else:
                    # Extract export name
                    if match.lastindex and match.lastindex >= 1:
                        export_name = match.group(1).strip()
                        if export_name in exports:
                            self.errors.append(CodeValidationError(
                                file_path,
                                "duplicate_named_export",
                                f"Duplicate export '{export_name}'"
                            ))
                        exports.append(export_name)
        
        # Check for both default and named export of same component
        # Pattern: export function X() followed by export default X
        component_export_pattern = r"export\s+(?:function|const)\s+(\w+)"
        component_exports = re.findall(component_export_pattern, content)
        
        if has_default and component_exports:
            # Remove comments before checking for default exports to avoid false positives
            content_no_comments = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            content_no_comments = re.sub(r'/\*.*?\*/', '', content_no_comments, flags=re.DOTALL)
            
            # Check if default export matches a named export
            default_pattern = r"export\s+default\s+(\w+)"
            default_matches = re.findall(default_pattern, content_no_comments)
            for default_name in default_matches:
                if default_name in component_exports:
                    self.errors.append(CodeValidationError(
                        file_path,
                        "conflicting_exports",
                        f"Component '{default_name}' has both named and default export"
                    ))
    
    def _validate_typescript_syntax(self, file_path: str, content: str):
        """Basic TypeScript syntax validation"""
        
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            self.warnings.append(CodeValidationError(
                file_path,
                "unmatched_braces",
                f"Unmatched braces: {open_braces} open, {close_braces} close",
                "warning"
            ))
        
        # Check for unmatched parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            self.warnings.append(CodeValidationError(
                file_path,
                "unmatched_parens",
                f"Unmatched parentheses: {open_parens} open, {close_parens} close",
                "warning"
            ))
    
    def _validate_imports_exports(self, files: Dict[str, str]):
        """Validate that imports match exports across files"""
        
        # Build export map
        export_map: Dict[str, Dict[str, str]] = {}  # file_path -> {export_name: export_kind('default'|'named'|'type')}
        
        for file_path, content in files.items():
            if not (file_path.endswith('.tsx') or file_path.endswith('.ts')):
                continue
            
            export_map[file_path] = {}
            
            # Find default exports
            if re.search(r"export\s+default\s+", content):
                export_map[file_path]['default'] = 'default'
            
            # Find named exports
            named_exports = re.findall(r"export\s+(?:function|const)\s+(\w+)", content)
            for export_name in named_exports:
                export_map[file_path][export_name] = 'named'

            # Find type/interface exports
            type_exports = re.findall(r"export\s+type\s+(\w+)", content)
            for export_name in type_exports:
                export_map[file_path][export_name] = 'type'

            interface_exports = re.findall(r"export\s+interface\s+(\w+)", content)
            for export_name in interface_exports:
                export_map[file_path][export_name] = 'type'
            
            # Find re-exports
            reexport_pattern = r"export\s+\{([^}]+)\}"
            reexports = re.findall(reexport_pattern, content)
            for reexport in reexports:
                names = [n.strip() for n in reexport.split(',') if n.strip()]
                for name in names:
                    export_map[file_path][name] = 'named'
        
        # Validate imports
        for file_path, content in files.items():
            if not (file_path.endswith('.tsx') or file_path.endswith('.ts')):
                continue
            
            # Find all imports
            import_pattern = r"import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]@/([^'\"]+)['\"]"
            imports = re.finditer(import_pattern, content)
            
            for match in imports:
                named_imports = match.group(1)
                default_import = match.group(2)
                import_path = match.group(3)
                
                # Construct file path
                imported_file = f"src/{import_path}.tsx"
                if imported_file not in export_map:
                    imported_file = f"src/{import_path}.ts"
                
                if imported_file in export_map:
                    exports = export_map[imported_file]
                    
                    # Check named imports
                    if named_imports:
                        import_names = [n.strip() for n in named_imports.split(',') if n.strip()]
                        for raw_name in import_names:
                            # Normalize 'type' imports and aliases: e.g., "type Project as ProjectType"
                            # Capture optional 'type' prefix, base name, and optional alias
                            m = re.match(r"^(?:type\s+)?(\w+)(?:\s+as\s+\w+)?$", raw_name.strip())
                            if m:
                                base_name = m.group(1)
                                is_type_import = raw_name.strip().startswith('type ')
                            else:
                                base_name = raw_name.strip()
                                is_type_import = False

                            if base_name not in exports:
                                self.errors.append(CodeValidationError(
                                    file_path,
                                    "import_export_mismatch",
                                    f"Named import '{raw_name}' from '{import_path}' not found. Available exports: {list(exports.keys())}"
                                ))
                            else:
                                export_kind = exports[base_name]
                                # If importing as value but export is type-only
                                if not is_type_import and export_kind == 'type':
                                    self.errors.append(CodeValidationError(
                                        file_path,
                                        "import_export_mismatch",
                                        f"'{base_name}' is exported as a type but imported as a value"
                                    ))
                                # If importing as type but export is value-only
                                if is_type_import and export_kind != 'type':
                                    self.errors.append(CodeValidationError(
                                        file_path,
                                        "import_export_mismatch",
                                        f"'{base_name}' is not a type export in '{import_path}'"
                                    ))
                    
                    # Check default import
                    if default_import:
                        if 'default' not in exports:
                            self.errors.append(CodeValidationError(
                                file_path,
                                "import_export_mismatch",
                                f"Default import from '{import_path}' but no default export found"
                            ))
    
    def _validate_no_duplicates(self, files: Dict[str, str]):
        """Check for duplicate components"""
        
        component_names: Dict[str, List[str]] = {}  # component_name -> [file_paths]
        
        for file_path, content in files.items():
            if not file_path.endswith('.tsx'):
                continue
            
            # Extract component names (functions and consts)
            component_pattern = r"(?:export\s+)?(?:function|const)\s+([A-Z]\w+)"
            components = re.findall(component_pattern, content)
            
            for component_name in components:
                if component_name not in component_names:
                    component_names[component_name] = []
                component_names[component_name].append(file_path)
        
        # Report duplicates
        for component_name, file_paths in component_names.items():
            if len(file_paths) > 1:
                # Only warn if they're in similar directories (actual duplicates)
                if self._are_duplicate_components(file_paths):
                    self.warnings.append(CodeValidationError(
                        file_paths[0],
                        "duplicate_component",
                        f"Component '{component_name}' defined in multiple files: {file_paths}",
                        "warning"
                    ))
    
    def _are_duplicate_components(self, file_paths: List[str]) -> bool:
        """Check if component files are actual duplicates (not UI vs section)"""
        # UI components can have same name as section components
        has_ui = any('/ui/' in path for path in file_paths)
        has_non_ui = any('/ui/' not in path for path in file_paths)
        
        # If one is UI and another is not, they're not duplicates
        if has_ui and has_non_ui:
            return False
        
        return True
    
    def _validate_component_props(self, files: Dict[str, str]):
        """Validate that component props are used correctly in pages"""
        
        # Build a map of component prop interfaces
        component_props: Dict[str, Dict[str, bool]] = {}  # component_name -> {prop_name: is_optional}
        
        for file_path, content in files.items():
            if not file_path.startswith('src/components/') or file_path.startswith('src/components/ui/'):
                continue
            if not file_path.endswith('.tsx'):
                continue
            
            # Extract component name
            component_name = file_path.split('/')[-1].replace('.tsx', '')
            
            # Extract props from interface (e.g., FeaturesProps, TestimonialsProps)
            # Look for interface ComponentNameProps { prop1: type; prop2: type; }
            interface_pattern = rf"interface\s+{component_name}Props\s*{{\s*([^}}]+)}}"
            interface_match = re.search(interface_pattern, content, re.DOTALL)
            
            if interface_match:
                interface_body = interface_match.group(1)
                # Extract prop names with optional flag (handles optional props with ?)
                prop_pattern = r"(\w+)(\??):"
                props = {}
                for match in re.finditer(prop_pattern, interface_body):
                    prop_name = match.group(1)
                    is_optional = match.group(2) == '?'
                    props[prop_name] = is_optional
                component_props[component_name] = props
        
        # Now check pages to see if they use correct prop names
        for file_path, content in files.items():
            if not file_path.startswith('src/pages/'):
                continue
            if not file_path.endswith('.tsx'):
                continue
            
            # Find component usages: <ComponentName prop={value} /> or multi-line
            for component_name, expected_props in component_props.items():
                # Match both single-line and multi-line component usage
                # Pattern handles: <Component prop="value" /> and <Component\n  prop="value"\n/>
                component_usage_pattern = rf"<{component_name}[\s\n]+([^/>]*?)(?:/>|>)"
                matches = re.finditer(component_usage_pattern, content, re.DOTALL)
                
                for match in matches:
                    props_string = match.group(1)
                    # Extract prop names used
                    used_prop_pattern = r"(\w+)="
                    used_props = set(re.findall(used_prop_pattern, props_string))
                    
                    # Check if used props are valid
                    for used_prop in used_props:
                        if used_prop not in expected_props:
                            # Create a helpful error message
                            valid_props_str = ', '.join(sorted(expected_props.keys()))
                            self.errors.append(CodeValidationError(
                                file_path,
                                "prop_name_mismatch",
                                f"Component '{component_name}' called with invalid prop '{used_prop}'. "
                                f"Valid props: {valid_props_str}"
                            ))
                    
                    # Check for missing required props
                    required_props = {k for k, v in expected_props.items() if not v}
                    missing_required = required_props - used_props
                    
                    if missing_required:
                        self.warnings.append(CodeValidationError(
                            file_path,
                            "missing_required_prop",
                            f"Component '{component_name}' missing required props: {', '.join(missing_required)}",
                            "warning"
                        ))
    
    def _validate_unused_imports(self, files: Dict[str, str]):
        """Validate that all imports are actually used"""
        
        for file_path, content in files.items():
            if not (file_path.endswith('.tsx') or file_path.endswith('.ts')):
                continue
            
            # Extract all imports
            import_pattern = r"import\s+(?:\{([^}]+)\}|(\w+))\s+from"
            imports = re.finditer(import_pattern, content)
            
            for match in imports:
                named_imports = match.group(1)
                default_import = match.group(2)
                
                if named_imports:
                    # Check each named import
                    import_names = [n.strip() for n in named_imports.split(',') if n.strip()]
                    for import_name in import_names:
                        # Remove any alias (e.g., "Button as Btn" -> "Btn")
                        actual_name = import_name.split(' as ')[-1].strip()
                        
                        # Check if used in the file (exclude the import line itself)
                        usage_pattern = rf"\b{re.escape(actual_name)}\b"
                        # Count occurrences (should be > 1 because import line counts as 1)
                        occurrences = len(re.findall(usage_pattern, content))
                        
                        if occurrences <= 1:
                            self.warnings.append(CodeValidationError(
                                file_path,
                                "unused_import",
                                f"Import '{actual_name}' is not used",
                                "warning"
                            ))
                
                elif default_import:
                    # Check default import
                    usage_pattern = rf"\b{re.escape(default_import)}\b"
                    occurrences = len(re.findall(usage_pattern, content))
                    
                    if occurrences <= 1:
                        self.warnings.append(CodeValidationError(
                            file_path,
                            "unused_import",
                            f"Import '{default_import}' is not used",
                            "warning"
                        ))
    
    def _validate_undefined_variables(self, files: Dict[str, str]):
        """Basic check for potentially undefined variables"""
        
        for file_path, content in files.items():
            if not file_path.endswith('.tsx'):
                continue
            
            # Look for common undefined variable patterns
            # This is a simplified check - full static analysis would require AST parsing
            
            # Check for variables used in JSX that might not be defined
            jsx_variable_pattern = r"\{(\w+)\}"
            jsx_variables = set(re.findall(jsx_variable_pattern, content))
            
            # Extract defined variables (const, let, var, function, parameters)
            defined_pattern = r"(?:const|let|var|function)\s+(\w+)"
            defined_vars = set(re.findall(defined_pattern, content))
            
            # Extract function parameters
            param_pattern = r"function\s+\w+\s*\(([^)]*)\)"
            params = re.findall(param_pattern, content)
            for param_list in params:
                if param_list.strip():
                    # Extract parameter names (handle destructuring and types)
                    param_names = re.findall(r"(\w+)(?:\??\s*:|,|\))", param_list)
                    defined_vars.update(param_names)
            
            # Common built-in/library values to ignore
            builtins = {'props', 'children', 'className', 'style', 'key', 'ref', 
                       'onClick', 'onChange', 'onSubmit', 'value', 'id', 'name',
                       'true', 'false', 'null', 'undefined', 'console', 'window',
                       'document', 'Array', 'Object', 'String', 'Number', 'Boolean'}
            
            # Check for potentially undefined variables
            for var in jsx_variables:
                if var not in defined_vars and var not in builtins and var[0].islower():
                    self.warnings.append(CodeValidationError(
                        file_path,
                        "potentially_undefined",
                        f"Variable '{var}' used in JSX but may not be defined",
                        "warning"
                    ))
    
    def validate_navigation_pages_sync(self, structure: 'WebsiteStructure') -> Tuple[List[str], List[str]]:
        """
        Validate that navigation items match pages in the structure
        
        Args:
            structure: WebsiteStructure with pages and navigation
            
        Returns:
            Tuple of (errors, warnings) as string lists
        """
        errors = []
        warnings = []
        
        page_paths = {page.path for page in structure.pages}
        nav_paths = {nav.path for nav in structure.navigation}
        
        # Find navigation items with no corresponding page
        missing_pages = nav_paths - page_paths
        
        # Find pages without navigation (excluding utility pages)
        utility_paths = {'/', '/404', '/privacy', '/terms', '/sitemap'}
        missing_nav = page_paths - nav_paths - utility_paths
        
        # Report errors for orphaned navigation
        for path in missing_pages:
            nav_item = next((n for n in structure.navigation if n.path == path), None)
            if nav_item:
                errors.append(
                    f"Navigation item '{nav_item.label}' links to {path} but page doesn't exist"
                )
        
        # Report warnings for pages without navigation
        for path in missing_nav:
            page = next((p for p in structure.pages if p.path == path), None)
            if page:
                warnings.append(
                    f"Page '{page.name}' ({path}) exists but has no navigation item"
                )
        
        return errors, warnings


def fix_lucide_icons_in_content(content: str) -> Tuple[str, List[str]]:
    """
    Automatically fix invalid lucide-react icons in content
    Fixes both import statements AND JSX usage
    
    Args:
        content: File content with potential invalid icons
        
    Returns:
        Tuple of (fixed_content, list_of_changes)
    """
    changes = []
    icon_replacements = {}  # Map invalid icon -> valid icon
    
    # Find all lucide-react imports and build replacement map
    icon_import_pattern = r"import\s+\{([^}]+)\}\s+from\s+['\"]lucide-react['\"]"
    
    def replace_icons_in_import(match):
        imported_icons = match.group(1)
        icons = [icon.strip() for icon in imported_icons.split(',') if icon.strip()]

        fixed_icons = []
        for icon in icons:
            if icon:
                fixed_icon, was_changed = validate_and_fix_icon(icon)
                if was_changed:
                    icon_replacements[icon] = fixed_icon
                    changes.append(f"Replaced '{icon}' with '{fixed_icon}'")
                fixed_icons.append(fixed_icon)
        
        return f"import {{ {', '.join(fixed_icons)} }} from 'lucide-react'"
    
    # First pass: Fix import statements and build replacement map
    fixed_content = re.sub(icon_import_pattern, replace_icons_in_import, content)
    
    # Second pass: Replace icon usages in JSX code
    # Patterns to match:
    # - <IconName /> (self-closing)
    # - <IconName ...> (opening tag)
    # - </IconName> (closing tag)
    # - {IconName} (in JSX expressions)
    
    for invalid_icon, valid_icon in icon_replacements.items():
        # Replace in JSX self-closing tags: <InvalidIcon /> or <InvalidIcon className="..." />
        jsx_self_closing_pattern = rf'<{re.escape(invalid_icon)}((\s[^>]*?)?)\s*/>'
        def replace_self_closing(match):
            attrs = match.group(1) if match.group(1) else ''
            return f'<{valid_icon}{attrs} />'
        fixed_content = re.sub(jsx_self_closing_pattern, replace_self_closing, fixed_content)
        
        # Replace in JSX opening tags: <InvalidIcon ...>
        jsx_opening_pattern = rf'<{re.escape(invalid_icon)}((\s[^>]*?)?)>'
        def replace_opening(match):
            attrs = match.group(1) if match.group(1) else ''
            return f'<{valid_icon}{attrs}>'
        fixed_content = re.sub(jsx_opening_pattern, replace_opening, fixed_content)
        
        # Replace closing tags: </InvalidIcon>
        closing_tag_pattern = rf'</{re.escape(invalid_icon)}>'
        fixed_content = re.sub(closing_tag_pattern, f'</{valid_icon}>', fixed_content)
        
        # Replace in JSX expressions: {InvalidIcon}
        jsx_expr_pattern = rf'\{{{re.escape(invalid_icon)}\}}'
        fixed_content = re.sub(jsx_expr_pattern, f'{{{valid_icon}}}', fixed_content)
        
        # Replace in JSX expressions with props: {InvalidIcon(...)}
        jsx_expr_with_props_pattern = rf'\{{{re.escape(invalid_icon)}\('
        fixed_content = re.sub(jsx_expr_with_props_pattern, f'{{{valid_icon}}}(', fixed_content)
    
    return fixed_content, changes


# Singleton instance
code_validator = CodeValidator()


if __name__ == "__main__":
    # Test the validator
    print("=== Code Validator Test ===\n")
    
    test_content = """
import { Button } from '@/components/ui/button'
import { Handshake, Heart } from 'lucide-react'

export function TestComponent() {
    return <div>Test</div>
}

export default TestComponent
"""
    
    validator = CodeValidator()
    validator._validate_typescript_file("test.tsx", test_content)
    
    print("Errors:")
    for error in validator.errors:
        print(f"  {error}")
    
    print("\nWarnings:")
    for warning in validator.warnings:
        print(f"  {warning}")
    
    print("\n=== Icon Fixing Test ===")
    fixed_content, changes = fix_lucide_icons_in_content(test_content)
    print(f"Changes: {changes}")
    print(f"\nFixed import line:")
    import_line = re.search(r"import.*lucide-react.*", fixed_content)
    if import_line:
        print(f"  {import_line.group(0)}")

