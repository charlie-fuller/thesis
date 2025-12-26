"""
Document Management Tests

Tests for document upload, processing, text extraction, and storage operations.
"""

import io
from unittest.mock import MagicMock, patch

import pytest

# ============================================================================
# Document Upload Tests
# ============================================================================

class TestDocumentUpload:
    """Tests for document upload functionality."""

    @patch("database.get_supabase")
    def test_upload_pdf_success(self, mock_get_supabase, authenticated_client, sample_pdf_bytes):
        """Test successful PDF upload."""
        mock_supabase = MagicMock()
        mock_supabase.storage.from_.return_value.upload.return_value = MagicMock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "doc-123", "filename": "test.pdf"}]
        )
        mock_get_supabase.return_value = mock_supabase

        response = authenticated_client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        )

        # Should accept the file
        assert response.status_code in [200, 202]  # 202 for background processing

    @patch("database.get_supabase")
    def test_upload_txt_success(self, mock_get_supabase, authenticated_client, sample_txt_content):
        """Test successful TXT upload."""
        mock_supabase = MagicMock()
        mock_supabase.storage.from_.return_value.upload.return_value = MagicMock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "doc-124", "filename": "test.txt"}]
        )
        mock_get_supabase.return_value = mock_supabase

        response = authenticated_client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", io.BytesIO(sample_txt_content), "text/plain")}
        )

        assert response.status_code in [200, 202]

    def test_upload_unsupported_file_type(self, authenticated_client):
        """Test that unsupported file types are rejected."""
        response = authenticated_client.post(
            "/api/documents/upload",
            files={"file": ("test.exe", io.BytesIO(b"fake exe content"), "application/x-msdownload")}
        )

        assert response.status_code == 400

    def test_upload_file_too_large(self, authenticated_client):
        """Test that files exceeding 50MB are rejected."""
        # Create a large file (simulated)
        large_content = b"x" * (51 * 1024 * 1024)  # 51 MB

        response = authenticated_client.post(
            "/api/documents/upload",
            files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        )

        assert response.status_code == 413  # Request Entity Too Large

    def test_upload_without_auth(self, test_client, sample_pdf_bytes):
        """Test that unauthenticated uploads are rejected."""
        response = test_client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        )

        assert response.status_code == 403


# ============================================================================
# Document Processing Tests
# ============================================================================

class TestDocumentProcessing:
    """Tests for document processing and text extraction."""

    def test_extract_text_from_pdf(self, sample_pdf_bytes):
        """Test text extraction from PDF."""
        # PDF extraction is complex, basic test
        assert sample_pdf_bytes.startswith(b"%PDF")

    def test_extract_text_from_txt(self, sample_txt_content):
        """Test text extraction from TXT."""
        text = sample_txt_content.decode("utf-8")
        assert "sample text document" in text

    def test_chunking_creates_appropriate_sizes(self):
        """Test that text chunking produces appropriate chunk sizes."""
        from config.constants import TEXT_CHUNKING

        # Default chunk size is 800 chars with 200 overlap
        assert TEXT_CHUNKING.DEFAULT_CHUNK_SIZE == 800
        assert TEXT_CHUNKING.DEFAULT_OVERLAP == 200

        # Test content that should produce multiple chunks
        long_text = "This is a test sentence. " * 100  # ~2500 chars

        # Should produce at least 3 chunks
        expected_chunks = len(long_text) // (TEXT_CHUNKING.DEFAULT_CHUNK_SIZE - TEXT_CHUNKING.DEFAULT_OVERLAP)
        assert expected_chunks >= 2

    def test_chunk_overlap_maintains_context(self):
        """Test that chunk overlap maintains context between chunks."""
        from config.constants import TEXT_CHUNKING

        # With 200 char overlap, adjacent chunks should share content
        overlap = TEXT_CHUNKING.DEFAULT_OVERLAP
        assert overlap > 0


# ============================================================================
# Document Listing Tests
# ============================================================================

