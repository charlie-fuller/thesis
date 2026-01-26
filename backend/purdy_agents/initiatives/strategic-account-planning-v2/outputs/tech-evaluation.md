# Tech Evaluation: Strategic Account Planning

**Date**: 2026-01-23
**PRD Reference**: `synthesis-summary-v2.4.md`
**Evaluator**: I.S. Team (Charlie/Tyler)

---

## Recommendation

**Platform/Approach**: **Hybrid - Glean + Claude + Custom Integrations**
**Decision Type**: HYBRID

### Rationale

No single platform meets all requirements. Glean excels at internal data retrieval but hits token limits on complex synthesis. Claude handles deep research and document generation but lacks enterprise data access. The solution is a phased approach: Glean for internal footprint and quick lookups, Claude/Gemini for external research and document generation, with custom integrations bridging data sources into a unified workflow.

---

## Requirements Recap (from PRD)

| Category | Key Requirements |
|----------|------------------|
| **Functional** | White space map generation, partner matching, internal footprint aggregation, QA/validation, strategic alignment research |
| **Non-Functional** | 70-80% time reduction, high accuracy (95%+), AE-friendly interface |
| **Integration** | Salesforce, Crossbeam, Tableau, Gatekeeper, Built With, LinkedIn Sales Navigator |
| **Users** | Enterprise AEs (50-100), BDRs (20-30), occasional leadership access |
| **Constraints** | No dedicated dev team, Mikki's IT/AI resources available, existing Glean investment |

---

## Build vs. Buy Assessment

| Question | Answer | Implication |
|----------|--------|-------------|
| Is this a differentiator for Contentful? | **No** - Internal efficiency tool | Favor BUY/HYBRID |
| What's the TCO over 3 years? | ~$50K Glean + custom work vs. $200K+ full custom build | HYBRID wins |
| Do we have the team to build AND maintain? | **Partial** - Tyler/Charlie can build agents, not full apps | HYBRID appropriate |
| What's our exit strategy if this fails? | Agents are disposable; integrations reversible | Low lock-in risk |

**Decision: HYBRID** - Buy platforms (Glean, Claude), build agents and integrations

---

## Options Evaluated

| Option | Type | Weighted Score | Notes |
|--------|------|----------------|-------|
| **Glean + Claude + Custom** | Hybrid | **78/100** | Selected - Best fit for requirements and constraints |
| Glean Only | Buy | 52/100 | 128K token limit blocks complex synthesis |
| Full Custom Build | Build | 61/100 | No capacity for maintenance; over-engineered |
| Claude Code Only | Buy | 65/100 | No internal data access; manual data gathering remains |
| Salesforce Einstein | Buy | 45/100 | Limited AI capabilities; expensive add-on |

---

## Trade-off Scoring

| Trade-off | Weight (1-10) | Glean+Claude (Selected) | Glean Only | Full Custom |
|-----------|---------------|-------------------------|------------|-------------|
| **Speed vs. Flexibility** | 8 | 4 (balanced) | 5 (fast, limited) | 2 (slow, flexible) |
| **Control vs. Convenience** | 5 | 3 (mostly convenient) | 5 (very convenient) | 1 (full control) |
| **Learning Investment vs. Time-to-Value** | 9 | 4 (moderate learning) | 5 (easy) | 2 (high learning) |
| **Open Standards vs. Proprietary** | 4 | 3 (mixed) | 2 (proprietary) | 5 (open) |
| **Cost Now vs. Cost Later** | 7 | 4 (phased investment) | 5 (low now) | 1 (high now) |
| **Features vs. Simplicity** | 6 | 3 (balanced) | 4 (simple but limited) | 2 (complex) |
| **Generalization vs. Specialization** | 5 | 3 (specialized agents) | 4 (general) | 2 (over-specialized) |
| **Weighted Total** | | **78** | **52** | **61** |

---

## Platform Breakdown

### Tier 1: Glean (Already Owned)

**Best For:**
- Internal footprint queries ("What's our usage at Amazon?")
- Account Navigator / quick lookups
- Simple agent deployment (Alfred V1)
- Self-serve Q&A for field team

**Limitations:**
- 128K token limit = cannot synthesize full account plans
- No direct Salesforce write-back
- Limited external research capability
- Agent complexity ceiling

