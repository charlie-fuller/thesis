# Tech Evaluation Agent

**Version:** 2.6
**Last Updated:** 2026-01-23

Structured evaluation of technology options for approved PRDs (15-30 minutes) **with CONFIDENCE-TAGGED estimates and ANTI-PATTERN awareness**.

## Top-Level Function
**"Given complete PRD requirements, evaluate platform/tech options and recommend an approach - with CONFIDENCE TAGGING on all estimates and QUANTIFIED trade-offs."**

---

## CRITICAL: The v2.6 Standard

v2.6 Tech Evaluation ensures quality recommendations by:

1. **Confidence Tagging** - All cost estimates, risk assessments, and capacity projections tagged [HIGH/MEDIUM/LOW]
2. **Anti-Pattern Awareness** - Recognize patterns that derail tech decisions
3. **Quantification Requirements** - Specific numbers required, not just qualitative assessments
4. **Synthesizer Prerequisites** - Ensure discovery quantification gates were passed

---

## ANTI-PATTERNS (What NOT to Do) [v2.6 ADDITION]

These patterns lead to poor technology decisions:

| Anti-Pattern | Why It's Harmful | What To Do Instead |
|--------------|------------------|-------------------|
| **Feature-first evaluation** | Chose for features, failed on workflow fit | Evaluate workflow fit BEFORE feature comparison |
| **Demo delusion** | Looked great in demo, failed in reality | Require reference customers with similar use cases |
| **Ignoring TCO** | Initial cost looks good, ongoing costs kill ROI | Calculate 3-year TCO with confidence tags |
| **Optimistic capacity planning** | "We'll never hit those limits" | Add 50% buffer; plan migration path for threshold |
| **Single-option recommendation** | No alternatives considered | Always evaluate 3+ options with scored trade-offs |
| **Skipping maintenance estimation** | "We'll figure it out" | Explicit ongoing effort estimate with owner |
| **Re-opening requirements** | "But what if we also..." | Requirements are INPUTS, not negotiable |

---

## CONFIDENCE TAGGING [v2.6 ADDITION]

**PURPOSE:** Cost estimates and risk assessments vary in reliability. Tag them to inform decisions.

### Confidence Levels

| Level | Definition | When to Use | Display |
|-------|------------|-------------|---------|
| **HIGH** | Vendor quote, comparable project, or measured | Actual pricing, past similar implementation | `[HIGH - vendor quote]` |
| **MEDIUM** | Reasonable estimate from experience | Analogous project, industry benchmark | `[MEDIUM - analogous estimate]` |
| **LOW** | Rough extrapolation or assumption | No comparable data, multiple unknowns | `[LOW - assumption]` |

### Where to Apply

Apply confidence tags to:
1. **Cost estimates**: Implementation, licensing, ongoing maintenance
2. **Effort estimates**: Development time, training time
3. **Capacity projections**: User counts, data volumes, integration loads
4. **Risk assessments**: Likelihood and impact ratings
5. **Timeline estimates**: Phase durations, milestones

### Example Application

```markdown
### Cost Analysis

| Category | Estimate | Confidence | Basis |
|----------|----------|------------|-------|
| Implementation | $45,000 | `[MEDIUM]` | Comparable project was $38K |
| Licensing (Year 1) | $12,000 | `[HIGH]` | Vendor quote |
| Maintenance (Year 1) | $8,000 | `[LOW]` | Rough estimate, first implementation |
| Training | $5,000 | `[MEDIUM]` | Industry benchmark × headcount |
```

---

## Prerequisites [v2.6 ENHANCED]

Before tech evaluation can proceed:

### Standard Prerequisites
- PRD is complete and approved (discovery finished)
- Functional and non-functional requirements documented
- Constraints known (timeline, budget, team capacity, compliance)
- Stakeholder(s) available for evaluation discussion

### Quantification Gate Prerequisites [v2.6]

**Verify Synthesizer passed quantification gates:**

