# Muda/Mura/Muri Diagnosis Framework

**Purpose:** Precise root cause taxonomy for process pain points
**Toyota Term:** "3M" - The three enemies of efficiency
**Usage:** Apply during synthesis to transform vague "pain points" into actionable diagnoses

---

## Why 3M Matters for Discovery

When stakeholders say "we have pain points" or "the process is broken," they're describing symptoms. The 3M framework provides diagnostic precision:

| Stakeholder Says | Traditional PuRDy | 3M-Enhanced PuRDy |
|------------------|-------------------|-------------------|
| "We work around the process" | Pain point identified | **MURI diagnosis:** Overburden forces workaround - official process requires 47 fields when 12 are relevant |
| "Data is inconsistent" | Quality issue flagged | **MURA diagnosis:** Inconsistency - 3 teams enter data differently because no governance exists |
| "We export to Excel and fix it" | Manual workaround noted | **MUDA diagnosis:** Pure waste - 18 hrs/week spent on non-value-adding transformation |

---

## The 3M Taxonomy

### MUDA (無駄) - Waste

**Definition:** Activity that consumes resources but creates no value for the customer or organization.

**The 8 Types of Muda:**

| Type | Definition | Discovery Signals | Example Quotes |
|------|------------|-------------------|----------------|
| **Defects** | Errors requiring rework | "We have to go back and fix..." | "About 20% of entries need correction" |
| **Overproduction** | Creating more than needed | "Just in case..." / reporting no one uses | "We generate 47 reports, maybe 10 are read" |
| **Waiting** | Idle time between steps | "We're waiting on..." / approval queues | "Approvals take 3-5 days average" |
| **Non-utilized talent** | Not using people's skills | Overqualified for tasks | "Engineers spending time on data entry" |
| **Transportation** | Moving data/materials unnecessarily | "We send it to X, then Y, then Z" | "The data goes through 4 systems" |
| **Inventory** | Excess WIP or backlogs | Growing queues, stale data | "We have a 6-week backlog of requests" |
| **Motion** | Unnecessary actions/clicks | Too many screens/steps | "It takes 23 clicks to complete" |
| **Extra processing** | Work beyond requirements | Gold-plating, over-engineering | "We format everything perfectly even if it's internal" |

**Quantification Template:**
```markdown
> **MUDA Identified:** [Type] - [Activity]
> **Time Consumed:** [X hours/week]
> **Value Created:** None
> **Recommendation:** Eliminate or automate
```

---

### MURA (斑) - Inconsistency

**Definition:** Variation and unevenness in process, creating unpredictability.

**Mura Patterns:**

| Pattern | Definition | Discovery Signals | Example Quotes |
|---------|------------|-------------------|----------------|
| **Process Inconsistency** | Same task done differently | "It depends on who does it" | "Each team has their own way" |
| **Workload Inconsistency** | Peaks and valleys in demand | Month-end crunches, idle periods | "End of quarter is chaos" |
| **Quality Inconsistency** | Unpredictable output quality | Variable results same input | "Sometimes it works, sometimes it doesn't" |
| **Data Inconsistency** | Same data differs across systems | Conflicting sources of truth | "Salesforce says X, but the spreadsheet says Y" |
| **Timing Inconsistency** | Unpredictable cycle times | "It takes anywhere from..." | "Could be 2 days or 2 weeks" |

**Root Cause Questions:**
1. Why isn't there a standard process?
2. Who decided it could vary?
3. What would standardization break?

**Quantification Template:**
```markdown
> **MURA Identified:** [Pattern] - [What varies]
> **Variance Range:** [Min] to [Max]
> **Impact:** [Downstream effects of unpredictability]
> **Recommendation:** Standardize at [level] while allowing [legitimate variation]
```

---

### MURI (無理) - Overburden

**Definition:** Unreasonable burden placed on people, equipment, or processes.

**Muri Patterns:**

| Pattern | Definition | Discovery Signals | Example Quotes |
|---------|------------|-------------------|----------------|
| **Process Overburden** | Steps exceed what's reasonable | "We're supposed to, but..." | "The checklist has 87 items" |
| **People Overburden** | Workload exceeds capacity | Burnout, shortcuts taken | "We're stretched too thin" |
| **System Overburden** | Technology beyond its limits | Slowdowns, crashes | "The system can't handle it" |
| **Information Overburden** | Too much to process | Analysis paralysis, ignored data | "We get 200 alerts a day" |
| **Skill Overburden** | Role exceeds expertise | Errors from untrained actions | "We're not qualified but we do it anyway" |

**Root Cause Questions:**
1. What drove this burden? (Compliance? Fear? Lack of trust?)
2. What would happen if burden was reduced?
3. Who designed this process and did they understand the actual work?

