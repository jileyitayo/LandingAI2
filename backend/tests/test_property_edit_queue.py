"""
Tests for Property Edit Queue Service

These tests verify that the queue system correctly processes property edits
sequentially and prevents race conditions.
"""

import pytest
import asyncio
from app.services.property_edit_queue_service import (
    PropertyEditQueueService,
    PropertyEditTask,
    get_queue_service
)


@pytest.mark.asyncio
async def test_queue_service_initialization():
    """Test that queue service initializes correctly"""
    service = PropertyEditQueueService()
    assert service is not None
    assert len(service._queues) == 0
    assert len(service._workers) == 0


@pytest.mark.asyncio
async def test_sequential_processing():
    """Test that tasks are processed sequentially in order"""
    service = PropertyEditQueueService()
    results = []
    
    async def handler(value: int) -> int:
        """Handler that adds value to results and sleeps briefly"""
        results.append(value)
        await asyncio.sleep(0.01)  # Small delay to simulate work
        return value
    
    # Enqueue multiple tasks for the same project
    tasks = [
        service.enqueue_task("project-1", handler, value=1),
        service.enqueue_task("project-1", handler, value=2),
        service.enqueue_task("project-1", handler, value=3),
    ]
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)
    
    # Verify sequential processing - results should be in order
    assert results == [1, 2, 3]
    
    # Verify stats
    stats = service.get_queue_stats("project-1")
    assert stats["total_tasks"] == 3
    assert stats["completed_tasks"] == 3
    assert stats["failed_tasks"] == 0
    assert stats["queue_size"] == 0
    
    await service.shutdown()


@pytest.mark.asyncio
async def test_parallel_projects():
    """Test that different projects can be processed in parallel"""
    service = PropertyEditQueueService()
    results = {"project-1": [], "project-2": []}
    
    async def handler(project_id: str, value: int) -> int:
        """Handler that tracks results per project"""
        results[project_id].append(value)
        await asyncio.sleep(0.01)
        return value
    
    # Enqueue tasks for different projects simultaneously
    tasks = [
        service.enqueue_task("project-1", handler, project_id="project-1", value=1),
        service.enqueue_task("project-2", handler, project_id="project-2", value=10),
        service.enqueue_task("project-1", handler, project_id="project-1", value=2),
        service.enqueue_task("project-2", handler, project_id="project-2", value=20),
    ]
    
    # Wait for all tasks
    await asyncio.gather(*tasks)
    
    # Verify each project's tasks were sequential
    assert results["project-1"] == [1, 2]
    assert results["project-2"] == [10, 20]
    
    # Verify stats for both projects
    stats1 = service.get_queue_stats("project-1")
    assert stats1["completed_tasks"] == 2
    
    stats2 = service.get_queue_stats("project-2")
    assert stats2["completed_tasks"] == 2
    
    await service.shutdown()


@pytest.mark.asyncio
async def test_error_handling():
    """Test that errors in one task don't affect subsequent tasks"""
    service = PropertyEditQueueService()
    results = []
    
    async def handler(value: int, should_fail: bool = False) -> int:
        """Handler that can be made to fail"""
        if should_fail:
            raise ValueError(f"Task {value} failed intentionally")
        results.append(value)
        return value
    
    # Enqueue tasks with one that will fail
    task1 = service.enqueue_task("project-1", handler, value=1, should_fail=False)
    task2 = service.enqueue_task("project-1", handler, value=2, should_fail=True)
    task3 = service.enqueue_task("project-1", handler, value=3, should_fail=False)
    
    # Task 1 should succeed
    result1 = await task1
    assert result1 == 1
    
    # Task 2 should fail
    with pytest.raises(ValueError):
        await task2
    
    # Task 3 should still succeed despite task 2 failing
    result3 = await task3
    assert result3 == 3
    
    # Verify results - task 2 never added to results
    assert results == [1, 3]
    
    # Verify stats show the failure
    stats = service.get_queue_stats("project-1")
    assert stats["total_tasks"] == 3
    assert stats["completed_tasks"] == 2
    assert stats["failed_tasks"] == 1
    
    await service.shutdown()


