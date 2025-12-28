from logger_config import get_logger

logger = get_logger(__name__)

"""
Authentication utilities for JWT validation
"""

import os
from typing import Optional

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

# Security scheme for Bearer token
security = HTTPBearer()

# Supabase JWT secret (from environment)
# For HS256: Use the JWT secret directly
# For ES256: Use the JWT public key (PEM format)
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', '')

if not SUPABASE_JWT_SECRET:
    logger.warning("SUPABASE_JWT_SECRET not set in environment variables")

# Check if it's a PEM-encoded public key (for ES256)
# Public keys start with "-----BEGIN PUBLIC KEY-----"
IS_PUBLIC_KEY = SUPABASE_JWT_SECRET.strip().startswith('-----BEGIN')


def decode_jwt(token: str) -> Optional[dict]:
    """
    Decode and validate a Supabase JWT token

    Args:
        token: The JWT token string

    Returns:
        dict: Decoded token payload if valid, None otherwise
    """
    if not SUPABASE_JWT_SECRET:
        logger.error("JWT validation failed: SUPABASE_JWT_SECRET is not set")
        return None

    try:
        # First, peek at the token header to see what algorithm is used
        unverified_header = jwt.get_unverified_header(token)
        token_alg = unverified_header.get('alg', 'HS256')
        logger.info(f"JWT token algorithm: {token_alg}")

        # Determine allowed algorithms based on what we have configured
        if IS_PUBLIC_KEY:
            # We have a public key, allow ECDSA algorithms
            allowed_algorithms = ['ES256', 'ES384', 'ES512']
        else:
            # We have a secret, allow HMAC algorithms
            allowed_algorithms = ['HS256', 'HS384', 'HS512']

        if token_alg not in allowed_algorithms:
            if token_alg in ['ES256', 'ES384', 'ES512'] and not IS_PUBLIC_KEY:
                logger.error(
                    f"JWT uses {token_alg} but SUPABASE_JWT_SECRET is not a public key. "
                    "For ES256, use the JWT public key from Supabase Dashboard -> Settings -> API -> JWT Settings."
                )
            elif token_alg in ['HS256', 'HS384', 'HS512'] and IS_PUBLIC_KEY:
                logger.error(
                    f"JWT uses {token_alg} but SUPABASE_JWT_SECRET is a public key. "
                    "For HS256, use the JWT secret from Supabase Dashboard -> Settings -> API."
                )
            else:
                logger.error(f"JWT validation error: Unsupported algorithm {token_alg}")
            return None

        # Decode the JWT token
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=allowed_algorithms,
            audience='authenticated'  # Supabase default audience
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("JWT validation error: Token has expired")
        return None
    except jwt.InvalidAudienceError:
        logger.error("JWT validation error: Invalid audience claim")
        return None
    except jwt.InvalidSignatureError:
        logger.error("JWT validation error: Signature verification failed - check SUPABASE_JWT_SECRET")
        return None
    except PyJWTError as e:
        logger.error(f"JWT validation error: {type(e).__name__}: {e}")
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Dependency to get the current authenticated user from JWT token

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

    user_id = payload.get('sub')

    # Fetch user role and client_id from database using centralized connection
    try:
        supabase = get_supabase()
        user_result = supabase.table('users').select('role, client_id').eq('id', user_id).single().execute()
        user_role = user_result.data.get('role', 'user') if user_result.data else 'user'
        user_client_id = user_result.data.get('client_id') if user_result.data else None
    except Exception as e:
        logger.info(f"Warning: Could not fetch user data from database: {e}")
        user_role = 'user'
        user_client_id = None

    return {
        'id': user_id,
        'email': payload.get('email'),
        'role': user_role,
        'client_id': user_client_id,
    }


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[dict]:
    """
    Optional authentication - doesn't raise error if no token

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

    user_id = payload.get('sub')

    # Fetch user role and client_id from database using centralized connection
    try:
        supabase = get_supabase()
        user_result = supabase.table('users').select('role, client_id').eq('id', user_id).single().execute()
        user_role = user_result.data.get('role', 'user') if user_result.data else 'user'
        user_client_id = user_result.data.get('client_id') if user_result.data else None
    except Exception as e:
        logger.info(f"Warning: Could not fetch user data from database: {e}")
        user_role = 'user'
        user_client_id = None

    return {
        'id': user_id,
        'email': payload.get('email'),
        'role': user_role,
        'client_id': user_client_id,
    }


def require_role(allowed_roles: list):
    """
    Dependency factory to require specific roles

    Args:
        allowed_roles: List of allowed role names

    Returns:
        Function that checks if user has required role
    """
    def role_checker(current_user: dict = Security(get_current_user)) -> dict:
        # For now, fetch user role from database
        # In future, we could include role in JWT payload
        user_role = current_user.get('role', 'user')

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )

        return current_user

    return role_checker


# Convenience dependencies for common role checks
require_admin = require_role(['admin'])
# Note: In single-tenant mode, client_admin role is deprecated
# For backward compatibility, require_client_admin now just requires 'admin'
require_client_admin = require_role(['admin'])
