# DISCo v4.1 Changelog (formerly PuRDy)

**Date:** 2026-01-25
**Author:** Claude Code session
**Previous Version:** v4.0 (2026-01-24)

---

## Overview

v4.1 addresses gaps identified in the v4.0 evaluation which scored 78.5/100. Two agents needed iteration (Synthesizer, Insight Extractor at 12/20 each), and four agents received minor improvements. Target score: 85+.

---

## Post-Release Fixes (2026-01-25)

### fix: Parse v4.1 decision line as executive summary (`e0a63142`)

The v4.1 Synthesizer format removed the "Executive Summary" heading and replaced it with decision-first format (`**GO:** ...`). The parser now falls back to extracting the decision line when no Executive Summary heading is found.

### fix: Use session token for condense endpoint auth (`ee194448`)

The condense endpoint was returning 401 because `OutputViewer.tsx` was using `localStorage.getItem('access_token')` (null) instead of `session?.access_token` from the `useAuth` hook.

### feat: Double status messages with ethics/safety humor (`4028ebeb`)

Expanded from 44 to 91 status messages. New categories include:
- Ethics/Safety/Bias (18): RLHF, Constitutional AI, paperclip maximizer, Skynet, alignment humor
- Movie quotes (8): Jurassic Park, Princess Bride, Matrix
- TV/Internet (6): The Office, GoT, IT Crowd
- Mundane activities, ADHD/distraction, absurdist, philosophical

---

## Breaking Changes

None. v4.0 agent files retained for rollback.

---

## Agent Changes

### Synthesizer (P0 - Major Revision)

**Previous Score:** 12/20
**Target Score:** 16/20+

| Issue | v4.0 Behavior | v4.1 Fix |
|-------|---------------|----------|
| Decision position | First paragraph | First WORD must be GO/NO-GO/CONDITIONAL |
| Owner names | Role titles allowed | Real names required, fallback: "[Requester to identify owner]" |
| Completion criteria | Missing | "Done When" field with observable criteria |
| Word count | 500 (actual: 1000+) | 800 (realistic limit) |

**New Anti-patterns:**
- "Decision Needed:" prefix (still not decision-first)
- Title as first line

**New Self-check:**
- Decision Position Test (is first word GO/NO-GO/CONDITIONAL?)
- Completion Test (is Done When observable?)

### Insight Extractor (P0 - Major Revision)

**Previous Score:** 12/20
**Target Score:** 16/20+

| Issue | v4.0 Behavior | v4.1 Fix |
|-------|---------------|----------|
| Patterns section | Text description only | Mermaid diagram template for reinforcing loops |
| Contradictions | Not required | Mandatory table with implication column |
| Surprises | Not structured | "What They Don't Realize" table with surprise value |
| Info Quality | 4 rows mentioned | 4 rows required with Gap column |
| Synthesizer handoff | Implicit | Explicit "For Synthesizer" section |
| Word count | 500 (actual: 1000+) | 700 (realistic limit) |

**New Sections:**
- Pattern Detection Guide (how to identify loops/contradictions)
- For Synthesizer (recommended leverage point, key quote, main risk)

**New Self-check:**
- Completeness Test (all 5 mandatory elements present?)

### Triage (P2 - Minor Update)

| Change | Description |
|--------|-------------|
| Tier routing | Added explicit field on second line after decision |
| Next Agent | Added to Next Step section |
| Parsing Test | Added to self-check for structured output validation |

### Discovery Planner (P2 - Minor Update)

| Change | Description |
|--------|-------------|
| Word count | Increased from 350 to 800-1000 |
| What We Already Know | New section documenting existing knowledge |
| Cut priority | Guidance to cut from "What We Already Know" first if over limit |

### Coverage Tracker (P2 - Minor Update)

| Change | Description |
|--------|-------------|
| Status codes | Standardized: READY FOR SYNTHESIS, GAPS REMAIN - CRITICAL, GAPS REMAIN - MINOR, BLOCKED - [reason] |
| Next Agent | Mandatory field with routing logic |
| Status Test | Added to self-check |