@pytest.mark.asyncio
async def test_timeout():
    """Test that tasks can timeout"""
    service = PropertyEditQueueService()
    
    async def slow_handler() -> str:
        """Handler that takes too long"""
        await asyncio.sleep(5)  # 5 seconds - longer than timeout
        return "done"
    
    # Enqueue with short timeout
    with pytest.raises(asyncio.TimeoutError):
        await service.enqueue_task(
            "project-1",
            slow_handler,
            timeout=0.5  # 500ms timeout
        )
    
    await service.shutdown()


@pytest.mark.asyncio
async def test_queue_stats():
    """Test that queue statistics are tracked correctly"""
    service = PropertyEditQueueService()
    
    async def handler(value: int) -> int:
        await asyncio.sleep(0.01)
        return value
    
    # Initially no stats
    initial_stats = service.get_queue_stats("project-1")
    assert initial_stats["total_tasks"] == 0
    assert initial_stats["completed_tasks"] == 0
    
    # Process some tasks
    await asyncio.gather(
        service.enqueue_task("project-1", handler, value=1),
        service.enqueue_task("project-1", handler, value=2),
    )
    
    # Check stats after completion
    stats = service.get_queue_stats("project-1")
    assert stats["total_tasks"] == 2
    assert stats["completed_tasks"] == 2
    assert stats["queue_size"] == 0
    assert stats["worker_running"] is True
    
    # Get all stats
    all_stats = service.get_all_stats()
    assert "project-1" in all_stats
    assert all_stats["project-1"]["completed_tasks"] == 2
    
    await service.shutdown()


@pytest.mark.asyncio
async def test_singleton_service():
    """Test that get_queue_service returns singleton instance"""
    service1 = get_queue_service()
    service2 = get_queue_service()
    
    # Should be the same instance
    assert service1 is service2
    
    # Stats should be shared
    async def handler(value: int) -> int:
        return value
    
    await service1.enqueue_task("project-1", handler, value=1)
    
    stats1 = service1.get_queue_stats("project-1")
    stats2 = service2.get_queue_stats("project-1")
    
    assert stats1["total_tasks"] == stats2["total_tasks"]
    
    await service1.shutdown()


@pytest.mark.asyncio
async def test_concurrent_enqueue():
    """Test that concurrent enqueues are handled correctly"""
    service = PropertyEditQueueService()
    results = []
    
    async def handler(value: int) -> int:
        """Handler that simulates some work"""
        results.append(f"start-{value}")
        await asyncio.sleep(0.01)
        results.append(f"end-{value}")
        return value
    
    # Fire off multiple concurrent enqueues
    tasks = [
        service.enqueue_task("project-1", handler, value=i)
        for i in range(5)
    ]
    
    # Wait for all to complete
    values = await asyncio.gather(*tasks)
    
    # All should complete successfully
    assert values == [0, 1, 2, 3, 4]
    
    # Check that each task completed fully before next started
    # Each task should have consecutive start-X, end-X pairs
    for i in range(5):
        start_idx = results.index(f"start-{i}")
        end_idx = results.index(f"end-{i}")
        
        # No other task should start between this task's start and end
        between = results[start_idx + 1:end_idx]
        assert between == [], f"Task {i} was interrupted: {between}"
    
    await service.shutdown()


@pytest.mark.asyncio
async def test_task_return_values():
    """Test that task return values are correctly propagated"""
    service = PropertyEditQueueService()
    
    async def handler(a: int, b: int) -> dict:
        """Handler that returns complex data"""
        return {
            "sum": a + b,
            "product": a * b,
            "message": f"{a} and {b}"
        }
    
    result = await service.enqueue_task(
        "project-1",
        handler,
        a=5,
        b=10
    )
    
    assert result["sum"] == 15
    assert result["product"] == 50
    assert result["message"] == "5 and 10"
    
    await service.shutdown()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])


