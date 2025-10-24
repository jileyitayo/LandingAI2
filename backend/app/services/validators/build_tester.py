"""
Build Tester Service
Tests generated React projects by running actual npm build commands.
"""

import os
import subprocess
import tempfile
import shutil
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BuildError:
    """Represents a build error"""
    file_path: str
    line: Optional[int]
    column: Optional[int]
    error_type: str
    message: str
    code: Optional[str] = None
    
    def __repr__(self):
        location = f"{self.file_path}"
        if self.line:
            location += f":{self.line}"
            if self.column:
                location += f":{self.column}"
        return f"[{self.error_type}] {location} - {self.message}"


@dataclass
class BuildTestResult:
    """Result of build test"""
    success: bool
    errors: List[BuildError]
    warnings: List[str]
    build_output: str
    install_output: str
    duration: float  # seconds
    
    def __repr__(self):
        if self.success:
            return f"Build successful ({self.duration:.2f}s)"
        return f"Build failed with {len(self.errors)} errors ({self.duration:.2f}s)"


class BuildTester:
    """Tests React projects by running actual builds"""
    
    def __init__(self, timeout: int = 120):
        """
        Initialize build tester
        
        Args:
            timeout: Maximum time in seconds for build process
        """
        self.timeout = timeout
    
    def test_build(self, files: Dict[str, str], project_name: str = "test-project") -> BuildTestResult:
        """
        Test build by creating temporary project and running npm build
        
        Args:
            files: Dictionary of file paths to contents
            project_name: Name for the temporary project
            
        Returns:
            BuildTestResult with success status and errors
        """
        import time
        start_time = time.time()
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"{project_name}_")
        logger.info(f"[BUILD TESTER] Creating temporary project in {temp_dir}")
        
        try:
            # Write all files to temp directory
            self._write_files(temp_dir, files)
            
            # Run npm install
            logger.info("[BUILD TESTER] Running npm install...")
            install_success, install_output = self._run_npm_install(temp_dir)
            
            if not install_success:
                duration = time.time() - start_time
                errors = self._parse_install_errors(install_output)
                return BuildTestResult(
                    success=False,
                    errors=errors,
                    warnings=[],
                    build_output="",
                    install_output=install_output,
                    duration=duration
                )
            
            # Run npm build
            logger.info("[BUILD TESTER] Running npm run build...")
            build_success, build_output = self._run_npm_build(temp_dir)
            
            duration = time.time() - start_time
            
            if build_success:
                logger.info(f"[BUILD TESTER] ✓ Build successful in {duration:.2f}s")
                return BuildTestResult(
                    success=True,
                    errors=[],
                    warnings=self._parse_warnings(build_output),
                    build_output=build_output,
                    install_output=install_output,
                    duration=duration
                )
            else:
                logger.error(f"[BUILD TESTER] ✗ Build failed in {duration:.2f}s")
                errors = self._parse_build_errors(build_output)
                return BuildTestResult(
                    success=False,
                    errors=errors,
                    warnings=self._parse_warnings(build_output),
                    build_output=build_output,
                    install_output=install_output,
                    duration=duration
                )
        
        finally:
            # Cleanup temp directory
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"[BUILD TESTER] Cleaned up temporary directory")
            except Exception as e:
                logger.warning(f"[BUILD TESTER] Failed to cleanup {temp_dir}: {e}")
    
    def _write_files(self, base_dir: str, files: Dict[str, str]):
        """Write all project files to disk"""
        for file_path, content in files.items():
            full_path = os.path.join(base_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _run_npm_install(self, project_dir: str) -> Tuple[bool, str]:
        """Run npm install"""
        try:
            result = subprocess.run(
                ['npm', 'install'],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            if not success:
                logger.error(f"[BUILD TESTER] npm install failed:\n{output}")
            
            return success, output
            
        except subprocess.TimeoutExpired:
            logger.error(f"[BUILD TESTER] npm install timed out after {self.timeout}s")
            return False, f"npm install timed out after {self.timeout} seconds"
        except Exception as e:
            logger.error(f"[BUILD TESTER] npm install error: {e}")
            return False, str(e)
    
    def _run_npm_build(self, project_dir: str) -> Tuple[bool, str]:
        """Run npm run build"""
        try:
            result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            if not success:
                logger.error(f"[BUILD TESTER] npm run build failed")
            
            return success, output
            
        except subprocess.TimeoutExpired:
            logger.error(f"[BUILD TESTER] npm run build timed out after {self.timeout}s")
            return False, f"npm run build timed out after {self.timeout} seconds"
        except Exception as e:
            logger.error(f"[BUILD TESTER] npm run build error: {e}")
            return False, str(e)
    
    def _parse_build_errors(self, output: str) -> List[BuildError]:
        """Parse build output to extract errors"""
        errors = []
        
        # TypeScript error pattern: src/file.tsx:12:5 - error TS2304: Cannot find name 'X'
        ts_error_pattern = r"([^:]+):(\d+):(\d+)\s*-\s*error\s+TS(\d+):\s*(.+)"
        
        for match in re.finditer(ts_error_pattern, output):
            file_path = match.group(1).strip()
            line = int(match.group(2))
            column = int(match.group(3))
            error_code = match.group(4)
            message = match.group(5).strip()
            
            errors.append(BuildError(
                file_path=file_path,
                line=line,
                column=column,
                error_type=f"TS{error_code}",
                message=message,
                code=error_code
            ))
        
        # Vite/build error pattern: error during build:
        vite_error_pattern = r"error during build:\s*\n([^\n]+)"
        for match in re.finditer(vite_error_pattern, output, re.MULTILINE):
            message = match.group(1).strip()
            errors.append(BuildError(
                file_path="build",
                line=None,
                column=None,
                error_type="BUILD_ERROR",
                message=message
            ))
        
        # Module not found pattern
        module_error_pattern = r"Cannot find module ['\"](.*?)['\"]"
        for match in re.finditer(module_error_pattern, output):
            module = match.group(1)
            errors.append(BuildError(
                file_path="unknown",
                line=None,
                column=None,
                error_type="MODULE_NOT_FOUND",
                message=f"Cannot find module '{module}'"
            ))
        
        # Generic error pattern (fallback)
        if not errors and "error" in output.lower():
            # Extract first error-looking line
            for line in output.split('\n'):
                if 'error' in line.lower() and line.strip():
                    errors.append(BuildError(
                        file_path="unknown",
                        line=None,
                        column=None,
                        error_type="BUILD_ERROR",
                        message=line.strip()
                    ))
                    break
        
        return errors
    
    def _parse_install_errors(self, output: str) -> List[BuildError]:
        """Parse npm install errors"""
        errors = []
        
        # Package not found
        package_error_pattern = r"npm ERR!.*404.*['\"](.*?)['\"]"
        for match in re.finditer(package_error_pattern, output):
            package = match.group(1)
            errors.append(BuildError(
                file_path="package.json",
                line=None,
                column=None,
                error_type="PACKAGE_NOT_FOUND",
                message=f"Package not found: {package}"
            ))
        
        # Generic npm errors
        if not errors and "npm ERR!" in output:
            for line in output.split('\n'):
                if 'npm ERR!' in line and line.strip():
                    errors.append(BuildError(
                        file_path="package.json",
                        line=None,
                        column=None,
                        error_type="NPM_ERROR",
                        message=line.replace('npm ERR!', '').strip()
                    ))
                    break
        
        return errors
    
    def _parse_warnings(self, output: str) -> List[str]:
        """Parse build warnings"""
        warnings = []
        
        # TypeScript warnings
        warning_pattern = r"warning TS\d+:.*"
        for match in re.finditer(warning_pattern, output):
            warnings.append(match.group(0))
        
        return warnings


# Singleton instance
build_tester = BuildTester()

