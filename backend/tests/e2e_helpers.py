"""E2E Test Helpers - Constants, fixture paths, and cleanup configuration.

This module provides shared constants for E2E browser tests executed via
Chrome DevTools MCP. All test data uses the E2E_PREFIX for easy identification
and cleanup.
"""

import os

# =============================================================================
# TEST DATA IDENTIFICATION
# =============================================================================

E2E_PREFIX = "E2E Test"
"""Prefix used for all E2E test data (tasks, projects, initiatives, etc.)."""

# =============================================================================
# FIXTURE PATHS
# =============================================================================

# Resolve paths relative to this file's location
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR = os.path.join(_THIS_DIR, "fixtures", "e2e")

FIXTURE_PDF = os.path.join(FIXTURE_DIR, "test-upload.pdf")
FIXTURE_MD = os.path.join(FIXTURE_DIR, "test-upload.md")
FIXTURE_TXT = os.path.join(FIXTURE_DIR, "test-upload.txt")
FIXTURE_INVALID = os.path.join(FIXTURE_DIR, "test-invalid.exe")

# =============================================================================
# CLEANUP CONFIGURATION
# =============================================================================

CLEANUP_ORDER = [
    "conversations",  # /chat - delete conversations with 'E2E' in title
    "meeting_rooms",  # /chat Meeting Rooms tab - delete 'E2E Test' rooms
    "tasks",  # /tasks - delete 'E2E Test' tasks
    "documents",  # /kb - delete uploaded test-upload.* docs
    "projects",  # /projects - delete 'E2E Test Project'
    "initiatives",  # /disco - delete 'E2E Test Initiative'
    "stakeholders",  # /intelligence - delete 'E2E Test' stakeholders
]
"""Order in which E2E test data should be cleaned up.

Conversations and meeting rooms first (they may reference tasks/projects),
then tasks and documents, then projects and initiatives last.
"""

# =============================================================================
# CLEANUP INSTRUCTIONS (for Claude Code to follow)
# =============================================================================

CLEANUP_PROTOCOL = """
E2E CLEANUP PROTOCOL
====================
Execute in order after every E2E test session:

1. CONVERSATIONS (/chat):
   - Search sidebar for conversations containing "E2E"
   - Delete each one (click delete, confirm)

2. MEETING ROOMS (/chat > Meeting Rooms tab):
   - Find rooms with "E2E Test" in name
   - Delete each room

3. TASKS (/tasks):
   - Search for "E2E Test"
   - Delete all matching tasks

4. DOCUMENTS (/kb):
   - Search for "test-upload" or "E2E Test"
   - Delete all matching documents

5. PROJECTS (/projects):
   - Find "E2E Test Project" or similar
   - Delete the project

6. INITIATIVES (/disco):
   - Find "E2E Test Initiative" or similar
   - Delete the initiative

7. STAKEHOLDERS (/intelligence > Stakeholders):
   - Find "E2E Test" stakeholders
   - Delete them

8. VERIFY:
   - Search "E2E Test" across tasks, projects, disco
   - Confirm no test data remains
"""

# =============================================================================
# TEST DATA TEMPLATES
# =============================================================================

TEST_TASK_TITLE = f"{E2E_PREFIX} Task - Automated"
TEST_TASK_DESCRIPTION = "Automated task created by E2E browser tests. Safe to delete."

TEST_PROJECT_NAME = f"{E2E_PREFIX} Project"
TEST_PROJECT_CODE = "E2E-001"
TEST_PROJECT_DESCRIPTION = "Automated project created by E2E browser tests."

TEST_INITIATIVE_NAME = f"{E2E_PREFIX} Initiative"
TEST_INITIATIVE_DESCRIPTION = "Automated initiative created by E2E browser tests."

TEST_MEETING_ROOM_NAME = f"{E2E_PREFIX} Meeting Room"

TEST_CHAT_MESSAGE = f"{E2E_PREFIX}: Hello, this is an automated test message."

TEST_STAKEHOLDER_NAME = f"{E2E_PREFIX} Stakeholder"
TEST_STAKEHOLDER_ROLE = "Test Role"
TEST_STAKEHOLDER_DEPARTMENT = "Test Department"


def verify_fixtures_exist() -> dict:
    """Verify all fixture files exist and return status."""
    fixtures = {
        "pdf": FIXTURE_PDF,
        "md": FIXTURE_MD,
        "txt": FIXTURE_TXT,
        "invalid": FIXTURE_INVALID,
    }
    return {name: os.path.exists(path) for name, path in fixtures.items()}


if __name__ == "__main__":
    print("E2E Test Helpers")
    print("=" * 40)
    print(f"Prefix: {E2E_PREFIX}")
    print(f"Fixture dir: {FIXTURE_DIR}")
    print()
    print("Fixture files:")
    for name, exists in verify_fixtures_exist().items():
        status = "OK" if exists else "MISSING"
        print(f"  {name}: [{status}]")
    print()
    print("Cleanup order:")
    for i, item in enumerate(CLEANUP_ORDER, 1):
        print(f"  {i}. {item}")
