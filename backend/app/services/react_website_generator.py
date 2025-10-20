"""
React Website Generator Service
Generates a complete React/TypeScript website structure based on business analysis.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from traceback import print_tb
from typing import Dict, Any, List, Union, Optional

from app.config import settings
from app.services.business_analyzer import BusinessAnalyzer, BusinessAnalysis
from app.services.prompt_open_ai import PromptOpenAI
from app.services.react_models import (
    PageComponent, PageStructure, WebsiteStructure, PageGenerationResponse,
    ValidationResult, ValidationError, BuildTestResult, GenerationResult
)
from app.services.react_file_manager import react_file_manager
from app.services.icon_validator import format_icons_for_prompt, validate_and_fix_icon, is_valid_icon
from app.services.code_validator import code_validator, fix_lucide_icons_in_content, CodeValidationError
from app.services.error_fixer import error_fixer
from app.services.build_tester import build_tester, BuildError

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
        self.google_client = PromptOpenAI(api_key=settings.google_api_key, url="https://generativelanguage.googleapis.com/v1beta/openai/")
        self.business_analyzer = BusinessAnalyzer()
    
    def generate_website_structure(
        self, 
        prompt: str, 
        enable_build_validation: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: Generate complete React website from prompt with validation
        
        Args:
            prompt: User's website description
            enable_build_validation: Whether to run actual build tests (None = use config default)
        
        Returns a dictionary containing:
        - website_structure: Complete website structure
        - business_analysis: Original business analysis
        - files: Dictionary of file paths to file contents
        - validation: Validation results
        - build_test: Build test results (if enabled)
        - retry_count: Number of retry attempts made
        - fixed_errors: List of errors that were auto-fixed
        - generation_time: Total generation time
        """
        start_time = time.time()
        
        # Use config default if not specified
        if enable_build_validation is None:
            enable_build_validation = settings.enable_build_validation
        
        logger.info("[REACT GEN] Starting React website generation with validation...")
        
        # Step 1: Analyze business requirements
        logger.info("[REACT GEN] Analyzing business requirements...")
        business_analysis = self.business_analyzer.generate_business_analysis(prompt)
        print(f"Business analysis: \n{business_analysis.model_dump_json(indent=2)}")
        
        # Step 2: Generate website structure
        logger.info("[REACT GEN] Generating website structure...")
        website_structure = self._generate_structure_from_analysis(business_analysis)

        print(f"Website structure: \n{website_structure.model_dump_json(indent=2)}")
        
        # Validate navigation matches pages
        logger.info("[REACT GEN] Validating structure consistency...")
        self._validate_structure_consistency(website_structure)
        
        # Debug: Write schema and structure to files
        with open('/tmp/website_structure_schema.json', 'w') as f:
            json.dump(website_structure.model_json_schema(), f, indent=2)
        
        with open('/tmp/website_structure_data.json', 'w') as f:
            json.dump(website_structure.model_dump(), f, indent=2)
        
        logger.info("[REACT GEN] ✓ Debug files written to /tmp/website_structure_*.json")
        
        # Step 3: Generate file contents
        logger.info("[REACT GEN] Generating React files...")

        

        files = self._generate_all_files(website_structure, business_analysis)
        
        # Step 4: Validation and error fixing loop
        logger.info("[REACT GEN] Starting validation and error fixing...")
        files, validation_result, retry_count, fixed_errors = self._validate_and_fix_files(
            files, 
            enable_build_validation
        )
        
        generation_time = time.time() - start_time
        
        logger.info(f"[REACT GEN] ✓ React website generation complete in {generation_time:.2f}s")
        logger.info(f"[REACT GEN] Retries: {retry_count}, Fixed errors: {len(fixed_errors)}")

        # Write files to disk with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        website_name = website_structure.name.lower().replace(" ", "-")
        output_path = f"app/data/generated_sites/{website_name}_{timestamp}"
        
        written_files = write_files_to_disk(files, output_path)
        
        return {
            "website_structure": website_structure.model_dump(),
            "business_analysis": business_analysis.model_dump(),
            "files": files,
            "validation": validation_result.model_dump(),
            "build_test": validation_result.model_dump() if hasattr(validation_result, 'build_test') else None,
            "retry_count": retry_count,
            "fixed_errors": fixed_errors,
            "generation_time": generation_time
        }
    
    def _generate_structure_from_analysis(self, analysis: BusinessAnalysis) -> WebsiteStructure:
        """Convert business analysis into website structure"""
        
        system_prompt = f"""You are a website architect. Generate a complete website structure based on business analysis.
        
Your task:
1. Create page structures for each key page - {', '.join(analysis.key_pages)}
2. Define components/sections for each page based on content_sections - {', '.join(analysis.content_sections)}
3. Map business requirements to appropriate React components
4. Ensure logical flow and user experience
5. Determing if its a single page website (ONLY 1 page) or multiple pages website (more than 1 page).
6. If its a single page website, ensure the page is named HomePage and the path is /, with header navigation urls pointing to the sections in the page with #menu for menu for example

CRITICAL: Navigation and Pages MUST Match Exactly
7. For EVERY navigation item you create, there MUST be a corresponding page with the EXACT same path
8. For EVERY page you create, there MUST be a corresponding navigation item (except utility pages like 404, privacy)
9. Navigation item path MUST exactly match page path
   Example: 
   Navigation: {{label: "About", path: "/about"}}
   Page: {{name: "About", path: "/about"}}
   There must be a one to one mapping between navigation items and pages
10. Do NOT create navigation items without creating the page
11. Do NOT create pages without adding them to navigation (unless utility pages)
12. ENSURE that all values in the "props" are generated with appropriate values, not just empty strings or numbers. And make use of href for links, not just url.
sample data might look like this for example:
{{
    id: 'linkedin',
    label: 'LinkedIn',
    href: 'https://linkedin.com/in/aureliaphoto', // not "url: ''"
    icon: <ExternalLink className="h-5 w-5" aria-hidden />
}}

CRITICAL: 
- Home path must be /
- Page and component names must be joined without spaces, not hyphens. Example: Home, About, ProjectDetail, etc.

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

These pages must be created: {', '.join(analysis.key_pages)}
These content sections must be created: {', '.join(analysis.content_sections)}
These must-have features must be created: {', '.join(analysis.must_have_features)}
Primary CTA: {analysis.primary_cta}

Tone: {analysis.tone}
Style: {', '.join(analysis.style_keywords)}
Colors: {', '.join(analysis.primary_colors)}

Value Propositions:
{chr(10).join(f"- {vp}" for vp in analysis.value_propositions)}

Create a website structure with appropriate pages and components for each page."""
        self.google_client.set_max_completion_tokens(6000)
        response, usage = self.google_client.call_openai_api_structured(
            system_prompt,
            user_prompt,
            WebsiteStructure,
            model="gemini-2.5-flash"
        )

        print(f"Usage for structure generation: {usage}")
        
        return response
    
    def _validate_structure_consistency(self, structure: WebsiteStructure) -> None:
        """
        Validate that navigation items match pages
        Ensures no orphaned navigation items or missing navigation
        """
        page_paths = {page.path for page in structure.pages}
        nav_paths = {nav.path for nav in structure.navigation}
        
        # Find navigation items with no corresponding page
        missing_pages = nav_paths - page_paths
        
        # Find pages without navigation (excluding home and utility pages)
        utility_paths = {'/', '/404', '/privacy', '/terms', '/sitemap'}
        missing_nav = page_paths - nav_paths - utility_paths
        
        # Report errors
        if missing_pages:
            logger.error(f"[STRUCTURE VALIDATION] ❌ Navigation items without pages: {missing_pages}")
            logger.error("[STRUCTURE VALIDATION] These navigation items link to pages that don't exist!")
            for path in missing_pages:
                nav_item = next((n for n in structure.navigation if n.path == path), None)
                if nav_item:
                    logger.error(f"  - '{nav_item.label}' → {path} (page not found)")
        
        # Report warnings for pages without navigation
        if missing_nav:
            logger.warning(f"[STRUCTURE VALIDATION] ⚠ Pages without navigation items: {missing_nav}")
            logger.warning("[STRUCTURE VALIDATION] Consider adding these pages to navigation")
            for path in missing_nav:
                page = next((p for p in structure.pages if p.path == path), None)
                if page:
                    logger.warning(f"  - '{page.name}' ({path}) has no navigation item")
        
        # Success message
        if not missing_pages and not missing_nav:
            logger.info("[STRUCTURE VALIDATION] ✓ All navigation items match pages perfectly!")
            logger.info(f"[STRUCTURE VALIDATION] {len(structure.pages)} pages, {len(structure.navigation)} nav items")
        
        # Summary
        page_list = [f"{p.name} ({p.path})" for p in structure.pages]
        nav_list = [f"{n.label} → {n.path}" for n in structure.navigation]
        logger.info(f"[STRUCTURE VALIDATION] Pages: {', '.join(page_list)}")
        logger.info(f"[STRUCTURE VALIDATION] Navigation: {', '.join(nav_list)}")
    
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
    
    def _validate_and_fix_files(
        self, 
        files: Dict[str, str], 
        enable_build_validation: bool
    ) -> tuple[Dict[str, str], ValidationResult, int, List[str]]:
        """
        Validate generated files and fix errors with retry mechanism
        
        Args:
            files: Generated files dictionary
            enable_build_validation: Whether to run build tests
            
        Returns:
            Tuple of (fixed_files, validation_result, retry_count, fixed_errors_list)
        """
        retry_count = 0
        fixed_errors = []
        current_files = files.copy()
        
        # Phase 1: Static validation with retry
        logger.info("[VALIDATION] Phase 1: Static validation...")
        
        for attempt in range(settings.max_validation_retries):
            errors, warnings = code_validator.validate_all_files(current_files)
            
            if not errors:
                logger.info(f"[VALIDATION] ✓ Static validation passed (attempt {attempt + 1})")
                break
            
            logger.warning(f"[VALIDATION] Found {len(errors)} errors (attempt {attempt + 1}/{settings.max_validation_retries})")
            
            if attempt < settings.max_validation_retries - 1:
                # Try to fix errors
                logger.info("[VALIDATION] Attempting to auto-fix errors...")
                fixed_files, all_fixed = error_fixer.fix_validation_errors(
                    current_files, 
                    errors, 
                    warnings
                )
                
                if all_fixed:
                    current_files = fixed_files
                    retry_count += 1
                    fixed_errors.extend([f"{e.error_type}: {e.message}" for e in errors])
                    logger.info(f"[VALIDATION] ✓ Auto-fixed all validation errors")
                else:
                    current_files = fixed_files
                    retry_count += 1
                    logger.warning(f"[VALIDATION] ⚠ Partially fixed validation errors")
            else:
                logger.error(f"[VALIDATION] ✗ Failed to fix all validation errors after {settings.max_validation_retries} attempts")
        
        # Create validation result
        validation_errors = [
            ValidationError(
                file_path=e.file_path,
                error_type=e.error_type,
                message=e.message,
                severity=e.severity
            )
            for e in errors
        ]
        
        validation_warnings = [
            ValidationError(
                file_path=w.file_path,
                error_type=w.error_type,
                message=w.message,
                severity="warning"
            )
            for w in warnings
        ]
        
        validation_result = ValidationResult(
            passed=len(errors) == 0,
            errors=validation_errors,
            warnings=validation_warnings,
            total_files_validated=len(current_files)
        )
        
        # Phase 2: Build validation (if enabled)
        if enable_build_validation and len(errors) == 0:
            logger.info("[VALIDATION] Phase 2: Build validation...")
            
            for attempt in range(settings.max_build_retries):
                build_result = build_tester.test_build(
                    current_files,
                    project_name="validation-test"
                )
                
                if build_result.success:
                    logger.info(f"[VALIDATION] ✓ Build validation passed (attempt {attempt + 1})")
                    break
                
                logger.warning(f"[VALIDATION] Build failed with {len(build_result.errors)} errors (attempt {attempt + 1}/{settings.max_build_retries})")
                
                if attempt < settings.max_build_retries - 1:
                    # Try to fix build errors
                    logger.info("[VALIDATION] Attempting to auto-fix build errors...")
                    fixed_files, all_fixed = error_fixer.fix_build_errors(
                        current_files,
                        build_result.errors,
                        build_result.build_output
                    )
                    
                    if all_fixed:
                        current_files = fixed_files
                        retry_count += 1
                        fixed_errors.extend([f"BUILD: {e.message}" for e in build_result.errors])
                        logger.info(f"[VALIDATION] ✓ Auto-fixed all build errors")
                    else:
                        current_files = fixed_files
                        retry_count += 1
                        logger.warning(f"[VALIDATION] ⚠ Partially fixed build errors")
                else:
                    logger.error(f"[VALIDATION] ✗ Failed to fix all build errors after {settings.max_build_retries} attempts")
            
            # Update validation result with build info
            if not build_result.success:
                # Add build errors to validation errors
                for build_error in build_result.errors:
                    validation_result.errors.append(
                        ValidationError(
                            file_path=build_error.file_path,
                            error_type=build_error.error_type,
                            message=build_error.message,
                            severity="error"
                        )
                    )
                validation_result.passed = False
        
        logger.info(f"[VALIDATION] Final result: {len(validation_result.errors)} errors, {len(validation_result.warnings)} warnings")
        
        return current_files, validation_result, retry_count, fixed_errors
    
    def _generate_page_files(self, structure: WebsiteStructure, analysis: BusinessAnalysis) -> Dict[str, str]:
        """Generate page component files"""
        
        files = {}
        
        for page in structure.pages:
            print(f"Generating page: {page.name}")
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
        system_prompt = self._create_page_generation_system_prompt1()
        
        # Create user prompt with context
        user_prompt = self._create_page_generation_user_prompt1(
            page=page,
            structure=structure,
            analysis=analysis,
            available_ui_components=available_ui_components,
            available_section_components=available_section_components
        )
        
        # Call LLM to generate page and components
        logger.info(f"[PAGE GEN] Calling LLM for page generation...")
        # self.openai_client.set_max_completion_tokens(16000)
        # response, usage = self.openai_client.call_openai_api_structured(
        #     system_prompt,
        #     user_prompt,
        #     PageGenerationResponse,
        #     model="o4-mini"
        # )

        self.google_client.set_max_completion_tokens(16000)
        response, usage = self.google_client.call_openai_api_structured(
            system_prompt,
            user_prompt,
            PageGenerationResponse,
            model="gemini-2.5-pro"
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
        # ui_components_list = []
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
    

    def _get_all_ui_components_usage_guide(self) -> str:
        """
        Get usage guide for all available UI components
        
        Returns:
            Formatted string with all UI component usage details
        """
        try:
            ui_components_path = Path("backend/app/templates/ui_components_slim.json")

            if not ui_components_path.exists():
                return "⚠️ UI components reference not available"

            with open(ui_components_path, 'r', encoding='utf-8') as f:
                ui_components_data = json.load(f)

            # Expecting an array of entries with component_name, description, usage
            if not isinstance(ui_components_data, list) or not ui_components_data:
                return "⚠️ No UI components found in reference"

            usage_guide = "AVAILABLE UI COMPONENTS REFERENCE:\n"
            usage_guide += "=" * 50 + "\n\n"

            for item in ui_components_data:
                component_name = item.get("component_name", "")
                description = item.get("description", "")
                usage = item.get("usage", "")

                if not component_name:
                    continue

                usage_guide += f"COMPONENT: {component_name}\n"
                if description:
                    usage_guide += f"Description: {description}\n\n"
                if usage:
                    usage_guide += f"Usage Example:\n{usage}\n"

                usage_guide += "\n" + "-" * 30 + "\n\n"

            return usage_guide
            
        except Exception as e:
            logger.error(f"[UI COMPONENT] Error loading UI components reference: {str(e)}")
            return "⚠️ Error loading UI components reference"

    def _create_page_generation_system_prompt(self) -> str:
        """Create system prompt for page generation"""
        
        # Get formatted list of safe icons
        safe_icons_list = format_icons_for_prompt()
        
        return f"""You are an expert React developer tasked with generating production-ready web application components. Your code must be professional, maintainable, and error-free.

Make use of the following UI components reference to generate the page:
{self._get_all_ui_components_usage_guide()}

CRITICAL VALIDATION - READ THIS FIRST ⚠️⚠️⚠️

Your code MUST pass TypeScript compilation with ZERO errors and ZERO warnings.
The following errors will cause IMMEDIATE BUILD FAILURE:

🚫 FORBIDDEN ERROR #1: Unused Variables/Props in Destructuring
   ❌ ERROR: const bgClass = ...; // Declared but NEVER used in JSX
   ❌ ERROR: experienceIcon: ExperienceIcon // Destructured prop but NEVER used
   ❌ ERROR: {{ title, unused, data }}: Props // 'unused' is never referenced
   ✅ FIX: Either USE the variable in your JSX OR remove it from destructuring
   
   Example of the error:
   export function Biography({{ experienceIcon: ExperienceIcon }}: Props) {{
     return <div>...</div>  // ExperienceIcon is NEVER used! ❌
   }}
   
   Fixed version:
   export function Biography({{ experienceIcon: ExperienceIcon }}: Props) {{
     return <div><ExperienceIcon className="..." /></div>  // Now it's used ✅
   }}
   OR just remove it:
   export function Biography({{ }}: Props) {{  // Don't destructure unused props ✅
     return <div>...</div>
   }}

🚫 FORBIDDEN ERROR #2: Missing Required Props
   ❌ ERROR: <Cta title="..." ctaLabel="..." /> // Missing required 'description' prop!
   ✅ FIX: Check component interface and pass ALL required props
   
   Example of the error:
   interface CtaProps {{
     title: string;
     description: string;  // REQUIRED (no ?)
     ctaLabel?: string;    // Optional (has ?)
   }}
   <Cta title="Get Started" ctaLabel="Click" />  // ❌ Missing description!
   
   Fixed version:
   <Cta 
     title="Get Started" 
     description="Join us today"  // ✅ All required props provided
     ctaLabel="Click" 
   />

🚫 FORBIDDEN ERROR #3: Invalid Icon Names
   ❌ ERROR: <Building className="..." />  // 'Building' doesn't exist!
   ❌ ERROR: import {{ Building }} from 'lucide-react'  // Will fail!
   ✅ FIX: Use Building2 from the verified icon list below

🚫 FORBIDDEN ERROR #4: Unused Imports
   ❌ ERROR: import {{ Camera, Heart, Star }} from 'lucide-react'; // Only using Heart
   ✅ FIX: import {{ Heart }} from 'lucide-react';  // Only import what's used

⚠️⚠️⚠️ EVERY SINGLE ONE of these errors will cause build failure ⚠️⚠️⚠️

BEFORE generating ANY code, you MUST verify:
✓ Every icon name exists in the verified list below (search it!)
✓ Every variable/prop is actually USED in the return/JSX
✓ Every import is actually USED in the component
✓ Every component receives ALL required props (check the interface!)
✓ Remove any unused code (props, variables, imports)

MANDATORY VALIDATION STEPS:
Step 1: When you destructure props {{ a, b, c }}, verify a, b, and c ALL appear in your JSX
Step 2: When you write const x = ..., verify x appears in your JSX  
Step 3: When you use <Component />, check Component's interface for required props
Step 4: When you import an icon, verify it's in the safe icons list AND used in JSX

Your task is to generate a complete page component with proper structure, imports, and styling using:
TECHNOLOGY STACK:
- React 19 with TypeScript (strict mode)
- Tailwind CSS for styling
- shadcn/ui components (built on Radix UI)
- Lucide React icons (CRITICAL: ONLY use verified icons from the list below)
- Modern React patterns and hooks
- Proper TypeScript types and interfaces
- Use working and functioning unsplash for images, for example: https://images.unsplash.com/photo-...
- CRITICAL: Use React Router's Link component for internal navigation
  * Import: import {{ Link }} from 'react-router-dom'
  * Internal routes: <Link to="/services">Services</Link>
  * External links: <a href="https://..." target="_blank">External</a>
  * DO NOT use <a href="/path"> for internal navigation
- Vite for building the website

{safe_icons_list}

🔴 ICON VALIDATION - ZERO TOLERANCE 🔴
- ONLY use icon names from the list above
- Icon names are CASE-SENSITIVE and EXACT
- Common mistakes to AVOID:
  ❌ Building (doesn't exist) → ✅ Building2
  ❌ Circle (doesn't exist) → ✅ Circle or CircleDot
  ❌ User (use cautiously) → ✅ UserCircle or UserRound
- Before using ANY icon, CTRL+F search the list above to verify it exists
- Using invalid icons will cause: error TS2304: Cannot find name 'IconName'

TYPESCRIPT VALIDATION RULES (CRITICAL - ZERO TOLERANCE):

1. **ONLY IMPORT WHAT YOU USE**
   - WRONG: import {{ Camera, Heart, Star }} from 'lucide-react'  // Then only using Heart ❌
   - CORRECT: import {{ Heart }} from 'lucide-react'  // Only import what's actually used ✓
   - Every import MUST be used in the component code
   - Remove ANY unused imports before generating

2. **NO UNDEFINED TYPES**
   - WRONG: icon: LucideIcon  // This type doesn't exist ❌
   - CORRECT: icon: React.ReactNode  // Or string if passing icon name ✓
   - Do NOT invent TypeScript types that don't exist
   - Common valid types: string, number, boolean, React.ReactNode, React.FC, JSX.Element

3. **NO UNUSED VARIABLES**
   - WRONG: const testimonialsData = [...]; // Then never using it ❌
   - CORRECT: const testimonialsData = [...]; <Testimonials testimonials={{testimonialsData}} /> ✓
   - Every variable declared MUST be used
   - If you declare data, pass it to the component

4. **VALIDATE BEFORE GENERATING**
   Before outputting code, check:
   - [ ] Every import is used in the component
   - [ ] Every variable is used in the JSX
   - [ ] All types exist (no LucideIcon, no custom undefined types)
   - [ ] All icon imports from lucide-react are actually rendered in JSX
   
5. **COMMON ERRORS TO AVOID**
   ❌ Importing icons you don't use: import {{ X, Y, Z }} when only using Y
   ❌ Declaring data variables you don't pass to components
   ❌ Using undefined TypeScript types like LucideIcon
   ❌ Importing React when not needed (React 19 auto-imports)

6. **ICON USAGE PATTERN**
   CORRECT Pattern:
   ```tsx
   import {{ Heart }} from 'lucide-react'  // Only import if used
   
   export function MyComponent() {{
     return <Heart className="h-5 w-5" />  // Actually use it
   }}
   ```
   
   WRONG Pattern:
   ```tsx
   import {{ Heart, Star, Camera }} from 'lucide-react'  // Importing unused icons
   
   export function MyComponent() {{
     return <Heart className="h-5 w-5" />  // Only Heart is used!
   }}
   ```

7. **DATA VARIABLE PATTERN**
   CORRECT Pattern:
   ```tsx
   const services = [/* data */]
   return <Services items={{services}} />  // Use the variable
   ```
   
   WRONG Pattern:
   ```tsx
   const services = [/* data */]
   return <div>Hello</div>  // Variable never used!
   ```

8. **UNUSED VARIABLE PREVENTION**
   This is one of the MOST COMMON errors. Follow these rules:
   
   ❌ WRONG - Variable declared but never used:
   ```tsx
   export function CallToAction({{ backgroundColor }}: Props) {{
     const bgClass = backgroundColor === 'black' ? 'bg-black' : `bg-${{backgroundColor}}`;
     // bgClass is NEVER used in the return!
     return <div className="bg-blue-500">...</div>  // ERROR: bgClass unused
   }}
   ```
   
   ✅ CORRECT - Use the variable:
   ```tsx
   export function CallToAction({{ backgroundColor }}: Props) {{
     const bgClass = backgroundColor === 'black' ? 'bg-black' : `bg-${{backgroundColor}}`;
     return <div className={{bgClass}}>...</div>  // bgClass is USED ✓
   }}
   ```
   
   ✅ ALSO CORRECT - Don't declare it if you won't use it:
   ```tsx
   export function CallToAction({{ backgroundColor }}: Props) {{
     // Use the prop directly instead
     return <div className={{backgroundColor === 'black' ? 'bg-black' : `bg-${{backgroundColor}}`}}>...</div>
   }}

    Even if a prop is in your interface, don't destructure it if you won't use it.
   
   ❌ WRONG - Destructuring unused prop:
   ```tsx
   interface BiographyProps {{
     imageUrl: string;
     title: string;
     experienceIcon: React.ReactNode;  // Defined in interface
   }}
   
   export function Biography({{ imageUrl, title, experienceIcon: ExperienceIcon }}: BiographyProps) {{
     // ExperienceIcon is NEVER used in the component!
     return <div>{{title}}</div>  // ERROR: ExperienceIcon unused ❌
   }}
   ```
   
   ✅ CORRECT - Only destructure what you use:
   ```tsx
   export function Biography({{ imageUrl, title }}: BiographyProps) {{
     // Only destructure props you actually use
     return <div>{{title}}</div>  // ✓
   }}
   ```
   
   ✅ OR USE IT:
   ```tsx
   export function Biography({{ imageUrl, title, experienceIcon: ExperienceIcon }}: BiographyProps) {{
     return (
       <div>
         {{title}}
         {{ExperienceIcon}}  // Now it's used! ✓
       </div>
     )
   }}
   ```
   
   RULE: Only destructure props you will actually use in the component body.

9. **REQUIRED PROPS MUST BE PROVIDED**
   When calling a component, provide ALL required props (non-optional props).
   
   ❌ WRONG - Missing required prop:
   ```tsx
   // Cta.tsx defines:
   interface CtaProps {{
     title: string;
     description: string;  // REQUIRED (no ?)
     ctaLabel: string;
   }}
   
   // Page.tsx uses:
   <Cta 
     title="Join Us" 
     ctaLabel="Sign Up"
     // Missing 'description' prop! ❌
   />
   ```
   
   ✅ CORRECT - Provide all required props:
   ```tsx
   <Cta 
     title="Join Us" 
     description="Start your journey today"  // ✓ All required props
     ctaLabel="Sign Up"
   />
   ```
   
   ✅ OR MAKE IT OPTIONAL in the component:
   ```tsx
   // Cta.tsx - make optional if it should be:
   interface CtaProps {{
     title: string;
     description?: string;  // Optional with ?
     ctaLabel: string;
   }}
   
   export function Cta({{ title, description = "Default description", ctaLabel }}: CtaProps) {{
     return <div>{{description}}</div>  // Has default value
   }}
   ```
   
   RULE: Check the component interface - if a prop has no `?`, you MUST provide it.
   ```
   
   RULE: If you declare a variable with const/let/var, it MUST appear in your JSX return.
CRITICAL: You MUST ONLY use icons from the above list. Using any other icon will cause build errors.

IMPORTANT RULES:
1. **Page Component**: Generate a clean, functional React component for the requested page. Ensure you build the components first before building the page. Making use of the properties in the components in the page.
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
   - CRITICAL: Remove ALL unused imports. Every single import MUST be used in the code.
   - CRITICAL: Do NOT use undefined types like 'LucideIcon'. Stick to valid TypeScript types.
   - CRITICAL: Every variable declared MUST be used. No unused constants or data variables.
   - ENSURE that All properties called in the code generated are defined in the section and ui components' file found in the @/components/ and @/components/ui/ directories
   An Example:
   If the page or section component uses the ui button defined as  "<button
      className={{`inline-flex items-center justify-center px-4 py-2 bg-black text-white hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500`}}
      {{...props}}
    >",
    Then it must be used as "<Button className={{ valid class name values }} {{ valid props}} />" in the page or section component
   
6. **CRITICAL - Props Consistency and Matching**:
   - When calling a component, prop names MUST EXACTLY MATCH the component's interface
   - If component defines some value say `items` prop, call it with `items={{data}}`, NOT `styles={{data}}` or any other prop name not defined in the component
   - The same rule applies for other props defined in the section components and the ui components
   - **CRITICAL**: Check the component's interface BEFORE using it - look for props without `?` (those are REQUIRED)
   - Define realistic test data (3-5 items) for all array/list props
   - Pass ALL required props with correct names and values
   - Example: Component has `items?: Item[]` → Page must pass `<Component items={{myItems}} />`
   
   **HOW TO CHECK IF A PROP IS REQUIRED:**
   ```tsx
   interface ComponentProps {{
     title: string;        // REQUIRED - no question mark
     description: string;  // REQUIRED - no question mark
     ctaLabel?: string;    // OPTIONAL - has question mark
   }}
   ```
   When using this component, you MUST provide title and description:
   ```tsx
   <Component title="Hello" description="World" />  // ✅ All required props
   <Component title="Hello" />  // ❌ Missing required 'description'
   ```
7. **Style Consistency**: Use Tailwind CSS classes and follow modern UI/UX principles
8. **TypeScript**: All components must have proper TypeScript types and interfaces
9. **Responsive Design**: Ensure all components are mobile-first and responsive
10. **Accessibility**: Follow ARIA standards and semantic HTML
11. **CRITICAL - No Duplicates**: Never generate the same component twice. Check available components first.
12. **CRITICAL - Icon Usage**: Only use icons from the verified list above. No exceptions.
13. ENSURE TO FILL ALL VALUES IN THE "props" WITH REAL VALUES, NOT JUST EMPTY STRINGS OR NUMBERS.

CRITICAL: PROP MATCHING RULES (NO ERRORS)
RULE 1: PROP NAMES MUST MATCH COMPONENT INTERFACE
When using a component, prop names must EXACTLY match the component's TypeScript interface.

WRONG Examples (WILL CAUSE ERRORS):
- Component has `items` → Page uses `<Features styles={{data}} />` ❌
- Component has `testimonials` → Page uses `<Testimonials reviews={{data}} />` ❌
- Component has `members` → Page uses `<Team people={{data}} />` ❌

CORRECT Examples:
- Component has `items` → Page uses `<Features items={{data}} />` ✓
- Component has `testimonials` → Page uses `<Testimonials testimonials={{data}} />` ✓
- Component has `members` → Page uses `<Team members={{data}} />` ✓

RULE 2: ALWAYS DEFINE TEST DATA
Every array/list prop must have 3-5 realistic items defined in the page:
```tsx
const services = [
  {{ id: '1', title: 'Service 1', description: 'Description 1' }},
  {{ id: '2', title: 'Service 2', description: 'Description 2' }},
  {{ id: '3', title: 'Service 3', description: 'Description 3' }}
]
<Features items={{services}} />  // Pass with correct prop name
```

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


MANDATORY PRE-GENERATION CHECKLIST
Before generating code, you MUST verify EVERY item below:

ICON VALIDATION:
□ Every icon I'm using appears in the verified icons list above
□ Icon names are spelled EXACTLY as shown (Building2 not Building)
□ All icons are imported from lucide-react
□ All imported icons are actually rendered in JSX

VARIABLE VALIDATION:
□ Every const/let/var declared is used in the return statement
□ No unused variables (check: does bgClass/userData/etc appear in JSX?)
□ If declaring a variable, it MUST be used - otherwise remove it

PROPS VALIDATION:
□ Only destructure props that are actually used in the component
□ If experienceIcon is destructured, it MUST be used in JSX
□ When calling components, ALL required props are provided
□ Check component interfaces - props without '?' are REQUIRED

IMPORT VALIDATION:
□ Every import is actually used in the component
□ No unused icon imports (Camera imported but never rendered)
□ Import style matches export style (named vs default)

TYPESCRIPT VALIDATION:
□ No undefined types (no LucideIcon, no invented types)
□ All props interfaces are defined
□ No 'any' types used

EXPORT VALIDATION:
□ Each component file has EXACTLY ONE export (named OR default, not both)
□ Section components use named exports
□ Pages use default exports


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
- Have ZERO unused imports (all imports must be used)
- Have ZERO unused variables (all declared variables must be used)
- Use ONLY defined TypeScript types (no LucideIcon or other undefined types)
- All lucide-react icon imports must be rendered in JSX


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
- `new_components`: Array of any new components needed (both section and UI components)

⚠️⚠️⚠️ FINAL WARNING BEFORE GENERATING ⚠️⚠️⚠️

Before you output anything, manually verify:
1. Every icon name is from the verified list (CTRL+F to check)
2. Every variable (const/let) is used in the JSX return
3. Every import is used in the code
4. Only destructure props you actually use (no unused ExperienceIcon, etc.)
5. When calling components, provide ALL required props (check for missing description, etc.)
6. No undefined TypeScript types

Common errors that will cause IMMEDIATE BUILD FAILURE:
- Using "Building" instead of "Building2"
- Declaring "const bgClass" and never using it
- Importing "Camera, Heart, Star" but only using "Heart"
- Using type "LucideIcon" which doesn't exist
- Destructuring "experienceIcon: ExperienceIcon" but never using ExperienceIcon
- Calling <Cta title="..." ctaLabel="..." /> without required 'description' prop

If you generate code with these errors, the entire build will fail. Triple-check before outputting."""


    def _create_page_generation_system_prompt1(self) -> str:
        """Create concise system prompt for page generation - captures all critical validation rules"""
        
        # Get formatted list of safe icons
        safe_icons_list = format_icons_for_prompt()
        
        return f"""Expert React 19 + TypeScript developer. Generate production-ready page + missing components.

UI COMPONENTS REFERENCE:
{self._get_all_ui_components_usage_guide()}

TECH STACK: React 19, TypeScript (strict), Tailwind, shadcn/ui, lucide-react, Vite, React Router (Link for internal nav)
IMAGES: Use Unsplash URLs (https://images.unsplash.com/...)

🚫 ZERO-TOLERANCE BUILD FAILURES (any violation = build fails):

1. UNUSED CODE
   ❌ const x = ...; return <div/> // x never used
   ❌ import {{ A, B }} from '...'; return <A/> // B unused
   ❌ ({{ prop }}: Props) => <div/> // prop never used
   ✅ Only declare/import/destructure what you USE in JSX

2. REQUIRED PROPS
   ❌ <Cta title="x" /> // Missing required 'description'
   ✅ Check interface - props without ? are REQUIRED
   ✅ Prop names must EXACTLY match interface

3. ICONS
   ❌ Building, Circle, User (don't exist)
   ✅ Only use icons from list below (Building2, CircleDot, UserCircle)
   ✅ Icons are CASE-SENSITIVE
   
{safe_icons_list}

4. TYPES
   ❌ icon: LucideIcon (undefined type)
   ✅ Use: string, number, boolean, React.ReactNode, JSX.Element

5. EXPORTS/IMPORTS
   ❌ export function X(); export default X; (duplicate)
   ✅ Section components: export function Name() {{}} → import {{ Name }}
   ✅ UI components: export const name → import {{ name }}
   ✅ Pages: export default function Page() {{}} → import Page

PRE-GENERATION CHECKLIST:
□ Every variable/import/prop is used in JSX
□ All required props provided with correct names
□ All icons exist in verified list and are rendered
□ No undefined types (no LucideIcon)
□ One export per file, imports match export style

STRUCTURE:
- Sections: src/components/<Name>.tsx (named export)
- UI: src/components/ui/<name>.tsx (named export)
- Pages: default export
- Define 3-5 realistic test data items for array props
- Fill all prop values (no empty strings)

QUALITY: Responsive, accessible, semantic HTML, no 'any' types, modern patterns

OUTPUT JSON:
{{
  "page_content": "complete page (default export)",
  "new_components": [{{ "path": "...", "content": "..." }}]
}}

Common errors causing build failure:
• Using "Building" instead of "Building2"
• Declaring const bgClass but never using it in className
• Importing Camera, Heart, Star but only rendering Heart
• Using type LucideIcon (doesn't exist)
• Destructuring experienceIcon but never using it
• Missing required description prop on Cta component

Verify EVERY item in checklist before generating."""

    def _create_page_generation_system_prompt2(self) -> str:
        """Create concise system prompt for page generation - captures all critical validation rules"""
        
        # Get formatted list of safe icons
        safe_icons_list = format_icons_for_prompt()
        
        return f"""Developer: You are an expert React + TypeScript developer. Your task is to generate a production-ready page component for a website and any needed missing section or UI components.


Component & Tech Stack:
- React 19 (TypeScript, strict mode), Tailwind CSS, shadcn/ui (Radix), lucide-react icons (use only the verified CASE-SENSITIVE icons), Vite.
- Use Unsplash image URLs (https://images.unsplash.com/...) and <a href="https://..."> for external links.
- Use React Router's <Link to="/route"> for internal navigation (import {{ Link }} from 'react-router-dom').

Hard Build Gates (Zero Tolerance):
- Code must compile with zero TypeScript errors or warnings.
- No unused variables, imports, or destructured props.
- All required props (non-optional in interface) must be provided and prop names must match interfaces exactly.
- Only import and use icons from the verified list ({safe_icons_list}). Every icon import must be rendered in JSX.
- No undefined/invalid types (e.g. no 'LucideIcon'), and no 'any' usage. Use standard types: string, number, boolean, React.ReactNode, JSX.Element.
- Each variable/constant must appear in JSX (no unused data).

Component Conventions:
- Section components in src/components/<Name>.tsx, use named exports.
- UI components in src/components/ui/<name>.tsx, follow shadcn/ui pattern, use named exports.
- Pages use default exports only.
- One export style per file; import style must match export style; no mixed or duplicate exports.

Props & Data:
- Prop names must match the interface exactly.
- For list/array props, create realistic test data (3-5 items) and provide via the correct prop name.
- All prop values must be real (not empty/defaults).
- Only destructure/use what you actually render or use in JSX.

UI COMPONENTS REFERENCE:
{self._get_all_ui_components_usage_guide()}

Checklist Before Output:
- Every variable appears in JSX and is used.
- No unused props, variables, or imports.
- All imported icons are rendered in JSX and exist in the verified list.
- All required props are provided.

Quality:
- Code is accessible, responsive, and semantic.
- Follows modern React and TypeScript patterns.
- Maintainable and well-typed code.

If any required section or UI component does not exist, define it in "new_components" (with path and code). Do not duplicate components that already exist.

OUTPUT JSON FORMAT:
- page_content: Complete, default-exported page component code
- new_components: Array of new section/UI components, each with path and contents

Generate the required code now according to these rules.
"""



    
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
        
        prompt = f"""Generate a production-ready React page component.

PAGE
- Name: {page.name}
- Route: {page.path}
- Title: {page.title}
- Description: {page.description}

BUSINESS CONTEXT
- Type: {analysis.business_type}
- Industry: {analysis.industry}
- Audience: {analysis.target_audience}
- Tone: {analysis.tone}
- Primary CTA: {analysis.primary_cta}
- Color Scheme: {structure.color_scheme}

REQUIRED SECTIONS
{chr(10).join(component_details)}

AVAILABLE UI COMPONENTS (@/components/ui/<name>)
{', '.join(available_ui_components) if available_ui_components else 'None yet - generate as needed'}

AVAILABLE SECTION COMPONENTS (@/components/<Name>)
{', '.join(available_section_components) if available_section_components else 'None yet - generate as needed'}

WEBSITE NAV
{chr(10).join(nav_items) if nav_items else 'None - Single page website'}

TASK
- Build a complete page for "{page.name}" by importing and using section components.
- If a needed section/UI component is missing, create it and include in new_components (no duplicates).
- Do not modify existing UI components; reuse them as-is.

HEADER/FOOTER
- Implement <Header /> and <Footer />; usage is without props.
- Define their values (brand, nav, cta, etc.) internally, using the website navigation above.

STRICT RULES
- Prop names must exactly match component interfaces; provide all required props (no '?').
- Only destructure props you actually use.
- Define realistic data (3–5 items) for list props and pass with the correct name (e.g., items={{{{data}}}}).
- Only use verified safe lucide icons (provided in system prompt); import only icons you render.
- No unused variables or imports.
- Section components: named export; UI components: named export; pages: default export.
- One export style per file; imports must match export style.
- TypeScript strict; no 'any'. Accessible, responsive, semantic HTML.
- Use Tailwind; use <a> for links.

OUTPUT (JSON)
- page_content: complete page component (default export).
- new_components: any created components (path + contents).

Generate now."""
        return prompt

    def _create_page_generation_user_prompt1(
        self,
        page: PageStructure,
        structure: WebsiteStructure,
        analysis: BusinessAnalysis,
        available_ui_components: List[str],
        available_section_components: List[str]
    ) -> str:
        """Concise user prompt for page generation"""
        
        # Format component requirements
        components_list = [
            f"  • {comp.name} ({comp.type}): {json.dumps({item.key: item.value for item in comp.props})}"
            for comp in page.components
        ]
        
        # Format navigation
        nav_list = [f"  • {nav.label} → {nav.path}" for nav in structure.navigation]
        
        return f"""PAGE: {page.name} ({page.path})

{page.description}

CONTEXT
Business: {analysis.business_type} | Industry: {analysis.industry}
Audience: {analysis.target_audience} | Tone: {analysis.tone}
CTA: {analysis.primary_cta} | Colors: {structure.color_scheme}

SECTIONS NEEDED
{chr(10).join(components_list)}

AVAILABLE COMPONENTS
UI (@/components/ui/): {', '.join(available_ui_components) or 'None - create as needed'}
Sections (@/components/): {', '.join(available_section_components) or 'None - create as needed'}

NAVIGATION
{chr(10).join(nav_list) if nav_list else '  • Single page (no nav)'}

TASK
1. Build page using/creating section components
2. Add missing components to new_components (no duplicates)
3. <Header /> and <Footer /> usage: no props; define values internally using nav above
4. Reuse existing UI components as-is

CRITICAL
✓ Prop names match interfaces exactly; provide ALL required props
✓ Only destructure props you use
✓ 3-5 realistic test items for arrays; pass with correct name (items={{{{data}}}})
✓ Use verified icons only; import only what you render
✓ No unused variables/imports
✓ Sections & UI: named export | Pages: default export
✓ TypeScript strict, no 'any', responsive, accessible

OUTPUT JSON: {{"page_content": "...", "new_components": [...]}}"""


# Create singleton instance
react_website_generator = ReactWebsiteGenerator()

