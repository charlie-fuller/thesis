# Manifesto Alignment: Full Summary (Levels 1-4) and Future Plans (Levels 5-6)

**Date:** 2026-02-17
**Status:** Levels 1-4 COMPLETE | Levels 5-6 PLANNED

---

## Why This Work Exists

Thesis is a multi-agent platform with 22 specialized AI agents advising enterprise clients on AI strategy. These agents operate under a shared manifesto -- 11 operational principles governing how they reason, communicate, and interact with humans.

The manifesto existed as a document. Agents included it in their system prompts. But there was no enforcement, no measurement, and no way to know whether agents actually followed the principles or just loaded them.

This work closes that gap across 4 levels: from auditing the gap, to fixing agent instructions, to building runtime compliance scoring, to adding semantic evaluation and user-facing transparency.

---

## What the Manifesto Defines

11 principles (v1.1):

| # | Principle | Core Idea |
|---|-----------|-----------|
| P1 | State Change | Every response should move something -- a decision, behavior, or understanding |
| P2 | Problems Before Solutions | Validate the problem before proposing solutions |
| P3 | Evidence Over Eloquence | Ground claims in data, not persuasive language |
| P4 | Know Your Output Type | Distinguish deterministic facts from non-deterministic interpretations |
| P5 | People Are the Center | Center the human experience in every recommendation |
| P6 | Humans Decide | Frame output as input to human decisions, not as decisions |
| P7 | Multiple Perspectives | Surface alternative viewpoints and dissent |
| P8 | Context and Brevity | Say what matters, skip what doesn't |
| P9 | Guardrails Not Gates | Enable with guardrails, don't block with gates |
| P10 | Trace the Connections | Show where things connect across systems |
| P11 | The Questions Stay the Same | Follow the shared DISCO methodology |

---

## Level 1: Audit + Shared/Agent Instruction Fixes

**Problem:** No one had systematically checked whether the 22 agents and their shared instruction files actually aligned with the manifesto they claimed to follow.

**What happened:**
1. Full audit of all 24 agent XMLs, 4 shared instruction files, and 6 governance documents against all 11 principles
2. Found 7 critical issues (Echo contradicting P3, Kraken tensions with P5, P1 absent everywhere, gate language in shared files, domain deferral contradictions)
3. Fixed shared files (smart_brevity.xml, conversational_awareness.xml, AGENT_GUARDRAILS.md) -- 9 edits addressing P1, P2, P3, P4, P6, P8
4. Fixed 6 individual agent XMLs (Echo, Kraken, Project Agent, Oracle, Capital, Reporter) -- 6 edits addressing P2, P3, P5, P9
5. Documented 8 advisory recommendations for governance documents in KB

**Files:** AUDIT_REPORT.md, TIER1_CHANGELOG.md, TIER2_CHANGELOG.md, TIER3_CHANGELOG.md

**Why it matters:** Found that P1 (State Change) -- the most foundational principle -- had zero behavioral implementation anywhere. P4 (People Are the Center) was the weakest across all governance docs. Multiple agents had instructions that directly contradicted the manifesto they loaded.

---

## Level 2: Structural Gaps + Code-Level Scoring

**Problem:** Level 1 fixed contradictions but left 4 structural gaps: P1 had no agent champions, P5 had only one (Sage), P11 (DISCO) had only one (initiative_agent), and everything was prompt-level only with no runtime detection.

**What happened:**
1. Added new P4 "Know Your Output Type" to manifesto (v1.0 -> v1.1), renumbered all subsequent principles
2. Created 2 new shared XML fragments: `state_change_check.xml` (5-step P1 protocol) and `disco_awareness.xml` (P11 awareness)
3. Edited 8 agent XMLs to champion underserved principles (Strategist, Operator, Scholar, Architect for P1/P5; Atlas, Pioneer, Nexus for P11; Catalyst for P5)
4. Built `manifesto_compliance.py` -- regex-based pattern matching scorer (microsecond latency, no LLM calls)
5. Integrated scoring at 2 response paths: chat endpoint + meeting orchestrator primary agent

**Key design decision:** Regex-based scoring was chosen for zero-latency impact on user responses. 11 principle signal sets with 5-11 patterns each, 14 agents with expected principle configurations. Results stored in existing JSONB metadata column -- zero schema changes.

**Files:** 3 new (state_change_check.xml, disco_awareness.xml, manifesto_compliance.py), 10 modified

