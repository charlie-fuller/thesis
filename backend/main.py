"""Thesis - Main Application Entry Point.

Multi-agent platform for enterprise GenAI strategy implementation.
Provides specialized agents for research (Atlas), finance (Capital),
IT/governance (Guardian), legal (Counselor), and transcript analysis (Oracle).
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Load environment variables BEFORE any other imports
load_dotenv()

from api.utils.error_handler import ThesisError, thesis_error_handler
from database import get_supabase
from errors import APIError, api_error_handler, generic_error_handler
from logger_config import get_logger, setup_logging

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Application Lifespan Context Manager
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    import asyncio

    # Startup — defer schedulers 30s so health check responds immediately
    async def _deferred_schedulers():
        await asyncio.sleep(30)
        logger.info("Starting deferred schedulers (30s post-startup)")

        # Start Atlas research scheduler
        try:
            from services.research_scheduler import start_research_scheduler

            start_research_scheduler(hour_utc=6, minute=0)
            logger.info("Atlas research scheduler started")
        except Exception as e:
            logger.error(f"Warning: Could not start research scheduler: {e}")

        # Start Knowledge Graph sync scheduler
        try:
            from services.graph_sync_scheduler import start_graph_sync_scheduler

            start_graph_sync_scheduler(hour_utc=3, minute=0)
            logger.info("Knowledge Graph sync scheduler started")
        except Exception as e:
            logger.error(f"Warning: Could not start graph sync scheduler: {e}")

        # Start Stakeholder Engagement scheduler (weekly)
        try:
            from services.engagement_scheduler import start_engagement_scheduler

            start_engagement_scheduler(day_of_week="sun", hour_utc=4, minute=0)
            logger.info("Stakeholder engagement scheduler started")
        except Exception as e:
            logger.error(f"Warning: Could not start engagement scheduler: {e}")

        # Start Manifesto Compliance Digest scheduler (weekly)
        try:
            from services.manifesto_digest_scheduler import start_manifesto_digest_scheduler

            start_manifesto_digest_scheduler(day_of_week="mon", hour_utc=7, minute=0)
            logger.info("Manifesto compliance digest scheduler started")
        except Exception as e:
            logger.error(f"Warning: Could not start manifesto digest scheduler: {e}")

        # Start Discovery Inbox scan scheduler (daily)
        try:
            from services.discovery_scan_scheduler import start_discovery_scan_scheduler

            start_discovery_scan_scheduler(hour_utc=5, minute=0)
            logger.info("Discovery scan scheduler started")
        except Exception as e:
            logger.error(f"Warning: Could not start discovery scan scheduler: {e}")

        logger.info("All deferred schedulers started")

    # Vault watcher deferred 60s (heaviest startup task — initial_sync disabled)
    async def _deferred_vault_watcher():
        await asyncio.sleep(60)
        try:
            from services.vault_watcher_scheduler import start_vault_watcher

            if start_vault_watcher(initial_sync=False):
                logger.info("Vault watcher started (60s deferred, no initial sync)")
        except Exception as e:
            logger.error(f"Warning: Could not start vault watcher: {e}")

    asyncio.create_task(_deferred_schedulers())
    asyncio.create_task(_deferred_vault_watcher())

    logger.info("Application startup complete (schedulers deferred 30s)")

    yield  # Application is running

    # Shutdown
    try:
        from services.research_scheduler import stop_research_scheduler

        stop_research_scheduler()
    except Exception as e:
        logger.error(f"Warning during research scheduler shutdown: {e}")

    try:
        from services.graph_sync_scheduler import stop_graph_sync_scheduler

        stop_graph_sync_scheduler()
    except Exception as e:
        logger.error(f"Warning during graph sync scheduler shutdown: {e}")

    try:
        from services.engagement_scheduler import stop_engagement_scheduler

        stop_engagement_scheduler()
    except Exception as e:
        logger.error(f"Warning during engagement scheduler shutdown: {e}")

    try:
        from services.manifesto_digest_scheduler import stop_manifesto_digest_scheduler

        stop_manifesto_digest_scheduler()
    except Exception as e:
        logger.error(f"Warning during manifesto digest scheduler shutdown: {e}")

    try:
        from services.discovery_scan_scheduler import stop_discovery_scan_scheduler

        stop_discovery_scan_scheduler()
    except Exception as e:
        logger.error(f"Warning during discovery scan scheduler shutdown: {e}")

    try:
        from services.vault_watcher_scheduler import stop_vault_watcher

        stop_vault_watcher()
    except Exception as e:
        logger.error(f"Warning during vault watcher shutdown: {e}")

    try:
        from services.graph import close_neo4j_connection

        await close_neo4j_connection()
        logger.info("Neo4j connection closed")
    except Exception as e:
        logger.error(f"Warning during Neo4j shutdown: {e}")

    logger.info("Application shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Thesis API",
    description=(
        "Multi-agent platform for enterprise GenAI strategy - "
        "Research, Finance, IT/Governance, Legal, and Transcript Analysis agents"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure app state
app.state.limiter = limiter

# Register exception handlers (order matters - more specific first)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(ThesisError, thesis_error_handler)
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# ============================================================================
# CORS Configuration
# ============================================================================

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Local development origins (only allowed in non-production environments)
LOCAL_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
]

# Check if running in production
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()


# Parse and normalize origins (ensure all have https:// prefix)
def normalize_origin(origin: str) -> str:
    """Ensure origin has proper https:// prefix."""
    origin = origin.strip()
    if origin and not origin.startswith(("http://", "https://")):
        origin = f"https://{origin}"
    return origin


