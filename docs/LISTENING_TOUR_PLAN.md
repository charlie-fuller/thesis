# Thesis Focus Plan: Listening Tour → Action

## The Situation

Charlie has a powerful 21-agent platform, but needs a focused workflow to:
- **Synthesize** listening tour insights into actionable intelligence
- **Track** relationships, commitments, and opportunities across G&A departments
- **Execute** on Legal as the anchor client while maintaining visibility into other departments
- **Position** for leadership as more AI Solutions Partners join

The goal is **action**, not document creation. The app should help you decide what to do next and track progress against commitments.

## Proposed Direction: Add Focused Pages

Keep all existing agents and infrastructure. Add 3 new focused pages that create a streamlined workflow for the listening tour deliverable.

### New Page 1: `/listening-tour` - Mission Control

**Purpose**: Your home base for the listening tour process

**Layout**:
- **Left sidebar**: Department filter (Legal, Finance, HR, IT, etc.)
- **Main area**: Meeting cards showing processed transcripts
- **Right panel**: Aggregate stats (meetings completed, opportunities found, follow-ups pending)

**Each meeting card shows**:
- Date, attendees, department
- AI readiness indicator (champion/neutral/skeptical)
- # of opportunities identified
- # of follow-ups owed
- Click to expand full analysis

**Key action**: "Process New Transcripts" button that scans Granola vault for unprocessed meetings

### New Page 2: `/listening-tour/insights` - Cross-Meeting Synthesis

**Purpose**: See patterns across all your meetings

**Sections**:
1. **Opportunities by Department** - Clustered view of all AI opportunities found
2. **Stakeholder Map** - Who you've met, their disposition, influence level
3. **Themes** - Common pain points, common asks, common blockers
4. **Follow-ups** - What you owe people, with due dates

**Key action**: "Generate Synthesis Report" - AI aggregates insights across meetings

### New Page 3: `/action-plan` - What To Do Next

**Purpose**: Prioritize and track actions, not write documents

**Layout**:
- **Priority Queue**: Top opportunities ranked by impact × readiness
- **Legal Focus Panel**: Deep-dive on your anchor client's pipeline
- **Commitments Tracker**: What you promised, to whom, by when
- **Next Actions**: AI-suggested next steps based on insights

**Key sections**:
1. **This Week**: Immediate actions (follow-ups due, meetings to schedule)
2. **Legal Pipeline**: Opportunities being scoped/built with legal team
3. **Other Departments**: Quick-hit opportunities for non-anchor teams
4. **Blocked/Waiting**: Items needing input from others

**Key action**: "Mark Complete" / "Schedule Meeting" / "Create Scope Doc"

This is a **kanban for your listening tour**, not a document builder.

## Which Agents Power This

| Agent | Role in Workflow |
|-------|------------------|
| **Oracle** | Extract structured data from each transcript |
| **Reporter** | Synthesize across meetings, draft document sections |
| **Nexus** | Identify cross-department patterns and system dynamics |
| **Coordinator** | Route any ad-hoc queries |
| **Facilitator** | If you want multi-agent sessions on specific topics |

The other agents remain available for other use cases - they just aren't central to this workflow.

## Implementation Approach

### Phase 1: Data Model & Backend (Days 1-2)

**Goal**: Create the data structures and API for listening tour tracking

1. **Database migration** (`/database/migrations/029_listening_tour.sql`)
   ```sql
   -- Core tables
   listening_tour_meetings (id, user_id, title, meeting_date, department,
                            source_file, processed_at, raw_content)
   listening_tour_attendees (id, meeting_id, name, role, department,
                             ai_disposition, influence_level)
   listening_tour_opportunities (id, meeting_id, description, department,
                                  potential_impact, effort_estimate, quote)
   listening_tour_followups (id, meeting_id, description, owner,
                              due_date, status, completed_at)
   listening_tour_themes (id, theme_name, description, meeting_count)
   ```

2. **Backend services**
   - `backend/services/listening_tour_processor.py` - Scan Granola vault, extract via Oracle
   - `backend/services/listening_tour_synthesis.py` - Cross-meeting aggregation

3. **API routes** (`backend/api/routes/listening_tour.py`)
   - `GET /listening-tour/meetings` - List all processed meetings
   - `POST /listening-tour/process` - Trigger processing of new transcripts
   - `GET /listening-tour/insights` - Aggregated insights
   - `GET /listening-tour/followups` - All follow-ups with status
   - `POST /listening-tour/generate-section` - Generate action plan section

