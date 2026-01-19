"""
Opportunity Context Service

Provides vector search and context retrieval for AI opportunities.
Used by the opportunity detail modal to show related documents
and provide context for the Q&A feature.

Key feature: Documents are searched using scoring-focused queries to find
evidence that supports or explains the opportunity's scoring rationale.
"""

from typing import Dict, List, Optional
from logger_config import get_logger
from document_processor import search_similar_chunks

logger = get_logger(__name__)

# Scoring dimension descriptions for building focused search queries
SCORING_DIMENSIONS = {
    'roi_potential': {
        'name': 'ROI Potential',
        'search_terms': 'ROI revenue cost savings time savings efficiency gains business value financial impact'
    },
    'implementation_effort': {
        'name': 'Implementation Effort',
        'search_terms': 'implementation complexity integration technical requirements resources effort timeline'
    },
    'strategic_alignment': {
        'name': 'Strategic Alignment',
        'search_terms': 'strategy goals priorities objectives alignment business direction vision'
    },
    'stakeholder_readiness': {
        'name': 'Stakeholder Readiness',
        'search_terms': 'stakeholder champion adoption readiness support engagement buy-in team'
    }
}


def get_scoring_related_documents(
    opportunity: Dict,
    client_id: str,
    limit: int = 8,
    min_similarity: float = 0.25
) -> List[Dict]:
    """
    Find documents that support the scoring rationale for an opportunity.

    Builds search queries focused on the scoring dimensions (ROI, effort,
    strategic alignment, stakeholder readiness) rather than just the
    title/description. This helps answer "why" the opportunity is scored
    the way it is.

    Args:
        opportunity: Full opportunity dict with all fields
        client_id: Client ID to filter results
        limit: Maximum number of results (default: 8)
        min_similarity: Minimum similarity score (default: 0.25)

    Returns:
        List of document chunks with relevance to scoring, formatted for frontend
    """
    title = opportunity.get('title', '')
    description = opportunity.get('description', '')
    department = opportunity.get('department', '')
    current_state = opportunity.get('current_state', '')
    desired_state = opportunity.get('desired_state', '')

    # Build a scoring-focused search query
    # Combine opportunity context with scoring dimension keywords
    query_parts = []

    # Core opportunity context
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
    roi_indicators = opportunity.get('roi_indicators', {})
    if roi_indicators:
        roi_terms = []
        if roi_indicators.get('time_savings_percent'):
            roi_terms.append(f"time savings {roi_indicators['time_savings_percent']}%")
        if roi_indicators.get('cost_savings_annual'):
            roi_terms.append(f"cost savings {roi_indicators['cost_savings_annual']}")
        if roi_indicators.get('hours_saved_weekly'):
            roi_terms.append(f"{roi_indicators['hours_saved_weekly']} hours saved")
        if roi_terms:
            query_parts.append(" ".join(roi_terms))

    # Add general scoring terms to help find relevant evidence
    query_parts.append("AI implementation opportunity ROI business case stakeholder")

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
            min_similarity=min_similarity
        )

        # Format results for frontend SourceDocument interface
        # Deduplicate by document_id but keep highest scoring chunk per doc
        doc_chunks = {}  # document_id -> best chunk

        for chunk in chunks:
            doc_id = chunk.get('document_id')
            if not doc_id:
                continue

            similarity = chunk.get('similarity', 0.0)

            # Keep only the highest-scoring chunk per document
            if doc_id not in doc_chunks or similarity > doc_chunks[doc_id].get('similarity', 0.0):
                doc_chunks[doc_id] = chunk

        # Sort by similarity and take top N
        sorted_docs = sorted(doc_chunks.values(), key=lambda x: x.get('similarity', 0.0), reverse=True)[:limit]

        # Format for frontend
        formatted_results = []
        for chunk in sorted_docs:
            # Extract metadata from JSONB field
            metadata = chunk.get('metadata', {}) or {}

            # Get document name from metadata.filename or fallback
            doc_name = metadata.get('filename') or metadata.get('title') or 'Unknown Document'

            formatted_results.append({
                'chunk_id': chunk.get('id', ''),
                'document_id': chunk.get('document_id'),
                'document_name': doc_name,
                'relevance_score': chunk.get('similarity', 0.0),
                'snippet': chunk.get('content', '')[:500],
                'metadata': {
                    'filename': metadata.get('filename'),
                    'page_number': metadata.get('page_number'),
                    'source_type': chunk.get('source_type') or metadata.get('source_type'),
                    'storage_path': metadata.get('storage_path')
                }
            })

        logger.info(f"Found {len(formatted_results)} scoring-relevant documents")
        return formatted_results

    except Exception as e:
        logger.error(f"Error searching for scoring-related documents: {e}")
        return []


