"""Authentication and Authorization Tests.

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
        assert payload["sub"] == "00000000-0000-0000-0000-000000000002"
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
            {
                "sub": "test-user",
                "aud": "authenticated",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "wrong-secret",
            algorithm="HS256",
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
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            os.environ["SUPABASE_JWT_SECRET"],
            algorithm="HS256",
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

        assert user["id"] == "00000000-0000-0000-0000-000000000002"
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
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception(
            "DB Error"
        )
        mock_get_supabase.return_value = mock_supabase

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_jwt_token)

        user = get_current_user(credentials)

        # Should still return user with default role
        assert user["id"] == "00000000-0000-0000-0000-000000000002"
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
            "/api/conversations", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    @patch("database.get_supabase")
    def test_protected_endpoint_with_valid_token(
        self, mock_get_supabase, test_client, valid_jwt_token
    ):
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
            "/api/conversations", headers={"Authorization": f"Bearer {valid_jwt_token}"}
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
            {
                "email": "test@example.com",
                "aud": "authenticated",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            os.environ["SUPABASE_JWT_SECRET"],
            algorithm="HS256",
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
        assert result["id"] == "00000000-0000-0000-0000-000000000002"

    def test_decode_empty_token(self):
        """Test that empty token returns None."""
        from auth import decode_jwt

        payload = decode_jwt("")

        assert payload is None

    def test_decode_token_with_malformed_header(self):
        """Test that tokens with malformed headers return None."""
        from auth import decode_jwt

        # Token with invalid base64 in header
        payload = decode_jwt("not-valid-base64.also-invalid.signature")

        assert payload is None

    @patch("database.get_supabase")
    def test_get_current_user_user_not_in_database(self, mock_get_supabase, valid_jwt_token):
        """Test that user exists in auth but not in users table raises 401."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        from auth import get_current_user

        # Mock empty result (user not found)
        mock_supabase = MagicMock()
        mock_execute = MagicMock(data=None)
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_execute
        mock_get_supabase.return_value = mock_supabase

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_jwt_token)

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "User profile not found" in exc_info.value.detail


# ============================================================================
# App Access Control Tests
# ============================================================================


class TestAppAccessControl:
    """Tests for app-based access control."""

    def test_require_app_access_admin_bypasses(self):
        """Test that admin users bypass app access checks."""
        from auth import require_app_access

        admin_user = {
            "id": "admin-id",
            "email": "admin@test.com",
            "role": "admin",
            "client_id": None,
            "app_access": [],  # No explicit app access
        }

        checker = require_app_access(["disco"])

        # Admin should pass despite no app_access
        result = checker(admin_user)
        assert result == admin_user

    def test_require_app_access_all_access_bypasses(self):
        """Test that users with 'all' access bypass app checks."""
        from auth import require_app_access

        user = {
            "id": "user-id",
            "email": "user@test.com",
            "role": "user",
            "client_id": "client-1",
            "app_access": ["all"],
        }

        checker = require_app_access(["disco", "thesis"])

        result = checker(user)
        assert result == user

    def test_require_app_access_with_required_app(self):
        """Test that user with required app access passes."""
        from auth import require_app_access

        user = {
            "id": "user-id",
            "email": "user@test.com",
            "role": "user",
            "client_id": "client-1",
            "app_access": ["disco", "thesis"],
        }

        checker = require_app_access(["disco"])

        result = checker(user)
        assert result == user

    def test_require_app_access_without_required_app(self):
        """Test that user without required app access is denied."""
        from fastapi import HTTPException

        from auth import require_app_access

        user = {
            "id": "user-id",
            "email": "user@test.com",
            "role": "user",
            "client_id": "client-1",
            "app_access": ["thesis"],  # Only thesis, not disco
        }

        checker = require_app_access(["disco"])

        with pytest.raises(HTTPException) as exc_info:
            checker(user)

        assert exc_info.value.status_code == 403
        assert "disco" in exc_info.value.detail

    def test_require_app_access_with_any_of_multiple(self):
        """Test that having any one of multiple required apps passes."""
        from auth import require_app_access

        user = {
            "id": "user-id",
            "email": "user@test.com",
            "role": "user",
            "client_id": "client-1",
            "app_access": ["purdy"],  # Has purdy, not disco
        }

        # User needs disco OR purdy
        checker = require_app_access(["disco", "purdy"])

        result = checker(user)
        assert result == user


# ============================================================================
# Ownership Check Utility Tests
# ============================================================================


