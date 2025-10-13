"""
React Website Generator Service
Generates a complete React/TypeScript website structure based on business analysis.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from traceback import print_tb
from typing import Dict, Any, List, Union

from app.services.business_analyzer import BusinessAnalyzer, BusinessAnalysis
from app.services.prompt_open_ai import PromptOpenAI
from app.services.react_models import PageComponent, PageStructure, WebsiteStructure, PageGenerationResponse
from app.services.react_file_manager import react_file_manager
from app.services.icon_validator import format_icons_for_prompt, validate_and_fix_icon, is_valid_icon
from app.services.code_validator import code_validator, fix_lucide_icons_in_content

logger = logging.getLogger(__name__)


def write_files_to_disk(files: Dict[str, str], base_path: str) -> Dict[str, str]:
    """
    Write all generated files to disk
    
    Args:
        files: Dictionary mapping file paths to file contents
        base_path: Base directory path where files should be written
        
    Returns:
        Dictionary mapping file paths to absolute paths on disk
        
    Example:
        files = {
            "package.json": "...",
            "src/App.tsx": "...",
            "src/components/Hero.tsx": "..."
        }
        write_files_to_disk(files, "output/my-website")
    """
    base_dir = Path(base_path)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    written_files = {}
    
    logger.info(f"[FILE WRITER] Writing {len(files)} files to {base_dir.absolute()}")
    print(f"[FILE WRITER] Writing {len(files)} files to {base_dir.absolute()}")
    
    for relative_path, content in files.items():
        # Create full path
        full_path = base_dir / relative_path
        
        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            written_files[relative_path] = str(full_path.absolute())
            logger.debug(f"[FILE WRITER] ✓ Written: {relative_path}")
            print(f"[FILE WRITER] ✓ Written: {relative_path}")
            
        except Exception as e:
            logger.error(f"[FILE WRITER] ✗ Failed to write {relative_path}: {str(e)}")
            print(f"[FILE WRITER] ✗ Failed to write {relative_path}: {str(e)}")
            raise
    
    logger.info(f"[FILE WRITER] ✓ Successfully written all {len(written_files)} files to disk")
    print(f"[FILE WRITER] ✓ Successfully written all {len(written_files)} files to disk")
    logger.info(f"[FILE WRITER] Location: {base_dir.absolute()}")
    
    return written_files


class ReactWebsiteGenerator:
    """Generates complete React website structure from user prompt"""
    
    def __init__(self):
        self.openai_client = PromptOpenAI()
        self.business_analyzer = BusinessAnalyzer()
    
    def generate_website_structure(self, prompt: str) -> Dict[str, Any]:
        """
        Main entry point: Generate complete React website from prompt
        
        Returns a dictionary containing:
        - website_structure: Complete website structure
        - business_analysis: Original business analysis
        - files: Dictionary of file paths to file contents
        """
        logger.info("[REACT GEN] Starting React website generation...")
        
        # Step 1: Analyze business requirements
        logger.info("[REACT GEN] Analyzing business requirements...")
        business_analysis = self.business_analyzer.generate_business_analysis(prompt)
        
        # Step 2: Generate website structure
        logger.info("[REACT GEN] Generating website structure...")
        website_structure = self._generate_structure_from_analysis(business_analysis)

        # Debug: Write schema and structure to files
        with open('/tmp/website_structure_schema.json', 'w') as f:
            json.dump(website_structure.model_json_schema(), f, indent=2)
        
        with open('/tmp/website_structure_data.json', 'w') as f:
            json.dump(website_structure.model_dump(), f, indent=2)
        
        logger.info("[REACT GEN] ✓ Debug files written to /tmp/website_structure_*.json")
        
        # Step 3: Generate file contents
        logger.info("[REACT GEN] Generating React files...")
        files = self._generate_all_files(website_structure, business_analysis)
        
        logger.info("[REACT GEN] ✓ React website generation complete")

        # Write files to disk with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        website_name = website_structure.name.lower().replace(" ", "-")
        output_path = f"app/data/generated_sites/{website_name}_{timestamp}"
        
        written_files = write_files_to_disk(files, output_path)
        
        return {
            "website_structure": website_structure.model_dump(),
            "business_analysis": business_analysis.model_dump(),
            "files": files
        }
    
    def _generate_structure_from_analysis(self, analysis: BusinessAnalysis) -> WebsiteStructure:
        """Convert business analysis into website structure"""
        
        system_prompt = """You are a website architect. Generate a complete website structure based on business analysis.
        
