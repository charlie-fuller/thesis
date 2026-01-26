# Discovery Template: Process Automation

**Version:** 1.0
**Last Updated:** 2026-01-23

Use this template for initiatives where the core pattern is: "We do this manually today and want to automate it."

---

## Pre-Meeting Knowledge Framework

### 1. Participant Knowledge

| Participant | Role | Pain Points | Stance | Power |
|-------------|------|-------------|--------|-------|
| [Name] | [Role] | [Known issues] | [Champion/Neutral/Skeptic] | [H/M/L] |
| | | | | |
| | | | | |

**What we still need to discover about participants:**
- [ ] Who handles exceptions today?
- [ ] Who loses control if this gets automated?
- [ ] Who are the hidden experts?

### 2. Problem/Opportunity Context

| Aspect | What We Know | What to Discover |
|--------|--------------|------------------|
| Current process flow | | |
| Volume (how many times/period) | | |
| Time per occurrence | | |
| Error rate | | |
| Who does it today | | |
| What triggers it | | |

### 3. Desired Outcomes

| Outcome | Priority | Definition of Done |
|---------|----------|-------------------|
| Process map (current state) | H | Complete swimlane with time per step |
| Happy path % estimate | H | Percentage that follows standard flow |
| Edge case inventory | H | List with frequency and handling |
| Baseline metrics | H | Time, cost, volume, error rate |
| Decision on scope | M | Clear in/out of scope list |

### 4. Strategic Context

| Aspect | Status |
|--------|--------|
| Named executive sponsor | [ ] |
| Strategic priority alignment | |
| Timeline/urgency | |
| Budget constraints | |
| Dependencies | |

---

## Hypotheses to Test

### H1: Problem Hypothesis
**We believe:** [The core inefficiency is...]
**Expected evidence:** [We expect to hear...]
**If wrong, we'd see:** [We'd hear instead...]

### H2: Solution Hypothesis
**We believe:** [The right solution approach is...]
**Who agrees:** [Expected champions]
**Who disagrees:** [Expected resistors]

### H3: Adoption Hypothesis
**We believe adoption will be:** [Easy/Moderate/Difficult]
**Key enablers:**
**Key barriers:**

### H4: Hidden Issue Hypothesis
**We suspect:** [There's an unstated issue around...]
**Detection signal:** [Listen for...]

---

## Required Questions (MUST answer before synthesis)

### Process Understanding
- [ ] "Walk me through exactly what happens when [trigger event] occurs."
- [ ] "What percentage of cases follow the standard flow vs. need exceptions?"
- [ ] "When things go wrong, what happens? Who handles it? How long does it take?"

### Quantification (BLOCKING)
- [ ] "How many times per [week/month] does this process run?"
- [ ] "How long does the standard case take? The exception cases?"
- [ ] "How many people are involved in this process today?"
- [ ] "What's the cost when this goes wrong?" (Get $ or hours)

### Edge Cases & Exceptions
- [ ] "What are the top 3 exceptions that require manual intervention?"
- [ ] "When do you need to override the system?"
- [ ] "What's the 'weird case' that breaks everything?"

### Audit & Compliance
- [ ] "What needs to be logged for compliance/audit purposes?"
- [ ] "Who reviews the output? How often?"
- [ ] "Are there any regulatory requirements we should know about?"

---

## Optional Questions (nice to have)

### History
- [ ] "Has automation been tried before? What happened?"
- [ ] "What would have to be true for this to succeed?"

### Integration
- [ ] "What systems does this process touch?"
- [ ] "Where does the input data come from?"
- [ ] "Where does the output need to go?"

### Change Management
- [ ] "Who would be most affected by automating this?"
- [ ] "What training would be needed?"

---

## Type-Specific Failure Patterns to Watch

| Pattern | Why Automation Initiatives Fail Here | Detection Questions |
|---------|--------------------------------------|---------------------|
| **Edge case explosion** | "Happy path" is only 40% of cases | "What % actually follows standard flow?" |
| **Exception handling gap** | No plan for when automation fails | "What happens when the bot gets stuck?" |
| **Audit trail blindness** | Compliance needs not considered | "What needs to be logged? Who reviews?" |
| **Override avoidance** | No way for humans to intervene | "When do you need to override?" |
| **Scope creep** | "While we're at it..." syndrome | "What's explicitly OUT of scope?" |

---

## Type-Specific Success Benchmarks

| Metric | Poor | Average | Good | Our Target |
|--------|------|---------|------|------------|
| Happy path % | <50% | 50-70% | >80% | |
| Exception handling time | >1 day | Same day | <1 hour | |
| Error rate improvement | <20% | 20-50% | >50% | |
| Adoption rate (week 4) | <30% | 30-60% | >80% | |

---

## Quantification Gate Checklist

Before synthesis, we MUST have:

- [ ] Volume: How many times per period
- [ ] Time: Current time per occurrence (happy path AND exceptions)
- [ ] Population: How many people affected
- [ ] Cost: Current $ or hours cost
- [ ] Edge case frequency: % that don't follow happy path
- [ ] Error rate: Current error/rework rate