**Quantification Template:**
```markdown
> **MURI Identified:** [Pattern] - [Who/what is overburdened]
> **Burden Metric:** [Requirements vs. capacity]
> **Consequence:** [What breaks/degrades under burden]
> **Recommendation:** [Reduce scope | Add capacity | Redesign process]
```

---

## Detection Protocol

### Step 1: Listen for Signals

When processing discovery artifacts, flag these phrases:

**MUDA Signals:**
- "We export and then..."
- "We have to re-enter..."
- "Nobody uses that report"
- "We create it just in case"
- "It sits in a queue for..."

**MURA Signals:**
- "It depends..."
- "Each team does it differently"
- "Sometimes it works, sometimes..."
- "The data doesn't match"
- "It could take anywhere from..."

**MURI Signals:**
- "We're supposed to, but we can't..."
- "We follow the process when we have time"
- "It's too much to do properly"
- "We skip steps because..."
- "The system can't handle..."

### Step 2: Classify and Quantify

For each pain point identified:

```markdown
| Pain Point | 3M Classification | Quantification | Root Cause |
|------------|-------------------|----------------|------------|
| [Issue] | [MUDA/MURA/MURI] - [Type] | [hrs/week or variance or capacity gap] | [Why this exists] |
```

### Step 3: Diagnose Interactions

Often, 3M issues compound:

```
MURI (overburden) → MUDA (shortcuts/waste) → MURA (inconsistency)
```

**Example:**
- Overburdened staff (MURI) creates workarounds (MUDA)
- Different staff create different workarounds (MURA)
- Inconsistency causes rework (more MUDA)

---

## Synthesis Output: 3M Analysis Section

Add this section to synthesis documents:

```markdown
## Process Health: 3M Analysis

### MUDA (Waste) Identified

| Waste Type | Activity | Impact | Hours/Week |
|------------|----------|--------|------------|
| [Type] | [Activity] | [Who it affects] | [Quantified] |

**Total Waste:** [X] hours/week across [Y] activities

### MURA (Inconsistency) Identified

| Inconsistency | Variance | Downstream Impact |
|---------------|----------|-------------------|
| [What varies] | [Range] | [What breaks] |

### MURI (Overburden) Identified

| Overburden | Capacity Gap | Consequence |
|------------|--------------|-------------|
| [Who/what] | [Requirement vs. actual] | [What degrades] |

### 3M Interaction Pattern

[Describe how the issues compound, e.g., "Overburden on data team creates inconsistent data entry, which creates rework downstream"]

### Priority Recommendation

Based on 3M analysis, address in this order:
1. **[Issue]** - [MUDA/MURA/MURI] - [Why first]
2. **[Issue]** - [MUDA/MURA/MURI] - [Why second]
```

---

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Instead Do |
|--------------|----------------|------------|
| Labeling everything as "waste" | MURA and MURI require different solutions | Distinguish carefully using signals |
| Ignoring MURI | Overburden is often the root cause | Always ask "why do workarounds exist?" |
| Treating MURA as bad | Some variation is legitimate | Distinguish necessary vs. unnecessary variation |
| Quantifying without context | "10 hours waste" means nothing alone | Compare to total effort, show percentage |

---

## Integration with Existing Frameworks

### With Root Cause Analysis (Analysis Lenses)
- 3M provides the taxonomy; existing Surface → Root Cause lens provides the method
- Apply 3M classification after identifying root cause

### With Gap Detection (Coverage Tracker)
- Flag when 3M signals appear but no diagnosis is made
- "Pain point without 3M classification" = gap

### With Opportunities (Synthesizer)
- Every opportunity should address specific MUDA, MURA, or MURI
- Quantify expected reduction in 3M as success metric

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    3M QUICK DIAGNOSIS                        │
├─────────────────────────────────────────────────────────────┤
│ MUDA (Waste)     │ Does this activity add customer value?   │
│ Key Question     │ If eliminated, would anyone notice?       │
│ Solution         │ ELIMINATE or AUTOMATE                     │
├─────────────────────────────────────────────────────────────┤
│ MURA (Unevenness)│ Does this vary when it shouldn't?        │
│ Key Question     │ Would standardization help or hurt?       │
│ Solution         │ STANDARDIZE (where it makes sense)        │
├─────────────────────────────────────────────────────────────┤
│ MURI (Overburden)│ Is this asking more than is reasonable?  │
│ Key Question     │ What breaks under this burden?            │
│ Solution         │ REDUCE LOAD or INCREASE CAPACITY          │
└─────────────────────────────────────────────────────────────┘
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-23 | Initial 3M framework for PuRDy v2.5 |
