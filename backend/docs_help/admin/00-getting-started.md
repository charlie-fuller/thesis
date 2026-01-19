# Admin Getting Started

So you've got admin access to Thesis. Here's what that means and what you can do.

---

## What Admins Do

As an admin, you can:
- Manage agent instructions and versions
- View system health and API status
- Access all user data and conversations
- Configure system settings

The main admin area is at `/admin`.

---

## The Admin Dashboard

Go to `/admin` to see:

**System Health:**
- API connectivity status
- Database connection status
- Service health checks

**Stats:**
- Active conversations
- Document counts
- User activity

**Quick Links:**
- Agent management
- User management
- System logs

---

## Key Admin Pages

**`/admin/agents`**
Manage agent instructions. This is where you edit what agents know and how they behave.

**`/admin/users`** (if configured)
User management. View, edit, manage access.

---

## What You Should Know

**Agent Instructions:**
Each agent has a system instruction defined in XML. These determine personality, behavior, expertise. You can view, edit, and version these instructions.

**Brevity Rules:**
All agents follow strict brevity limits (100-150 words in chat, 50-100 in meetings). This is enforced by both the instructions and token limits.

**The Guardrails:**
[AGENT_GUARDRAILS.md](../AGENT_GUARDRAILS.md) documents all behavioral constraints. Read this before modifying instructions.

---

## Common Admin Tasks

**Viewing agent behavior:**
Go to `/admin/agents` → click an agent → view current instruction

**Editing agent instructions:**
Click Edit → modify the XML → save as new version → activate

**Checking system health:**
Dashboard shows API and database status. If something's red, investigate.

**Reviewing conversations:**
You can access all conversations for troubleshooting and quality review.

---

## What's Next?

- [Agent Management](./01-agents.md) - Deep dive on managing agents
- [User Management](./02-users.md) - Managing user access
