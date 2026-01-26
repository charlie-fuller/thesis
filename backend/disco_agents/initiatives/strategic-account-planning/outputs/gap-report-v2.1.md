# Gap Report: Strategic Account Planning v2.1

## Summary

Discovery sessions provided strong coverage of problem definition, stakeholder perspectives, and scope. The primary gaps are in success metrics (no baseline measurements), specific technical requirements for integrations, and formalized processes for cross-functional handoffs (CSM, Partner, Value Engineering). The synthesis is sufficient to begin Phase 1 quick wins while gathering remaining data for later phases.

---

## Critical Gaps

| Gap | Impact | Recommended Action | Owner |
|-----|--------|-------------------|-------|
| No baseline measurement of time-per-account-plan | Cannot measure improvement; cannot prove ROI | Survey AEs for estimates; implement simple time tracking for 2 weeks | Sales Ops |
| Platform decision pending (Glean vs. other) | Architectural uncertainty; may build on wrong foundation | Request decision timeline from Mikki; assume Glean for now given investment | Mikki |
| Specific Tableau fields needed undefined | Cannot build unified dashboard or agent without knowing what to pull | Working session with 2-3 AEs + BI team to document requirements | AE team + BI |
| Value Engineering handoff process unknown | May build wrong IVP output format | 30-min interview with Sean Winter | Charlie/Chris |

---

## Noted Gaps (Non-Critical)

| Gap | Impact | Recommended Action | Owner |
|-----|--------|-------------------|-------|
| "Strategic account" criteria unclear | Unclear rollout scope beyond top 100 | Clarify with Steve/Rich; likely tier-based | Sales Leadership |
| Commercial account variant not designed | Can't extend solution to broader team | Defer; focus on strategic first, adapt later | Future |
| Training curriculum not scoped | Adoption may suffer without upskilling | Chris has draft curriculum; schedule beta test | Charlie |
| Change management approach undocumented | Risk of "this is how I've always done it" resistance | Include in rollout plan; show time savings | Chris B |

---

## Unresolved Tensions

| Tension | Options | Recommendation | Decision Needed From |
|---------|---------|----------------|---------------------|
| How standardized should prompts be? | A) Strict library B) Starter + freestyle C) No library | **B: Starter prompts for onboarding, advanced users freestyle** - balances consistency with Thomas's "prompting is the past" view | Tyler to implement; Sales Leadership to endorse |
| Net new vs. existing customer workflows | A) Same template, different fields populated B) Separate templates C) Conditional logic | **A: Same template, graceful degradation** - simpler to maintain; already acknowledged different data availability | Sales Leadership |
| Where does account plan live? | A) Excel/Sheets B) Salesforce object C) Glean output D) All of above | **D: Template in Sheets/Excel for now, eventual Salesforce object** - "Salesforce is the only thing for them internally" but object requires more work | Tom Woodhouse for feasibility |

---

## Thin Coverage Areas

| PRD Section | Confidence | What's Missing | Suggested Action |
|-------------|------------|----------------|------------------|
| Success Metrics (2.2) | Low | No baseline data; targets are aspirational | Sales Ops survey + 2-week time tracking |
| Non-Functional Requirements | Medium | Performance expectations guessed; security not discussed | Technical feasibility session |
| Integration Requirements | Low | How agents connect to data sources not detailed | Data deep dive with Rob/Justin |
| CSM/PM Contribution Process | Medium | Conceptually agreed but not designed | Process design session |

---

## Action Items (Tiered)

### Immediate (This Week)

| Action | Owner | Deliverable |
|--------|-------|-------------|
| Publish Deep Research starter prompts to team | Tyler | Prompt library (v1) in Replit app |
| Finalize Nationwide Whitespace template as standard | Chris Powers | Documented template with column definitions |
| Request platform decision timeline from Mikki | Charlie | Decision date committed |
| Draft CSM contribution questionnaire | Charlie | Questionnaire document (5-10 questions) |
| Request access to gold standard docs (Nationwide, Amazon) | Chris B | Links documented in PRD |

### Short-Term (2-4 Weeks)

| Action | Owner | Deliverable | Prerequisites |
|--------|-------|-------------|---------------|
| Conduct baseline survey of AEs on time-per-plan | Sales Ops | Baseline metrics report | Survey questions drafted |
| Technical feasibility review session | Tyler, Rob, Tom, Justin | Feasibility assessment, impact/effort matrix | All transcripts shared with tech team |
| Data deep dive: Salesforce/Tableau field inventory | Rob, Justin | Data inventory with field locations, quality notes | AE input on what fields needed |
| Interview Sean Winter on IVP handoff | Charlie | IVP process documentation | N/A |
| Design Internal Footprint Agent v1 | Tyler | Agent specification | Data inventory complete |

### Medium-Term (1-2 Months)

| Action | Owner | Deliverable | Prerequisites |
|--------|-------|-------------|---------------|
| Build unified Tableau dashboard | BI Team | Single dashboard with all usage metrics | Field requirements defined |
| Implement Internal Footprint Agent | Tyler | Working Glean agent | Data accessible in Glean |
| Pilot AI fluency training | Charlie | Training pilot with 5 AEs | Curriculum finalized |
| Design Partner Intelligence Agent | Tyler | Agent specification | Partner team cooperation, clean data source |
| Validation workshop with AEs | Chris B | Validated PRD, adjusted priorities | Draft solutions demonstrated |

### Before Full Implementation

| Gate | Criteria | Owner |
|------|----------|-------|
| Baseline established | Time-per-plan measured for at least 10 accounts | Sales Ops |
| Platform decision made | Glean confirmed or alternative selected | Mikki |
| Data accessibility confirmed | Key fields accessible via Glean or API | Rob/Justin |
| Quick wins adopted | Prompt library + template in active use by 5+ AEs | Tyler/Chris Powers |
| Stakeholder buy-in | Steve/Rich approve final PRD and priorities | Sales Leadership |

---

## Recommended Specialized Analyses

Based on discovery findings, the following specialized lens analyses would add value:

### Data Quality Analysis (Recommended - Produce Now)
**Rationale:** Data issues were discussed in 5+ sessions; cited as major blocker to automation
**Audience:** Data team (Rob, Justin), IT, Sales Ops
**Status:** Produced as separate document (data-quality-analysis-v2.1.md)

### People & Process Recommendations (Recommended - Produce Now)
**Rationale:** Several non-technical process changes identified (CSM questionnaire, AE/BDR split)
**Audience:** Sales Leadership, Field Teams
**Status:** Captured in PRD Section 4; can be extracted if needed

### Technical Implementation Roadmap (Defer)
**Rationale:** Needs technical feasibility session first
**Audience:** IT/AI Team
**Status:** Defer until after technical feasibility review

---

*Generated using PuRDy v2.1 Synthesizer with enhanced tiered action items*
