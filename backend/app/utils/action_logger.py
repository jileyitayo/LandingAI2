"""Action logging decorator for FastAPI route handlers.

This decorator logs metadata about each action/function call to the database
using the Supabase client. It captures request metadata, user information,
execution duration, success/failure, and limited request/response payloads.
"""

import time
from functools import wraps
from typing import Any, Dict

from fastapi import Request, HTTPException
from pydantic import BaseModel
from starlette.responses import JSONResponse, Response

from app.utils.supabase_client import supabase
from app.middleware.auth_middleware import get_user_from_request


def _safe_extract_payload_from_args(args: tuple, kwargs: dict) -> Dict[str, Any]:
    """
    Build a JSON-serializable payload snapshot from handler arguments.

    - Includes Pydantic BaseModel arguments via model_dump.
    - Includes minimal info for Starlette UploadFile: filename and content_type.
    - Skips non-serializable objects.
    """
    payload: Dict[str, Any] = {}

    def serialize_value(value: Any) -> Any:
        try:
            if isinstance(value, BaseModel):
                # Pydantic v2
                return value.model_dump()
        except Exception:
            pass

        # Starlette UploadFile without importing directly to avoid heavy dependency here
        try:
            from starlette.datastructures import UploadFile  # type: ignore

            if isinstance(value, UploadFile):
                return {
                    "filename": value.filename,
                    "content_type": value.content_type,
                    "size": None,  # unknown without reading body
                }
        except Exception:
            pass

        # Primitive or already serializable
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, (list, tuple)):
            return [serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {str(k): serialize_value(v) for k, v in value.items()}

        # Fallback: string representation
        return str(value)

    # Positional args (skip the first arg which should be Request)
    for index, arg in enumerate(args):
        if index == 0:
            continue
        payload[f"arg_{index}"] = serialize_value(arg)

    # Keyword args
    for key, value in kwargs.items():
        if key == "request":
            continue
        payload[key] = serialize_value(value)

    return payload


def _safe_extract_response_payload(response: Any) -> Any:
    """Return a JSON-serializable snapshot of the response if feasible."""
    try:
        if isinstance(response, BaseModel):
            return response.model_dump()
    except Exception:
        pass

    if isinstance(response, dict):
        return response

    if isinstance(response, JSONResponse):
        # JSONResponse has a private attribute .body, but we avoid relying on it.
        # We can return the content set at init if accessible via .media_type
        return None

    if isinstance(response, Response):
        return None

    # Fallback: None to avoid large/unserializable payloads
    return None


def log_action(action_type: str, target_resource_type: str = None):
    """
    Decorator to log FastAPI route handler calls to the action_logs table.

    Args:
        action_type: e.g., 'CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', ...
        target_resource_type: Optional resource type, e.g. 'user_profile'
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Expect first arg to be Request for route handlers
            request: Request = kwargs.get("request") or (args[0] if args else None)
            if not isinstance(request, Request):
                # If not a typical FastAPI handler signature, just call through
                return await func(*args, **kwargs)

            start_time = time.time()
            success = True
            status_code = 200
            error_message = None
            error_details = None
            response_payload = None

            # Build request payload snapshot from args/kwargs
            request_payload = _safe_extract_payload_from_args(args, kwargs)

            # Resolve user id if present
            user_id = None
            try:
                user_info = get_user_from_request(request)
                if isinstance(user_info, dict):
                    user_id = user_info.get("sub") or user_info.get("id")
            except HTTPException as e:
                # Allow unauthenticated requests to still be logged
                if e.status_code != 401:
                    # Other auth errors should still propagate after logging
                    pass
            except Exception:
                # Non-auth related errors in extracting user should not block
                pass

            try:
                response = await func(*args, **kwargs)
                # Attempt to derive status code and payload
                if hasattr(response, "status_code"):
                    status_code = getattr(response, "status_code", 200)
                response_payload = _safe_extract_response_payload(response)
            except HTTPException as http_exc:
                success = False
                status_code = http_exc.status_code
                error_message = str(http_exc.detail)
                response_payload = {"error": http_exc.detail}
                raise
            except Exception as exc:
                success = False
                status_code = 500
                error_message = str(exc)
                response_payload = {"error": "Internal Server Error"}
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)

                # Determine target resource id from path params if present
                path_params = getattr(request, "path_params", {}) or {}
                target_resource_id = next(iter(path_params.values()), None) if path_params else None

                # Build log record
                log_data: Dict[str, Any] = {
                    "timestamp": None,  # default NOW() in DB
                    "user_id": user_id,
                    "action_name": func.__name__,
                    "action_type": action_type,
                    "success": success,
                    "duration_ms": duration_ms,
                    "ip_address": getattr(request.client, "host", None) if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "http_method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "request_payload": request_payload if request_payload else None,
                    "response_payload": response_payload,
                    "error_message": error_message,
                    "error_details": None if not error_details else {"details": error_details},
                    "target_resource_type": target_resource_type,
                    "target_resource_id": target_resource_id,
                }

                # Remove keys with None to keep logs compact
                log_data = {k: v for k, v in log_data.items() if v is not None}

                try:
                    supabase.table("action_logs").insert(log_data).execute()
                except Exception as log_exc:
                    # Do not interrupt main flow if logging fails
                    print(f"[action_logger] Failed to insert action log: {log_exc}")

            return response

        return wrapper

    return decorator


