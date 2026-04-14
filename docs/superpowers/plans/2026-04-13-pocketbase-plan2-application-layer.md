# Application Layer + Backend Rewrite (Plan 2 of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all Supabase database access with PocketBase via a repository layer, replace JWT auth with API key auth, and update all routes and services.

**Architecture:** New `pb_client.py` (httpx wrapper) replaces `database.py`. New `repositories/` layer sits between routes/services and pb_client. Auth simplified to API key middleware. All 138 files that import `get_supabase` or `DatabaseService` must be updated.

**Tech Stack:** Python 3.12, FastAPI, httpx, pydantic-settings

**Spec:** `docs/superpowers/specs/2026-04-13-supabase-to-pocketbase-migration.md`

**Depends on:** Plan 1 (PocketBase deployed with all 78 collections)

---

## File Structure

```
backend/
  config.py                         -- NEW: pydantic-settings (replaces env vars scattered across files)
  pb_client.py                      -- NEW: PocketBase httpx wrapper (replaces database.py)
  vec_client.py                     -- NEW: Vector sidecar httpx wrapper
  auth.py                           -- REWRITE: API key middleware (replaces JWT/Supabase auth)
  database.py                       -- DELETE after migration complete
  main.py                           -- MODIFY: swap init, add auth middleware, remove backward compat routes
  repositories/
    __init__.py                     -- NEW
    projects.py                     -- NEW: ai_projects, project_candidates, project_documents, project_folders, project_conversations, project_stakeholder_link, portfolio_projects, roi_opportunities
    tasks.py                        -- NEW: project_tasks, task_candidates, task_comments, task_history
    agents.py                       -- NEW: agents, agent_handoffs, agent_instruction_versions, agent_knowledge_base, agent_topic_mapping
    stakeholders.py                 -- NEW: stakeholders, stakeholder_candidates, stakeholder_insights, stakeholder_metrics
    documents.py                    -- NEW: documents, document_chunks, document_classifications, document_tags
    conversations.py                -- NEW: conversations, messages, message_documents
    meetings.py                     -- NEW: meeting_rooms, meeting_room_messages, meeting_room_participants, meeting_transcripts
    help_repo.py                    -- NEW: help_documents, help_chunks, help_conversations, help_messages
    disco.py                        -- NEW: all disco_* collections
    purdy.py                        -- NEW: all purdy_* collections
    research.py                     -- NEW: research_tasks, research_sources, research_schedule
    obsidian.py                     -- NEW: obsidian_*, graph_* collections
    search.py                       -- NEW: wraps vec_client for unified search
    misc.py                         -- NEW: api_usage_logs, compass_status_reports, department_kpis, engagement_level_history, glean_*, knowledge_gaps, theme_settings, user_quick_prompts
  api/routes/*.py                   -- MODIFY: replace get_supabase imports with repository calls
  services/*.py                     -- MODIFY: replace get_supabase imports with repository calls
```

## Supabase-to-PocketBase Query Translation

This table governs ALL route and service rewrites. Every Supabase query builder call maps to a pb_client or repository call:

| Supabase Pattern | PocketBase Equivalent |
|-----------------|----------------------|
| `supabase = get_supabase()` | `from repositories import <domain> as <domain>_repo` |
| `supabase.table("X").select("*").execute()` | `pb.get_all("X")` |
| `supabase.table("X").select("*").eq("id", id).single().execute()` | `pb.get_record("X", id)` |
| `supabase.table("X").select("*").eq("status", "active").execute()` | `pb.get_all("X", filter="status='active'")` |
| `supabase.table("X").select("*").eq("a", v1).eq("b", v2).execute()` | `pb.get_all("X", filter="a='v1' && b='v2'")` |
| `supabase.table("X").select("*").neq("status", "done").execute()` | `pb.get_all("X", filter="status!='done'")` |
| `supabase.table("X").select("id, title").execute()` | `pb.get_all("X", fields="id,title")` |
| `supabase.table("X").select("*").order("updated_at", desc=True).execute()` | `pb.get_all("X", sort="-updated_at")` |
| `supabase.table("X").select("*").limit(10).execute()` | `pb.list_records("X", per_page=10)["items"]` |
| `supabase.table("X").select("*").range(0, 49).execute()` | `pb.list_records("X", page=1, per_page=50)["items"]` |
| `supabase.table("X").select("*").ilike("title", "%search%").execute()` | `pb.get_all("X", filter="title~'search'")` |
| `supabase.table("X").select("*").contains("arr", [val]).execute()` | `pb.get_all("X", filter="arr~'val'")` (json search) |
| `supabase.table("X").select("*").in_("id", ids).execute()` | Loop: `[pb.get_record("X", id) for id in ids]` or build OR filter |
| `supabase.table("X").select("*, Y(name)").execute()` | `pb.get_all("X", expand="Y")` then access `item["expand"]["Y"]` |
| `supabase.table("X").insert(data).execute()` | `pb.create_record("X", data)` |
| `supabase.table("X").upsert(data, on_conflict="a,b").execute()` | Check `get_first` then `create_record` or `update_record` |
| `supabase.table("X").update(data).eq("id", id).execute()` | `pb.update_record("X", id, data)` |
| `supabase.table("X").delete().eq("id", id).execute()` | `pb.delete_record("X", id)` |
| `supabase.table("X").select("id", count="exact").execute()` | `pb.count("X")` |
| `supabase.rpc("fn_name", params).execute()` | Implement in repository as application code |
| `.eq("client_id", cid)` | REMOVE (single-tenant, no client_id) |
| `Depends(get_current_user)` | `Depends(verify_api_key)` |
| `current_user["client_id"]` | REMOVE all references |
| `current_user["id"]` | REMOVE (no user tracking) |

### PocketBase filter syntax rules:
- String values use single quotes: `filter="status='active'"`
- AND: `&&`
- OR: `||`
- NOT EQUAL: `!=`
- LIKE (case-insensitive): `~`
- GREATER THAN: `>`
- Escape single quotes in values: `pb.escape_filter(value)`
- Date comparison: `filter="created>='2026-01-01 00:00:00'"`

### PocketBase sort syntax:
- Ascending: `sort="field_name"`
- Descending: `sort="-field_name"`
- Multiple: `sort="-updated,title"`

