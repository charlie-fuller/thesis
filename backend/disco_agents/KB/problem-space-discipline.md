# Problem Space Discipline

> **Source**: DISCO Pipeline KB -- Deep Research Reference
> **Purpose**: Teaches agents to stay in the problem space long enough, resist premature convergence, and recognize that "no action" is a valid professional outcome.

## Overview

Problem Space Discipline is the practice of deliberately resisting the gravitational pull toward solutions until the problem is sufficiently understood, quantified, and validated. In enterprise product discovery, the most expensive mistakes are not building the wrong thing -- they are building anything at all when the problem did not warrant a build. This document provides decision frameworks, detection signals, and structured taxonomies for agents operating in the DISCO pipeline.

---

## 1. Problem Space vs. Solution Space

### Definitions

| Space | Focus | Activities | Output |
|-------|-------|------------|--------|
| **Problem Space** | Understanding needs, pains, constraints | Interviews, observation, data analysis, process mapping | Problem statements, gap reports, root cause models |
| **Solution Space** | Designing responses to validated problems | Prototyping, architecture, vendor evaluation, roadmapping | PRDs, build/buy recommendations, implementation plans |

### The Boundary Rule

The boundary between problem space and solution space is not a phase gate -- it is a discipline. Teams cross it constantly and unconsciously. The agent's role is to detect crossings and redirect when they are premature.

**Key principle**: You can reference the solution space to validate problem understanding ("If we built X, would that address what you described?") but you must not commit to solution evaluation until the Dwell Time Criteria (Section 2) are satisfied.

### Premature Convergence Signal Phrases

When these phrases appear in discovery session transcripts, stakeholder interviews, or initiative descriptions, they indicate the conversation has jumped to solutions before the problem is adequately explored.

#### High-Confidence Signals (Almost Always Premature)

| Signal Phrase | What It Reveals | Agent Response |
|---------------|-----------------|----------------|
| "We just need..." | Assumes solution simplicity; skips problem scoping | Ask: "What happens today without it? How often? What does it cost?" |
| "If only we had..." | Wishful-tool thinking; anchors on a specific solution | Ask: "What would change if you had it? How do you handle this today?" |
| "The obvious answer is..." | Closes down exploration; assumes consensus | Ask: "What has been tried before? Why didn't it work?" |
| "Can't we just..." | Minimizes complexity; signals impatience with discovery | Ask: "Walk me through the current workflow. Where does it break?" |
| "We need an AI that..." | Technology-first framing; skips need validation | Ask: "What decision or task would improve? How is it done now?" |
| "Let's just buy..." | Vendor-first thinking; skips problem quantification | Ask: "What is the cost of the current state? Who is affected?" |

#### Moderate-Confidence Signals (Context-Dependent)

| Signal Phrase | When It Is Premature | When It Is Legitimate |
|---------------|----------------------|----------------------|
| "I've seen this solved by..." | Before root cause is established | After validated problem with analogous context |
| "There's a tool for this" | Before problem is quantified | During solution-type hypothesis formation |
| "We should automate..." | Before process is mapped and stable | After stable, repeatable process is documented |
| "The real issue is..." | When stated by someone without direct operational experience | When stated by the person who does the work daily |

#### AI Tool Proliferation Bias (2025-2026 Context)

Enterprise environments in 2025-2026 face a specific form of solution bias driven by AI tool proliferation. According to industry research, 72% of AI investments are destroying value rather than creating it, driven by tool sprawl and unmanaged "Shadow AI." Over 28% of enterprises now use more than 10 different AI applications, and 70% have not moved beyond basic integration. Gartner predicts 40% of enterprise apps will feature task-specific AI agents by 2026, up from less than 5% in 2025.

This environment creates three distinct biases agents must detect:

