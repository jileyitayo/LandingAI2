"""
Media Router
API endpoints for uploading and managing project media (images now, video later).
Used for chat attachments, site assets, and favicons.
"""

import io
import uuid
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import log_action

logger = logging.getLogger(__name__)
router = APIRouter(tags=["media"])

MEDIA_BUCKET = "project-media"

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
}

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Images larger than this on either axis are downscaled before storage
# (keeps multimodal LLM payloads and page weight sane)
MAX_DIMENSION = 2048

ALLOWED_PURPOSES = {"attachment", "favicon"}


class MediaResponse(BaseModel):
    """Uploaded media item"""
    id: str
    project_id: Optional[str] = None
    public_url: str
    media_type: str
    mime_type: str
    original_filename: Optional[str] = None
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    purpose: str
    created_at: Optional[str] = None


class MediaListResponse(BaseModel):
    """List of media for a project"""
    media: List[MediaResponse]


def _verify_project_ownership(supabase, project_id: str, user_id: str) -> dict:
    """Fetch a project and verify the current user owns it."""
    response = (
        supabase.table("projects")
        .select("id, user_id")
        .eq("id", project_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    project = response.data[0]
    if project["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this project",
        )
    return project


def _process_image(file_content: bytes, mime_type: str):
    """
    Extract dimensions and downscale oversized images.

    Returns (content, mime_type, width, height, extension).
    Falls back to the original bytes if Pillow can't parse the image.
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(file_content))
        width, height = img.size

        if max(width, height) > MAX_DIMENSION and mime_type != "image/gif":
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
            width, height = img.size
            buffer = io.BytesIO()
            if mime_type in ("image/jpeg", "image/jpg"):
                img = img.convert("RGB")
                img.save(buffer, format="JPEG", quality=90)
            elif mime_type == "image/webp":
                img.save(buffer, format="WEBP", quality=90)
            else:
                img.save(buffer, format="PNG")
            file_content = buffer.getvalue()

        return file_content, width, height
    except Exception as e:
        logger.warning(f"Image processing failed, storing original: {e}")
        return file_content, None, None


@router.post("/media", response_model=MediaResponse)
@log_action(action_type='CREATE', target_resource_type='project_media')
async def upload_media(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    purpose: str = Form("attachment"),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a media file (image) to Supabase Storage.

    project_id is optional: dashboard uploads happen before a project exists
    and are linked to the project after generation.
    """
    user_id = current_user["id"]
    supabase = get_supabase_client()

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}",
        )

    if purpose not in ALLOWED_PURPOSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid purpose. Allowed: {', '.join(sorted(ALLOWED_PURPOSES))}",
        )

    if project_id:
        _verify_project_ownership(supabase, project_id, user_id)

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.0f}MB",
        )

    file_content, width, height = _process_image(file_content, file.content_type)

    file_extension = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "jpg"
    storage_path = f"{user_id}/{uuid.uuid4()}.{file_extension}"

    try:
        supabase.storage.from_(MEDIA_BUCKET).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": file.content_type},
        )
    except Exception as upload_error:
        logger.error(f"Failed to upload media: {upload_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload media: {upload_error}",
        )

    public_url = supabase.storage.from_(MEDIA_BUCKET).get_public_url(storage_path)
    # Supabase appends a trailing '?' to public URLs sometimes; normalize
    public_url = public_url.rstrip("?")

    insert_response = (
        supabase.table("project_media")
        .insert({
            "project_id": project_id,
            "user_id": user_id,
            "media_type": "image",
            "storage_path": storage_path,
            "public_url": public_url,
            "original_filename": file.filename,
            "mime_type": file.content_type,
            "size_bytes": len(file_content),
            "width": width,
            "height": height,
            "purpose": purpose,
        })
        .execute()
    )

    if not insert_response.data:
        try:
            supabase.storage.from_(MEDIA_BUCKET).remove([storage_path])
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save media record",
        )

    row = insert_response.data[0]
    return MediaResponse(
        id=row["id"],
        project_id=row.get("project_id"),
        public_url=row["public_url"],
        media_type=row["media_type"],
        mime_type=row["mime_type"],
        original_filename=row.get("original_filename"),
        size_bytes=row["size_bytes"],
        width=row.get("width"),
        height=row.get("height"),
        purpose=row["purpose"],
        created_at=row.get("created_at"),
    )


@router.get("/projects/{project_id}/media", response_model=MediaListResponse)
@log_action(action_type='READ', target_resource_type='project_media')
async def list_project_media(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """List all media attached to a project."""
    user_id = current_user["id"]
    supabase = get_supabase_client()

    _verify_project_ownership(supabase, project_id, user_id)

    response = (
        supabase.table("project_media")
        .select("*")
        .eq("project_id", project_id)
        .order("created_at", desc=True)
        .execute()
    )

    return MediaListResponse(
        media=[
            MediaResponse(
                id=row["id"],
                project_id=row.get("project_id"),
                public_url=row["public_url"],
                media_type=row["media_type"],
                mime_type=row["mime_type"],
                original_filename=row.get("original_filename"),
                size_bytes=row["size_bytes"],
                width=row.get("width"),
                height=row.get("height"),
                purpose=row.get("purpose") or "attachment",
                created_at=row.get("created_at"),
            )
            for row in (response.data or [])
        ]
    )


@router.delete("/media/{media_id}")
@log_action(action_type='DELETE', target_resource_type='project_media')
async def delete_media(
    media_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a media file (storage object + record)."""
    user_id = current_user["id"]
    supabase = get_supabase_client()

    response = (
        supabase.table("project_media")
        .select("*")
        .eq("id", media_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )
    media = response.data[0]
    if media["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this media",
        )

    try:
        supabase.storage.from_(MEDIA_BUCKET).remove([media["storage_path"]])
    except Exception as e:
        logger.warning(f"Failed to remove storage object {media['storage_path']}: {e}")

    supabase.table("project_media").delete().eq("id", media_id).execute()

    return {"message": "Media deleted"}
