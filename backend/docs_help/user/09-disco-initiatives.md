# DISCO Initiatives

DISCO stands for Discovery, Intelligence, Synthesis, Convergence, Operationalize. It's your AI-assisted product discovery workflow - specialized agents that help you evaluate whether an idea is worth pursuing, and if so, turn it into something actionable.

Think of it as a structured way to go from "we should look into this" to "here's the PRD."

---

## Getting Started

Click **DISCO** in the navigation bar.

If you have existing initiatives, you'll see them as cards. Click **New Initiative** to create one.

If this is your first initiative, click **Create Initiative** in the empty state.

Fill in the **Create New Initiative** modal:
- **Name** (required) - What you're exploring
- **Description** - Context for the agents

Click **Create Initiative**. You'll land on the initiative detail view.

---

## The Initiative Detail View

Every initiative has five tabs:

| Tab | What It's For |
|-----|---------------|
| **Documents** | Link documents from the Knowledge Base or upload new ones |
| **Run Agent** | Execute discovery agents and see streaming output |
| **Outputs** | View all agent results in one place |
| **Projects** | See and manage projects linked to this initiative |
| **Alignment** | Analyze how well the initiative aligns with strategic goals |

**Editing name and description:** Click the initiative name or description in the header to open an edit modal. This provides more space for editing multi-line descriptions than inline editing.

**Chat Button:** In the header area, click the **Chat** button to open the main chat interface with full initiative context. This redirects to `/chat?initiative_id=xxx` with the Initiative Agent auto-selected.

**Documents tab features:**
- **Link from KB** - Browse and select existing KB documents
- **Upload** - Add new documents directly (they go to KB automatically)
- **Unlink** - Remove document association (keeps document in KB)

**Projects tab features:**
- View all projects linked to this initiative
- Click a project to navigate to its detail view
- See project status and tier at a glance
- **Active only** toggle (on by default) - hides archived projects

---

## The Workflow Stages

DISCO moves through four stages, each with specific agents:

### Stage 1: Discovery
Get the lay of the land. Is this worth pursuing?

| Agent | What It Does |
|-------|--------------|
| **Discovery Prep** | Analyzes uploaded documents, extracts key themes |
| **Triage** | GO/NO-GO/INVESTIGATE gate - should you proceed? |
| **Discovery Planner** | Creates session agendas for stakeholder interviews |
| **Discovery Workshop** | Facilitates structured discovery sessions |
| **Coverage Tracker** | Tracks what's been covered, identifies gaps (READY/GAPS) |

### Stage 2: Intelligence
Extract patterns from your discovery sessions.

| Agent | What It Does |
|-------|--------------|
| **Insight Extractor** | Pulls patterns with evidence from transcripts |

### Stage 3: Synthesis
Turn insights into decisions.

| Agent | What It Does |
|-------|--------------|
| **Consolidator** | Creates a decision document from all insights |
| **Strategist** | Proposes feature bundles with business rationale |

### Stage 4: Convergence
Build the thing.

| Agent | What It Does |
|-------|--------------|
| **PRD Generator** | Creates product requirements from approved bundles |
| **Tech Evaluation** | Assesses technical feasibility and approaches |

---

## Running Agents

1. Go to the **Run Agent** tab
2. Select an agent from the dropdown
3. Click **Run**
4. Watch the streaming output
5. Review the guidance panel for what to do next

Agents run in sequence - earlier stages inform later ones. The system will tell you if you're trying to run something out of order.

---

## Understanding Decisions

Three key decision badges appear throughout the workflow:

| Badge | Color | Meaning |
|-------|-------|---------|
| **GO** | Green | Proceed with discovery |
| **NO-GO** | Red | Stop - not worth pursuing |
| **INVESTIGATE** | Amber | Gather more info before deciding |

Triage produces the main GO/NO-GO decision. Coverage Tracker produces READY/GAPS.

---

## Status Progression

Initiatives move through statuses as you run agents:

| Status | Card Badge | Detail View | When |
|--------|------------|-------------|------|
| Initial | `Draft` | `Draft` | Just created |
| After Triage | `Triaged` | `Triaged` | Triage complete |
| During Discovery | `Discovery` | `In Discovery` | Running discovery agents |
| After Consolidator | `Intelligence` | `Consolidated` | Insights consolidated |
| After Strategist | `Synthesis` | `Synthesized` | Bundles proposed |
| After PRD | `Convergence` | `PRD Generated` | PRD created |
| Done | `Archived` | `Archived` | Manually archived |

---

## Managing Bundles

After Strategist runs, you'll have proposed bundles to review.

Each bundle shows:
- Feature grouping with rationale
- Business value assessment
- Implementation complexity estimate

**To review bundles:**
1. Go to **Outputs** tab
2. Find Strategist output
3. Review **Pending Review** bundles
4. Click **Approve** or **Reject** for each

Only approved bundles can generate output documents.

---

## Flexible Output Types

When you approve a bundle, you choose the output document type. The system uses AI to suggest the most appropriate type based on the bundle's content.

