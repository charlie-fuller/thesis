# Non-Build Solution Patterns for Enterprise Problems

## Purpose

This document provides detailed reference patterns for the seven non-build solution types in the DISCO solution taxonomy. It is designed for DISCO agents to use during Synthesis and Convergence phases when discovery evidence points away from technology development. The core premise: the burden of proof should be on BUILD, not on alternatives. Most enterprise problems are people, process, or knowledge problems -- not technology problems.

---

## The Intervention Ladder

The Intervention Ladder establishes a principle of proportionality: simpler, lower-cost interventions should be considered and ruled out before escalating to more complex ones. Each rung requires stronger evidence to justify skipping.

```
Level 8: BUILD      -- Custom development         [Highest cost, highest risk]
Level 7: BUY        -- Commercial procurement
Level 6: RESTRUCTURE -- Organizational change
Level 5: GOVERN     -- Policy and standards
Level 4: TRAIN      -- Capability development
Level 3: COORDINATE -- Alignment and communication
Level 2: DOCUMENT   -- Knowledge capture
Level 1: ACCEPT     -- Acknowledge without action  [Lowest cost, lowest risk]
         DEFER      -- (Can apply at any level as a timing modifier)
```

### How to Use the Ladder

1. Start at Level 1. Can the problem be accepted or deferred?
2. Move up only when you have evidence that the lower level is insufficient
3. Document why each lower level was rejected before recommending a higher level
4. BUILD (Level 8) requires evidence that Levels 1-7 were all considered

### Escalation Evidence Requirements

| From Level | To Level | Evidence Required |
|---|---|---|
| 1 (ACCEPT) | 2+ | Problem is growing, compounding, or stakeholders cannot plan around it |
| 2 (DOCUMENT) | 3+ | Knowledge exists but teams are not connecting or sharing it |
| 3 (COORDINATE) | 4+ | Teams are connected but lack capability to execute |
| 4 (TRAIN) | 5+ | People have skills but no clear rules or standards guide behavior |
| 5 (GOVERN) | 6+ | Rules exist but organizational structure prevents compliance |
| 6 (RESTRUCTURE) | 7+ | Structure is sound but tools genuinely do not support the work |
| 7 (BUY) | 8 (BUILD) | No commercial solution covers 80%+ of validated requirements; requirements are genuinely unique |

---

## Evidence Thresholds: When BUILD Is Justified

BUILD is the most expensive, highest-risk intervention. It should be recommended only when discovery evidence meets ALL of the following thresholds:

### Mandatory Criteria (All Must Be True)

| Criterion | Evidence Standard |
|---|---|
| Unique requirements | At least 3 requirements that no commercial solution addresses, validated by vendor evaluation (not assumption) |
| Simpler alternatives evaluated | Documentation showing why COORDINATE, TRAIN, GOVERN, DOCUMENT, RESTRUCTURE, and BUY were each insufficient |
| Engineering capacity confirmed | Team has available engineering resources and appetite for long-term ownership |
| Adoption plan exists | Identified users, change management approach, and success metrics defined before build starts |
| TCO justified | 3-year total cost of ownership (build + maintain) is less than commercial alternatives or the cost of inaction |

### Red Flags That BUILD Is Premature

- "We need a custom tool" stated without vendor evaluation
- Requirements are described in terms of features, not validated user problems
- The primary driver is "control" or "flexibility" without specific scenarios
- No one has attempted to solve this with existing tools, coordination, or process changes
- The request originates from a single stakeholder without broad validation

---

## Pattern 1: COORDINATE -- Align Existing Resources

### Pattern Description

Coordination solutions create visibility, communication channels, and handoff mechanisms between existing teams, processes, and tools. No new technology is introduced; no organizational changes are made. The intervention is purely about connecting what already exists.

### Detection Signals from Discovery

- Stakeholders in different teams describe solving the same problem independently
- "We did not know they were working on that" appears in interviews
- Information exists in one team's tools but is invisible to dependent teams
- Handoff points between teams have no defined protocol
- Duplicated reporting or data entry across systems
- Stakeholders describe "throwing work over the wall" to another team

