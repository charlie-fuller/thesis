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


def parse_json_field(value, default=None):
    """Safely parse a value that may be a JSON string or already-parsed object.

    PocketBase returns JSON columns as already-parsed dicts/lists from resp.json().
    The old Supabase layer sometimes returned raw JSON strings. This helper handles
    both cases so callers don't need isinstance guards at every call site.

    Usage: data = pb.parse_json_field(record.get("metadata", {}))
    """
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        import json
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return default
    return default
