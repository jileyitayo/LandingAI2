"""
Editing Router
Endpoints for AI component edits (sync + streaming), property edits, and
edit-queue statistics. The heavy lifting lives in app.services.edit_pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging

from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import log_action
from app.utils.auth import get_current_user
from app.services.property_edit_queue_service import get_queue_service
from app.services.edit_pipeline import _run_edit_pipeline, _handle_property_edit
from app.models.generation import (
    ComponentEditRequest,
    ComponentEditResponse,
    PropertyEditRequest,
    PropertyEditResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generation"])


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
