"""
Graph API Routes

Provides REST endpoints for graph queries and management.
Used for stakeholder network analysis, influence mapping, and blocker detection.
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import get_current_user
from services.graph import (
    get_neo4j_connection,
    GraphSyncService,
    GraphQueryService,
    RelationshipExtractor,
    initialize_schema,
    verify_schema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["graph"])


# =============================================================================
# Pydantic Models
# =============================================================================

class SyncRequest(BaseModel):
    """Request to sync data to graph."""
    entity_types: Optional[list[str]] = None
    since: Optional[datetime] = None


class SyncResponse(BaseModel):
    """Response from sync operation."""
    status: str
    client_id: str
    results: dict


class NetworkResponse(BaseModel):
    """Stakeholder network response."""
    center: Optional[dict]
    connected: list[dict]
    connection_count: int


class InfluencePathResponse(BaseModel):
    """Influence path between stakeholders."""
    found: bool
    path: Optional[dict] = None
    message: Optional[str] = None


class BlockerResponse(BaseModel):
    """ROI blocker analysis response."""
    opportunity_id: str
    blockers: list[dict]
    supporters: list[dict]
    strategy: Optional[dict] = None


class GraphStatsResponse(BaseModel):
    """Graph statistics response."""
    nodes: dict
    relationships: dict


# =============================================================================
# Dependency Injection
# =============================================================================

async def get_graph_query_service():
    """Get the graph query service."""
    try:
        connection = await get_neo4j_connection()
        return GraphQueryService(connection)
    except Exception as e:
        logger.error(f"Failed to get graph query service: {e}")
        raise HTTPException(
            status_code=503,
            detail="Graph service unavailable. Check Neo4j connection."
        )


async def get_graph_sync_service(current_user: dict = Depends(get_current_user)):
    """Get the graph sync service."""
    try:
        from database import get_supabase
        supabase = get_supabase()
        connection = await get_neo4j_connection()
        return GraphSyncService(supabase, connection)
    except Exception as e:
        logger.error(f"Failed to get graph sync service: {e}")
        raise HTTPException(
            status_code=503,
            detail="Graph sync service unavailable."
        )


# =============================================================================
# Health & Admin Endpoints
# =============================================================================

@router.get("/health")
async def graph_health():
    """
    Check Neo4j connection health.
    """
    try:
        connection = await get_neo4j_connection()
        health = await connection.health_check()
        return health
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/schema/init")
async def init_schema(current_user: dict = Depends(get_current_user)):
    """
    Initialize the graph schema (constraints and indexes).

    Requires admin privileges.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        connection = await get_neo4j_connection()
        result = await initialize_schema(connection)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Schema initialization failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/schema/verify")
