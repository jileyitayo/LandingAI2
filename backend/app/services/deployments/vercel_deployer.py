"""
Vercel Deployment Service
Handles deployment of projects (both static HTML/CSS/JS and React) to Vercel using Vercel API v13.
"""

import httpx
import json
import base64
import time
import logging
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
from app.config import settings
from app.utils.supabase_client import get_supabase_client
from app.services.project_file_manager import ProjectFileManager

logger = logging.getLogger(__name__)


class VercelDeploymentError(Exception):
    """Custom exception for Vercel deployment errors."""
    pass


class VercelDeployer:
    """Deploy projects (static HTML or Vite + React) to Vercel from database or in-memory files."""
    
    def __init__(self):
        """Initialize the Vercel deployer."""
        self.token = settings.vercel_api_token
        self.team_id = settings.vercel_team_id
        self.api_base = "https://api.vercel.com"
        
        if not self.token:
            raise VercelDeploymentError("Vercel API token not configured")
        
        self.file_manager = ProjectFileManager()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for Vercel API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _get_api_url(self, endpoint: str) -> str:
        """Build complete API URL with team ID if configured."""
        url = f"{self.api_base}{endpoint}"
        if self.team_id:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}teamId={self.team_id}"
        return url
    
    async def _ensure_vercel_project(self, project_name: str) -> str:
        """
        Ensure a Vercel project exists, creating it if necessary.
        
        Args:
            project_name: Name for the Vercel project
            
        Returns:
            The project name/slug that was created or already existed
            
        Raises:
            VercelDeploymentError: If project creation fails
        """
        try:
            # Sanitize project name for Vercel
            sanitized_name = project_name.lower().replace(" ", "-").replace("_", "-")
            # Remove any characters that aren't alphanumeric or hyphens
            sanitized_name = "".join(c for c in sanitized_name if c.isalnum() or c == "-")
            # Remove consecutive hyphens
            while "--" in sanitized_name:
                sanitized_name = sanitized_name.replace("--", "-")
            # Remove leading/trailing hyphens
            sanitized_name = sanitized_name.strip("-")
            
            # Ensure name is not empty and has minimum length
            if not sanitized_name or len(sanitized_name) < 3:
                sanitized_name = f"website-{int(time.time())}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check if project already exists
                list_projects_url = self._get_api_url("/v9/projects")
                response = await client.get(
                    list_projects_url,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    projects_data = response.json()
                    projects = projects_data.get("projects", [])
                    
                    # Check if a project with this name exists
                    for project in projects:
                        if project.get("name") == sanitized_name:
                            logger.info(f"Vercel project '{sanitized_name}' already exists")
                            return sanitized_name
                
                # Project doesn't exist, create it
                logger.info(f"Creating new Vercel project: {sanitized_name}")
                
                create_project_url = self._get_api_url("/v9/projects")
                
                project_payload = {
                    "name": sanitized_name,
                    "framework": None,
                    "publicSource": True,  # Make the project publicly viewable
                }
                
                response = await client.post(
                    create_project_url,
                    headers=self._get_headers(),
                    json=project_payload
                )
                
                if response.status_code in [200, 201]:
                    project_data = response.json()
                    logger.info(f"Vercel project created successfully: {sanitized_name}")
                    return project_data.get("name", sanitized_name)
                else:
                    # If project creation fails, we can still try to deploy without it
                    logger.warning(f"Could not create Vercel project: {response.text}")
                    return sanitized_name
        
        except Exception as e:
            # If there's an error creating the project, log it but don't fail
            # We can still attempt deployment without explicitly creating the project
            logger.warning(f"Error ensuring Vercel project exists: {str(e)}")
            return project_name.lower().replace(" ", "-")
    
    async def _generate_static_files(self, project_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate static files from project content for HTML/CSS/JS projects.
        
        Args:
            project_data: Project data including html_content, css_content, js_content
            
        Returns:
            Dict with file names as keys and file content as values
        """
        files = {}
        
        # Get project content
        html_content = project_data.get("html_content", "")
        css_content = project_data.get("css_content", "")
        js_content = project_data.get("js_content", "")
        
        # Generate index.html
        if html_content:
            # Check if it's a full HTML document or just content
            if "<html" in html_content.lower():
                # Already a complete HTML document
                html_template = html_content
            else:
                # Wrap content in HTML structure
                project_name = project_data.get("name", "My Website")
                seo_title = project_data.get("seo_title", project_name)
                seo_description = project_data.get("seo_description", "")
                
                html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{seo_description}">
    <title>{seo_title}</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
{html_content}
<script src="/script.js"></script>
</body>
</html>"""
            
            files["index.html"] = html_template
        
        # Generate styles.css
        if css_content:
            files["styles.css"] = css_content
        else:
            files["styles.css"] = "/* No custom styles */"
        
        # Generate script.js
        if js_content:
            files["script.js"] = js_content
        else:
            files["script.js"] = "// No custom JavaScript"
        
        # Generate vercel.json for configuration
        vercel_config = {
            "version": 2,
            "builds": [
                {"src": "index.html", "use": "@vercel/static"},
                {"src": "styles.css", "use": "@vercel/static"},
                {"src": "script.js", "use": "@vercel/static"}
            ],
            "routes": [
                {
                    "src": "/(.*)",
                    "dest": "/$1"
                }
            ]
        }
        files["vercel.json"] = json.dumps(vercel_config, indent=2)
        
        # Generate package.json (required by Vercel)
        project_subdomain = project_data.get("subdomain", "website")
        if not project_subdomain:
            project_subdomain = project_data.get("name", "website").lower().replace(" ", "-")
        package_json = {
            "name": project_subdomain,
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "build": "echo 'Static site - no build required'"
            }
        }
        logger.info(f"Generated package.json for project {project_data.get('id')}")
        files["package.json"] = json.dumps(package_json, indent=2)
        
        return files
    
    async def _wait_for_deployment(self, deployment_id: str, max_wait: int = 120) -> None:
        """
        Wait for a deployment to be ready.
        
        Args:
            deployment_id: Vercel deployment ID
            max_wait: Maximum time to wait in seconds
        """
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while time.time() - start_time < max_wait:
                try:
                    status_url = self._get_api_url(f"/v13/deployments/{deployment_id}")
                    response = await client.get(
                        status_url,
                        headers=self._get_headers()
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        state = data.get("readyState", "").upper()
                        
                        if state == "READY":
                            logger.info(f"Deployment {deployment_id} is ready")
                            return
                        elif state == "ERROR":
                            # Extract error details from Vercel response
                            error_info = data.get("error", {})
                            error_message = error_info.get("message", "Unknown error")
                            error_code = error_info.get("code", "")
                            inspector_url = data.get("inspectorUrl", "")

                            # Log full error details for debugging
                            logger.error(f"Deployment {deployment_id} failed with state ERROR")
                            logger.error(f"Error code: {error_code}")
                            logger.error(f"Error message: {error_message}")
                            if inspector_url:
                                logger.error(f"View build logs at: {inspector_url}")
                            
                            logger.error(f"Full response data: {json.dumps(data, indent=2)}")
                            
                            raise VercelDeploymentError(
                                f"Deployment build failed: {error_message} (code: {error_code})"
                            )
                    
                    # Wait before next check
                    await asyncio.sleep(5)
                
                except VercelDeploymentError:
                    raise
                except Exception as e:
                    logger.warning(f"Error checking deployment status: {str(e)}")
        
        logger.warning(f"Deployment {deployment_id} status check timed out")
    
    async def _make_project_public(self, project_id: str) -> None:
        """
        Make a Vercel project publicly accessible.
        
        Args:
            project_id: Vercel project ID
        """
        try:
            logger.info(f"Making project publicly viewable: {project_id}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                project_payload = {
                    "ssoProtection": None,
                    "passwordProtection": None,
                    "publicSource": True,
                }
                update_project_url = self._get_api_url(f"/v9/projects/{project_id}")

                response = await client.patch(
                    update_project_url,
                    headers=self._get_headers(),
                    json=project_payload
                )

                if response and response.status_code not in [200, 201]:
                    logger.warning(f"Failed to make project public: {response.text}")
                else:
                    logger.info(f"Project {project_id} is now public")
        except Exception as e:
            logger.warning(f"Error making project public: {str(e)}")
    
    async def deploy_from_files(
        self,
        project_files: Dict[str, str],
        project_name: str,
        is_react: bool = True,
        progress_cb=None
    ) -> Dict[str, Any]:
        """
        Deploy project files to Vercel from in-memory dictionary.
        
        Args:
            project_files: Dictionary where keys are file paths and values are file contents
                          Example: {"package.json": "...", "src/App.tsx": "..."}
            project_name: Name for the Vercel project
            is_react: Whether this is a React project (uses Vite) or static HTML
            
        Returns:
            Dictionary containing deployment information (URL, status, etc.)
            
        Raises:
            VercelDeploymentError: If deployment fails
        """
        try:
            logger.info(f"Starting deployment for project: {project_name}")
            logger.info(f"Uploading {len(project_files)} files...")
            
            # Prepare files for upload
            files = []
            for path, content in project_files.items():
                # Encode file content to base64
                encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                files.append({
                    "file": path,
                    "data": encoded_content,
                    "encoding": "base64"
                })
            
            # Ensure the Vercel project exists
            vercel_project_name = await self._ensure_vercel_project(project_name)
            
            # Prepare deployment payload
            if is_react:
                payload = {
                    "name": vercel_project_name,
                    "files": files,
                    "projectSettings": {
                        "framework": "vite",
                        "buildCommand": "npm run build",
                        "outputDirectory": "dist",
                        "installCommand": "npm install"
                    },
                    "target": "production"
                }
            else:
                payload = {
                    "name": vercel_project_name,
                    "files": files,
                    "projectSettings": {
                        "framework": None,
                        "buildCommand": None,
                        "outputDirectory": "."
                    },
                    "target": "production"
                }
            
            # Create deployment
            async with httpx.AsyncClient(timeout=60.0) as client:
                deploy_url = self._get_api_url("/v13/deployments")
                
                response = await client.post(
                    deploy_url,
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code not in [200, 201]:
                    error_message = response.text
                    logger.error(f"Vercel deployment failed: {error_message}")
                    raise VercelDeploymentError(f"Deployment failed: {error_message}")
                
                deployment = response.json()
            
            # Extract deployment information
            deployment_id = deployment.get("id")
            deployment_project_id = deployment.get("projectId")
            deployment_url = deployment.get("url")
            
            # Add https:// prefix if not present
            if deployment_url and not deployment_url.startswith("http"):
                deployment_url = f"https://{deployment_url}"
            
            logger.info(f"Deployment created successfully: {deployment_url}")
            
            # Files accepted — Vercel is now building
            if progress_cb:
                try:
                    progress_cb("building", "Vercel is building your site")
                except Exception as e:
                    logger.warning(f"Deploy progress callback failed: {e}")

            # Make the project publicly viewable
            if deployment_project_id:
                await self._make_project_public(deployment_project_id)

            # Wait for deployment to be ready
            await self._wait_for_deployment(deployment_id)
            
            logger.info(f"Deployment completed: {deployment_url}")
            
            return {
                "deployment_id": deployment_id,
                "deployment_url": deployment_url,
                "project_id": deployment_project_id,
                "status": "ready",
                "deployed_at": datetime.utcnow().isoformat()
            }
        
        except VercelDeploymentError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during deployment: {str(e)}")
            raise VercelDeploymentError(f"Deployment failed: {str(e)}")
    
    async def deploy_website(self, project_id: str, progress_cb=None) -> Dict[str, Any]:
        """
        Deploy a project to Vercel from database.

        This method fetches the project from the database and determines whether
        it's a React project or static HTML/CSS/JS project, then deploys accordingly.

        Args:
            project_id: UUID of the project to deploy
            progress_cb: Optional callback(stage: str, detail: str) invoked at
                stage transitions ("uploading", "building")

        Returns:
            Dict containing deployment_url, deployment_id, and other deployment info

        Raises:
            VercelDeploymentError: If deployment fails
        """
        supabase = get_supabase_client()

        def _progress(stage: str, detail: str):
            if progress_cb:
                try:
                    progress_cb(stage, detail)
                except Exception as e:
                    logger.warning(f"Deploy progress callback failed: {e}")

        try:
            # Fetch project from database
            logger.info(f"Fetching project {project_id} for deployment")
            response = supabase.table("projects").select("*").eq("id", project_id).execute()

            if not response.data:
                raise VercelDeploymentError(f"Project {project_id} not found")

            project = response.data[0]
            project_type = project.get("project_type", "static")
            project_name = project.get("subdomain") or project.get("name", "website").lower().replace(" ", "-")

            # Determine if this is a React project
            is_react = project_type == "react"

            _progress("uploading", "Preparing and uploading project files")

            if is_react:
                # Fetch React project files from database
                logger.info(f"Fetching React project files for project {project_id}")
                project_files = await self.file_manager.get_project_files(project_id)

                if not project_files:
                    raise VercelDeploymentError("No React project files found. Please generate the project first.")

                logger.info(f"Found {len(project_files)} React files to deploy")
            else:
                # Generate static files from HTML/CSS/JS content
                if not project.get("html_content"):
                    raise VercelDeploymentError("Project must have HTML content to deploy")

                logger.info(f"Generating static files for project {project_id}")
                project_files = await self._generate_static_files(project)

            # Deploy using the unified deployment method
            deployment_result = await self.deploy_from_files(
                project_files=project_files,
                project_name=project_name,
                is_react=is_react,
                progress_cb=_progress
            )

            # Update project in database
            now = datetime.utcnow().isoformat()
            update_data = {
                "deployment_id": deployment_result["deployment_id"],
                "deployment_url": deployment_result["deployment_url"],
                "last_deployed_at": now,
                "updated_at": now,
                "published": True
            }

            supabase.table("projects").update(update_data).eq("id", project_id).execute()

            logger.info(f"Project {project_id} deployment information updated in database")
            # Note: deploy_from_files already polls Vercel until READY
            # (_wait_for_deployment) — no artificial sleep needed.

            return {
                "deployment_id": deployment_result["deployment_id"],
                "deployment_url": deployment_result["deployment_url"],
                "status": "ready",
                "deployed_at": now
            }

        except VercelDeploymentError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during deployment: {str(e)}")
            raise VercelDeploymentError(f"Deployment failed: {str(e)}")
    
    async def delete_deployment(self, deployment_id: str) -> bool:
        """
        Delete a deployment from Vercel.
        
        Args:
            deployment_id: Vercel deployment ID
            
        Returns:
            True if deletion was successful
            
        Raises:
            VercelDeploymentError: If deletion fails
        """
        try:
            logger.info(f"Deleting deployment {deployment_id}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                delete_url = self._get_api_url(f"/v13/deployments/{deployment_id}")

                # Get deployment info first to find the project
                deployment_response = await client.get(
                    delete_url,
                    headers=self._get_headers()
                )
                
                # Delete the deployment
                response = await client.delete(
                    delete_url,
                    headers=self._get_headers()
                )
                
                if response.status_code not in [200, 204]:
                    error_message = response.text
                    logger.error(f"Failed to delete deployment: {error_message}")
                    raise VercelDeploymentError(f"Failed to delete deployment: {error_message}")

                # Delete the associated project if we got the deployment info
                if deployment_response.status_code == 200:
                    data = deployment_response.json()
                    project_id = data.get("projectId")
                    
                    if project_id:
                        project_url = self._get_api_url(f"/v9/projects/{project_id}")
                        project_response = await client.delete(
                            project_url,
                            headers=self._get_headers()
                        )

                        if project_response.status_code not in [200, 204]:
                            error_message = project_response.text
                            logger.error(f"Failed to delete project: {error_message}")
                            # Don't raise error here - deployment was deleted successfully
            
            logger.info(f"Deployment {deployment_id} deleted successfully")
            return True
        
        except VercelDeploymentError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting deployment: {str(e)}")
            raise VercelDeploymentError(f"Failed to delete deployment: {str(e)}")
    
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get the status of a deployment.
        
        Args:
            deployment_id: Vercel deployment ID
            
        Returns:
            Dict containing deployment status information
            
        Raises:
            VercelDeploymentError: If status check fails
        """
        try:
            logger.info(f"Checking status of deployment {deployment_id}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                status_url = self._get_api_url(f"/v13/deployments/{deployment_id}")
                
                response = await client.get(
                    status_url,
                    headers=self._get_headers()
                )
                
                if response.status_code != 200:
                    error_message = response.text
                    logger.error(f"Failed to get deployment status: {error_message}")
                    raise VercelDeploymentError(f"Failed to get deployment status: {error_message}")
                
                data = response.json()
            
            # Note: Vercel's "ready" field is a timestamp (ms), not a boolean —
            # readiness is derived from readyState.
            state = data.get("readyState", "UNKNOWN")
            return {
                "deployment_id": data.get("id"),
                "url": data.get("url"),
                "state": state,
                "created_at": data.get("createdAt"),
                "ready": state == "READY"
            }
        
        except VercelDeploymentError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking deployment status: {str(e)}")
            raise VercelDeploymentError(f"Failed to check deployment status: {str(e)}")


# Backwards compatibility alias
VercelDeploymentService = VercelDeployer