### Key behavioral differences:
1. **No `.single()` equivalent.** Use `pb.get_record(collection, id)` for ID lookups or `pb.get_first(collection, filter)` for filter lookups. Both return `None` instead of raising.
2. **No `client_id` filtering.** Remove all `.eq("client_id", ...)` chains. Single-tenant.
3. **No user ownership checks.** Remove `.eq("user_id", ...)`, `.eq("uploaded_by", ...)`. Single-user.
4. **No RLS.** PocketBase API rules set to `""` (any authenticated user). Backend authenticates as superuser.
5. **No `asyncio.to_thread`.** pb_client is synchronous (httpx.Client, not AsyncClient). Remove all `await asyncio.to_thread(lambda: ...)` wrappers around DB calls.
6. **`created_at`/`updated_at` become `created`/`updated`.** PocketBase autodate fields use these names by default.
7. **`total_score` and `tier` are not stored.** Compute via `repositories.projects.compute_scores()` after fetching.
8. **`result.data` becomes the return value directly.** No `.data` attribute -- pb_client returns plain dicts/lists.

---

### Task 1: Create config.py

**Files:**
- Create: `backend/config.py`

- [ ] **Step 1: Write the config module**

```python
"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PocketBase
    pocketbase_url: str = "http://127.0.0.1:8090"
    pocketbase_email: str = ""
    pocketbase_password: str = ""

    # Vector sidecar
    vec_url: str = "http://127.0.0.1:8080"

    # Auth
    api_key: str = ""

    # AI providers
    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    mem0_api_key: str = ""

    # Server
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    default_model: str = "claude-sonnet-4-6"
    cors_origins: str = ""
    environment: str = "development"

    # Neo4j (kept for graph features)
    neo4j_uri: str = ""
    neo4j_user: str = ""
    neo4j_password: str = ""

    model_config = {"env_prefix": "THESIS_"}


settings = Settings()
```

- [ ] **Step 2: Verify imports work**

```bash
cd backend && python -c "from config import settings; print(settings.pocketbase_url)"
```

Expected: `http://127.0.0.1:8090`

- [ ] **Step 3: Commit**

```bash
git add backend/config.py
git commit -m "feat: add pydantic-settings config for PocketBase migration"
```

---

### Task 2: Create pb_client.py

**Files:**
- Create: `backend/pb_client.py`
- Reference: `~/Vault/GitHub/glean-agent-factory-app/backend/pb_client.py`

- [ ] **Step 1: Write the PocketBase client**

Copy from GAF's `pb_client.py` (187 lines) and update the import:

```python
"""PocketBase HTTP client for Thesis.

Thin wrapper around httpx that maps to PocketBase's REST API.
All methods are synchronous (matching the old database.py contract).
Returns plain dicts -- no ORM, no SDK dependency.
"""

import logging
from urllib.parse import quote

import httpx

from config import settings

logger = logging.getLogger(__name__)

_client: httpx.Client | None = None


def init_pb() -> None:
    """Create the httpx client and authenticate as superuser. Called once at startup."""
    global _client
    _client = httpx.Client(
        base_url=settings.pocketbase_url,
        timeout=30.0,
    )

    if settings.pocketbase_email and settings.pocketbase_password:
        resp = _client.post(
            "/api/collections/_superusers/auth-with-password",
            json={
                "identity": settings.pocketbase_email,
                "password": settings.pocketbase_password,
            },
        )
        resp.raise_for_status()
        token = resp.json()["token"]
        _client.headers["Authorization"] = f"Bearer {token}"
        logger.info("PocketBase client authenticated as %s", settings.pocketbase_email)
    else:
        logger.warning("PocketBase credentials not set -- requests will be unauthenticated")

    logger.info("PocketBase client initialized: %s", settings.pocketbase_url)


def close_pb() -> None:
    """Close the httpx client. Called at shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def _get_client() -> httpx.Client:
    if _client is None:
        raise RuntimeError("PocketBase client not initialized -- call init_pb() first")
    return _client


# ---------------------------------------------------------------------------
# Core CRUD
# ---------------------------------------------------------------------------

def list_records(
    collection: str,
    *,
    filter: str = "",
    sort: str = "",
    page: int = 1,
    per_page: int = 200,
    expand: str = "",
    fields: str = "",
) -> dict:
    """List records from a collection.

    Returns the full PocketBase response:
    {page, perPage, totalPages, totalItems, items: [...]}
    """
    params: dict = {"page": page, "perPage": per_page}
    if filter:
        params["filter"] = filter
    if sort:
        params["sort"] = sort
    if expand:
        params["expand"] = expand
    if fields:
        params["fields"] = fields

    resp = _get_client().get(f"/api/collections/{collection}/records", params=params)
    resp.raise_for_status()
    return resp.json()


def get_record(collection: str, record_id: str, *, expand: str = "") -> dict | None:
    """Get a single record by ID. Returns None if not found."""
    params = {}
    if expand:
        params["expand"] = expand
    try:
        resp = _get_client().get(
            f"/api/collections/{collection}/records/{record_id}",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise


def create_record(collection: str, data: dict) -> dict:
    """Create a record. Returns the created record (including id, created, updated)."""
    resp = _get_client().post(
        f"/api/collections/{collection}/records",
        json=data,
    )
    if resp.status_code >= 400:
        logger.error("PocketBase create %s failed (%s): %s", collection, resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


def update_record(collection: str, record_id: str, data: dict) -> dict:
    """Update a record. Returns the updated record."""
    resp = _get_client().patch(
        f"/api/collections/{collection}/records/{record_id}",
        json=data,
    )
    resp.raise_for_status()
    return resp.json()


def delete_record(collection: str, record_id: str) -> None:
    """Delete a record."""
    resp = _get_client().delete(
        f"/api/collections/{collection}/records/{record_id}",
    )
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def get_first(collection: str, filter: str, *, sort: str = "", expand: str = "") -> dict | None:
    """Get the first record matching a filter, or None."""
    result = list_records(collection, filter=filter, sort=sort, per_page=1, expand=expand)
    items = result.get("items", [])
    return items[0] if items else None


def get_all(collection: str, *, filter: str = "", sort: str = "", expand: str = "") -> list[dict]:
    """Fetch all records from a collection (handles pagination).

    For small collections (< 500 records), this is a single request.
    For larger ones, it paginates automatically.
    """
    all_items = []
    page = 1
    while True:
        result = list_records(
            collection, filter=filter, sort=sort, expand=expand,
            page=page, per_page=500,
        )
        all_items.extend(result.get("items", []))
        if page >= result.get("totalPages", 1):
            break
        page += 1
    return all_items


def count(collection: str, *, filter: str = "") -> int:
    """Count records in a collection."""
    result = list_records(collection, filter=filter, per_page=1, fields="id")
    return result.get("totalItems", 0)


def escape_filter(value: str) -> str:
    """Escape a string value for use in PocketBase filter expressions.

    PocketBase filters use single quotes for string values.
    This escapes single quotes within the value.
    """
    return value.replace("'", "\\'")
```

- [ ] **Step 2: Verify imports work**

```bash
cd backend && python -c "import pb_client; print('pb_client imported OK')"
```

Expected: `pb_client imported OK`

