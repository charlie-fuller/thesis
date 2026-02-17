# Projects

The AI project pipeline. Where you track, score, and prioritize multi-step AI initiatives.

Projects are strategic initiatives that require planning, coordination, and multiple steps to complete. They're different from tasks, which are atomic actions completable in a single session.

---

## The Pipeline

Go to **Projects** in the navigation.

You'll see projects organized by tier:
- **Tier 1** - High priority (score 17-20)
- **Tier 2** - Medium-high (score 14-16)
- **Tier 3** - Medium-low (score 11-13)
- **Tier 4** - Low priority (score 0-10)

Tiers expand and collapse. High-tier projects are what you should focus on.

---

## The Scoring System

Each project is scored on four dimensions (1-5 each):

**ROI Potential**
How much value could this deliver?
- 5: Transformative impact, significant revenue/savings
- 3: Moderate impact, solid business case
- 1: Minimal financial benefit

**Implementation Effort**
How hard is this to do? (Inverted - high score = easier)
- 5: Quick win, low complexity
- 3: Moderate effort, some dependencies
- 1: Major initiative, many moving parts

**Strategic Alignment**
How well does this fit company priorities?
- 5: Direct alignment with stated strategy
- 3: Indirect connection to priorities
- 1: Nice to have, not strategic

**Stakeholder Readiness**
Are the people ready for this?
- 5: Champions exist, low resistance expected
- 3: Mixed support, some change management needed
- 1: Significant resistance, political challenges

Total score determines the tier. It's a simple framework, but it forces you to think through multiple dimensions.

---

## Creating Projects

There are three ways to create projects:

### Direct Creation
Click **+ New Project** on the Projects page.

**Required:**
- Name
- Description
- All four scores

**Optional:**
- Department
- Owner (links to a stakeholder)
- Status
- Initiative link

The form walks you through the scoring. Each dimension has guidelines for what each score means. A project code is auto-generated based on department.

### From DISCO (Two Paths)
**Direct creation:** Approve a proposed initiative in Synthesis view and click **Create Project**. Scores map automatically (impact → roi_potential, feasibility → effort, urgency → alignment).

**Via output document:** Generate an output document (PRD, Evaluation, or Decision Framework) and click **Create Project** on the output. AI pre-fills the project fields with confidence indicators.

