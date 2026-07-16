"""Application configuration using Pydantic settings."""

from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "SiteSmith API"
    app_version: str = "0.1.0"
    app_brand_name: str = "SiteSmith"  # Brand name displayed in generated websites (e.g., footer attribution)
    debug: bool = False

    # Supabase (optional for initial setup)
    supabase_url: str = ""
    supabase_service_key: str = ""

    # OpenAI (optional for initial setup)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # LLM model selection (env-overridable; gemini-3.5-flash-lite does not exist
    # on this API key — only gemini-3.5-flash and gemini-3.1-flash-lite do).
    # The provider is inferred from the model-name prefix, so these can be
    # swapped freely between gemini-* (google_api_key), gpt-*/o* (openai_api_key),
    # and claude-* (anthropic_api_key) — the matching API key must be set.
    # Model used for component editing and build-error fixing
    edit_model: str = "gemini-3.1-flash-lite"
    # Model used for per-page website code generation (the expensive call)
    generation_model: str = "gemini-3.5-flash"
    # Model used for business analysis, structure, theme, and guardrails
    analysis_model: str = "gemini-3.1-flash-lite"

    # Stripe (optional for initial setup)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Vercel (optional for initial setup)
    vercel_api_token: str = ""
    vercel_team_id: str = ""

    # Custom domains (Pro tier). DNS values shown to users; Vercel may echo
    # newer recommended targets in API responses, which take precedence.
    vercel_apex_a_value: str = "76.76.21.21"
    vercel_cname_value: str = "cname.vercel-dns.com"
    # Hostname suffixes users may not connect as custom domains
    blocked_domain_suffixes: Union[list[str], str] = [".vercel.app", "vercel.com", "sitesmith.app"]

    # Backend URL (for generating absolute URLs in Railway/production)
    backend_url: str = "http://localhost:8000"

    # CORS
    # Allow both localhost and 0.0.0.0 for development flexibility
    cors_origins: Union[list[str], str] = ["http://localhost:3000", "http://0.0.0.0:3000"]

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
    
    # Animation Configuration
    enable_animations_default: bool = True  # Enable animations by default for all users (Pro users always get animations)

    # Parallel Generation Configuration
    enable_parallel_generation: bool = False  # Enable parallel page and component generation (faster but uses more resources)
    max_parallel_pages: int = 5  # Maximum number of pages to generate in parallel

    # Pre-flight intent check + URL ingestion kill switches (all fail open:
    # any pre-flight error degrades to normal generation, never blocks it)
    intent_preflight_enabled: bool = True  # Intent check + clarification gate on /generate_website
    url_ingestion_enabled: bool = True  # Outbound fetching of user-referenced sites (generation + edits)
    edit_clarify_enabled: bool = True  # Clarifying questions in the edit chat
    site_ingest_timeout_s: float = 15.0  # Overall cap for one site extraction
    site_ingest_max_html_bytes: int = 2 * 1024 * 1024  # Byte cap for the index HTML fetch

    # LangGraph settings
    enable_langgraph_checkpoints: bool = True
    langgraph_max_retries: int = 3
    langgraph_parallel_workers: int = 3
    guardrails_max_prompt_length: int = 10000
    guardrails_rate_limit_per_minute: int = 60 

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

    @field_validator("cors_origins", "blocked_domain_suffixes", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse list settings from JSON/comma-separated string or list."""
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