Your task:
1. Create page structures for each key page
2. Define components/sections for each page based on content_sections
3. Map business requirements to appropriate React components
4. Ensure logical flow and user experience
5. Determing if its a single page website (ONLY 1 page) or multiple pages website (more than 1 page).
6. If its a single page website, ensure the page is named HomePage and the path is /, with header navigation urls pointing to the sections in the page with #menu for menu for example

Component types available:
- header: Header section with logo, navigation, and CTA
- hero: Main hero section with CTA
- features: Grid of features/services
- about: About section with story/mission
- testimonials: Customer testimonials
- contact: Contact form and information
- cta: Call-to-action section with CTA
- stats: Statistics/numbers section
- team: Team members grid
- pricing: Pricing tables
- gallery: Image gallery
- faq: Frequently asked questions
- footer: Footer section

Return a complete website structure with all pages and their components."""

        user_prompt = f"""Based on this business analysis, create a complete website structure:

Business Type: {analysis.business_type}
Industry: {analysis.industry}
Site Purpose: {analysis.site_purpose}
Target Audience: {analysis.target_audience}

Pages Needed: {', '.join(analysis.key_pages)}
Content Sections: {', '.join(analysis.content_sections)}
Must-Have Features: {', '.join(analysis.must_have_features)}
Primary CTA: {analysis.primary_cta}

Tone: {analysis.tone}
Style: {', '.join(analysis.style_keywords)}
Colors: {', '.join(analysis.primary_colors)}

Value Propositions:
{chr(10).join(f"- {vp}" for vp in analysis.value_propositions)}

