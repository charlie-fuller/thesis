# DISCO Discoveries

DISCO stands for Discovery, Intelligence, Synthesis, Convergence, Operationalize. It's your AI-assisted product discovery workflow - specialized agents that help you evaluate whether an idea is worth pursuing, and if so, turn it into something actionable.

Think of it as a structured way to go from "we should look into this" to "here's the PRD."

---

## Getting Started

Click **DISCO** in the navigation bar.

If you have existing discoveries, you'll see them as cards. Click **New Discovery** to create one.

If this is your first discovery, click **Create Discovery** in the empty state.

Fill in the **Create New Discovery** modal:
- **Name** (required) - What you're exploring
- **Description** - Context for the agents
- **Investigation Framing** (optional) - Click to expand. You can define your throughline upfront, or let the triage agent suggest framing from your documents.

Click **Create Discovery**. You'll land on the discovery detail view.

---

## The Discovery Detail View

Every discovery has five tabs:

| Tab | What It's For |
|-----|---------------|
| **Documents** | Link documents from the Knowledge Base or upload new ones |
| **Run Agent** | Execute discovery agents and see streaming output |
| **Outputs** | View all agent results in one place |
| **Projects** | See and manage projects linked to this discovery |
| **Alignment** | Analyze how well the discovery aligns with strategic goals |

**Editing name and description:** Click the discovery name or description in the header to open an edit modal. This provides more space for editing multi-line descriptions than inline editing. You can also edit the throughline from here.

**Throughline summary:** If you defined a throughline, a compact summary appears below the description showing counts of problem statements, hypotheses, and gaps. Click to expand the full detail.

**Value alignment tags:** When populated, KPI tags and department goal badges appear in the header area.

**Chat Button:** In the header area, click the **Chat** button to open the main chat interface with full discovery context. This redirects to `/chat?initiative_id=xxx` with the Initiative Agent auto-selected.

**Documents tab features:**
- **Link from KB** - Browse and select existing KB documents
- **Upload** - Add new documents directly (they go to KB automatically)
- **Unlink** - Remove document association (keeps document in KB)

**Projects tab features:**
- View all projects linked to this discovery
- Click a project to navigate to its detail view
- See project status and tier at a glance
- **Active only** toggle (on by default) - hides archived projects

---

## Investigation Framing (Throughline)

The Investigation Framing is an optional but powerful way to give your discovery structured direction. It defines what you're trying to solve, what you believe, and what you don't know.

### What Goes in a Throughline

| Section | Purpose | Example |
|---------|---------|---------|
| **Problem Statements** | What you're trying to solve | "Our enterprise customers churn at 2x the rate after year one" |
| **Hypotheses** | What you believe to be true (to validate or refute) | "AI-assisted onboarding will reduce time-to-value by 40%" |
| **Gaps** | What you don't know yet | "No data on competitor retention strategies" |
| **Desired Outcome State** | What success looks like | "Clear retention playbook with executive buy-in" |

### Two Ways to Get a Throughline

**Option 1: Let the Agent Extract It (Recommended)**
1. Create a discovery with just a name, description, and linked documents
2. Run the **Triage** agent
3. If your throughline is sparse, the agent analyzes your documents and suggests problem statements, hypotheses, gaps, KPIs, and stakeholders
4. A **Review Suggested Framing** panel appears after triage completes
5. Click **Accept All** to populate your throughline, or **Dismiss** if the suggestions aren't useful

**Option 2: Define It Manually**
1. When creating or editing a discovery, expand **Investigation Framing**
2. Add items to each section using the **+ Add** buttons
3. Each hypothesis has a type: `assumption`, `belief`, or `prediction`
4. Each gap has a type: `data`, `people`, `process`, or `capability`
5. Items get auto-assigned IDs (ps-1, h-1, g-1) for tracking

### How Agents Use the Throughline

When a throughline is defined, all four DISCO stages reference it:

- **Discovery Guide**: Evaluates problem statements against the triage gate, uses Five Whys and root cause analysis, designs sessions targeting specific gaps
- **Insight Analyst**: Maps findings to hypothesis IDs, tracks which gaps are addressed
- **Initiative Builder**: Notes which problem statements and hypotheses each proposed initiative addresses
- **Requirements Generator**: Produces a structured **Throughline Resolution** with hypothesis verdicts, gap statuses, recommended state changes, and a "So What?" synthesis

### Gap Types

Gaps are categorized by type to guide investigation approach:

| Type | Meaning | Investigation Focus |
|------|---------|-------------------|
| **Data** | Missing or inaccessible information | Data discovery, quantification, access |
| **People** | Missing expertise, knowledge, or capacity | Stakeholder interviews, expertise mapping |
| **Process** | Missing or broken workflows | Process mapping, bottleneck analysis |
| **Capability** | Missing tools, technology, or skills | Technical assessment, build vs. buy |

### Throughline Resolution

After running the Requirements Generator (Convergence stage), the output includes a resolution section showing:

- **Hypothesis verdicts**: confirmed, refuted, or inconclusive (with evidence)
- **Gap statuses**: addressed, partially addressed, or unaddressed (with findings)
- **Recommended state changes**: specific actions to take
- **So What?**: The bottom line - what should change, what's the next human action, and what's the kill test

