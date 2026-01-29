# DISCo Initiatives

DISCo stands for Discovery, Intelligence, Synthesis, Capabilities, Operationalize. It's your AI-assisted product discovery workflow - 8 specialized agents that help you evaluate whether an idea is worth pursuing, and if so, turn it into something actionable.

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

Every initiative has four tabs:

| Tab | What It's For |
|-----|---------------|
| **Documents** | Upload supporting materials - research, transcripts, competitor analyses |
| **Run Agent** | Execute discovery agents and see streaming output |
| **Outputs** | View all agent results in one place |
| **Chat** | Ask questions about the initiative with full context |

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

### Stage 4: Capabilities
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
| After PRD | `Capabilities` | `PRD Generated` | PRD created |
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

## Tips for Better Results

1. **Upload context first.** The more documents you provide, the better Discovery Prep and Triage can assess the opportunity.

2. **Run agents in order.** The workflow is designed to build on itself. Skipping steps weakens later outputs.

3. **Don't skip Triage.** Even if you're excited about an idea, Triage often surfaces concerns you hadn't considered.

4. **Add transcripts after interviews.** Insight Extractor works best with actual conversation transcripts, not summaries.

5. **Review bundles carefully.** The Strategist proposes options - your judgment on which bundles to approve shapes the final PRD.

---

## What's Next?

- [Discovery Inbox](./10-discovery-inbox.md) - Auto-extracted candidates from your documents
- [Knowledge Base](./04-knowledge-base.md) - Managing the documents that feed DISCo
- [Projects](./06-projects.md) - Where approved initiatives become projects
