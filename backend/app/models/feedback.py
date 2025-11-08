from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# Define valid actions as a type
ActionType = Literal[
    "create_project",
    "edit_project",
    "generate_website",
    "edit_component",
    "edit_properties",
    "publish_deploy",
    "download_project",
    "manage_settings",
    "upload_avatar",
    "view_analytics",
    "duplicate_project",
    "delete_project",
    "code_editing",
    "preview_project",
    "other"
]


class FeedbackSubmitRequest(BaseModel):
    """Feedback submission request"""
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    message: str = Field(..., min_length=1, max_length=2000, description="Feedback message")
    category: str = Field(
        default="general",
        description="Feedback category: general, bug, feature, ui/ux, other"
    )
    action: Optional[ActionType] = Field(
        None,
        description="Action user was performing or action needed for the feature"
    )
    project_id: Optional[str] = Field(None, description="Optional project ID if feedback relates to a specific project")


class FeedbackResponse(BaseModel):
    """Feedback response model"""
    id: str
    user_id: str
    rating: Optional[int]
    message: str
    category: str
    action: Optional[str]
    project_id: Optional[str]
    is_resolved: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    """List of feedback with pagination"""
    feedback: list[FeedbackResponse]
    total: int
    limit: int
    offset: int
