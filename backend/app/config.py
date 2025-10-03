"""Application configuration using Pydantic settings."""

from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "SiteSmith API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Supabase (optional for initial setup)
    supabase_url: str = ""
    supabase_service_key: str = ""

    # OpenAI (optional for initial setup)
    openai_api_key: str = ""

    # Stripe (optional for initial setup)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Vercel (optional for initial setup)
    vercel_api_token: str = ""
    vercel_team_id: str = ""

    # CORS
    cors_origins: Union[list[str], str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle JSON array string format
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Handle comma-separated string format
                return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()

