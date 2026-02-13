# Root Cause Analysis: Five Whys, Fishbone, and Fault Tree for Enterprise Discovery

## Purpose

This document is an agent-consumable reference for conducting root cause analysis (RCA) during the Discovery stage of the DISCO pipeline. It covers three primary techniques -- Five Whys, Fishbone (Ishikawa), and Fault Tree Analysis -- adapted for enterprise technology, knowledge work, and business strategy contexts. Manufacturing examples are excluded; all examples target IT, data, process, and organizational problems.

---

## 1. Technique Selection Decision Tree

Use this decision tree to select the appropriate RCA method based on problem characteristics.

```
START: A problem statement has been identified during Discovery.
  |
  v
Is the problem clearly scoped to a single failure chain?
  |
  +-- YES --> Is the problem novel (first occurrence, no prior analysis)?
  |             |
  |             +-- YES --> Use FIVE WHYS (rapid, single-thread first pass)
  |             +-- NO  --> Has prior Five Whys analysis stalled or looped?
  |                           |
  |                           +-- YES --> Escalate to FISHBONE DIAGRAM
  |                           +-- NO  --> Repeat Five Whys with fresh framing
  |
  +-- NO  --> Are there multiple independent contributing factors?
                |
                +-- YES --> Is the system safety-critical or high-stakes?
                |             |
                |             +-- YES --> Use FAULT TREE ANALYSIS
                |             +-- NO  --> Use FISHBONE DIAGRAM
                |
                +-- NO  --> Is the problem ambiguous or poorly defined?
                              |
                              +-- YES --> Use FISHBONE to decompose first,
                              |           then Five Whys on each branch
                              +-- NO  --> Use FIVE WHYS
```

### Selection Summary Table

| Technique | Best When | Complexity | Time Investment | Output |
|-----------|-----------|------------|-----------------|--------|
| Five Whys | Single failure chain, rapid triage, clear symptom | Low | 15-30 min | Linear causal chain to root cause |
| Fishbone (Ishikawa) | Multiple potential cause categories, ambiguous problem, collaborative analysis | Medium | 1-2 hours | Categorized cause map with weighted branches |
| Fault Tree Analysis | Safety-critical systems, compliance-driven analysis, quantitative risk needed | High | 2-8 hours | Boolean logic tree with probability estimates |

---

## 2. Five Whys Methodology

### Core Process

1. State the observable problem precisely (not a guess, not a solution).
2. Ask "Why does this happen?" and write the answer.
3. For each answer, ask "Why?" again.
4. Continue until you reach an **actionable root cause** (see termination criteria below).
5. Validate the chain by reading it forward: "Because [root cause], therefore [cause N-1], therefore... [symptom]."

### Termination Criteria: The Actionable Root Cause Test

A root cause is the **deepest cause you can actually influence**. Apply these three tests:

| Test | Question | If NO, keep digging |
|------|----------|---------------------|
| **Influence Test** | Can someone in our organization change this? | The cause is external or environmental -- stop here but flag dependency. |
| **Action Test** | Can we define a concrete action to address this? | The cause is too abstract -- ask "Why?" one more time. |
| **Recurrence Test** | If we fix this, will the original problem stop recurring? | You found a contributing factor, not the root cause -- branch the analysis. |

**Critical rule**: If you reach "Why #5" and the answer is still a symptom or intermediate cause, do not stop. Five is a guideline, not a hard limit. Some enterprise problems require 7-8 levels. Others resolve at 3.

### Five Whys Pitfalls

#### Pitfall 1: Single-Thread Thinking

**What it looks like**: The analyst follows one causal path and declares it "the" root cause, ignoring parallel causes.

**Example (bad)**:
- Problem: Dashboard reports are consistently 2 days late.
- Why? The data pipeline fails on Mondays.
- Why? The source system times out.
- Why? The query is too slow.
- Why? The table lacks proper indexing.
- Why? No one owns database performance.
- Root cause declared: "No database performance owner."

**What was missed**: The pipeline also lacks retry logic, the reporting team has no SLA with the data team, and the dashboard could use cached data for non-critical metrics. Single-thread analysis found one real cause but missed three others.

