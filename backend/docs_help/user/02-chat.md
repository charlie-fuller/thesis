# Using the Chat Interface

The chat interface is where most of your one-on-one conversations with agents happen. Simple idea, but there's more going on than meets the eye.

---

## The Basics

Click **Chat** in the navigation. Type a message. Get a response.

Easy enough. But here's what makes it interesting:

---

## Agent Selection

Above the message input, you'll see the **Agent Selector**.

**Auto Mode** (the default): The Coordinator analyzes your query and routes it to the most appropriate specialist. Ask about ROI and you'll probably get Capital. Ask about security and Guardian shows up.

**Manual Selection**: Click the dropdown and pick specific agents. You can select up to three. Each will respond to your query from their perspective.

**Agent stickiness**: Once an agent is selected (manually or via routing), subsequent messages in the same conversation stay with that agent rather than re-routing every time. This gives you a more natural back-and-forth. Start a new conversation or manually switch agents to change.

**When to use Auto vs. Manual:**
- Auto when you're not sure who should answer
- Manual when you have a specific question for a specific domain
- Manual with multiple agents when you want different perspectives on the same question

---

## The @Mention Syntax

Here's a trick that changes how you interact with the system.

Type `@` followed by an agent name to invoke them inline:

> "This architecture looks solid, but @guardian what security concerns should we address?"

> "@capital can you help me turn this into a business case?"

> "I like Sage's adoption plan. @architect what technical dependencies should we consider?"

It's like being able to tap someone on the shoulder mid-conversation. The agent you mention will respond to that specific context.

**Available mentions:**
- `@atlas`, `@capital`, `@guardian`, `@counselor`, `@sage`, `@oracle`
- `@strategist`, `@architect`, `@operator`, `@pioneer`
- `@catalyst`, `@scholar`, `@echo`, `@compass`
- `@nexus`, `@facilitator`, `@reporter`
- `@glean` (for Glean Evaluator)
- `@taskmaster` (for task plan creation)
- `@project_agent`, `@initiative_agent` (for context-specific discussions - initiative_agent is the Discovery Agent)

---

## Agent Badges

Every response shows a badge indicating which agent answered. This matters because:

1. You know whose perspective you're getting
2. You can follow up with the same agent or switch to another
3. In multi-agent responses, you can see who said what

---

## Conversation History

Your conversations persist. Come back tomorrow and pick up where you left off.

The sidebar shows your recent conversations. Titles are auto-generated from your first message.

**Pro tip:** Start a new conversation for different topics. It helps both you and the agents maintain context.

---

## Project and Initiative Context

The chat interface supports context-aware conversations tied to specific projects or initiatives.

**Filter by Context:**
At the top of the left sidebar, you'll see two dropdowns:
- **Project** - Filter conversations by project
- **Initiative** - Filter conversations by DISCO initiative

When you select a context:
- The conversation list filters to show only conversations for that project/initiative
- New conversations automatically associate with the selected context
- Conversations show a colored badge indicating their context (blue for projects, purple for initiatives)

**Context-Aware Agents:**
When you start a conversation with project or initiative context, the system auto-selects specialized agents:
- **Project Agent** - Understands project structure, scores, linked documents, and lifecycle
- **Discovery Agent** - Receives full initiative context (throughline, agent outputs, linked documents, value alignment) and can propose structured framing

**URL Navigation:**
You can navigate directly to context-filtered chat:
- `/chat?project_id=xxx` - Opens chat with project context and Project Agent selected
- `/chat?initiative_id=xxx` - Opens chat with initiative context and Discovery Agent selected

**From Projects and Initiatives:**
- In a project modal, click the **Chat** button in the header to start a conversation with that project's context
- On an initiative page, click the **Chat** button in the header to chat with full initiative context

---

## Dig Deeper Links

Most agent responses include links formatted like `[Learn more](dig-deeper:topic)`.

Click these to get elaboration on specific points. It's a way to keep initial responses concise while still letting you drill into detail when you want it.

---

## Knowledge Base Context

When you upload documents to the Knowledge Base, agents automatically reference them in their responses.

You'll see something like:
> "According to your Security Policy document, the required controls include..."

The agents cite their sources. They're not making things up - they're pulling from your actual documents.

**Agent-Filtered RAG**: Each agent prioritizes documents tagged as relevant to their domain. Guardian pulls security docs. Capital pulls financial analyses. The system learned which documents matter for which questions.

---

## Response Structure

Agents follow a consistent format (we call it Smart Brevity):

1. **The Big Thing** - Key insight in 1-2 sentences
2. **Why It Matters** - Business impact
3. **Key Details** - 3-5 bullets or a small table
4. **Dig Deeper Links** - 2-4 links for expansion

This isn't arbitrary. It's designed so you can scan quickly and decide whether to go deeper.

---

## Asking Good Questions

I've noticed some patterns in what works well:

**Specific beats vague:**
- Vague: "Tell me about AI governance"
- Specific: "What governance structure should we use for a customer-facing AI chatbot in financial services?"

**Context helps:**
- Without: "How do we build a business case?"
- With: "We're proposing a $500K AI initiative for customer service automation. Our CFO wants to see ROI in 18 months. Help me build the business case."

**Name the domain:**
- Instead of hoping the system routes correctly, just ask: "@capital how do we justify this investment to finance?"

---

## Starting Fresh vs. Continuing

**New conversation** when:
- Different topic
- Different project
- You want a clean slate

**Continue conversation** when:
- Following up on previous discussion
- Iterating on a deliverable
- Building on earlier context

The agents remember context within a conversation but not across conversations. (Though they do have persistent memory through Mem0 for things like your preferences and previous decisions.)

---

## Streaming Responses

Responses stream in real-time. You'll see text appearing as the agent generates it.

If a response is going in the wrong direction, you can interrupt by sending a new message.

---

## Common Patterns

**The Perspective Gather:**
Ask the same question with different agents selected to see how different stakeholders would view it.

**The Deep Dive:**
Start with Auto mode to get a quick answer, then follow up with `@agentname` to dig into specific aspects.

**The Reality Check:**
After getting an optimistic answer from one agent, invoke `@guardian` or `@nexus` to surface risks and unintended consequences.

**The Document Grounding:**
Upload relevant documents first, then ask questions. The responses become much more specific to your situation.

---

## What's Next?

- [Meeting Rooms](./03-meeting-rooms.md) - When one-on-one isn't enough
- [Knowledge Base](./04-knowledge-base.md) - Making agents smarter with your documents
- [Agent Guide](./01-agents.md) - Deep dive on each agent's capabilities
