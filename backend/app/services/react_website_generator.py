"""
React Website Generator Service
Generates a complete React/TypeScript website structure based on business analysis.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from functools import lru_cache
from traceback import print_tb
from typing import Dict, Any, List, Union, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from app.config import settings
from app.services.business_analyzer import BusinessAnalyzer, BusinessAnalysis
from app.services.prompt_open_ai import PromptOpenAI
from app.services.react_models import (
    PageComponent, PageStructure, WebsiteStructure, PageGenerationResponse,
    ValidationResult, ValidationError, BuildTestResult, GenerationResult
)
from app.services.react_file_manager import react_file_manager
from app.services.validators.icon_validator import get_safe_icons
from app.services.validators.code_validator import code_validator, fix_lucide_icons_in_content, CodeValidationError
from app.services.validators.error_fixer import error_fixer
from app.services.validators.build_tester import build_tester, BuildError
import re
import importlib.util
import sys

# Import StructureGenerator from pre-generation folder (hyphen in folder name requires special handling)
spec = importlib.util.spec_from_file_location(
    "structure_generator",
    str(Path(__file__).parent / "pre-generation" / "structure_generator.py")
)
structure_generator_module = importlib.util.module_from_spec(spec)
sys.modules["structure_generator"] = structure_generator_module
spec.loader.exec_module(structure_generator_module)
StructureGenerator = structure_generator_module.StructureGenerator

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
    # print(f"[FILE WRITER] Writing {len(files)} files to {base_dir.absolute()}")
    
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
            # print(f"[FILE WRITER] ✓ Written: {relative_path}")
            
        except Exception as e:
            logger.error(f"[FILE WRITER] ✗ Failed to write {relative_path}: {str(e)}")
            # print(f"[FILE WRITER] ✗ Failed to write {relative_path}: {str(e)}")
            raise
    
    logger.info(f"[FILE WRITER] ✓ Successfully written all {len(written_files)} files to disk")
    # print(f"[FILE WRITER] ✓ Successfully written all {len(written_files)} files to disk")
    logger.info(f"[FILE WRITER] Location: {base_dir.absolute()}")
    
    return written_files


class ReactWebsiteGenerator:
    """Generates complete React website structure from user prompt"""

    def __init__(self):
        self.openai_client = PromptOpenAI()
        self.google_client = PromptOpenAI(is_google=True)
        self.anthropic_client = PromptOpenAI(is_anthropic=True)
        self.business_analyzer = BusinessAnalyzer()
        self.structure_generator = StructureGenerator()
        # self.design_system_generator = DesignSystemGenerator()  # NEW
        # self.visual_optimizer = VisualHierarchyOptimizer()      # NEW
        # self.pattern_library = ComponentPatternLibrary()        # NEW
        # self.quality_scorer = WebsiteQualityScorer()           # NEW

    
    
    def generate_website_structure(
        self,
        prompt: str,
        enable_build_validation: Optional[bool] = None,
        enable_animations: Optional[bool] = None,
        cost_tracker=None,
        progress_callback=None,
        media_context: Optional[str] = None,
        design_context: Optional[str] = None,
        design_extraction=None,
        design_fidelity: str = "none",
    ) -> Dict[str, Any]:
        """
        Main entry point: Generate complete React website from prompt with validation
        
        Args:
            prompt: User's website description
            enable_build_validation: Whether to run actual build tests (None = use config default)
            enable_animations: Whether to include animations (None = use config default)
            cost_tracker: Optional CostTracker instance to track AI costs
            progress_callback: Optional async callback function(progress: int, stage: str, stage_message: str) to update progress
        
        Returns a dictionary containing:
        - website_structure: Complete website structure
        - business_analysis: Original business analysis
        - files: Dictionary of file paths to file contents
        - validation: Validation results
        - build_test: Build test results (if enabled)
        - retry_count: Number of retry attempts made
        - fixed_errors: List of errors that were auto-fixed
        - generation_time: Total generation time
        - cost_breakdown: Cost breakdown if cost_tracker provided
        """
        start_time = time.time()
        
        # Use config defaults if not specified
        if enable_build_validation is None:
            enable_build_validation = settings.enable_build_validation
        if enable_animations is None:
            enable_animations = settings.enable_animations_default
        
        logger.info("[REACT GEN] Starting React website generation with validation...")
        
        # Step 1: Analyze business requirements
        logger.info("[REACT GEN] Analyzing business requirements...")
        analysis_prompt = prompt
        if media_context:
            analysis_prompt = f"{analysis_prompt}\n\n{media_context}"
        if design_context:
            analysis_prompt = f"{analysis_prompt}\n\n{design_context}"
        business_analysis = self.business_analyzer.generate_business_analysis(analysis_prompt, cost_tracker=cost_tracker)
        # print(f"Business analysis: \n{business_analysis.model_dump_json(indent=2)}")

        # Re-attach the media/design blocks verbatim: business analysis SUMMARIZES
        # the prompt, which would mangle the exact asset URLs, hex colors and font
        # names that must reach page generation (page prompts include analysis.prompt).
        if media_context:
            business_analysis.prompt = f"{business_analysis.prompt}\n\n{media_context}"
        if design_context:
            business_analysis.prompt = f"{business_analysis.prompt}\n\n{design_context}"

        # Step 2: Generate website structure
        logger.info("[REACT GEN] Generating website structure...")
        website_structure = self.structure_generator.generate_structure(business_analysis, cost_tracker=cost_tracker, design_context=design_context)

        # print(f"Website structure: \n{website_structure.model_dump_json(indent=2)}")
        
        # Fix home page path
        logger.info("[REACT GEN] Fixing home page path...")
        self._fix_home_page_path(website_structure)
        
        # Validate navigation matches pages
        if website_structure.page_count > 1: # might need to remove if it doesnt skip for single page websites
            logger.info("[REACT GEN] Validating structure consistency...")
            self._validate_structure_consistency(website_structure)
        
        # Update progress: Structure generated, now creating components
        if progress_callback:
            try:
                progress_callback(
                    progress=50,
                    stage="creating_components",
                    stage_message="Building React components and bringing your design to life..."
                )
            except Exception as e:
                logger.warning(f"[REACT GEN] Failed to update progress: {str(e)}")
        
        # Debug: Write schema and structure to files
        # with open('/tmp/website_structure_schema.json', 'w') as f:
        #     json.dump(website_structure.model_json_schema(), f, indent=2)
        
        # with open('/tmp/website_structure_data.json', 'w') as f:
        #     json.dump(website_structure.model_dump(), f, indent=2)
        
        # logger.info("[REACT GEN] ✓ Debug files written to /tmp/website_structure_*.json")
        
        # Step 3: Generate file contents
        logger.info("[REACT GEN] Generating React files...")
        logger.info(f"[REACT GEN] Animations enabled: {enable_animations}")

        files = self._generate_all_files(
            website_structure, business_analysis, enable_animations, cost_tracker=cost_tracker,
            design_extraction=design_extraction, design_fidelity=design_fidelity
        )

        # Deterministic nav-link repair: rewrite bad Header/Footer anchors
        # (e.g. <a href="#features">Shop</a>) to <Link to="/shop"> so every
        # page is reachable. Runs before build validation so the rewritten
        # code is what gets verified.
        try:
            from app.services.validators.nav_link_validator import validate_and_fix_nav_links
            fixed_nav_files, nav_changes = validate_and_fix_nav_links(files, website_structure.model_dump())
            files.update(fixed_nav_files)
            if nav_changes:
                logger.info(f"[REACT GEN] Nav link validator repaired {len(nav_changes)} link(s)")
        except Exception as e:
            logger.warning(f"[REACT GEN] Nav link validation failed (non-fatal): {e}")

        # Update progress: Components created, now building pages
        if progress_callback:
            try:
                progress_callback(
                    progress=70,
                    stage="building_pages",
                    stage_message="Assembling pages and layouts for your website..."
                )
            except Exception as e:
                logger.warning(f"[REACT GEN] Failed to update progress: {str(e)}")
        
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
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        website_name = website_structure.name.lower().replace(" ", "-")
        # output_path = f"app/data/generated_sites/{website_name}_{timestamp}"
        
        # written_files = write_files_to_disk(files, output_path)
        
        result = {
            "name": website_name,
            "website_structure": website_structure.model_dump(),
            "business_analysis": business_analysis.model_dump(),
            "files": files,
            "validation": validation_result.model_dump(),
            "build_test": validation_result.model_dump() if hasattr(validation_result, 'build_test') else None,
            "retry_count": retry_count,
            "fixed_errors": fixed_errors,
            "generation_time": generation_time
        }
        
        # Add cost breakdown if cost_tracker was used
        if cost_tracker:
            cost_breakdown = cost_tracker.get_breakdown()
            result["cost_breakdown"] = cost_breakdown
            logger.info(f"[REACT GEN] {cost_tracker.get_summary_string()}")
        
        return result
    
    def _is_home_page(self, name: str) -> bool:
        """
        Check if a page name represents a home page
        Handles various forms like 'home', 'home_page', 'homePage', 'Home Page', etc.
        """
        if not name:
            return False
        
        # Convert to lowercase and remove spaces/underscores for comparison
        normalized_name = name.lower().replace(" ", "").replace("_", "").replace("-", "")
        
        # Check for various home page patterns
        home_patterns = [
            "home",
            "homepage", 
            "homepage",
            "main",
            "index",
            "landing",
            "start"
        ]
        
        return normalized_name in home_patterns


    def _fix_home_page_path(self, website_structure: WebsiteStructure) -> Dict[str, Any]:
        """
        Fix Home page path from '/home' or any other path to '/' in the website structure (in place)
        Handles various forms of home page names like 'home', 'home_page', 'homePage', 'Home Page', etc.
        
        Args:
            website_structure: Website structure data dictionary (modified in place)
            
        Returns:
            dict: Dictionary containing:
                - fixed: bool - Whether any fixes were made
                - fixes_made: list - List of fixes that were applied
                - original_paths: dict - Original paths before fixing
        """
        fixes_made = []
        original_paths = {}
        fixed = False
        
        pages = website_structure.pages
        navigation = website_structure.navigation
        
        # Fix Home page path - check all pages for home-like names
        for i, page in enumerate(pages):
            page_name = page.name
            if self._is_home_page(page_name):
                current_path = page.path
                if current_path != "/":
                    original_paths["home_page"] = current_path
                    page.path = "/"
                    fixes_made.append(f"Changed {page_name} page path from '{current_path}' to '/'")
                    fixed = True
                break
        
        # Fix Home navigation path - check all navigation items for home-like labels
        for i, nav_item in enumerate(navigation):
            nav_label = nav_item.label
            if self._is_home_page(nav_label):
                current_path = nav_item.path
                if current_path != "/":
                    original_paths["home_navigation"] = current_path
                    nav_item.path = "/"
                    fixes_made.append(f"Changed {nav_label} navigation path from '{current_path}' to '/'")
                    fixed = True
                break
        
        return {
            "fixed": fixed,
            "fixes_made": fixes_made,
            "original_paths": original_paths
        }
    
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
    
    def _generate_initial_files_parallel(self, structure: WebsiteStructure, analysis: BusinessAnalysis, enable_animations: bool = False, cost_tracker=None, extracted_colors=None, is_ground_truth: bool = False, google_fonts_urls=None) -> tuple[Dict[str, str], Any]:
        """Generate initial project files in parallel (config, UI components, app files, theme)

        This runs independent file generation operations concurrently for faster initial setup.

        Args:
            structure: Website structure
            analysis: Business analysis
            enable_animations: Whether to include animation files
            cost_tracker: Optional CostTracker instance to track AI costs

        Returns:
            Tuple of (files_dict, theme_object)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger.info("[PARALLEL GEN] Starting parallel initial file generation...")

        files = {}
        theme = None
        errors = []

        # Define worker functions for each independent operation
        def generate_config():
            logger.info("[PARALLEL GEN] Generating config files...")
            return ('config', react_file_manager.generate_config_files(structure, google_fonts_urls=google_fonts_urls))

        def generate_ui_components():
            logger.info("[PARALLEL GEN] Generating UI components...")
            return ('ui', react_file_manager.generate_ui_components())

        def generate_app_files():
            logger.info("[PARALLEL GEN] Generating app files...")
            return ('app', react_file_manager.generate_app_files(structure, enable_animations))

        # Animation files (if enabled)
        def generate_animation_files():
            if enable_animations:
                logger.info("[PARALLEL GEN] Including animation utilities...")
                return ('animation', react_file_manager.generate_animation_files())
            else:
                # Return empty dict when animations are disabled to avoid unpacking errors
                return ('animation', {})

        def generate_theme():
            logger.info("[PARALLEL GEN] Generating custom theme...")
            try:
                from app.services.theme_generator import theme_generator
                theme_obj = theme_generator.generate_theme_with_fallback(
                    business_analysis=analysis,
                    color_scheme=structure.color_scheme,
                    cost_tracker=cost_tracker,
                    extracted_colors=extracted_colors,
                    is_ground_truth=is_ground_truth
                )
                logger.info(f"[PARALLEL GEN] ✓ Theme generated: primary={theme_obj.primary}")
                return ('theme', theme_obj)
            except Exception as e:
                logger.warning(f"[PARALLEL GEN] ⚠ Theme generation warning: {str(e)}, using fallback")
                return ('theme', None)

        # Run all operations in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks
            futures = {
                executor.submit(generate_config): 'config',
                executor.submit(generate_ui_components): 'ui',
                executor.submit(generate_app_files): 'app',
                executor.submit(generate_animation_files): 'animation',
                executor.submit(generate_theme): 'theme'
            }

            # Collect results as they complete
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result()

                    # Handle None results (shouldn't happen with our current code, but defensive)
                    if result is None:
                        logger.warning(f"[PARALLEL GEN] ⚠ {task_name} returned None, skipping")
                        continue

                    result_type, result_data = result

                    if result_type == 'theme':
                        theme = result_data
                        logger.info("[PARALLEL GEN] ✓ Theme generation completed")
                    else:
                        if result_data:  # Only update if there's actual data
                            files.update(result_data)
                            logger.info(f"[PARALLEL GEN] ✓ {task_name} files generated ({len(result_data)} files)")
                        else:
                            logger.info(f"[PARALLEL GEN] ✓ {task_name} completed (no files)")

                except Exception as e:
                    error_msg = f"{task_name} generation failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"[PARALLEL GEN] ✗ {error_msg}")

                    # Only fail for critical tasks
                    if task_name in ['config', 'ui', 'app']:
                        raise Exception(f"Critical task {task_name} failed: {str(e)}")

        if errors:
            # Log errors but don't fail if they're only from optional tasks (animation, theme)
            error_summary = "\n".join(errors)
            logger.warning(f"[PARALLEL GEN] ⚠ Some optional tasks had errors:\n{error_summary}")

        logger.info(f"[PARALLEL GEN] ✓ Initial files generated in parallel ({len(files)} files total)")
        return files, theme

    def _generate_all_files(self, structure: WebsiteStructure, analysis: BusinessAnalysis, enable_animations: bool = False, cost_tracker=None, design_extraction=None, design_fidelity: str = "none") -> Dict[str, str]:
        """Generate all React project files

        Args:
            structure: Website structure
            analysis: Business analysis
            enable_animations: Whether to include animation files
            cost_tracker: Optional CostTracker instance to track AI costs
        """

        files = {}

        # Reference-site design data (URL ingestion): exact colors steer the
        # theme; fonts/Google Fonts links are injected only for replicas.
        is_ground_truth = design_fidelity == "replica"
        extracted_colors = None
        replica_fonts = None
        replica_google_fonts = None
        if design_extraction is not None and getattr(design_extraction, "ok", False):
            extracted_colors = [c.value for c in design_extraction.colors] or None
            if is_ground_truth:
                replica_fonts = design_extraction.fonts or None
                replica_google_fonts = design_extraction.google_fonts_urls or None

        # Generate initial files (config, UI components, app files, theme)
        # Use parallel generation if enabled
        if settings.enable_parallel_generation:
            logger.info("[REACT GEN] Using parallel generation for initial files...")
            files, theme = self._generate_initial_files_parallel(
                structure, analysis, enable_animations, cost_tracker,
                extracted_colors=extracted_colors, is_ground_truth=is_ground_truth,
                google_fonts_urls=replica_google_fonts
            )
        else:
            # Sequential generation (original approach)
            # Core config files (package.json, vite.config, etc.)
            files.update(react_file_manager.generate_config_files(structure, google_fonts_urls=replica_google_fonts))

            # UI components (shadcn/ui primitives - base set)
            files.update(react_file_manager.generate_ui_components())

            # App setup files (App.tsx, main.tsx)
            files.update(react_file_manager.generate_app_files(structure, enable_animations))

            # Generate custom theme based on business analysis
            logger.info("[REACT GEN] Generating custom theme...")
            theme = None
            try:
                from app.services.theme_generator import theme_generator
                theme = theme_generator.generate_theme_with_fallback(
                    business_analysis=analysis,
                    color_scheme=structure.color_scheme,
                    cost_tracker=cost_tracker,
                    extracted_colors=extracted_colors,
                    is_ground_truth=is_ground_truth
                )
                logger.info(f"[REACT GEN] ✓ Theme generated: primary={theme.primary}")
            except Exception as e:
                logger.warning(f"[REACT GEN] ⚠ Theme generation warning: {str(e)}, using fallback")
                # theme will remain None, generate_style_files will handle fallback

        # Style files (index.css) with custom theme (depends on theme, so runs after)
        files.update(react_file_manager.generate_style_files(structure, theme, fonts=replica_fonts))
        
        # Animation files (if enabled)
        # if enable_animations:
        #     logger.info("[REACT GEN] Including animation utilities...")
        #     files.update(react_file_manager.generate_animation_files())

        # Page components (will auto-generate any missing section/UI components)
        # Use parallel generation if enabled and we have multiple pages
        if settings.enable_parallel_generation and len(structure.pages) > 1:
            logger.info(f"[REACT GEN] Using parallel page generation for {len(structure.pages)} pages...")
            files.update(self._generate_page_files_parallel(structure, analysis, files, enable_animations, cost_tracker=cost_tracker))
        else:
            if settings.enable_parallel_generation and len(structure.pages) == 1:
                logger.info("[REACT GEN] Parallel generation enabled but only 1 page, using sequential generation...")
            files.update(self._generate_page_files(structure, analysis, files, enable_animations, cost_tracker=cost_tracker))
        
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
        
        # Post-process Footer components to add brand attribution
        files = self._add_footer_attribution(files)
        
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
    
    def _generate_page_files(self, structure: WebsiteStructure, analysis: BusinessAnalysis, files: Dict[str, str], enable_animations: bool = False, cost_tracker=None) -> Dict[str, str]:
        """Generate page component files

        Args:
            structure: Website structure
            analysis: Business analysis
            files: Existing files dictionary
            enable_animations: Whether animations are enabled
            cost_tracker: Optional CostTracker instance to track AI costs
        """

        # files = {}

        for page in structure.pages:
            print(f"Generating page: {page.name}")
            page_content = self._generate_page_component(page, structure, analysis, files, enable_animations, cost_tracker=cost_tracker)
            page_filename = page.name.lower().replace(" ", "-")
            files[f"src/pages/{page_filename}.tsx"] = page_content

        return files

    def _generate_page_files_parallel(self, structure: WebsiteStructure, analysis: BusinessAnalysis, files: Dict[str, str], enable_animations: bool = False, cost_tracker=None) -> Dict[str, str]:
        """Generate page component files in parallel

        This function generates multiple pages and their components simultaneously using a thread pool,
        which can significantly speed up generation for websites with multiple pages.

        Args:
            structure: Website structure
            analysis: Business analysis
            files: Existing files dictionary (will be updated thread-safely)
            enable_animations: Whether animations are enabled
            cost_tracker: Optional CostTracker instance to track AI costs

        Returns:
            Dictionary of generated files

        Note:
            - Uses ThreadPoolExecutor for parallel execution
            - Thread-safe file dictionary updates using a lock
            - Respects max_parallel_pages configuration setting
            - Captures all new components generated during page creation
        """

        # Thread-safe lock for updating the shared files dictionary
        files_lock = threading.Lock()

        # Determine number of parallel workers
        max_workers = min(len(structure.pages), settings.max_parallel_pages)

        logger.info(f"[PARALLEL GEN] Starting parallel page generation with {max_workers} workers for {len(structure.pages)} pages")

        def generate_single_page(page: PageStructure) -> tuple[str, str, str, Dict[str, str]]:
            """
            Generate a single page component (thread worker function)

            Returns:
                Tuple of (page_filename, page_path, page_content, new_files_dict)
                where new_files_dict contains the page and any new components generated
            """
            try:
                logger.info(f"[PARALLEL GEN] Generating page: {page.name}")
                print(f"Generating page: {page.name}")

                # Generate the page component
                # Create a working copy that includes existing files for context
                with files_lock:
                    files_snapshot = files.copy()

                # Track the number of files before generation
                files_before_count = len(files_snapshot)

                # Generate the page - this modifies files_snapshot by adding new components
                page_content = self._generate_page_component(
                    page,
                    structure,
                    analysis,
                    files_snapshot,
                    enable_animations,
                    cost_tracker=cost_tracker
                )

                page_filename = page.name.lower().replace(" ", "-")
                page_path = f"src/pages/{page_filename}.tsx"

                # Add the page content to the snapshot
                files_snapshot[page_path] = page_content

                # Calculate how many new files were generated (components + page)
                new_files_count = len(files_snapshot) - files_before_count

                logger.info(f"[PARALLEL GEN] ✓ Completed page: {page.name} (generated {new_files_count} files)")

                # Return the complete files snapshot which includes all new components
                return (page_filename, page_path, page_content, files_snapshot)

            except Exception as e:
                logger.error(f"[PARALLEL GEN] ✗ Failed to generate page {page.name}: {str(e)}")
                raise

        # Use ThreadPoolExecutor to generate pages in parallel
        all_generated_files = {}
        errors = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all page generation tasks
            future_to_page = {
                executor.submit(generate_single_page, page): page
                for page in structure.pages
            }

            # Collect results as they complete
            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    page_filename, page_path, _, page_files = future.result()

                    # Merge all files from this page generation into our collection
                    # This includes the page itself and any new components created
                    with files_lock:
                        for file_path, file_content in page_files.items():
                            # Only add if it's a new file (page or component from this generation)
                            if file_path not in files or file_path == page_path:
                                all_generated_files[file_path] = file_content

                    logger.info(f"[PARALLEL GEN] ✓ Successfully generated: {page_filename}")
                except Exception as e:
                    error_msg = f"Page {page.name} generation failed: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"[PARALLEL GEN] ✗ {error_msg}")

        # Check if any pages failed to generate
        if errors:
            error_summary = "\n".join(errors)
            logger.error(f"[PARALLEL GEN] ✗ Failed to generate {len(errors)} page(s):\n{error_summary}")
            raise Exception(f"Parallel page generation failed for {len(errors)} page(s): {error_summary}")

        # Update main files dictionary with all generated content
        files.update(all_generated_files)

        # Count pages vs components
        pages_count = sum(1 for path in all_generated_files.keys() if path.startswith('src/pages/'))
        components_count = len(all_generated_files) - pages_count

        logger.info(f"[PARALLEL GEN] ✓ Successfully generated {pages_count} pages and {components_count} components in parallel")

        return files
    
    def _generate_page_component(self, page: PageStructure, structure: WebsiteStructure, analysis: BusinessAnalysis, files: Dict[str, str], enable_animations: bool = False, cost_tracker=None) -> str:
        """
        Generate individual page component using LLM.
        Automatically generates any missing section or UI components needed.
        
        Args:
            page: Page structure
            structure: Website structure
            analysis: Business analysis
            files: Existing files dictionary
            enable_animations: Whether animations are enabled
            cost_tracker: Optional CostTracker instance to track AI costs
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
        system_prompt = self._create_page_generation_system_prompt1(enable_animations, analysis)
        
        # Create user prompt with context
        user_prompt = self._create_page_generation_user_prompt1(
            page=page,
            structure=structure,
            analysis=analysis,
            available_ui_components=available_ui_components,
            available_section_components=available_section_components
        )
        
        # Call LLM to generate page and components
        logger.info(f"[PAGE GEN] Calling LLM for page {page.name} generation...")
        # self.openai_client.set_max_completion_tokens(16000)
        # response, usage = self.openai_client.call_openai_api_structured(
        #     system_prompt,
        #     user_prompt,
        #     PageGenerationResponse,
        #     model="o4-mini"
        # )

        # self.google_client.set_max_completion_tokens(8000)
        # response, usage = self.google_client.call_openai_api_structured(
        #     system_prompt,
        #     user_prompt,
        #     PageGenerationResponse,
        #     model="o4-mini"   
        # )
        # TODO: regulate this base on the complexity of the page
        self.google_client.set_max_completion_tokens(32000)
        response, usage = self.google_client.call_openai_api_structured(
            system_prompt,
            user_prompt,
            PageGenerationResponse,
            model=settings.generation_model
        )

        print(f"Usage for page {page.name} generation: {usage}")
        
        # Track cost if cost_tracker is provided
        if cost_tracker:
            cost_tracker.track_call(
                service_name="page_generation",
                model_name=settings.generation_model,
                usage=usage,
                metadata={"page_name": page.name, "page_path": page.path}
            )
        
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

            # Validate and inject data attributes
            validated_content, was_modified = code_validator._validate_and_inject_data_attributes(
                component_file.path,
                component_file.content
            )
            if was_modified:
                logger.info(f"[PAGE GEN] ✓ Added data attributes to {component_file.path}")
                component_file.content = validated_content

            # Check for duplicates
            if component_file.path in files:
                logger.warning(f"[PAGE GEN] ⚠ Component {component_file.path} already exists, skipping...")
                continue

            # Check if the component is a duplicate
            component_name = component_file.path.split("/")[-1].replace(".tsx", "").lower()
            if component_name not in set_available_ui_components:
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
    

    def _add_footer_attribution(self, files: Dict[str, str]) -> Dict[str, str]:
        """
        Post-process Footer components to add brand attribution at the bottom of the footer
        
        This function finds all Footer.tsx files and adds "Made with 💜 from {brand_name}"
        at the bottom of the footer component, just before the closing tag.
        
        Args:
            files: Dictionary of file paths to file contents
            
        Returns:
            Updated files dictionary with attribution added to Footer components
        """
        brand_name = settings.app_brand_name
        attribution_text = f"Made with 💜 from {brand_name}"
        
        # Find all Footer component files
        footer_files = [
            path for path in files.keys() 
            if path.endswith("Footer.tsx") or path.endswith("footer.tsx")
        ]
        
        if not footer_files:
            logger.info("[FOOTER ATTRIBUTION] No Footer components found to process")
            return files
        
        logger.info(f"[FOOTER ATTRIBUTION] Processing {len(footer_files)} Footer component(s)...")
        
        for footer_path in footer_files:
            footer_content = files[footer_path]
            
            # Check if attribution already exists to avoid duplicates
            if attribution_text in footer_content:
                logger.info(f"[FOOTER ATTRIBUTION] Attribution already exists in {footer_path}, skipping")
                continue
            
            # Find the closing tag of the root element in the return statement
            # Look for common footer root elements: </footer>, </div>, </section>
            # Pattern matches closing tags that appear before the closing parenthesis of return statement
            # We want to insert before the last closing tag in the return statement
            
            # Strategy: Find the last occurrence of </footer>, </div>, or </section> 
            # that appears before the closing ) of the return statement
            # We'll look for the pattern: </tagName> followed by whitespace and then )
            
            # Try to find the root element closing tag
            # Common patterns: </footer>, </div>, </section>
            root_closing_patterns = [
                r'(</footer>)',  # </footer> tag
                r'(</div>)',     # </div> tag  
                r'(</section>)', # </section> tag
            ]
            
            updated_content = footer_content
            insertion_made = False
            
            # Try each pattern to find the root closing tag
            for pattern in root_closing_patterns:
                # Find all matches
                matches = list(re.finditer(pattern, footer_content, re.IGNORECASE | re.MULTILINE))
                
                if matches:
                    # Get the last match (should be the root element closing tag)
                    last_match = matches[-1]
                    
                    # Verify this is likely the root element by checking if it's followed by 
                    # whitespace and closing parenthesis (end of return statement)
                    after_match = footer_content[last_match.end():last_match.end() + 20]
                    
                    # Check if this looks like the end of a return statement
                    if re.search(r'^\s*\)\s*;?\s*$', after_match, re.MULTILINE) or \
                       re.search(r'^\s*\)\s*$', after_match.split('\n')[0]):
                        # Get the indentation of the closing tag by finding the start of the line
                        line_start = footer_content.rfind('\n', 0, last_match.start()) + 1
                        line_before_tag = footer_content[line_start:last_match.start()]
                        # Extract indentation (whitespace before the tag)
                        indentation = ''
                        for char in line_before_tag:
                            if char in [' ', '\t']:
                                indentation += char
                            else:
                                break
                        
                        # Wrap attribution text in a JSX span with data-locked="true" to make it uneditable
                        # Match the indentation of the closing tag
                        locked_attribution = f'{indentation}<p className="text-center text-xs text-gray-500" data-locked="true" data-editable-text="false">{attribution_text}</p>\n'
                        
                        # Insert attribution before the closing tag
                        insertion_point = last_match.start()
                        updated_content = (
                            footer_content[:insertion_point] +
                            locked_attribution +
                            footer_content[insertion_point:]
                        )
                        insertion_made = True
                        logger.info(f"[FOOTER ATTRIBUTION] ✓ Added attribution to bottom of {footer_path}")
                        break
            
            # If no pattern matched, try a fallback: find the last </tag> before the return closes
            if not insertion_made:
                # Fallback: Find any closing tag that appears before the final closing parenthesis
                # Look for the pattern: </...> followed by whitespace and )
                fallback_pattern = r'(</\w+>)'
                matches = list(re.finditer(fallback_pattern, footer_content))
                
                if matches:
                    # Find the match that's closest to the end but before the return closes
                    # Look for the last </tag> that has a closing ) after it
                    for match in reversed(matches):
                        after_text = footer_content[match.end():match.end() + 50]
                        # Check if this is followed by closing parenthesis (end of return)
                        if ')' in after_text:
                            # Count how many closing tags are between this and the )
                            text_between = footer_content[match.end():match.end() + after_text.find(')')]
                            open_tags = text_between.count('<')
                            close_tags = text_between.count('</')
                            
                            # If this appears to be the root closing tag
                            if open_tags == 0 or (close_tags == 1 and open_tags <= 1):
                                # Get the indentation of the closing tag
                                line_start = footer_content.rfind('\n', 0, match.start()) + 1
                                line_before_tag = footer_content[line_start:match.start()]
                                # Extract indentation (whitespace before the tag)
                                indentation = ''
                                for char in line_before_tag:
                                    if char in [' ', '\t']:
                                        indentation += char
                                    else:
                                        break
                                
                                # Wrap attribution text with matching indentation
                                locked_attribution = f'{indentation}<p className="text-center text-xs text-gray-500" data-locked="true" data-editable-text="false">{attribution_text}</p>\n'
                                
                                insertion_point = match.start()
                                updated_content = (
                                    footer_content[:insertion_point] +
                                    locked_attribution +
                                    footer_content[insertion_point:]
                                )
                                insertion_made = True
                                logger.info(f"[FOOTER ATTRIBUTION] ✓ Added attribution to bottom of {footer_path} (fallback)")
                                break
            
            if insertion_made:
                files[footer_path] = updated_content
            else:
                logger.warning(f"[FOOTER ATTRIBUTION] ⚠ Could not find root closing tag in {footer_path}")
        
        return files

    def _create_page_generation_system_prompt1(self, enable_animations: bool = False, analysis: BusinessAnalysis = None) -> str:
        """Create concise system prompt for page generation - captures all critical validation rules

        The static rules live in _static_page_system_prompt() so every page
        call sends a byte-identical leading prefix (Gemini implicit caching
        keys on prefix identity). Per-project content — animation
        instructions here, business/design context in the user prompt — must
        never move ahead of the static block.

        Args:
            enable_animations: Whether to include animation instructions
            analysis: Business analysis for animation style selection
        """
        # Get animation instructions if enabled
        animation_instructions = ""
        if enable_animations and analysis:
            from app.services.animation_config import get_component_animation_instructions
            animation_instructions = get_component_animation_instructions(analysis.business_type)

        prompt = _static_page_system_prompt()
        if animation_instructions:
            prompt = f"{prompt}\n\n{animation_instructions}"
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

        smooth_scroll_instructions = ""
        if structure.page_count == 1:
            smooth_scroll_instructions = """
            🔗 NAVIGATION & SMOOTH SCROLLING (For Single-Page Websites):
