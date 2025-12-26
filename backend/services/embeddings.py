"""
Embeddings Service - Voyage AI Integration
Provides embedding generation for help documentation and RAG
"""

import os
from typing import List

import voyageai

# Initialize Voyage AI client
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
if not VOYAGE_API_KEY:
    raise ValueError("VOYAGE_API_KEY environment variable is required")

vo = voyageai.Client(api_key=VOYAGE_API_KEY)

def create_embedding(text: str, input_type: str = "document") -> List[float]:
    """
    Create embedding for a single text using Voyage AI

    Args:
        text: Text to embed
        input_type: Type of input ("document" or "query")

    Returns:
        List of floats representing the embedding vector (1536 dimensions)
    """
    try:
        result = vo.embed(
            texts=[text],
            model="voyage-large-2",
            input_type=input_type
        )
        return result.embeddings[0]
    except Exception as e:
        raise Exception(f"Error creating embedding: {e}")


def create_embeddings_batch(texts: List[str], input_type: str = "document") -> List[List[float]]:
    """
    Create embeddings for multiple texts in a single batch

    Args:
        texts: List of texts to embed
        input_type: Type of input ("document" or "query")

    Returns:
        List of embedding vectors
    """
    try:
        result = vo.embed(
            texts=texts,
            model="voyage-large-2",
            input_type=input_type
        )
        return result.embeddings
    except Exception as e:
        raise Exception(f"Error creating embeddings batch: {e}")
