# Stakeholder Personas Library

**Purpose:** Enable personalized synthesis narratives for each stakeholder type
**Capability:** Moves from one-size-fits-all to "this was written for me"
**Usage:** Transform single synthesis into role-specific versions

---

## Why Personalization Matters

The same finding resonates differently with different stakeholders:

| Finding | Finance Framing | Engineering Framing | Sales Framing | Executive Framing |
|---------|-----------------|---------------------|---------------|-------------------|
| "4 systems with redundant data" | "$47K/year in license waste + data reconciliation labor" | "N+1 query patterns, 340ms added latency, 3 integration points to maintain" | "Reps spend 23 min/day finding correct customer data" | "Data fragmentation creates strategic risk: no single customer view" |
| "Manual report compilation" | "15 hrs/week at fully-loaded cost = $39K/year" | "Opportunity to automate: cron job + API aggregation" | "Delayed insights mean stale pipeline forecasts" | "Decision latency: competitors move faster" |

---

## The Four Primary Personas

### Persona 1: Finance/Operations

**Role Examples:** CFO, Controller, Finance Manager, Operations Director

**Primary Lens:**
- ROI and payback period
- Total cost of ownership
- Risk quantification
- Budget impact

**What They Care About:**

| Priority | Their Questions | How to Frame Findings |
|----------|----------------|----------------------|
| 1 | "What does this cost us?" | Quantify current-state cost (labor + tools + opportunity) |
| 2 | "What's the investment required?" | Implementation cost + ongoing operational cost |
| 3 | "When do we break even?" | Payback period with assumptions stated |
| 4 | "What are the risks?" | Financial exposure if project fails/succeeds |
| 5 | "How does this hit budget cycles?" | CapEx vs OpEx, timing against fiscal year |

**Language Patterns:**

| Instead of... | Use... |
|---------------|--------|
| "Improves efficiency" | "Reduces cost by $X per [unit]" |
| "Better data quality" | "Reduces write-offs by X%; saves $Y in correction labor" |
| "Faster processing" | "Reduces cycle time from X to Y, freeing $Z in working capital" |
| "Technical debt" | "Deferred maintenance liability of $X" |

**Metrics They Respect:**
- Net Present Value (NPV)
- Internal Rate of Return (IRR)
- Payback period (months)
- Cost per transaction
- Labor cost per process

**Finance Persona Synthesis Template:**

```markdown
## Financial Impact Summary

> **Bottom Line:** [Net annual impact in dollars]

### Current State Cost Analysis

| Cost Category | Annual Amount | Notes |
|---------------|---------------|-------|
| Labor (direct) | $XX,XXX | [Hours × rate calculation] |
| Labor (indirect) | $XX,XXX | [Management, coordination] |
| Tool/License costs | $XX,XXX | [Current tooling] |
| Opportunity cost | $XX,XXX | [What this prevents doing] |
| **Total Current Cost** | **$XXX,XXX** | |

### Investment Required

| Phase | One-Time | Ongoing/Year |
|-------|----------|--------------|
| Implementation | $XX,XXX | - |
| Training | $XX,XXX | $X,XXX |
| Tooling | $XX,XXX | $XX,XXX |
| **Total Investment** | **$XX,XXX** | **$XX,XXX/year** |

### ROI Projection

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| Savings | $XX,XXX | $XX,XXX | $XX,XXX |
| Investment | ($XX,XXX) | ($XX,XXX) | ($XX,XXX) |
| Net Benefit | $XX,XXX | $XX,XXX | $XX,XXX |
| Cumulative | $XX,XXX | $XX,XXX | $XX,XXX |

**Payback Period:** [X months]
**3-Year NPV:** [$X] at [Y]% discount rate

### Risk Quantification

| Risk | Probability | Financial Impact | Mitigation |
|------|-------------|-----------------|------------|
| [Risk 1] | [%] | $XX,XXX | [Action] |
```

---

### Persona 2: Engineering/Technical

**Role Examples:** CTO, VP Engineering, Tech Lead, Solutions Architect

**Primary Lens:**
- Technical feasibility and complexity
- Integration requirements
- Scalability and performance
- Maintenance burden

**What They Care About:**

| Priority | Their Questions | How to Frame Findings |
|----------|----------------|----------------------|
| 1 | "How does this fit our stack?" | Integration points, compatibility, tech debt implications |
| 2 | "What's the technical complexity?" | Architecture diagrams, API dependencies, data flows |
| 3 | "What are the performance implications?" | Latency, throughput, scaling characteristics |
| 4 | "Who maintains this?" | Ongoing engineering investment, skill requirements |
| 5 | "What's the blast radius if it fails?" | Failure modes, dependencies, recovery paths |

**Language Patterns:**

