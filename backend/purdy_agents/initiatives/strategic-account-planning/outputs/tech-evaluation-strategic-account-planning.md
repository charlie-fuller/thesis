# Tech Evaluation: Strategic Account Planning

**Date**: 2026-01-23
**PRD Reference**: `prd-strategic-account-planning.md`
**Evaluator**: Charlie Fuller (I.S. Team)

---

## Recommendation

**Platform/Approach**: **Hybrid - Claude/Custom Build + Salesforce Native**
**Decision Type**: Hybrid

### Rationale (2-3 sentences)

Given the complexity of integrating 7+ data sources, the need for sophisticated AI reasoning (QA validation, research synthesis), and the 128K token limit of Glean, a **custom Claude-based solution** provides the flexibility and capability required. Salesforce should remain the system of record with enhanced fields, while Claude handles research automation and synthesis. This approach avoids the "tool graveyard" risk by building on proven infrastructure rather than adding another disconnected point solution.

---

## Options Evaluated

| Option | Type | Weighted Score | Notes |
|--------|------|----------------|-------|
| **Claude/Custom Build + SF Native** | Hybrid | **78** | **Selected** - Best balance of capability and integration |
| **Glean Agent** | Buy | 62 | Token limits, can't do external research, limited integration |
| **Full Custom Application** | Build | 71 | Higher capability but higher maintenance burden |
| **Salesforce-Only Enhancement** | Buy | 55 | Limited AI capability, doesn't solve research problem |

---

## Requirements Recap (from PRD)

| Category | Key Requirements |
|----------|-----------------|
| **Functional** | Automated landscape research, internal footprint aggregation, white space mapping, partner intelligence, standard output generation |
| **Non-Functional** | 90%+ data accuracy, 1-2 hour account plan completion, 80% AE adoption |
| **Integration** | Salesforce (read/write), Tableau, Gatekeeper, Crossbeam, external AI APIs |
| **Users** | 15-20 AEs, supporting CSMs and Sales Ops; permission complexity medium |
| **Constraints** | Governance-first (30 days); 6-week MVP build; existing tool fatigue |

---

## Build vs. Buy Assessment

| Question | Answer | Implication |
|----------|--------|-------------|
| Is this a differentiator for Contentful? | **No** - Account planning is table stakes | Leans Buy |
| What's the TCO over 3 years? | Build: ~$150K initial + $50K/yr. Buy (Glean): ~$0 (already licensed) but limited | Build justified if Glean can't meet requirements |
| Do we have the team to build AND maintain? | **Yes** - I.S. team (Charlie/Tyler) + AI expertise available | Enables Build |
| What's our exit strategy if this fails? | Modular design allows pivoting; Salesforce data persists regardless | Low lock-in risk |

**Build vs. Buy Verdict**: **Hybrid** - Glean alone can't meet requirements (token limits, no external research), but full custom is overkill. Use Claude API for AI layer, Salesforce for data persistence, custom lightweight orchestration.

---

## Trade-off Scoring

| Trade-off | Weight (1-10) | Glean Agent | Claude/Custom Hybrid | Full Custom |
|-----------|---------------|-------------|---------------------|-------------|
| **Speed vs. Flexibility** | 8 | 4 (fast, rigid) | 3 (moderate both) | 2 (slow, flexible) |
| **Control vs. Convenience** | 6 | 2 (convenient, no control) | 4 (balanced) | 5 (full control) |
| **Learning Investment vs. Time-to-Value** | 7 | 5 (low learning) | 3 (moderate) | 2 (high learning) |
| **Open Standards vs. Proprietary** | 5 | 2 (proprietary) | 4 (API-based, portable) | 4 (open) |
| **Cost Now vs. Cost Later** | 7 | 5 (low now) | 3 (moderate now) | 2 (high now) |
| **Features vs. Simplicity** | 6 | 3 (simple, limited) | 4 (balanced) | 5 (feature-rich) |
| **Generalization vs. Specialization** | 5 | 3 (general Q&A) | 4 (specialized for use case) | 5 (fully specialized) |
| **Weighted Total** | | **62** | **78** | **71** |

**Scoring Notes**:
- **Glean** loses on flexibility and control—128K token limit means it can't process full account context; can't do external web research
- **Full Custom** scores high on capability but lower on speed and cost efficiency
- **Hybrid** optimizes for the specific requirements without over-engineering

---

## Capability Threshold Check

| Dimension | PRD Requirement | Glean Capacity | Claude/Custom Capacity | At Risk? |
|-----------|-----------------|----------------|----------------------|----------|
| **Data volume** | 7+ sources, ~100 accounts | Limited (128K tokens) | High (API batching) | Glean at risk |
| **User count** | 15-20 AEs | OK | OK | No |
| **Integration count** | 7 systems | 3-4 max | Unlimited via APIs | Glean at risk |
| **Workflow complexity** | Multi-step research + QA + synthesis | Basic chains only | Complex orchestration | Glean at risk |
| **Compliance needs** | Standard enterprise | OK | OK | No |

**Threshold Verdict**: Glean approaches or exceeds limits on data volume, integration count, and workflow complexity. Claude/Custom has headroom.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **API cost overruns (Claude)** | Medium | Medium | Implement caching, batch processing, cost monitoring |
| **Integration complexity** | Medium | High | Start with 3 core integrations (SF, Gatekeeper, research); add incrementally |
| **Team bandwidth** | Medium | Medium | Leverage existing I.S. capacity; phase delivery |
| **Maintenance burden** | Low | Medium | Modular architecture; document thoroughly |
| **AI accuracy for research** | Medium | High | QA validation layer; human-in-loop for critical fields |

