"""
Templates Router
API endpoints for template generation and management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import ActionLogger, log_action
from app.utils.auth import get_current_user
from app.services.template_generator import template_generator, TemplateGenerationError
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["templates"])


# ============================================================================
# Request/Response Models
# ============================================================================

class GenerateTemplateRequest(BaseModel):
    """Request model for template generation"""
    prompt: str = Field(..., min_length=10, max_length=1000, description="Description of desired website")
    style_preferences: Optional[Dict[str, Any]] = Field(None, description="Style preferences (colors, fonts, etc.)")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate prompt is meaningful"""
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class TemplateResponse(BaseModel):
    """Response model for template data"""
    id: str
    name: str
    description: str
    sections_config: List[Dict[str, Any]]
    style_config: Dict[str, Any]
    content_schema: Dict[str, Any]
    preview_html: Optional[str] = None
    preview_url: Optional[str] = None
    category: str
    tags: List[str]
    is_public: bool
    created_by: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class TemplateListItem(BaseModel):
    """Simplified template data for list views"""
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    is_public: bool
    preview_url: Optional[str] = None
    created_at: str
    created_by: Optional[str] = None


class GenerationStatus(BaseModel):
    """Status of template generation"""
    status: str  # "pending", "processing", "completed", "failed"
    template_id: Optional[str] = None
    error: Optional[str] = None


class UpdateTemplateRequest(BaseModel):
    """Request model for updating a template"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    sections_config: Optional[List[Dict[str, Any]]] = None
    style_config: Optional[Dict[str, Any]] = None
    content_schema: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter for template generation"""
    
    def __init__(self):
        self.user_requests: Dict[str, List[datetime]] = {}
        self.max_requests_per_hour = 3
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Clean up old requests
        if user_id in self.user_requests:
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if req_time > hour_ago
            ]
        else:
            self.user_requests[user_id] = []
        
        # Check limit
        if len(self.user_requests[user_id]) >= self.max_requests_per_hour:
            return False
        
        # Add current request
        self.user_requests[user_id].append(now)
        return True
    
    def get_remaining_requests(self, user_id: str) -> int:
        """Get number of remaining requests for user"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        if user_id not in self.user_requests:
            return self.max_requests_per_hour
        
        recent_requests = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > hour_ago
        ]
        
        return max(0, self.max_requests_per_hour - len(recent_requests))


# Global rate limiter instance
rate_limiter = RateLimiter()


# ============================================================================
# Helper Functions
# ============================================================================
@log_action(action_type='READ', target_resource_type='template')
async def get_template_from_db(template_id: str, supabase_client) -> Optional[Dict[str, Any]]:
    """Fetch template from database"""
    try:
        response = supabase_client.table("templates").select("*").eq("id", template_id).single().execute()
        return response.data if response.data else None
    except Exception as e:
        logger.error(f"Error fetching template {template_id}: {str(e)}")
        return None

@log_action(action_type='CREATE', target_resource_type='template')
async def save_template_to_db(template_data: Dict[str, Any], supabase_client) -> str:
    """Save template to database"""
    try:
        # Generate ID
        template_id = str(uuid.uuid4())
        template_data["id"] = template_id
        
        # Insert into database
        response = supabase_client.table("templates").insert(template_data).execute()
        
        if not response.data:
            raise Exception("Failed to insert template")
        
        return template_id
    except Exception as e:
        logger.error(f"Error saving template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save template"
        )


# ============================================================================
# API Endpoints
# ============================================================================
# TODO: OBSOLETE, REMOVE THIS ENDPOINT - MIGHT BE GOOD FOR JUST GENERATING TEMPLATES
async def generate_template(
    request: GenerateTemplateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a new website template from a prompt.
    
    - **prompt**: Description of the desired website (10-1000 characters)
    - **style_preferences**: Optional style preferences (colors, fonts, etc.)
    
    Rate limit: 3 generations per hour for free tier users.
    """
    logger.info(f"Generating template for user {current_user['id']}")
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    # Check rate limit
    if not rate_limiter.check_rate_limit(user_id):
        remaining = rate_limiter.get_remaining_requests(user_id)
        logger.error(f"Rate limit exceeded. You have {remaining} generations remaining this hour.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. You have {remaining} generations remaining this hour."
        )
    
    try:
        # Log action
        action_logger = ActionLogger(supabase)
        await action_logger.log_action(
            user_id=user_id,
            action="template_generation_started",
            details={"prompt": request.prompt[:100]}
        )
        
        # Generate template
        logger.info(f"Starting template generation for user {user_id}")
        template_data = template_generator.generate_template(
            prompt=request.prompt,
            user_id=user_id,
            style_preferences=request.style_preferences
        )
        
        # Save to database
        template_id = await save_template_to_db(template_data, supabase)
        template_data["id"] = template_id
        
        # Log success
        await action_logger.log_action(
            user_id=user_id,
            action="template_generated",
            details={"template_id": template_id, "category": template_data.get("category")}
        )
        
        logger.info(f"Template {template_id} generated successfully for user {user_id}")
        
        return TemplateResponse(**template_data)
    
    except TemplateGenerationError as e:
        logger.error(f"Template generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during template generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template generation failed"
        )


