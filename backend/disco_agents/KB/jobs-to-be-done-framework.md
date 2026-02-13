# Jobs-to-Be-Done Framework for Enterprise Discovery

## Purpose

This document is an agent-consumable reference for applying Jobs-to-Be-Done (JTBD) theory during the Discovery stage of the DISCO pipeline. It is adapted specifically for enterprise internal tool and process discovery -- not consumer product innovation. The focus is on validating whether problems are real, worth solving, and not already adequately served by existing solutions.

---

## 1. JTBD Core Theory for Enterprise Contexts

### The Foundational Principle

People (and organizations) do not want products or tools. They want to make progress in a specific situation. A "job" is the progress a person or team is trying to make in a given circumstance. Tools, processes, and workarounds are all "hired" to do that job.

In enterprise contexts, the "customer" is an internal stakeholder -- a business unit leader, an operations team, a data analyst, a compliance officer. They hire internal tools, processes, vendor products, and manual workarounds to get their jobs done.

### Three Dimensions of Enterprise Jobs

| Dimension | Definition | Enterprise Example |
|-----------|------------|--------------------|
| **Functional** | The practical task the stakeholder needs to accomplish | "Generate a quarterly compliance report that satisfies audit requirements within 5 business days of quarter close" |
| **Emotional** | How the stakeholder wants to feel (or avoid feeling) while doing the job | "Feel confident that the numbers are accurate before presenting to the board" / "Avoid the anxiety of manual data reconciliation" |
| **Social** | How the stakeholder wants to be perceived by others | "Be seen as a data-driven leader by the executive team" / "Not be the person who holds up the quarterly close process" |

### Why All Three Dimensions Matter in Discovery

Discovery often focuses exclusively on functional jobs. This is a mistake in enterprise contexts because:

- **Emotional jobs explain resistance to change.** A team may reject a faster tool because they do not trust it. The functional job is served, but the emotional job (confidence in accuracy) is not.
- **Social jobs explain adoption patterns.** A manager may resist automation because it reduces their team's visible contribution, threatening their organizational standing.
- **Functional-only analysis leads to technically correct but organizationally rejected solutions.**

### Job Statement Syntax

Use this structure for precise, testable job statements:

```
[Action verb] + [object of the action] + [contextual qualifier]
```

**Examples**:

| Bad Job Statement | Problem | Good Job Statement |
|-------------------|---------|--------------------|
| "Need a better dashboard" | Solution-contaminated; a dashboard is a solution, not a job | "Monitor key SaaS renewal dates so no contract auto-renews without review" |
| "Want to automate reporting" | Automation is a solution; what job does reporting serve? | "Deliver accurate department spend data to finance within 48 hours of month close" |
| "Need AI for customer support" | Technology-first framing | "Resolve tier-1 customer inquiries within 4 hours without escalation to specialized agents" |

---

## 2. JTBD for Problem Validation During Triage

### The Triage Question

During Discovery triage, the critical question is: **Is this problem real, and is it worth solving?** JTBD provides a structured way to answer this by separating the job from the current solution.

### Problem Validation Decision Tree

```
START: A stakeholder has described a problem or requested a solution.
  |
  v
Can you identify the underlying job (not the requested solution)?
  |
  +-- NO --> Conduct a Switch Interview (Section 3) to uncover the job.
  |
  +-- YES --> Is the job currently being done at all?
                |
                +-- NO --> NEW JOB: High potential value, but validate
                |          demand -- why isn't anyone doing this today?
                |          Is it a real need or a hypothetical?
                |
                +-- YES --> How well is the job currently being served?
                              |
                              +-- POORLY (high frustration, workarounds,
                              |    errors, delays)
                              |    --> UNDERSERVED JOB: Strong candidate
                              |        for Discovery. Proceed to
                              |        importance/satisfaction analysis.
                              |
                              +-- ADEQUATELY (job gets done, complaints
                              |    are minor, no significant consequences)
                              |    --> ADEQUATELY SERVED: See Section 6
                              |        ("No Action" outcomes).
                              |
                              +-- WELL (stakeholders are satisfied,
                                   solution works reliably)
                                   --> OVERSERVED JOB: Do not invest.
                                       The "problem" is likely a
                                       preference, not a need.
```

### Validation Evidence Table