When creating a Header component with navigation links to page sections:
- Import smooth scroll utility: `import {{ handleSmoothScroll }} from '@/utils/smoothScroll';`
- For navigation links, use onClick handler:
   ```tsx
   <a 
     href="#features" 
     onClick={{(e) => handleSmoothScroll(e, '#features')}}
     className="..."
   >
     Features
   </a>
   ```
- For mobile menu, pass callback to close menu:
   ```tsx
   <a 
     href="#features"
     onClick={{(e) => handleSmoothScroll(e, '#features', () => setIsMenuOpen(false))}}
     className="..."
   >
     Features
   </a>
   ```
- Ensure ALL section components have `id` attribute matching their lowercase name
- Example: Features component should have `<section id="features" ...>`
            """
        return f"""BUILD THIS PAGE BASED ON THE FOLLOWING CONTEXT:

PAGE: {page.name} ({page.path})
{page.description}

CONTEXT
Original prompt: {analysis.prompt}
Business: {analysis.business_type} | Industry: {analysis.industry}
Audience: {analysis.target_audience} | Tone: {analysis.tone}
CTA: {analysis.primary_cta} | Colors: {structure.color_scheme}


SECTIONS NEEDED
{chr(10).join(components_list)}

AVAILABLE COMPONENTS
UI (@/components/ui/): {', '.join(available_ui_components) or 'None - create as needed'}
Sections (@/components/): {', '.join(available_section_components) or 'None - create as needed'}