- [ ] **Step 3: Commit**

```bash
git add backend/pb_client.py
git commit -m "feat: add PocketBase httpx client for Thesis"
```

---

### Task 3: Create vec_client.py

**Files:**
- Create: `backend/vec_client.py`

- [ ] **Step 1: Write the vector sidecar client**

```python
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
    """Store a text embedding in the vector database.

    Args:
        collection: The collection name (e.g. "document_chunks", "help_chunks")
        record_id: The PocketBase record ID to associate with
        text: The text content to embed
        title: Optional title for search result display

    Returns:
        dict with id and status
    """
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
    """Search for similar documents in a collection.

    Args:
        collection: The collection to search in
        query: The search query text
        limit: Maximum number of results

    Returns:
        List of dicts with id, collection, title, content_preview, similarity
    """
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/vec_client.py
git commit -m "feat: add vector sidecar httpx client"
```

---

### Task 4: Rewrite auth.py

**Files:**
- Modify: `backend/auth.py`

Replace the entire 398-line JWT auth module with API key middleware.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_auth_apikey.py
import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth import verify_api_key


@pytest.fixture
def app():
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    app.middleware("http")(verify_api_key)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_valid_api_key(client):
    with patch("auth.settings") as mock_settings:
        mock_settings.api_key = "test-key-123"
        resp = client.get("/test", headers={"Authorization": "Bearer test-key-123"})
        assert resp.status_code == 200


def test_invalid_api_key(client):
    with patch("auth.settings") as mock_settings:
        mock_settings.api_key = "test-key-123"
        resp = client.get("/test", headers={"Authorization": "Bearer wrong-key"})
        assert resp.status_code == 401


def test_missing_api_key(client):
    with patch("auth.settings") as mock_settings:
        mock_settings.api_key = "test-key-123"
        resp = client.get("/test")
        assert resp.status_code == 401


def test_health_bypasses_auth(client):
    with patch("auth.settings") as mock_settings:
        mock_settings.api_key = "test-key-123"
        resp = client.get("/health")
        assert resp.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_auth_apikey.py -v
```

Expected: FAIL (auth.py still has JWT code)

- [ ] **Step 3: Rewrite auth.py**

Replace the entire contents of `backend/auth.py` with:

```python
"""API key authentication middleware.

Replaces Supabase JWT auth with a simple API key check.
All requests must include Authorization: Bearer <api_key>
except for health/docs endpoints.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from config import settings

logger = logging.getLogger(__name__)

# Paths that bypass authentication
PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}


async def verify_api_key(request: Request, call_next):
    """Middleware that checks API key on all requests except public paths."""
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    # Allow OPTIONS for CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {settings.api_key}"

    if not settings.api_key or auth != expected:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key"},
        )

    return await call_next(request)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_auth_apikey.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/auth.py tests/test_auth_apikey.py
git commit -m "feat: replace JWT auth with API key middleware"
```

---

### Task 5: Update main.py

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Update imports and lifespan**

Replace the database import and initialization at line 23-24 and line 427:

```python
# REMOVE these lines:
from database import get_supabase
# ...
supabase = get_supabase()

# ADD these lines (after load_dotenv):
from pb_client import init_pb, close_pb
from vec_client import init_vec, close_vec
```

In the `lifespan` function, add PocketBase init at startup (before schedulers) and close at shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_pb()
    init_vec()

    # ... existing scheduler code stays ...

    yield

    # Shutdown
    close_pb()
    close_vec()

    # ... existing scheduler shutdown code stays ...
```

- [ ] **Step 2: Add auth middleware**

After the existing middleware registrations, add:

```python
from auth import verify_api_key
app.middleware("http")(verify_api_key)
```

- [ ] **Step 3: Remove backward compatibility routes**

Delete the backward compatibility section (lines ~515-597) that uses the module-level `supabase` variable:
- `list_client_conversations`
- `get_user_storage`
- `get_user_documents`

These rely on `client_id` and `user_id` which no longer exist.

- [ ] **Step 4: Update health check**

Replace the health check that queries `users` table:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        import pb_client as pb
        pb.list_records("ai_projects", per_page=1, fields="id")
        return {"status": "healthy", "database": "connected", "version": "2.0.0"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
```

- [ ] **Step 5: Remove `Depends(get_current_user)` import**

Remove `from auth import get_current_user` (line ~519) and its usage in backward compat routes.

- [ ] **Step 6: Commit**

```bash
git add backend/main.py
git commit -m "feat: wire PocketBase client and API key auth into main.py"
```

---

### Task 6: Create repositories/__init__.py

**Files:**
- Create: `backend/repositories/__init__.py`

- [ ] **Step 1: Create the init file**

```python
"""Repository layer for PocketBase data access.

Each module wraps pb_client calls for a domain, providing typed
functions that routes and services import directly.
"""
```

- [ ] **Step 2: Commit**

```bash
git add backend/repositories/__init__.py
git commit -m "feat: add repositories package for PocketBase layer"
```

---

### Task 7: Create repositories/projects.py

**Files:**
- Create: `backend/repositories/projects.py`
- Test: `backend/tests/test_repo_projects.py`

This is the most complex repository -- it serves `api/routes/projects.py` (2473 lines, 30+ endpoints). It covers: `ai_projects`, `project_candidates`, `project_documents`, `project_folders`, `project_conversations`, `project_stakeholder_link`, `portfolio_projects`, `roi_opportunities`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_repo_projects.py
import pytest
from unittest.mock import patch, MagicMock

from repositories.projects import (
    list_projects,
    get_project,
    create_project,
    update_project,
    delete_project,
    compute_scores,
    list_project_candidates,
    get_project_stakeholder_links,
)


def test_compute_scores_all_fives():
    project = {
        "roi_potential": 5,
        "implementation_effort": 5,
        "strategic_alignment": 5,
        "stakeholder_readiness": 5,
    }
    result = compute_scores(project)
    assert result["total_score"] == 20
    assert result["tier"] == 1


def test_compute_scores_all_ones():
    project = {
        "roi_potential": 1,
        "implementation_effort": 1,
        "strategic_alignment": 1,
        "stakeholder_readiness": 1,
    }
    result = compute_scores(project)
    assert result["total_score"] == 4
    assert result["tier"] == 4


def test_compute_scores_missing_values():
    project = {"roi_potential": 4}
    result = compute_scores(project)
    assert result["total_score"] == 4
    assert result["tier"] == 4


def test_compute_scores_tier_boundaries():
    # Tier 1: >= 16
    assert compute_scores({"roi_potential": 4, "implementation_effort": 4, "strategic_alignment": 4, "stakeholder_readiness": 4})["tier"] == 1
    # Tier 2: >= 12
    assert compute_scores({"roi_potential": 3, "implementation_effort": 3, "strategic_alignment": 3, "stakeholder_readiness": 3})["tier"] == 2
    # Tier 3: >= 8
    assert compute_scores({"roi_potential": 2, "implementation_effort": 2, "strategic_alignment": 2, "stakeholder_readiness": 2})["tier"] == 3
    # Tier 4: < 8
    assert compute_scores({"roi_potential": 1, "implementation_effort": 1, "strategic_alignment": 1, "stakeholder_readiness": 1})["tier"] == 4


@patch("repositories.projects.pb")
def test_list_projects(mock_pb):
    mock_pb.get_all.return_value = [
        {"id": "abc", "project_code": "T01", "title": "Test", "roi_potential": 5,
         "implementation_effort": 5, "strategic_alignment": 5, "stakeholder_readiness": 5}
    ]
    result = list_projects()
    mock_pb.get_all.assert_called_once()
    assert len(result) == 1
    assert result[0]["total_score"] == 20
    assert result[0]["tier"] == 1


@patch("repositories.projects.pb")
def test_get_project_not_found(mock_pb):
    mock_pb.get_record.return_value = None
    result = get_project("nonexistent")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_repo_projects.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: Write the repository**

```python
# repositories/projects.py
"""Repository for project-related collections.