allowed_origins = [normalize_origin(origin) for origin in FRONTEND_URL.split(",")]

# Always include production Vercel frontends
production_origins = [
    "https://thesis.vercel.app",
    "https://thesis-woad.vercel.app",
    "https://thesis-mvp.vercel.app",
]
for origin in production_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

# Only include local dev origins in non-production environments
if ENVIRONMENT != "production":
    for origin in LOCAL_DEV_ORIGINS:
        if origin not in allowed_origins:
            allowed_origins.append(origin)
else:
    logger.info("Production environment: localhost origins disabled")

# Log configured origins for debugging
logger.info(f"CORS allowed origins: {allowed_origins}")


# ============================================================================
# Custom CORS Middleware (handles CORS before anything else)
# ============================================================================


class CustomCORSMiddleware:
    """Pure ASGI CORS middleware that handles preflight requests directly.

    This ensures CORS headers are always added, even when exceptions occur.

    Note: Using pure ASGI instead of BaseHTTPMiddleware to avoid
    event loop issues with async resources (Neo4j, etc.).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info from scope
        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin", b"").decode("utf-8")
        path = scope.get("path", "")
        method = scope.get("method", "")

        # Log all incoming requests for debugging
        logger.debug(f"CORS middleware: {method} {path} from origin: '{origin}'")

        # Check if origin is allowed
        is_allowed = origin in allowed_origins
        logger.debug(f"CORS origin allowed: {is_allowed}")

        # Handle preflight OPTIONS requests
        if method == "OPTIONS":
            if is_allowed:
                logger.debug(f"CORS preflight ALLOWED for {path} from {origin}")
                response = Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": (
                            "Authorization, Content-Type, Accept, X-Requested-With, X-Request-ID"
                        ),
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Max-Age": "86400",
                    },
                )
            else:
                logger.warning(f"CORS preflight REJECTED for {path} - origin '{origin}' not in allowed list")
                response = Response(status_code=403, content="CORS not allowed")

            await response(scope, receive, send)
            return

        # For non-OPTIONS requests, wrap send to add CORS headers
        async def send_with_cors(message):
            if message["type"] == "http.response.start" and is_allowed and origin:
                # Add CORS headers to the response
                headers = list(message.get("headers", []))
                headers.append((b"access-control-allow-origin", origin.encode()))
                headers.append((b"access-control-allow-credentials", b"true"))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_cors)
        except Exception as e:
            logger.error(f"CORS middleware caught exception: {e}")
            # Return error with CORS headers
            error_headers = []
            if is_allowed and origin:
                error_headers = [
                    (b"access-control-allow-origin", origin.encode()),
                    (b"access-control-allow-credentials", b"true"),
                ]
            response = Response(
                status_code=500,
                content=str(e),
                headers={h[0].decode(): h[1].decode() for h in error_headers},
            )
            await response(scope, receive, send)


# Add custom CORS middleware (added last = runs first due to LIFO)
app.add_middleware(CustomCORSMiddleware)


# ============================================================================
# HTTPS Redirect Fix Middleware
# ============================================================================
# Fly.io/proxies terminate TLS and forward requests as HTTP internally.
# FastAPI's trailing-slash redirects use the internal HTTP scheme, causing
# mixed content errors. This middleware intercepts redirects and fixes the scheme.


class HTTPSRedirectFixMiddleware:
    """Fix redirect URLs to use HTTPS when behind a proxy."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status = message.get("status", 200)
                # Fix redirects (301, 302, 307, 308)
                if status in (301, 302, 307, 308):
                    headers = list(message.get("headers", []))
                    new_headers = []
                    for name, value in headers:
                        if name.lower() == b"location":
                            location = value.decode("utf-8")
                            # Replace http:// with https:// for production URLs behind proxy
                            if location.startswith("http://") and (
                                "fly.dev" in location or "vercel.app" in location
                            ):
                                location = location.replace("http://", "https://", 1)
                                value = location.encode("utf-8")
                        new_headers.append((name, value))
                    message = {**message, "headers": new_headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)


# Add HTTPS redirect fix middleware (runs after CORS)
app.add_middleware(HTTPSRedirectFixMiddleware)


# ============================================================================
# Request ID Middleware for Correlation
# ============================================================================