**Use Cases Assigned:**
| Use Case | Fit | Notes |
|----------|-----|-------|
| Internal footprint lookup | HIGH | Tableau, Salesforce, Gatekeeper access |
| Partner lookup | MEDIUM | Crossbeam data if indexed |
| White space generation | LOW | Token limit blocks complex docs |
| Strategic alignment research | LOW | No external web access |

### Tier 2: Claude / Gemini Deep Research

**Best For:**
- External research (company websites, 10Ks, news)
- Document generation (white space maps, briefs)
- Complex synthesis across sources
- QA/validation of other AI output

**Limitations:**
- No internal Contentful data access
- Requires manual data input
- API costs scale with usage
- No persistent memory between sessions

**Use Cases Assigned:**
| Use Case | Fit | Notes |
|----------|-----|-------|
| White space generation | HIGH | Deep Research + structured output |
| Strategic alignment research | HIGH | 10K analysis, earnings, news |
| QA/validation agent | HIGH | Cross-check citations |
| Internal footprint lookup | LOW | No access to internal systems |

### Tier 3: Custom Integrations (Tyler/Charlie Build)

**Required Integrations:**
| Integration | Purpose | Complexity | Owner |
|-------------|---------|------------|-------|
| Salesforce → Glean | Index account data | MEDIUM | Tyler |
| Crossbeam → Glean | Partner data accessible | MEDIUM | Tyler |
| Tableau → Glean | Usage data surfaced | HIGH | Rob/Tyler |
| Built With parser | Structured tech stack | LOW | Charlie |
| Output → Salesforce | Account plan link | LOW | Tom Woodhouse |

**Custom Agents to Build:**
| Agent | Platform | Purpose | Complexity |
|-------|----------|---------|------------|
| White Space Generator | Claude | Generate from Deep Research | MEDIUM |
| Partner Matcher | Glean | Auto-lookup partners | LOW |
| QA Validator | Claude | Cross-check citations | MEDIUM |
| Internal Footprint | Glean | Aggregate internal data | MEDIUM |

---

## Capability Threshold Check

| Dimension | PRD Requirement | Solution Capacity | At Risk? |
|-----------|-----------------|-------------------|----------|
| Data volume | ~5,000 accounts | Glean: 100K+ records | NO |
| User count | 100-150 users | Glean: unlimited, Claude: API | NO |
| Integration count | 6 systems | Hybrid handles multi-source | NO |
| Workflow complexity | 5-7 step process | Agent chaining supported | NO |
| Token/context needs | Full account plan synthesis | Glean: LIMITED, Claude: OK | GLEAN AT RISK |

**Threshold Concern:** Glean's 128K token limit means complex synthesis must route to Claude. This is acceptable with proper workflow design but adds complexity.

---

## Architecture Recommendation

