"""Global pytest configuration and session-wide fixtures."""

from __future__ import annotations

from typing import Dict, List

import pytest

try:
    from app.config import settings
    from app.utils.supabase_client import get_supabase_client
except Exception:
    settings = None  # type: ignore
    get_supabase_client = None  # type: ignore


# In-memory registry for users created during tests
_TEST_USERS_TO_DELETE: List[Dict[str, str]] = []


@pytest.fixture(scope="session")
def test_user_registry() -> List[Dict[str, str]]:
    """Provide a shared registry to record users created during tests.

    Tests can append dicts like {"id": "...", "email": "..."}.
    """
    return _TEST_USERS_TO_DELETE


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_users_at_session_end():
    """Automatically run once after all tests to delete registered users."""
    yield

    if not _TEST_USERS_TO_DELETE:
        return

    # Ensure we have configuration and a working client
    try:
        if settings is None or get_supabase_client is None:
            return
        if not settings.supabase_url or not settings.supabase_service_key:
            return
        client = get_supabase_client()
    except Exception:
        # If we cannot initialize a real client, skip cleanup silently
        return

    # Attempt to delete any recorded users
    for entry in _TEST_USERS_TO_DELETE:
        user_id = entry.get("id")
        if user_id:
            try:
                print(f"Deleting user {user_id}")
                client.auth.admin.delete_user(user_id)
                continue
            except Exception:
                print(f"Error deleting user {user_id}")
                pass