Resolution results appear color-coded in the output viewer (green = confirmed/addressed, red = refuted/unaddressed, yellow = inconclusive/partial).

### Resolution Annotations

You can override agent-assigned resolution statuses with your own assessment:

1. In the throughline summary, click the edit icon next to any hypothesis or gap
2. Select your status override (e.g., "You: refuted" or "You: addressed")
3. Add an optional note explaining why
4. Your annotation appears alongside the agent's assessment

This lets you track corrections as new information emerges without re-running agents.

---

## Value Alignment

Each discovery can track its alignment with organizational value streams. This is optional at creation and can be filled in progressively as you learn more during investigation.

| Field | Purpose | Example |
|-------|---------|---------|
| **Target Department** | Which department this discovery serves | "People", "Engineering" |
| **KPIs** | Measurable outcomes this discovery supports | "Time to fill", "Cost per hire" |
| **Department Goals** | Goals this supports (free text) | "Eliminate manual recruiting overhead" |
| **Company Priority** | Which company priority it aligns with | "Cost-Efficient GTM Growth" |
| **Strategic Pillar** | Enable, Operationalize, or Govern | "operationalize" |
| **Notes** | Context on how alignment was discovered | "Discovered during kickoff with Bella" |

The triage agent can suggest KPIs and department context from your documents. Value alignment is validated at the Convergence stage - the Requirements Generator confirms whether the recommendation ties to measurable KPIs.

---

## Sponsors and Stakeholders

You can link a sponsor and stakeholders from the Stakeholders database:

- **Sponsor** - The executive sponsor for this discovery
- **Stakeholders** - Other people involved or affected

These are set in the discovery create/edit modal and appear in the header area.

---

## The Workflow Stages

DISCO moves through four stages, each with specific agents:

### Stage 1: Discovery
Get the lay of the land. Is this worth pursuing?

| Agent | What It Does |
|-------|--------------|
| **Discovery Prep** | Analyzes uploaded documents, extracts key themes |
| **Triage** | GO/NO-GO/INVESTIGATE gate - should you proceed? Also extracts suggested framing from documents using Five Whys and root cause analysis |
| **Discovery Planner** | Creates session agendas for stakeholder interviews, with gap-targeted questions |
| **Discovery Workshop** | Facilitates structured discovery sessions |
| **Coverage Tracker** | Tracks what's been covered, identifies gaps (READY/GAPS), includes "Why This Matters" and absence reports |

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
| **Strategist** | Proposes initiatives with business rationale |

### Stage 4: Convergence
Build the thing.

| Agent | What It Does |
|-------|--------------|
| **PRD Generator** | Creates product requirements from approved proposed initiatives |
| **Evaluation Framework** | Weighted criteria matrix for vendor/tool selection |
| **Decision Framework** | Options analysis for governance decisions |

Convergence outputs now include tool/platform recommendations, evaluation/QA plans, value alignment confirmation, and AI risk/compliance review.

---

## Running Agents

1. Go to the **Run Agent** tab
2. Select an agent from the dropdown
3. Click **Run**
4. Watch the streaming output
5. Review the guidance panel for what to do next

Agents run in sequence - earlier stages inform later ones. The system will tell you if you're trying to run something out of order.

**Framing hints:** If your discovery has no throughline and triage hasn't been run yet, you'll see a hint to run triage first for auto-discovery of framing. If triage has already run with suggestions available, you'll see a prompt to review the suggested framing.

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

Discoveries move through statuses as you run agents:

| Status | Card Badge | Detail View | When |
|--------|------------|-------------|------|
| Initial | `Draft` | `Draft` | Just created |
| After Triage | `Triaged` | `Triaged` | Triage complete |
| During Discovery | `Discovery` | `In Discovery` | Running discovery agents |
| After Consolidator | `Intelligence` | `Consolidated` | Insights consolidated |
| After Strategist | `Synthesis` | `Synthesized` | Proposed initiatives created |
| After PRD | `Convergence` | `PRD Generated` | Output document created |
| Done | `Archived` | `Archived` | Manually archived |

---

## Managing Proposed Initiatives

After Strategist runs, you'll have proposed initiatives to review.

Each proposed initiative shows:
- Feature grouping with rationale
- Business value assessment
- Implementation complexity estimate

**To review proposed initiatives:**
1. Go to **Outputs** tab
2. Find Strategist output
3. Review **Pending Review** proposed initiatives
4. Click **Approve** or **Reject** for each

Only approved proposed initiatives can generate output documents or create projects.

---

## Creating Projects

There are two paths from proposed initiative to project:

### Direct Project Creation (Simple Cases)
1. Approve a proposed initiative in the Synthesis view
2. Click **Create Project** on the approved proposed initiative
3. Review the pre-filled fields (name, description, scores mapped from impact/feasibility/urgency)
4. Click **Create** to add the project to your pipeline

