# Decision Science Frameworks for Enterprise Technology Strategy

*Reference document for Insight Analyst agents supporting enterprise technology decisions during DISCO analysis.*

---

## Purpose

This document provides decision-making frameworks that AI agents should apply when evaluating enterprise technology strategy options. These frameworks help structure recommendations, identify decision traps, and ensure that DISCO analysis produces actionable, well-reasoned guidance rather than information overload.

---

## 1. Type 1 vs. Type 2 Decisions

Based on the Bezos framework, decisions fall into two categories that require fundamentally different approaches.

### Decision Classification

| Attribute | Type 1 (One-Way Door) | Type 2 (Two-Way Door) |
|-----------|----------------------|----------------------|
| **Reversibility** | Difficult or impossible to reverse | Easily reversible at low cost |
| **Stakes** | High -- wrong choice causes lasting damage | Moderate to low -- wrong choice wastes some time/money |
| **Decision speed** | Deliberate; invest in getting it right | Fast; cost of delay usually exceeds cost of being wrong |
| **Who decides** | Senior leadership with broad input | Closest competent person to the problem |
| **Information threshold** | 85-90% of desired information before deciding | 50-70% is sufficient |
| **Examples** | Platform migration, major vendor commitment, organizational restructuring, data architecture | Tool selection within a category, process changes, feature prioritization, pilot scope |

### Classification Decision Tree

```
Is this decision reversible within 90 days at reasonable cost?
  |
  +-- YES: Type 2. Decide quickly. Delegate to the person closest to the problem.
  |     |
  |     +-- Can the decision-maker articulate the top 2 options?
  |           +-- YES --> Decide now. Document briefly.
  |           +-- NO  --> Spend 1-2 days gathering input, then decide.
  |
  +-- NO: Type 1. Invest in the decision.
        |
        +-- Have we gathered input from all affected stakeholders?
              +-- NO  --> Conduct structured stakeholder input (max 2 weeks).
              +-- YES --> Apply decision framework (see Sections 3-5), then decide.
```

### Common Error: Treating Type 2 as Type 1

The most frequent organizational failure is applying Type 1 rigor to Type 2 decisions. Symptoms:
- 6-month evaluation for a tool that costs $500/month
- Executive committee review for a pilot that affects 5 people
- Full RFP process for a decision that can be reversed next quarter

**Agent guidance**: When analyzing an initiative, classify decisions within the initiative. If stakeholders are applying Type 1 process to Type 2 decisions, flag this as a Decision Bottleneck or Perfectionism Trap pattern (see Pattern Library).

---

## 2. Decision Velocity and the 70% Rule

### The Principle

Most decisions should be made with approximately 70% of the information you wish you had. Waiting for more information has costs:

```
Total Decision Cost = Risk of Wrong Decision + Cost of Delay

At 50% information: Risk is high, but delay cost is low  --> Usually too early
At 70% information: Risk is moderate, delay cost is moderate --> Optimal zone
At 90% information: Risk is low, but delay cost is high --> Usually too late
At 100% information: Delay cost has often exceeded the value of being right
```

### Applying the 70% Rule

**Step 1**: List the key unknowns for the decision.

**Step 2**: For each unknown, assess: "Do I know enough to make a directional judgment?"

**Step 3**: Count how many unknowns you can answer directionally vs. how many remain opaque.

**Step 4**: If 70%+ of unknowns have directional answers, proceed with the decision. Document the remaining unknowns as risks to monitor.

### When NOT to Apply the 70% Rule

- Irreversible decisions with catastrophic downside (Type 1 with existential risk)
- Regulatory or compliance decisions where "directional" is insufficient
- Decisions where the cost of gathering more information is very low relative to the decision's impact

### Agent Guidance

When producing DISCO analysis, explicitly note the information completeness level:
```
DECISION READINESS: ~[X]% of key information available.
Known: [list what we know]
Unknown: [list what we do not know]
Recommendation: [Proceed / Gather more on specific unknowns / Insufficient for decision]
```

---

## 3. Pre-Mortem Technique for Risk Identification

### The Method

Instead of asking "What could go wrong?" (which invites vague worry), the pre-mortem assumes failure has already occurred and asks "Why did it fail?"

### Pre-Mortem Protocol

