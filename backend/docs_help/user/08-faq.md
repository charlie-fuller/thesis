# Frequently Asked Questions

Quick answers to common questions. If you're looking for something specific, this is the place.

---

## Agents

**How many agents are there?**
Twenty. See the [Agent Guide](./01-agents.md) for the full roster.

**Which agent should I use?**
Depends on the question. Use Auto mode to let the Coordinator decide, or pick based on domain:
- Money → Capital
- Security → Guardian
- Legal → Counselor
- People → Sage
- Research → Atlas
- Technical → Architect

**Can I use multiple agents at once?**
Yes. In Chat, select up to 3 agents. In Meeting Rooms, select 2-5.

**What's the @mention syntax?**
Type `@agentname` in your message to invoke a specific agent inline. Like: "Great point from Capital. @guardian what are the security implications?"

---

## Chat

**How long do conversations last?**
Conversations persist until you delete them. Come back anytime.

**Can agents remember things across conversations?**
They have persistent memory via Mem0 for things like preferences and decisions, but detailed conversation context is per-conversation.

**Why are responses so short?**
Intentional. We call it Smart Brevity. Each response has one key insight. Use "dig deeper" links for more detail.

**What if the agent's response goes in the wrong direction?**
Send a new message to interrupt. Clarify what you actually wanted.

---

## Meeting Rooms

**How is a meeting room different from chat?**
Chat is one-on-one (or one-to-few). Meeting rooms have multiple agents in actual dialogue - they respond to each other, not just to you.

**What is autonomous discussion?**
Agents discuss a topic amongst themselves. You pose the topic, they debate it. You can interject anytime.

**Can I add agents to an existing meeting?**
Yes. Edit the meeting to add or remove participants.

**How do I get a summary?**
Ask: "Reporter, summarize this discussion" or "What are the key takeaways?"

---

## Knowledge Base

**What file types can I upload?**
PDF, DOCX, Markdown, CSV, JSON, XML, plain text.

**How does auto-classification work?**
The system analyzes content and tags documents with relevant agents. High confidence (>80%) is auto-tagged. Ambiguous results get flagged for your review.

**Can I connect external sources?**
Yes. Google Drive, Notion, and Obsidian vaults can sync automatically.

**How do I know if agents are using my documents?**
Responses will cite sources: "According to your Security Policy document..."

---

## Tasks

**What's the difference between Tasks and Opportunities?**
Tasks are specific actions that need to happen. Opportunities are potential AI initiatives you're evaluating.

**Can I extract tasks from meetings?**
Yes. Upload a transcript or ask the agents to identify action items from a discussion.

**How do I track who's responsible?**
Assign tasks to stakeholders. The linkage shows in both Task and Intelligence views.

---

## Opportunities

**What determines the tier?**
Total score across four dimensions: ROI Potential, Implementation Effort, Strategic Alignment, Stakeholder Readiness. Each scored 1-5. Total 16-20 = Tier 1, 12-15 = Tier 2, etc.

**Can scores change?**
Yes. Edit an opportunity to update scores. The tier recalculates automatically.

**How does Operator use this?**
Operator has access to your pipeline. When you ask about priorities or triage, it references your actual opportunities.

---

## Stakeholders

**How does engagement level get calculated?**
Based on interaction patterns. Champions need 5+ interactions AND commitment or support signals. See [Stakeholder Guide](./07-stakeholders.md) for full criteria.

**What's the engagement trend chart?**
A visualization showing how engagement levels shift over time across your stakeholder map.

**Can Oracle auto-extract stakeholders from transcripts?**
Yes. Upload a meeting transcript, Oracle identifies participants and can link them to existing records.

---

## Integrations

**What can I connect?**
- Google Drive (documents sync)
- Notion (pages sync)
- Obsidian vaults (local markdown sync)

**How does Obsidian sync work?**
A file watcher monitors your vault. Changes (create/modify/delete) sync to the KB. Run the watcher: `python -m scripts.obsidian_watcher --user-id <uuid>`

---

## Troubleshooting

**Agents aren't referencing my documents**
- Check the document was uploaded successfully (KB page)
- Verify classification (is it tagged for the right agents?)
- Make sure you're asking questions related to the document's content

**Meeting room feels chaotic**
- Try fewer agents (2-3 instead of 5)
- Let Facilitator manage turn-taking
- Ask for synthesis: "Reporter, what have we established so far?"

**Stakeholder data isn't updating**
- Check if engagement calculation has run (weekly, Sunday 4 AM UTC)
- Manually update last contact date
- Upload recent transcripts for Oracle analysis

**Responses are too generic**
- Upload more context documents
- Be more specific in your questions
- Make sure documents are classified for the right agents

---

## Getting Help

**Where's the main documentation?**
[CLAUDE.md](/CLAUDE.md) is the primary reference for developers. Help docs (what you're reading) cover user features.

**Agent behavior seems wrong**
[AGENT_GUARDRAILS.md](../AGENT_GUARDRAILS.md) documents the rules agents follow. If behavior seems off, that's the reference.

**Found a bug?**
Note what happened, what you expected, and any error messages. Report to your administrator.

---

## What's Next?

- [Quick Start](./00-quick-start.md) - The 5-minute intro
- [Agent Guide](./01-agents.md) - Deep dive on each agent
- [Meeting Rooms](./03-meeting-rooms.md) - Where the magic happens