@router.get("", response_model=List[TemplateListItem])
async def list_templates(
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    List templates (system templates + user's templates).
    
    - **category**: Filter by category (optional)
    - **is_public**: Filter by public/private (optional)
    - **limit**: Maximum number of templates to return (default: 50)
    - **offset**: Number of templates to skip (default: 0)
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Build query
        query = supabase.table("templates").select("id, name, description, category, tags, is_public, preview_url, created_at")
        
        # Filter: show public templates OR user's own templates
        query = query.or_(f"is_public.eq.true,created_by.eq.{user_id}")
        
        # Apply additional filters
        if category:
            query = query.eq("category", category)
        
        if is_public is not None:
            query = query.eq("is_public", is_public)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Order by creation date
        query = query.order("created_at", desc=True)
        
        # Execute query
        response = query.execute()
        
        templates = response.data if response.data else []
        
        return [TemplateListItem(**t) for t in templates]
    
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list templates"
        )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific template by ID.
    
    Users can access:
    - Public templates
    - Their own templates
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch template
        template = await get_template_from_db(template_id, supabase)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check access permissions
        is_owner = template.get("created_by") == user_id
        is_public = template.get("is_public", False)
        
        if not (is_owner or is_public):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return TemplateResponse(**template)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch template"
        )


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a user's template.
    
    Users can only update their own templates.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch template
        template = await get_template_from_db(template_id, supabase)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check ownership
        if template.get("created_by") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own templates"
            )
        
        # Build update data
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.sections_config is not None:
            update_data["sections_config"] = request.sections_config
        if request.style_config is not None:
            update_data["style_config"] = request.style_config
        if request.content_schema is not None:
            update_data["content_schema"] = request.content_schema
        if request.tags is not None:
            update_data["tags"] = request.tags
        if request.is_public is not None:
            update_data["is_public"] = request.is_public
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update in database
        response = supabase.table("templates").update(update_data).eq("id", template_id).execute()
        
        if not response.data:
            raise Exception("Failed to update template")
        
        # Log action
        action_logger = ActionLogger(supabase)
        await action_logger.log_action(
            user_id=user_id,
            action="template_updated",
            details={"template_id": template_id}
        )
        
        return TemplateResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a user's template.
    
    Users can only delete their own templates.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch template
        template = await get_template_from_db(template_id, supabase)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check ownership
        if template.get("created_by") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own templates"
            )
        
        # Delete from database
        supabase.table("templates").delete().eq("id", template_id).execute()
        
        # Log action
        action_logger = ActionLogger(supabase)
        await action_logger.log_action(
            user_id=user_id,
            action="template_deleted",
            details={"template_id": template_id}
        )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


@router.get("/{template_id}/status", response_model=GenerationStatus)
async def get_generation_status(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check the status of template generation.
    
    This endpoint is useful for polling when generation is done in the background.
    For now, generation is synchronous, so this will always return "completed" or "failed".
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        template = await get_template_from_db(template_id, supabase)
        
        if not template:
            return GenerationStatus(status="failed", error="Template not found")
        
        # Check access
        is_owner = template.get("created_by") == user_id
        is_public = template.get("is_public", False)
        
        if not (is_owner or is_public):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return GenerationStatus(status="completed", template_id=template_id)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        return GenerationStatus(status="failed", error="Failed to check status")

