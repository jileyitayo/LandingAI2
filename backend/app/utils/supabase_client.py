"""Supabase client initialization and utilities."""

from supabase import create_client, Client
from app.config import settings


def get_supabase_client() -> Client:
    """
    Create and return a Supabase client instance.
    
    Returns:
        Client: Initialized Supabase client
        
    Raises:
        ValueError: If Supabase credentials are not configured
    """
    if not settings.supabase_url or not settings.supabase_service_key:
        raise ValueError(
            "Supabase credentials not configured. "
            "Please set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
        )
    
    return create_client(settings.supabase_url, settings.supabase_service_key)


# Global Supabase client instance
supabase: Client = get_supabase_client()