---

## Detailed Option Analysis

### Option A: Glean Agent (NOT RECOMMENDED)

**Pros:**
- Already licensed (no incremental cost)
- Fast to deploy for simple use cases
- Good for internal knowledge Q&A

**Cons:**
- 128K token limit insufficient for full account context
- Cannot perform external web research (subsidiary/tech stack)
- Limited integration capabilities
- Basic workflow chains only
- Prior "simple agent" attempts haven't stuck

**Verdict**: Glean is appropriate for self-serve Q&A, not complex multi-source synthesis. Would become tool #4 in the graveyard.

---

### Option B: Claude/Custom Hybrid (RECOMMENDED)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Account Planning Tool                     │
├─────────────────────────────────────────────────────────────┤
│  Orchestration Layer (Python/Node)                          │
│  - Workflow coordination                                     │
│  - Data aggregation                                          │
│  - Output generation                                         │
├─────────────────────────────────────────────────────────────┤
│  Claude API            │  Salesforce API    │  Other APIs   │
│  - Research synthesis  │  - Account data    │  - Gatekeeper │
│  - QA validation       │  - Write-back      │  - Crossbeam  │
│  - Natural language    │  - Built With      │  - Tableau    │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Sufficient context window for complex synthesis
- Can perform external research with web access
- Flexible integration via APIs
- Modular—can swap components
- Leverages team's existing Claude expertise

**Cons:**
- Requires development effort (~6 weeks)
- API costs (~$500-1000/month estimated)
- Maintenance responsibility

**Verdict**: Best fit for requirements. Balances capability with pragmatism.

---

### Option C: Full Custom Application (NOT RECOMMENDED FOR V1)

**Pros:**
- Maximum flexibility and control
- Could become platform for other use cases
- Full ownership of roadmap

**Cons:**
- Longer development timeline (3-4 months)
- Higher maintenance burden
- Risk of over-engineering for v1 needs
- Delays time-to-value

**Verdict**: Consider for v2 if needs expand significantly. Overkill for current scope.

---

## Implementation Approach

### Phase 1: Governance + Foundation (Weeks 1-4)
- [ ] Data Quality Owner appointed
- [ ] Gold template finalized
- [ ] Built With field categorized in Salesforce
- [ ] API access confirmed (Gatekeeper, Crossbeam)

### Phase 2: Core Build (Weeks 5-10)
- [ ] Salesforce integration (read account data)
- [ ] Claude research agent (landscape + subsidiaries)
- [ ] QA validation layer
- [ ] Internal footprint aggregation (Gatekeeper)
- [ ] Standard output generation (gold template)

### Phase 3: Pilot + Iterate (Weeks 11-14)
- [ ] Deploy to 3 pilot AEs (Thomas, Matt L, Chris P)
- [ ] Collect feedback, measure accuracy
- [ ] Iterate on prompts and data flows
- [ ] Document and prepare for rollout

### Phase 4: Rollout (Week 15+)
- [ ] Training materials created
- [ ] Expand to all strategic AEs
- [ ] Monitor adoption and accuracy metrics

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Claude API costs exceed budget** | Implement aggressive caching; batch similar requests; set hard spending limits |
| **Research accuracy below 90%** | Human-in-loop QA for critical fields; continuous prompt refinement; use Gemini Deep Research for validation |
| **Salesforce integration complexity** | Use existing SF API patterns; leverage Tyler's experience; start read-only |
| **Team capacity constrained** | Phase delivery; leverage existing tools (Claude Code); prioritize ruthlessly |

---

## Open Questions for Implementation

1. **Hosting decision**: Where does the orchestration layer run? (Vercel, AWS Lambda, internal?)
2. **Authentication**: How do AEs access the tool? (Slack bot, web app, Salesforce embedded?)
3. **Crossbeam access**: Can we get API access or do we need PM intermediary workflow?
4. **Cost model approval**: Is $500-1000/month API spend acceptable?

---

## Approvals

- [ ] Requester accepts recommended approach (Claude/Custom Hybrid)
- [ ] I.S. team confirms capacity for 10-week build
- [ ] Budget approval for Claude API costs (~$6-12K/year)
- [ ] Salesforce admin confirms API access and field modifications

---

## Comparison Summary

| Criterion | Glean | Claude/Custom Hybrid | Full Custom |
|-----------|-------|---------------------|-------------|
| Meets functional requirements | ❌ Partial | ✅ Yes | ✅ Yes |
| Time to value | ✅ Fast | ⚠️ Moderate | ❌ Slow |
| Maintenance burden | ✅ Low | ⚠️ Moderate | ❌ High |
| Scalability | ❌ Limited | ✅ Good | ✅ Excellent |
| Cost (3-year TCO) | ✅ Lowest | ⚠️ Moderate | ❌ Highest |
| Risk of becoming "tool #4" | ❌ High | ✅ Low | ⚠️ Medium |

**Final Recommendation**: **Claude/Custom Hybrid** provides the best balance of capability, time-to-value, and risk mitigation for this initiative.

---

*Generated via PuRDy Tech Evaluation Agent*
