# Level 4 Changelog: Manifesto Alignment System Hardening

**Date:** 2026-02-17
**Scope:** 4 new files, 8 modified files, 34 new tests
**Status:** COMPLETE

---

## Overview

Level 4 closes 7 remaining gaps identified after Level 3:
1. Semantic evaluation beyond regex pattern matching
2. Weekly digest notifications for compliance trends
3. Defined thresholds for compliance levels
4. Deeper principle-level analysis
5. UI transparency (compliance indicators on messages)
6. Metadata normalization (source tagging)
7. Unit test coverage for the compliance system

---

## Phase 1: Defined Thresholds (Gap 3)

### `backend/services/manifesto_compliance.py`

New constants:
- `COMPLIANCE_THRESHOLDS`: aligned >= 0.60, drifting >= 0.30, misaligned < 0.30
- `DRIFT_ALERT_THRESHOLD`: 0.25 (25% hit rate minimum)
- `MIN_MESSAGES_FOR_EVALUATION`: 3 (minimum messages before drift alerts fire)

New helper:
- `_get_compliance_level(score) -> str`: Returns "aligned", "drifting", or "misaligned"
- `level` field now included in all `score_manifesto_compliance()` return dicts

### `backend/api/routes/admin/manifesto_compliance.py`

- Uses imported constants instead of hardcoded values
- `level_distribution` added to response: counts of aligned/drifting/misaligned messages

---

## Phase 2: Metadata Normalization (Gap 6)

### `backend/services/manifesto_compliance.py`

- `source` parameter added to `score_manifesto_compliance()`
- When provided, `source` field included in return dict

### Call site updates

| File | Call Site | Source Value |
|------|-----------|-------------|
| `api/routes/chat.py` | Non-streaming chat response | `"chat"` |
| `services/meeting_orchestrator.py` | Facilitator response | `"meeting"` |
| `services/meeting_orchestrator.py` | Reporter response | `"meeting"` |
| `services/meeting_orchestrator.py` | Primary agent response | `"meeting"` |
| `services/meeting_orchestrator.py` | Autonomous agent turns | `"meeting"` |

### `backend/api/routes/admin/manifesto_compliance.py`

- `by_source` aggregation added: message counts and avg scores per source
- Included in response as `by_source`

---

## Phase 3: Unit Tests (Gap 7)

### New file: `backend/tests/test_manifesto_compliance.py`

34 tests across 3 test classes:

**TestManifestoScorer (23 tests):**
- Empty/None response handling
- P1 (state change), P3 (evidence), P4 (output type), P5 (people), P6 (humans decide) signal detection
- Agent-specific scoring: full signals = 1.0, partial = proportional ratio
- Unknown agent fallback scoring
- `_normalize_agent_name` with display names, prefixes, case, whitespace
- Valid principle keys in AGENT_EXPECTED_PRINCIPLES
- `_get_compliance_level` boundary values
- Source field presence/absence
- Level field always present

**TestAdminEndpoint (5 tests):**
- Response structure with mocked Supabase data
- Empty data returns zeros without errors
- Drift alert fires when agent <25% hit rate with 5+ messages
- No drift alert for agents with <3 messages
- `level_distribution` and `by_source` in response

**TestSemanticScorer (6 tests):**
- Selection logic: zero signals with expected principles triggers evaluation
- Zero signals without expected principles does not trigger
- With signals: only random 20% sample triggers
- No event loop: trigger gracefully skips
- Rate limiter blocks after 10 calls/minute
- Missing API key returns None

---

## Phase 4: Semantic Scorer (Gaps 1 + 4)

### New file: `backend/services/manifesto_semantic_scorer.py`

LLM-based semantic compliance evaluation:
- Model: `claude-haiku-4-5-20251001`
- Rate limiter: in-memory counter, max 10 evaluations/minute
- `evaluate_semantic_compliance(response_text, agent_name, regex_result)` -> dict
- Returns: `semantic_score`, `principle_assessments` (per-principle 0-1), `behavioral_flags`
- `_store_semantic_result(message_id, table_name, result)` -> async Supabase metadata update