| Evidence Type | Underserved Signal | Adequately Served Signal |
|---------------|-------------------|-------------------------|
| **Workarounds** | Users built spreadsheets, scripts, or manual processes to compensate | Users use the existing tool as intended, with minor complaints |
| **Time spent** | Disproportionate time on the job relative to its importance | Time investment is reasonable for the value delivered |
| **Error rate** | Frequent errors, rework, or reconciliation needed | Errors are rare and caught by existing checks |
| **Stakeholder language** | "This is killing us," "We spend all week on this," "I dread this every month" | "It's fine," "It works," "It could be better but it's not urgent" |
| **Escalation history** | Repeated IT tickets, leadership complaints, audit findings | Occasional requests, no pattern of escalation |
| **Switching behavior** | Users actively seeking alternatives, trialing other tools | Users are not looking for alternatives |

---

## 3. Switch Interviews and the Four Forces of Progress

### What is a Switch Interview?

A Switch Interview reconstructs the timeline of how a stakeholder moved (or attempted to move) from one way of doing a job to another. In enterprise contexts, this reveals the forces that drive and resist change.

### The Four Forces of Progress (Enterprise Adaptation)

```
            FORCES DRIVING CHANGE                FORCES RESISTING CHANGE
        (push toward new solution)            (pull back to current state)

  +----------------------------------+    +----------------------------------+
  | PUSH: Dissatisfaction with       |    | HABIT: Comfort with current      |
  | current situation                |    | process/tool                     |
  |                                  |    |                                  |
  | "Our current reporting process   |    | "Everyone knows how the current  |
  |  takes 3 people 4 days every     |    |  spreadsheet works. Switching    |
  |  month and still has errors."    |    |  means retraining 30 people."    |
  +----------------------------------+    +----------------------------------+

  +----------------------------------+    +----------------------------------+
  | PULL: Attraction of new          |    | ANXIETY: Fear of the unknown     |
  | solution/approach                |    | with a new approach              |
  |                                  |    |                                  |
  | "The new platform could cut      |    | "What if the new system breaks   |
  |  reporting to 2 hours with       |    |  during quarter close? We can't  |
  |  automated validation."          |    |  afford to miss the deadline."   |
  +----------------------------------+    +----------------------------------+

  For change to happen: PUSH + PULL must exceed HABIT + ANXIETY
```

### Enterprise-Specific Force Amplifiers

| Force | Consumer Context | Enterprise Amplifier |
|-------|-----------------|---------------------|
| **Push** | Personal frustration | Audit findings, compliance risk, executive pressure, competitive threat |
| **Pull** | Product marketing, word of mouth | Peer company case studies, vendor demos, analyst reports, internal champion advocacy |
| **Habit** | Muscle memory, learned behavior | Organizational inertia, sunk cost in current system, tribal knowledge encoded in current process, integration dependencies |
| **Anxiety** | Will I lose my data? Is this hard to learn? | Will this break existing workflows? Who owns it if it fails? Will my team lose headcount? What happens to our current vendor relationship? |

### Conducting a Switch Interview (Enterprise Adaptation)

**Interview structure** (30-45 minutes with a stakeholder who has recently changed how they do a job, or who is actively seeking to change):

1. **Timeline reconstruction** (15 min): "Walk me through how this job was being done 6 months ago, and what changed." Capture specific dates, triggers, and events.

2. **Push exploration** (5 min): "What was the moment you realized the current approach was no longer acceptable?" Look for a specific incident, not a general complaint.

3. **Pull exploration** (5 min): "What did you see or hear that made you think there was a better way?" Identify where the idea for change originated.

4. **Habit exploration** (5 min): "What made it hard to move away from the old approach?" Uncover dependencies, training costs, integration risks.

5. **Anxiety exploration** (5 min): "What worried you most about making a change?" Surface organizational risks, not just technical ones.

6. **Outcome assessment** (5 min): "Now that you've [made the change / attempted the change], how does it compare to what you expected?" Validate whether the job is better served.

### Interview Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Asking "What do you want?" | Elicits feature wish lists, not jobs | Ask "What were you trying to accomplish when you did [action]?" |
| Asking about hypothetical futures | Stakeholders cannot reliably predict their own behavior | Focus on actual past events and decisions |
| Interviewing only the requester | One person's frustration may not represent the team | Interview 3-5 people who do the same job to find patterns |
| Accepting the first answer | First answer is usually a surface symptom | Probe with "Tell me more about that" and "What happened next?" |

