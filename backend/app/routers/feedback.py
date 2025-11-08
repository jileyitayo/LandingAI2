"""Feedback management endpoints."""

import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status, Query
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

from app.models.feedback import (
    FeedbackSubmitRequest,
    FeedbackResponse,
    FeedbackListResponse,
)
from app.middleware.auth_middleware import get_user_from_request
from app.utils.supabase_client import supabase
from app.utils.action_logger import log_action

router = APIRouter()


@router.post("", response_model=dict)
@log_action(action_type='CREATE', target_resource_type='feedback')
async def submit_feedback(request: Request, feedback_data: FeedbackSubmitRequest):
    """
    Submit user feedback or feature request.

    Users can provide general feedback, report bugs, or suggest features.
    Optional rating from 1-5 stars.
    """
    try:
        user_info = get_user_from_request(request)
        user_id = user_info.get("sub") or user_info.get("id")

        # Validate category
        valid_categories = ['general', 'bug', 'feature', 'ui/ux', 'other']
        if feedback_data.category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )

        # Prepare feedback data
        feedback_insert = {
            "user_id": user_id,
            "message": feedback_data.message,
            "category": feedback_data.category,
        }

        # Add optional fields
        if feedback_data.rating is not None:
            feedback_insert["rating"] = feedback_data.rating

        if feedback_data.action:
            feedback_insert["action"] = feedback_data.action

        if feedback_data.project_id:
            feedback_insert["project_id"] = feedback_data.project_id

        # Insert feedback into database
        response = supabase.table("feedback").insert(feedback_insert).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit feedback"
            )

        logger.info(f"Feedback submitted by user {user_id}: {feedback_data.category}")

        return {
            "id": response.data[0]["id"],
            "message": "Thank you for your feedback! We appreciate your input."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("", response_model=FeedbackListResponse)
@log_action(action_type='READ', target_resource_type='feedback')
async def get_user_feedback(
    request: Request,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Get current user's feedback history.

    Returns a paginated list of feedback submitted by the authenticated user.
    """
    try:
        user_info = get_user_from_request(request)
        user_id = user_info.get("sub") or user_info.get("id")

        # Get total count
        count_response = supabase.table("feedback").select(
            "id",
            count="exact"
        ).eq("user_id", user_id).execute()

        total = count_response.count or 0

        # Get feedback with pagination
        response = supabase.table("feedback").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).range(
            offset, offset + limit - 1
        ).execute()

        feedback_list = []
        for item in response.data:
            feedback_list.append(FeedbackResponse(
                id=item["id"],
                user_id=item["user_id"],
                rating=item.get("rating"),
                message=item["message"],
                category=item["category"],
                action=item.get("action"),
                project_id=item.get("project_id"),
                is_resolved=item.get("is_resolved", False),
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            ))

        return FeedbackListResponse(
            feedback=feedback_list,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to fetch feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
@log_action(action_type='READ', target_resource_type='feedback')
async def get_feedback_by_id(request: Request, feedback_id: str):
    """
    Get a specific feedback by ID.

    Users can only access their own feedback.
    """
    try:
        user_info = get_user_from_request(request)
        user_id = user_info.get("sub") or user_info.get("id")

        # Get feedback
        response = supabase.table("feedback").select("*").eq(
            "id", feedback_id
        ).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )

        item = response.data[0]
        return FeedbackResponse(
            id=item["id"],
            user_id=item["user_id"],
            rating=item.get("rating"),
            message=item["message"],
            category=item["category"],
            action=item.get("action"),
            project_id=item.get("project_id"),
            is_resolved=item.get("is_resolved", False),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
