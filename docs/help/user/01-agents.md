# Understanding the Agent System

Here's something I keep thinking about: most AI tools give you one voice, one perspective. It's like asking a single consultant for advice on everything from your security posture to your change management strategy to your legal exposure.

That's... not how expertise works in the real world.

Thesis has twenty agents. Each one thinks differently. Has different concerns. Notices different things. And that's the point.

**Finding the agent roster:** Go to **Intelligence** in the navigation, then click the **Agents** tab. You'll see all agents with their stats - versions, KB docs, chats, and meetings.

---

## The Big Idea

Each agent is designed around a specific stakeholder perspective or domain. When you ask Capital about an AI initiative, you're getting the finance lens - ROI, business case, budget justification. Ask Guardian the same question and suddenly you're in security and compliance territory.

Neither is wrong. They're just seeing different parts of the elephant.

What gets interesting is when you put them in a room together.

---

## The Agent Roster

### Meta-Agents (The Facilitators)

These two show up in every meeting room. They're not domain experts - they're orchestrators.

**Facilitator**
The one who runs the room. Welcomes you, clarifies what you're trying to figure out, routes questions to the right specialists. Facilitator doesn't pretend to know the answers - its job is to make everyone else brilliant.

*When you see it:* In meeting rooms, orchestrating the conversation.

**Reporter**
Creates the summaries and documentation you can actually share with stakeholders. Uses domain labels instead of agent names (so your report says "Financial analysis shows..." not "Capital said..."). Single voice for all documentation.

*When to ask:* "Summarize this discussion" or "Create an executive brief"

---

### Stakeholder Perspectives (The Core Team)

These agents are aligned to actual stakeholder personas - the people you're likely working with in an enterprise AI initiative.

**Atlas** (Research)
The researcher. Tracks GenAI implementation research, consulting approaches, benchmarks. When the knowledge base doesn't have an answer, Atlas goes looking - it actually performs web research using credibility-tiered sources.

*Best for:* "What does McKinsey say about AI governance?" or "What benchmarks exist for AI adoption rates?"

**Capital** (Finance)
Thinks in spreadsheets and ROI. Business case development, budget justification, SOX compliance, financial risk. If it involves money, Capital has opinions.

*Best for:* "Help me build a business case" or "What's the ROI framework for this project?"

**Guardian** (IT/Governance)
The security person. Compliance, vendor evaluation, shadow IT concerns, governance frameworks. Guardian worries so you don't have to - but also so you remember to.

*Best for:* "What security considerations exist for this approach?" or "How do we evaluate this vendor?"

**Counselor** (Legal)
Contracts, liability, data privacy, AI-specific legal risks. The voice that says "have we considered the legal implications?"

*Best for:* "What legal risks should we consider?" or "How should the contract address AI liability?"

**Sage** (People)
Change management. Adoption. Human flourishing. Sage is the one who asks "but how will people actually experience this?" - the perspective that's often missing from technical discussions.

*Best for:* "How do we drive adoption?" or "What change management considerations exist?"

**Oracle** (Meeting Intelligence)
Analyzes meeting transcripts. Extracts stakeholder dynamics, sentiment, evidence-based insights. Upload a transcript, Oracle tells you what actually happened.

*Best for:* Transcript analysis, stakeholder sentiment extraction

---

### Consulting/Implementation Agents

**Strategist** (Executive Strategy)
C-suite engagement, organizational politics, governance structures. How to navigate the executive layer.

*Best for:* "How do we get executive buy-in?" or "What's the governance structure for this initiative?"

**Architect** (Technical)
Enterprise AI patterns, RAG architectures, integration approaches, build vs. buy decisions. The technical lens.

*Best for:* "What architecture should we use?" or "Build vs. buy for this use case?"

**Operator** (Business Operations)
Process optimization, automation projects, operational metrics. Also manages the **Project Triage** pipeline - scoring and prioritizing AI projects.

*Best for:* "How do we optimize this process?" or "Which projects should we prioritize?"

**Pioneer** (Innovation/R&D)
Emerging technology, hype filtering, maturity assessment. Pioneer gets excited about new things but also knows how to distinguish signal from noise.

*Best for:* "What emerging technologies should we watch?" or "Is this technology mature enough?"

---

### Internal Enablement Agents

**Catalyst** (Communications)
AI messaging strategy, employee engagement, addressing AI anxiety. How to communicate about AI internally.

*Best for:* "How do we message this initiative?" or "How do we address AI anxiety?"

