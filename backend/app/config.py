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
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Stripe (optional for initial setup)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Vercel (optional for initial setup)
    vercel_api_token: str = ""
    vercel_team_id: str = ""

    # CORS
    cors_origins: Union[list[str], str] = ["http://localhost:3000"]

    # Set's open ai calls to use already existing data instead of generating new data
    training_wheels: bool = False
    cost_savings_mode: bool = False
    
    # React Website Generation Validation
    enable_build_validation: bool = True  # Enable actual npm build testing
    strict_validation_mode: bool = False  # Treat warnings as errors and fix them
    max_validation_retries: int = 3  # Maximum retry attempts for fixing validation errors
    max_build_retries: int = 2  # Maximum retry attempts for fixing build errors
    build_timeout: int = 120  # Build timeout in seconds
    max_parallel_fixes: int = 5  # Maximum number of files to fix in parallel

    # Icon Configuration
    use_essential_icons_only: bool = True  # Use minimal 63-icon set (True) or full 313-icon set (False) 

    # # Model settings
    # use_premium_models: bool = True
    # model_temperature: float = 0.7
    
    # # Design settings
    # enable_design_system: bool = True
    # enable_visual_optimizer: bool = True
    # min_quality_score: float = 0.8
    
    # # Performance
    # enable_parallel_generation: bool = True
    # enable_component_cache: bool = True
    
    # # Features
    # enable_animations: bool = True
    # enable_dark_mode: bool = True
    # enable_a11y_checks: bool = True

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

