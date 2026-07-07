"""
Generation Router
API endpoints for AI website content generation and rendering.
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
import uuid
import json
import logging
import asyncio
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import ActionLogger, log_action
from app.utils.auth import get_current_user
from app.utils.rate_limiter import RateLimiter
from app.utils.image_loader import fetch_images_as_data_urls
from app.services.content_generator import content_generator, ContentGenerationError
from app.services.templates.template_renderer import template_renderer, TemplateRenderError
from app.services.templates.template_generator import template_generator
from app.routers.templates import save_template_to_db
from app.services.react_website_generator import react_website_generator
from app.services.project_file_manager import project_file_manager
from app.services.vite_preview_service import vite_preview_service
from app.services.component_editor_service import component_editor_service
from app.services import component_library
from app.services.validators.error_fixer import error_fixer
from app.services.validators.build_tester import BuildError, BuildTester
from app.services.direct_code_editor import direct_code_editor
from app.services.component_relationship_tracker import ComponentRelationshipTracker
from app.services.property_edit_queue_service import get_queue_service
from app.config import settings
from app.models.generation import (
    GenerateWebsiteRequest,
    GenerationStatusResponse,
    GenerateWebsiteResponse,
    RateLimitInfo,
    GenerateReactWebsiteRequest,
    GenerateReactWebsiteResponse,
    ComponentEditRequest,
    ComponentEditResponse,
    PropertyChange,
    PropertyEditRequest,
    PropertyEditResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generation"])


# ============================================================================
# Rate Limiting Functions - NEW DUAL RATE LIMITING
# ============================================================================
@log_action(action_type='READ', target_resource_type='rate_limit_check')
async def check_user_rate_limit(user_id: str, supabase_client, call_type: str = "generation") -> tuple[bool, Dict[str, Any]]:
    """
    Check if user has exceeded rate limit (per-minute OR daily).

    Uses new dual rate limiting:
    - call_type='generation': per-minute (Free=1/min, Pro=2/min) + daily
      (Free=5/day, Pro=30/day) via the shared generation counter
    - call_type='edit': separate edit quota (Free=10/day+2/min, Pro=30/day+5/min,
      Premium=10000/day+20/min) counted from ai_call_logs

    Returns:
        Tuple of (is_allowed, rate_limit_info)
    """
    rate_limiter = RateLimiter(supabase_client)
    return await rate_limiter.check_rate_limit(user_id, call_type=call_type)


async def log_ai_call(
    user_id: str,
    call_type: str,
    project_id: str = None,
    endpoint: str = None,
    supabase_client = None
) -> None:
    """
    Log AI call for rate limiting tracking.

    Args:
        user_id: User ID making the call
        call_type: 'generation', 'edit', or 'question'
        project_id: Optional project ID
        endpoint: Optional endpoint path
        supabase_client: Supabase client instance
    """
    if supabase_client is None:
        supabase_client = get_supabase_client()

    rate_limiter = RateLimiter(supabase_client)
    await rate_limiter.log_ai_call(user_id, call_type, project_id, endpoint)

# async def business_analyzer(prompt: str, ) -> tuple[bool, Dict[str, Any]]:
#     """
#     Check if user has exceeded rate limit.
#     I'm building a website generator and I need to analyze the prompt to determine the site requirements/business analysis to be able to generate a template stucture for a website
#     This analysis will be an input to another AI model to generate a template stucture for a website
#     generate a business analysis for the prompt in json format
#     """
#     return True, {
#         "tier": "unknown",
#         "limit": 5,
#         "used": 0,
#         "remaining": 5,
#         "resets_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
#     }

# async def template_creation_analyzer(prompt: str, business_analysis: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
#     """
#     Check if user has exceeded rate limit.
#     """
#     return True, {
#         "tier": "unknown",
#         "limit": 5,
#         "used": 0,
#         "remaining": 5,
#         "resets_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
#     }

# @log_action(action_type='UPDATE', target_resource_type='generation_count')
# async def increment_generation_count(user_id: str, supabase_client) -> None:
#     """Increment user's generation count"""
#     try:
#         # Increment both counters
#         supabase_client.rpc(
#             "increment_generation_count",
#             {"user_id_param": user_id}
#         ).execute()
#     except Exception as e:
#         # If RPC doesn't exist, use direct update
#         logger.warning(f"RPC increment failed, using direct update: {str(e)}")
#         try:
#             response = supabase_client.table("users")\
#                 .select("current_period_generations, generation_count")\
#                 .eq("id", user_id)\
#                 .execute()
            
#             if response.data:
#                 data = response.data[0]
#                 supabase_client.table("users")\
#                     .update({
#                         "current_period_generations": data["current_period_generations"] + 1,
#                         "generation_count": data["generation_count"] + 1
#                     })\
#                     .eq("id", user_id)\
#                     .execute()
#         except Exception as inner_e:
#             logger.error(f"Failed to increment generation count: {str(inner_e)}")


# ============================================================================
# Helper Functions
# ============================================================================

async def check_project_limit(user_id: str, supabase_client) -> Tuple[bool, dict]:
    """
    Check if user has reached their project limit based on subscription tier.
    Free users are limited to 3 projects maximum.

    Returns:
        tuple: (is_allowed: bool, info: dict)
    """
    limit = 3
    try:
        # Get user's subscription tier
        user_response = supabase_client.table("users")\
            .select("*, user_subscriptions(id, status, subscription_tiers(tier_name))")\
            .eq("id", user_id)\
            .single()\
            .execute()

        if not user_response.data:
            logger.error(f"User {user_id} not found")
            return True, {"error": "user_not_found"}

        user = user_response.data

        # Get tier information
        subscription = user.get("user_subscriptions")
        if not subscription or not subscription.get("subscription_tiers"):
            # Default to free tier if no subscription
            tier_name = "free"
        else:
            tier_name = subscription["subscription_tiers"]["tier_name"]

        # Only check project limit for free tier users
        if tier_name != "free":
            return True, {"tier": tier_name}

        # Count user's existing projects (excluding soft-deleted ones)
        projects_response = supabase_client.table("projects")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .is_("deleted_at", "null")\
            .execute()

        project_count = projects_response.count or 0

        # Free users are limited to 5 projects
        if project_count >= limit:
            return False, {
                "tier": tier_name,
                "project_count": project_count,
                "project_limit": limit,
                "message": f"Free tier users are limited to 3 projects. You currently have {project_count} projects. Please delete some projects or upgrade to Pro for unlimited projects.",
                "upgrade_suggestion": "Upgrade to Pro for unlimited projects and higher generation limits"
            }

        return True, {
            "tier": tier_name,
            "project_count": project_count,
            "project_limit": limit
        }

    except Exception as e:
        logger.error(f"Error checking project limit: {str(e)}")
        # Allow request on error to avoid blocking users
        return True, {"error": str(e)}


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
            "project_type": "react",
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