```
Setup:  "It is 12 months from now. The initiative has failed completely.
         The budget was spent. The goals were not met. Stakeholders are frustrated."

Step 1: Each participant independently writes 3-5 reasons WHY it failed.
        (Not what MIGHT go wrong -- what DID go wrong in this hypothetical future.)

Step 2: Collect and categorize all failure reasons.

Step 3: For each failure reason, assess:
        - Likelihood (1-5)
        - Impact severity (1-5)
        - Detectability: Would we notice early? (1=hard to detect, 5=obvious)

Step 4: Risk Score = Likelihood x Impact x (6 - Detectability)
        Higher scores = higher priority risks.

Step 5: For top 5 risks, define:
        - Leading indicator: What early signal would tell us this is happening?
        - Mitigation: What can we do now to reduce likelihood or impact?
        - Contingency: If it happens despite mitigation, what is our response?
```

### Pre-Mortem Output Template

| Rank | Failure Reason | Likelihood | Impact | Detectability | Risk Score | Leading Indicator | Mitigation |
|------|---------------|------------|--------|---------------|------------|-------------------|------------|
| 1 | Champion left the company | 3 | 5 | 2 | 60 | Champion expressing frustration or exploring other roles | Document knowledge, formalize sponsorship, distribute ownership |
| 2 | Integration with legacy system took 3x longer than estimated | 4 | 4 | 3 | 48 | First integration task exceeds estimate by >50% | Build integration spike first, budget 3x estimate |
| 3 | Users reverted to old process | 3 | 4 | 4 | 24 | Usage metrics declining after week 4 | Mandatory cutover date, remove old process access |

### Agent Guidance

When conducting DISCO Insight analysis, apply a lightweight pre-mortem to every major recommendation. Include the top 3 risks and their leading indicators in the analysis output.

---

## 4. Options Framework: Maintaining Optionality

### The Principle

When facing uncertainty, prefer decisions that keep future options open over decisions that commit to a single path. An option has value precisely because it provides the right (but not the obligation) to take an action in the future when more information is available.

### Optionality Assessment Matrix

For each decision option, evaluate:

| Factor | High Optionality | Low Optionality |
|--------|-----------------|-----------------|
| **Vendor lock-in** | Open standards, exportable data, standard APIs | Proprietary formats, custom integrations, data trapped |
| **Contractual commitment** | Month-to-month, cancellable, modular | Multi-year, all-or-nothing, bundled |
| **Architecture coupling** | Loosely coupled, replaceable components | Tightly coupled, monolithic dependency |
| **Skill dependency** | Common skills, transferable knowledge | Rare skills, platform-specific expertise |
| **Switching cost** | Low -- can migrate in days/weeks | High -- migration requires months and significant investment |

### Decision Rules for Optionality

1. **When uncertain about the future**: Choose the option with higher optionality, even if it costs slightly more or performs slightly worse today.
2. **When the landscape is changing quickly**: Avoid long commitments. Prefer shorter contracts with renewal options over multi-year lock-ins.
3. **When building on top of a platform decision**: The platform decision constrains all subsequent decisions. Apply extra rigor to platform choices.
4. **When piloting**: Structure pilots to generate options, not commitments. A good pilot tells you whether to proceed AND gives you the ability to pivot.

### Optionality Anti-Patterns

| Anti-Pattern | Description | Correction |
|-------------|-------------|------------|
| **Option hoarding** | Keeping all options open forever, never committing | Options must be exercised or expire. Set decision deadlines. |
| **Sunk cost optionality** | "We already invested in X so we must keep using it" | Past investment does not create future option value. Evaluate options based on future costs and benefits only. |
| **False optionality** | "We can always switch later" when switching costs are actually prohibitive | Honestly assess switching costs before claiming optionality exists. |
| **Over-paying for optionality** | Accepting significantly worse current performance to maintain theoretical flexibility | If the "flexible" option costs 3x more today, the option value must be justified. |

---

## 5. Cognitive Biases in Enterprise Decisions

### Bias Reference Table