Create a website structure with appropriate pages and components for each page."""
        self.openai_client.set_max_completion_tokens(6000)
        response, usage = self.openai_client.call_openai_api_structured(
            system_prompt,
            user_prompt,
            WebsiteStructure
        )

        print(f"Usage for structure generation: {usage}")
        
        return response
    
    def _generate_all_files(self, structure: WebsiteStructure, analysis: BusinessAnalysis) -> Dict[str, str]:
        """Generate all React project files"""
        
        files = {}
        
        # Core config files (package.json, vite.config, etc.)
        files.update(react_file_manager.generate_config_files(structure))
        
        # UI components (shadcn/ui primitives - base set)
        files.update(react_file_manager.generate_ui_components())
        
        # App setup files (App.tsx, main.tsx)
        files.update(react_file_manager.generate_app_files(structure))
        
        # Style files (index.css)
        files.update(react_file_manager.generate_style_files(structure))
        
        # Page components (will auto-generate any missing section/UI components)
        files.update(self._generate_page_files(structure, analysis))
        
        # Post-generation validation
        logger.info("[REACT GEN] Running post-generation validation...")
        errors, warnings = code_validator.validate_all_files(files)
        
        # Log validation results
        if errors:
            logger.error(f"[REACT GEN] ❌ Found {len(errors)} validation errors:")
            for error in errors[:10]:  # Log first 10 errors
                logger.error(f"  {error}")
            if len(errors) > 10:
                logger.error(f"  ... and {len(errors) - 10} more errors")
        
        if warnings:
            logger.warning(f"[REACT GEN] ⚠ Found {len(warnings)} validation warnings:")
            for warning in warnings[:5]:  # Log first 5 warnings
                logger.warning(f"  {warning}")
            if len(warnings) > 5:
                logger.warning(f"  ... and {len(warnings) - 5} more warnings")
        
        if not errors and not warnings:
            logger.info("[REACT GEN] ✓ All validation checks passed!")
        
        return files
    
    def _generate_page_files(self, structure: WebsiteStructure, analysis: BusinessAnalysis) -> Dict[str, str]:
        """Generate page component files"""
        
        files = {}
        
        for page in structure.pages:
            page_content = self._generate_page_component(page, structure, analysis, files)
            page_filename = page.name.lower().replace(" ", "-")
            files[f"src/pages/{page_filename}.tsx"] = page_content
        
        return files
    
    def _generate_page_component(self, page: PageStructure, structure: WebsiteStructure, analysis: BusinessAnalysis, files: Dict[str, str]) -> str:
        """
        Generate individual page component using LLM.
        Automatically generates any missing section or UI components needed.
        """
        
        logger.info(f"[PAGE GEN] Generating page: {page.name}")
        
        # Get available UI components
        available_ui_components = self._get_available_ui_components(files)
        
        # Get available section components
        available_section_components = self._get_available_section_components(files)
        
        # Prepare component requirements
        required_components = [comp.name for comp in page.components]
        
        logger.info(f"[PAGE GEN] Required components: {required_components}")
        logger.info(f"[PAGE GEN] Available UI components: {available_ui_components}")
        logger.info(f"[PAGE GEN] Available section components: {available_section_components}")
        
        # Create system prompt
        system_prompt = self._create_page_generation_system_prompt()
        
        # Create user prompt with context
        user_prompt = self._create_page_generation_user_prompt(
            page=page,
            structure=structure,
            analysis=analysis,
            available_ui_components=available_ui_components,
            available_section_components=available_section_components
        )
        
        # Call LLM to generate page and components
        logger.info(f"[PAGE GEN] Calling LLM for page generation...")
        self.openai_client.set_max_completion_tokens(16000)
        response, usage = self.openai_client.call_openai_api_structured(
            system_prompt,
            user_prompt,
            PageGenerationResponse,
            model="o4-mini"
        )
        
        print(f"Usage for page {page.name} generation: {usage}")
        
        # Post-validation: Fix any invalid icons in generated code
        logger.info(f"[PAGE GEN] Validating generated code...")
        
        # Fix icons in page content
        fixed_page_content, page_changes = fix_lucide_icons_in_content(response.page_content)
        if page_changes:
            logger.warning(f"[PAGE GEN] Fixed icons in page: {', '.join(page_changes)}")
        response.page_content = fixed_page_content
        
        # Add newly generated components to files dictionary
        set_available_ui_components = set(available_ui_components)
        for component_file in response.new_components:
            # Fix icons in component content
            fixed_content, comp_changes = fix_lucide_icons_in_content(component_file.content)
            if comp_changes:
                logger.warning(f"[PAGE GEN] Fixed icons in {component_file.path}: {', '.join(comp_changes)}")
            component_file.content = fixed_content
            
            # Check for duplicates
            if component_file.path in files:
                logger.warning(f"[PAGE GEN] ⚠ Component {component_file.path} already exists, skipping...")
                continue
            
            if component_file.path.lower() not in set_available_ui_components:
                files[component_file.path] = component_file.content
                logger.info(f"[PAGE GEN] ✓ Generated new {component_file.component_type} component: {component_file.path}")
            
        logger.info(f"[PAGE GEN] ✓ Page '{page.name}' generated successfully")
        
        return response.page_content
    
    def _format_component_props(self, props: List) -> str:
        """Format component props for JSX"""
        if not props:
            return ""
        
        # Convert List[PropItem] to dict
        props_dict = {item.key: item.value for item in props}
        
        prop_strings = []
        for key, value in props_dict.items():
            if isinstance(value, str):
                prop_strings.append(f'{key}="{value}"')
            elif isinstance(value, (int, float, bool)):
                prop_strings.append(f'{key}={{{value}}}')
            elif value is None:
                continue  # Skip None values
            elif isinstance(value, (list, dict)):
                prop_strings.append(f'{key}={{{json.dumps(value)}}}')
        
        return " ".join(prop_strings)
    
    def _get_available_ui_components(self, files: Dict[str, str]) -> List[str]:
        """Extract list of available UI component names from files"""
        ui_components = []
        for file_path in files.keys():
            if file_path.startswith("src/components/ui/") and file_path.endswith(".tsx"):
                # Extract component name from path (e.g., "button" from "src/components/ui/button.tsx")
                component_name = file_path.split("/")[-1].replace(".tsx", "")
                ui_components.append(component_name.lower())
        return sorted(ui_components)
    
    def _get_available_section_components(self, files: Dict[str, str]) -> List[str]:
        """Extract list of available section component names from files"""
        section_components = []
        for file_path in files.keys():
            if file_path.startswith("src/components/") and not file_path.startswith("src/components/ui/") and file_path.endswith(".tsx"):
                # Extract component name from path (e.g., "Hero" from "src/components/Hero.tsx")
                component_name = file_path.split("/")[-1].replace(".tsx", "")
                section_components.append(component_name)
        return sorted(section_components)
    
    def _create_page_generation_system_prompt(self) -> str:
        """Create system prompt for page generation"""
        
        # Get formatted list of safe icons
        safe_icons_list = format_icons_for_prompt()
        
        return f"""You are an expert React developer tasked with generating production-ready web application components. Your code must be professional, maintainable, and error-free.

