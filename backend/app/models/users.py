"""
User-related models for analytics and usage tracking.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class AnalyticsDataPoint(BaseModel):
    """Single data point in usage analytics"""
    timestamp: str = Field(..., description="ISO timestamp for this data point")
    count: int = Field(..., description="Total number of calls in this time bucket")
    call_types: Dict[str, int] = Field(default_factory=dict, description="Breakdown by call type (generation, edit, question)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": "2025-10-24T00:00:00Z",
                "count": 8,
                "call_types": {
                    "generation": 5,
                    "edit": 3
                }
            }
        }
    }


class UsageAnalyticsResponse(BaseModel):
    """Response model for usage analytics"""
    period: str = Field(..., description="Time period covered (24h, 7d, 30d, all)")
    granularity: str = Field(..., description="Data granularity (hourly, daily)")
    data_points: List[AnalyticsDataPoint] = Field(default_factory=list, description="Time series data points")
    total_calls: int = Field(..., description="Total calls in the period")
    rpm_peak: int = Field(..., description="Peak requests per minute")
    rpd_average: float = Field(..., description="Average requests per day")
    breakdown_by_type: Dict[str, int] = Field(default_factory=dict, description="Total breakdown by call type")

    model_config = {
        "json_schema_extra": {
            "example": {
                "period": "7d",
                "granularity": "daily",
                "data_points": [
                    {
                        "timestamp": "2025-10-18T00:00:00Z",
                        "count": 5,
                        "call_types": {"generation": 3, "edit": 2}
                    },
                    {
                        "timestamp": "2025-10-19T00:00:00Z",
                        "count": 8,
                        "call_types": {"generation": 5, "edit": 3}
                    }
                ],
                "total_calls": 45,
                "rpm_peak": 2,
                "rpd_average": 6.4,
                "breakdown_by_type": {
                    "generation": 30,
                    "edit": 15
                }
            }
        }
    }