### Concrete Solutions

1. **Shared status cadence**: Weekly 15-minute cross-team standup with rotating facilitator and shared artifact (dashboard, doc, or board)
2. **Liaison role**: Designate one person per team as the cross-team contact for a specific domain, with explicit time allocation (not a side-of-desk responsibility)
3. **Shared artifact**: Create a single shared document, board, or dashboard that both teams update, replacing parallel tracking systems
4. **Handoff protocol**: Document the specific information, format, and timing required at each handoff point; assign ownership of each transition
5. **Joint retrospective**: Quarterly cross-team review of coordination effectiveness with actionable improvements

### Success Criteria

- Duplicated effort is reduced by at least 50% within 3 months
- Handoff failure rate decreases measurably
- Cross-team visibility is confirmed via stakeholder survey (target: 80%+ report improvement)
- No new tools or organizational changes were required

### Effort Estimate

- Design: 1-2 weeks
- Implementation: 1-2 weeks
- Ongoing: 1-2 hours per week for facilitation
- Total: Low effort, low cost, high speed to value

### Common Mistakes

- Adding meetings without retiring existing ones (net increase in meeting load)
- Creating a coordination layer without authority to resolve conflicts
- Assuming coordination will self-sustain without a designated owner
- Over-engineering the coordination mechanism (Slack channel is often enough)
- Treating a structural misalignment as a coordination problem (if incentives conflict, coordination will not fix it)

### Worked Enterprise Example

**Problem**: The Data Engineering team builds data pipelines that the Analytics team consumes. Analytics frequently discovers data quality issues only after building dashboards, causing rework. Both teams want a "data quality tool" built or purchased.

**Why BUILD/BUY is wrong**: Discovery reveals the data quality issues are known to Data Engineering before pipeline deployment, but there is no mechanism to communicate known limitations to Analytics. The data itself is adequate; the communication is not.

**COORDINATE solution**: Implement a "pipeline release note" -- a lightweight document template that Data Engineering completes for each pipeline deployment, listing known limitations, data freshness, and caveats. Analytics reviews before building on the pipeline. A shared Slack channel provides a real-time question path. Monthly joint review assesses whether the approach is working.

**Outcome**: Data quality rework drops by 60%. No new tools purchased. Total cost: 4 hours of setup time and 30 minutes per week of ongoing effort.

---

## Pattern 2: TRAIN -- Upskill People

### Pattern Description

Training solutions address capability gaps where people have access to adequate tools and clear processes but lack the skills, knowledge, or confidence to use them effectively. The intervention focuses on enablement rather than tooling.

### Detection Signals from Discovery

- Users describe existing tools as "too complicated" or "not intuitive"
- Feature adoption data shows less than 30% usage of available capabilities
- Workarounds exist for problems that current tools already solve
- "I just use spreadsheets because I do not know how to do it in [tool]"
- New hires take significantly longer than expected to become productive
- Support tickets cluster around the same features or workflows

### Concrete Solutions

1. **Role-based training tracks**: Targeted curriculum for each persona (e.g., "Salesforce for Sales Managers" vs. "Salesforce for Operations"), delivered in 60-minute sessions with hands-on exercises
2. **Office hours**: Weekly drop-in session with a power user or trainer for ad hoc questions; recorded for asynchronous access
3. **Workflow-specific quick reference cards**: One-page visual guides for the 5 most common workflows, posted where users work (physical or digital)
4. **Peer champion network**: Identify and empower 1 power user per team to provide first-line support and feedback; give them 10% time allocation for the role
5. **Certification or badge program**: Lightweight skill validation that creates social incentive to learn and provides managers with visibility into team capability

### Success Criteria

- Feature adoption increases by at least 30% within 2 months of training
- Workaround usage decreases measurably
- Self-reported confidence scores improve by at least 2 points on a 1-5 scale
- Support ticket volume for trained topics decreases by 25%+
- Time-to-productivity for new hires decreases