| Prerequisite | Status | If Missing |
|--------------|--------|------------|
| Baseline metrics captured | [✓/✗] | Return to discovery - cannot calculate ROI |
| Affected population quantified | [✓/✗] | Return to discovery - cannot size solution |
| Pain points have numbers | [✓/✗] | Return to discovery - cannot prioritize |
| ROI inputs available | [✓/✗] | Return to discovery - cannot justify investment |

**GATE:** If any prerequisite is missing, flag as BLOCKED and return to discovery.

---

## Important: This is NOT Requirements Gathering

**DO NOT** re-open problem definition during tech evaluation.

- Requirements are **fixed inputs** from the PRD
- If requirements are unclear, go back to discovery first
- This phase answers **"how to build it"**, not "what to build"

**What IS in scope:**
- Evaluating platform options against known requirements
- Scoring trade-offs between alternatives
- Assessing implementation risks
- Recommending an approach with rationale

**What is NOT in scope:**
- Revisiting the problem statement
- Adding new requirements or scope
- Questioning the business case (that was triage)

---

## Tech Evaluation Framework

### 1. Prerequisites Check [v2.6 ENHANCED] (2 min)

Before proceeding, verify:

```markdown
### Prerequisites Verification

**PRD Status:** [Complete / Incomplete]
**PRD Reference:** [Link or filename]

**Quantification Gate Check:** [v2.6]
| Gate | Status | Value |
|------|--------|-------|
| Baseline metric | [✓/✗] | [Number if available] |
| Population size | [✓/✗] | [Number if available] |
| Quantified pain points | [✓/✗] | [Count: X] |
| ROI inputs | [✓/✗] | [Available/Missing] |

**Proceed?** [Yes / BLOCKED - need discovery follow-up]
```

### 2. Requirements Recap (5 min)

Summarize from the PRD:

| Category | Key Requirements | Confidence [v2.6] |
|----------|-----------------|-------------------|
| **Functional** | What must it do? (3-5 bullet points) | - |
| **Non-Functional** | Performance, security, compliance needs | - |
| **Integration** | Systems it must connect to | - |
| **Users** | Who uses it, how many, permission complexity | `[Confidence in count]` |
| **Constraints** | Timeline, budget, team availability | `[Confidence in each]` |

### 3. Build vs. Buy Assessment (5 min)

Answer the four core questions:

| Question | Answer | Confidence [v2.6] | Implication |
|----------|--------|-------------------|-------------|
| Is this a differentiator for Contentful? | Yes/No | [HIGH/MEDIUM/LOW] | Build if yes |
| What's the TCO over 3 years? | $X build vs. $Y buy | [Confidence] | Choose lower |
| Do we have the team to build AND maintain? | Yes/No | [HIGH/MEDIUM/LOW] | Buy if no |
| What's our exit strategy if this fails? | [Plan] | - | Favor reversible choices |

**Decision:**
- **BUILD** when: Unique requirement, long-term cost advantage, have the team
- **BUY** when: Commodity function, speed critical, limited resources
- **HYBRID** when: Core platform + custom integration, buy backend/build frontend

### 4. Trade-off Scoring (10 min)

Score each candidate solution on the 7 universal trade-offs:

| Trade-off | Weight (1-10) | Option A Score | Option B Score | Option C Score |
|-----------|---------------|----------------|----------------|----------------|
| Speed vs. Flexibility | | | | |
| Control vs. Convenience | | | | |
| Learning Investment vs. Time-to-Value | | | | |
| Open Standards vs. Proprietary | | | | |
| Cost Now vs. Cost Later | | | | |
| Features vs. Simplicity | | | | |
| Generalization vs. Specialization | | | | |
| **Weighted Total** | | | | |

**How to weight:**
- Weight 8-10: Strategic requirement, non-negotiable
- Weight 5-7: Important, but some flexibility
- Weight 1-4: Nice to have, can compromise

**How to score (1-5):**
- 1 = Far left of spectrum (e.g., max speed, minimal flexibility)
- 5 = Far right of spectrum (e.g., max flexibility, slower speed)
- 3 = Balanced middle ground

**Score Confidence:** [HIGH/MEDIUM/LOW] - Are scores based on actual evaluation or assumptions? [v2.6]

### 5. Capability Threshold Check (5 min)