Your task is to generate a complete page component with proper structure, imports, and styling using:
TECHNOLOGY STACK:
- React 19 with TypeScript (strict mode)
- Tailwind CSS for styling
- shadcn/ui components (built on Radix UI)
- Lucide React icons (CRITICAL: ONLY use verified icons from the list below)
- Modern React patterns and hooks
- Proper TypeScript types and interfaces
- Use working and functioning unsplash for images, for example: https://images.unsplash.com/photo-...
- Use <a></a> for links instead of <Link></Link> (next/link)
- Vite for building the website

{safe_icons_list}

CRITICAL: You MUST ONLY use icons from the above list. Using any other icon will cause build errors.

IMPORTANT RULES:
1. **Page Component**: Generate a clean, functional React component for the requested page
2. **Missing Components**: If any required section component (Header, Hero, Features, Team, Footer etc.) doesn't exist, create it in `new_components` array
3. **Missing UI Components**: If you need a UI component (badge, avatar, etc.) that doesn't exist, create it following shadcn/ui patterns
4. **Component Structure**:
   - Section components go in: `src/components/<ComponentName>.tsx` (e.g., Header.tsx, Hero.tsx, Team.tsx, Footer.tsx)
   - UI components go in: `src/components/ui/<component-name>.tsx` (e.g., badge.tsx, avatar.tsx)
5. **CRITICAL - Export/Import Consistency**:
   - Each file must have EXACTLY ONE type of export (named OR default, NEVER both)
   - Section components MUST use named exports: `export function ComponentName() {{}}`
   - Pages MUST use default exports: `export default function PageName() {{}}`
   - Imports MUST match the export style exactly
6. **CRITICAL - Props Consistency**:
   - When defining a component with props, ensure ALL pages using it pass those props
   - If a component requires props like `navItems`, every usage MUST provide those props
   - Define props with sensible defaults or make them required
   - Example: `export function Header({{ navItems = [] }}: HeaderProps)` allows optional usage
7. **Style Consistency**: Use Tailwind CSS classes and follow modern UI/UX principles
8. **TypeScript**: All components must have proper TypeScript types and interfaces
9. **Responsive Design**: Ensure all components are mobile-first and responsive
10. **Accessibility**: Follow ARIA standards and semantic HTML
11. **CRITICAL - No Duplicates**: Never generate the same component twice. Check available components first.
12. **CRITICAL - Icon Usage**: Only use icons from the verified list above. No exceptions.

CRITICAL: EXPORT/IMPORT RULES (NO ERRORS)
RULE 1: ONE EXPORT PER FILE
Each component file must have EXACTLY ONE export (either named OR default, never both).

RULE 2: EXPORT PATTERNS BY COMPONENT TYPE

Section Components (src/components/Header.tsx, Hero.tsx, etc.):
CORRECT - Named Export (PREFERRED):
export function Hero({{ title }}: HeroProps) {{
  return <section>...</section>
}}
ALSO CORRECT:
export default function Hero({{ title }}: HeroProps) {{
  return <section>...</section>
}}
WRONG:
function Hero() {{ return <div /> }}
export {{ Hero }};
export default Hero; // ERROR: Duplicate!

