"""Vector search sidecar -- FastAPI app with sqlite-vec.

Provides embedding storage and similarity search for Thesis.
Runs as a separate Fly.io service (thesis-vec).
"""

import json
import logging
import os
from contextlib import asynccontextmanager

import voyageai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from database import get_db, close_db

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Voyage AI client
voyage_client: voyageai.Client | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global voyage_client
    voyage_api_key = os.getenv("VOYAGE_API_KEY", "")
    if voyage_api_key:
        voyage_client = voyageai.Client(api_key=voyage_api_key)
        logger.info("Voyage AI client initialized")
    else:
        logger.warning("VOYAGE_API_KEY not set -- embeddings will fail")

    # Initialize database
    get_db()

    yield

    close_db()


app = FastAPI(title="Thesis Vector Sidecar", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class StoreRequest(BaseModel):
    collection: str = Field(..., description="Collection name (e.g. 'document_chunks')")
    record_id: str = Field(..., description="PocketBase record ID")
    text: str = Field(..., description="Text content to embed")
    title: str = Field("", description="Optional title for search results")


class SearchRequest(BaseModel):
    collection: str = Field(..., description="Collection to search")
    query: str = Field(..., description="Search query text")
    limit: int = Field(5, ge=1, le=50, description="Max results")


class SearchResult(BaseModel):
    id: str
    collection: str
    title: str
    content_preview: str
    similarity: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Health check."""
    try:
        db = get_db()
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/embeddings/store")
async def store_embedding(req: StoreRequest):
    """Store a text embedding."""
    if not voyage_client:
        raise HTTPException(status_code=503, detail="Voyage AI client not initialized")

    db = get_db()

    # Generate embedding
    result = voyage_client.embed([req.text], model="voyage-3", input_type="document")
    embedding = result.embeddings[0]

    # Store metadata
    db.execute(
        """INSERT OR REPLACE INTO vec_metadata (id, collection, title, content_preview)
           VALUES (?, ?, ?, ?)""",
        (req.record_id, req.collection, req.title, req.text[:200]),
    )

    # Store embedding
    embedding_json = json.dumps(embedding)
    db.execute(
        """INSERT OR REPLACE INTO vec_embeddings (id, embedding)
           VALUES (?, ?)""",
        (req.record_id, embedding_json),
    )

    db.commit()

    return {"id": req.record_id, "status": "stored", "dimensions": len(embedding)}


@app.post("/search", response_model=list[SearchResult])
async def search(req: SearchRequest):
    """Search for similar documents."""
    if not voyage_client:
        raise HTTPException(status_code=503, detail="Voyage AI client not initialized")

    db = get_db()

    # Generate query embedding
    result = voyage_client.embed([req.query], model="voyage-3", input_type="query")
    query_embedding = result.embeddings[0]

    query_json = json.dumps(query_embedding)

    # Vector similarity search with collection filter
    rows = db.execute(
        """SELECT
             v.id,
             v.distance,
             m.collection,
             m.title,
             m.content_preview
           FROM vec_embeddings v
           JOIN vec_metadata m ON v.id = m.id
           WHERE m.collection = ?
             AND v.embedding MATCH ?
           ORDER BY v.distance ASC
           LIMIT ?""",
        (req.collection, query_json, req.limit),
    ).fetchall()

    results = []
    for row in rows:
        results.append(SearchResult(
            id=row["id"],
            collection=row["collection"],
            title=row["title"] or "",
            content_preview=row["content_preview"] or "",
            similarity=1.0 - row["distance"],
        ))

    return results


@app.delete("/embeddings/{record_id}")
async def delete_embedding(record_id: str):
    """Delete an embedding by record ID."""
    db = get_db()

    db.execute("DELETE FROM vec_metadata WHERE id = ?", (record_id,))
    db.execute("DELETE FROM vec_embeddings WHERE id = ?", (record_id,))
    db.commit()

    return {"id": record_id, "status": "deleted"}


@app.get("/stats")
async def get_stats():
    """Get vector database statistics."""
    db = get_db()

    total = db.execute("SELECT COUNT(*) as count FROM vec_metadata").fetchone()["count"]

    by_collection = {}
    rows = db.execute(
        "SELECT collection, COUNT(*) as count FROM vec_metadata GROUP BY collection"
    ).fetchall()
    for row in rows:
        by_collection[row["collection"]] = row["count"]

    return {"total_embeddings": total, "by_collection": by_collection}
