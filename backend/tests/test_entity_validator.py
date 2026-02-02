"""Tests for Entity Validation System

Tests the phonetic matching, entity validation, and registry management services.

Version: 1.0.0
Created: 2026-01-23
"""

from unittest.mock import MagicMock

import pytest

# ============================================================================
# PhoneticMatcher Tests
# ============================================================================


class TestPhoneticMatcher:
    """Tests for the PhoneticMatcher service."""

    def test_get_metaphone_codes_simple_name(self):
        """Test metaphone codes for a simple name."""
        try:
            from services.phonetic_matcher import PhoneticMatcher

            matcher = PhoneticMatcher()

            codes = matcher.get_metaphone_codes("Charlie")
            assert codes[0] != ""  # Primary code should exist
        except ImportError:
            pytest.skip("metaphone package not installed")

    def test_get_metaphone_codes_empty_name(self):
        """Test metaphone codes for empty input."""
        try:
            from services.phonetic_matcher import PhoneticMatcher

            matcher = PhoneticMatcher()

            codes = matcher.get_metaphone_codes("")
            assert codes == ("", "")

            codes = matcher.get_metaphone_codes("  ")
            assert codes == ("", "")
        except ImportError:
            pytest.skip("metaphone package not installed")

    def test_get_name_codes_full_name(self):
        """Test getting codes for first and last name separately."""
        try:
            from services.phonetic_matcher import PhoneticMatcher

            matcher = PhoneticMatcher()

            first_codes, last_codes = matcher.get_name_codes("Charlie Fuller")
            assert first_codes[0] != ""  # First name should have code
            assert last_codes[0] != ""  # Last name should have code
        except ImportError:
            pytest.skip("metaphone package not installed")

    def test_get_name_codes_single_name(self):
        """Test getting codes for single name."""
        try:
            from services.phonetic_matcher import PhoneticMatcher

            matcher = PhoneticMatcher()

            first_codes, last_codes = matcher.get_name_codes("Charlie")
            assert first_codes[0] != ""
            assert last_codes == ("", "")
        except ImportError:
            pytest.skip("metaphone package not installed")

    def test_compare_names_exact_phonetic_match(self):
        """Test comparing names that sound alike."""
        try:
            from services.phonetic_matcher import PhoneticMatcher

            matcher = PhoneticMatcher()

            # Charlie vs Charley - should sound the same
            result = matcher.compare_names("Charlie", "Charley")
            assert result.is_match is True
            assert result.confidence > 0.7
        except ImportError:
            pytest.skip("metaphone package not installed")

    def test_compare_names_different_sounds(self):
        """Test comparing names that sound different."""
        try:
            from services.phonetic_matcher import PhoneticMatcher

            matcher = PhoneticMatcher()

            # Charlie vs Robert - should not match
            result = matcher.compare_names("Charlie", "Robert")
            assert result.is_match is False
        except ImportError:
            pytest.skip("metaphone package not installed")

    def test_compare_names_full_names(self):
        """Test comparing full names."""
        try:
            from services.phonetic_matcher import PhoneticMatcher

            matcher = PhoneticMatcher()

            # Same person, different spelling
            result = matcher.compare_names("Sara Chen", "Sarah Chen")
            assert result.is_match is True

            # Different people
            result = matcher.compare_names("Sara Chen", "Sara Smith")
            # First names match but last names don't
            assert result.primary_match is False or result.confidence < 0.8
        except ImportError:
            pytest.skip("metaphone package not installed")

    def test_find_best_match(self):
        """Test finding best match from candidates."""
        try:
            from services.phonetic_matcher import PhoneticMatcher

            matcher = PhoneticMatcher()

            candidates = ["Charlie Fuller", "Robert Smith", "Sara Chen"]
            result = matcher.find_best_match("Charley Fuller", candidates)

            assert result is not None
            assert result[0] == "Charlie Fuller"
            assert result[1] > 0.7
        except ImportError:
            pytest.skip("metaphone package not installed")

    def test_find_best_match_no_match(self):
        """Test find_best_match when no good match exists."""
        try:
            from services.phonetic_matcher import PhoneticMatcher

            matcher = PhoneticMatcher()

            candidates = ["Robert Smith", "Sara Chen"]
            result = matcher.find_best_match("Charlie Fuller", candidates, threshold=0.9)

            assert result is None
        except ImportError:
            pytest.skip("metaphone package not installed")