**Fix**: At each "Why?" level, ask "Is there another reason this happens?" If yes, branch. Run parallel Five Whys on each branch.

#### Pitfall 2: Stopping Too Early

**What it looks like**: The analyst accepts a proximate cause as the root cause because it feels actionable.

**Example (bad)**:
- Problem: Sales team is not using the new CRM.
- Why? They say it is too slow.
- Why? The CRM loads pages in 8+ seconds.
- Root cause declared: "CRM performance is poor."

**What was missed**: Two more "Whys" would reveal: the CRM is slow because it loads 10 years of unarchived data by default (Why?), because the data retention policy was never configured during implementation (Why?), because the implementation partner was never given data governance requirements (actual root cause: procurement did not include data governance in the SOW).

**Fix**: Always apply the Recurrence Test. Ask: "If we fix CRM performance, will the sales team adopt it?" Probably not -- there are also training and workflow integration issues.

#### Pitfall 3: Accepting Symptoms as Causes

**What it looks like**: An answer to "Why?" restates the problem in different words.

**Example (bad)**:
- Problem: Employee satisfaction scores dropped 15%.
- Why? Employees are dissatisfied. (This is a restatement, not a cause.)

**Fix**: Each answer must introduce a new, falsifiable causal claim. If the answer is a synonym or restatement, reject it and rephrase the question.

### Anti-Pattern: Solution Contamination

**Definition**: Solution Contamination occurs when the analyst (consciously or unconsciously) steers the root cause analysis toward a predetermined solution. The causal chain is reverse-engineered from a desired outcome rather than discovered through honest inquiry.

**How to detect it**:

| Signal | Example | Problem |
|--------|---------|---------|
| The "root cause" is phrased as the absence of a specific solution | "Root cause: We don't have Tool X" | This is a solution masquerading as a cause. The real question is: what need is unmet? |
| Every branch of analysis converges on the same conclusion | All five branches point to "we need a new platform" | Confirmation bias. Rerun analysis with a different facilitator. |
| The root cause was known before the analysis started | Team already had budget approval for a vendor; RCA confirms it | The analysis is theater, not discovery. |
| Causes skip logical steps to reach the desired conclusion | "Reports are late" -> "We need AI-powered automation" | Missing 3-4 intermediate causes that might point elsewhere. |

**Mitigation**: Before starting Five Whys, document any pre-existing solution hypotheses. After completing the analysis, explicitly check: "Does this root cause point to the solution we already wanted? If so, have we honestly considered alternatives?" Assign a devil's advocate to argue for a different root cause.

### Multi-Branch Analysis Template

When a single "Why?" yields multiple valid answers, branch the analysis:

```
Problem: IT ticket resolution time increased 40% this quarter.
  |
  +-- Why? (Branch A): Ticket volume increased 25%.
  |     +-- Why? New software rollout generated support requests.
  |           +-- Why? Training was insufficient.
  |                 +-- Why? Training budget was cut in Q3.
  |                       +-- ROOT CAUSE A: Training investment
  |                           not tied to rollout decisions.
  |
  +-- Why? (Branch B): Average handle time increased.
  |     +-- Why? Tier 1 agents are escalating more tickets.
  |           +-- Why? Knowledge base is outdated.
  |                 +-- Why? No process for KB updates after changes.
  |                       +-- ROOT CAUSE B: Change management does
  |                           not include KB update step.
  |
  +-- Why? (Branch C): Staffing levels did not scale.
        +-- Why? Headcount request was denied.
              +-- Why? IT support is funded as fixed cost, not variable.
                    +-- ROOT CAUSE C: Funding model does not
                        account for demand variability.
```

**Prioritization**: After identifying multiple root causes, rank by (a) influence (can we change it?), (b) impact (how much of the problem does it explain?), and (c) effort (what does it cost to address?).

---

## 3. Fishbone / Ishikawa Diagram for Knowledge Work

### Adapted Categories

The traditional manufacturing categories (Man, Machine, Material, Method, Measurement, Mother Nature) do not map well to enterprise knowledge work. Use these six categories instead:

