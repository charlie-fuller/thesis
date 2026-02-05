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

### From DISCO PRD
When a DISCO initiative produces an approved PRD, click **Create Project** on the PRD output. AI pre-fills the project fields with confidence indicators. See the [DISCO help](./09-disco-initiatives.md#creating-projects-from-prds) for details.

### From Chat
Use the "Create Project from Chat" action to extract project details from a conversation context.

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
- **By Initiative** - Filter to projects linked to a specific DISCo initiative

---

## Linking to Stakeholders

Set an **Owner** to connect a project to a stakeholder.

This lets you:
- See which stakeholders own which projects
- Track who's driving what
- Connect your project pipeline to your relationship map

---

## Linking to Initiatives

Projects can be linked to DISCo initiatives for traceability.

**From the Projects page:**
- Use the Initiative filter to see projects for a specific initiative
- Click a project to open its modal and see/change the linked initiative

**From a DISCo Initiative:**
- Go to the **Projects** tab on the initiative detail page
- See all projects linked to that initiative
- Click a project to navigate to it

This connects your discovery work (DISCo) to your execution tracking (Projects).

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

This redirects to `/chat?project_id=xxx` with the Project Agent auto-selected.

**What the Project Agent sees:**
- All project details (title, description, states, scores)
- Linked documents from the Knowledge Base
- Related stakeholders and their roles
- Initiative associations

**Example questions:**
- "What documents support this project's ROI score?"
- "Summarize the current state and desired state"
- "What risks should we consider for implementation?"
- "Who are the key stakeholders involved?"

**Conversation History:**
All conversations with project context are saved and can be filtered in the main chat sidebar. Select the project from the dropdown to see all related conversations.

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