CRITICAL: Use ONLY icons from the verified list in the system prompt, properly imported from lucide-react.

NAVIGATION
{chr(10).join(nav_list) if nav_list else '  • Single page (no nav)'}

TASK
1. Build page using/creating section components
2. Add missing components to new_components (no duplicates)
3. <Header /> and <Footer /> usage: no props; define values internally using nav above
4. Reuse existing UI components as-is

{smooth_scroll_instructions}

🚨 CRITICAL: VISUAL EDITING TRACKING - MANDATORY 🚨
5. EVERY section component's ROOT element MUST have these exact attributes:
   - data-component="ComponentName" (exact component name, e.g., "Hero", "Features", "Footer")
   - data-file="src/components/ComponentName.tsx" (exact file path)
   - id="componentname" (lowercase component name for navigation, e.g., "hero", "features", "contact")
6. EXAMPLE - Hero.tsx component:
   ✅ CORRECT:
   export function Hero() {{
     return (
       <section id="hero" data-component="Hero" data-file="src/components/Hero.tsx" className="...">
         <h1 data-element="hero-title">Title</h1>
         <button data-element="hero-cta">Get Started</button>
       </section>
     )
   }}
   ❌ WRONG (missing data attributes and id):
   export function Hero() {{
     return (
       <section className="...">
         <h1>Title</h1>
       </section>
     )
   }}
