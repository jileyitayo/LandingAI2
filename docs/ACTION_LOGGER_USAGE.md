# ActionLogger Usage Guide

This document describes how to use the `ActionLogger` class for logging actions to the database.

## Overview

The `ActionLogger` class provides a flexible, function-based approach to logging actions, complementing the decorator-based `@log_action` for cases where you need more control or want to log actions manually.

## Basic Usage

### Simple Action Logging

The most basic usage with just the required parameters:

```python
from app.utils.action_logger import ActionLogger
from app.utils.supabase_client import get_supabase_client

# Initialize the logger
supabase = get_supabase_client()
action_logger = ActionLogger(supabase)

# Log a simple action
await action_logger.log_action(
    user_id="user-123",
    action="template_generation_started",
    details={"prompt": "Create a restaurant website"}
)
```

### Action with Additional Context

Log with more context for better tracking:

```python
await action_logger.log_action(
    user_id=user_id,
    action="template_generated",
    details={
        "template_id": template_id,
        "category": "restaurant",
        "sections_count": 6
    },
    action_type="CREATE",
    target_resource_type="template",
    target_resource_id=template_id,
    duration_ms=5432
)
```

### Logging with Request Context

Use the `log_request` convenience method to automatically extract request metadata:

```python
from fastapi import Request

@router.post("/templates/generate")
async def generate_template(
    request: Request,
    data: GenerateTemplateRequest,
    current_user: dict = Depends(get_current_user)
):
    supabase = get_supabase_client()
    action_logger = ActionLogger(supabase)
    
    # Automatically captures IP, user agent, HTTP method, and path
    await action_logger.log_request(
        request=request,
        user_id=current_user["id"],
        action="template_generation_started",
        details={"prompt": data.prompt[:100]},
        target_resource_type="template"
    )
```

### Logging Failed Actions

Log errors and failures:

```python
try:
    template = generate_template(prompt)
    
    await action_logger.log_action(
        user_id=user_id,
        action="template_generated",
        details={"template_id": template.id},
        success=True,
        status_code=201
    )
except Exception as e:
    await action_logger.log_action(
        user_id=user_id,
        action="template_generation_failed",
        details={"prompt": prompt[:100]},
        success=False,
        error_message=str(e),
        error_details={"exception_type": type(e).__name__},
        status_code=500
    )
    raise
```

## Available Parameters

### Required Parameters

- `user_id` (str): ID of the user performing the action
- `action` (str): Name/description of the action (e.g., "template_generated")

### Optional Parameters

- `details` (dict): Additional details about the action (stored in response_payload)
- `action_type` (str): Type of action - "CREATE", "READ", "UPDATE", "DELETE", "AUTH", or "OTHER"
  - If not provided, will be inferred from the action name
- `success` (bool): Whether the action was successful (default: True)
- `duration_ms` (int): Duration of the action in milliseconds
- `ip_address` (str): IP address of the client
- `user_agent` (str): User agent string
- `http_method` (str): HTTP method (GET, POST, PUT, PATCH, DELETE)
- `path` (str): URL path
- `status_code` (int): HTTP status code (default: 200 if success, 500 if not)
- `request_payload` (dict): Request data snapshot
- `response_payload` (dict): Response data snapshot (falls back to `details` if not provided)
- `error_message` (str): Error message if action failed
- `error_details` (dict): Additional error details
- `target_resource_type` (str): Type of resource being acted upon (e.g., "template", "project")
  - If not provided, will be inferred from the action name
- `target_resource_id` (str): ID of the resource being acted upon

## Automatic Inference

The `ActionLogger` automatically infers some fields if not provided:

### Action Type Inference

Based on keywords in the action name:
- **CREATE**: create, generat*, add, new, insert
- **READ**: read, get, fetch, list, view, check
- **UPDATE**: update, edit, modify, change, patch
- **DELETE**: delete, remove, destroy
- **AUTH**: login, logout, signin, signout, auth
- **OTHER**: anything else

Example:
```python
# These actions will automatically be typed as CREATE
"template_generated" → CREATE
"project_created" → CREATE
"user_added" → CREATE

# These will be READ
"template_fetched" → READ
"list_projects" → READ
```

### Resource Type Inference

Detects common resource types from action names:
- template
- project
- user
- profile
- avatar
- website
- component
- deployment
- subscription

Example:
```python
# These actions will automatically detect resource type
"template_generated" → resource_type: "template"
"project_updated" → resource_type: "project"
"user_profile_viewed" → resource_type: "user" or "profile"
```

## Real-World Examples

### Example 1: Template Generation Flow

```python
from app.utils.action_logger import ActionLogger
from app.utils.supabase_client import get_supabase_client
import time

@router.post("/templates/generate")
async def generate_template(
    request: Request,
    data: GenerateTemplateRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    supabase = get_supabase_client()
    action_logger = ActionLogger(supabase)
    
    # Log start
    start_time = time.time()
    await action_logger.log_action(
        user_id=user_id,
        action="template_generation_started",
        details={"prompt": data.prompt[:100]}
    )
    
    try:
        # Generate template
        template = template_generator.generate_template(
            prompt=data.prompt,
            user_id=user_id
        )
        
        # Save to database
        template_id = await save_template_to_db(template, supabase)
        
        # Log success
        duration_ms = int((time.time() - start_time) * 1000)
        await action_logger.log_action(
            user_id=user_id,
            action="template_generated",
            details={
                "template_id": template_id,
                "category": template.get("category"),
                "sections_count": len(template.get("sections_config", []))
            },
            duration_ms=duration_ms,
            target_resource_id=template_id
        )
        
        return TemplateResponse(**template)
        
    except TemplateGenerationError as e:
        # Log failure
        duration_ms = int((time.time() - start_time) * 1000)
        await action_logger.log_action(
            user_id=user_id,
            action="template_generation_failed",
            details={"prompt": data.prompt[:100]},
            success=False,
            error_message=str(e),
            duration_ms=duration_ms,
            status_code=400
        )
        raise HTTPException(status_code=400, detail=str(e))
```

