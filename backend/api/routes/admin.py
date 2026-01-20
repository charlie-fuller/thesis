"""
Admin dashboard routes
Handles statistics, analytics, and administrative operations
"""
import asyncio
import io
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

import os

from auth import require_admin
from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])
supabase = get_supabase()


@router.get("/stats")
async def get_admin_stats(
    current_user: dict = Depends(require_admin)
):
    """Get overall platform statistics"""
    try:
        # Count users
        users_result = await asyncio.to_thread(
            lambda: supabase.table('users').select('id', count='exact').execute()
        )
        total_users = users_result.count or 0

        # Count conversations
        convos_result = await asyncio.to_thread(
            lambda: supabase.table('conversations').select('id', count='exact').execute()
        )
        total_conversations = convos_result.count or 0

        # Count documents
        docs_result = await asyncio.to_thread(
            lambda: supabase.table('documents').select('id', count='exact').execute()
        )
        total_documents = docs_result.count or 0

        # Count messages
        messages_result = await asyncio.to_thread(
            lambda: supabase.table('messages').select('id', count='exact').execute()
        )
        total_messages = messages_result.count or 0

        logger.info(f"📊 Stats: {total_users} users, {total_conversations} conversations, {total_documents} documents, {total_messages} messages")

        return {
            'success': True,
            'total_users': total_users,
            'total_conversations': total_conversations,
            'total_documents': total_documents,
            'total_messages': total_messages
        }
    except Exception as e:
        logger.error(f"❌ Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/usage-trends")
async def get_usage_trends(
    current_user: dict = Depends(require_admin),
    days: int = 30
):
    """Get usage trends over time, grouped by agent"""
    try:
        from datetime import datetime, timedelta

        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get all agents for reference
        agents_result = await asyncio.to_thread(
            lambda: supabase.table('agents')
                .select('id, name, display_name')
                .execute()
        )
        agents = {a['id']: a for a in (agents_result.data or [])}
        # Also create a name -> display_name mapping for normalization
        agent_display_names = {a['name']: a.get('display_name', a['name']) for a in (agents_result.data or [])}

        # Get all assistant messages in range WITH metadata (for agent tracking)
        messages = await asyncio.to_thread(
            lambda: supabase.table('messages')
                .select('created_at, metadata')
                .eq('role', 'assistant')
                .gte('created_at', start_date.isoformat())
                .lte('created_at', end_date.isoformat())
                .execute()
        )

        # Also get meeting room messages for multi-agent conversations
        meeting_messages = await asyncio.to_thread(
            lambda: supabase.table('meeting_room_messages')
                .select('created_at, agent_id, agent_name')
                .gte('created_at', start_date.isoformat())
                .lte('created_at', end_date.isoformat())
                .not_.is_('agent_id', 'null')
                .execute()
        )

        # Get all conversations in range for the trends
        convos = await asyncio.to_thread(
            lambda: supabase.table('conversations')
                .select('created_at')
                .gte('created_at', start_date.isoformat())
                .lte('created_at', end_date.isoformat())
                .execute()
        )

        # Get all documents in range
        docs = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('uploaded_at')
                .gte('uploaded_at', start_date.isoformat())
                .lte('uploaded_at', end_date.isoformat())
                .execute()
        )

        # Initialize trends by date with agent tracking
        trends_by_date = {}
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_str = current_date.isoformat()
            trends_by_date[date_str] = {
                'date': date_str,
                'conversations': 0,
                'documents': 0,
                'messages': 0,
                'agent_usage': {}  # agent_name -> count
            }
            current_date += timedelta(days=1)

        # Count messages by date AND extract agent from metadata
        for msg in (messages.data or []):
            date = datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00')).date().isoformat()
            if date in trends_by_date:
                trends_by_date[date]['messages'] += 1

                # Extract agent from metadata if available
                metadata = msg.get('metadata') or {}
                agent_name = metadata.get('agent_display_name') or metadata.get('agent_name')
                if agent_name:
                    # Normalize to display name if we have a mapping
                    normalized_name = agent_display_names.get(agent_name, agent_name)
                    # Capitalize first letter for consistency
                    if normalized_name and normalized_name[0].islower():
                        normalized_name = normalized_name.capitalize()
                    trends_by_date[date]['agent_usage'][normalized_name] = trends_by_date[date]['agent_usage'].get(normalized_name, 0) + 1

        # Count meeting room messages by date and agent
        for msg in (meeting_messages.data or []):
            date = datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00')).date().isoformat()
            if date in trends_by_date:
                trends_by_date[date]['messages'] += 1
                agent_name = msg.get('agent_name', 'Unknown')
                if agent_name:
                    # Normalize to display name if we have a mapping
                    normalized_name = agent_display_names.get(agent_name, agent_name)
                    # Capitalize first letter for consistency
                    if normalized_name and normalized_name[0].islower():
                        normalized_name = normalized_name.capitalize()
                    trends_by_date[date]['agent_usage'][normalized_name] = trends_by_date[date]['agent_usage'].get(normalized_name, 0) + 1

        # Count conversations by date
        for convo in (convos.data or []):
            date = datetime.fromisoformat(convo['created_at'].replace('Z', '+00:00')).date().isoformat()
            if date in trends_by_date:
                trends_by_date[date]['conversations'] += 1

        # Count documents by date
        for doc in (docs.data or []):
            date = datetime.fromisoformat(doc['uploaded_at'].replace('Z', '+00:00')).date().isoformat()
            if date in trends_by_date:
                trends_by_date[date]['documents'] += 1

        # Collect all agent names for consistent series
        all_agents = set()
        for day_data in trends_by_date.values():
            all_agents.update(day_data['agent_usage'].keys())

        # Build final trends with per-agent columns
        trends = []
        for date_str in sorted(trends_by_date.keys()):
            day = trends_by_date[date_str]
            trend_entry = {
                'date': day['date'],
                'conversations': day['conversations'],
                'documents': day['documents'],
                'messages': day['messages'],
            }
            # Add per-agent counts (default to 0 if not used that day)
            for agent_name in all_agents:
                trend_entry[agent_name] = day['agent_usage'].get(agent_name, 0)
            trends.append(trend_entry)

        # Build agent summary (total usage across the period)
        agent_totals = {}
        for day_data in trends_by_date.values():
            for agent_name, count in day_data['agent_usage'].items():
                agent_totals[agent_name] = agent_totals.get(agent_name, 0) + count

        # Sort agents by total usage (descending) for chart legend order
        sorted_agents = sorted(agent_totals.items(), key=lambda x: -x[1])

        return {
            'success': True,
            'trends': trends,
            'agents': [a[0] for a in sorted_agents],  # List of agent names sorted by usage
            'agent_totals': dict(sorted_agents)  # Agent name -> total count
        }
    except Exception as e:
        logger.error(f"❌ Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/active-users")
