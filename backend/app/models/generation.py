"""
Generation API request/response models.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List, Union


class GenerateWebsiteRequest(BaseModel):
    """Request model for website generation"""
    prompt: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="Business description for content generation"
    )
    template_id: Optional[str] = Field(
        None,
        description="Template ID to use for generation. If not provided, a suitable template will be generated."
    )
    project_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional project name"
    )
    style_preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional style preferences for template generation"
    )
    attachments: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Uploaded media attachments: [{media_id, url, media_type}]"
    )

    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate prompt is meaningful"""
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class GenerationStatusResponse(BaseModel):
    """Response model for generation status"""
    status: str  # "idle", "generating", "completed", "failed"
    project_id: Optional[str] = None
    progress: Optional[int] = None  # 0-100
    stage: Optional[str] = None  # "analyzing", "generating_structure", "creating_components", etc.
    stage_message: Optional[str] = None  # Human-readable stage message
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class GenerateWebsiteResponse(BaseModel):
    """Response model for website generation"""
    project_id: str
    status: str
    message: str
    html_preview_url: Optional[str] = None


class RateLimitInfo(BaseModel):
    """Response model for rate limit information"""
    tier: str
    limit: int
    used: int
    remaining: int
    resets_at: str


class GenerateReactWebsiteRequest(BaseModel):
    """Request model for React website generation"""
    prompt: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="Business description for React website generation"
    )
    project_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional project name"
    )
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate prompt is meaningful"""
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class GenerateReactWebsiteResponse(BaseModel):
    """Response model for React website generation"""
    project_id: str
    status: str
    message: str
    website_structure: Optional[Dict[str, Any]] = None
    business_analysis: Optional[Dict[str, Any]] = None
    files_count: Optional[int] = None


class ComponentEditRequest(BaseModel):
    """Request model for component editing"""
    selected_element: Optional[Dict[str, Any]] = Field(None, description="Element data from selector (primary/last selected); None = page-scope edit")
    selected_elements: Optional[List[Dict[str, Any]]] = Field(None, description="All selected elements for multi-select edits")
    scope: str = Field("element", description="Edit scope: element, section, or page")
    instruction: str = Field(..., min_length=5, max_length=2000, description="Natural language edit instruction")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Uploaded media attachments: [{media_id, url, media_type}]")
    current_route: Optional[str] = Field(None, description="Route currently shown in the preview iframe (e.g. '/about') — resolves page-scope edits to the right page file")
    confirmed_target: Optional[str] = Field(None, description="File path the user confirmed as the edit target (skips the retarget confirmation)")

    @validator('instruction')
    def validate_instruction(cls, v):
        """Validate instruction is meaningful"""
        if not v.strip():
            raise ValueError("Instruction cannot be empty")
        return v.strip()

    @validator('scope')
    def validate_scope(cls, v):
        if v not in ("element", "section", "page"):
            raise ValueError("scope must be one of: element, section, page")
        return v


class ComponentEditResponse(BaseModel):
    """Response model for component editing"""
    success: bool
    message: str
    updated_file: Optional[str] = None
    updated_files: Optional[List[str]] = None
    preview_url: Optional[str] = None
    preview_id: Optional[str] = None
    old_code: Optional[str] = None
    new_code: Optional[str] = None
    edit_description: Optional[str] = None
    chat_message_id: Optional[str] = None
    needs_confirmation: bool = False
    confirmation: Optional[Dict[str, Any]] = None  # {kind, target_file, resolved_file, affected_pages, reason}


class PropertyChange(BaseModel):
    """Model for a single property change"""
    property: str = Field(..., description="Property name (e.g., 'textColor', 'fontSize')")
    value: Union[str, int, float, bool] = Field(..., description="New property value")
    oldValue: Optional[Union[str, int, float, bool]] = Field(None, description="Previous value (optional)")
    unit: Optional[str] = Field(None, description="Unit for the value (e.g., 'px', 'rem', '%')")


class PropertyEditRequest(BaseModel):
    """Request model for property editing"""
    element_selector: str = Field(..., description="CSS selector for the element")
    component_file: str = Field(..., description="Path to the component file to edit")
    properties: List[PropertyChange] = Field(..., min_items=1, description="List of property changes")
    batch: bool = Field(False, description="Whether to apply all changes at once")


class PropertyEditResponse(BaseModel):
    """Response model for property editing"""
    success: bool
    message: str
    updated_file: str
    changes_applied: List[PropertyChange]
    preview_url: Optional[str] = None
    new_code: Optional[str] = None
    old_code: Optional[str] = None
    prop_edit_info: Optional[Dict[str, Any]] = None  # Info about prop edits (prop_name, source_file)


class ChatMessageRequest(BaseModel):
    """Request model for saving chat messages"""
    message_type: str = Field(..., description="Type: generation, edit, or question")
    user_prompt: str = Field(..., min_length=1, description="User's message")
    ai_response: str = Field(..., min_length=1, description="AI's response")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ChatMessageResponse(BaseModel):
    """Response model for chat message"""
    id: str
    project_id: str
    user_id: str
    message_type: str
    user_prompt: str
    ai_response: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    messages: list[ChatMessageResponse]
    total_count: int

