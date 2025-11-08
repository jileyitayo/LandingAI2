# Property Edit Queue System

## Overview

The Property Edit Queue System ensures that all property changes to a project are processed sequentially, preventing race conditions and ensuring data integrity. This is particularly important when multiple property edits are requested simultaneously for the same project.

## Architecture

### Components

1. **PropertyEditQueueService** (`backend/app/services/property_edit_queue_service.py`)
   - Manages queues for each project
   - Ensures sequential processing of property edits
   - Provides statistics and monitoring capabilities

2. **Queue Worker**
   - Each project gets its own dedicated worker task
   - Processes property edit tasks sequentially from the project's queue
   - Automatically created when the first task is enqueued for a project

3. **API Endpoint** (`/edit/project/{project_id}/properties`)
   - Entry point for property edit requests
   - Automatically enqueues tasks and waits for completion
   - Returns results to the client

## How It Works

### Request Flow

```
Client Request
     ↓
API Endpoint
     ↓
Queue Service (enqueue_task)
     ↓
Project-Specific Queue
     ↓
Worker Task (sequential processing)
     ↓
Property Edit Handler
     ↓
Return Result to Client
```

### Sequential Processing

1. **Request arrives**: Client sends a property edit request
2. **Task creation**: The request is wrapped in a `PropertyEditTask` object
3. **Enqueuing**: Task is added to the project's queue
4. **Worker processing**: The dedicated worker picks up the task
5. **Execution**: Property changes are applied
6. **Result return**: Result is sent back to the waiting client
7. **Next task**: Worker processes the next task in queue

### Queue per Project

- Each project has its own independent queue
- Requests for different projects are processed in parallel
- Requests for the same project are processed sequentially
- This prevents conflicts while maintaining throughput

## Key Features

### 1. Race Condition Prevention

Multiple simultaneous edits to the same project are automatically queued and processed in order:

```python
# Multiple requests for the same project
Request 1: Change color to blue   → Queued at position 1
Request 2: Change size to large    → Queued at position 2
Request 3: Change text to "Hello"  → Queued at position 3

# Processed sequentially:
1. Process Request 1 → Apply color change
2. Process Request 2 → Apply size change  
3. Process Request 3 → Apply text change
```

### 2. Timeout Protection

Each request has a configurable timeout (default: 2 minutes):
- Prevents hanging requests
- Returns proper error response if timeout occurs
- Queue worker continues processing other tasks

### 3. Error Handling

- Individual task failures don't stop the queue
- Each task has its own error handling
- Failed tasks are logged and tracked in statistics
- Queue worker continues processing subsequent tasks

### 4. Statistics & Monitoring

Track queue performance per project:
- Total tasks processed
- Completed tasks
- Failed tasks
- Current queue size
- Worker status

## API Endpoints

### 1. Edit Properties (with Queue)

**POST** `/edit/project/{project_id}/properties`

Submit a property edit request. The request will be automatically queued and processed sequentially.

**Request Body:**
```json
{
  "element_selector": ".hero-title",
  "component_file": "src/components/Hero.tsx",
  "properties": [
    {
      "property": "color",
      "value": "blue",
      "oldValue": "red"
    }
  ],
  "batch": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully updated 1 properties",
  "updated_file": "src/components/Hero.tsx",
  "changes_applied": [...],
  "preview_url": null,
  "new_code": "...",
  "old_code": "..."
}
```

**Timeout Response (504):**
```json
{
  "detail": "Property edit request timed out. Please try again."
}
```

### 2. Get Queue Statistics (Single Project)

**GET** `/edit/queue-stats/{project_id}`

Get queue statistics for a specific project.

**Response:**
```json
{
  "project_id": "abc-123",
  "queue_stats": {
    "total_tasks": 45,
    "completed_tasks": 42,
    "failed_tasks": 2,
    "queue_size": 1,
    "worker_running": true
  }
}
```

### 3. Get All Queue Statistics

**GET** `/edit/queue-stats`

Get queue statistics for all projects (monitoring endpoint).

**Response:**
```json
{
  "total_projects": 3,
  "projects": {
    "project-1": {
      "total_tasks": 45,
      "completed_tasks": 42,
      "failed_tasks": 2,
      "queue_size": 1,
      "worker_running": true
    },
    "project-2": {
      "total_tasks": 12,
      "completed_tasks": 12,
      "failed_tasks": 0,
      "queue_size": 0,
      "worker_running": true
    }
  }
}
```

## Configuration

### Timeout Settings

The default timeout for property edit requests is 120 seconds (2 minutes). This can be adjusted in the endpoint:

```python
result = await queue_service.enqueue_task(
    project_id=project_id,
    handler=_handle_property_edit,
    timeout=120.0,  # Adjust timeout here
    ...
)
```

### Queue Cleanup

Idle queues (empty with no recent activity) can be cleaned up to free resources:

