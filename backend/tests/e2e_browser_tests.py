"""E2E Browser Tests for Thesis Platform.

This file contains test scenario definitions for Chrome DevTools MCP-based E2E testing.
These tests are meant to be executed by Claude Code using the Chrome DevTools MCP tools.

Usage:
    Claude Code reads these scenarios and executes them using MCP tools:
    - mcp__chrome-devtools__navigate_page
    - mcp__chrome-devtools__take_snapshot
    - mcp__chrome-devtools__click
    - mcp__chrome-devtools__fill
    - mcp__chrome-devtools__wait_for
    - mcp__chrome-devtools__list_console_messages
    - mcp__chrome-devtools__list_network_requests
    - mcp__chrome-devtools__take_screenshot
    - mcp__chrome-devtools__drag

Prerequisites:
    1. Backend running at localhost:8000
    2. Frontend running at localhost:3000
    3. Chrome browser open to the app
    4. Test user credentials available
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TestCategory(Enum):
    AUTH = "auth"
    CHAT = "chat"
    KB = "kb"
    TASKS = "tasks"
    OPPORTUNITIES = "projects"
    MEETING = "meeting"
    STAKEHOLDERS = "stakeholders"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    GRANOLA = "granola"
    HELP = "help"
    DISCO = "disco"


class TestType(Enum):
    HAPPY_PATH = "happy_path"
    VALIDATION = "validation"
    ERROR = "error"
    EMPTY_STATE = "empty_state"
    EDGE_CASE = "edge_case"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    FEATURE = "feature"
    LOADING = "loading"
    METRICS = "metrics"
    LOAD = "load"
    MONITORING = "monitoring"
    RESPONSIVE = "responsive"
    CONCURRENCY = "concurrency"


@dataclass
class E2ETestScenario:
    """Represents a single E2E test scenario."""

    id: str
    category: TestCategory
    test_type: TestType
    description: str
    steps: List[str]
    expected_result: str
    prerequisites: Optional[List[str]] = None
    cleanup: Optional[List[str]] = None


# =============================================================================
# TEST SCENARIOS
# =============================================================================

E2E_TEST_SCENARIOS = {
    # =========================================================================
    # AUTHENTICATION (8 tests)
    # =========================================================================
    "auth_login_success": E2ETestScenario(
        id="auth_login_success",
        category=TestCategory.AUTH,
        test_type=TestType.HAPPY_PATH,
        description="Successful login with valid credentials",
        steps=[
            "Navigate to /auth/login",
            "Take snapshot to find form elements",
            "Fill email field with test@example.com",
            "Fill password field with testpassword",
            "Click login button",
            "Wait for redirect to /chat",
            "Verify user menu shows logged in state",
        ],
        expected_result="User is logged in and redirected to /chat",
    ),
    "auth_login_invalid_email": E2ETestScenario(
        id="auth_login_invalid_email",
        category=TestCategory.AUTH,
        test_type=TestType.VALIDATION,
        description="Login fails with invalid email format",
        steps=[
            "Navigate to /auth/login",
            "Fill email field with 'notanemail'",
            "Fill password field with 'password123'",
            "Click login button",
            "Take snapshot to check for error",
        ],
        expected_result="Error message 'Invalid email' displayed",
    ),
    "auth_login_wrong_password": E2ETestScenario(
        id="auth_login_wrong_password",
        category=TestCategory.AUTH,
        test_type=TestType.ERROR,
        description="Login fails with incorrect password",
        steps=[
            "Navigate to /auth/login",
            "Fill email field with test@example.com",
            "Fill password field with wrongpassword",
            "Click login button",
            "Wait for error message",
            "Check network for 401 response",
        ],
        expected_result="Error message about invalid credentials shown",
    ),
    "auth_login_empty_fields": E2ETestScenario(
        id="auth_login_empty_fields",
        category=TestCategory.AUTH,
        test_type=TestType.VALIDATION,
        description="Login blocked with empty fields",
        steps=[
            "Navigate to /auth/login",
            "Click login button without filling fields",
            "Take snapshot to check for validation errors",
        ],
        expected_result="Required field errors shown for email and password",
    ),
    "auth_logout": E2ETestScenario(
        id="auth_logout",
        category=TestCategory.AUTH,
        test_type=TestType.HAPPY_PATH,
        description="User can log out successfully",
        steps=[
            "Login first (prerequisite)",
            "Click user menu in header",
            "Click logout button",
            "Wait for redirect to /auth/login",
            "Verify logged out state",
        ],
        expected_result="User is logged out and redirected to login page",
        prerequisites=["auth_login_success"],
    ),
    "auth_session_persistence": E2ETestScenario(
        id="auth_session_persistence",
        category=TestCategory.AUTH,
        test_type=TestType.EDGE_CASE,
        description="Session persists across page refresh",
        steps=[
            "Login first",
            "Navigate to /chat",
            "Refresh the page (navigate_page with reload)",
            "Verify still on /chat (not redirected to login)",
            "Verify user menu shows logged in state",
        ],
        expected_result="Session maintained after refresh",
        prerequisites=["auth_login_success"],
    ),
    "auth_protected_route": E2ETestScenario(
        id="auth_protected_route",
        category=TestCategory.AUTH,
        test_type=TestType.ERROR,
        description="Protected routes redirect to login when not authenticated",
        steps=[
            "Clear cookies/logout first",
            "Navigate directly to /chat",
            "Verify redirect to /auth/login",
        ],
        expected_result="Redirected to login page",
    ),
    "auth_expired_session": E2ETestScenario(
        id="auth_expired_session",
        category=TestCategory.AUTH,
        test_type=TestType.EDGE_CASE,
        description="Expired session prompts re-login",
        steps=[
            "Login first",
            "Wait for session expiry (or simulate via API)",
            "Try to perform an action requiring auth",
            "Verify redirect to login or error message",
        ],
        expected_result="User prompted to re-authenticate",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # CHAT (10 tests)
    # =========================================================================
    "chat_send_message": E2ETestScenario(
        id="chat_send_message",
        category=TestCategory.CHAT,
        test_type=TestType.HAPPY_PATH,
        description="Send a message and receive AI response",
        steps=[
            "Navigate to /chat",
            "Take snapshot to find input field",
            "Fill message input with 'Hello, can you help me?'",
            "Click send button",
            "Wait for message to appear in chat",
            "Wait for AI response to stream",
            "Verify both messages visible",
        ],
        expected_result="Message sent and AI response received",
        prerequisites=["auth_login_success"],
    ),
    "chat_empty_message_blocked": E2ETestScenario(
        id="chat_empty_message_blocked",
        category=TestCategory.CHAT,
        test_type=TestType.VALIDATION,
        description="Cannot send empty message",
        steps=[
            "Navigate to /chat",
            "Click send button with empty input",
            "Take snapshot to verify button disabled or error shown",
            "Check network - no API call should be made",
        ],
        expected_result="Send blocked, no API call made",
        prerequisites=["auth_login_success"],
    ),
    "chat_multiline_input": E2ETestScenario(
        id="chat_multiline_input",
        category=TestCategory.CHAT,
        test_type=TestType.EDGE_CASE,
        description="Multiline messages are supported",
        steps=[
            "Navigate to /chat",
            "Fill input with multiline text (use Shift+Enter)",
            "Send message",
            "Verify multiline preserved in sent message",
        ],
        expected_result="Multiline message displayed correctly",
        prerequisites=["auth_login_success"],
    ),
    "chat_at_mention_routing": E2ETestScenario(
        id="chat_at_mention_routing",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="@mention routes to specific agent",
        steps=[
            "Navigate to /chat",
            "Type '@atlas research AI trends'",
            "Send message",
            "Verify Atlas agent responds (check response header/attribution)",
        ],
        expected_result="Atlas agent specifically responds to query",
        prerequisites=["auth_login_success"],
    ),
    "chat_conversation_history": E2ETestScenario(
        id="chat_conversation_history",
        category=TestCategory.CHAT,
        test_type=TestType.READ,
        description="Conversation history persists",
        steps=[
            "Send a message in chat",
            "Refresh the page",
            "Verify conversation appears in sidebar",
            "Click on conversation",
            "Verify previous messages visible",
        ],
        expected_result="Conversation history preserved",
        prerequisites=["auth_login_success"],
    ),
    "chat_new_conversation": E2ETestScenario(
        id="chat_new_conversation",
        category=TestCategory.CHAT,
        test_type=TestType.CREATE,
        description="Create new conversation",
        steps=[
            "Navigate to /chat",
            "Click 'New Conversation' button",
            "Verify input cleared",
            "Verify new conversation created in sidebar",
        ],
        expected_result="New empty conversation started",
        prerequisites=["auth_login_success"],
    ),
    "chat_empty_state": E2ETestScenario(
        id="chat_empty_state",
        category=TestCategory.CHAT,
        test_type=TestType.EMPTY_STATE,
        description="Empty state for new users",
        steps=[
            "Login as new user with no conversations",
            "Navigate to /chat",
            "Verify welcome message or empty state UI",
            "Verify input is available",
        ],
        expected_result="Appropriate empty state shown",
        prerequisites=["auth_login_success"],
    ),
    "chat_loading_state": E2ETestScenario(
        id="chat_loading_state",
        category=TestCategory.CHAT,
        test_type=TestType.LOADING,
        description="Loading indicator while waiting for response",
        steps=[
            "Send a message",
            "Immediately take snapshot",
            "Verify loading indicator visible",
            "Wait for response",
            "Verify loading indicator gone",
        ],
        expected_result="Loading state shown during API call",
        prerequisites=["auth_login_success"],
    ),
    "chat_api_error_handling": E2ETestScenario(
        id="chat_api_error_handling",
        category=TestCategory.CHAT,
        test_type=TestType.ERROR,
        description="Handle API errors gracefully",
        steps=[
            "Send message (with backend returning error - may need to simulate)",
            "Verify error message shown in UI",
            "Verify retry option available",
            "Check console for proper error logging",
        ],
        expected_result="Error displayed with recovery option",
        prerequisites=["auth_login_success"],
    ),
    "chat_long_message": E2ETestScenario(
        id="chat_long_message",
        category=TestCategory.CHAT,
        test_type=TestType.EDGE_CASE,
        description="Handle very long messages",
        steps=[
            "Navigate to /chat",
            "Fill input with 5000+ character message",
            "Send message",
            "Verify message handled correctly (sent or truncation warning)",
        ],
        expected_result="Long message handled appropriately",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # KNOWLEDGE BASE (12 tests)
    # =========================================================================
    "kb_list_documents": E2ETestScenario(
        id="kb_list_documents",
        category=TestCategory.KB,
        test_type=TestType.READ,
        description="List documents in knowledge base",
        steps=[
            "Navigate to /kb",
            "Wait for document list to load",
            "Verify document cards display (title, date, tags)",
            "Check network for successful API call",
        ],
        expected_result="Document list displayed with metadata",
        prerequisites=["auth_login_success"],
    ),
    "kb_upload_pdf": E2ETestScenario(
        id="kb_upload_pdf",
        category=TestCategory.KB,
        test_type=TestType.CREATE,
        description="Upload a PDF document",
        steps=[
            "Navigate to /kb",
            "Click upload button",
            "Select PDF file using upload_file MCP tool",
            "Wait for upload progress",
            "Verify document appears in list",
            "Check network for successful upload",
        ],
        expected_result="PDF uploaded and appears in document list",
        prerequisites=["auth_login_success"],
    ),
    "kb_upload_invalid_type": E2ETestScenario(
        id="kb_upload_invalid_type",
        category=TestCategory.KB,
        test_type=TestType.VALIDATION,
        description="Reject invalid file types",
        steps=[
            "Navigate to /kb",
            "Try to upload .exe file",
            "Verify error message about unsupported file type",
            "Check that file was not uploaded",
        ],
        expected_result="Error: Unsupported file type",
        prerequisites=["auth_login_success"],
    ),
    "kb_upload_large_file": E2ETestScenario(
        id="kb_upload_large_file",
        category=TestCategory.KB,
        test_type=TestType.EDGE_CASE,
        description="Handle large file uploads",
        steps=[
            "Navigate to /kb",
            "Upload 50MB file",
            "Verify either: size limit error OR successful upload with progress",
        ],
        expected_result="Large file handled appropriately",
        prerequisites=["auth_login_success"],
    ),
    "kb_search_documents": E2ETestScenario(
        id="kb_search_documents",
        category=TestCategory.KB,
        test_type=TestType.READ,
        description="Search documents by keyword",
        steps=[
            "Navigate to /kb",
            "Fill search input with keyword",
            "Verify results filter as you type",
            "Verify 'no results' message if no matches",
        ],
        expected_result="Search filters documents correctly",
        prerequisites=["auth_login_success"],
    ),
    "kb_filter_by_tag": E2ETestScenario(
        id="kb_filter_by_tag",
        category=TestCategory.KB,
        test_type=TestType.READ,
        description="Filter documents by tag",
        steps=[
            "Navigate to /kb",
            "Click tag filter dropdown",
            "Select a tag",
            "Verify only matching documents shown",
        ],
        expected_result="Documents filtered by selected tag",
        prerequisites=["auth_login_success"],
    ),
    "kb_document_preview": E2ETestScenario(
        id="kb_document_preview",
        category=TestCategory.KB,
        test_type=TestType.READ,
        description="Preview document content",
        steps=[
            "Navigate to /kb",
            "Click on a document card",
            "Verify preview modal/panel opens",
            "Verify document content displayed",
        ],
        expected_result="Document preview shows content",
        prerequisites=["auth_login_success"],
    ),
    "kb_edit_document_tags": E2ETestScenario(
        id="kb_edit_document_tags",
        category=TestCategory.KB,
        test_type=TestType.UPDATE,
        description="Edit document tags",
        steps=[
            "Open document preview",
            "Click edit tags button",
            "Add new tag",
            "Save changes",
            "Verify tag persists after refresh",
        ],
        expected_result="Tags updated and persisted",
        prerequisites=["auth_login_success"],
    ),
    "kb_delete_document": E2ETestScenario(
        id="kb_delete_document",
        category=TestCategory.KB,
        test_type=TestType.DELETE,
        description="Delete a document",
        steps=[
            "Open document preview",
            "Click delete button",
            "Confirm deletion in dialog",
            "Verify document removed from list",
            "Check network for DELETE request",
        ],
        expected_result="Document deleted and removed from UI",
        prerequisites=["auth_login_success"],
        cleanup=["Re-upload test document if needed"],
    ),
    "kb_empty_state": E2ETestScenario(
        id="kb_empty_state",
        category=TestCategory.KB,
        test_type=TestType.EMPTY_STATE,
        description="Empty state when no documents",
        steps=[
            "Login as new user with no documents",
            "Navigate to /kb",
            "Verify 'No documents' message",
            "Verify upload CTA visible",
        ],
        expected_result="Empty state with upload prompt",
        prerequisites=["auth_login_success"],
    ),
    "kb_upload_error_recovery": E2ETestScenario(
        id="kb_upload_error_recovery",
        category=TestCategory.KB,
        test_type=TestType.ERROR,
        description="Recover from upload error",
        steps=[
            "Start file upload",
            "Simulate network failure",
            "Verify error message shown",
            "Verify retry option available",
        ],
        expected_result="Error shown with retry option",
        prerequisites=["auth_login_success"],
    ),
    "kb_bulk_upload": E2ETestScenario(
        id="kb_bulk_upload",
        category=TestCategory.KB,
        test_type=TestType.EDGE_CASE,
        description="Upload multiple files at once",
        steps=[
            "Select multiple files for upload",
            "Verify progress shown for each file",
            "Verify all files appear in list after upload",
        ],
        expected_result="All files uploaded successfully",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # TASKS (10 tests)
    # =========================================================================
    "tasks_kanban_load": E2ETestScenario(
        id="tasks_kanban_load",
        category=TestCategory.TASKS,
        test_type=TestType.READ,
        description="Kanban board loads with columns",
        steps=[
            "Navigate to /tasks",
            "Verify kanban columns load (Backlog, In Progress, Done, etc.)",
            "Verify tasks appear in correct columns",
            "Check network for successful API call",
        ],
        expected_result="Kanban board displays with tasks",
        prerequisites=["auth_login_success"],
    ),
    "tasks_create": E2ETestScenario(
        id="tasks_create",
        category=TestCategory.TASKS,
        test_type=TestType.CREATE,
        description="Create a new task",
        steps=[
            "Navigate to /tasks",
            "Click 'New Task' button",
            "Fill title field with 'Test Task from E2E'",
            "Fill description field",
            "Click save button",
            "Wait for task to appear in Backlog column",
            "Check network for POST request",
        ],
        expected_result="Task created and appears in Backlog",
        prerequisites=["auth_login_success"],
        cleanup=["Delete test task"],
    ),
    "tasks_create_empty_title": E2ETestScenario(
        id="tasks_create_empty_title",
        category=TestCategory.TASKS,
        test_type=TestType.VALIDATION,
        description="Cannot create task with empty title",
        steps=[
            "Click 'New Task' button",
            "Leave title field empty",
            "Try to save",
            "Verify validation error message",
            "Check network - no POST request made",
        ],
        expected_result="Validation error prevents save",
        prerequisites=["auth_login_success"],
    ),
    "tasks_edit": E2ETestScenario(
        id="tasks_edit",
        category=TestCategory.TASKS,
        test_type=TestType.UPDATE,
        description="Edit an existing task",
        steps=[
            "Click on a task card",
            "Edit the title",
            "Save changes",
            "Verify changes persisted",
            "Refresh and verify changes still there",
        ],
        expected_result="Task updated successfully",
        prerequisites=["auth_login_success"],
    ),
    "tasks_drag_drop": E2ETestScenario(
        id="tasks_drag_drop",
        category=TestCategory.TASKS,
        test_type=TestType.UPDATE,
        description="Drag task between columns",
        steps=[
            "Navigate to /tasks",
            "Find task in Backlog column (take snapshot)",
            "Drag task to In Progress column (use drag MCP tool)",
            "Verify task moved to new column",
            "Check network for PATCH/PUT request",
        ],
        expected_result="Task moved and status updated",
        prerequisites=["auth_login_success"],
    ),
    "tasks_delete": E2ETestScenario(
        id="tasks_delete",
        category=TestCategory.TASKS,
        test_type=TestType.DELETE,
        description="Delete a task",
        steps=[
            "Click on a task card",
            "Click delete button",
            "Confirm deletion",
            "Verify task removed from board",
            "Check network for DELETE request",
        ],
        expected_result="Task deleted and removed from UI",
        prerequisites=["auth_login_success", "tasks_create"],
    ),
    "tasks_empty_state": E2ETestScenario(
        id="tasks_empty_state",
        category=TestCategory.TASKS,
        test_type=TestType.EMPTY_STATE,
        description="Empty state when no tasks",
        steps=[
            "Login as new user with no tasks",
            "Navigate to /tasks",
            "Verify empty kanban message or prompt",
            "Verify create task CTA visible",
        ],
        expected_result="Empty state with create prompt",
        prerequisites=["auth_login_success"],
    ),
    "tasks_status_update": E2ETestScenario(
        id="tasks_status_update",
        category=TestCategory.TASKS,
        test_type=TestType.UPDATE,
        description="Update task status via dropdown",
        steps=[
            "Open task details",
            "Change status dropdown value",
            "Verify task moves to corresponding column",
            "Check network for update request",
        ],
        expected_result="Task status updated via dropdown",
        prerequisites=["auth_login_success"],
    ),
    "tasks_save_error": E2ETestScenario(
        id="tasks_save_error",
        category=TestCategory.TASKS,
        test_type=TestType.ERROR,
        description="Handle save errors gracefully",
        steps=[
            "Edit a task",
            "Simulate API failure on save",
            "Verify error message shown",
            "Verify data not lost (can retry)",
        ],
        expected_result="Error shown, data preserved",
        prerequisites=["auth_login_success"],
    ),
    "tasks_filter": E2ETestScenario(
        id="tasks_filter",
        category=TestCategory.TASKS,
        test_type=TestType.READ,
        description="Filter tasks",
        steps=[
            "Navigate to /tasks",
            "Apply filter (e.g., by agent assignment)",
            "Verify only matching tasks shown",
        ],
        expected_result="Tasks filtered correctly",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # OPPORTUNITIES (12 tests)
    # =========================================================================
    "opps_pipeline_load": E2ETestScenario(
        id="opps_pipeline_load",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.READ,
        description="Pipeline board loads with stages",
        steps=[
            "Navigate to /projects",
            "Verify pipeline columns load (Identified, Qualified, etc.)",
            "Verify projects appear in correct stages",
        ],
        expected_result="Pipeline displays with projects",
        prerequisites=["auth_login_success"],
    ),
    "opps_create": E2ETestScenario(
        id="opps_create",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.CREATE,
        description="Create new project",
        steps=[
            "Click 'New Project' button",
            "Fill project code (e.g., TEST-001)",
            "Fill title",
            "Set scores (feasibility, impact, etc.)",
            "Save",
            "Verify project appears in pipeline",
        ],
        expected_result="Project created in Identified stage",
        prerequisites=["auth_login_success"],
        cleanup=["Delete test project"],
    ),
    "opps_create_missing_required": E2ETestScenario(
        id="opps_create_missing_required",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.VALIDATION,
        description="Cannot create without required fields",
        steps=[
            "Click 'New Project'",
            "Leave code field empty",
            "Try to save",
            "Verify validation error for code field",
        ],
        expected_result="Validation error prevents save",
        prerequisites=["auth_login_success"],
    ),
    "opps_score_validation": E2ETestScenario(
        id="opps_score_validation",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.VALIDATION,
        description="Score values must be 1-5",
        steps=[
            "Create/edit project",
            "Enter score > 5 in a score field",
            "Verify validation error 'Score must be 1-5'",
        ],
        expected_result="Invalid score rejected",
        prerequisites=["auth_login_success"],
    ),
    "opps_tier_calculation": E2ETestScenario(
        id="opps_tier_calculation",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.FEATURE,
        description="Tier calculated from scores",
        steps=[
            "Create project with all scores = 5",
            "Verify Tier 1 badge displayed",
            "Edit scores to all = 1",
            "Verify Tier changes to 4",
        ],
        expected_result="Tier calculated correctly from scores",
        prerequisites=["auth_login_success"],
    ),
    "opps_edit": E2ETestScenario(
        id="opps_edit",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.UPDATE,
        description="Edit project details",
        steps=[
            "Click on project card",
            "Edit description",
            "Save changes",
            "Verify changes persisted",
        ],
        expected_result="Project updated successfully",
        prerequisites=["auth_login_success"],
    ),
    "opps_drag_between_stages": E2ETestScenario(
        id="opps_drag_between_stages",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.UPDATE,
        description="Drag project between pipeline stages",
        steps=[
            "Find project in Identified stage",
            "Drag to Qualified stage",
            "Verify project moved",
            "Verify status updated in API",
        ],
        expected_result="Project stage updated",
        prerequisites=["auth_login_success"],
    ),
    "opps_delete": E2ETestScenario(
        id="opps_delete",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.DELETE,
        description="Delete an project",
        steps=[
            "Open project details",
            "Click delete",
            "Confirm deletion",
            "Verify removed from pipeline",
        ],
        expected_result="Project deleted",
        prerequisites=["auth_login_success", "opps_create"],
    ),
    "opps_empty_state": E2ETestScenario(
        id="opps_empty_state",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.EMPTY_STATE,
        description="Empty state when no projects",
        steps=[
            "Login as new user",
            "Navigate to /projects",
            "Verify 'No projects' message",
        ],
        expected_result="Empty state displayed",
        prerequisites=["auth_login_success"],
    ),
    "opps_filter_by_tier": E2ETestScenario(
        id="opps_filter_by_tier",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.READ,
        description="Filter projects by tier",
        steps=[
            "Navigate to /projects",
            "Select Tier 1 filter",
            "Verify only Tier 1 projects shown",
        ],
        expected_result="Filtered by tier correctly",
        prerequisites=["auth_login_success"],
    ),
    "opps_search": E2ETestScenario(
        id="opps_search",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.READ,
        description="Search projects by title",
        steps=[
            "Navigate to /projects",
            "Enter search query",
            "Verify matching projects shown",
        ],
        expected_result="Search returns correct results",
        prerequisites=["auth_login_success"],
    ),
    "opps_link_stakeholder": E2ETestScenario(
        id="opps_link_stakeholder",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.FEATURE,
        description="Link stakeholder to project",
        steps=[
            "Open project details",
            "Click add stakeholder",
            "Select stakeholder from list",
            "Save",
            "Verify stakeholder linked",
        ],
        expected_result="Stakeholder linked to project",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # MEETING ROOMS (8 tests)
    # =========================================================================
    "meeting_list": E2ETestScenario(
        id="meeting_list",
        category=TestCategory.MEETING,
        test_type=TestType.READ,
        description="List meeting rooms",
        steps=[
            "Navigate to /meeting-room",
            "Verify meeting rooms list loads",
        ],
        expected_result="Meeting rooms displayed",
        prerequisites=["auth_login_success"],
    ),
    "meeting_create": E2ETestScenario(
        id="meeting_create",
        category=TestCategory.MEETING,
        test_type=TestType.CREATE,
        description="Create new meeting room",
        steps=[
            "Click create room button",
            "Enter room name",
            "Select agents to include",
            "Save room",
            "Verify room appears in list",
        ],
        expected_result="Meeting room created",
        prerequisites=["auth_login_success"],
        cleanup=["Delete test room"],
    ),
    "meeting_create_no_agents": E2ETestScenario(
        id="meeting_create_no_agents",
        category=TestCategory.MEETING,
        test_type=TestType.VALIDATION,
        description="Cannot create room without agents",
        steps=[
            "Click create room",
            "Enter room name",
            "Try to save without selecting agents",
            "Verify error 'Select at least one agent'",
        ],
        expected_result="Validation error shown",
        prerequisites=["auth_login_success"],
    ),
    "meeting_send_message": E2ETestScenario(
        id="meeting_send_message",
        category=TestCategory.MEETING,
        test_type=TestType.FEATURE,
        description="Send message in meeting room",
        steps=[
            "Enter a meeting room",
            "Send a message",
            "Verify agents respond",
            "Verify each agent's response is labeled",
        ],
        expected_result="Agents respond to user message",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_autonomous_mode": E2ETestScenario(
        id="meeting_autonomous_mode",
        category=TestCategory.MEETING,
        test_type=TestType.FEATURE,
        description="Autonomous discussion mode",
        steps=[
            "Enter meeting room",
            "Enable autonomous mode toggle",
            "Verify agents begin discussing",
            "Verify user can interject",
        ],
        expected_result="Agents discuss autonomously",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_delete": E2ETestScenario(
        id="meeting_delete",
        category=TestCategory.MEETING,
        test_type=TestType.DELETE,
        description="Delete meeting room",
        steps=[
            "Click room settings",
            "Click delete room",
            "Confirm deletion",
            "Verify removed from list",
        ],
        expected_result="Meeting room deleted",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_empty_state": E2ETestScenario(
        id="meeting_empty_state",
        category=TestCategory.MEETING,
        test_type=TestType.EMPTY_STATE,
        description="Empty state when no rooms",
        steps=[
            "Login as new user",
            "Navigate to /meeting-room",
            "Verify 'No meeting rooms' message",
        ],
        expected_result="Empty state displayed",
        prerequisites=["auth_login_success"],
    ),
    "meeting_synthesis": E2ETestScenario(
        id="meeting_synthesis",
        category=TestCategory.MEETING,
        test_type=TestType.FEATURE,
        description="Generate meeting synthesis",
        steps=[
            "Have discussion in room",
            "Click generate synthesis button",
            "Wait for synthesis generation",
            "Verify synthesis report displayed",
        ],
        expected_result="Synthesis report generated",
        prerequisites=["auth_login_success", "meeting_send_message"],
    ),
    # =========================================================================
    # PERFORMANCE & QUALITY (6 tests)
    # =========================================================================
    "perf_home_page": E2ETestScenario(
        id="perf_home_page",
        category=TestCategory.PERFORMANCE,
        test_type=TestType.METRICS,
        description="Home page Core Web Vitals",
        steps=[
            "Navigate to home page",
            "Capture performance metrics (LCP, FID, CLS)",
            "Verify LCP < 2.5s",
            "Verify CLS < 0.1",
        ],
        expected_result="Core Web Vitals within targets",
        prerequisites=["auth_login_success"],
    ),
    "perf_kb_with_many_docs": E2ETestScenario(
        id="perf_kb_with_many_docs",
        category=TestCategory.PERFORMANCE,
        test_type=TestType.LOAD,
        description="KB performance with many documents",
        steps=[
            "Navigate to /kb with 100+ documents",
            "Verify page loads in < 3s",
            "Scroll through documents",
            "Verify no jank or freezing",
        ],
        expected_result="KB performs well with many docs",
        prerequisites=["auth_login_success"],
    ),
    "console_no_errors": E2ETestScenario(
        id="console_no_errors",
        category=TestCategory.QUALITY,
        test_type=TestType.MONITORING,
        description="No console errors during navigation",
        steps=[
            "Navigate through all main pages",
            "Check console messages after each navigation",
            "Verify no JavaScript errors",
        ],
        expected_result="No JS errors in console",
        prerequisites=["auth_login_success"],
    ),
    "network_api_calls": E2ETestScenario(
        id="network_api_calls",
        category=TestCategory.QUALITY,
        test_type=TestType.MONITORING,
        description="API calls succeed without 5xx errors",
        steps=[
            "Perform CRUD operations across features",
            "Monitor network requests",
            "Verify no 5xx errors",
            "Verify correct endpoints called",
        ],
        expected_result="All API calls successful",
        prerequisites=["auth_login_success"],
    ),
    "responsive_mobile": E2ETestScenario(
        id="responsive_mobile",
        category=TestCategory.QUALITY,
        test_type=TestType.RESPONSIVE,
        description="Mobile viewport responsiveness",
        steps=[
            "Resize viewport to mobile (375x667)",
            "Navigate through main pages",
            "Verify layout adapts correctly",
            "Verify all features accessible",
        ],
        expected_result="UI responsive on mobile",
        prerequisites=["auth_login_success"],
    ),
    "concurrent_operations": E2ETestScenario(
        id="concurrent_operations",
        category=TestCategory.QUALITY,
        test_type=TestType.CONCURRENCY,
        description="Handle concurrent edits",
        steps=[
            "Open same page in 2 browser tabs",
            "Make edits in both tabs",
            "Verify no data loss or corruption",
        ],
        expected_result="Concurrent edits handled safely",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # HELP SYSTEM (8 tests)
    # =========================================================================
    "help_panel_open": E2ETestScenario(
        id="help_panel_open",
        category=TestCategory.HELP,
        test_type=TestType.HAPPY_PATH,
        description="Open help panel from navigation",
        steps=[
            "Navigate to any page (e.g., /chat)",
            "Take snapshot to find help button (question mark icon in header)",
            "Click help button",
            "Verify help panel/modal opens",
            "Verify search input is visible",
            "Verify help categories are displayed",
        ],
        expected_result="Help panel opens with search and categories",
        prerequisites=["auth_login_success"],
    ),
    "help_panel_close": E2ETestScenario(
        id="help_panel_close",
        category=TestCategory.HELP,
        test_type=TestType.HAPPY_PATH,
        description="Close help panel",
        steps=[
            "Open help panel",
            "Click close button or click outside panel",
            "Verify help panel closes",
            "Verify underlying page still visible and functional",
        ],
        expected_result="Help panel closes cleanly",
        prerequisites=["auth_login_success", "help_panel_open"],
    ),
    "help_search_agents": E2ETestScenario(
        id="help_search_agents",
        category=TestCategory.HELP,
        test_type=TestType.READ,
        description="Search help for agent information",
        steps=[
            "Open help panel",
            "Type 'agents' in search input",
            "Wait for search results",
            "Verify results include agent-related help topics",
            "Verify results show titles and snippets",
        ],
        expected_result="Search returns relevant agent help topics",
        prerequisites=["auth_login_success"],
    ),
    "help_search_disco": E2ETestScenario(
        id="help_search_disco",
        category=TestCategory.HELP,
        test_type=TestType.READ,
        description="Search help for DISCo information",
        steps=[
            "Open help panel",
            "Type 'DISCo' in search input",
            "Wait for search results",
            "Verify results include DISCo initiatives help",
            "Verify results mention workflow stages (Discovery, Intelligence, Synthesis, Convergence)",
        ],
        expected_result="Search returns DISCo-related help content",
        prerequisites=["auth_login_success"],
    ),
    "help_search_discovery_inbox": E2ETestScenario(
        id="help_search_discovery_inbox",
        category=TestCategory.HELP,
        test_type=TestType.READ,
        description="Search help for Discovery Inbox",
        steps=[
            "Open help panel",
            "Type 'Discovery Inbox' in search input",
            "Wait for search results",
            "Verify results explain auto-extraction feature",
            "Verify results mention tasks, projects, stakeholders candidates",
        ],
        expected_result="Search returns Discovery Inbox help content",
        prerequisites=["auth_login_success"],
    ),
    "help_search_no_results": E2ETestScenario(
        id="help_search_no_results",
        category=TestCategory.HELP,
        test_type=TestType.EMPTY_STATE,
        description="Handle search with no results",
        steps=[
            "Open help panel",
            "Type 'xyznonexistent123' in search input",
            "Wait for search to complete",
            "Verify 'No results found' or similar message",
            "Verify suggestions or fallback options shown",
        ],
        expected_result="No results message displayed gracefully",
        prerequisites=["auth_login_success"],
    ),
    "help_navigate_to_doc": E2ETestScenario(
        id="help_navigate_to_doc",
        category=TestCategory.HELP,
        test_type=TestType.FEATURE,
        description="Navigate to full help documentation",
        steps=[
            "Open help panel",
            "Search for a topic (e.g., 'meeting rooms')",
            "Click on a search result",
            "Verify help content expands or navigates to full doc",
            "Verify content matches the selected topic",
        ],
        expected_result="Full help content displayed for selected topic",
        prerequisites=["auth_login_success"],
    ),
    "help_contextual": E2ETestScenario(
        id="help_contextual",
        category=TestCategory.HELP,
        test_type=TestType.FEATURE,
        description="Help shows contextual suggestions based on current page",
        steps=[
            "Navigate to /tasks",
            "Open help panel",
            "Verify task-related help topics appear prominently",
            "Navigate to /disco",
            "Open help panel",
            "Verify DISCo-related help topics appear prominently",
        ],
        expected_result="Help suggestions relevant to current page context",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # DISCO INITIATIVES (10 tests)
    # =========================================================================
    "disco_list_initiatives": E2ETestScenario(
        id="disco_list_initiatives",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="List DISCo initiatives",
        steps=[
            "Navigate to /disco",
            "Wait for page to load",
            "Take snapshot to verify page structure",
            "Verify initiative cards display (if any exist)",
            "Verify 'New Initiative' or 'Create Initiative' button visible",
        ],
        expected_result="DISCo page loads with initiatives list",
        prerequisites=["auth_login_success"],
    ),
    "disco_create_initiative": E2ETestScenario(
        id="disco_create_initiative",
        category=TestCategory.DISCO,
        test_type=TestType.CREATE,
        description="Create new DISCo initiative",
        steps=[
            "Navigate to /disco",
            "Click 'New Initiative' button (or 'Create Initiative' if empty state)",
            "Verify 'Create New Initiative' modal opens",
            "Fill 'Name' field with 'E2E Test Initiative'",
            "Fill 'Description' field with 'Test initiative for E2E testing'",
            "Click 'Create Initiative' button",
            "Wait for initiative to be created",
            "Verify redirected to initiative detail view",
            "Verify initiative name visible",
        ],
        expected_result="Initiative created and detail view shown",
        prerequisites=["auth_login_success"],
        cleanup=["Delete test initiative"],
    ),
    "disco_create_missing_name": E2ETestScenario(
        id="disco_create_missing_name",
        category=TestCategory.DISCO,
        test_type=TestType.VALIDATION,
        description="Cannot create initiative without name",
        steps=[
            "Navigate to /disco",
            "Click 'New Initiative' button",
            "Leave 'Name' field empty",
            "Fill 'Description' field",
            "Try to click 'Create Initiative' button",
            "Verify validation error or button disabled",
        ],
        expected_result="Validation prevents creation without name",
        prerequisites=["auth_login_success"],
    ),
    "disco_initiative_tabs": E2ETestScenario(
        id="disco_initiative_tabs",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="Initiative detail view has correct tabs",
        steps=[
            "Navigate to an existing initiative detail view",
            "Take snapshot to verify tabs",
            "Verify 'Documents' tab exists",
            "Verify 'Run Agent' tab exists",
            "Verify 'Outputs' tab exists",
            "Verify 'Chat' tab exists",
            "Click each tab and verify content area changes",
        ],
        expected_result="All four tabs present and functional",
        prerequisites=["auth_login_success", "disco_create_initiative"],
    ),
    "disco_upload_document": E2ETestScenario(
        id="disco_upload_document",
        category=TestCategory.DISCO,
        test_type=TestType.CREATE,
        description="Upload document to initiative",
        steps=[
            "Navigate to initiative detail view",
            "Click 'Documents' tab",
            "Click upload button",
            "Select a test document using upload_file MCP tool",
            "Wait for upload to complete",
            "Verify document appears in documents list",
        ],
        expected_result="Document uploaded to initiative",
        prerequisites=["auth_login_success", "disco_create_initiative"],
    ),
    "disco_run_agent": E2ETestScenario(
        id="disco_run_agent",
        category=TestCategory.DISCO,
        test_type=TestType.FEATURE,
        description="Run a DISCo agent on initiative",
        steps=[
            "Navigate to initiative detail view",
            "Click 'Run Agent' tab",
            "Select 'Discovery Prep' or 'Triage' from dropdown",
            "Click 'Run' button",
            "Verify streaming output appears",
            "Wait for agent to complete",
            "Verify output is displayed",
        ],
        expected_result="Agent runs and output displayed",
        prerequisites=["auth_login_success", "disco_create_initiative", "disco_upload_document"],
    ),
    "disco_view_outputs": E2ETestScenario(
        id="disco_view_outputs",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="View agent outputs",
        steps=[
            "Navigate to initiative detail view",
            "Click 'Outputs' tab",
            "Verify previous agent outputs are listed",
            "Click on an output to expand it",
            "Verify output content is displayed",
        ],
        expected_result="Agent outputs viewable in Outputs tab",
        prerequisites=["auth_login_success", "disco_run_agent"],
    ),
    "disco_status_badges": E2ETestScenario(
        id="disco_status_badges",
        category=TestCategory.DISCO,
        test_type=TestType.FEATURE,
        description="Initiative status badges update correctly",
        steps=[
            "Navigate to /disco",
            "Find initiative card",
            "Note current status badge (e.g., 'Draft')",
            "Run Triage agent on initiative",
            "Return to /disco list",
            "Verify status badge changed to 'Triaged'",
        ],
        expected_result="Status badge reflects workflow progress",
        prerequisites=["auth_login_success", "disco_create_initiative"],
    ),
    "disco_share_initiative": E2ETestScenario(
        id="disco_share_initiative",
        category=TestCategory.DISCO,
        test_type=TestType.FEATURE,
        description="Share initiative with another user",
        steps=[
            "Navigate to initiative detail view",
            "Click 'Share' button",
            "Verify share modal opens",
            "Enter email address in input",
            "Select role ('Viewer' or 'Editor')",
            "Click 'Invite' button",
            "Verify success message or collaborator added to list",
        ],
        expected_result="Initiative shared with specified user",
        prerequisites=["auth_login_success", "disco_create_initiative"],
    ),
    "disco_empty_state": E2ETestScenario(
        id="disco_empty_state",
        category=TestCategory.DISCO,
        test_type=TestType.EMPTY_STATE,
        description="Empty state when no initiatives",
        steps=[
            "Login as new user with no initiatives",
            "Navigate to /disco",
            "Verify empty state message displayed",
            "Verify 'Create Initiative' button visible",
        ],
        expected_result="Empty state with create prompt",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # GRANOLA SYNC (3 tests)
    # =========================================================================
    "granola_sync_new_file": E2ETestScenario(
        id="granola_sync_new_file",
        category=TestCategory.GRANOLA,
        test_type=TestType.FEATURE,
        description="Create Granola meeting file, verify sync picks it up and extracts task/project/stakeholder",
        steps=[
            "Navigate to home dashboard to see GranolaScanPanel",
            "Take snapshot to see current Granola status",
            "Create test file at ~/vaults/Contentful/Granola/Transcripts/E2E-Test-Meeting-{timestamp}.md",
            "File content should include:",
            "  - Meeting header with date: 2026-01-28",
            "  - Participants: Charlie, Dr. Elena Vostokov (VP of Data Science), Marcus Chen (Director of Engineering)",
            "  - Strategic task FROM Chris Baumgartner TO Charlie: 'Present quantum computing ROI analysis to board by Feb 15'",
            "  - High-score project: 'Quantum-enhanced ML Pipeline' with exec sponsorship, $2M annual savings, CEO priority",
            "  - New stakeholder: Dr. Elena Vostokov with role, concerns about data governance, interests in ML ops",
            "Wait 15-20 seconds for Obsidian watcher to detect file change",
            "Observe GranolaScanPanel - should show sync activity indicator",
            "Wait for sync to complete (indicator disappears or shows 'Just synced')",
            "Click Scan button on GranolaScanPanel to trigger Granola scanner",
            "Wait for scan to complete",
            "Navigate to /tasks and verify new task candidate appears (may need to check candidates section)",
            "Navigate to /projects and verify new project candidate appears",
            "Navigate to /stakeholders or admin page and verify Dr. Elena Vostokov appears as candidate",
        ],
        expected_result="File synced, task/project/stakeholder candidates created from meeting content",
        prerequisites=["auth_login_success"],
        cleanup=[
            "Delete test file E2E-Test-Meeting-{timestamp}.md from Granola/Transcripts folder"
        ],
    ),
    "granola_sync_activity_display": E2ETestScenario(
        id="granola_sync_activity_display",
        category=TestCategory.GRANOLA,
        test_type=TestType.FEATURE,
        description="Verify sync activity indicator shows during file sync",
        steps=[
            "Navigate to home dashboard",
            "Take snapshot to find GranolaScanPanel",
            "Create or modify a file in ~/vaults/Contentful/Granola/Transcripts/",
            "Watch GranolaScanPanel for sync activity indicator (amber banner with spinning icon)",
            "Verify 'Syncing: filename.md' message appears",
            "Wait for sync to complete",
            "Verify 'Just synced: N file(s)' message appears briefly",
        ],
        expected_result="Sync activity indicator shows during sync and completion message appears",
        prerequisites=["auth_login_success"],
    ),
    "granola_scan_panel_status": E2ETestScenario(
        id="granola_scan_panel_status",
        category=TestCategory.GRANOLA,
        test_type=TestType.READ,
        description="GranolaScanPanel shows correct status",
        steps=[
            "Navigate to home dashboard",
            "Take snapshot to find GranolaScanPanel",
            "Verify panel shows connection status (green if connected)",
            "Verify panel shows scanned/total files count",
            "Verify pending files count if any unscanned files exist",
            "Click Scan button",
            "Verify scanning state (button shows 'Scanning...' with spinner)",
            "Wait for scan to complete",
            "Verify scan message appears",
        ],
        expected_result="GranolaScanPanel displays accurate status and responds to scan action",
        prerequisites=["auth_login_success"],
    ),
}


# =============================================================================
# GRANOLA E2E TEST FIXTURES
# =============================================================================

# Sample meeting content for granola_sync_new_file test
# This content is designed to reliably trigger extraction of:
# - 1 strategic task (from Chris Baumgartner to Charlie)
# - 1 Tier-1 project (high scores, exec sponsorship)
# - 1 new stakeholder (VP with role, concerns, interests)
GRANOLA_E2E_TEST_MEETING_CONTENT = """## Granola Notes.
## E2E Test - Quantum Computing Strategy Session
**Granola ID:** e2e-test-{timestamp}
**Created:** 2026-01-28T10:00:00.000Z
**Updated:** 2026-01-28T11:30:00.000Z

