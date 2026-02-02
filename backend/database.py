"""Centralized database connection management.
Provides singleton Supabase client to avoid connection pool exhaustion.
"""

import asyncio
import functools
import os
from typing import Callable, Optional, TypeVar

from logger_config import get_logger
from supabase import Client, create_client

logger = get_logger(__name__)

T = TypeVar("T")


class DatabaseService:
    """Singleton service for managing Supabase database connection."""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get the singleton Supabase client instance.

        Returns:
            Supabase Client instance

        Raises:
            ValueError: If SUPABASE_URL or SUPABASE_KEY not configured
        """
        if cls._instance is None:
            supabase_url = os.environ.get("SUPABASE_URL")
            # Prefer service role key for backend operations (bypasses RLS)
            # Fall back to SUPABASE_KEY for backwards compatibility
            supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get(
                "SUPABASE_KEY"
            )

            if not supabase_url or not supabase_key:
                raise ValueError(
                    "Supabase not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY)"
                )

            logger.info("Initializing Supabase database connection")
            cls._instance = create_client(supabase_url, supabase_key)

        return cls._instance

    @classmethod
    def reset_client(cls):
        """Reset the client instance. Useful for testing."""
        cls._instance = None


# Convenience function for getting the client
def get_supabase() -> Client:
    """Get the Supabase client instance.

    This is the preferred way to access the database throughout the application.

    Returns:
        Supabase Client instance
    """
    return DatabaseService.get_client()


def with_db_retry(max_retries: int = 2):
    """Decorator that retries database operations on connection errors.

    Handles "Broken pipe" and similar connection errors by resetting
    the Supabase client and retrying the operation.

    Args:
        max_retries: Maximum number of retry attempts (default 2)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (BrokenPipeError, ConnectionError, OSError) as e:
                    last_error = e
                    error_msg = str(e).lower()
                    # Check for connection-related errors
                    if (
                        "broken pipe" in error_msg
                        or "errno 32" in error_msg
                        or "connection" in error_msg
                    ):
                        if attempt < max_retries:
                            logger.warning(
                                f"Database connection error in {func.__name__}, "
                                f"resetting client and retrying (attempt {attempt + 1}/{max_retries}): {e}"
                            )
                            DatabaseService.reset_client()
                            await asyncio.sleep(0.1 * (attempt + 1))  # Brief backoff
                            continue
                    raise
                except Exception as e:
                    # Check if the error message indicates a broken pipe
                    error_msg = str(e).lower()
                    if "broken pipe" in error_msg or "errno 32" in error_msg:
                        last_error = e
                        if attempt < max_retries:
                            logger.warning(
                                f"Database connection error in {func.__name__}, "
                                f"resetting client and retrying (attempt {attempt + 1}/{max_retries}): {e}"
                            )
                            DatabaseService.reset_client()
                            await asyncio.sleep(0.1 * (attempt + 1))
                            continue
                    raise
            # If we exhausted all retries, raise the last error
            raise last_error  # type: ignore

        return wrapper

    return decorator