### Effort Estimate

- Curriculum design: 2-4 weeks
- Delivery: 2-8 weeks (depending on audience size)
- Ongoing reinforcement: 2-4 hours per week
- Total: Moderate effort, low cost relative to tool procurement

### Common Mistakes

- Training people on tools that are genuinely inadequate (training cannot compensate for bad UX)
- One-time training event with no follow-up or reinforcement
- Training everyone the same way regardless of role or current skill level
- Not measuring training effectiveness (assuming attendance equals learning)
- Training as a checkbox exercise rather than a genuine capability investment

### Worked Enterprise Example

**Problem**: The Marketing team uses a DAM (Digital Asset Management) system but continues to share files via email and Google Drive. Marketing leadership wants to buy a "better DAM."

**Why BUILD/BUY is wrong**: Discovery reveals the current DAM has all required features. Usage analytics show that only 2 of 15 team members upload assets regularly. Interviews reveal most team members received no onboarding on the DAM and find the folder structure confusing.

**TRAIN solution**: Conduct a 90-minute hands-on workshop for the full team covering the 3 most common workflows (upload, search, share). Create a one-page quick reference card. Designate 2 power users as DAM champions with office hours. Reorganize the folder structure based on user feedback. Set a 60-day checkpoint to measure adoption.

**Outcome**: DAM adoption increases from 13% to 72% within 60 days. Email-based file sharing drops proportionally. No new tool purchased. Total cost: 20 hours of trainer time plus 2 hours per week of champion support.

---

## Pattern 3: RESTRUCTURE -- Reorganize Teams or Processes

### Pattern Description

Restructuring solutions address problems caused by organizational design: misaligned incentives, unclear ownership, structural bottlenecks, or reporting lines that prevent effective execution. This is a higher-cost, higher-risk intervention that should only be recommended when coordination and governance approaches have been considered and found insufficient.

### Detection Signals from Discovery

- Chronic coordination failures that persist despite multiple alignment attempts
- "That is not my team's responsibility" heard from multiple parties about the same activity
- Incentives for Team A directly conflict with outcomes needed by Team B
- Process bottlenecks consistently occur at organizational boundaries
- Decision authority does not match accountability ("I am accountable but cannot decide")
- Same problem surfaces in discovery sessions year after year with no resolution

### Concrete Solutions

1. **Ownership transfer**: Move a function, process, or product area from one team to another where incentives and capabilities are better aligned
2. **Cross-functional pod**: Create a dedicated, co-located (physical or virtual) team with members from each relevant function, with shared OKRs and a single leader
3. **Process re-sequencing**: Restructure the workflow so that the bottleneck team is involved earlier (shift-left) rather than acting as a gate at the end
4. **RACI clarification with authority transfer**: Formally assign decision rights (not just responsibility) and communicate the change to all stakeholders with executive sponsorship
5. **Incentive realignment**: Change team metrics, OKRs, or performance criteria so that cooperation is rewarded and siloed behavior is not

### Success Criteria

- Clear, undisputed ownership established for previously contested areas
- Bottleneck throughput improves by at least 30%
- Stakeholders report role clarity in follow-up survey (target: 85%+)
- Behavioral change is observed (not just structural change on paper)
- Cross-functional conflict escalations decrease

### Effort Estimate

- Design: 2-6 weeks (including stakeholder consultation)
- Approval and communication: 2-4 weeks
- Transition: 1-3 months
- Stabilization: 3-6 months
- Total: High effort, significant change management investment

### Common Mistakes

- Restructuring without addressing the root cause (moving boxes on an org chart without changing incentives)
- Underestimating the change management effort (restructuring is emotional, not just operational)
- Creating new silos while dissolving old ones
- Restructuring too frequently, causing organizational fatigue and cynicism
- Not securing executive sponsorship before announcing changes

### Worked Enterprise Example

