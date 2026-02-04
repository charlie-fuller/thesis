# DISCo Initiatives

DISCo stands for Discovery, Intelligence, Synthesis, Convergence, Operationalize. It's your AI-assisted product discovery workflow - 8 specialized agents that help you evaluate whether an idea is worth pursuing, and if so, turn it into something actionable.

Think of it as a structured way to go from "we should look into this" to "here's the PRD."

---

## Getting Started

Click **DISCo** in the navigation bar.

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
| **Chat** | Ask questions about the initiative - sees all linked documents |

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

DISCo moves through four stages, each with specific agents:

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

Only approved bundles can be turned into PRDs.

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

DISCo uses the Knowledge Base as its single source of truth for documents.

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

## Using the Chat

The **Chat** tab lets you ask questions about your initiative with full context.

**What the chat sees:**
- All documents linked to the initiative (listed by name)
- Relevant content chunks via semantic search
- Previous agent outputs (triage results, PRDs, etc.)
- PuRDy methodology reference

**Example questions:**
- "What documents do you have access to?"
- "Summarize the key findings from the planning doc"
- "What concerns did Triage raise?"
- "Compare the two approaches in the tech evaluation"

The chat always knows what documents are linked, so you can ask meta-questions like "can you see the planning document?" and get a direct answer.

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
- [Knowledge Base](./04-knowledge-base.md) - Managing the documents that feed DISCo
- [Projects](./06-projects.md) - Where approved initiatives become projects