### `backend/services/manifesto_compliance.py`

- `should_semantic_evaluate(regex_result, agent_name)` -> bool
  - True when: zero regex signals + agent has expected principles, OR 20% random sample
- `trigger_semantic_evaluation(response_text, agent_name, regex_result, message_id, table_name)`
  - Fire-and-forget using `asyncio.create_task()`
  - Graceful no-op if no running event loop

### Call site wiring

All 5 compliance scoring paths now trigger semantic evaluation when `should_semantic_evaluate()` returns True:
- `api/routes/chat.py`: after DB insert, captures message ID from result
- `services/meeting_orchestrator.py`: 4 sites, each captures message ID from `_store_message()` / `_store_autonomous_message()` return value

---

## Phase 5: Weekly Digest (Gap 2)

### New file: `backend/services/manifesto_digest_scheduler.py`

Follows `engagement_scheduler.py` pattern:
- APScheduler with CronTrigger: Monday 07:00 UTC
- `start_manifesto_digest_scheduler(day_of_week, hour_utc, minute)`
- `stop_manifesto_digest_scheduler()`
- `get_manifesto_digest_status()` -> dict
- `trigger_manual_digest()` -> dict (for admin use)

Digest content:
- 7-day lookback across `messages` and `meeting_room_messages`
- Per-agent stats: message count, avg score, compliance level
- Level distribution: aligned/drifting/misaligned counts
- Drift alerts: expected principles with <25% hit rate

Delivery:
- Resend email to configured admin address
- HTML + plain text body
- Fallback to logging if Resend unavailable

### `backend/main.py`

- Startup: `start_manifesto_digest_scheduler(day_of_week="mon", hour_utc=7, minute=0)`
- Shutdown: `stop_manifesto_digest_scheduler()`

---

## Phase 6: UI Indicator (Gap 5)

### `frontend/components/ChatMessage.tsx`

- `ManifestoCompliance` TypeScript interface
- `PRINCIPLE_LABELS` mapping (P1-P11 to human-readable names)
- `COMPLIANCE_COLORS` mapping (aligned=teal, drifting=amber, misaligned=red)
- `ManifestoIndicator` component: small colored dot next to agent badge
- Hover tooltip shows detected principles and compliance level
- Renders when `metadata.manifesto_compliance?.level` exists

### `frontend/components/meeting-room/MeetingMessage.tsx`

- Same `ManifestoIndicator` pattern for meeting room messages
- Renders next to agent name in message header

---

## Files Summary

**New files (4):**
1. `backend/services/manifesto_semantic_scorer.py`
2. `backend/services/manifesto_digest_scheduler.py`
3. `backend/tests/test_manifesto_compliance.py`
4. `docs/Manifesto-Alignment/LEVEL4_CHANGELOG.md` (this file)

**Modified files (8):**
1. `backend/services/manifesto_compliance.py` -- thresholds, levels, source, semantic trigger
2. `backend/api/routes/admin/manifesto_compliance.py` -- level distribution, source aggregation
3. `backend/api/routes/admin/__init__.py` -- register manifesto_compliance router
4. `backend/api/routes/chat.py` -- source param, semantic trigger
5. `backend/services/meeting_orchestrator.py` -- source param (4 sites), semantic trigger (4 sites)
6. `backend/main.py` -- digest scheduler startup/shutdown
7. `frontend/components/ChatMessage.tsx` -- ManifestoIndicator
8. `frontend/components/meeting-room/MeetingMessage.tsx` -- ManifestoIndicator

**Test file (1):**
9. `backend/tests/conftest.py` -- sample_compliance_response fixture

---

## Risk Assessment

- **Zero breakage risk:** All changes are additive, no existing behavior modified
- **Semantic scorer is fire-and-forget:** Cannot block or slow response delivery
- **Rate limited:** Max 10 Haiku calls/minute prevents cost runaway
- **Digest scheduler follows proven pattern:** Same architecture as engagement_scheduler
- **UI indicators are passive:** Only render when data exists, no new API calls
- **Fully reversible:** Remove new files, revert parameter additions
