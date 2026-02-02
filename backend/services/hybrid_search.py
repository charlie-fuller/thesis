"""Hybrid Search Service - Combines Vector Search + Graph Context.

This service enhances RAG (Retrieval Augmented Generation) by combining:
1. Vector similarity search (PostgreSQL + Voyage AI embeddings)
2. Graph context (Neo4j stakeholders, concerns, ROI opportunities)

The graph context provides relationship-based insights that pure semantic
search may miss, especially for stakeholder-related queries.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from document_processor import search_similar_chunks
from services.graph.connection import get_neo4j_connection
from services.graph.query_service import GraphQueryService

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """Result of hybrid vector + graph search."""

    # Vector search results (document chunks)
    vector_chunks: list[dict[str, Any]] = field(default_factory=list)

    # Graph context
    stakeholders: list[dict[str, Any]] = field(default_factory=list)
    concerns: list[dict[str, Any]] = field(default_factory=list)
    roi_opportunities: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    stakeholder_documents: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    keywords_detected: list[str] = field(default_factory=list)
    used_graph_context: bool = False

    @property
    def has_vector_results(self) -> bool:
        return len(self.vector_chunks) > 0

    @property
    def has_graph_context(self) -> bool:
        return (
            len(self.stakeholders) > 0
            or len(self.concerns) > 0
            or len(self.roi_opportunities) > 0
            or len(self.relationships) > 0
        )

    def to_context_string(self) -> str:
        """Format the hybrid results as a context string for prompts."""
        sections = []

        # Vector search results
        if self.vector_chunks:
            kb_parts = []
            for i, chunk in enumerate(self.vector_chunks):
                source_info = f"[Source {i + 1}"
                metadata = chunk.get("metadata", {})
                if metadata.get("filename"):
                    source_info += f" - {metadata['filename']}"
                source_info += f" - Relevance: {chunk.get('similarity', 0):.2f}]"
                kb_parts.append(f"{source_info}:\n{chunk['content']}")

            sections.append(
                "<knowledge_base_context>\n" + "\n\n".join(kb_parts) + "\n</knowledge_base_context>"
            )

        # Graph context
        graph_parts = []

        if self.stakeholders:
            stakeholder_lines = []
            for s in self.stakeholders[:5]:
                sentiment = s.get("sentiment_score") or 0.5
                sentiment_label = (
                    "positive" if sentiment > 0.6 else "neutral" if sentiment > 0.4 else "cautious"
                )
                stakeholder_lines.append(
                    f"- {s['name']} ({s.get('role', 'Unknown role')}) - {sentiment_label}"
                )
            graph_parts.append("RELEVANT STAKEHOLDERS:\n" + "\n".join(stakeholder_lines))

        if self.concerns:
            concern_lines = []
            for c in self.concerns[:5]:
                raisers = ", ".join([p["name"] for p in c.get("raised_by", [])])
                severity = c.get("severity", "unknown")
                content = c.get("content", "")[:100]
                concern_lines.append(f"- [{severity}] {content}... (raised by: {raisers})")
            graph_parts.append("SHARED CONCERNS:\n" + "\n".join(concern_lines))

        if self.roi_opportunities:
            roi_lines = []
            for o in self.roi_opportunities[:3]:
                value = o.get("estimated_value", "TBD")
                status = o.get("status", "unknown")
                blockers = ", ".join([b for b in (o.get("blockers") or []) if b][:3]) or "none"
                roi_lines.append(
                    f"- {o.get('name', 'Unnamed')}: ${value} ({status}) - blockers: {blockers}"
                )
            graph_parts.append("ROI OPPORTUNITIES:\n" + "\n".join(roi_lines))

        if self.relationships:
            rel_lines = []
            for r in self.relationships[:5]:
                rel_type = (r.get("relationship") or "relates_to").lower().replace("_", " ")
                rel_lines.append(f"- {r['from_name']} {rel_type} {r['to_name']}")
            graph_parts.append("STAKEHOLDER RELATIONSHIPS:\n" + "\n".join(rel_lines))

        if graph_parts:
            sections.append("<graph_context>\n" + "\n\n".join(graph_parts) + "\n</graph_context>")

        return "\n\n".join(sections)


def should_use_graph_context(query: str) -> bool:
    """Determine if a query would benefit from graph context.

    Graph context is useful for:
    - Stakeholder-related queries
    - ROI/opportunity discussions
    - Relationship and influence questions
    - Concern/blocker analysis
    """
    query_lower = query.lower()

    # Keywords that suggest graph context would help
    graph_keywords = [
        # Stakeholder-related
        "stakeholder",
        "person",
        "people",
        "who",
        "team",
        "department",
        "manager",
        "executive",
        "lead",
        "champion",
        "sponsor",
        "blocker",
        # Relationship-related
        "influence",
        "relationship",
        "network",
        "connected",
        "reports to",
        "works with",
        "collaborates",
        "aligned",
        "opposed",
        # ROI/opportunity-related
        "roi",
        "opportunity",
        "initiative",
        "project",
        "budget",
        "cost",
        "value",
        "benefit",
        "investment",
        "savings",
        # Concern-related
        "concern",
        "risk",
        "issue",
        "problem",
        "challenge",
        "objection",
        "resistance",
        "worried",
        "skeptic",
        # Sentiment-related
        "sentiment",
        "feeling",
        "attitude",
        "support",
        "opposition",
    ]

    for keyword in graph_keywords:
        if keyword in query_lower:
            return True

    return False


async def hybrid_search(
    query: str,
    client_id: str,
    limit: int = 5,
    include_conversations: bool = True,
    min_similarity: float = 0.0,
    user_id: Optional[str] = None,
    document_ids: Optional[list[str]] = None,
    conversation_id: Optional[str] = None,
    agent_ids: Optional[list[str]] = None,
    use_graph_context: Optional[bool] = None,  # None = auto-detect
    graph_limit: int = 5,
) -> HybridSearchResult:
    """Perform hybrid search combining vector similarity and graph context.

    Args:
        query: The search query
        client_id: Client ID for filtering
        limit: Maximum vector search results
        include_conversations: Whether to include conversation chunks
        min_similarity: Minimum similarity score
        user_id: Optional user ID filter
        document_ids: Optional document ID filter
        conversation_id: Optional conversation context
        agent_ids: Optional agent filter
        use_graph_context: Force graph context on/off (None = auto-detect)
        graph_limit: Maximum results per graph category

    Returns:
        HybridSearchResult with both vector and graph results
    """
    result = HybridSearchResult()

    # Vector search
    logger.info(f"[Hybrid Search] Vector search for: {query[:50]}...")
    vector_results = search_similar_chunks(
        query=query,
        client_id=client_id,
        limit=limit,
        include_conversations=include_conversations,
        min_similarity=min_similarity,
        user_id=user_id,
        document_ids=document_ids,
        conversation_id=conversation_id,
        agent_ids=agent_ids,
    )
    result.vector_chunks = vector_results
    logger.info(f"[Hybrid Search] Found {len(vector_results)} vector results")

    # Determine if we should use graph context
    if use_graph_context is None:
        use_graph_context = should_use_graph_context(query)

    if use_graph_context:
        logger.info("[Hybrid Search] Fetching graph context from Neo4j...")
        result.used_graph_context = True

        try:
            neo4j = await get_neo4j_connection()
            graph_service = GraphQueryService(neo4j)

            # Get graph context using the existing get_meeting_context method
            graph_context = await graph_service.get_meeting_context(
                query=query, client_id=client_id, limit=graph_limit
            )

            result.keywords_detected = graph_context.get("keywords_detected", [])
            result.stakeholders = graph_context.get("stakeholders", [])
            result.concerns = graph_context.get("concerns", [])
            result.roi_opportunities = graph_context.get("roi_opportunities", [])
            result.relationships = graph_context.get("relationships", [])
            result.stakeholder_documents = graph_context.get("stakeholder_documents", [])

            total_graph = (
                len(result.stakeholders)
                + len(result.concerns)
                + len(result.roi_opportunities)
                + len(result.relationships)
            )
            logger.info(f"[Hybrid Search] Found {total_graph} graph context items")

        except Exception as e:
            logger.warning(f"[Hybrid Search] Graph context fetch failed: {e}")
            # Continue without graph context - vector results still valid
    else:
        logger.info("[Hybrid Search] Skipping graph context (not relevant to query)")

    return result


async def get_hybrid_context_for_chat(
    query: str,
    client_id: str,
    limit: int = 5,
    user_id: Optional[str] = None,
    document_ids: Optional[list[str]] = None,
    conversation_id: Optional[str] = None,
    agent_ids: Optional[list[str]] = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Convenience function for chat routes - returns formatted context string
    and source document list.

    Args:
        Same as hybrid_search

    Returns:
        Tuple of (context_string, source_documents)
    """
    result = await hybrid_search(
        query=query,
        client_id=client_id,
        limit=limit,
        user_id=user_id,
        document_ids=document_ids,
        conversation_id=conversation_id,
        agent_ids=agent_ids,
    )

    # Build source documents list for frontend
    source_documents = []
    for i, chunk in enumerate(result.vector_chunks):
        metadata = chunk.get("metadata", {})
        source_documents.append(
            {
                "chunk_id": chunk.get("id", f"chunk_{i}"),
                "document_id": chunk.get("document_id", ""),
                "document_name": metadata.get(
                    "filename", metadata.get("conversation_title", "Unknown")
                ),
                "relevance_score": chunk.get("similarity", 0),
                "snippet": chunk.get("content", "")[:500],
                "metadata": metadata,
                "source_type": "vector",
            }
        )

    # Add stakeholder documents from graph as additional sources
    for doc in result.stakeholder_documents:
        doc_info = doc.get("document", {})
        source_documents.append(
            {
                "chunk_id": f"graph_{doc_info.get('id', 'unknown')}",
                "document_id": doc_info.get("id", ""),
                "document_name": doc_info.get("title") or doc_info.get("filename", "Unknown"),
                "relevance_score": 0.0,  # Graph docs don't have similarity scores
                "snippet": f"Related to stakeholder: {doc.get('stakeholder_name', 'Unknown')}",
                "metadata": doc_info,
                "source_type": "graph",
                "stakeholder_name": doc.get("stakeholder_name"),
            }
        )

    return result.to_context_string(), source_documents
