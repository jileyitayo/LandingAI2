"""
Generation Orchestration Service
Project row lifecycle (create/status/progress) and the background React
generation task driven by the /generate_website endpoint.
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import ActionLogger, log_action
from app.services.react_website_generator import react_website_generator
from app.services.project_file_manager import project_file_manager
from app.services.site_ingestion import to_prompt_block, DesignExtraction
from app.config import settings
from app.models.generation import GenerateReactWebsiteResponse

logger = logging.getLogger(__name__)


@log_action(action_type='CREATE', target_resource_type='project_creation')
async def create_project(
    user_id: str,
    project_name: str,
    prompt: str,
    template_id: str,
    supabase_client,
    polished_prompt: Optional[str] = None
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
            "polished_prompt": polished_prompt,
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

def _get_status_message(status: str) -> str:
    """Get user-friendly status message"""
    messages = {
        "idle": "Generation not started",
        "generating": "Generating your website... This may take 4-6 minutes",
        "completed": "Website generated successfully",
        "failed": "Generation failed. Please try again"
    }
    return messages.get(status, "Unknown status")



async def process_react_generation(
    project_id: str,
    prompt: str,
    user_id: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    design_extraction: Optional[DesignExtraction] = None,
    design_fidelity: str = "none",
    preflight_usage: Optional[Dict[str, Any]] = None,
):
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

    # Reference-site design data from the pre-flight, injected verbatim like
    # media_context so exact hexes/font names/logo URLs survive summarization.
    design_context = None
    if design_extraction is not None:
        try:
            design_context = to_prompt_block(
                design_extraction,
                design_fidelity if design_fidelity in ("replica", "inspired") else "inspired",
            )
            if design_context:
                logger.info(f"[BG] Design context built for project {project_id} (fidelity={design_fidelity})")
        except Exception as e:
            logger.warning(f"[BG] Design context build failed, generating without it: {e}")

    # Import CostTracker
    from app.services.cost_calculator import CostTracker

    # Initialize cost tracker
    cost_tracker = CostTracker(
        generation_type="website",
        endpoint="/generate_website"
    )
    if preflight_usage:
        try:
            cost_tracker.track_call(
                service_name="preflight_intent_check",
                model_name=settings.analysis_model,
                usage=preflight_usage,
            )
        except Exception as e:
            logger.warning(f"[BG] Failed to track preflight usage: {e}")

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
                    media_context=media_context,
                    design_context=design_context,
                    design_extraction=design_extraction,
                    design_fidelity=design_fidelity,
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

