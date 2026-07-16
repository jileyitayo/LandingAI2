"""
Deployment Router
API endpoints for deploying projects to Vercel.
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio
import logging

from app.utils.auth import get_current_user
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import log_action
from app.services.deployments.vercel_deployer import VercelDeployer, VercelDeploymentError
from app.services.thumbnail_service import capture_thumbnail

logger = logging.getLogger(__name__)
router = APIRouter(tags=["deployment"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DeploymentQueuedResponse(BaseModel):
    """Response for an accepted (queued) async deployment"""
    status: str
    message: str


class DeploymentStatusResponse(BaseModel):
    """Deployment status response model"""
    deployment_id: Optional[str]
    deployment_url: Optional[str]
    state: str
    ready: bool
    last_deployed_at: Optional[str]
    last_edited_at: Optional[str] = None
    has_unpublished_changes: bool = False
    # Async deploy progress (DB-backed, written by the background task)
    deploy_status: str = "idle"
    deploy_stage_detail: Optional[str] = None
    deploy_error: Optional[str] = None


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


IN_FLIGHT_DEPLOY_STATUSES = ("queued", "uploading", "building")


def _set_deploy_status(project_id: str, deploy_status: str, detail: Optional[str] = None, error: Optional[str] = None):
    """Write the async deploy progress to the project row (best-effort)."""
    try:
        supabase = get_supabase_client()
        supabase.table("projects").update({
            "deploy_status": deploy_status,
            "deploy_stage_detail": detail,
            "deploy_error": error,
        }).eq("id", project_id).execute()
    except Exception as e:
        logger.warning(f"Failed to write deploy status '{deploy_status}' for project {project_id}: {e}")


async def perform_deployment(project_id: str, user_id: str):
    """
    Background task to perform deployment.
    Writes staged progress (uploading -> building -> ready | error) to the
    project row; the frontend polls deployment-status to render it.
    """
    try:
        deployment_service = VercelDeployer()
        result = await deployment_service.deploy_website(
            project_id,
            progress_cb=lambda stage, detail: _set_deploy_status(project_id, stage, detail),
        )
        _set_deploy_status(project_id, "ready", "Deployment live")
        logger.info(f"Background deployment succeeded for project {project_id}")

        # Fire-and-forget dashboard thumbnail capture; never blocks the deploy
        deployment_url = (result or {}).get("deployment_url")
        if deployment_url:
            asyncio.create_task(capture_thumbnail(project_id, user_id, deployment_url))
    except Exception as e:
        logger.error(f"Background deployment failed for project {project_id}: {str(e)}")
        _set_deploy_status(project_id, "error", None, error=str(e)[:1000])


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/projects/{project_id}/deploy", response_model=DeploymentQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
@log_action(action_type='DEPLOY', target_resource_type='project')
async def deploy_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Deploy a project to Vercel (async).

    Validates the project, marks it queued, and runs the deployment as a
    background task. The frontend polls /deployment-status for staged
    progress (queued -> uploading -> building -> ready | error).
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
        if not project.get("project_type") == "react":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project must be a React project to deploy. Please generate or add content first."
            )

        # Check if project generation is still in progress
        if project.get("generation_status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project generation is still in progress. Please wait until it completes."
            )

        # Only one deploy at a time per project
        if project.get("deploy_status") in IN_FLIGHT_DEPLOY_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A deployment is already in progress for this project."
            )

        _set_deploy_status(project_id, "queued", "Deployment queued")
        background_tasks.add_task(perform_deployment, project_id, user_id)

        logger.info(f"Deployment queued for project {project_id}")
        return DeploymentQueuedResponse(
            status="queued",
            message="Deployment started. Poll deployment-status for progress."
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
        deployment_service = VercelDeployer()
        
        # Delete deployment from Vercel
        logger.info(f"Deleting deployment {deployment_id} for project {project_id}")
        await deployment_service.delete_deployment(deployment_id)
        
        # Clear deployment information from database
        from datetime import datetime
        update_data = {
            "deployment_id": None,
            "deployment_url": None,
            "vercel_project_id": None,
            "published": False,
            "deploy_status": "idle",
            "deploy_stage_detail": None,
            "deploy_error": None,
            "updated_at": datetime.utcnow().isoformat()
        }
        # Keep the custom domain so the next publish re-attaches it; the
        # Vercel project deletion above already detached it on Vercel's side
        if project.get("custom_domain"):
            update_data["custom_domain_status"] = "pending_dns"
        
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
        last_edited_at = project.get("last_edited_at")

        # The live site is behind the preview if an edit landed after the last deploy
        def _parse_ts(value):
            if not value:
                return None
            try:
                from datetime import datetime as _dt
                parsed = _dt.fromisoformat(str(value).replace("Z", "+00:00"))
                return parsed.replace(tzinfo=None)  # compare as naive UTC
            except ValueError:
                return None

        edited_ts = _parse_ts(last_edited_at)
        deployed_ts = _parse_ts(last_deployed_at)
        has_unpublished_changes = bool(
            deployment_id and edited_ts and (not deployed_ts or edited_ts > deployed_ts)
        )

        deploy_status = project.get("deploy_status") or "idle"
        deploy_stage_detail = project.get("deploy_stage_detail")
        deploy_error = project.get("deploy_error")
        deploy_in_flight = deploy_status in IN_FLIGHT_DEPLOY_STATUSES

        # If no deployment, return not deployed status
        if not deployment_id:
            return DeploymentStatusResponse(
                deployment_id=None,
                deployment_url=None,
                state="NOT_DEPLOYED",
                ready=False,
                last_deployed_at=None,
                last_edited_at=last_edited_at,
                has_unpublished_changes=False,
                deploy_status=deploy_status,
                deploy_stage_detail=deploy_stage_detail,
                deploy_error=deploy_error
            )

        # While a deploy is in flight, skip the Vercel roundtrip — the DB-backed
        # progress written by the background task is the source of truth
        if deploy_in_flight:
            return DeploymentStatusResponse(
                deployment_id=deployment_id,
                deployment_url=deployment_url,
                state="DEPLOYING",
                ready=False,
                last_deployed_at=last_deployed_at,
                last_edited_at=last_edited_at,
                has_unpublished_changes=has_unpublished_changes,
                deploy_status=deploy_status,
                deploy_stage_detail=deploy_stage_detail,
                deploy_error=deploy_error
            )

        # Initialize deployment service
        deployment_service = VercelDeployer()

        # Get deployment status from Vercel
        try:
            logger.info(f"Checking deployment status for project {project_id}")
            status_data = await deployment_service.get_deployment_status(deployment_id)

            return DeploymentStatusResponse(
                deployment_id=status_data.get("deployment_id"),
                deployment_url=f"https://{status_data.get('url')}" if status_data.get('url') else deployment_url,
                state=status_data.get("state", "UNKNOWN"),
                ready=status_data.get("ready", False),
                last_deployed_at=last_deployed_at,
                last_edited_at=last_edited_at,
                has_unpublished_changes=has_unpublished_changes,
                deploy_status=deploy_status,
                deploy_stage_detail=deploy_stage_detail,
                deploy_error=deploy_error
            )

        except VercelDeploymentError as e:
            # If we can't get status from Vercel, return cached info
            logger.warning(f"Could not get live deployment status: {str(e)}")
            return DeploymentStatusResponse(
                deployment_id=deployment_id,
                deployment_url=deployment_url,
                state="UNKNOWN",
                ready=True,  # Assume ready if we have a deployment URL
                last_deployed_at=last_deployed_at,
                last_edited_at=last_edited_at,
                has_unpublished_changes=has_unpublished_changes,
                deploy_status=deploy_status,
                deploy_stage_detail=deploy_stage_detail,
                deploy_error=deploy_error
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting deployment status for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get deployment status. Please try again later."
        )