7. These attributes MUST be on the FIRST/ROOT element in the return statement
8. Without these attributes, visual editing will NOT work
9. The `id` attribute enables smooth navigation from the header to sections
10. This is absolutely required for ALL section components (Header, Hero, Footer, etc.)



CRITICAL
✓ Prop names match interfaces exactly; provide ALL required props
✓ Only destructure props you use
✓ 3-5 realistic test items for arrays; pass with correct name (items={{{{data}}}})
✓ Use verified icons only; import only what you render
✓ No unused variables/imports
✓ Sections & UI: named export | Pages: default export
✓ TypeScript strict, no 'any', responsive, accessible

OUTPUT JSON: {{"page_content": "...", "new_components": [...]}}"""


@lru_cache(maxsize=1)
def _static_page_system_prompt() -> str:
    """Static, byte-identical prefix of the page-generation system prompt.

    Built once per process and shared by every page call so Gemini's implicit
    caching (which keys on a byte-identical leading prefix) can discount these
    tokens from the second page onward. Keep ALL per-project variability out
    of this block: animation instructions are appended after it, and
    business/design context belongs in the user prompt. Note that
    enable_parallel_generation can miss the cache on concurrent page calls —
    the sequential default is cache-optimal.
    """
    safe_icons_list = get_safe_icons()
    return f"""Expert React 19 + TypeScript + Vite developer. Generate production-ready page + missing components.