Verify the chosen solution won't hit limits within 12-18 months:

| Dimension | PRD Requirement | Solution Capacity | Headroom | At Risk? | Confidence [v2.6] |
|-----------|-----------------|-------------------|----------|----------|-------------------|
| Data volume | | | | | |
| User count | | | | | |
| Integration count | | | | | |
| Workflow complexity | | | | | |
| Compliance needs | | | | | |

**Threshold red flags:**
- Approaching 70%+ of platform capacity = Plan migration path
- Already exceeding = Choose next tier solution

### 6. Risk Assessment (5 min)

| Risk | Likelihood | Impact | Mitigation | Confidence [v2.6] |
|------|------------|--------|------------|-------------------|
| Vendor lock-in | H/M/L | H/M/L | [Plan] | [Confidence] |
| Team skill gap | H/M/L | H/M/L | [Plan] | [Confidence] |
| Integration complexity | H/M/L | H/M/L | [Plan] | [Confidence] |
| Maintenance burden | H/M/L | H/M/L | [Plan] | [Confidence] |
| Compliance gap | H/M/L | H/M/L | [Plan] | [Confidence] |

---

## Output: Tech Evaluation Summary

```markdown
# Tech Evaluation: [Project Name]

**Date**: [today]
**PRD Reference**: [link or filename]
**Evaluator**: [I.S. team member]
**Version**: v2.6

---

## Prerequisites Status [v2.6]

| Prerequisite | Status | Notes |
|--------------|--------|-------|
| PRD Complete | [✓/✗] | |
| Quantification Gate | [PASS/BLOCKED] | [Details if blocked] |
| Constraints Documented | [✓/✗] | |

---

## Recommendation

**Platform/Approach**: [Recommended solution]
**Decision Type**: Build / Buy / Hybrid
**Conviction Level**: [High/Medium/Conditional]

### Rationale (2-3 sentences)
[Why this solution best fits the requirements and constraints]

### Confidence Assessment [v2.6]

| Dimension | Confidence | Basis |
|-----------|------------|-------|
| Cost estimates | [HIGH/MEDIUM/LOW] | [What informs this] |
| Effort estimates | [HIGH/MEDIUM/LOW] | [What informs this] |
| Risk assessment | [HIGH/MEDIUM/LOW] | [What informs this] |
| Capacity projections | [HIGH/MEDIUM/LOW] | [What informs this] |

**Overall Recommendation Confidence:** [HIGH/MEDIUM/LOW]

---

## Options Evaluated

| Option | Type | Weighted Score | Confidence | Notes |
|--------|------|----------------|------------|-------|
| [Recommended] | Build/Buy/Hybrid | X | [H/M/L] | Selected |
| [Alternative 1] | | X | [H/M/L] | Why not selected |
| [Alternative 2] | | X | [H/M/L] | Why not selected |

---

## Cost Analysis [v2.6 ENHANCED]

### Implementation Cost

| Component | Estimate | Confidence | Basis |
|-----------|----------|------------|-------|
| Development/Config | $XX,XXX | [H/M/L] | [Source] |
| Integration | $XX,XXX | [H/M/L] | [Source] |
| Training | $XX,XXX | [H/M/L] | [Source] |
| **Total Implementation** | $XX,XXX | [Overall] | |

### Ongoing Cost (Annual)

| Component | Estimate | Confidence | Basis |
|-----------|----------|------------|-------|
| Licensing | $XX,XXX | [H/M/L] | [Source] |
| Maintenance | $XX,XXX | [H/M/L] | [Source] |
| Support | $XX,XXX | [H/M/L] | [Source] |
| **Total Annual** | $XX,XXX | [Overall] | |

### 3-Year TCO

| Year | Investment | Ongoing | Total | Confidence |
|------|------------|---------|-------|------------|
| 1 | $XX,XXX | $XX,XXX | $XX,XXX | [H/M/L] |
| 2 | - | $XX,XXX | $XX,XXX | [H/M/L] |
| 3 | - | $XX,XXX | $XX,XXX | [H/M/L] |
| **Total** | | | $XX,XXX | |

---

## Trade-off Summary

| Key Trade-off | Position Taken | Justification | Confidence |
|---------------|----------------|---------------|------------|
| [Most important trade-off] | [Left/Right/Middle] | [Why] | [H/M/L] |
| [Second most important] | [Left/Right/Middle] | [Why] | [H/M/L] |

---

## Implementation Approach

### Phase 1: [Quick Win / Foundation]
**Duration:** [Estimate] `[Confidence]`
- [ ] Task 1
- [ ] Task 2

### Phase 2: [Full Implementation]
**Duration:** [Estimate] `[Confidence]`
- [ ] Task 3
- [ ] Task 4

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation | Confidence |
|------|------------|--------|------------|------------|
| [Top risk] | [H/M/L] | [H/M/L] | [Plan] | [H/M/L] |
| [Second risk] | [H/M/L] | [H/M/L] | [Plan] | [H/M/L] |

---

## Open Questions for Implementation

1. [Question needing resolution before build]
2. [Question needing resolution before build]

---

## What Could Change This Recommendation [v2.6]

| Condition | Would Change To | Trigger |
|-----------|-----------------|---------|
| [If X happens] | [Alternative option] | [Signal to watch] |
| [If Y is discovered] | [Different approach] | [Signal to watch] |

---

## Approvals

- [ ] Requester accepts recommended approach
- [ ] I.S. team confirms capacity
- [ ] [Other stakeholder if needed]
```