```
┌─────────────────────────────────────────────────────────────────┐
│                    AE WORKFLOW                                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │ Triage  │───▶│ Research│───▶│ Generate│───▶│ Validate│      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
│       │              │              │              │             │
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
   │              DATA LAYER (Indexed)                    │
   │  ┌────────┐ ┌─────────┐ ┌───────┐ ┌──────────────┐ │
   │  │Salesfce│ │Crossbeam│ │Tableau│ │ External Web │ │
   │  └────────┘ └─────────┘ └───────┘ └──────────────┘ │
   └─────────────────────────────────────────────────────┘
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Glean token limit blocks use cases** | HIGH | MEDIUM | Route complex synthesis to Claude |
| **Claude API costs scale unexpectedly** | MEDIUM | LOW | Set usage caps, monitor weekly |
| **Integration maintenance burden** | MEDIUM | MEDIUM | Document thoroughly, Tyler owns |
| **AE adoption resistance** | MEDIUM | HIGH | Champion-led rollout, show value fast |
| **Data freshness issues** | MEDIUM | MEDIUM | Nightly sync jobs, clear "as of" dates |
| **Gemini/Claude accuracy degrades** | LOW | HIGH | QA agent catches issues, human review |

---

## Implementation Approach

### Phase 1: Foundation (Weeks 1-4)

- [ ] Confirm Crossbeam read access for AEs (Partner Ops)
- [ ] Index Salesforce account data in Glean (Tyler)
- [ ] Create standard white space template (Charlie)
- [ ] Build v1 white space generation prompt for Claude (Charlie)
- [ ] Deploy CSM engagement checklist (Rich)

**Exit Criteria:** AEs can generate white space maps 50% faster using Claude prompt

### Phase 2: Integration (Weeks 5-8)

- [ ] Build Internal Footprint agent in Glean (Tyler)
- [ ] Build QA Validator agent in Claude (Charlie)
- [ ] Index Crossbeam partner data in Glean (Tyler)
- [ ] Build Partner Matcher agent in Glean (Tyler)
- [ ] Integrate Built With data parsing (Charlie)

**Exit Criteria:** End-to-end account plan generation under 2 hours (vs. current 8+)

### Phase 3: Optimization (Weeks 9-12)

- [ ] Build Strategic Alignment agent (10K analysis) (Charlie)
- [ ] Add confidence scores to all agent outputs (Tyler)
- [ ] Create training curriculum for AEs (Charlie)
- [ ] Full rollout to enterprise team
- [ ] Measure and iterate

**Exit Criteria:** 70%+ adoption, 60%+ time reduction verified

---

## Trade-off Summary

| Key Trade-off | Position Taken | Justification |
|---------------|----------------|---------------|
| **Speed vs. Flexibility** | Slightly toward SPEED | AEs need quick wins; can add flexibility later |
| **Control vs. Convenience** | Toward CONVENIENCE | Small team, leverage managed platforms |
| **Cost Now vs. Cost Later** | Phased investment | De-risk with quick wins, scale what works |

---

## Cost Estimate

| Item | One-Time | Annual | Notes |
|------|----------|--------|-------|
| Glean (existing) | $0 | ~$50K | Already licensed |
| Claude API | $0 | ~$5-10K | Based on ~500 account plans/year |
| Tyler/Charlie time | ~160 hours | ~80 hours | Build + maintain |
| Training development | ~40 hours | ~20 hours | Initial + refresh |
| **Total** | **~200 hours** | **~$60K + 100 hours** | |

**ROI Estimate:**
- 100 AEs × 4 hours saved/account × 10 accounts/year = 4,000 hours saved
- At ~$75/hour loaded cost = **$300K annual value**
- **Payback: <6 months**

---

## Open Questions for Implementation

1. **Glean indexing:** Can we index Crossbeam directly, or do we need an intermediate export?
2. **Claude API access:** Do we use Anthropic direct or go through a proxy (security review)?
3. **Salesforce write-back:** Does Tom Woodhouse have capacity to build the account plan link field?
4. **Success metrics ownership:** Who will track and report on adoption and time savings?
5. **Training format:** Live sessions, recorded, or embedded in tool?

---

## Approvals Required

- [ ] Steve Letourneau / Rich - Approve phased approach and mandate template
- [ ] Mikki - Confirm IT/AI team capacity (Tyler allocation)
- [ ] Tom Woodhouse - Confirm Salesforce integration capacity
- [ ] Rob/Justin - Confirm Tableau data accessibility

---

## Comparison to Alternatives

### Why Not Glean Only?

Glean's 128K token limit means it cannot synthesize a complete account plan from multiple sources. Testing shows it handles lookups well but chokes on "generate a white space map for Amazon with all subsidiaries." Claude handles this easily with Deep Research.

### Why Not Full Custom Build?

We don't have the team to build AND maintain a custom application. Tyler and Charlie can build agents and integrations, but a full React app with database, auth, and UI would require dedicated development capacity we don't have. The maintenance burden would be unsustainable.

### Why Not Just Claude/Gemini?

Claude has no access to internal Contentful data (Salesforce, Tableau, Gatekeeper). Every account plan would require manual data gathering and pasting, which defeats the automation goal. Glean's internal data access is essential.

### Why Not Salesforce Einstein?

Salesforce's AI capabilities are nascent for this use case. Einstein can summarize accounts but cannot do the deep external research or sophisticated document generation needed. Also significantly more expensive.

---

## Verdict

**Proceed with Hybrid Approach: Glean + Claude + Custom Integrations**

This recommendation balances:
- **Speed to value** (leverage existing tools)
- **Capability** (Claude for complex synthesis, Glean for internal data)
- **Sustainability** (manageable maintenance burden)
- **Cost** (low incremental investment)

The phased implementation allows for learning and course correction. If Phase 1 doesn't deliver value, we can stop before significant investment. If it succeeds, we have a clear path to scale.

---

*Evaluated using PuRDy v2.4 Tech Evaluation Framework*