### Phase 2: Listening Tour Dashboard (Days 3-4)

**Goal**: Build the `/listening-tour` mission control page

**Files**:
- `frontend/app/listening-tour/page.tsx` - Main dashboard
- `frontend/components/listening-tour/MeetingCard.tsx` - Individual meeting display
- `frontend/components/listening-tour/DepartmentFilter.tsx` - Sidebar filter
- `frontend/components/listening-tour/StatsPanel.tsx` - Right panel stats

**Features**:
- Process new transcripts button (calls Granola vault scan)
- Department filter sidebar
- Meeting cards with expandable detail
- Stats: meetings by dept, opportunities found, follow-ups pending

### Phase 3: Insights & Synthesis Page (Days 5-6)

**Goal**: Build `/listening-tour/insights` for cross-meeting patterns

**Files**:
- `frontend/app/listening-tour/insights/page.tsx`
- `frontend/components/listening-tour/OpportunityCluster.tsx`
- `frontend/components/listening-tour/StakeholderMap.tsx`
- `frontend/components/listening-tour/ThemesList.tsx`
- `frontend/components/listening-tour/FollowupTracker.tsx`

**Features**:
- Opportunities grouped by department
- Stakeholder grid (name, dept, disposition, meetings)
- Common themes extracted across meetings
- Follow-up tracker with due dates and status

### Phase 4: Action Dashboard (Days 7-10)

**Goal**: Build `/action-plan` as an action-oriented dashboard, not a document builder

**Files**:
- `frontend/app/action-plan/page.tsx`
- `frontend/components/action-plan/PriorityQueue.tsx`
- `frontend/components/action-plan/LegalPipeline.tsx`
- `frontend/components/action-plan/CommitmentsTracker.tsx`
- `frontend/components/action-plan/NextActions.tsx`

**Features**:
- Priority-ranked opportunity queue (sortable by impact, readiness, department)
- Legal-specific pipeline view (your anchor client focus)
- Commitments tracker with due dates and status
- AI-suggested next actions based on current state
- Quick actions: mark complete, schedule meeting, create scope doc

## Confirmed Direction

- **Approach**: Add focused pages on top of existing platform (keep all agents)
- **Orientation**: Action-first (track commitments, prioritize opportunities, execute)
- **Transcript source**: Granola vault at `/Users/charlie.fuller/vaults/Contentful/Granola/`
- **Focus**: Legal as anchor client, other G&A secondary

## Leadership Positioning

Your leadership proof point isn't a document - it's **demonstrable results**:

1. **Track record with Legal**: Show what you scoped, built, and delivered
2. **Methodology in action**: The app itself becomes the playbook for future AI Solutions Partners
3. **Governance framework**: The PRD/BRD process you're building with Tyler, tested with Legal first
4. **Visibility**: Dashboard shows your pipeline, not a one-time report

When more AI Solutions Partners join, you hand them access to Thesis and say "here's how I work."

## Verification Plan

After each phase, verify:

**Phase 1 (Backend)**:
- Run migration successfully
- API endpoints return expected data structures
- Processor extracts correct fields from a test transcript

**Phase 2 (Dashboard)**:
- `/listening-tour` page loads
- Process button triggers vault scan
- Meeting cards display with correct data
- Department filter works

**Phase 3 (Insights)**:
- `/listening-tour/insights` shows aggregated data
- Opportunities grouped correctly by department
- Follow-up tracker shows all commitments

**Phase 4 (Action Dashboard)**:
- `/action-plan` page loads with priority queue
- Can mark items complete, change status
- Legal pipeline shows current opportunities
- Next actions suggestions appear

## Immediate First Step

When plan is approved, I'll start with:
1. Create the database migration for listening tour tables
2. Build the transcript processor service that integrates with Oracle agent
3. Create API routes
4. Build the listening tour dashboard

This gives you a working transcript-to-insights pipeline in 3-4 days.

## How This Fits With Existing Thesis

| Existing Feature | Relationship to New Pages |
|------------------|---------------------------|
| Knowledge Base | Listening tour meetings auto-added as documents |
| Stakeholders | Attendees can optionally sync to stakeholder table |
| Meeting Rooms | Can spin up a room to discuss specific department findings |
| Tasks | Follow-ups can optionally create tasks |
| Chat | Ask agents questions about listening tour data |

The new pages are additive - they don't replace anything, they provide a focused workflow.
