"""
Projects Router
API endpoints for project CRUD operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import logging
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import log_action
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ProjectListItem(BaseModel):
    """Project list item response model"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    prompt: Optional[str]
    template_id: Optional[str]
    published: bool
    subdomain: Optional[str]
    deployment_url: Optional[str]
    generation_status: str
    created_at: str
    updated_at: str


class ProjectDetail(BaseModel):
    """Detailed project response model"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    prompt: Optional[str]
    template_id: Optional[str]
    html_content: Optional[str]
    css_content: Optional[str]
    js_content: Optional[str]
    published: bool
    subdomain: Optional[str]
    deployment_url: Optional[str]
    theme_settings: Optional[dict]
    whatsapp_number: Optional[str]
    generation_status: str
    generation_error: Optional[str]
    created_at: str
    updated_at: str


class ProjectUpdateRequest(BaseModel):
    """Project update request model"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    html_content: Optional[str] = None
    css_content: Optional[str] = None
    js_content: Optional[str] = None
    theme_settings: Optional[dict] = None
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    published: Optional[bool] = None


class ProjectDuplicateRequest(BaseModel):
    """Project duplicate request model"""
    new_name: Optional[str] = Field(None, max_length=200)


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


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=List[ProjectListItem])
async def list_projects(
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    List all projects for the current user.
    
    - **status_filter**: Filter by generation status (generating, completed, failed)
    - **search**: Search projects by name or description
    - **limit**: Maximum number of projects to return (default: 50)
    - **offset**: Number of projects to skip (default: 0)
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Build query
        query = supabase.table("projects").select(
            "id, user_id, name, description, prompt, template_id, published, "
            "subdomain, deployment_url, generation_status, created_at, updated_at"
        ).eq("user_id", user_id)
        
        # Apply status filter
        if status_filter:
            query = query.eq("generation_status", status_filter)
        
        # Apply search filter
        if search:
            # Search in name and description
            query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Order by updated date (most recent first)
        query = query.order("updated_at", desc=True)
        
        # Execute query
        response = query.execute()
        
        projects = response.data if response.data else []
        
        return [ProjectListItem(**p) for p in projects]
    
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list projects"
        )


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific project.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch project
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        
        # Verify ownership
        verify_project_ownership(project, user_id)
        
        return ProjectDetail(**project)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project"
        )


@router.patch("/{project_id}")
@log_action(action_type='UPDATE', target_resource_type='project')
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a project.
    
    Only the project owner can update the project.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # First, verify project exists and user owns it
        response = supabase.table("projects").select("user_id").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        verify_project_ownership(project, user_id)
        
        # Build update data (only include fields that were provided)
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.html_content is not None:
            update_data["html_content"] = request.html_content
        if request.css_content is not None:
            update_data["css_content"] = request.css_content
        if request.js_content is not None:
            update_data["js_content"] = request.js_content
        if request.theme_settings is not None:
            update_data["theme_settings"] = request.theme_settings
        if request.whatsapp_number is not None:
            update_data["whatsapp_number"] = request.whatsapp_number
        if request.published is not None:
            update_data["published"] = request.published
        
        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update project
        response = supabase.table("projects").update(update_data).eq("id", project_id).execute()
        
        if not response.data:
            raise Exception("Failed to update project")
        
        return {
            "id": project_id,
            "message": "Project updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.delete("/{project_id}")
@log_action(action_type='DELETE', target_resource_type='project')
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a project.
    
    Only the project owner can delete the project.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # First, verify project exists and user owns it
        response = supabase.table("projects").select("user_id").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        verify_project_ownership(project, user_id)
        
        # Delete project
        response = supabase.table("projects").delete().eq("id", project_id).execute()
        
        return {
            "message": "Project deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )


@router.post("/{project_id}/duplicate")
@log_action(action_type='CREATE', target_resource_type='project_duplicate')
async def duplicate_project(
    project_id: str,
    request: ProjectDuplicateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Duplicate a project.
    
    Creates a copy of the project with all its content.
    Only the project owner can duplicate the project.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch original project
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        original_project = response.data[0]
        verify_project_ownership(original_project, user_id)
        
        # Create new project data
        new_project_id = str(uuid.uuid4())
        new_name = request.new_name or f"{original_project['name']} (Copy)"
        
        new_project = {
            "id": new_project_id,
            "user_id": user_id,
            "name": new_name,
            "description": original_project.get("description"),
            "prompt": original_project.get("prompt"),
            "template_id": original_project.get("template_id"),
            "html_content": original_project.get("html_content"),
            "css_content": original_project.get("css_content"),
            "js_content": original_project.get("js_content"),
            "theme_settings": original_project.get("theme_settings"),
            "whatsapp_number": original_project.get("whatsapp_number"),
            "published": False,  # Duplicates are not published by default
            "generation_status": "completed",  # Mark as completed since content is copied
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert new project
        response = supabase.table("projects").insert(new_project).execute()
        
        if not response.data:
            raise Exception("Failed to duplicate project")
        
        return {
            "id": new_project_id,
            "message": "Project duplicated successfully",
            "name": new_name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate project"
        )