| Bias | Description | Detection Signal |
|------|-------------|------------------|
| **AI Hammer Bias** | Every problem looks like it needs an AI solution | "We should use AI/ML to..." appears before the problem is quantified |
| **Tool Accumulation Bias** | Adding another tool feels like progress | "We just need one more tool that..." without assessing existing tool utilization |
| **Demo-Driven Discovery** | A vendor demo reframes the problem to fit the product | Problem statement changes after a vendor presentation |

**Agent directive**: When AI or specific tooling is mentioned before the problem is quantified, flag the conversation as exhibiting solution bias and redirect to problem quantification.

---

## 2. Dwell Time Criteria

Dwell Time is the minimum period and depth of investigation required before it is responsible to move from problem space to solution space. Moving too early wastes resources on wrong solutions. Moving too late creates analysis paralysis.

### The Checklist

All six criteria must be satisfied before an agent recommends transitioning to solution evaluation. If any criterion is unmet, the agent should identify it as a gap and recommend further investigation.

| # | Criterion | Definition | Evidence Required | Status |
|---|-----------|------------|-------------------|--------|
| 1 | **Root cause identified and validated** | The underlying cause of the problem is established through evidence, not assumption | At least 2 independent data sources confirm the root cause; alternative causes explicitly ruled out | [ ] Met / [ ] Unmet |
| 2 | **Problem quantified (cost / frequency / impact)** | The problem has measurable dimensions: how much it costs, how often it occurs, and who it affects | Numeric estimates for at least 2 of: annual cost, frequency per week/month, number of people affected, hours wasted | [ ] Met / [ ] Unmet |
| 3 | **Solution-type hypothesis formed** | A general category of solution (not a specific product) has been hypothesized | Statement of the form "This is likely a [COORDINATE/TRAIN/BUILD/etc.] problem" with reasoning | [ ] Met / [ ] Unmet |
| 4 | **2+ discovery sessions completed** | Multiple perspectives have been gathered across sessions | Session notes from at least 2 separate discovery conversations with different participants or different angles | [ ] Met / [ ] Unmet |
| 5 | **Problem statement stable across sessions** | The core problem description has not materially changed between the most recent sessions | Side-by-side comparison of problem statements from sessions N and N-1 shows convergence, not divergence | [ ] Met / [ ] Unmet |
| 6 | **"No action" explicitly considered and rejected** | The team has formally evaluated whether doing nothing is the best course | Documented assessment of the cost-of-living-with-it vs. cost-of-solving (see Section 5); explicit rationale for why action is warranted | [ ] Met / [ ] Unmet |

### Decision Tree: Is It Safe to Move to Solutions?

```
START: Has the problem been investigated?
  |
  +-- NO --> Conduct initial discovery session --> STAY IN PROBLEM SPACE
  |
  +-- YES --> Is root cause validated by 2+ sources?
        |
        +-- NO --> Investigate further; rule out alternative causes --> STAY IN PROBLEM SPACE
        |
        +-- YES --> Is the problem quantified (cost/frequency/impact)?
              |
              +-- NO --> Quantify: gather data on cost, frequency, affected people --> STAY IN PROBLEM SPACE
              |
              +-- YES --> Have 2+ discovery sessions been completed?
                    |
                    +-- NO --> Schedule additional sessions with different stakeholders --> STAY IN PROBLEM SPACE
                    |
                    +-- YES --> Is the problem statement stable across sessions?
                          |
                          +-- NO --> Problem is still shifting; needs more investigation --> STAY IN PROBLEM SPACE
                          |
                          +-- YES --> Has "no action" been explicitly evaluated?
                                |
                                +-- NO --> Conduct cost-of-living-with-it analysis (Section 5) --> STAY IN PROBLEM SPACE
                                |
                                +-- YES, and action is warranted --> READY TO MOVE TO SOLUTION SPACE
                                |
                                +-- YES, and no action is best --> RECOMMEND NO ACTION (Section 3)
```

### Dwell Time Anti-Patterns

