# Thesis: Supabase to PocketBase Migration

## Overview

Migrate the full Thesis platform database from Supabase (PostgreSQL) to PocketBase (embedded SQLite), following the pattern established by the Glean Agent Factory app. Includes a Python sidecar for vector search using sqlite-vec.

## Goals

- Remove Supabase dependency (cost, IPv6 issues, broken direct psql)
- Simplify auth to API key (no JWT, no RLS, no user/org/team hierarchy)
- Maintain all existing functionality for the full-stack Thesis app
- Add vector search via sqlite-vec sidecar for document/help similarity
- Deploy PocketBase + sidecar on Fly.io

## Reference Implementation

GAF's PocketBase setup at `~/Vault/GitHub/glean-agent-factory-app/`:
- `backend/pb_client.py` -- thin httpx wrapper with superuser auth
- `backend/repositories/` -- 7 repository modules
- `pb_migrations/1713000000_collections.js` -- PB v0.25 migration syntax
- `Dockerfile.pocketbase` + `fly.pocketbase.toml` -- Fly.io setup
- `backend/config.py` -- pocketbase_url/email/password settings

## Architecture

```
Thesis Backend (thesis-genai-api.fly.dev)
  FastAPI, Python 3.12
  API key auth middleware
         |
    +---------+-----------+
    |                     |
thesis-db.fly.dev     thesis-vec.fly.dev
  PocketBase 0.25       FastAPI + sqlite-vec
  All CRUD               Vector search
  Port 8090              Port 8080
  pb_data volume         vec_data volume
    |                     |
    +--- Fly private network ---+
         (thesis-db.internal)
```

## Scope

### Excluded

| Table(s) | Reason |
|-----------|--------|
| `gaf_*` (10 tables) | Already in GAF's own PocketBase |
| `v_*` views (10) | Recreate as application queries |
| `_migrations` | PocketBase manages its own |
| `oauth_states` | OAuth flow not needed with API key auth |
| `google_drive_tokens`, `google_drive_sync_log` | Google Drive integration (separate concern) |
| `users` | Replaced by API key auth |
| `clients` | Single-tenant, no org hierarchy |

### Simplified

- All `client_id` FK columns: removed (single-tenant)
- All `user_id` / `created_by` / `updated_by`: removed or stored as plain text
- Generated columns (`total_score`, `tier`, `decision_velocity_days`): computed in application code
- PostgreSQL arrays (`text[]`): stored as PB `json` type (JSON arrays)
- Embedding vectors: stored in sqlite-vec sidecar, not in PocketBase

### Migrated (78 tables -> PocketBase collections)

**Core (migration: 1001_core.js)**
- `agents` (10 cols)
- `agent_handoffs` (9 cols)
- `agent_instruction_versions` (9 cols)
- `agent_knowledge_base` (13 cols)
- `agent_topic_mapping` (5 cols)
- `ai_projects` (42 cols, minus generated: 40)
- `stakeholders` (35 cols)
- `strategic_goals` (17 cols)

**Tasks (migration: 1002_tasks.js)**
- `project_tasks` (39 cols)
- `task_candidates` (38 cols)
- `task_comments` (6 cols)
- `task_history` (7 cols)

**Chat (migration: 1003_chat.js)**
- `conversations` (14 cols)
- `messages` (6 cols)
- `message_documents` (4 cols)

**Documents (migration: 1004_documents.js)**
- `documents` (44 cols)
- `document_chunks` (6 cols, embedding col excluded)
- `document_classifications` (15 cols)
- `document_tags` (5 cols)

**Projects (migration: 1005_projects.js)**
- `projects` (8 cols)
- `project_candidates` (28 cols)
- `project_conversations` (8 cols)
- `project_documents` (6 cols)
- `project_folders` (6 cols)
- `project_stakeholder_link` (6 cols)
- `portfolio_projects` (15 cols)
- `roi_opportunities` (20 cols)

**Meetings (migration: 1006_meetings.js)**
- `meeting_rooms` (13 cols)
- `meeting_room_messages` (10 cols)
- `meeting_room_participants` (8 cols)
- `meeting_transcripts` (21 cols)