### Tech Evaluation (P2 - No Changes)

Version bump only for consistency. Agent performing well in evaluation.

---

## Files Changed

### New Files
```
backend/disco_agents/synthesizer-v4.1.md
backend/disco_agents/insight-extractor-v4.1.md
backend/disco_agents/triage-v4.1.md
backend/disco_agents/discovery-planner-v4.1.md
backend/disco_agents/coverage-tracker-v4.1.md
backend/disco_agents/tech-evaluation-v4.1.md
```
(Note: `purdy_agents/` path alias still supported for backwards compatibility)

### Modified Files
```
backend/services/disco/agent_service.py
  - AGENT_FILES dict updated to v4.1 filenames
  - AGENT_DESCRIPTIONS dict updated with v4.1 versions and descriptions

backend/disco_agents/REVISION-NOTES-v4.1.md
  - Updated with implementation details
  - Added testing checklist
  - Added rollback instructions
```
(Note: `services/purdy/` path alias still supported for backwards compatibility)

---

## Code Changes

### agent_service.py

```python
# Before (v4.0)
AGENT_FILES = {
    "triage": "triage-v4.0.md",
    "discovery_planner": "discovery-planner-v4.0.md",
    "coverage_tracker": "coverage-tracker-v4.0.md",
    "insight_extractor": "insight-extractor-v4.0.md",
    "synthesizer": "synthesizer-v4.0.md",
    "tech_evaluation": "tech-evaluation-v4.0.md",
    "meta_synthesizer": "meta-synthesizer-v1.0.md"
}

# After (v4.1)
AGENT_FILES = {
    "triage": "triage-v4.1.md",
    "discovery_planner": "discovery-planner-v4.1.md",
    "coverage_tracker": "coverage-tracker-v4.1.md",
    "insight_extractor": "insight-extractor-v4.1.md",
    "synthesizer": "synthesizer-v4.1.md",
    "tech_evaluation": "tech-evaluation-v4.1.md",
    "meta_synthesizer": "meta-synthesizer-v1.0.md"
}
```

---

## Testing Required

### Manual Testing Checklist

**Synthesizer:**
- [ ] First word is GO/NO-GO/CONDITIONAL (not title, not "Decision Needed:")
- [ ] Real names in Evidence, Blockers, First Action (no role titles)
- [ ] "Done When" field present with observable criteria
- [ ] Word count under 800

**Insight Extractor:**
- [ ] Patterns Detected section with mermaid diagram
- [ ] Contradictions table present
- [ ] "What They Don't Realize" table present
- [ ] Information Quality table has all 4 rows with Gap column
- [ ] "For Synthesizer" section present
- [ ] Word count under 700

**Triage:**
- [ ] Tier routing on second line (ELT/Solutions/Self-Serve)
- [ ] Next Agent specified in Next Step section

**Coverage Tracker:**
- [ ] Status is one of 4 standard codes
- [ ] Next Agent field present

**Discovery Planner:**
- [ ] Word count between 800-1000
- [ ] "What We Already Know" section present

### Success Criteria
- Synthesizer: 12/20 -> 16/20+
- Insight Extractor: 12/20 -> 16/20+
- Overall: 78.5/100 -> 85/100+

---

## Rollback Instructions

If v4.1 produces worse outputs:

1. Revert AGENT_FILES in `agent_service.py`:
```python
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

2. Revert AGENT_DESCRIPTIONS versions to "v4.0"

3. v4.1 files remain for debugging

---

## Related Documents

- `backend/disco_agents/REVISION-NOTES-v4.1.md` - Implementation details
- `backend/disco_agents/EVALUATION-v4.0-RESULTS.md` - Evaluation that drove these changes
- `backend/disco_agents/RUBRIC-v3.0.md` - Scoring methodology

(Note: `purdy_agents/` path alias still supported for backwards compatibility)
