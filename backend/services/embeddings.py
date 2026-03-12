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

        # Fetch message metadata for Pinecone
        result = (
            supabase_client.table("meeting_room_messages")
            .select("id, meeting_room_id")
            .eq("id", str(message_id))
            .execute()
        )

        if not result.data:
            logger.warning(f"No message found with ID {message_id}")
            return False

        msg_data = result.data[0] if result.data else {}
        from services.pinecone_service import upsert_vectors

        metadata = {
            "message_id": str(message_id),
        }
        if msg_data.get("meeting_room_id"):
            metadata["meeting_room_id"] = str(msg_data["meeting_room_id"])

        upsert_vectors(
            vectors=[{"id": str(message_id), "values": embedding, "metadata": metadata}],
            namespace="meeting_room_messages",
        )

        logger.info(f"Embedded meeting room message {message_id}")
        return True

    except Exception as e:
        logger.error(f"Error embedding message {message_id}: {e}")
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
        # Query for messages (embeddings stored in Pinecone, not Supabase)
        query = (
            supabase_client.table("meeting_room_messages")
            .select("id, content")
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
                embeddings = create_embeddings_batch(texts, input_type=EMBEDDING.INPUT_TYPE_DOCUMENT)

                # Update each message status and collect for Pinecone
                pinecone_vectors = []
                for msg_id, embedding, msg in zip(ids, embeddings, batch, strict=False):
                    embedded_count += 1

                    # Collect for Pinecone batch upsert
                    pinecone_vectors.append(
                        {"id": str(msg_id), "values": embedding, "metadata": {"message_id": str(msg_id)}}
                    )

                # Batch upsert to Pinecone
                if pinecone_vectors:
                    from services.pinecone_service import upsert_vectors

                    upsert_vectors(vectors=pinecone_vectors, namespace="meeting_room_messages")

            except Exception as e:
                logger.error(f"Error embedding batch: {e}")
                pass  # Error already logged above

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

        # Try Pinecone first
        from services.pinecone_service import get_index, query_vectors

        if get_index() is not None:
            # Build Pinecone metadata filter
            pc_filter = {}
            if client_id:
                pc_filter["client_id"] = {"$eq": str(client_id)}
            if user_id:
                pc_filter["user_id"] = {"$eq": str(user_id)}
            if meeting_room_id:
                pc_filter["meeting_room_id"] = {"$eq": str(meeting_room_id)}

            matches = query_vectors(
                embedding=query_embedding,
                namespace="meeting_room_messages",
                top_k=match_count,
                filter=pc_filter if pc_filter else None,
            )

            if not matches:
                return []

            # Filter by threshold (Pinecone uses cosine similarity, higher = more similar)
            matches = [m for m in matches if m["score"] >= match_threshold]

            if not matches:
                return []

            # Fetch full message data from Supabase
            message_ids = [m["id"] for m in matches]
            scores_map = {m["id"]: m["score"] for m in matches}

            msg_result = (
                supabase_client.table("meeting_room_messages")
                .select("id, content, user_id, meeting_room_id, client_id, created_at")
                .in_("id", message_ids)
                .execute()
            )

            # Combine with similarity scores
            results = []
            for msg in msg_result.data or []:
                msg["similarity"] = scores_map.get(msg["id"], 0)
                results.append(msg)

            # Sort by similarity descending
            results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            return results

        # Fallback to pgvector RPC
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
