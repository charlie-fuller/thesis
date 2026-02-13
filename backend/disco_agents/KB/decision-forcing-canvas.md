# Decision-Forcing Canvas for Enterprise AI Initiatives

*Reference document for DISCO agents evaluating whether AI or technology initiatives should proceed. Based on the Decision-Forcing AI Business Case Canvas methodology.*

---

## Purpose

This document provides a structured decision-forcing framework that DISCO agents should apply when evaluating AI and technology initiatives. The framework forces clarity before commitment -- ensuring that critical questions about ownership, permissions, failure modes, and kill conditions are answered before building begins.

**Core principle: "This defines what must be true before building is responsible. Discomfort here is information."**

Most organizations fail at AI not because they lack ambition or intelligence, but because they commit too early -- before ownership, controls, and consequences are clear. This framework slows that moment down.

---

## 1. The Decision-Forcing Philosophy

### Why Decision-Forcing Matters

The same pattern repeats across executive rooms, boards, and operating teams: pressure to "do something with AI" arrives before clarity on:

- What work is actually changing
- Who owns the outcomes and the risks
- Where autonomy must stop
- How failure would be detected and contained

Once delivery begins, these questions become politically difficult to ask. The DISCO pipeline must force these questions **before** that point.

### The Language Rule

**Forbid vague aspirational language in problem and solution framing.**

Banned terms in initiative descriptions:
- "assist" / "support" / "enhance" / "improve" / "optimize" / "leverage"
- "AI-powered" / "intelligent" / "smart" (without concrete specification)

Replace with concrete state-change language:
- BAD: "AI will assist sales teams with proposal writing"
- GOOD: "Proposal first drafts will be generated from CRM opportunity data, reducing time-to-proposal from 5 days to 4 hours"

**Agent guidance**: When analyzing initiative descriptions, flag vague language and request concrete state-change descriptions. If the requester cannot articulate what specifically changes, the initiative is not ready for evaluation.

---

## 2. The 13-Section Canvas Framework

Each section below is a forcing function. If any section cannot be answered honestly, the initiative should pause.

### Section 1: Job to Be Done (State Change)

**Core questions:**
- What job changes hands, end-to-end?
- What is different if this works?

This section demands a concrete state-change description, not aspirational outcomes. The "job" is not "help people" or "improve efficiency" -- it is a specific workflow outcome that is measurably different.

**Agent application**: During Discovery triage, extract the state change. If the problem statement describes a desire ("we want AI to help with X") rather than a state change ("X currently takes Y hours and produces Z errors"), flag this as insufficient framing.

### Section 2: Current Friction

**Core questions:**
- Where do time, cost, error, or risk accumulate today?
- Why intervene now?

This maps to the DISCO triage criteria "Problem is real" and "Problem is costly." The Canvas adds urgency framing: why now, specifically?

**Agent application**: During Discovery, quantify friction across four dimensions:

| Friction Type | Measurement | Example |
|--------------|-------------|---------|
| **Time** | Hours/week wasted | 20 hrs/week on manual data reconciliation |
| **Cost** | Direct financial loss | $50K/year in duplicate vendor payments |
| **Error** | Error rate and impact | 15% of reports contain stale data |
| **Risk** | Exposure if unchecked | Compliance gap growing with each new regulation |

### Section 3: Workflow Delta

**Core questions:**
- What changes in the workflow?
- Which steps move, disappear, or become autonomous?

This is one of the most powerful Canvas concepts. Do not describe what the AI "does" -- describe what changes in the human workflow.

**Agent application**: For BUILD/BUY recommendations, require a Workflow Delta table:

| Step | Current State | Proposed State | Change Type |
|------|--------------|----------------|-------------|
| [Step 1] | [How it works now] | [How it works after] | Eliminated / Automated / Assisted / Unchanged |

Every "Automated" step must specify: what triggers it, what it produces, and what human review (if any) occurs before the output is used.

### Section 4: Value Hypothesis (Falsifiable)

**Core questions:**
- How would value show up? (time, errors, cycle time, risk, revenue)
- When should it appear?
- **How would you know it isn't working?**

The third question is the forcing function. It requires defining what absence of value looks like, creating a falsifiable hypothesis rather than unfalsifiable aspiration.

**Agent application**: Every PRD and Assessment must include:
```
VALUE HYPOTHESIS: [Specific measurable claim]
TIMELINE: [When value should be visible]
FALSIFICATION CRITERIA: [What would prove this isn't working]
MEASUREMENT METHOD: [How to measure]
```

### Section 5: Boundary and Scope

**Core questions:**
- What is in scope?
- What is explicitly out of scope?
- Where does this intervention stop?

