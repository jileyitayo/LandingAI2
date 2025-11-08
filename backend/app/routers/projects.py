"""
Projects Router
API endpoints for project CRUD operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import logging
import zipfile
import io
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import log_action
from app.utils.auth import get_current_user
from app.services.project_file_manager import project_file_manager

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
    project_type: Optional[str]
    files_count: Optional[int]
    subdomain: Optional[str]
    deployment_url: Optional[str]
    theme_settings: Optional[dict]
    whatsapp_number: Optional[str]
    seo_title: Optional[str]
    seo_description: Optional[str]
    generation_status: str
    generation_error: Optional[str]
    generation_cost: Optional[dict] = None  # Cost breakdown from generation_cost_tracking
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
    subdomain: Optional[str] = Field(None, min_length=3, max_length=20, pattern="^[a-z0-9-]+$")
    seo_title: Optional[str] = Field(None, max_length=60)
    seo_description: Optional[str] = Field(None, max_length=160)


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
    deleted: Optional[bool] = True,
    current_user: dict = Depends(get_current_user)
):
    """
    List all projects for the current user.
    
    - **status_filter**: Filter by generation status (generating, completed, failed)
    - **search**: Search projects by name or description
    - **limit**: Maximum number of projects to return (default: 50)
    - **offset**: Number of projects to skip (default: 0)
    - **deleted**: Filter by deleted projects (default: False)
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Build query
        query = supabase.table("projects").select(
            "id, user_id, name, description, prompt, template_id, published, "
            "subdomain, deployment_url, generation_status, created_at, updated_at"
        ).eq("user_id", user_id)

        if deleted:
            query = query.is_("deleted_at", "null")
        
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
    Get detailed information about a specific project, including cost breakdown.
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
        
        # Fetch cost information from generation_cost_tracking
        from app.services.cost_calculator import get_project_costs
        cost_data = get_project_costs(project_id, supabase)
        
        if cost_data:
            # Format cost breakdown for response
            project["generation_cost"] = {
                "total_cost_usd": float(cost_data.get("total_cost_usd", 0)),
                "breakdown": {
                    "business_analysis": float(cost_data.get("business_analysis_cost", 0)),
                    "structure_generation": float(cost_data.get("structure_generation_cost", 0)),
                    "theme_generation": float(cost_data.get("theme_generation_cost", 0)),
                    "page_generation": float(cost_data.get("page_generation_cost", 0)),
                    "validation": float(cost_data.get("validation_cost", 0)),
                    "edit": float(cost_data.get("edit_cost", 0))
                },
                "total_tokens": cost_data.get("total_tokens", 0),
                "total_input_tokens": cost_data.get("total_input_tokens", 0),
                "total_output_tokens": cost_data.get("total_output_tokens", 0),
                "models_used": cost_data.get("models_used", []),
                "generation_time_seconds": float(cost_data.get("generation_time_seconds", 0)),
                "status": cost_data.get("status", "unknown")
            }
        else:
            project["generation_cost"] = None
        
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
        if request.subdomain is not None:
            # Check subdomain uniqueness if subdomain is being updated
            existing = supabase.table("projects").select("id").eq("subdomain", request.subdomain).execute()
            if existing.data and existing.data[0]["id"] != project_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This subdomain is already taken"
                )
            update_data["subdomain"] = request.subdomain.lower()
        if request.seo_title is not None:
            update_data["seo_title"] = request.seo_title
        if request.seo_description is not None:
            update_data["seo_description"] = request.seo_description
        
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
    hard_delete: bool = True,  # Option 1: Hard delete (default) - removes row completely
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a project with two options:
    - Option 1 (hard_delete=True, default): Completely remove the project row from the database
    - Option 2 (hard_delete=False): Soft delete - marks as deleted but keeps data
    
    Only the project owner can delete the project.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()

    # Delete project deployment
    try:    
        from app.routers.deployment import delete_project_deployment
        logger.info(f"Deleting project deployment for project {project_id}")
        await delete_project_deployment(project_id, current_user=current_user)
    except Exception as e:
        logger.error(f"Error deleting project deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project deployment"
        )
    
    try:
        # First, verify project exists and user owns it
        response = supabase.table("projects").select("user_id, deleted_at").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        verify_project_ownership(project, user_id)
        
        # Check if already deleted (only for soft delete)
        if not hard_delete and project.get("deleted_at"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is already deleted"
            )
        
        if hard_delete:
            # Option 1: Hard delete - completely remove the row from database
            # Related tables (project_files, project_chat_messages, project_edit_history) 
            # will be automatically deleted due to ON DELETE CASCADE constraints
            logger.info(f"Hard deleting project {project_id} - removing row completely")
            response = supabase.table("projects").delete().eq("id", project_id).execute()
            
            return {
                "message": "Project permanently deleted successfully"
            }
        else:
            # Option 2: Soft delete - mark as deleted but keep data
            logger.info(f"Soft deleting project {project_id} - marking as deleted")
            response = supabase.table("projects").update({
                "deleted_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", project_id).execute()
            
            return {
                "message": "Project deleted successfully (soft delete)"
            }
        
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )


@router.get("/subdomain/check/{subdomain}")
async def check_subdomain(
    subdomain: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check if a subdomain is available.
    
    Returns:
        - available: bool - Whether the subdomain is available
        - suggestions: list - Alternative suggestions if unavailable
    """
    import re
    
    supabase = get_supabase_client()
    
    # Validate subdomain format
    if not re.match(r"^[a-z0-9-]{3,20}$", subdomain.lower()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain must be 3-20 characters long and contain only lowercase letters, numbers, and hyphens"
        )
    
    try:
        # Check if subdomain exists
        response = supabase.table("projects").select("id").eq("subdomain", subdomain.lower()).execute()
        
        available = not response.data or len(response.data) == 0
        suggestions = []
        
        # Generate suggestions if subdomain is taken
        if not available:
            import random
            base = subdomain.lower().rstrip("-0123456789")
            suggestions = [
                f"{base}-{random.randint(10, 99)}",
                f"{base}-{random.randint(100, 999)}",
                f"{base}-site",
                f"{base}-web",
                f"my-{base}",
            ]
        
        return {
            "available": available,
            "subdomain": subdomain.lower(),
            "suggestions": suggestions[:3] if suggestions else []
        }
    
    except Exception as e:
        logger.error(f"Error checking subdomain: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check subdomain availability"
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


@router.get("/{project_id}/download")
@log_action(action_type='READ', target_resource_type='project_download')
async def download_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download a React project as a ZIP file.
    
    Only the project owner can download the project.
    Returns a ZIP file containing all project files.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch project details
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        verify_project_ownership(project, user_id)
        
        # Check if it's a React project
        if project.get("project_type") != "react":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Download is only available for React projects"
            )
        
        # Get all project files
        files = await project_file_manager.get_project_files(project_id)
        
        if not files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No files found for this project"
            )
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, file_content in files.items():
                # Add file to ZIP
                zip_file.writestr(file_path, file_content)
        
        # Reset buffer position
        zip_buffer.seek(0)
        
        # Create filename
        project_name = project.get("name", "react-project")
        # Sanitize filename
        safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '-')
        filename = f"{safe_name}.zip"
        
        # Return ZIP file as streaming response
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/zip"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download project"
        )