---

## 4. Outcome-Driven Innovation: Importance vs. Satisfaction

### The Framework

Outcome-Driven Innovation (ODI), developed by Tony Ulwick, quantifies job satisfaction to identify where investment will create the most value. For each desired outcome of a job, measure two dimensions:

- **Importance**: How critical is this outcome to getting the job done well? (1-10 scale)
- **Satisfaction**: How well does the current solution deliver this outcome? (1-10 scale)

### The Opportunity Score

```
Opportunity Score = Importance + max(Importance - Satisfaction, 0)
```

| Score Range | Interpretation | Action |
|-------------|----------------|--------|
| 15-20 | **Highly underserved**: Critical outcome, poorly delivered | Top priority for Discovery |
| 10-14 | **Underserved**: Important outcome with room for improvement | Strong candidate, validate with data |
| 6-9 | **Appropriately served**: Outcome is adequately met | Low priority unless strategic |
| 0-5 | **Overserved**: More capability than needed | Do not invest; potential to simplify |

### Enterprise Example: Quarterly Financial Close Process

| Desired Outcome | Importance (1-10) | Satisfaction (1-10) | Opportunity Score | Interpretation |
|----------------|-------------------|--------------------|--------------------|----------------|
| Reconcile intercompany transactions without manual intervention | 9 | 3 | 15 | Highly underserved |
| Identify and resolve discrepancies before controller review | 8 | 4 | 12 | Underserved |
| Generate variance explanations for material changes | 7 | 5 | 9 | Appropriately served |
| Produce formatted reports for audit committee | 6 | 7 | 6 | Appropriately served |
| Track individual task completion across the close checklist | 5 | 8 | 5 | Overserved |

**Implication**: Investment should target intercompany reconciliation automation and discrepancy detection, not report formatting or task tracking.

### How to Gather ODI Data in Enterprise Contexts

1. **Identify 8-15 desired outcomes** for the job through interviews or workshops.
2. **Survey 10-30 stakeholders** who perform the job (even small sample sizes are directionally useful in enterprise settings where the user base is limited).
3. **Calculate Opportunity Scores** and plot on an importance/satisfaction matrix.
4. **Validate outliers**: If a single outcome scores very differently from the rest, investigate whether the scoring reflects a real gap or a misunderstanding of the outcome statement.

---

## 5. Integration with Value Proposition Canvas

### Mapping JTBD to the Value Proposition Canvas

The Value Proposition Canvas (Strategyzer) has two sides: the Customer Profile and the Value Map. JTBD analysis feeds directly into the Customer Profile.

```
CUSTOMER PROFILE (from JTBD analysis)     VALUE MAP (for proposed solution)
+------------------------------------+    +------------------------------------+
|                                    |    |                                    |
|  JOBS                              |    |  PRODUCTS & SERVICES               |
|  - Functional jobs identified      |    |  - Features/capabilities that      |
|    via job statements              |    |    address the jobs                |
|  - Emotional jobs from switch      |    |                                    |
|    interviews                      |    |  GAIN CREATORS                     |
|  - Social jobs from stakeholder    |    |  - How the solution delivers       |
|    persona analysis                |    |    the gains stakeholders want     |
|                                    |    |                                    |
|  PAINS                             |    |  PAIN RELIEVERS                    |
|  - Push forces (dissatisfaction)   |    |  - How the solution eliminates     |
|  - Anxiety forces (fears)          |    |    or reduces the pains            |
|  - Underserved outcomes from ODI   |    |                                    |
|                                    |    |                                    |
|  GAINS                             |    |                                    |
|  - Pull forces (desired future)    |    |                                    |
|  - Highly important outcomes       |    |                                    |
|  - Emotional/social payoffs        |    |                                    |
+------------------------------------+    +------------------------------------+
```

### Translation Table

