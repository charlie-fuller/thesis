# Evidence Evaluation Framework for Enterprise Discovery

*Reference document for Insight Analyst agents conducting enterprise product discovery analysis.*

---

## Purpose

This framework provides structured methods for evaluating evidence quality, calibrating confidence, and determining decision-relevance during DISCO Insight analysis. It prevents two failure modes: (1) treating weak evidence as strong, leading to overconfident recommendations, and (2) treating strong evidence as weak, leading to analysis paralysis.

---

## 1. Evidence Quality Hierarchy

Not all evidence carries equal weight. When multiple sources conflict, defer to the higher tier unless there is specific reason to doubt its applicability.

| Tier | Evidence Type | Description | Confidence Modifier |
|------|--------------|-------------|-------------------|
| **T1** | Direct Observation | Analyst or stakeholder directly witnessed the behavior, process, or outcome in situ | +0.3 |
| **T2** | Quantitative Data | System logs, usage metrics, financial records, survey results with N>30 | +0.2 |
| **T3** | Direct Quotes | Verbatim statements from involved stakeholders with context preserved | +0.1 |
| **T4** | Summarized Reports | Meeting notes, executive summaries, third-party analyst reports | +0.0 (baseline) |
| **T5** | Expert Opinions | Industry analyst perspectives, consultant recommendations without supporting data | -0.1 |
| **T6** | Assumptions | Inferred from adjacent context, analogies, or "common sense" | -0.2 |

### Application Rules

- **T1-T2 evidence can stand alone** to support a finding.
- **T3 evidence requires corroboration** from at least one other T3+ source or two T4+ sources.
- **T4-T5 evidence requires a pattern** across 3+ independent sources to anchor a recommendation.
- **T6 evidence must be explicitly labeled** as assumption and flagged for validation. Never build a recommendation solely on T6 evidence.

### Tier Escalation

When lower-tier evidence is all that is available, explicitly note:
```
EVIDENCE GAP: Finding X is supported by [T5/T6] evidence only.
Recommended validation: [specific action to obtain T1-T3 evidence]
```

---

## 2. Source Credibility Assessment

Evaluate every source against three dimensions. Score each 1-5, then calculate a composite credibility score.

### Scoring Rubric

| Dimension | 1 (Low) | 3 (Medium) | 5 (High) |
|-----------|---------|------------|----------|
| **Expertise** | No direct experience with the domain; speaking from general knowledge | Some experience; involved peripherally or in adjacent areas | Deep practitioner; directly responsible for the area under discussion |
| **Bias Risk** | Strong incentive to present a particular narrative (vendor, budget holder, champion of competing solution) | Some positional interest but multiple motivations at play | No obvious stake in the outcome; or actively argues against their own interest |
| **Corroboration** | Sole source; no other evidence supports the claim | Partially supported by 1-2 other sources | Independently confirmed by 3+ sources or verifiable data |

### Composite Credibility Score

```
Credibility = (Expertise + Bias_Inverted + Corroboration) / 15

Where Bias_Inverted = 6 - Bias_Risk_Score
(A high bias risk REDUCES credibility)
```

| Composite Score | Credibility Rating | Handling |
|----------------|-------------------|----------|
| 0.80 - 1.00 | HIGH | Can anchor recommendations directly |
| 0.53 - 0.79 | MEDIUM | Include in analysis with noted caveats |
| 0.20 - 0.52 | LOW | Flag for validation; do not use as sole basis for findings |

### Example Assessment

| Source | Expertise | Bias Risk | Corroboration | Composite | Rating |
|--------|-----------|-----------|---------------|-----------|--------|
| Head of Engineering (on tech debt) | 5 | 2 (owns the backlog) | 4 | (5 + 4 + 4) / 15 = 0.87 | HIGH |
| Vendor sales rep (on product fit) | 4 | 5 (strong sales incentive) | 2 | (4 + 1 + 2) / 15 = 0.47 | LOW |
| End user (on daily workflow pain) | 5 | 1 (no agenda) | 3 | (5 + 5 + 3) / 15 = 0.87 | HIGH |
| External consultant report | 3 | 3 (paid engagement) | 3 | (3 + 3 + 3) / 15 = 0.60 | MEDIUM |