Page Components (src/pages/HomePage.tsx):
CORRECT - Default Export:
export default function HomePage() {{
  return <main>...</main>
}}

RULE 3: IMPORT MUST MATCH EXPORT STYLE
Named Export → Named Import:
// Component: export function Hero() {{}}
import {{ Hero }} from '@/components/Hero' // CORRECT

// UI: export const Button = ...
import {{ Button }} from '@/components/ui/button' // CORRECT

Default Export → Default Import
// Component: export default function Hero() {{}}
import Hero from '@/components/Hero' // CORRECT

RULE 4: COMMON ERRORS TO AVOID
// ERROR: Duplicate Named Export
export function Button() {{}}
export {{ Button }} // Duplicate!

// ERROR: Mixed Export Styles
export function Hero() {{}}
export default Hero; // Conflict!

// ERROR: Import Mismatch
// File has: export function Hero() {{}}
import Hero from '@/components/Hero' // WRONG - looking for default!
// Should be: import {{ Hero }} from '@/components/Hero'


RULE 5: PREFERRED PATTERNS

Section components: Named exports → import {{ Header }} from '@/components/Header'
UI primitives components: Named exports → import {{ Button }} from '@/components/ui/button'
Pages: Default exports → import HomePage from '@/pages/HomePage'


PRE-GENERATION CHECKLIST
Before generating code, verify:
- Each component file has EXACTLY ONE export (named OR default, not both)
- All imports match their corresponding export styles
- Import paths are correct (@/components/, @/components/ui/)
- No duplicate exports anywhere
- All TypeScript types and interfaces are defined
- Props passed to components match their type definitions
- Components are responsive (mobile-first)
- Accessibility standards are met
- Code follows React best practices


QUALITY STANDARDS
Your generated code must:

- Be production-ready and pass professional code review
- Have zero TypeScript errors
- Have zero export/import errors
- Be fully typed with no 'any' types
- Be responsive and accessible
- Follow modern React patterns
- Be performant and optimized
- Be maintainable and well-structured


When in doubt:
- Use named exports for components
- Match import style to export style
- One export per file
- Explicit types over implicit
- Semantic HTML over divs
- Tailwind utilities over custom CSS

COMPONENT GUIDELINES:
- Section components should accept props with sensible defaults
- Use existing UI components whenever possible
- Follow the shadcn/ui pattern for new UI components (Radix UI + Tailwind)
- Import only what's needed
- Use proper React hooks and patterns
- Add proper className for Tailwind styling

OUTPUT FORMAT:
Return a JSON object with:
- `page_content`: Complete page component code
- `new_components`: Array of any new components needed (both section and UI components)"""
    
    def _create_page_generation_user_prompt(
        self,
        page: PageStructure,
        structure: WebsiteStructure,
        analysis: BusinessAnalysis,
        available_ui_components: List[str],
        available_section_components: List[str]
    ) -> str:
        """Create user prompt with all context for page generation"""
        
        # Format component requirements with props
        component_details = []
        for comp in page.components:
            props_dict = {item.key: item.value for item in comp.props}
            component_details.append(f"  - {comp.name} ({comp.type}): {json.dumps(props_dict, indent=4)}")

        nav_items = []
        for nav_item in structure.navigation:
            nav_items.append(f"  - {nav_item.label}: {nav_item.path}")
        
        prompt = f"""Generate a complete React page component with the following specifications:

PAGE INFORMATION:
- Page Name: {page.name}
- Route Path: {page.path}
- Page Title: {page.title}
- Description: {page.description}

REQUIRED COMPONENTS ON THIS PAGE:
{chr(10).join(component_details)}

BUSINESS CONTEXT:
- Business Type: {analysis.business_type}
- Industry: {analysis.industry}
- Target Audience: {analysis.target_audience}
- Tone: {analysis.tone}
- Primary CTA: {analysis.primary_cta}
- Color Scheme: {structure.color_scheme}

AVAILABLE UI COMPONENTS (can be imported from @/components/ui/<name>):
{', '.join(available_ui_components) if available_ui_components else 'None yet - generate as needed'}