### Via Output Document (Complex Cases)
1. Approve a proposed initiative and generate an output document (PRD, Evaluation, or Decision Framework)
2. In the output viewer, click **Create Project**
3. Review the AI-extracted fields - title, description, department, scoring dimensions
4. Fields show confidence indicators (high/medium/low) - check amber-highlighted fields carefully
5. Optionally extract tasks from the document's requirements section
6. Click **Create** to add the project to your pipeline

The project is automatically linked to the parent discovery with a source badge for traceability.

---

## Creating Tasks from State Changes

When the Requirements Generator produces a throughline resolution with state changes, you can create tasks directly from them:

1. In the output viewer, find the **Throughline Resolution** section
2. Click **Create Tasks from State Changes**
3. Select which state changes to create as tasks (all selected by default)
4. Optionally link tasks to a project
5. Click **Create N Tasks**
6. Tasks appear in your Kanban board with a "disco" tag

The "Next Human Action" from the "So What?" section is included as a high-priority task option.

---

## Flexible Output Types

When you approve a proposed initiative, you choose the output document type. The system uses AI to suggest the most appropriate type based on the content.

| Output Type | When to Use | What It Produces |
|-------------|-------------|------------------|
| **PRD** (default) | Build/development proposed initiatives | Product Requirements Document with user stories, acceptance criteria, technical specs, tool/platform recommendations |
| **Evaluation Framework** | Research/evaluation proposed initiatives (vendor selection, tool comparison) | Weighted criteria matrix, platform comparison table, recommendation |
| **Decision Framework** | Governance decisions | Decision criteria, stakeholder analysis, options comparison, risk/benefit assessment |

All output types now include:
- **Value Alignment Confirmation** - States which KPIs the recommendation supports
- **Tool & Platform Recommendations** - Recommends the simplest effective tool for the problem
- **AI Risk & Compliance Review** - Data classification, EU AI Act considerations, platform governance

**How it works:**
1. Click **Approve** on a proposed initiative
2. The system analyzes it and suggests an output type with rationale
3. You can accept the suggestion or choose a different type
4. Click **Generate** to create the output document

---

## Goal Alignment

The **Alignment** tab lets you analyze how well a discovery (and its linked projects) align with strategic goals.

**Discovery alignment:**
1. Go to the **Alignment** tab
2. Click **Analyze** (editors/owners only)
3. The system scores alignment (0-100) across 4 IS FY27 strategic pillars (25 points each):
   - **Customer and Prospect Journey** - Decision-ready first touch to churn
   - **Maximize Value from Core Systems & AI** - Productivity, spend optimization, experience
   - **Data First Digital Workforce** - Automation, Insight 360, AI-enabled platforms
   - **High-Trust IS Culture** - Strategic partnership, transparency, career growth
4. Each pillar shows a score, progress bar, rationale, and relevant KPIs
5. An analysis summary and impacted KPIs are shown at the top

If agent outputs exist (triage, strategist, insight analyst, etc.), they are included in the analysis for more accurate scoring. Without outputs, analysis uses only the discovery name and description.

**Project roll-up:**
- Shows the average alignment score across all linked projects
- Distribution summary (count of High/Moderate/Low/Minimal)
- Individual project scores in a grid with quick links
- Projects not yet analyzed are highlighted

**Stale data indicator:** If new agent outputs have been generated since the last analysis, a warning appears prompting you to re-analyze.

---

## Sharing and Collaboration

Click the **Share** button on any discovery.

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
- Documents stay up-to-date across all discoveries
- No duplicate uploads needed
- Search across all your org's content

---

## Using Chat with Discovery Context

Click the **Chat** button in the discovery header to open a conversation with full discovery context.

**What the Initiative Agent sees:**
- All documents linked to the discovery
- All DISCO agent outputs (triage results, insights, PRDs, etc.)
- Discovery metadata (name, description, status)
- PuRDy methodology reference

**Example questions:**
- "What documents do you have access to?"
- "Summarize the key findings from the planning doc"
- "What concerns did Triage raise?"
- "Compare the two approaches in the tech evaluation"

**Conversation History:**
All conversations with discovery context are saved and can be filtered in the main chat sidebar. Select the discovery from the dropdown to see all related conversations.

---

## Tips for Better Results

1. **Link context first.** The more documents you provide, the better Discovery Prep and Triage can assess the opportunity.

2. **Let triage suggest framing.** Instead of manually defining problem statements and hypotheses, link your documents and run triage first. The agent will extract suggested framing for you to review.

3. **Run agents in order.** The workflow is designed to build on itself. Skipping steps weakens later outputs.

4. **Don't skip Triage.** Even if you're excited about an idea, Triage often surfaces concerns you hadn't considered.

5. **Add transcripts after interviews.** Insight Extractor works best with actual conversation transcripts, not summaries.

6. **Review proposed initiatives carefully.** The Strategist proposes options - your judgment on which to approve shapes the final output.

7. **Create tasks from state changes.** After convergence, use the "Create Tasks" button to turn recommended actions into trackable Kanban items.

---

## What's Next?

- [Discovery Inbox](./10-discovery-inbox.md) - Auto-extracted candidates from your documents
- [Knowledge Base](./04-knowledge-base.md) - Managing the documents that feed DISCO
- [Projects](./06-projects.md) - Where approved discoveries become projects
