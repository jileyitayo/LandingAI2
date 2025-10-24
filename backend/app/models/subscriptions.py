"""
Subscription models for Pydantic validation and API responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============================================================================
# Subscription Tier Models
# ============================================================================

class SubscriptionTierResponse(BaseModel):
    """Response model for subscription tier information"""
    id: str
    tier_name: str
    display_name: str
    description: Optional[str] = None
    daily_generation_limit: int
    per_minute_limit: int
    price_monthly: Decimal
    price_yearly: Decimal
    features: List[str] = []
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SubscriptionTierListResponse(BaseModel):
    """Response model for list of subscription tiers"""
    tiers: List[SubscriptionTierResponse]
    total_count: int


# ============================================================================
# User Subscription Models
# ============================================================================

class UserSubscriptionResponse(BaseModel):
    """Response model for user's subscription information"""
    id: str
    user_id: str
    tier: SubscriptionTierResponse
    status: str  # 'active', 'cancelled', 'expired', 'past_due', 'trialing'
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    cancelled_at: Optional[str] = None
    trial_start: Optional[str] = None
    trial_end: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ============================================================================
# Stripe Checkout Models
# ============================================================================

class CreateCheckoutSessionRequest(BaseModel):
    """Request model for creating Stripe checkout session"""
    tier_id: str = Field(..., description="Subscription tier ID to subscribe to")
    billing_period: str = Field(..., description="'monthly' or 'yearly'")
    success_url: Optional[str] = Field(None, description="URL to redirect after successful payment")
    cancel_url: Optional[str] = Field(None, description="URL to redirect if payment cancelled")

    @validator('billing_period')
    def validate_billing_period(cls, v):
        if v not in ['monthly', 'yearly']:
            raise ValueError("billing_period must be 'monthly' or 'yearly'")
        return v


class CheckoutSessionResponse(BaseModel):
    """Response model for Stripe checkout session"""
    session_id: str
    checkout_url: str
    message: str = "Redirect user to checkout_url to complete payment"


class CustomerPortalSessionRequest(BaseModel):
    """Request model for creating Stripe customer portal session"""
    return_url: Optional[str] = Field(None, description="URL to return to after managing subscription")


class CustomerPortalSessionResponse(BaseModel):
    """Response model for Stripe customer portal session"""
    portal_url: str
    message: str = "Redirect user to portal_url to manage their subscription"


# ============================================================================
# Subscription Management Models
# ============================================================================

class CancelSubscriptionRequest(BaseModel):
    """Request model for cancelling subscription"""
    cancel_immediately: bool = Field(False, description="If true, cancel immediately. If false, cancel at period end.")
    cancellation_reason: Optional[str] = Field(None, max_length=500, description="Optional reason for cancellation")


class CancelSubscriptionResponse(BaseModel):
    """Response model for subscription cancellation"""
    success: bool
    message: str
    cancelled_at: Optional[str] = None
    cancel_at_period_end: bool = False
    subscription_ends_at: Optional[str] = None


# ============================================================================
# Usage Tracking Models
# ============================================================================

class DailyUsageInfo(BaseModel):
    """Daily usage information"""
    limit: int
    used: int
    remaining: int
    resets_at: str
    resets_in_seconds: int


class PerMinuteUsageInfo(BaseModel):
    """Per-minute usage information"""
    limit: int
    calls_in_last_minute: int
    can_call_now: bool
    retry_after_seconds: int = 0


class CurrentUsageResponse(BaseModel):
    """Response model for current usage statistics"""
    tier: str
    tier_display_name: str
    daily: DailyUsageInfo
    per_minute: PerMinuteUsageInfo


# ============================================================================
# Rate Limit Error Models
# ============================================================================

class RateLimitErrorDetail(BaseModel):
    """Detailed rate limit error information"""
    detail: str
    limit_type: str  # 'per_minute' or 'daily'
    tier: str
    retry_after_seconds: int
    countdown_message: str
    upgrade_suggestion: Optional[str] = None


# ============================================================================
# Billing Event Models
# ============================================================================

class BillingEventResponse(BaseModel):
    """Response model for billing event"""
    id: str
    user_id: str
    event_type: str
    stripe_event_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: str

    class Config:
        from_attributes = True


class BillingHistoryResponse(BaseModel):
    """Response model for billing history"""
    events: List[BillingEventResponse]
    total_count: int


# ============================================================================
# AI Call Log Models (for debugging/analytics)
# ============================================================================

class AICallLogResponse(BaseModel):
    """Response model for AI call log"""
    id: str
    user_id: str
    project_id: Optional[str] = None
    call_type: str  # 'generation', 'edit', 'question'
    endpoint: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