async def get_active_users(
    current_user: dict = Depends(require_admin),
    days: int = 7
):
    """Get active users in specified timeframe"""
    try:
        from datetime import datetime, timedelta

        # Get total users count
        total_users_result = await asyncio.to_thread(
            lambda: supabase.table('users').select('id', count='exact').execute()
        )
        total_users = total_users_result.count or 0

        # Get users active in last 7 days (users who updated conversations)
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        active_7_convos = await asyncio.to_thread(
            lambda: supabase.table('conversations')\
                .select('user_id')\
                .gte('updated_at', seven_days_ago)\
                .execute()
        )

        # Get unique user IDs
        active_7_user_ids = set()
        for convo in (active_7_convos.data or []):
            if convo.get('user_id'):
                active_7_user_ids.add(convo['user_id'])

        # Get users active in last 30 days
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        active_30_convos = await asyncio.to_thread(
            lambda: supabase.table('conversations')\
                .select('user_id')\
                .gte('updated_at', thirty_days_ago)\
                .execute()
        )

        # Get unique user IDs
        active_30_user_ids = set()
        for convo in (active_30_convos.data or []):
            if convo.get('user_id'):
                active_30_user_ids.add(convo['user_id'])

        return {
            'success': True,
            'active_users': {
                'last_7_days': len(active_7_user_ids),
                'last_30_days': len(active_30_user_ids),
                'total_users': total_users
            }
        }
    except Exception as e:
        logger.error(f"❌ Active users error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/recent-activity")
async def get_recent_activity(
    current_user: dict = Depends(require_admin),
    limit: int = 20
):
    """Get recent platform activity"""
    try:
        # Get recent conversations with user info
        convos = await asyncio.to_thread(
            lambda: supabase.table('conversations')\
                .select('id, title, created_at, user_id, users:user_id(id, name, email)')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
        )

        # Get recent document uploads with user info
        docs = await asyncio.to_thread(
            lambda: supabase.table('documents')\
                .select('id, filename, uploaded_at, uploaded_by, users:uploaded_by(id, name, email)')\
                .order('uploaded_at', desc=True)\
                .limit(limit)\
                .execute()
        )

        # Transform to unified activity format
        activity = []

        # Add conversations with message counts
        for conv in (convos.data or []):
            # Count messages in this conversation
            msg_count_result = await asyncio.to_thread(
                lambda c=conv: supabase.table('messages')\
                    .select('id', count='exact')\
                    .eq('conversation_id', c['id'])\
                    .execute()
            )

            activity.append({
                'type': 'conversation',
                'id': conv['id'],
                'timestamp': conv['created_at'],
                'title': conv.get('title'),
                'user': conv.get('users') if conv.get('users') else None,
                'message_count': msg_count_result.count or 0
            })

        # Add documents
        for doc in (docs.data or []):
            activity.append({
                'type': 'document',
                'id': doc['id'],
                'timestamp': doc['uploaded_at'],
                'filename': doc.get('filename'),
                'user': doc.get('users') if doc.get('users') else None
            })

        # Sort by timestamp, most recent first
        activity.sort(key=lambda x: x['timestamp'], reverse=True)

        # Limit results
        activity = activity[:limit]

        return {
            'success': True,
            'activity': activity
        }
    except Exception as e:
        logger.error(f"❌ Recent activity error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def get_all_users(
    current_user: dict = Depends(require_admin)
):
    """Get all users for admin (for KPI user selector)"""
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('users')\
                .select('id, email, name')\
                .order('email')\
                .execute()
        )

        logger.info(f"📋 Retrieved {len(result.data)} users for selector")

        return {
            'success': True,
            'users': result.data
        }
    except Exception as e:
        logger.error(f"❌ Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients")
