# Comprehensive E2E Browser Tests

Run a complete end-to-end test of all Thesis application functionality using Chrome DevTools MCP on production.

## Usage

```
/e2e-full              # Run all E2E tests on production
/e2e-full --cleanup    # Only run cleanup of test data
```

## Prerequisites

1. **Chrome DevTools MCP** - Chrome browser must be open with DevTools MCP connected
2. **Authentication** - You should be logged into thesis-mvp.vercel.app in Chrome

## Test Configuration

- **Production URL**: https://thesis-mvp.vercel.app
- **Test Data Prefix**: All test data uses "E2E Test" prefix for easy identification and cleanup

## Instructions

Execute ALL test scenarios in order. After each test, record PASS/FAIL. At the end, clean up all test data.

---

## PHASE 1: AUTHENTICATION & NAVIGATION

### Test 1.1: Verify Authentication State

*Purpose:* Confirm user is logged in

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app`
2. `mcp__chrome-devtools__take_snapshot`
3. Look for "User menu" button (indicates logged in) or login form
4. If login form visible:
   - Fill email and password fields
   - Click login button
   - Wait for dashboard to load
5. If user menu visible: PASS

*Expected:* User is authenticated with access to all app sections

---

### Test 1.2: Navigation Bar Verification

*Purpose:* Verify all navigation links are present and functional

Steps:
1. `mcp__chrome-devtools__take_snapshot` on any page
2. Verify presence of navigation links:
   - Dashboard
   - Chat
   - Tasks
   - Projects
   - Intelligence
   - Agents
   - KB
   - DISCo
3. Click each link and verify page loads without error

*Expected:* All navigation links present and functional

---

## PHASE 2: DASHBOARD

### Test 2.1: Dashboard Load

*Purpose:* Verify dashboard displays correctly

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/`
2. `mcp__chrome-devtools__take_snapshot`
3. Verify dashboard content loads (widgets, stats, or welcome message)
4. Check for any error messages in console with `mcp__chrome-devtools__list_console_messages`

*Expected:* Dashboard loads without errors, displays relevant content

---

## PHASE 3: CHAT & AI AGENTS

### Test 3.1: New Chat Creation

*Purpose:* Verify chat interface works

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/chat`
2. `mcp__chrome-devtools__take_snapshot`
3. Find and click "+ New Chat" button
4. Verify chat interface shows with message input

*Expected:* New chat created, ready for input

---

### Test 3.2: Send Message and Receive Response

*Purpose:* Verify AI agent responds to messages

Steps:
1. In chat interface, find message textbox ("Type your message...")
2. `mcp__chrome-devtools__fill` with: "E2E Test: Hello, this is an automated test message. Please acknowledge."
3. `mcp__chrome-devtools__click` Send button or press Enter
4. Wait for AI response (look for new message bubble from agent)
5. `mcp__chrome-devtools__take_snapshot` to verify response appeared

*Expected:* Message sent, AI agent responds with acknowledgment

---

### Test 3.3: KB Context Chat (CRITICAL)

*Purpose:* Verify chat uses Knowledge Base for context-aware responses

Steps:
1. Click "+ New Chat" to start fresh conversation
2. `mcp__chrome-devtools__take_snapshot` to get message input element
3. `mcp__chrome-devtools__fill` with: "E2E KB Test: What are the key topics and themes from the documents added to the Knowledge Base in the last week? Please cite specific documents."
4. `mcp__chrome-devtools__click` Send button
5. Wait for response (may take 10-15 seconds for KB search + AI response)
6. `mcp__chrome-devtools__take_snapshot` to capture response
7. **Verify response contains:**
   - References to specific KB documents (filenames or titles)
   - Relevance scores (if visible)
   - Actual content/themes from documents
   - Agent attribution (e.g., "Atlas" or similar)

*Expected:*
- Agent searches KB and finds relevant documents
- Response cites specific documents from KB
- Content reflects actual document themes (not generic response)

*Pass Criteria:*
- At least 1 document cited in response
- Document names/dates appear to be real (not made up)
- Response contains substantive content from KB

---

### Test 3.4: Agent Selection

*Purpose:* Verify agent selection works

Steps:
1. `mcp__chrome-devtools__take_snapshot`
2. Find "Agent:" selector or "Auto" button
3. `mcp__chrome-devtools__click` to open agent selection
4. Verify list of agents appears
5. Select a specific agent (e.g., "Atlas" for research)
6. Send a message: "E2E Agent Test: Brief research summary on AI trends"
7. Verify response comes from selected agent

*Expected:* Agent selection changes which AI responds

---

### Test 3.5: Chat Conversation Actions

*Purpose:* Verify chat list actions work

Steps:
1. `mcp__chrome-devtools__take_snapshot` to find chat list
2. Locate "Rename" button for a test conversation
3. Click Rename
4. Change name to "E2E Renamed Conversation"
5. Verify name updates in list
6. Test Archive button (if present)

*Expected:* Rename and archive actions work correctly

---

## PHASE 4: TASKS (KANBAN)

### Test 4.1: View Tasks Board

*Purpose:* Verify Kanban board loads

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/tasks`
2. `mcp__chrome-devtools__take_snapshot`
3. Verify presence of Kanban columns:
   - To Do
   - In Progress
   - Done (or similar)