```python
# In your maintenance/cleanup task
await queue_service.cleanup_idle_queues(max_idle_time=3600)  # 1 hour
```

## Benefits

### 1. Data Integrity
- No conflicting simultaneous edits
- Changes applied in predictable order
- File state remains consistent

### 2. User Experience
- Optimistic updates in frontend remain smooth
- Backend ensures changes are actually applied correctly
- No lost edits due to race conditions

### 3. Reliability
- Failed edits don't affect subsequent edits
- Timeout protection prevents hanging requests
- Comprehensive error handling and logging

### 4. Scalability
- Each project has independent queue
- Projects process changes in parallel
- Only sequential within same project

### 5. Observability
- Detailed logging at each step
- Queue statistics for monitoring
- Easy debugging with task IDs

## Implementation Details

### PropertyEditTask

Each queued task contains:
- **task_id**: Unique identifier for logging/tracking
- **project_id**: Which project this task belongs to
- **handler**: The async function to execute (property edit logic)
- **kwargs**: Arguments to pass to the handler
- **result_future**: asyncio.Future to store result and communicate back to caller

### Queue Worker Lifecycle

1. **Creation**: Worker created when first task enqueued for a project
2. **Processing**: Continuously processes tasks from queue
3. **Idle**: Waits for new tasks when queue is empty
4. **Cleanup**: Can be stopped for idle queues (optional)

### Error Recovery

- Task execution errors are caught and logged
- Error is set on the task's result_future
- Worker continues processing next task
- Client receives proper error response

## Logging

All queue operations are logged with the `[QUEUE]` prefix:

```
[QUEUE] PropertyEditQueueService initialized
[QUEUE] Creating new queue for project abc-123
[QUEUE] Worker started for project abc-123
[QUEUE] Enqueuing task f3a2b1c8 for project abc-123 (current queue size: 0)
[QUEUE] Executing task f3a2b1c8 for project abc-123
[QUEUE] Task f3a2b1c8 completed successfully
```

## Testing

### Unit Tests

Test the queue service independently:

```python
import pytest
from app.services.property_edit_queue_service import PropertyEditQueueService

@pytest.mark.asyncio
async def test_sequential_processing():
    service = PropertyEditQueueService()
    results = []
    
    async def handler(value):
        results.append(value)
        return value
    
    # Enqueue multiple tasks
    await asyncio.gather(
        service.enqueue_task("project-1", handler, value=1),
        service.enqueue_task("project-1", handler, value=2),
        service.enqueue_task("project-1", handler, value=3),
    )
    
    # Verify sequential processing
    assert results == [1, 2, 3]
```

### Integration Tests

Test the full API endpoint with queue:

```python
@pytest.mark.asyncio
async def test_property_edit_queue():
    # Send multiple simultaneous requests
    responses = await asyncio.gather(
        client.post("/edit/project/proj-1/properties", json=request1),
        client.post("/edit/project/proj-1/properties", json=request2),
        client.post("/edit/project/proj-1/properties", json=request3),
    )
    
    # All should succeed
    assert all(r.status_code == 200 for r in responses)
    
    # Check final state is correct
    stats = await client.get("/edit/queue-stats/proj-1")
    assert stats.json()["queue_stats"]["completed_tasks"] == 3
```

## Migration from Old System

The queue system is a drop-in replacement. No changes needed in:
- Frontend code
- API contract
- Database schema

The queue processing is transparent to clients - they just get results faster and more reliably.

## Troubleshooting

### Issue: Request Timeout

**Symptom**: 504 timeout error  
**Cause**: Property edit taking longer than 120 seconds  
**Solution**: 
- Check logs for the specific task
- Increase timeout if legitimate
- Investigate why edit is slow (large files, complex changes)

### Issue: Queue Size Growing

**Symptom**: Queue size keeps increasing  
**Cause**: Tasks are taking longer than new tasks arriving  
**Solution**:
- Check queue stats: `/edit/queue-stats/{project_id}`
- Investigate slow tasks in logs
- Consider optimizing property edit logic

### Issue: Worker Not Running

**Symptom**: `worker_running: false` in stats  
**Cause**: Worker crashed or was cancelled  
**Solution**:
- Check error logs for worker crash
- Queue will auto-recreate worker on next request
- Consider adding worker health monitoring

## Future Enhancements

1. **Priority Queue**: Allow high-priority edits to jump the queue
2. **Batch Optimization**: Detect multiple edits to same file and batch them
3. **Persistence**: Store queue state to survive server restarts
4. **Rate Limiting**: Prevent queue flooding from single user
5. **Metrics**: Export queue metrics to monitoring system (Prometheus, etc.)

## Related Documentation

- [Click-to-Edit Implementation](./CLICK_TO_EDIT_IMPLEMENTATION.md)
- [Direct Code Editor](../backend/app/services/direct_code_editor.py)
- [Component Relationship Tracker](../backend/app/services/component_relationship_tracker.py)

