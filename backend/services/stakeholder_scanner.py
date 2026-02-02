"""Stakeholder Scanner Service

Coordinates the stakeholder extraction process:
1. Identifies meeting documents to scan
2. Calls extractor to get stakeholders from each document
3. Runs deduplication to find potential matches
4. Links to related opportunities/tasks
5. Creates stakeholder candidates for review
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import anthropic

from services.stakeholder_deduplicator import StakeholderDeduplicator, find_duplicate_candidates
from services.stakeholder_extractor import ExtractedStakeholder, StakeholderExtractor
from services.stakeholder_linker import StakeholderLinker

logger = logging.getLogger(__name__)

# Document types/folders that typically contain meeting content
MEETING_DOCUMENT_PATTERNS = [
    "granola",
    "meeting",
    "transcript",
    "summary",
    "notes",
    "otter",
    "teams",
    "zoom",
]


class StakeholderScanner:
    """Coordinates stakeholder extraction from meeting documents."""

    def __init__(self, supabase_client, anthropic_client: Optional[anthropic.Anthropic] = None):
        self.supabase = supabase_client
        self.anthropic = anthropic_client
        self.extractor = StakeholderExtractor(anthropic_client)
        self.deduplicator = StakeholderDeduplicator(supabase_client)
        self.linker = StakeholderLinker(supabase_client)

    async def scan_documents(
        self,
        client_id: str,
        user_id: str,
        force_rescan: bool = False,
        since_days: int = 90,
        limit: int = 20,
    ) -> dict:
        """Scan meeting documents for stakeholders.

        Args:
            client_id: Client ID to scope documents
            user_id: User initiating the scan
            force_rescan: If True, rescan already-scanned documents
            since_days: Only scan documents from the last N days
            limit: Maximum documents to scan

        Returns:
            Summary of scan results
        """
        results = {
            "documents_scanned": 0,
            "stakeholders_found": 0,
            "candidates_created": 0,
            "duplicates_found": 0,
            "errors": [],
        }

        try:
            # Get documents to scan
            documents = await self._get_scannable_documents(
                client_id, force_rescan, since_days, limit
            )

            if not documents:
                logger.info("No documents to scan for stakeholders")
                return results

            logger.info(f"Scanning {len(documents)} documents for stakeholders")

            for doc in documents:
                try:
                    doc_results = await self._scan_single_document(doc, client_id, user_id)

                    results["documents_scanned"] += 1
                    results["stakeholders_found"] += doc_results["found"]
                    results["candidates_created"] += doc_results["created"]
                    results["duplicates_found"] += doc_results["duplicates"]

                    # Mark document as scanned
                    await self._mark_document_scanned(doc["id"])

                except Exception as e:
                    logger.error(f"Error scanning document {doc['id']}: {e}")
                    results["errors"].append(f"Document {doc.get('title', doc['id'])}: {str(e)}")

            return results

        except Exception as e:
            logger.error(f"Stakeholder scan failed: {e}")
            results["errors"].append(str(e))
            return results

    async def _get_scannable_documents(
        self, client_id: str, force_rescan: bool, since_days: int, limit: int
    ) -> list[dict]:
        """Get meeting documents that should be scanned."""
        try:
            from datetime import timedelta

            # Calculate date threshold
            cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

            # Build query
            query = (
                self.supabase.table("documents")
                .select("id, title, content, file_name, source, created_at, original_date")
                .eq("client_id", client_id)
                .gte("created_at", cutoff.isoformat())
            )

            # Filter for unscanned unless force_rescan
            if not force_rescan:
                query = query.is_("stakeholders_scanned_at", None)

            # Order by most recent first
            result = query.order("created_at", desc=True).limit(limit * 2).execute()

            if not result.data:
                return []

            # Filter for meeting-like documents
            meeting_docs = []
            for doc in result.data:
                if self._is_meeting_document(doc):
                    meeting_docs.append(doc)
                    if len(meeting_docs) >= limit:
                        break

            return meeting_docs

        except Exception as e:
            logger.error(f"Error fetching scannable documents: {e}")
            return []

    def _is_meeting_document(self, doc: dict) -> bool:
        """Check if document appears to be a meeting summary/transcript."""
        # Check title
        title = (doc.get("title") or "").lower()
        if any(pattern in title for pattern in MEETING_DOCUMENT_PATTERNS):
            return True

        # Check filename
        filename = (doc.get("file_name") or "").lower()
        if any(pattern in filename for pattern in MEETING_DOCUMENT_PATTERNS):
            return True

        # Check source
        source = (doc.get("source") or "").lower()
        if any(pattern in source for pattern in MEETING_DOCUMENT_PATTERNS):
            return True

        # Check content for meeting-like structure
        content = (doc.get("content") or "")[:2000].lower()
        meeting_indicators = [
            "meeting summary",
            "meeting notes",
            "attendees:",
            "participants:",
            "agenda:",
            "action items:",
            "key decisions:",
            "discussion points:",
            "transcript",
        ]
        if sum(1 for indicator in meeting_indicators if indicator in content) >= 2:
            return True

        return False

    async def _scan_single_document(self, doc: dict, client_id: str, user_id: str) -> dict:
        """Scan a single document and create candidates."""
        results = {"found": 0, "created": 0, "duplicates": 0}

        content = doc.get("content", "")
        if not content or len(content) < 100:
            return results

        # Extract date from document
        doc_date = doc.get("original_date") or doc.get("created_at", "")[:10]
        doc_name = doc.get("title") or doc.get("file_name") or "Unknown Document"

        # Extract stakeholders using LLM
        extracted = await self.extractor.extract_with_llm(
            text=content, source_document=doc_name, document_date=doc_date
        )

        results["found"] = len(extracted)
        if not extracted:
            return results

        # Find potential matches with existing stakeholders
        matches = await self.deduplicator.find_matches(extracted, client_id)

        # Create candidates
        for idx, stakeholder in enumerate(extracted):
            # Check for existing candidate with same name from this document
            existing = await find_duplicate_candidates(
                self.supabase, client_id, stakeholder.name, stakeholder.email
            )

            if existing:
                # Already have a candidate for this person
                results["duplicates"] += 1
                continue

            # Find related opportunities and tasks
            opp_ids, task_ids = await self.linker.find_related_entities(stakeholder, client_id)

            # Get match info if available
            match_info = matches.get(idx)

            # Create the candidate
            await self._create_candidate(
                stakeholder=stakeholder,
                client_id=client_id,
                doc_id=doc["id"],
                match_info=match_info,
                opportunity_ids=opp_ids,
                task_ids=task_ids,
            )

            results["created"] += 1

        return results

    async def _create_candidate(
        self,
        stakeholder: ExtractedStakeholder,
        client_id: str,
        doc_id: str,
        match_info,
        opportunity_ids: list[str],
        task_ids: list[str],
    ):
        """Create a stakeholder candidate record."""
        try:
            data = {
                "client_id": client_id,
                "name": stakeholder.name,
                "role": stakeholder.role,
                "department": stakeholder.department,
                "organization": stakeholder.organization,
                "email": stakeholder.email,
                "key_concerns": stakeholder.key_concerns,
                "interests": stakeholder.interests,
                "initial_sentiment": stakeholder.initial_sentiment,
                "influence_level": stakeholder.influence_level,
                "source_document_id": doc_id,
                "source_document_name": stakeholder.source_document,
                "source_text": stakeholder.source_text,
                "extraction_context": stakeholder.extraction_context,
                "confidence": stakeholder.confidence,
                "related_opportunity_ids": opportunity_ids,
                "related_task_ids": task_ids,
                "status": "pending",
            }

            # Add match info if found
            if match_info:
                data["potential_match_stakeholder_id"] = match_info.existing_stakeholder_id
                data["match_confidence"] = match_info.match_confidence

            self.supabase.table("stakeholder_candidates").insert(data).execute()

        except Exception as e:
            logger.error(f"Error creating stakeholder candidate: {e}")
            raise

    async def _mark_document_scanned(self, doc_id: str):
        """Mark a document as scanned for stakeholders."""
        try:
            self.supabase.table("documents").update(
                {"stakeholders_scanned_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", doc_id).execute()
        except Exception as e:
            logger.error(f"Error marking document as scanned: {e}")
