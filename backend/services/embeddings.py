"""Embeddings Service - Voyage AI Integration.

Provides embedding generation for documents, chat messages, and meeting room messages.
"""

import logging
import os
from typing import List, Optional
from uuid import UUID

import voyageai

from config.constants import EMBEDDING

logger = logging.getLogger(__name__)

# Initialize Voyage AI client
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
if not VOYAGE_API_KEY:
    raise ValueError("VOYAGE_API_KEY environment variable is required")

vo = voyageai.Client(api_key=VOYAGE_API_KEY)


def create_embedding(text: str, input_type: str = "document") -> List[float]:
    """Create embedding for a single text using Voyage AI.

    Args:
        text: Text to embed
        input_type: Type of input ("document" or "query")

    Returns:
        List of floats representing the embedding vector (1024 dimensions for voyage-3)
    """
    try:
        result = vo.embed(texts=[text], model=EMBEDDING.MODEL_NAME, input_type=input_type)
        return result.embeddings[0]
    except Exception as e:
        raise Exception(f"Error creating embedding: {e}") from None


def create_embeddings_batch(texts: List[str], input_type: str = "document") -> List[List[float]]:
    """Create embeddings for multiple texts in a single batch.

    Args:
        texts: List of texts to embed
        input_type: Type of input ("document" or "query")

    Returns:
        List of embedding vectors
    """
    try:
        result = vo.embed(texts=texts, model=EMBEDDING.MODEL_NAME, input_type=input_type)
        return result.embeddings
    except Exception as e:
        raise Exception(f"Error creating embeddings batch: {e}") from None


async def embed_meeting_room_message(supabase_client, message_id: UUID, content: str) -> bool:
    """Create and store embedding for a meeting room message.

    Args:
        supabase_client: Authenticated Supabase client
        message_id: UUID of the message to embed
        content: Text content of the message

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create embedding
        embedding = create_embedding(content, input_type=EMBEDDING.INPUT_TYPE_DOCUMENT)

        # Update message with embedding
        result = (
            supabase_client.table("meeting_room_messages")
            .update({"embedding": embedding, "embedding_status": "completed"})
            .eq("id", str(message_id))
            .execute()
        )

        if result.data:
            logger.info(f"Embedded meeting room message {message_id}")
            return True
        else:
            logger.warning(f"No message found with ID {message_id}")
            return False

    except Exception as e:
        logger.error(f"Error embedding message {message_id}: {e}")
        # Mark as failed
        try:
            supabase_client.table("meeting_room_messages").update(
                {"embedding_status": "failed"}
            ).eq("id", str(message_id)).execute()
        except Exception:
            pass
        return False


async def embed_pending_meeting_messages(
    supabase_client, limit: int = 50, meeting_room_id: Optional[UUID] = None
) -> int:
    """Process pending meeting room messages that need embedding.

    Args:
        supabase_client: Authenticated Supabase client
        limit: Maximum messages to process
        meeting_room_id: Optional filter for specific meeting room

    Returns:
        Number of messages successfully embedded
    """
    try:
        # Query for pending messages
        query = (
            supabase_client.table("meeting_room_messages")
            .select("id, content")
            .eq("embedding_status", "pending")
            .limit(limit)
        )

        if meeting_room_id:
            query = query.eq("meeting_room_id", str(meeting_room_id))

        result = query.execute()
        messages = result.data or []

        if not messages:
            return 0

        # Process in batches for efficiency
        batch_size = EMBEDDING.DEFAULT_BATCH_SIZE
        embedded_count = 0

        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]
            texts = [m["content"] for m in batch]
            ids = [m["id"] for m in batch]

            try:
                embeddings = create_embeddings_batch(
                    texts, input_type=EMBEDDING.INPUT_TYPE_DOCUMENT
                )

                # Update each message with its embedding
                for msg_id, embedding in zip(ids, embeddings, strict=False):
                    supabase_client.table("meeting_room_messages").update(
                        {"embedding": embedding, "embedding_status": "completed"}
                    ).eq("id", msg_id).execute()
                    embedded_count += 1

            except Exception as e:
                logger.error(f"Error embedding batch: {e}")
                # Mark batch as failed
                for msg_id in ids:
                    try:
                        supabase_client.table("meeting_room_messages").update(
                            {"embedding_status": "failed"}
                        ).eq("id", msg_id).execute()
                    except Exception:
                        pass

        logger.info(f"Embedded {embedded_count} meeting room messages")
        return embedded_count

    except Exception as e:
        logger.error(f"Error processing pending messages: {e}")
        return 0


async def search_meeting_room_messages(
    supabase_client,
    query: str,
    match_threshold: float = 0.5,
    match_count: int = 10,
    client_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    meeting_room_id: Optional[UUID] = None,
) -> List[dict]:
    """Search meeting room messages using semantic similarity.

    Args:
        supabase_client: Authenticated Supabase client
        query: Search query
        match_threshold: Minimum similarity score (0-1)
        match_count: Maximum results to return
        client_id: Optional filter by client
        user_id: Optional filter by user
        meeting_room_id: Optional filter by meeting room

    Returns:
        List of matching messages with similarity scores
    """
    try:
        # Create query embedding
        query_embedding = create_embedding(query, input_type=EMBEDDING.INPUT_TYPE_QUERY)

        # Call the vector search function
        result = supabase_client.rpc(
            "match_meeting_room_messages",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "p_client_id": str(client_id) if client_id else None,
                "p_user_id": str(user_id) if user_id else None,
                "p_meeting_room_id": str(meeting_room_id) if meeting_room_id else None,
            },
        ).execute()

        return result.data or []

    except Exception as e:
        logger.error(f"Error searching meeting room messages: {e}")
        return []