| Category | Scope | Example Causes |
|----------|-------|----------------|
| **People** | Skills, capacity, roles, incentives, communication | Lack of training, unclear ownership, misaligned incentives, key-person dependency |
| **Process** | Workflows, handoffs, approvals, sequencing | Missing approval step, serial bottleneck, no escalation path, undocumented tribal knowledge |
| **Technology** | Tools, platforms, integrations, infrastructure | System downtime, poor UX, missing integration, technical debt, inadequate monitoring |
| **Data** | Quality, availability, timeliness, governance | Stale data, duplicate records, no single source of truth, missing metadata, access restrictions |
| **Policy** | Governance, compliance, organizational rules, budgeting | Rigid procurement rules, annual-only budgeting, overly broad access controls, conflicting policies |
| **Environment** | Organizational culture, market conditions, timing, external dependencies | Reorg in progress, vendor instability, competing priorities, seasonal demand spikes |

### Fishbone Construction Process

1. Write the problem statement at the "head" of the fish.
2. Draw the six category branches.
3. For each category, brainstorm potential causes (aim for 3-5 per branch).
4. For each potential cause, ask "Why does this contribute?" to add sub-causes.
5. Mark the 2-3 most likely root causes across all branches.
6. Validate marked causes with data or stakeholder interviews.

### Enterprise Example: Failed Data Governance Initiative

**Problem**: Data governance initiative launched 6 months ago has less than 20% adoption across business units.

| Category | Causes | Sub-Causes |
|----------|--------|------------|
| **People** | Data stewards lack authority | Role is advisory, not decision-making; no executive sponsor enforcement |
| | Business users see no personal benefit | Governance adds work without visible payoff; no incentive alignment |
| **Process** | Governance workflow is too heavy | 12-step approval for any schema change; no fast-track for low-risk changes |
| | No onboarding path for new teams | Teams discover governance exists only when blocked by it |
| **Technology** | Data catalog tool is difficult to use | UI requires 15+ clicks to register a dataset; no API for automation |
| | No integration with existing workflows | Governance is a separate portal, not embedded in ETL or BI tools |
| **Data** | Metadata quality is poor in the catalog | Auto-imported metadata is incomplete; manual enrichment backlog is 6 months |
| **Policy** | Governance charter is ambiguous on scope | Unclear whether it covers analytics datasets or only production systems |
| | Non-compliance has no consequences | No enforcement mechanism; governance is purely advisory |
| **Environment** | Competing digital transformation initiative | Leadership attention and budget directed elsewhere; governance deprioritized |

**Likely root causes** (after validation): (1) Governance workflow is too heavy for low-risk changes; (2) No integration with existing tools; (3) Non-compliance has no consequences.

---

## 4. Fault Tree Analysis (FTA) for Enterprise Systems

### When to Use FTA

FTA is appropriate when:
- The problem involves a **system failure** with multiple potential paths to failure.
- **Quantitative risk assessment** is needed (probability estimates).
- The analysis must be **auditable** for compliance or executive review.
- You need to distinguish between causes that are individually sufficient (OR gates) vs. causes that must combine (AND gates).

### FTA Structure

FTA uses Boolean logic gates:
- **OR gate**: The parent event occurs if ANY child event occurs.
- **AND gate**: The parent event occurs only if ALL child events occur simultaneously.

### Enterprise Example: Customer Data Breach

```
TOP EVENT: Customer PII exposed externally
  |
  OR gate
  |
  +-- Unauthorized access to production database
  |     |
  |     OR gate
  |     +-- Compromised credentials (AND: weak password policy + no MFA)
  |     +-- Unpatched vulnerability exploited
  |     +-- Insider threat (AND: excessive permissions + no audit logging)
  |
  +-- Data exfiltrated via application layer
  |     |
  |     OR gate
  |     +-- SQL injection in customer-facing app
  |     +-- API endpoint returns excessive data (AND: no field-level auth + no rate limiting)
  |     +-- Third-party integration leaks data (AND: vendor has broad access + no DLP controls)
  |
  +-- Accidental exposure
        |
        OR gate
        +-- PII included in analytics export (AND: no data masking + export to shared drive)
        +-- Backup stored in unencrypted bucket
        +-- Error message reveals PII in logs
```