Do not recreate existing ui components in the @/components/ui/ path.

TECH STACK: React 19, TypeScript (strict), Tailwind, shadcn/ui, lucide-react, Vite, React Router (Link for internal nav)

📸 IMAGE URLs - USE PICSUM PHOTOS (100% RELIABLE): Use Lorem Picsum for all images:
FORMATS:
- Random image: https://picsum.photos/1200/800
- Specific image: https://picsum.photos/id/237/1200/800 (id can be 1-1000+)
- Grayscale: https://picsum.photos/1200/800?grayscale
- Blur effect: https://picsum.photos/1200/800?blur

RECOMMENDED DIMENSIONS BY USE CASE:
- Hero sections: 1920/1080 or 1600/900
- Content images: 1200/800 or 800/600
- Profile/testimonial: 400/400 or 600/600
- Logos: 400/400

EXAMPLES:
✅ Hero image: https://picsum.photos/2560/1440
✅ About image: https://picsum.photos/1200/800
✅ Grayscale hero: https://picsum.photos/1600/900?grayscale
✅ Specific ID: https://picsum.photos/id/42/1200/800
✅ Team photo: https://picsum.photos/600/600

RULE: All image URLs MUST use picsum.photos format. No other image sources.

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
CRITICAL: Ensure you use ONLY the icons from the list below, and ensure Icons are properly imported from lucide-react:
{safe_icons_list}

   ❌ Building, Circle, User (don't exist)
   ✅ Only use icons from list below (Building2, CircleDot, UserCircle)
   ✅ Icons are CASE-SENSITIVE
   
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
□ Ensure the year is the current year at the footer
□ CRITICAL: ALL section components have data-component and data-file on root element
□ CRITICAL: Major interactive elements have data-element attributes

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
• import only what you render and ensure they are imported from lucide-react and valid from the list of verified icons
• Destructuring experienceIcon but never using it
• Missing required description prop on Cta component
• Dont escape quotes in the generated code

🎨 VISUAL EDITING REQUIREMENTS (REQUIRED FOR ALL COMPONENTS):

All generated components MUST include data attributes for visual editing:

1. SECTION COMPONENTS (Root element of every section):
   data-component="ComponentName"
   data-file="src/components/ComponentName.tsx"

2. EDITABLE ELEMENTS (All user-facing content):
   Required attributes for ALL elements users might want to edit:
   
   a) Text Elements (headings, paragraphs, labels, spans):
      data-element="descriptive-name" 
      data-element-type="heading|paragraph|label|span"
      data-editable-text="true"
      
   b) Images:
      data-element="image-name"
      data-element-type="image"
      data-editable-src="true"
      
   c) Links:
      data-element="link-name"
      data-element-type="link"
      
   d) Buttons:
      data-element="button-name"
      data-element-type="button"
      
   e) Containers (divs, sections that affect layout):
      data-element="container-name"
      data-element-type="container"

