# Tasks

A Kanban board for tracking the work that comes out of all those conversations.

Because what's the point of great AI insights if you don't actually do anything with them?

---

## The Board

Go to **Tasks** in the navigation.

You'll see four columns:
- **To Do** - Ready to work on
- **In Progress** - Currently happening
- **Blocked** - Waiting on something
- **Done** - Completed

Drag cards between columns to update status.

**Column sorting:** Click the sort icon in any column header to change the order. Options include position (default), priority, due date, newest first, oldest first, and sequence number (for Taskmaster-created plans).

---

## Creating Tasks

Click **+ Add Task** at the top of any column.

**What you can set:**
- **Title** - What needs to be done
- **Description** - Details and context
- **Priority** - P1 (urgent) through P4 (low)
- **Assignee** - Link to a stakeholder or team member
- **Due Date** - When it needs to happen
- **Team** - Department assignment (Engineering, Product, People, etc.)
- **Notes** - Free-text field for additional context, updates, or reminders
- **Project** - Link to an existing project for traceability

**Priority colors:**
- P1: Red (do this now)
- P2: Orange (important)
- P3: Yellow (normal)
- P4: Green (low priority)

---

## Task Cards

Each card shows:
- Title
- Priority badge (colored)
- Assignee (if set)
- Due date (if set)
- Comments count

Click a card to open its detail view.

---

## Task Details

In the detail view, you can:
- Edit all fields
- Add comments
- See status history (who changed what, when)
- View related context

**Comments:** Use these for updates, questions, notes. They persist with the task.

---

## Creating Task Plans with Taskmaster

Ask Taskmaster to create a sequenced plan and it will generate an ordered set of tasks linked to a project.

**How to use it:**
1. In Chat, mention `@taskmaster` or let Auto mode route to it
2. Ask something like: "Create a task plan for the platform migration project"
3. Taskmaster proposes a numbered sequence of tasks with descriptions, priorities, and dependencies
4. Review the proposal cards that appear in chat
5. Click **Accept All** to create them, or review individually

Tasks created by Taskmaster include sequence numbers (01, 02, 03...) so they display in order on the Kanban board. Use the **Sequence** sort option in column headers to see them in plan order.

---

## Extracting Tasks from Meetings

After a meeting room discussion, you can extract action items:
1. Upload a meeting transcript
2. Ask Oracle to analyze it
3. Tasks get suggested based on commitments and action items in the transcript

Or ask directly:
> "What action items came out of this discussion?"

The agents surface what needs to happen next.

---

## Filtering and Searching

Above the board:
- **Search** by task title
- **Filter** by assignee - Cascades by team and project selection
- **Filter** by team - Department filter (Engineering, Product, People, etc.)
- **Filter** by project - See only tasks linked to a specific project
- **Filter** by priority
- **Filter** by date range
- **Filter** by source - Manual, conversation, or agent-created

Filters cascade: selecting a team narrows the assignee dropdown to people in that team. Selecting a project narrows to assignees on that project.

Useful when the board gets full.

---

## Linking Tasks to Projects

Tasks can be linked to projects for better traceability.

**When creating a task:**
- Select a project from the dropdown to associate the task with it

**From a project:**
- Open the project modal and go to the **Tasks** tab
- See all tasks linked to that project
- Create new tasks directly from the project

**From the Tasks page:**
- Use the project filter to see tasks for a specific project
- Click a project link from within task details

This connects your day-to-day work to your strategic initiatives.

---

## Status History

Every status change is tracked:
- When was it moved?
- Who moved it?
- What was the previous status?

Good for understanding how work progresses (or doesn't).

---

## Linking to Stakeholders

When you assign a task to a stakeholder, it connects to your stakeholder tracking. You'll see:
- Tasks assigned to each stakeholder
- Which stakeholders have overdue tasks
- Patterns in task completion

This is where Tasks meets Intelligence.

---

## Best Practices

**Be specific.** "Talk to Finance" is not a task. "Send ROI model to CFO for review by Friday" is.

**Use priorities honestly.** Not everything is P1. If everything is urgent, nothing is.

**Keep it current.** Move cards as work progresses. A stale board is useless.

**Extract tasks from meetings.** Don't let action items die in transcripts.

**Link to stakeholders.** Makes the connection between work and relationships visible.

---

## What Tasks Are For

Tasks track *work* - specific actions that need to happen.

**Use Tasks for:**
- Action items from meetings
- Follow-ups with stakeholders
- Deliverables you've committed to
- Research you need to do

**Don't use Tasks for:**
- Tracking stakeholder relationships (use Intelligence)
- Managing AI projects (use Projects)
- Storing documents (use Knowledge Base)

---

## What's Next?

- [Projects](./06-projects.md) - The AI project pipeline
- [Stakeholder Intelligence](./07-stakeholders.md) - Connect tasks to people
- [Meeting Rooms](./03-meeting-rooms.md) - Where many tasks come from
