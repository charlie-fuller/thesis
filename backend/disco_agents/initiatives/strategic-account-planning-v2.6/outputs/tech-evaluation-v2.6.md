# Tech Evaluation: Strategic Account Planning

**Version:** v2.6
**Date:** 2026-01-23
**PRD Reference:** `synthesis-v2.6.md`
**Evaluator:** I.S. Team (Charlie/Tyler)

---

## Recommendation

**Platform/Approach:** **Hybrid - Glean + Claude + Custom Integrations**
**Conviction Level:** MEDIUM `[Platform decisions should follow governance, not precede it]`

### The One-Sentence Rationale

> No single platform meets all requirements; Glean handles internal data, Claude handles external research and synthesis, custom integrations bridge them.

---

## Prerequisites (From Synthesis) - BLOCKING GATES

> **CRITICAL:** This tech evaluation assumes governance-first approach is adopted. If Data Quality Owner is not established, the technical architecture below will inherit the same problems that caused previous tools to fail.

| Prerequisite | Status | Dependency | Confidence |
|--------------|--------|------------|------------|
| Data Quality Owner designated | **PENDING** | Must complete before Phase 2 | `[HIGH - required]` |
| Gold template standardized | **PENDING** | Must complete before Phase 2 | `[HIGH - required]` |
| Crossbeam access granted to AEs | **PENDING** | Enables partner data integration | `[MEDIUM - helpful]` |

---

## Requirements Recap

| Category | Requirement | Priority | Confidence |
|----------|-------------|----------|------------|
| **Functional** | White space map generation | HIGH | `[HIGH]` |
| | Internal footprint aggregation | HIGH | `[HIGH]` |
| | Partner matching | MEDIUM | `[MEDIUM]` |
| | QA/validation of AI output | HIGH | `[HIGH]` |
| | Strategic alignment research (10K, news) | MEDIUM | `[MEDIUM]` |
| **Non-Functional** | 95%+ accuracy (or confidence scoring) | HIGH | `[HIGH]` |
| | <2 hour end-to-end account plan | HIGH | `[MEDIUM - derived]` |
| | AE-friendly interface (low learning curve) | HIGH | `[HIGH]` |
| **Integration** | Salesforce (read) | HIGH | `[HIGH]` |
| | Crossbeam (read) | HIGH | `[MEDIUM - access TBD]` |
| | Tableau/Gatekeeper (read) | MEDIUM | `[MEDIUM]` |
| | Built With (parse) | LOW | `[LOW]` |
| **Constraints** | No dedicated dev team | HIGH | `[HIGH]` |
| | Existing Glean investment | MEDIUM | `[HIGH]` |
| | Tool fatigue risk | HIGH | `[HIGH]` |

---

## Build vs. Buy Assessment

| Question | Answer | Implication | Confidence |
|----------|--------|-------------|------------|
| Is this a differentiator? | NO - Internal efficiency | Favor BUY | `[HIGH]` |
| Do we have capacity to maintain? | PARTIAL - Tyler/Charlie can maintain agents, not full apps | HYBRID | `[HIGH]` |
| What's the exit strategy? | Agents are disposable; data persists in Salesforce | Low risk | `[HIGH]` |
| What did past tools fail from? | Bad data, not bad architecture | Governance matters more than platform | `[HIGH]` |

**Verdict:** HYBRID - Buy platforms (Glean, Claude), build agents and integrations

---

## Options Evaluated

| Option | Score | Recommendation | Confidence |
|--------|-------|----------------|------------|
| **Glean + Claude + Custom** | **78/100** | **SELECTED** | `[HIGH]` |
| Glean Only | 52/100 | Token limits, no external research | `[HIGH]` |
| Claude/Gemini Only | 65/100 | No internal data access | `[HIGH]` |
| Full Custom Build | 61/100 | No team capacity to maintain | `[HIGH]` |
| Salesforce Einstein | 45/100 | Limited AI capability | `[MEDIUM]` |

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

| Use Case | Fit | Notes | Confidence |
|----------|-----|-------|------------|
| Internal footprint lookup | HIGH | Tableau, Salesforce, Gatekeeper | `[HIGH]` |
| Partner lookup | MEDIUM | Needs Crossbeam indexing | `[MEDIUM]` |
| White space generation | LOW | Token limit | `[HIGH]` |
| Strategic alignment | LOW | No external access | `[HIGH]` |

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

| Use Case | Fit | Notes | Confidence |
|----------|-----|-------|------------|
| White space generation | HIGH | Deep Research + structured output | `[HIGH]` |
| Strategic alignment | HIGH | 10K analysis, earnings | `[HIGH]` |
| QA validation | HIGH | Cross-check citations | `[MEDIUM]` |
| Internal footprint | LOW | No access | `[HIGH]` |

### Tier 3: Custom Integrations

**Required:**