| JTBD Element | Maps To (Canvas) | Example |
|-------------|-------------------|---------|
| Functional job statement | Customer Job | "Reconcile intercompany transactions without manual intervention" |
| Push force from switch interview | Customer Pain | "Current process requires 3 people for 4 days with persistent errors" |
| Pull force from switch interview | Customer Gain | "Automated reconciliation with exception-only review" |
| Anxiety force | Customer Pain (adoption risk) | "Fear of system failure during quarter close" |
| Habit force | Customer Pain (switching cost) | "30 people trained on current spreadsheet process" |
| Underserved outcome (ODI score > 12) | Priority pain to relieve | "Identify discrepancies before controller review" |
| Overserved outcome (ODI score < 5) | Do not address (or simplify) | "Track individual task completion" -- already well served |

### When to Build the Canvas

Build the Value Proposition Canvas **after** completing JTBD analysis, not before. The Canvas is a synthesis artifact that organizes JTBD findings into a format that bridges Discovery and the Intelligence stage. Attempting to fill the Canvas without JTBD data leads to assumption-driven strategy.

---

## 6. When JTBD Reveals "No Action" -- The Adequately Served Job

### Why "No Action" Is a Valid Discovery Outcome

One of the most valuable things JTBD analysis can reveal is that the job is already adequately served. This means:

- Stakeholders accomplish their goals with current tools/processes.
- Frustrations exist but are minor relative to switching costs.
- Opportunity Scores for key outcomes fall in the 6-9 range.
- The Four Forces analysis shows Habit + Anxiety significantly outweigh Push + Pull.

**"No action" is not a failure of Discovery. It is a success.** It prevents the organization from investing in a solution to a problem that does not meaningfully exist.

### Decision Tree: Is "No Action" the Right Call?

```
JTBD analysis is complete. Is "no action" appropriate?
  |
  v
Are all key outcomes scoring below 10 on the Opportunity Score?
  |
  +-- NO (some outcomes score 10+) --> NOT "no action." Investigate
  |                                     underserved outcomes further.
  |
  +-- YES --> Do stakeholders describe significant workarounds?
                |
                +-- YES --> Investigate further. Workarounds indicate
                |           the job IS underserved, but stakeholders may
                |           have normalized the pain. Re-score with
                |           explicit comparison to best-practice benchmarks.
                |
                +-- NO --> Is there a strategic or compliance mandate
                           requiring change regardless of satisfaction?
                             |
                             +-- YES --> Proceed, but frame as compliance/
                             |           strategic initiative, not user need.
                             +-- NO --> "NO ACTION" IS CORRECT.
                                        Document findings and close.
```

### How to Document a "No Action" Outcome

```
## Discovery Outcome: No Action Recommended

**Job Analyzed**: [Job statement]
**Stakeholders Interviewed**: [Count and roles]
**Analysis Date**: [Date]

### Finding Summary
The job "[job statement]" is adequately served by the current
[tool/process/approach]. Key outcomes score in the appropriately
served range (Opportunity Scores 6-9). Stakeholders express minor
frustrations but no significant workarounds, errors, or delays.

### Evidence
- Average Opportunity Score across [N] outcomes: [score]
- Highest-scoring outcome: [outcome] at [score] -- below threshold
- Four Forces assessment: Habit + Anxiety significantly exceed
  Push + Pull
- No escalation history or audit findings related to this job

### What Would Change This Assessment
- [Trigger 1: e.g., "Regulatory change requiring real-time reporting"]
- [Trigger 2: e.g., "Team size doubles, making manual process unscalable"]
- [Trigger 3: e.g., "Current vendor announces end-of-life"]

### Recommendation
Close this Discovery item. Revisit if triggers above materialize.
```

### Anti-Pattern: Ignoring "No Action" Signals

Organizations frequently ignore "no action" signals because:

| Reason | Why It Happens | Consequence |
|--------|---------------|-------------|
| Sunk cost | "We already spent time analyzing this" | Investment in a solution nobody needs |
| Champion bias | A senior leader already advocated for the project | Political project that drains resources from real needs |
| Vendor pressure | A vendor demo looked impressive | Shelfware -- purchased but unused software |
| Innovation theater | "We need to be seen doing something" | Deploys change for change's sake, increasing organizational fatigue |

**Agent guidance**: When evidence points to "no action," explicitly state this finding. Do not soften it into "low priority" or "future consideration" unless there are genuine triggers that would change the assessment.

---

## 7. JTBD Interview Question Bank

### For Identifying the Job