This maps to the existing PRD "Out of Scope" section but adds the critical "where does this intervention stop?" question -- preventing scope creep at the design phase.

### Section 6: Owner and Accountability

**Core questions:**
- Who is the single accountable human owner?
- What outcomes do they own?
- What harms do they own?
- What is their authority to stop the initiative?

**Agent application**: This reinforces the DISCO "Real Names Requirement." A named human must own both the upside and the downside. If no single owner can be identified, the initiative is not ready to proceed.

### Section 7: Corridors (Permissions and Constraints)

**Core questions:**
- What can the system do without asking?
- What requires human approval?
- What is forbidden?

The "corridors" metaphor defines the lanes within which an AI system operates. This is critical for any BUILD recommendation involving AI agents or automation.

**Agent application**: For AI/agentic initiatives, include a Corridors table in the PRD:

| Action Category | Autonomous | Requires Approval | Forbidden |
|----------------|-----------|-------------------|-----------|
| Data read | [Scope] | [Scope] | [Scope] |
| Data write | [Scope] | [Scope] | [Scope] |
| External communication | [Scope] | [Scope] | [Scope] |
| Financial transactions | [Scope] | [Scope] | [Scope] |

**Key principle**: Permission scopes must be readable by non-engineers. "An agent without a control plane is not 'going rogue.' It is a high-speed intern with a master key and no manager."

### Section 8: Failure Modes and Blast Radius

**Core questions:**
- How could this fail?
- What is the blast radius?

Structure failure analysis across four dimensions:

| Dimension | Failure Mode | Blast Radius | Reversible? |
|-----------|-------------|-------------|-------------|
| **Operational** | [What breaks] | [How widely] | [Yes/No] |
| **Reputational** | [What looks bad] | [Who sees it] | [Yes/No] |
| **Financial** | [What costs money] | [How much] | [Yes/No] |
| **Regulatory** | [What violates rules] | [Consequences] | [Yes/No] |

**Agent application**: Most agent/AI failures are boundary failures, not model failures -- mis-scoped connectors, skipped approval steps, unintended data access. Focus failure analysis on boundaries, not capabilities.

### Section 9: Receipts (Evidence and Traceability)

**Core questions:**
- What must be logged? (inputs, outputs, actions, overrides)
- What evidence would be needed after an incident?

The standard: "An audit trail that can survive a lawyer, a regulator, and a board pack without collapsing into hand-waving."

**Agent application**: For AI initiatives, specify logging requirements:

| Log Category | What to Capture | Retention | Access |
|-------------|----------------|-----------|--------|
| Inputs | [Data sources, prompts, context] | [Duration] | [Who can access] |
| Outputs | [Responses, actions taken] | [Duration] | [Who can access] |
| Decisions | [Approvals, overrides, escalations] | [Duration] | [Who can access] |
| Errors | [Failures, fallbacks, exceptions] | [Duration] | [Who can access] |

### Section 10: Controls and Monitoring