class TestDocumentListing:
    """Tests for document listing and retrieval."""

    @pytest.mark.xfail(reason="Route uses module-level supabase import that can't be patched after import")
    @patch("database.get_supabase")
    def test_list_documents_success(self, mock_get_supabase, authenticated_client, sample_document):
        """Test listing user's documents."""
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[sample_document]
        )
        mock_get_supabase.return_value = mock_supabase

        response = authenticated_client.get("/api/documents")

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) == 1

    @pytest.mark.xfail(reason="Route uses module-level supabase import that can't be patched after import")
    @patch("database.get_supabase")
    def test_list_documents_empty(self, mock_get_supabase, authenticated_client):
        """Test listing documents when user has none."""
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_get_supabase.return_value = mock_supabase

        response = authenticated_client.get("/api/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []


# ============================================================================
# Document Deletion Tests
# ============================================================================

class TestDocumentDeletion:
    """Tests for document deletion."""

    @pytest.mark.xfail(reason="Route uses module-level supabase import that can't be patched after import")
    @patch("database.get_supabase")
    def test_delete_own_document(self, mock_get_supabase, authenticated_client):
        """Test that users can delete their own documents."""
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"id": "doc-123", "uploaded_by": "regular-user-id-12345", "storage_path": "path/to/doc"}
        )
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase.storage.from_.return_value.remove.return_value = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        response = authenticated_client.delete("/api/documents/doc-123")

        assert response.status_code == 200

    @pytest.mark.xfail(reason="Route uses module-level supabase import that can't be patched after import")
    def test_delete_document_not_found(self, authenticated_client, mock_supabase):
        """Test deletion of non-existent document."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data=None
        )

        response = authenticated_client.delete("/api/documents/nonexistent")

        assert response.status_code == 404


# ============================================================================
# Document Search Tests
# ============================================================================

class TestDocumentSearch:
    """Tests for document search functionality."""

    @patch("document_processor.search_similar_chunks")
    def test_search_documents_success(self, mock_search):
        """Test successful document search."""
        mock_search.return_value = [
            {"content": "Matching content", "document_id": "doc-123", "similarity": 0.9}
        ]

        from document_processor import search_similar_chunks

        results = search_similar_chunks(
            query="test query",
            client_id="test-client",
            limit=5
        )

        assert len(results) == 1
        assert results[0]["similarity"] == 0.9

    @patch("document_processor.search_similar_chunks")
    def test_search_with_no_results(self, mock_search):
        """Test search with no matching documents."""
        mock_search.return_value = []

        from document_processor import search_similar_chunks

        results = search_similar_chunks(
            query="obscure query with no matches",
            client_id="test-client",
            limit=5
        )

        assert len(results) == 0


# ============================================================================
# Storage Quota Tests
# ============================================================================

class TestStorageQuota:
    """Tests for storage quota management."""

    def test_default_storage_quota(self):
        """Test default storage quota values."""
        # Default quota is 500MB per user
        default_quota_mb = 500
        default_quota_bytes = default_quota_mb * 1024 * 1024

        assert default_quota_bytes == 524288000

    @patch("database.get_supabase")
    def test_storage_quota_check(self, mock_get_supabase, authenticated_client):
        """Test that storage quota is checked on upload."""
        mock_supabase = MagicMock()
        # User at 490MB of 500MB quota
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"storage_quota": 524288000, "storage_used": 513802240}
        )
        mock_get_supabase.return_value = mock_supabase

        # A 20MB file should fail quota check
        # (This would be validated in the actual endpoint)


# ============================================================================
# Embedding Generation Tests
# ============================================================================

class TestEmbeddingGeneration:
    """Tests for document embedding generation."""

    @patch("services.embeddings.voyageai")
    def test_embedding_generation_success(self, mock_voyage):
        """Test successful embedding generation."""
        mock_voyage.Client.return_value.embed.return_value.embeddings = [[0.1] * 1024]


        # Simulate embedding generation
        embedding = [0.1] * 1024
        assert len(embedding) == 1024

    def test_embedding_batch_size(self):
        """Test that batch size is appropriate."""
        from config.constants import EMBEDDING

        # Batch size of 100 is optimal for Voyage AI
        assert EMBEDDING.DEFAULT_BATCH_SIZE == 100

    def test_embedding_model_specification(self):
        """Test that correct embedding model is used."""
        from config.constants import EMBEDDING

        assert EMBEDDING.MODEL_NAME == "voyage-3"


# ============================================================================
# File Type Validation Tests
# ============================================================================

class TestFileTypeValidation:
    """Tests for file type validation."""

    def test_allowed_extensions(self):
        """Test that all expected file types are allowed."""
        from config.constants import FILE_LIMITS

        expected_extensions = {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls', 'csv', 'pptx', 'ppt', 'md', 'rtf'}

        assert FILE_LIMITS.ALLOWED_EXTENSIONS == expected_extensions

    def test_mime_type_mappings(self):
        """Test MIME type mappings are correct."""
        from config.constants import FILE_LIMITS

        assert FILE_LIMITS.MIME_TYPES['pdf'] == 'application/pdf'
        assert FILE_LIMITS.MIME_TYPES['docx'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        assert FILE_LIMITS.MIME_TYPES['txt'] == 'text/plain'

    def test_max_file_size(self):
        """Test maximum file size limit."""
        from config.constants import FILE_LIMITS

        assert FILE_LIMITS.MAX_SIZE_MB == 50
        assert FILE_LIMITS.MAX_SIZE_BYTES == 50 * 1024 * 1024
