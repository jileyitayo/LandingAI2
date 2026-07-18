"""
Chat Router
Endpoints for a project's chat history and message persistence.
"""

from fastapi import APIRouter, HTTPException, Depends, status
import uuid
import logging

from app.utils.supabase_client import get_supabase_client
from app.utils.auth import get_current_user
from app.utils.project_access import get_owned_project
from app.models.generation import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generation"])


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
        get_owned_project(supabase, project_id, user_id)

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
        get_owned_project(supabase, project_id, user_id)

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