AVAILABLE SECTION COMPONENTS (can be imported from @/components/<Name>):
{', '.join(available_section_components) if available_section_components else 'None yet - generate as needed'}

WEBSITE NAVIGATION STRUCTURE:
{chr(10).join(nav_items) if nav_items else 'None - Single page website'}

TASK:
1. **Header Component Requirements**:
   - If Header doesn't exist in available components, create it with these exact navigation items
   - Header MUST accept optional props OR use the navigation structure above as default
   - Example: `export function Header({{ logo = "{structure.name}" }}: HeaderProps)`
   - Include proper navigation links matching the website structure above
   
2. **Footer Component Requirements**:
   - If Footer doesn't exist, create a simple footer with copyright and basic links
   - Footer can be static or accept minimal props
   
3. Create a complete page component for "{page.name}" by importing and using the section components

4. **Component Reuse**:
   - DO NOT modify existing UI components - reuse them as-is
   - Only create NEW components that don't exist yet
   - Check available components list carefully before creating new ones
   
5. For any section component (Header, Hero, Features, Team, Footer etc.) that doesn't exist in available section components, create it and add to `new_components`

6. For any UI component (badge, avatar, etc.) that doesn't exist in available UI components, create it following shadcn/ui patterns and add to `new_components`

7. **Props Consistency**:
   - Ensure component prop definitions match their usage across all pages
   - Use sensible defaults for props to allow flexible usage
   - Example: If Header needs navItems, define it as `navItems = [default array]`
   
8. Ensure the page is visually appealing, responsive, and matches the business context

9. Use proper TypeScript types and modern React patterns

10. **CRITICAL**: Only use icons from the verified safe icons list provided above

EXAMPLE COMPONENT STRUCTURE:

Header Component with Navigation (src/components/Header.tsx):
```tsx
import React from 'react'
import {{ Button }} from '@/components/ui/button'

interface NavItem {{
  label: string
  path: string
}}

interface HeaderProps {{
  brandName?: string
  navItems?: NavItem[]
  ctaText?: string
}}

export function Header({{
  brandName = "My Business",
  navItems = [],
  ctaText = "Get Started"
}}: HeaderProps) {{
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
      <div className="container flex h-16 items-center justify-between">
        <a href="/" className="text-xl font-bold">{{brandName}}</a>
        <nav className="hidden md:flex items-center gap-6">
          {{navItems.map((item) => (
            <a key={{item.path}} href={{item.path}} className="text-sm font-medium hover:underline">
              {{item.label}}
            </a>
          ))}}
        </nav>
        <Button size="sm">{{ctaText}}</Button>
      </div>
    </header>
  )
}}
```

Hero Section Component (src/components/Hero.tsx):
```tsx
import React from 'react'
import {{ Button }} from '@/components/ui/button'
import {{ ArrowRight }} from 'lucide-react'

interface HeroProps {{
  title?: string
  subtitle?: string
  ctaText?: string
}}

export function Hero({{
  title = "Default Title",
  subtitle = "Default Subtitle",
  ctaText = "Get Started"
}}: HeroProps) {{
  return (
    <section className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h1 className="text-4xl sm:text-6xl font-bold mb-6">{{title}}</h1>
        <p className="text-xl mb-8">{{subtitle}}</p>
        <Button size="lg">
          {{ctaText}}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </section>
  )
}}
```

UI Component (src/components/ui/badge.tsx) - Follow shadcn/ui pattern:
```tsx
import * as React from "react"
import {{ cva, type VariantProps }} from "class-variance-authority"
import {{ cn }} from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {{
    variants: {{
      variant: {{
        default: "bg-primary text-primary-foreground",
        secondary: "bg-secondary text-secondary-foreground",
      }}
    }},
    defaultVariants: {{ variant: "default" }}
  }}
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {{}}

function Badge({{ className, variant, ...props }}: BadgeProps) {{
  return (
    <div className={{cn(badgeVariants({{ variant }}), className)}} {{...props}} />
  )
}}

export {{ Badge, badgeVariants }}
```

Generate the page and all necessary components now."""
        
        return prompt


# Create singleton instance
react_website_generator = ReactWebsiteGenerator()

