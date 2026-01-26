# A3 Problem Solving Framework

**Purpose:** Structured single-page problem definition for every opportunity
**Toyota Origin:** Named after the A3 paper size (11x17") - forces clarity through constraints
**Usage:** Transform vague opportunities into actionable, measurable problem statements

---

## Why A3 Matters for Discovery

Discovery often surfaces "opportunities" that are actually symptoms or wishes. A3 forces structured thinking:

| Discovery Output | Without A3 | With A3 |
|------------------|------------|---------|
| "We need better reporting" | Vague wish added to backlog | Current State: 4 hours/week manual compilation. Target State: Real-time dashboard. Gap: No automated data pipeline. Root Cause: Legacy system lacks API. |
| "Data quality is poor" | General complaint | Current State: 23% error rate. Target State: <2% error rate. Gap: No validation rules. Root Cause: No governance + multiple entry points. |
| "The process is slow" | Subjective pain | Current State: 12-day cycle time. Target State: 3-day cycle time. Gap: 9 days. Root Cause: 4 approval layers + batch processing. |

---

## The A3 Structure

Every opportunity should be expressible as an A3:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     A3: [PROBLEM TITLE]                                      │
│                     Owner: [Name]  Date: [Date]                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. BACKGROUND                    │ 5. COUNTERMEASURES                       │
│ [Why this matters now]           │ [Specific actions to close gap]          │
│                                  │                                          │
├──────────────────────────────────┤                                          │
│ 2. CURRENT STATE                 │                                          │
│ [Measured reality today]         ├──────────────────────────────────────────┤
│                                  │ 6. IMPLEMENTATION PLAN                   │
├──────────────────────────────────┤ [Who, What, When]                        │
│ 3. TARGET STATE                  │                                          │
│ [Specific, measurable goal]      │                                          │
│                                  ├──────────────────────────────────────────┤
├──────────────────────────────────┤ 7. FOLLOW-UP                             │
│ 4. GAP ANALYSIS + ROOT CAUSE     │ [How we'll verify success]               │
│ [Why gap exists - 5 Whys]        │                                          │
│                                  │                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Section-by-Section Guidance

### 1. Background (The "Why Now")

**Purpose:** Establish context and urgency

**Required Elements:**
- Business impact if not addressed
- Why this problem surfaced in discovery
- Connection to strategic priorities

**Template:**
```markdown
### Background

**Business Context:** [How this connects to goals]
**Discovery Source:** [Which session/stakeholder surfaced this]
**Impact of Inaction:** [What happens if we don't address this]
**Urgency Driver:** [Why now, not later]
```

**Good Example:**
> "Sales team spends 15 hours/week on manual forecast compilation, reducing customer-facing time by 20%. This directly impacts Q3 pipeline targets. CFO requires weekly forecasts, making this non-negotiable."

**Bad Example:**
> "We need better forecasting because it would be nice to have."

---

### 2. Current State (Measured Reality)

**Purpose:** Objective, quantified description of today

**Required Elements:**
- Specific metrics (not adjectives)
- Process steps with time/effort
- Who is affected and how

**Template:**
```markdown
### Current State

**Key Metric:** [Quantified measure] (as of [date])
**Process Steps:**
1. [Step] - [Time/Effort] - [Who]
2. [Step] - [Time/Effort] - [Who]

**Pain Distribution:**
- [Stakeholder 1]: [Specific impact]
- [Stakeholder 2]: [Specific impact]

**Current Cost:** [Time/money/effort]
```

**Quantification Requirements:**
| Element | Must Have | Nice to Have |
|---------|-----------|--------------|
| Time | Hours per week/month | Breakdown by step |
| Quality | Error rate, rework % | Error types |
| Money | Cost estimate | ROI baseline |
| People | Who + how many | Skill level required |

---

### 3. Target State (Specific Goal)

**Purpose:** Concrete, measurable end state

**Required Elements:**
- Quantified target (same metrics as Current State)
- Timeline for achievement
- Success criteria

**SMART Check:**
- **S**pecific: Exactly what will be different?
- **M**easurable: Same units as Current State
- **A**chievable: Within scope of initiative
- **R**elevant: Addresses root cause
- **T**ime-bound: When will we know?

**Template:**
```markdown
### Target State

**Target Metric:** [Quantified goal] by [date]
**Success Criteria:**
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] [Measurable criterion 3]

**What "Done" Looks Like:**
[Narrative description of improved state]
```

**Good Example:**
> "Reduce forecast compilation time from 15 hours/week to 2 hours/week (87% reduction) by end of Q2. Success: Forecast accuracy maintains >90% while time drops."

**Bad Example:**
> "Better forecasting that's faster and easier."

---

### 4. Gap Analysis + Root Cause (The "Why")

**Purpose:** Diagnose why the gap exists

**Required Elements:**
- Gap size (Current vs. Target)
- 5 Whys analysis to root cause
- 3M classification (Muda/Mura/Muri)

**5 Whys Template:**
```markdown
### Gap Analysis

**Gap:** [Target] - [Current] = [Difference]

**5 Whys:**
1. Why does this gap exist?
   → [Answer 1]
2. Why [Answer 1]?
   → [Answer 2]
3. Why [Answer 2]?
   → [Answer 3]
4. Why [Answer 3]?
   → [Answer 4]
5. Why [Answer 4]?
   → [ROOT CAUSE]

**3M Classification:**
- MUDA (Waste): [If applicable]
- MURA (Inconsistency): [If applicable]
- MURI (Overburden): [If applicable]

**Root Cause Summary:** [One sentence]
```

**Example:**
```markdown
**Gap:** 15 hrs/week - 2 hrs/week = 13 hrs/week

**5 Whys:**
1. Why do forecasts take 15 hours?
   → Data must be pulled from 4 systems manually
2. Why is data in 4 systems?
   → Each department chose their own tools
3. Why did departments choose separately?
   → No central IT governance for sales tools
4. Why no governance?
   → Rapid growth, no time for standardization
5. Why prioritize speed over standardization?
   → [ROOT] Short-term thinking + no visibility into downstream costs

**3M Classification:**
- MUDA: 8 hours of data transformation (pure waste)
- MURA: Format differences across systems
- MURI: One analyst handles all compilation

**Root Cause:** Decentralized tool decisions + no data integration layer
```

---

### 5. Countermeasures (Actions to Close Gap)

**Purpose:** Specific actions that address root cause

**Required Elements:**
- Actions tied to root cause (not symptoms)
- Prioritization rationale
- Expected impact per action

**Template:**
```markdown
### Countermeasures

| # | Countermeasure | Addresses | Expected Impact | Effort |
|---|----------------|-----------|-----------------|--------|
| 1 | [Action] | [Which root cause] | [Quantified] | [H/M/L] |
| 2 | [Action] | [Which root cause] | [Quantified] | [H/M/L] |

**Sequence Rationale:**
[Why this order - dependencies, quick wins, etc.]
```

**Countermeasure Quality Check:**
- Does it address root cause, not symptom?
- Is it specific enough to implement?
- Can we measure if it worked?
- Is the owner clear?

---

### 6. Implementation Plan (Who/What/When)

**Purpose:** Actionable next steps with ownership

**Template:**
```markdown
### Implementation Plan

| Action | Owner | Start | End | Dependencies |
|--------|-------|-------|-----|--------------|
| [Action 1] | [Name] | [Date] | [Date] | [None/Other actions] |
| [Action 2] | [Name] | [Date] | [Date] | [Action 1] |

**Key Milestones:**
- [ ] [Date]: [Milestone]
- [ ] [Date]: [Milestone]

**Resources Required:**
- [People/budget/tools]
```

---

### 7. Follow-Up (Verification)

**Purpose:** How we'll know if we succeeded

**Template:**
```markdown
### Follow-Up

**Verification Method:** [How we'll measure]
**Check Dates:**
- [ ] [Date]: First check - looking for [X]
- [ ] [Date]: Second check - looking for [Y]
- [ ] [Date]: Final verification - [Target achieved?]

**If Unsuccessful:**
[Plan for iteration - what we'll try next]

**Learning to Capture:**
[What we'll document regardless of outcome]
```

---

## A3 Template for Synthesis Output

Use this template for each major opportunity in synthesis:

```markdown
## A3: [Opportunity Name]

> **One-Line Summary:** [Current State] → [Target State] by addressing [Root Cause]

### Background
[2-3 sentences: why this matters, who raised it, urgency]

### Current → Target → Gap

| Dimension | Current State | Target State | Gap |
|-----------|---------------|--------------|-----|
| [Primary metric] | [Value] | [Value] | [Difference] |
| [Secondary] | [Value] | [Value] | [Difference] |

### Root Cause (5 Whys Summary)
**Surface:** [Symptom stakeholders described]
**Root:** [Actual underlying cause]
**3M Type:** [MUDA/MURA/MURI classification]

### Countermeasures

| Priority | Action | Addresses | Owner | Timeline |
|----------|--------|-----------|-------|----------|
| P1 | [Action] | [Root cause] | [TBD] | [Estimate] |
| P2 | [Action] | [Root cause] | [TBD] | [Estimate] |

### Success Verification
- **Metric:** [What we'll measure]
- **Target:** [Specific value]
- **Check date:** [When we'll verify]
```

---

## A3 Quality Checklist

Before finalizing any A3:

- [ ] Background explains why this matters NOW
- [ ] Current State uses numbers, not adjectives
- [ ] Target State uses same units as Current State
- [ ] Gap is explicitly calculated
- [ ] 5 Whys reaches actual root cause (not stopped at symptom)
- [ ] 3M classification applied
- [ ] Countermeasures address root cause, not symptoms
- [ ] Each countermeasure has an owner
- [ ] Success is measurable
- [ ] Follow-up dates are set

---

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Instead Do |
|--------------|----------------|------------|
| "Better" as Target State | Not measurable | Quantify improvement |
| Stopping 5 Whys at symptom | Treats symptom, not cause | Keep asking until organizational/process root |
| Solution as Current State | Backward reasoning | Describe reality first, solution last |
| Skipping Background | Loses urgency/context | Always anchor to business impact |
| Vague countermeasures | "Improve X" isn't actionable | Specific actions with owners |

---

## A3 Thinking vs. Traditional PRD Thinking

| Dimension | Traditional PRD | A3 Thinking |
|-----------|-----------------|-------------|
| Problem definition | "Users need X" | "Current: [Y], Target: [Z], Gap: [Delta]" |
| Root cause | Often skipped | Mandatory 5 Whys |
| Success criteria | Subjective | Quantified, same units as problem |
| Solutions | Jump to features | Countermeasures tied to root cause |
| Follow-up | "Launch and done" | Verification checkpoints |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-23 | Initial A3 framework for PuRDy v2.5 |
