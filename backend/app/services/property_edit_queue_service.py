"""
Property Edit Queue Service

This service manages a queue system for property edit operations to ensure
that changes to a project are processed sequentially, preventing race conditions
and ensuring data integrity.

Each project gets its own queue, and all property edit requests for that project
are processed one after another in the order they were received.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class PropertyEditTask:
    """Represents a property edit task in the queue"""
    
    def __init__(
        self,
        task_id: str,
        project_id: str,
        handler: Callable,
        **kwargs
    ):
        self.task_id = task_id
        self.project_id = project_id
        self.handler = handler  # The async function to execute
        self.kwargs = kwargs  # Arguments to pass to the handler
        self.created_at = datetime.utcnow()
        self.result_future = asyncio.Future()  # To store the result
        
    async def execute(self) -> Dict[str, Any]:
        """Execute the task and return the result"""
        try:
            logger.info(f"[QUEUE] Executing task {self.task_id} for project {self.project_id}")
            result = await self.handler(**self.kwargs)
            self.result_future.set_result({"success": True, "data": result})
            return result
        except Exception as e:
            # HTTPException (4xx errors) are expected client errors, log as warning
            if hasattr(e, 'status_code') and 400 <= getattr(e, 'status_code', 0) < 500:
                logger.warning(
                    f"[QUEUE] Task {self.task_id} failed with client error ({getattr(e, 'status_code', 'unknown')}): {str(e)}"
                )
            else:
                # Server errors (5xx) or unexpected errors should be logged as errors
                logger.error(f"[QUEUE] Task {self.task_id} failed: {str(e)}", exc_info=True)
            
            self.result_future.set_exception(e)
            raise


class PropertyEditQueueService:
    """
    Service for managing property edit queues per project.
    
    This ensures that all property edits for a given project are processed
    sequentially, preventing race conditions and conflicts.
    """
    
    def __init__(self):
        # Dictionary to store queues for each project
        self._queues: Dict[str, asyncio.Queue] = {}
        
        # Dictionary to store worker tasks for each project queue
        self._workers: Dict[str, asyncio.Task] = {}
        
        # Dictionary to track queue statistics
        self._stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "queue_size": 0
        })
        
        # Lock for thread-safe queue creation
        self._lock = asyncio.Lock()
        
        logger.info("[QUEUE] PropertyEditQueueService initialized")
    
    async def _get_or_create_queue(self, project_id: str) -> asyncio.Queue:
        """
        Get existing queue for a project or create a new one.
        Thread-safe queue creation.
        """
        if project_id not in self._queues:
            async with self._lock:
                # Double-check after acquiring lock
                if project_id not in self._queues:
                    logger.info(f"[QUEUE] Creating new queue for project {project_id}")
                    self._queues[project_id] = asyncio.Queue()
                    # Start worker for this queue
                    self._workers[project_id] = asyncio.create_task(
                        self._queue_worker(project_id)
                    )
        
        return self._queues[project_id]
    
    async def _queue_worker(self, project_id: str):
        """
        Worker task that processes items from a project's queue.
        Runs continuously until the queue is empty and stays idle.
        """
        logger.info(f"[QUEUE] Worker started for project {project_id}")
        queue = self._queues[project_id]
        
        while True:
            try:
                # Wait for a task from the queue
                task: PropertyEditTask = await queue.get()
                
                try:
                    # Update queue size stat
                    self._stats[project_id]["queue_size"] = queue.qsize()
                    
                    # Execute the task
                    logger.info(
                        f"[QUEUE] Processing task {task.task_id} for project {project_id} "
                        f"(queue size: {queue.qsize()})"
                    )
                    
                    await task.execute()
                    
                    # Update stats
                    self._stats[project_id]["completed_tasks"] += 1
                    logger.info(f"[QUEUE] Task {task.task_id} completed successfully")
                    
                except Exception as e:
                    # Task execution failed, but worker continues
                    self._stats[project_id]["failed_tasks"] += 1
                    
                    # HTTPException (4xx errors) are expected client errors, not server errors
                    # Log them as warnings instead of errors
                    if hasattr(e, 'status_code') and 400 <= getattr(e, 'status_code', 0) < 500:
                        logger.warning(
                            f"[QUEUE] Task {task.task_id} failed with client error ({getattr(e, 'status_code', 'unknown')}): {str(e)}"
                        )
                    else:
                        # Server errors (5xx) or unexpected errors should be logged as errors
                        logger.error(
                            f"[QUEUE] Task {task.task_id} failed: {str(e)}",
                            exc_info=True
                        )
                    
                finally:
                    # Mark task as done in the queue
                    queue.task_done()
                    
            except asyncio.CancelledError:
                logger.info(f"[QUEUE] Worker for project {project_id} cancelled")
                break
            except Exception as e:
                logger.error(
                    f"[QUEUE] Worker error for project {project_id}: {str(e)}",
                    exc_info=True
                )
                # Wait a bit before continuing to avoid rapid error loops
                await asyncio.sleep(1)
    
    async def enqueue_task(
        self,
        project_id: str,
        handler: Callable,
        timeout: Optional[float] = 120.0,  # 2 minutes default timeout
        **kwargs
    ) -> Any:
        """
        Add a property edit task to the queue and wait for its result.
        
        Args:
            project_id: The ID of the project being edited
            handler: The async function to execute
            timeout: Maximum time to wait for the task to complete (seconds)
            **kwargs: Arguments to pass to the handler function
        
        Returns:
            The result from the handler function
        
        Raises:
            asyncio.TimeoutError: If the task takes longer than timeout
            Exception: Any exception raised by the handler
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())[:8]
        
        # Get or create queue for this project
        queue = await self._get_or_create_queue(project_id)
        
        # Create task - automatically include project_id in kwargs for handler
        # (unless it's already provided, in which case use the provided value)
        # Note: project_id is removed from kwargs before passing to PropertyEditTask
        # since PropertyEditTask takes project_id as a direct parameter
        handler_kwargs = kwargs.copy()
        if 'project_id' not in handler_kwargs:
            handler_kwargs['project_id'] = project_id
        
        # Remove project_id from handler_kwargs before creating PropertyEditTask
        # since PropertyEditTask.__init__ takes project_id as a direct parameter
        handler_kwargs_for_task = {k: v for k, v in handler_kwargs.items() if k != 'project_id'}
        
        task = PropertyEditTask(
            task_id=task_id,
            project_id=project_id,  # Direct parameter for PropertyEditTask
            handler=handler,
            **handler_kwargs_for_task  # Handler kwargs (includes project_id for the handler)
        )
        
        # Ensure project_id is in the handler kwargs (it was removed above for PropertyEditTask)
        # but we need it for the handler function
        task.kwargs['project_id'] = project_id
        
        # Update stats
        self._stats[project_id]["total_tasks"] += 1
        
        # Add task to queue
        logger.info(
            f"[QUEUE] Enqueuing task {task_id} for project {project_id} "
            f"(current queue size: {queue.qsize()})"
        )
        await queue.put(task)
        
        # Wait for task to complete with timeout
        try:
            if timeout:
                result = await asyncio.wait_for(
                    task.result_future,
                    timeout=timeout
                )
            else:
                result = await task.result_future
            
            # Extract the actual data from the result wrapper
            return result.get("data")
            
        except asyncio.TimeoutError:
            logger.error(
                f"[QUEUE] Task {task_id} timed out after {timeout}s"
            )
            raise
    
    def get_queue_stats(self, project_id: str) -> Dict[str, Any]:
        """Get statistics for a project's queue"""
        stats = self._stats[project_id].copy()
        
        if project_id in self._queues:
            stats["queue_size"] = self._queues[project_id].qsize()
            stats["worker_running"] = project_id in self._workers
        else:
            stats["queue_size"] = 0
            stats["worker_running"] = False
            
        return stats
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all project queues"""
        return {
            project_id: self.get_queue_stats(project_id)
            for project_id in self._stats.keys()
        }
    
    async def cleanup_idle_queues(self, max_idle_time: int = 3600):
        """
        Clean up queues that have been idle for too long.
        
        Args:
            max_idle_time: Maximum idle time in seconds (default: 1 hour)
        """
        current_time = datetime.utcnow()
        projects_to_remove = []
        
        for project_id, queue in self._queues.items():
            # If queue is empty and stats show no recent activity
            if queue.qsize() == 0:
                stats = self._stats[project_id]
                # Check if queue has been idle (you might want to add last_activity timestamp)
                # For now, we'll just check if it's empty
                projects_to_remove.append(project_id)
        
        # Cancel workers and remove queues
        for project_id in projects_to_remove:
            logger.info(f"[QUEUE] Cleaning up idle queue for project {project_id}")
            
            if project_id in self._workers:
                self._workers[project_id].cancel()
                del self._workers[project_id]
            
            if project_id in self._queues:
                del self._queues[project_id]
    
    async def shutdown(self):
        """Gracefully shutdown all workers and queues"""
        logger.info("[QUEUE] Shutting down PropertyEditQueueService")
        
        # Cancel all workers
        for project_id, worker in self._workers.items():
            logger.info(f"[QUEUE] Cancelling worker for project {project_id}")
            worker.cancel()
        
        # Wait for all workers to finish
        if self._workers:
            await asyncio.gather(*self._workers.values(), return_exceptions=True)
        
        # Clear all queues
        self._queues.clear()
        self._workers.clear()
        
        logger.info("[QUEUE] PropertyEditQueueService shutdown complete")


# Singleton instance
_queue_service: Optional[PropertyEditQueueService] = None


def get_queue_service() -> PropertyEditQueueService:
    """Get or create the singleton queue service instance"""
    global _queue_service
    if _queue_service is None:
        _queue_service = PropertyEditQueueService()
    return _queue_service

