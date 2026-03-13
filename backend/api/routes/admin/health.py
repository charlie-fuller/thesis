"""Admin health routes - system health checks."""

import asyncio
import os
import time

from fastapi import APIRouter, Depends, HTTPException

from auth import require_admin
from logger_config import get_logger

from ._shared import supabase

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def get_system_health(current_user: dict = Depends(require_admin)):
    """Get real-time system health metrics for admin dashboard.

    Args:
        current_user: Injected by FastAPI dependency.
    """
    try:
        health_data = {
            "supabase": {"status": "checking", "responseTime": 0},
            "backend": {"status": "running"},
            "anthropic": {"status": "checking", "latency": 0},
            "voyageAI": {"status": "checking", "latency": 0},
            "neo4j": {"status": "checking", "responseTime": 0},
        }

        db_time = 0

        # 1. Check Supabase (Database) Health
        try:
            db_start = time.time()
            await asyncio.to_thread(lambda: supabase.table("users").select("id", count="exact").limit(1).execute())
            db_time = round((time.time() - db_start) * 1000)
            health_data["supabase"] = {"status": "connected", "responseTime": db_time}
        except Exception as e:
            logger.error(f"Supabase health check failed: {str(e)}")
            health_data["supabase"] = {"status": "error", "responseTime": 0}

        # 2. Backend API - If this endpoint is responding, the backend is running
        health_data["backend"] = {"status": "running", "uptime": True}

        # 3. Check Anthropic (Claude) - Make a real API call to verify connectivity
        try:
            import anthropic

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                health_data["anthropic"] = {"status": "not_configured", "latency": 0}
            else:
                anthropic_start = time.time()
                client = anthropic.Anthropic(api_key=api_key)
                await asyncio.to_thread(
                    lambda: client.messages.count_tokens(
                        model="claude-sonnet-4-20250514",
                        messages=[{"role": "user", "content": "health check"}],
                    )
                )
                anthropic_latency = round(time.time() - anthropic_start, 2)
                health_data["anthropic"] = {"status": "connected", "latency": anthropic_latency}
        except anthropic.AuthenticationError:
            logger.error("Anthropic authentication failed - invalid API key")
            health_data["anthropic"] = {"status": "auth_error", "latency": 0}
        except anthropic.RateLimitError:
            health_data["anthropic"] = {"status": "rate_limited", "latency": 0}
        except Exception as e:
            logger.error(f"Anthropic health check failed: {str(e)}")
            health_data["anthropic"] = {"status": "error", "latency": 0}

        # 4. Check Voyage AI (Embeddings)
        try:
            import voyageai

            api_key = os.getenv("VOYAGE_API_KEY")
            if not api_key:
                health_data["voyageAI"] = {"status": "not_configured", "latency": 0}
            else:
                voyage_start = time.time()
                vo = voyageai.Client(api_key=api_key)
                await asyncio.to_thread(
                    lambda: vo.embed(texts=["health check"], model="voyage-large-2", input_type="query")
                )
                voyage_latency = round(time.time() - voyage_start, 2)
                health_data["voyageAI"] = {"status": "connected", "latency": voyage_latency}
        except Exception as e:
            error_str = str(e).lower()
            if "authentication" in error_str or "unauthorized" in error_str or "api key" in error_str:
                logger.error("Voyage AI authentication failed - invalid API key")
                health_data["voyageAI"] = {"status": "auth_error", "latency": 0}
            elif "rate limit" in error_str or "too many requests" in error_str:
                health_data["voyageAI"] = {"status": "rate_limited", "latency": 0}
            else:
                logger.error(f"Voyage AI health check failed: {str(e)}")
                health_data["voyageAI"] = {"status": "error", "latency": 0}

        # 5. Check Neo4j (Graph Database) Health
        neo4j_time = 0
        try:
            from services.graph.connection import get_neo4j_connection

            neo4j_start = time.time()
            connection = await get_neo4j_connection()
            neo4j_health = await connection.health_check()
            neo4j_time = round((time.time() - neo4j_start) * 1000)

            if neo4j_health.get("status") == "healthy":
                health_data["neo4j"] = {"status": "connected", "responseTime": neo4j_time}
            else:
                health_data["neo4j"] = {
                    "status": "error",
                    "responseTime": 0,
                    "error": neo4j_health.get("error", "Unknown error"),
                }
        except ValueError as e:
            logger.warning(f"Neo4j not configured: {str(e)}")
            health_data["neo4j"] = {"status": "not_configured", "responseTime": 0}
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            health_data["neo4j"] = {"status": "error", "responseTime": 0}

        logger.info(
            f"Health check: Supabase {db_time}ms, Backend OK, "
            f"Anthropic {health_data['anthropic']['status']}, "
            f"Voyage {health_data['voyageAI']['status']}, "
            f"Neo4j {health_data['neo4j']['status']} ({neo4j_time}ms)"
        )

        return {"success": True, "health": health_data}
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