---

## Level 3: Full Coverage + Admin Visibility

**Problem:** Level 2 scored only 2 of 5 response paths. The new P4 principle had no agent champions. Compliance data was stored but not queryable.

**What happened:**
1. Designated 4 P4 agent champions (Oracle, Capital, Architect, Reporter) with new capabilities and output format additions
2. Created `output_type_classifier.xml` shared fragment (4-step classification protocol)
3. Added compliance scoring at 3 more response paths in meeting_orchestrator.py (facilitator, reporter, autonomous agents) -- total now 5/5
4. Built admin analytics endpoint: `GET /api/admin/analytics/manifesto-compliance` with per-agent stats, per-principle stats, and drift alerts

**Files:** 2 new (output_type_classifier.xml, admin/manifesto_compliance.py), 7 modified

---

## Level 4: System Hardening

**Problem:** Level 3 had full instrumentation but 7 gaps between "instrumented" and "effective": no thresholds, surface-level regex only, no feedback loop, no tests, chat/meeting metadata asymmetry, no user transparency.

**What happened:**
1. **Thresholds:** Defined aligned (>=0.60), drifting (>=0.30), misaligned (<0.30) levels with `_get_compliance_level()` helper. Every compliance result now includes a `level` field.
2. **Metadata normalization:** Added `source` parameter to scoring function. Chat path tags `source="chat"`, meeting paths tag `source="meeting"`. Admin endpoint aggregates by source.
3. **Tests:** 34 unit tests across 3 test classes (TestManifestoScorer: 23, TestAdminEndpoint: 5, TestSemanticScorer: 6). Covers regex detection, scoring math, normalization, boundary values, admin endpoint structure, drift alerts, rate limiting.
4. **Semantic scorer:** Background LLM evaluation using Claude Haiku. Fire-and-forget via `asyncio.create_task()`. Triggers when regex finds zero signals on an agent with expected principles, or on 20% random sample. Rate limited to 10/minute. Stores `semantic_compliance` in message metadata.
5. **Weekly digest:** APScheduler CronTrigger (Monday 07:00 UTC). Queries 7 days of data, computes per-agent stats, level distribution, drift alerts. Sends HTML email via Resend with logging fallback.
6. **UI indicators:** Colored dots on chat and meeting messages (teal=aligned, amber=drifting, red=misaligned). Hover tooltip shows detected principles. Only renders when compliance data exists.

**Files:** 4 new (manifesto_semantic_scorer.py, manifesto_digest_scheduler.py, test_manifesto_compliance.py, LEVEL4_CHANGELOG.md), 9 modified

---

## Cumulative Impact (Levels 1-4)

| Metric | Before | After |
|--------|--------|-------|
| Principles with behavioral implementation | ~5 of 10 | 11 of 11 |
| Agents with champion designations | ~4 | 14+ |
| Response paths scored | 0 | 5 of 5 |
| Compliance data queryable | No | Yes (admin endpoint + weekly digest) |
| Semantic evaluation | None | Background LLM eval on suspicious/sampled responses |
| User transparency | None | Colored indicators on every scored message |
| Test coverage | 0 | 34 dedicated tests |
| Contradictions in agent instructions | 7 critical | 0 |

**Total files touched across all 4 levels:** ~35 (new + modified)

---

## Level 5 Plan: Governance Document Updates + Streaming Path Coverage

**Status:** PLANNED -- not started

### 5A: Apply Governance Document Recommendations

The Tier 3 audit identified 8 specific recommendations for 6 governance documents stored in the Knowledge Base. These are advisory-only today.

**Work:**
1. Download current versions of all 6 governance docs from Supabase KB
2. Apply the 8 recommended changes documented in TIER3_CHANGELOG.md:
   - Add "People Impact" section to all 6 docs (P4)
   - Add DISCO phase references to all 6 docs (P11)
   - Add Stage 0 problem validation to Builder Agreement (P2)
   - Add named decision authority to Decision Framework (P5)
   - Add System Impact dimension to Rubric (P9)
   - Add job displacement section to REVISED Report (P4)
3. Re-upload updated versions to KB
4. Verify agents can cite the updated content via RAG

### 5B: Streaming Chat Path Compliance Scoring

The non-streaming chat path (legacy, used for simple requests) is scored. The streaming multi-agent chat path (~line 2094 in chat.py) is not. This is the primary user-facing path.