**Scholar** (Learning & Development)
Training programs, champion enablement, adult learning principles. How to build AI capability in the org.

*Best for:* "How do we train people on this?" or "What does a champion program look like?"

**Echo** (Brand Voice)
Voice analysis, style profiling, AI emulation guidelines. Understanding and preserving brand voice.

*Best for:* "Analyze this writing style" or "How do we maintain voice consistency?"

**Glean Evaluator** (Platform Fit)
Specifically for evaluating whether Glean (enterprise search platform) is the right tool for a use case. Connector analysis, build vs. buy for search.

*Best for:* "Can Glean handle this?" or "What connectors are available?"

**Compass** (Career Coach)
Win capture, performance tracking, check-in preparation, strategic alignment with company priorities. Your career development partner.

*Best for:* "Help me document this win" or "Prepare me for my check-in"

---

### Task Management

**Taskmaster** (Task Planning)
Creates sequenced task plans from chat conversations. Analyzes project context to propose ordered tasks with priorities, descriptions, and dependencies. Tasks appear as proposal cards you can accept or reject.

*Best for:* "Create a task plan for this project" or "Break this initiative into action items"

---

### Context-Aware Agents

These agents are specialized for conversations within a specific project or initiative context. They're auto-selected when you navigate to chat from a project or initiative.

**Project Agent**
Your project specialist. Understands project structure, scoring rubrics, linked documents, and stakeholder relationships. When you chat with a project's context, this agent sees everything about that project without you having to explain it.

*Best for:* Questions about a specific project's scores, status, linked documents, or implementation approach. Access via the Chat button in any project detail modal.

**Initiative Agent**
Your DISCO initiative specialist. Knows the discovery workflow, all agent outputs, linked documents, and PuRDy methodology. Can guide you through the discovery process and help extract project ideas from conversations.

*Best for:* Questions about a specific initiative's discovery progress, agent outputs, or methodology. Access via the Chat button on any initiative detail page.

---

### Systems/Coordination

**Nexus** (Systems Thinking)
Interconnections, feedback loops, leverage points, unintended consequences. The one who asks "what happens when this interacts with that?"

*Best for:* "What are the system effects?" or "What unintended consequences should we consider?"

**Coordinator** (The Router)
You don't talk to Coordinator directly. It works behind the scenes in Auto mode, analyzing your query and routing it to the best specialist(s).

---

## How to Choose

Here's my mental model:

**Money question?** → Capital
**Security/compliance?** → Guardian
**Legal risk?** → Counselor
**People/adoption?** → Sage
**Research needed?** → Atlas
**Technical architecture?** → Architect
**Process/operations?** → Operator
**Emerging tech?** → Pioneer
**Executive politics?** → Strategist
**Training/enablement?** → Scholar
**Internal comms?** → Catalyst

**Not sure?** Use Auto mode. Or put a few of them in a meeting room and see what emerges.

---

## The @Mention Trick

You can invoke agents inline with `@agentname`. This is useful when you want a specific perspective mid-conversation:

> "I love this ROI analysis from Capital, but @guardian what security considerations should we add?"

> "Before we finalize this recommendation, @nexus what system effects should we consider?"

It's like being able to tap someone on the shoulder and say "hey, what do you think?"

---

## Multi-Agent Dynamics

Here's where it gets interesting. In meeting rooms, agents don't just take turns. They:

- **Build on each other's points** - "Building on what Sage said about adoption..."
- **Challenge each other** - "I hear Guardian's concern, but from the business side..."
- **Connect across domains** - "The security issue Counselor raised has a financial dimension too"
- **Defer when appropriate** - "That's really Architect's territory"

They're not isolated experts giving disconnected monologues. They're colleagues thinking together.

---

## Brevity Rules

One thing you'll notice: the agents are brief. This is intentional.

- Chat responses: 100-150 words max
- Meeting room responses: 50-100 words max
- Autonomous discussion: 75 words max

The idea is that every response has **one key insight**, and if you want more detail, you can ask for it. It's easier to expand than to wade through paragraphs looking for the point.

**Dig Deeper**: Most responses include links like `[Learn more](dig-deeper:section)`. Click these to get elaboration on specific points.

---

## What's Next?

- [Using Meeting Rooms](./03-meeting-rooms.md) - Where multi-agent collaboration really shines
- [Chat Interface Guide](./02-chat.md) - Master the one-on-one conversations
- [Setting Up Your Knowledge Base](./04-knowledge-base.md) - Make all the agents smarter
