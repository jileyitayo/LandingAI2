"""
Error Fixer Service
Uses LLM to automatically fix validation and build errors in generated code.
"""

import logging
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel

from app.config import settings
from app.services.prompt_open_ai import PromptOpenAI
from app.services.edit_patcher import (
    PATCH_FORMAT_SPEC,
    PatchApplyError,
    PatchFormatError,
    apply_blocks,
    parse_blocks,
)
from app.services.validators.code_validator import CodeValidationError
from app.services.validators.build_tester import BuildError

logger = logging.getLogger(__name__)


class CodeFix(BaseModel):
    """Represents a code fix"""
    file_path: str
    original_content: str
    fixed_content: str
    changes_made: List[str]


class FixResult(BaseModel):
    """Result of error fixing attempt"""
    success: bool
    fixes: List[CodeFix]
    remaining_errors: List[str]
    fix_summary: str


class ErrorFixer:
    """Fixes code errors using LLM"""
    
    def __init__(self):
        self.openai_client = PromptOpenAI()
        self.google_client = PromptOpenAI(is_google=True)
        self.max_retries = 3

    def _llm_fix_with_patch_fallback(
        self,
        system_prompt: str,
        user_prompt_base: str,
        original_content: str,
        file_path: str,
        max_tokens: int,
        call_label: str,
        cost_tracker=None,
    ) -> Optional[str]:
        """
        Run a fix prompt in patch mode first (SEARCH/REPLACE blocks — output
        tokens scale with the fix, not the file), falling back to one
        full-file attempt when the patch can't be parsed or applied.
        """
        self.google_client.set_max_completion_tokens(max_tokens)

        patch_user_prompt = (
            f"{user_prompt_base}\n\n"
            f"OUTPUT FORMAT — SEARCH/REPLACE BLOCKS:\n{PATCH_FORMAT_SPEC}"
        )
        try:
            response, usage = self.google_client.call_openai_api(
                system_prompt,
                patch_user_prompt,
                model=settings.edit_model
            )
            logger.info(f"Usage for {call_label} (patch mode): {usage}")
            if cost_tracker:
                cost_tracker.track_call("validation", settings.edit_model, usage, metadata={"call": call_label, "file": file_path, "mode": "patch"})
            blocks = parse_blocks(response or "")
            fixed = apply_blocks(original_content, blocks)
            logger.info(f"[ERROR FIXER] Applied {len(blocks)} patch block(s) to {file_path}")
            return fixed
        except (PatchFormatError, PatchApplyError) as e:
            logger.warning(f"[ERROR FIXER] Patch-mode fix failed for {file_path} ({e}); falling back to full-file rewrite")
        except Exception as e:
            logger.error(f"[ERROR FIXER] Error calling LLM: {e}")
            return None

        full_user_prompt = (
            f"{user_prompt_base}\n\n"
            "Return the complete fixed file content, nothing else."
        )
        try:
            response, usage = self.google_client.call_openai_api(
                system_prompt,
                full_user_prompt,
                model=settings.edit_model
            )
            logger.info(f"Usage for {call_label} (full-file fallback): {usage}")
            if cost_tracker:
                cost_tracker.track_call("validation", settings.edit_model, usage, metadata={"call": call_label, "file": file_path, "mode": "full_file_fallback"})
            fixed_content = self._extract_code_from_response(response)
            if fixed_content:
                return fixed_content
            logger.error(f"[ERROR FIXER] Failed to extract fixed code from LLM response")
            return None
        except Exception as e:
            logger.error(f"[ERROR FIXER] Error calling LLM: {e}")
            return None


    def fix_validation_errors(
        self,
        files: Dict[str, str],
        errors: List[CodeValidationError],
        warnings: List[CodeValidationError],
        cost_tracker=None
    ) -> Tuple[Dict[str, str], bool]:
        """
        Fix validation errors in generated files
        
        Args:
            files: Dictionary of file paths to contents
            errors: List of validation errors
            warnings: List of validation warnings
            
        Returns:
            Tuple of (fixed_files, all_fixed)
        """
        if not errors:
            logger.info("[ERROR FIXER] No validation errors to fix")
            return files, True
        
        logger.info(f"[ERROR FIXER] Attempting to fix {len(errors)} validation errors...")
        
        # Group errors by file
        errors_by_file = self._group_errors_by_file(errors)
        
        fixed_files = files.copy()
        all_fixed = True
        
        for file_path, file_errors in errors_by_file.items():
            if file_path not in fixed_files:
                logger.warning(f"[ERROR FIXER] File {file_path} not found in files dict")
                all_fixed = False
                continue
            
            logger.info(f"[ERROR FIXER] Fixing {len(file_errors)} errors in {file_path}")
            
            fixed_content = self._fix_file_errors(
                file_path=file_path,
                original_content=fixed_files[file_path],
                errors=file_errors,
                all_files=fixed_files,
                cost_tracker=cost_tracker
            )
            
            if fixed_content:
                fixed_files[file_path] = fixed_content
                logger.info(f"[ERROR FIXER] ✓ Fixed errors in {file_path}")
            else:
                logger.error(f"[ERROR FIXER] ✗ Failed to fix errors in {file_path}")
                all_fixed = False
        
        return fixed_files, all_fixed
    
    def fix_build_errors(
        self,
        files: Dict[str, str],
        errors: List[BuildError],
        build_output: str,
        cost_tracker=None
    ) -> Tuple[Dict[str, str], bool]:
        """
        Fix build errors in generated files
        
        Args:
            files: Dictionary of file paths to contents
            errors: List of build errors
            build_output: Full build output for context
            
        Returns:
            Tuple of (fixed_files, all_fixed)
        """
        if not errors:
            logger.info("[ERROR FIXER] No build errors to fix")
            return files, True
        
        logger.info(f"[ERROR FIXER] Attempting to fix {len(errors)} build errors...")
        
        # Group errors by file
        errors_by_file = {}
        for error in errors:
            # Normalize file path (remove leading ./ or src/)
            file_path = error.file_path
            if file_path.startswith('./'):
                file_path = file_path[2:]
            if not file_path.startswith('src/') and '/' in file_path:
                file_path = f"src/{file_path}"
            
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append(error)
        
        fixed_files = files.copy()
        all_fixed = True
        
        for file_path, file_errors in errors_by_file.items():
            # Find matching file in files dict
            matching_file = self._find_matching_file(file_path, fixed_files)
            
            if not matching_file:
                logger.warning(f"[ERROR FIXER] File {file_path} not found in files dict")
                all_fixed = False
                continue
            
            logger.info(f"[ERROR FIXER] Fixing {len(file_errors)} build errors in {matching_file}")
            
            fixed_content = self._fix_file_build_errors(
                file_path=matching_file,
                original_content=fixed_files[matching_file],
                errors=file_errors,
                build_output=build_output,
                all_files=fixed_files,
                cost_tracker=cost_tracker
            )
            
            if fixed_content:
                fixed_files[matching_file] = fixed_content
                logger.info(f"[ERROR FIXER] ✓ Fixed build errors in {matching_file}")
            else:
                logger.error(f"[ERROR FIXER] ✗ Failed to fix build errors in {matching_file}")
                all_fixed = False
        
        return fixed_files, all_fixed
    
    def _find_matching_file(self, error_file_path: str, files: Dict[str, str]) -> Optional[str]:
        """Find matching file path in files dict"""
        # Try exact match first
        if error_file_path in files:
            return error_file_path
        
        # Try with src/ prefix
        if f"src/{error_file_path}" in files:
            return f"src/{error_file_path}"
        
        # Try matching by filename
        error_filename = error_file_path.split('/')[-1]
        for file_path in files.keys():
            if file_path.endswith(error_filename):
                return file_path
        
        return None
    
    def _group_errors_by_file(self, errors: List[CodeValidationError]) -> Dict[str, List[CodeValidationError]]:
        """Group errors by file path"""
        errors_by_file = {}
        for error in errors:
            if error.file_path not in errors_by_file:
                errors_by_file[error.file_path] = []
            errors_by_file[error.file_path].append(error)
        return errors_by_file
    
    def _fix_file_errors(
        self,
        file_path: str,
        original_content: str,
        errors: List[CodeValidationError],
        all_files: Dict[str, str],
        cost_tracker=None
    ) -> Optional[str]:
        """Fix errors in a single file using LLM"""

        # Skip fixing utility and hook files - they're pre-tested templates
        if '/utils/' in file_path or '/hooks/' in file_path:
            logger.info(f"[ERROR FIXER] Skipping LLM fix for template file: {file_path}")
            return original_content
        
        # Create error summary
        error_messages = [f"- {error.error_type}: {error.message}" for error in errors]
        error_summary = "\n".join(error_messages)
        
        # Get related files for context
        related_files = self._get_related_files(file_path, all_files)
        
        system_prompt = """You are an expert TypeScript/React developer tasked with fixing code errors.

Your task:
1. Analyze the errors provided
2. Fix ALL errors in the code
3. Ensure the fixed code:
   - Has correct TypeScript types
   - Has matching imports/exports
   - Has correct prop names matching component interfaces
   - Follows React best practices
   - Is production-ready

CRITICAL RULES:
- Only fix the errors, don't change working code
- Maintain the original functionality
- Keep the same component structure
- Use exact prop names from component interfaces
- Ensure all imports match exports
- Remove unused imports
- Follow the OUTPUT FORMAT instructions exactly"""

        user_prompt = f"""Fix the following errors in this file:

FILE: {file_path}

ERRORS TO FIX:
{error_summary}

CURRENT FILE CONTENT:
```tsx
{original_content}
```

{related_files}

Make sure to fix ALL the errors listed above."""

        logger.info(f"Fixing validation errors in {file_path}")
        return self._llm_fix_with_patch_fallback(
            system_prompt=system_prompt,
            user_prompt_base=user_prompt,
            original_content=original_content,
            file_path=file_path,
            max_tokens=8000,
            call_label="validation_fix",
            cost_tracker=cost_tracker,
        )

    def _fix_file_build_errors(
        self,
        file_path: str,
        original_content: str,
        errors: List[BuildError],
        build_output: str,
        all_files: Dict[str, str],
        cost_tracker=None
    ) -> Optional[str]:
        """Fix build errors in a single file using LLM"""
        
        # Create error summary
        error_messages = []
        for error in errors:
            location = f"Line {error.line}" if error.line else "Unknown location"
            error_messages.append(f"- {location}: {error.error_type}: {error.message}")
        error_summary = "\n".join(error_messages)
        
        # Get related files for context
        related_files = self._get_related_files(file_path, all_files)
        
        system_prompt = """You are an expert TypeScript/React developer tasked with fixing build errors.

Your task:
1. Analyze the TypeScript/build errors provided
2. Fix ALL errors in the code
3. Ensure the fixed code:
   - Compiles without TypeScript errors
   - Has correct types and interfaces
   - Has all required imports
   - Has no undefined variables or functions
   - Is production-ready

CRITICAL RULES:
- Only fix the errors, don't change working code
- Maintain the original functionality
- Keep the same component structure
- Add missing type definitions if needed
- Fix import paths if incorrect
- Follow the OUTPUT FORMAT instructions exactly"""

        user_prompt = f"""Fix the following build errors in this file:

FILE: {file_path}

BUILD ERRORS TO FIX:
{error_summary}

CURRENT FILE CONTENT:
```tsx
{original_content}
```

{related_files}

RELEVANT BUILD OUTPUT:
```
{build_output[:500]}
```

Make sure to fix ALL the build errors listed above."""

        logger.info(f"Fixing build errors in {file_path}")
        return self._llm_fix_with_patch_fallback(
            system_prompt=system_prompt,
            user_prompt_base=user_prompt,
            original_content=original_content,
            file_path=file_path,
            max_tokens=6000,
            call_label="build_fix",
            cost_tracker=cost_tracker,
        )

    def _get_related_files(self, file_path: str, all_files: Dict[str, str], max_files: int = 3) -> str:
        """Get related files for context"""
        related = []
        
        # If this is a page, get components it imports
        if file_path.startswith('src/pages/'):
            for path, content in all_files.items():
                if path.startswith('src/components/') and len(related) < max_files:
                    # Check if the page imports this component
                    component_name = path.split('/')[-1].replace('.tsx', '')
                    if component_name in all_files.get(file_path, ''):
                        related.append(f"\nRELATED FILE: {path}\n```tsx\n{content[:500]}...\n```")
        
        # If this is a component, get related components
        elif file_path.startswith('src/components/'):
            for path, content in all_files.items():
                if path.startswith('src/components/ui/') and len(related) < max_files:
                    # Check if the component imports this UI component
                    ui_name = path.split('/')[-1].replace('.tsx', '')
                    if ui_name in all_files.get(file_path, ''):
                        related.append(f"\nRELATED FILE: {path}\n```tsx\n{content[:300]}...\n```")
        
        return "\n".join(related) if related else ""
    
    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Extract code from LLM response"""
        # Try to find code block
        import re
        
        # Look for ```tsx or ```typescript code blocks
        code_block_pattern = r"```(?:tsx|typescript|ts|jsx|javascript|js)?\n(.*?)```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            # Return the first (or largest) code block
            return max(matches, key=len).strip()
        
        # If no code block found, check if entire response is code
        # (starts with import or export)
        if response.strip().startswith(('import', 'export', '/')):
            return response.strip()
        
        return None


# Singleton instance
error_fixer = ErrorFixer()