| Instead of... | Use... |
|---------------|--------|
| "Slow process" | "340ms P95 latency; bottleneck at [X] due to [Y]" |
| "Data issues" | "Referential integrity violations; orphan records in [table]" |
| "Need integration" | "RESTful API required; OAuth 2.0 auth; rate limits at [X]/sec" |
| "Complex system" | "[X] services, [Y] data stores, [Z] integration points" |

**Metrics They Respect:**
- Response time (P50, P95, P99)
- Throughput (requests/sec)
- Uptime/availability (nines)
- Error rates
- Technical debt score
- Code complexity metrics

**Engineering Persona Synthesis Template:**

```markdown
## Technical Assessment

> **Architecture Impact:** [One-line summary of technical implications]

### Current Technical State

```
[ASCII diagram of current system architecture]
```

**Key Components:**
| Component | Technology | Pain Points |
|-----------|------------|-------------|
| [System] | [Stack] | [Technical issues] |

**Integration Landscape:**
- Inbound: [APIs/feeds consumed]
- Outbound: [APIs/feeds produced]
- Internal: [Service dependencies]

### Technical Complexity Analysis

| Dimension | Current | Target | Effort |
|-----------|---------|--------|--------|
| Data stores | [N] | [N] | [Migration scope] |
| API integrations | [N] | [N] | [New connections] |
| Authentication | [Method] | [Method] | [Changes] |
| Deployment | [Method] | [Method] | [Ops changes] |

### Performance Considerations

| Metric | Current | Target | Approach |
|--------|---------|--------|----------|
| Latency (P95) | [X]ms | [Y]ms | [How] |
| Throughput | [X]/sec | [Y]/sec | [How] |
| Availability | [X]% | [Y]% | [How] |

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| [Risk] | [Severity] | [Likelihood] | [Technical approach] |

### Engineering Effort Estimate

| Phase | Scope | Estimate | Dependencies |
|-------|-------|----------|--------------|
| [Phase 1] | [Scope] | [Weeks] | [Blockers] |
```

---

### Persona 3: Sales/Customer-Facing

**Role Examples:** VP Sales, Sales Director, Customer Success, Account Executives

**Primary Lens:**
- Customer impact and experience
- Revenue implications
- Competitive positioning
- Time savings for customer-facing work

**What They Care About:**

| Priority | Their Questions | How to Frame Findings |
|----------|----------------|----------------------|
| 1 | "How does this help me close deals?" | Customer-facing efficiency, faster response times |
| 2 | "What's the customer experience impact?" | Friction points, satisfaction drivers |
| 3 | "How do competitors handle this?" | Market positioning, differentiation opportunities |
| 4 | "How much time does this save reps?" | Hours back for selling vs. admin |
| 5 | "What's the revenue impact?" | Pipeline velocity, win rates, deal size |

**Language Patterns:**

| Instead of... | Use... |
|---------------|--------|
| "Process inefficiency" | "Reps spend [X] hours on admin instead of customers" |
| "Data quality issues" | "Wrong customer data = embarrassing calls, lost trust" |
| "System integration" | "Complete customer view = personalized selling" |
| "Faster reporting" | "Know today's pipeline, not last week's" |

**Metrics They Respect:**
- Hours saved per rep per week
- Pipeline visibility (real-time vs. delayed)
- Customer response time
- Win rate impact
- Average deal size
- Sales cycle length

**Sales Persona Synthesis Template:**

```markdown
## Sales Impact Summary

> **Revenue Opportunity:** [How this affects the ability to sell]

### Time Back for Selling

| Activity | Current Time/Week | After | Hours Saved |
|----------|-------------------|-------|-------------|
| [Admin task] | [X hrs] | [Y hrs] | [Z hrs] |
| [Data finding] | [X hrs] | [Y hrs] | [Z hrs] |
| **Total per rep** | | | **[Z hrs]** |

*With [N] reps, that's [X] hours/week back for customer time*

### Customer Experience Impact

| Touchpoint | Current Pain | Future State | Customer Benefit |
|------------|--------------|--------------|------------------|
| [Touchpoint] | [Issue] | [Improved] | [What they'll notice] |

### Competitive Positioning

| Capability | Us Today | Competitors | After |
|------------|----------|-------------|-------|
| [Capability] | [State] | [Their state] | [Our new state] |

### Revenue Model Impact

| Metric | Current | Target | Impact |
|--------|---------|--------|--------|
| Sales cycle length | [X days] | [Y days] | Faster close |
| Pipeline accuracy | [X]% | [Y]% | Better forecasting |
| Rep productivity | [baseline] | [improved] | More deals worked |
```

---

### Persona 4: Executive/Strategic

**Role Examples:** CEO, COO, SVP, General Manager, Board

**Primary Lens:**
- Strategic alignment
- Competitive advantage
- Risk to the business
- Speed of execution

**What They Care About:**

