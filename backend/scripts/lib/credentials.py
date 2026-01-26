"""
Shared credentials module for scripts.

This module provides a secure way to access credentials from environment
variables or 1Password instead of hardcoding them in scripts.

Usage:
    from scripts.lib.credentials import get_supabase_client, get_credentials

    # Get a configured Supabase client
    supabase = get_supabase_client()

    # Or get raw credentials
    creds = get_credentials()
    url = creds['supabase_url']

Priority:
    1. Environment variables (if set)
    2. 1Password CLI (if available and configured)
    3. .env file (fallback)
"""

import os
import subprocess
import sys
from pathlib import Path

# Ensure we can import from the backend root
backend_root = Path(__file__).parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

# Load environment variables from .env as fallback
from dotenv import load_dotenv
load_dotenv(backend_root / ".env")

# 1Password item reference
OP_ITEM_ID = "bqvwidzwtlswzndi5wjq33gon4"
OP_VAULT = "Employee"


def _get_from_1password(field_name: str) -> str | None:
    """Try to get a credential from 1Password CLI."""
    try:
        result = subprocess.run(
            ["op", "item", "get", OP_ITEM_ID, "--field", field_name, "--reveal"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _get_credential(env_var: str, op_field: str = None) -> str | None:
    """
    Get a credential with priority: 1Password (if enabled) > env var > .env.

    Args:
        env_var: Environment variable name
        op_field: 1Password field name (defaults to env_var)
    """
    # Try 1Password first if USE_1PASSWORD is set
    if os.getenv('USE_1PASSWORD', '').lower() in ('1', 'true', 'yes'):
        op_value = _get_from_1password(op_field or env_var)
        if op_value:
            return op_value

    # Fall back to environment variable
    value = os.getenv(env_var)
    # Skip dotenvx encrypted values (they start with "encrypted:")
    if value and not value.startswith('encrypted:'):
        return value

    return None


def get_credentials() -> dict:
    """
    Get all required credentials from environment variables.

    Returns:
        dict with keys: supabase_url, supabase_key, supabase_jwt_secret,
                       anthropic_api_key, voyage_api_key, neo4j_uri,
                       neo4j_username, neo4j_password

    Raises:
        ValueError if required credentials are missing
    """
    creds = {
        'supabase_url': _get_credential('SUPABASE_URL'),
        'supabase_key': _get_credential('SUPABASE_SERVICE_ROLE_KEY') or _get_credential('SUPABASE_KEY'),
        'supabase_jwt_secret': _get_credential('SUPABASE_JWT_SECRET'),
        'anthropic_api_key': _get_credential('ANTHROPIC_API_KEY'),
        'voyage_api_key': _get_credential('VOYAGE_API_KEY'),
        'neo4j_uri': _get_credential('NEO4J_URI'),
        'neo4j_username': _get_credential('NEO4J_USERNAME'),
        'neo4j_password': _get_credential('NEO4J_PASSWORD'),
        'mem0_api_key': _get_credential('MEM0_API_KEY'),
    }

    # Check for required Supabase credentials
    missing = []
    if not creds['supabase_url']:
        missing.append('SUPABASE_URL')
    if not creds['supabase_key']:
        missing.append('SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY')

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Make sure your .env file is configured or run with: dotenvx run -- python {sys.argv[0]}"
        )

    return creds


def get_supabase_client():
    """
    Get a configured Supabase client using environment credentials.

    Returns:
        supabase.Client instance
    """
    from supabase import create_client

    creds = get_credentials()
    return create_client(creds['supabase_url'], creds['supabase_key'])


def get_admin_token() -> str:
    """
    Generate an admin JWT token for API testing.

    Returns:
        JWT token string
    """
    import jwt
    from datetime import datetime, timezone, timedelta

    creds = get_credentials()
    secret = creds['supabase_jwt_secret']

    if not secret:
        raise ValueError("SUPABASE_JWT_SECRET not set in environment")

    # Create a token that expires in 1 hour
    payload = {
        'sub': 'admin-script-user',
        'role': 'service_role',
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
    }

    return jwt.encode(payload, secret, algorithm='HS256')