See the [DISCO help](./09-disco-initiatives.md#creating-projects) for details.

### From Chat
Use the "Create Project from Chat" action to extract project details from a conversation context.

---

## Project Activation

When moving a project to **Active** status, the activation dialog pre-fills the project name and description from the existing record. You confirm (or edit) rather than re-entering from scratch.

After activation:
- The project receives an automatic **confidence score** from the rubric evaluator
- The **Generate Tasks** button triggers in the Tasks tab, calling the Taskmaster endpoint to propose initial tasks

---

## Status Tracking

Projects move through a simple lifecycle:

1. **Backlog** - Identified but not yet started
2. **Active** - Currently being worked on
3. **Completed** - Done and delivered
4. **Archived** - No longer relevant

Status changes are tracked. You can see the history.

---

## View Modes

Toggle between two views at the top of the page:

**List View** - Simple list of all projects, sorted by tier score
**Tier View** - Projects grouped by tier (1-4) in collapsible sections

---

## Filtering

At the top of the page:
- **Active Only** - Toggle to show only active projects (on by default)
- **By Department** - Focus on a specific area
- **By Status** - See what's in progress vs. completed
- **By Initiative** - Filter to projects linked to a specific DISCO discovery

---

## Linking to Stakeholders

Set an **Owner** to connect a project to a stakeholder.

This lets you:
- See which stakeholders own which projects
- Track who's driving what
- Connect your project pipeline to your relationship map

---

## Linking to Discoveries

Projects can be linked to DISCO discoveries for traceability.

**From the Projects page:**
- Use the Initiative filter to see projects for a specific discovery
- Click a project to open its modal and see/change the linked discovery

**From a DISCO Discovery:**
- Go to the **Projects** tab on the discovery detail page
- See all projects linked to that discovery
- Click a project to navigate to it

This connects your discovery work (DISCO) to your execution tracking (Projects).

---

## How Operator Uses This

The Operator agent has access to your project pipeline.

When you ask Operator about priorities, triage, or what to work on next, it pulls from this data:
- Current projects by tier
- Blocked items
- Status distribution

> "What should I focus on this week?"

Operator can reference your actual pipeline to answer.

---

## The Tier Summary

In Tier View, you'll see projects grouped by tier with counts:
- Tier sections expand/collapse
- Quick visibility into your portfolio distribution

If everything is Tier 4, you might need better projects. If everything is Tier 1, you might need to be more honest about scoring.

---

## Documents Tab

The project detail modal includes a **Documents** tab for managing linked KB documents.

**Link from Initiative:** If the project is linked to a DISCO discovery, a **Link from Initiative** button shows all documents linked to the parent initiative. Select which ones to import into the project without searching the full KB.

**Link from KB:** Browse and link documents from the full Knowledge Base using the same search/filter browser as DISCO.

**Unlink:** Remove document associations (keeps the document in KB).

---

## Goal Alignment Tab

The **Alignment** tab shows how the project aligns with IS FY27 strategic pillars.

**Editing results:** After generating alignment analysis, you can refine results directly:
- **Remove KPI impacts** - Hover over any green KPI chip and click X
- **Remove strategic pillars** - Hover over any pillar card to reveal the X button next to the score
- **Edit pillar rationales** - Hover and click the pencil icon to rewrite

All edits save immediately.

---

## Generate Tasks

The **Tasks** tab includes a **Generate Tasks** button that calls the Taskmaster endpoint to propose tasks based on the project's description and context. Tasks are created directly on the project (not in the inbox).

---

## Editing Projects

Click any project to open its detail view.

You can:
- Update scores (tier recalculates automatically)
- Change status
- Update owner
- Add notes
- View and manage linked tasks

---

## Using Chat with Project Context

Click the **Chat** button in the project detail header to open a conversation with full project context.

This redirects to `/chat?project_id=xxx` with the Project Agent and Taskmaster auto-selected.

**What the Project Agent sees:**
- All project details (title, description, states, scores)
- Linked documents from the Knowledge Base
- Related stakeholders and their roles
- Initiative associations

**Project-scoped RAG search:**
When chatting in a project context, document search is scoped to only documents linked to that project. This means agent responses draw from your project's specific documents rather than the entire Knowledge Base. If no documents are linked, the full KB is used as a fallback.

**Taskmaster auto-selection:**
The Taskmaster agent is automatically included alongside the Project Agent so you can ask about tasks and action items in the same conversation.

**Example questions:**
- "What documents support this project's ROI score?"
- "Summarize the current state and desired state"
- "What risks should we consider for implementation?"
- "Who are the key stakeholders involved?"
- "What tasks are open for this project?"

**Conversation History:**
All conversations with project context are saved and can be filtered in the main chat sidebar. Select the project from the dropdown to see all related conversations.

---

## Kraken: Autonomous Task Evaluation

The Kraken panel appears in the project detail modal when a project has linked tasks. It evaluates which tasks AI can handle autonomously.

### How to Use Kraken

1. Open any project detail modal
2. Scroll to the **Kraken** panel (below tasks)
3. Click **Release the Kraken** to evaluate all linked tasks
4. Review the evaluation results

### Task Categories

Kraken classifies each task into one of three categories:

| Category | Meaning | Example |
|----------|---------|---------|
| **Automatable** | AI can complete this fully | Research summaries, document drafts, analysis |
| **Assistable** | AI can help but needs human input | Strategy documents, stakeholder communications |
| **Manual** | Requires human judgment | Executive decisions, relationship-building, approvals |

Each evaluation includes a confidence level and proposed action describing what Kraken would do.

### Agenticity Score

After evaluation, the project gets an **agenticity score** - the percentage of tasks that are automatable. This helps you understand how much of a project's workload AI can handle.

### Executing Tasks

1. After evaluation, select automatable tasks using the checkboxes
2. Click **Execute N Tasks**
3. Kraken produces output non-destructively:
   - **Task comments** - Detailed work product added as a comment on the task
   - **KB documents** - Longer outputs saved to the Knowledge Base
4. Tasks are marked as completed after successful execution

Kraken uses project documents and KB context for better output quality. Results include web research when relevant.

### Stale Evaluations

If you add or remove tasks after evaluation, Kraken shows a "stale" indicator. Re-run the evaluation to get updated results.

---

## Projects vs Tasks

**Projects** are multi-step initiatives:
- "Implement AI-powered invoice processing"
- "Build a customer service chatbot"
- "Create a data warehouse for analytics"

**Tasks** are atomic actions:
- "Schedule meeting with finance team"
- "Review vendor proposal"
- "Send follow-up email"

Tasks can be linked to projects. When you create a task, you can associate it with a parent project. This helps you track what work supports which strategic initiatives.

---

## Auto-Extraction

Projects are automatically extracted from meeting transcripts via the Discovery Inbox. When you sync meeting notes from your vault:

1. The system scans for multi-step initiatives
2. Candidates appear in the Discovery Inbox
3. You review and accept or reject each candidate
4. Accepted candidates become projects

Tasks extracted from the same meetings can be automatically linked to their parent projects.

---

## Best Practices

**Score honestly.** It's tempting to inflate scores to make something look better. Resist.

**Review tiers regularly.** As you learn more, scores change. A project that seemed like a quick win might turn out to be harder.

**Link to stakeholders.** Every project should have an owner.

**Don't hoard.** Remove projects that aren't going anywhere. A clean pipeline is easier to work with.

**Use status actively.** Move things through the lifecycle. Blocked items need attention or removal.

**Link tasks.** Connect related tasks to projects so you can track execution.

---

## What Projects Are For

Track *multi-step AI initiatives* - strategic work that requires planning and coordination.

**Use Projects for:**
- AI use cases you're implementing
- Automation initiatives
- GenAI applications being built

**Don't use Projects for:**
- Day-to-day tasks (use Tasks)
- Documents and research (use Knowledge Base)
- Stakeholder tracking (use Intelligence)

---

## What's Next?

- [Stakeholder Intelligence](./07-stakeholders.md) - Connect projects to people
- [Tasks](./05-tasks.md) - Track the work that supports projects
- [Chat Interface](./02-chat.md) - Ask Operator about your pipeline