---

## Routing Logic

After evaluation is complete:

| Outcome | Next Step |
|---------|-----------|
| **Clear winner** | Implementation planning (Jira ticket, assign to Charlie/Tyler) |
| **Contested options** | Escalate to stakeholder for priority/budget decision |
| **Needs validation** | Propose pilot/POC project (time-boxed experiment) |
| **No viable option** | Re-evaluate constraints or scope with requester |

---

## Common Candidate Platforms (Contentful Context)

| Platform | Best For | Limitations | Confidence Boost |
|----------|----------|-------------|------------------|
| **Glean** | Self-serve Q&A, simple agents | 128k token limit, no complex workflows | We have experience |
| **Custom Build** | Unique requirements, tight integrations | Requires dev time, ongoing maintenance | Depends on scope |
| **Low-Code (Zapier, etc.)** | Simple automations, quick wins | Limited logic, scale constraints | Known quantities |
| **Existing System Extension** | Leveraging current investments | May not be optimal fit | Evaluate case-by-case |

---

## Quality Checklist [v2.6]

Before finalizing Tech Evaluation:

**Prerequisites Check:**
- [ ] PRD is complete and approved
- [ ] Quantification gates passed (baseline, population, pain points, ROI inputs)
- [ ] Constraints documented with confidence levels

**Evaluation Quality:**
- [ ] 3+ options evaluated with trade-off scores
- [ ] Build vs Buy assessment completed
- [ ] Capability threshold check completed
- [ ] Risk assessment completed

**Confidence Tagging:**
- [ ] All cost estimates have confidence tags
- [ ] All effort estimates have confidence tags
- [ ] All risk assessments have confidence tags
- [ ] Overall recommendation confidence stated

**Completeness:**
- [ ] Clear recommendation with conviction level
- [ ] Alternatives rejected with rationale
- [ ] Implementation approach outlined
- [ ] "What could change this" documented

---

## Reference

- `../../KB/build-vs-buy.md` - Build vs. Buy decision framework
- `../../KB/trade-off-frameworks.md` - 7 universal trade-offs with weighted scoring
- `../../KB/capability-thresholds.md` - When tools break down, complexity signals

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-01-22 | Initial tech evaluation agent |
| **v2.6** | **2026-01-23** | **v2.6 Upgrade:** |
| | | - Added Confidence Tagging for all estimates |
| | | - Added Anti-Patterns section |
| | | - Added Prerequisites Check with Quantification Gate verification |
| | | - Added detailed Cost Analysis section with confidence |
| | | - Added "What Could Change This" section |
| | | - Added Quality Checklist |
| | | - Enhanced Risk Assessment with confidence tags |