### Participants
- Charlie Fuller (AI Solutions Partner)
- Dr. Elena Vostokov (VP of Data Science)
- Marcus Chen (Director of Engineering)
- Chris Baumgartner (Chief Technology Officer)

### Executive Summary

Chris Baumgartner opened the meeting emphasizing this is a CEO-priority initiative. The board has approved a $2.5M budget for quantum computing exploration in 2026, and we need to move quickly to capture first-mover advantage.

### Quantum-Enhanced ML Pipeline Initiative

Dr. Elena Vostokov presented the business case for implementing quantum-enhanced machine learning pipelines:

- **Annual cost savings: $2M** through 40% reduction in model training time
- **Executive sponsorship:** Direct CEO priority, board-approved budget
- **Strategic alignment:** Directly tied to company's AI-first transformation strategy
- **Timeline:** Proof of concept ready in 8 weeks, production in Q2 2026
- **Team readiness:** Budget approved, quantum computing team already hired

Chris Baumgartner: "This is exactly the kind of transformative initiative we need. Elena, your team has done excellent work on the business case. Charlie, I need you to present the quantum computing ROI analysis to the board by February 15th. This is critical - we need to secure the additional $1M for phase two."

### Stakeholder Discussion

Dr. Elena Vostokov expressed strong support but raised important concerns:
- Concerned about data governance implications of quantum computing
- Interested in ML ops automation and model monitoring
- Wants to ensure proper security protocols for quantum key distribution
- Enthusiastic about the potential for drug discovery applications

