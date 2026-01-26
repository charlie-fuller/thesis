# PRD: Strategic Account Planning Automation

**Date**: 2026-01-23
**Author**: Charlie Fuller (I.S. Team)
**Requester**: Steve Letourneau / Massimo (ELT)
**Tier**: ELT Sponsor

---

## Problem Statement

Enterprise AEs spend 4-6+ hours per strategic account gathering data from 7+ fragmented systems (Salesforce, Tableau, Gatekeeper, Crossbeam, LinkedIn, Built With, external AI tools) to build account plans. This manual work reduces client-facing time and produces inconsistent outputs. Three prior tool attempts have failed due to data quality and ownership issues—the underlying problem is an **organizational ownership vacuum**, not a technical gap.

## Current State

### Process Pain Points

| Stage | Current Pain | Time Spent |
|-------|--------------|------------|
| **Landscape Research** | AI tools (ChatGPT) return 10-40% outdated subsidiary/website data | 1-2 hrs |
| **Internal Footprint** | Sites/use cases scattered across QBRs, Gatekeeper, tribal knowledge | 1 hr |
| **White Space Mapping** | No standard template; manual Built With/Wappalyzer verification | 1-2 hrs |
| **Partner Intelligence** | Crossbeam gatekept; AEs lack direct access | 30 min |
| **Usage/Health Data** | Fragmented across 3+ Tableau views; MAPs not available | 30 min |
| **Contact/Org Charts** | LinkedIn gaps (especially EMEA); no systematic capture | 30 min |

### Data Quality Issues (Root Cause)

| System | Issue |
|--------|-------|
| **Salesforce** | "Built With" is an uncategorized blob; account hierarchy inaccurate; opportunity history scattered |
| **Tableau** | 80% of data in one view, 20% requires 2-3 additional views |
| **Gatekeeper** | Good for spaces/content types; no feature/product/front-end visibility |
| **Crossbeam** | Stale relationships; PM gatekeeping; AEs have no direct access |
| **AI Research** | 9/10 subsidiaries obsolete in one test; requires extensive QA |

### Root Cause Analysis

> "The account planning problem isn't data fragmentation—it's an ownership vacuum. Until someone is chartered to own 'account intelligence' as a discipline, every technical solution becomes another silo."

**Evidence**: When asked "Who owns account data quality?" in workshops—silence. This silence predicts tool failure.

## Proposed Solution

**Two-phase approach:**

### Phase 1: Governance Foundation (30 days)
- Establish Data Quality Owner role
- Define "golden" white space template (Nationwide example)
- Categorize Built With data (Front-end, CMS, Commerce, Personalization, Search)
- Establish data entry standards and accountability

### Phase 2: Automated Account Planning Tool
- AI-assisted research with validation layer
- Unified view of account intelligence (internal + external)
- Standard output format aligned to gold template
- Integration with existing systems via APIs

**Why governance first**: Three prior tools failed without it. Tools without ownership become shelfware.

---

## Scope

### In Scope (v1)

- [ ] Standardized white space mapping output (gold template)
- [ ] Automated landscape research with QA validation
- [ ] Internal footprint aggregation (Gatekeeper + Salesforce)
- [ ] Partner intelligence summary (Crossbeam data surfaced)
- [ ] Usage metrics consolidated view
- [ ] Data Quality Owner role definition and charter

### Out of Scope (v1 / Future)

- Technical blueprinting (moved to opportunity stage)
- Real-time data sync (batch refresh acceptable for v1)
- Full org chart automation (manual augmentation expected)
- Net-new account prospecting (focus is existing strategic accounts)
- Mobile interface

---

## Systems & Integrations

| System | Integration Type | Data Flow | Risk Level |
|--------|-----------------|-----------|------------|
| **Salesforce** | API (read/write) | Account hierarchy, contacts, opportunities, Built With | Medium - data quality issues |
| **Tableau** | API or embed | Usage metrics, analytics | Low - read-only |
| **Gatekeeper** | API | Space/content type data | Low - structured data |
| **Crossbeam** | API (via PM) | Partner relationships | High - access restrictions |
| **LinkedIn Sales Nav** | Manual/scrape | Org charts, contacts | High - regional gaps, ToS |
| **Built With/Wappalyzer** | API | Tech stack detection | Low - commodity data |
| **External AI (Gemini Deep Research)** | API | Subsidiary/landscape research | Medium - requires QA layer |