### Example 2: Resource Access Tracking

```python
@router.get("/templates/{template_id}")
async def get_template(
    request: Request,
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    supabase = get_supabase_client()
    action_logger = ActionLogger(supabase)
    
    # Fetch template
    template = await get_template_from_db(template_id, supabase)
    
    if not template:
        await action_logger.log_action(
            user_id=current_user["id"],
            action="template_access_denied",
            details={"reason": "not_found"},
            success=False,
            target_resource_id=template_id,
            status_code=404
        )
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check permissions
    if not (template.get("created_by") == current_user["id"] or template.get("is_public")):
        await action_logger.log_action(
            user_id=current_user["id"],
            action="template_access_denied",
            details={"reason": "forbidden"},
            success=False,
            target_resource_id=template_id,
            status_code=403
        )
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Log successful access
    await action_logger.log_request(
        request=request,
        user_id=current_user["id"],
        action="template_viewed",
        details={"template_name": template.get("name")},
        target_resource_id=template_id
    )
    
    return TemplateResponse(**template)
```

### Example 3: Bulk Operations

```python
@router.post("/templates/bulk-update")
async def bulk_update_templates(
    data: BulkUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    supabase = get_supabase_client()
    action_logger = ActionLogger(supabase)
    
    updated_count = 0
    failed_count = 0
    
    for template_id in data.template_ids:
        try:
            # Update template
            await update_template(template_id, data.updates, supabase)
            updated_count += 1
        except Exception as e:
            failed_count += 1
    
    # Log bulk operation summary
    await action_logger.log_action(
        user_id=current_user["id"],
        action="templates_bulk_updated",
        details={
            "total_requested": len(data.template_ids),
            "updated": updated_count,
            "failed": failed_count
        },
        action_type="UPDATE",
        target_resource_type="template",
        success=failed_count == 0
    )
    
    return {
        "updated": updated_count,
        "failed": failed_count
    }
```

## Comparison with Decorator

### When to Use ActionLogger (Function-Based)

✅ **Use when:**
- You need fine-grained control over what gets logged
- You want to log multiple actions within a single endpoint
- You need to log actions in non-route functions
- You want to log different details for success vs. failure
- You need to log before/after an operation

### When to Use @log_action Decorator

✅ **Use when:**
- You want automatic logging for entire route handlers
- You want consistent logging across many endpoints
- You don't need custom logic for what to log
- You want less boilerplate code

### Using Both Together

You can use both approaches in the same application:

```python
# Decorator for automatic logging of the entire endpoint
@router.post("/projects")
@log_action(action_type="CREATE", target_resource_type="project")
async def create_project(
    request: Request,
    data: CreateProjectRequest,
    current_user: dict = Depends(get_current_user)
):
    supabase = get_supabase_client()
    action_logger = ActionLogger(supabase)
    
    # Manual logging for specific sub-actions
    await action_logger.log_action(
        user_id=current_user["id"],
        action="project_validation_started",
        details={"name": data.name}
    )
    
    # Validation...
    
    await action_logger.log_action(
        user_id=current_user["id"],
        action="project_template_applied",
        details={"template_id": data.template_id}
    )
    
    # Create project...
    
    return project
```

## Database Schema

The logs are stored in the `action_logs` table with these fields:

```sql
CREATE TABLE action_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_id TEXT,
    action_name TEXT,
    action_type TEXT,
    success BOOLEAN DEFAULT true,
    duration_ms INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    http_method TEXT,
    path TEXT,
    status_code INTEGER,
    request_payload JSONB,
    response_payload JSONB,
    error_message TEXT,
    error_details JSONB,
    target_resource_type TEXT,
    target_resource_id TEXT
);
```

## Best Practices

1. **Always log user actions**: Track who did what and when
2. **Include relevant details**: But avoid logging sensitive data (passwords, tokens, etc.)
3. **Log both success and failure**: Helps with debugging and security monitoring
4. **Use consistent action names**: Makes querying logs easier
5. **Include resource IDs**: Helps track actions on specific resources
6. **Measure duration**: Useful for performance monitoring
7. **Handle logging errors gracefully**: Don't let logging failures break your application

## Querying Logs

Example queries for analyzing logs in Supabase:

```sql
-- Recent template generations
SELECT * FROM action_logs
WHERE action_name = 'template_generated'
ORDER BY timestamp DESC
LIMIT 100;

-- Failed actions in the last hour
SELECT * FROM action_logs
WHERE success = false
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- User activity summary
SELECT 
    user_id,
    COUNT(*) as total_actions,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
    AVG(duration_ms) as avg_duration
FROM action_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY user_id;

-- Most common errors
SELECT 
    error_message,
    COUNT(*) as occurrences
FROM action_logs
WHERE success = false
  AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY error_message
ORDER BY occurrences DESC;
```

## Troubleshooting

### Logs not appearing in database

1. Check Supabase connection
2. Verify the `action_logs` table exists
3. Check for errors in application logs
4. Verify user_id is valid

### Performance impact

The ActionLogger is designed to be lightweight:
- Async operations don't block your handlers
- Failed logging won't crash your app
- Consider using background tasks for high-volume logging

### Memory usage

For high-throughput applications:
- Avoid logging large payloads
- Use `details` for summary info only
- Consider sampling (log 1 in N requests)

