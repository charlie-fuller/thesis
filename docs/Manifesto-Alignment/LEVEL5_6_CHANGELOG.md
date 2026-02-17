# Manifesto Alignment Levels 5+6 Changelog

## Overview

Levels 5+6 close the remaining gaps in the compliance system: the streaming chat path (primary user-facing endpoint) was unscored, there was no admin dashboard UI for compliance data, and drift detection was passive-only (alerts sat unread with no active response).

## Phase 5B: Streaming Chat Path Compliance Scoring

**Problem:** The streaming multi-agent chat path (`chat_stream`) was the primary user-facing endpoint but had no compliance scoring. All scoring was on the non-streaming path only.

**Changes:**
- `backend/api/routes/chat.py`: Added `score_manifesto_compliance()` call after streaming response is fully accumulated, before `save_messages()` definition
- Compliance data stored in `assistant_metadata["manifesto_compliance"]` via closure
- Semantic evaluation triggered after message save when warranted
- Drift score recording added for both streaming and non-streaming paths

## Phase 5C: Compliance Tab on Dashboard

**Problem:** Compliance data was only accessible via API endpoint. No UI for viewing trends, per-agent breakdown, or drift alerts.

**Changes:**
- `frontend/app/page.tsx`: Added "Compliance" tab to the admin dashboard navigation (between Process Map and Knowledge Graph)
- `frontend/components/ManifestoCompliancePanel.tsx`: New self-contained panel component

**Panel features:**
- Time range selector (7d / 30d / 90d pill buttons)
- Summary cards: Total scored, Aligned %, Drifting %, Misaligned %
- Level distribution bar (stacked horizontal, teal/amber/red)
- Per-agent table with AgentIcon, message count, avg score, level badge
- Drift alerts section with agent + principle + hit rate
- Source breakdown (chat vs meeting stats)

## Phase 6A: Active Drift Response

**Problem:** Drift detection was passive -- alerts were generated but never acted on. An agent could drift through an entire conversation without correction.

**Changes:**
- `backend/services/compliance_drift_tracker.py`: New module providing in-memory, conversation-scoped drift tracking

**Drift tracker design:**
- `record_compliance_score()`: Records scores per agent per conversation
- `get_compliance_reminder()`: Returns reminder text when avg of last 3 scores < 0.30
- `clear_conversation()`: Cleanup for ended conversations
- `OrderedDict` with `MAX_TRACKED_CONVERSATIONS=500` cap prevents memory leaks
- Reminder includes self-assessment instruction (Phase 6D embedded)

**Integration points (8 total):**

Score recording (6 sites):
1. `chat.py` non-streaming path (after existing `score_manifesto_compliance`)
2. `chat.py` streaming path (new scoring + recording)
3. `meeting_orchestrator.py` facilitator response
4. `meeting_orchestrator.py` reporter response
5. `meeting_orchestrator.py` primary agent response
6. `meeting_orchestrator.py` autonomous agent response

System prompt injection (4 sites):
1. `chat.py` non-streaming path (before LLM call)
2. `chat.py` streaming path (before LLM call)
3. `meeting_orchestrator.py` primary agent (via `_build_meeting_system_prompt`)
4. `meeting_orchestrator.py` autonomous agent (via `_build_autonomous_system_prompt`)

**Reminder template:**
```
[COMPLIANCE NOTE] Your recent responses have not demonstrated these expected principles: {gap_names}. Please actively incorporate them. Briefly reflect on which principles you've been strong and weak on before responding.
```

## Phase 6D: Self-Assessment (Embedded)

Self-assessment is embedded directly in the compliance reminder rather than as a separate system. The reminder's final sentence ("Briefly reflect on which principles you've been strong and weak on before responding") prompts the agent to self-assess before generating its response.

## Tests

8 new tests added to `backend/tests/test_manifesto_compliance.py` in `TestDriftTracker` class:

1. `test_no_reminder_fewer_than_3_scores` -- No reminder with insufficient data
2. `test_no_reminder_above_threshold` -- No reminder when performing adequately
3. `test_reminder_generated_when_drifting` -- Reminder fires when avg < 0.30
4. `test_reminder_includes_gap_names` -- Human-readable principle names in text
5. `test_recovery_clears_reminder` -- Good scores clear the reminder
6. `test_clear_conversation` -- Explicit cleanup works
7. `test_memory_limit_eviction` -- Oldest conversations evicted at capacity
8. `test_self_assessment_in_reminder` -- Self-reflection instruction present

**Total test count: 42 (34 existing + 8 new), all passing.**

## Files Summary

**New files (2):**
- `backend/services/compliance_drift_tracker.py`
- `frontend/components/ManifestoCompliancePanel.tsx`

**Modified files (4):**
- `frontend/app/page.tsx`
- `backend/api/routes/chat.py`
- `backend/services/meeting_orchestrator.py`
- `backend/tests/test_manifesto_compliance.py`

**Documentation (1):**
- `docs/Manifesto-Alignment/LEVEL5_6_CHANGELOG.md` (this file)

## Deferred

- **5A (Governance Doc Updates):** Manual KB re-upload, not code
- **6B (Semantic Calibration):** Needs production data for threshold tuning
- **6C (Principle Versioning):** Needs production data for version tracking