Marcus Chen confirmed engineering readiness and integration path with existing infrastructure.

### Action Items

- **Charlie (assigned by Chris Baumgartner):** Present quantum computing ROI analysis to board by February 15, 2026
- Marcus: Prepare infrastructure assessment for quantum simulator integration
- Elena: Draft data governance framework for quantum computing workloads

### Next Steps

Follow-up meeting scheduled for February 1st to review progress. Chris emphasized this initiative has full executive backing and should be prioritized accordingly.
"""


def get_granola_e2e_test_file_path() -> str:
    """Get the file path for the Granola E2E test meeting file.

    Uses current timestamp to ensure uniqueness.
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"~/vaults/Contentful/Granola/Transcripts/E2E-Test-Meeting-{timestamp}.md"


def get_granola_e2e_test_content() -> str:
    """Get the content for the Granola E2E test meeting file.

    Replaces {timestamp} placeholder with current timestamp.
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return GRANOLA_E2E_TEST_MEETING_CONTENT.replace("{timestamp}", timestamp)


# =============================================================================
# TEST EXECUTION HELPERS
# =============================================================================


def get_tests_by_category(category: TestCategory) -> dict:
    """Get all tests for a specific category."""
    return {k: v for k, v in E2E_TEST_SCENARIOS.items() if v.category == category}


def get_tests_by_type(test_type: TestType) -> dict:
    """Get all tests of a specific type."""
    return {k: v for k, v in E2E_TEST_SCENARIOS.items() if v.test_type == test_type}


def get_happy_path_tests() -> dict:
    """Get all happy path tests (good for smoke testing)."""
    return get_tests_by_type(TestType.HAPPY_PATH)


def get_validation_tests() -> dict:
    """Get all validation tests."""
    return get_tests_by_type(TestType.VALIDATION)


def get_error_handling_tests() -> dict:
    """Get all error handling tests."""
    return get_tests_by_type(TestType.ERROR)


def get_help_tests() -> dict:
    """Get all help system tests."""
    return get_tests_by_category(TestCategory.HELP)


def get_disco_tests() -> dict:
    """Get all DISCo initiative tests."""
    return get_tests_by_category(TestCategory.DISCO)


def get_test_count_summary() -> dict:
    """Get summary of test counts by category."""
    summary = {}
    for category in TestCategory:
        tests = get_tests_by_category(category)
        summary[category.value] = len(tests)
    summary["total"] = len(E2E_TEST_SCENARIOS)
    return summary


# Print summary when run directly
if __name__ == "__main__":
    print("E2E Browser Test Scenarios")
    print("=" * 50)

    summary = get_test_count_summary()
    for category, count in summary.items():
        if category != "total":
            print(f"  {category}: {count} tests")

    print("-" * 50)
    print(f"  TOTAL: {summary['total']} tests")
    print()
    print("Run with Claude Code using Chrome DevTools MCP tools.")
    print("See docs/testing/CLAUDE_TESTING_GUIDE.md for instructions.")