| Anti-Pattern | Description | Remedy |
|--------------|-------------|--------|
| **Checkbox Discovery** | Rushing through sessions to "check the box" without deep investigation | Require specific evidence artifacts, not just session counts |
| **Echo Chamber Validation** | Interviewing only people who agree on the problem | Ensure at least one session includes a skeptic or someone unaffected |
| **Quantification Theater** | Producing numbers without methodology ("it costs millions") | Require explicit calculation methodology: inputs, assumptions, formula |
| **Premature Stability** | Declaring the problem statement stable after only surface-level agreement | Test stability by introducing contradictory evidence and observing if the statement holds |

---

## 3. "No Action" as a Valid Professional Outcome

### The Principle

Recommending "no action" after rigorous discovery is not failure -- it is one of the highest-value outcomes a discovery process can produce. It prevents wasted investment, avoids change fatigue, and preserves organizational capacity for problems that genuinely warrant intervention.

**The professional standard**: A recommendation of "no action" backed by evidence is more valuable than a recommendation to build backed by enthusiasm.

### When "No Action" Is the Right Call

| Condition | Reasoning |
|-----------|-----------|
| Cost of solving exceeds cost of living with it (over 3 years) | The problem is real but the cure is worse than the disease |
| Problem is self-correcting | An organizational change, market shift, or system migration already underway will resolve it |
| Insufficient organizational readiness | The organization lacks sponsor strength, team capacity, or appetite for change right now (see Section 6) |
| Problem affects too few people to justify intervention | Impact is contained; affected individuals have developed effective workarounds |
| Root cause is upstream and outside control | The real fix requires action by a different team, vendor, or executive; local intervention would be a bandage |
| Solution would create worse problems | Automation of a broken process codifies the brokenness; new tooling increases tool sprawl |

### Framing "No Action" for Stakeholders

Agents must help frame "no action" recommendations in ways that are professional, evidence-based, and constructive. Stakeholders often interpret "no action" as "you wasted our time" unless it is positioned correctly.

**Framing Template**:

> **Finding**: After [N] discovery sessions and analysis of [data sources], we have identified [problem statement].
>
> **Assessment**: The annual cost of this problem is approximately [X]. The estimated cost to address it (including implementation, change management, and ongoing maintenance) is [Y] over [Z] years.
>
> **Recommendation**: We recommend **monitoring without intervention** at this time because [primary reason]. We have established [metric/trigger] as the threshold at which this recommendation should be revisited.
>
> **Value of this finding**: This analysis has prevented an estimated [Y] in premature investment and preserved team capacity for [higher-priority initiative].

### "No Action" Sub-Types

Not all "no action" recommendations are the same. Agents should specify the sub-type:

| Sub-Type | Definition | Review Trigger |
|----------|------------|----------------|
| **MONITOR** | Problem is real but below action threshold; watch for escalation | Cost doubles, frequency increases 50%, or affected population grows |
| **DEFER** | Problem warrants action but timing is wrong (see DEFER in Section 4) | Blocking condition resolves (migration completes, budget cycle opens, sponsor identified) |
| **ACCEPT** | Problem is real but the cost of living with it is permanently lower than any intervention (see ACCEPT in Section 4) | Fundamental change in cost structure or available solutions |
| **REDIRECT** | Problem is real but the root cause is owned by another team or initiative | Other team/initiative takes action, or ownership is reassigned |

---

## 4. Non-Build Solutions Taxonomy

Most enterprise problems do not require building software. The nine solution types below are ordered from lightest intervention to heaviest. Agents should evaluate options starting from the top and moving down, recommending the lightest intervention that adequately addresses the validated problem.

### Taxonomy Table