**Work:**
1. Add `score_manifesto_compliance(full_response, selected_agent, source="chat")` after the streaming response is fully assembled
2. Store compliance data in message metadata (same pattern as non-streaming path)
3. Add semantic trigger at the same location
4. Update test coverage

### 5C: Admin Dashboard UI

The admin endpoint exists but has no frontend. Build a simple dashboard page.

**Work:**
1. New page: `/admin/manifesto` (or tab on existing admin page)
2. Fetch from `GET /api/admin/analytics/manifesto-compliance`
3. Display: level distribution chart, per-agent compliance table, drift alerts list, source breakdown
4. Time range selector (7d, 30d, 90d)
5. Link to semantic evaluation details when available

---

## Level 6 Plan: Closed-Loop Enforcement + Continuous Improvement

**Status:** PLANNED -- not started

### 6A: Active Drift Response

Currently, drift alerts are passive (shown in admin endpoint, included in weekly digest). Level 6 makes the system respond to drift.

**Work:**
1. When an agent's average compliance drops below `drifting` threshold for 3+ consecutive messages:
   - Inject a system prompt addendum for that agent's next response: "Recent responses have not demonstrated [principle names]. Please actively incorporate these principles."
   - Log the injection event for audit trail
2. Admin notification (real-time, not just weekly) when an agent enters `misaligned` state
3. Auto-recovery: remove the addendum once the agent returns to `aligned` for 3+ messages
4. Configurable: admin can enable/disable per agent

### 6B: Semantic Evaluation Calibration

The semantic scorer uses a static prompt. Level 6 calibrates it against human judgment.

**Work:**
1. Build a calibration dataset: 50-100 agent responses manually labeled for compliance by a human reviewer
2. Run the semantic scorer against the calibration set
3. Measure agreement rate (target: >80%)
4. Tune the evaluation prompt based on disagreements
5. Store calibration results for future comparison
6. Add a `/api/admin/manifesto/calibration` endpoint to view agreement metrics

### 6C: Principle Evolution Tracking

The manifesto will change over time. Level 6 tracks principle additions, removals, and modifications.

**Work:**
1. Version the manifesto in Supabase (not just the XML file): `manifesto_versions` table with version number, principles JSON, effective date
2. When compliance is scored, tag the result with the manifesto version
3. Admin endpoint shows compliance trends across manifesto versions
4. Weekly digest notes if the manifesto changed that week and which agents need instruction updates

### 6D: Agent Self-Assessment

Let agents periodically evaluate their own compliance.

**Work:**
1. New shared XML fragment: `self_assessment.xml` -- protocol for agents to reflect on their own recent outputs
2. Triggered at conversation boundaries (start of new conversation, or every N messages)
3. Agent generates a brief self-assessment: "In my recent responses, I've been strong on [principles] and weak on [principles]"
4. Stored in a dedicated `agent_self_assessments` table
5. Compared against regex + semantic scores to identify self-awareness gaps

---

## Architecture Diagram

```
Level 1: AUDIT
  manifesto.xml ----audit----> AUDIT_REPORT.md
  24 agent XMLs                TIER1_CHANGELOG (shared fixes)
  4 shared XMLs                TIER2_CHANGELOG (agent fixes)
  6 gov docs                   TIER3_CHANGELOG (advisory)

Level 2: STRUCTURAL FIXES + RUNTIME SCORING
  New shared XMLs (state_change_check, disco_awareness)
  8 agent XML edits (champion designations)
  manifesto_compliance.py (regex scorer)
  2 integration points (chat + meeting primary agent)

Level 3: FULL COVERAGE + VISIBILITY
  4 P4 agent champions + output_type_classifier.xml
  3 new scoring call sites (facilitator, reporter, autonomous)
  Admin analytics endpoint

Level 4: HARDENING
  Thresholds + levels
  Metadata normalization (source tagging)
  34 unit tests
  Semantic scorer (background Haiku eval)
  Weekly digest scheduler
  UI compliance indicators

Level 5: GOVERNANCE + COVERAGE COMPLETION (planned)
  Apply 8 governance doc recommendations
  Score streaming chat path
  Admin dashboard UI

Level 6: CLOSED-LOOP ENFORCEMENT (planned)
  Active drift response (system prompt injection)
  Semantic scorer calibration
  Principle evolution tracking
  Agent self-assessment
```
