"""
History Router
Edit history listing and one-click revert (undo) for AI edits.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.utils.supabase_client import get_supabase_client
from app.services.project_file_manager import project_file_manager
from app.services.vite_preview_service import vite_preview_service
from app.services.component_editor_service import component_editor_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["history"])


class EditHistoryFile(BaseModel):
    file_path: str
    is_reverted: bool


class EditHistoryItem(BaseModel):
    chat_message_id: str
    instruction: str
    edit_description: Optional[str] = None
    created_at: str
    files: List[EditHistoryFile]
    is_reverted: bool
    can_revert: bool


class EditHistoryResponse(BaseModel):
    edits: List[EditHistoryItem]


class RevertResponse(BaseModel):
    success: bool
    message: str
    reverted_files: List[str]
    preview_url: Optional[str] = None
    preview_id: Optional[str] = None


def _get_owned_project(supabase, project_id: str, user_id: str) -> dict:
    response = supabase.table("projects").select("id, user_id, preview_id").eq("id", project_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    project = response.data[0]
    if project["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return project


async def rebuild_and_swap_preview(supabase, project_id: str, project: dict, files: Dict[str, str]) -> Dict[str, Any]:
    """Build a fresh preview from files, point the project at it, and clean up the old one."""
    preview_result = await asyncio.to_thread(vite_preview_service.create_preview, project_id, files)
    new_preview_id = preview_result.get("preview_id")
    old_preview_id = project.get("preview_id")
    try:
        supabase.table("projects").update({
            "preview_id": new_preview_id,
            "last_edited_at": datetime.utcnow().isoformat(),
        }).eq("id", project_id).execute()
    except Exception as e:
        logger.warning(f"[HISTORY] Failed to update preview_id/last_edited_at: {e}")
    if old_preview_id and old_preview_id != new_preview_id:
        try:
            vite_preview_service.delete_preview(old_preview_id)
        except Exception as e:
            logger.warning(f"[HISTORY] Failed to delete old preview {old_preview_id}: {e}")
    return preview_result


@router.get("/projects/{project_id}/edit-history", response_model=EditHistoryResponse)
async def get_edit_history(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """List AI edits (grouped per chat message) with their files and revert state."""
    user_id = current_user["id"]
    supabase = get_supabase_client()
    _get_owned_project(supabase, project_id, user_id)

    rows = (
        supabase.table("project_edit_history")
        .select("chat_message_id, file_path, ai_instruction, edit_description, is_reverted, created_at")
        .eq("project_id", project_id)
        .order("created_at", desc=True)
        .limit(500)
        .execute()
    )

    grouped: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for row in rows.data or []:
        key = row.get("chat_message_id") or f"row-{row['created_at']}"
        if key not in grouped:
            grouped[key] = {
                "chat_message_id": key,
                "instruction": row.get("ai_instruction") or "",
                "edit_description": row.get("edit_description"),
                "created_at": row["created_at"],
                "files": [],
            }
            order.append(key)
        grouped[key]["files"].append(
            EditHistoryFile(file_path=row["file_path"], is_reverted=row["is_reverted"])
        )

    edits = []
    for key in order:
        g = grouped[key]
        all_reverted = all(f.is_reverted for f in g["files"])
        edits.append(EditHistoryItem(
            chat_message_id=g["chat_message_id"],
            instruction=g["instruction"],
            edit_description=g["edit_description"],
            created_at=g["created_at"],
            files=g["files"],
            is_reverted=all_reverted,
            can_revert=not all_reverted and not g["chat_message_id"].startswith("row-"),
        ))

    return EditHistoryResponse(edits=edits)


@router.post("/projects/{project_id}/edits/{chat_message_id}/revert", response_model=RevertResponse)
async def revert_edit(
    project_id: str,
    chat_message_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Revert an AI edit: restore each touched file to its pre-edit code, rebuild
    the preview, and record the revert as a chat message.

    Semantics: last-write-wins per file — later edits to the same files are
    overwritten by this restore (the frontend confirms with the user first).
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()
    project = _get_owned_project(supabase, project_id, user_id)

    rows = (
        supabase.table("project_edit_history")
        .select("*")
        .eq("project_id", project_id)
        .eq("chat_message_id", chat_message_id)
        .execute()
    )
    if not rows.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edit not found")

    pending = [r for r in rows.data if not r["is_reverted"]]
    if not pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This edit has already been reverted")

    # Restore old code in the candidate file set, then build BEFORE saving —
    # the same verify-then-save order the edit endpoint uses.
    files = await project_file_manager.get_project_files(project_id)
    candidate_files = dict(files)
    for row in pending:
        candidate_files[row["file_path"]] = row["old_code"]

    try:
        preview_result = await rebuild_and_swap_preview(supabase, project_id, project, candidate_files)
    except Exception as e:
        logger.error(f"[HISTORY] Revert build failed for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The reverted code failed to build; nothing was changed."
        )

    reverted_files = []
    for row in pending:
        save_success, save_message = await component_editor_service.apply_component_edit(
            project_id=project_id,
            file_path=row["file_path"],
            new_code=row["old_code"],
        )
        if not save_success:
            logger.error(f"[HISTORY] Failed to save reverted {row['file_path']}: {save_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restore {row['file_path']}: {save_message}"
            )
        reverted_files.append(row["file_path"])

    now = datetime.utcnow().isoformat()
    supabase.table("project_edit_history").update({
        "is_reverted": True,
        "reverted_at": now,
    }).eq("chat_message_id", chat_message_id).eq("project_id", project_id).execute()

    description = pending[0].get("edit_description") or pending[0].get("ai_instruction") or "edit"
    try:
        supabase.table("project_chat_messages").insert({
            "project_id": project_id,
            "user_id": user_id,
            "message_type": "edit",
            "user_prompt": f"Undo: {pending[0].get('ai_instruction', 'edit')[:200]}",
            "ai_response": f"Reverted: {description}",
            "metadata": {
                "reverted_chat_message_id": chat_message_id,
                "files": reverted_files,
            },
        }).execute()
    except Exception as e:
        logger.warning(f"[HISTORY] Failed to record revert chat message: {e}")

    return RevertResponse(
        success=True,
        message=f"Reverted {len(reverted_files)} file(s)",
        reverted_files=reverted_files,
        preview_url=preview_result.get("preview_url"),
        preview_id=preview_result.get("preview_id"),
    )
