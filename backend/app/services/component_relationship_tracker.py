"""
Component Relationship Tracker Service

This service analyzes React/TypeScript project files to build a map of component
relationships, tracking which components are imported and used in other files,
and what props are passed to them.

This enables prop-aware editing where changes to prop values are made at the
source (parent component) rather than hardcoding them in the child component.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class ComponentUsage:
    """Represents a single usage of a component"""

    def __init__(
        self,
        component_name: str,
        used_in_file: str,
        props: Dict[str, str],
        start_pos: int,
        end_pos: int,
        full_jsx: str
    ):
        self.component_name = component_name
        self.used_in_file = used_in_file
        self.props = props
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.full_jsx = full_jsx

    def __repr__(self):
        return f"<ComponentUsage {self.component_name} in {self.used_in_file}>"


class ComponentRelationshipTracker:
    """
    Tracks component import and usage relationships across a React project.

    This service analyzes all project files to identify:
    1. Which components are imported in which files
    2. Where components are used (rendered) in JSX
    3. What props are passed to each component instance
    """

    def __init__(self):
        self.component_map: Dict[str, List[ComponentUsage]] = {}
        self.file_imports: Dict[str, List[str]] = {}

    def analyze_project_structure(self, files: Dict[str, str]) -> Dict[str, List[ComponentUsage]]:
        """
        Analyze all project files to build component usage map.

        Args:
            files: Dictionary mapping file paths to file contents

        Returns:
            Dictionary mapping component names to list of their usages
        """
        logger.info(f"Analyzing {len(files)} files for component relationships")

        self.component_map = {}
        self.file_imports = {}

        # First pass: Extract imports from all files
        for file_path, content in files.items():
            if self._is_react_file(file_path):
                imports = self._extract_imports(content, file_path)
                self.file_imports[file_path] = imports

        # Second pass: Find component usages
        for file_path, content in files.items():
            if self._is_react_file(file_path):
                imported_components = self.file_imports.get(file_path, [])
                for component_name in imported_components:
                    usages = self._find_component_usages(content, component_name, file_path)
                    if component_name not in self.component_map:
                        self.component_map[component_name] = []
                    self.component_map[component_name].extend(usages)

        logger.info(f"Found {len(self.component_map)} components with usages")
        return self.component_map

    def get_component_usages(self, component_name: str) -> List[ComponentUsage]:
        """
        Get all usages of a specific component.

        Args:
            component_name: Name of the component (e.g., "HeroSection")

        Returns:
            List of ComponentUsage objects
        """
        return self.component_map.get(component_name, [])

    def find_prop_source(
        self,
        component_file: str,
        prop_name: str
    ) -> Optional[Tuple[str, str, ComponentUsage]]:
        """
        Find the source file and value for a specific prop.

        Args:
            component_file: Path to component file (e.g., "src/components/HeroSection.tsx")
            prop_name: Name of the prop (e.g., "title")

        Returns:
            Tuple of (parent_file, prop_value, usage) if found, None otherwise
        """
        # Extract component name from file path
        component_name = self._extract_component_name(component_file)

        # Get all usages of this component
        usages = self.get_component_usages(component_name)

        if not usages:
            logger.warning(f"No usages found for component {component_name}")
            return None

        # Find usage that has this prop
        for usage in usages:
            if prop_name in usage.props:
                prop_value = usage.props[prop_name]
                return (usage.used_in_file, prop_value, usage)

        logger.warning(f"Prop '{prop_name}' not found in any usage of {component_name}")
        return None

    def _is_react_file(self, file_path: str) -> bool:
        """Check if file is a React component file"""
        return file_path.endswith(('.tsx', '.jsx', '.ts', '.js'))

    def _extract_component_name(self, file_path: str) -> str:
        """Extract component name from file path"""
        # Get filename without extension
        # e.g., "src/components/HeroSection.tsx" -> "HeroSection"
        return Path(file_path).stem

    def _extract_imports(self, content: str, file_path: str) -> List[str]:
        """
        Extract imported component names from a file.

        Handles:
        - Named imports: import { Hero } from '@/components/Hero'
        - Default imports: import Hero from '@/components/Hero'
        - Multiple imports: import { Hero, Footer } from '@/components'
        """
        imports = []

        # Pattern 1: Named imports
        # import { Hero, Footer } from '@/components/...'
        named_pattern = r'import\s+\{([^}]+)\}\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(named_pattern, content):
            names = match.group(1)
            import_path = match.group(2)

            # Skip non-component imports (hooks, utils, etc.)
            if not self._looks_like_component_import(import_path):
                continue

            # Split multiple imports: { Hero, Footer } -> ["Hero", "Footer"]
            for name in names.split(','):
                name = name.strip()
                # Remove any 'type' keyword: import { type Props, Hero }
                name = re.sub(r'^type\s+', '', name)
                if name and name[0].isupper():  # Component names start with uppercase
                    imports.append(name)

        # Pattern 2: Default imports
        # import Hero from '@/components/Hero'
        default_pattern = r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(default_pattern, content):
            name = match.group(1)
            import_path = match.group(2)

            # Skip non-component imports
            if not self._looks_like_component_import(import_path):
                continue

            if name and name[0].isupper():
                imports.append(name)

        logger.debug(f"Found {len(imports)} component imports in {file_path}: {imports}")
        return imports

    def _looks_like_component_import(self, import_path: str) -> bool:
        """Check if import path looks like a component import"""
        # Component imports typically come from:
        # - @/components/...
        # - ./components/...
        # - ../components/...
        # But NOT from libraries like 'react', 'framer-motion', etc.

        if import_path.startswith(('@/components', './components', '../components')):
            return True
        if import_path.startswith(('./', '../')) and 'components' in import_path.lower():
            return True

        # Exclude common library imports
        excluded = ['react', 'react-dom', 'framer-motion', 'lucide-react', '@radix-ui']
        return not any(import_path.startswith(lib) for lib in excluded)

    def _find_component_usages(
        self,
        content: str,
        component_name: str,
        file_path: str
    ) -> List[ComponentUsage]:
        """
        Find all usages of a component in a file and extract props.

        Handles:
        - Self-closing: <Hero title="..." />
        - With children: <Hero title="...">children</Hero>
        - Multi-line props
        """
        usages = []

        # Pattern for component usage (both self-closing and with children)
        # <ComponentName ...props />  OR  <ComponentName ...props>
        pattern = rf'<{component_name}\s+([^>]*?)(/?>)'

        for match in re.finditer(pattern, content, re.DOTALL):
            props_str = match.group(1).strip()
            is_self_closing = match.group(2) == '/>'

            # Parse props from the props string
            props = self._parse_props(props_str)

            # Get the full JSX including closing tag if not self-closing
            start_pos = match.start()
            if is_self_closing:
                end_pos = match.end()
                full_jsx = content[start_pos:end_pos]
            else:
                # Find closing tag
                closing_pattern = rf'</{component_name}>'
                closing_match = re.search(closing_pattern, content[match.end():])
                if closing_match:
                    end_pos = match.end() + closing_match.end()
                    full_jsx = content[start_pos:end_pos]
                else:
                    # Couldn't find closing tag, just use opening
                    end_pos = match.end()
                    full_jsx = content[start_pos:end_pos]

            usage = ComponentUsage(
                component_name=component_name,
                used_in_file=file_path,
                props=props,
                start_pos=start_pos,
                end_pos=end_pos,
                full_jsx=full_jsx
            )

            usages.append(usage)
            logger.debug(f"Found usage of {component_name} in {file_path} with props: {list(props.keys())}")

        return usages

    def _parse_props(self, props_str: str) -> Dict[str, str]:
        """
        Extract prop values from a component's props string.

        Handles:
        - String props: title="Hello"
        - Expression props: count={42}
        - Multi-line props
        - Props with quotes in values

        Args:
            props_str: String containing all props (e.g., 'title="Hello" count={42}')

        Returns:
            Dictionary mapping prop names to values
        """
        props = {}

        # Pattern to match prop assignments
        # Matches: propName="string value"  OR  propName={expression}
        # This regex handles:
        # - String literals: title="Hello World"
        # - JSX expressions: count={42}, items={items}, className={cn("base", className)}

        # Match string props: propName="value"
        string_pattern = r'(\w+)="([^"]*)"'
        for match in re.finditer(string_pattern, props_str):
            prop_name = match.group(1)
            prop_value = match.group(2)
            props[prop_name] = prop_value

        # Match expression props: propName={value}
        # This is more complex as expressions can contain nested braces
        expr_pattern = r'(\w+)=\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        for match in re.finditer(expr_pattern, props_str):
            prop_name = match.group(1)
            prop_value = match.group(2)
            # Store expressions with braces to indicate they're not strings
            props[prop_name] = f"{{{prop_value}}}"

        return props


# Singleton instance
component_tracker = ComponentRelationshipTracker()