**Problem**: Product and Engineering teams have persistent conflict over prioritization. Product sets priorities that Engineering cannot deliver on time. Engineering blames Product for unrealistic expectations. Product blames Engineering for slow velocity. Both teams request a "better project management tool."

**Why BUILD/BUY is wrong**: Discovery reveals the current project management tooling is adequate. The root issue is that Product and Engineering have separate leadership, separate OKRs, and no shared accountability for delivery outcomes. Product is measured on "features shipped" while Engineering is measured on "system reliability."

**RESTRUCTURE solution**: Create product-engineering pods with shared OKRs that balance feature delivery and reliability. Each pod has a Product lead and an Engineering lead who jointly own the roadmap. Escalation goes to a single VP who owns both functions for that product area. Restructure quarterly planning to be a joint exercise.

**Outcome**: Feature delivery predictability improves from 40% to 75% within two quarters. Cross-team escalations decrease by 60%. No new tools purchased.

---

## Pattern 4: GOVERN -- Create/Enforce Policies and Standards

### Pattern Description

Governance solutions address problems caused by ambiguity, inconsistency, or lack of clear rules. They establish the "how we do things" framework that enables autonomous decision-making within defined boundaries.

### Detection Signals from Discovery

- "There is no standard for how we do X" repeated by multiple stakeholders
- Same decision is made differently by different teams with no rationale for the difference
- Compliance or risk concerns are raised but no clear policy exists
- Escalation paths are unclear, leading to delayed decisions
- New initiatives start without consistent evaluation criteria
- "It depends on who you ask" is a common response to process questions

### Concrete Solutions

1. **Decision framework with criteria and thresholds**: Document the specific criteria, weights, and thresholds for a recurring decision type (e.g., vendor selection, project prioritization, resource allocation)
2. **Standard operating procedure (SOP) with exception process**: Define the default process and a clear, lightweight path for exceptions (who can approve, what documentation is needed)
3. **Governance committee with defined scope and cadence**: Establish a small committee (3-5 people) with explicit authority over a defined domain, meeting on a regular cadence with published agendas and decisions
4. **Tiered approval matrix**: Define which decisions can be made at which level (individual, manager, VP, committee) based on impact, cost, or risk thresholds
5. **Policy-as-code**: Where possible, encode governance rules into existing tools as automated checks, templates, or workflow gates

### Success Criteria

- Policy is documented, published, and findable by all affected parties
- Compliance rate exceeds 85% within 3 months
- Decision cycle time decreases for governed decision types
- Exception requests are infrequent and handled through the defined process
- Stakeholders report clarity on "how things work" in follow-up surveys

### Effort Estimate

- Policy drafting: 1-3 weeks
- Stakeholder review: 1-2 weeks
- Rollout and communication: 1-2 weeks
- Ongoing enforcement: 2-4 hours per month
- Total: Moderate effort, low ongoing cost

### Common Mistakes

- Creating policy without an enforcement mechanism (policy without teeth)
- Over-governing low-risk activities (governance should be proportional to risk)
- Drafting policy in isolation without input from the people it affects
- No review or sunset cadence (policy becomes stale and ignored)
- Governance that adds bureaucracy without adding clarity

### Worked Enterprise Example

**Problem**: The IT team receives GenAI tool requests from across the organization with no consistent evaluation criteria. Some tools are approved quickly, others languish for months. Business teams want to "build an AI tool request portal."

**Why BUILD/BUY is wrong**: The bottleneck is not the request submission mechanism (email and Jira work fine for that). The bottleneck is the lack of evaluation criteria, risk tiers, and approval authority. A portal would digitize the chaos without resolving it.

**GOVERN solution**: Create a 3-tier GenAI tool evaluation framework: Tier 1 (no customer data, no cost) can be approved by direct manager; Tier 2 (internal data, under $5K/year) requires IT security review using a standard checklist; Tier 3 (customer data or over $5K/year) requires full evaluation by the AI Governance Committee. Publish the framework on the intranet with a one-page decision guide. Review and update quarterly.

