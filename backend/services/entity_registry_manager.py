"""
Entity registry management service.
Handles CRUD operations and learning from corrections.

Version: 1.0.0
Created: 2026-01-23
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from services.phonetic_matcher import get_phonetic_matcher

logger = logging.getLogger(__name__)


@dataclass
class OrganizationEntry:
    """Organization registry entry."""

    id: str
    client_id: str
    canonical_name: str
    aliases: list[str]
    domain: Optional[str]
    industry: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class PersonEntry:
    """Person name registry entry."""

    id: str
    client_id: str
    canonical_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    aliases: list[str]
    metaphone_first: Optional[str]
    metaphone_last: Optional[str]
    stakeholder_id: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class EntityRegistryManager:
    """
    Manages entity registries for organizations and persons.

    Provides:
    - CRUD operations for registry entries
    - Bootstrap from existing stakeholders
    - Learning from user corrections
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self._phonetic_matcher = None

    @property
    def phonetic_matcher(self):
        """Lazy-load phonetic matcher."""
        if self._phonetic_matcher is None:
            try:
                self._phonetic_matcher = get_phonetic_matcher()
            except ImportError:
                logger.warning("Phonetic matching unavailable")
        return self._phonetic_matcher

    # =========================================================================
    # Organization Registry
    # =========================================================================

    async def add_organization(
        self,
        client_id: str,
        canonical_name: str,
        aliases: Optional[list[str]] = None,
        domain: Optional[str] = None,
        industry: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[str]:
        """
        Add an organization to the registry.

        Returns the new entry ID or None if already exists.
        """
        try:
            result = self.supabase.table("organization_registry").insert({
                "client_id": client_id,
                "canonical_name": canonical_name,
                "aliases": aliases or [],
                "domain": domain,
                "industry": industry,
                "notes": notes
            }).execute()

            if result.data:
                return result.data[0]["id"]
            return None
        except Exception as e:
            if "duplicate key" in str(e).lower():
                logger.debug(f"Organization '{canonical_name}' already exists")
                return None
            logger.error(f"Error adding organization: {e}")
            raise

    async def get_organization(
        self,
        client_id: str,
        org_id: Optional[str] = None,
        canonical_name: Optional[str] = None
    ) -> Optional[OrganizationEntry]:
        """Get an organization by ID or canonical name."""
        try:
            query = self.supabase.table("organization_registry").select("*")
            query = query.eq("client_id", client_id)

            if org_id:
                query = query.eq("id", org_id)
            elif canonical_name:
                query = query.eq("canonical_name", canonical_name)
            else:
                return None

            result = query.single().execute()

            if result.data:
                return OrganizationEntry(**result.data)
            return None
        except Exception as e:
            logger.error(f"Error getting organization: {e}")
            return None

    async def list_organizations(
        self,
        client_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[OrganizationEntry]:
        """List organizations in the registry."""
        try:
            result = self.supabase.table("organization_registry") \
                .select("*") \
                .eq("client_id", client_id) \
                .order("canonical_name") \
                .range(offset, offset + limit - 1) \
                .execute()

            return [OrganizationEntry(**row) for row in (result.data or [])]
        except Exception as e:
            logger.error(f"Error listing organizations: {e}")
            return []

    async def add_organization_alias(
        self,
        org_id: str,
        alias: str
    ) -> bool:
        """Add an alias to an organization."""
        try:
            self.supabase.rpc(
                "add_organization_alias",
                {"p_org_id": org_id, "p_alias": alias}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error adding organization alias: {e}")
            return False

    # =========================================================================
    # Person Name Registry
    # =========================================================================

    async def add_person(
        self,
        client_id: str,
        canonical_name: str,
        aliases: Optional[list[str]] = None,
        stakeholder_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[str]:
        """
        Add a person to the registry.

        Automatically computes metaphone codes for phonetic matching.
        Returns the new entry ID or None if already exists.
        """
        # Parse name parts
        parts = canonical_name.strip().split()
        first_name = parts[0] if parts else None
        last_name = " ".join(parts[1:]) if len(parts) > 1 else None

        # Compute metaphone codes
        metaphone_first = None
        metaphone_last = None
        if self.phonetic_matcher:
            codes = self.phonetic_matcher.get_name_codes(canonical_name)
            metaphone_first = codes[0][0] if codes[0][0] else None
            metaphone_last = codes[1][0] if codes[1][0] else None

        try:
            result = self.supabase.table("person_name_registry").insert({
                "client_id": client_id,
                "canonical_name": canonical_name,
                "first_name": first_name,
                "last_name": last_name,
                "aliases": aliases or [],
                "metaphone_first": metaphone_first,
                "metaphone_last": metaphone_last,
                "stakeholder_id": stakeholder_id,
                "notes": notes
            }).execute()

            if result.data:
                return result.data[0]["id"]
            return None
        except Exception as e:
            if "duplicate key" in str(e).lower():
                logger.debug(f"Person '{canonical_name}' already exists")
                return None
            logger.error(f"Error adding person: {e}")
            raise

    async def get_person(
        self,
        client_id: str,
        person_id: Optional[str] = None,
        canonical_name: Optional[str] = None
    ) -> Optional[PersonEntry]:
        """Get a person by ID or canonical name."""
        try:
            query = self.supabase.table("person_name_registry").select("*")
            query = query.eq("client_id", client_id)

            if person_id:
                query = query.eq("id", person_id)
            elif canonical_name:
                query = query.eq("canonical_name", canonical_name)
            else:
                return None

            result = query.single().execute()

            if result.data:
                return PersonEntry(**result.data)
            return None
        except Exception as e:
            logger.error(f"Error getting person: {e}")
            return None

    async def list_persons(
        self,
        client_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[PersonEntry]:
        """List persons in the registry."""
        try:
            result = self.supabase.table("person_name_registry") \
                .select("*") \
                .eq("client_id", client_id) \
                .order("canonical_name") \
                .range(offset, offset + limit - 1) \
                .execute()

            return [PersonEntry(**row) for row in (result.data or [])]
        except Exception as e:
            logger.error(f"Error listing persons: {e}")
            return []

    async def add_person_alias(
        self,
        person_id: str,
        alias: str
    ) -> bool:
        """Add an alias to a person."""
        try:
            self.supabase.rpc(
                "add_person_alias",
                {"p_person_id": person_id, "p_alias": alias}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error adding person alias: {e}")
            return False

    # =========================================================================
    # Learning from Corrections
    # =========================================================================

    async def learn_from_correction(
        self,
        client_id: str,
        entity_type: str,
        original_value: str,
        corrected_value: str,
        source_document_id: Optional[str] = None,
        source_candidate_id: Optional[str] = None,
        corrected_by: Optional[str] = None,
        context: Optional[str] = None
    ) -> bool:
        """
        Learn from a user correction.

        Records the correction and adds the original as an alias to the
        corrected entry (if it exists in the registry).
        """
        # Record the correction
        try:
            self.supabase.table("entity_corrections").insert({
                "client_id": client_id,
                "entity_type": entity_type,
                "original_value": original_value,
                "corrected_value": corrected_value,
                "source_document_id": source_document_id,
                "source_candidate_id": source_candidate_id,
                "corrected_by": corrected_by,
                "correction_context": context
            }).execute()
        except Exception as e:
            logger.error(f"Error recording correction: {e}")

        # Add original as alias to the corrected entry
        if entity_type == "person":
            entry = await self.get_person(client_id, canonical_name=corrected_value)
            if entry:
                await self.add_person_alias(entry.id, original_value)
                logger.info(
                    f"Added '{original_value}' as alias for person '{corrected_value}'"
                )
                return True
            else:
                # Corrected value not in registry - add it with original as alias
                await self.add_person(
                    client_id=client_id,
                    canonical_name=corrected_value,
                    aliases=[original_value]
                )
                logger.info(
                    f"Created person '{corrected_value}' with alias '{original_value}'"
                )
                return True

        elif entity_type == "organization":
            entry = await self.get_organization(
                client_id, canonical_name=corrected_value
            )
            if entry:
                await self.add_organization_alias(entry.id, original_value)
                logger.info(
                    f"Added '{original_value}' as alias for org '{corrected_value}'"
                )
                return True
            else:
                await self.add_organization(
                    client_id=client_id,
                    canonical_name=corrected_value,
                    aliases=[original_value]
                )
                logger.info(
                    f"Created org '{corrected_value}' with alias '{original_value}'"
                )
                return True

        return False

    # =========================================================================
    # Bootstrap
    # =========================================================================

    async def bootstrap_from_stakeholders(
        self,
        client_id: str
    ) -> dict:
        """
        Populate registries from existing stakeholder data.

        Returns dict with counts of created entries.
        """
        stats = {
            "persons_created": 0,
            "persons_skipped": 0,
            "organizations_created": 0,
            "organizations_skipped": 0
        }

        try:
            # Get all stakeholders for client
            result = self.supabase.table("stakeholders") \
                .select("id, name, organization, title") \
                .eq("client_id", client_id) \
                .execute()

            stakeholders = result.data or []
            logger.info(f"Bootstrapping from {len(stakeholders)} stakeholders")

            # Track unique organizations
            orgs_seen = set()

            for stakeholder in stakeholders:
                name = stakeholder.get("name")
                org = stakeholder.get("organization")
                stakeholder_id = stakeholder.get("id")

                # Add person
                if name:
                    person_id = await self.add_person(
                        client_id=client_id,
                        canonical_name=name,
                        stakeholder_id=stakeholder_id
                    )
                    if person_id:
                        stats["persons_created"] += 1
                    else:
                        stats["persons_skipped"] += 1

                # Add organization (dedup)
                if org and org not in orgs_seen:
                    orgs_seen.add(org)
                    org_id = await self.add_organization(
                        client_id=client_id,
                        canonical_name=org
                    )
                    if org_id:
                        stats["organizations_created"] += 1
                    else:
                        stats["organizations_skipped"] += 1

            logger.info(f"Bootstrap complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error during bootstrap: {e}")
            raise

    async def get_correction_history(
        self,
        client_id: str,
        entity_type: Optional[str] = None,
        limit: int = 50
    ) -> list[dict]:
        """Get recent correction history."""
        try:
            query = self.supabase.table("entity_corrections") \
                .select("*") \
                .eq("client_id", client_id) \
                .order("created_at", desc=True) \
                .limit(limit)

            if entity_type:
                query = query.eq("entity_type", entity_type)

            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting correction history: {e}")
            return []
