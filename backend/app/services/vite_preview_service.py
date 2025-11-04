"""
Vite Preview Service
Creates temporary preview builds of React projects using shared node_modules for fast builds.
"""

from pathlib import Path
import subprocess
import shutil
import uuid
import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.services.react_file_manager import ReactFileManager
from app.services.react_models import WebsiteStructure
from app.services.react_models import PageStructure
from app.services.react_models import PageComponent
from app.services.react_models import NavItem
import logging

logger = logging.getLogger(__name__)


class VitePreviewService:
    """Service for creating temporary preview builds of React projects"""
    
    def __init__(self):
        # Get the absolute path to the backend directory
        backend_dir = Path(__file__).parent.parent.parent
        self.preview_base_dir = backend_dir / "previews"
        self.shared_template_dir = self.preview_base_dir / "shared_template"
        self.builds_dir = self.preview_base_dir / "builds"
        self.active_previews = {}  # {preview_id: {"created_at": timestamp, "project_id": str}}
        
        # Create directories
        self.preview_base_dir.mkdir(exist_ok=True)
        self.builds_dir.mkdir(exist_ok=True)
        
        # Initialize shared template on first use
        self._ensure_shared_template()
    
    def _ensure_shared_template(self):
        """Create and initialize shared template with node_modules (one-time setup)"""
        logger.info("[VITE PREVIEW] Ensuring shared template is initialized...")
        always_recreate = False
        
        # Check if shared template already exists
        if (self.shared_template_dir / "node_modules").exists() and not always_recreate:
            logger.info("[VITE PREVIEW] Shared template already exists")
            return
        
        logger.info("[VITE PREVIEW] Creating shared template directory...")

        # Create shared template directory
        self.shared_template_dir.mkdir(exist_ok=True)
        
        # Write package.json with all dependencies
        react_file_manager = ReactFileManager()
        sample_structure = WebsiteStructure(
            name="Preview Website",
            tagline="Preview Website",
            description="This is a preview website",
            color_scheme="blue",
            secondary_color="indigo",
            accent_color="emerald",
            pages=[PageStructure(name="Home", path="/", title="Home", description="Home page", has_header=True, has_footer=True, components=[])],
            navigation=[NavItem(label="Home", path="/")],
            header=PageComponent(name="Header", type="header", props=[]),
            footer=PageComponent(name="Footer", type="footer", props=[])
        )
        config_files = react_file_manager.generate_config_files(sample_structure)

        (self.shared_template_dir / "package.json").write_text(config_files["package.json"])
        
        # Write vite.config.ts
        # This is needed specifically for vite preview 
        vite_config = '''import { defineConfig } from 'vite'
            import react from '@vitejs/plugin-react'
            import path from 'path'

            export default defineConfig({
            plugins: [react()],
            resolve: {
                alias: {
                '@': path.resolve(__dirname, './src'),
                },
            },
            build: {
                outDir: 'dist',
                sourcemap: false,
                minify: 'esbuild',
            },
            server: {
                port: 3000,
                host: true,
            },
            })'''
        (self.shared_template_dir / "vite.config.ts").write_text(vite_config)
        
        # Write tsconfig.json
        tsconfig = config_files["tsconfig.json"]
        (self.shared_template_dir / "tsconfig.json").write_text(tsconfig)
        
        # Write tsconfig.node.json
        tsconfig_node = config_files["tsconfig.node.json"]
        (self.shared_template_dir / "tsconfig.node.json").write_text(tsconfig_node)
        
        # Write tsconfig.node.json
        tsconfig_app = config_files["tsconfig.app.json"]
        (self.shared_template_dir / "tsconfig.app.json").write_text(tsconfig_app)
        

        # Write tailwind.config.js
        tailwind_config = config_files["tailwind.config.js"]
        (self.shared_template_dir / "tailwind.config.js").write_text(tailwind_config)

        # Write postcss.config.js
        postcss_config = config_files["postcss.config.js"]
        (self.shared_template_dir / "postcss.config.js").write_text(postcss_config)
        
        # Write index.html
        index_html = config_files["index.html"]
        (self.shared_template_dir / "index.html").write_text(index_html)
        
        # Run npm install
        logger.info("[VITE PREVIEW] Installing shared dependencies...")
        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=self.shared_template_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                logger.error("[VITE PREVIEW] npm install failed: " + str(result.stderr))
                raise Exception("npm install failed: " + str(result.stderr))
            
            # Get directory size
            total_size = sum(f.stat().st_size for f in self.shared_template_dir.rglob('*') if f.is_file())
            logger.info("[VITE PREVIEW] Shared template initialized (" + str(round(total_size / 1024 / 1024, 1)) + " MB)")
            
        except subprocess.TimeoutExpired:
            logger.error("[VITE PREVIEW] npm install timed out")
            raise Exception("npm install timed out")
        except Exception as e:
            logger.error("[VITE PREVIEW] Failed to initialize shared template: " + str(e))
            raise
    
    def create_preview(self, project_id, files):
        """
        Create a temporary preview build using shared node_modules.
        
        Args:
            project_id: The project ID
            files: Dictionary of file paths to contents
            
        Returns:
            {
                "preview_id": str,
                "preview_url": str (e.g., "/previews/builds/{id}/dist/index.html"),
                "expires_at": str (ISO timestamp)
            }
        """
        logger.info("[VITE PREVIEW] Creating preview for project " + str(project_id))
        
        # Generate preview ID
        preview_id = str(uuid.uuid4())
        preview_dir = self.builds_dir / preview_id
        
        try:
            # Clean up any existing directory with the same ID
            if preview_dir.exists():
                if preview_dir.is_symlink():
                    preview_dir.unlink()
                else:
                    shutil.rmtree(preview_dir)
            
            # Create preview directory
            preview_dir.mkdir(exist_ok=True)
            
            # Write user's source files
            self._write_project_files(preview_dir, files)
            
            # Create symlinks to shared template
            self._create_symlinks(preview_dir)

            # Write vite.config.ts with correct base path for this specific preview
            vite_config_content = f'''import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import {{ fileURLToPath }} from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default defineConfig({{
  plugins: [react()],
  resolve: {{
    alias: {{
      '@': path.resolve(__dirname, './src'),
    }},
  }},
  base: '/previews/builds/{preview_id}/dist/',
  build: {{
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
  }},
  server: {{
    port: 3000,
    host: true,
  }},
}})'''
        
            (preview_dir / "vite.config.ts").write_text(vite_config_content)
            # Run npm run build
            logger.info("[VITE PREVIEW] Building preview " + str(preview_id) + "...")
            start_time = time.time()
            
            result = subprocess.run(
                ["npm", "run", "build:dev"],
                cwd=preview_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            build_time = time.time() - start_time
            print("build_time", build_time)
            
            if result.returncode != 0:
                logger.error("[VITE PREVIEW] Build failed for " + str(preview_id) + ": " + str(result.stderr))
                # Clean up failed build
                shutil.rmtree(preview_dir, ignore_errors=True)
                raise Exception("Build failed: " + str(result.stderr))
            
            # Check if dist directory was created
            dist_dir = preview_dir / "dist"
            if not dist_dir.exists():
                logger.error("[VITE PREVIEW] Build completed but no dist directory found")
                shutil.rmtree(preview_dir, ignore_errors=True)
                raise Exception("Build completed but no dist directory found")
            
            # Track preview
            expires_at = datetime.utcnow() + timedelta(hours=1)
            self.active_previews[preview_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "project_id": project_id,
                "expires_at": expires_at.isoformat()
            }
            
            # Inject the selector script into the built HTML
            preview_path = dist_dir / "index.html"
            
            if preview_path.exists():
                # Read the built HTML
                html_content = preview_path.read_text(encoding="utf-8")
                
                # Inject the selector script before </body>
                selector_injection_path = self.shared_template_dir / "selector-injection.js"
                selector_script = ""
                if selector_injection_path.exists():
                    selector_script = "<script>\n" + selector_injection_path.read_text(encoding="utf-8") + "\n</script>"
                    html_content = html_content.replace('</body>', f'{selector_script}</body>')
                    preview_path.write_text(html_content, encoding="utf-8")
                    logger.info("[VITE PREVIEW] Selector script injected successfully")
                else:
                    logger.warning("[VITE PREVIEW] selector-injection.js not found in shared_template. Injection skipped.")
            else:
                logger.warning("[VITE PREVIEW] index.html not found in dist directory")

            # Get project name
            logger.info("[VITE PREVIEW] Preview " + str(preview_id) + " built successfully in " + str(round(build_time, 1)) + "s")
            
            return {
                "preview_id": preview_id,
                "preview_url": "/previews/builds/" + str(preview_id) + "/dist/index.html",
                "expires_at": expires_at.isoformat()
            }
            
        except subprocess.TimeoutExpired:
            logger.error("[VITE PREVIEW] Build timed out for " + str(preview_id))
            shutil.rmtree(preview_dir, ignore_errors=True)
            raise Exception("Build timed out after 5 minutes")
        except Exception as e:
            logger.error("[VITE PREVIEW] Failed to create preview " + str(preview_id) + ": " + str(e))
            shutil.rmtree(preview_dir, ignore_errors=True)
            raise
    
    def _write_project_files(self, preview_dir, files):
        """Write user's project files to preview directory"""
        for file_path, content in files.items():
            # Skip config files that will be symlinked
            if file_path in ["package.json", "vite.config.ts"]: #, "tsconfig.json", "tsconfig.node.json", "tsconfig.app.json", "tailwind.config.js", "postcss.config.js"]:
                continue

            if file_path == "src/App.tsx":
                content = content.replace("BrowserRouter", "HashRouter")
                
            full_path = preview_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
    
    def _create_symlinks(self, preview_dir):
        """Create symlinks to shared template files"""
        try:
            # Create symlinks to shared template
            os.symlink(
                str(self.shared_template_dir / "node_modules"),
                str(preview_dir / "node_modules")
            )
            os.symlink(
                str(self.shared_template_dir / "package.json"),
                str(preview_dir / "package.json")
            )
        except OSError as e:
            # On Windows, symlinks might not work, try copying instead
            logger.warning("[VITE PREVIEW] Symlink failed, copying files instead: " + str(e))
            
            # Remove existing files/directories before copying
            files_to_copy = [
                ("node_modules", "copytree"),
                ("package.json", "copy2")
            ]
            
            for file_name, copy_method in files_to_copy:
                target_path = preview_dir / file_name
                source_path = self.shared_template_dir / file_name
                
                # Remove existing file/directory if it exists
                if target_path.exists():
                    if target_path.is_symlink():
                        # Remove symlink
                        target_path.unlink()
                    elif target_path.is_dir():
                        # Remove directory
                        shutil.rmtree(target_path)
                    else:
                        # Remove file
                        target_path.unlink()
                
                # Copy the file/directory
                if copy_method == "copytree":
                    shutil.copytree(source_path, target_path)
                else:
                    shutil.copy2(source_path, target_path)
    
    def delete_preview(self, preview_id):
        """Remove a preview build directory"""
        try:
            preview_dir = self.builds_dir / preview_id
            if preview_dir.exists():
                shutil.rmtree(preview_dir)
                logger.info("[VITE PREVIEW] Deleted preview " + str(preview_id))
            
            # Remove from active previews
            if preview_id in self.active_previews:
                del self.active_previews[preview_id]
            
            return True
        except Exception as e:
            logger.error("[VITE PREVIEW] Failed to delete preview " + str(preview_id) + ": " + str(e))
            return False
    
    def cleanup_old_previews(self, max_age_hours=1):
        """Remove previews older than max_age_hours"""
        logger.info("[VITE PREVIEW] Cleaning up previews older than " + str(max_age_hours) + " hours...")
        
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=max_age_hours)
        
        # Clean up based on active_previews tracking
        to_remove = []
        for preview_id, info in self.active_previews.items():
            created_at = datetime.fromisoformat(info["created_at"])
            if created_at < cutoff_time:
                to_remove.append(preview_id)
        
        # Remove old previews
        for preview_id in to_remove:
            self.delete_preview(preview_id)
        
        # Also clean up any orphaned directories
        for preview_dir in self.builds_dir.iterdir():
            if preview_dir.is_dir() and preview_dir.name not in self.active_previews:
                # Check if directory is older than max_age_hours
                if preview_dir.stat().st_mtime < (current_time - timedelta(hours=max_age_hours)).timestamp():
                    try:
                        shutil.rmtree(preview_dir)
                        logger.info("[VITE PREVIEW] Cleaned up orphaned preview " + str(preview_dir.name))
                    except Exception as e:
                        logger.error("[VITE PREVIEW] Failed to clean up orphaned preview " + str(preview_dir.name) + ": " + str(e))
        
        logger.info("[VITE PREVIEW] Cleanup completed, removed " + str(len(to_remove)) + " old previews")
    
    def get_preview_status(self, preview_id):
        """Get status of a preview"""
        if preview_id not in self.active_previews:
            return None
        
        info = self.active_previews[preview_id]
        preview_dir = self.builds_dir / preview_id
        
        return {
            "exists": preview_dir.exists(),
            "preview_url": "/previews/builds/" + str(preview_id) + "/dist/index.html",
            "created_at": info["created_at"],
            "expires_at": info["expires_at"]
        }
    
    def update_shared_template(self):
        """
        Update shared template dependencies (run when package.json changes).
        Removes node_modules and runs npm install fresh.
        """
        logger.info("[VITE PREVIEW] Updating shared template...")
        
        # Remove existing node_modules
        if (self.shared_template_dir / "node_modules").exists():
            shutil.rmtree(self.shared_template_dir / "node_modules")
        
        # Re-run npm install
        self._ensure_shared_template()


# Singleton instance
vite_preview_service = VitePreviewService()