| Bias | Description | How It Manifests in Enterprise Decisions | Detection Signal | Agent Countermeasure |
|------|-------------|----------------------------------------|-----------------|---------------------|
| **Sunk Cost Fallacy** | Continuing an action because of past investment rather than future value | "We've already spent $2M on this platform, we can't switch now" | Decision rationale references past expenditure instead of future ROI | Reframe: "Ignoring what we've already spent, would we choose this option today for its future value?" |
| **Anchoring** | Over-weighting the first piece of information received | First vendor demo sets the bar; all subsequent evaluations compare to it instead of to requirements | Evaluation criteria shift after the first demo; first-seen option consistently rated highest | Establish evaluation criteria BEFORE any vendor engagement. Randomize demo order. |
| **Confirmation Bias** | Seeking evidence that supports an existing preference | Teams only gather positive references for the preferred tool; negative signals dismissed as "edge cases" | Evidence gathering is asymmetric; disconfirming evidence is not actively sought | Assign a "red team" to build the case AGAINST the preferred option. Require equal evidence gathering for all options. |
| **Status Quo Bias** | Preferring the current state over change, even when change is clearly beneficial | "Let's just keep what we have" even when current costs exceed alternative costs | Change proposals die in committee despite strong business cases; "risk" cited without quantification | Quantify the cost of inaction. Frame the status quo as an active choice with its own risks, not as the safe default. |
| **Bandwagon Effect** | Adopting something because others have | "Everyone is using GenAI, we need to as well" without clear use case | Initiative rationale cites competitor adoption, not internal need | Ask: "If no competitor were doing this, would we still do it? What specific problem does it solve for us?" |
| **Dunning-Kruger Effect** | Overestimating competence in unfamiliar domains | Business leaders making technical architecture decisions without technical input | Technical decisions made in business-only meetings; phrases like "how hard can it be?" | Ensure every decision domain has a qualified voice in the room. Flag when decisions cross competency boundaries. |
| **Availability Heuristic** | Over-weighting readily available examples | "That happened to Company X" drives disproportionate caution or enthusiasm based on one anecdote | One case study or news article drives strategy; systematic evidence is not gathered | Require N>3 examples before an anecdote influences strategy. Distinguish "this happened once" from "this happens frequently." |

### How AI Agents Can Counteract Biases

AI agents have a structural advantage in bias mitigation because they do not have personal stakes, institutional memory of sunk costs, or social pressure to conform. Agents should:

1. **Always present the cost of inaction** alongside the cost of action. Humans default to perceiving action as risky and inaction as safe. Agents should make both explicit.

2. **Actively seek disconfirming evidence**. When the analysis points in one direction, explicitly search for evidence against that direction. Report it even if the original direction holds.

3. **Reframe sunk costs**. When stakeholder input references past investment as justification, the agent should note: "Past investment is noted as context but excluded from the forward-looking recommendation per standard decision science practice."

4. **Separate popularity from suitability**. When an option is popular in the market, evaluate it on the same criteria as unpopular alternatives. Market popularity is not evidence of fit.

