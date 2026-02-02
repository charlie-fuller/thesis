"""Thesis Backend Test Suite.

This package contains all unit, integration, and API tests for the Thesis backend.

Test organization:
- test_auth.py - Authentication and authorization tests
- test_chat.py - Chat endpoint and RAG tests
- test_documents.py - Document upload and processing tests
- test_kpis.py - KPI calculation tests
- test_integrations.py - External service integration tests

Run tests with:
    cd backend
    pytest tests/ -v

Run with coverage:
    pytest tests/ -v --cov=. --cov-report=term-missing
"""