class TestOwnershipChecks:
    """Tests for ownership check utilities."""

    def test_check_owner_or_admin_admin_access(self):
        """Test that admin can access any resource."""
        from auth import check_owner_or_admin

        admin_user = {"id": "admin-id", "role": "admin"}

        # Should not raise even though admin doesn't own the resource
        check_owner_or_admin(admin_user, "other-user-id", "document")

    def test_check_owner_or_admin_owner_access(self):
        """Test that owner can access their own resource."""
        from auth import check_owner_or_admin

        user = {"id": "user-123", "role": "user"}

        # Should not raise - user owns the resource
        check_owner_or_admin(user, "user-123", "document")

    def test_check_owner_or_admin_non_owner_denied(self):
        """Test that non-owner is denied access."""
        from fastapi import HTTPException

        from auth import check_owner_or_admin

        user = {"id": "user-123", "role": "user"}

        with pytest.raises(HTTPException) as exc_info:
            check_owner_or_admin(user, "other-user-id", "document")

        assert exc_info.value.status_code == 403
        assert "document" in exc_info.value.detail

    def test_check_client_member_or_admin_admin_access(self):
        """Test that admin can access any client's resource."""
        from auth import check_client_member_or_admin

        admin_user = {"id": "admin-id", "role": "admin", "client_id": None}

        # Should not raise
        check_client_member_or_admin(admin_user, "any-client-id", "project")

    def test_check_client_member_or_admin_member_access(self):
        """Test that client member can access client resources."""
        from auth import check_client_member_or_admin

        user = {"id": "user-123", "role": "user", "client_id": "client-abc"}

        # Should not raise - user belongs to client
        check_client_member_or_admin(user, "client-abc", "project")

    def test_check_client_member_or_admin_non_member_denied(self):
        """Test that non-member is denied access to client resource."""
        from fastapi import HTTPException

        from auth import check_client_member_or_admin

        user = {"id": "user-123", "role": "user", "client_id": "client-abc"}

        with pytest.raises(HTTPException) as exc_info:
            check_client_member_or_admin(user, "different-client", "project")

        assert exc_info.value.status_code == 403
        assert "project" in exc_info.value.detail

    def test_check_self_or_admin_admin_access(self):
        """Test that admin can access any user's profile."""
        from auth import check_self_or_admin

        admin_user = {"id": "admin-id", "role": "admin"}

        # Should not raise
        check_self_or_admin(admin_user, "any-user-id")

    def test_check_self_or_admin_self_access(self):
        """Test that user can access their own profile."""
        from auth import check_self_or_admin

        user = {"id": "user-123", "role": "user"}

        # Should not raise
        check_self_or_admin(user, "user-123")

    def test_check_self_or_admin_other_user_denied(self):
        """Test that user cannot access another user's profile."""
        from fastapi import HTTPException

        from auth import check_self_or_admin

        user = {"id": "user-123", "role": "user"}

        with pytest.raises(HTTPException) as exc_info:
            check_self_or_admin(user, "other-user-id")

        assert exc_info.value.status_code == 403


# ============================================================================
# JWT Key Parsing Tests
# ============================================================================


class TestJWTKeyParsing:
    """Tests for JWT key parsing from various formats."""

    def test_parse_raw_secret(self):
        """Test parsing a raw HMAC secret."""
        from auth import _parse_jwt_key

        key, is_public, alg_family = _parse_jwt_key("my-secret-key")

        assert key == "my-secret-key"
        assert is_public is False
        assert alg_family == "HS"

    def test_parse_pem_key(self):
        """Test parsing a PEM-encoded key."""
        from auth import _parse_jwt_key

        pem_key = "-----BEGIN PUBLIC KEY-----\nMFkwEwYH...\n-----END PUBLIC KEY-----"

        key, is_public, alg_family = _parse_jwt_key(pem_key)

        assert key == pem_key
        assert is_public is True
        assert alg_family == "ES"

    def test_parse_jwk_ec_key(self):
        """Test parsing a JWK EC (elliptic curve) key."""
        from auth import _parse_jwt_key

        # Minimal EC JWK structure
        jwk = '{"kty":"EC","crv":"P-256","x":"test","y":"test"}'

        # This will fail to create a valid key but should detect it's a JWK
        key, is_public, alg_family = _parse_jwt_key(jwk)

        # On parse failure, falls back to raw secret
        # The important thing is it doesn't raise an exception
        assert key is not None

    def test_parse_invalid_json_jwk(self):
        """Test handling of invalid JSON that looks like JWK."""
        from auth import _parse_jwt_key

        invalid_jwk = "{not valid json"

        key, is_public, alg_family = _parse_jwt_key(invalid_jwk)

        # Should fall back to treating as raw secret
        assert key == invalid_jwk
        assert is_public is False
        assert alg_family == "HS"

    def test_key_cache_invalidation(self):
        """Test that key cache is invalidated when secret changes."""
        from auth import _get_parsed_jwt_key, _jwt_key_cache

        # Clear cache
        _jwt_key_cache.clear()

        with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "secret1"}):
            key1, _, _ = _get_parsed_jwt_key()
            assert _jwt_key_cache.get("secret") == "secret1"

        with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "secret2"}):
            key2, _, _ = _get_parsed_jwt_key()
            assert _jwt_key_cache.get("secret") == "secret2"

        assert key1 != key2


# ============================================================================
# Algorithm Mismatch Tests
# ============================================================================


class TestAlgorithmMismatch:
    """Tests for JWT algorithm mismatch handling."""

    def test_hs256_token_with_hs256_secret(self):
        """Test that HS256 token with HS256 secret works."""
        from auth import decode_jwt

        token = jwt.encode(
            {
                "sub": "user-123",
                "aud": "authenticated",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            os.environ["SUPABASE_JWT_SECRET"],
            algorithm="HS256",
        )

        payload = decode_jwt(token)

        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_none_algorithm_rejected(self):
        """Test that 'none' algorithm is rejected."""
        from auth import decode_jwt

        # Create unsigned token (alg: none) - security vulnerability if accepted
        token = jwt.encode(
            {
                "sub": "attacker",
                "aud": "authenticated",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "",  # No key for "none" algorithm
            algorithm="HS256",
        )
        # Manually tamper to use "none" algorithm
        parts = token.split(".")
        import base64

        header = base64.urlsafe_b64decode(parts[0] + "==")
        import json as json_module

        header_dict = json_module.loads(header)
        header_dict["alg"] = "none"
        new_header = (
            base64.urlsafe_b64encode(json_module.dumps(header_dict).encode()).rstrip(b"=").decode()
        )
        tampered_token = f"{new_header}.{parts[1]}."

        payload = decode_jwt(tampered_token)

        # Should be rejected
        assert payload is None