| # | Type | Definition | Detection Signals | Typical Effort | Typical Timeline | Success Criteria |
|---|------|------------|-------------------|----------------|------------------|------------------|
| 1 | **COORDINATE** | The problem exists because people or teams are not aligned, not because tools or processes are missing | "The left hand doesn't know what the right hand is doing"; duplicate work across teams; conflicting priorities; information silos | Low: meeting cadence, shared channels, RACI clarification | 2-4 weeks to establish; 1-2 quarters to see results | Duplicate work eliminated; decisions made faster; stakeholders report alignment |
| 2 | **TRAIN** | The capability exists but people do not know how to use it, or use it incorrectly | "Nobody knows how to use [tool]"; underutilized features in existing platforms; recurring mistakes from knowledge gaps; high support ticket volume for existing tools | Low-Medium: training materials, workshops, office hours | 2-6 weeks for initial training; ongoing enablement | Tool utilization increases measurably; support tickets for trained topics decrease 50%+; task completion time decreases |
| 3 | **RESTRUCTURE** | The problem is caused by organizational design, reporting lines, or team composition, not by tools or processes | Handoffs between teams create delays; accountability is unclear; skills are in the wrong team; approval chains are too long | Medium-High: org design, role redefinition, hiring/reassignment | 1-2 quarters for design; 2-4 quarters for full implementation | Handoff time reduced; accountability clear (single owner per outcome); team satisfaction improves |
| 4 | **GOVERN** | The problem exists because there are no rules, standards, or enforcement mechanisms | Inconsistent outputs; every team does it differently; no quality standards; "shadow" processes and tools proliferating; compliance gaps | Medium: policy creation, review cadence, enforcement tooling | 4-8 weeks for policy design; 1-2 quarters for adoption | Compliance rate measurable and above threshold; variance across teams reduced; audit findings decrease |
| 5 | **DOCUMENT** | The knowledge exists but is not captured, findable, or maintained | "Ask [person name]" is the answer to every question; critical processes live in one person's head; onboarding takes months; same questions asked repeatedly | Low-Medium: documentation sprints, knowledge base setup, templates | 2-6 weeks for initial documentation; ongoing maintenance cadence | Time-to-answer for common questions drops; onboarding time decreases; bus factor increases from 1 to 3+ |
| 6 | **DEFER** | The problem is real and warrants action, but conditions are not right for intervention now | Organization mid-migration; budget cycle closed; key sponsor departing; competing priority consumes team capacity; prerequisite system not yet in place | None (now): set calendar reminder, define trigger conditions | Re-evaluate at defined trigger point (typically 1-2 quarters) | Trigger conditions documented; re-evaluation happens on schedule; problem does not silently escalate |
| 7 | **ACCEPT** | The problem is real but the cost of any intervention permanently exceeds the cost of living with it | Affects very few people; effective workarounds exist; cost of change management exceeds efficiency gains; problem is annoying but not damaging | None: document the decision and rationale | Permanent unless conditions change fundamentally | Decision documented and communicated; team stops spending emotional energy on it; no further discovery cycles wasted |
| 8 | **BUY** | The problem requires a tool or platform, and a suitable commercial solution exists | Problem is common across industries (not unique); vendor solutions are mature; internal team lacks capacity to build and maintain; speed to value is critical | Medium-High: vendor evaluation, procurement, implementation, integration | 1-3 quarters including evaluation, procurement, and rollout | Tool adopted by target users; measurable improvement on quantified problem metrics; TCO within budget |
| 9 | **BUILD** | The problem requires a custom solution because it is unique to the organization, involves proprietary processes, or no adequate commercial solution exists | Problem is unique to the organization's competitive position; existing tools evaluated and ruled out; internal team has capacity to build AND maintain; long-term TCO favors build | High: development, testing, deployment, ongoing maintenance, documentation, on-call | 2-4 quarters for MVP; ongoing investment | Custom solution deployed; adoption targets met; problem metrics improve; maintenance is sustainable |

### Solution Type Decision Tree