**Core elements:**
- Performance evaluation criteria (how to know it's working)
- Drift detection mechanisms (how to know it's degrading)
- Review frequency (how often to formally evaluate)

**Agent application**: Beyond success metrics, define drift indicators -- signals that the system is moving away from expected behavior:

| Indicator | Expected Range | Drift Signal | Response |
|-----------|---------------|-------------|----------|
| [Metric] | [Normal range] | [What triggers concern] | [What to do] |

### Section 11: Kill Switch and Escalation

**Core questions:**
- What triggers shutdown?
- Who is authorized to shut it down?
- How fast can it be shut down?

**Agent application**: For AI initiatives, the Kill Switch section must specify:

```
SHUTDOWN TRIGGERS:
- [Condition 1]: [Specific threshold or event]
- [Condition 2]: [Specific threshold or event]

AUTHORIZED TO KILL: [Named person(s)]
SHUTDOWN SPEED: [Immediate / hours / days]
MECHANISM: [How shutdown works technically]
POST-MORTEM: [How to understand what happened]
```

Organizations need "a simple, fast way to revoke access instantly" -- not a process that requires code redeployment.

### Section 12: Go / No-Go Decision

**Decision options:**
- **Go**: Proceed to implementation
- **No-go**: Do not proceed (with documented rationale)
- **Go with conditions**: Proceed only if specified conditions are met

The "Go with conditions" option is critical -- it prevents both premature commitment and unnecessary paralysis. Conditions must be specific and time-bounded.

**Agent application**: The DISCO pipeline triage already has GO/NO-GO/INVESTIGATE. The Canvas adds "GO WITH CONDITIONS" as a valid outcome, where conditions are explicit prerequisites that must be satisfied before the initiative proceeds past a specified gate.

### Section 13: Immediate Next Step

**Core question:**
- What is the smallest responsible next step?

This constrains post-decision action to the minimum viable next move, preventing the common pattern where a "go" decision immediately triggers large-scale delivery planning.

**Agent application**: Every DISCO output should end with the "smallest responsible next step" -- not a project plan, but the single next action that moves this forward responsibly.

---

## 3. When to Apply the Canvas

### Full Canvas Application

Apply the complete 13-section framework when:
- The initiative involves AI/ML/agentic systems
- The initiative involves significant automation of human workflows
- The initiative is Type 1 (irreversible) per decision science frameworks
- The initiative affects external-facing systems (customer, partner, regulatory)
- The estimated investment exceeds $50K or 3+ months of effort

### Lightweight Application

Apply Sections 1 (State Change), 4 (Value Hypothesis), 6 (Accountability), and 12 (Go/No-Go) for:
- Internal tool improvements
- Process changes
- Non-AI technology decisions
- Lower-investment initiatives

### Skip Application

The Canvas is not needed for:
- Bug fixes and maintenance
- Configuration changes
- Documentation updates
- Training initiatives (use Assessment output type instead)

---

## 4. Integration with DISCO Pipeline Stages

### Discovery Stage (Discovery Guide)

- **Triage**: Apply language rule (no assist/support/enhance). Extract state change from problem framing. Assess whether the Canvas is needed for this initiative.
- **Planning**: Design discovery sessions that will gather Canvas inputs (friction quantification, workflow mapping, stakeholder accountability).
- **Coverage**: Verify Canvas-critical information is captured before proceeding.

### Intelligence Stage (Insight Analyst)

- Include Workflow Delta analysis in the Decision Document
- Assess whether evidence supports the stated value hypothesis
- Flag boundary/permission concerns early

### Synthesis Stage (Initiative Builder)

- Ensure each bundle has a clear state-change description
- For AI/agentic bundles, flag Canvas requirement in bundle metadata
- Apply falsifiable value hypothesis to each bundle's scoring rationale

### Convergence Stage (Output Generators)

- **PRD Generator**: Include Corridors, Receipts, Kill Switch sections for AI initiatives
- **Assessment Generator**: Use Go/No-Go with Conditions framing
- **All generators**: End with "smallest responsible next step"

---

## 5. Anti-Patterns the Canvas Prevents

| Anti-Pattern | How the Canvas Prevents It |
|-------------|---------------------------|
| **Aspiration theater** ("we'll use AI to improve everything") | Section 1 forces concrete state change |
| **Accountability diffusion** ("the team will own it") | Section 6 demands a single named human |
| **Permission sprawl** ("give the agent full access to test") | Section 7 forces explicit corridors |
| **Optimism bias** ("it will definitely work") | Section 4 requires falsification criteria |
| **Scope creep** ("while we're at it...") | Section 5 defines hard boundaries |
| **Failure blindness** ("what could go wrong?") | Section 8 structures failure across 4 dimensions |
| **Invisible operation** ("trust the AI") | Section 9 requires complete audit trails |
| **No exit plan** ("we're committed now") | Section 11 defines kill switch upfront |
| **Big bang launches** ("let's go all in") | Section 13 forces smallest responsible next step |

---

## 6. Quick Reference: Canvas Questions by DISCO Stage

### For Discovery Guide (Triage)
1. What job changes hands? (State Change)
2. Where does friction accumulate? (Current Friction)
3. Why now? (Urgency)
4. Who is the single accountable owner? (Accountability)

### For Insight Analyst
5. What changes in the workflow? (Workflow Delta)
6. How would value show up? How would you know it isn't? (Value Hypothesis)
7. What is in/out of scope? (Boundary)

### For Initiative Builder
8. What can the system do autonomously? What requires approval? What is forbidden? (Corridors)
9. How could this fail across operational/reputational/financial/regulatory? (Failure Modes)

### For Requirements Generator / Assessment Generator
10. What must be logged for audit? (Receipts)
11. How to detect drift? (Controls)
12. What triggers shutdown? Who can kill it? How fast? (Kill Switch)
13. Go / No-Go / Go with conditions? (Decision)
14. What is the smallest responsible next step? (Next Step)

---

*This framework is adapted from Stuart Winter-Tear's Decision-Forcing AI Business Case Canvas (Unhyped AI, 2026). The Canvas defines what must be true before building is responsible -- and recognizes that discomfort in answering these questions is valuable information, not resistance to overcome.*
