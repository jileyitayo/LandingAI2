"""
Vercel Deployment Service
Handles deployment of projects to Vercel using Vercel API v2.
"""

import httpx
import json
import logging
import time
from time import sleep
from typing import Optional, Dict, Any
from datetime import datetime
from app.config import settings
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class VercelDeploymentError(Exception):
    """Custom exception for Vercel deployment errors."""
    pass


class VercelDeploymentService:
    """Service for managing Vercel deployments."""
    
    def __init__(self):
        """Initialize Vercel deployment service."""
        self.api_token = settings.vercel_api_token
        self.team_id = settings.vercel_team_id
        self.base_url = "https://api.vercel.com"
        
        if not self.api_token:
            raise VercelDeploymentError("Vercel API token not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for Vercel API requests."""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        return headers
    
    def _get_api_url(self, endpoint: str) -> str:
        """Build complete API URL with team ID if configured."""
        url = f"{self.base_url}{endpoint}"
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
                    "ssoProtection": None,
                    "passwordProtection": None,
                    "publicSource": True, # Make the project publicly viewable
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
        Generate static files from project content.
        
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
        # Extract just the body content if full HTML is provided
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
                { "src": "index.html", "use": "@vercel/static" },
                { "src": "styles.css", "use": "@vercel/static" },
                { "src": "script.js", "use": "@vercel/static" }
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

    async def deploy_website(self, project_id: str) -> Dict[str, Any]:
        """
        Deploy a project to Vercel.
        
        Args:
            project_id: UUID of the project to deploy
            
        Returns:
            Dict containing deployment_url, deployment_id, and other deployment info
            
        Raises:
            VercelDeploymentError: If deployment fails
        """
        supabase = get_supabase_client()
        
        try:
            # Fetch project from database
            logger.info(f"Fetching project {project_id} for deployment")
            response = supabase.table("projects").select("*").eq("id", project_id).execute()
            
            if not response.data:
                raise VercelDeploymentError(f"Project {project_id} not found")
            
            project = response.data[0]
            
            # Validate project has content
            if not project.get("html_content"):
                raise VercelDeploymentError("Project must have HTML content to deploy")
            
            # Generate static files
            logger.info(f"Generating static files for project {project_id}")
            files = await self._generate_static_files(project)
            
            # Prepare deployment data
            logger.info(f"Preparing deployment data for project {project_id}")
            project_name = project.get("subdomain") or project.get("name", "website").lower().replace(" ", "-")
            
            # Ensure the Vercel project exists or create it
            logger.info(f"Ensuring Vercel project exists for project {project_name}")
            vercel_project_name = await self._ensure_vercel_project(project_name)
            
            # Create deployment payload
            deployment_payload = {
                "name": vercel_project_name,
                "files": [],
                "projectSettings": {
                    "framework": None,
                    "buildCommand": None,
                    "outputDirectory": "."
                },
                "target": "production",
                "public": True  # Explicitly set deployment as public
            }
            
            # Add files to payload
            for filename, content in files.items():
                deployment_payload["files"].append({
                    "file": filename,
                    "data": content
                })
            
            # Check if deployment already exists
            existing_deployment_id = project.get("deployment_id")
            
            # Create deployment via Vercel API
            logger.info(f"Creating deployment on Vercel for project {project_id}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                deploy_url = self._get_api_url("/v13/deployments")
                
                response = await client.post(
                    deploy_url,
                    headers=self._get_headers(),
                    json=deployment_payload
                )
                
                if response.status_code not in [200, 201]:
                    error_message = response.text
                    logger.error(f"Vercel deployment failed: {error_message}")
                    raise VercelDeploymentError(f"Deployment failed: {error_message}")
                
                deployment_data = response.json()
            
            logger.info(f"Deployment data: {deployment_data}")

            # Extract deployment information
            deployment_id = deployment_data.get("id")
            deployment_project_id = deployment_data.get("projectId")
            deployment_url = deployment_data.get("url")
            
            # Add https:// prefix if not present
            if deployment_url and not deployment_url.startswith("http"):
                deployment_url = f"https://{deployment_url}"
            
            logger.info(f"Deployment created successfully: {deployment_url}")
            
            # Wait for deployment to be ready (optional - you can make this async)
            await self._wait_for_deployment(deployment_id)

            # Make the project publicly viewable
            logger.info(f"Making the project publicly viewable for project {deployment_project_id}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                project_payload = {
                    "ssoProtection": None,
                    "passwordProtection": None,
                    "publicSource": True, # Make the project publicly viewable
                }
                create_project_url = self._get_api_url(f"/v9/projects/{deployment_project_id}")

                response = await client.patch(
                    create_project_url,
                    headers=self._get_headers(),
                    json=project_payload
                )

                if response and response.status_code not in [200, 201]:
                    logger.info(f"Vercel project created during deployment: {vercel_project_name}")
            
            
            # Update project in database
            now = datetime.utcnow().isoformat()
            update_data = {
                "deployment_id": deployment_id,
                "deployment_url": deployment_url,
                "last_deployed_at": now,
                "updated_at": now,
                "published": True
            }
            
            supabase.table("projects").update(update_data).eq("id", project_id).execute()
            
            logger.info(f"Project {project_id} deployment information updated in database")
            
            # Sleep for 5 seconds to ensure project is created
            logger.info(f"Sleeping for 10 seconds to ensure project is created")
            await asyncio.sleep(10)
            return {
                "deployment_id": deployment_id,
                "deployment_url": deployment_url,
                "status": "ready",
                "deployed_at": now
            }
        
        except VercelDeploymentError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during deployment: {str(e)}")
            raise VercelDeploymentError(f"Deployment failed: {str(e)}")
    
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
                            raise VercelDeploymentError("Deployment failed with error state")
                    
                    # Wait before next check
                    await asyncio.sleep(5)
                
                except Exception as e:
                    logger.warning(f"Error checking deployment status: {str(e)}")
        
        logger.warning(f"Deployment {deployment_id} status check timed out")
    
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

                deployment_response = await client.get(
                    delete_url,
                    headers=self._get_headers()
                )
                
                response = await client.delete(
                    delete_url,
                    headers=self._get_headers()
                )
                
                if response.status_code not in [200, 204]:
                    error_message = response.text
                    logger.error(f"Failed to delete deployment: {error_message}")
                    raise VercelDeploymentError(f"Failed to delete deployment: {error_message}")

                data = deployment_response.json()
                project_id = data.get("projectId")
                project_url = self._get_api_url(f"/v9/projects/{project_id}")

                project_response = await client.delete(
                    project_url,
                    headers=self._get_headers()
                )

                if project_response.status_code not in [200, 204]:
                    error_message = project_response.text
                    logger.error(f"Failed to delete project: {error_message}")
                    raise VercelDeploymentError(f"Failed to delete project: {error_message}")
                
            
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
            
            return {
                "deployment_id": data.get("id"),
                "url": data.get("url"),
                "state": data.get("readyState", "UNKNOWN"),
                "created_at": data.get("createdAt"),
                "ready": data.get("ready", False)
            }
        
        except VercelDeploymentError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking deployment status: {str(e)}")
            raise VercelDeploymentError(f"Failed to check deployment status: {str(e)}")


# Import asyncio at the end to avoid circular imports
import asyncio