async def get_all_clients(
    current_user: dict = Depends(require_admin)
):
    """Get all clients for admin"""
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table('clients')\
                .select('id, name')\
                .order('name')\
                .execute()
        )

        logger.info(f"📋 Retrieved {len(result.data)} clients")

        return {
            'success': True,
            'clients': result.data
        }
    except Exception as e:
        logger.error(f"❌ Error fetching clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def get_all_conversations(
    current_user: dict = Depends(require_admin),
    limit: int = 100,
    client_id: str = None
):
    """Get all conversations with user and client info for admin"""
    try:
        # Build query with joins
        query = supabase.table('conversations')\
            .select('''
                *,
                users:user_id(name, email),
                clients:client_id(name)
            ''')

        # Apply client filter if provided
        if client_id:
            query = query.eq('client_id', client_id)

        # Apply limit and order
        result = await asyncio.to_thread(
            lambda: query.order('updated_at', desc=True)\
                .limit(limit)\
                .execute()
        )

        # Count messages for each conversation
        conversations_with_counts = []
        for conv in result.data:
            # Count messages
            msg_count_result = await asyncio.to_thread(
                lambda c=conv: supabase.table('messages')\
                    .select('id', count='exact')\
                    .eq('conversation_id', c['id'])\
                    .execute()
            )

            conv['message_count'] = msg_count_result.count or 0
            conversations_with_counts.append(conv)

        logger.info(f"📋 Retrieved {len(conversations_with_counts)} conversations")

        return {
            'success': True,
            'conversations': conversations_with_counts
        }
    except Exception as e:
        logger.error(f"❌ Error fetching conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_system_health(
    current_user: dict = Depends(require_admin)
):
    """Get real-time system health metrics for admin dashboard"""
    try:
        health_data = {
            'supabase': {'status': 'checking', 'responseTime': 0},
            'railway': {'status': 'running'},
            'anthropic': {'status': 'checking', 'latency': 0},
            'voyageAI': {'status': 'checking', 'latency': 0},
            'neo4j': {'status': 'checking', 'responseTime': 0}
        }

        db_time = 0

        # 1. Check Supabase (Database) Health
        try:
            db_start = time.time()
            await asyncio.to_thread(
                lambda: supabase.table('users').select('id', count='exact').limit(1).execute()
            )
            db_time = round((time.time() - db_start) * 1000)
            health_data['supabase'] = {
                'status': 'connected',
                'responseTime': db_time
            }
        except Exception as e:
            logger.error(f"❌ Supabase health check failed: {str(e)}")
            health_data['supabase'] = {
                'status': 'error',
                'responseTime': 0
            }

        # 2. Railway (Backend API) - If this endpoint is responding, Railway is running
        health_data['railway'] = {
            'status': 'running',
            'uptime': True
        }

        # 3. Check Anthropic (Claude) - Make a real API call to verify connectivity
        try:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                health_data['anthropic'] = {
                    'status': 'not_configured',
                    'latency': 0
                }
            else:
                anthropic_start = time.time()
                client = anthropic.Anthropic(api_key=api_key)
                # Use count_tokens as a lightweight health check (doesn't consume tokens)
                await asyncio.to_thread(
                    lambda: client.messages.count_tokens(
                        model="claude-sonnet-4-20250514",
                        messages=[{"role": "user", "content": "health check"}]
                    )
                )
                anthropic_latency = round(time.time() - anthropic_start, 2)
                health_data['anthropic'] = {
                    'status': 'connected',
                    'latency': anthropic_latency
                }
        except anthropic.AuthenticationError:
            logger.error("❌ Anthropic authentication failed - invalid API key")
            health_data['anthropic'] = {
                'status': 'auth_error',
                'latency': 0
            }
        except anthropic.RateLimitError:
            # Rate limited but API key is valid
            health_data['anthropic'] = {
                'status': 'rate_limited',
                'latency': 0
            }
        except Exception as e:
            logger.error(f"❌ Anthropic health check failed: {str(e)}")
            health_data['anthropic'] = {
                'status': 'error',
                'latency': 0
            }

        # 4. Check Voyage AI (Embeddings) - Make a real API call to verify connectivity
        try:
            import voyageai
            api_key = os.getenv("VOYAGE_API_KEY")
            if not api_key:
                health_data['voyageAI'] = {
                    'status': 'not_configured',
                    'latency': 0
                }
            else:
                voyage_start = time.time()
                vo = voyageai.Client(api_key=api_key)
                # Make a minimal embedding call as health check
                await asyncio.to_thread(
                    lambda: vo.embed(
                        texts=["health check"],
                        model="voyage-large-2",
                        input_type="query"
                    )
                )
                voyage_latency = round(time.time() - voyage_start, 2)
                health_data['voyageAI'] = {
                    'status': 'connected',
                    'latency': voyage_latency
                }
        except Exception as e:
            error_str = str(e).lower()
            if 'authentication' in error_str or 'unauthorized' in error_str or 'api key' in error_str:
                logger.error("❌ Voyage AI authentication failed - invalid API key")
                health_data['voyageAI'] = {
                    'status': 'auth_error',
                    'latency': 0
                }
            elif 'rate limit' in error_str or 'too many requests' in error_str:
                # Rate limited but API key is valid
                health_data['voyageAI'] = {
                    'status': 'rate_limited',
                    'latency': 0
                }
            else:
                logger.error(f"❌ Voyage AI health check failed: {str(e)}")
                health_data['voyageAI'] = {
                    'status': 'error',
                    'latency': 0
                }

        # 5. Check Neo4j (Graph Database) Health
        neo4j_time = 0
        try:
            from services.graph.connection import get_neo4j_connection
            neo4j_start = time.time()
            connection = await get_neo4j_connection()
            neo4j_health = await connection.health_check()
            neo4j_time = round((time.time() - neo4j_start) * 1000)

            if neo4j_health.get('status') == 'healthy':
                health_data['neo4j'] = {
                    'status': 'connected',
                    'responseTime': neo4j_time
                }
            else:
                health_data['neo4j'] = {
                    'status': 'error',
                    'responseTime': 0,
                    'error': neo4j_health.get('error', 'Unknown error')
                }
        except ValueError as e:
            # Neo4j not configured (missing env vars)
            logger.warning(f"⚠️ Neo4j not configured: {str(e)}")
            health_data['neo4j'] = {
                'status': 'not_configured',
                'responseTime': 0
            }
        except Exception as e:
            logger.error(f"❌ Neo4j health check failed: {str(e)}")
            health_data['neo4j'] = {
                'status': 'error',
                'responseTime': 0
            }

        logger.info(f"🏥 Health check: Supabase {db_time}ms, Railway ✓, Anthropic {health_data['anthropic']['status']}, Voyage {health_data['voyageAI']['status']}, Neo4j {health_data['neo4j']['status']} ({neo4j_time}ms)")

        return {
            'success': True,
            'health': health_data
        }
    except Exception as e:
        logger.error(f"❌ Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-system-instructions-cache")
async def clear_system_instructions_cache(
    current_user: dict = Depends(require_admin)
):
    """
    Clear all system instructions cache (Redis + lru_cache).
    Use this when system instructions have been updated.
    Requires admin role.
    """
    try:
        from cache import invalidate_all_system_instructions

        count = invalidate_all_system_instructions()
        logger.info(f"🗑️ Admin {current_user.get('email')} cleared system instructions cache")

        return {
            'success': True,
            'message': f'Cleared {count} Redis cache entries and lru_cache',
            'redis_entries_cleared': count
        }
    except Exception as e:
        logger.error(f"❌ Cache clear error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-search-cache")
async def clear_search_cache(
    current_user: dict = Depends(require_admin)
):
    """
    Clear all RAG search cache (Redis).
    Use this when documents have been uploaded/updated and cached search results are stale.
    Requires admin role.
    """
    try:
        from cache import invalidate_search_cache

        # Clear all search cache
        invalidate_search_cache("")
        logger.info(f"Admin {current_user.get('email')} cleared search cache")

        return {
            'success': True,
            'message': 'Cleared all RAG search cache entries'
        }
    except Exception as e:
        logger.error(f"Search cache clear error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/upload-health")
