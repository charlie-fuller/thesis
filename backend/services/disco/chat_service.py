"""PuRDy Chat Service.

Provides RAG-based Q&A functionality for initiatives.
"""

import asyncio
import os
from typing import Dict, List, Optional
from uuid import uuid4

import anthropic

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
supabase = get_supabase()

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

CHAT_MODEL = os.environ.get("PURDY_CHAT_MODEL", "claude-sonnet-4-20250514")

CHAT_SYSTEM_PROMPT = """You are a helpful assistant for PuRDy (Product Requirements Document).
You help users understand their initiative documents, agent outputs, and discovery findings.

You have access to:
1. Documents uploaded directly to this initiative
2. Knowledge Base documents linked to this initiative
3. Previous agent outputs (triage, discovery plans, PRDs, tech evaluations)
4. PuRDy methodology knowledge base

Your role is to:
- Answer questions about this specific initiative and its documents
- Explain agent recommendations and findings
- Help users understand next steps in the discovery process
- Provide insights based on the methodology and best practices
- Be direct and concise in your responses

When citing information, reference the source document or output.
Keep responses focused and actionable."""


async def create_conversation(initiative_id: str, user_id: str) -> Dict:
    """Create a new conversation for an initiative.

    Args:
        initiative_id: Initiative UUID
        user_id: User's ID

    Returns:
        Created conversation record
    """
    conversation_id = str(uuid4())

    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_conversations")
            .insert({"id": conversation_id, "initiative_id": initiative_id, "user_id": user_id})
            .execute()
        )

        logger.info(f"Created conversation {conversation_id} for initiative {initiative_id}")
        return result.data[0] if result.data else {"id": conversation_id}

    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise


