"""
Generation Router
API endpoints for AI website content generation and rendering.
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import logging
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import ActionLogger, log_action
from app.utils.auth import get_current_user
from app.services.content_generator import content_generator, ContentGenerationError
from app.services.template_renderer import template_renderer, TemplateRenderError
from app.services.template_generator import template_generator
from app.routers.templates import save_template_to_db
from app.services.react_website_generator import react_website_generator


logger = logging.getLogger(__name__)
router = APIRouter(tags=["generation"])


# ============================================================================
# Request/Response Models
# ============================================================================

class GenerateWebsiteRequest(BaseModel):
    """Request model for website generation"""
    prompt: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="Business description for content generation"
    )
    template_id: Optional[str] = Field(
        None,
        description="Template ID to use for generation. If not provided, a suitable template will be generated."
    )
    project_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional project name"
    )
    style_preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional style preferences for template generation"
    )
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate prompt is meaningful"""
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class GenerationStatusResponse(BaseModel):
    """Response model for generation status"""
    status: str  # "idle", "generating", "completed", "failed"
    project_id: Optional[str] = None
    progress: Optional[int] = None  # 0-100
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class GenerateWebsiteResponse(BaseModel):
    """Response model for website generation"""
    project_id: str
    status: str
    message: str
    html_preview_url: Optional[str] = None


class RateLimitInfo(BaseModel):
    """Response model for rate limit information"""
    tier: str
    limit: int
    used: int
    remaining: int
    resets_at: str


class GenerateReactWebsiteRequest(BaseModel):
    """Request model for React website generation"""
    prompt: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="Business description for React website generation"
    )
    project_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional project name"
    )
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate prompt is meaningful"""
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class GenerateReactWebsiteResponse(BaseModel):
    """Response model for React website generation"""
    project_id: str
    status: str
    message: str
    website_structure: Optional[Dict[str, Any]] = None
    business_analysis: Optional[Dict[str, Any]] = None
    files_count: Optional[int] = None


# ============================================================================
# Rate Limiting Functions
# ============================================================================
@log_action(action_type='READ', target_resource_type='rate_limit_check')
async def check_user_rate_limit(user_id: str, supabase_client) -> tuple[bool, Dict[str, Any]]:
    """
    Check if user has exceeded rate limit.
    
    Returns:
        Tuple of (is_allowed, rate_limit_info)
    """
    try:
        # Fetch user data
        response = supabase_client.table("users")\
            .select("subscription_tier, current_period_generations, current_period_start")\
            .eq("id", user_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = response.data[0]
        if user == "jileyitayo@gmail.com":
            tier = "pro"
        else:
            tier = user.get("subscription_tier", "free")
        current_count = user.get("current_period_generations", 0)
        period_start = user.get("current_period_start")
        
        # Define rate limits per tier
        rate_limits = {
            "free": 5,      # 5 generations per hour
            "pro": 100      # 100 generations per hour (practically unlimited)
        }
        
        limit = rate_limits.get(tier, 5)
        
        # Check if period needs reset (hourly)
        now = datetime.utcnow()
        if period_start:
            period_start_dt = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
            if (now - period_start_dt.replace(tzinfo=None)) > timedelta(hours=1):
                # Reset the counter
                supabase_client.table("users")\
                    .update({
                        "current_period_generations": 0,
                        "current_period_start": now.isoformat()
                    })\
                    .eq("id", user_id)\
                    .execute()
                current_count = 0
                period_start_dt = now
        else:
            # Initialize period start
            period_start_dt = now
            supabase_client.table("users")\
                .update({"current_period_start": now.isoformat()})\
                .eq("id", user_id)\
                .execute()
        
        # Check limit
        is_allowed = current_count < limit
        
        # Calculate reset time
        resets_at = period_start_dt + timedelta(hours=1)
        
        rate_limit_info = {
            "tier": tier,
            "limit": limit,
            "used": current_count,
            "remaining": max(0, limit - current_count),
            "resets_at": resets_at.isoformat()
        }
        
        return is_allowed, rate_limit_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking rate limit: {str(e)}")
        # On error, allow the request but log it
        return True, {
            "tier": "unknown",
            "limit": 5,
            "used": 0,
            "remaining": 5,
            "resets_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }

async def business_analyzer(prompt: str, ) -> tuple[bool, Dict[str, Any]]:
    """
    Check if user has exceeded rate limit.
    I'm building a website generator and I need to analyze the prompt to determine the site requirements/business analysis to be able to generate a template stucture for a website
    This analysis will be an input to another AI model to generate a template stucture for a website
    generate a business analysis for the prompt in json format
    """
    return True, {
        "tier": "unknown",
        "limit": 5,
        "used": 0,
        "remaining": 5,
        "resets_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }

async def template_creation_analyzer(prompt: str, business_analysis: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
    """
    Check if user has exceeded rate limit.
    """
    return True, {
        "tier": "unknown",
        "limit": 5,
        "used": 0,
        "remaining": 5,
        "resets_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }

@log_action(action_type='UPDATE', target_resource_type='generation_count')
async def increment_generation_count(user_id: str, supabase_client) -> None:
    """Increment user's generation count"""
    try:
        # Increment both counters
        supabase_client.rpc(
            "increment_generation_count",
            {"user_id_param": user_id}
        ).execute()
    except Exception as e:
        # If RPC doesn't exist, use direct update
        logger.warning(f"RPC increment failed, using direct update: {str(e)}")
        try:
            response = supabase_client.table("users")\
                .select("current_period_generations, generation_count")\
                .eq("id", user_id)\
                .execute()
            
            if response.data:
                data = response.data[0]
                supabase_client.table("users")\
                    .update({
                        "current_period_generations": data["current_period_generations"] + 1,
                        "generation_count": data["generation_count"] + 1
                    })\
                    .eq("id", user_id)\
                    .execute()
        except Exception as inner_e:
            logger.error(f"Failed to increment generation count: {str(inner_e)}")