async def get_upload_health(
    current_user: dict = Depends(require_admin)
):
    """
    Get document upload health metrics.
    Returns success rates, failure breakdown, and stuck documents.
    """
    try:
        now = datetime.now(timezone.utc)
        one_day_ago = (now - timedelta(days=1)).isoformat()
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
        one_hour_ago = (now - timedelta(hours=1)).isoformat()

        # Get all documents with status counts for different time periods
        async def get_status_counts(since: str):
            result = await asyncio.to_thread(
                lambda: supabase.table('documents')
                    .select('processing_status, filename')
                    .gte('uploaded_at', since)
                    .execute()
            )
            docs = result.data or []

            counts = {
                'total': len(docs),
                'completed': 0,
                'failed': 0,
                'pending': 0,
                'processing': 0
            }
            failed_by_type = {}

            for doc in docs:
                status = doc.get('processing_status', 'pending')
                if status in counts:
                    counts[status] += 1

                # Track failed uploads by file type
                if status == 'failed':
                    filename = doc.get('filename', '')
                    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'unknown'
                    failed_by_type[ext] = failed_by_type.get(ext, 0) + 1

            success_rate = (counts['completed'] / counts['total'] * 100) if counts['total'] > 0 else 100
            return counts, success_rate, failed_by_type

        # Get counts for each time period
        counts_24h, rate_24h, failed_types_24h = await get_status_counts(one_day_ago)
        counts_7d, rate_7d, failed_types_7d = await get_status_counts(seven_days_ago)
        counts_30d, rate_30d, failed_types_30d = await get_status_counts(thirty_days_ago)

        # Get stuck documents (pending/processing for > 1 hour)
        stuck_result = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, filename, processing_status, uploaded_at')
                .in_('processing_status', ['pending', 'processing'])
                .lt('uploaded_at', one_hour_ago)
                .execute()
        )
        stuck_docs = stuck_result.data or []

        # Get recent failures with error messages
        recent_failures = await asyncio.to_thread(
            lambda: supabase.table('documents')
                .select('id, filename, processing_error, uploaded_at')
                .eq('processing_status', 'failed')
                .gte('uploaded_at', seven_days_ago)
                .order('uploaded_at', desc=True)
                .limit(5)
                .execute()
        )

        logger.info(f"📊 Upload health: {rate_24h:.1f}% success (24h), {len(stuck_docs)} stuck")

        return {
            'success': True,
            'periods': {
                '24h': {
                    'total': counts_24h['total'],
                    'completed': counts_24h['completed'],
                    'failed': counts_24h['failed'],
                    'pending': counts_24h['pending'],
                    'processing': counts_24h['processing'],
                    'success_rate': round(rate_24h, 1),
                    'failed_by_type': failed_types_24h
                },
                '7d': {
                    'total': counts_7d['total'],
                    'completed': counts_7d['completed'],
                    'failed': counts_7d['failed'],
                    'success_rate': round(rate_7d, 1),
                    'failed_by_type': failed_types_7d
                },
                '30d': {
                    'total': counts_30d['total'],
                    'completed': counts_30d['completed'],
                    'failed': counts_30d['failed'],
                    'success_rate': round(rate_30d, 1)
                }
            },
            'stuck_documents': [
                {
                    'id': doc['id'],
                    'filename': doc['filename'],
                    'status': doc['processing_status'],
                    'uploaded_at': doc['uploaded_at']
                }
                for doc in stuck_docs
            ],
            'recent_failures': [
                {
                    'id': doc['id'],
                    'filename': doc['filename'],
                    'error': doc.get('processing_error', 'Unknown error'),
                    'uploaded_at': doc['uploaded_at']
                }
                for doc in (recent_failures.data or [])
            ]
        }
    except Exception as e:
        logger.error(f"❌ Upload health error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/interface-health")
async def get_interface_health(
    current_user: dict = Depends(require_admin)
):
    """
    Get interface health metrics.
    Returns response length stats, image generation stats, and workflow metrics.
    """
    try:
        now = datetime.now(timezone.utc)
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        five_minutes_ago = (now - timedelta(minutes=5)).isoformat()
        one_hour_ago = (now - timedelta(hours=1)).isoformat()

        # Run all independent queries in parallel for better performance
        messages_task = asyncio.to_thread(
            lambda: supabase.table('messages')
                .select('content')
                .eq('role', 'assistant')
                .gte('created_at', seven_days_ago)
                .execute()
        )

        convos_task = asyncio.to_thread(
            lambda: supabase.table('conversations')
                .select('id', count='exact')
                .gte('created_at', seven_days_ago)
                .execute()
        )

        active_users_task = asyncio.to_thread(
            lambda: supabase.table('conversations')
                .select('user_id')
                .gte('updated_at', seven_days_ago)
                .execute()
        )

        # Check for stuck conversations - simplified query
        recent_messages_task = asyncio.to_thread(
            lambda: supabase.table('messages')
                .select('conversation_id, metadata, created_at')
                .gte('created_at', one_hour_ago)
                .lt('created_at', five_minutes_ago)
                .order('created_at', desc=True)
                .limit(50)
                .execute()
        )

        # Execute all queries in parallel
        messages_result, convos_result, active_users_result, recent_messages_result = await asyncio.gather(
            messages_task, convos_task, active_users_task, recent_messages_task
        )

        messages = messages_result.data or []

        # Calculate average response length (word count)
        total_words = 0
        response_count = 0

        for msg in messages:
            content = msg.get('content', '')
            if content:
                word_count = len(content.split())
                total_words += word_count
                response_count += 1

        avg_response_length = round(total_words / response_count) if response_count > 0 else 0

        total_conversations_7d = convos_result.count or 0

        # Get active users count
        active_user_ids = set()
        for convo in (active_users_result.data or []):
            if convo.get('user_id'):
                active_user_ids.add(convo['user_id'])
        active_users_count = len(active_user_ids)

        # Check for stuck conversations (awaiting_image_confirmation)
        stuck_conversations = set()
        for msg in (recent_messages_result.data or []):
            metadata = msg.get('metadata') or {}
            if metadata.get('awaiting_image_confirmation'):
                stuck_conversations.add(msg['conversation_id'])

        # Get conversations with useable output tracking (if column exists)
        # This is a separate query since it may fail if column doesn't exist
        avg_turns = 0
        useable_convos = []
        try:
            useable_result = await asyncio.to_thread(
                lambda: supabase.table('conversations')
                    .select('turns_to_useable_output')
                    .not_.is_('turns_to_useable_output', 'null')
                    .gte('updated_at', seven_days_ago)
                    .limit(100)
                    .execute()
            )
            useable_convos = useable_result.data or []
            total_turns = sum(c.get('turns_to_useable_output', 0) for c in useable_convos)
            avg_turns = round(total_turns / len(useable_convos), 1) if useable_convos else 0
        except Exception as e:
            # Column may not exist yet - gracefully handle
            logger.warning(f"turns_to_useable_output query failed (column may not exist): {str(e)}")

        # Determine health status
        response_status = 'healthy' if avg_response_length <= 500 else ('warning' if avg_response_length <= 800 else 'critical')
        stuck_status = 'healthy' if len(stuck_conversations) == 0 else ('warning' if len(stuck_conversations) <= 2 else 'critical')

        logger.info(f"📊 Interface health: {avg_response_length} avg words, {len(stuck_conversations)} stuck, {total_conversations_7d} chats, {active_users_count} active users")

        return {
            'success': True,
            'response_metrics': {
                'avg_word_count': avg_response_length,
                'total_responses': response_count,
                'target': 500,
                'status': response_status
            },
            'activity_metrics': {
                'conversations_7d': total_conversations_7d,
                'active_users_7d': active_users_count
            },
            'workflow_metrics': {
                'avg_turns_to_useable': avg_turns,
                'conversations_tracked': len(useable_convos),
                'stuck_conversations': len(stuck_conversations),
                'stuck_status': stuck_status
            },
            'period': '7d'
        }
    except Exception as e:
        logger.error(f"❌ Interface health error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/help-documents/{document_id}")