```
START: Problem validated and quantified (Dwell Time Criteria met)
  |
  +-- Is the problem caused by misalignment between people/teams?
  |     +-- YES --> COORDINATE
  |
  +-- Is the capability already available but underused?
  |     +-- YES --> TRAIN
  |
  +-- Is the problem caused by organizational structure?
  |     +-- YES --> RESTRUCTURE
  |
  +-- Is the problem caused by lack of standards or enforcement?
  |     +-- YES --> GOVERN
  |
  +-- Is the problem caused by knowledge trapped in people's heads?
  |     +-- YES --> DOCUMENT
  |
  +-- Is the timing wrong for intervention? (Migration underway, budget frozen, no sponsor)
  |     +-- YES --> DEFER (set re-evaluation trigger)
  |
  +-- Is the cost of any intervention > cost of living with it?
  |     +-- YES --> ACCEPT (document and communicate)
  |
  +-- Does a mature commercial solution exist?
  |     +-- YES --> BUY (evaluate vendors)
  |     +-- NO --> BUILD (scope MVP)
```

### Distribution Heuristic

In a healthy enterprise discovery practice, the distribution of recommendations across solution types should roughly follow this pattern:

| Solution Type | Expected Frequency | If Over-Represented |
|---------------|--------------------|---------------------|
| COORDINATE | 15-25% | Normal -- most enterprises have alignment problems |
| TRAIN | 10-20% | May indicate poor onboarding or change management |
| RESTRUCTURE | 5-10% | Over 10% suggests org design review is needed |
| GOVERN | 10-15% | Over 15% suggests governance debt |
| DOCUMENT | 10-15% | Over 15% suggests knowledge management crisis |
| DEFER | 5-15% | Over 15% suggests decision avoidance culture |
| ACCEPT | 5-10% | Under 5% suggests teams are not willing to let problems go |
| BUY | 10-20% | Over 20% suggests vendor dependency pattern |
| BUILD | 5-15% | Over 15% suggests NIH syndrome (Not Invented Here) |

**Agent directive**: If BUILD or BUY together exceed 40% of recommendations, flag this as potential solution bias and recommend a portfolio review.

---

## 5. Cost of Solving vs. Cost of Living With It Framework

This framework provides the quantitative foundation for the "no action" evaluation in Dwell Time Criterion #6. It forces explicit comparison between the total cost of intervention and the total cost of continued operation under the current state.

### The Comparison Model

| Cost Category | Cost of Living With It (Annual) | Cost of Solving (Total 3-Year) |
|---------------|--------------------------------|-------------------------------|
| **Direct labor cost** | Hours wasted x hourly rate x frequency | Implementation hours x rate |
| **Opportunity cost** | Revenue/value not captured | Team capacity consumed (what else could they build?) |
| **Error/rework cost** | Error rate x cost per error x frequency | Testing, QA, bug fixes |
| **Tool/infrastructure** | Current tool costs (if any) | New tool licenses + infrastructure + integration |
| **Change management** | N/A (current state) | Training, documentation, transition period productivity loss |
| **Ongoing maintenance** | Current maintenance (if any) | Annual maintenance, support, upgrades |
| **Risk/compliance** | Probability x impact of adverse event | Residual risk after solution + new risks introduced |
| **Morale/retention** | Estimated attrition cost from frustration | Change fatigue cost (see Section 6) |
| **TOTAL** | Sum = Annual Cost of Inaction | Sum = 3-Year Cost of Action |

**Decision rule**: If (3-Year Cost of Action) > (Annual Cost of Inaction x 3), the intervention does not pay for itself within 3 years. Recommend ACCEPT or DEFER unless there are compelling non-financial reasons (compliance, safety, strategic positioning).

### Worked Enterprise Examples

#### Example A: Manual Report Generation

