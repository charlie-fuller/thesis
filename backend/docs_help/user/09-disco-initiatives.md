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

Every discovery has six tabs:

| Tab | What It's For |
|-----|---------------|
| **Documents** | Link documents from the Knowledge Base or upload new ones |
| **Framing** | Edit problem statements, hypotheses, gaps, and desired outcome inline |
| **Alignment** | Analyze how well the discovery aligns with strategic goals |
| **Projects** | See and manage projects linked to this discovery |
| **Run Agents** | Execute discovery agents and see streaming output |
| **Outputs** | View all agent results in one place |

**Editing discovery details:** Click the pencil icon next to the discovery name, or use "Edit Discovery Details" to open a modal for name, description, department, KPIs, and strategic pillar.

**Value alignment tags:** When populated, department, KPI, and strategic pillar badges appear inline with the description in the header.

**Chat Button:** In the header area, click the **Chat** button to open the main chat interface with full discovery context. This redirects to `/chat?initiative_id=xxx` with the Discovery Agent auto-selected.

**Create Project:** Click the **Create Project** button in the header to create a project directly linked to this discovery.

**Documents tab features:**
- **Link from KB** - Browse and select existing KB documents
- **Upload** - Add new documents directly (they go to KB automatically)
- **Unlink** - Remove document association (keeps document in KB)

**Projects tab features:**
- View all projects linked to this discovery
- Click a project to open its detail modal directly (deep-links to the Projects page with the modal open)
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

### Three Ways to Get a Throughline

**Option 1: Generate from Documents (Recommended for new discoveries)**
1. Create a discovery with just a name, description, and linked documents
2. Go to the **Framing** tab and click **Generate from Documents**
3. The Discovery Guide agent analyzes your linked documents and suggests problem statements, hypotheses, gaps, KPIs, and stakeholders
4. A **Review Suggested Framing** panel appears when complete
5. Click **Accept All** to populate your throughline, or **Dismiss** if the suggestions aren't useful
6. Accepting deduplicates against existing items - clicking Accept All multiple times won't create duplicates

If you already have framing, the button reads **Regenerate from Documents** and suggests additional items.

**Option 2: Chat with the Discovery Agent (Recommended for iterating)**
1. Click the **Chat** button in the discovery header
2. Discuss the problem space conversationally: "Help me frame this discovery" or "What problem statements should we be working with?"
3. The Discovery Agent reviews your linked documents, agent outputs, and existing throughline
4. When ready, it proposes structured framing as a card with checkboxes
5. Select which items to keep, then click **Apply to Discovery** to merge them into your throughline
6. You can iterate - chat more and get additional proposals

**Option 3: Edit Directly on the Framing Tab**
1. Go to the **Framing** tab
2. Add items to each section using the **+ Add** buttons
3. Edit any item inline - the full text is editable in the input field
4. Each hypothesis has a type dropdown: Assumption, Belief, or Prediction
5. Each gap has a type dropdown: Data, People, Process, or Capability
6. Delete items with the trash icon
7. Click the **Save Framing** button (appears when you have unsaved changes)

### Ground-Truth Corrections

At the bottom of the Framing tab, expand **Ground-Truth Corrections** to enter free-text overrides that correct errors in your linked documents.

Agents treat corrections as authoritative and prioritize them over conflicting document content. Use this when:
- Documents contain misattributions (e.g., wrong team owns a tool)
- Stats or figures are outdated
- Assumptions in source documents are known to be wrong

Example corrections:
- "Our company uses Salesforce, NOT HubSpot"
- "Q3 revenue was $12M (not $8M as stated in the deck)"
- "The n8n integration is owned by IT, not Engineering"

Corrections are injected into every agent prompt as a dedicated "Ground-Truth Corrections" section between the throughline and document content.

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

### Resolution in Outputs

Resolution results from the Requirements Generator appear in the **Outputs** tab. If a gap needs action, create a task for it from the state changes section rather than annotating the framing items directly.

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

**Framing hints:** If your discovery has no throughline, head to the **Framing** tab to add items directly or click **Generate from Documents**. If the Discovery Guide has already run with suggestions available, you'll see a prompt to review the suggested framing.

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

