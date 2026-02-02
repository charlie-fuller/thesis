from logger_config import get_logger

logger = get_logger(__name__)

"""
Notion Sync Service

Handles syncing documents from Notion to Thesis using LlamaIndex.
Manages OAuth tokens, document fetching, and integration with existing document processor.

Flow:
1. Get OAuth token from database
2. Initialize LlamaIndex NotionPageReader
3. Fetch pages from Notion workspace
4. Create/update document records in database
5. Save document content to Supabase storage
6. Trigger existing document processor for embedding generation
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from llama_index.readers.notion import NotionPageReader

from database import get_supabase
from document_processor import process_document
from services.oauth_crypto import OAuthCryptoError, decrypt_token

load_dotenv()

# Get centralized Supabase client
supabase = get_supabase()

# Supabase URL for storage paths
SUPABASE_URL = os.getenv("SUPABASE_URL", "")


class NotionSyncError(Exception):
    """Raised when Notion sync operations fail"""

    pass


# ============================================================================
# Token Management
# ============================================================================


def get_user_tokens(user_id: str) -> Optional[Dict]:
    """Get OAuth tokens for a user from database.

    Args:
        user_id: UUID of the user

    Returns:
        Dict with token info or None if not connected

    Raises:
        NotionSyncError: If token retrieval fails
    """
    try:
        logger.info(f"   🔍 Querying notion_tokens for user_id={user_id}, is_active=True")
        result = (
            supabase.table("notion_tokens")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )

        logger.info(f"   🔍 Query returned {len(result.data)} token record(s)")

        if not result.data:
            logger.warning(f"   ⚠️  No active token found for user {user_id}")
            return None

        logger.info(
            f"   ✓ Found active token for workspace: {result.data[0].get('workspace_name')}"
        )
        return result.data[0]

    except Exception as e:
        logger.error(f"   ❌ Error querying tokens: {e}")
        raise NotionSyncError(f"Failed to get user tokens: {e}")


def get_notion_token(user_id: str) -> str:
    """Get valid Notion integration token.

    Args:
        user_id: UUID of the user

    Returns:
        Decrypted Notion token

    Raises:
        NotionSyncError: If no tokens found or decryption fails
    """
    token_record = get_user_tokens(user_id)

    if not token_record:
        raise NotionSyncError(
            "No Notion connection found. Please connect your Notion workspace first."
        )

    try:
        # Decrypt token
        access_token = decrypt_token(token_record["access_token_encrypted"])
        return access_token

    except OAuthCryptoError as e:
        raise NotionSyncError(f"Token decryption failed: {e}")
    except Exception as e:
        raise NotionSyncError(f"Failed to get token: {e}")


# ============================================================================
# Document Management
# ============================================================================


def get_document_by_notion_id(user_id: str, notion_page_id: str) -> Optional[Dict]:
    """Check if a document with given Notion page ID already exists.

    Args:
        user_id: UUID of the user
        notion_page_id: Notion page ID

    Returns:
        Document record or None if not found
    """
    try:
        result = (
            supabase.table("documents")
            .select("*")
            .eq("user_id", user_id)
            .eq("notion_page_id", notion_page_id)
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception as e:
        logger.warning(f"   ⚠️  Error checking for existing document: {e}")
        return None


def create_notion_document(
    user_id: str,
    client_id: str,
    filename: str,
    file_content: bytes,
    notion_page_id: str,
    external_url: str,
    notion_database_id: Optional[str] = None,
) -> Dict:
    """Create a new document record and upload content to storage.

    Args:
        user_id: UUID of the user
        client_id: UUID of the client/organization
        filename: Name of the page/document
        file_content: Document content as bytes
        notion_page_id: Notion page ID
        external_url: URL to view page in Notion
        notion_database_id: Notion database ID if page is from database

    Returns:
        Created document record

    Raises:
        NotionSyncError: If document creation fails
    """
    try:
        # Generate storage path with UUID to prevent collisions
        unique_id = str(uuid.uuid4())
        # Sanitize filename
        safe_filename = filename.replace("/", "-").replace("\\", "-")
        storage_path = f"{user_id}/{unique_id}_{safe_filename}.txt"

        # Upload to Supabase storage
        logger.info(f"      📤 Uploading to storage: {storage_path}")
        supabase.storage.from_("documents").upload(
            path=storage_path, file=file_content, file_options={"content-type": "text/plain"}
        )

        # Get storage URL
        storage_url = f"{SUPABASE_URL}/storage/v1/object/public/documents/{storage_path}"

        # Create document record
        now = datetime.now(timezone.utc).isoformat()
        document_data = {
            "user_id": user_id,
            "client_id": client_id,
            "uploaded_by": user_id,  # Required for documents list filtering
            "filename": filename,
            "storage_url": storage_url,
            "source_platform": "notion",
            "external_id": notion_page_id,
            "external_url": external_url,
            "notion_page_id": notion_page_id,
            "notion_database_id": notion_database_id,
            "last_synced_at": now,
            "processed": False,
            "uploaded_at": now,
        }

        result = supabase.table("documents").insert(document_data).execute()
        document = result.data[0]

        logger.info(f"      ✓ Created document record: {document['id']}")
        return document

    except Exception as e:
        raise NotionSyncError(f"Failed to create document: {e}")


def update_notion_document(
    document_id: str, file_content: bytes, storage_url: str, filename: Optional[str] = None
) -> Dict:
    """Update an existing document's content and optionally its filename.

    Args:
        document_id: UUID of the document
        file_content: New file content as bytes
        storage_url: Current storage URL
        filename: Optional updated filename/title

    Returns:
        Updated document record

    Raises:
        NotionSyncError: If update fails
    """
    try:
        # Extract storage path from URL
        storage_path = storage_url.split("/documents/")[-1]

        # Update file in storage
        logger.info(f"      📤 Updating storage: {storage_path}")
        supabase.storage.from_("documents").update(
            path=storage_path, file=file_content, file_options={"upsert": "true"}
        )

        # Delete old embeddings
        logger.info("      🗑️  Deleting old embeddings...")
        supabase.table("document_chunks").delete().eq("document_id", document_id).execute()

        # Update document record
        now = datetime.now(timezone.utc).isoformat()
        update_data = {
            "last_synced_at": now,
            "processed": False,  # Will be re-processed
            "processed_at": None,
        }

        # Update filename if provided (Notion page title may have changed)
        if filename:
            update_data["filename"] = filename
            logger.info(f"      📝 Updating title to: {filename}")

        result = supabase.table("documents").update(update_data).eq("id", document_id).execute()

        logger.info("      ✓ Updated document record")
        return result.data[0]

    except Exception as e:
        raise NotionSyncError(f"Failed to update document: {e}")


# ============================================================================
# Page Discovery
# ============================================================================


def get_accessible_pages(user_id: str) -> List[Dict]:
    """Fetch all pages accessible to the user's Notion integration.

    Args:
        user_id: UUID of the user

    Returns:
        List of page objects with id, title, url, icon, and last_edited_time

    Raises:
        NotionSyncError: If fetching pages fails
    """
    try:
        logger.info(f"\n🔍 Fetching accessible Notion pages for user {user_id}")

        # Get valid token
        integration_token = get_notion_token(user_id)

        # Use Notion Search API to find accessible pages
        headers = {
            "Authorization": f"Bearer {integration_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        all_pages = []
        has_more = True
        start_cursor = None

        while has_more:
            # Build request body
            body = {
                "filter": {"value": "page", "property": "object"},
                "sort": {"direction": "descending", "timestamp": "last_edited_time"},
            }

            if start_cursor:
                body["start_cursor"] = start_cursor

            # Make API request
            response = requests.post(
                "https://api.notion.com/v1/search", headers=headers, json=body, timeout=30
            )

            if response.status_code != 200:
                raise NotionSyncError(f"Notion API error: {response.status_code} - {response.text}")

            data = response.json()
            results = data.get("results", [])

            # Extract page information
            for page in results:
                try:
                    # Extract title from different possible locations
                    title = "Untitled"
                    if "properties" in page:
                        # Check for title property
                        for prop_name, prop_value in page["properties"].items():
                            if prop_value.get("type") == "title":
                                title_array = prop_value.get("title", [])
                                if title_array:
                                    title = title_array[0].get("plain_text", "Untitled")
                                break

                    # Get icon
                    icon = None
                    if "icon" in page and page["icon"]:
                        if page["icon"].get("type") == "emoji":
                            icon = page["icon"].get("emoji")
                        elif page["icon"].get("type") == "external":
                            icon = page["icon"].get("external", {}).get("url")
                        elif page["icon"].get("type") == "file":
                            icon = page["icon"].get("file", {}).get("url")

                    page_info = {
                        "id": page["id"],
                        "title": title,
                        "url": page.get("url", f"https://notion.so/{page['id'].replace('-', '')}"),
                        "icon": icon,
                        "last_edited_time": page.get("last_edited_time"),
                        "created_time": page.get("created_time"),
                    }

                    all_pages.append(page_info)

                except Exception as e:
                    logger.warning(f"   ⚠️  Error parsing page: {e}")
                    continue

            # Check for pagination
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        logger.info(f"   ✓ Found {len(all_pages)} accessible pages")
        return all_pages

    except NotionSyncError:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch accessible pages: {e}")
        raise NotionSyncError(f"Failed to fetch accessible pages: {e}")


# ============================================================================
# Sync Logic
# ============================================================================


def _fetch_page_title(page_id: str, integration_token: str) -> str:
    """Fetch the actual page title from Notion's API.

    Tries multiple methods to extract the title:
    1. From page properties (for database pages)
    2. From the first child block (for regular pages)
    3. From parent property if it's a child page

    Args:
        page_id: Notion page ID
        integration_token: Notion integration token

    Returns:
        Page title or "Untitled" if not found
    """
    try:
        headers = {
            "Authorization": f"Bearer {integration_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        # First, try to get the page metadata
        response = requests.get(
            f"https://api.notion.com/v1/pages/{page_id}", headers=headers, timeout=30
        )

        if response.status_code != 200:
            logger.warning(f"   ⚠️  Failed to fetch page {page_id}: {response.status_code}")
            return "Untitled"

        page_data = response.json()
        logger.debug(f"   📄 Page data keys: {page_data.keys()}")

        # Method 1: Try to extract title from properties (works for database pages)
        if "properties" in page_data:
            for prop_name, prop_value in page_data["properties"].items():
                if prop_value.get("type") == "title":
                    title_array = prop_value.get("title", [])
                    if title_array and len(title_array) > 0:
                        title = title_array[0].get("plain_text", "").strip()
                        if title:
                            logger.info(f"   📝 Found title in properties: {title}")
                            return title

        # Method 2: Try to get the first block (title block) for regular pages
        logger.info("   🔍 Title not in properties, checking child blocks...")
        blocks_response = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            params={"page_size": 1},  # Only need the first block
            timeout=30,
        )

        if blocks_response.status_code == 200:
            blocks_data = blocks_response.json()
            results = blocks_data.get("results", [])

            if results:
                first_block = results[0]
                block_type = first_block.get("type")

                # Check various block types that could contain the title
                if block_type in ["heading_1", "heading_2", "heading_3"]:
                    rich_text = first_block.get(block_type, {}).get("rich_text", [])
                    if rich_text:
                        title = "".join([t.get("plain_text", "") for t in rich_text]).strip()
                        if title:
                            logger.info(f"   📝 Found title in {block_type}: {title}")
                            return title
                elif block_type == "paragraph":
                    rich_text = first_block.get("paragraph", {}).get("rich_text", [])
                    if rich_text:
                        title = "".join([t.get("plain_text", "") for t in rich_text]).strip()
                        if title:
                            logger.info(f"   📝 Found title in paragraph: {title}")
                            return title

        # Method 3: Check if there's a parent database and get the title from there
        if "parent" in page_data and page_data["parent"].get("type") == "database_id":
            logger.info("   🔍 Page is in a database, checking parent...")
            # Already tried properties above, so this is a fallback

        logger.warning(f"   ⚠️  Could not extract title for page {page_id}, using 'Untitled'")
        return "Untitled"

    except Exception as e:
        logger.warning(f"   ⚠️  Error fetching page title: {e}")
        return "Untitled"


def create_placeholder_documents(user_id: str, page_ids: List[str]) -> List[Dict]:
    """Create placeholder document records immediately for selected pages.
    This allows documents to appear in the UI with "Processing" status
    before the full content is downloaded.

    Args:
        user_id: UUID of the user
        page_ids: List of Notion page IDs

    Returns:
        List of created document records

    Raises:
        NotionSyncError: If creation fails
    """
    try:
        logger.info(f"\n📝 Creating placeholder documents for user {user_id}")
        logger.info(f"   Page IDs: {len(page_ids)}")

        # Get valid token
        integration_token = get_notion_token(user_id)

        # Get user's client_id
        user_result = supabase.table("users").select("client_id").eq("id", user_id).execute()
        if not user_result.data:
            raise NotionSyncError(f"User {user_id} not found")

        client_id = user_result.data[0].get("client_id")

        # Notion API headers
        headers = {
            "Authorization": f"Bearer {integration_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        created_docs = []
        now = datetime.now(timezone.utc).isoformat()

        for page_id in page_ids:
            try:
                # Fetch page metadata from Notion API
                response = requests.get(
                    f"https://api.notion.com/v1/pages/{page_id}", headers=headers, timeout=30
                )

                if response.status_code != 200:
                    logger.error(f"   ❌ Failed to fetch page {page_id}: {response.status_code}")
                    continue

                page_data = response.json()

                # Extract title
                title = "Untitled"
                if "properties" in page_data:
                    for prop_name, prop_value in page_data["properties"].items():
                        if prop_value.get("type") == "title":
                            title_array = prop_value.get("title", [])
                            if title_array:
                                title = title_array[0].get("plain_text", "Untitled")
                            break

                # Get page URL
                page_url = page_data.get("url", f"https://notion.so/{page_id.replace('-', '')}")

                # Create placeholder document record
                document_data = {
                    "user_id": user_id,
                    "client_id": client_id,
                    "uploaded_by": user_id,
                    "filename": f"{title}.md",
                    "storage_url": f"placeholder/{page_id}",  # Temporary, will be updated
                    "source_platform": "notion",
                    "external_id": page_id,
                    "external_url": page_url,
                    "notion_page_id": page_id,
                    "last_synced_at": now,
                    "processed": False,  # Will be set to True after processing
                    "uploaded_at": now,
                }

                result = supabase.table("documents").insert(document_data).execute()
                document = result.data[0]

                created_docs.append(document)
                logger.info(f"   ✓ Created placeholder for: {title} (ID: {document['id']})")

            except Exception as e:
                logger.error(f"   ❌ Failed to create placeholder for {page_id}: {e}")
                # Continue with other pages
                continue

        logger.info(f"   ✅ Created {len(created_docs)} placeholder documents")
        return created_docs

    except Exception as e:
        logger.error(f"❌ Failed to create placeholder documents: {e}")
        raise NotionSyncError(f"Failed to create placeholder documents: {e}")


def sync_pages(
    user_id: str,
    page_ids: Optional[List[str]] = None,
    placeholder_doc_ids: Optional[List[str]] = None,
) -> Dict:
    """Sync documents from Notion workspace.

    Args:
        user_id: UUID of the user
        page_ids: Optional list of specific page IDs to sync (None = all accessible pages)

    Returns:
        Dict with sync results

    Raises:
        NotionSyncError: If sync fails
    """
    # Create sync log entry
    sync_log_id = _create_sync_log(user_id, page_ids)

    try:
        logger.info(f"\n📘 Starting Notion sync for user {user_id}")
        if page_ids:
            logger.info(f"   Syncing {len(page_ids)} specific pages")
        else:
            logger.info("   Syncing all accessible pages")

        # Get valid token
        integration_token = get_notion_token(user_id)

        # Get user's client_id
        user_result = supabase.table("users").select("client_id").eq("id", user_id).execute()
        if not user_result.data:
            raise NotionSyncError(f"User {user_id} not found")

        client_id = user_result.data[0].get("client_id")

        # Initialize LlamaIndex Notion reader
        logger.info("   🔌 Connecting to Notion...")
        reader = NotionPageReader(integration_token=integration_token)

        # Load documents
        logger.info("   📥 Fetching pages...")
        if page_ids:
            # Fetch specific pages
            documents = []
            for page_id in page_ids:
                try:
                    page_docs = reader.load_data(page_ids=[page_id])
                    documents.extend(page_docs)
                except Exception as e:
                    logger.warning(f"   ⚠️  Failed to fetch page {page_id}: {e}")
        else:
            # Fetch all accessible pages
            # Note: Notion requires explicit page IDs, we can't fetch "all" pages
            # For MVP, we'll require users to specify page_ids
            raise NotionSyncError(
                "Please specify page IDs to sync. Notion requires explicit page access."
            )

        logger.info(f"   ✓ Found {len(documents)} pages")

        # Optimize: Fetch all existing documents once
        logger.info("   📋 Fetching existing documents...")
        existing_docs_result = (
            supabase.table("documents")
            .select("*")
            .eq("user_id", user_id)
            .not_.is_("notion_page_id", "null")
            .execute()
        )

        # Create lookup map by notion_page_id
        existing_docs_map = {
            doc["notion_page_id"]: doc
            for doc in existing_docs_result.data
            if doc.get("notion_page_id")
        }
        logger.info(f"   ✓ Found {len(existing_docs_map)} existing Notion documents")

        # Track sync statistics
        stats = {"documents_added": 0, "documents_updated": 0, "documents_skipped": 0, "errors": []}

        # Process each document
        for idx, doc in enumerate(documents, 1):
            try:
                # Extract metadata
                page_id = doc.metadata.get("page_id") or doc.id_

                # Fetch actual title from Notion API (LlamaIndex metadata might not include it)
                page_title = _fetch_page_title(page_id, integration_token)

                logger.info(f"\n   📄 [{idx}/{len(documents)}] Processing: {page_title}")

                # Get page URL from metadata or construct it
                page_url = doc.metadata.get("url", f"https://notion.so/{page_id.replace('-', '')}")

                # Get document text content
                file_content = doc.text.encode("utf-8")

                # Check if document already exists
                existing_doc = existing_docs_map.get(page_id)

                # Check if it's a placeholder document (created immediately for UI)
                is_placeholder = existing_doc and existing_doc.get("storage_url", "").startswith(
                    "placeholder/"
                )

                if existing_doc and not is_placeholder:
                    # Update existing real document (re-sync)
                    logger.info("      📝 Document exists, updating...")
                    updated_doc = update_notion_document(
                        document_id=existing_doc["id"],
                        file_content=file_content,
                        storage_url=existing_doc["storage_url"],
                        filename=page_title,  # Update title in case it changed in Notion
                    )

                    # Re-process document for embeddings
                    logger.info("      🔄 Re-processing for embeddings...")
                    process_document(existing_doc["id"])

                    stats["documents_updated"] += 1

                elif is_placeholder:
                    # Populate placeholder document with actual content
                    logger.info("      📋 Populating placeholder document...")

                    # Upload content to storage
                    storage_path = f"{user_id}/{page_id}_{page_title}.md"
                    logger.info(f"      📤 Uploading to storage: {storage_path}")

                    supabase.storage.from_("documents").upload(
                        path=storage_path, file=file_content, file_options={"upsert": "true"}
                    )

                    storage_url = (
                        f"{SUPABASE_URL}/storage/v1/object/public/documents/{storage_path}"
                    )

                    # Update placeholder with real content
                    now = datetime.now(timezone.utc).isoformat()
                    update_data = {
                        "storage_url": storage_url,
                        "filename": f"{page_title}.md",  # Update with actual title
                        "last_synced_at": now,
                        "processed": False,  # Will be set to True after embedding
                    }

                    supabase.table("documents").update(update_data).eq(
                        "id", existing_doc["id"]
                    ).execute()

                    logger.info("      ✓ Populated placeholder document")

                    # Process document for embeddings
                    logger.info("      🔄 Processing for embeddings...")
                    process_document(existing_doc["id"])

                    stats["documents_added"] += 1

                else:
                    # Create completely new document
                    logger.info("      ➕ New document, creating...")
                    new_doc = create_notion_document(
                        user_id=user_id,
                        client_id=client_id,
                        filename=page_title,
                        file_content=file_content,
                        notion_page_id=page_id,
                        external_url=page_url,
                        notion_database_id=doc.metadata.get("database_id"),
                    )

                    # Process document for embeddings
                    logger.info("      🔄 Processing for embeddings...")
                    process_document(new_doc["id"])

                    stats["documents_added"] += 1

                logger.info("      ✅ Done")

            except Exception as e:
                logger.error(f"      ❌ Error: {e}")
                stats["errors"].append(
                    {"page_title": doc.metadata.get("title", "Unknown"), "error": str(e)}
                )
                stats["documents_skipped"] += 1

        # Update sync log with results
        _complete_sync_log(sync_log_id, "completed", stats)

        logger.info("\n✅ Sync complete!")
        logger.info(f"   Added: {stats['documents_added']}")
        logger.info(f"   Updated: {stats['documents_updated']}")
        logger.info(f"   Skipped: {stats['documents_skipped']}")

        return {"status": "success", "sync_log_id": sync_log_id, **stats}

    except Exception as e:
        # Mark sync as failed
        error_message = str(e)
        _complete_sync_log(sync_log_id, "failed", error_message=error_message)

        logger.error(f"\n❌ Sync failed: {e}")
        raise NotionSyncError(f"Sync failed: {e}")


def _create_sync_log(user_id: str, page_ids: Optional[List[str]]) -> str:
    """Create a sync log entry and return its ID"""
    page_count = len(page_ids) if page_ids else 0
    page_name = f"{page_count} pages" if page_ids else "All accessible pages"

    log_data = {
        "user_id": user_id,
        "page_id": page_ids[0] if page_ids and len(page_ids) == 1 else None,
        "page_name": page_name,
        "sync_type": "full",
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    result = supabase.table("notion_sync_log").insert(log_data).execute()
    return result.data[0]["id"]


def _complete_sync_log(
    sync_log_id: str, status: str, stats: Optional[Dict] = None, error_message: Optional[str] = None
):
    """Update sync log entry with completion status"""
    now = datetime.now(timezone.utc).isoformat()

    update_data = {"status": status, "completed_at": now}

    if stats:
        update_data.update(
            {
                "documents_added": stats.get("documents_added", 0),
                "documents_updated": stats.get("documents_updated", 0),
                "documents_skipped": stats.get("documents_skipped", 0),
            }
        )

    if error_message:
        update_data["error_message"] = error_message

    supabase.table("notion_sync_log").update(update_data).eq("id", sync_log_id).execute()


# ============================================================================
# Connection Management
# ============================================================================


def is_user_connected(user_id: str) -> bool:
    """Check if user has an active Notion connection"""
    token_record = get_user_tokens(user_id)
    return token_record is not None


def get_connection_status(user_id: str) -> Dict:
    """Get Notion connection status for a user.

    Returns:
        Dict with connection status, last sync time, document count
    """
    try:
        connected = is_user_connected(user_id)

        if not connected:
            return {"connected": False, "last_sync": None, "document_count": 0}

        # Get token info
        token_record = get_user_tokens(user_id)
        workspace_name = token_record.get("workspace_name", "Unknown Workspace")

        # Get last sync time
        sync_result = (
            supabase.table("notion_sync_log")
            .select("completed_at")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .order("completed_at", desc=True)
            .limit(1)
            .execute()
        )

        last_sync = sync_result.data[0]["completed_at"] if sync_result.data else None

        # Get document count from cache (fast) or fall back to exact count
        document_count = 0
        try:
            counts_result = (
                supabase.table("user_document_counts")
                .select("notion_count")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            if counts_result.data:
                document_count = counts_result.data.get("notion_count", 0)
            else:
                # Cache miss - fall back to exact count
                doc_result = (
                    supabase.table("documents")
                    .select("id", count="exact")
                    .eq("uploaded_by", user_id)
                    .eq("source_platform", "notion")
                    .execute()
                )
                document_count = doc_result.count or 0
        except Exception:
            # Cache table may not exist yet - fall back to exact count
            doc_result = (
                supabase.table("documents")
                .select("id", count="exact")
                .eq("uploaded_by", user_id)
                .eq("source_platform", "notion")
                .execute()
            )
            document_count = doc_result.count or 0

        return {
            "connected": True,
            "workspace_name": workspace_name,
            "last_sync": last_sync,
            "document_count": document_count,
        }

    except Exception as e:
        logger.warning(f"⚠️  Error getting connection status: {e}")
        return {"connected": False, "last_sync": None, "document_count": 0, "error": str(e)}


def disconnect_user(user_id: str) -> Dict:
    """Disconnect user's Notion (revoke tokens).
    Note: Does not delete synced documents.
    """
    try:
        now = datetime.now(timezone.utc).isoformat()

        supabase.table("notion_tokens").update({"is_active": False, "revoked_at": now}).eq(
            "user_id", user_id
        ).execute()

        return {"status": "success", "message": "Notion disconnected"}

    except Exception as e:
        raise NotionSyncError(f"Failed to disconnect: {e}")


def get_sync_history(user_id: str, limit: int = 10) -> Dict:
    """Get recent sync history for a user.

    Args:
        user_id: UUID of the user
        limit: Max number of sync logs to return

    Returns:
        Dict with sync logs and count
    """
    try:
        result = (
            supabase.table("notion_sync_log")
            .select("*")
            .eq("user_id", user_id)
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )

        return {"sync_logs": result.data, "count": len(result.data)}

    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        return {"sync_logs": [], "count": 0, "error": str(e)}