> **Problem**: A team of 4 analysts spends 8 hours per week each manually compiling a cross-system report.
>
> **Cost of Living With It (Annual)**:
> - Direct labor: 4 people x 8 hours x 50 weeks x $75/hr = **$120,000/year**
> - Error rate: ~2 errors/month requiring 4 hours rework = $7,200/year
> - Total annual cost: **$127,200**
>
> **Cost of Solving (3-Year, BUILD automated pipeline)**:
> - Development: 3 engineers x 6 weeks x 40 hrs x $100/hr = $72,000
> - Infrastructure: $500/month x 36 months = $18,000
> - Maintenance: 4 hrs/week x 50 weeks x $100/hr x 3 years = $60,000
> - Change management: 2 weeks training + transition = $12,000
> - Total 3-year cost: **$162,000**
>
> **Comparison**: $162,000 (solve) vs. $381,600 (live with it x 3 years)
>
> **Verdict**: **Action warranted**. Payback period is approximately 15 months. But first evaluate COORDINATE (can the report be eliminated?) and TRAIN (can existing BI tools produce it?).

#### Example B: Inconsistent Naming Conventions Across Teams

> **Problem**: Three teams use different naming conventions for Salesforce fields, causing confusion in cross-team reports.
>
> **Cost of Living With It (Annual)**:
> - Confusion time: ~2 hours/week across all affected staff = $7,800/year
> - Occasional wrong-field errors: ~$3,000/year in correction effort
> - Total annual cost: **$10,800**
>
> **Cost of Solving (3-Year, BUILD custom validation layer)**:
> - Development: 2 engineers x 4 weeks x 40 hrs x $100/hr = $32,000
> - Migration of existing data: 1 engineer x 3 weeks = $12,000
> - Change management and retraining: $8,000
> - Ongoing maintenance: $6,000/year x 3 years = $18,000
> - Total 3-year cost: **$70,000**
>
> **Comparison**: $70,000 (solve with BUILD) vs. $32,400 (live with it x 3 years)
>
> **Verdict**: **BUILD is not warranted**. But GOVERN (establish naming convention, enforce in review) at ~$5,000 effort could reduce the annual cost by 60%. Recommend GOVERN.

#### Example C: AI Chatbot for Internal IT Help Desk

> **Problem**: IT help desk receives 200 tickets/week, 40% are repetitive password resets and FAQ-type questions.
>
> **Cost of Living With It (Annual)**:
> - Repetitive ticket handling: 80 tickets x 15 min x 50 weeks x $40/hr = **$40,000/year**
> - Employee wait time: 80 tickets x 30 min wait x $50/hr = $100,000/year (opportunity cost)
> - Total annual cost: **$140,000**
>
> **Cost of Solving (3-Year, BUY AI chatbot platform)**:
> - Vendor license: $2,000/month x 36 months = $72,000
> - Integration and setup: $25,000
> - Training and knowledge base creation: $15,000
> - Ongoing tuning and maintenance: $10,000/year x 3 years = $30,000
> - Change management: $8,000
> - Total 3-year cost: **$150,000**
>
> **Comparison**: $150,000 (solve) vs. $420,000 (live with it x 3 years)
>
> **Verdict**: **Action warranted**. But first evaluate DOCUMENT (self-service FAQ) and TRAIN (password self-service enablement), which could address 50-70% of the problem at 10% of the cost. If DOCUMENT + TRAIN reduce the annual cost to $50,000, the chatbot ROI weakens significantly.

### Common Errors in Cost Analysis

| Error | Description | Correction |
|-------|-------------|------------|
| **Ignoring maintenance** | Calculating build cost without ongoing upkeep | Add 15-25% of build cost annually for maintenance |
| **Phantom opportunity cost** | Claiming freed time will generate revenue without a plan for it | Only count opportunity cost if there is a specific, planned use for the freed capacity |
| **Discount rate neglect** | Treating future costs as equal to present costs | Apply a discount rate (typically 8-12% for enterprise) to future cash flows |
| **Change management blindness** | Omitting the cost of getting people to actually adopt the solution | Add 10-20% of total project cost for change management |
| **Sunk cost inclusion** | Including money already spent as part of the "cost of solving" | Only include forward-looking costs |

---

## 6. Organizational Readiness Assessment

Even when a problem is validated, quantified, and warrants action, the organization may not be ready to absorb the change. Deploying a solution into an unready organization wastes the investment and creates resistance that makes future initiatives harder. Research from Prosci and other change management frameworks consistently shows that organizational readiness is a stronger predictor of initiative success than solution quality.