| Output Type | When to Use | What It Produces |
|-------------|-------------|------------------|
| **PRD** (default) | Build/development bundles | Product Requirements Document with user stories, acceptance criteria, technical specs |
| **Evaluation Framework** | Research/evaluation bundles (vendor selection, tool comparison) | Weighted criteria matrix, platform comparison table, recommendation |
| **Decision Framework** | Governance decisions | Decision criteria, stakeholder analysis, options comparison, risk/benefit assessment |

**How it works:**
1. Click **Approve** on a bundle
2. The system analyzes the bundle and suggests an output type with rationale
3. You can accept the suggestion or choose a different type
4. Click **Generate** to create the output document

---

## Creating Projects from PRDs

Approved PRDs can spawn projects directly with AI-extracted fields.

**To create a project from a PRD:**
1. Go to **Outputs** tab and find a generated PRD
2. Click **Create Project**
3. Review the pre-filled fields - AI extracts title, description, department, scoring dimensions
4. Fields show confidence indicators (high/medium/low) - check amber-highlighted fields carefully
5. Optionally extract tasks from the PRD requirements section
6. Click **Create** to add the project to your pipeline

The project is automatically linked to the parent initiative with a "From PRD" badge for traceability.

---

## Goal Alignment

The **Alignment** tab lets you analyze how well an initiative (and its linked projects) align with strategic goals.

**Initiative alignment:**
1. Go to the **Alignment** tab
2. Click **Analyze** (editors/owners only)
3. The system scores alignment (0-100) across 4 IS FY27 strategic pillars (25 points each):
   - **Customer and Prospect Journey** - Decision-ready first touch to churn
   - **Maximize Value from Core Systems & AI** - Productivity, spend optimization, experience
   - **Data First Digital Workforce** - Automation, Insight 360, AI-enabled platforms
   - **High-Trust IS Culture** - Strategic partnership, transparency, career growth
4. Each pillar shows a score, progress bar, rationale, and relevant KPIs
5. An analysis summary and impacted KPIs are shown at the top

If agent outputs exist (triage, strategist, insight analyst, etc.), they are included in the analysis for more accurate scoring. Without outputs, analysis uses only the initiative name and description.

**Project roll-up:**
- Shows the average alignment score across all linked projects
- Distribution summary (count of High/Moderate/Low/Minimal)
- Individual project scores in a grid with quick links
- Projects not yet analyzed are highlighted

**Stale data indicator:** If new agent outputs have been generated since the last analysis, a warning appears prompting you to re-analyze.

---

## Sharing and Collaboration

Click the **Share** button on any initiative.

In the share modal:
1. Enter the collaborator's email
2. Select role: `Viewer` or `Editor`
3. Click **Invite**

Viewers can see everything. Editors can run agents and manage documents.

---

## Linking Documents from KB

DISCO uses the Knowledge Base as its single source of truth for documents.

**To link documents:**
1. Go to the **Documents** tab
2. Click **Link from KB**
3. The browser opens with search and tag filter on the first row
4. Use sort and source filter on the second row
5. Click a document's eye icon to preview it
6. Select documents with checkboxes
7. Click **Link X Document(s)** in the footer

**Sorting options:**
- **Most Recent** - Newest documents first (default)
- **Oldest First** - Oldest documents first
- **Name (A-Z)** - Alphabetical order
- **Name (Z-A)** - Reverse alphabetical

**Source filter:**
- **All Sources** - Show all documents
- **Vault** - Obsidian synced documents
- **Google Drive** - Drive imports
- **Notion** - Notion imports
- **Uploaded** - Manually uploaded files

Click **Reset filters** to return to defaults.

**The browser shows:**
- Document title and source
- Preview panel on the right (60%)
- Highlighted border for previewed document
- Tag badges for quick filtering

**Benefits of KB integration:**
- Documents stay up-to-date across all initiatives
- No duplicate uploads needed
- Search across all your org's content

---

## Using Chat with Initiative Context

Click the **Chat** button in the initiative header to open a conversation with full initiative context.

**What the Initiative Agent sees:**
- All documents linked to the initiative
- All DISCO agent outputs (triage results, insights, PRDs, etc.)
- Initiative metadata (name, description, status)
- PuRDy methodology reference

**Example questions:**
- "What documents do you have access to?"
- "Summarize the key findings from the planning doc"
- "What concerns did Triage raise?"
- "Compare the two approaches in the tech evaluation"

**Conversation History:**
All conversations with initiative context are saved and can be filtered in the main chat sidebar. Select the initiative from the dropdown to see all related conversations.

---

## Tips for Better Results

1. **Link context first.** The more documents you provide, the better Discovery Prep and Triage can assess the opportunity.

2. **Run agents in order.** The workflow is designed to build on itself. Skipping steps weakens later outputs.

3. **Don't skip Triage.** Even if you're excited about an idea, Triage often surfaces concerns you hadn't considered.

4. **Add transcripts after interviews.** Insight Extractor works best with actual conversation transcripts, not summaries.

5. **Review bundles carefully.** The Strategist proposes options - your judgment on which bundles to approve shapes the final PRD.

---

## What's Next?

- [Discovery Inbox](./10-discovery-inbox.md) - Auto-extracted candidates from your documents
- [Knowledge Base](./04-knowledge-base.md) - Managing the documents that feed DISCO
- [Projects](./06-projects.md) - Where approved initiatives become projects
