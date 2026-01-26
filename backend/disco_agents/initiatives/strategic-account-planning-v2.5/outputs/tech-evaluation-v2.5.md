# Tech Evaluation: Strategic Account Planning

**Version:** v2.5
**Date:** 2026-01-23
**PRD Reference:** `synthesis-v2.5.md`
**Evaluator:** I.S. Team (Charlie/Tyler)

---

## Recommendation

**Platform/Approach:** **Hybrid - Glean + Claude + Custom Integrations**
**Conviction Level:** MEDIUM (appropriate for technical decisions that should follow governance)

### The One-Sentence Rationale

> No single platform meets all requirements; Glean handles internal data, Claude handles external research and synthesis, custom integrations bridge them.

---

## Prerequisites (From Synthesis)

> **CRITICAL:** This tech evaluation assumes governance-first approach is adopted. If Data Quality Owner is not established, the technical architecture below will inherit the same problems that caused previous tools to fail.

| Prerequisite | Status | Dependency |
|--------------|--------|------------|
| Data Quality Owner designated | **PENDING** | Must complete before Phase 2 |
| Gold template standardized | **PENDING** | Must complete before Phase 2 |
| Crossbeam access granted to AEs | **PENDING** | Enables partner data integration |

---

## Requirements Recap

| Category | Requirement | Priority |
|----------|-------------|----------|
| **Functional** | White space map generation | HIGH |
| | Internal footprint aggregation | HIGH |
| | Partner matching | MEDIUM |
| | QA/validation of AI output | HIGH |
| | Strategic alignment research (10K, news) | MEDIUM |
| **Non-Functional** | 95%+ accuracy (or confidence scoring) | HIGH |
| | <2 hour end-to-end account plan | HIGH |
| | AE-friendly interface (low learning curve) | HIGH |
| **Integration** | Salesforce (read) | HIGH |
| | Crossbeam (read) | HIGH |
| | Tableau/Gatekeeper (read) | MEDIUM |
| | Built With (parse) | LOW |
| **Constraints** | No dedicated dev team | HIGH |
| | Existing Glean investment | MEDIUM |
| | Tool fatigue risk | HIGH |

---

## Build vs. Buy Assessment

| Question | Answer | Implication |
|----------|--------|-------------|
| Is this a differentiator? | NO - Internal efficiency | Favor BUY |
| Do we have capacity to maintain? | PARTIAL - Tyler/Charlie can maintain agents, not full apps | HYBRID |
| What's the exit strategy? | Agents are disposable; data persists in Salesforce | Low risk |
| What did past tools fail from? | Bad data, not bad architecture | Governance matters more than platform |

**Verdict:** HYBRID - Buy platforms (Glean, Claude), build agents and integrations

---

## Options Evaluated

| Option | Score | Recommendation |
|--------|-------|----------------|
| **Glean + Claude + Custom** | **78/100** | **SELECTED** |
| Glean Only | 52/100 | Token limits, no external research |
| Claude/Gemini Only | 65/100 | No internal data access |
| Full Custom Build | 61/100 | No team capacity to maintain |
| Salesforce Einstein | 45/100 | Limited AI capability |

---

## Platform Breakdown

### Tier 1: Glean (Already Owned)

**Use For:**
- Internal footprint queries ("What's our usage at Amazon?")
- Account Navigator / quick lookups
- Partner data (if Crossbeam indexed)
- Simple agent deployment

**Limitations:**
- 128K token limit = can't synthesize full account plans
- No external web research
- Limited complex reasoning

**Assigned Use Cases:**

| Use Case | Fit | Notes |
|----------|-----|-------|
| Internal footprint lookup | HIGH | Tableau, Salesforce, Gatekeeper |
| Partner lookup | MEDIUM | Needs Crossbeam indexing |
| White space generation | LOW | Token limit |
| Strategic alignment | LOW | No external access |

### Tier 2: Claude / Gemini Deep Research

**Use For:**
- External research (websites, 10Ks, news)
- White space map generation
- Complex synthesis
- QA/validation of other AI output

**Limitations:**
- No internal Contentful data access
- Requires manual data input or integration
- API costs scale with usage

**Assigned Use Cases:**

| Use Case | Fit | Notes |
|----------|-----|-------|
| White space generation | HIGH | Deep Research + structured output |
| Strategic alignment | HIGH | 10K analysis, earnings |
| QA validation | HIGH | Cross-check citations |
| Internal footprint | LOW | No access |

### Tier 3: Custom Integrations

**Required:**

| Integration | Purpose | Complexity | Owner |
|-------------|---------|------------|-------|
| Salesforce → Glean | Index account data | MEDIUM | Tyler |
| Crossbeam → Glean | Partner data | MEDIUM | Tyler |
| Tableau → Glean | Usage data | HIGH | Rob/Tyler |
| Built With parser | Structured tech stack | LOW | Charlie |
| Output → Salesforce | Account plan link | LOW | Tom Woodhouse |

**Agents to Build:**