### FTA vs. Fishbone Decision

| Factor | Use Fishbone | Use FTA |
|--------|-------------|---------|
| Problem type | Process inefficiency, adoption failure, strategic misalignment | System failure, security incident, compliance violation |
| Analysis goal | Identify categories of causes for brainstorming | Map precise failure paths with logic gates |
| Audience | Cross-functional team workshop | Security review, audit committee, risk assessment |
| Quantitative needs | Not required | Probability estimates expected |

---

## 5. Combining Techniques in DISCO Discovery

The Discovery stage often benefits from using techniques in sequence:

1. **Start with Five Whys** on the initial problem statement to establish a preliminary causal hypothesis (15-30 minutes).
2. **If Five Whys reveals multiple branches or ambiguity**, switch to Fishbone to map the full cause landscape across all six categories (1-2 hours).
3. **If Fishbone reveals a system-critical or compliance-sensitive root cause**, escalate to FTA for that specific branch to build a defensible, auditable analysis.
4. **Document the root causes** with the Actionable Root Cause Test (Influence, Action, Recurrence) before advancing to the Intelligence stage.

### Output Format for DISCO Pipeline

When completing root cause analysis during Discovery, structure the output as:

```
## Root Cause Analysis Summary

**Problem Statement**: [Precise, observable problem]
**Method Used**: [Five Whys / Fishbone / FTA / Combined]
**Analysis Date**: [Date]

### Root Causes Identified (ranked by impact)

1. **[Root Cause 1]**: [Description]
   - Influence: [High/Medium/Low -- can we change this?]
   - Impact: [Estimated % of problem explained]
   - Evidence: [What data supports this?]

2. **[Root Cause 2]**: [Description]
   - Influence: [High/Medium/Low]
   - Impact: [Estimated %]
   - Evidence: [Data or stakeholder input]

### Causes Investigated but Ruled Out
- [Cause]: [Why ruled out]

### Solution Contamination Check
- Pre-existing solution hypotheses: [List any]
- Does the analysis confirm a pre-existing hypothesis? [Yes/No]
- If yes, what alternative explanations were tested? [List]

### Recommended Next Steps
- [Action items for Intelligence stage]
```

---

## 6. Common Enterprise RCA Scenarios

### Scenario: Low Adoption of Internal Tool

**Recommended approach**: Five Whys first (targeting "why don't users use it?"), then Fishbone across People/Process/Technology if Five Whys reveals multiple threads. Watch for Solution Contamination -- the team that built the tool will steer toward "users need more training" rather than "the tool doesn't solve the right problem."

### Scenario: Data Quality Degradation

**Recommended approach**: Fishbone first (Data, Process, Technology, and People categories are all likely contributors). Then Five Whys on the top 2-3 branches. Root causes in data quality problems are almost always in Process and Policy, not Technology.

### Scenario: Project Delivery Delays

**Recommended approach**: Five Whys with mandatory multi-branch analysis. The most common pitfall is stopping at "not enough resources" -- push past this to find why resources were misallocated, why scope expanded, or why dependencies were not identified early.

### Scenario: Security or Compliance Incident

**Recommended approach**: FTA for the incident itself (precise failure path mapping). Then Fishbone for the systemic conditions that allowed the incident (why controls were missing, why monitoring gaps existed). FTA output goes to the security/compliance team; Fishbone output goes to the executive sponsor for systemic remediation.

---

## 7. Validation Checklist

Before concluding any root cause analysis, verify:

- [ ] The root cause is a cause, not a restatement of the symptom.
- [ ] The root cause is not a solution in disguise ("we lack Tool X" is a solution, not a cause).
- [ ] The forward-reading test passes: "Because [root cause], therefore... [symptom]."
- [ ] The Recurrence Test passes: fixing this cause would prevent recurrence.
- [ ] Multiple branches were explored (not just the first thread).
- [ ] Solution Contamination check was performed.
- [ ] The root cause is at the deepest level the organization can influence.
- [ ] Evidence (data, stakeholder input, or system logs) supports the conclusion.