**Help (migration: 1007_help.js)**
- `help_documents` (9 cols)
- `help_chunks` (8 cols, embedding col excluded)
- `help_conversations` (6 cols)
- `help_messages` (8 cols)

**DISCO (migration: 1008_disco.js)**
- `disco_initiatives` (21 cols)
- `disco_bundles` (23 cols, minus generated: 22)
- `disco_bundle_feedback` (7 cols)
- `disco_checkpoints` (10 cols)
- `disco_conversations` (4 cols)
- `disco_documents` (10 cols)
- `disco_document_chunks` (7 cols, embedding col excluded)
- `disco_initiative_documents` (6 cols)
- `disco_initiative_folders` (6 cols)
- `disco_initiative_members` (5 cols)
- `disco_messages` (6 cols)
- `disco_outcome_metrics` (13 cols)
- `disco_outputs` (24 cols)
- `disco_prds` (13 cols)
- `disco_run_documents` (2 cols)
- `disco_runs` (11 cols)
- `disco_system_kb` (7 cols)
- `disco_system_kb_chunks` (5 cols, embedding col excluded)

**PuRDy (migration: 1009_purdy.js)**
- `purdy_conversations` (4 cols)
- `purdy_documents` (9 cols)
- `purdy_document_chunks` (7 cols, embedding col excluded)
- `purdy_initiative_members` (5 cols)
- `purdy_initiatives` (7 cols)
- `purdy_messages` (6 cols)
- `purdy_outputs` (13 cols)
- `purdy_run_documents` (2 cols)
- `purdy_runs` (10 cols)
- `purdy_system_kb` (7 cols)
- `purdy_system_kb_chunks` (6 cols, embedding col excluded)

**Research (migration: 1010_research.js)**
- `research_schedule` (11 cols)
- `research_sources` (12 cols)
- `research_tasks` (18 cols)

**Stakeholders (migration: 1011_stakeholders.js)**
- `stakeholder_candidates` (30 cols)
- `stakeholder_insights` (14 cols)
- `stakeholder_metrics` (15 cols)

**Obsidian (migration: 1012_obsidian.js)**
- `obsidian_sync_log` (17 cols)
- `obsidian_sync_state` (13 cols)
- `obsidian_vault_configs` (13 cols)
- `graph_sync_log` (11 cols)
- `graph_sync_state` (8 cols)

**Misc (migration: 1013_misc.js)**
- `api_usage_logs` (14 cols)
- `compass_status_reports` (27 cols)
- `department_kpis` (17 cols)
- `engagement_level_history` (10 cols)
- `glean_connectors` (19 cols)
- `glean_connector_gaps` (8 cols)
- `glean_connector_requests` (13 cols)
- `glean_connector_summary` (4 cols)
- `glean_disco_integration_matrix` (8 cols)
- `knowledge_gaps` (15 cols)
- `theme_settings` (41 cols)
- `user_quick_prompts` (9 cols)

## Field Type Mapping

| PostgreSQL | PocketBase | Notes |
|------------|------------|-------|
| `uuid` PK | PB auto `id` (15-char) | Migration script maintains UUID -> PB ID map |
| `varchar(N)` | `text` | |
| `text` (short) | `text` | |
| `text` (large: prompts, markdown, JSON, reports, instructions) | `editor` | PB text type has 5000 char limit |
| `integer` | `number` | Don't set `required: true` if 0 is valid |
| `boolean` | `bool` | |
| `jsonb` | `json` | |
| `text[]` | `json` | Store as JSON arrays |
| `timestamptz` (created_at) | `autodate` | `{ onCreate: true, onUpdate: false }` |
| `timestamptz` (updated_at) | `autodate` | `{ onCreate: true, onUpdate: true }` |
| `timestamptz` (business) | `date` | Due dates, completed_at, etc. |
| `uuid` FK | `relation` | `{ collectionId: parent.id, maxSelect: 1 }` |
| `vector(1536)` | excluded | Stored in sqlite-vec sidecar |
| `GENERATED ALWAYS` | excluded | Computed in application code |

## PocketBase v0.25 Rules

Learned from GAF migration:

1. Use plain objects for fields: `{ name: "x", type: "text" }`, NOT `new Field(...)` or `new RelationField(...)`
2. Use `editor` type for any field over 5000 chars
3. Add `created`/`updated` autodate fields explicitly (not auto-included on base collections)
4. Filters use single quotes: `filter=f"status='active'"`
5. Don't mark number fields as `required` if 0 is a valid value
6. Relations: `{ name: "x", type: "relation", collectionId: parent.id, cascadeDelete: true, maxSelect: 1 }`
7. API rules: set all to `""` (authenticated users) since backend authenticates as superuser
8. After deploying, verify fields via REST API. Patch via `PATCH /api/collections/{name}` if migration JS silently failed.

## Auth

Replace entire Supabase auth system with API key middleware.

**Backend middleware** (`auth.py` replacement):
```python
from fastapi import Request, HTTPException
from config import settings

async def verify_api_key(request: Request):
    if request.url.path in ("/health", "/docs", "/openapi.json"):
        return
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {settings.api_key}":
        raise HTTPException(status_code=401, detail="Invalid API key")
```

**Frontend**: Store API key in environment variable `NEXT_PUBLIC_API_KEY`. Send as `Authorization: Bearer <key>` header on all requests.

**Remove**: Supabase JWK validation, ES256 JWT parsing, `get_current_user` dependency, RLS policies, user session management, `AuthContext` in frontend.

## Application Layer

### pb_client.py

Copy from GAF, update config prefix from `GAF_` to `THESIS_`. Same interface: `list_records`, `get_record`, `create_record`, `update_record`, `delete_record`, `get_first`, `get_all`, `count`, `escape_filter`.

### vec_client.py

Thin httpx wrapper for the vector search sidecar:
```python
def store_embedding(collection: str, record_id: str, text: str) -> dict
def search(collection: str, query: str, limit: int = 5) -> list[dict]
def delete_embedding(collection: str, record_id: str) -> None
```

### config.py

```python
class Settings(BaseSettings):
    pocketbase_url: str = "http://127.0.0.1:8090"
    pocketbase_email: str = ""
    pocketbase_password: str = ""
    vec_url: str = "http://127.0.0.1:8080"
    api_key: str = ""
    voyage_api_key: str = ""
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    default_model: str = "claude-sonnet-4-6"
    cors_origins: str = ""

    model_config = {"env_prefix": "THESIS_"}
```

### Repository Layer

One module per domain (matching migration file grouping):

| Repository | Collections | Key Operations |
|-----------|-------------|----------------|
| `projects.py` | ai_projects, project_candidates, project_documents, project_folders, project_conversations, project_stakeholder_link, portfolio_projects, roi_opportunities | CRUD, filter by status/tier/department, computed total_score/tier |
| `tasks.py` | project_tasks, task_candidates, task_comments, task_history | CRUD, Kanban moves, filter by status/priority/project |
| `agents.py` | agents, agent_handoffs, agent_instruction_versions, agent_knowledge_base, agent_topic_mapping | CRUD, list active agents |
| `stakeholders.py` | stakeholders, stakeholder_candidates, stakeholder_insights, stakeholder_metrics | CRUD, search, engagement tracking |
| `documents.py` | documents, document_chunks, document_classifications, document_tags | CRUD, classification, search (delegates to vec_client) |
| `conversations.py` | conversations, messages, message_documents | CRUD, message history |
| `meetings.py` | meeting_rooms, meeting_room_messages, meeting_room_participants, meeting_transcripts | CRUD, autonomous discussion |
| `help.py` | help_documents, help_chunks, help_conversations, help_messages | CRUD, search (delegates to vec_client) |
| `disco.py` | all disco_* collections | Initiatives, runs, outputs, PRDs, bundles, system KB |
| `purdy.py` | all purdy_* collections | Initiatives, runs, outputs, system KB |
| `research.py` | research_tasks, research_sources, research_schedule | CRUD, scheduling |
| `obsidian.py` | obsidian_sync_log, obsidian_sync_state, obsidian_vault_configs, graph_sync_log, graph_sync_state | Sync tracking |
| `search.py` | wraps vec_client | Unified search interface for all embedding collections |
| `misc.py` | api_usage_logs, compass_status_reports, department_kpis, engagement_level_history, glean_connectors, knowledge_gaps, theme_settings, user_quick_prompts | Various CRUD |