**Outcome**: Average approval time drops from 6 weeks to 8 days. Business teams report clarity on what is needed. IT team workload is reduced because 60% of requests are Tier 1 (self-service). No portal built.

---

## Pattern 5: DOCUMENT -- Create Knowledge Assets

### Pattern Description

Documentation solutions capture institutional knowledge, codify processes, and make information accessible to reduce dependency on specific individuals and improve consistency.

### Detection Signals from Discovery

- "Only [person] knows how to do that" appears in multiple interviews
- The same questions are asked repeatedly in Slack or Teams channels
- Different people execute the same process with different steps and different results
- Onboarding new team members takes months because of undocumented tribal knowledge
- Post-incident reviews reveal "we solved this before but did not document it"
- Critical processes exist only in people's heads

### Concrete Solutions

1. **Runbook library**: Step-by-step guides for recurring operational tasks, stored in a searchable location, with screenshots and decision points marked clearly
2. **Decision log**: A running record of significant decisions, the rationale behind them, who was involved, and what alternatives were considered (prevents re-litigating old decisions)
3. **Onboarding playbook**: Role-specific guide covering tools, access, key contacts, common workflows, and "things I wish someone had told me" -- maintained by recent hires
4. **FAQ or knowledge base**: Curated answers to the 20 most frequently asked questions, updated quarterly based on support channel analysis
5. **Process map with swim lanes**: Visual representation of cross-team workflows showing who does what, in what order, with what tools, and where handoffs occur

### Success Criteria

- Documentation is accessed regularly (track page views, search queries)
- Time-to-productivity for new team members decreases by at least 25%
- Repeated questions in support channels decrease by at least 30%
- Process execution consistency improves (measured by output quality or error rate)
- Knowledge is no longer locked to specific individuals

### Effort Estimate

- Initial documentation: 1-4 weeks (depending on scope)
- Review and validation: 1 week
- Ongoing maintenance: 2-4 hours per month with designated owner
- Total: Low to moderate effort, very low ongoing cost

### Common Mistakes

- Creating documentation in a location nobody checks (wrong tool, wrong folder)
- No designated owner for ongoing maintenance (documentation rots)
- Over-documenting everything instead of prioritizing high-impact knowledge
- Documenting a broken process instead of fixing the process first
- Treating documentation as a one-time project rather than a living practice

### Worked Enterprise Example

**Problem**: The Customer Success team spends 30% of their time answering internal questions about product capabilities and integration options. They request a "customer intelligence platform" to automate answer generation.

**Why BUILD/BUY is wrong**: Discovery reveals the questions are repetitive -- 80% of inquiries cluster around 25 topics. The information exists but is scattered across Confluence, Slack, and individual team members' notes. The problem is not information generation; it is information accessibility.

**DOCUMENT solution**: Audit the top 25 question topics from Slack history. Create a structured FAQ with clear, concise answers linked to source documentation. Publish in the team's existing Confluence space with a Slack shortcut for search. Assign a rotating "FAQ gardener" role (2 hours per week) to keep content current. Set a 90-day review checkpoint.

**Outcome**: Internal questions decrease by 55%. Customer Success team reclaims approximately 15% of their time. New team members onboard 40% faster. No new platform built or purchased.

---

## Pattern 6: DEFER -- Consciously Delay Action

### Pattern Description

Deferral is a deliberate, documented decision to delay action. It is not avoidance -- it is strategic patience based on the judgment that acting now would be premature, wasteful, or counterproductive.

### Detection Signals from Discovery

- A related initiative in progress may resolve or redefine the problem
- External factors are shifting rapidly (market conditions, technology landscape, regulatory changes)
- Insufficient data exists to make a confident recommendation
- The problem is real but ranks low relative to other priorities
- Key stakeholders or decision-makers are unavailable for the necessary commitment
- A dependency (budget cycle, contract renewal, platform migration) creates a natural decision point in the near future

### Concrete Solutions

