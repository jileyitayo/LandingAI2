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
        
        # Check if shared template already exists
        if (self.shared_template_dir / "node_modules").exists():
            logger.info("[VITE PREVIEW] Shared template already exists")
            return
        
        # Create shared template directory
        self.shared_template_dir.mkdir(exist_ok=True)
        
        # Write package.json with all dependencies
        package_json = {
            "name": "preview-template",
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "lint": "eslint .",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^19.1.1",
                "react-dom": "^19.1.1",
                "react-router-dom": "^6.8.0",
                "@tanstack/react-query": "^5.0.0",
                "lucide-react": "^0.462.0",
                "class-variance-authority": "^0.7.0",
                "clsx": "^2.0.0",
                "tailwind-merge": "^2.0.0",
                "@radix-ui/react-slot": "^1.0.2",
                "@radix-ui/react-label": "^2.0.2",
                "@radix-ui/react-select": "^2.0.0",
                "@radix-ui/react-dialog": "^1.0.5",
                "@radix-ui/react-avatar": "^1.0.4",
                "@radix-ui/react-separator": "^1.0.3",
                "@radix-ui/react-switch": "^1.0.3",
                "@radix-ui/react-progress": "^1.0.3",
                "@radix-ui/react-accordion": "^1.1.2",
                "@radix-ui/react-tabs": "^1.0.4",
                "@radix-ui/react-tooltip": "^1.0.7",
                "@radix-ui/react-popover": "^1.0.7",
                "@radix-ui/react-alert-dialog": "^1.0.5",
                "@radix-ui/react-dropdown-menu": "^2.0.6",
                "@radix-ui/react-toggle": "^1.0.3",
                "@radix-ui/react-toggle-group": "^1.0.4",
                "@radix-ui/react-radio-group": "^1.1.3",
                "@radix-ui/react-context-menu": "^2.1.5",
                "sonner": "^1.3.1"
            },
            "devDependencies": {
                "@eslint/js": "^9.36.0",
                "@types/node": "^20.0.0",
                "@types/react": "^19.1.13",
                "@types/react-dom": "^19.1.9",
                "@vitejs/plugin-react": "^5.0.3",
                "autoprefixer": "^10.4.0",
                "eslint": "^9.36.0",
                "eslint-plugin-react-hooks": "^5.2.0",
                "eslint-plugin-react-refresh": "^0.4.20",
                "globals": "^16.4.0",
                "postcss": "^8.4.0",
                "tailwindcss": "^3.4.0",
                "typescript": "~5.8.3",
                "typescript-eslint": "^8.44.0",
                "vite": "^7.1.7"
            }
        }
        
        (self.shared_template_dir / "package.json").write_text(json.dumps(package_json, indent=2))
        
        # Write vite.config.ts
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
        tsconfig = {
            "files": [],
            "references": [
                {
                "path": "./tsconfig.app.json"
                },
                {
                "path": "./tsconfig.node.json"
                }
            ]
            }
        (self.shared_template_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))
        
        # Write tsconfig.node.json
        tsconfig_node = {
            "compilerOptions": {
                "composite": True,
                "skipLibCheck": True,
                "module": "ESNext",
                "moduleResolution": "bundler",
                "allowSyntheticDefaultImports": True
            },
            "include": ["vite.config.ts"]
        }
        (self.shared_template_dir / "tsconfig.node.json").write_text(json.dumps(tsconfig_node, indent=2))
        
        # Write tsconfig.node.json
        tsconfig_app = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": [
                "ES2020",
                "DOM",
                "DOM.Iterable"
                ],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "isolatedModules": True,
                "moduleDetection": "force",
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True,
                "baseUrl": ".",
                "paths": {
                    "@/*": [
                        "./src/*"
                    ]
                }
            },
            "include": [
                "src"
            ]
        }
        (self.shared_template_dir / "tsconfig.app.json").write_text(json.dumps(tsconfig_app, indent=2))
        

        # Write tailwind.config.js
        tailwind_config = '''/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
}
'''
        (self.shared_template_dir / "tailwind.config.js").write_text(tailwind_config)
        
        # Write postcss.config.js
        postcss_config = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}'''
        (self.shared_template_dir / "postcss.config.js").write_text(postcss_config)
        
        # Write index.html
        index_html = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Preview</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>'''
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
                ["npm", "run", "build"],
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
            # Don't symlink vite.config.ts - copy it instead
            # os.symlink(
            #     str(self.shared_template_dir / "vite.config.ts"),
            #     str(preview_dir / "vite.config.ts")
            # )
            # os.symlink(
            #     str(self.shared_template_dir / "tsconfig.json"),
            #     str(preview_dir / "tsconfig.json")
            # )
            # os.symlink(
            #     str(self.shared_template_dir / "tsconfig.node.json"),
            #     str(preview_dir / "tsconfig.node.json")
            # )
            # os.symlink(
            #     str(self.shared_template_dir / "tsconfig.app.json"),
            #     str(preview_dir / "tsconfig.app.json")
            # )
            # os.symlink(
            #     str(self.shared_template_dir / "tailwind.config.js"),
            #     str(preview_dir / "tailwind.config.js")
            # )
            # os.symlink(
            #     str(self.shared_template_dir / "postcss.config.js"),
            #     str(preview_dir / "postcss.config.js")
            # )
        except OSError as e:
            # On Windows, symlinks might not work, try copying instead
            logger.warning("[VITE PREVIEW] Symlink failed, copying files instead: " + str(e))
            
            # Remove existing files/directories before copying
            files_to_copy = [
                ("node_modules", "copytree"),
                ("package.json", "copy2"),
                # ("vite.config.ts", "copy2"),
                # ("tsconfig.json", "copy2"),
                # ("tsconfig.node.json", "copy2"),
                # ("tsconfig.app.json", "copy2"),
                # ("tailwind.config.js", "copy2"),
                # ("postcss.config.js", "copy2")
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