4. Note current task counts per column

*Expected:* Kanban board displays with status columns

---

### Test 4.2: Create New Task

*Purpose:* Verify task creation

Steps:
1. Find and click "Add Task" or "+" button
2. `mcp__chrome-devtools__take_snapshot` to find modal/form
3. Fill in task details:
   - Title: "E2E Test Task - Full Suite Verification"
   - Description: "Automated test task for E2E verification"
4. Click Create/Save button
5. `mcp__chrome-devtools__wait_for` task to appear in To Do column
6. Verify task count increased

*Expected:* New task created in To Do column

---

### Test 4.3: Drag Task to In Progress

*Purpose:* Verify drag-and-drop status change

Steps:
1. `mcp__chrome-devtools__take_snapshot`
2. Find the "E2E Test Task" heading element
3. Find the "In Progress" column target
4. `mcp__chrome-devtools__drag` from task to In Progress column
5. `mcp__chrome-devtools__take_snapshot` to verify position changed
6. Click Refresh button to reload from database
7. Verify task persisted in In Progress column

*Expected:* Task moves to In Progress, persists after refresh

---

### Test 4.4: Task Details Modal

*Purpose:* Verify task editing

Steps:
1. Click on the E2E test task card to open details
2. `mcp__chrome-devtools__take_snapshot` to capture modal
3. Verify details are displayed:
   - Title
   - Description
   - Status
   - Priority (if applicable)
4. Close modal

*Expected:* Task details modal opens with correct information

---

## PHASE 5: PROJECTS

### Test 5.1: View Projects List

*Purpose:* Verify projects page loads

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/projects`
2. `mcp__chrome-devtools__take_snapshot`
3. Verify projects list or pipeline view displays
4. Note current project count

*Expected:* Projects page loads with list/pipeline view

---

### Test 5.2: Create New Project

*Purpose:* Verify project creation

Steps:
1. Find and click "Add Project" or "New Project" button
2. `mcp__chrome-devtools__take_snapshot` to find form
3. Fill in project details:
   - Name: "E2E Test Project - Automated Verification"
   - Description: "Test project for E2E suite"
   - Status: Discovery (or first status option)
4. Click Create button
5. Verify project appears in list

*Expected:* New project created and visible

---

### Test 5.3: Project Pipeline/Status View

*Purpose:* Verify project status pipeline

Steps:
1. Look for pipeline/kanban view of projects
2. Verify status columns (Discovery, Evaluation, Proposal, etc.)
3. Verify E2E test project appears in correct status column

*Expected:* Pipeline view shows projects by status

---

## PHASE 6: KNOWLEDGE BASE

### Test 6.1: KB Page Load

*Purpose:* Verify Knowledge Base interface

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/kb`
2. `mcp__chrome-devtools__take_snapshot`
3. Verify KB interface displays:
   - Document list or navigator
   - Search functionality
   - Document preview area

*Expected:* KB page loads with document browser

---

### Test 6.2: KB Navigator Search

*Purpose:* Verify KB search functionality

Steps:
1. Find KB Navigator section (may need to expand)
2. `mcp__chrome-devtools__take_snapshot` to find search input
3. `mcp__chrome-devtools__fill` search input with: "AI"
4. Wait for search results
5. `mcp__chrome-devtools__take_snapshot`
6. Verify search returns relevant documents

