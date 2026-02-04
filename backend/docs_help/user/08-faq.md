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
Yes. Google Drive, Notion, and local vaults can sync automatically.

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
Yes. Edit a project to update scores. The tier recalculates automatically.

**How does Operator use this?**
Operator has access to your pipeline. When you ask about priorities or triage, it references your actual projects.

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
- Local vault (markdown sync)

**How does vault sync work?**
A file watcher monitors your vault. Changes (create/modify/delete) sync to the KB. Run the watcher: `python -m scripts.vault_watcher --user-id <uuid>`

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

## DISCO Initiatives

**What is DISCO?**
Discovery, Intelligence, Synthesis, Convergence, Operationalize. It's a structured product discovery workflow with 8 specialized agents.

**What's the difference between DISCO and regular Chat?**
Chat is for questions and exploration. DISCO is a structured workflow that takes you from idea through to PRD, with specific agents for each stage.

**What do GO/NO-GO/INVESTIGATE mean?**
These are Triage decisions. **GO** (green) means proceed with discovery. **NO-GO** (red) means stop - not worth pursuing. **INVESTIGATE** (amber) means gather more info before deciding.

**Do I have to run agents in order?**
Generally yes. The workflow is designed to build on itself - later agents need outputs from earlier ones. The system will tell you if you're trying to skip ahead.

**What are bundles?**
After Strategist runs, it proposes feature bundles - groupings of capabilities that make sense together. You approve or reject bundles, and approved ones become PRDs.

---

## Discovery Inbox

**What is the Discovery Inbox?**
An auto-extraction feature that scans your documents and surfaces potential tasks, projects, and stakeholders you might want to track.

**Where do I find it?**
Click **Dashboard** in the navigation, then the **System Health** tab. The **Discovery Inbox** panel shows pending items.

**What does "high" vs "medium" confidence mean?**
**High** confidence (green) means strong signal - explicit mention with clear context. **Medium** confidence (yellow) means reasonable inference but less certainty.

**What happens when I skip something?**
It's dismissed and won't be shown again. If you accidentally skip, the item expires anyway after 2 weeks.

**Can I edit before accepting?**
Yes. When you click **Accept**, a modal opens with pre-filled data. Edit any fields before confirming.

**How do I avoid duplicates?**
The system checks for potential duplicates when you accept. If a match is found, you can link to the existing item instead of creating a new one.

---

## Getting Help

**How do I get help while using the app?**
Click the help icon (question mark) in the top right corner of any page. This opens the help sidebar where you can ask questions about how to use Thesis. The Manual agent will answer based on this documentation.

**Does the help sidebar stay open?**
Yes. The help panel state persists across navigation and sessions. Open it once, and it stays open as you move between pages. Close it when you're done.

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
- [DISCO Initiatives](./09-disco-initiatives.md) - Product discovery workflow
- [Discovery Inbox](./10-discovery-inbox.md) - Auto-extracted candidates