There are three paths to create projects from a discovery:

### From the Discovery Header (Quick Start)
1. Click **Create Project** in the discovery header
2. Fill in the project details in the modal
3. The project is automatically linked to this discovery
4. This is useful when you want to create a project before running all DISCO stages

### Direct Project Creation from Proposed Initiatives (Simple Cases)
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

**Editing alignment results:**
Analysis results are editable after generation - no need to re-analyze to fix incorrect items:
- **Remove KPI impacts**: Hover over any green KPI chip and click the X to dismiss it
- **Edit pillar rationales**: Hover over a pillar's rationale text and click the pencil icon to rewrite it
- **Correct the summary**: Click the pencil icon next to "Analysis Summary" to edit the text
- **Remove irrelevant pillars**: Hover over any pillar card to reveal the X button (red square outline) next to the score

All edits save immediately. Re-analyzing will regenerate all results from scratch.

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

## Linking Folders

Instead of linking individual documents, you can link entire vault folders. All documents in the folder are automatically associated with the discovery.

**To link a folder:**
1. Go to the **Documents** tab
2. In the **Linked Folders** section, click **Link Folder**
3. Browse the folder tree and select a folder
4. All documents in that folder are automatically linked

**How it works:**
- Documents are linked at the time of folder linking
- If you remove a folder link, the associated documents are unlinked
- Individual document links made separately are not affected by folder operations
- Linked folders and their document counts are shown in the Linked Folders section

This is useful when your Obsidian vault is organized by topic or initiative - link the whole folder instead of picking individual files.

---

## Using Chat with Discovery Context

Click the **Chat** button in the discovery header to open a conversation with full discovery context.

**What the Discovery Agent sees:**
- Discovery metadata (name, description, status, department)
- Current throughline (problem statements, hypotheses, gaps, desired outcome state)
- Latest agent output summaries (recommendation and confidence from each agent that has run)
- Names of all linked documents
- Value alignment data (KPIs, department goals, strategic pillar)

**Example questions:**
- "What do you know about this initiative?"
- "Summarize the key findings from the planning doc"
- "What concerns did Triage raise?"
- "Help me frame this discovery"
- "What gaps should we address next?"

**Framing proposals:**
When you ask the Discovery Agent to help with framing, it can propose structured items (problem statements, hypotheses, gaps, desired outcome). These appear as an interactive card where you can:
1. Review each proposed item
2. Deselect any items you don't want
3. Click **Apply to Discovery** to merge selected items into your throughline

The agent references existing throughline items and avoids duplicating them. You can iterate multiple times to build up your framing progressively.

**Conversation History:**
All conversations with discovery context are saved and can be filtered in the main chat sidebar. Select the discovery from the dropdown to see all related conversations.

---

## Platform Governance Maps

The DISCO page includes two platform governance reference tabs, separated by a visual divider from the workflow tabs:

### Platform Map

An interactive 7-stage process map for AI platform selection at Contentful. Shows the full journey from idea to operationalized solution, including:
- Idea submission and initial screening
- Capability mapping against existing platforms
- Governance review with German Works Council considerations
- Implementation and operationalization paths

### Platform Decision Tree

An interactive decision tree that guides platform selection decisions step by step. Covers:
- **Use case classification** - What type of problem are you solving?
- **Platform matching** - Which existing platform fits? (Glean, Google Workspace AI, MuleSoft, custom build)
- **Governance evaluation** - Reliability, governance, traceability, auditability, fault tolerance
- **Compliance check** - Works Council approval status for each platform

Both maps are standalone interactive HTML pages. Navigate through nodes by clicking options to explore different decision paths.

---

## Tips for Better Results

1. **Link context first.** The more documents you provide, the better Discovery Prep and Triage can assess the opportunity.

2. **Let agents suggest framing.** Instead of manually defining problem statements and hypotheses, go to the **Framing** tab and click **Generate from Documents**, or chat with the Discovery Agent to iteratively build your framing through conversation.

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
