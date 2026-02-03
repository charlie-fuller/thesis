"""Admin routes package - modular organization of admin endpoints."""

from fastapi import APIRouter

from . import analytics, cache, health, help_docs, stats, users_and_clients
from ._shared import limiter

# Create main router with prefix and tags
router = APIRouter(prefix="/api/admin", tags=["admin"])

# Include sub-routers
router.include_router(stats.router)
router.include_router(analytics.router)
router.include_router(users_and_clients.router)
router.include_router(health.router)
router.include_router(cache.router)
router.include_router(help_docs.router)

# Export shared utilities
__all__ = ["router", "limiter"]