---

## 3. Practical Bayesian Confidence Calibration

This is not a mathematical exercise. It is a disciplined method for updating beliefs as new evidence arrives during discovery.

### The Update Protocol

**Step 1: State your Prior**
Before examining new evidence, articulate your current belief and its basis.
```
PRIOR: "I believe [claim] is [likely/unlikely] because [basis]."
Confidence: [HIGH/MEDIUM/LOW]
```

**Step 2: Evaluate the New Evidence**
Ask three questions:
1. **Diagnosticity**: If the claim is true, how likely would I see this evidence? If false, how likely?
   - If the evidence is equally likely under both scenarios, it is non-diagnostic -- it should not change your belief.
   - If the evidence is much more likely under one scenario, it is highly diagnostic -- update accordingly.
2. **Independence**: Is this evidence truly new, or is it derived from the same source as evidence I already have?
   - Dependent evidence (e.g., two reports based on the same survey) counts as one piece, not two.
3. **Quality Tier**: Where does this evidence sit in the hierarchy (Section 1)?

**Step 3: Update and Document**
```
UPDATED BELIEF: "[claim] is now [more/less] likely."
Evidence that caused update: [description]
Direction: [strengthened/weakened/unchanged]
New Confidence: [HIGH/MEDIUM/LOW]
Remaining uncertainty: [what would further change my mind]
```

### Common Update Patterns

| Scenario | Update Direction | Example |
|----------|-----------------|---------|
| Strong evidence confirms prior | Strengthen moderately (not to certainty) | You believed adoption was low; usage metrics confirm 12% adoption |
| Weak evidence confirms prior | Minimal update | A single anecdote matches your hypothesis |
| Strong evidence contradicts prior | Significant update toward new position | You believed the tool was unused; logs show 200 daily active users |
| Weak evidence contradicts prior | Small update; flag for investigation | One stakeholder disputes your finding but provides no data |
| Evidence is ambiguous | No update; note the ambiguity | Survey results split 50/50 |

### Over-Confidence and Under-Confidence Patterns

**Signs of Over-Confidence (calibrate downward):**
- Relying on a single strong source without seeking disconfirmation
- Treating T4-T6 evidence as if it were T1-T2
- Using phrases like "clearly," "obviously," or "without question" in analysis
- Not identifying any remaining uncertainties
- Every finding is HIGH confidence

**Signs of Under-Confidence (calibrate upward):**
- Refusing to state a position despite consistent T1-T3 evidence from multiple sources
- Adding excessive caveats to well-supported findings
- Treating every stakeholder disagreement as equal regardless of credibility
- Every finding is LOW confidence
- Requesting more data when the existing evidence already converges

---

## 4. Correlation vs. Causation in Qualitative Discovery

Enterprise discovery frequently surfaces apparent relationships. Use this decision tree to classify them.

### Classification Decision Tree

```
Observed pattern: "When X happens, Y also happens"

Step 1: TEMPORAL ORDER
  Does X reliably precede Y?
  - No  --> Possible correlation only. Label: ASSOCIATION
  - Yes --> Continue to Step 2

Step 2: MECHANISM
  Can you articulate a plausible causal chain from X to Y?
  - No  --> Likely spurious or mediated by hidden factor. Label: CORRELATION
  - Yes --> Continue to Step 3

Step 3: ALTERNATIVE EXPLANATIONS
  Could a third factor Z cause both X and Y?
  - Yes, and Z is more parsimonious --> Label: CONFOUNDED. Investigate Z.
  - No, or Z is less plausible      --> Continue to Step 4

Step 4: CONSISTENCY
  Does the X-->Y relationship hold across multiple contexts/teams/time periods?
  - No  --> Label: CONTEXT-DEPENDENT RELATIONSHIP
  - Yes --> Label: PROBABLE CAUSAL RELATIONSHIP
```

