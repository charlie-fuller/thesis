"""Project Context Service.

Provides vector search and context retrieval for AI projects.
Used by the project detail modal to show related documents
and provide context for the Q&A feature.

Key feature: Documents are searched using scoring-focused queries to find
evidence that supports or explains the project's scoring rationale.
"""

from typing import Dict, List, Optional

from document_processor import search_similar_chunks
from logger_config import get_logger

logger = get_logger(__name__)

# Scoring dimension descriptions for building focused search queries
SCORING_DIMENSIONS = {
    "roi_potential": {
        "name": "ROI Potential",
        "search_terms": "ROI revenue cost savings time savings efficiency gains business value financial impact",
    },
    "implementation_effort": {
        "name": "Implementation Effort",
        "search_terms": "implementation complexity integration technical requirements resources effort timeline",
    },
    "strategic_alignment": {
        "name": "Strategic Alignment",
        "search_terms": "strategy goals priorities objectives alignment business direction vision",
    },
    "stakeholder_readiness": {
        "name": "Stakeholder Readiness",
        "search_terms": "stakeholder champion adoption readiness support engagement buy-in team",
    },
}


def get_scoring_related_documents(
    project: Dict, client_id: str, limit: int = 8, min_similarity: float = 0.25
) -> List[Dict]:
    """Find documents that support the scoring rationale for a project.

    Builds search queries focused on the scoring dimensions (ROI, effort,
    strategic alignment, stakeholder readiness) rather than just the
    title/description. This helps answer "why" the project is scored
    the way it is.

    Args:
        project: Full project dict with all fields
        client_id: Client ID to filter results
        limit: Maximum number of results (default: 8)
        min_similarity: Minimum similarity score (default: 0.25)

    Returns:
        List of document chunks with relevance to scoring, formatted for frontend
    """
    title = project.get("title", "")
    project.get("description", "")
    department = project.get("department", "")
    current_state = project.get("current_state", "")
    desired_state = project.get("desired_state", "")

    # Build a scoring-focused search query
    # Combine project context with scoring dimension keywords
    query_parts = []

    # Core project context
    if title:
        query_parts.append(title)
    if department:
        query_parts.append(f"{department} department")

    # Add scoring-relevant context
    if current_state:
        query_parts.append(f"current problems: {current_state[:200]}")
    if desired_state:
        query_parts.append(f"target outcomes: {desired_state[:200]}")

    # Add ROI indicators if present
    roi_indicators = project.get("roi_indicators", {})
    if roi_indicators:
        roi_terms = []
        if roi_indicators.get("time_savings_percent"):
            roi_terms.append(f"time savings {roi_indicators['time_savings_percent']}%")
        if roi_indicators.get("cost_savings_annual"):
            roi_terms.append(f"cost savings {roi_indicators['cost_savings_annual']}")
        if roi_indicators.get("hours_saved_weekly"):
            roi_terms.append(f"{roi_indicators['hours_saved_weekly']} hours saved")
        if roi_terms:
            query_parts.append(" ".join(roi_terms))

    # Add general scoring terms to help find relevant evidence
    query_parts.append("AI implementation project ROI business case stakeholder")

    search_query = " ".join(query_parts)

    logger.info(f"Searching for scoring-relevant documents for: {title[:50]}...")
    logger.debug(f"Query: {search_query[:200]}...")

    try:
        # Search using existing vector search function
        chunks = search_similar_chunks(
            query=search_query,
            client_id=client_id,
            limit=limit * 2,  # Get more to allow deduplication
            include_conversations=False,  # Only documents, not chat history
            min_similarity=min_similarity,
        )

        # Format results for frontend SourceDocument interface
        # Deduplicate by document_id but keep highest scoring chunk per doc
        doc_chunks = {}  # document_id -> best chunk

        for chunk in chunks:
            doc_id = chunk.get("document_id")
            if not doc_id:
                continue

            similarity = chunk.get("similarity", 0.0)

            # Keep only the highest-scoring chunk per document
            if doc_id not in doc_chunks or similarity > doc_chunks[doc_id].get("similarity", 0.0):
                doc_chunks[doc_id] = chunk

        # Sort by similarity and take top N
        sorted_docs = sorted(doc_chunks.values(), key=lambda x: x.get("similarity", 0.0), reverse=True)[:limit]

        # Format for frontend
        formatted_results = []
        for chunk in sorted_docs:
            # Extract metadata from JSONB field
            metadata = chunk.get("metadata", {}) or {}

            # Get document name from metadata.filename or fallback
            doc_name = metadata.get("filename") or metadata.get("title") or "Unknown Document"

            formatted_results.append(
                {
                    "chunk_id": chunk.get("id", ""),
                    "document_id": chunk.get("document_id"),
                    "document_name": doc_name,
                    "relevance_score": chunk.get("similarity", 0.0),
                    "snippet": chunk.get("content", "")[:500],
                    "metadata": {
                        "filename": metadata.get("filename"),
                        "page_number": metadata.get("page_number"),
                        "source_type": chunk.get("source_type") or metadata.get("source_type"),
                        "storage_path": metadata.get("storage_path"),
                    },
                }
            )

        logger.info(f"Found {len(formatted_results)} scoring-relevant documents")
        return formatted_results

    except Exception as e:
        logger.error(f"Error searching for scoring-related documents: {e}")
        return []