Collections: ai_projects, project_candidates, project_documents,
project_folders, project_conversations, project_stakeholder_link,
portfolio_projects, roi_opportunities.
"""

import pb_client as pb


# ---------------------------------------------------------------------------
# Computed fields (replaces PostgreSQL GENERATED columns)
# ---------------------------------------------------------------------------

def compute_scores(project: dict) -> dict:
    """Add computed total_score and tier to a project dict."""
    scores = [
        project.get("roi_potential") or 0,
        project.get("implementation_effort") or 0,
        project.get("strategic_alignment") or 0,
        project.get("stakeholder_readiness") or 0,
    ]
    total = sum(scores)
    if total >= 16:
        tier = 1
    elif total >= 12:
        tier = 2
    elif total >= 8:
        tier = 3
    else:
        tier = 4
    return {**project, "total_score": total, "tier": tier}


def _with_scores(projects: list[dict]) -> list[dict]:
    """Apply compute_scores to a list of projects."""
    return [compute_scores(p) for p in projects]


# ---------------------------------------------------------------------------
# ai_projects
# ---------------------------------------------------------------------------

def list_projects(
    *,
    department: str = "",
    tier: int = 0,
    status: str = "",
    owner_stakeholder_id: str = "",
    sort: str = "-updated",
    limit: int = 0,
    offset: int = 0,
) -> list[dict]:
    """List projects with optional filters."""
    parts = []
    if department:
        parts.append(f"department='{pb.escape_filter(department)}'")
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    if owner_stakeholder_id:
        parts.append(f"owner_stakeholder_id='{pb.escape_filter(owner_stakeholder_id)}'")
    filter_str = " && ".join(parts)

    if limit:
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records("ai_projects", filter=filter_str, sort=sort, page=page, per_page=limit)
        projects = _with_scores(result.get("items", []))
    else:
        projects = _with_scores(pb.get_all("ai_projects", filter=filter_str, sort=sort))

    # Post-filter tier (computed, not stored)
    if tier:
        projects = [p for p in projects if p.get("tier") == tier]

    return projects


def get_project(project_id: str) -> dict | None:
    """Get a single project by ID, with computed scores."""
    record = pb.get_record("ai_projects", project_id)
    return compute_scores(record) if record else None


def create_project(data: dict) -> dict:
    """Create a project. Returns the created record with computed scores."""
    # Remove fields that don't exist in PocketBase
    data.pop("client_id", None)
    data.pop("total_score", None)
    data.pop("tier", None)
    return compute_scores(pb.create_record("ai_projects", data))


def update_project(project_id: str, data: dict) -> dict:
    """Update a project. Returns the updated record with computed scores."""
    data.pop("client_id", None)
    data.pop("total_score", None)
    data.pop("tier", None)
    return compute_scores(pb.update_record("ai_projects", project_id, data))


def delete_project(project_id: str) -> None:
    """Delete a project."""
    pb.delete_record("ai_projects", project_id)


def get_projects_summary() -> dict:
    """Get summary counts by tier, status, department."""
    projects = _with_scores(pb.get_all("ai_projects", fields="id,roi_potential,implementation_effort,strategic_alignment,stakeholder_readiness,status,department"))
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    status_counts: dict[str, int] = {}
    dept_counts: dict[str, int] = {}
    for p in projects:
        tier_counts[p.get("tier", 4)] = tier_counts.get(p.get("tier", 4), 0) + 1
        s = p.get("status", "backlog")
        status_counts[s] = status_counts.get(s, 0) + 1
        d = p.get("department") or "unassigned"
        dept_counts[d] = dept_counts.get(d, 0) + 1
    return {"total": len(projects), "by_tier": tier_counts, "by_status": status_counts, "by_department": dept_counts}


# ---------------------------------------------------------------------------
# project_candidates
# ---------------------------------------------------------------------------

def list_project_candidates(*, status: str = "pending", limit: int = 50, offset: int = 0) -> list[dict]:
    page = (offset // limit) + 1 if limit else 1
    result = pb.list_records(
        "project_candidates",
        filter=f"status='{pb.escape_filter(status)}'",
        sort="-created",
        page=page,
        per_page=limit,
    )
    return result.get("items", [])


def get_project_candidate(candidate_id: str) -> dict | None:
    return pb.get_record("project_candidates", candidate_id)


def update_project_candidate(candidate_id: str, data: dict) -> dict:
    return pb.update_record("project_candidates", candidate_id, data)


def count_pending_candidates() -> int:
    return pb.count("project_candidates", filter="status='pending'")


# ---------------------------------------------------------------------------
# project_documents (junction table)
# ---------------------------------------------------------------------------

def get_project_documents(project_id: str) -> list[dict]:
    esc = pb.escape_filter(project_id)
    return pb.get_all("project_documents", filter=f"project_id='{esc}'", sort="-created")


def link_document(project_id: str, document_id: str, linked_by: str = "") -> dict:
    existing = pb.get_first("project_documents", filter=f"project_id='{pb.escape_filter(project_id)}' && document_id='{pb.escape_filter(document_id)}'")
    if existing:
        return existing
    return pb.create_record("project_documents", {
        "project_id": project_id,
        "document_id": document_id,
        "linked_by": linked_by,
    })


def unlink_document(project_id: str, document_id: str) -> None:
    record = pb.get_first("project_documents", filter=f"project_id='{pb.escape_filter(project_id)}' && document_id='{pb.escape_filter(document_id)}'")
    if record:
        pb.delete_record("project_documents", record["id"])


# ---------------------------------------------------------------------------
# project_folders
# ---------------------------------------------------------------------------

def get_project_folders(project_id: str) -> list[dict]:
    return pb.get_all("project_folders", filter=f"project_id='{pb.escape_filter(project_id)}'", sort="folder_path")


def link_folder(project_id: str, folder_path: str, recursive: bool = True, linked_by: str = "") -> dict:
    existing = pb.get_first("project_folders", filter=f"project_id='{pb.escape_filter(project_id)}' && folder_path='{pb.escape_filter(folder_path)}'")
    if existing:
        return pb.update_record("project_folders", existing["id"], {"recursive": recursive, "linked_by": linked_by})
    return pb.create_record("project_folders", {
        "project_id": project_id,
        "folder_path": folder_path,
        "recursive": recursive,
        "linked_by": linked_by,
    })


def unlink_folder(project_id: str, folder_path: str) -> None:
    record = pb.get_first("project_folders", filter=f"project_id='{pb.escape_filter(project_id)}' && folder_path='{pb.escape_filter(folder_path)}'")
    if record:
        pb.delete_record("project_folders", record["id"])


# ---------------------------------------------------------------------------
# project_stakeholder_link
# ---------------------------------------------------------------------------

def get_project_stakeholder_links(project_id: str) -> list[dict]:
    return pb.get_all("project_stakeholder_link", filter=f"project_id='{pb.escape_filter(project_id)}'")


def link_stakeholder(project_id: str, stakeholder_id: str, role: str = "involved", notes: str = "") -> dict:
    return pb.create_record("project_stakeholder_link", {
        "project_id": project_id,
        "stakeholder_id": stakeholder_id,
        "role": role,
        "notes": notes,
    })


def unlink_stakeholder(project_id: str, stakeholder_id: str) -> None:
    record = pb.get_first("project_stakeholder_link", filter=f"project_id='{pb.escape_filter(project_id)}' && stakeholder_id='{pb.escape_filter(stakeholder_id)}'")
    if record:
        pb.delete_record("project_stakeholder_link", record["id"])


# ---------------------------------------------------------------------------
# project_conversations
# ---------------------------------------------------------------------------

def get_project_conversations(project_id: str, *, limit: int = 20, offset: int = 0) -> list[dict]:
    page = (offset // limit) + 1 if limit else 1
    result = pb.list_records(
        "project_conversations",
        filter=f"project_id='{pb.escape_filter(project_id)}'",
        sort="-created",
        page=page,
        per_page=limit,
    )
    return result.get("items", [])


def create_project_conversation(data: dict) -> dict:
    return pb.create_record("project_conversations", data)


# ---------------------------------------------------------------------------
# portfolio_projects
# ---------------------------------------------------------------------------

def list_portfolio_projects(**kwargs) -> list[dict]:
    parts = []
    for key, val in kwargs.items():
        if val:
            parts.append(f"{key}='{pb.escape_filter(str(val))}'")
    return pb.get_all("portfolio_projects", filter=" && ".join(parts), sort="-updated")


# ---------------------------------------------------------------------------
# roi_opportunities
# ---------------------------------------------------------------------------

def list_roi_opportunities(**kwargs) -> list[dict]:
    parts = []
    for key, val in kwargs.items():
        if val:
            parts.append(f"{key}='{pb.escape_filter(str(val))}'")
    return pb.get_all("roi_opportunities", filter=" && ".join(parts), sort="-updated")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_repo_projects.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/repositories/projects.py tests/test_repo_projects.py
git commit -m "feat: add projects repository with computed scores"
```

---

### Task 8: Create repositories/tasks.py

**Files:**
- Create: `backend/repositories/tasks.py`

- [ ] **Step 1: Write the repository**

Collections: `project_tasks`, `task_candidates`, `task_comments`, `task_history`.

Follow the same pattern as `repositories/projects.py`. Key functions:

```python
# repositories/tasks.py
import pb_client as pb

def list_tasks(*, project_id: str = "", status: str = "", priority: str = "",
               sort: str = "-updated", limit: int = 0, offset: int = 0) -> list[dict]:
    parts = []
    if project_id:
        esc = pb.escape_filter(project_id)
        parts.append(f"(source_project_id='{esc}' || linked_project_id='{esc}')")
    if status:
        parts.append(f"status='{pb.escape_filter(status)}'")
    if priority:
        parts.append(f"priority='{pb.escape_filter(priority)}'")
    filter_str = " && ".join(parts)
    if limit:
        page = (offset // limit) + 1 if limit else 1
        result = pb.list_records("project_tasks", filter=filter_str, sort=sort, page=page, per_page=limit)
        return result.get("items", [])
    return pb.get_all("project_tasks", filter=filter_str, sort=sort)

def get_task(task_id: str) -> dict | None:
    return pb.get_record("project_tasks", task_id)

def create_task(data: dict) -> dict:
    data.pop("client_id", None)
    data.pop("user_id", None)
    return pb.create_record("project_tasks", data)

def update_task(task_id: str, data: dict) -> dict:
    return pb.update_record("project_tasks", task_id, data)

def delete_task(task_id: str) -> None:
    pb.delete_record("project_tasks", task_id)

# task_candidates
def list_task_candidates(*, status: str = "pending", limit: int = 50) -> list[dict]:
    result = pb.list_records("task_candidates", filter=f"status='{pb.escape_filter(status)}'", sort="-created", per_page=limit)
    return result.get("items", [])

def get_task_candidate(candidate_id: str) -> dict | None:
    return pb.get_record("task_candidates", candidate_id)

def update_task_candidate(candidate_id: str, data: dict) -> dict:
    return pb.update_record("task_candidates", candidate_id, data)

def count_pending_task_candidates() -> int:
    return pb.count("task_candidates", filter="status='pending'")

# task_comments
def get_task_comments(task_id: str) -> list[dict]:
    return pb.get_all("task_comments", filter=f"task_id='{pb.escape_filter(task_id)}'", sort="created")

def create_task_comment(data: dict) -> dict:
    return pb.create_record("task_comments", data)

# task_history
def get_task_history(task_id: str) -> list[dict]:
    return pb.get_all("task_history", filter=f"task_id='{pb.escape_filter(task_id)}'", sort="-created")

def create_task_history(data: dict) -> dict:
    return pb.create_record("task_history", data)
```

- [ ] **Step 2: Commit**

```bash
git add backend/repositories/tasks.py
git commit -m "feat: add tasks repository"
```

---

### Task 9: Create remaining repositories (agents, stakeholders, documents, conversations, meetings, help, disco, purdy, research, obsidian, search, misc)

**Files:**
- Create: `backend/repositories/agents.py`
- Create: `backend/repositories/stakeholders.py`
- Create: `backend/repositories/documents.py`
- Create: `backend/repositories/conversations.py`
- Create: `backend/repositories/meetings.py`
- Create: `backend/repositories/help_repo.py`
- Create: `backend/repositories/disco.py`
- Create: `backend/repositories/purdy.py`
- Create: `backend/repositories/research.py`
- Create: `backend/repositories/obsidian.py`
- Create: `backend/repositories/search.py`
- Create: `backend/repositories/misc.py`

Each follows the identical pattern as `repositories/projects.py` and `repositories/tasks.py`. The standard functions per collection are:

```python
import pb_client as pb

# For each collection <name>:
def list_<plural>(**filter_kwargs) -> list[dict]
def get_<singular>(id: str) -> dict | None
def create_<singular>(data: dict) -> dict
def update_<singular>(id: str, data: dict) -> dict
def delete_<singular>(id: str) -> None
```

**Implementation notes per repository:**

- [ ] **Step 1: agents.py** -- Collections: agents, agent_handoffs, agent_instruction_versions, agent_knowledge_base, agent_topic_mapping. Key: `list_agents(is_active=True)` filters on `is_active=true`.

- [ ] **Step 2: stakeholders.py** -- Collections: stakeholders, stakeholder_candidates, stakeholder_insights, stakeholder_metrics. Key: `search_stakeholders(query)` uses `filter="name~'query' || email~'query'"`.

- [ ] **Step 3: documents.py** -- Collections: documents, document_chunks, document_classifications, document_tags. Key: `search_documents(query)` delegates to `vec_client.search("document_chunks", query)` then fetches parent documents. Skip `embedding` column entirely.

- [ ] **Step 4: conversations.py** -- Collections: conversations, messages, message_documents. Key: `get_conversation_messages(conv_id)` sorts by created ascending.

- [ ] **Step 5: meetings.py** -- Collections: meeting_rooms, meeting_room_messages, meeting_room_participants, meeting_transcripts. Key: `get_room_messages(room_id, since_turn=N)` for incremental fetching.

- [ ] **Step 6: help_repo.py** (not `help.py` -- shadows Python builtin) -- Collections: help_documents, help_chunks, help_conversations, help_messages. Key: `search_help(query)` delegates to `vec_client.search("help_chunks", query)`.

- [ ] **Step 7: disco.py** -- All 18 `disco_*` collections. This is the largest repository. Group functions by sub-domain: initiatives, runs, outputs, bundles, PRDs, documents, system KB, messages, checkpoints, folders, members, metrics.

- [ ] **Step 8: purdy.py** -- All 11 `purdy_*` collections. Mirrors disco.py structure but simpler.

- [ ] **Step 9: research.py** -- Collections: research_tasks, research_sources, research_schedule. Straightforward CRUD.

- [ ] **Step 10: obsidian.py** -- Collections: obsidian_sync_log, obsidian_sync_state, obsidian_vault_configs, graph_sync_log, graph_sync_state.

- [ ] **Step 11: search.py** -- Wraps vec_client for unified search. Functions: `search_all(query, collections, limit)`, `search_documents(query)`, `search_help(query)`, `search_disco(query)`.

- [ ] **Step 12: misc.py** -- Collections: api_usage_logs, compass_status_reports, department_kpis, engagement_level_history, glean_connectors, glean_connector_gaps, glean_connector_requests, glean_connector_summary, glean_disco_integration_matrix, knowledge_gaps, theme_settings, user_quick_prompts. Each gets basic CRUD.

- [ ] **Step 13: Commit all repositories**

```bash
git add backend/repositories/
git commit -m "feat: add all 12 remaining repository modules"
```

---

### Task 10: Rewrite route files -- Projects domain

**Files:**
- Modify: `backend/api/routes/projects.py`
- Modify: `backend/api/routes/portfolio.py`
- Modify: `backend/api/routes/opportunities.py`
- Modify: `backend/api/routes/strategy.py`

For each route file, apply these mechanical transformations:

1. Replace `from database import get_supabase` with `from repositories import projects as projects_repo`
2. Remove `Depends(get_current_user)` from all endpoint parameters
3. Remove `supabase=Depends(get_supabase)` from all endpoint parameters
4. Remove all `current_user["client_id"]` and `current_user["id"]` references
5. Replace `supabase.table("ai_projects").select(...)...execute()` chains with repository calls
6. Remove `asyncio.to_thread(lambda: ...)` wrappers (pb_client is already synchronous)
7. Replace `result.data` with direct return values (pb_client returns plain dicts)

**Example transformation for `list_projects` endpoint:**

```python
# BEFORE (projects.py:387-428)
@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    department: Optional[str] = None,
    tier: Optional[int] = Query(None, ge=1, le=4),
    status: Optional[str] = None,
    owner_stakeholder_id: Optional[str] = None,
    initiative_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase),
):
    query = supabase.table("ai_projects").select("*").eq("client_id", current_user["client_id"])
    if department:
        query = query.eq("department", department)
    # ... more filters ...
    result = query.order("total_score", desc=True).range(offset, offset + limit - 1).execute()
    proj_ids = [p["id"] for p in result.data]
    owner_names = await _get_owner_names(supabase, proj_ids)
    return [_format_project(p, owner_names.get(p["id"])) for p in result.data]

# AFTER
@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    department: Optional[str] = None,
    tier: Optional[int] = Query(None, ge=1, le=4),
    status: Optional[str] = None,
    owner_stakeholder_id: Optional[str] = None,
    initiative_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    projects = projects_repo.list_projects(
        department=department or "",
        tier=tier or 0,
        status=status or "",
        owner_stakeholder_id=owner_stakeholder_id or "",
        limit=limit,
        offset=offset,
    )
    # Owner name lookup via stakeholders repo
    from repositories import stakeholders as sh_repo
    for p in projects:
        if p.get("owner_stakeholder_id"):
            owner = sh_repo.get_stakeholder(p["owner_stakeholder_id"])
            p["owner_name"] = owner["name"] if owner else None
    return [_format_project(p, p.get("owner_name")) for p in projects]
```

- [ ] **Step 1: Rewrite `api/routes/projects.py`**

Apply the transformation pattern above to all ~30 endpoints. Key changes:
- All `supabase.table("ai_projects")...` calls become `projects_repo.*` calls
- All `supabase.table("project_candidates")...` calls become `projects_repo.list_project_candidates(...)` etc.
- All `supabase.table("project_documents")...` calls become `projects_repo.link_document(...)` etc.
- All `supabase.table("project_stakeholder_link")...` calls become `projects_repo.link_stakeholder(...)` etc.
- All `supabase.table("project_folders")...` calls become `projects_repo.link_folder(...)` etc.
- `supabase.rpc("count_project_codes_by_prefix", ...)` becomes `projects_repo.count_project_codes_by_prefix(...)` (implement in repo using `pb.count("ai_projects", filter="project_code~'^{prefix}'")`)
- `_get_owner_names` helper refactored to use stakeholders repo
- Remove `get_default_client_id` import and usage

- [ ] **Step 2: Rewrite `api/routes/portfolio.py`, `opportunities.py`, `strategy.py`**

Same transformation pattern. These are smaller files.

- [ ] **Step 3: Run existing tests**

```bash
cd backend && python -m pytest tests/test_integration.py -v -k "project"
```

Fix any failures by updating test mocks from Supabase to pb_client.

- [ ] **Step 4: Commit**

```bash
git add backend/api/routes/projects.py backend/api/routes/portfolio.py backend/api/routes/opportunities.py backend/api/routes/strategy.py
git commit -m "refactor: rewrite project routes to use PocketBase repository"
```

---

### Task 11: Rewrite route files -- Tasks domain

**Files:**
- Modify: `backend/api/routes/tasks.py`

- [ ] **Step 1: Apply transformations**

Same pattern. Replace `from database import get_supabase` with `from repositories import tasks as tasks_repo`. Replace all `supabase.table("project_tasks")` with `tasks_repo.*` calls. Remove `client_id`, `user_id` filters.

- [ ] **Step 2: Commit**

```bash
git add backend/api/routes/tasks.py
git commit -m "refactor: rewrite task routes to use PocketBase repository"
```

---

### Task 12: Rewrite route files -- Chat + Conversations domain

**Files:**
- Modify: `backend/api/routes/chat.py`
- Modify: `backend/api/routes/conversations.py`

- [ ] **Step 1: Apply transformations**

Use `from repositories import conversations as conv_repo`. Replace `supabase.table("conversations")`, `supabase.table("messages")` calls.

- [ ] **Step 2: Commit**

```bash
git add backend/api/routes/chat.py backend/api/routes/conversations.py
git commit -m "refactor: rewrite chat/conversation routes to use PocketBase repository"
```

---

### Task 13: Rewrite route files -- Documents domain

**Files:**
- Modify: `backend/api/routes/documents/crud.py`
- Modify: `backend/api/routes/documents/search.py`
- Modify: `backend/api/routes/documents/upload.py`
- Modify: `backend/api/routes/documents/admin.py`
- Modify: `backend/api/routes/documents/agents_and_classification.py`
- Modify: `backend/api/routes/documents/tags_and_metadata.py`
- Modify: `backend/api/routes/documents/_shared.py`
- Modify: `backend/api/routes/document_mappings.py`

- [ ] **Step 1: Apply transformations**

Use `from repositories import documents as docs_repo`. Replace all Supabase query builder calls. For search, replace `supabase.rpc("match_chunks", ...)` with `docs_repo.search_documents(query)`.

- [ ] **Step 2: Commit**

```bash
git add backend/api/routes/documents/ backend/api/routes/document_mappings.py
git commit -m "refactor: rewrite document routes to use PocketBase repository"
```

---

### Task 14: Rewrite route files -- Agents, Stakeholders, Meetings, Help

**Files:**
- Modify: `backend/api/routes/agents.py`
- Modify: `backend/api/routes/stakeholders.py`
- Modify: `backend/api/routes/stakeholder_metrics.py`
- Modify: `backend/api/routes/meeting_rooms.py`
- Modify: `backend/api/routes/meeting_prep.py`
- Modify: `backend/api/routes/help_chat.py`
- Modify: `backend/api/routes/system_instructions.py`
- Modify: `backend/api/routes/transcripts.py`

- [ ] **Step 1: Apply transformations for each file**

Each file follows the same mechanical pattern. Use the appropriate repository import.

- [ ] **Step 2: Commit**

```bash
git add backend/api/routes/agents.py backend/api/routes/stakeholders.py backend/api/routes/stakeholder_metrics.py backend/api/routes/meeting_rooms.py backend/api/routes/meeting_prep.py backend/api/routes/help_chat.py backend/api/routes/system_instructions.py backend/api/routes/transcripts.py
git commit -m "refactor: rewrite agent/stakeholder/meeting/help routes to use PocketBase"
```

---

### Task 15: Rewrite route files -- DISCO + PuRDy

**Files:**
- Modify: `backend/api/routes/disco/initiatives.py`
- Modify: `backend/api/routes/disco/chat.py`
- Modify: `backend/api/routes/disco/documents.py`
- Modify: `backend/api/routes/disco/synthesis.py`
- Modify: `backend/api/routes/disco/workflow.py`
- Modify: `backend/api/routes/disco/admin.py`
- Modify: `backend/api/routes/disco/_shared.py`
- Modify: `backend/api/routes/discovery.py`

- [ ] **Step 1: Apply transformations**

Use `from repositories import disco as disco_repo`. DISCO has the most complex queries. Key translations:
- `supabase.table("disco_initiatives").select("*").eq("client_id", cid)` -> `disco_repo.list_initiatives()`
- `supabase.table("disco_outputs").select(...)` -> `disco_repo.list_outputs(initiative_id=..., agent_type=...)`
- `supabase.table("disco_runs").insert(...)` -> `disco_repo.create_run(...)`

- [ ] **Step 2: Commit**

```bash
git add backend/api/routes/disco/ backend/api/routes/discovery.py
git commit -m "refactor: rewrite DISCO/discovery routes to use PocketBase repository"
```

---

### Task 16: Rewrite route files -- Remaining routes

**Files:**
- Modify: `backend/api/routes/admin/analytics.py`
- Modify: `backend/api/routes/admin/cache.py`
- Modify: `backend/api/routes/admin/health.py`
- Modify: `backend/api/routes/admin/help_docs.py`
- Modify: `backend/api/routes/admin/manifesto_compliance.py`
- Modify: `backend/api/routes/admin/stats.py`
- Modify: `backend/api/routes/admin/users_and_clients.py`
- Modify: `backend/api/routes/admin/_shared.py`
- Modify: `backend/api/routes/clients.py`
- Modify: `backend/api/routes/command.py`
- Modify: `backend/api/routes/compass.py`
- Modify: `backend/api/routes/digest.py`
- Modify: `backend/api/routes/entity_corrections.py`
- Modify: `backend/api/routes/entity_registry.py`
- Modify: `backend/api/routes/glean_connectors.py`
- Modify: `backend/api/routes/graph.py`
- Modify: `backend/api/routes/images.py`
- Modify: `backend/api/routes/obsidian_sync.py`
- Modify: `backend/api/routes/pipeline.py`
- Modify: `backend/api/routes/quick_prompts.py`
- Modify: `backend/api/routes/research.py`
- Modify: `backend/api/routes/templates.py`
- Modify: `backend/api/routes/theme.py`
- Modify: `backend/api/routes/users.py`

- [ ] **Step 1: Apply transformations**

Same mechanical pattern. Special cases:
- `clients.py` and `users.py`: These manage entities that no longer exist (users, clients). **Delete the route files** or stub them with 404 responses.
- `admin/users_and_clients.py`: Same -- delete or stub.
- `graph.py`: Neo4j queries stay as-is. Only replace Supabase calls (for reading graph sync state).

- [ ] **Step 2: Update main.py router registrations**

Remove `clients` and `users` router imports/registrations from main.py if those routes are deleted.

- [ ] **Step 3: Commit**

```bash
git add backend/api/routes/
git commit -m "refactor: rewrite all remaining routes to use PocketBase"
```

---

### Task 17: Rewrite service files -- Core services

**Files (38 service files that import get_supabase):**
- Modify: `backend/services/admin_notifications.py`
- Modify: `backend/services/agent_observer.py`
- Modify: `backend/services/career_status_report.py`
- Modify: `backend/services/chat_agent_service.py`
- Modify: `backend/services/conversation_service.py`
- Modify: `backend/services/document_classifier.py`
- Modify: `backend/services/document_digests.py`
- Modify: `backend/services/embeddings.py`
- Modify: `backend/services/engagement_calculator.py`
- Modify: `backend/services/goal_alignment_analyzer.py`
- Modify: `backend/services/granola_scanner.py`
- Modify: `backend/services/hybrid_search.py`
- Modify: `backend/services/manifesto_semantic_scorer.py`
- Modify: `backend/services/obsidian_sync.py`
- Modify: `backend/services/project_chat.py`
- Modify: `backend/services/project_context.py`
- Modify: `backend/services/project_kb_sync.py`
- Modify: `backend/services/research_context.py`
- Modify: `backend/services/useable_output_detector.py`
- Modify: `backend/services/web_researcher.py`
- Modify: `backend/services/project_confidence.py`
- Modify: `backend/services/project_justification.py`

Each follows the same pattern:

```python
# BEFORE
from database import get_supabase
supabase = get_supabase()
result = supabase.table("ai_projects").select("*").eq("id", pid).single().execute()
project = result.data

# AFTER
from repositories import projects as projects_repo
project = projects_repo.get_project(pid)
```

- [ ] **Step 1: Replace Supabase imports and calls in all core service files**

For services that accept `supabase` as a parameter (like `task_kraken.py`), update the function signatures to remove the parameter and use repository calls internally.

- [ ] **Step 2: Commit**

```bash
git add backend/services/
git commit -m "refactor: rewrite core service files to use PocketBase repositories"
```

---

### Task 18: Rewrite service files -- DISCO + Scheduler services

**Files:**
- Modify: `backend/services/disco/agent_service.py`
- Modify: `backend/services/disco/chat_service.py`
- Modify: `backend/services/disco/condenser_service.py`
- Modify: `backend/services/disco/document_service.py`
- Modify: `backend/services/disco/initiative_alignment_analyzer.py`
- Modify: `backend/services/disco/initiative_context.py`
- Modify: `backend/services/disco/initiative_service.py`
- Modify: `backend/services/disco/prd_service.py`
- Modify: `backend/services/disco/project_service.py`
- Modify: `backend/services/disco/sharing_service.py`
- Modify: `backend/services/disco/synthesis_service.py`
- Modify: `backend/services/disco/system_kb_service.py`
- Modify: `backend/services/discovery_scan_scheduler.py`
- Modify: `backend/services/graph_sync_scheduler.py`
- Modify: `backend/services/manifesto_digest_scheduler.py`
- Modify: `backend/services/research_scheduler.py`
- Modify: `backend/services/sync_scheduler.py`

- [ ] **Step 1: Replace Supabase imports and calls**

DISCO services are the most complex. Use `from repositories import disco as disco_repo`. Replace all `supabase.table("disco_*")` calls.

- [ ] **Step 2: Commit**

```bash
git add backend/services/disco/ backend/services/*_scheduler.py
git commit -m "refactor: rewrite DISCO and scheduler services to use PocketBase"
```

---

### Task 19: Update test infrastructure

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_integration.py`
- Modify: other test files as needed

- [ ] **Step 1: Update conftest.py**

Replace Supabase mock fixtures with pb_client mocks:

```python
# BEFORE
@pytest.fixture
def mock_supabase():
    with patch("database.get_supabase") as mock:
        yield mock.return_value

# AFTER
@pytest.fixture
def mock_pb():
    with patch("pb_client._client") as mock:
        yield mock
```

- [ ] **Step 2: Update test files that mock Supabase**

Every test file that mocks `get_supabase` or `DatabaseService` must be updated to mock the appropriate repository instead.

- [ ] **Step 3: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v --tb=short
```

Fix failures iteratively.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "refactor: update test infrastructure for PocketBase"
```

---

### Task 20: Remove database.py and clean up

**Files:**
- Delete: `backend/database.py`
- Modify: `backend/api/utils/supabase_async.py` (delete if unused)
- Remove Supabase dependencies from `requirements.txt` / `pyproject.toml`

- [ ] **Step 1: Verify no remaining Supabase imports**

```bash
cd backend && grep -r "from database import\|from supabase import\|get_supabase\|DatabaseService" --include="*.py" | grep -v "__pycache__" | grep -v ".pyc"
```

Expected: No results (all imports replaced)

- [ ] **Step 2: Delete database.py and supabase_async.py**

```bash
rm backend/database.py
rm backend/api/utils/supabase_async.py
```

- [ ] **Step 3: Remove supabase from dependencies**

Remove `supabase`, `gotrue`, `postgrest`, `realtime` from requirements.txt or pyproject.toml. Keep `httpx` (used by pb_client).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove Supabase dependency, clean up database.py"
```

---

## Plan Self-Review

- **Spec coverage:** All application layer items from the spec are covered: config.py, pb_client.py, vec_client.py, auth.py rewrite, repository layer (14 modules), route rewrites (51 files), service rewrites (52 files), test updates, dependency cleanup.
- **Placeholder scan:** Tasks 10-18 describe the transformation pattern rather than providing complete file rewrites for every file. This is intentional: the transformation is mechanical (documented in the query translation table), and the subagent has the complete repository API and pattern examples. Task 7 provides the complete reference implementation. Task 10 provides a worked example of the route transformation.
- **Type consistency:** All repositories use `pb_client as pb` import. All return `dict | None` or `list[dict]`. All route transformations follow the same import -> replace -> remove pattern.

---

## Next Plan

- **Plan 3:** Vector Sidecar + Data Migration + Frontend (sqlite-vec FastAPI app, migration script, frontend auth changes)
