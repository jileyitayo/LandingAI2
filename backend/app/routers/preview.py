"""
Preview Router
Endpoints for creating, checking, and deleting Vite project previews.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
import logging

from app.utils.supabase_client import get_supabase_client
from app.utils.auth import get_current_user
from app.services.project_file_manager import project_file_manager
from app.services.vite_preview_service import vite_preview_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generation"])


@router.post("/preview/{project_id}", response_model=Dict[str, Any])
async def create_project_preview(
    project_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a temporary preview of the generated React project.
    
    - Builds the project using shared node_modules (fast: ~5-10s)
    - Serves static files
    - Preview expires after 1 hour
    
    Returns:
        {
            "preview_id": "abc-123-def",
            "preview_url": "/previews/builds/abc-123-def/dist/index.html",
            "expires_at": "2025-10-17T10:00:00Z"
        }
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch project
        response = supabase.table("projects")\
            .select("id, name, project_type, generation_status, user_id")\
            .eq("id", project_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        
        # Check ownership
        if project["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if it's a React project
        if project.get("project_type") != "react":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This is not a React project"
            )
        
        # Check if project is completed
        if project.get("generation_status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project generation is not completed yet"
            )
        
        # Get project files
        files = await project_file_manager.get_project_files(project_id)
        
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files found for this project"
            )
        
        # Create preview
        result = vite_preview_service.create_preview(project_id, files)
        
        # Store preview ID in project for future updates
        preview_id = result.get("preview_id")
        if preview_id:
            supabase.table("projects").update({
                "preview_id": preview_id
            }).eq("id", project_id).execute()
        
        logger.info(f"✓ Preview created for project {project_id}: {result['preview_id']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create preview"
        )


@router.get("/preview/{preview_id}/status")
async def get_preview_status(
    preview_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check if a preview exists and when it expires.
    
    Returns:
        {
            "exists": true,
            "preview_url": "/previews/builds/abc-123/dist/index.html",
            "created_at": "2025-10-16T09:00:00Z",
            "expires_at": "2025-10-16T10:00:00Z"
        }
    """
    try:
        status_info = vite_preview_service.get_preview_status(preview_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preview not found"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preview status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get preview status"
        )


@router.delete("/preview/{preview_id}")
async def delete_preview(
    preview_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Manually delete a preview before it expires."""
    try:
        success = vite_preview_service.delete_preview(preview_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete preview"
            )
        
        return {"message": "Preview deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete preview"
        )