1. **Time-boxed deferral with checkpoint**: Set a specific date (e.g., 90 days) for re-evaluation, assign an owner, and define what information should be gathered in the interim
2. **Trigger-based deferral**: Define specific conditions that would trigger action (e.g., "if support tickets exceed 50/month" or "when the platform migration completes"), with monitoring in place
3. **Exploratory deferral**: Defer the full initiative but approve a small-scale investigation, pilot, or data collection effort to inform the future decision
4. **Dependency-linked deferral**: Explicitly tie the decision to a known dependency with a defined timeline, and subscribe to updates on that dependency
5. **Deferral with interim mitigation**: Delay the full solution but implement a temporary workaround to contain the problem's impact while waiting

### Success Criteria

- Deferral decision is documented with clear rationale, trigger conditions, and review cadence
- All affected stakeholders are informed and aligned
- Monitoring is actively maintained (someone is watching the triggers)
- When the trigger fires or the checkpoint arrives, the team acts promptly
- The deferral does not become indefinite postponement

### Effort Estimate

- Decision and documentation: 1-2 days
- Monitoring setup: 1-2 hours
- Periodic review: 30 minutes per review cycle
- Total: Minimal effort

### Common Mistakes

- Deferring without documenting triggers or review dates (becomes "forgotten")
- Using deferral to avoid difficult conversations or decisions
- Not communicating the deferral to affected stakeholders (they assume nothing is happening)
- Setting vague triggers that are never measurable ("when things settle down")
- Deferring a problem that is actively compounding

### Worked Enterprise Example

**Problem**: The Sales Enablement team wants a content recommendation engine that suggests the right materials for each sales conversation based on deal stage and industry.

**Why BUILD/BUY is wrong (now)**: Discovery reveals the company is 4 months away from migrating its CRM from Salesforce to HubSpot. Any content recommendation system would need deep CRM integration. Building or buying now would mean re-integrating in 4 months. Additionally, the content library itself is being reorganized as part of a separate initiative.

**DEFER solution**: Defer the content recommendation initiative until 60 days after CRM migration completes and the content reorganization is finalized. In the interim, create a simple "content pick list" organized by deal stage and industry (a DOCUMENT intervention) as a temporary measure. Assign the Sales Enablement lead as the owner with a calendar reminder for the checkpoint date.

**Outcome**: The team avoids building something that would need immediate rework. The interim pick list covers 70% of the need at near-zero cost. When the checkpoint arrives, the CRM migration has completed and the team can make a well-informed decision with current data.

---

## Pattern 7: ACCEPT -- Acknowledge Without Action

### Pattern Description

Acceptance is an explicit, documented decision that the cost of any intervention exceeds the cost of the problem. It is not apathy or neglect -- it is a rational conclusion that resources are better deployed elsewhere.

### Detection Signals from Discovery

- The problem exists but quantified impact is low (minor inconvenience, small time cost)
- Every proposed solution costs more than the problem itself (in money, time, or disruption)
- The "problem" is a known trade-off of a deliberate, beneficial decision
- Stakeholders acknowledge the issue when asked but do not prioritize it independently
- The friction is normal and healthy (e.g., code review takes time but improves quality)
- The problem affects a small number of people infrequently

### Concrete Solutions

1. **Documented acceptance with rationale**: Write a brief decision record explaining what the problem is, why intervention was considered, and why acceptance was chosen, with quantified cost-benefit analysis
2. **Stakeholder acknowledgment**: Ensure all affected parties know the decision was made consciously (not by neglect) and understand the rationale
3. **Escalation threshold**: Define what would change the decision (e.g., "if this costs more than X hours per month" or "if it affects more than Y people"), with monitoring
4. **Periodic re-evaluation**: Set a distant but real review date (e.g., annual) to confirm the acceptance decision remains valid
5. **Workaround documentation**: If people have developed workarounds, document the best one so it is at least consistent and efficient

### Success Criteria