async def update_generation_progress(
    project_id: str,
    progress: int,
    stage: Optional[str] = None,
    stage_message: Optional[str] = None,
    supabase_client = None
) -> None:
    """
    Update generation progress with stage information for live updates.
    
    Args:
        project_id: The project ID
        progress: Progress percentage (0-100)
        stage: Current generation stage (e.g., "analyzing", "generating_structure")
        stage_message: Human-readable message for the current stage
        supabase_client: Supabase client instance (optional, will create if not provided)
    """
    try:
        if supabase_client is None:
            supabase_client = get_supabase_client()
        
        # Store progress info in generation_metadata JSON field
        # First, get existing metadata
        response = supabase_client.table("projects")\
            .select("generation_metadata")\
            .eq("id", project_id)\
            .execute()
        
        existing_metadata = {}
        if response.data and response.data[0].get("generation_metadata"):
            existing_metadata = response.data[0]["generation_metadata"]
        
        # Update metadata with progress info
        existing_metadata["progress"] = progress
        if stage:
            existing_metadata["stage"] = stage
        if stage_message:
            existing_metadata["stage_message"] = stage_message
        
        update_data = {
            "generation_metadata": existing_metadata,
            "generation_status": "generating",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase_client.table("projects")\
            .update(update_data)\
            .eq("id", project_id)\
            .execute()
        
        logger.debug(f"[PROGRESS] Updated progress for {project_id}: {progress}% - {stage}")
            
    except Exception as e:
        logger.error(f"Error updating generation progress: {str(e)}")


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
def generate_react_website_background(
    prompt: str,
):
    """Background task for React website generation"""
    supabase = get_supabase_client()
    
    try:        
        # Generate complete React website structure
        logger.info(f"[REACT BG] Generating React website structure...")
        result = react_website_generator.generate_website_structure(prompt)
        return result
        
        
    except Exception as e:
        logger.error(f"[REACT BG] ✗ React generation failed: {str(e)}")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/generate_website", response_model=GenerateWebsiteResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_react_website_from_prompt(
    request: GenerateWebsiteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a complete website from prompt only.
    Uses asyncio.create_task for background generation with live progress updates.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    logger.info(f"Website generation requested by user {user_id}")
    error_message = None
    try:
        # Step 1: Check rate limits first (dual: per-minute + daily)
        logger.info("Checking rate limits...")
        is_allowed, rate_info = await check_user_rate_limit(user_id, supabase)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_id}: {rate_info.get('limit_type')}")
            error_message = rate_info.get('message', 'Rate limit exceeded')
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=rate_info.get('message', 'Rate limit exceeded'),
                headers={
                    "Retry-After": str(rate_info.get('retry_after_seconds', 60)),
                    "X-RateLimit-Type": rate_info.get('limit_type', 'unknown'),
                    "X-RateLimit-Tier": rate_info.get('tier', 'unknown')
                }
            )

        # Step 2: Check project limit for free users
        logger.info("Checking project limit...")
        is_allowed, project_limit_info = await check_project_limit(user_id, supabase)

        if not is_allowed:
            logger.warning(f"Project limit exceeded for user {user_id}: {project_limit_info.get('project_count')}/{project_limit_info.get('project_limit')}")
            error_message = project_limit_info.get('message', 'Project limit exceeded')
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": project_limit_info.get('message', 'Project limit exceeded'),
                    "project_count": project_limit_info.get('project_count'),
                    "project_limit": project_limit_info.get('project_limit'),
                    "tier": project_limit_info.get('tier'),
                    "upgrade_suggestion": project_limit_info.get('upgrade_suggestion')
                }
            )

        # Step 3: Create project
        logger.info("Creating project...")
        project_id = await create_project(
            user_id=user_id,
            project_name=request.project_name or f"React Website - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            prompt=request.prompt,
            template_id=None,
            supabase_client=supabase
        )

        # Step 3.5: Link pre-project media uploads (dashboard attachments) to the new project
        if request.attachments:
            try:
                media_ids = [a["media_id"] for a in request.attachments if a.get("media_id")]
                if media_ids:
                    supabase.table("project_media")\
                        .update({"project_id": project_id})\
                        .in_("id", media_ids)\
                        .eq("user_id", user_id)\
                        .execute()
                    logger.info(f"Linked {len(media_ids)} media attachment(s) to project {project_id}")
            except Exception as e:
                logger.warning(f"Failed to link media attachments to project {project_id}: {e}")

        # Step 4: Log AI call for rate limiting (counts as 1 generation)
        await log_ai_call(
            user_id=user_id,
            call_type="generation",
            project_id=project_id,
            endpoint="/generate_website",
            supabase_client=supabase
        )

        # Step 5: Start BACKGROUND generation using asyncio.create_task for proper async handling
        logger.info(f"Starting background generation for project {project_id}")
        # Use asyncio.create_task instead of background_tasks for better async control
        # background_tasks.add_task(
        #     process_react_generation,  # New function below
        #     project_id=project_id,
        #     prompt=request.prompt,
        #     user_id=user_id
        # )
        asyncio.create_task(
            process_react_generation(
                project_id=project_id,
                prompt=request.prompt,
                user_id=user_id,
                attachments=request.attachments
            )
        )

        logger.info(f"✓ Generation initiated for project {project_id}")
        
        # Return immediately with "generating" status
        return GenerateWebsiteResponse(
            project_id=project_id,
            status="generating",
            message="React website generation started. Check status endpoint for progress."
        )

    except Exception as e:
        logger.error(f"Unexpected error during generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="React website generation failed. " + error_message
        )