# ============================================================================
# EntityValidator Tests
# ============================================================================


class TestEntityValidator:
    """Tests for the EntityValidator service."""

    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def validator(self, mock_supabase):
        """Create EntityValidator instance."""
        from services.entity_validator import EntityValidator

        return EntityValidator(mock_supabase)

    def test_validation_result_to_candidate_status(self):
        """Test converting ValidationResult to candidate status."""
        from services.entity_validator import ValidationResult, ValidationStatus

        # Exact match -> validated
        result = ValidationResult(
            original_value="Charlie",
            status=ValidationStatus.EXACT_MATCH,
            suggested_value="Charlie",
            confidence=1.0,
            match_reason="Exact match",
        )
        assert result.to_candidate_status() == "validated"

        # Fuzzy match -> suggested_correction
        result = ValidationResult(
            original_value="Charley",
            status=ValidationStatus.FUZZY_MATCH,
            suggested_value="Charlie",
            confidence=0.9,
            match_reason="Similar",
        )
        assert result.to_candidate_status() == "suggested_correction"

        # New entity -> new
        result = ValidationResult(
            original_value="New Person",
            status=ValidationStatus.NEW_ENTITY,
            suggested_value=None,
            confidence=1.0,
            match_reason="New",
        )
        assert result.to_candidate_status() == "new"

        # Potential error -> potential_error
        result = ValidationResult(
            original_value="???",
            status=ValidationStatus.POTENTIAL_ERROR,
            suggested_value=None,
            confidence=0.3,
            match_reason="Unclear",
        )
        assert result.to_candidate_status() == "potential_error"

    @pytest.mark.asyncio
    async def test_validate_person_name_empty(self, validator):
        """Test validating empty name."""
        result = await validator.validate_person_name("", "client123")

        assert result.status.value == "potential_error"
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_validate_person_name_exact_match(self, validator, mock_supabase):
        """Test validating name with exact match in registry."""
        # Mock the RPC response
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "reg123",
                    "canonical_name": "Charlie Fuller",
                    "aliases": [],
                    "match_type": "exact",
                    "similarity": 1.0,
                }
            ]
        )

        result = await validator.validate_person_name("Charlie Fuller", "client123")

        assert result.status.value == "exact_match"
        assert result.confidence == 1.0
        assert result.suggested_value == "Charlie Fuller"

    @pytest.mark.asyncio
    async def test_validate_person_name_no_match(self, validator, mock_supabase):
        """Test validating name with no match in registry."""
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])

        result = await validator.validate_person_name("New Person", "client123")

        assert result.status.value == "new_entity"
        assert result.confidence == 1.0
        assert result.suggested_value is None

    @pytest.mark.asyncio
    async def test_validate_organization_empty(self, validator):
        """Test validating empty organization name."""
        result = await validator.validate_organization("", "client123")

        assert result.status.value == "potential_error"

    @pytest.mark.asyncio
    async def test_validate_organization_alias_match(self, validator, mock_supabase):
        """Test validating organization with alias match."""
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "org123",
                    "canonical_name": "Contentful",
                    "aliases": ["Content Full", "Contentfull"],
                    "match_type": "alias",
                    "similarity": 0.95,
                }
            ]
        )

        result = await validator.validate_organization("Content Full", "client123")

        assert result.status.value == "alias_match"
        assert result.suggested_value == "Contentful"

    def test_calculate_fuzzy_similarity(self, validator):
        """Test fuzzy similarity calculation."""
        # Identical strings
        sim = validator.calculate_fuzzy_similarity("Charlie", "Charlie")
        assert sim == 1.0

        # Similar strings
        sim = validator.calculate_fuzzy_similarity("Charlie", "Charley")
        assert sim > 0.8

        # Different strings
        sim = validator.calculate_fuzzy_similarity("Charlie", "Robert")
        assert sim < 0.5

        # Empty strings
        sim = validator.calculate_fuzzy_similarity("", "")
        assert sim == 0.0


# ============================================================================
# EntityRegistryManager Tests
# ============================================================================