async def get_help_document(
    document_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Get a single help document with its full content for editing.
    """
    try:
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('help_documents')
                .select('id, title, file_path, category, content, created_at, updated_at')
                .eq('id', document_id)
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = doc_result.data[0]

        # Get chunk count
        chunk_result = await asyncio.to_thread(
            lambda: supabase.table('help_chunks')
                .select('id', count='exact')
                .eq('document_id', document_id)
                .execute()
        )
        doc['chunk_count'] = chunk_result.count or 0

        return {
            'success': True,
            'document': doc
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get help document error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/help-documents")
async def get_help_documents(
    current_user: dict = Depends(require_admin)
):
    """
    Get all help documents with their metadata.
    Returns documents grouped by category (user/admin).
    """
    try:
        # Get all documents
        docs_result = await asyncio.to_thread(
            lambda: supabase.table('help_documents')
                .select('id, title, file_path, category, created_at, updated_at')
                .order('category')
                .order('title')
                .execute()
        )
        documents = docs_result.data or []

        # Get chunk counts for each document
        for doc in documents:
            chunk_result = await asyncio.to_thread(
                lambda doc_id=doc['id']: supabase.table('help_chunks')
                    .select('id', count='exact')
                    .eq('document_id', doc_id)
                    .execute()
            )
            doc['chunk_count'] = chunk_result.count or 0

        # Group by category
        user_docs = [d for d in documents if d.get('category') == 'user']
        admin_docs = [d for d in documents if d.get('category') == 'admin']

        return {
            'success': True,
            'documents': {
                'user': user_docs,
                'admin': admin_docs
            },
            'total_count': len(documents)
        }
    except Exception as e:
        logger.error(f"❌ Help documents error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/help-documents/{document_id}/reindex")
async def reindex_help_document(
    document_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Reindex a single help document by its ID.
    Deletes existing chunks and recreates them with fresh embeddings.
    """
    try:
        # Get the document to find its file path
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('help_documents')
                .select('id, title, file_path, category')
                .eq('id', document_id)
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = doc_result.data[0]
        file_path = doc['file_path']
        title = doc['title']
        category = doc['category']

        logger.info(f"Reindexing document: {title} ({file_path})")

        # Delete existing chunks for this document
        await asyncio.to_thread(
            lambda: supabase.table('help_chunks')
                .delete()
                .eq('document_id', document_id)
                .execute()
        )

        # Get the document content from the database
        content_result = await asyncio.to_thread(
            lambda: supabase.table('help_documents')
                .select('content')
                .eq('id', document_id)
                .execute()
        )

        if not content_result.data or not content_result.data[0].get('content'):
            raise HTTPException(status_code=400, detail="Document has no content to index")

        content = content_result.data[0]['content']

        # Import embedding service
        from services.embeddings import create_embedding

        # Role access mapping
        ROLE_ACCESS_MAP = {
            "admin": ["admin"],
            "system": ["admin", "user"],
            "user": ["user"],
            "technical": ["admin"]
        }

        # Extract sections from markdown
        def extract_sections(content: str):
            sections = []
            current_heading = "Introduction"
            current_content = []

            for line in content.split('\n'):
                if line.strip().startswith('#'):
                    if current_content:
                        sections.append((current_heading, '\n'.join(current_content)))
                    current_heading = line.strip().lstrip('#').strip()
                    current_content = []
                else:
                    current_content.append(line)

            if current_content:
                sections.append((current_heading, '\n'.join(current_content)))

            return sections

        # Chunk text
        def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
            chunks = []
            start = 0

            while start < len(text):
                end = start + chunk_size

                if end < len(text):
                    sentence_end = max(
                        text.rfind('. ', start, end),
                        text.rfind('.\n', start, end),
                        text.rfind('? ', start, end),
                        text.rfind('! ', start, end)
                    )
                    if sentence_end > start + chunk_size - 100:
                        end = sentence_end + 1

                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)

                start = end - overlap if end < len(text) else len(text)

            return chunks

        sections = extract_sections(content)
        chunks_created = 0
        chunk_index = 0

        for heading, section_content in sections:
            section_chunks = chunk_text(section_content)

            for chunk_text_content in section_chunks:
                if len(chunk_text_content.strip()) < 50:
                    continue

                try:
                    embedding_content = f"{title} - {heading}\n\n{chunk_text_content}"
                    embedding = create_embedding(embedding_content, input_type="document")

                    await asyncio.to_thread(
                        lambda emb=embedding, idx=chunk_index, head=heading, chunk=chunk_text_content: supabase.table('help_chunks').insert({
                            'document_id': document_id,
                            'content': chunk,
                            'embedding': emb,
                            'chunk_index': idx,
                            'heading_context': head,
                            'role_access': ROLE_ACCESS_MAP.get(category, ['admin', 'user']),
                            'metadata': {
                                'category': category,
                                'title': title,
                                'section': head
                            }
                        }).execute()
                    )

                    chunks_created += 1
                    chunk_index += 1

                except Exception as e:
                    logger.error(f"Error creating embedding for chunk {chunk_index}: {e}")
                    continue

        # Update document's updated_at timestamp
        await asyncio.to_thread(
            lambda: supabase.table('help_documents')
                .update({'updated_at': datetime.now(timezone.utc).isoformat()})
                .eq('id', document_id)
                .execute()
        )

        logger.info(f"Reindexed {title}: {chunks_created} chunks created")

        return {
            'success': True,
            'document_id': document_id,
            'title': title,
            'chunks_created': chunks_created
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Reindex document error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/help-documents/{document_id}")
async def update_help_document(
    document_id: str,
    request: Request,
    current_user: dict = Depends(require_admin)
):
    """
    Update a help document's title and/or content.
    Automatically triggers reindexing after update.
    """
    try:
        body = await request.json()
        title = body.get('title')
        content = body.get('content')

        if not title and not content:
            raise HTTPException(status_code=400, detail="Must provide title or content to update")

        # Get the existing document
        doc_result = await asyncio.to_thread(
            lambda: supabase.table('help_documents')
                .select('id, title, file_path, category, content')
                .eq('id', document_id)
                .execute()
        )

        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        doc = doc_result.data[0]
        new_title = title if title else doc['title']
        new_content = content if content else doc['content']
        category = doc['category']

        # Validate title
        if not new_title or len(new_title.strip()) < 3:
            raise HTTPException(status_code=400, detail="Title must be at least 3 characters")

        # Validate content
        if not new_content or len(new_content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Content must be at least 50 characters")

        # Calculate word count
        word_count = len(new_content.split())

        # Update the document
        await asyncio.to_thread(
            lambda: supabase.table('help_documents')
                .update({
                    'title': new_title.strip(),
                    'content': new_content,
                    'word_count': word_count,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })
                .eq('id', document_id)
                .execute()
        )

        logger.info(f"Updated help document: {new_title} by admin {current_user['id']}")

        # Delete existing chunks for this document
        await asyncio.to_thread(
            lambda: supabase.table('help_chunks')
                .delete()
                .eq('document_id', document_id)
                .execute()
        )

        # Import embedding service
        from services.embeddings import create_embedding

        # Role access mapping
        ROLE_ACCESS_MAP = {
            "admin": ["admin"],
            "system": ["admin", "user"],
            "user": ["user"],
            "technical": ["admin"]
        }

        # Extract sections from markdown
        def extract_sections(md_content: str):
            sections = []
            current_heading = "Introduction"
            current_content = []

            for line in md_content.split('\n'):
                if line.strip().startswith('#'):
                    if current_content:
                        sections.append((current_heading, '\n'.join(current_content)))
                    current_heading = line.strip().lstrip('#').strip()
                    current_content = []
                else:
                    current_content.append(line)

            if current_content:
                sections.append((current_heading, '\n'.join(current_content)))

            return sections

        # Chunk text
        def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
            chunks = []
            start = 0

            while start < len(text):
                end = start + chunk_size

                if end < len(text):
                    sentence_end = max(
                        text.rfind('. ', start, end),
                        text.rfind('.\n', start, end),
                        text.rfind('? ', start, end),
                        text.rfind('! ', start, end)
                    )
                    if sentence_end > start + chunk_size - 100:
                        end = sentence_end + 1

                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)

                start = end - overlap if end < len(text) else len(text)

            return chunks

        sections = extract_sections(new_content)
        chunks_created = 0
        chunk_index = 0

        for heading, section_content in sections:
            section_chunks = chunk_text(section_content)

            for chunk_text_content in section_chunks:
                if len(chunk_text_content.strip()) < 50:
                    continue

                try:
                    embedding_content = f"{new_title} - {heading}\n\n{chunk_text_content}"
                    embedding = create_embedding(embedding_content, input_type="document")

                    await asyncio.to_thread(
                        lambda emb=embedding, idx=chunk_index, head=heading, chunk=chunk_text_content: supabase.table('help_chunks').insert({
                            'document_id': document_id,
                            'content': chunk,
                            'embedding': emb,
                            'chunk_index': idx,
                            'heading_context': head,
                            'role_access': ROLE_ACCESS_MAP.get(category, ['admin', 'user']),
                            'metadata': {
                                'category': category,
                                'title': new_title,
                                'section': head
                            }
                        }).execute()
                    )

                    chunks_created += 1
                    chunk_index += 1

                except Exception as e:
                    logger.error(f"Error creating embedding for chunk {chunk_index}: {e}")
                    continue

        logger.info(f"Reindexed {new_title} after update: {chunks_created} chunks created")

        return {
            'success': True,
            'document_id': document_id,
            'title': new_title,
            'word_count': word_count,
            'chunks_created': chunks_created
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update help document error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/help-analytics")
async def get_help_analytics(
    current_user: dict = Depends(require_admin),
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze")
):
    """
    Get analytics for the help system.
    Returns questions asked, low confidence responses, and feedback breakdown.

    The confidence metric is derived from the vector similarity scores of the
    sources returned with each response. Lower similarity = lower confidence.
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get all help messages (both user questions and assistant responses)
        messages_result = await asyncio.to_thread(
            lambda: supabase.table('help_messages')
                .select('id, conversation_id, role, content, sources, feedback, feedback_timestamp, timestamp')
                .gte('timestamp', start_date.isoformat())
                .order('timestamp', desc=True)
                .execute()
        )
        messages = messages_result.data or []

        # Get help conversations for context (including help_type)
        conversations_result = await asyncio.to_thread(
            lambda: supabase.table('help_conversations')
                .select('id, user_id, title, created_at, help_type')
                .gte('created_at', start_date.isoformat())
                .execute()
        )
        conversations = {c['id']: c for c in (conversations_result.data or [])}

        # Analyze messages
        user_questions = []
        low_confidence_responses = []
        feedback_counts = {'positive': 0, 'negative': 0, 'none': 0}
        total_responses = 0
        total_similarity = 0
        similarity_count = 0

        for msg in messages:
            if msg.get('role') == 'user':
                user_questions.append({
                    'id': msg['id'],
                    'conversation_id': msg['conversation_id'],
                    'question': msg.get('content', '')[:200],
                    'timestamp': msg.get('timestamp')
                })
            elif msg.get('role') == 'assistant':
                total_responses += 1
                sources = msg.get('sources') or []

                # Calculate average similarity (confidence) from sources
                if sources:
                    similarities = [s.get('similarity', 0) for s in sources if s.get('similarity')]
                    if similarities:
                        avg_similarity = sum(similarities) / len(similarities)
                        total_similarity += avg_similarity
                        similarity_count += 1

                        # Low confidence threshold: similarity < 0.75
                        if avg_similarity < 0.75:
                            # Find the corresponding user question
                            conv_id = msg['conversation_id']
                            conv = conversations.get(conv_id, {})

                            low_confidence_responses.append({
                                'id': msg['id'],
                                'conversation_id': conv_id,
                                'conversation_title': conv.get('title', 'Unknown'),
                                'help_type': conv.get('help_type', 'user'),
                                'response_preview': msg.get('content', '')[:150],
                                'avg_similarity': round(avg_similarity, 3),
                                'source_count': len(sources),
                                'sources': [{'title': s.get('title'), 'section': s.get('section'), 'similarity': round(s.get('similarity', 0), 3)} for s in sources],
                                'timestamp': msg.get('timestamp'),
                                'feedback': msg.get('feedback')
                            })

                # Track feedback
                feedback = msg.get('feedback')
                if feedback == 1:
                    feedback_counts['positive'] += 1
                elif feedback == -1:
                    feedback_counts['negative'] += 1
                else:
                    feedback_counts['none'] += 1

        # Sort low confidence by similarity (lowest first)
        low_confidence_responses.sort(key=lambda x: x['avg_similarity'])

        # Calculate overall stats
        avg_confidence = round(total_similarity / similarity_count, 3) if similarity_count > 0 else 0
        feedback_rate = round((feedback_counts['positive'] + feedback_counts['negative']) / total_responses * 100, 1) if total_responses > 0 else 0

        # Determine health status
        if avg_confidence >= 0.8 and feedback_counts['negative'] <= feedback_counts['positive']:
            health_status = 'healthy'
        elif avg_confidence >= 0.7 or feedback_counts['negative'] <= feedback_counts['positive'] * 2:
            health_status = 'warning'
        else:
            health_status = 'critical'

        logger.info(f"📊 Help analytics: {len(user_questions)} questions, {len(low_confidence_responses)} low confidence, avg confidence {avg_confidence}")

        return {
            'success': True,
            'period_days': days,
            'summary': {
                'total_questions': len(user_questions),
                'total_responses': total_responses,
                'avg_confidence': avg_confidence,
                'low_confidence_count': len(low_confidence_responses),
                'feedback_rate': feedback_rate,
                'health_status': health_status
            },
            'feedback': {
                'positive': feedback_counts['positive'],
                'negative': feedback_counts['negative'],
                'no_feedback': feedback_counts['none']
            },
            'low_confidence_responses': low_confidence_responses[:20],  # Top 20 lowest confidence
            'recent_questions': user_questions[:20]  # Most recent 20 questions
        }
    except Exception as e:
        logger.error(f"❌ Help analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/help-conversations/export")
async def export_help_conversations(
    current_user: dict = Depends(require_admin),
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    format: str = Query("json", description="Export format: json or csv")
):
    """
    Export all help conversations with messages for analysis.
    Returns conversations with their full message history.
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get all help conversations in the period
        conversations_result = await asyncio.to_thread(
            lambda: supabase.table('help_conversations')
                .select('id, user_id, title, help_type, created_at, updated_at')
                .gte('created_at', start_date.isoformat())
                .order('created_at', desc=True)
                .execute()
        )
        conversations = conversations_result.data or []

        if not conversations:
            return {
                'success': True,
                'count': 0,
                'conversations': [],
                'period_days': days
            }

        # Get all messages for these conversations
        conversation_ids = [c['id'] for c in conversations]
        messages_result = await asyncio.to_thread(
            lambda: supabase.table('help_messages')
                .select('id, conversation_id, role, content, sources, feedback, timestamp')
                .in_('conversation_id', conversation_ids)
                .order('timestamp')
                .execute()
        )
        messages = messages_result.data or []

        # Get user info for conversations
        user_ids = list(set(c['user_id'] for c in conversations if c.get('user_id')))
        users_result = await asyncio.to_thread(
            lambda: supabase.table('users')
                .select('id, email, name')
                .in_('id', user_ids)
                .execute()
        ) if user_ids else type('obj', (object,), {'data': []})()
        users = {u['id']: u for u in (users_result.data or [])}

        # Group messages by conversation
        messages_by_conv = {}
        for msg in messages:
            conv_id = msg['conversation_id']
            if conv_id not in messages_by_conv:
                messages_by_conv[conv_id] = []
            messages_by_conv[conv_id].append({
                'id': msg['id'],
                'role': msg['role'],
                'content': msg['content'],
                'sources': msg.get('sources'),
                'feedback': msg.get('feedback'),
                'timestamp': msg['timestamp']
            })

        # Build export data
        export_data = []
        for conv in conversations:
            user = users.get(conv.get('user_id'), {})
            export_data.append({
                'id': conv['id'],
                'title': conv.get('title', 'Help Chat'),
                'help_type': conv.get('help_type', 'user'),
                'user_email': user.get('email', 'Unknown'),
                'user_name': user.get('name', 'Unknown'),
                'created_at': conv['created_at'],
                'message_count': len(messages_by_conv.get(conv['id'], [])),
                'messages': messages_by_conv.get(conv['id'], [])
            })

        logger.info(f"📥 Exported {len(export_data)} help conversations for admin {current_user['id']}")

        return {
            'success': True,
            'count': len(export_data),
            'period_days': days,
            'conversations': export_data
        }

    except Exception as e:
        logger.error(f"❌ Help conversations export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/keyword-trends")
async def get_keyword_trends(
    current_user: dict = Depends(require_admin),
    days: int = 30
):
    """
    Analyze keyword trends from user messages.
    Returns top keywords, questions asked, and suggested FAQs.
    """
    import re
    from collections import Counter

    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get all user messages in range
        messages_result = await asyncio.to_thread(
            lambda: supabase.table('messages')
                .select('content, created_at')
                .eq('role', 'user')
                .gte('created_at', start_date.isoformat())
                .lte('created_at', end_date.isoformat())
                .execute()
        )

        messages = messages_result.data if messages_result.data else []

        # GenAI Strategy domain keywords to track
        domain_keywords = {
            # Strategy & Business
            'strategy', 'roadmap', 'initiative', 'transformation', 'adoption',
            'roi', 'business case', 'value', 'impact', 'metrics', 'kpi',
            # AI/ML Technical
            'genai', 'llm', 'rag', 'embeddings', 'fine-tuning', 'prompt',
            'model', 'inference', 'training', 'deployment', 'api',
            'chatbot', 'agent', 'copilot', 'automation', 'workflow',
            # Governance & Security
            'governance', 'compliance', 'security', 'privacy', 'policy',
            'risk', 'audit', 'regulation', 'gdpr', 'sox', 'hipaa',
            'data protection', 'access control', 'shadow ai',
            # Stakeholder Management
            'stakeholder', 'sponsor', 'champion', 'executive', 'c-suite',
            'alignment', 'buy-in', 'resistance', 'change management',
            # Implementation
            'pilot', 'poc', 'mvp', 'prototype', 'integration', 'vendor',
            'build vs buy', 'architecture', 'infrastructure', 'scalability',
            # Research & Innovation
            'research', 'benchmark', 'best practice', 'use case', 'experiment',
            'innovation', 'emerging', 'trend', 'disruption'
        }

        # Categorize domain keywords
        keyword_categories = {
            'strategy': 'Strategy', 'roadmap': 'Strategy', 'initiative': 'Strategy',
            'transformation': 'Strategy', 'adoption': 'Strategy',
            'roi': 'Business Value', 'business case': 'Business Value', 'value': 'Business Value',
            'impact': 'Business Value', 'metrics': 'Business Value', 'kpi': 'Business Value',
            'genai': 'AI Technology', 'llm': 'AI Technology', 'rag': 'AI Technology',
            'embeddings': 'AI Technology', 'fine-tuning': 'AI Technology', 'prompt': 'AI Technology',
            'model': 'AI Technology', 'inference': 'AI Technology', 'agent': 'AI Technology',
            'chatbot': 'AI Technology', 'copilot': 'AI Technology', 'automation': 'AI Technology',
            'governance': 'Governance', 'compliance': 'Governance', 'security': 'Governance',
            'privacy': 'Governance', 'policy': 'Governance', 'risk': 'Governance',
            'audit': 'Governance', 'regulation': 'Governance', 'shadow ai': 'Governance',
            'stakeholder': 'Stakeholders', 'sponsor': 'Stakeholders', 'champion': 'Stakeholders',
            'executive': 'Stakeholders', 'c-suite': 'Stakeholders', 'alignment': 'Stakeholders',
            'pilot': 'Implementation', 'poc': 'Implementation', 'mvp': 'Implementation',
            'prototype': 'Implementation', 'integration': 'Implementation', 'vendor': 'Implementation',
            'research': 'Research', 'benchmark': 'Research', 'best practice': 'Research',
            'use case': 'Research', 'innovation': 'Research', 'emerging': 'Research'
        }

        # Process messages
        word_counts = Counter()
        questions = []
        all_words = []

        for msg in messages:
            content = msg.get('content', '').lower()

            # Extract questions (messages ending with ?)
            if content.strip().endswith('?'):
                questions.append({
                    'text': msg.get('content', '').strip()[:200],
                    'timestamp': msg.get('created_at')
                })

            # Tokenize and count words
            words = re.findall(r'\b[a-zA-Z]{3,}\b', content)
            all_words.extend(words)

        # Count word frequencies
        word_counts = Counter(all_words)

        # Common stop words to filter out
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'were', 'will',
            'this', 'that', 'with', 'from', 'they', 'what', 'which', 'when', 'would',
            'there', 'their', 'about', 'could', 'other', 'into', 'some', 'than', 'then',
            'these', 'only', 'just', 'also', 'more', 'after', 'before', 'should',
            'how', 'like', 'help', 'want', 'need', 'please', 'thanks', 'thank'
        }

        # Build keyword list with domain detection
        keywords = []
        for word, count in word_counts.most_common(100):
            if word not in stop_words and len(word) > 2:
                is_domain = word in domain_keywords
                category = keyword_categories.get(word, 'General')
                keywords.append({
                    'word': word,
                    'count': count,
                    'is_domain_keyword': is_domain,
                    'category': category
                })

        # Sort: domain keywords first, then by count
        keywords.sort(key=lambda x: (not x['is_domain_keyword'], -x['count']))
        keywords = keywords[:30]  # Top 30

        # Generate FAQ suggestions from repeated questions
        question_texts = [q['text'].lower() for q in questions]
        question_themes = Counter()

        for q in question_texts:
            # Extract key themes
            if 'how' in q:
                question_themes['how-to guides'] += 1
            if 'what' in q:
                question_themes['definitions/concepts'] += 1
            if 'why' in q:
                question_themes['rationale/reasoning'] += 1
            if any(word in q for word in ['example', 'sample', 'template']):
                question_themes['examples/templates'] += 1
            if any(word in q for word in ['best', 'practice', 'recommend']):
                question_themes['best practices'] += 1

        # Build FAQ suggestions
        suggested_faqs = []
        for theme, count in question_themes.most_common(5):
            if count >= 2:
                suggestion_map = {
                    'how-to guides': 'Create step-by-step how-to guides',
                    'definitions/concepts': 'Add a glossary or concept definitions',
                    'rationale/reasoning': 'Document decision rationale and reasoning',
                    'examples/templates': 'Provide more examples and templates',
                    'best practices': 'Compile best practices documentation'
                }
                suggested_faqs.append({
                    'topic': theme,
                    'count': count,
                    'suggestion': suggestion_map.get(theme, f'Create resources for {theme}')
                })

        # Count domain keywords found
        domain_keyword_count = sum(1 for k in keywords if k['is_domain_keyword'])

        # Format date range
        date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

        logger.info(f"📊 Keyword trends: {len(keywords)} keywords, {len(questions)} questions, {domain_keyword_count} L&D terms")

        return {
            'keywords': keywords,
            'questions': questions[:20],  # Most recent 20
            'message_count': len(messages),
            'date_range': date_range,
            'domain_keyword_count': domain_keyword_count,
            'suggested_faqs': suggested_faqs
        }

    except Exception as e:
        logger.error(f"❌ Keyword trends error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/export")
async def export_conversations(
    current_user: dict = Depends(require_admin),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    format: str = Query("json", description="Export format: json or txt")
):
    """
    Export all conversations with messages.

    Optional date filters to limit the export range.
    Returns a downloadable file with all conversation data.
    """
    try:
        # Build base query for conversations
        query = supabase.table('conversations').select('''
            *,
            users:user_id(id, name, email),
            clients:client_id(id, name)
        ''')

        # Apply date filters if provided
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.gte('created_at', start_dt.isoformat())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                # Add one day to include the end date fully
                end_dt = end_dt + timedelta(days=1)
                query = query.lt('created_at', end_dt.isoformat())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

        # Execute query
        result = await asyncio.to_thread(
            lambda: query.order('created_at', desc=True).execute()
        )

        conversations = result.data or []
        logger.info(f"📥 Exporting {len(conversations)} conversations")

        # Fetch messages for each conversation
        export_data = []
        for conv in conversations:
            # Get messages for this conversation
            messages_result = await asyncio.to_thread(
                lambda c=conv: supabase.table('messages')
                    .select('id, role, content, timestamp, metadata')
                    .eq('conversation_id', c['id'])
                    .order('timestamp')
                    .execute()
            )

            messages = messages_result.data or []

            export_data.append({
                'conversation_id': conv['id'],
                'title': conv.get('title', 'Untitled'),
                'created_at': conv.get('created_at'),
                'updated_at': conv.get('updated_at'),
                'user': {
                    'id': conv.get('users', {}).get('id') if conv.get('users') else None,
                    'name': conv.get('users', {}).get('name') if conv.get('users') else 'Unknown',
                    'email': conv.get('users', {}).get('email') if conv.get('users') else None
                },
                'client': {
                    'id': conv.get('clients', {}).get('id') if conv.get('clients') else None,
                    'name': conv.get('clients', {}).get('name') if conv.get('clients') else 'Unknown'
                },
                'message_count': len(messages),
                'messages': [
                    {
                        'id': msg['id'],
                        'role': msg['role'],
                        'content': msg['content'],
                        'timestamp': msg['timestamp']
                    }
                    for msg in messages
                ]
            })

        # Generate filename with date range
        date_suffix = ""
        if start_date or end_date:
            date_suffix = f"_{start_date or 'start'}_to_{end_date or 'now'}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "txt":
            # Generate plain text format
            text_output = []
            text_output.append("=" * 80)
            text_output.append("CONVERSATION HISTORY EXPORT")
            text_output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if start_date:
                text_output.append(f"From: {start_date}")
            if end_date:
                text_output.append(f"To: {end_date}")
            text_output.append(f"Total Conversations: {len(export_data)}")
            text_output.append("=" * 80)
            text_output.append("")

            for conv in export_data:
                text_output.append("-" * 80)
                text_output.append(f"Conversation: {conv['title']}")
                text_output.append(f"ID: {conv['conversation_id']}")
                text_output.append(f"User: {conv['user']['name']} ({conv['user']['email']})")
                text_output.append(f"Client: {conv['client']['name']}")
                text_output.append(f"Created: {conv['created_at']}")
                text_output.append(f"Messages: {conv['message_count']}")
                text_output.append("-" * 80)
                text_output.append("")

                for msg in conv['messages']:
                    role_label = "USER" if msg['role'] == 'user' else "ASSISTANT"
                    text_output.append(f"[{msg['timestamp']}] {role_label}:")
                    text_output.append(msg['content'])
                    text_output.append("")

                text_output.append("")

            content = "\n".join(text_output)
            filename = f"conversation_export{date_suffix}_{timestamp}.txt"

            return StreamingResponse(
                io.BytesIO(content.encode('utf-8')),
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # JSON format (default)
            export_json = {
                'export_info': {
                    'generated_at': datetime.now().isoformat(),
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_conversations': len(export_data),
                    'total_messages': sum(c['message_count'] for c in export_data)
                },
                'conversations': export_data
            }

            content = json.dumps(export_json, indent=2, default=str)
            filename = f"conversation_export{date_suffix}_{timestamp}.json"

            return StreamingResponse(
                io.BytesIO(content.encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Export conversations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