### Common Confounders in Enterprise Discovery

| Observed Correlation | Likely Confounder | Test |
|---------------------|-------------------|------|
| Teams with more tools have lower productivity | Team dysfunction causes both tool sprawl and low productivity | Compare productivity in teams given identical toolsets |
| Departments that adopted GenAI have higher satisfaction | Early adopters are already higher-performing departments | Check pre-adoption satisfaction scores |
| Projects with more stakeholder meetings succeed more | Larger/better-funded projects get both more meetings and more resources | Control for budget and team size |
| Teams that document decisions deliver faster | Disciplined teams do both; documentation does not cause speed | Look for cases where documentation was mandated |

### Reporting Language

| Classification | Appropriate Language |
|---------------|---------------------|
| PROBABLE CAUSAL | "X drives Y" / "X causes Y" / "Addressing X will improve Y" |
| CORRELATION | "X is associated with Y" / "X and Y co-occur" |
| CONFOUNDED | "X and Y both appear driven by Z" |
| CONTEXT-DEPENDENT | "In [context], X relates to Y, but not in [other context]" |
| ASSOCIATION | "X and Y were observed together; relationship unclear" |

---

## 5. Decision-Relevance Filter

Not every finding belongs in a recommendation. Apply this filter to each insight before including it.

### The Decision-Relevance Test

For each finding, answer:

```
1. ACTIONABILITY: Does this finding suggest a specific action?
   - Yes --> Continue
   - No  --> Classify as "Context" (include in background, not recommendations)

2. DIFFERENTIATION: Would the recommendation change if this finding were different?
   - Yes --> Decision-relevant. Include with prominence.
   - No  --> Supporting context only. Summarize briefly.

3. STAKEHOLDER IMPACT: Does at least one decision-maker need to know this?
   - Yes --> Include and tag the relevant stakeholder(s)
   - No  --> Archive for reference. Do not surface in primary analysis.

4. TIMELINESS: Is there a window for action?
   - Urgent (days/weeks)  --> Flag as time-sensitive
   - Standard (months)    --> Include in normal analysis
   - Historical           --> Context only unless pattern is recurring
```

### Relevance Classification

| Classification | Criteria | Placement |
|---------------|----------|-----------|
| **PRIMARY** | Passes all 4 tests; changes the recommendation | Lead finding in analysis |
| **SUPPORTING** | Passes 2-3 tests; reinforces a primary finding | Evidence section under primary finding |
| **CONTEXTUAL** | Passes 1 test; useful background | Background/context section |
| **ARCHIVED** | Passes 0 tests | Not included; stored for future reference |

---

## 6. Handling Contradictory Evidence

When sources or data points disagree, do not ignore or average them. Follow this protocol.

### Contradiction Resolution Protocol

```
Step 1: VERIFY
  Are both pieces of evidence correctly understood?
  - Check: Could different definitions explain the disagreement?
  - Check: Are they measuring the same thing at the same time?
  - Check: Is one source outdated?

Step 2: WEIGHT
  Apply the evidence quality hierarchy and source credibility scoring.
  If one source is T1/T2 and the other is T5/T6, defer to the stronger source.
  Document: "Conflicting evidence weighted toward [source] due to [reason]."

Step 3: EXPLAIN
  If both sources are credible, determine whether the contradiction reveals:
  - Different perspectives on the same reality (e.g., leadership vs. practitioner views)
  - Different time periods (the situation may have changed)
  - Different scopes (true at team level but not org level)
  Document: "Contradiction explained by [factor]. Both are accurate within their scope."

Step 4: INVESTIGATE
  If Steps 2-3 do not resolve the contradiction:
  - Flag it explicitly in the analysis
  - Identify what additional evidence would resolve it
  - Do not force a premature resolution
  Document: "Unresolved contradiction between [A] and [B]. Resolution requires [action]."
```

### Contradiction Resolution Examples