async def verify_graph_schema(current_user: dict = Depends(get_current_user)):
    """
    Verify the current graph schema state.
    """
    try:
        connection = await get_neo4j_connection()
        result = await verify_schema(connection)
        return result
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/stats")
async def get_stats(
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Get graph statistics for the current user's client.
    """
    try:
        stats = await query_service.get_graph_stats(current_user["client_id"])
        return GraphStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# =============================================================================
# Sync Endpoints
# =============================================================================

@router.post("/sync/full", response_model=SyncResponse)
async def full_sync(
    current_user: dict = Depends(get_current_user),
    sync_service: GraphSyncService = Depends(get_graph_sync_service)
):
    """
    Perform a full sync of all data to the graph.

    This syncs stakeholders, meetings, insights, documents, and ROI opportunities.
    """
    try:
        result = await sync_service.full_sync(current_user["client_id"])
        return SyncResponse(
            status="completed",
            client_id=current_user["client_id"],
            results=result
        )
    except Exception as e:
        logger.error(f"Full sync failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/sync/incremental", response_model=SyncResponse)
async def incremental_sync(
    request: SyncRequest,
    current_user: dict = Depends(get_current_user),
    sync_service: GraphSyncService = Depends(get_graph_sync_service)
):
    """
    Perform an incremental sync for recently updated entities.
    """
    try:
        since = request.since or datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        result = await sync_service.incremental_sync(
            current_user["client_id"],
            since=since,
            entity_types=request.entity_types
        )
        return SyncResponse(
            status="completed",
            client_id=current_user["client_id"],
            results=result
        )
    except Exception as e:
        logger.error(f"Incremental sync failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/sync/stakeholders")
async def sync_stakeholders(
    current_user: dict = Depends(get_current_user),
    sync_service: GraphSyncService = Depends(get_graph_sync_service)
):
    """
    Sync only stakeholders and their relationships.
    """
    try:
        result = await sync_service.sync_stakeholders(current_user["client_id"])
        return {"status": "completed", "result": result}
    except Exception as e:
        logger.error(f"Stakeholder sync failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# =============================================================================
# Stakeholder Network Endpoints
# =============================================================================

@router.get("/stakeholder/{stakeholder_id}/network")
async def get_stakeholder_network(
    stakeholder_id: str,
    depth: int = Query(default=2, ge=1, le=4),
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Get the network around a stakeholder.

    Args:
        stakeholder_id: The stakeholder ID
        depth: How many hops to include (1-4)
    """
    try:
        network = await query_service.get_stakeholder_network(stakeholder_id, depth)
        return network
    except Exception as e:
        logger.error(f"Failed to get stakeholder network: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/influence/path")
async def get_influence_path(
    from_id: str = Query(..., description="Source stakeholder ID"),
    to_id: str = Query(..., description="Target stakeholder ID"),
    max_depth: int = Query(default=5, ge=1, le=10),
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Find the influence path between two stakeholders.
    """
    try:
        result = await query_service.get_influence_path(from_id, to_id, max_depth)
        return result
    except Exception as e:
        logger.error(f"Failed to find influence path: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/influence/key-influencers")
async def get_key_influencers(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Find the most influential stakeholders in the network.
    """
    try:
        influencers = await query_service.find_key_influencers(
            current_user["client_id"],
            limit
        )
        return {"influencers": influencers}
    except Exception as e:
        logger.error(f"Failed to find key influencers: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/influence/chains/{target_id}")
async def get_influence_chains(
    target_id: str,
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Find all stakeholders who can influence a target through chains.
    """
    try:
        chains = await query_service.find_influence_chains(
            current_user["client_id"],
            target_id
        )
        return {"target_id": target_id, "influence_chains": chains}
    except Exception as e:
        logger.error(f"Failed to find influence chains: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# =============================================================================
# ROI & Blocker Endpoints
# =============================================================================

@router.get("/roi/{opportunity_id}/analysis")
async def get_roi_analysis(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Get full analysis of an ROI opportunity including blockers and supporters.
    """
    try:
        blockers = await query_service.get_roi_blockers(opportunity_id)
        supporters = await query_service.get_roi_supporters(opportunity_id)
        strategy = await query_service.suggest_blocker_strategy(opportunity_id)

        return BlockerResponse(
            opportunity_id=opportunity_id,
            blockers=blockers,
            supporters=supporters,
            strategy=strategy
        )
    except Exception as e:
        logger.error(f"Failed to get ROI analysis: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/roi/{opportunity_id}/blockers")
async def get_roi_blockers(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Get stakeholders blocking an ROI opportunity.
    """
    try:
        blockers = await query_service.get_roi_blockers(opportunity_id)
        return {"opportunity_id": opportunity_id, "blockers": blockers}
    except Exception as e:
        logger.error(f"Failed to get ROI blockers: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/roi/{opportunity_id}/strategy")
async def get_blocker_strategy(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Get recommended strategy for addressing blockers.
    """
    try:
        strategy = await query_service.suggest_blocker_strategy(opportunity_id)
        return strategy
    except Exception as e:
        logger.error(f"Failed to get blocker strategy: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# =============================================================================
# Concern Endpoints
# =============================================================================

@router.get("/concerns/shared")
async def get_shared_concerns(
    min_stakeholders: int = Query(default=2, ge=2),
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Find concerns shared by multiple stakeholders.
    """
    try:
        concerns = await query_service.find_shared_concerns(
            current_user["client_id"],
            min_stakeholders
        )
        return {"shared_concerns": concerns}
    except Exception as e:
        logger.error(f"Failed to find shared concerns: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/stakeholder/{stakeholder_id}/concerns")
async def get_stakeholder_concerns(
    stakeholder_id: str,
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Get all concerns raised by a stakeholder.
    """
    try:
        concerns = await query_service.get_stakeholder_concerns(stakeholder_id)
        return {"stakeholder_id": stakeholder_id, "concerns": concerns}
    except Exception as e:
        logger.error(f"Failed to get stakeholder concerns: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# =============================================================================
# Meeting & Alignment Endpoints
# =============================================================================

@router.get("/meeting/{meeting_id}/network")
async def get_meeting_network(
    meeting_id: str,
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Get the stakeholder network from a meeting.
    """
    try:
        network = await query_service.get_meeting_network(meeting_id)
        return network
    except Exception as e:
        logger.error(f"Failed to get meeting network: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/concepts/{concept_name}/advocates")
async def get_concept_advocates(
    concept_name: str,
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Find stakeholders who advocate for a concept.
    """
    try:
        advocates = await query_service.find_concept_advocates(
            concept_name,
            current_user["client_id"]
        )
        return {"concept": concept_name, "advocates": advocates}
    except Exception as e:
        logger.error(f"Failed to find concept advocates: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/stakeholder/{stakeholder_id}/aligned")
async def get_aligned_stakeholders(
    stakeholder_id: str,
    min_shared_meetings: int = Query(default=2, ge=1),
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Find stakeholders aligned with a given stakeholder.
    """
    try:
        aligned = await query_service.find_aligned_stakeholders(
            stakeholder_id,
            min_shared_meetings
        )
        return {"stakeholder_id": stakeholder_id, "aligned": aligned}
    except Exception as e:
        logger.error(f"Failed to find aligned stakeholders: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# =============================================================================
# Agent Routing Endpoints
# =============================================================================

@router.get("/agents/routing")
async def get_agent_routing_suggestion(
    question: str = Query(..., description="The user's question"),
    current_agent_id: Optional[str] = Query(default=None, description="Current agent ID"),
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Suggest the best agent to handle a question based on expertise.

    Uses the agent expertise graph to match question topics to agent capabilities.
    """
    try:
        suggestion = await query_service.suggest_agent_for_question(
            question,
            current_agent_id
        )
        return suggestion
    except Exception as e:
        logger.error(f"Failed to get agent routing suggestion: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/agents/{agent_id}/expertise")
async def get_agent_expertise(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Get the expertise areas for a specific agent.
    """
    try:
        expertise = await query_service.get_agent_expertise(agent_id)
        return expertise
    except Exception as e:
        logger.error(f"Failed to get agent expertise: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/agents/handoff-patterns")
async def get_handoff_patterns(
    current_user: dict = Depends(get_current_user),
    query_service: GraphQueryService = Depends(get_graph_query_service)
):
    """
    Get agent handoff patterns and frequencies.

    Useful for understanding agent collaboration flows.
    """
    try:
        patterns = await query_service.get_agent_handoff_patterns()
        return {"patterns": patterns}
    except Exception as e:
        logger.error(f"Failed to get handoff patterns: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# =============================================================================
# Relationship Inference Endpoints
# =============================================================================

async def get_relationship_extractor(current_user: dict = Depends(get_current_user)):
    """Get the relationship extractor service."""
    try:
        from database import get_supabase
        supabase = get_supabase()
        connection = await get_neo4j_connection()
        return RelationshipExtractor(supabase, connection)
    except Exception as e:
        logger.error(f"Failed to get relationship extractor: {e}")
        raise HTTPException(
            status_code=503,
            detail="Relationship extractor unavailable."
        )


@router.post("/infer/influences")
async def infer_influences(
    current_user: dict = Depends(get_current_user),
    extractor: RelationshipExtractor = Depends(get_relationship_extractor)
):
    """
    Infer influence relationships from meeting co-attendance patterns.

    Analyzes which stakeholders attend meetings together and their roles
    to infer who influences whom.
    """
    try:
        result = await extractor.infer_influences(current_user["client_id"])
        return {
            "status": "completed",
            "client_id": current_user["client_id"],
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to infer influences: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/infer/concepts")
async def extract_all_concepts(
    current_user: dict = Depends(get_current_user),
    extractor: RelationshipExtractor = Depends(get_relationship_extractor)
):
    """
    Extract concepts from all meeting transcripts.

    Uses LLM to identify key topics discussed in each meeting and creates
    DISCUSSES relationships between meetings and concepts.
    """
    try:
        result = await extractor.extract_all_meeting_concepts(current_user["client_id"])
        return {
            "status": "completed",
            "client_id": current_user["client_id"],
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to extract concepts: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/infer/clusters")
async def detect_stakeholder_clusters(
    current_user: dict = Depends(get_current_user),
    extractor: RelationshipExtractor = Depends(get_relationship_extractor)
):
    """
    Detect natural clusters of stakeholders.

    Identifies groups of stakeholders who share concerns or frequently
    attend meetings together.
    """
    try:
        result = await extractor.detect_stakeholder_clusters(current_user["client_id"])
        return {
            "status": "completed",
            "client_id": current_user["client_id"],
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to detect clusters: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.post("/meetings/{meeting_id}/concepts")
async def extract_meeting_concepts(
    meeting_id: str,
    current_user: dict = Depends(get_current_user),
    extractor: RelationshipExtractor = Depends(get_relationship_extractor)
):
    """
    Extract concepts from a specific meeting transcript.
    """
    try:
        result = await extractor.extract_concepts_from_meeting(meeting_id)
        return {
            "status": "completed",
            "meeting_id": meeting_id,
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to extract concepts from meeting: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# =============================================================================
# Scheduler Management Endpoints
# =============================================================================

@router.get("/sync/scheduler-status")
async def get_scheduler_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the status of the graph sync scheduler.
    """
    try:
        from services.graph_sync_scheduler import get_graph_scheduler_status
        status = get_graph_scheduler_status()
        return {
            "success": True,
            **status
        }
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        return {
            "success": False,
            "running": False,
            "error": str(e)
        }


@router.post("/sync/trigger")
async def trigger_sync(
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger an immediate graph sync for the current user's client.
    This runs asynchronously in the background.
    """
    try:
        from services.graph_sync_scheduler import trigger_manual_sync
        result = trigger_manual_sync()
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


# =============================================================================
# Visualization Endpoints
# =============================================================================

@router.get("/visualization")
async def get_visualization_data(
    limit: int = Query(default=500, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """
    Get graph data formatted for visualization (react-force-graph-2d).

    Returns nodes and links arrays suitable for force-directed graph rendering.
    """
    try:
        connection = await get_neo4j_connection()
        client_id = current_user["client_id"]

        # Query all nodes and relationships for this client
        # Include global nodes (Agents, Expertise) and connected nodes (Chunks, Messages)
        result = await connection.execute_query("""
            // Get client-specific nodes and global nodes
            MATCH (n)
            WHERE n.client_id = $client_id OR n:Agent OR n:Expertise
            WITH collect(DISTINCT n) as baseNodes

            // Also get nodes connected to client nodes (like Chunks connected to Documents)
            UNWIND baseNodes as bn
            OPTIONAL MATCH (connected)-[:PART_OF|BELONGS_TO|IN_CONVERSATION]->(bn)
            WITH baseNodes, collect(DISTINCT connected) as connectedNodes

            // Combine all nodes
            WITH baseNodes + [n IN connectedNodes WHERE n IS NOT NULL] as allNodes

            // Deduplicate
            UNWIND allNodes as node
            WITH collect(DISTINCT node) as nodes

            // Get relationships between these nodes
            UNWIND nodes as n
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE m IN nodes

            WITH nodes, collect(DISTINCT {
                source: id(startNode(r)),
                target: id(endNode(r)),
                type: type(r),
                sourceId: startNode(r).id,
                targetId: endNode(r).id
            }) as rels

            // Format nodes for visualization
            UNWIND nodes as node
            WITH rels, collect(DISTINCT {
                id: node.id,
                neo4jId: id(node),
                label: labels(node)[0],
                name: COALESCE(node.name, node.display_name, node.filename, node.title, labels(node)[0]),
                properties: properties(node)
            }) as formattedNodes

            RETURN formattedNodes as nodes,
                   [r IN rels WHERE r.source IS NOT NULL | {
                       source: r.sourceId,
                       target: r.targetId,
                       type: r.type
                   }] as links
        """, {"client_id": client_id})

        if result and len(result) > 0:
            data = result[0]
            nodes = data.get("nodes", [])
            links = data.get("links", [])

            # Apply limit to nodes if needed
            if len(nodes) > limit:
                nodes = nodes[:limit]
                # Filter links to only include those between limited nodes
                node_ids = {n["id"] for n in nodes}
                links = [l for l in links if l["source"] in node_ids and l["target"] in node_ids]

            return {
                "nodes": nodes,
                "links": links,
                "total_nodes": len(nodes),
                "total_links": len(links)
            }

        return {
            "nodes": [],
            "links": [],
            "total_nodes": 0,
            "total_links": 0
        }

    except Exception as e:
        logger.error(f"Failed to get visualization data: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")