async def get_conversation(initiative_id: str, user_id: str) -> Optional[Dict]:
    """Get or create a conversation for a user in an initiative.

    Args:
        initiative_id: Initiative UUID
        user_id: User's ID

    Returns:
        Conversation with messages
    """
    try:
        # Try to find existing conversation
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_conversations")
            .select("*, disco_messages(*)")
            .eq("initiative_id", initiative_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if result.data:
            conversation = result.data[0]
            # Sort messages by created_at
            if conversation.get("disco_messages"):
                conversation["messages"] = sorted(conversation["disco_messages"], key=lambda m: m["created_at"])
                del conversation["disco_messages"]
            else:
                conversation["messages"] = []
            return conversation

        # Create new conversation if none exists
        return await create_conversation(initiative_id, user_id)

    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise


async def ask_question(initiative_id: str, question: str, user_id: str, conversation_id: Optional[str] = None) -> Dict:
    """Answer a question about an initiative using RAG.

    Args:
        initiative_id: Initiative UUID
        question: User's question
        user_id: User's ID
        conversation_id: Optional existing conversation ID

    Returns:
        Dict with response and source citations
    """
    logger.info(f"Processing question for initiative {initiative_id}: {question[:50]}...")

    try:
        # Get or create conversation
        if not conversation_id:
            conversation = await get_conversation(initiative_id, user_id)
            conversation_id = conversation["id"]

        # Store user message
        await asyncio.to_thread(
            lambda: supabase.table("disco_messages")
            .insert(
                {
                    "conversation_id": conversation_id,
                    "role": "user",
                    "content": question,
                    "sources": [],
                }
            )
            .execute()
        )

        # Search for relevant context
        from .document_service import (
            get_linked_document_names,
            search_initiative_docs,
            search_linked_kb_docs,
        )
        from .system_kb_service import search_system_kb

        # Search initiative documents (direct uploads to disco_document_chunks)
        doc_chunks = await search_initiative_docs(initiative_id, question, limit=8)

        # Search linked KB documents (from disco_initiative_documents junction table)
        linked_kb_chunks = await search_linked_kb_docs(initiative_id, question, limit=8)

        # Get linked document names (for meta-questions like "what documents do you have?")
        linked_docs_list = await get_linked_document_names(initiative_id)

        # Search system KB (PuRDy methodology)
        kb_chunks = await search_system_kb(question, limit=5)

        # Build context - START with document availability so Claude knows what's linked
        context_parts = []

        if linked_docs_list:
            context_parts.append("## Available Linked KB Documents\n")
            context_parts.append(
                "You have access to the following knowledge base documents linked to this initiative:\n"
            )
            for doc in linked_docs_list:
                doc_name = doc.get("title") or doc.get("filename", "Unknown")
                context_parts.append(f"- {doc_name}")
            context_parts.append("\n")

        if doc_chunks:
            context_parts.append("## Initiative Documents (Uploaded)\n")
            for chunk in doc_chunks:
                context_parts.append(f"[From {chunk.get('filename', 'document')}]:")
                context_parts.append(chunk["content"])
                context_parts.append("\n---\n")

        if linked_kb_chunks:
            context_parts.append("\n## Linked Knowledge Base Documents\n")
            for chunk in linked_kb_chunks:
                context_parts.append(f"[From {chunk.get('filename', 'document')}]:")
                context_parts.append(chunk["content"])
                context_parts.append("\n---\n")

        if kb_chunks:
            context_parts.append("\n## PuRDy Methodology Reference\n")
            for chunk in kb_chunks:
                context_parts.append(f"[From {chunk.get('filename', 'methodology')}]:")
                context_parts.append(chunk["content"])
                context_parts.append("\n---\n")

        context = "\n".join(context_parts)

        # Get conversation history (last 10 messages)
        history_result = await asyncio.to_thread(
            lambda: supabase.table("disco_messages")
            .select("role, content")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        # Build messages for Claude
        messages = []

        # Add history (reversed to chronological)
        if history_result.data:
            history = list(reversed(history_result.data))
            for msg in history[:-1]:  # Exclude the question we just added
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current question with context
        messages.append(
            {
                "role": "user",
                "content": f"""Here is relevant context for answering the question:

{context}

User question: {question}

Please answer based on the context provided. Cite sources when referencing specific information.""",
            }
        )

        # Call Claude
        response = anthropic_client.messages.create(
            model=CHAT_MODEL, max_tokens=2048, system=CHAT_SYSTEM_PROMPT, messages=messages
        )

        answer = response.content[0].text

        # Build source citations
        sources = []
        seen_sources = set()

        for chunk in doc_chunks:
            source_id = chunk.get("document_id")
            if source_id and source_id not in seen_sources:
                seen_sources.add(source_id)
                sources.append(
                    {
                        "type": "document",
                        "id": source_id,
                        "name": chunk.get("filename", "Document"),
                        "similarity": chunk.get("similarity", 0),
                    }
                )

        for chunk in linked_kb_chunks:
            source_id = chunk.get("document_id")
            if source_id and source_id not in seen_sources:
                seen_sources.add(source_id)
                sources.append(
                    {
                        "type": "linked_kb",
                        "id": source_id,
                        "name": chunk.get("filename", "KB Document"),
                        "similarity": chunk.get("similarity", 0),
                    }
                )

        for chunk in kb_chunks:
            source_id = chunk.get("kb_id")
            if source_id and source_id not in seen_sources:
                seen_sources.add(source_id)
                sources.append(
                    {
                        "type": "system_kb",
                        "id": source_id,
                        "name": chunk.get("filename", "Methodology"),
                        "similarity": chunk.get("similarity", 0),
                    }
                )

        # Store assistant message
        await asyncio.to_thread(
            lambda: supabase.table("disco_messages")
            .insert(
                {
                    "conversation_id": conversation_id,
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                }
            )
            .execute()
        )

        logger.info(f"Generated response for chat ({len(answer)} chars)")

        return {"response": answer, "sources": sources, "conversation_id": conversation_id}

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise


async def get_conversation_history(conversation_id: str, limit: int = 50) -> List[Dict]:
    """Get message history for a conversation.

    Args:
        conversation_id: Conversation UUID
        limit: Max messages to return

    Returns:
        List of messages in chronological order
    """
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("disco_messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at")
            .limit(limit)
            .execute()
        )

        return result.data or []

    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []


async def clear_conversation(conversation_id: str) -> bool:
    """Clear all messages in a conversation.

    Args:
        conversation_id: Conversation UUID

    Returns:
        True if cleared successfully
    """
    try:
        await asyncio.to_thread(
            lambda: supabase.table("disco_messages").delete().eq("conversation_id", conversation_id).execute()
        )

        logger.info(f"Cleared conversation {conversation_id}")
        return True

    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise
