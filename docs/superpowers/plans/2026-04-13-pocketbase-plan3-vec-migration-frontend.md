# Vector Sidecar + Data Migration + Frontend (Plan 3 of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the sqlite-vec vector search sidecar, migrate all data from Supabase to PocketBase, and update the frontend to use API key auth.

**Architecture:** Python FastAPI sidecar with sqlite-vec for vector search (`thesis-vec` on Fly.io). Migration script pulls from Supabase Management API, pushes to PocketBase REST API in 3 passes (leaf, relations, embeddings). Frontend drops Supabase JS client and uses API key Bearer tokens.

**Tech Stack:** Python 3.12, FastAPI, sqlite-vec, Voyage AI, httpx, Next.js 16

**Spec:** `docs/superpowers/specs/2026-04-13-supabase-to-pocketbase-migration.md`

**Depends on:** Plan 1 (PocketBase deployed), Plan 2 (backend rewritten)

---

## File Structure

```
thesis/
  vec_sidecar/
    main.py                         -- FastAPI app with /embeddings/store, /search, /health
    database.py                     -- sqlite-vec init, schema creation
    requirements.txt                -- fastapi, uvicorn, sqlite-vec, voyageai, httpx
  Dockerfile.vec                    -- Python 3.12-slim + requirements
  fly.vec.toml                      -- Fly.io config for thesis-vec
  scripts/
    migrate_supabase_to_pb.py       -- 3-pass data migration script
  frontend/
    lib/api.ts                      -- MODIFY: replace Supabase client with fetch + API key
    contexts/AuthContext.tsx         -- DELETE or stub
    .env.local                      -- MODIFY: add NEXT_PUBLIC_API_KEY, remove SUPABASE_*
```

---

### Task 1: Create vec_sidecar/database.py

**Files:**
- Create: `vec_sidecar/database.py`

- [ ] **Step 1: Write the database module**

```python
"""sqlite-vec database initialization and management."""

import logging
import os
import sqlite3

import sqlite_vec

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("VEC_DB_PATH", "/app/data/vectors.db")

_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    """Get the sqlite-vec database connection (singleton)."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.enable_load_extension(True)
        sqlite_vec.load(_conn)
        _conn.enable_load_extension(False)
        _init_schema(_conn)
        logger.info("sqlite-vec database initialized at %s", DB_PATH)
    return _conn


def close_db() -> None:
    """Close the database connection."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def _init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vec_metadata (
            id TEXT PRIMARY KEY,
            collection TEXT NOT NULL,
            title TEXT DEFAULT '',
            content_preview TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_vec_metadata_collection
        ON vec_metadata(collection);
    """)

    # Check if vec_embeddings exists
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='vec_embeddings'"
    )
    if cursor.fetchone() is None:
        conn.execute("""
            CREATE VIRTUAL TABLE vec_embeddings USING vec0(
                id TEXT PRIMARY KEY,
                embedding float[1536]
            )
        """)

    conn.commit()
```

- [ ] **Step 2: Commit**

```bash
git add vec_sidecar/database.py
git commit -m "feat: add sqlite-vec database module for vector sidecar"
```

---

### Task 2: Create vec_sidecar/main.py

**Files:**
- Create: `vec_sidecar/main.py`

- [ ] **Step 1: Write the failing test**

```python
# vec_sidecar/tests/test_main.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with patch("database.get_db") as mock_db:
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        from main import app
        yield TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd vec_sidecar && python -m pytest tests/test_main.py -v
```

Expected: FAIL (main.py not found)

- [ ] **Step 3: Write the FastAPI app**

```python
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
            similarity=1.0 - row["distance"],  # Convert distance to similarity
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
```

- [ ] **Step 4: Run test**

```bash
cd vec_sidecar && python -m pytest tests/test_main.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add vec_sidecar/main.py vec_sidecar/tests/
git commit -m "feat: add vector sidecar FastAPI app with sqlite-vec"
```

---

### Task 3: Create vec_sidecar/requirements.txt

**Files:**
- Create: `vec_sidecar/requirements.txt`

- [ ] **Step 1: Write requirements**

```
fastapi>=0.115.0
uvicorn>=0.32.0
sqlite-vec>=0.1.6
voyageai>=0.3.0
pydantic>=2.0.0
```

- [ ] **Step 2: Commit**

```bash
git add vec_sidecar/requirements.txt
git commit -m "feat: add vector sidecar requirements"
```

---

### Task 4: Create Dockerfile.vec

**Files:**
- Create: `Dockerfile.vec`

- [ ] **Step 1: Write the Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install build tools for sqlite-vec compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY vec_sidecar/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vec_sidecar/ .

# Create data directory for sqlite-vec database
RUN mkdir -p /app/data

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 2: Commit**

```bash
git add Dockerfile.vec
git commit -m "feat: add Dockerfile for vector sidecar"
```

---

### Task 5: Create fly.vec.toml

**Files:**
- Create: `fly.vec.toml`

- [ ] **Step 1: Write the fly config**

```toml
app = "thesis-vec"
primary_region = "dfw"

[build]
  dockerfile = "Dockerfile.vec"

[mounts]
  source = "vec_data"
  destination = "/app/data"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "off"
  auto_start_machines = true
  min_machines_running = 1

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"

[[vm]]
  size = "shared-cpu-1x"
  memory = "256mb"
```

- [ ] **Step 2: Commit**

```bash
git add fly.vec.toml
git commit -m "feat: add Fly.io config for vector sidecar"
```

---

### Task 6: Deploy vector sidecar to Fly.io

**Files:** None (infrastructure task)

- [ ] **Step 1: Create the Fly.io app**

```bash
cd ~/Vault/GitHub/thesis
flyctl apps create thesis-vec --org personal
```

- [ ] **Step 2: Create the persistent volume**

```bash
flyctl volumes create vec_data --region dfw --size 1 -a thesis-vec
```

- [ ] **Step 3: Set secrets**

```bash
flyctl secrets set VOYAGE_API_KEY=<key> -a thesis-vec
```

Get the Voyage API key from 1Password or from `~/.thesis-env`.

- [ ] **Step 4: Deploy**

```bash
flyctl deploy --config fly.vec.toml -a thesis-vec
```

Expected: successful deploy, app running.

- [ ] **Step 5: Verify health**

```bash
curl -s https://thesis-vec.fly.dev/health
```

Expected: `{"status":"healthy","database":"connected"}`

- [ ] **Step 6: Verify stats endpoint**

```bash
curl -s https://thesis-vec.fly.dev/stats
```

Expected: `{"total_embeddings":0,"by_collection":{}}`

---

### Task 7: Create data migration script

**Files:**
- Create: `scripts/migrate_supabase_to_pb.py`

- [ ] **Step 1: Write the migration script**

```python
"""Migrate Thesis data from Supabase to PocketBase.

Three-pass approach:
  Pass 1: Leaf collections (no foreign keys)
  Pass 2: Collections with relations (using ID map)
  Pass 3: Embeddings (to vector sidecar)

Usage:
  python scripts/migrate_supabase_to_pb.py [--pass 1|2|3|all] [--table TABLE_NAME] [--dry-run]

Requires:
  - Supabase CLI token in macOS keychain (for Management API queries)
  - PocketBase running and accessible
  - Vector sidecar running (for pass 3)
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUPABASE_PROJECT_ID = "imdavfgreeddxluslsdl"
PB_URL = os.getenv("THESIS_POCKETBASE_URL", "https://thesis-db.fly.dev")
PB_EMAIL = os.getenv("THESIS_POCKETBASE_EMAIL", "")
PB_PASSWORD = os.getenv("THESIS_POCKETBASE_PASSWORD", "")
VEC_URL = os.getenv("THESIS_VEC_URL", "https://thesis-vec.fly.dev")

ID_MAP_FILE = "scripts/id_map.json"

# Tables to skip
SKIP_TABLES = {
    "users", "clients", "oauth_states",
    "google_drive_tokens", "google_drive_sync_log",
    "_migrations",
}

# Tables with generated columns to skip
SKIP_COLUMNS = {
    "total_score", "tier", "decision_velocity_days",
    "client_id", "user_id", "created_by", "updated_by", "embedding",
}

# Pass 1: Leaf collections (no foreign keys to other migrated tables)
PASS_1_TABLES = [
    "agents", "agent_topic_mapping", "ai_projects", "stakeholders", "strategic_goals",
    "project_tasks", "task_candidates",
    "conversations",
    "documents",
    "projects", "portfolio_projects", "roi_opportunities",
    "meeting_rooms", "meeting_transcripts",
    "help_documents", "help_conversations",
    "disco_initiatives", "disco_system_kb", "disco_conversations", "disco_outcome_metrics",
    "purdy_initiatives", "purdy_system_kb", "purdy_conversations",
    "research_tasks", "research_sources", "research_schedule",
    "stakeholder_candidates", "stakeholder_insights", "stakeholder_metrics",
    "obsidian_vault_configs", "graph_sync_log", "graph_sync_state",
    "api_usage_logs", "compass_status_reports", "department_kpis",
    "engagement_level_history", "glean_connectors", "glean_connector_gaps",
    "glean_connector_requests", "glean_connector_summary",
    "glean_disco_integration_matrix", "knowledge_gaps", "theme_settings",
    "user_quick_prompts",
]

# Pass 2: Collections with relations
PASS_2_TABLES = [
    "agent_handoffs", "agent_instruction_versions", "agent_knowledge_base",
    "task_comments", "task_history",
    "messages", "message_documents",
    "document_chunks", "document_classifications", "document_tags",
    "project_candidates", "project_conversations", "project_documents",
    "project_folders", "project_stakeholder_link",
    "meeting_room_messages", "meeting_room_participants",
    "help_chunks", "help_messages",
    "disco_bundles", "disco_checkpoints", "disco_documents",
    "disco_initiative_documents", "disco_initiative_folders",
    "disco_initiative_members", "disco_messages", "disco_runs", "disco_outputs",
    "disco_document_chunks", "disco_system_kb_chunks",
    "disco_bundle_feedback", "disco_prds", "disco_run_documents",
    "purdy_documents", "purdy_initiative_members", "purdy_messages",
    "purdy_runs", "purdy_outputs", "purdy_document_chunks",
    "purdy_system_kb_chunks", "purdy_run_documents",
    "obsidian_sync_log", "obsidian_sync_state",
]

# Pass 3: Embedding tables (column name -> vec collection)
EMBEDDING_TABLES = {
    "document_chunks": "document_chunks",
    "help_chunks": "help_chunks",
    "disco_document_chunks": "disco_document_chunks",
    "disco_system_kb_chunks": "disco_system_kb_chunks",
    "purdy_document_chunks": "purdy_document_chunks",
    "purdy_system_kb_chunks": "purdy_system_kb_chunks",
}


# ---------------------------------------------------------------------------
# Supabase query via Management API
# ---------------------------------------------------------------------------

def get_supabase_token() -> str:
    """Get Supabase CLI token from macOS keychain."""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "Supabase CLI", "-w"],
        capture_output=True, text=True, check=True,
    )
    raw = result.stdout.strip()
    # Decode from base64 if prefixed
    if raw.startswith("go-keyring-base64:"):
        import base64
        return base64.b64decode(raw.replace("go-keyring-base64:", "")).decode()
    return raw


def query_supabase(sql: str) -> list[dict]:
    """Execute SQL against Supabase via Management API."""
    token = get_supabase_token()
    resp = httpx.post(
        f"https://api.supabase.com/v1/projects/{SUPABASE_PROJECT_ID}/database/query",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"query": sql},
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# PocketBase client
# ---------------------------------------------------------------------------

class PBClient:
    def __init__(self, url: str, email: str, password: str):
        self.client = httpx.Client(base_url=url, timeout=30.0)
        if email and password:
            resp = self.client.post(
                "/api/collections/_superusers/auth-with-password",
                json={"identity": email, "password": password},
            )
            resp.raise_for_status()
            token = resp.json()["token"]
            self.client.headers["Authorization"] = f"Bearer {token}"

    def create_record(self, collection: str, data: dict) -> dict:
        resp = self.client.post(
            f"/api/collections/{collection}/records",
            json=data,
        )
        if resp.status_code >= 400:
            logger.error("Create %s failed (%s): %s", collection, resp.status_code, resp.text[:500])
            resp.raise_for_status()
        return resp.json()

    def get_collection_fields(self, collection: str) -> list[str]:
        """Get field names for a collection."""
        resp = self.client.get(f"/api/collections/{collection}")
        resp.raise_for_status()
        return [f["name"] for f in resp.json().get("fields", [])]


# ---------------------------------------------------------------------------
# Migration logic
# ---------------------------------------------------------------------------

def load_id_map() -> dict:
    if os.path.exists(ID_MAP_FILE):
        with open(ID_MAP_FILE) as f:
            return json.load(f)
    return {}


def save_id_map(id_map: dict) -> None:
    os.makedirs(os.path.dirname(ID_MAP_FILE), exist_ok=True)
    with open(ID_MAP_FILE, "w") as f:
        json.dump(id_map, f, indent=2)


def clean_row(row: dict, pb_fields: list[str]) -> dict:
    """Clean a Supabase row for PocketBase insertion."""
    cleaned = {}
    for key, value in row.items():
        # Skip columns we don't want
        if key in SKIP_COLUMNS or key == "id":
            continue

        # Rename timestamp columns
        if key == "created_at":
            key = "created"
        elif key == "updated_at":
            key = "updated"

        # Skip if PB collection doesn't have this field
        if key not in pb_fields and key not in ("created", "updated"):
            continue

        # Convert arrays to JSON if they're strings
        if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
            # PostgreSQL array format: {a,b,c}
            try:
                items = value[1:-1].split(",") if value != "{}" else []
                value = items
            except Exception:
                pass

        # Convert None to empty string for required text fields
        if value is None:
            continue  # Skip nulls, PB handles defaults

        cleaned[key] = value

    return cleaned


def migrate_table(table: str, pb: PBClient, id_map: dict, dry_run: bool = False) -> int:
    """Migrate a single table from Supabase to PocketBase."""
    logger.info("Migrating table: %s", table)

    # Get PB collection fields
    try:
        pb_fields = pb.get_collection_fields(table)
    except Exception as e:
        logger.error("Collection %s not found in PocketBase: %s", table, e)
        return 0

    # Fetch all rows from Supabase
    rows = query_supabase(f"SELECT * FROM {table} ORDER BY created_at ASC NULLS FIRST")
    logger.info("  Found %d rows in Supabase", len(rows))

    if table not in id_map:
        id_map[table] = {}

    migrated = 0
    for row in rows:
        old_id = row.get("id")
        if not old_id:
            continue

        # Skip if already migrated
        if old_id in id_map[table]:
            continue

        cleaned = clean_row(row, pb_fields)

        if dry_run:
            logger.info("  [DRY RUN] Would create: %s", json.dumps(cleaned)[:200])
            migrated += 1
            continue

        try:
            result = pb.create_record(table, cleaned)
            new_id = result["id"]
            id_map[table][old_id] = new_id
            migrated += 1

            if migrated % 100 == 0:
                logger.info("  Migrated %d rows...", migrated)
                save_id_map(id_map)

        except Exception as e:
            logger.error("  Failed to create record in %s: %s (data: %s)", table, e, json.dumps(cleaned)[:300])

    save_id_map(id_map)
    logger.info("  Migrated %d/%d rows for %s", migrated, len(rows), table)
    return migrated


def migrate_embeddings(table: str, id_map: dict, dry_run: bool = False) -> int:
    """Migrate embeddings from a Supabase table to the vector sidecar."""
    collection = EMBEDDING_TABLES[table]
    logger.info("Migrating embeddings: %s -> %s", table, collection)

    # Fetch rows with embeddings
    rows = query_supabase(
        f"SELECT id, embedding, content FROM {table} WHERE embedding IS NOT NULL"
    )
    logger.info("  Found %d rows with embeddings", len(rows))

    migrated = 0
    vec_client = httpx.Client(base_url=VEC_URL, timeout=60.0)

    for row in rows:
        old_id = row["id"]
        # Map to new PB ID
        new_id = id_map.get(table, {}).get(old_id, old_id)
        content = row.get("content", "")

        if dry_run:
            logger.info("  [DRY RUN] Would store embedding for %s", new_id)
            migrated += 1
            continue

        try:
            resp = vec_client.post("/embeddings/store", json={
                "collection": collection,
                "record_id": new_id,
                "text": content,
            })
            resp.raise_for_status()
            migrated += 1

            if migrated % 50 == 0:
                logger.info("  Stored %d embeddings...", migrated)

        except Exception as e:
            logger.error("  Failed to store embedding for %s: %s", new_id, e)

    vec_client.close()
    logger.info("  Migrated %d embeddings for %s", migrated, table)
    return migrated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Migrate Thesis data from Supabase to PocketBase")
    parser.add_argument("--pass", dest="migration_pass", choices=["1", "2", "3", "all"], default="all")
    parser.add_argument("--table", help="Migrate a single table")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without writing")
    args = parser.parse_args()

    id_map = load_id_map()
    pb = PBClient(PB_URL, PB_EMAIL, PB_PASSWORD)

    total = 0
    start = time.time()

    if args.table:
        total += migrate_table(args.table, pb, id_map, args.dry_run)
    else:
        if args.migration_pass in ("1", "all"):
            logger.info("===== PASS 1: Leaf collections =====")
            for table in PASS_1_TABLES:
                total += migrate_table(table, pb, id_map, args.dry_run)

        if args.migration_pass in ("2", "all"):
            logger.info("===== PASS 2: Relation collections =====")
            for table in PASS_2_TABLES:
                total += migrate_table(table, pb, id_map, args.dry_run)

        if args.migration_pass in ("3", "all"):
            logger.info("===== PASS 3: Embeddings =====")
            for table in EMBEDDING_TABLES:
                total += migrate_embeddings(table, id_map, args.dry_run)

    elapsed = time.time() - start
    logger.info("Migration complete: %d records in %.1fs", total, elapsed)
    logger.info("ID map saved to %s", ID_MAP_FILE)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test with dry run on a single table**

```bash
cd ~/Vault/GitHub/thesis
THESIS_POCKETBASE_URL=https://thesis-db.fly.dev \
THESIS_POCKETBASE_EMAIL=<email> \
THESIS_POCKETBASE_PASSWORD=<password> \
python scripts/migrate_supabase_to_pb.py --pass 1 --table ai_projects --dry-run
```

Expected: Prints rows that would be migrated without writing.

- [ ] **Step 3: Commit**

```bash
git add scripts/migrate_supabase_to_pb.py
git commit -m "feat: add Supabase-to-PocketBase data migration script"
```

---

### Task 8: Run data migration -- Pass 1 (leaf collections)

**Files:** None (data task)

- [ ] **Step 1: Run pass 1**

```bash
cd ~/Vault/GitHub/thesis
THESIS_POCKETBASE_URL=https://thesis-db.fly.dev \
THESIS_POCKETBASE_EMAIL=<email> \
THESIS_POCKETBASE_PASSWORD=<password> \
python scripts/migrate_supabase_to_pb.py --pass 1
```

- [ ] **Step 2: Verify record counts**

```bash
# Check a few key tables
curl -s "https://thesis-db.fly.dev/api/collections/ai_projects/records?perPage=1" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import json,sys; print('ai_projects:', json.load(sys.stdin)['totalItems'])"

curl -s "https://thesis-db.fly.dev/api/collections/stakeholders/records?perPage=1" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import json,sys; print('stakeholders:', json.load(sys.stdin)['totalItems'])"
```

- [ ] **Step 3: Verify ID map**

```bash
python3 -c "import json; m=json.load(open('scripts/id_map.json')); print(f'{len(m)} tables mapped'); print({k:len(v) for k,v in m.items()})"
```

---

### Task 9: Run data migration -- Pass 2 (relation collections)

**Files:** None (data task)

- [ ] **Step 1: Run pass 2**

```bash
THESIS_POCKETBASE_URL=https://thesis-db.fly.dev \
THESIS_POCKETBASE_EMAIL=<email> \
THESIS_POCKETBASE_PASSWORD=<password> \
python scripts/migrate_supabase_to_pb.py --pass 2
```

- [ ] **Step 2: Verify relation collections have data**

Spot-check `agent_handoffs`, `messages`, `document_chunks`, `disco_outputs`.

---

### Task 10: Run data migration -- Pass 3 (embeddings)

**Files:** None (data task)

- [ ] **Step 1: Run pass 3**

```bash
THESIS_POCKETBASE_URL=https://thesis-db.fly.dev \
THESIS_POCKETBASE_EMAIL=<email> \
THESIS_POCKETBASE_PASSWORD=<password> \
THESIS_VEC_URL=https://thesis-vec.fly.dev \
python scripts/migrate_supabase_to_pb.py --pass 3
```

Note: This pass re-embeds all text via Voyage AI. It will take longer and cost money. If the original embeddings should be preserved instead, modify the script to extract the raw vector from Supabase and POST directly to the vec sidecar's store endpoint with a pre-computed embedding.

- [ ] **Step 2: Verify embeddings**

```bash
curl -s https://thesis-vec.fly.dev/stats
```

Expected: Non-zero counts for document_chunks, help_chunks, etc.

- [ ] **Step 3: Test search**

```bash
curl -s -X POST https://thesis-vec.fly.dev/search \
  -H "Content-Type: application/json" \
  -d '{"collection":"help_chunks","query":"how to use the platform","limit":3}'
```

Expected: Returns search results with similarity scores.

---

### Task 11: Update Fly.io secrets for backend

**Files:** None (infrastructure task)

- [ ] **Step 1: Remove old Supabase secrets**

```bash
flyctl secrets unset SUPABASE_URL SUPABASE_KEY SUPABASE_SERVICE_ROLE_KEY SUPABASE_JWT_SECRET -a thesis-genai-api
```

- [ ] **Step 2: Add PocketBase + vec secrets**

```bash
flyctl secrets set \
  THESIS_POCKETBASE_URL=http://thesis-db.internal:8090 \
  THESIS_POCKETBASE_EMAIL=<superuser_email> \
  THESIS_POCKETBASE_PASSWORD=<superuser_password> \
  THESIS_VEC_URL=http://thesis-vec.internal:8080 \
  THESIS_API_KEY=$(openssl rand -hex 32) \
  -a thesis-genai-api
```

Save the generated API key to 1Password as "Thesis API Key".

- [ ] **Step 3: Redeploy backend**

```bash
flyctl deploy -a thesis-genai-api
```

- [ ] **Step 4: Verify health**

```bash
curl -s https://thesis-genai-api.fly.dev/health
```

Expected: `{"status":"healthy","database":"connected","version":"2.0.0"}`

---

### Task 12: Update frontend auth

**Files:**
- Modify: `frontend/.env.local`
- Modify: `frontend/lib/api.ts` (or equivalent API client file)
- Delete or stub: `frontend/contexts/AuthContext.tsx`

- [ ] **Step 1: Update environment variables**

In `frontend/.env.local`:

```bash
# REMOVE these:
# NEXT_PUBLIC_SUPABASE_URL=...
# NEXT_PUBLIC_SUPABASE_ANON_KEY=...

# ADD this:
NEXT_PUBLIC_API_KEY=<the-api-key-from-step-11>
NEXT_PUBLIC_API_URL=https://thesis-genai-api.fly.dev
```

- [ ] **Step 2: Update API client**

Find the frontend's API client module (likely `lib/api.ts` or `lib/supabase.ts`). Replace the Supabase client with a simple fetch wrapper:

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${API_KEY}`);
  headers.set('Content-Type', 'application/json');

  return fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });
}

export async function apiGet<T>(path: string): Promise<T> {
  const resp = await apiFetch(path);
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const resp = await apiFetch(path, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const resp = await apiFetch(path, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

export async function apiDelete(path: string): Promise<void> {
  const resp = await apiFetch(path, { method: 'DELETE' });
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
}
```

- [ ] **Step 3: Remove Supabase auth context**

Delete or stub `frontend/contexts/AuthContext.tsx`. Remove the `AuthProvider` wrapper from `_app.tsx` or `layout.tsx`. Remove login/logout UI components that reference Supabase auth.

- [ ] **Step 4: Remove @supabase/supabase-js dependency**

```bash
cd frontend && npm uninstall @supabase/supabase-js @supabase/auth-helpers-nextjs
```

- [ ] **Step 5: Build and verify**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no Supabase import errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "refactor: replace Supabase auth with API key in frontend"
```

---

### Task 13: Update frontend components

**Files:**
- All frontend components that call the Supabase client directly

- [ ] **Step 1: Find remaining Supabase imports**

```bash
cd frontend && grep -r "supabase\|@supabase\|createClient" --include="*.ts" --include="*.tsx" -l
```

- [ ] **Step 2: Replace each with apiFetch calls**

For each file found, replace:
```typescript
// BEFORE
import { supabase } from '@/lib/supabase';
const { data, error } = await supabase.from('ai_projects').select('*');

// AFTER
import { apiGet } from '@/lib/api';
const data = await apiGet<Project[]>('/api/projects/');
```

The frontend already calls the backend API for most things (the backend was the Supabase consumer). Only files that used the Supabase JS client directly (auth, realtime) need changes.

- [ ] **Step 3: Replace realtime subscriptions with polling**

If any components use Supabase realtime (`supabase.channel(...)` or `supabase.on(...)`), replace with polling:

```typescript
// BEFORE
const channel = supabase.channel('changes').on('postgres_changes', ...)

// AFTER
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await apiGet('/api/...');
    setData(data);
  }, 5000);
  return () => clearInterval(interval);
}, []);
```

- [ ] **Step 4: Build and test**

```bash
cd frontend && npm run build && npm run dev
```

Open in browser, verify core pages load.

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "refactor: remove all Supabase client usage from frontend"
```

---

### Task 14: End-to-end verification

**Files:** None (testing task)

- [ ] **Step 1: Start all services locally**

```bash
# Terminal 1: PocketBase (local)
docker build -f Dockerfile.pocketbase -t thesis-pb . && docker run -p 8090:8090 -v pb_data:/pb/pb_data thesis-pb

# Terminal 2: Vector sidecar (local)
cd vec_sidecar && pip install -r requirements.txt && VOYAGE_API_KEY=<key> VEC_DB_PATH=./vectors.db uvicorn main:app --port 8080

# Terminal 3: Backend
cd backend && THESIS_POCKETBASE_URL=http://127.0.0.1:8090 THESIS_POCKETBASE_EMAIL=<email> THESIS_POCKETBASE_PASSWORD=<password> THESIS_VEC_URL=http://127.0.0.1:8080 THESIS_API_KEY=test-key uvicorn main:app --reload --port 8000

# Terminal 4: Frontend
cd frontend && npm run dev
```

- [ ] **Step 2: Verify backend health**

```bash
curl -s http://localhost:8000/health
```

Expected: `{"status":"healthy","database":"connected","version":"2.0.0"}`

- [ ] **Step 3: Verify authenticated request**

```bash
curl -s http://localhost:8000/api/projects/ -H "Authorization: Bearer test-key"
```

Expected: JSON list of projects (or empty list if no data).

- [ ] **Step 4: Verify unauthenticated request rejected**

```bash
curl -s http://localhost:8000/api/projects/
```

Expected: `{"detail":"Invalid or missing API key"}` with 401 status.

- [ ] **Step 5: Run backend tests**

```bash
cd backend && python -m pytest tests/ -v --tb=short
```

Fix any remaining failures.

- [ ] **Step 6: Test frontend in browser**

Open http://localhost:3000, verify:
- Projects page loads and shows data
- Tasks page loads
- Chat works
- Document upload works
- Help search returns results

---

### Task 15: Deploy all services and verify production

**Files:** None (deployment task)

- [ ] **Step 1: Deploy backend**

```bash
flyctl deploy -a thesis-genai-api
```

- [ ] **Step 2: Deploy frontend**

Push to GitHub, Vercel auto-deploys. Set `NEXT_PUBLIC_API_KEY` in Vercel environment variables.

- [ ] **Step 3: Verify production health**

```bash
curl -s https://thesis-genai-api.fly.dev/health
curl -s https://thesis-db.fly.dev/api/health
curl -s https://thesis-vec.fly.dev/health
```

- [ ] **Step 4: Verify production authenticated request**

```bash
curl -s https://thesis-genai-api.fly.dev/api/projects/ \
  -H "Authorization: Bearer <production-api-key>"
```

- [ ] **Step 5: Test production frontend**

Open https://thesis-mvp.vercel.app, verify core functionality.

---

## Plan Self-Review

- **Spec coverage:** All Plan 3 items from the spec are covered: vector sidecar (FastAPI + sqlite-vec + Voyage AI), data migration script (3-pass), frontend auth changes (API key, Supabase removal), deployment, and end-to-end verification.
- **Placeholder scan:** No TBDs. All code blocks are complete. Migration script has full 3-pass logic with ID mapping.
- **Type consistency:** vec_sidecar uses `voyageai.Client` for embeddings. Migration script uses `httpx` for both Supabase Management API and PocketBase REST API. Frontend uses `apiFetch` wrapper consistently.
- **Spec gap:** The spec mentions updating the `/thesis` slash command skill to use PocketBase instead of Supabase MCP. This is outside the codebase and should be done separately after migration is verified.
