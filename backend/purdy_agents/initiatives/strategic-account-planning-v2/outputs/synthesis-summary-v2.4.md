# Synthesis Summary: Strategic Account Planning
## v2.4 Analysis

**Initiative:** Strategic Account Planning Process Improvement
**Sponsor:** Steve Letourneau / Massimo (ELT)
**Date:** 2026-01-23
**Status:** Discovery 75% Complete - Ready for Technical Feasibility Review

---

## 1. Initiative Overview

### The Problem Statement

Contentful's AEs spend 70-80% of their time on manual data gathering for account planning instead of meeting with customers. Account plan formats vary by rep, data lives in 70-80 different locations, and AI tools (when used) produce unreliable output requiring extensive manual validation.

### The Vision

A standardized account planning process where AI handles 70-80% of data gathering, enabling AEs to focus on strategy and customer relationships. One-click generation of account plans that meet a consistent quality standard.

### Strategic Alignment

- **ELT Priority:** Top Customer Growth
- **FY27 Tie-In:** Enterprise adoption, accelerating customer deployment
- **Executive Sponsor:** Massimo (provided IT/AI resources), Steve Letourneau (day-to-day champion)

---

## 2. Current State Analysis

### Process Stages (As Documented)

| Stage | Current Process | Key Pain Points |
|-------|-----------------|-----------------|
| **Landscape Definition** | ChatGPT/Gemini Deep Research → manual validation → Excel | Inaccurate AI output, no standard format |
| **White Space Mapping** | Manual site crawling, Built With, Wappalyzer | Time-consuming, varies by rep |
| **Partner Leverage** | Salesforce lookup → Crossbeam (via PM) → partner outreach | No direct Crossbeam access, incomplete data |
| **Internal Footprint** | Salesforce + Tableau + Gatekeeper + CSM conversations | Fragmented data, informal CSM engagement |
| **Power Mapping** | LinkedIn Sales Navigator + educated guesses | No systematic process, C-Suite focus decided |
| **Strategic Alignment** | Gemini Deep Research, Glean Account Navigator | Working reasonably well with good prompts |
| **Technical Blueprinting** | Moved to opportunity stage | Out of scope for account planning |

### Tools Currently in Use

| Tool | Purpose | Effectiveness |
|------|---------|---------------|
| ChatGPT | Research, landscape mapping | LOW - "generic unuseful responses" |
| Gemini Deep Research | Strategic alignment, landscape | HIGH - "99% accurate" with good prompts |
| Glean Account Navigator | Account research, strategic selling | MEDIUM - useful but limited |
| LinkedIn Sales Navigator | Power mapping, contact research | MEDIUM - gaps in EMEA |
| Salesforce | CRM, partner data, opportunities | MEDIUM - data exists but scattered |
| Crossbeam | Partner mapping | LOW access - gated through PMs |
| Tableau | Usage data, metrics | MEDIUM - navigation difficult |
| Gatekeeper | Product usage | LOW - limited visibility |
| Built With | Tech stack detection | MEDIUM - blob of data, not structured |

### Data Sources Inventory

| Data Element | Source(s) | Quality | Accessibility |
|--------------|-----------|---------|---------------|
| Subsidiaries | ChatGPT, ZoomInfo, Salesforce | LOW | Easy |
| Tech stack | Built With, Wappalyzer, manual | MEDIUM | Easy |
| Partner relationships | Crossbeam | MEDIUM | Restricted |
| Internal footprint | Salesforce, Gatekeeper, Tableau | MEDIUM | Fragmented |
| Usage/MAPs | Tableau, Gatekeeper | MEDIUM | Difficult |
| Strategic priorities | 10K, earnings, news | HIGH | Requires research |
| Contacts/Org charts | Sales Navigator, ZoomInfo | MEDIUM | Easy |
| Customer health | CSM knowledge, Gainsight | MEDIUM | Informal |

---

## 3. Desired Future State

### The Gold Standard: Nationwide White Space Map

Based on workshop consensus, the ideal account plan format includes:

