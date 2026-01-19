"""
Opportunity Chat Service

Provides Q&A functionality for AI opportunities.
Uses the Operator agent persona to answer questions about specific opportunities,
incorporating knowledge base context and storing conversations.
"""

import os
from typing import Dict, List, Optional
from uuid import uuid4

import anthropic
from logger_config import get_logger
from database import get_supabase
from services.opportunity_context import get_scoring_related_documents, build_opportunity_context

logger = get_logger(__name__)

# Initialize clients
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
supabase = get_supabase()

OPPORTUNITY_CHAT_SYSTEM_PROMPT = """You are an AI assistant helping users understand and evaluate AI implementation opportunities.

You have access to:
1. Complete details about a specific AI opportunity including its scoring, status, and context
2. Relevant documents from the knowledge base that may provide additional insights

Your role is to:
- Answer questions about this specific opportunity
- Explain the scoring rationale (ROI potential, implementation effort, strategic alignment, stakeholder readiness)
- Provide insights based on related documents when relevant
- Help users understand next steps, blockers, and potential approaches
- Be direct and concise in your responses

When citing information from related documents, reference them as "According to [document name]..."

Keep responses focused and actionable. Use bullet points for clarity when listing multiple items."""


async def ask_about_opportunity(
    opportunity_id: str,
    question: str,
    client_id: str,
    user_id: str
) -> Dict:
    """
    Answer a question about a specific opportunity.

    Fetches opportunity details, finds related documents via vector search,
    builds context, calls Claude, and stores the conversation.

    Args:
        opportunity_id: The opportunity UUID
        question: The user's question
        client_id: Client ID for access control
        user_id: User ID for conversation storage

    Returns:
        Dict with response text and source documents
    """
    logger.info(f"Processing question about opportunity {opportunity_id}: {question[:50]}...")

    # 1. Fetch the opportunity
    opp_result = supabase.table('ai_opportunities')\
        .select('*, stakeholders(name)')\
        .eq('id', opportunity_id)\
        .eq('client_id', client_id)\
        .single()\
        .execute()

    if not opp_result.data:
        raise ValueError(f"Opportunity not found: {opportunity_id}")

    opportunity = opp_result.data

    # Add owner name from joined data
    if opportunity.get('stakeholders'):
        opportunity['owner_name'] = opportunity['stakeholders'].get('name')

    # 2. Get scoring-relevant documents
    related_docs = get_scoring_related_documents(
        opportunity=opportunity,
        client_id=client_id,
        limit=5,
        min_similarity=0.25
    )

    # 3. Build context string
    context = build_opportunity_context(opportunity, related_docs)

    # 4. Call Claude
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=OPPORTUNITY_CHAT_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"""Here is the context about the opportunity and related documents:

{context}

User question: {question}

Please answer the question based on the opportunity details and any relevant information from the related documents."""
                }
            ]
        )

        answer = response.content[0].text
        logger.info(f"Generated response for opportunity question ({len(answer)} chars)")

    except Exception as e:
        logger.error(f"Error calling Claude for opportunity question: {e}")
        raise

    # 5. Store the conversation
    try:
        # Format source documents for storage
        source_docs_json = [
            {
                'document_id': doc.get('document_id'),
                'document_name': doc.get('document_name'),
                'relevance_score': doc.get('relevance_score'),
                'snippet': doc.get('snippet', '')[:200]  # Limit snippet size
            }
            for doc in related_docs
        ]

        supabase.table('opportunity_conversations').insert({
            'id': str(uuid4()),
            'opportunity_id': opportunity_id,
            'client_id': client_id,
            'user_id': user_id,
            'question': question,
            'response': answer,
            'source_documents': source_docs_json
        }).execute()

        logger.info(f"Stored conversation for opportunity {opportunity_id}")

    except Exception as e:
        logger.error(f"Failed to store opportunity conversation: {e}")
        # Don't fail the request if storage fails

    # 6. Return response with sources
    return {
        'response': answer,
        'sources': related_docs
    }


async def get_opportunity_conversations(
    opportunity_id: str,
    client_id: str,
    limit: int = 20,
    offset: int = 0
) -> List[Dict]:
    """
    Get conversation history for an opportunity.

    Args:
        opportunity_id: The opportunity UUID
        client_id: Client ID for access control
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip (for pagination)

    Returns:
        List of conversation dicts (newest first)
    """
    logger.info(f"Fetching conversations for opportunity {opportunity_id}")

    try:
        result = supabase.table('opportunity_conversations')\
            .select('id, question, response, source_documents, created_at')\
            .eq('opportunity_id', opportunity_id)\
            .eq('client_id', client_id)\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        conversations = result.data or []
        logger.info(f"Found {len(conversations)} conversations")
        return conversations

    except Exception as e:
        logger.error(f"Error fetching opportunity conversations: {e}")
        return []
