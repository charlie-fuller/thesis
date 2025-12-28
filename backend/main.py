"""
Thesis - Main Application Entry Point

Multi-agent platform for enterprise GenAI strategy implementation.
Provides specialized agents for research (Atlas), finance (Fortuna),
IT/governance (Guardian), legal (Counselor), and transcript analysis (Oracle).
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

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

# Initialize FastAPI app
app = FastAPI(
    title="Thesis API",
    description="Multi-agent platform for enterprise GenAI strategy - Research, Finance, IT/Governance, Legal, and Transcript Analysis agents",
    version="1.0.0"
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

# Local development origins (always allowed in dev)
LOCAL_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
]

# Parse and normalize origins (ensure all have https:// prefix)
def normalize_origin(origin: str) -> str:
    """Ensure origin has proper https:// prefix"""
    origin = origin.strip()
    if origin and not origin.startswith(('http://', 'https://')):
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

# Always include local dev origins
for origin in LOCAL_DEV_ORIGINS:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

# Log configured origins for debugging
logger.info(f"CORS allowed origins: {allowed_origins}")


# ============================================================================
# Custom CORS Middleware (handles CORS before anything else)
# ============================================================================

class CustomCORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware that handles preflight requests directly.
    This ensures CORS headers are always added, even when exceptions occur.
    """

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        path = request.url.path
        method = request.method

        # Log all incoming requests for debugging
        logger.info(f"CORS middleware: {method} {path} from origin: '{origin}'")

        # Check if origin is allowed
        is_allowed = origin in allowed_origins
        logger.info(f"CORS origin allowed: {is_allowed}")

        # Handle preflight OPTIONS requests
        if method == "OPTIONS":
            if is_allowed:
                logger.info(f"CORS preflight ALLOWED for {path} from {origin}")
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, X-Requested-With, X-Request-ID",
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Max-Age": "86400",
                    }
                )
            else:
                logger.warning(f"CORS preflight REJECTED for {path} - origin '{origin}' not in allowed list")
                return Response(status_code=403, content="CORS not allowed")

        # For non-OPTIONS requests, proceed and add CORS headers to response
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"CORS middleware caught exception: {e}")
            # Return error with CORS headers
            response = Response(
                status_code=500,
                content=str(e),
            )

        if is_allowed and origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


# Add custom CORS middleware (added last = runs first due to LIFO)
app.add_middleware(CustomCORSMiddleware)

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
    conversations,
    document_mappings,
    documents,
    google_drive,
    graph,
    help_chat,
    images,
    meeting_rooms,
    notion,
    projects,
    quick_prompts,
    research,
    stakeholders,
    system_instructions,
    templates,
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
app.include_router(google_drive.router)
app.include_router(notion.router)
app.include_router(admin.router)
app.include_router(document_mappings.router)
app.include_router(clients.router)
app.include_router(quick_prompts.router)
app.include_router(theme.router)
app.include_router(images.router)
app.include_router(help_chat.router)
app.include_router(templates.router)
app.include_router(projects.router)
app.include_router(system_instructions.router)
app.include_router(transcripts.router)
app.include_router(stakeholders.router)
app.include_router(graph.router)
app.include_router(meeting_rooms.router)
app.include_router(research.router)

logger.info("✅ All route modules registered (including Thesis multi-agent, graph, meeting room, and research routes)")

# ============================================================================
# Backward Compatibility Routes
# ============================================================================

import asyncio

from fastapi import Depends, HTTPException

from auth import get_current_user
from validation import validate_uuid


@app.get("/api/clients/{client_id}/conversations")
async def list_client_conversations(
    client_id: str,
    include_archived: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """List all conversations for a client (backward compatibility)"""
    try:
        validate_uuid(client_id, "client_id")

        query = supabase.table('conversations')\
            .select('*')\
            .eq('client_id', client_id)

        if not include_archived:
            query = query.eq('archived', False)

        result = await asyncio.to_thread(
            lambda: query.order('updated_at', desc=True).execute()
        )

        return {
            'success': True,
            'conversations': result.data
        }

    except Exception as e:
        logger.error(f"❌ Error listing client conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/me/storage")
async def get_user_storage(
    current_user: dict = Depends(get_current_user)
):
    """Get user storage info (backward compatibility - forwards to documents router)"""
    try:
        # Query user storage from database
        result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .select('storage_used, storage_quota')\
                .eq('id', current_user['id'])\
                .single()\
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        storage_quota = result.data.get('storage_quota') or 524288000  # 500MB default
        storage_used = result.data.get('storage_used') or 0

        return {
            'success': True,
            'storage_quota': storage_quota,
            'storage_used': storage_used,
            'storage_available': max(0, storage_quota - storage_used),
            'usage_percentage': round((storage_used / storage_quota * 100), 2) if storage_quota > 0 else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching storage data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/me/documents")
async def get_user_documents(
    current_user: dict = Depends(get_current_user)
):
    """Get user documents (backward compatibility - forwards to documents router)"""
    try:
        # Query user's documents from database
        result = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('*')\
                .eq('uploaded_by', current_user['id'])\
                .order('uploaded_at', desc=True)\
                .execute()
        )

        return {
            'success': True,
            'documents': result.data,
            'count': len(result.data)
        }

    except Exception as e:
        logger.error(f"❌ Error fetching user documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Application Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    # Start Google Drive sync scheduler
    try:
        from services.sync_scheduler import start_scheduler
        # Start the Google Drive sync scheduler (checks every 5 minutes)
        start_scheduler(check_interval_minutes=5)
        logger.info("✅ Google Drive sync scheduler started")
    except Exception as e:
        logger.error(f"⚠️ Warning: Could not start sync scheduler: {e}")

    # Start Atlas research scheduler
    try:
        from services.research_scheduler import start_research_scheduler
        # Start the research scheduler (runs daily at 6 AM UTC)
        start_research_scheduler(hour_utc=6, minute=0)
        logger.info("✅ Atlas research scheduler started")
    except Exception as e:
        logger.error(f"⚠️ Warning: Could not start research scheduler: {e}")

    logger.info("✅ Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        from services.sync_scheduler import stop_scheduler
        stop_scheduler()
    except Exception as e:
        logger.error(f"⚠️ Warning during sync scheduler shutdown: {e}")

    try:
        from services.research_scheduler import stop_research_scheduler
        stop_research_scheduler()
    except Exception as e:
        logger.error(f"⚠️ Warning during research scheduler shutdown: {e}")

    try:
        from services.graph import close_neo4j_connection
        await close_neo4j_connection()
        logger.info("✅ Neo4j connection closed")
    except Exception as e:
        logger.error(f"⚠️ Warning during Neo4j shutdown: {e}")

    logger.info("✅ Application shutdown complete")


# ============================================================================
# Core Health Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "Thesis API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        supabase.table('users').select('id').limit(1).execute()

        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ============================================================================
# Application Information
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
