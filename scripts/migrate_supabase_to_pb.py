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

    def get_collection_field_types(self, collection: str) -> dict[str, str]:
        """Get field name -> type mapping for a collection."""
        resp = self.client.get(f"/api/collections/{collection}")
        resp.raise_for_status()
        return {f["name"]: f["type"] for f in resp.json().get("fields", [])}


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


def remap_id(value: str, id_map: dict) -> str | None:
    """Try to remap a Supabase UUID to a PocketBase ID using the id_map."""
    if not value or not isinstance(value, str):
        return value
    # Search all tables in id_map for this UUID
    for table_ids in id_map.values():
        if value in table_ids:
            return table_ids[value]
    return value  # Return original if not found (may cause relation error)


def clean_row(row: dict, pb_fields: list[str], field_types: dict | None = None,
              id_map: dict | None = None) -> dict:
    """Clean a Supabase row for PocketBase insertion."""
    cleaned = {}
    relation_fields = set()
    if field_types:
        relation_fields = {k for k, v in field_types.items() if v == "relation"}

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

        # Remap relation field values using id_map
        if id_map and key in relation_fields and value:
            if isinstance(value, list):
                value = [remap_id(v, id_map) for v in value]
            else:
                value = remap_id(value, id_map)

        cleaned[key] = value

    return cleaned


def migrate_table(table: str, pb: PBClient, id_map: dict, dry_run: bool = False) -> int:
    """Migrate a single table from Supabase to PocketBase."""
    logger.info("Migrating table: %s", table)

    # Get PB collection fields and types
    try:
        pb_fields = pb.get_collection_fields(table)
        field_types = pb.get_collection_field_types(table)
    except Exception as e:
        logger.error("Collection %s not found in PocketBase: %s", table, e)
        return 0

    # Build column list excluding problematic columns (vectors, generated)
    try:
        col_rows = query_supabase(
            f"SELECT column_name FROM information_schema.columns "
            f"WHERE table_name = '{table}' AND table_schema = 'public' "
            f"AND data_type NOT IN ('USER-DEFINED') "  # skip vector columns
            f"ORDER BY ordinal_position"
        )
        columns = [r["column_name"] for r in col_rows if r["column_name"] not in SKIP_COLUMNS]
        col_list = ", ".join(f'"{c}"' for c in columns)
    except Exception:
        col_list = "*"

    # Fetch all rows from Supabase
    try:
        rows = query_supabase(f"SELECT {col_list} FROM {table} ORDER BY created_at ASC NULLS FIRST")
    except Exception:
        # Fallback: table may not have created_at
        rows = query_supabase(f"SELECT {col_list} FROM {table}")
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

        cleaned = clean_row(row, pb_fields, field_types=field_types, id_map=id_map)

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

    # Fetch rows that had embeddings (re-embed via Voyage AI in vec sidecar)
    # Don't SELECT the embedding column -- Management API can't serialize vectors
    rows = query_supabase(
        f"SELECT id, content FROM {table} WHERE content IS NOT NULL AND content != ''"
    )
    logger.info("  Found %d rows with content to embed", len(rows))

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