### The Four Readiness Dimensions

#### 6a. Change Fatigue

| Factor | Low Fatigue (Green) | Moderate Fatigue (Yellow) | High Fatigue (Red) |
|--------|--------------------|--------------------------|--------------------|
| Active change initiatives | 0-1 concurrent | 2-3 concurrent | 4+ concurrent |
| Time since last major change | 6+ months | 3-6 months | Less than 3 months |
| Employee sentiment | "Ready for improvement" | "Cautiously open" | "Not another thing" |
| Completion rate of recent initiatives | 80%+ completed as planned | 50-80% completed | Under 50% completed |

**Agent directive**: If Change Fatigue is Red, recommend DEFER regardless of problem severity, unless the problem involves immediate compliance or safety risk.

#### 6b. Competing Priorities

| Factor | Clear Path (Green) | Crowded (Yellow) | Blocked (Red) |
|--------|--------------------|--------------------|----------------|
| Number of active strategic priorities | 1-3 for the affected team | 4-5 | 6+ or "everything is priority 1" |
| This initiative's rank | Top 3 | 4-6 | Not ranked or below 6 |
| Resource conflicts | No shared resources with other initiatives | Some overlap, manageable | Key resources fully committed elsewhere |
| Executive attention available | Sponsor has bandwidth | Sponsor is juggling | Sponsor is overwhelmed or absent |

**Agent directive**: If Competing Priorities is Red, recommend DEFER and specify which competing priority would need to complete or de-scope before this initiative can proceed.

#### 6c. Sponsor Strength

| Factor | Strong Sponsor (Green) | Adequate Sponsor (Yellow) | Weak/No Sponsor (Red) |
|--------|------------------------|---------------------------|-----------------------|
| Authority level | Can approve budget and direct affected teams | Can influence but needs escalation for budget/people | Has interest but no authority |
| Engagement level | Actively participates in discovery; removes blockers | Available when asked; responds to updates | Passive; delegates everything; hard to reach |
| Organizational credibility | Respected across affected teams; track record of successful initiatives | Respected within own team | New to role, or credibility damaged by past failures |
| Commitment signal | Has publicly committed to the initiative | Has verbally supported it privately | Has not explicitly endorsed it |

**Agent directive**: If Sponsor Strength is Red, do not recommend any solution type that requires budget, cross-team coordination, or organizational change. Recommend DOCUMENT or COORDINATE (lightweight interventions) or DEFER until a sponsor is secured.

#### 6d. Team Capacity

| Factor | Available (Green) | Stretched (Yellow) | Overloaded (Red) |
|--------|--------------------|--------------------|-------------------|
| Current utilization | Under 80% | 80-95% | Over 95% or in sustained crunch |
| Key skills available | Team has required skills in-house | Skills available but in high demand | Missing critical skills; would need to hire or contract |
| Backlog health | Manageable; team regularly completes sprint commitments | Growing; team completes 60-80% of commitments | Out of control; team is firefighting |
| Attrition risk | Stable team; low turnover | Some turnover or impending departures | Key people actively looking or recently departed |

**Agent directive**: If Team Capacity is Red, only recommend interventions that reduce load (ACCEPT, DEFER) or require no team capacity (COORDINATE at leadership level). Do not recommend BUILD or BUY, which require significant team investment to implement.

### Readiness Scoring

| Dimension | Score |
|-----------|-------|
| Change Fatigue | Green (3) / Yellow (2) / Red (1) |
| Competing Priorities | Green (3) / Yellow (2) / Red (1) |
| Sponsor Strength | Green (3) / Yellow (2) / Red (1) |
| Team Capacity | Green (3) / Yellow (2) / Red (1) |
| **Total** | **/12** |

