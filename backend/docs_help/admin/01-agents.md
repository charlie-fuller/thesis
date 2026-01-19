# Agent Management

This is where you shape how agents think and behave.

---

## The Agent Registry

Thesis has 20 agents. Each is defined in the database with:
- Name (internal identifier)
- Display name (what users see)
- Description
- Active status
- Capabilities list

Go to `/admin/agents` to see the full roster.

---

## Agent Instructions

Each agent has a **system instruction** - the XML document that defines:
- Role and persona
- Capabilities and expertise
- Response patterns
- What to avoid
- Example interactions

These instructions live in `/backend/system_instructions/agents/`.

---

## The Instruction Format

We use **Gigawatt v4.0 RCCI Framework** - XML structure with:

```xml
<version>1.0</version>
<role>The agent's core role</role>
<context>Background and domain</context>
<capabilities>What it can do</capabilities>
<instructions>How it should behave</instructions>
<criteria>Quality standards</criteria>
<few_shot_examples>Example interactions</few_shot_examples>
<wisdom>Domain insights</wisdom>
<anti_patterns>What to avoid</anti_patterns>
```

All agents also include shared directives:
- `shared/smart_brevity.xml` - Response format and length limits
- `shared/conversational_awareness.xml` - Multi-agent coherence

---

## Viewing Instructions

1. Go to `/admin/agents`
2. Click an agent
3. View "Current Instruction" tab

You'll see the full XML including:
- Version number
- Last modified date
- Who modified it

---

## Editing Instructions

1. Click **Edit** on an agent
2. Modify the XML
3. Add a version note (what changed)
4. Save

**This creates a new version.** Old versions are preserved for rollback.

---

## Version History

Every edit creates a new version. You can:
- View all versions for an agent
- Compare versions side-by-side
- Rollback to a previous version
- See who made changes and when

**Why versioning?** Because changes to agent behavior can have unexpected effects. You want a way back.

---

## Activating Versions

Each agent has one **active** version - the one actually in use.

When you save an edit, you can choose to:
- Activate immediately
- Save as draft (not active)

To activate a different version:
1. Go to version history
2. Select the version
3. Click "Activate"

---

## The Smart Brevity Directive

All agents include `shared/smart_brevity.xml`. This enforces:

**Response structure:**
1. The Big Thing (1-2 sentences)
2. Why It Matters (1-2 sentences)
3. Key Details (3-5 bullets)
4. Dig-Deeper Links (2-4)

**Word limits:**
- Chat: 100-150 words
- Meeting room: 50-100 words
- Autonomous: 75 words

**Don't change these limits** without understanding the implications. Multi-agent meetings become unreadable with longer responses.

---

## The Conversational Awareness Directive

`shared/conversational_awareness.xml` ensures agents:
- Acknowledge previous speakers
- Build on each other's points
- Don't repeat what others said
- Maintain coherent dialogue

This is what makes meeting rooms feel like actual conversations rather than sequential monologues.

---

## Testing Changes

Before activating changes widely:

1. Make your edit
2. Save as draft (not active)
3. Test in a conversation
4. Review the responses
5. If good, activate

**Or:** Keep a test agent for experimentation.

---

## Common Modifications

**Adjusting persona:**
Edit the `<role>` and `<context>` sections. Keep the personality aligned with the stakeholder perspective.

**Adding capabilities:**
Update `<capabilities>`. Make sure to add corresponding examples in `<few_shot_examples>`.

**Changing response patterns:**
Modify `<instructions>`. Be specific about what you want.

**Adding domain knowledge:**
Update `<wisdom>` with new insights the agent should know.

**Preventing bad behavior:**
Add to `<anti_patterns>` with specific things to avoid.

---

## Best Practices

**Small changes, often.** Don't rewrite entire instructions at once. Iterate.

**Version everything.** Always add a clear version note about what changed.

**Test before activating.** Save as draft, test, then activate.

**Read the guardrails.** [AGENT_GUARDRAILS.md](../AGENT_GUARDRAILS.md) documents the rules. Follow them.

**Don't break brevity.** The 100-word limits exist for good reasons.

**Keep persona alignment.** Each agent represents a specific stakeholder perspective. Maintain that consistency.

---

## Troubleshooting

**Agent giving wrong advice:**
- Check instructions for outdated content
- Review anti_patterns for gaps
- Add examples of correct behavior

**Agent too verbose:**
- Verify smart_brevity.xml is included
- Check max_tokens setting in code
- Add explicit brevity reminders to instructions

**Agent not using KB documents:**
- Check the instruction includes KB context rules
- Verify documents are classified for this agent

**Agent not connecting in meetings:**
- Verify conversational_awareness.xml is included
- Check for directives about building on others' points

---

## What's Next?

- [User Management](./02-users.md) - Managing user access
- [AGENT_GUARDRAILS.md](../AGENT_GUARDRAILS.md) - The complete behavior rules
