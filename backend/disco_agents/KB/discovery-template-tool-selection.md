# Discovery Template: Tool Selection & New Build

**Version:** 1.0
**Last Updated:** 2026-01-23

Use this template for initiatives where the core pattern is: "We're evaluating vendors" or "We need a new tool/platform" or "Current tool doesn't fit."

---

## Pre-Meeting Knowledge Framework

### 1. Participant Knowledge

| Participant | Role | Current Tool Experience | Stance | Power |
|-------------|------|------------------------|--------|-------|
| [Name] | [Role] | [What they use today] | [Champion/Neutral/Skeptic] | [H/M/L] |
| | | | | |
| | | | | |

**What we still need to discover about participants:**
- [ ] Who are the power users of current tools?
- [ ] Who will champion adoption?
- [ ] Who has veto power over tool selection?

### 2. Problem/Opportunity Context

| Aspect | What We Know | What to Discover |
|--------|--------------|------------------|
| What problem we're solving | | |
| Current tool/solution | | |
| Why current isn't working | | |
| Must-have requirements | | |
| Nice-to-have requirements | | |
| Integration requirements | | |

### 3. Desired Outcomes

| Outcome | Priority | Definition of Done |
|---------|----------|-------------------|
| Requirements (must-have vs nice-to-have) | H | Prioritized list with stakeholder sign-off |
| Workflow impact assessment | H | How daily work changes |
| Integration requirements | H | What it must connect to |
| Migration scope | M | What data/config moves |
| Evaluation criteria | M | Weighted scorecard |

### 4. Strategic Context

| Aspect | Status |
|--------|--------|
| Named executive sponsor | [ ] |
| Budget range | |
| Timeline | |
| Procurement constraints | |
| Existing vendor relationships | |

---

## Hypotheses to Test

### H1: Problem Hypothesis
**We believe:** [The core problem with current state is...]
**Expected evidence:** [We expect to hear...]
**If wrong, we'd see:** [We'd hear instead...]

### H2: Solution Hypothesis
**We believe:** [The right solution direction is...]
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

### Problem Clarity (CRITICAL)
- [ ] "What specific problems MUST this solve? What happens if we don't solve them?"
- [ ] "What's must-have vs nice-to-have? If you could only have 3 things, what are they?"
- [ ] "Why isn't the current solution working?"

### Workflow Impact
- [ ] "How does this fit into daily work? Walk me through a typical use case."
- [ ] "What changes for users if we adopt this?"
- [ ] "What do users do today that they wouldn't do with the new tool?"

### Integration Requirements
- [ ] "What must this connect to? (Be specific: system names, data flows)"
- [ ] "Are there API requirements? Who would build the integration?"
- [ ] "What data needs to flow in and out?"

### Migration Reality
- [ ] "What data or configuration needs to move from the old system?"
- [ ] "Who would do the migration? How long would it take?"
- [ ] "Can we run both systems in parallel? For how long?"

### Change Management
- [ ] "Who needs training? How much behavior change is this?"
- [ ] "Who will champion this internally?"
- [ ] "What happened last time we rolled out a new tool?"

---

## Optional Questions (nice to have)

### Vendor Relationship
- [ ] "Do we have existing vendor relationships that matter?"
- [ ] "Any political considerations on vendor selection?"
- [ ] "Budget constraints or approval requirements?"

### Long-term View
- [ ] "Where do you see this tool in 3 years?"
- [ ] "What future needs should we consider?"

---

## Type-Specific Failure Patterns to Watch

| Pattern | Why Tool Selection Initiatives Fail Here | Detection Questions |
|---------|------------------------------------------|---------------------|
| **Feature fixation** | Focused on features, not workflow fit | "How does this fit your actual daily work?" |
| **Migration underestimation** | "We'll just export and import" | "What data complexity exists? Edge cases?" |
| **Training gap** | "It's intuitive, no training needed" | "What happened last time we rolled out a new tool?" |
| **Integration fantasy** | "It has an API" vs reality | "Who specifically builds the integration?" |
| **Shelfware syndrome** | Tool bought, never adopted | "Who will champion adoption? What's their incentive?" |
| **Consensus paralysis** | Everyone has different requirements | "If you could only have 3 features, what are they?" |

---

## Type-Specific Success Benchmarks

| Metric | Poor | Average | Good | Our Target |
|--------|------|---------|------|------------|
| User adoption (month 1) | <20% | 20-50% | >70% | |
| Training completion | <50% | 50-80% | >90% | |
| Key workflow coverage | <60% | 60-80% | >90% | |
| Integration success | Partial | Most | All critical | |
| Time to value | >6 months | 3-6 months | <3 months | |

---

## Quantification Gate Checklist

Before synthesis, we MUST have:

- [ ] Must-have requirements: Prioritized with stakeholder agreement
- [ ] Integration scope: Systems, APIs, data flows identified
- [ ] Migration scope: What moves, who does it, timeline estimate
- [ ] User population: How many users, what roles
- [ ] Current state cost: What we spend today (time, money, frustration)
- [ ] Change management: Who trains, who champions, what support needed

---

## Build vs Buy Decision Framework

If considering custom build, also capture:

| Factor | Buy | Build |
|--------|-----|-------|
| Time to value | Faster | Slower |
| Customization | Limited | Unlimited |
| Maintenance | Vendor | Internal team |
| Total cost | Known | Unknown |
| Risk profile | Lower | Higher |

Key questions for build consideration:
- [ ] "Do we have engineering capacity to build AND maintain this?"
- [ ] "Is this core to our competitive advantage?"
- [ ] "What's our track record with internal tool builds?"