class TestEntityRegistryManager:
    """Tests for the EntityRegistryManager service."""

    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def manager(self, mock_supabase):
        """Create EntityRegistryManager instance."""
        from services.entity_registry_manager import EntityRegistryManager

        return EntityRegistryManager(mock_supabase)

    @pytest.mark.asyncio
    async def test_add_organization(self, manager, mock_supabase):
        """Test adding organization to registry."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "org123"}]
        )

        result = await manager.add_organization(
            client_id="client123", canonical_name="Contentful", aliases=["Content Full"]
        )

        assert result == "org123"
        mock_supabase.table.assert_called_with("organization_registry")

    @pytest.mark.asyncio
    async def test_add_organization_duplicate(self, manager, mock_supabase):
        """Test adding duplicate organization returns None."""
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception(
            "duplicate key value"
        )

        result = await manager.add_organization(client_id="client123", canonical_name="Contentful")

        assert result is None

    @pytest.mark.asyncio
    async def test_add_person(self, manager, mock_supabase):
        """Test adding person to registry."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "person123"}]
        )

        result = await manager.add_person(client_id="client123", canonical_name="Charlie Fuller")

        assert result == "person123"

    @pytest.mark.asyncio
    async def test_add_organization_alias(self, manager, mock_supabase):
        """Test adding alias to organization."""
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()

        result = await manager.add_organization_alias("org123", "Content Full")

        assert result is True
        mock_supabase.rpc.assert_called_with(
            "add_organization_alias", {"p_org_id": "org123", "p_alias": "Content Full"}
        )

    @pytest.mark.asyncio
    async def test_learn_from_correction_person(self, manager, mock_supabase):
        """Test learning from person name correction."""
        # Mock get_person to return an existing entry
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={
                "id": "person123",
                "client_id": "client123",
                "canonical_name": "Charlie Fuller",
                "first_name": "Charlie",
                "last_name": "Fuller",
                "aliases": [],
                "metaphone_first": "XRL",
                "metaphone_last": "FLR",
                "stakeholder_id": None,
                "notes": None,
                "created_at": "2026-01-23T00:00:00Z",
                "updated_at": "2026-01-23T00:00:00Z",
            }
        )

        # Mock insert for correction record
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

        # Mock RPC for adding alias
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()

        result = await manager.learn_from_correction(
            client_id="client123",
            entity_type="person",
            original_value="Charley Fuller",
            corrected_value="Charlie Fuller",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_bootstrap_from_stakeholders(self, manager, mock_supabase):
        """Test bootstrapping registries from stakeholders."""
        # Mock stakeholder query
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "sh1",
                    "name": "Charlie Fuller",
                    "organization": "Contentful",
                    "title": "Engineer",
                },
                {"id": "sh2", "name": "Sara Chen", "organization": "Contentful", "title": "VP"},
            ]
        )

        # Mock insert for persons
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "new123"}]
        )

        stats = await manager.bootstrap_from_stakeholders("client123")

        assert "persons_created" in stats
        assert "organizations_created" in stats


# ============================================================================
# Integration-style Tests
# ============================================================================


class TestEntityValidationIntegration:
    """Integration-style tests for entity validation flow."""

    @pytest.mark.asyncio
    async def test_validation_flow_new_entity(self):
        """Test validation flow for a completely new entity."""
        from services.entity_validator import EntityValidator, ValidationStatus

        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])

        validator = EntityValidator(mock_supabase)
        result = await validator.validate_person_name("Brand New Person", "client123")

        assert result.status == ValidationStatus.NEW_ENTITY
        assert result.to_candidate_status() == "new"

    @pytest.mark.asyncio
    async def test_validation_flow_with_suggestion(self):
        """Test validation flow where correction is suggested."""
        from services.entity_validator import EntityValidator, ValidationStatus

        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "reg123",
                    "canonical_name": "Charlie Fuller",
                    "aliases": [],
                    "stakeholder_id": None,
                    "match_type": "fuzzy",
                    "similarity": 0.9,
                }
            ]
        )

        validator = EntityValidator(mock_supabase)
        result = await validator.validate_person_name("Charley Fuller", "client123")

        assert result.status == ValidationStatus.FUZZY_MATCH
        assert result.suggested_value == "Charlie Fuller"
        assert result.to_candidate_status() == "suggested_correction"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