*Expected:* Search filters documents by query

---

### Test 6.3: Document Preview

*Purpose:* Verify document preview works

Steps:
1. Click on a document in the list
2. `mcp__chrome-devtools__take_snapshot`
3. Verify document preview displays:
   - Document title
   - Content or summary
   - Metadata (tags, dates, etc.)

*Expected:* Document preview shows content

---

### Test 6.4: Tag Filtering

*Purpose:* Verify tag-based filtering

Steps:
1. Find tag filter dropdown or chips
2. Select a tag to filter by
3. Verify document list updates to show only tagged documents
4. Clear filter and verify all documents return

*Expected:* Tag filtering works correctly

---

## PHASE 7: AGENTS

### Test 7.1: Agents Directory

*Purpose:* Verify agents page displays all agents

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/agents`
2. `mcp__chrome-devtools__take_snapshot`
3. Verify agent cards/list displays
4. Look for agent categories or groupings
5. Verify at least these key agents are visible:
   - Atlas (Research)
   - Compass (Strategy)
   - Capital (Finance)
   - Guardian (IT/Security)

*Expected:* Agents page shows full agent roster

---

### Test 7.2: Agent Details

*Purpose:* Verify agent details view

Steps:
1. Click on an agent card to view details
2. `mcp__chrome-devtools__take_snapshot`
3. Verify agent details display:
   - Agent name and icon
   - Description/capabilities
   - Start chat option

*Expected:* Agent details view shows capabilities

---

## PHASE 8: INTELLIGENCE

### Test 8.1: Intelligence Dashboard

*Purpose:* Verify intelligence/analytics page

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/intelligence`
2. `mcp__chrome-devtools__take_snapshot`
3. Verify intelligence content displays:
   - Charts/graphs
   - Insights
   - Analytics data

*Expected:* Intelligence page loads with data visualizations

---

## PHASE 9: DISCo

### Test 9.1: DISCo Page Load

*Purpose:* Verify DISCo (Discovery-Insights-Synthesis-Capabilities) interface

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/disco`
2. `mcp__chrome-devtools__take_snapshot`
3. Verify DISCo interface displays:
   - Initiatives list or dashboard
   - Create/manage options

*Expected:* DISCo page loads with interface

---

## PHASE 10: MEETING ROOMS

### Test 10.1: Meeting Rooms Interface

*Purpose:* Verify meeting rooms feature

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/chat`
2. `mcp__chrome-devtools__take_snapshot`
3. Find and click "Meeting Rooms" tab/button
4. `mcp__chrome-devtools__take_snapshot`
5. Verify meeting rooms list or creation interface

*Expected:* Meeting rooms interface accessible

---

## PHASE 11: ADMIN HELP

### Test 11.1: Help Panel

*Purpose:* Verify help functionality

Steps:
1. On any page, find Admin Help panel (usually right side)
2. `mcp__chrome-devtools__take_snapshot`
3. Verify help panel shows:
   - How can I help?
   - Quick action buttons
   - Ask a question input

*Expected:* Help panel visible and functional

---

### Test 11.2: Help Question

*Purpose:* Verify help responds to questions

Steps:
1. Find help textbox ("Ask a question...")
2. `mcp__chrome-devtools__fill` with: "How do I create a new task?"
3. Submit the question
4. Wait for response
5. Verify helpful response appears

*Expected:* Help provides relevant guidance

---

## PHASE 12: CLEANUP

### Cleanup 12.1: Delete Test Conversations

*Purpose:* Remove all E2E test conversations

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/chat`
2. `mcp__chrome-devtools__take_snapshot`
3. For each conversation containing "E2E" in the title:
   - Find Delete button
   - Click Delete
   - Confirm deletion in dialog
4. Repeat until no E2E conversations remain

*Expected:* All E2E test conversations deleted

---

### Cleanup 12.2: Delete Test Tasks

*Purpose:* Remove all E2E test tasks

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/tasks`
2. `mcp__chrome-devtools__take_snapshot`
3. For each task containing "E2E Test" in the title:
   - Click on the task to open details
   - Find and click Delete button
   - Confirm deletion
4. Repeat until no E2E tasks remain

*Expected:* All E2E test tasks deleted

---