class RequestIDMiddleware:
    """Add unique request ID for tracing and correlation.

    Generates a unique ID for each request that can be used to correlate
    logs across the request lifecycle. The ID is:
    - Generated for each request (or taken from X-Request-ID header if provided)
    - Stored in request.state.request_id
    - Returned in X-Request-ID response header
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        import uuid

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get or generate request ID
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode("utf-8")
        if not request_id:
            request_id = str(uuid.uuid4())[:8]  # Short ID for readability

        # Store in scope for later access
        scope["state"] = scope.get("state", {})
        scope["state"]["request_id"] = request_id

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_request_id)


# Add request ID middleware (runs after HTTPS fix)
app.add_middleware(RequestIDMiddleware)

# Initialize Supabase connection
supabase = get_supabase()

# ============================================================================
# Import and Register Route Modules
# ============================================================================

# Import all route modules
from api.routes import (
    admin,
    agents,
    chat,
    clients,
    command,
    compass,
    strategy,
    conversations,
    digest,
    disco,
    discovery,
    document_mappings,
    documents,
    entity_corrections,
    entity_registry,
    glean_connectors,
    graph,
    help_chat,
    images,
    meeting_prep,
    meeting_rooms,
    obsidian_sync,
    pipeline,
    portfolio,
    projects,
    research,
    stakeholder_metrics,
    stakeholders,
    system_instructions,
    tasks,
    theme,
    transcripts,
    users,
)

# Register routers
app.include_router(agents.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(documents.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(document_mappings.router)
app.include_router(clients.router)
app.include_router(theme.router)
app.include_router(images.router)
app.include_router(help_chat.router)
app.include_router(system_instructions.router)
app.include_router(transcripts.router)
app.include_router(stakeholders.router)
app.include_router(graph.router)
app.include_router(meeting_rooms.router)
app.include_router(research.router)
app.include_router(projects.router)
app.include_router(glean_connectors.router)
app.include_router(discovery.router)
app.include_router(stakeholder_metrics.router)
app.include_router(meeting_prep.router)
app.include_router(tasks.router)
app.include_router(obsidian_sync.router)
app.include_router(compass.router)
app.include_router(digest.router)
app.include_router(pipeline.router)
app.include_router(disco.router)
app.include_router(entity_registry.router)
app.include_router(entity_corrections.router)
app.include_router(command.router)
app.include_router(strategy.router)
app.include_router(portfolio.router)

logger.info(
    "All route modules registered (including Thesis multi-agent, graph, meeting room, "
    "research, Glean connector, project-triage, task management, Obsidian sync, "
    "Compass, Digest, Pipeline, DISCo, and Entity Validation routes)"
)

# ============================================================================
# Backward Compatibility Routes
# ============================================================================

import asyncio

from fastapi import Depends, HTTPException

from auth import get_current_user
from validation import validate_uuid


@app.get("/api/clients/{client_id}/conversations")
async def list_client_conversations(
    client_id: str, include_archived: bool = False, current_user: dict = Depends(get_current_user)
):
    """List all conversations for a client (backward compatibility)."""
    try:
        validate_uuid(client_id, "client_id")

        query = supabase.table("conversations").select("*").eq("client_id", client_id)

        if not include_archived:
            query = query.eq("archived", False)

        result = await asyncio.to_thread(lambda: query.order("updated_at", desc=True).execute())

        return {"success": True, "conversations": result.data}

    except Exception as e:
        logger.error(f"❌ Error listing client conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@app.get("/api/users/me/storage")
async def get_user_storage(current_user: dict = Depends(get_current_user)):
    """Get user storage info (backward compatibility - forwards to documents router)."""
    try:
        # Query user storage from database
        result = await asyncio.to_thread(
            lambda: supabase.table("users")
            .select("storage_used, storage_quota")
            .eq("id", current_user["id"])
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        storage_quota = result.data.get("storage_quota") or 524288000  # 500MB default
        storage_used = result.data.get("storage_used") or 0

        return {
            "success": True,
            "storage_quota": storage_quota,
            "storage_used": storage_used,
            "storage_available": max(0, storage_quota - storage_used),
            "usage_percentage": round((storage_used / storage_quota * 100), 2) if storage_quota > 0 else 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching storage data: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@app.get("/api/users/me/documents")
async def get_user_documents(current_user: dict = Depends(get_current_user)):
    """Get user documents (backward compatibility - forwards to documents router)."""
    try:
        # Query user's documents from database
        result = await asyncio.to_thread(
            lambda: supabase.table("documents")
            .select("*")
            .eq("uploaded_by", current_user["id"])
            .order("uploaded_at", desc=True)
            .execute()
        )

        return {"success": True, "documents": result.data, "count": len(result.data)}

    except Exception as e:
        logger.error(f"❌ Error fetching user documents: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


# ============================================================================
# Core Health Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint - API status."""
    return {
        "message": "Thesis API is running",
        "version": "1.0.1",
        "status": "healthy",
        "deploy_marker": "2026-03-13-flyio-railway-cleanup",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        supabase.table("users").select("id").limit(1).execute()

        return {"status": "healthy", "database": "connected", "version": "1.0.0"}
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# ============================================================================
# Application Information
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
