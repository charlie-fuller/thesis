"""Project Chat Service.

Provides Q&A functionality for AI projects.
Uses the Operator agent persona to answer questions about specific projects,
incorporating knowledge base context and storing conversations.
"""

import os
from typing import Dict, List
from uuid import uuid4

import anthropic

import pb_client as pb
from repositories import projects as projects_repo
from logger_config import get_logger
from services.project_context import build_project_context, get_scoring_related_documents

logger = get_logger(__name__)

# Initialize clients
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

PROJECT_CHAT_SYSTEM_PROMPT = """You are an AI assistant helping users understand and evaluate AI implementation projects.

You have access to:
1. Complete details about a specific AI project including its scoring, status, and context
2. Relevant documents from the knowledge base that may provide additional insights

Your role is to:
- Answer questions about this specific project
- Explain the scoring rationale (ROI potential, implementation effort, strategic alignment, stakeholder readiness)
- Provide insights based on related documents when relevant
- Help users understand next steps, blockers, and potential approaches
- Be direct and concise in your responses

When citing information from related documents, reference them as "According to [document name]..."

Keep responses focused and actionable. Use bullet points for clarity when listing multiple items."""


async def ask_about_project(project_id: str, question: str, client_id: str, user_id: str) -> Dict:
    """Answer a question about a specific project.

    Fetches project details, finds related documents via vector search,
    builds context, calls Claude, and stores the conversation.

    Args:
        project_id: The project UUID
        question: The user's question
        client_id: Client ID for access control
        user_id: User ID for conversation storage

    Returns:
        Dict with response text and source documents
    """
    logger.info(f"Processing question about project {project_id}: {question[:50]}...")

    # 1. Fetch the project
    project = projects_repo.get_project(project_id)
    if not project:
        raise ValueError(f"Project not found: {project_id}")

    # Look up owner name if owner_stakeholder_id is set
    if project.get("owner_stakeholder_id"):
        from repositories import stakeholders as stakeholders_repo
        owner = stakeholders_repo.get_stakeholder(project["owner_stakeholder_id"])
        if owner:
            project["owner_name"] = owner.get("name")

    # 2. Get scoring-relevant documents
    related_docs = get_scoring_related_documents(project=project, client_id=client_id, limit=5, min_similarity=0.25)

    # 3. Build context string
    context = build_project_context(project, related_docs)

    # 4. Call Claude
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=PROJECT_CHAT_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"""Here is the context about the project and related documents:

{context}

User question: {question}

Please answer the question based on the project details and any relevant information from the related documents.""",
                }
            ],
        )

        answer = response.content[0].text
        logger.info(f"Generated response for project question ({len(answer)} chars)")

    except Exception as e:
        logger.error(f"Error calling Claude for project question: {e}")
        raise

    # 5. Store the conversation
    try:
        # Format source documents for storage
        source_docs_json = [
            {
                "document_id": doc.get("document_id"),
                "document_name": doc.get("document_name"),
                "relevance_score": doc.get("relevance_score"),
                "snippet": doc.get("snippet", "")[:200],  # Limit snippet size
            }
            for doc in related_docs
        ]

        pb.create_record("project_conversations", {
            "project_id": project_id,
            "question": question,
            "response": answer,
            "source_documents": source_docs_json,
        })

        logger.info(f"Stored conversation for project {project_id}")

    except Exception as e:
        logger.error(f"Failed to store project conversation: {e}")
        # Don't fail the request if storage fails

    # 6. Return response with sources
    return {"response": answer, "sources": related_docs}


async def get_project_conversations(project_id: str, client_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
    """Get conversation history for a project.

    Args:
        project_id: The project UUID
        client_id: Client ID for access control
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip (for pagination)

    Returns:
        List of conversation dicts (newest first)
    """
    logger.info(f"Fetching conversations for project {project_id}")

    try:
        esc_pid = pb.escape_filter(project_id)
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records(
            "project_conversations",
            filter=f"project_id='{esc_pid}'",
            sort="-created",
            page=page,
            per_page=limit,
        )
        conversations = result.get("items", [])
        logger.info(f"Found {len(conversations)} conversations")
        return conversations

    except Exception as e:
        logger.error(f"Error fetching project conversations: {e}")
        return []