| Agent | Platform | Purpose | Complexity |
|-------|----------|---------|------------|
| White Space Generator | Claude | Deep Research → template | MEDIUM |
| QA Validator | Claude | Cross-check citations | MEDIUM |
| Internal Footprint | Glean | Aggregate internal data | MEDIUM |
| Partner Matcher | Glean | Auto-lookup partners | LOW |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AE WORKFLOW                                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │ Request │───▶│ Research│───▶│ Generate│───▶│ Validate│      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
└───────┼──────────────┼──────────────┼──────────────┼─────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
   │  Glean  │    │ Claude/ │    │  Claude │    │  Claude │
   │ Account │    │ Gemini  │    │ White   │    │   QA    │
   │Navigator│    │ Deep    │    │ Space   │    │ Agent   │
   │         │    │Research │    │ Agent   │    │         │
   └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
   ┌─────────────────────────────────────────────────────┐
   │              DATA LAYER (Governed)                   │
   │  ┌────────┐ ┌─────────┐ ┌───────┐ ┌──────────────┐ │
   │  │Salesfce│ │Crossbeam│ │Tableau│ │ External Web │ │
   │  └────────┘ └─────────┘ └───────┘ └──────────────┘ │
   │                                                     │
   │  DATA QUALITY OWNER: [TBD - Must be designated]     │
   └─────────────────────────────────────────────────────┘
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Glean token limit blocks complex use cases | HIGH | MEDIUM | Route synthesis to Claude |
| No Data Quality Owner designated | **MEDIUM** | **HIGH** | **Gate Phase 2 on governance** |
| Claude API costs exceed budget | MEDIUM | LOW | Set caps, monitor weekly |
| Thomas undermines adoption | LOW | HIGH | Make him co-designer |
| Integration complexity | MEDIUM | MEDIUM | Start with 3 sources, expand later |

---

## Implementation Phases

### Phase 1: Governance + Foundation (Weeks 1-4)

| Action | Owner | Dependency |
|--------|-------|------------|
| Designate Data Quality Owner | Steve/Mikki | None |
| Finalize gold template | Charlie + Chris P | None |
| Grant Crossbeam read access | Partner Ops | None |
| Document Deep Research best practices | Matt Lazar | None |

**Exit Criteria:** Data Quality Owner named, template approved

### Phase 2: Core Build (Weeks 5-10)

| Action | Owner | Dependency |
|--------|-------|------------|
| Build White Space Generator agent | Charlie | Template approved |
| Build QA Validator agent | Tyler | None |
| Index Salesforce in Glean | Tyler | DQO approval |
| Build Internal Footprint agent | Tyler | Glean indexing |

**Exit Criteria:** End-to-end account plan generation working

### Phase 3: Pilot (Weeks 11-14)

| Action | Owner | Dependency |
|--------|-------|------------|
| Deploy to champions (Thomas, Matt L, Chris P) | Charlie | Phase 2 complete |
| Collect feedback | Charlie | Pilot running |
| Measure time savings | Charlie | Pilot running |
| Iterate on agents | Tyler | Feedback collected |

**Exit Criteria:** Champions endorse rollout

### Phase 4: Rollout (Week 15+)

| Action | Owner | Dependency |
|--------|-------|------------|
| Training materials | Charlie | Pilot complete |
| Expand to all strategic AEs | Steve/Rich | Champion endorsement |
| Monitor adoption | Data Quality Owner | Rollout |

---

## Cost Estimate

| Item | One-Time | Annual | Notes |
|------|----------|--------|-------|
| Glean | $0 | ~$50K | Already licensed |
| Claude API | $0 | ~$5-10K | ~500 account plans/year |
| Tyler/Charlie time | ~200 hours | ~100 hours | Build + maintain |
| Training | ~40 hours | ~20 hours | Initial + refresh |
| **Total** | **~240 hours** | **~$60K + 120 hours** | |

**ROI Estimate:**
- 100 AEs × 4 hours saved/account × 10 accounts/year = 4,000 hours saved
- At $75/hour = **$300K annual value**
- **Payback: <6 months** (assuming governance success)

---

## Objections Anticipated

| Objection | Response |
|-----------|----------|
| "Why not just Glean?" | 128K token limit. Can't synthesize full plans or do external research. |
| "Why not full custom?" | No team to maintain. Tyler/Charlie can build agents, not applications. |
| "What if governance fails?" | Then this will fail too. That's why governance is Phase 1 gate, not parallel. |
| "Isn't this expensive?" | $60K/year is less than one headcount. We're buying back 0.5 FTE of selling time. |

---

## Approvals Required

- [x] Technical approach (Tyler validated feasibility)
- [ ] **Data Quality Owner designation (BLOCKING for Phase 2)**
- [ ] Budget approval for Claude API (~$60K over 3 years)
- [ ] Crossbeam access policy change
- [ ] Salesforce field modifications (Tom Woodhouse)

---

## Quality Gate Verification

**Political Test:**
- [x] Thomas engagement strategy included (co-designer role)
- [x] Champion-led rollout planned
- [x] Blocker risks identified with mitigation

**Decision Test:**
- [x] Clear recommendation with rationale
- [x] Alternatives rejected with reasoning
- [x] Governance dependency explicitly stated
- [x] Phased approach with gates

---

*Generated using PuRDy v2.5 Tech Evaluation with governance-first framing*
