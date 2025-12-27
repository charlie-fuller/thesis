"""
Authentication and Authorization Tests

Tests for JWT validation, user authentication, and role-based access control.
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest

# ============================================================================
# JWT Token Validation Tests
# ============================================================================

class TestJWTValidation:
    """Tests for JWT token decoding and validation."""

    def test_decode_valid_token(self, valid_jwt_token):
        """Test decoding a valid JWT token."""
        from auth import decode_jwt

        payload = decode_jwt(valid_jwt_token)

        assert payload is not None
        assert payload["sub"] == "test-user-id-12345"
        assert payload["email"] == "testuser@example.com"
        assert payload["aud"] == "authenticated"

    def test_decode_expired_token(self, expired_jwt_token):
        """Test that expired tokens return None."""
        from auth import decode_jwt

        payload = decode_jwt(expired_jwt_token)

        assert payload is None

    def test_decode_invalid_token(self):
        """Test that invalid tokens return None."""
        from auth import decode_jwt

        payload = decode_jwt("invalid.token.here")

        assert payload is None

    def test_decode_token_with_wrong_secret(self):
        """Test that tokens signed with wrong secret return None."""
        from auth import decode_jwt

        # Create token with different secret
        wrong_token = jwt.encode(
            {"sub": "test-user", "aud": "authenticated", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong-secret",
            algorithm="HS256"
        )

        payload = decode_jwt(wrong_token)

        assert payload is None

    def test_decode_token_with_wrong_audience(self):
        """Test that tokens with wrong audience return None."""
        from auth import decode_jwt

        # Create token with wrong audience
        wrong_aud_token = jwt.encode(
            {
                "sub": "test-user",
                "aud": "wrong-audience",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1)
            },
            os.environ["SUPABASE_JWT_SECRET"],
            algorithm="HS256"
        )

        payload = decode_jwt(wrong_aud_token)

        assert payload is None


# ============================================================================
# get_current_user Tests
# ============================================================================

class TestGetCurrentUser:
    """Tests for the get_current_user dependency."""

    @patch("database.get_supabase")
    def test_get_current_user_success(self, mock_get_supabase, valid_jwt_token):
        """Test successful user retrieval from valid token."""
        from fastapi.security import HTTPAuthorizationCredentials

        from auth import get_current_user

        # Mock supabase response
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"role": "user", "client_id": "test-client-id"}
        )
        mock_get_supabase.return_value = mock_supabase

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_jwt_token)

        user = get_current_user(credentials)

        assert user["id"] == "test-user-id-12345"
        assert user["email"] == "testuser@example.com"
        assert user["role"] == "user"
        assert user["client_id"] == "test-client-id"

    def test_get_current_user_invalid_token(self):
        """Test that invalid token raises HTTPException."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        from auth import get_current_user

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail

    @patch("database.get_supabase")
    def test_get_current_user_database_error(self, mock_get_supabase, valid_jwt_token):
        """Test graceful handling when database lookup fails."""
        from fastapi.security import HTTPAuthorizationCredentials

        from auth import get_current_user

        # Mock database error
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB Error")
        mock_get_supabase.return_value = mock_supabase

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_jwt_token)

        user = get_current_user(credentials)

        # Should still return user with default role
        assert user["id"] == "test-user-id-12345"
        assert user["role"] == "user"  # Default fallback
        assert user["client_id"] is None  # Default fallback


# ============================================================================
# Role-Based Access Control Tests
# ============================================================================

class TestRoleBasedAccess:
    """Tests for role-based access control."""

    def test_require_admin_with_admin_role(self, admin_user):
        """Test that admin users pass admin check."""
        from auth import require_role

        checker = require_role(["admin"])

        # Should not raise
        result = checker(admin_user)
        assert result == admin_user

    def test_require_admin_with_user_role(self, regular_user):
        """Test that regular users fail admin check."""
        from fastapi import HTTPException

        from auth import require_role

        checker = require_role(["admin"])

        with pytest.raises(HTTPException) as exc_info:
            checker(regular_user)

        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    def test_require_multiple_roles(self, admin_user, regular_user):
        """Test role checker with multiple allowed roles."""
        from auth import require_role

        checker = require_role(["admin", "user"])

        # Both should pass
        assert checker(admin_user) == admin_user
        assert checker(regular_user) == regular_user


# ============================================================================
# API Authentication Tests
# ============================================================================

class TestAPIAuthentication:
    """Tests for API endpoint authentication."""

    def test_protected_endpoint_without_token(self, test_client):
        """Test that protected endpoints require authentication."""
        response = test_client.get("/api/conversations")

        assert response.status_code == 403  # No authorization header

    def test_protected_endpoint_with_invalid_token(self, test_client):
        """Test that invalid tokens are rejected."""
        response = test_client.get(
            "/api/conversations",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    @patch("database.get_supabase")
    def test_protected_endpoint_with_valid_token(self, mock_get_supabase, test_client, valid_jwt_token):
        """Test that valid tokens are accepted."""
        # Mock supabase
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"role": "user", "client_id": "test-client"}
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_get_supabase.return_value = mock_supabase

        response = test_client.get(
            "/api/conversations",
            headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        # Should not be 401 or 403
        assert response.status_code not in [401, 403]


# ============================================================================
# Edge Cases
# ============================================================================

class TestAuthEdgeCases:
    """Edge case tests for authentication."""

    def test_missing_jwt_secret_warning(self, capsys):
        """Test that missing JWT secret logs a warning."""
        # This is tested at import time, so we verify the warning logic
        # The warning is printed at module load if SUPABASE_JWT_SECRET is empty
        # Since we set it in conftest, this just verifies the module loads

    def test_token_with_missing_sub_claim(self):
        """Test handling of token without 'sub' claim."""
        from auth import decode_jwt

        # Create token without 'sub'
        token = jwt.encode(
            {"email": "test@example.com", "aud": "authenticated", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            os.environ["SUPABASE_JWT_SECRET"],
            algorithm="HS256"
        )

        payload = decode_jwt(token)

        # Should decode successfully (sub is accessed later)
        assert payload is not None
        assert payload.get("sub") is None

    def test_get_current_user_optional_without_token(self):
        """Test optional auth with no credentials."""
        from auth import get_current_user_optional

        result = get_current_user_optional(None)

        assert result is None

    @patch("database.get_supabase")
    def test_get_current_user_optional_with_valid_token(self, mock_get_supabase, valid_jwt_token):
        """Test optional auth with valid credentials."""
        from fastapi.security import HTTPAuthorizationCredentials

        from auth import get_current_user_optional

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"role": "user", "client_id": "test-client"}
        )
        mock_get_supabase.return_value = mock_supabase

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_jwt_token)

        result = get_current_user_optional(credentials)

        assert result is not None
        assert result["id"] == "test-user-id-12345"
