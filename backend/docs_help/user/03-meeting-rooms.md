# Meeting Rooms

This is where things get interesting.

A meeting room puts multiple agents in conversation together. Not just sequential responses, but actual dialogue. They build on each other's points, push back, connect ideas across domains.

It's the closest thing to having a room full of specialists actually think together.

---

## Creating a Meeting Room

**From the Meeting Rooms page:**
1. Click **Meeting Room** in the navigation
2. Click **New Meeting**
3. Give it a name (optional - it'll auto-generate one)
4. Select 2-5 agents

**From the Chat interface:**
1. Go to **Chat** in the navigation
2. Click the **Meeting Rooms** tab in the sidebar
3. Click **New Meeting Room**
4. Configure and create

**Which agents?** Think about who would actually be in this meeting in real life:
- Security review? Guardian, Architect, Counselor, maybe Strategist for the political angle
- Business case development? Capital, Operator, Sage (for adoption considerations)
- Technology evaluation? Pioneer, Architect, Guardian, Operator

You can always add or remove agents later.

---

## The Facilitator and Reporter

Two agents are always present, even if you don't select them:

**Facilitator** runs the meeting:
- Welcomes you and clarifies your intent
- Invites relevant agents to speak (one at a time)
- Weaves threads together
- Keeps the conversation balanced

**Reporter** handles documentation:
- Creates summaries on request
- Uses domain labels ("Financial analysis shows...") not agent names
- Produces shareable output

You don't need to manage turn-taking. Facilitator handles it.

---

## How Conversations Flow

Here's how a typical meeting room conversation works:

1. **You ask a question or pose a topic**
2. **Facilitator** welcomes you, clarifies if needed, invites the first relevant agent
3. **First agent** gives their perspective (50-100 words)
4. **Facilitator** bridges to the next perspective
5. **Second agent** responds, often building on the first
6. **Process continues** with natural handoffs

The key thing: agents don't just take turns. They connect.

> **Capital**: "The ROI looks strong at 18 months, but the initial investment is steep."
> **Sage**: "Building on Capital's point about that steep investment - we need to think about how we'll maintain momentum during the pre-ROI period. People get skeptical when they don't see results."

That connection is intentional. They're thinking together, not just presenting sequentially.

---

## Autonomous Discussion Mode

This is the thing I keep coming back to.

**The Autonomous Panel** appears in every meeting room and includes:
- **Topic input** - Enter a discussion topic
- **Turn count** - Set how many turns before stopping (or unlimited)
- **Start/Stop buttons** - Control the discussion

Enter your topic and click **Start**:
> "Discuss the risks and opportunities of implementing customer-facing AI without human review."

Then watch. Click **Stop** at any time to end the autonomous discussion.

The agents discuss amongst themselves. They:
- Ask each other questions
- Challenge assumptions
- Make connections you didn't see
- Build towards synthesis

**The discourse moves they use:**
1. **Question** - Clarifying questions (most common)
2. **Connect** - Link ideas across domains
3. **Challenge** - Push back with alternative perspectives
4. **Extend** - Build on another's point
5. **Synthesize** - Combine viewpoints (usually at the end)

**You can interject anytime.** Just type. The agents will incorporate your input and continue.

**When to use it:**
- Complex topics with no obvious answer
- When you want to surface tensions
- When you want to see what emerges
- When you're not even sure what the question is yet

---

## Speaking Order Display

During autonomous discussion, you'll see a display showing the discussion flow. Who's speaking, who's been invited, the thread being followed.

This helps you track what's happening without getting lost.

---

## Getting a Summary

At any point, ask:
> "Reporter, summarize this discussion"
> "What are the key takeaways?"
> "Create an executive brief"

Reporter will synthesize the entire conversation into shareable output with domain labels (not agent names) so you can share it with stakeholders.

---

## Exporting to Knowledge Base

You can export meeting conversations to your Knowledge Base for future reference:

1. Click the **Export to KB** button in the meeting room header
2. Confirm the export
3. The conversation becomes a searchable KB document

This lets agents reference past meeting discussions in future conversations.

---

## Context from Your Knowledge Base

Meeting rooms pull context from your Knowledge Base automatically. Before agents respond, the system:
1. Searches your documents for relevant content
2. Queries the stakeholder graph for related concerns and relationships
3. Injects this context into each agent's response

You'll see **Context Sources** appear before responses - the documents and graph data being referenced.

This is why uploading your documents matters. Generic AI advice versus advice grounded in *your* actual documents and stakeholder context.

---

## Conversation Patterns That Work

**The Problem Exploration:**
Pose a fuzzy problem you're wrestling with. Let autonomous discussion surface the dimensions you haven't considered.

**The Decision Framework:**
"Help me decide between Option A and Option B" - agents will advocate, challenge, and help you think through trade-offs.

**The Risk Surface:**
"What could go wrong with this approach?" - Guardian, Counselor, and Nexus will find things you missed.

**The Stakeholder Simulation:**
"How would our CFO react to this proposal?" - Capital can role-play stakeholder perspectives.

**The Action Planning:**
"We've decided on X. What's our implementation plan?" - Operator, Architect, and Sage can build it out.

---

## Best Practices

**Pick the right mix.** Don't just grab everyone. Think about who would actually be in this meeting.

**Let it breathe.** In autonomous mode, let the discussion run for a few rounds before interjecting. See what emerges.

**Ask for synthesis.** Periodically ask Reporter to summarize so you can track the threads.

**Don't over-constrain.** The best discussions happen when you pose the topic and let agents explore rather than asking a narrow question.

**Use it for messy problems.** Meeting rooms shine when there's no obvious answer. For simple questions, chat is faster.

---

## The Meeting List

Your meetings persist. You'll see them listed with:
- Meeting name
- Participant agents
- "Autonomous" badge if autonomous discussion was used (with tooltip showing the topic)
- Last activity timestamp

Return to any meeting to continue the conversation.

---

## What's Next?

- [Knowledge Base](./04-knowledge-base.md) - Make meeting rooms smarter with your documents
- [Stakeholder Intelligence](./07-stakeholders.md) - Connect meetings to your stakeholder tracking
- [Agent Guide](./01-agents.md) - Understand each agent's perspective