---

## Success Metrics

| Metric | Current | Target | How Measured |
|--------|---------|--------|--------------|
| Time to complete account plan | 4-6 hours | 1-2 hours | Self-reported + tool logging |
| Data accuracy (spot check) | ~60% (AI research) | 90%+ | Quarterly audit of 10 plans |
| Template consistency | 0% (no standard) | 100% | All plans use gold template |
| AE adoption | 0 (no tool) | 80% of strategic AEs | Active users / total AEs |
| Client-facing time | Baseline TBD | +10-15% | Sales Ops tracking |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Data Quality Owner role unfilled** | Medium | High | Identify candidate by Week 2; escalate to Steve if blocked |
| **Thomas undermines adoption** | Low | High | Make him co-designer, not recipient; leverage his AI expertise |
| **Crossbeam access remains gatekept** | Medium | Medium | Escalate to Partnership leadership; build summary view as interim |
| **AI research accuracy insufficient** | Medium | Medium | QA validation layer; human-in-loop for critical fields |
| **Change fatigue from prior tool failures** | High | Medium | Governance-first proves commitment; 10% wins before asking adoption |

---

## Stakeholder Map

| Role | Person(s) | Interest | Influence | Engagement |
|------|-----------|----------|-----------|------------|
| **ELT Sponsor** | Massimo, Steve | Strategic alignment | High | Steering committee |
| **Sales Leadership** | Rich | Visibility, consistency | High | Approve requirements |
| **AEs (Primary Users)** | Matt L, Matt V, Chris P, Joel, Thomas | Time savings | High | Co-design, pilot |
| **Sales Ops** | Chris Baumgartner | Process owner | Medium | Template definition |
| **CSM** | Farsheed | Internal footprint data | Medium | Input on customer knowledge |
| **Partner Team** | PM leadership | Crossbeam access | Medium | Data access negotiation |
| **I.S./AI Team** | Tyler, Charlie, Mikki | Build capability | High | Technical delivery |

---

## Timeline

- **Governance Phase**: 2026-02-01 to 2026-02-28 (4 weeks)
  - Week 1-2: Data Quality Owner identified and chartered
  - Week 3-4: Gold template finalized, Built With categorization complete

- **MVP Build**: 2026-03-01 to 2026-04-15 (6 weeks)
  - Automated landscape research with QA
  - Internal footprint aggregation
  - Standard output generation

- **Pilot Users**: Thomas, Matt Lazar, Chris Powers (3 AEs)
- **Full Rollout**: 2026-05-01 (targeting top 20 strategic accounts first)

---

## Open Questions

1. **Who will be the Data Quality Owner?** (Decision needed by 2026-02-05)
2. **Can we get direct AE access to Crossbeam or do we need PM intermediary permanently?**
3. **What's the platform decision—Glean agent, custom build, or hybrid?** (→ Tech Evaluation)
4. **How do we handle different account types (net-new vs. existing)?** (Proposed: v1 focuses on existing only)
5. **What training resources exist vs. need to be created?**

---

## Approvals Needed

- [x] ELT Sponsor acknowledgment (Steve/Massimo) - Confirmed via workshops
- [ ] Data Quality Owner appointment - **Decision required by 2026-02-05**
- [ ] Platform selection - Pending tech evaluation
- [ ] Security review (if PII/sensitive data flows) - TBD based on architecture
- [ ] Budget approval for build - Feed to Michael's BRD

---

## Appendix: Source Documents

| Document | Location |
|----------|----------|
| Workshop transcripts (4 sessions) | `/strategic-account-planning/transcripts/` |
| Data Hygiene Gap Analysis | `/strategic-account-planning/Data-Hygiene-Gap-Analysis.md` |
| Nationwide White Space (gold template) | Google Sheets (Chris Powers) |
| Amazon Account Plan FY'27 | Google Sheets |
| PuRDy Evaluation v2.4 | `/strategic-account-planning/purdy/evaluation-scores-v2.4.md` |

---

*Generated via PuRDy Discovery Agent*
