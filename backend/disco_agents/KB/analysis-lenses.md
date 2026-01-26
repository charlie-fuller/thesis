# Analysis Lenses for Deep Interpretation

**Purpose:** Frameworks for moving beyond surface findings to strategic insight
**Usage:** Apply during Layer 2 synthesis to surface "So What?" implications

---

## What Are Analysis Lenses?

Analysis lenses are interpretive frameworks that help translate **what was said** into **what it means**. They prevent synthesis from being mere summarization by forcing deeper questioning.

---

## Lens 1: Surface → Root Cause

**Purpose:** Distinguish symptoms from underlying causes

### Framework

| Surface Finding | Questions to Probe | Possible Root Causes |
|-----------------|-------------------|---------------------|
| Data fragmentation | Why did it fragment? Who decided? | Siloed ownership, no governance, competing priorities |
| Manual workarounds | Why does official process fail? | Policy/tool mismatch, edge cases not handled |
| "We need real-time" | What decisions require real-time? | Fear of missing something, vs. actual latency need |
| Duplicate data entry | Why wasn't this integrated? | Budget constraints, technical debt, ownership gaps |
| Communication breakdowns | Where specifically? | Handoff points, unclear RACI, tool fragmentation |

### Application Template

```markdown
**Surface Finding:** [What was stated]

**Root Cause Analysis:**
- **Why does this exist?** [Historical/organizational reason]
- **Who benefits from status quo?** [Stakeholder interests]
- **What failed before?** [Previous attempts]

**Implication:** Addressing [surface issue] without resolving [root cause]
will likely result in [predicted outcome].
```

---

## Lens 2: Organizational Patterns

**Purpose:** Connect technical findings to organizational dynamics

### Common Patterns

| Finding Pattern | Organizational Signal | Implications |
|-----------------|----------------------|--------------|
| Multiple tools doing same thing | Teams optimized locally, not globally | Need enterprise governance, not just integration |
| "Tribal knowledge" | High-trust culture but risky | Documentation initiative may face resistance |
| Process workarounds | Policy/reality mismatch | Policy update may be easier than automation |
| Data quality issues | No clear data owner | Governance before technology |
| "We tried that before" | Change fatigue or past failures | Need to address history explicitly |

### Application Template

```markdown
**Technical Finding:** [What the data/process shows]

**Organizational Pattern:** This typically indicates [pattern]

**Questions to Validate:**
1. [Question to confirm pattern]
2. [Question to understand history]

**If Pattern Confirmed:**
- Technical solution alone will [likely outcome]
- Additionally need [organizational intervention]
```

---

## Lens 3: Stakeholder Interests

**Purpose:** Understand how different roles experience the same situation

### Stakeholder Perspective Matrix

| Role | Primary Concern | Success Looks Like | Hidden Fear |
|------|-----------------|-------------------|-------------|
| Executive | Strategic impact, ROI | Metrics improve, costs down | Investment doesn't pay off |
| Manager | Team efficiency, delivery | Team productive, deadlines met | Blamed for failures |
| End User | Daily workflow, friction | Job easier, less frustration | More work, learning curve |
| IT/Ops | Stability, maintenance | Runs smoothly, few tickets | Another system to maintain |
| Finance | Budget, predictability | Within budget, clear costs | Unexpected expenses |

### Application Template

```markdown
**Finding:** [What was discussed]

**Stakeholder Lens:**

| Stakeholder | Their Interpretation | Their Concern |
|-------------|---------------------|---------------|
| [Role 1] | [How they see it] | [What worries them] |
| [Role 2] | [How they see it] | [What worries them] |

**Tension to Navigate:** [Role 1] wants [X] while [Role 2] needs [Y].

**Recommendation:** [How to address both]
```

---

## Lens 4: Change Readiness

**Purpose:** Assess likelihood of adoption and resistance

### Readiness Indicators

| Signal | Readiness Level | Implication |
|--------|-----------------|-------------|
| "We've been asking for this" | High | Fast adoption likely |
| "We tried before and failed" | Mixed | Need to address history |
| "That's not how we do things" | Low | Change management critical |
| Workarounds already exist | Medium | Validate workaround users will switch |
| Strong process ownership exists | Variable | Owner could champion or resist |

### Resistance Patterns

