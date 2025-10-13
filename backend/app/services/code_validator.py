"""
Code Validator Service
Validates generated React/TypeScript code for common errors.
"""

import re
import logging
from typing import Dict, List, Tuple, Set
from app.services.icon_validator import is_valid_icon, validate_and_fix_icon

logger = logging.getLogger(__name__)


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
        
        logger.info(f"[CODE VALIDATOR] Found {len(self.errors)} errors and {len(self.warnings)} warnings")
        
        return self.errors, self.warnings
    
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
            icons = [icon.strip() for icon in imported_icons.split(',')]
            
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
            # Check if default export matches a named export
            default_pattern = r"export\s+default\s+(\w+)"
            default_matches = re.findall(default_pattern, content)
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
        export_map: Dict[str, Dict[str, str]] = {}  # file_path -> {export_name: export_type}
        
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
            
            # Find re-exports
            reexport_pattern = r"export\s+\{([^}]+)\}"
            reexports = re.findall(reexport_pattern, content)
            for reexport in reexports:
                names = [n.strip() for n in reexport.split(',')]
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
                        import_names = [n.strip() for n in named_imports.split(',')]
                        for name in import_names:
                            if name not in exports:
                                self.errors.append(CodeValidationError(
                                    file_path,
                                    "import_export_mismatch",
                                    f"Named import '{name}' from '{import_path}' not found. Available exports: {list(exports.keys())}"
                                ))
                            elif exports[name] != 'named':
                                self.errors.append(CodeValidationError(
                                    file_path,
                                    "import_export_mismatch",
                                    f"'{name}' is exported as default but imported as named"
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


def fix_lucide_icons_in_content(content: str) -> Tuple[str, List[str]]:
    """
    Automatically fix invalid lucide-react icons in content
    
    Args:
        content: File content with potential invalid icons
        
    Returns:
        Tuple of (fixed_content, list_of_changes)
    """
    changes = []
    
    # Find all lucide-react imports
    icon_import_pattern = r"import\s+\{([^}]+)\}\s+from\s+['\"]lucide-react['\"]"
    
    def replace_icons(match):
        imported_icons = match.group(1)
        icons = [icon.strip() for icon in imported_icons.split(',')]
        
        fixed_icons = []
        for icon in icons:
            if icon:
                fixed_icon, was_changed = validate_and_fix_icon(icon)
                if was_changed:
                    changes.append(f"Replaced '{icon}' with '{fixed_icon}'")
                fixed_icons.append(fixed_icon)
        
        return f"import {{ {', '.join(fixed_icons)} }} from 'lucide-react'"
    
    fixed_content = re.sub(icon_import_pattern, replace_icons, content)
    
    return fixed_content, changes


# Singleton instance
code_validator = CodeValidator()


if __name__ == "__main__":
    # Test the validator
    print("=== Code Validator Test ===\n")
    
    test_content = """
import React from 'react'
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