### Cleanup 12.3: Delete Test Projects

*Purpose:* Remove all E2E test projects

Steps:
1. `mcp__chrome-devtools__navigate_page` to `https://thesis-mvp.vercel.app/projects`
2. `mcp__chrome-devtools__take_snapshot`
3. For each project containing "E2E Test" in the title:
   - Click on the project to open details
   - Find and click Delete button
   - Confirm deletion
4. Repeat until no E2E projects remain

*Expected:* All E2E test projects deleted

---

## FINAL SUMMARY

After ALL phases complete, provide a summary:

```
============================================
COMPREHENSIVE E2E TEST SUMMARY
============================================
Date: [CURRENT_DATE]
Environment: Production (thesis-mvp.vercel.app)
============================================

PHASE 1: Authentication & Navigation
- Test 1.1 Verify Auth:           [PASS/FAIL]
- Test 1.2 Navigation:            [PASS/FAIL]

PHASE 2: Dashboard
- Test 2.1 Dashboard Load:        [PASS/FAIL]

PHASE 3: Chat & AI Agents
- Test 3.1 New Chat:              [PASS/FAIL]
- Test 3.2 Send/Receive Message:  [PASS/FAIL]
- Test 3.3 KB Context Chat:       [PASS/FAIL] [CRITICAL]
- Test 3.4 Agent Selection:       [PASS/FAIL]
- Test 3.5 Chat Actions:          [PASS/FAIL]

PHASE 4: Tasks (Kanban)
- Test 4.1 View Tasks Board:      [PASS/FAIL]
- Test 4.2 Create New Task:       [PASS/FAIL]
- Test 4.3 Drag Task:             [PASS/FAIL]
- Test 4.4 Task Details Modal:    [PASS/FAIL]

PHASE 5: Projects
- Test 5.1 View Projects:         [PASS/FAIL]
- Test 5.2 Create New Project:    [PASS/FAIL]
- Test 5.3 Pipeline View:         [PASS/FAIL]

PHASE 6: Knowledge Base
- Test 6.1 KB Page Load:          [PASS/FAIL]
- Test 6.2 KB Search:             [PASS/FAIL]
- Test 6.3 Document Preview:      [PASS/FAIL]
- Test 6.4 Tag Filtering:         [PASS/FAIL]

PHASE 7: Agents
- Test 7.1 Agents Directory:      [PASS/FAIL]
- Test 7.2 Agent Details:         [PASS/FAIL]

PHASE 8: Intelligence
- Test 8.1 Intelligence Dashboard: [PASS/FAIL]

PHASE 9: DISCo
- Test 9.1 DISCo Page:            [PASS/FAIL]

PHASE 10: Meeting Rooms
- Test 10.1 Meeting Rooms:        [PASS/FAIL]

PHASE 11: Admin Help
- Test 11.1 Help Panel:           [PASS/FAIL]
- Test 11.2 Help Question:        [PASS/FAIL]

PHASE 12: Cleanup
- Cleanup 12.1 Conversations:     [DONE/PARTIAL]
- Cleanup 12.2 Tasks:             [DONE/PARTIAL]
- Cleanup 12.3 Projects:          [DONE/PARTIAL]

--------------------------------------------
TOTALS:  XX/28 tests passed
         XX/28 tests failed
         X items cleaned up
============================================

KB Context Chat Details:
- Documents found: [COUNT]
- Documents cited in response: [LIST]
- Response quality: [GOOD/NEEDS_IMPROVEMENT]
============================================
```

## Troubleshooting

### Chrome DevTools Connection Issues
- Verify Chrome is open with an active page
- Run `mcp__chrome-devtools__list_pages` to check connection
- Restart Chrome DevTools MCP server if needed

### Authentication Issues
- If redirected to login, complete auth flow manually or via automation
- Session may expire - re-login if needed

### Element Not Found
- Always take fresh snapshot before interacting
- Element UIDs change between page loads
- Wait for page to fully load before snapshot

### Slow Responses
- Chat with KB context may take 10-15 seconds
- Be patient with AI responses, especially for complex queries
- Use `mcp__chrome-devtools__wait_for` for expected content

### Cleanup Failures
- If delete fails, try refreshing page and retrying
- Some items may require additional confirmation
- Note any items that couldn't be deleted for manual cleanup