- "When you do [task], what are you ultimately trying to achieve?"
- "If [task] were magically done perfectly, what would be different about your work?"
- "Walk me through the last time you did [task]. What triggered it? What did you do first?"
- "What does 'done well' look like for this? How do you know when it's been done successfully?"

### For Uncovering Emotional and Social Jobs

- "How do you feel when this goes wrong? What is the worst-case scenario?"
- "Who else is affected when this job is not done well? What do they say?"
- "When this goes smoothly, what does that mean for you personally?"
- "Is there pressure from leadership or peers around how this gets done?"

### For Assessing Current Satisfaction

- "On a scale of 1-10, how well does your current approach serve this need?"
- "What workarounds have you built to compensate for gaps in the current approach?"
- "If you could change one thing about how this gets done today, what would it be?"
- "How much time do you spend on this relative to how much time you think is reasonable?"

### For Four Forces Exploration

- "What would have to get worse before you would seriously consider changing your approach?" (Push threshold)
- "What would a new approach need to offer for you to seriously consider switching?" (Pull threshold)
- "What would you lose by changing how you do this today?" (Habit)
- "What risks worry you most about changing this process?" (Anxiety)

---

## 8. JTBD Output Format for DISCO Pipeline

When completing JTBD analysis during Discovery, structure the output as:

```
## JTBD Analysis Summary

**Job Statement**: [Precise job statement using verb + object + context]
**Job Dimensions**:
  - Functional: [Description]
  - Emotional: [Description]
  - Social: [Description]

**Stakeholders Interviewed**: [Count, roles]

### Current State Assessment

**How the job is done today**: [Description of current approach]
**Satisfaction level**: [Underserved / Appropriately Served / Overserved]
**Key evidence**: [Workarounds, time spent, error rates, stakeholder quotes]

### Four Forces Assessment

| Force | Strength (1-10) | Key Evidence |
|-------|-----------------|--------------|
| Push (dissatisfaction) | [score] | [evidence] |
| Pull (attraction of new) | [score] | [evidence] |
| Habit (inertia) | [score] | [evidence] |
| Anxiety (fear of change) | [score] | [evidence] |

**Net assessment**: [Push + Pull] vs [Habit + Anxiety] = [Favorable / Unfavorable / Marginal]

### Outcome Priorities (ODI)

| Desired Outcome | Importance | Satisfaction | Opportunity Score |
|----------------|------------|--------------|-------------------|
| [Outcome 1] | [1-10] | [1-10] | [calculated] |
| [Outcome 2] | [1-10] | [1-10] | [calculated] |

### Recommendation

[One of: Proceed to Intelligence stage / No Action / Defer pending triggers]

**If No Action**: [Document triggers that would change this assessment]
**If Proceed**: [Key underserved outcomes to focus on in Intelligence stage]
```

---

## 9. Common Enterprise JTBD Scenarios

### Scenario: "We Need a New Dashboard"

**Surface request**: Build a new executive dashboard.
**JTBD reframe**: The job is "Identify emerging risks in department-level KPIs before they require executive escalation." The dashboard is one possible solution. Others include automated alerting, weekly briefing docs, or delegated monitoring.

**Discovery approach**: Interview 3-5 executives and their chiefs of staff. Ask what they do when they open the current dashboard. Often the real job is "Prepare for the weekly leadership meeting with data that demonstrates my department is on track" (functional + social).

### Scenario: "Our Data Quality Is Bad"

**Surface request**: Implement a data quality tool.
**JTBD reframe**: The job is "Trust that the data in [system] is accurate enough to make [specific decision] without manual verification." Data quality is a means, not an end.

**Discovery approach**: Identify the 3-5 decisions that depend on the data. For each, assess: Does data quality actually prevent the decision, or is it invoked as a reason to delay decisions people are uncomfortable making? (This is where emotional jobs surface.)

### Scenario: "We Need to Adopt AI"

**Surface request**: Launch an AI initiative.
**JTBD reframe**: There is no single job here. "Adopt AI" is a technology push, not a job pull. The correct approach is to identify specific jobs across the organization where AI could improve outcomes, then run JTBD analysis on each.

**Discovery approach**: Resist the urge to find jobs for the technology. Instead, identify the organization's top 5-10 most underserved jobs (via ODI scoring) and then assess which, if any, benefit from AI capabilities. Many will not. This is the correct finding.
