"""
Tests for Project Detail Modal functionality

Tests the new endpoints and services added for:
- Related documents via vector search
- Q&A conversations with AI
- Conversation history

Run with: python -m pytest tests/test_project_modal.py -v
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4


class TestProjectContext:
    """Tests for services/project_context.py"""

    def test_get_scoring_related_documents_formats_correctly(self):
        """Verify that document chunks are formatted correctly for frontend"""
        from services.project_context import get_scoring_related_documents

        # Mock the search_similar_chunks function
        mock_chunks = [
            {
                'id': str(uuid4()),
                'document_id': str(uuid4()),
                'content': 'This is a test document about AI implementation.',
                'similarity': 0.85,
                'metadata': {
                    'filename': 'test_doc.pdf',
                    'page_number': 5,
                    'source_type': 'pdf',
                    'storage_path': '/uploads/test_doc.pdf'
                }
            }
        ]

        with patch('services.project_context.search_similar_chunks', return_value=mock_chunks):
            project = {
                'title': 'Test Project',
                'description': 'A test project',
                'department': 'IT',
                'current_state': 'Manual processes',
                'desired_state': 'Automated workflows',
                'roi_indicators': {}
            }

            results = get_scoring_related_documents(
                project=project,
                client_id=str(uuid4()),
                limit=5
            )

            assert len(results) == 1
            result = results[0]

            # Verify structure matches frontend interface
            assert 'chunk_id' in result
            assert 'document_id' in result
            assert 'document_name' in result
            assert 'relevance_score' in result
            assert 'snippet' in result
            assert 'metadata' in result

            # Verify metadata extraction from JSONB
            assert result['document_name'] == 'test_doc.pdf'
            assert result['metadata']['filename'] == 'test_doc.pdf'
            assert result['metadata']['page_number'] == 5

    def test_build_project_context_includes_all_sections(self):
        """Verify context string includes all project details"""
        from services.project_context import build_project_context

        project = {
            'title': 'AI Invoice Processing',
            'project_code': 'F01',
            'department': 'Finance',
            'status': 'scoping',
            'roi_potential': 4,
            'implementation_effort': 3,
            'strategic_alignment': 5,
            'stakeholder_readiness': 4,
            'total_score': 16,
            'tier': 2,
            'description': 'Automate invoice processing',
            'current_state': 'Manual entry',
            'desired_state': 'Automated OCR',
            'next_step': 'Schedule POC',
            'blockers': ['Budget approval needed'],
            'roi_indicators': {'time_savings_percent': 40}
        }

        related_docs = [
            {
                'document_name': 'Finance Strategy.pdf',
                'snippet': 'The finance team prioritizes automation...'
            }
        ]

        context = build_project_context(project, related_docs)

        # Verify key sections are present
        assert '<project_context>' in context
        assert 'AI Invoice Processing' in context
        assert 'F01' in context
        assert 'Finance' in context
        assert 'ROI Potential: 4/5' in context
        assert 'Manual entry' in context
        assert '<related_knowledge_base_documents>' in context
        assert 'Finance Strategy.pdf' in context


class TestProjectChat:
    """Tests for services/project_chat.py"""

    @pytest.mark.asyncio
    async def test_ask_about_project_returns_response_and_sources(self):
        """Verify ask_about_project returns expected structure"""
        from services.project_chat import ask_about_project

        mock_project = {
            'id': str(uuid4()),
            'title': 'Test Project',
            'project_code': 'T01',
            'department': 'IT',
            'status': 'identified',
            'total_score': 12,
            'tier': 3,
            'stakeholders': {'name': 'John Doe'}
        }

        mock_docs = [
            {
                'document_id': str(uuid4()),
                'document_name': 'Related.pdf',
                'relevance_score': 0.75,
                'snippet': 'Relevant content...'
            }
        ]

        with patch('services.project_chat.supabase') as mock_sb, \
             patch('services.project_chat.get_scoring_related_documents', return_value=mock_docs), \
             patch('services.project_chat.anthropic_client') as mock_anthropic:

            # Mock Supabase query
            mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = mock_project

            # Mock Anthropic response
            mock_response = Mock()
            mock_response.content = [Mock(text='This is the AI response about the project.')]
            mock_anthropic.messages.create.return_value = mock_response

            # Mock conversation storage
            mock_sb.table.return_value.insert.return_value.execute.return_value = Mock()

            result = await ask_about_project(
                project_id=str(uuid4()),
                question='What is the ROI potential?',
                client_id=str(uuid4()),
                user_id=str(uuid4())
            )

            assert 'response' in result
            assert 'sources' in result
            assert result['response'] == 'This is the AI response about the project.'


class TestProjectsAPI:
    """Tests for api/routes/projects.py endpoints"""

    def test_related_documents_endpoint_returns_list(self):
        """Verify GET /{id}/related-documents returns list"""
        # This test would require a running server or async test client
        # Documenting expected behavior:
        # - Should return List[RelatedDocumentResponse]
        # - Each item has: chunk_id, document_id, document_name, relevance_score, snippet, metadata
        pass

    def test_conversations_endpoint_returns_list(self):
        """Verify GET /{id}/conversations returns list"""
        # Expected behavior:
        # - Should return List[ConversationResponse]
        # - Ordered by created_at DESC (newest first)
        # - Each item has: id, question, response, source_documents, created_at
        pass

    def test_ask_endpoint_creates_conversation(self):
        """Verify POST /{id}/ask creates and returns conversation"""
        # Expected behavior:
        # - Accepts { question: string }
        # - Returns { response: string, sources: List[RelatedDocumentResponse] }
        # - Creates record in project_conversations table
        pass


class TestPydanticModels:
    """Tests for Pydantic model validation"""

    def test_related_document_response_model(self):
        """Verify RelatedDocumentResponse validates correctly"""
        from api.routes.projects import RelatedDocumentResponse, RelatedDocumentMetadata

        data = {
            'chunk_id': str(uuid4()),
            'document_id': str(uuid4()),
            'document_name': 'Test.pdf',
            'relevance_score': 0.85,
            'snippet': 'Test snippet content',
            'metadata': {
                'filename': 'Test.pdf',
                'page_number': 1,
                'source_type': 'pdf',
                'storage_path': '/path/to/file'
            }
        }

        model = RelatedDocumentResponse(**data)
        assert model.document_name == 'Test.pdf'
        assert model.relevance_score == 0.85

    def test_ask_question_request_validation(self):
        """Verify AskQuestionRequest validates correctly"""
        from api.routes.projects import AskQuestionRequest

        # Valid request
        req = AskQuestionRequest(question='What is the ROI?')
        assert req.question == 'What is the ROI?'

        # Empty question should fail
        with pytest.raises(Exception):
            AskQuestionRequest(question='')

    def test_conversation_response_model(self):
        """Verify ConversationResponse validates correctly"""
        from api.routes.projects import ConversationResponse

        data = {
            'id': str(uuid4()),
            'question': 'Test question?',
            'response': 'Test answer.',
            'source_documents': [
                {'document_id': str(uuid4()), 'document_name': 'Doc.pdf'}
            ],
            'created_at': '2026-01-16T12:00:00Z'
        }

        model = ConversationResponse(**data)
        assert model.question == 'Test question?'
        assert len(model.source_documents) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
