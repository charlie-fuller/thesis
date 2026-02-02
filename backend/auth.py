from logger_config import get_logger

logger = get_logger(__name__)

"""
Authentication utilities for JWT validation
"""

import json
import os
from typing import Optional

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

# Security scheme for Bearer token
security = HTTPBearer()


def _get_jwt_secret() -> str:
    """Get JWT secret fresh from environment (allows dynamic override)."""
    return os.getenv("SUPABASE_JWT_SECRET", "")


def _parse_jwt_key(key_data: str):
    """Parse JWT key from various formats (PEM, JWK, or raw secret).
    Returns tuple of (key, is_public_key, algorithm_family).
    """
    key_data = key_data.strip()

    # Check if it's a PEM-encoded key
    if key_data.startswith("-----BEGIN"):
        return key_data, True, "ES"

    # Check if it's a JWK (JSON format)
    if key_data.startswith("{"):
        try:
            jwk_dict = json.loads(key_data)
            # Use PyJWT's JWK support to load the key
            from jwt import PyJWK

            jwk = PyJWK.from_dict(jwk_dict)
            alg_family = "ES" if jwk_dict.get("kty") == "EC" else "HS"
            return jwk.key, True, alg_family
        except Exception as e:
            logger.error(f"Failed to parse JWK: {e}")
            return key_data, False, "HS"

    # Otherwise, treat as raw HMAC secret
    return key_data, False, "HS"


# Cache for parsed key (lazy initialization)
_jwt_key_cache = {}


def _get_parsed_jwt_key():
    """Get parsed JWT key with lazy initialization and cache invalidation on secret change."""
    secret = _get_jwt_secret()
    if not secret:
        return None, False, "HS"

    # Check if cached key is still valid
    if _jwt_key_cache.get("secret") != secret:
        key, is_public, alg_family = _parse_jwt_key(secret)
        _jwt_key_cache["secret"] = secret
        _jwt_key_cache["key"] = key
        _jwt_key_cache["is_public"] = is_public
        _jwt_key_cache["alg_family"] = alg_family

    return _jwt_key_cache["key"], _jwt_key_cache["is_public"], _jwt_key_cache["alg_family"]