| Resistance Type | Signal | Mitigation |
|-----------------|--------|------------|
| Skill-based | "I don't know how to..." | Training, gradual rollout |
| Ownership-based | "That's my job" | Involve early, show evolution not replacement |
| Trust-based | "The data is wrong" | Prove accuracy, allow parallel run |
| Effort-based | "Too much to learn" | Simplify, phase features |
| Political | Silence, passive agreement | Find real objections, address offline |

### Application Template

```markdown
**Proposed Change:** [What would change]

**Readiness Assessment:**

| Factor | Status | Evidence |
|--------|--------|----------|
| Stakeholder buy-in | [High/Med/Low] | [Quote or observation] |
| Previous attempts | [Success/Failed/None] | [What happened] |
| Ownership clarity | [Clear/Unclear] | [Who owns today] |
| Skill readiness | [Ready/Gap] | [Training needed?] |

**Risk Level:** [High/Medium/Low]

**Mitigation Recommendations:**
1. [Action to address specific risk]
2. [Action to address specific risk]
```

---

## Lens 5: Second-Order Effects

**Purpose:** Anticipate downstream consequences of changes

### Framework

```
[Change] → [First-Order Effect] → [Second-Order Effect] → [Third-Order Effect]
```

### Common Second-Order Effects

| First-Order Change | Often Leads To | Which Can Cause |
|--------------------|----------------|-----------------|
| Automate manual process | Reduced headcount need | Knowledge loss, resistance |
| Consolidate data sources | Single point of failure | New availability requirements |
| Add approval workflow | Slower decisions | Workarounds, shadow processes |
| Increase visibility/reporting | Behavior changes to metrics | Gaming, Goodhart's Law |
| Integrate systems | Coupling increases | Cascade failures, harder changes |

### Application Template

```markdown
**Proposed Change:** [What would be implemented]

**Effect Chain:**
1. **Immediate:** [What happens right away]
2. **Secondary:** [What that causes]
3. **Tertiary:** [What that eventually leads to]

**Unintended Consequences to Monitor:**
- [Potential negative outcome]
- [Potential negative outcome]

**Mitigation:** [How to prevent or detect early]
```

---

## Lens 6: The Skeptic's View

**Purpose:** Stress-test findings by arguing the opposite

### Skeptic Questions by Finding Type

| Finding | Skeptic Would Ask |
|---------|-------------------|
| "This will save time" | How much? How do you know? Who verified? |
| "Users want this" | Which users? How many? What's the sample? |
| "This is a priority" | Says who? Compared to what else? |
| "Easy to implement" | What's the complexity they're not seeing? |
| "Everyone agrees" | Who was silent? Who wasn't in the room? |
| "We need it now" | What's actually driving urgency? |

### Application Template

```markdown
**Claim:** [What was stated with confidence]

**Skeptic's Challenge:**
- **Evidence quality:** [How solid is the supporting evidence?]
- **Alternative explanation:** [What else could explain this?]
- **Who benefits:** [Whose interests does this claim serve?]
- **What's missing:** [What wasn't said?]

**Verdict:** [Claim holds / Needs validation / Likely overstated]

**If Needs Validation:** [Specific question to ask]
```

---

## Lens Application Checklist

When synthesizing findings, apply at least 3 lenses:

- [ ] **Surface → Root Cause:** Have I identified underlying causes, not just symptoms?
- [ ] **Organizational Patterns:** Have I connected technical issues to organizational dynamics?
- [ ] **Stakeholder Interests:** Have I understood different perspectives?
- [ ] **Change Readiness:** Have I assessed adoption likelihood and resistance?
- [ ] **Second-Order Effects:** Have I anticipated downstream consequences?
- [ ] **Skeptic's View:** Have I stress-tested confident claims?

---

## Quick Reference: When to Use Each Lens

| Situation | Primary Lens | Secondary Lens |
|-----------|--------------|----------------|
| Multiple stakeholders disagree | Stakeholder Interests | Organizational Patterns |
| "We tried this before" | Change Readiness | Surface → Root Cause |
| Highly confident claims | Skeptic's View | Second-Order Effects |
| Process/system problems | Surface → Root Cause | Organizational Patterns |
| Automation proposals | Second-Order Effects | Change Readiness |
| Data/integration projects | Organizational Patterns | Stakeholder Interests |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-22 | Initial analysis lenses for PuRDy v2.2 |