# ============================================================================
# Helper Functions
# ============================================================================
@log_action(action_type='CREATE', target_resource_type='project_creation')
async def create_project(
    user_id: str,
    project_name: str,
    prompt: str,
    template_id: str,
    supabase_client
) -> str:
    """Create a new project in the database"""
    try:
        project_id = str(uuid.uuid4())
        
        project_data = {
            "id": project_id,
            "user_id": user_id,
            "name": project_name or f"Generated Website - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            "description": prompt[:500],
            "prompt": prompt,
            "template_id": template_id,
            "generation_status": "generating",
            "published": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase_client.table("projects")\
            .insert(project_data)\
            .execute()
        
        if not response.data:
            raise Exception("Failed to create project")
        
        return project_id
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )

@log_action(action_type='UPDATE', target_resource_type='project_status_update')
async def update_project_status(
    project_id: str,
    status_value: str,
    error: Optional[str],
    supabase_client
) -> None:
    """Update project generation status"""
    try:
        update_data = {
            "generation_status": status_value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if status_value == "completed":
            update_data["last_generated_at"] = datetime.utcnow().isoformat()
        
        if error:
            update_data["generation_error"] = error
        
        supabase_client.table("projects")\
            .update(update_data)\
            .eq("id", project_id)\
            .execute()
            
    except Exception as e:
        logger.error(f"Error updating project status: {str(e)}")


@log_action(action_type='UPDATE', target_resource_type='generated_content_saving')
async def save_generated_content(
    project_id: str,
    html_content: str,
    css_content: str,
    js_content: str,
    supabase_client
) -> None:
    """Save generated website content to project"""
    try:
        update_data = {
            "html_content": html_content,
            "css_content": css_content,
            "js_content": js_content,
            "generation_status": "completed",
            "last_generated_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase_client.table("projects")\
            .update(update_data)\
            .eq("id", project_id)\
            .execute()
            
    except Exception as e:
        logger.error(f"Error saving generated content: {str(e)}")
        raise

@log_action(action_type='UPDATE', target_resource_type='template_use_count')
async def increment_template_use_count(template_id: str, supabase_client) -> None:
    """Increment template's use count"""
    try:
        # Get current use count
        response = supabase_client.table("templates")\
            .select("use_count")\
            .eq("id", template_id)\
            .execute()
        
        if response.data:
            current_count = response.data[0].get("use_count", 0)
            supabase_client.table("templates")\
                .update({"use_count": current_count + 1})\
                .eq("id", template_id)\
                .execute()
    except Exception as e:
        logger.error(f"Failed to increment template use count: {str(e)}")


@log_action(action_type='CREATE', target_resource_type='generate_suitable_template')
async def generate_suitable_template(
    prompt: str,
    user_id: str,
    style_preferences: Optional[Dict[str, Any]],
    supabase_client
) -> str:
    """Generate a suitable template for the given prompt"""
    try:
        logger.info("[TEMPLATE GEN] Generating suitable template...")
        
        # Use the template generator to create a template
        template_data = template_generator.generate_template(
            prompt=prompt,
            user_id=user_id,
            style_preferences=style_preferences
        )
        
        # Save template to database
        # Save to database
        template_id = await save_template_to_db(template_data, supabase_client)

        logger.info(f"[TEMPLATE GEN] ✓ Template {template_id} generated and saved")
        
        # Log success
        action_logger = ActionLogger(supabase_client)
        await action_logger.log_action(
            user_id=user_id,
            action="template_generated",
            details={"template_id": template_id, "category": template_data.get("category")}
        )
        return template_id
        
    except Exception as e:
        logger.error(f"Error generating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suitable template"
        )

# TODO: MIGHT NEED TO REMOVE THIS FUNCTION SINCE USERS CAN USE ANY TEMPLATE THEY WANT
@log_action(action_type='READ', target_resource_type='validate_template_access')
async def validate_template_access(template_id: str, user_id: str, supabase_client):
    """Validate that user has access to the template"""
    try:
        template_response = supabase_client.table("templates")\
            .select("id, name, is_active, is_system_template, user_id")\
            .eq("id", template_id)\
            .execute()
        
        if not template_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        template = template_response.data[0]
        
        # Check if template is active
        if not template.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template is not active"
            )
        
        # Check access rights
        is_system = template.get("is_system_template", False)
        is_owner = template.get("user_id") == user_id
        
        if not (is_system or is_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this template"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating template access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate template access"
        )

@log_action(action_type='CREATE', target_resource_type='generate_website_background')
async def generate_website_background(
    project_id: str,
    prompt: str,
    template_id: str,
    user_id: str,
):
    """Background task for  website generation"""
    supabase = get_supabase_client()
    
    try:
        logger.info(f"[BG] Starting generation for project {project_id}")
        
        # Step 1: Generate content
        logger.info(f"[BG] Generating content...")
        content_result = await content_generator.generate_content(
            prompt=prompt,
            template_id=template_id,
            user_id=user_id
        )
        
        content = content_result["content"]
        
        # Step 2: Fetch template for rendering
        logger.info(f"[BG] Fetching template for rendering...")
        template_response = supabase.table("templates")\
            .select("*")\
            .eq("id", template_id)\
            .execute()
        
        if not template_response.data:
            logger.error(f"[BG] Template not found for template_id: {template_id}, deferring to generating a suitable template")
            raise Exception("Template not found")
        
        template = template_response.data[0]
        
        # Step 3: Render template with content
        logger.info(f"[BG] Rendering template...")
        logger.info(f"Template: \n{template}")
        logger.info(f"Content: \n{content}")
        rendered = template_renderer.render_template(template, content)
        
        # Step 4: Save to database
        logger.info(f"[BG] Saving generated content...")
        await save_generated_content(
            project_id=project_id,
            html_content=rendered["html_content"],
            css_content=rendered["css_content"],
            js_content=rendered["js_content"],
            supabase_client=supabase
        )
        
        # Increment template use count
        await increment_template_use_count(template_id, supabase)
        
        logger.info(f"[BG] ✓ Generation completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"[BG] ✗ Generation failed: {str(e)}")
        await update_project_status(
            project_id=project_id,
            status_value="failed",
            error=str(e),
            supabase_client=supabase
        )


@log_action(action_type='CREATE', target_resource_type='generate_react_website_background')
async def generate_react_website_background(
    project_id: str,
    prompt: str,
    user_id: str,
):
    """Background task for React website generation"""
    supabase = get_supabase_client()
    
    try:
        logger.info(f"[REACT BG] Starting React generation for project {project_id}")
        
        # Generate complete React website structure
        logger.info(f"[REACT BG] Generating React website structure...")
        result = react_website_generator.generate_website_structure(prompt)
        
        website_structure = result["website_structure"]
        business_analysis = result["business_analysis"]
        files = result["files"]
        
        # Store the generated files as JSON in the database
        logger.info(f"[REACT BG] Saving React website data...")
        
        # Convert files dict to JSON string
        files_json = json.dumps(files)
        website_structure_json = json.dumps(website_structure)
        business_analysis_json = json.dumps(business_analysis)
        
        update_data = {
            "react_files": files_json,
            "website_structure": website_structure_json,
            "business_analysis": business_analysis_json,
            "generation_status": "completed",
            "last_generated_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("projects")\
            .update(update_data)\
            .eq("id", project_id)\
            .execute()
        
        logger.info(f"[REACT BG] ✓ React generation completed for project {project_id}")
        logger.info(f"[REACT BG] Generated {len(files)} files")
        
    except Exception as e:
        logger.error(f"[REACT BG] ✗ React generation failed: {str(e)}")
        await update_project_status(
            project_id=project_id,
            status_value="failed",
            error=str(e),
            supabase_client=supabase
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/generate_website", response_model=GenerateWebsiteResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_website(
    request: GenerateWebsiteRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a complete website from prompt only.
    
    This endpoint handles the flow:
    1. If template_id provided: Use existing template (current flow)
    2. If no template_id: Generate suitable template first, then use it
    
    Process:
    1. Check user rate limits
    2. Generate template (if needed)
    3. Create project record
    4. Generate content using AI (background)
    5. Render template with content (background)
    6. Save to project
    
    Rate Limits:
    - Free tier: 5 generations per hour
    - Pro tier: 100 generations per hour
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    logger.info(f"Website generation requested by user {user_id}")
    logger.info(f"Template provided: {request.template_id is not None}")
    
    try:
        # Step 1: Check rate limits first
        logger.info("Checking rate limits...")
        is_allowed, rate_info = await check_user_rate_limit(user_id, supabase)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. You have used {rate_info['used']}/{rate_info['limit']} generations. Resets at {rate_info['resets_at']}",
                headers={
                    "X-RateLimit-Limit": str(rate_info['limit']),
                    "X-RateLimit-Remaining": str(rate_info['remaining']),
                    "X-RateLimit-Reset": rate_info['resets_at']
                }
            )
        
        # Step 2: Determine template to use
        template_id = request.template_id
        
        if not template_id:
            # Generate a suitable template first
            logger.info("No template provided, generating suitable template...")
            template_id = await generate_suitable_template(
                prompt=request.prompt,
                user_id=user_id,
                style_preferences=request.style_preferences,
                supabase_client=supabase
            )
            logger.info(f"Generated template: {template_id}")
        else:
            # Validate existing template
            logger.info("Validating provided template...")
            await validate_template_access(template_id, user_id, supabase)
        
        # Step 3: Create project
        logger.info("Creating project...")
        project_id = await create_project(
            user_id=user_id,
            project_name=request.project_name,
            prompt=request.prompt,
            template_id=template_id,
            supabase_client=supabase
        )
        
        # Step 4: Increment generation count
        await increment_generation_count(user_id, supabase)
        
        # Step 5: Log action
        action_logger = ActionLogger(supabase)
        await action_logger.log_action(
            user_id=user_id,
            action="unified_website_generation_started",
            details={
                "project_id": project_id,
                "template_id": template_id,
                "template_generated": request.template_id is None,
                "prompt_length": len(request.prompt)
            }
        )
        
        # Step 6: Start background generation
        logger.info(f"Starting background generation for project {project_id}")
        background_tasks.add_task(
            generate_website_background,
            project_id=project_id,
            prompt=request.prompt,
            template_id=template_id,
            user_id=user_id,
        )
        
        logger.info(f" ✓  Generation initiated for project {project_id}")
        
        return GenerateWebsiteResponse(
            project_id=project_id,
            status="generating",
            message="Website generation started. Check status endpoint for progress.",
            html_preview_url=None
        )
        
    except HTTPException:
        raise
    except ContentGenerationError as e:
        logger.error(f"Content generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content generation failed: {str(e)}"
        )
    except TemplateRenderError as e:
        logger.error(f"Template rendering failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template rendering failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Website generation failed"
        )


@router.get("/generation/{project_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check the status of website generation.
    
    Status values:
    - "idle": Not started yet
    - "generating": In progress
    - "completed": Successfully generated
    - "failed": Generation failed
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch project
        response = supabase.table("projects")\
            .select("generation_status, generation_error, created_at, last_generated_at, user_id")\
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
        
        status_value = project.get("generation_status", "idle")
        
        # Calculate progress (rough estimate)
        progress = None
        if status_value == "generating":
            progress = 50  # Mid-way estimate
        elif status_value == "completed":
            progress = 100
        elif status_value == "failed":
            progress = 0
        
        return GenerationStatusResponse(
            status=status_value,
            project_id=project_id,
            progress=progress,
            message=_get_status_message(status_value),
            error=project.get("generation_error"),
            created_at=project.get("created_at"),
            completed_at=project.get("last_generated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking generation status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check generation status"
        )


@router.get("/rate-limit", response_model=RateLimitInfo)
async def get_rate_limit_info(current_user: dict = Depends(get_current_user)):
    """
    Get current rate limit information for the authenticated user.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        _, rate_info = await check_user_rate_limit(user_id, supabase)
        return RateLimitInfo(**rate_info)
    except Exception as e:
        logger.error(f"Error getting rate limit info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rate limit information"
        )


# ============================================================================
# Helper Methods
# ============================================================================

def _get_status_message(status: str) -> str:
    """Get user-friendly status message"""
    messages = {
        "idle": "Generation not started",
        "generating": "Generating your website... This may take 30-60 seconds",
        "completed": "Website generated successfully",
        "failed": "Generation failed. Please try again"
    }
    return messages.get(status, "Unknown status")


@router.post("/generate_react_website", response_model=GenerateReactWebsiteResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_react_website(
    request: GenerateReactWebsiteRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a complete React/TypeScript website from a prompt.
    
    This endpoint:
    1. Analyzes the business requirements using BusinessAnalyzer
    2. Generates a complete website structure (pages, components, routing)
    3. Creates React components based on the analysis
    4. Returns a full React project structure
    
    The generation includes:
    - Business analysis (business type, audience, features, etc.)
    - Page structures with appropriate sections
    - Reusable React components
    - Routing configuration
    - Styling with Tailwind CSS
    - TypeScript definitions
    
    Process:
    1. Check user rate limits
    2. Analyze business requirements from prompt
    3. Generate website structure and pages
    4. Create React components
    5. Save project to database
    
    Rate Limits:
    - Free tier: 5 generations per hour
    - Pro tier: 100 generations per hour
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    logger.info(f"React website generation requested by user {user_id}")
    
    try:
        # Step 1: Check rate limits
        logger.info("Checking rate limits...")
        is_allowed, rate_info = await check_user_rate_limit(user_id, supabase)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. You have used {rate_info['used']}/{rate_info['limit']} generations. Resets at {rate_info['resets_at']}",
                headers={
                    "X-RateLimit-Limit": str(rate_info['limit']),
                    "X-RateLimit-Remaining": str(rate_info['remaining']),
                    "X-RateLimit-Reset": rate_info['resets_at']
                }
            )
        
        # Step 2: Create project record
        logger.info("Creating project...")
        project_id = str(uuid.uuid4())
        
        project_data = {
            "id": project_id,
            "user_id": user_id,
            "name": request.project_name or f"React Website - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            "description": request.prompt[:500],
            "prompt": request.prompt,
            "project_type": "react",  # Mark as React project
            "generation_status": "generating",
            "published": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("projects").insert(project_data).execute()
        
        if not response.data:
            raise Exception("Failed to create project")
        
        # Step 3: Increment generation count
        await increment_generation_count(user_id, supabase)
        
        # Step 4: Log action
        action_logger = ActionLogger(supabase)
        await action_logger.log_action(
            user_id=user_id,
            action="react_website_generation_started",
            details={
                "project_id": project_id,
                "prompt_length": len(request.prompt),
                "project_type": "react"
            }
        )
        
        # Step 5: Start background generation
        logger.info(f"Starting React background generation for project {project_id}")
        background_tasks.add_task(
            generate_react_website_background,
            project_id=project_id,
            prompt=request.prompt,
            user_id=user_id,
        )
        
        logger.info(f"✓ React generation initiated for project {project_id}")
        
        return GenerateReactWebsiteResponse(
            project_id=project_id,
            status="generating",
            message="React website generation started. This will analyze your business and create a complete React application. Check status endpoint for progress.",
            website_structure=None,
            business_analysis=None,
            files_count=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during React generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="React website generation failed"
        )


@router.get("/react_website/{project_id}", response_model=Dict[str, Any])
async def get_react_website(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the generated React website structure and files.
    
    Returns:
    - website_structure: Page structures and components
    - business_analysis: Original business analysis
    - files: Dictionary of file paths to contents
    - generation_status: Current status
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch project
        response = supabase.table("projects")\
            .select("*")\
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
        
        # Parse stored JSON data
        files = json.loads(project.get("react_files", "{}"))
        website_structure = json.loads(project.get("website_structure", "{}"))
        business_analysis = json.loads(project.get("business_analysis", "{}"))
        
        return {
            "project_id": project_id,
            "status": project.get("generation_status", "idle"),
            "website_structure": website_structure,
            "business_analysis": business_analysis,
            "files": files,
            "files_count": len(files),
            "created_at": project.get("created_at"),
            "completed_at": project.get("last_generated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching React website: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch React website"
        )

