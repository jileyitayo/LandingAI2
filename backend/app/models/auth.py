"""Authentication request/response models."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """User signup request model."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "first_name": "John",
                "last_name": "Doe",
            }
        }
    }


class LoginRequest(BaseModel):
    """User login request model."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Token refresh request model."""

    refresh_token: str = Field(..., description="Refresh token from login")

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }
    }


class AuthResponse(BaseModel):
    """Authentication response model."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field(default="bearer", description="Token type")
    user: dict = Field(..., description="User information")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expires_in": 3600,
                "token_type": "bearer",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "created_at": "2025-10-03T12:00:00Z",
                },
            }
        }
    }


class UserResponse(BaseModel):
    """User information response model."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    created_at: str = Field(..., description="Account creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "created_at": "2025-10-03T12:00:00Z",
                "updated_at": "2025-10-03T12:00:00Z",
            }
        }
    }


class MessageResponse(BaseModel):
    """Generic message response model."""

    message: str = Field(..., description="Response message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Operation completed successfully",
            }
        }
    }

