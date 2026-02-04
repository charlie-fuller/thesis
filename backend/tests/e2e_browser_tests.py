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
    DASHBOARD = "dashboard"
    PIPELINE = "pipeline"
    INTELLIGENCE = "intelligence"


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
    # =========================================================================
    # CHAT CONTEXT FILTERING (9 tests) - February 3, 2026 changes
    # =========================================================================
    "chat_project_filter_dropdown": E2ETestScenario(
        id="chat_project_filter_dropdown",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="Filter conversations by project dropdown",
        steps=[
            "Navigate to /chat",
            "Take snapshot to find sidebar",
            "Locate 'Project:' dropdown in sidebar header",
            "Click dropdown to expand options",
            "Verify dropdown shows 'None' option and project list",
            "Select a project from the dropdown",
            "Verify conversation list updates to show only project-filtered conversations",
        ],
        expected_result="Conversation list filters to show only conversations for selected project",
        prerequisites=["auth_login_success"],
    ),
    "chat_initiative_filter_dropdown": E2ETestScenario(
        id="chat_initiative_filter_dropdown",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="Filter conversations by initiative dropdown",
        steps=[
            "Navigate to /chat",
            "Take snapshot to find sidebar",
            "Locate 'Initiative:' dropdown in sidebar header",
            "Click dropdown to expand options",
            "Verify dropdown shows 'None' option and initiative list",
            "Select an initiative from the dropdown",
            "Verify conversation list updates to show only initiative-filtered conversations",
        ],
        expected_result="Conversation list filters to show only conversations for selected initiative",
        prerequisites=["auth_login_success"],
    ),
    "chat_context_badge_project": E2ETestScenario(
        id="chat_context_badge_project",
        category=TestCategory.CHAT,
        test_type=TestType.READ,
        description="Blue 'Proj' badge on conversation items with project context",
        steps=[
            "Navigate to /chat",
            "Take snapshot to find conversation items",
            "Look for conversation with project_id association",
            "Verify blue badge with project code or 'Proj' text visible",
            "Hover over badge to verify tooltip shows full project name",
        ],
        expected_result="Blue project badge displays on conversations with project context",
        prerequisites=["auth_login_success"],
    ),
    "chat_context_badge_initiative": E2ETestScenario(
        id="chat_context_badge_initiative",
        category=TestCategory.CHAT,
        test_type=TestType.READ,
        description="Purple 'Init' badge on conversation items with initiative context",
        steps=[
            "Navigate to /chat",
            "Take snapshot to find conversation items",
            "Look for conversation with initiative_id association",
            "Verify purple badge with 'Init' text visible",
            "Hover over badge to verify tooltip shows full initiative name",
        ],
        expected_result="Purple initiative badge displays on conversations with initiative context",
        prerequisites=["auth_login_success"],
    ),
    "chat_url_project_context": E2ETestScenario(
        id="chat_url_project_context",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="Navigate with project_id URL parameter",
        steps=[
            "Get a valid project ID from /api/projects",
            "Navigate to /chat?project_id={id}",
            "Verify Project dropdown shows the selected project",
            "Verify agent selector shows Project Agent selected",
            "Send a message",
            "Verify conversation is associated with project context",
        ],
        expected_result="URL parameter sets project context and auto-selects Project Agent",
        prerequisites=["auth_login_success"],
    ),
    "chat_url_initiative_context": E2ETestScenario(
        id="chat_url_initiative_context",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="Navigate with initiative_id URL parameter",
        steps=[
            "Get a valid initiative ID from /api/disco/initiatives",
            "Navigate to /chat?initiative_id={id}",
            "Verify Initiative dropdown shows the selected initiative",
            "Verify agent selector shows Initiative Agent selected",
            "Send a message",
            "Verify conversation is associated with initiative context",
        ],
        expected_result="URL parameter sets initiative context and auto-selects Initiative Agent",
        prerequisites=["auth_login_success"],
    ),
    "chat_new_conversation_with_context": E2ETestScenario(
        id="chat_new_conversation_with_context",
        category=TestCategory.CHAT,
        test_type=TestType.CREATE,
        description="New conversation inherits filter context",
        steps=[
            "Navigate to /chat",
            "Select a project from the Project dropdown",
            "Click 'New Chat' button",
            "Verify URL includes project_id parameter",
            "Send a message to create conversation",
            "Verify new conversation shows project badge",
        ],
        expected_result="New conversations inherit the currently selected filter context",
        prerequisites=["auth_login_success"],
    ),
    "chat_clear_project_filter": E2ETestScenario(
        id="chat_clear_project_filter",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="Clear filter returns to all conversations",
        steps=[
            "Navigate to /chat",
            "Select a project from the Project dropdown",
            "Verify filtered conversation list",
            "Change Project dropdown to 'None'",
            "Verify all conversations now visible (not filtered)",
        ],
        expected_result="Setting dropdown to None clears the filter and shows all conversations",
        prerequisites=["auth_login_success"],
    ),
    "chat_combined_filters": E2ETestScenario(
        id="chat_combined_filters",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="Both project and initiative filters together",
        steps=[
            "Navigate to /chat",
            "Select a project from the Project dropdown",
            "Select an initiative from the Initiative dropdown",
            "Verify conversation list shows only items matching BOTH filters",
            "Clear one filter",
            "Verify list updates to match remaining filter",
        ],
        expected_result="Combined filters work correctly with AND logic",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # NEW AGENTS (8 tests) - February 3, 2026 changes
    # =========================================================================
    "chat_project_agent_mention": E2ETestScenario(
        id="chat_project_agent_mention",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="@project_agent routes correctly",
        steps=[
            "Navigate to /chat",
            "Type '@project_agent what projects are we tracking?'",
            "Send message",
            "Wait for response",
            "Verify response is from Project Agent (check agent badge)",
        ],
        expected_result="@project_agent mention routes to Project Agent",
        prerequisites=["auth_login_success"],
    ),
    "chat_initiative_agent_mention": E2ETestScenario(
        id="chat_initiative_agent_mention",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="@initiative_agent routes correctly",
        steps=[
            "Navigate to /chat",
            "Type '@initiative_agent what initiatives are in discovery?'",
            "Send message",
            "Wait for response",
            "Verify response is from Initiative Agent (check agent badge)",
        ],
        expected_result="@initiative_agent mention routes to Initiative Agent",
        prerequisites=["auth_login_success"],
    ),
    "chat_project_agent_auto_select": E2ETestScenario(
        id="chat_project_agent_auto_select",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="Project Agent auto-selected when project context set",
        steps=[
            "Navigate to /chat?project_id={valid_id}",
            "Take snapshot of agent selector",
            "Verify 'Project Agent' is shown as selected agent",
            "Send a message without @mention",
            "Verify response is from Project Agent",
        ],
        expected_result="Project Agent is automatically selected with project context",
        prerequisites=["auth_login_success"],
    ),
    "chat_initiative_agent_auto_select": E2ETestScenario(
        id="chat_initiative_agent_auto_select",
        category=TestCategory.CHAT,
        test_type=TestType.FEATURE,
        description="Initiative Agent auto-selected when initiative context set",
        steps=[
            "Navigate to /chat?initiative_id={valid_id}",
            "Take snapshot of agent selector",
            "Verify 'Initiative Agent' is shown as selected agent",
            "Send a message without @mention",
            "Verify response is from Initiative Agent",
        ],
        expected_result="Initiative Agent is automatically selected with initiative context",
        prerequisites=["auth_login_success"],
    ),
    "agent_selector_shows_new_agents": E2ETestScenario(
        id="agent_selector_shows_new_agents",
        category=TestCategory.CHAT,
        test_type=TestType.READ,
        description="Both new agents appear in selector dropdown",
        steps=[
            "Navigate to /chat",
            "Click on agent selector dropdown",
            "Take snapshot of dropdown options",
            "Verify 'Project Agent' appears in the list",
            "Verify 'Initiative Agent' appears in the list",
        ],
        expected_result="Agent selector includes Project Agent and Initiative Agent",
        prerequisites=["auth_login_success"],
    ),
    "agent_icon_project_agent": E2ETestScenario(
        id="agent_icon_project_agent",
        category=TestCategory.CHAT,
        test_type=TestType.READ,
        description="Blue PieChart icon displays for Project Agent",
        steps=[
            "Navigate to /chat?project_id={valid_id}",
            "Take snapshot to view agent icon",
            "Verify Project Agent icon is PieChart",
            "Verify icon color is blue",
        ],
        expected_result="Project Agent displays with blue PieChart icon",
        prerequisites=["auth_login_success"],
    ),
    "agent_icon_initiative_agent": E2ETestScenario(
        id="agent_icon_initiative_agent",
        category=TestCategory.CHAT,
        test_type=TestType.READ,
        description="Purple CircleDot icon displays for Initiative Agent",
        steps=[
            "Navigate to /chat?initiative_id={valid_id}",
            "Take snapshot to view agent icon",
            "Verify Initiative Agent icon is CircleDot",
            "Verify icon color is purple",
        ],
        expected_result="Initiative Agent displays with purple CircleDot icon",
        prerequisites=["auth_login_success"],
    ),
    "intelligence_page_new_agents": E2ETestScenario(
        id="intelligence_page_new_agents",
        category=TestCategory.INTELLIGENCE,
        test_type=TestType.READ,
        description="Agents tab shows both new agents",
        steps=[
            "Navigate to /intelligence",
            "Click on 'Agents' tab",
            "Take snapshot of agents list",
            "Verify 'Project Agent' card is visible",
            "Verify 'Initiative Agent' card is visible",
            "Verify both show appropriate icons and descriptions",
        ],
        expected_result="Intelligence Agents tab displays Project Agent and Initiative Agent",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # DASHBOARD (12 tests) - February 3, 2026 changes
    # =========================================================================
    "dashboard_tab_order": E2ETestScenario(
        id="dashboard_tab_order",
        category=TestCategory.DASHBOARD,
        test_type=TestType.READ,
        description="Tabs display in correct order: System Health, Analytics, Process Map, Knowledge Graph",
        steps=[
            "Navigate to / (home/dashboard)",
            "Take snapshot to find tab navigation",
            "Verify tabs are in order: System Health, Analytics, Process Map, Knowledge Graph",
            "Click each tab to verify it's functional",
        ],
        expected_result="Dashboard tabs display in correct order",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_interface_health_in_analytics": E2ETestScenario(
        id="dashboard_interface_health_in_analytics",
        category=TestCategory.DASHBOARD,
        test_type=TestType.READ,
        description="InterfaceHealthPanel displays in Analytics tab",
        steps=[
            "Navigate to / (home/dashboard)",
            "Click 'Analytics' tab",
            "Take snapshot of tab content",
            "Verify InterfaceHealthPanel is visible",
            "Verify it shows interface health metrics",
        ],
        expected_result="Analytics tab contains InterfaceHealthPanel",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_discovery_panel_tasks_carousel": E2ETestScenario(
        id="dashboard_discovery_panel_tasks_carousel",
        category=TestCategory.DASHBOARD,
        test_type=TestType.FEATURE,
        description="Tasks prev/next navigation in Discovery Inbox",
        steps=[
            "Navigate to / (home/dashboard)",
            "Verify on System Health tab (default)",
            "Locate Discovery Inbox panel",
            "Find Tasks panel within Discovery Inbox",
            "If tasks exist, verify '1/N' counter is shown",
            "Click next arrow (>)",
            "Verify counter updates to '2/N'",
            "Click prev arrow (<)",
            "Verify counter returns to '1/N'",
        ],
        expected_result="Task carousel navigation works with counter display",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_discovery_panel_projects_carousel": E2ETestScenario(
        id="dashboard_discovery_panel_projects_carousel",
        category=TestCategory.DASHBOARD,
        test_type=TestType.FEATURE,
        description="Projects prev/next navigation in Discovery Inbox",
        steps=[
            "Navigate to / (home/dashboard)",
            "Locate Discovery Inbox panel",
            "Find Projects panel within Discovery Inbox",
            "If projects exist, verify counter is shown",
            "Test next and prev navigation",
        ],
        expected_result="Project carousel navigation works correctly",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_discovery_panel_stakeholders_carousel": E2ETestScenario(
        id="dashboard_discovery_panel_stakeholders_carousel",
        category=TestCategory.DASHBOARD,
        test_type=TestType.FEATURE,
        description="Stakeholders prev/next navigation in Discovery Inbox",
        steps=[
            "Navigate to / (home/dashboard)",
            "Locate Discovery Inbox panel",
            "Find Stakeholders panel within Discovery Inbox",
            "If stakeholders exist, verify counter is shown",
            "Test next and prev navigation",
        ],
        expected_result="Stakeholder carousel navigation works correctly",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_discovery_accept_task": E2ETestScenario(
        id="dashboard_discovery_accept_task",
        category=TestCategory.DASHBOARD,
        test_type=TestType.CREATE,
        description="Accept task candidate creates task",
        steps=[
            "Navigate to / (home/dashboard)",
            "Locate Discovery Inbox panel",
            "Find a task candidate",
            "Note the task title",
            "Click Accept button (green checkmark)",
            "Verify success toast appears",
            "Navigate to /tasks",
            "Verify new task exists with the noted title",
        ],
        expected_result="Accepted task candidate creates actual task",
        prerequisites=["auth_login_success"],
        cleanup=["Delete created test task"],
    ),
    "dashboard_discovery_skip_task": E2ETestScenario(
        id="dashboard_discovery_skip_task",
        category=TestCategory.DASHBOARD,
        test_type=TestType.DELETE,
        description="Skip/reject task candidate removes it",
        steps=[
            "Navigate to / (home/dashboard)",
            "Locate Discovery Inbox panel",
            "Find a task candidate",
            "Note the candidate count",
            "Click Skip button (red X)",
            "Verify success toast appears",
            "Verify candidate count decreased by 1",
        ],
        expected_result="Skipped candidate is removed from inbox",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_discovery_scanning_indicator": E2ETestScenario(
        id="dashboard_discovery_scanning_indicator",
        category=TestCategory.DASHBOARD,
        test_type=TestType.READ,
        description="Amber spinner displays during document scan",
        steps=[
            "Navigate to / (home/dashboard)",
            "Locate Discovery Inbox panel",
            "If scanning is active, verify amber spinner icon",
            "Verify 'Analyzing X more...' text is displayed",
        ],
        expected_result="Scanning indicator shows amber spinner with count",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_discovery_empty_state": E2ETestScenario(
        id="dashboard_discovery_empty_state",
        category=TestCategory.DASHBOARD,
        test_type=TestType.EMPTY_STATE,
        description="'All caught up' message when no candidates",
        steps=[
            "Navigate to / (home/dashboard)",
            "Locate Discovery Inbox panel",
            "If no candidates exist, verify 'All caught up - no items to review' message",
            "Verify green checkmark icon",
        ],
        expected_result="Empty state shows 'All caught up' message",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_system_health_tab": E2ETestScenario(
        id="dashboard_system_health_tab",
        category=TestCategory.DASHBOARD,
        test_type=TestType.READ,
        description="System Health tab is default and shows UnifiedDiscoveryPanel",
        steps=[
            "Navigate to / (home/dashboard)",
            "Verify 'System Health' tab is active (highlighted)",
            "Verify UnifiedDiscoveryPanel (Discovery Inbox) is visible",
        ],
        expected_result="System Health is default tab showing Discovery Inbox",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_knowledge_graph_subtabs": E2ETestScenario(
        id="dashboard_knowledge_graph_subtabs",
        category=TestCategory.DASHBOARD,
        test_type=TestType.READ,
        description="Knowledge Graph tab has Data, Visualization, What is this? subtabs",
        steps=[
            "Navigate to / (home/dashboard)",
            "Click 'Knowledge Graph' tab",
            "Verify subtab navigation appears",
            "Verify 'Data' subtab exists and is default",
            "Click 'Visualization' subtab",
            "Verify GraphVisualizationPanel appears",
            "Click 'What is this?' subtab",
            "Verify explanation content appears",
        ],
        expected_result="Knowledge Graph tab has three functional subtabs",
        prerequisites=["auth_login_success"],
    ),
    "dashboard_process_map_tab": E2ETestScenario(
        id="dashboard_process_map_tab",
        category=TestCategory.DASHBOARD,
        test_type=TestType.READ,
        description="Process Map tab displays ProcessMapPanel",
        steps=[
            "Navigate to / (home/dashboard)",
            "Click 'Process Map' tab",
            "Take snapshot of tab content",
            "Verify ProcessMapPanel is displayed",
        ],
        expected_result="Process Map tab shows ProcessMapPanel",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # HELP DOCUMENTATION (4 tests) - February 3, 2026 changes
    # =========================================================================
    "help_search_project_context": E2ETestScenario(
        id="help_search_project_context",
        category=TestCategory.HELP,
        test_type=TestType.READ,
        description="Help search returns project filter documentation",
        steps=[
            "Open help panel",
            "Type 'project context' or 'project filter' in search",
            "Wait for results",
            "Verify results mention filtering conversations by project",
            "Verify results mention the Project dropdown in sidebar",
        ],
        expected_result="Help search returns documentation about project context filtering",
        prerequisites=["auth_login_success"],
    ),
    "help_search_initiative_context": E2ETestScenario(
        id="help_search_initiative_context",
        category=TestCategory.HELP,
        test_type=TestType.READ,
        description="Help search returns initiative filter documentation",
        steps=[
            "Open help panel",
            "Type 'initiative context' or 'initiative filter' in search",
            "Wait for results",
            "Verify results mention filtering conversations by initiative",
            "Verify results mention the Initiative dropdown in sidebar",
        ],
        expected_result="Help search returns documentation about initiative context filtering",
        prerequisites=["auth_login_success"],
    ),
    "help_project_agent_mention": E2ETestScenario(
        id="help_project_agent_mention",
        category=TestCategory.HELP,
        test_type=TestType.READ,
        description="Help documents @project_agent mention syntax",
        steps=[
            "Open help panel",
            "Type 'project agent' in search",
            "Wait for results",
            "Verify results mention @project_agent syntax",
            "Verify results explain what Project Agent does",
        ],
        expected_result="Help search returns documentation about Project Agent",
        prerequisites=["auth_login_success"],
    ),
    "help_initiative_agent_mention": E2ETestScenario(
        id="help_initiative_agent_mention",
        category=TestCategory.HELP,
        test_type=TestType.READ,
        description="Help documents @initiative_agent mention syntax",
        steps=[
            "Open help panel",
            "Type 'initiative agent' in search",
            "Wait for results",
            "Verify results mention @initiative_agent syntax",
            "Verify results explain what Initiative Agent does",
        ],
        expected_result="Help search returns documentation about Initiative Agent",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # TASKS PAGE COMPREHENSIVE TESTS (11 tests)
    # =========================================================================
    "tasks_filter_by_assignee": E2ETestScenario(
        id="tasks_filter_by_assignee",
        category=TestCategory.TASKS,
        test_type=TestType.READ,
        description="Assignee dropdown filter",
        steps=[
            "Navigate to /tasks",
            "Locate assignee filter dropdown",
            "Click dropdown to expand options",
            "Select an assignee",
            "Verify only tasks assigned to that person are shown",
        ],
        expected_result="Tasks filtered by assignee",
        prerequisites=["auth_login_success"],
    ),
    "tasks_filter_by_due_date": E2ETestScenario(
        id="tasks_filter_by_due_date",
        category=TestCategory.TASKS,
        test_type=TestType.READ,
        description="Date range filter for due dates",
        steps=[
            "Navigate to /tasks",
            "Locate due date filter",
            "Select a date range (e.g., 'This Week')",
            "Verify only tasks within date range are shown",
        ],
        expected_result="Tasks filtered by due date range",
        prerequisites=["auth_login_success"],
    ),
    "tasks_filter_by_priority": E2ETestScenario(
        id="tasks_filter_by_priority",
        category=TestCategory.TASKS,
        test_type=TestType.READ,
        description="Priority checkbox filters",
        steps=[
            "Navigate to /tasks",
            "Locate priority filter checkboxes",
            "Check 'High' priority",
            "Verify only high priority tasks are shown",
            "Check additional priority levels",
            "Verify filter is cumulative",
        ],
        expected_result="Tasks filtered by priority level",
        prerequisites=["auth_login_success"],
    ),
    "tasks_filter_by_team": E2ETestScenario(
        id="tasks_filter_by_team",
        category=TestCategory.TASKS,
        test_type=TestType.READ,
        description="Team filter dropdown",
        steps=[
            "Navigate to /tasks",
            "Locate team filter dropdown",
            "Select a team",
            "Verify only tasks for that team are shown",
        ],
        expected_result="Tasks filtered by team",
        prerequisites=["auth_login_success"],
    ),
    "tasks_filter_by_project": E2ETestScenario(
        id="tasks_filter_by_project",
        category=TestCategory.TASKS,
        test_type=TestType.READ,
        description="URL param ?project= filters tasks",
        steps=[
            "Navigate to /tasks?project={project_id}",
            "Verify only tasks linked to that project are shown",
            "Verify project name is shown in filter indicator",
        ],
        expected_result="Tasks filtered by project URL parameter",
        prerequisites=["auth_login_success"],
    ),
    "tasks_search": E2ETestScenario(
        id="tasks_search",
        category=TestCategory.TASKS,
        test_type=TestType.READ,
        description="Search text input filters tasks",
        steps=[
            "Navigate to /tasks",
            "Locate search input",
            "Type a search term",
            "Verify tasks filter to show only matching titles/descriptions",
        ],
        expected_result="Tasks filtered by search query",
        prerequisites=["auth_login_success"],
    ),
    "tasks_toggle_completed": E2ETestScenario(
        id="tasks_toggle_completed",
        category=TestCategory.TASKS,
        test_type=TestType.FEATURE,
        description="Include Completed checkbox toggle",
        steps=[
            "Navigate to /tasks",
            "Locate 'Include Completed' checkbox",
            "Verify checkbox is unchecked by default",
            "Check the checkbox",
            "Verify completed tasks now appear in Done column",
        ],
        expected_result="Completed tasks visibility toggled",
        prerequisites=["auth_login_success"],
    ),
    "tasks_clear_filters": E2ETestScenario(
        id="tasks_clear_filters",
        category=TestCategory.TASKS,
        test_type=TestType.FEATURE,
        description="Clear all filters button",
        steps=[
            "Navigate to /tasks",
            "Apply multiple filters",
            "Locate 'Clear Filters' or reset button",
            "Click the button",
            "Verify all filters are reset to default",
        ],
        expected_result="All filters cleared to default state",
        prerequisites=["auth_login_success"],
    ),
    "tasks_edit_inline_assignee": E2ETestScenario(
        id="tasks_edit_inline_assignee",
        category=TestCategory.TASKS,
        test_type=TestType.UPDATE,
        description="Change assignee from task card",
        steps=[
            "Navigate to /tasks",
            "Click on a task card to open details",
            "Locate assignee field",
            "Change assignee to different person",
            "Save changes",
            "Verify assignee updated",
        ],
        expected_result="Task assignee changed inline",
        prerequisites=["auth_login_success"],
    ),
    "tasks_overdue_indicator": E2ETestScenario(
        id="tasks_overdue_indicator",
        category=TestCategory.TASKS,
        test_type=TestType.READ,
        description="Red overdue styling on past-due tasks",
        steps=[
            "Navigate to /tasks",
            "Find a task with past due date",
            "Verify due date displays in red/warning color",
            "Verify overdue indicator or badge is visible",
        ],
        expected_result="Overdue tasks show red warning styling",
        prerequisites=["auth_login_success"],
    ),
    "tasks_refresh_button": E2ETestScenario(
        id="tasks_refresh_button",
        category=TestCategory.TASKS,
        test_type=TestType.FEATURE,
        description="Refresh button reloads task list",
        steps=[
            "Navigate to /tasks",
            "Locate refresh button",
            "Click refresh button",
            "Verify loading state shown",
            "Verify task list reloads",
        ],
        expected_result="Refresh button reloads task data",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # PROJECTS PAGE COMPREHENSIVE TESTS (7 tests)
    # =========================================================================
    "projects_view_toggle": E2ETestScenario(
        id="projects_view_toggle",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.FEATURE,
        description="List/Tier view toggle",
        steps=[
            "Navigate to /projects",
            "Locate view toggle (List/Tier)",
            "Click to switch views",
            "Verify view changes between list and tier layout",
            "Toggle back and verify",
        ],
        expected_result="View toggles between List and Tier layouts",
        prerequisites=["auth_login_success"],
    ),
    "projects_active_only_toggle": E2ETestScenario(
        id="projects_active_only_toggle",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.FEATURE,
        description="Active Only checkbox filter",
        steps=[
            "Navigate to /projects",
            "Locate 'Active Only' checkbox",
            "Verify checkbox is checked by default",
            "Uncheck the checkbox",
            "Verify archived projects now appear",
        ],
        expected_result="Active Only toggle controls archived project visibility",
        prerequisites=["auth_login_success"],
    ),
    "projects_filter_by_initiative": E2ETestScenario(
        id="projects_filter_by_initiative",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.READ,
        description="Initiative filter dropdown",
        steps=[
            "Navigate to /projects",
            "Locate initiative filter dropdown",
            "Select an initiative",
            "Verify only projects linked to that initiative are shown",
        ],
        expected_result="Projects filtered by initiative",
        prerequisites=["auth_login_success"],
    ),
    "projects_sort_options": E2ETestScenario(
        id="projects_sort_options",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.READ,
        description="Sort dropdown options",
        steps=[
            "Navigate to /projects",
            "Locate sort dropdown",
            "Click to expand options",
            "Verify sort options include: Date, Name, Tier, Score",
            "Select each option and verify order changes",
        ],
        expected_result="Sort options work correctly",
        prerequisites=["auth_login_success"],
    ),
    "projects_reorder_buttons": E2ETestScenario(
        id="projects_reorder_buttons",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.UPDATE,
        description="Up/down reorder buttons",
        steps=[
            "Navigate to /projects",
            "Find a project card with reorder buttons",
            "Click up arrow to move project up",
            "Verify project position changes",
            "Click down arrow to move project down",
            "Verify position changes again",
        ],
        expected_result="Reorder buttons change project position",
        prerequisites=["auth_login_success"],
    ),
    "projects_detail_modal": E2ETestScenario(
        id="projects_detail_modal",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.READ,
        description="Click project to open detail modal",
        steps=[
            "Navigate to /projects",
            "Click on a project card",
            "Verify detail modal opens",
            "Verify modal shows project details (title, scores, description)",
            "Click close button or outside modal",
            "Verify modal closes",
        ],
        expected_result="Project detail modal opens and closes correctly",
        prerequisites=["auth_login_success"],
    ),
    "projects_confidence_indicator": E2ETestScenario(
        id="projects_confidence_indicator",
        category=TestCategory.OPPORTUNITIES,
        test_type=TestType.READ,
        description="Confidence bar display on project cards",
        steps=[
            "Navigate to /projects",
            "Find a project card",
            "Locate confidence indicator/bar",
            "Verify bar shows confidence level visually",
            "Verify tooltip or label shows confidence score",
        ],
        expected_result="Confidence indicator displays on project cards",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # MEETING ROOMS COMPREHENSIVE TESTS (11 tests)
    # =========================================================================
    "meeting_room_title_edit": E2ETestScenario(
        id="meeting_room_title_edit",
        category=TestCategory.MEETING,
        test_type=TestType.UPDATE,
        description="Inline title editing",
        steps=[
            "Navigate to /meeting-room",
            "Enter a meeting room",
            "Click on the room title",
            "Verify title becomes editable",
            "Change the title",
            "Click outside or press Enter",
            "Verify title is saved",
        ],
        expected_result="Meeting room title can be edited inline",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_room_export_to_kb": E2ETestScenario(
        id="meeting_room_export_to_kb",
        category=TestCategory.MEETING,
        test_type=TestType.FEATURE,
        description="Export to KB button",
        steps=[
            "Navigate to /meeting-room",
            "Enter a meeting room with messages",
            "Locate 'Export to KB' button",
            "Click the button",
            "Verify confirmation dialog or success toast",
            "Navigate to /kb",
            "Verify meeting transcript appears as document",
        ],
        expected_result="Meeting conversation exported to Knowledge Base",
        prerequisites=["auth_login_success", "meeting_send_message"],
    ),
    "meeting_room_participant_bar": E2ETestScenario(
        id="meeting_room_participant_bar",
        category=TestCategory.MEETING,
        test_type=TestType.READ,
        description="Agent participant list bar",
        steps=[
            "Navigate to /meeting-room",
            "Enter a meeting room",
            "Locate participant bar showing agents",
            "Verify all room agents are displayed with icons",
            "Verify agent count matches room configuration",
        ],
        expected_result="Participant bar shows all room agents",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_room_autonomous_panel": E2ETestScenario(
        id="meeting_room_autonomous_panel",
        category=TestCategory.MEETING,
        test_type=TestType.READ,
        description="Autonomous mode panel UI elements",
        steps=[
            "Navigate to /meeting-room",
            "Enter a meeting room",
            "Locate autonomous mode panel",
            "Verify panel shows topic input",
            "Verify Start/Stop buttons visible",
            "Verify turn count controls visible",
        ],
        expected_result="Autonomous panel displays all control elements",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_room_autonomous_start_stop": E2ETestScenario(
        id="meeting_room_autonomous_start_stop",
        category=TestCategory.MEETING,
        test_type=TestType.FEATURE,
        description="Start/Stop autonomous discussion buttons",
        steps=[
            "Navigate to /meeting-room",
            "Enter a meeting room",
            "Enter a topic in autonomous panel",
            "Click Start button",
            "Verify agents begin discussing",
            "Click Stop button",
            "Verify discussion stops",
        ],
        expected_result="Autonomous discussion starts and stops on command",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_room_user_interjection": E2ETestScenario(
        id="meeting_room_user_interjection",
        category=TestCategory.MEETING,
        test_type=TestType.FEATURE,
        description="User message during autonomous mode",
        steps=[
            "Start autonomous discussion",
            "While agents are discussing, type a message",
            "Send the message",
            "Verify user message appears in conversation",
            "Verify agents respond to user interjection",
        ],
        expected_result="User can interject during autonomous discussion",
        prerequisites=["auth_login_success", "meeting_room_autonomous_start_stop"],
    ),
    "meeting_room_context_sources": E2ETestScenario(
        id="meeting_room_context_sources",
        category=TestCategory.MEETING,
        test_type=TestType.READ,
        description="KB/Graph sources on messages",
        steps=[
            "Enter a meeting room",
            "Send a message that triggers KB lookup",
            "Wait for agent response",
            "Look for source citations in response",
            "Verify sources show KB document names or graph references",
        ],
        expected_result="Agent responses show context sources",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_room_token_counter": E2ETestScenario(
        id="meeting_room_token_counter",
        category=TestCategory.MEETING,
        test_type=TestType.READ,
        description="Token usage counter display",
        steps=[
            "Enter a meeting room",
            "Locate token counter (usually in footer or header)",
            "Send a message",
            "Verify token count increases after response",
        ],
        expected_result="Token counter tracks usage",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_room_back_button": E2ETestScenario(
        id="meeting_room_back_button",
        category=TestCategory.MEETING,
        test_type=TestType.FEATURE,
        description="Back navigation from meeting room",
        steps=[
            "Navigate to /meeting-room",
            "Enter a meeting room",
            "Locate back button or arrow",
            "Click back button",
            "Verify navigation returns to meeting room list",
        ],
        expected_result="Back button returns to meeting room list",
        prerequisites=["auth_login_success", "meeting_create"],
    ),
    "meeting_rooms_context_filter": E2ETestScenario(
        id="meeting_rooms_context_filter",
        category=TestCategory.MEETING,
        test_type=TestType.READ,
        description="Project/initiative context filtering",
        steps=[
            "Navigate to /meeting-room",
            "Locate context filter dropdown",
            "Select a project or initiative",
            "Verify meeting rooms list filters to show only matching rooms",
        ],
        expected_result="Meeting rooms can be filtered by project/initiative",
        prerequisites=["auth_login_success"],
    ),
    "chat_meeting_rooms_create_from_tab": E2ETestScenario(
        id="chat_meeting_rooms_create_from_tab",
        category=TestCategory.CHAT,
        test_type=TestType.CREATE,
        description="Create meeting room from Chat Meeting Rooms tab",
        steps=[
            "Navigate to /chat",
            "Click 'Meeting Rooms' tab",
            "Click 'New Meeting Room' button",
            "Fill in room details",
            "Select agents",
            "Click create",
            "Verify room is created",
        ],
        expected_result="Meeting room created from chat interface",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # DISCO PAGE COMPREHENSIVE TESTS (9 tests)
    # =========================================================================
    "disco_workflow_map_tab": E2ETestScenario(
        id="disco_workflow_map_tab",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="Workflow Map tab displays",
        steps=[
            "Navigate to /disco",
            "Look for Workflow Map or view toggle",
            "Click to show workflow map view",
            "Verify workflow stages are displayed visually",
            "Verify initiatives are positioned in correct stages",
        ],
        expected_result="Workflow map shows initiatives in workflow stages",
        prerequisites=["auth_login_success"],
    ),
    "disco_status_summary_cards": E2ETestScenario(
        id="disco_status_summary_cards",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="Status filter summary cards",
        steps=[
            "Navigate to /disco",
            "Locate status summary cards (Draft, Triaged, etc.)",
            "Verify each status shows count",
            "Click on a status card",
            "Verify list filters to show only that status",
        ],
        expected_result="Status cards filter initiatives when clicked",
        prerequisites=["auth_login_success"],
    ),
    "disco_initiative_search": E2ETestScenario(
        id="disco_initiative_search",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="Search input filters initiatives",
        steps=[
            "Navigate to /disco",
            "Locate search input",
            "Type a search term",
            "Verify initiative list filters to matching items",
        ],
        expected_result="Search filters initiatives by name/description",
        prerequisites=["auth_login_success"],
    ),
    "disco_initiative_card_click": E2ETestScenario(
        id="disco_initiative_card_click",
        category=TestCategory.DISCO,
        test_type=TestType.FEATURE,
        description="Click initiative card navigates to detail",
        steps=[
            "Navigate to /disco",
            "Click on an initiative card",
            "Verify navigation to /disco/{id} detail page",
            "Verify initiative details are displayed",
        ],
        expected_result="Clicking card navigates to initiative detail",
        prerequisites=["auth_login_success", "disco_create_initiative"],
    ),
    "disco_triage_recommendation_badge": E2ETestScenario(
        id="disco_triage_recommendation_badge",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="GO/NO-GO/INVESTIGATE badge on triaged initiatives",
        steps=[
            "Navigate to /disco",
            "Find a triaged initiative",
            "Locate the recommendation badge",
            "Verify badge shows GO (green), NO-GO (red), or INVESTIGATE (amber)",
        ],
        expected_result="Triage recommendation badge displays correctly",
        prerequisites=["auth_login_success", "disco_run_agent"],
    ),
    "disco_detail_documents_tab": E2ETestScenario(
        id="disco_detail_documents_tab",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="Documents tab in initiative detail",
        steps=[
            "Navigate to initiative detail page",
            "Click 'Documents' tab",
            "Verify linked documents are listed",
            "Verify 'Link from KB' button is present",
            "Verify 'Upload' button is present",
        ],
        expected_result="Documents tab shows linked documents with actions",
        prerequisites=["auth_login_success", "disco_create_initiative"],
    ),
    "disco_detail_run_agent_tab": E2ETestScenario(
        id="disco_detail_run_agent_tab",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="Run Agent tab UI elements",
        steps=[
            "Navigate to initiative detail page",
            "Click 'Run Agent' tab",
            "Verify agent dropdown is present",
            "Verify 'Run' button is present",
            "Verify guidance panel shows next recommended agent",
        ],
        expected_result="Run Agent tab has dropdown, run button, and guidance",
        prerequisites=["auth_login_success", "disco_create_initiative"],
    ),
    "disco_detail_outputs_tab": E2ETestScenario(
        id="disco_detail_outputs_tab",
        category=TestCategory.DISCO,
        test_type=TestType.READ,
        description="Outputs tab shows agent results",
        steps=[
            "Navigate to initiative detail page (with previous agent runs)",
            "Click 'Outputs' tab",
            "Verify list of agent outputs is displayed",
            "Click on an output to expand",
            "Verify output content is shown",
        ],
        expected_result="Outputs tab displays expandable agent results",
        prerequisites=["auth_login_success", "disco_run_agent"],
    ),
    "disco_detail_chat_tab": E2ETestScenario(
        id="disco_detail_chat_tab",
        category=TestCategory.DISCO,
        test_type=TestType.FEATURE,
        description="Chat tab or button with initiative context",
        steps=[
            "Navigate to initiative detail page",
            "Click 'Chat' button in header",
            "Verify redirect to /chat?initiative_id={id}",
            "Verify Initiative Agent is selected",
            "Send a message",
            "Verify response has initiative context",
        ],
        expected_result="Chat button opens chat with initiative context",
        prerequisites=["auth_login_success", "disco_create_initiative"],
    ),
    # =========================================================================
    # KNOWLEDGE BASE COMPREHENSIVE TESTS (5 tests)
    # =========================================================================
    "kb_conversations_tab": E2ETestScenario(
        id="kb_conversations_tab",
        category=TestCategory.KB,
        test_type=TestType.READ,
        description="Conversations tab in KB",
        steps=[
            "Navigate to /kb",
            "Locate tab navigation",
            "Click 'Conversations' tab",
            "Verify conversations added to KB are listed",
            "Verify conversation preview is available",
        ],
        expected_result="KB Conversations tab shows indexed conversations",
        prerequisites=["auth_login_success"],
    ),
    "kb_data_map_tab": E2ETestScenario(
        id="kb_data_map_tab",
        category=TestCategory.KB,
        test_type=TestType.READ,
        description="Data Map tab visualization",
        steps=[
            "Navigate to /kb",
            "Click 'Data Map' tab (if present)",
            "Verify data visualization or map is displayed",
            "Verify documents are represented visually",
        ],
        expected_result="Data Map tab shows document visualization",
        prerequisites=["auth_login_success"],
    ),
    "kb_upload_multiple_types": E2ETestScenario(
        id="kb_upload_multiple_types",
        category=TestCategory.KB,
        test_type=TestType.CREATE,
        description="Upload PDF, DOCX, XLSX, PPTX files",
        steps=[
            "Navigate to /kb",
            "Click upload button",
            "Upload a PDF file",
            "Verify PDF appears in document list",
            "Repeat for DOCX, XLSX, PPTX",
            "Verify all file types are accepted and processed",
        ],
        expected_result="Multiple document types upload successfully",
        prerequisites=["auth_login_success"],
    ),
    "kb_document_classification": E2ETestScenario(
        id="kb_document_classification",
        category=TestCategory.KB,
        test_type=TestType.READ,
        description="Auto-classification display on documents",
        steps=[
            "Navigate to /kb",
            "Find an uploaded document",
            "Verify classification tags/badges are displayed",
            "Verify document type is shown",
        ],
        expected_result="Documents show auto-classification metadata",
        prerequisites=["auth_login_success", "kb_upload_pdf"],
    ),
    "kb_agent_filter": E2ETestScenario(
        id="kb_agent_filter",
        category=TestCategory.KB,
        test_type=TestType.READ,
        description="Filter documents by agent association",
        steps=[
            "Navigate to /kb",
            "Locate agent filter dropdown",
            "Select an agent (e.g., Guardian, Capital)",
            "Verify documents filter to show agent-relevant docs",
        ],
        expected_result="Documents filter by associated agent domain",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # PIPELINE PAGE TESTS (7 tests)
    # =========================================================================
    "pipeline_priority_queue": E2ETestScenario(
        id="pipeline_priority_queue",
        category=TestCategory.PIPELINE,
        test_type=TestType.READ,
        description="Priority Queue panel displays",
        steps=[
            "Navigate to /pipeline",
            "Locate Priority Queue panel",
            "Verify queue items are displayed in priority order",
            "Verify each item shows priority score",
        ],
        expected_result="Priority Queue panel shows ordered items",
        prerequisites=["auth_login_success"],
    ),
    "pipeline_commitments_panel": E2ETestScenario(
        id="pipeline_commitments_panel",
        category=TestCategory.PIPELINE,
        test_type=TestType.READ,
        description="Commitments panel with due dates",
        steps=[
            "Navigate to /pipeline",
            "Locate Commitments panel",
            "Verify commitments are listed with due dates",
            "Verify overdue items are highlighted",
        ],
        expected_result="Commitments panel shows items with due dates",
        prerequisites=["auth_login_success"],
    ),
    "pipeline_stakeholder_pulse": E2ETestScenario(
        id="pipeline_stakeholder_pulse",
        category=TestCategory.PIPELINE,
        test_type=TestType.READ,
        description="Stakeholder engagement pulse",
        steps=[
            "Navigate to /pipeline",
            "Locate stakeholder engagement section",
            "Verify engagement levels are displayed",
            "Verify recent interactions are shown",
        ],
        expected_result="Stakeholder pulse shows engagement data",
        prerequisites=["auth_login_success"],
    ),
    "pipeline_department_filter": E2ETestScenario(
        id="pipeline_department_filter",
        category=TestCategory.PIPELINE,
        test_type=TestType.READ,
        description="Department dropdown filter",
        steps=[
            "Navigate to /pipeline",
            "Locate department filter dropdown",
            "Select a department",
            "Verify pipeline items filter to that department",
        ],
        expected_result="Pipeline filters by department",
        prerequisites=["auth_login_success"],
    ),
    "pipeline_granola_scan_button": E2ETestScenario(
        id="pipeline_granola_scan_button",
        category=TestCategory.PIPELINE,
        test_type=TestType.FEATURE,
        description="Granola scan trigger button",
        steps=[
            "Navigate to /pipeline or dashboard",
            "Locate Granola/scan panel",
            "Click Scan button",
            "Verify scanning indicator appears",
            "Wait for scan to complete",
            "Verify results update",
        ],
        expected_result="Granola scan button triggers document scan",
        prerequisites=["auth_login_success"],
    ),
    "pipeline_stats_row": E2ETestScenario(
        id="pipeline_stats_row",
        category=TestCategory.PIPELINE,
        test_type=TestType.READ,
        description="Stats cards display",
        steps=[
            "Navigate to /pipeline",
            "Locate stats row/cards at top",
            "Verify cards show counts (e.g., Active Projects, Tasks, etc.)",
            "Verify numbers update when data changes",
        ],
        expected_result="Stats cards show current counts",
        prerequisites=["auth_login_success"],
    ),
    "pipeline_click_to_navigate": E2ETestScenario(
        id="pipeline_click_to_navigate",
        category=TestCategory.PIPELINE,
        test_type=TestType.FEATURE,
        description="Click item navigates to detail",
        steps=[
            "Navigate to /pipeline",
            "Click on a project or task item",
            "Verify navigation to item detail page",
            "Verify correct item is displayed",
        ],
        expected_result="Clicking items navigates to their detail pages",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # INTELLIGENCE PAGE TESTS (6 tests)
    # =========================================================================
    "intelligence_strategy_tab": E2ETestScenario(
        id="intelligence_strategy_tab",
        category=TestCategory.INTELLIGENCE,
        test_type=TestType.READ,
        description="Strategy tab is default on Intelligence page",
        steps=[
            "Navigate to /intelligence",
            "Verify 'Strategy' tab is active by default",
            "Verify strategy content is displayed",
        ],
        expected_result="Strategy tab is default view",
        prerequisites=["auth_login_success"],
    ),
    "intelligence_stakeholder_view_toggle": E2ETestScenario(
        id="intelligence_stakeholder_view_toggle",
        category=TestCategory.INTELLIGENCE,
        test_type=TestType.FEATURE,
        description="Grid/By Team view toggle for stakeholders",
        steps=[
            "Navigate to /intelligence",
            "Click 'Stakeholders' tab",
            "Locate view toggle (Grid/By Team)",
            "Click to toggle view",
            "Verify layout changes between grid and team grouping",
        ],
        expected_result="Stakeholder view toggles between grid and team layouts",
        prerequisites=["auth_login_success"],
    ),
    "intelligence_stakeholder_create_form": E2ETestScenario(
        id="intelligence_stakeholder_create_form",
        category=TestCategory.INTELLIGENCE,
        test_type=TestType.CREATE,
        description="Add Stakeholder form",
        steps=[
            "Navigate to /intelligence",
            "Click 'Stakeholders' tab",
            "Click 'Add Stakeholder' button",
            "Fill in name, role, department",
            "Click save/create",
            "Verify stakeholder appears in list",
        ],
        expected_result="New stakeholder created via form",
        prerequisites=["auth_login_success"],
        cleanup=["Delete test stakeholder"],
    ),
    "intelligence_stakeholder_delete": E2ETestScenario(
        id="intelligence_stakeholder_delete",
        category=TestCategory.INTELLIGENCE,
        test_type=TestType.DELETE,
        description="Delete stakeholder",
        steps=[
            "Navigate to /intelligence",
            "Click 'Stakeholders' tab",
            "Click on a stakeholder to open detail",
            "Click delete button",
            "Confirm deletion",
            "Verify stakeholder removed from list",
        ],
        expected_result="Stakeholder deleted successfully",
        prerequisites=["auth_login_success", "intelligence_stakeholder_create_form"],
    ),
    "intelligence_engagement_trends_chart": E2ETestScenario(
        id="intelligence_engagement_trends_chart",
        category=TestCategory.INTELLIGENCE,
        test_type=TestType.READ,
        description="Engagement trends chart display",
        steps=[
            "Navigate to /intelligence",
            "Locate engagement trends section",
            "Verify chart or visualization is displayed",
            "Verify trend data is shown over time",
        ],
        expected_result="Engagement trends chart displays data",
        prerequisites=["auth_login_success"],
    ),
    "intelligence_agent_card_navigation": E2ETestScenario(
        id="intelligence_agent_card_navigation",
        category=TestCategory.INTELLIGENCE,
        test_type=TestType.FEATURE,
        description="Agent card click navigates to chat",
        steps=[
            "Navigate to /intelligence",
            "Click 'Agents' tab",
            "Click on an agent card",
            "Verify navigation to /chat with that agent selected",
        ],
        expected_result="Clicking agent card opens chat with agent",
        prerequisites=["auth_login_success"],
    ),
    # =========================================================================
    # CHAT TAB SYSTEM TESTS (2 tests)
    # =========================================================================
    "chat_tab_system": E2ETestScenario(
        id="chat_tab_system",
        category=TestCategory.CHAT,
        test_type=TestType.READ,
        description="Chat/Meeting Rooms tabs in chat interface",
        steps=[
            "Navigate to /chat",
            "Locate tab navigation (Chat, Meeting Rooms)",
            "Verify 'Chat' tab is active by default",
            "Click 'Meeting Rooms' tab",
            "Verify meeting rooms list is displayed",
            "Click 'Chat' tab",
            "Verify conversations list returns",
        ],
        expected_result="Chat interface has working Chat and Meeting Rooms tabs",
        prerequisites=["auth_login_success"],
    ),
    "chat_sidebar_meeting_rooms_list": E2ETestScenario(
        id="chat_sidebar_meeting_rooms_list",
        category=TestCategory.CHAT,
        test_type=TestType.READ,
        description="Meeting Rooms tab shows room list",
        steps=[
            "Navigate to /chat",
            "Click 'Meeting Rooms' tab",
            "Verify meeting rooms are listed",
            "Click on a meeting room",
            "Verify navigation to that room",
        ],
        expected_result="Meeting Rooms tab lists and links to rooms",
        prerequisites=["auth_login_success", "meeting_create"],
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


def get_dashboard_tests() -> dict:
    """Get all dashboard tests."""
    return get_tests_by_category(TestCategory.DASHBOARD)


def get_pipeline_tests() -> dict:
    """Get all pipeline tests."""
    return get_tests_by_category(TestCategory.PIPELINE)


def get_intelligence_tests() -> dict:
    """Get all intelligence page tests."""
    return get_tests_by_category(TestCategory.INTELLIGENCE)


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