### Route Changes

All 51 route files import `from database import get_supabase` and use the Supabase Python client query builder. Each must be rewritten to use repository calls.

Translation pattern:
```python
# Before
supabase = get_supabase()
result = supabase.table("ai_projects").select("*").eq("status", "active").order("updated_at", desc=True).execute()
projects = result.data

# After
from repositories import projects as projects_repo
projects = projects_repo.list_projects(status="active")
```

Key query builder translations:
| Supabase | PocketBase (via pb_client) |
|----------|--------------------------|
| `.select("*")` | default (all fields returned) |
| `.select("id, title")` | `fields="id,title"` |
| `.eq("status", "active")` | `filter="status='active'"` |
| `.neq("status", "done")` | `filter="status!='done'"` |
| `.in_("id", ids)` | `filter="id='a' \|\| id='b'"` or loop |
| `.ilike("title", "%search%")` | `filter="title~'search'"` |
| `.order("updated_at", desc=True)` | `sort="-updated"` |
| `.limit(10)` | `per_page=10` |
| `.single()` | `get_first()` or `get_record()` |
| `.rpc("match_chunks", params)` | `vec_client.search()` |

### Service Changes

All 52 service files that import `get_supabase` must be updated to use repositories. Same translation pattern as routes.

### Generated Column Computation

Move to repository layer:

```python
# projects.py
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
```

## Vector Search Sidecar

### Tech Stack
- FastAPI + uvicorn
- sqlite-vec (Python bindings)
- voyageai (Python SDK, existing embedding provider)
- httpx (for PocketBase communication)

### Database Schema

Single sqlite-vec database (`/app/data/vectors.db`):
```sql
-- Metadata table (standard SQLite)
CREATE TABLE vec_metadata (
    id TEXT PRIMARY KEY,          -- PocketBase record ID
    collection TEXT NOT NULL,     -- e.g. "document_chunks", "help_chunks"
    title TEXT,                   -- for display in search results
    content_preview TEXT,         -- first 200 chars
    created_at TEXT DEFAULT (datetime('now'))
);

-- Vector table (sqlite-vec virtual table)
CREATE VIRTUAL TABLE vec_embeddings USING vec0(
    id TEXT PRIMARY KEY,
    embedding float[1536]        -- Voyage AI dimension
);
```

### Endpoints

```
GET  /health
POST /embeddings/store    { collection, record_id, text, title? }
POST /search              { collection, query, limit=5 }
DELETE /embeddings/{id}
GET  /stats               { total_embeddings, by_collection: {...} }
```

### Embedding Collections

| Collection | Source Table | Content Field |
|-----------|-------------|---------------|
| `document_chunks` | document_chunks | chunk text |
| `help_chunks` | help_chunks | chunk text |
| `disco_document_chunks` | disco_document_chunks | chunk text |
| `disco_system_kb_chunks` | disco_system_kb_chunks | chunk text |
| `purdy_document_chunks` | purdy_document_chunks | chunk text |
| `purdy_system_kb_chunks` | purdy_system_kb_chunks | chunk text |

## Deployment

### thesis-db (PocketBase)

```dockerfile
# Dockerfile.pocketbase
FROM alpine:latest
ARG PB_VERSION=0.25.9
RUN apk add --no-cache unzip ca-certificates
ADD https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_linux_amd64.zip /tmp/pb.zip
RUN unzip /tmp/pb.zip -d /pb/ && rm /tmp/pb.zip
COPY pb_migrations /pb/pb_migrations
EXPOSE 8090
CMD ["/pb/pocketbase", "serve", "--http=0.0.0.0:8090", "--dir=/pb/pb_data", "--migrationsDir=/pb/pb_migrations"]
```

```toml
# fly.pocketbase.toml
app = "thesis-db"
primary_region = "dfw"

[build]
  dockerfile = "Dockerfile.pocketbase"

[mounts]
  source = "pb_data"
  destination = "/pb/pb_data"

[http_service]
  internal_port = 8090
  force_https = true
  auto_stop_machines = "off"
  auto_start_machines = true
  min_machines_running = 1

  [http_service.concurrency]
    type = "requests"
    soft_limit = 25
    hard_limit = 50

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/api/health"
  timeout = "5s"

[[vm]]
  size = "shared-cpu-1x"
  memory = "256mb"
```

