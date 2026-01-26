# Triage Questions

Quick intake questions for the 5-10 minute triage phase.

## Purpose

Rapidly assess whether a request is worth pursuing and estimate effort tier.

---

## Core Triage Questions

Ask these in order. Keep it conversational.

### 1. The Problem
> "In 1-2 sentences, what's the problem you're trying to solve?"

**Listen for**: Clarity, specificity, actual pain vs. nice-to-have

### 2. Who's Affected
> "Who feels this pain? Which team, and roughly how many people?"

**Listen for**: Team name, headcount, frequency of impact

### 3. Current Workaround
> "How are you handling this today?"

**Listen for**: Manual process, spreadsheets, copy-paste, tribal knowledge
- If no workaround exists, that's a signal (either critical or not actually needed)

### 4. Urgency
> "Is there a deadline driving this, or is it ongoing friction?"

**Listen for**: Hard dates (compliance, launch), soft preferences, "ASAP" (dig deeper)

### 5. Strategic Alignment
> "Does this tie to any FY27 priorities?"

FY27 Priorities:
- Accelerating customer deployment
- Personalization everywhere
- Enterprise adoption (wall-to-wall)
- Next Gen platform (fall launch)

**Listen for**: Direct tie vs. indirect vs. none

### 6. Quick ROI Estimate
> "Roughly how much time does this cost you today? How often?"

**Calculate**: `time saved × frequency × people = ROI potential`

Example:
- 30 min/week × 52 weeks × 10 people = 260 hours/year saved
- At $75/hr fully loaded = ~$20K/year value

---

## Red Flags (Probe Deeper)

| Signal | What to Ask |
|--------|-------------|
| "We need AI" | "What would AI do that you can't do today?" |
| Vague problem | "Can you walk me through a specific example?" |
| Solution-first | "Let's back up - what's the underlying problem?" |
| "ASAP" urgency | "What happens if we don't do this by [date]?" |
| No current workaround | "How critical is this if you've been living without it?" |
| Many stakeholders | "Who's the decision maker?" |

---

## Complexity Signals

### Simple (<8 hours)
- Single system involved
- Clear input → output
- No approvals needed
- Glean agent could handle it

### Medium (8-40 hours)
- 2-3 systems involved
- Some data transformation
- Single team affected
- Clear success criteria

### Complex (>40 hours)
- 4+ systems involved
- Cross-functional stakeholders
- Data sensitivity concerns
- Unclear requirements
- Needs ELT sponsor

---

## Output: Triage Summary

After questions, produce:

```markdown
## Triage Summary

**Request**: [one-line summary]
**Requester**: [name/team]
**Date**: [today]

### Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Strategic Fit | High/Med/Low | |
| Effort | Simple/Medium/Complex | |
| ROI Potential | High/Med/Low | |
| Integration Risk | High/Med/Low | |

### Recommendation

**Decision**: GO / NO-GO / NEEDS INFO
**Tier**: ELT Sponsor / Solutions Partner / Self-Serve
**Next Step**: [specific action]

### Rationale
[2-3 sentences]
```

---

## Routing Rules

| Tier | Criteria | Route To |
|------|----------|----------|
| ELT Sponsor | ≥40 hours OR cross-functional OR strategic | Michael's BRD process |
| Solutions Partner | 8-40 hours, clear scope | Charlie/Tyler |
| Self-Serve | <8 hours, Q&A, simple agent | Recommend Glean |
| Decline | Low ROI + Low strategic fit | Politely defer |