def decode_jwt(token: str) -> Optional[dict]:
    """Decode and validate a Supabase JWT token.

    Args:
        token: The JWT token string

    Returns:
        dict: Decoded token payload if valid, None otherwise
    """
    jwt_secret = _get_jwt_secret()
    if not jwt_secret:
        logger.error("JWT validation failed: SUPABASE_JWT_SECRET is not set")
        return None

    # Get parsed key (with caching)
    jwt_key, is_public_key, key_alg_family = _get_parsed_jwt_key()

    try:
        # First, peek at the token header to see what algorithm is used
        unverified_header = jwt.get_unverified_header(token)
        token_alg = unverified_header.get("alg", "HS256")
        logger.info(f"JWT token algorithm: {token_alg}")

        # Determine allowed algorithms based on what key type we have
        if key_alg_family == "ES":
            allowed_algorithms = ["ES256", "ES384", "ES512"]
        else:
            allowed_algorithms = ["HS256", "HS384", "HS512"]

        if token_alg not in allowed_algorithms:
            if token_alg.startswith("ES") and key_alg_family != "ES":
                logger.error(
                    f"JWT uses {token_alg} but SUPABASE_JWT_SECRET is not a public key. "
                    "For ES256, use the JWT Signing Key (JWK format) from Supabase Dashboard -> Settings -> API -> JWT Settings."
                )
            elif token_alg.startswith("HS") and key_alg_family == "ES":
                logger.error(
                    f"JWT uses {token_alg} but SUPABASE_JWT_SECRET is a public key. "
                    "For HS256, use the JWT secret from Supabase Dashboard -> Settings -> API."
                )
            else:
                logger.error(f"JWT validation error: Unsupported algorithm {token_alg}")
            return None

        # Decode the JWT token using the parsed key
        payload = jwt.decode(
            token,
            jwt_key,
            algorithms=allowed_algorithms,
            audience="authenticated",  # Supabase default audience
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("JWT validation error: Token has expired")
        return None
    except jwt.InvalidAudienceError:
        logger.error("JWT validation error: Invalid audience claim")
        return None
    except jwt.InvalidSignatureError:
        logger.error(
            "JWT validation error: Signature verification failed - check SUPABASE_JWT_SECRET"
        )
        return None
    except PyJWTError as e:
        logger.error(f"JWT validation error: {type(e).__name__}: {e}")
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        dict: User information from JWT payload + role and client_id from database

    Raises:
        HTTPException: If token is invalid or missing
    """
    from database import get_supabase

    token = credentials.credentials
    payload = decode_jwt(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")

    # Fetch user role, client_id, and app_access from database using centralized connection
    try:
        supabase = get_supabase()
        user_result = (
            supabase.table("users")
            .select("role, client_id, app_access")
            .eq("id", user_id)
            .single()
            .execute()
        )
        user_role = user_result.data.get("role", "user") if user_result.data else "user"
        user_client_id = user_result.data.get("client_id") if user_result.data else None
        user_app_access = user_result.data.get("app_access") if user_result.data else ["thesis"]
    except Exception as e:
        logger.info(f"Warning: Could not fetch user data from database: {e}")
        user_role = "user"
        user_client_id = None
        user_app_access = ["thesis"]

    return {
        "id": user_id,
        "email": payload.get("email"),
        "role": user_role,
        "client_id": user_client_id,
        "app_access": user_app_access or ["thesis"],
    }


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Optional[dict]:
    """Optional authentication - doesn't raise error if no token.

    Args:
        credentials: HTTP Bearer credentials (optional)

    Returns:
        dict or None: User information if authenticated, None otherwise
    """
    from database import get_supabase

    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_jwt(token)

    if not payload:
        return None

    user_id = payload.get("sub")

    # Fetch user role, client_id, and app_access from database using centralized connection
    try:
        supabase = get_supabase()
        user_result = (
            supabase.table("users")
            .select("role, client_id, app_access")
            .eq("id", user_id)
            .single()
            .execute()
        )
        user_role = user_result.data.get("role", "user") if user_result.data else "user"
        user_client_id = user_result.data.get("client_id") if user_result.data else None
        user_app_access = user_result.data.get("app_access") if user_result.data else ["thesis"]
    except Exception as e:
        logger.info(f"Warning: Could not fetch user data from database: {e}")
        user_role = "user"
        user_client_id = None
        user_app_access = ["thesis"]

    return {
        "id": user_id,
        "email": payload.get("email"),
        "role": user_role,
        "client_id": user_client_id,
        "app_access": user_app_access or ["thesis"],
    }


def require_role(allowed_roles: list):
    """Dependency factory to require specific roles.

    Args:
        allowed_roles: List of allowed role names

    Returns:
        Function that checks if user has required role
    """

    def role_checker(current_user: dict = Security(get_current_user)) -> dict:
        # For now, fetch user role from database
        # In future, we could include role in JWT payload
        user_role = current_user.get("role", "user")

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403, detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )

        return current_user

    return role_checker


# Convenience dependencies for common role checks
require_admin = require_role(["admin"])
# Note: In single-tenant mode, client_admin role is deprecated
# For backward compatibility, require_client_admin now just requires 'admin'
require_client_admin = require_role(["admin"])


def require_app_access(required_apps: list):
    """Dependency factory to require access to specific apps.

    Args:
        required_apps: List of required app names (e.g., ['disco', 'thesis'])

    Returns:
        Function that checks if user has required app access
    """

    def app_access_checker(current_user: dict = Security(get_current_user)) -> dict:
        user_role = current_user.get("role", "user")
        user_app_access = current_user.get("app_access", ["thesis"])

        # Admins have access to everything
        if user_role == "admin":
            return current_user

        # Check if user has 'all' access
        if "all" in user_app_access:
            return current_user

        # Check if user has any of the required apps
        has_access = any(app in user_app_access for app in required_apps)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required app access: {', '.join(required_apps)}",
            )

        return current_user

    return app_access_checker


# Convenience dependencies for common app access checks
require_disco_access = require_app_access(["disco", "purdy"])  # purdy for legacy compatibility
require_thesis_access = require_app_access(["thesis"])