def get_related_documents(
    project_title: str,
    project_description: Optional[str],
    client_id: str,
    limit: int = 5,
    min_similarity: float = 0.3,
) -> List[Dict]:
    """Find documents related to a project using vector search.

    (Legacy function - prefer get_scoring_related_documents for detail modal).

    Builds a search query from the project's title and description,
    then searches the knowledge base for relevant document chunks.

    Args:
        project_title: The project title
        project_description: Optional project description
        client_id: Client ID to filter results
        limit: Maximum number of results (default: 5)
        min_similarity: Minimum similarity score (default: 0.3)

    Returns:
        List of document chunks with source information formatted for frontend
    """
    # Build search query from project data
    query_parts = [project_title]
    if project_description:
        # Limit description to first 500 chars to avoid overly long queries
        query_parts.append(project_description[:500])

    search_query = " ".join(query_parts)

    logger.info(f"Searching for documents related to project: {project_title[:50]}...")

    try:
        # Search using existing vector search function
        chunks = search_similar_chunks(
            query=search_query,
            client_id=client_id,
            limit=limit,
            include_conversations=False,  # Only documents, not chat history
            min_similarity=min_similarity,
        )

        # Format results for frontend SourceDocument interface
        formatted_results = []
        seen_docs = set()  # Deduplicate by document_id

        for chunk in chunks:
            doc_id = chunk.get("document_id")

            # Skip if we've already included a chunk from this document
            if doc_id in seen_docs:
                continue
            seen_docs.add(doc_id)

            # Extract metadata from JSONB field
            metadata = chunk.get("metadata", {}) or {}

            # Get document name from metadata.filename or fallback
            doc_name = metadata.get("filename") or metadata.get("title") or "Unknown Document"

            formatted_results.append(
                {
                    "chunk_id": chunk.get("id", ""),
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "relevance_score": chunk.get("similarity", 0.0),
                    "snippet": chunk.get("content", "")[:500],  # First 500 chars
                    "metadata": {
                        "filename": metadata.get("filename"),
                        "page_number": metadata.get("page_number"),
                        "source_type": chunk.get("source_type") or metadata.get("source_type"),
                        "storage_path": metadata.get("storage_path"),
                    },
                }
            )

        logger.info(f"Found {len(formatted_results)} related documents for project")
        return formatted_results

    except Exception as e:
        logger.error(f"Error searching for related documents: {e}")
        return []


