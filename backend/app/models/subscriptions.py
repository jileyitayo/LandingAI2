"""
Subscription models for Pydantic validation and API responses.
"""

from pydantic import BaseModel
from typing import Optional, List
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
