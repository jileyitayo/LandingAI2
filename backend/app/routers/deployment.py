"""
Deployment Router
API endpoints for deploying projects to Vercel.
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging

from app.utils.auth import get_current_user
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import log_action
from app.services.deployment import VercelDeploymentService, VercelDeploymentError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["deployment"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DeploymentResponse(BaseModel):
    """Deployment response model"""
    deployment_id: str
    deployment_url: str
    status: str
    deployed_at: str


class DeploymentStatusResponse(BaseModel):
    """Deployment status response model"""
    deployment_id: Optional[str]
    deployment_url: Optional[str]
    state: str
    ready: bool
    last_deployed_at: Optional[str]


class DeploymentErrorResponse(BaseModel):
    """Deployment error response model"""
    error: str
    detail: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def verify_project_ownership(project: dict, user_id: str):
    """Verify that the project belongs to the current user"""
    if project["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this project"
        )


async def perform_deployment(project_id: str, user_id: str):
    """
    Background task to perform deployment.
    This runs asynchronously to avoid blocking the request.
    """
    try:
        deployment_service = VercelDeploymentService()
        await deployment_service.deploy_website(project_id)
    except Exception as e:
        logger.error(f"Background deployment failed for project {project_id}: {str(e)}")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/projects/{project_id}/deploy", response_model=DeploymentResponse)
@log_action(action_type='DEPLOY', target_resource_type='project')
async def deploy_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Deploy a project to Vercel.
    
    This endpoint:
    1. Validates the project exists and user has permission
    2. Generates static HTML/CSS/JS files
    3. Deploys to Vercel using Vercel API v2
    4. Updates the project with deployment URL
    5. Uses subdomain if configured, or generates one
    
    The deployment runs synchronously to return the deployment URL immediately.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Verify project exists and user owns it
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        verify_project_ownership(project, user_id)
        
        # Check if project has content to deploy
        if not project.get("html_content"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project must have HTML content to deploy. Please generate or add content first."
            )
        
        # Check if project generation is still in progress
        if project.get("generation_status") == "generating":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project generation is still in progress. Please wait until it completes."
            )
        
        # Initialize deployment service
        deployment_service = VercelDeploymentService()
        
        # Deploy the project
        logger.info(f"Starting deployment for project {project_id}")
        deployment_result = await deployment_service.deploy_website(project_id)
        
        return DeploymentResponse(**deployment_result)
    
    except VercelDeploymentError as e:
        logger.error(f"Deployment error for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deploying project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deploy project. Please try again later."
        )


@router.delete("/projects/{project_id}/deploy")
@log_action(action_type='UNDEPLOY', target_resource_type='project')
async def delete_project_deployment(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a project's deployment from Vercel.
    
    This endpoint:
    1. Validates the project exists and user has permission
    2. Deletes the deployment from Vercel
    3. Clears deployment information from the database
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Verify project exists and user owns it
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        verify_project_ownership(project, user_id)
        
        deployment_id = project.get("deployment_id")
        
        if not deployment_id:
            logger.error(f"Project {project_id} has no active deployment")
            return {
                "message": "Project has no active deployment",
                "project_id": project_id
            }
            
        # Initialize deployment service
        deployment_service = VercelDeploymentService()
        
        # Delete deployment from Vercel
        logger.info(f"Deleting deployment {deployment_id} for project {project_id}")
        await deployment_service.delete_deployment(deployment_id)
        
        # Clear deployment information from database
        from datetime import datetime
        update_data = {
            "deployment_id": None,
            "deployment_url": None,
            "published": False,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("projects").update(update_data).eq("id", project_id).execute()
        
        logger.info(f"Deployment deleted successfully for project {project_id}")
        
        return {
            "message": "Deployment deleted successfully",
            "project_id": project_id
        }
    
    except VercelDeploymentError as e:
        logger.error(f"Error deleting deployment for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting deployment for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete deployment. Please try again later."
        )


@router.get("/projects/{project_id}/deployment-status", response_model=DeploymentStatusResponse)
async def get_project_deployment_status(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the deployment status of a project.
    
    This endpoint:
    1. Validates the project exists and user has permission
    2. Checks the deployment status from Vercel (if deployed)
    3. Returns deployment information
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Verify project exists and user owns it
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        verify_project_ownership(project, user_id)
        
        deployment_id = project.get("deployment_id")
        deployment_url = project.get("deployment_url")
        last_deployed_at = project.get("last_deployed_at")
        
        # If no deployment, return not deployed status
        if not deployment_id:
            return DeploymentStatusResponse(
                deployment_id=None,
                deployment_url=None,
                state="NOT_DEPLOYED",
                ready=False,
                last_deployed_at=None
            )
        
        # Initialize deployment service
        deployment_service = VercelDeploymentService()
        
        # Get deployment status from Vercel
        try:
            logger.info(f"Checking deployment status for project {project_id}")
            status_data = await deployment_service.get_deployment_status(deployment_id)
            
            return DeploymentStatusResponse(
                deployment_id=status_data.get("deployment_id"),
                deployment_url=f"https://{status_data.get('url')}" if status_data.get('url') else deployment_url,
                state=status_data.get("state", "UNKNOWN"),
                ready=status_data.get("ready", False),
                last_deployed_at=last_deployed_at
            )
        
        except VercelDeploymentError as e:
            # If we can't get status from Vercel, return cached info
            logger.warning(f"Could not get live deployment status: {str(e)}")
            return DeploymentStatusResponse(
                deployment_id=deployment_id,
                deployment_url=deployment_url,
                state="UNKNOWN",
                ready=True,  # Assume ready if we have a deployment URL
                last_deployed_at=last_deployed_at
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting deployment status for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get deployment status. Please try again later."
        )