def get_related_documents(
    opportunity_title: str,
    opportunity_description: Optional[str],
    client_id: str,
    limit: int = 5,
    min_similarity: float = 0.3
) -> List[Dict]:
    """
    Find documents related to an opportunity using vector search.
    (Legacy function - prefer get_scoring_related_documents for detail modal)

    Builds a search query from the opportunity's title and description,
    then searches the knowledge base for relevant document chunks.

    Args:
        opportunity_title: The opportunity title
        opportunity_description: Optional opportunity description
        client_id: Client ID to filter results
        limit: Maximum number of results (default: 5)
        min_similarity: Minimum similarity score (default: 0.3)

    Returns:
        List of document chunks with source information formatted for frontend
    """
    # Build search query from opportunity data
    query_parts = [opportunity_title]
    if opportunity_description:
        # Limit description to first 500 chars to avoid overly long queries
        query_parts.append(opportunity_description[:500])

    search_query = " ".join(query_parts)

    logger.info(f"Searching for documents related to opportunity: {opportunity_title[:50]}...")

    try:
        # Search using existing vector search function
        chunks = search_similar_chunks(
            query=search_query,
            client_id=client_id,
            limit=limit,
            include_conversations=False,  # Only documents, not chat history
            min_similarity=min_similarity
        )

        # Format results for frontend SourceDocument interface
        formatted_results = []
        seen_docs = set()  # Deduplicate by document_id

        for chunk in chunks:
            doc_id = chunk.get('document_id')

            # Skip if we've already included a chunk from this document
            if doc_id in seen_docs:
                continue
            seen_docs.add(doc_id)

            # Extract metadata from JSONB field
            metadata = chunk.get('metadata', {}) or {}

            # Get document name from metadata.filename or fallback
            doc_name = metadata.get('filename') or metadata.get('title') or 'Unknown Document'

            formatted_results.append({
                'chunk_id': chunk.get('id', ''),
                'document_id': doc_id,
                'document_name': doc_name,
                'relevance_score': chunk.get('similarity', 0.0),
                'snippet': chunk.get('content', '')[:500],  # First 500 chars
                'metadata': {
                    'filename': metadata.get('filename'),
                    'page_number': metadata.get('page_number'),
                    'source_type': chunk.get('source_type') or metadata.get('source_type'),
                    'storage_path': metadata.get('storage_path')
                }
            })

        logger.info(f"Found {len(formatted_results)} related documents for opportunity")
        return formatted_results

    except Exception as e:
        logger.error(f"Error searching for related documents: {e}")
        return []


def build_opportunity_context(
    opportunity: Dict,
    related_documents: List[Dict]
) -> str:
    """
    Build a context string for Claude containing opportunity details
    and related document content.

    Args:
        opportunity: The opportunity data dict
        related_documents: List of related document chunks

    Returns:
        Formatted context string for inclusion in Claude prompt
    """
    context_parts = []

    # Opportunity details section
    context_parts.append("<opportunity_context>")
    context_parts.append(f"Title: {opportunity.get('title', 'Unknown')}")
    context_parts.append(f"Code: {opportunity.get('opportunity_code', 'N/A')}")
    context_parts.append(f"Department: {opportunity.get('department', 'Not specified')}")
    context_parts.append(f"Status: {opportunity.get('status', 'Unknown')}")

    # Scoring
    context_parts.append(f"\nScoring (1-5 scale, max 20 total):")
    context_parts.append(f"  - ROI Potential: {opportunity.get('roi_potential', 'Not scored')}/5")
    context_parts.append(f"  - Implementation Effort: {opportunity.get('implementation_effort', 'Not scored')}/5")
    context_parts.append(f"  - Strategic Alignment: {opportunity.get('strategic_alignment', 'Not scored')}/5")
    context_parts.append(f"  - Stakeholder Readiness: {opportunity.get('stakeholder_readiness', 'Not scored')}/5")
    context_parts.append(f"  - Total Score: {opportunity.get('total_score', 0)}/20")
    context_parts.append(f"  - Tier: {opportunity.get('tier', 4)}")

    if opportunity.get('description'):
        context_parts.append(f"\nDescription: {opportunity['description']}")

    if opportunity.get('current_state'):
        context_parts.append(f"\nCurrent State: {opportunity['current_state']}")

    if opportunity.get('desired_state'):
        context_parts.append(f"\nDesired State: {opportunity['desired_state']}")

    if opportunity.get('next_step'):
        context_parts.append(f"\nNext Step: {opportunity['next_step']}")

    blockers = opportunity.get('blockers', [])
    if blockers:
        context_parts.append(f"\nBlockers: {', '.join(blockers)}")

    roi_indicators = opportunity.get('roi_indicators', {})
    if roi_indicators:
        context_parts.append(f"\nROI Indicators: {roi_indicators}")

    context_parts.append("</opportunity_context>")

    # Related documents section
    if related_documents:
        context_parts.append("\n<related_knowledge_base_documents>")
        for i, doc in enumerate(related_documents, 1):
            context_parts.append(f"\n[Source {i} - {doc.get('document_name', 'Unknown')}]")
            context_parts.append(doc.get('snippet', ''))
        context_parts.append("\n</related_knowledge_base_documents>")

    return "\n".join(context_parts)
