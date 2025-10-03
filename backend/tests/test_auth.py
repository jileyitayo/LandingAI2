"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from app.main import app


client = TestClient(app)

class MockSupabaseUser:
    """Mock Supabase user object."""
    
    def __init__(self, id="test-user-id", email="newuser@example.com"):
        self.id = id
        self.email = email
        self.created_at = "2025-10-03T12:00:00Z"
        self.updated_at = "2025-10-03T12:00:00Z"
        self.user_metadata = {"first_name": "Test", "last_name": "User"}
        self.app_metadata = {}


class MockSupabaseSession:
    """Mock Supabase session object."""
    
    def __init__(self):
        self.access_token = "mock_access_token"
        self.refresh_token = "mock_refresh_token"
        self.expires_in = 3600


class MockSupabaseResponse:
    """Mock Supabase response object."""
    
    def __init__(self, user=None, session=None):
        self.user = user or MockSupabaseUser()
        self.session = session or MockSupabaseSession()


@pytest.fixture
def mock_supabase():
    """Fixture to mock Supabase client."""
    # Patch all locations where supabase is imported
    with patch("app.utils.supabase_client.supabase") as mock_client, \
         patch("app.utils.auth.supabase") as mock_auth, \
         patch("app.routers.auth.supabase") as mock_router:
        # Make all mocks reference the same auth object
        mock_auth.auth = mock_client.auth
        mock_router.auth = mock_client.auth
        yield mock_client


class TestSignup:
    """Test cases for signup endpoint."""
    
    def test_signup_success(self, mock_supabase, test_user_registry):
        """Test successful user signup."""
        # Mock Supabase response
        mock_response = MockSupabaseResponse()
        mock_supabase.auth.sign_up.return_value = mock_response
        
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "first_name": "New",
                "last_name": "User",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        
    
    def test_signup_invalid_email(self, mock_supabase):
        """Test signup with invalid email format."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "invalid-email",
                "password": "securepassword123",
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_signup_short_password(self, mock_supabase):
        """Test signup with password shorter than 8 characters."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "user@example.com",
                "password": "short",
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_signup_duplicate_email(self, mock_supabase):
        """Test signup with existing email."""
        # Mock Supabase error for duplicate email
        mock_supabase.auth.sign_up.side_effect = Exception("User already registered")
        
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )
        
        assert response.status_code == 409  # Conflict


class TestLogin:
    """Test cases for login endpoint."""
    
    def test_login_success(self, mock_supabase):
        """Test successful user login."""
        # Mock Supabase response
        mock_response = MockSupabaseResponse()
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, mock_supabase):
        """Test login with invalid credentials."""
        # Mock Supabase error
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401


class TestRefreshToken:
    """Test cases for token refresh endpoint."""
    
    def test_refresh_token_success(self, mock_supabase):
        """Test successful token refresh."""
        # Mock Supabase response
        mock_response = MockSupabaseResponse()
        mock_supabase.auth.refresh_session.return_value = mock_response
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "mock_refresh_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_token_invalid(self, mock_supabase):
        """Test refresh with invalid token."""
        # Mock Supabase error
        mock_supabase.auth.refresh_session.side_effect = Exception("Invalid refresh token")
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )
        
        assert response.status_code == 401


class TestGetUser:
    """Test cases for get user endpoint."""
    
    def test_get_user_success(self, mock_supabase):
        """Test getting current user information."""
        # Mock token verification
        mock_user = MockSupabaseUser()
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_supabase.auth.get_user.return_value = mock_response
        
        response = client.get(
            "/api/v1/auth/user",
            headers={"Authorization": "Bearer valid_access_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
    
    def test_get_user_no_token(self, mock_supabase):
        """Test get user without authentication token."""
        response = client.get("/api/v1/auth/user")
        
        assert response.status_code == 403  # Forbidden (no credentials)
    
    def test_get_user_invalid_token(self, mock_supabase):
        """Test get user with invalid token."""
        # Mock invalid token
        mock_response = MagicMock()
        mock_response.user = None
        mock_supabase.auth.get_user.return_value = mock_response
        
        response = client.get(
            "/api/v1/auth/user",
            headers={"Authorization": "Bearer invalid_token"},
        )
        
        assert response.status_code == 401


class TestLogout:
    """Test cases for logout endpoint."""
    
    def test_logout_success(self, mock_supabase):
        """Test successful logout."""
        # Mock token verification
        mock_user = MockSupabaseUser()
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_supabase.auth.get_user.return_value = mock_response
        
        # Mock sign out
        mock_supabase.auth.sign_out.return_value = None
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer mock_access_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_logout_no_token(self, mock_supabase):
        """Test logout without authentication token."""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 403  # Forbidden