### thesis-vec (Vector Sidecar)

```dockerfile
# Dockerfile.vec
FROM python:3.12-slim
WORKDIR /app
COPY vec_sidecar/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY vec_sidecar/ .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```toml
# fly.vec.toml
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

Secrets for thesis-vec:
```bash
flyctl secrets set VOYAGE_API_KEY=<key> -a thesis-vec
flyctl secrets set PB_URL=http://thesis-db.internal:8090 -a thesis-vec
flyctl secrets set PB_EMAIL=<superuser_email> -a thesis-vec
flyctl secrets set PB_PASSWORD=<superuser_password> -a thesis-vec
```

### thesis-genai-api (Backend Update)

Update existing Fly.io secrets:
```bash
# Remove Supabase secrets
flyctl secrets unset SUPABASE_URL SUPABASE_KEY SUPABASE_SERVICE_ROLE_KEY SUPABASE_JWT_SECRET -a thesis-genai-api

# Add PocketBase + vec secrets
flyctl secrets set THESIS_POCKETBASE_URL=http://thesis-db.internal:8090 -a thesis-genai-api
flyctl secrets set THESIS_POCKETBASE_EMAIL=<superuser_email> -a thesis-genai-api
flyctl secrets set THESIS_POCKETBASE_PASSWORD=<superuser_password> -a thesis-genai-api
flyctl secrets set THESIS_VEC_URL=http://thesis-vec.internal:8080 -a thesis-genai-api
flyctl secrets set THESIS_API_KEY=<generated_api_key> -a thesis-genai-api
```

## Data Migration

### Script: `scripts/migrate_supabase_to_pb.py`

Three-pass approach:

**Pass 1 -- Leaf collections (no foreign keys):**
Pull from Supabase Management API, push to PocketBase REST API. Build ID mapping (UUID -> PB 15-char ID).

Order: agents, ai_projects, stakeholders, strategic_goals, documents, help_documents, meeting_rooms, disco_initiatives, purdy_initiatives, research_tasks, obsidian_vault_configs, etc.

**Pass 2 -- Collections with relations:**
Use ID mapping to resolve foreign keys. Push to PocketBase.

Order: project_tasks, task_candidates, messages, document_chunks, meeting_room_messages, disco_outputs, disco_runs, help_chunks, purdy_runs, etc.

**Pass 3 -- Embeddings:**
For each `*_chunks` table that has an embedding column, extract the vector and POST to thesis-vec `/embeddings/store`.

### Migration rules:
- Skip `client_id` columns
- Skip generated columns (`total_score`, `tier`, `decision_velocity_days`)
- Convert `text[]` arrays to JSON arrays
- Convert `timestamptz` to ISO 8601 strings
- Map UUID foreign keys to PocketBase IDs via mapping file
- Store embedding vectors in sidecar, not PocketBase
- Write `id_map.json` for reference: `{ "table": { "old_uuid": "new_pb_id" } }`

### Supabase query method:
```bash
TOKEN=$(security find-generic-password -s "Supabase CLI" -w | sed 's/go-keyring-base64://' | base64 -d)
curl -s -X POST "https://api.supabase.com/v1/projects/imdavfgreeddxluslsdl/database/query" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"SELECT * FROM <table> ORDER BY created_at"}'
```

## Frontend Changes

- Remove `@supabase/supabase-js` dependency
- Remove `AuthContext` / Supabase auth provider
- Replace with simple API key auth (key stored in env var, sent as Bearer token)
- All data fetching already goes through the backend API -- no direct Supabase client calls should remain after backend migration
- If any components use Supabase realtime subscriptions, replace with polling or SSE (existing pattern)

## Testing

- Existing test suite (370+ unit, 35+ integration) must pass after migration
- Mock `pb_client` in unit tests (same as GAF mocks Supabase)
- Integration tests hit a local PocketBase instance
- E2E browser tests verify frontend works with new auth
