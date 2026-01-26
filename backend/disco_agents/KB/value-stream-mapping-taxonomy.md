# Value Stream Mapping Taxonomy

**Purpose:** Categorize every process step as value-adding, necessary non-value, or pure Muda
**Toyota Origin:** "Value Stream" - all activities from request to delivery
**Usage:** Transform process descriptions into quantified waste analysis

---

## Why VSM Matters for Discovery

When stakeholders describe processes, they list steps. VSM reveals which steps actually matter:

| Process Step | Stakeholder View | VSM Analysis |
|--------------|------------------|--------------|
| "Enter data into system" | Normal step | **Necessary Non-Value** (required for system but doesn't help customer) |
| "Export to Excel for formatting" | Workaround | **MUDA (Motion)** - Pure waste, adds no value |
| "Generate customer report" | Core work | **Value-Adding** - Customer would pay for this |
| "Wait for approval" | Just part of process | **MUDA (Waiting)** - 3 days of delay, zero value |

---

## The Three Categories

### Category 1: Value-Adding (VA)

**Definition:** Activities that transform the product/service in ways the customer cares about and would pay for.

**Tests:**
1. Does this step change the form, fit, or function of what we're delivering?
2. Would the customer be willing to pay for this step?
3. Is this step done right the first time?

**Discovery Examples:**

| Domain | Value-Adding Steps |
|--------|-------------------|
| Data Integration | Data transformation that creates new insight |
| Reporting | Analysis that informs decisions |
| Process Automation | Execution of the core business logic |
| Customer Service | Resolution that solves customer problem |

**Tracking:**
```markdown
| VA Step | Time (min) | Output | Customer Benefit |
|---------|------------|--------|------------------|
| [Step] | [Time] | [What it produces] | [Why customer cares] |
```

---

### Category 2: Necessary Non-Value-Adding (NNVA)

**Definition:** Activities that add no direct value but are required by current systems, regulations, or constraints.

**Tests:**
1. Would the customer notice if we skipped this? (No)
2. Is this required by law, contract, or system? (Yes)
3. Can we eliminate it with different technology/process? (Maybe)

**Common NNVA Types:**

| Type | Examples | Path to Elimination |
|------|----------|-------------------|
| **Regulatory Compliance** | Audit logging, data retention | Automate fully |
| **System Constraints** | Data re-entry, format conversion | API integration |
| **Organizational Structure** | Handoffs between teams | Cross-functional teams |
| **Risk Mitigation** | Approvals, reviews | Risk-based thresholds |
| **Technical Debt** | Workarounds for legacy systems | Modernization |

**Discovery Signals:**
- "We have to do this because the system requires..."
- "Compliance needs us to..."
- "It's always been done this way"
- "Another team needs this format"

**Tracking:**
```markdown
| NNVA Step | Time (min) | Why Required | Elimination Path |
|-----------|------------|--------------|------------------|
| [Step] | [Time] | [Constraint] | [What would remove need] |
```

---

### Category 3: Pure Muda (Waste)

**Definition:** Activities that consume resources without adding value AND are not required.

**Tests:**
1. Would the customer notice if we skipped this? (No)
2. Is this required by any constraint? (No)
3. Why does this exist? (Historical reasons, habit, lack of alternative)

**The 8 Muda in Process Context:**

| Muda Type | Process Manifestation | Time Waste Typical |
|-----------|----------------------|-------------------|
| **Defects** | Rework, error correction | 10-30% of process time |
| **Overproduction** | Reports no one reads, data no one uses | 5-20% |
| **Waiting** | Approval queues, batch delays | 20-60% of cycle time |
| **Non-utilized talent** | Overqualified people on routine tasks | Hidden |
| **Transportation** | Moving data between systems unnecessarily | 5-15% |
| **Inventory** | Backlogs, queues, WIP | Creates waiting |
| **Motion** | Extra clicks, unnecessary screens | 5-20% |
| **Extra processing** | Over-formatting, gold-plating | 10-25% |

**Discovery Signals:**
- "We've always done it this way"
- "Just in case someone needs it"
- "It's not ideal but it works"
- "We export and then..."
- "We wait for..."

---

## Process Mapping Protocol

### Step 1: Extract Process from Discovery

For every process described in discovery:

```markdown
### Process: [Name]
**Source:** [Session/Stakeholder]
**Scope:** [Start event] → [End event]
**Frequency:** [How often]
**Volume:** [How many per period]
```

### Step 2: List All Steps

Capture every step exactly as described:

| # | Step Description | Who | Time Estimate |
|---|-----------------|-----|---------------|
| 1 | [Step] | [Role] | [Minutes] |
| 2 | [Step] | [Role] | [Minutes] |

### Step 3: Classify Each Step

Apply the three-category test to each step:

| # | Step | Category | Evidence | Time |
|---|------|----------|----------|------|
| 1 | [Step] | VA/NNVA/MUDA | [Why] | [Min] |
| 2 | [Step] | VA/NNVA/MUDA | [Why] | [Min] |

### Step 4: Calculate Value Ratio

```markdown
**Value Stream Summary:**
- Total Steps: [N]
- Total Time: [X minutes]

| Category | Steps | Time | % of Total |
|----------|-------|------|------------|
| Value-Adding | [n] | [x min] | [%] |
| Necessary Non-Value | [n] | [x min] | [%] |
| Pure Muda | [n] | [x min] | [%] |

**Value Ratio:** [VA time / Total time] = [X]%
**Target Value Ratio:** >50% (industry benchmark)
```

### Step 5: Create Value Stream Diagram

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Step 1  │───>│ Step 2  │───>│ Step 3  │───>│ Step 4  │
│ [VA]    │    │ [MUDA]  │    │ [NNVA]  │    │ [VA]    │
│ 15 min  │    │ 45 min  │    │ 10 min  │    │ 20 min  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │
   GREEN          RED           YELLOW         GREEN
```

Color coding:
- **GREEN (VA):** Protect and optimize
- **YELLOW (NNVA):** Automate or streamline
- **RED (MUDA):** Eliminate

---

## Synthesis Output Template

Add this section to synthesis for each major process:

```markdown
## Value Stream Analysis: [Process Name]

> **Key Finding:** Only [X]% of process time is value-adding.
> [Y] hours/week are pure waste (Muda).

### Process Steps Classified

| Step | Category | Time | Issue |
|------|----------|------|-------|
| [Step 1] | **VA** | 15 min | Core value creation |
| [Step 2] | **MUDA** (Waiting) | 45 min | Approval queue delay |
| [Step 3] | **NNVA** (Compliance) | 10 min | Required audit log |
| [Step 4] | **MUDA** (Motion) | 20 min | Manual data transfer |
| [Step 5] | **VA** | 20 min | Analysis delivery |

### Value Stream Metrics

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Total cycle time | 110 min | 45 min | 65 min |
| Value-adding time | 35 min | 35 min | 0 min |
| **Value ratio** | 32% | >75% | 43 pts |
| Muda time | 65 min | 0 min | 65 min |

### Waste Breakdown

| Muda Type | Time | % of Waste | Root Cause |
|-----------|------|------------|------------|
| Waiting | 45 min | 69% | Batch approval process |
| Motion | 20 min | 31% | No system integration |

### Recommendations

1. **Eliminate:** [Muda step] - Saves [X] min/instance
2. **Automate:** [NNVA step] - Reduces from [X] to [Y] min
3. **Streamline:** [VA step] - Currently inefficient because [reason]

### Projected Improvement

| Scenario | Cycle Time | Value Ratio | Hours Saved/Week |
|----------|------------|-------------|------------------|
| Current state | 110 min | 32% | - |
| Remove Muda | 45 min | 78% | [X] |
| Optimize NNVA | 38 min | 92% | [Y] |
```

---

## Discovery Probes for VSM

When stakeholders describe processes, ask:

### For Each Step
1. "What happens to the output of this step?"
2. "Who uses this and what do they use it for?"
3. "What happens if you skip this step?"
4. "Has anyone ever skipped this? What happened?"

### For Waiting/Delays
1. "How long does this typically take?"
2. "What's the shortest it's ever taken? What made that possible?"
3. "What are you waiting on during this time?"
4. "Could this be done in parallel with something else?"

### For Handoffs
1. "What information do you receive?"
2. "What information do you pass on?"
3. "Is there anything you receive that you don't use?"
4. "Is there anything you wish you received but don't?"

---

## Value Stream Benchmarks

### By Industry

| Industry | Typical Value Ratio | Top Quartile |
|----------|---------------------|--------------|
| Manufacturing | 5-15% | 25%+ |
| Software Development | 15-25% | 40%+ |
| Financial Services | 10-20% | 35%+ |
| Healthcare Admin | 5-15% | 25%+ |
| Professional Services | 20-35% | 50%+ |

### By Process Type

| Process Type | Expected Muda | Focus Area |
|--------------|---------------|------------|
| Data entry | 30-50% | Motion, Defects |
| Approval workflows | 40-70% | Waiting |
| Reporting | 25-45% | Overproduction, Motion |
| Customer requests | 30-50% | Waiting, Transportation |
| Integration/handoffs | 40-60% | Transportation, Defects |

---

## Common VSM Patterns in Discovery

### Pattern 1: The Approval Black Hole
**Signal:** "We submit and wait"
**Typical Waste:** 50-80% of cycle time is waiting
**Question:** "What decisions are actually being made in each approval?"

### Pattern 2: The Format Shuffle
**Signal:** "We export, reformat, then import"
**Typical Waste:** 15-30% of total effort
**Question:** "Why do these systems need different formats?"

### Pattern 3: The Just-In-Case Report
**Signal:** "We generate this weekly"
**Typical Waste:** Reports no one reads (100% Muda)
**Question:** "When was this last used for a decision?"

### Pattern 4: The Human API
**Signal:** "We look it up in System A, then enter it in System B"
**Typical Waste:** 20-40% of process time
**Question:** "Could these systems talk directly?"

### Pattern 5: The Quality Tax
**Signal:** "We check everything before it goes out"
**Typical Waste:** Inspection instead of prevention
**Question:** "What percentage of items actually have issues?"

---

## Integration with Other Frameworks

### With 3M Diagnosis
- VSM identifies WHAT is waste
- 3M explains WHY waste exists
- Use together: VSM reveals steps, 3M diagnoses root cause

### With A3 Problem Solving
- VSM provides Current State data
- Value Ratio becomes the metric
- Muda elimination becomes the countermeasure

### With Gap Analysis
- Low Value Ratio = coverage gap
- Flag: "Process described but not value-mapped"

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-23 | Initial VSM framework for PuRDy v2.5 |