def build_project_context(project: Dict, related_documents: List[Dict]) -> str:
    """Build a context string for Claude containing project details.

    and related document content.

    Args:
        project: The project data dict
        related_documents: List of related document chunks

    Returns:
        Formatted context string for inclusion in Claude prompt
    """
    context_parts = []

    # Project details section
    context_parts.append("<project_context>")
    context_parts.append(f"Project ID: {project.get('id', 'Unknown')}")
    context_parts.append(f"Title: {project.get('title', 'Unknown')}")
    context_parts.append(f"Code: {project.get('project_code', 'N/A')}")
    context_parts.append(f"Department: {project.get('department', 'Not specified')}")
    context_parts.append(f"Status: {project.get('status', 'Unknown')}")

    # Scoring
    context_parts.append("\nScoring (1-5 scale, max 20 total):")
    context_parts.append(f"  - ROI Potential: {project.get('roi_potential', 'Not scored')}/5")
    context_parts.append(f"  - Implementation Effort: {project.get('implementation_effort', 'Not scored')}/5")
    context_parts.append(f"  - Strategic Alignment: {project.get('strategic_alignment', 'Not scored')}/5")
    context_parts.append(f"  - Stakeholder Readiness: {project.get('stakeholder_readiness', 'Not scored')}/5")
    context_parts.append(f"  - Total Score: {project.get('total_score', 0)}/20")
    context_parts.append(f"  - Tier: {project.get('tier', 4)}")

    if project.get("description"):
        context_parts.append(f"\nDescription: {project['description']}")

    if project.get("current_state"):
        context_parts.append(f"\nCurrent State: {project['current_state']}")

    if project.get("desired_state"):
        context_parts.append(f"\nDesired State: {project['desired_state']}")

    if project.get("next_step"):
        context_parts.append(f"\nNext Step: {project['next_step']}")

    blockers = project.get("blockers", [])
    if blockers:
        context_parts.append(f"\nBlockers: {', '.join(blockers)}")

    roi_indicators = project.get("roi_indicators", {})
    if roi_indicators:
        context_parts.append(f"\nROI Indicators: {roi_indicators}")

    context_parts.append("</project_context>")

    # Related documents section
    if related_documents:
        context_parts.append("\n<related_knowledge_base_documents>")
        for i, doc in enumerate(related_documents, 1):
            context_parts.append(f"\n[Source {i} - {doc.get('document_name', 'Unknown')}]")
            context_parts.append(doc.get("snippet", ""))
        context_parts.append("\n</related_knowledge_base_documents>")

    return "\n".join(context_parts)


def build_task_context(tasks: List[Dict]) -> str:
    """Build a <project_tasks> XML block from a list of task dicts.

    Args:
        tasks: List of task dicts from the project_tasks table

    Returns:
        Formatted XML string for injection into agent prompt
    """
    if not tasks:
        return ""

    STATUS_MAP = {
        "pending": "TODO",
        "in_progress": "IN PROGRESS",
        "blocked": "BLOCKED",
        "completed": "DONE",
    }

    lines = ["<project_tasks>"]
    for t in tasks[:30]:
        status = STATUS_MAP.get(t.get("status", ""), t.get("status", "unknown")).upper()
        priority = t.get("priority", 3)
        title = t.get("title", "Untitled")
        task_id = t.get("id", "")
        parts = [f"- [{status}] (id={task_id}) P{priority}: {title}"]

        assignee = t.get("assignee_name")
        if assignee:
            parts.append(f"[assigned: {assignee}]")

        due = t.get("due_date")
        if due:
            parts.append(f"[due: {due}]")

        blocker = t.get("blocker_reason")
        if blocker:
            parts.append(f"[blocked: {blocker}]")

        lines.append(" ".join(parts))

    lines.append("</project_tasks>")
    return "\n".join(lines)


def build_doc_digest_context(docs: List[Dict]) -> str:
    """Build a <project_kb_documents> XML block from document digest dicts.

    Args:
        docs: List of {id, title, digest} dicts from get_project_document_digests()

    Returns:
        Formatted XML string for injection into agent prompt
    """
    if not docs:
        return ""

    lines = ["<project_kb_documents>"]
    for d in docs[:20]:
        title = d.get("title", "Untitled")
        doc_id = d.get("id", "")
        digest = d.get("digest") or "No summary available"
        lines.append(f"[Document: {title}] (id={doc_id})")
        lines.append(f"Summary: {digest}")
        lines.append("")

    lines.append("</project_kb_documents>")
    return "\n".join(lines)