EXAMPLES:

✅ Hero Title:
<h1 
  className="text-4xl font-bold" 
  data-element="hero-title" 
  data-element-type="heading"
  data-editable-text="true"
>
  Welcome to Our Platform
</h1>

✅ Feature Description:
<p 
  className="text-gray-600" 
  data-element="feature-description" 
  data-element-type="paragraph"
  data-editable-text="true"
>
  Build amazing websites in minutes
</p>

✅ Hero Image:
<img 
  src="https://picsum.photos/2560/1440"
  alt="Hero background"
  data-element="hero-image"
  data-element-type="image"
  data-editable-src="true"
/>

✅ CTA Button:
<button 
  className="bg-blue-600 text-white px-6 py-3 rounded-lg"
  data-element="primary-cta"
  data-element-type="button"
>
  Get Started
</button>

✅ Feature Card Container:
<div 
  className="bg-white p-6 rounded-lg shadow-md"
  data-element="feature-card"
  data-element-type="container"
>
  {{/* card content */}}
</div>

NAMING CONVENTIONS for data-element:
- Use kebab-case (e.g., "hero-title", "about-description")
- Be descriptive and specific (e.g., "pricing-tier-1-price" not just "price")
- Include context when needed (e.g., "testimonial-1-author" not just "author")

⚠️ CRITICAL: Missing data attributes will break the visual editor. Add them to ALL user-facing elements.

Verify EVERY item in checklist before generating."""


# Create singleton instance
react_website_generator = ReactWebsiteGenerator()

