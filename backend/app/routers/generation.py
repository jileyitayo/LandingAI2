"""
Generation Router
API endpoints for AI website content generation and rendering.
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any
from datetime import datetime
import uuid
import json
import logging
import asyncio
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import ActionLogger, log_action
from app.utils.auth import get_current_user
from app.services.project_file_manager import project_file_manager
from app.services.vite_preview_service import vite_preview_service
from app.services.property_edit_queue_service import get_queue_service
from app.services.intent_checker import check_generation_intent
from app.services.site_ingestion import extract_site_design, WEAK_CONFIDENCE
from app.services.quota_service import check_user_rate_limit, log_ai_call, check_project_limit
from app.services.generation_orchestration import (
    create_project,
    generate_react_website_background,
    process_react_generation,
    _get_status_message,
)
from app.services.edit_pipeline import _run_edit_pipeline, _handle_property_edit
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
    PropertyEditRequest,
    PropertyEditResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generation"])



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

        # Step 2.5: Pre-flight intent check + URL ingestion (before project
        # creation and before log_ai_call, so a clarification return creates
        # no orphan project and burns no quota — same precedent as the edit
        # pipeline's confirm-first responses). Fails open: any error here
        # degrades to normal generation.
        design_extraction = None
        design_fidelity = "none"
        preflight_usage = None
        polished_prompt = None
        if settings.intent_preflight_enabled:
            try:
                async def _preflight():
                    intent, usage = await asyncio.to_thread(
                        check_generation_intent,
                        request.prompt,
                        bool(request.attachments),
                        settings.url_ingestion_enabled,
                        request.clarification_response,
                    )
                    extraction = None
                    if intent.url_refs and settings.url_ingestion_enabled:
                        extraction = await extract_site_design(intent.url_refs[0])
                    return intent, extraction, usage

                intent, design_extraction, preflight_usage = await asyncio.wait_for(
                    _preflight(), timeout=20.0
                )
                design_fidelity = intent.fidelity
                polished_prompt = intent.polished_prompt
                logger.info(
                    f"[PREFLIGHT] clarify={intent.needs_clarification} urls={len(intent.url_refs)} "
                    f"fidelity={intent.fidelity} polished={bool(polished_prompt)} "
                    f"extraction_ok={getattr(design_extraction, 'ok', None)} "
                    f"confidence={getattr(design_extraction, 'confidence', None)}"
                )

                if not request.skip_clarification:
                    weak_extraction = design_extraction is not None and (
                        not design_extraction.ok or design_extraction.confidence < WEAK_CONFIDENCE
                    )
                    clarification = None
                    if weak_extraction:
                        url = intent.url_refs[0]
                        clarification = {
                            "question": (
                                f"I couldn't read enough of {url} to copy its design — could you "
                                "attach a screenshot of the site, or describe its colors, fonts "
                                "and sections?"
                            ),
                            "wants_attachment": True,
                            "reason": design_extraction.failure_reason or "weak_extraction",
                            "url": url,
                        }
                    elif intent.needs_clarification and intent.question:
                        # Guardrail: a successful site fetch already supplies the
                        # design assets (logo, colors, fonts) — don't ask the user
                        # for an attachment the reference site just provided.
                        asset_covered_by_site = (
                            intent.wants_attachment
                            and design_extraction is not None
                            and design_extraction.ok
                            and design_extraction.confidence >= WEAK_CONFIDENCE
                        )
                        if asset_covered_by_site:
                            logger.info("[PREFLIGHT] guardrail: asset clarification covered by fetched site, proceeding")
                        else:
                            clarification = {
                                "question": intent.question,
                                "wants_attachment": intent.wants_attachment,
                                "reason": "intent",
                                "url": intent.url_refs[0] if intent.url_refs else None,
                            }
                    if clarification:
                        # Deliberately no create_project and no log_ai_call —
                        # a clarification round is free.
                        logger.info(f"[PREFLIGHT] returning clarification: {clarification['reason']}")
                        return JSONResponse(
                            status_code=status.HTTP_200_OK,
                            content=GenerateWebsiteResponse(
                                project_id=None,
                                status="needs_clarification",
                                message=clarification["question"],
                                clarification=clarification,
                            ).dict(),
                        )
                # Weak/failed extractions never feed the pipeline.
                if design_extraction is not None and (
                    not design_extraction.ok or design_extraction.confidence < WEAK_CONFIDENCE
                ):
                    design_extraction = None
            except Exception as e:
                logger.warning(f"[PREFLIGHT] failed, proceeding with normal generation: {e}")
                design_extraction = None

        # The clarification answer rides with the prompt from here on (project
        # row, business analysis, page prompts).
        effective_prompt = request.prompt
        if request.clarification_response:
            effective_prompt = f"{request.prompt}\n\nUser clarification: {request.clarification_response.strip()}"

        # Generation consumes the polished spec when the preflight produced one;
        # the raw effective_prompt stays the user-facing project record.
        generation_prompt = polished_prompt or effective_prompt

        # Step 3: Create project
        logger.info("Creating project...")
        project_id = await create_project(
            user_id=user_id,
            project_name=request.project_name or f"React Website - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            prompt=effective_prompt,
            template_id=None,
            supabase_client=supabase,
            polished_prompt=polished_prompt
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
                prompt=generation_prompt,
                user_id=user_id,
                attachments=request.attachments,
                design_extraction=design_extraction,
                design_fidelity=design_fidelity,
                preflight_usage=preflight_usage,
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