| Column | Description | Source |
|--------|-------------|--------|
| Business Unit/LOB | Logical groupings within account | Research |
| Web Domain | Primary website for BU | Research |
| CMS | Current content management system | Built With + validation |
| Personalization | Current personalization tool | Research |
| A/B Testing | Current testing platform | Research |
| Commerce | E-commerce platform if applicable | Research |
| Mobile App | Mobile presence | Research |
| Knowledge Base | Support/docs platform | Research |
| Partner Portal | B2B portal if applicable | Research |
| Front End | Framework (React, Angular, Next.js) | Built With |
| MAPs | Monthly Active Profiles (personalization sizing) | New - requires tool |
| Current Spend | Contentful revenue from BU | Salesforce |
| SI Partner | System integrator relationship | Crossbeam + PM |
| ISV Partner | Technology partner relationship | Crossbeam + PM |
| Contentful Status | Won/Lost/Prospect | Salesforce |

### Process Simplification Decisions

1. **Landscape Definition + White Space Mapping = MERGED** (same artifact)
2. **Partner Leverage = MOVED UP** (pair with white space)
3. **Technical Blueprinting = OUT OF SCOPE** (opportunity stage)
4. **Power Mapping = SIMPLIFIED** (C-Suite focus for planning)

---

## 4. Gap Analysis

### Critical Gaps (Must Address)

| Gap | Impact | Recommended Solution |
|-----|--------|---------------------|
| No standard template | Every rep does it differently | Mandate Nationwide format |
| ChatGPT inaccuracy | Manual validation required | Use Deep Research + QA agents |
| Crossbeam access | PM bottleneck | Grant AE read access |
| Fragmented internal data | 4-5 systems to check | Build aggregation view |
| No success metrics | Can't measure improvement | Define baseline + targets |

### Important Gaps (Should Address)

| Gap | Impact | Recommended Solution |
|-----|--------|---------------------|
| Informal CSM engagement | Knowledge not captured | Create standard checklist |
| No prompt library | Inconsistent AI usage | Build agent workflows instead |
| MAPs data unavailable | Can't size personalization opps | Integrate Sunrush or similar |
| Training gaps | AI literacy varies | Offer cognitive shifts course |

### Nice-to-Have Gaps (Could Address)

| Gap | Impact | Recommended Solution |
|-----|--------|---------------------|
| Miro vs. Excel debate | Tool fragmentation | Standardize on Excel, link Miro |
| Built With blob format | Unstructured data | Parse into specific columns |
| Sales Navigator EMEA gaps | Incomplete org charts | Accept limitation, use alternatives |

---

## 5. Stakeholder Analysis

### Decision Makers

| Name | Role | Position | Engagement Strategy |
|------|------|----------|---------------------|
| Massimo | ELT Sponsor | Committed | Keep informed, celebrate wins |
| Steve Letourneau | Sales Leadership | Champion | Co-design, get sign-off |
| Mikki | IT/AI Lead | Supportive | Regular check-ins, resource allocation |
| Rich | Sales Leadership | Champion | Validate with field reality |

### Key Influencers

| Name | Role | Position | Engagement Strategy |
|------|------|----------|---------------------|
| Chris Powers | AE | Champion | Use his examples as gold standard |
| Thomas | AE | Cautious | Address automation concerns directly |
| Matt Vosberg | AE | Supportive | Practical testing partner |
| Matt Lazar | AE | Supportive | Deep Research advocate |
| Moran | Solution Strategist | Supportive | Technical assessment liaison |

### Skeptic Management

**Thomas raised valid concerns:**
> "There's a danger if you just click a button and trust data without verifying"

**Mitigation:**
- Build confidence scores into agent output
- Keep human validation step
- Position AI as "80% starting point, not 100% answer"
- Involve Thomas in testing to convert skeptic to advocate

---

## 6. Recommendations

### Tier 1: Quick Wins (Weeks 1-4)

| Recommendation | Owner | Effort | Impact |
|----------------|-------|--------|--------|
| **Standardize white space template** | Charlie/Tyler | LOW | HIGH |
| **Create CSM engagement checklist** | Rich + CSM Lead | LOW | MEDIUM |
| **Grant AE Crossbeam read access** | Partner Ops | LOW | MEDIUM |
| **Document Deep Research best practices** | Matt Lazar + Chris Powers | LOW | MEDIUM |

### Tier 2: Build Phase (Weeks 5-8)