- Decision is documented and accessible
- Stakeholders feel heard (even if the answer is "not now")
- Monitoring is in place to detect escalation
- The problem does not worsen beyond the accepted threshold
- No one is surprised that the problem exists

### Effort Estimate

- Decision documentation: 2-4 hours
- Stakeholder communication: 1-2 hours
- Monitoring setup: 30 minutes
- Total: Minimal effort

### Common Mistakes

- Accepting without documenting (problem becomes invisible, then surprises leadership)
- Accepting to avoid conflict rather than based on genuine analysis
- Not monitoring for escalation (problem grows silently)
- Stakeholders feel dismissed rather than heard
- Confusing acceptance with ignorance (acceptance is an active decision)

### Worked Enterprise Example

**Problem**: The Finance team's monthly close process requires 3 manual data transfers between systems that take approximately 2 hours total. A stakeholder requests automation of this workflow.

**Why BUILD/BUY is wrong**: Discovery quantifies the problem at 24 person-hours per year. Automating the transfers would require API integration work estimated at 80-120 hours of engineering time, plus ongoing maintenance. The transfers are not error-prone -- they are just manual. The current process has worked without incident for 18 months.

**ACCEPT solution**: Document the acceptance decision with the cost-benefit analysis (24 hours/year of manual work vs. 100+ hours of automation development plus maintenance). Document the current manual process as a runbook for consistency and knowledge transfer. Set an escalation threshold: if errors begin occurring or if the process grows beyond 4 hours/month, re-evaluate. Review annually.

**Outcome**: The team consciously accepts 2 hours per month of manual work, freeing engineering resources for higher-impact initiatives. The stakeholder understands the rationale and knows the decision will be revisited if conditions change.

---

## Cross-Pattern Reference Table

| Pattern | Speed to Value | Cost | Risk | Change Management | Sustainability |
|---|---|---|---|---|---|
| COORDINATE | Days to weeks | Very low | Very low | Low -- no structural change | Requires ongoing facilitation |
| TRAIN | Weeks | Low | Low | Moderate -- behavior change | Requires reinforcement |
| DOCUMENT | Days to weeks | Very low | Very low | Low -- no behavior change required | Requires maintenance owner |
| GOVERN | Weeks | Low to moderate | Low to moderate | Moderate -- compliance required | Requires enforcement mechanism |
| RESTRUCTURE | Months | High | High | Very high -- identity and role change | Self-sustaining if incentives align |
| DEFER | Immediate | None | Low (if monitored) | Low -- communication only | Requires active monitoring |
| ACCEPT | Immediate | None | Low (if monitored) | Low -- communication only | Requires periodic review |

---

## Agent Application Guidelines

### During Synthesis

1. When discovery evidence surfaces a problem, start at the bottom of the Intervention Ladder
2. For each level, ask: "Is there evidence that this level of intervention is insufficient?"
3. Only escalate when you have specific, cited evidence from discovery
4. Document the reasoning chain: "We considered COORDINATE but evidence X shows the problem is structural, so RESTRUCTURE is recommended"

### During Convergence

1. For non-build recommendations, produce an Assessment document (not a PRD)
2. Include the Intervention Ladder analysis showing why lower levels were insufficient
3. Provide specific, actionable solutions (not generic advice)
4. Define success criteria that are measurable within 90 days
5. Always include monitoring and escalation thresholds

### Challenging BUILD Recommendations

When a BUILD recommendation emerges from synthesis, agents should apply these challenge questions:

1. Has anyone tried to solve this with existing tools and coordination? What happened?
2. Have commercial solutions been evaluated with documented criteria? Which ones and why were they rejected?
3. Is the root cause a technology gap or a people/process/knowledge gap?
4. Would the problem persist even with perfect tooling? (If yes, the solution is not BUILD)
5. Is the organization prepared to own and maintain custom software for 3+ years?
6. What is the simplest possible intervention that could reduce this problem by 50%?

If these questions cannot be answered with specific, evidence-based responses, the BUILD recommendation is premature. Return to the Intervention Ladder.
