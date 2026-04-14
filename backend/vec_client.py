"""Vector search sidecar client.

Thin httpx wrapper for the thesis-vec FastAPI service.
Used by repositories that need embedding storage/search
(documents, help, disco, purdy).
"""

import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

_client: httpx.Client | None = None


def init_vec() -> None:
    """Create the httpx client for the vector sidecar."""
    global _client
    _client = httpx.Client(
        base_url=settings.vec_url,
        timeout=30.0,
    )
    logger.info("Vector sidecar client initialized: %s", settings.vec_url)


def close_vec() -> None:
    """Close the httpx client."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def _get_client() -> httpx.Client:
    if _client is None:
        raise RuntimeError("Vector client not initialized -- call init_vec() first")
    return _client


def store_embedding(collection: str, record_id: str, text: str, title: str = "") -> dict:
    """Store a text embedding in the vector database."""
    resp = _get_client().post(
        "/embeddings/store",
        json={
            "collection": collection,
            "record_id": record_id,
            "text": text,
            "title": title,
        },
    )
    resp.raise_for_status()
    return resp.json()


def search(collection: str, query: str, limit: int = 5) -> list[dict]:
    """Search for similar documents in a collection."""
    resp = _get_client().post(
        "/search",
        json={
            "collection": collection,
            "query": query,
            "limit": limit,
        },
    )
    resp.raise_for_status()
    return resp.json()


def delete_embedding(record_id: str) -> None:
    """Delete an embedding by its record ID."""
    resp = _get_client().delete(f"/embeddings/{record_id}")
    resp.raise_for_status()


def get_stats() -> dict:
    """Get vector database statistics."""
    resp = _get_client().get("/stats")
    resp.raise_for_status()
    return resp.json()
