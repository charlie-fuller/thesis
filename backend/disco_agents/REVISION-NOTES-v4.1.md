# PuRDy v4.1 Revision Notes

**Created:** 2026-01-25
**Status:** IMPLEMENTED - awaiting testing

---

## Summary

v4.1 addresses gaps identified in the v4.0 evaluation (78.5/100 score). Two agents needed iteration (Synthesizer, Insight Extractor), four agents received minor improvements.

---

## Changes by Agent

### Synthesizer (P0 - ITERATE) - Score: 12/20 -> Target: 16/20+

**Issues Addressed:**
1. Decision in first paragraph, not FIRST SENTENCE
2. Uses role titles ("Discovery Lead") not real names
3. Missing "Done When" criteria
4. 2-4x over word limit (500 -> actual 1000+)

**Changes Made:**
- Decision position: First word must be GO/NO-GO/CONDITIONAL (not just first paragraph)
- Real names: Expanded section with fallback "[Requester to identify owner]"
- Done When: Added to First Action section with examples
- Word count: Increased from 500 to 800 (realistic based on actual outputs)
- Anti-patterns: Updated to catch "Decision Needed:" prefix

### Insight Extractor (P0 - ITERATE) - Score: 12/20 -> Target: 16/20+

**Issues Addressed:**
1. Missing "Patterns Detected" section with reinforcing loop
2. Missing "Contradictions" table
3. Missing "What They Don't Realize" table
4. Incomplete Information Quality table
5. 2x over word limit

**Changes Made:**
- Patterns Detected: Added with mermaid diagram template
- Contradictions: Added table template with implication column
- What They Don't Realize: Added with surprise value identification
- Information Quality: All 4 rows required, added Gap column
- For Synthesizer: New handoff section with recommended leverage point
- Word count: Increased from 500 to 700
- Pattern Detection Guide: Added to help identify loops/contradictions
- Completeness Test: Added to self-check

### Triage (P2 - Minor)

**Changes Made:**
- Tier routing: Added explicit field on second line
- Next Agent: Added to Next Step section
- Parsing Test: Added to self-check
- Status codes clarified for downstream parsing

### Discovery Planner (P2 - Minor)

**Changes Made:**
- Word count: Increased from 350 to 800-1000
- What We Already Know: Added section
- Cut priority: "Cut from What We Already Know first"
- Word Count Test: Added to self-check

### Coverage Tracker (P2 - Minor)

**Changes Made:**
- Status codes standardized:
  - `READY FOR SYNTHESIS`
  - `GAPS REMAIN - CRITICAL`
  - `GAPS REMAIN - MINOR`
  - `BLOCKED - [reason]`
- Next Agent: Added mandatory field with routing logic
- Status Test: Added to self-check

### Tech Evaluation (P2 - No Changes)

- Version bump only for consistency
- Agent performing well in evaluation

---

## Files Modified

| File | Change Type |
|------|-------------|
| `synthesizer-v4.1.md` | NEW - major revision |
| `insight-extractor-v4.1.md` | NEW - major revision |
| `triage-v4.1.md` | NEW - minor updates |
| `discovery-planner-v4.1.md` | NEW - minor updates |
| `coverage-tracker-v4.1.md` | NEW - minor updates |
| `tech-evaluation-v4.1.md` | NEW - version bump only |
| `agent_service.py` | MODIFIED - AGENT_FILES and AGENT_DESCRIPTIONS |

---

## Testing Checklist

### Manual Testing
- [ ] Run Synthesizer on "Strategic Account Planning" initiative
  - [ ] Decision in first word (GO/NO-GO/CONDITIONAL)?
  - [ ] Real names present (not role titles)?
  - [ ] "Done When" criteria in First Action?
  - [ ] Word count under 800?

- [ ] Run Insight Extractor on "Strategic Account Planning" initiative
  - [ ] Patterns Detected section with mermaid diagram?
  - [ ] Contradictions table present?
  - [ ] What They Don't Realize table present?
  - [ ] Information Quality all 4 rows filled?
  - [ ] For Synthesizer section present?
  - [ ] Word count under 700?

- [ ] Run Triage
  - [ ] Tier routing on second line?
  - [ ] Next Agent specified?

- [ ] Run Coverage Tracker
  - [ ] Status is one of the 4 standard codes?
  - [ ] Next Agent specified?

- [ ] Run Discovery Planner
  - [ ] Word count between 800-1000?
  - [ ] What We Already Know section present?

### Automated Checks
- [ ] Run `scripts/query_purdy_outputs.py` after test runs
- [ ] Compare v4.0 vs v4.1 outputs
- [ ] Re-score using RUBRIC-v3.0.md

### Success Criteria
- Synthesizer score: 12/20 -> 16/20+
- Insight Extractor score: 12/20 -> 16/20+
- Overall score: 78.5 -> 85+

---

## Rollback Plan

If v4.1 agents produce worse outputs:

1. Revert AGENT_FILES in `agent_service.py` to point to v4.0 files
2. Keep v4.1 files for debugging
3. Document issues in this file

```python
# Rollback to v4.0
AGENT_FILES = {
    "triage": "triage-v4.0.md",
    "discovery_planner": "discovery-planner-v4.0.md",
    "coverage_tracker": "coverage-tracker-v4.0.md",
    "insight_extractor": "insight-extractor-v4.0.md",
    "synthesizer": "synthesizer-v4.0.md",
    "tech_evaluation": "tech-evaluation-v4.0.md",
    "meta_synthesizer": "meta-synthesizer-v1.0.md"
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v4.0 | 2026-01-24 | Consulting quality bar, Insight Extractor agent added |
| **v4.1** | **2026-01-25** | Evaluation gap fixes based on RUBRIC-v3.0 scoring |
