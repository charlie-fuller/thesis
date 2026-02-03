"""Shared utilities for admin routes."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)
supabase = get_supabase()