| Priority | Their Questions | How to Frame Findings |
|----------|----------------|----------------------|
| 1 | "Does this support our strategy?" | Tie to stated company priorities |
| 2 | "What's the competitive implication?" | Market position, first-mover advantage |
| 3 | "What's the risk if we don't do this?" | Cost of inaction, strategic exposure |
| 4 | "How fast can we move?" | Timeline, dependencies, decision points |
| 5 | "What decisions do you need from me?" | Clear asks, authority needed |

**Language Patterns:**

| Instead of... | Use... |
|---------------|--------|
| "Technical debt" | "Strategic agility constraint" |
| "Process inefficiency" | "Execution drag on growth initiatives" |
| "Integration work" | "Enabling cross-functional capability" |
| "Data cleanup" | "Foundation for data-driven decision making" |

**Metrics They Respect:**
- Strategic initiative alignment
- Competitive position impact
- Time to market
- Risk-adjusted return
- Resource constraints and trade-offs

**Executive Persona Synthesis Template:**

```markdown
## Executive Brief

> **Strategic Implication:** [One sentence: what this means for the business]

### Strategic Alignment

| Company Priority | How This Supports |
|------------------|-------------------|
| [Priority 1] | [Connection] |
| [Priority 2] | [Connection] |

### Competitive Context

**If we act:**
- [Advantage 1]
- [Advantage 2]

**If we don't:**
- [Risk 1]
- [Risk 2]

### Investment vs. Return (Summary)

| | Year 1 | Year 2 | Year 3 |
|-|--------|--------|--------|
| Investment | ($X) | ($Y) | ($Z) |
| Return | $A | $B | $C |
| Net | $N | $N | $N |

### Decision Required

**Ask:** [What you need them to decide]

**Options:**
1. **[Option A]** - [Implication]
2. **[Option B]** - [Implication]

**Recommendation:** [Which and why]

### Key Risks

| Risk | Mitigation | Owner |
|------|------------|-------|
| [Risk] | [Approach] | [Who] |

### Timeline

| Milestone | Target Date | Dependency |
|-----------|-------------|------------|
| [Milestone] | [Date] | [What's needed] |
```

---

## Narrative Transformation Rules

### Rule 1: Lead with Their Priority

| Persona | Lead With |
|---------|-----------|
| Finance | Dollar impact |
| Engineering | Technical architecture |
| Sales | Customer/rep time impact |
| Executive | Strategic implication |

### Rule 2: Use Their Vocabulary

Maintain a persona-specific glossary when synthesizing:

```markdown
| Concept | Finance Term | Engineering Term | Sales Term | Exec Term |
|---------|--------------|------------------|------------|-----------|
| Time savings | "Labor cost reduction" | "Automation" | "Hours back for selling" | "Execution efficiency" |
| Quality issues | "Rework cost" | "Defect rate" | "Customer frustration" | "Brand risk" |
| Process delay | "Working capital impact" | "Latency" | "Response time" | "Speed to market" |
```

### Rule 3: Match Their Detail Level

| Persona | Detail Level | Document Length |
|---------|--------------|-----------------|
| Finance | High (numbers) | 2-3 pages |
| Engineering | High (technical) | 3-5 pages |
| Sales | Medium (outcomes) | 1-2 pages |
| Executive | Low (strategic) | 1 page max |

### Rule 4: Answer Their Skeptic Questions

| Persona | Their Skeptic Question | Proactively Address |
|---------|------------------------|---------------------|
| Finance | "What's the real cost?" | All-in TCO, not just obvious costs |
| Engineering | "What's the catch?" | Technical risks and complexity |
| Sales | "Why should I care?" | Direct impact on their metrics |
| Executive | "Why now?" | Urgency and cost of delay |

---

## Multi-Persona Synthesis Protocol

When creating synthesis for multiple stakeholders:

### Step 1: Create Master Synthesis
Full synthesis with all findings (per existing synthesizer protocol)

### Step 2: Create Persona Extracts
For each persona, extract and reframe relevant findings:

```markdown
## Synthesis: [Initiative Name]
### Version: [Finance/Engineering/Sales/Executive]

> **One-Line:** [Persona-relevant summary]

[Persona-specific sections using templates above]

---
*Full synthesis available in master document. This version emphasizes [persona] perspective.*
```

### Step 3: Cross-Reference
Each persona version should reference the master and other versions:
- "For technical details, see Engineering brief"
- "For financial model, see Finance analysis"

---

## Synthesis Quality Check: Persona Resonance

For each stakeholder-specific synthesis:

- [ ] Lead statement uses persona's vocabulary
- [ ] Metrics match what persona cares about
- [ ] Detail level matches persona expectation
- [ ] Skeptic question proactively addressed
- [ ] Clear "so what" for this persona
- [ ] Actionable next steps for their domain

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-23 | Initial stakeholder personas for PuRDy v2.5 |