| Total Score | Readiness Level | Recommendation |
|-------------|-----------------|----------------|
| 10-12 | **Ready** | Proceed with any warranted solution type |
| 7-9 | **Conditional** | Proceed with lightweight solutions (COORDINATE, TRAIN, DOCUMENT, GOVERN); DEFER heavier interventions until specific conditions improve |
| 4-6 | **Not Ready** | DEFER all but the lightest interventions; focus on readiness improvement |
| 1-3 | **Crisis** | ACCEPT current state or REDIRECT to leadership for organizational intervention |

### Readiness Override Conditions

In rare cases, action must proceed despite low readiness:

| Override Condition | Rationale | Mitigation |
|--------------------|-----------|------------|
| Regulatory deadline | Non-compliance penalty exceeds all readiness costs | Narrow scope to minimum viable compliance; accept higher change management cost |
| Security breach or active incident | Immediate harm exceeds organizational comfort | Emergency intervention with explicit post-incident review |
| Contractual obligation | Failure to act triggers contract penalties | Scope to contractual minimum; defer enhancements |

---

## Agent Integration Notes

### How DISCO Agents Should Use This Document

| Agent | Usage |
|-------|-------|
| **Discovery Planner** | Reference Dwell Time Criteria when designing discovery plans; ensure all 6 criteria are targeted by planned sessions |
| **Insight Extractor** | Detect premature convergence signal phrases in transcripts and flag them; tag insights with problem-space vs. solution-space classification |
| **Coverage Tracker** | Track Dwell Time Criteria completion status per initiative; flag initiatives attempting to skip criteria |
| **Synthesizer** | Apply Non-Build Solutions Taxonomy when forming recommendations; default to lightest intervention; include Cost of Solving vs. Cost of Living With It when recommending action |
| **Triage** | Use Organizational Readiness Assessment during initial triage to determine if an initiative should enter the pipeline at all |
| **Consolidator** | When comparing across initiatives, normalize recommendations using the taxonomy; flag portfolio-level solution bias (BUILD/BUY > 40%) |

### Cross-References

- **Build vs. Buy Decision Framework** (`build-vs-buy.md`): Use after this document determines BUILD or BUY is warranted
- **Trade-off Frameworks** (`trade-off-frameworks.md`): Apply when evaluating solution architecture choices
- **Gap Taxonomy Reference** (`gap-taxonomy-reference.md`): Use gap types to structure problem-space investigation
- **Impact-Effort Scoring** (`impact-effort-scoring.md`): Use to compare intervention options within the taxonomy
- **Initiative Risk Framework** (`initiative-risk-framework.md`): Cross-reference readiness assessment with risk factors
- **Project Failures and Warning Signs** (`project-failures.md`): Review failure patterns before recommending BUILD

---

## References

- [SVPG: Discovery - Problem vs. Solution](https://www.svpg.com/discovery-problem-vs-solution/)
- [Prosci: Change Management Readiness Assessment](https://www.prosci.com/blog/when-should-you-use-a-change-management-readiness-assessment)
- [TechCrunch: VCs predict enterprises will spend more on AI in 2026 through fewer vendors](https://techcrunch.com/2025/12/30/vcs-predict-enterprises-will-spend-more-on-ai-in-2026-through-fewer-vendors/)
- [Zapier: Tool sprawl limits AI integration for 70% of enterprises](https://zapier.com/blog/ai-sprawl-survey/)
- [Gartner: 40% of enterprise apps will feature AI agents by 2026](https://www.gartner.com/en/newsroom/press-releases/2025-08-26-gartner-predicts-40-percent-of-enterprise-apps-will-feature-task-specific-ai-agents-by-2026-up-from-less-than-5-percent-in-2025)
- [SDxCentral: How enterprises can identify and control AI sprawl](https://www.sdxcentral.com/analysis/how-enterprises-can-identify-and-control-ai-sprawl/)
- [Korn Ferry: Overcoming Change Fatigue](https://www.kornferry.com/insights/featured-topics/leadership/overcoming-change-fatigue)