| Integration | Purpose | Complexity | Owner | Confidence |
|-------------|---------|------------|-------|------------|
| Salesforce → Glean | Index account data | MEDIUM | Tyler | `[HIGH]` |
| Crossbeam → Glean | Partner data | MEDIUM | Tyler | `[MEDIUM - access TBD]` |
| Tableau → Glean | Usage data | HIGH | Rob/Tyler | `[MEDIUM]` |
| Built With parser | Structured tech stack | LOW | Charlie | `[HIGH]` |
| Output → Salesforce | Account plan link | LOW | Tom Woodhouse | `[MEDIUM]` |

**Agents to Build:**

| Agent | Platform | Purpose | Complexity | Confidence |
|-------|----------|---------|------------|------------|
| White Space Generator | Claude | Deep Research → template | MEDIUM | `[HIGH]` |
| QA Validator | Claude | Cross-check citations | MEDIUM | `[MEDIUM]` |
| Internal Footprint | Glean | Aggregate internal data | MEDIUM | `[HIGH]` |
| Partner Matcher | Glean | Auto-lookup partners | LOW | `[MEDIUM]` |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation | Confidence |
|------|-------------|--------|------------|------------|
| Glean token limit blocks complex use cases | HIGH | MEDIUM | Route synthesis to Claude | `[HIGH]` |
| No Data Quality Owner designated | **MEDIUM** | **HIGH** | **Gate Phase 2 on governance** | `[HIGH]` |
| Claude API costs exceed budget | MEDIUM | LOW | Set caps, monitor weekly | `[HIGH]` |
| Thomas undermines adoption | LOW | HIGH | Make him co-designer | `[HIGH]` |
| Integration complexity | MEDIUM | MEDIUM | Start with 3 sources, expand later | `[MEDIUM]` |
| Crossbeam access denied | MEDIUM | MEDIUM | Work around with PM requests initially | `[MEDIUM]` |

---

## Cost Estimate

| Item | One-Time | Annual | Notes | Confidence |
|------|----------|--------|-------|------------|
| Glean | $0 | ~$50K | Already licensed | `[HIGH]` |
| Claude API | $0 | ~$5-10K | ~500 account plans/year | `[MEDIUM - estimated]` |
| Tyler/Charlie time | ~200 hours | ~100 hours | Build + maintain | `[MEDIUM - estimated]` |
| Training | ~40 hours | ~20 hours | Initial + refresh | `[MEDIUM]` |
| **Total** | **~240 hours** | **~$60K + 120 hours** | | `[MEDIUM]` |

**ROI Estimate:**
- 100 AEs × 4 hours saved/account × 10 accounts/year = 4,000 hours saved `[MEDIUM - derived]`
- At $75/hour = **$300K annual value** `[MEDIUM - derived]`
- **Payback: <6 months** (assuming governance success) `[MEDIUM - conditional]`

---

## Implementation Phases

### Phase 1: Governance + Foundation (Weeks 1-4)

| Action | Owner | Dependency | Confidence |
|--------|-------|------------|------------|
| Designate Data Quality Owner | Steve/Mikki | None | `[HIGH]` |
| Finalize gold template | Charlie + Chris P | None | `[HIGH]` |
| Grant Crossbeam read access | Partner Ops | None | `[MEDIUM]` |
| Document Deep Research best practices | Matt Lazar | None | `[HIGH]` |

**Exit Criteria:** Data Quality Owner named, template approved

### Phase 2: Core Build (Weeks 5-10)

| Action | Owner | Dependency | Confidence |
|--------|-------|------------|------------|
| Build White Space Generator agent | Charlie | Template approved | `[HIGH]` |
| Build QA Validator agent | Tyler | None | `[MEDIUM]` |
| Index Salesforce in Glean | Tyler | DQO approval | `[HIGH]` |
| Build Internal Footprint agent | Tyler | Glean indexing | `[HIGH]` |

**Exit Criteria:** End-to-end account plan generation working

### Phase 3: Pilot (Weeks 11-14)

| Action | Owner | Dependency | Confidence |
|--------|-------|------------|------------|
| Deploy to champions (Thomas, Matt L, Chris P) | Charlie | Phase 2 complete | `[HIGH]` |
| Collect feedback | Charlie | Pilot running | `[HIGH]` |
| Measure time savings | Charlie | Pilot running | `[MEDIUM]` |
| Iterate on agents | Tyler | Feedback collected | `[HIGH]` |

**Exit Criteria:** Champions endorse rollout

### Phase 4: Rollout (Week 15+)

| Action | Owner | Dependency | Confidence |
|--------|-------|------------|------------|
| Training materials | Charlie | Pilot complete | `[HIGH]` |
| Expand to all strategic AEs | Steve/Rich | Champion endorsement | `[HIGH]` |
| Monitor adoption | Data Quality Owner | Rollout | `[HIGH]` |

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

**Confidence Test [v2.6]:**
- [x] All cost estimates tagged with confidence
- [x] ROI marked as derived, not measured
- [x] Conditional assumptions stated

---

*Generated using PuRDy v2.6 Tech Evaluation with Confidence Tagging*
