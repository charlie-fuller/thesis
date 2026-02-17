# Tier 2 Changelog: Agent-Specific Fixes

**Date:** 2026-02-17
**Scope:** Individual agent XML files
**Impact:** Per-agent behavioral corrections

---

## echo.xml — P3 Evidence Over Eloquence

### 1. Added distinction between brand voice emulation and factual claims
- **Before:** "Don't hedge with 'may', 'might', 'could potentially'" and "Don't be humble or understated about capabilities" applied universally
- **After:** Those rules now explicitly apply only "when emulating brand voice." Added IMPORTANT DISTINCTION block clarifying that standard epistemic honesty applies when Echo makes factual claims about analysis results or voice characteristics.
- **Why:** Echo's blanket ban on hedging directly contradicted P3. The fix preserves Echo's core function (analyzing and emulating confident brand voices) while ensuring Echo itself remains honest about its own analytical confidence.

---

## kraken.xml — P5 Humans Decide

### 2. Added per-output human review requirement
- **Before:** 7 absolute rules focused on non-destructive execution but no explicit per-output review gate
- **After:** Added rule #8: "HUMAN REVIEW PER OUTPUT — Every execution output is input to a human decision, not a final deliverable. Batch approval of evaluation is acceptable; batch approval of execution output without review is not."
- **Why:** Kraken's autonomous execution model used batch approval, which risks bypassing per-output human judgment. The fix distinguishes between approving the evaluation (acceptable) and approving execution output sight-unseen (not acceptable).

---

## project_agent.xml — P2 Problems Before Solutions

### 3. Added problem validation check before scoring
- **Before:** Score discussion guidelines jumped straight to score analysis
- **After:** Added "Problem Validation Check (Principle 2)" section requiring verification that: the problem is clearly articulated, current_state is evidence-grounded, and "do nothing" has been considered as an option.
- **Why:** Project Agent takes projects as given and scores them without checking whether the problem they solve is validated. This fix adds a structural P2 check.

---

## oracle.xml — P5 Humans Decide

### 4. Added recommendation framing as input, not decision
- **Before:** Strategic Recommendations section presented recommendations as directives ("follow up with Mike")
- **After:** Added P5 annotation: "Frame all recommendations as input to the user's decision, not as decisions themselves. 'Consider following up with Mike' not 'You should follow up with Mike.'"
- **Why:** Oracle's recommendations read as decisions. The fix preserves actionability while making the human decision point explicit.

---

## capital.xml — P3 Evidence Over Eloquence

### 5. Clarified headcount reduction framing
- **Before:** "Never frame AI as replacing people" — absolute rule
- **After:** Default framing remains "scaling without adding headcount," but added P3 exception: if evidence genuinely shows headcount reduction as primary ROI driver, say so honestly rather than reframing cost savings as "strategic reallocation."
- **Why:** An absolute ban on honest financial framing contradicts P3. The fix maintains the default but allows Capital to be truthful when the numbers are clear, letting the human decide how to position it.

---

## reporter.xml — P9 Trace the Connections

### 6. Added conditional attribution policy
- **Before:** "NEVER use agent names" — absolute ban in all contexts, removing evidence provenance
- **After:** Default remains domain labels for shareable documents. Added P9 exception: in internal meeting recaps where tracing who said what matters for follow-up, agent names are permitted when the user requests internal-format output.
- **Why:** Removing all attribution strips evidence provenance (P9 violation). The fix preserves the shareable-by-default approach while allowing evidence tracing in internal contexts.

---

## Summary

| Agent | Fix | Principle |
|-------|-----|-----------|
| Echo | Brand voice vs factual claims distinction | P3 |
| Kraken | Per-output human review requirement | P5 |
| Project Agent | Problem validation before scoring | P2 |
| Oracle | Recommendations as input, not decisions | P5 |
| Capital | Honest headcount framing when evidence supports it | P3 |
| Reporter | Conditional attribution for evidence provenance | P9 |
| **Total** | **6 edits across 6 agents** | **P2, P3, P5, P9** |
