"""
Mutation Testing Configuration

Run with: mutmut run
View results: mutmut results
Generate HTML report: mutmut html

Mutation testing verifies test quality by introducing small code changes (mutants)
and checking if tests catch them. Surviving mutants indicate weak test coverage.
"""

# Files to mutate - focus on core business logic
def targets():
    """Return list of files to mutate."""
    return [
        "api/routes/chat.py",
        "api/routes/conversations.py",
        "api/routes/documents.py",
        "api/routes/tasks.py",
        "api/routes/opportunities.py",
        "services/agent_router.py",
        "services/embedding_service.py",
        "services/document_processor.py",
        "services/meeting_orchestrator.py",
        "agents/coordinator.py",
        "agents/atlas.py",
        "agents/capital.py",
        "agents/guardian.py",
    ]


# Test command to run
def test_command():
    """Return the test command to run."""
    return "pytest tests/ -x -q --tb=no"


# Files/directories to exclude
def exclude():
    """Return patterns to exclude from mutation."""
    return [
        "tests/*",
        "**/test_*.py",
        "migrations/*",
        "__pycache__/*",
        ".venv/*",
        "*.pyc",
    ]


# Mutants to skip (known false positives)
def skip_mutations():
    """Return mutation types to skip."""
    return [
        # Skip string literal mutations in log messages
        "string",
        # Skip number literal mutations for magic numbers
        # "number",
    ]


# Configuration for mutmut
def configure():
    """Additional configuration."""
    return {
        # Number of parallel workers
        "parallel": True,
        # Stop after first surviving mutant
        "quick_check": False,
        # Timeout multiplier for slow tests
        "timeout_multiplier": 2.0,
    }