async def process_react_generation(project_id: str, prompt: str, user_id: str, attachments: Optional[List[Dict[str, Any]]] = None):
    """Background task that actually does the generation with live progress updates"""
    supabase = get_supabase_client()

    # Classify uploaded images (logo / product photo / style reference) once;
    # the block is injected verbatim downstream (business analysis summarizes the
    # prompt, which would mangle exact URLs). The stored project prompt stays as
    # the user wrote it.
    media_context = None
    if attachments:
        try:
            from app.services.media_classifier import build_media_context
            media_context = await build_media_context(attachments, prompt)
            if media_context:
                logger.info(f"[BG] Media context built for project {project_id}")
        except Exception as e:
            logger.warning(f"[BG] Media classification failed, generating without media context: {e}")
    
    # Import CostTracker
    from app.services.cost_calculator import CostTracker
    
    # Initialize cost tracker
    cost_tracker = CostTracker(
        generation_type="website",
        endpoint="/generate_website"
    )

    try:
        logger.info(f"[BG] Starting React generation for project {project_id}")
        logger.info(f"[BG] Cost tracker initialized for project {project_id}")
        
        # Update initial status
        await update_generation_progress(
            project_id=project_id,
            progress=5,
            stage="analyzing",
            stage_message="Analyzing your requirements and understanding your business needs...",
            supabase_client=supabase
        )
        
        # Step 0: Determine if animations should be enabled based on user tier
        enable_animations = settings.enable_animations_default  # Start with config default
        
        try:
            # Fetch user subscription tier
            user_response = supabase.table("users").select(
                "user_subscriptions(subscription_tiers(tier_name))"
            ).eq("id", user_id).single().execute()
            
            if user_response.data and user_response.data.get("user_subscriptions"):
                tier_data = user_response.data["user_subscriptions"].get("subscription_tiers", {})
                tier_name = tier_data.get("tier_name", "free")
                
                # Pro and enterprise users always get  nimations
                if tier_name in ["pro", "enterprise"]:
                    enable_animations = True
                    logger.info(f"[BG] Animations enabled for {tier_name} tier user")
                else:
                    logger.info(f"[BG] Animations {'enabled' if enable_animations else 'disabled'} based on config (tier: {tier_name})")
                await ActionLogger(supabase).log_action(
                    user_id=user_id,
                    action="animation_enabled",
                    details={"user_id": user_id, "tier_name": tier_name, "enable_animations": enable_animations}
                )
            else:
                logger.warning(f"[BG] No subscription found for user {user_id}, using config default: {enable_animations}")
                await ActionLogger(supabase).log_action(
                    user_id=user_id,
                    action="animation_disabled",
                    details={"user_id": user_id, "tier_name": "free", "enable_animations": enable_animations}
                )
        except Exception as e:
            logger.warning(f"[BG] Failed to fetch user tier: {str(e)}, using config default: {enable_animations}")
        
        # Update progress: Starting structure generation
        await update_generation_progress(
            project_id=project_id,
            progress=15,
            stage="generating_structure",
            stage_message="Designing the blueprint and architecture of your website...",
            supabase_client=supabase
        )
        
        # Step 1: Generate React website (SYNC function) with cost tracking and progress callback
        # Store the event loop reference before calling sync function
        loop = asyncio.get_running_loop()
        
        # Create a progress callback that updates the database
        async def progress_callback(progress: int, stage: str, stage_message: str):
            """Callback to update progress during generation"""
            await update_generation_progress(
                project_id=project_id,
                progress=progress,
                stage=stage,
                stage_message=stage_message,
                supabase_client=supabase
            )
        
        # Note: Since generate_website_structure is sync and blocks the event loop,
        # we need a wrapper that can schedule async tasks from a sync context.
        # We'll use run_coroutine_threadsafe to schedule from the sync thread to the async loop.
        def sync_progress_callback(progress: int, stage: str, stage_message: str):
            """Synchronous wrapper for async progress callback"""
            try:
                logger.info(f"[BG] Progress callback called: {progress}% - {stage}")
                # Schedule the coroutine to run on the event loop
                # This works even when called from a sync function running in a thread
                future = asyncio.run_coroutine_threadsafe(
                    progress_callback(progress, stage, stage_message),
                    loop
                )
                # Don't wait for the result - fire and forget
                logger.debug(f"[BG] Scheduled progress update: {progress}% - {stage}")
            except Exception as e:
                # Log error but don't fail the generation
                logger.warning(f"[BG] Failed to schedule progress callback: {str(e)}", exc_info=True)

        # Run the sync function in a thread pool executor so it doesn't block the event loop
        # This allows progress callbacks to execute immediately
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                lambda: react_website_generator.generate_website_structure(
                    prompt,
                    enable_animations=enable_animations,
                    cost_tracker=cost_tracker,
                    progress_callback=sync_progress_callback,
                    media_context=media_context
                )
            )
        # await asyncio.sleep(10)
        # progress_callback(progress=40, stage="creating_components", stage_message="Assembling pages and layouts for your website...")
        # result = {"website_structure": "website_structure", "business_analysis": "business_analysis", "validation": "validation", "files": ", "cost_breakdown": "cost_breakdown"}
        # await asyncio.sleep(10)
        # progress_callback(progress=60, stage="building_pages", stage_message="Assembling pages and layouts for your website...")
        # await asyncio.sleep(10)
        website_structure = result["website_structure"]
        business_analysis = result["business_analysis"]
        validation_result = result["validation"]
        files = result["files"]
        cost_breakdown = result.get("cost_breakdown")
        
        # Step 2: Save files to database (ASYNC)
        logger.info(f"[BG] Saving {len(files)} files to database...")
        
        # Update progress: Saving files
        await update_generation_progress(
            project_id=project_id,
            progress=85,
            stage="saving_files",
            stage_message="Saving your project files securely...",
            supabase_client=supabase
        )
        
        stats = await project_file_manager.save_project_files(
            project_id=project_id,
            files=files,
            overwrite=True
        )
        
        logger.info(f"[BG] ✓ Saved {stats['inserted']} files ({stats['total_size'] / 1024:.2f} KB)")
        
        # Update progress: Finalizing
        await update_generation_progress(
            project_id=project_id,
            progress=95,
            stage="finalizing",
            stage_message="Adding finishing touches and preparing your website...",
            supabase_client=supabase
        )

        # Step 3: Update project with metadata
        logger.info(f"[BG] Updating project metadata...")
        generation_metadata = {
            "retry_count": result.get("retry_count", 0),
            "fixed_errors": result.get("fixed_errors", []),
            "generation_time": result.get("generation_time", 0),
            "files_count": stats.get("inserted", 0),
            "total_size_bytes": stats.get("total_size", 0)
        }
        
        # Add cost breakdown to metadata if available
        if cost_breakdown:
            generation_metadata["cost_breakdown"] = cost_breakdown
        
        # Ensure metadata includes final progress
        generation_metadata["progress"] = 100
        generation_metadata["stage"] = "completed"
        generation_metadata["stage_message"] = "Generation completed successfully!"
        
        update_data = {
            "name": result.get("name", "My Generated Website - " + datetime.utcnow().strftime("%Y-%m-%d %H:%M")),
            "website_structure": website_structure,
            "business_analysis": business_analysis,
            "validation_result": validation_result,
            "generation_metadata": generation_metadata,
            "generation_status": "completed",
            "last_generated_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        supabase.table("projects").update(update_data).eq("id", project_id).execute()

        await ActionLogger(supabase).log_action(
            user_id=user_id,
            action="generation_completed_successfully",
            details={
                "project_id": project_id,
                "generation_metadata": generation_metadata,
                "generation_status": "completed",
                "last_generated_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )

        # Step 4: Save cost tracking to database
        if cost_tracker:
            cost_tracker.mark_completed()
            tracking_id = await cost_tracker.save_to_database(
                project_id=project_id,
                user_id=user_id,
                supabase_client=supabase
            )
            if tracking_id:
                logger.info(f"[BG] ✓ Cost tracking saved: {tracking_id}")
            else:
                logger.warning(f"[BG] ⚠ Failed to save cost tracking")
            await ActionLogger(supabase).log_action(
                user_id=user_id,
                action="cost_tracking_completed_successfully",
                details={
                    "project_id": project_id,
                    "tracking_id": tracking_id
                }
            )

        logger.info(f"[BG] ✓ React generation completed for project {project_id}")

        # # Step 4: Save initial generation to chat history
        # logger.info(f"[BG] Saving initial generation to chat history...")
        # try:
        #     # Create initial chat message
        #     chat_message_id = str(uuid.uuid4())
        #     business_type = business_analysis.get("business_type", "website")
        #     pages_count = len(website_structure.get("pages", []))

        #     ai_response = (
        #         f"Website generated successfully! I've created a complete React website for your {business_type}. "
        #         f"The project includes {pages_count} pages with responsive design and modern styling. "
        #         f"Your React project is ready to view and edit."
        #     )

            # chat_insert = supabase.table("project_chat_messages").insert({
            #     "id": chat_message_id,
            #     "project_id": project_id,
            #     "user_id": user_id,
            #     "message_type": "generation",
            #     "user_prompt": prompt,
            #     "ai_response": ai_response,
            #     "metadata": {
            #         "business_analysis": {
            #             "business_type": business_analysis.get("business_type"),
            #             "target_audience": business_analysis.get("target_audience"),
            #             "key_features": business_analysis.get("key_features", [])[:3]  # First 3 features
            #         },
            #         "website_structure": {
            #             "pages_count": pages_count,
            #             "pages": [page.get("name") for page in website_structure.get("pages", [])]
            #         },
            #         "files_count": len(files)
            #     }
            # }).execute()

            # logger.info(f"[BG] ✓ Saved initial chat message with ID: {chat_message_id}")

        # except Exception as e:
        #     logger.error(f"[BG] Failed to save chat message: {str(e)}")
        #     # Don't fail the generation if chat save fails

        return GenerateReactWebsiteResponse(
            project_id=project_id,
            status="completed",
            message="React website generation completed",

            website_structure=website_structure,
            business_analysis=business_analysis,
            validation_result=validation_result,
            files_count=len(files)
        )
        
    except Exception as e:
        logger.error(f"[BG] ✗ React generation failed: {str(e)}", exc_info=True)
        
        # Mark cost tracker as failed and save
        if cost_tracker:
            cost_tracker.mark_failed(str(e))
            try:
                tracking_id = await cost_tracker.save_to_database(
                    project_id=project_id,
                    user_id=user_id,
                    supabase_client=supabase
                )
                if tracking_id:
                    logger.info(f"[BG] ✓ Failed generation cost tracking saved: {tracking_id}")
            except Exception as cost_error:
                logger.error(f"[BG] Failed to save cost tracking: {str(cost_error)}")
            await ActionLogger(supabase).log_action(
                user_id=user_id,
                action="cost_tracking_failed",
                details={
                    "project_id": project_id,
                    "error_message": str(cost_error)
                }
            )
        # Update project status to failed
        await update_project_status(
            project_id=project_id,
            status_value="failed",
            error=str(e),
            supabase_client=supabase
        )


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

        # Step 7: Log AI call for rate limiting (counts as 1 generation)
        await log_ai_call(
            user_id=user_id,
            call_type="generation",
            project_id=project_id,
            endpoint="/generate_website",
            supabase_client=supabase
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
    Check the status of website generation with live progress updates.
    
    Status values:
    - "idle": Not started yet
    - "generating": In progress
    - "completed": Successfully generated
    - "failed": Generation failed
    
    Progress information is stored in generation_metadata and includes:
    - progress: 0-100 percentage
    - stage: Current generation stage
    - stage_message: Human-readable stage message
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    try:
        # Fetch project with generation_metadata
        response = supabase.table("projects")\
            .select("generation_status, generation_error, generation_metadata, created_at, last_generated_at, user_id")\
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
        
        # Extract progress info from generation_metadata
        metadata = project.get("generation_metadata") or {}
        progress = metadata.get("progress")
        stage = metadata.get("stage")
        stage_message = metadata.get("stage_message")
        
        # Fallback progress calculation if not in metadata
        if progress is None:
            if status_value == "generating":
                progress = 50  # Mid-way estimate
            elif status_value == "completed":
                progress = 100
            elif status_value == "failed":
                progress = 0
            else:
                progress = 0
        
        return GenerationStatusResponse(
            status=status_value,
            project_id=project_id,
            progress=progress,
            stage=stage,
            stage_message=stage_message,
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
        "generating": "Generating your website... This may take 4-6 minutes",
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
        # Step 1: Check rate limits (dual: per-minute + daily)
        logger.info("Checking rate limits...")
        is_allowed, rate_info = await check_user_rate_limit(user_id, supabase)
        await ActionLogger(supabase).log_action(
            user_id=user_id,
            action="rate_limit_check",
            details={"user_id": user_id, "rate_info": rate_info, "is_allowed": is_allowed}
        )

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_id}: {rate_info.get('limit_type')}")
            await ActionLogger(supabase).log_action(
                user_id=user_id,
                action="rate_limit_check_failed",
                details={
                    "user_id": user_id,
                    "rate_info": rate_info,
                    "is_allowed": is_allowed,
                    "message": rate_info.get('message', 'Rate limit exceeded')
                }
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=rate_info.get('message', 'Rate limit exceeded'),
                headers={
                    "Retry-After": str(rate_info.get('retry_after_seconds', 60)),
                    "X-RateLimit-Type": rate_info.get('limit_type', 'unknown'),
                    "X-RateLimit-Tier": rate_info.get('tier', 'unknown')
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

        # Step 4.5: Log AI call for rate limiting (counts as 1 generation)
        await log_ai_call(
            user_id=user_id,
            call_type="generation",
            project_id=project_id,
            endpoint="/generate_react_website",
            supabase_client=supabase
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
            .select(
                "id, user_id, name, description, prompt, project_type, "
                "website_structure, business_analysis, validation_result, generation_metadata, "
                "generation_status, generation_error, files_count, "
                "created_at, last_generated_at, updated_at"
            )\
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
        
         # JSONB columns are automatically parsed as dicts by Supabase client
        website_structure = project.get("website_structure", {})
        business_analysis = project.get("business_analysis", {})
        validation_result = project.get("validation_result", {})
        generation_metadata = project.get("generation_metadata", {})

        # (only if user needs them - lazy loading)
        from app.services.project_file_manager import project_file_manager
        
        # Option 1: Fetch all files
        files = await project_file_manager.get_project_files(project_id)

        return {
            "project_id": project_id,
            "name": project["name"],
            "status": project.get("generation_status", "idle"),
            
            # Metadata from projects table (JSONB)
            "website_structure": website_structure,
            "business_analysis": business_analysis,
            "validation_result": validation_result,
            "generation_metadata": generation_metadata,
            
            # Files from project_files table
            "files": files,
            "files_count": len(files),
            
            # Timestamps
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


# ============================================================================
# Preview Endpoints
# ============================================================================

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


def _find_page_file(files: Dict[str, str]) -> Optional[str]:
    """Pick the page file to target for a no-selection (whole page) edit."""
    page_files = sorted(f for f in files if f.startswith("src/pages/") and f.endswith(".tsx"))
    # Prefer the landing page regardless of casing (Home.tsx, home.tsx, index.tsx, ...)
    for name in ("home.tsx", "index.tsx", "landing.tsx", "main.tsx"):
        for f in page_files:
            if f.rsplit("/", 1)[-1].lower() == name:
                return f
    if page_files:
        return page_files[0]
    if "src/App.tsx" in files:
        return "src/App.tsx"
    return None


async def _run_edit_pipeline(
    project_id: str,
    request: ComponentEditRequest,
    user_id: str,
    progress=None,
) -> ComponentEditResponse:
    """
    Core edit pipeline shared by the standard and streaming edit endpoints.

    Identifies the target component, runs the AI edit (multimodal + structural
    escalation), build-verifies, saves, and records history. `progress(stage,
    detail)` — if provided — is called at stage boundaries so the streaming
    endpoint can surface live status; it's a no-op for the standard endpoint.

    Returns a ComponentEditResponse or raises HTTPException.
    """
    progress = progress or (lambda *a, **k: None)
    supabase = get_supabase_client()

    logger.info(f"[COMPONENT EDIT] Starting edit request for project {project_id} by user {user_id}")
    logger.info(f"[COMPONENT EDIT] Instruction: '{request.instruction}' (length: {len(request.instruction)})")
    if request.selected_element:
        logger.info(f"[COMPONENT EDIT] Selected element tag: {request.selected_element.get('tagName', 'unknown')}")
        logger.info(f"[COMPONENT EDIT] Selected element text content: '{request.selected_element.get('textContent', '')[:50]}...'")
    else:
        logger.info(f"[COMPONENT EDIT] No element selected — page-scope edit")

    try:
        # Check edit-specific rate limits (dual: per-minute + daily, separate from generation quota)
        logger.info(f"[COMPONENT EDIT] Checking rate limits...")
        is_allowed, rate_info = await check_user_rate_limit(user_id, supabase, call_type="edit")

        if not is_allowed:
            logger.warning(f"[COMPONENT EDIT] Rate limit exceeded for user {user_id}: {rate_info.get('limit_type')}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=rate_info.get('message', 'Rate limit exceeded'),
                headers={
                    "Retry-After": str(rate_info.get('retry_after_seconds', 60)),
                    "X-RateLimit-Type": rate_info.get('limit_type', 'unknown'),
                    "X-RateLimit-Tier": rate_info.get('tier', 'unknown')
                }
            )

        # Verify project ownership and fetch business context
        logger.info(f"[COMPONENT EDIT] Fetching project {project_id} from database")
        response = supabase.table("projects")\
            .select("id, user_id, project_type, generation_status, business_analysis, preview_id")\
            .eq("id", project_id)\
            .execute()

        if not response.data:
            logger.error(f"[COMPONENT EDIT] Project {project_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        logger.info(f"[COMPONENT EDIT] Found project: type={project.get('project_type')}, status={project.get('generation_status')}, owner={project.get('user_id')}")
        
        # Check ownership
        if project["user_id"] != user_id:
            logger.error(f"[COMPONENT EDIT] Access denied: user {user_id} does not own project {project_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if it's a React project
        if project.get("project_type") != "react":
            logger.error(f"[COMPONENT EDIT] Project {project_id} is not a React project (type: {project.get('project_type')})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This is not a React project"
            )
        
        # Check if project is completed
        if project.get("generation_status") != "completed":
            logger.error(f"[COMPONENT EDIT] Project {project_id} is not completed (status: {project.get('generation_status')})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project generation is not completed yet"
            )
        
        # Resolve the selection set (multi-select sends selected_elements; single select falls back)
        selected_elements = request.selected_elements or (
            [request.selected_element] if request.selected_element else []
        )
        scope = request.scope or "element"
        files = await project_file_manager.get_project_files(project_id)

        if not selected_elements:
            # No selection: the whole page is the target (chat message without a selection)
            scope = "page"
            page_file = _find_page_file(files)
            if not page_file:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not identify a page file to edit"
                )
            selected_elements = [{
                "tagName": "page",
                "textContent": "",
                "classList": [],
                "attributes": {},
                "component": {"componentFile": page_file},
            }]
        logger.info(f"[COMPONENT EDIT] Editing {len(selected_elements)} selected element(s), scope={scope}")

        # Group selected elements by their component file
        targets_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for element in selected_elements:
            component_file = await component_editor_service.identify_component(element, files)
            if not component_file:
                logger.error(f"[COMPONENT EDIT] Could not identify component file for element: {element.get('tagName', 'unknown')}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not identify component file for one of the selected elements"
                )
            targets_by_file.setdefault(component_file, []).append(element)

        logger.info(f"[COMPONENT EDIT] Target files: {list(targets_by_file.keys())}")

        # Extract business context for better AI editing
        business_analysis = project.get("business_analysis", {})
        logger.info(f"[COMPONENT EDIT] Business analysis available: {bool(business_analysis)}")

        # Conversational context: feed the last few edits so follow-ups resolve
        # ("make it darker" after "make the heading blue" should target the same
        # element/color without re-selection). Kept as a SEPARATE prompt block
        # (not merged into the instruction text) — mixing it into the quoted
        # "USER INSTRUCTION" let history bleed into targeting and caused edits
        # to land on a previously-touched element instead of the new selection.
        effective_instruction = request.instruction
        conversation_context = None
        try:
            recent_messages = (
                supabase.table("project_chat_messages")
                .select("user_prompt, ai_response")
                .eq("project_id", project_id)
                .eq("message_type", "edit")
                .order("created_at", desc=True)
                .limit(6)
                .execute()
            )
            history_rows = list(reversed(recent_messages.data or []))
            if history_rows:
                transcript_lines = []
                budget = 1500  # rough character budget, not exact tokens
                for row in history_rows:
                    line = f'User: {row["user_prompt"][:200]}\nApplied: {row["ai_response"][:200]}'
                    if budget - len(line) < 0:
                        break
                    transcript_lines.append(line)
                    budget -= len(line)
                if transcript_lines:
                    conversation_context = "\n---\n".join(transcript_lines)
        except Exception as e:
            logger.warning(f"[COMPONENT EDIT] Failed to load conversational context: {e}")

        # Make uploaded attachment URLs available to the LLM: when the user says
        # "use the attached image", the model must embed these exact public URLs.
        # The images themselves are also sent as multimodal input (base64 data URLs).
        attachment_images: List[str] = []
        if request.attachments:
            media_ids = [a["media_id"] for a in request.attachments if a.get("media_id")]
            if media_ids:
                owned = supabase.table("project_media")\
                    .select("id")\
                    .in_("id", media_ids)\
                    .eq("user_id", user_id)\
                    .execute()
                owned_ids = {r["id"] for r in (owned.data or [])}
                if owned_ids != set(media_ids):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="One or more attachments do not belong to you"
                    )
            attachment_urls = [a["url"] for a in request.attachments if a.get("url")]
            attachment_images = await fetch_images_as_data_urls(attachment_urls)
            if attachment_urls:
                url_lines = "\n".join(f"  {i+1}. {u}" for i, u in enumerate(attachment_urls))
                effective_instruction = (
                    f"{effective_instruction}\n\n"
                    f"[The user attached {len(attachment_urls)} uploaded image(s), publicly hosted at:\n"
                    f"{url_lines}\n"
                    f"Follow the ATTACHED IMAGES guidance for whether to embed these URLs or "
                    f"treat the images as a style reference only.]"
                )
                logger.info(f"[COMPONENT EDIT] {len(attachment_urls)} attachment URL(s) added to instruction context")

        # Analyze the request once up front: structural rewrites ("turn this into
        # a carousel") escalate element scope to section, drop containment, and
        # pull vetted patterns (+ their npm deps) from the component library.
        progress("analyzing", "Understanding your request")
        edit_analysis = await component_editor_service.analyze_edit_request(
            effective_instruction, selected_elements[0], images=attachment_images or None
        )
        is_structural = bool(edit_analysis.get("requires_structural_rewrite")) and \
            edit_analysis.get("confidence", 0) >= 0.6
        matched_library = []
        library_note = None
        if is_structural:
            matched_library = component_library.match_components(
                edit_analysis.get("suggested_components"), request.instruction
            )
            library_note = component_library.build_library_note(matched_library)
            if scope == "element":
                scope = "section"
                logger.info(
                    f"[COMPONENT EDIT] Structural rewrite detected "
                    f"(components: {[c.name for c in matched_library]}) — escalating scope to section"
                )

        # LLM edit per target file, with scope-containment verification and one strict retry
        old_codes: Dict[str, str] = {}
        new_codes: Dict[str, str] = {}
        for component_file, targets in targets_by_file.items():
            primary_element = targets[0]
            additional = targets[1:]
            strict_note = None
            contained = True
            old_code, new_code = "", ""

            progress("editing", f"Rewriting {component_file.split('/')[-1]}")
            for attempt in range(2):
                logger.info(f"[COMPONENT EDIT] Calling AI to modify {component_file} (attempt {attempt + 1})")
                success, old_code, new_code, error = await component_editor_service.modify_component_code(
                    file_path=component_file,
                    instruction=effective_instruction,
                    element_context=primary_element,
                    project_id=project_id,
                    files=files,
                    business_context=business_analysis,
                    additional_contexts=additional,
                    scope=scope,
                    strict_note=strict_note,
                    images=attachment_images or None,
                    analysis=edit_analysis,
                    library_note=library_note,
                    conversation_context=conversation_context
                )

                if not success:
                    logger.error(f"[COMPONENT EDIT] AI modification failed: {error}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to modify component: {error}"
                    )

                # Element scope must only change the selected element(s)
                if scope != "element":
                    break
                contained, violation = component_editor_service.check_edit_containment(
                    old_code, new_code, targets
                )
                if contained:
                    break
                strict_note = (
                    f"You modified code outside the selected element(s) ({violation}). "
                    "Output the original file with ONLY the selected element(s) changed; "
                    "reproduce every other line exactly."
                )

            if scope == "element" and not contained:
                logger.error(f"[COMPONENT EDIT] Containment violation persisted for {component_file}; nothing saved")
                return ComponentEditResponse(
                    success=False,
                    message=(
                        "The AI kept changing code outside your selection, so nothing was changed. "
                        "Try rephrasing the instruction or widening the scope to the section."
                    )
                )

            old_codes[component_file] = old_code
            new_codes[component_file] = new_code

        # Structural rewrites may need new npm deps (e.g. embla for carousels):
        # merge them into package.json BEFORE the preview build (which runs npm install)
        if matched_library and "package.json" in files:
            deps = component_library.collect_dependencies(matched_library)
            updated_package = component_library.ensure_package_dependencies(
                new_codes.get("package.json", files["package.json"]), deps
            )
            if updated_package:
                old_codes.setdefault("package.json", files["package.json"])
                new_codes["package.json"] = updated_package

        # Build-verify: the edit is only saved after the project compiles.
        # On failure, feed build errors back to the LLM for up to 2 repair attempts.
        progress("building", "Building and verifying the preview")
        candidate_files = {**files, **new_codes}
        preview_result = None
        build_output = ""
        build_tester = BuildTester()
        max_repair_attempts = 2

        for attempt in range(max_repair_attempts + 1):
            try:
                preview_result = await asyncio.to_thread(
                    vite_preview_service.create_preview, project_id, candidate_files
                )
                break
            except Exception as build_exc:
                build_output = str(build_exc)
                logger.warning(f"[COMPONENT EDIT] Candidate build failed (attempt {attempt + 1}): {build_output[:500]}")
                if attempt >= max_repair_attempts:
                    break

                parsed_errors = build_tester._parse_build_errors(build_output)
                # Keep only errors that resolve to a real project file — the parser
                # sometimes attributes vite output to bogus paths like "build"
                parsed_errors = [
                    e for e in parsed_errors
                    if error_fixer._find_matching_file(e.file_path, candidate_files)
                ]
                if not parsed_errors:
                    # Attribute errors from file paths mentioned in the build output,
                    # falling back to the files this edit touched
                    import re as _re
                    mentioned = {
                        m for m in _re.findall(r"src/[\w\-./]+\.(?:tsx|ts|jsx|js|css)", build_output)
                        if m in candidate_files
                    }
                    target_files = mentioned or set(new_codes.keys())
                    parsed_errors = [
                        BuildError(file_path=f, line=None, column=None,
                                   error_type="build", message=build_output[:1500])
                        for f in target_files
                    ]

                fixed_files, _ = await asyncio.to_thread(
                    error_fixer.fix_build_errors, candidate_files, parsed_errors, build_output
                )
                candidate_files = fixed_files
                # Keep edited-file contents in sync with any repairs
                for f in new_codes:
                    new_codes[f] = candidate_files.get(f, new_codes[f])

        if preview_result is None:
            logger.error(f"[COMPONENT EDIT] Build failed after {max_repair_attempts} repair attempts; nothing saved")
            return ComponentEditResponse(
                success=False,
                message=(
                    "The AI's change didn't compile, so nothing was changed. "
                    "Try rephrasing the instruction."
                )
            )

        # Green build — persist every file that changed (edits + any build repairs)
        files_to_save = {
            path: content for path, content in candidate_files.items()
            if files.get(path) != content
        }
        logger.info(f"[COMPONENT EDIT] Saving {len(files_to_save)} changed file(s) to database")
        for file_path, file_content in files_to_save.items():
            save_success, save_message = await component_editor_service.apply_component_edit(
                project_id=project_id,
                file_path=file_path,
                new_code=file_content
            )
            if not save_success:
                logger.error(f"[COMPONENT EDIT] Failed to save {file_path}: {save_message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save component: {save_message}"
                )

        # Swap the project's preview to the freshly verified build and clean up the old one
        new_preview_id = preview_result.get("preview_id")
        preview_url = preview_result.get("preview_url")
        old_preview_id = project.get("preview_id")
        try:
            supabase.table("projects").update({"preview_id": new_preview_id}).eq("id", project_id).execute()
        except Exception as e:
            logger.warning(f"[COMPONENT EDIT] Failed to store new preview_id: {e}")
        try:
            supabase.table("projects").update(
                {"last_edited_at": datetime.utcnow().isoformat()}
            ).eq("id", project_id).execute()
        except Exception as e:
            logger.warning(f"[COMPONENT EDIT] Failed to stamp last_edited_at: {e}")
        if old_preview_id and old_preview_id != new_preview_id:
            try:
                vite_preview_service.delete_preview(old_preview_id)
            except Exception as e:
                logger.warning(f"[COMPONENT EDIT] Failed to delete old preview {old_preview_id}: {e}")

        # Primary file for descriptions/history (first target file)
        component_file = next(iter(targets_by_file.keys()))
        old_code = old_codes[component_file]
        new_code = new_codes[component_file]
        primary_element = request.selected_element or selected_elements[0]

        # Generate edit description
        edit_description = await component_editor_service.generate_edit_description(
            instruction=request.instruction,
            element_context=primary_element,
            file_path=component_file
        )
        logger.info(f"[COMPONENT EDIT] Generated description: {edit_description}")

        # Save to chat history
        logger.info(f"[COMPONENT EDIT] Saving to chat history")
        chat_message_id = str(uuid.uuid4())

        try:
            # Insert chat message
            chat_insert = supabase.table("project_chat_messages").insert({
                "id": chat_message_id,
                "project_id": project_id,
                "user_id": user_id,
                "message_type": "edit",
                "user_prompt": request.instruction,
                "ai_response": edit_description,
                "metadata": {
                    "file_path": component_file,
                    "scope": scope,
                    "selected_element": {
                        "tagName": primary_element.get('tagName', ''),
                        "textContent": (primary_element.get('textContent') or '')[:100],
                        "component": primary_element.get('component', {})
                    },
                    "attachments": request.attachments or []
                }
            }).execute()

            # Insert edit history — one row per changed file (including files the
            # build-repair step touched), all sharing this chat_message_id, so a
            # revert restores the complete pre-edit state.
            history_rows = [
                {
                    "project_id": project_id,
                    "chat_message_id": chat_message_id,
                    "file_path": file_path,
                    "old_code": files.get(file_path, ""),
                    "new_code": file_content,
                    "diff_summary": edit_description,
                    "selected_element": primary_element,
                    "edit_description": edit_description,
                    "ai_instruction": request.instruction
                }
                for file_path, file_content in files_to_save.items()
            ]
            if history_rows:
                supabase.table("project_edit_history").insert(history_rows).execute()

            logger.info(f"[COMPONENT EDIT] Chat and edit history saved successfully")

        except Exception as e:
            logger.error(f"[COMPONENT EDIT] Failed to save chat/edit history: {str(e)}")
            # Don't fail the request if history saving fails

        # Log the action
        logger.info(f"[COMPONENT EDIT] Logging action to database")
        action_logger = ActionLogger(supabase)
        await action_logger.log_action(
            user_id=user_id,
            action="component_edited",
            details={
                "project_id": project_id,
                "component_file": component_file,
                "instruction": request.instruction,
                "element_tag": primary_element.get('tagName', ''),
                "element_text": (primary_element.get('textContent') or '')[:100]
            }
        )

        # Log AI call for rate limiting (counts as 1 edit)
        await log_ai_call(
            user_id=user_id,
            call_type="edit",
            project_id=project_id,
            endpoint=f"/edit/project/{project_id}",
            supabase_client=supabase
        )

        logger.info(f"[COMPONENT EDIT] ✓ Component {component_file} edited successfully for project {project_id}")

        progress("done", "Edit applied")
        return ComponentEditResponse(
            success=True,
            message=f"Component {component_file} updated successfully",
            updated_file=component_file,
            updated_files=sorted(files_to_save.keys()),
            preview_url=preview_url,
            preview_id=new_preview_id,
            old_code=old_code,
            new_code=new_code,
            edit_description=edit_description,
            chat_message_id=chat_message_id
        )

    except HTTPException as e:
        logger.error(f"[COMPONENT EDIT] HTTPException: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(f"[COMPONENT EDIT] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to edit component"
        )


@router.post("/edit/project/{project_id}", response_model=ComponentEditResponse)
async def edit_project_component(
    project_id: str,
    request: ComponentEditRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Edit a React component using visual selection and natural language instructions.
    Standard (non-streaming) endpoint — runs the shared edit pipeline and returns
    the final result.
    """
    return await _run_edit_pipeline(project_id, request, current_user["id"])


@router.post("/edit/project/{project_id}/stream")
async def edit_project_component_stream(
    project_id: str,
    request: ComponentEditRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Streaming variant: runs the same edit pipeline but emits Server-Sent Events
    for each stage (analyzing → editing → building → done|error) so the chat can
    show live progress. The terminal event carries the full ComponentEditResponse
    (on success) or an error message. The frontend falls back to the standard
    endpoint if the stream fails.
    """
    user_id = current_user["id"]
    queue: asyncio.Queue = asyncio.Queue()

    def progress(stage: str, detail: str = ""):
        # Called from the pipeline's async context; thread-safe enough for our use
        queue.put_nowait({"type": "progress", "stage": stage, "detail": detail})

    async def run():
        try:
            result = await _run_edit_pipeline(project_id, request, user_id, progress=progress)
            queue.put_nowait({"type": "result", "data": result.model_dump()})
        except HTTPException as e:
            queue.put_nowait({"type": "error", "detail": str(e.detail), "status": e.status_code})
        except Exception as e:
            logger.error(f"[COMPONENT EDIT STREAM] Unexpected error: {e}", exc_info=True)
            queue.put_nowait({"type": "error", "detail": "Failed to edit component"})
        finally:
            queue.put_nowait(None)  # sentinel: stream complete

    async def event_generator():
        task = asyncio.create_task(run())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            if not task.done():
                await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx proxy buffering for SSE
        },
    )


async def _handle_property_edit(
    project_id: str,
    request: PropertyEditRequest,
    user_id: str,
    supabase: Any
) -> PropertyEditResponse:
    """
    Core handler for property edit operations.
    
    This function contains all the logic for editing properties and is called
    through the queue system to ensure sequential processing per project.
    
    Args:
        project_id: ID of the project being edited
        request: Property edit request containing changes
        user_id: ID of the current user
        supabase: Supabase client instance
    
    Returns:
        PropertyEditResponse with the edit results
    
    Raises:
        HTTPException: On validation or processing errors
    """
    logger.info(f"[PROPERTY EDIT] Handler processing edit for project {project_id}")
    logger.info(f"[PROPERTY EDIT] Editing {request.component_file} with {len(request.properties)} property changes")
    
    try:
        # Verify project ownership and type
        project_response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        
        if not project_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = project_response.data
        
        if project.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this project"
            )
        
        if project.get("project_type") != "react":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property editing is only supported for React projects"
            )
        
        # Load ALL project files (needed for prop-aware editing)
        logger.info(f"[PROPERTY EDIT] Loading all project files for {project_id}")
        project_files = await project_file_manager.get_project_files(project_id)

        if not project_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project files not found"
            )

        # Check if the component file exists
        if request.component_file not in project_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Component file '{request.component_file}' not found in project"
            )

        # Get the component file content
        original_code = project_files[request.component_file]

        logger.info(f"[PROPERTY EDIT] Applying {len(request.properties)} property changes to {request.component_file}")

        # Build component relationship map (needed for prop-based edits)
        component_tracker = ComponentRelationshipTracker()

        # Log the property edit started
        await ActionLogger(supabase).log_action(
            user_id=user_id,
            action="property_edit_started",
            details={
                "project_id": project_id,
                "component_file": request.component_file,
                "properties": [p.property for p in request.properties]
            }
        )
        component_tracker.analyze_project_structure(project_files)

        # Convert PropertyChange objects to dicts for direct_code_editor
        properties_dict = [
            {
                "property": p.property,
                "value": p.value,
                "oldValue": p.oldValue,
                "unit": p.unit
            }
            for p in request.properties
        ]

        # Apply property changes using direct code editor
        success, modified_code, error_message, prop_edit_metadata = direct_code_editor.edit_properties(
            code=original_code,
            element_selector=request.element_selector,
            properties=properties_dict,
            files=project_files,
            component_tracker=component_tracker
        )

        await ActionLogger(supabase).log_action(
            user_id=user_id,
            action="property_edit_completed",
            details={
                "project_id": project_id,
                "component_file": request.component_file,
                "success": success,
                "error_message": error_message,
                "prop_edit_metadata": prop_edit_metadata
            }
        )

        # Check if this is a prop edit that needs parent component update
        prop_edit_info_response = None  # Initialize here so it's accessible later
        
        # If we have component edits (success=True and modified_code), save them first
        # This handles cases where both component edits (like alt) and prop edits (like src) are made
        if success and modified_code and prop_edit_metadata:
            logger.info(f"[PROPERTY EDIT] Saving component edits before handling prop edits")
            await project_file_manager.save_project_file(
                project_id=project_id,
                file_path=request.component_file,
                file_content=modified_code,
                overwrite=False
            )
            # Update project_files dict with component edits for prop edit handling
            project_files[request.component_file] = modified_code
        
        # Handle array prop edits (array items passed as props)
        if prop_edit_metadata and prop_edit_metadata.get('type') == 'array_prop_edit':
            logger.info(f"[PROPERTY EDIT] Array prop edit detected - updating array '{prop_edit_metadata['prop_name']}[{prop_edit_metadata['array_index']}].{prop_edit_metadata['property_path']}' at source")
            
            # Update array item at source (parent component)
            array_prop_success, updated_files, array_prop_error = direct_code_editor.update_array_prop_at_source(
                files=project_files,
                component_file=request.component_file,
                prop_name=prop_edit_metadata['prop_name'],
                array_index=prop_edit_metadata['array_index'],
                property_path=prop_edit_metadata['property_path'],
                new_value=prop_edit_metadata['new_value'],
                object_name=prop_edit_metadata['object_name'],
                component_tracker=component_tracker
            )
            
            if array_prop_success and updated_files:
                logger.info(f"[PROPERTY EDIT] Successfully updated array prop at source")
                
                # Save all updated files
                files_updated = []
                prop_source_file = None
                for file_path, file_content in updated_files.items():
                    if file_content != project_files.get(file_path):
                        logger.info(f"[PROPERTY EDIT] Saving updated file: {file_path}")
                        await project_file_manager.save_project_file(
                            project_id=project_id,
                            file_path=file_path,
                            file_content=file_content,
                            overwrite=False
                        )
                        files_updated.append(file_path)
                        if file_path != request.component_file:
                            prop_source_file = file_path
                
                # Merge updated files into project_files (don't replace, as component file might not be in updated_files)
                project_files.update(updated_files)
                # Ensure modified_code is preserved if component file wasn't in updated_files
                if request.component_file not in updated_files and modified_code:
                    project_files[request.component_file] = modified_code
                # Get the latest modified_code (either from updated_files or preserved)
                modified_code = project_files.get(request.component_file, modified_code)
                
                logger.info(f"[PROPERTY EDIT] Updated {len(files_updated)} files: {files_updated}")
                
                # Store prop edit info for response
                prop_edit_info_response = {
                    'prop_name': prop_edit_metadata['prop_name'],
                    'source_file': prop_source_file or request.component_file,
                    'new_value': prop_edit_metadata['new_value']
                }
                
                # Mark as successful since we've updated the files
                success = True
            else:
                error_msg = f"Could not update array prop at source: {array_prop_error}"
                logger.error(f"[PROPERTY EDIT] {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
        
        # Handle regular prop edits
        elif prop_edit_metadata and prop_edit_metadata.get('type') == 'prop_edit':
            logger.info(f"[PROPERTY EDIT] Prop edit detected - updating prop '{prop_edit_metadata['prop_name']}' at source")

            # Update prop at source (parent component)
            prop_success, updated_files, prop_error = direct_code_editor.update_prop_at_source(
                files=project_files,
                component_file=request.component_file,
                prop_name=prop_edit_metadata['prop_name'],
                new_value=prop_edit_metadata['new_value'],
                component_tracker=component_tracker
            )

            if prop_success and updated_files:
                logger.info(f"[PROPERTY EDIT] Successfully updated prop at source")

                # Save all updated files
                files_updated = []
                prop_source_file = None
                for file_path, file_content in updated_files.items():
                    if file_content != project_files.get(file_path):
                        logger.info(f"[PROPERTY EDIT] Saving updated file: {file_path}")
                        await project_file_manager.save_project_file(
                            project_id=project_id,
                            file_path=file_path,
                            file_content=file_content,
                            overwrite=False
                        )
                        files_updated.append(file_path)
                        # The parent file (where prop is defined) is the one that's not the component file
                        if file_path != request.component_file:
                            prop_source_file = file_path

                # Merge updated files into project_files (don't replace, as component file might not be in updated_files)
                project_files.update(updated_files)
                # Ensure modified_code is preserved if component file wasn't in updated_files
                if request.component_file not in updated_files and modified_code:
                    project_files[request.component_file] = modified_code
                # Get the latest modified_code (either from updated_files or preserved)
                modified_code = project_files.get(request.component_file, modified_code)

                logger.info(f"[PROPERTY EDIT] Updated {len(files_updated)} files: {files_updated}")
                
                # Store prop edit info for response
                prop_edit_info_response = {
                    'prop_name': prop_edit_metadata['prop_name'],
                    'source_file': prop_source_file or request.component_file,
                    'new_value': prop_edit_metadata['new_value']
                }
            else:
                # Fallback: Couldn't update at source, hardcode the value
                logger.warning(f"[PROPERTY EDIT] Could not update prop at source: {prop_error}")
                logger.warning(f"[PROPERTY EDIT] Falling back to hardcoding the value in component")

                # Use modified_code if we have component edits, otherwise use original_code
                # This ensures we're working with the latest version of the component file
                code_to_use = modified_code if modified_code else original_code
                logger.info(f"[PROPERTY EDIT] Using {'modified_code' if modified_code else 'original_code'} for fallback")

                # Hardcode the value by directly replacing the JSX expression
                # Replace {propName} with the actual value
                prop_expr = f"{{{prop_edit_metadata['prop_name']}}}"
                new_value = prop_edit_metadata['new_value']

                # Use regex to find and replace the prop expression in the element
                # This is a simple find-replace that should work for most cases
                if prop_expr in code_to_use:
                    # Find the element and replace the prop expression
                    # We need to be careful to only replace within the specific element
                    element_selector = request.element_selector

                    # Use the direct editor to find the element content
                    from app.services.direct_code_editor import DirectCodeEditor
                    editor = DirectCodeEditor()
                    element_data = editor._find_element_content(code_to_use, element_selector)

                    if element_data:
                        _, tag_end, content_end, _, _, old_content = element_data

                        if prop_expr in old_content:
                            # Replace the prop expression with the new value
                            new_content = old_content.replace(prop_expr, new_value)
                            modified_code = code_to_use[:tag_end] + new_content + code_to_use[content_end:]

                            logger.info(f"[PROPERTY EDIT] Successfully hardcoded value in component")

                            # Save the hardcoded version
                            await project_file_manager.save_project_file(
                                project_id=project_id,
                                file_path=request.component_file,
                                file_content=modified_code,
                                overwrite=False
                            )

                            # Update project_files dict for preview
                            project_files[request.component_file] = modified_code
                        else:
                            # Couldn't find prop expression in element
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Could not update prop '{prop_edit_metadata['prop_name']}' at source and fallback failed: {prop_error}"
                            )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Could not locate element for fallback edit: {prop_error}"
                        )
                else:
                    await ActionLogger(supabase).log_action(
                        user_id=user_id,
                        action="property_edit_fallback_failed",
                        details={"project_id": project_id, "component_file": request.component_file, "error_message": "Could not find prop expression in element", "prop_name": prop_edit_metadata['prop_name']}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Could not update prop '{prop_edit_metadata['prop_name']}' at source and fallback failed: {prop_error}"
                    )

        elif not success:
            # Log the failed file
            await ActionLogger(supabase).log_action(
                user_id=user_id,
                action="property_edit_failed",
                details={"project_id": project_id, "component_file": request.component_file, "error_message": error_message}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to apply property changes: {error_message}"
            )

        else:
            # Regular direct edit (not a prop)
            # Save the updated file
            logger.info(f"[PROPERTY EDIT] Saving updated file to project {project_id}")
            await project_file_manager.save_project_file(
                project_id=project_id,
                file_path=request.component_file,
                file_content=modified_code,
                overwrite=False
            )

            # Update project_files dict for preview
            project_files[request.component_file] = modified_code
        
        # Rebuild preview in background so it's ready for next load (tab switch, page reload)
        # Don't return preview_url to frontend to avoid iframe reload (keeps optimistic update visible)
        logger.info(f"[PROPERTY EDIT] Rebuilding preview in background")
        preview_url = None  # Don't return URL to frontend
        
        try:
            existing_preview = project.get("preview_id")
            
            if existing_preview:
                preview_status = vite_preview_service.get_preview_status(existing_preview)
                
                if preview_status and preview_status.get("exists"):
                    # Update existing preview in background
                    # Include all files that were updated (component + parent files for prop edits)
                    logger.info(f"[PROPERTY EDIT] Updating preview {existing_preview} in background")
                    changed_files = {}
                    
                    # Always include the component file
                    if request.component_file in project_files:
                        changed_files[request.component_file] = project_files[request.component_file]
                    
                    # Include parent files if they were updated (for prop edits)
                    if prop_edit_info_response and prop_edit_info_response.get('source_file'):
                        source_file = prop_edit_info_response['source_file']
                        if source_file != request.component_file and source_file in project_files:
                            changed_files[source_file] = project_files[source_file]
                            logger.info(f"[PROPERTY EDIT] Including parent file '{source_file}' in preview update")
                    
                    if changed_files:
                        update_result = vite_preview_service.update_preview_files(
                            preview_id=existing_preview,
                            updated_files=changed_files
                        )
                        
                        if update_result.get("success"):
                            build_time = update_result.get("build_time", 0)
                            logger.info(f"[PROPERTY EDIT] Background rebuild completed in {build_time}s")
                        else:
                            logger.warning(f"[PROPERTY EDIT] Background rebuild failed: {update_result.get('error')}")
                    else:
                        logger.warning(f"[PROPERTY EDIT] No files to update in preview")
                else:
                    logger.warning(f"[PROPERTY EDIT] Preview expired, will recreate on next view")
            else:
                logger.info(f"[PROPERTY EDIT] No preview yet, will create on first view")
                    
        except Exception as preview_error:
            logger.error(f"[PROPERTY EDIT] Background rebuild failed: {str(preview_error)}", exc_info=True)
        
        # Log the successful action
        await ActionLogger(supabase).log_action(
            user_id=user_id,
            action="property_edit_applied",
            details={
                "project_id": project_id,
                "component_file": request.component_file,
                "properties_changed": [p.property for p in request.properties],
                "element_selector": request.element_selector,
                "batch_mode": request.batch,
                "success": True
            }
        )
        
        logger.info(f"[PROPERTY EDIT] Property edit completed successfully")

        # Stamp last edit time for the unpublished-changes indicator
        try:
            supabase.table("projects").update(
                {"last_edited_at": datetime.utcnow().isoformat()}
            ).eq("id", project_id).execute()
        except Exception as e:
            logger.warning(f"[PROPERTY EDIT] Failed to stamp last_edited_at: {e}")

        # Prepare prop_edit_info if this was a prop edit
        # prop_edit_info_response is already set above if it was a prop edit

        return PropertyEditResponse(
            success=True,
            message=f"Successfully updated {len(request.properties)} properties",
            updated_file=request.component_file,
            changes_applied=request.properties,
            preview_url=preview_url,
            new_code=modified_code,
            old_code=original_code,
            prop_edit_info=prop_edit_info_response
        )
        
    except HTTPException as e:
        logger.error(f"[PROPERTY EDIT] HTTPException: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(f"[PROPERTY EDIT] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to edit properties"
        )


@router.post("/edit/project/{project_id}/properties", response_model=PropertyEditResponse)
@log_action(action_type='UPDATE', target_resource_type='project_properties_edit')
async def edit_project_properties(
    project_id: str,
    request: PropertyEditRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Edit React component properties directly (click-to-edit system).
    
    This endpoint uses a queue system to ensure all property changes for a project
    are processed sequentially, preventing race conditions and ensuring data integrity.
    Multiple simultaneous requests for the same project will be queued and processed
    one after the other in the order they were received.
    
    This endpoint allows direct property editing without natural language processing.
    It modifies component files by updating Tailwind classes, inline styles, or text content.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    # Get the queue service
    queue_service = get_queue_service()
    
    logger.info(f"[PROPERTY EDIT] Queueing property edit for project {project_id}")
    logger.info(f"[PROPERTY EDIT] Request for {request.component_file} with {len(request.properties)} changes")
    
    try:
        # Enqueue the task and wait for result
        # The queue ensures sequential processing per project
        # Note: project_id is automatically added to handler kwargs by the queue service
        result = await queue_service.enqueue_task(
            project_id=project_id,  # For queue service to identify which queue
            handler=_handle_property_edit,
            timeout=120.0,  # 2 minutes timeout
            # Handler arguments (project_id is automatically included by queue service)
            request=request,
            user_id=user_id,
            supabase=supabase
        )
        
        # Get queue stats for logging
        stats = queue_service.get_queue_stats(project_id)
        logger.info(
            f"[PROPERTY EDIT] Task completed. Queue stats - "
            f"Total: {stats['total_tasks']}, "
            f"Completed: {stats['completed_tasks']}, "
            f"Failed: {stats['failed_tasks']}, "
            f"Queue Size: {stats['queue_size']}"
        )
        
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"[PROPERTY EDIT] Request timed out for project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Property edit request timed out. Please try again."
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"[PROPERTY EDIT] Queue processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process property edit request"
        )


@router.get("/edit/queue-stats/{project_id}")
async def get_queue_stats(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get queue statistics for a specific project.
    
    Returns information about the property edit queue including:
    - Total tasks processed
    - Completed tasks
    - Failed tasks
    - Current queue size
    - Worker status
    
    This is useful for monitoring and debugging purposes.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    
    # Verify project ownership
    try:
        project_response = supabase.table("projects").select("user_id").eq("id", project_id).single().execute()
        
        if not project_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if project_response.data.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this project's queue stats"
            )
        
        # Get queue stats
        queue_service = get_queue_service()
        stats = queue_service.get_queue_stats(project_id)
        
        return {
            "project_id": project_id,
            "queue_stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[QUEUE] Error fetching queue stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch queue statistics"
        )


@router.get("/edit/queue-stats")
async def get_all_queue_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get queue statistics for all projects (admin/monitoring endpoint).
    
    Returns statistics for all active project queues.
    Useful for system monitoring and debugging.
    """
    try:
        queue_service = get_queue_service()
        all_stats = queue_service.get_all_stats()
        
        return {
            "total_projects": len(all_stats),
            "projects": all_stats
        }
        
    except Exception as e:
        logger.error(f"[QUEUE] Error fetching all queue stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch queue statistics"
        )


@router.get("/projects/{project_id}/chat-history", response_model=ChatHistoryResponse)
async def get_chat_history(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get chat history for a project.

    Returns all chat messages (generation, edits, questions) for the project.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()

    logger.info(f"[CHAT HISTORY] Fetching chat history for project {project_id}")

    try:
        # Verify project ownership
        project_response = supabase.table("projects")\
            .select("id, user_id")\
            .eq("id", project_id)\
            .execute()

        if not project_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        project = project_response.data[0]
        if project["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Fetch chat messages
        chat_response = supabase.table("project_chat_messages")\
            .select("*")\
            .eq("project_id", project_id)\
            .order("created_at", desc=False)\
            .execute()

        messages = []
        for msg in chat_response.data:
            messages.append(ChatMessageResponse(
                id=msg["id"],
                project_id=msg["project_id"],
                user_id=msg["user_id"],
                message_type=msg["message_type"],
                user_prompt=msg["user_prompt"],
                ai_response=msg["ai_response"],
                metadata=msg.get("metadata", {}),
                created_at=msg["created_at"],
                updated_at=msg["updated_at"]
            ))

        logger.info(f"[CHAT HISTORY] Retrieved {len(messages)} messages for project {project_id}")

        return ChatHistoryResponse(
            messages=messages,
            total_count=len(messages)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CHAT HISTORY] Error fetching chat history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chat history"
        )


@router.post("/projects/{project_id}/chat-messages", response_model=ChatMessageResponse)
async def save_chat_message(
    project_id: str,
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Save a chat message to the project history.

    Used for saving general questions/answers that don't involve edits.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()

    logger.info(f"[SAVE CHAT] Saving chat message for project {project_id}, type: {request.message_type}")

    try:
        # Verify project ownership
        project_response = supabase.table("projects")\
            .select("id, user_id")\
            .eq("id", project_id)\
            .execute()

        if not project_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        project = project_response.data[0]
        if project["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Insert chat message
        message_id = str(uuid.uuid4())
        insert_response = supabase.table("project_chat_messages").insert({
            "id": message_id,
            "project_id": project_id,
            "user_id": user_id,
            "message_type": request.message_type,
            "user_prompt": request.user_prompt,
            "ai_response": request.ai_response,
            "metadata": request.metadata
        }).execute()

        if not insert_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save chat message"
            )

        saved_message = insert_response.data[0]
        logger.info(f"[SAVE CHAT] Chat message saved with ID: {message_id}")

        return ChatMessageResponse(
            id=saved_message["id"],
            project_id=saved_message["project_id"],
            user_id=saved_message["user_id"],
            message_type=saved_message["message_type"],
            user_prompt=saved_message["user_prompt"],
            ai_response=saved_message["ai_response"],
            metadata=saved_message.get("metadata", {}),
            created_at=saved_message["created_at"],
            updated_at=saved_message["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SAVE CHAT] Error saving chat message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save chat message"
        )