| Recommendation | Owner | Effort | Impact |
|----------------|-------|--------|--------|
| **White space generation agent** | Tyler/Charlie | MEDIUM | HIGH |
| **Internal footprint aggregation view** | Rob/Tom Woodhouse | MEDIUM | HIGH |
| **QA/validation agent** | Tyler | MEDIUM | HIGH |
| **Define success metrics + baseline** | Steve + Analytics | LOW | HIGH |

### Tier 3: Scale Phase (Weeks 9-12)

| Recommendation | Owner | Effort | Impact |
|----------------|-------|--------|--------|
| **Partner matching automation** | Tyler | MEDIUM | MEDIUM |
| **Strategic alignment agent (10K analysis)** | Charlie | MEDIUM | MEDIUM |
| **Training rollout (cognitive shifts)** | Charlie | MEDIUM | MEDIUM |
| **Pattern recognition by use case** | Data team | HIGH | MEDIUM |

---

## 7. Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Deep Research accuracy degrades | LOW | HIGH | Multiple validation sources |
| Integration complexity underestimated | MEDIUM | MEDIUM | Spike first, estimate after |
| Glean token limits constrain use cases | MEDIUM | LOW | Use Claude for complex analysis |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Template becomes checkbox exercise | MEDIUM | HIGH | Tie to reviews, make it useful |
| AEs don't adopt new tools | MEDIUM | HIGH | Champions lead rollout |
| Scope creep into opportunity stage | MEDIUM | MEDIUM | Hard scope boundaries |
| IT priorities shift | LOW | HIGH | Mikki commitment documented |

### External Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI tool pricing changes | LOW | MEDIUM | Multi-tool strategy |
| Data source APIs change | LOW | LOW | Abstraction layer |

---

## 8. Success Metrics (Proposed)

### Quantitative

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Time to create account plan | TBD (measure now) | -60% | Self-reported + sampling |
| % of accounts with standardized plan | ~10% (estimate) | 80% | Audit |
| Agent usage rate | 0 | 70% of account plans | Glean analytics |
| Data accuracy (spot check) | TBD | 95% | Monthly sampling |

### Qualitative

| Metric | Measurement Method |
|--------|-------------------|
| AE satisfaction with tools | Quarterly survey |
| Leadership confidence in account data | Stakeholder interviews |
| Time spent with customers vs. admin | Self-reported |

---

## 9. Implementation Roadmap

```
Week 1-2: Foundation
├── Finalize template standard
├── Document current state baseline
├── Technical feasibility review (Session 3)
└── Data deep dive (Session 4)

Week 3-4: Quick Wins
├── Deploy template
├── CSM checklist rollout
├── Crossbeam access granted
└── Best practices documentation

Week 5-8: Build Phase
├── White space agent development
├── Internal footprint aggregation
├── QA agent development
└── Pilot with champion AEs

Week 9-12: Scale Phase
├── Full rollout to enterprise team
├── Training program launch
├── Partner automation live
└── Success measurement + iteration
```

---

## 10. Open Questions for Validation Session

1. **Template Mandatory?** Will leadership mandate the standard template, or is it optional?
2. **Account Scope?** Top 100 only, or all enterprise, or including commercial?
3. **Platform Decision?** Glean primary, Claude for complex, or custom build?
4. **Success Owner?** Who owns the success metrics and ongoing measurement?
5. **Change Management?** How will we handle AEs who don't adopt?

---

## 11. Appendix: Source Documents

### Transcripts Analyzed
1. Strategic Account Plan - intro (2026-01-16)
2. Strategic Account Plan - working session 1 (2026-01-16)
3. Strategic Account Plan - session 2 (2026-01-16)
4. Strategic Account Plan - summary of process (2026-01-16)
5. Strategic account planning next steps with Chris (2026-01-16)
6. Strategic account planning and AI research prompt standardization (2026-01-16)
7. Top customer growth strategy session (2026-01-16)

### Key Artifacts Referenced
- Nationwide White Space Map (Chris Powers) - Gold Standard
- Amazon Account Plan (Matt Lazar/Joel) - Complex Example
- Signet Exec Brief (IVP Document) - 3 Whys Framework
- J&J Process Document (Matt Vosberg) - Research Workflow

---

*Synthesized using PuRDy v2.4 Methodology*
*"Would McKinsey charge $500K for this output?" - 105% Quality Standard*