5. **Flag anchoring**. If the analysis is based on a single reference point (one vendor, one case study, one stakeholder's strong opinion), explicitly note: "This finding may be anchored on [source]. Recommend additional reference points before finalizing."

---

## 6. Decision Documentation Template

Every significant decision surfaced in DISCO analysis should be documented using this template. The purpose is to capture WHY, not just WHAT.

### Template

```
DECISION RECORD: [ID]
Date: [YYYY-MM-DD]
Decision: [One-sentence statement of what was decided]
Type: [Type 1 / Type 2]
Status: [Proposed / Accepted / Superseded by DR-XXX]

CONTEXT
What situation prompted this decision?
[2-3 sentences describing the problem or opportunity]

OPTIONS CONSIDERED
Option A: [Name]
  - Pros: [bullet list]
  - Cons: [bullet list]
  - Estimated cost: [time, money, effort]
  - Optionality: [HIGH/MEDIUM/LOW -- how easily can we reverse or change course?]

Option B: [Name]
  - Pros: [bullet list]
  - Cons: [bullet list]
  - Estimated cost: [time, money, effort]
  - Optionality: [HIGH/MEDIUM/LOW]

Option C: Do nothing / Status quo
  - Pros: [bullet list]
  - Cons: [bullet list]
  - Estimated ongoing cost: [what does inaction cost per month/quarter?]

DECISION
Chosen option: [A/B/C]
Rationale: [WHY this option -- not restating what it is, but why it was selected over others]
Information completeness: [~X% -- what key unknowns remain]
Deciding factor: [The single most important reason]

BIASES CHECKED
[Which biases from Section 5 were considered and how they were mitigated]

RISKS AND MONITORING
Risk 1: [Description] -- Monitor via: [Leading indicator]
Risk 2: [Description] -- Monitor via: [Leading indicator]
Reversal trigger: [What would cause us to revisit this decision?]
Review date: [When to reassess -- no longer than 6 months out]

STAKEHOLDERS
Decision maker: [Name/Role]
Consulted: [Names/Roles]
Informed: [Names/Roles]
```

### Decision Record Decision Tree

```
Is this decision worth documenting?
  |
  +-- Does it affect more than one team? --> YES --> Document
  +-- Does it involve spending >$10K? --> YES --> Document
  +-- Is it Type 1 (irreversible)? --> YES --> Document
  +-- Will someone ask "why did we do this?" in 6 months? --> YES --> Document
  +-- None of the above? --> Lightweight note is sufficient (Slack message, ticket comment)
```

---

## 7. Integrated Decision Framework for DISCO Analysis

When conducting DISCO Insight analysis that involves technology strategy recommendations, apply these frameworks in sequence:

### Step-by-Step Application

```
1. CLASSIFY the decision (Section 1)
   --> Type 1 or Type 2?
   --> This determines how much analysis is warranted.

2. ASSESS information completeness (Section 2)
   --> Are we at 70%+ for Type 2? 85%+ for Type 1?
   --> If not, identify specific gaps and recommend targeted investigation.

3. EVALUATE options for optionality (Section 4)
   --> Which options keep future doors open?
   --> Are we paying a reasonable premium for flexibility?

4. CHECK for cognitive biases (Section 5)
   --> Apply each bias check to the emerging recommendation.
   --> Assign a red-team perspective to the preferred option.

5. CONDUCT pre-mortem on the recommendation (Section 3)
   --> Assume the recommendation fails. Why?
   --> Include top 3 risks with leading indicators.

6. DOCUMENT the recommendation (Section 6)
   --> Use the decision record template.
   --> Capture WHY, not just WHAT.
   --> Include reversal triggers and review dates.
```

### Quality Checklist for Decision Recommendations

Before finalizing any DISCO analysis that includes a technology strategy recommendation, verify:

```
[ ] Decision classified as Type 1 or Type 2
[ ] Information completeness level stated explicitly
[ ] At least 2 options evaluated (including "do nothing")
[ ] Optionality assessed for each option
[ ] Cost of inaction quantified
[ ] Sunk cost references excluded from rationale
[ ] Disconfirming evidence actively sought and reported
[ ] Pre-mortem conducted with top 3 risks identified
[ ] Leading indicators defined for each risk
[ ] Bias check completed against the 7 common biases
[ ] Reversal trigger defined ("we would change course if...")
[ ] Review date set (no longer than 6 months)
[ ] Decision documented with WHY, not just WHAT
```

---

## 8. Quick Reference Tables

### Decision Speed Guide

| Information Available | Type 2 Decision | Type 1 Decision |
|----------------------|-----------------|-----------------|
| <50% | Wait -- gather more | Wait -- gather more |
| 50-70% | Decide if cost of delay is high | Continue gathering |
| 70-85% | Decide now | Decide if cost of delay is growing |
| 85-100% | You have already waited too long | Decide now |

### Bias-to-Countermeasure Quick Map

| If you suspect... | Apply this countermeasure |
|-------------------|-------------------------|
| Sunk cost fallacy | "Would we choose this today if we started fresh?" |
| Anchoring | Establish criteria before exposure to options |
| Confirmation bias | Red team the preferred option |
| Status quo bias | Quantify the cost of inaction |
| Bandwagon effect | "Would we do this if no one else was?" |
| Dunning-Kruger | Verify domain expertise of decision-makers |
| Availability heuristic | Require N>3 examples, not one anecdote |

### Optionality Quick Assessment

| Question | Yes = Higher Optionality |
|----------|------------------------|
| Can we export our data in standard formats? | Yes |
| Is the contract month-to-month or cancellable? | Yes |
| Are the required skills common in the labor market? | Yes |
| Can we swap this component without rebuilding adjacent systems? | Yes |
| Does the vendor support open standards and APIs? | Yes |

**Score**: 4-5 Yes = High optionality. 2-3 Yes = Medium. 0-1 Yes = Low (flag as risk).

---

*This framework is designed for AI agent consumption during DISCO Insight Analyst stage processing. Apply these decision science frameworks to structure technology strategy recommendations and surface decision traps that stakeholders may not recognize.*
