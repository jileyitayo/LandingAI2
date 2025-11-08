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
    selected_element: Dict[str, Any] = Field(..., description="Element data from selector")
    instruction: str = Field(..., min_length=5, max_length=500, description="Natural language edit instruction")
    
    @validator('instruction')
    def validate_instruction(cls, v):
        """Validate instruction is meaningful"""
        if not v.strip():
            raise ValueError("Instruction cannot be empty")
        return v.strip()


class ComponentEditResponse(BaseModel):
    """Response model for component editing"""
    success: bool
    message: str
    updated_file: Optional[str] = None
    preview_url: Optional[str] = None
    old_code: Optional[str] = None
    new_code: Optional[str] = None
    edit_description: Optional[str] = None
    chat_message_id: Optional[str] = None


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