| Source A | Source B | Resolution |
|----------|----------|------------|
| VP says adoption is 80% | Usage logs show 15% weekly active | WEIGHT: T2 data overrides T3 quote. VP likely citing "accounts provisioned," not active usage. |
| Engineering says system is stable | Support tickets show 40 incidents/month | EXPLAIN: Different definitions of "stable." Engineering means "no outages"; users experience frequent minor issues. |
| Team A says process works | Team B says process is broken | INVESTIGATE: Same process may function differently with different team sizes, workloads, or skill levels. Interview both teams with specific scenarios. |
| Consultant recommends Platform X | Internal architect recommends Platform Y | WEIGHT and EXPLAIN: Assess credibility of each. Consultant may lack internal context; architect may have familiarity bias. Recommend evaluation criteria, not a platform. |

---

## 7. Confidence Calibration Guide

### What Confidence Levels Mean

| Level | Definition | Evidence Requirements | Appropriate Wording |
|-------|-----------|----------------------|-------------------|
| **HIGH** | Finding is well-established; unlikely to change with additional evidence | 3+ independent T1-T3 sources converging; no unresolved contradictions | "Evidence strongly indicates..." / "Analysis confirms..." |
| **MEDIUM** | Finding is probable but could shift with new evidence | 1-2 T1-T3 sources, or 3+ T4 sources with consistent pattern; minor contradictions explained | "Evidence suggests..." / "Analysis indicates..." |
| **LOW** | Finding is directional but uncertain; treat as hypothesis | Limited to T4-T6 sources, or T1-T3 sources that partially conflict | "Preliminary evidence points to..." / "Initial analysis suggests, pending validation..." |

### Calibration Checks

Run these checks before finalizing any analysis:

**Distribution Check**: If more than 70% of findings are HIGH confidence, you are likely over-confident. If more than 70% are LOW confidence, you are likely under-confident. A well-calibrated analysis typically has 20-30% HIGH, 40-60% MEDIUM, and 10-30% LOW.

**Surprise Test**: For each HIGH-confidence finding, ask: "What evidence would make me change this to MEDIUM?" If you cannot imagine any such evidence, you are over-confident.

**Usefulness Test**: For each LOW-confidence finding, ask: "Is there enough here for a stakeholder to take a preliminary action?" If yes, consider upgrading to MEDIUM with explicit caveats.

### Confidence Anti-Patterns

| Anti-Pattern | Description | Correction |
|-------------|-------------|------------|
| **Confidence Anchoring** | First finding sets the tone; all subsequent findings match | Evaluate each finding independently before comparing |
| **Authority Deference** | Senior stakeholder said it, so it must be HIGH | Apply credibility rubric regardless of seniority |
| **Data Worship** | Quantitative data is always HIGH; qualitative is always LOW | T1 direct observation outranks T4 survey data with poor methodology |
| **Hedge Everything** | All findings are MEDIUM to avoid being wrong | Force-rank: at least 20% must be HIGH, at least 10% must be LOW |
| **Recency Bias** | Latest evidence overwrites everything before it | Weight by quality tier, not by when it was collected |

---

## 8. Quick Reference: Evidence Evaluation Checklist

Use this checklist for each major finding before including it in a DISCO Insight analysis.

```
[ ] Evidence tier identified (T1-T6)
[ ] Source credibility scored (Expertise, Bias, Corroboration)
[ ] If multiple sources, independence verified (not derived from same origin)
[ ] Correlation/causation classification applied
[ ] Decision-relevance filter passed (Actionable? Differentiating? Stakeholder impact? Timely?)
[ ] Contradictions addressed (Weighted, Explained, or Flagged for investigation)
[ ] Confidence level assigned (HIGH/MEDIUM/LOW) with stated basis
[ ] Confidence distribution checked across all findings
[ ] Evidence gaps explicitly noted with validation recommendations
```

---

*This framework is designed for AI agent consumption during DISCO Insight Analyst stage processing. Apply it systematically to every evidence source encountered during enterprise product discovery analysis.*
