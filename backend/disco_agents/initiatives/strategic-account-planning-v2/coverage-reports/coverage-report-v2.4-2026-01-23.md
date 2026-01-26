# Coverage Report: Strategic Account Planning

**Version:** v2.4
**Generated:** 2026-01-23
**Initiative:** Strategic Account Planning Process Improvement
**Sessions Analyzed:** 7 transcripts from 2026-01-16

---

## Executive Summary

Discovery is **substantially complete** for the core problem definition and desired outcomes. The workshop sessions produced rich process documentation and clear articulation of the ideal state. However, critical gaps remain in technical feasibility, data architecture, and success metrics that need addressing before PRD finalization.

**Overall Coverage:** 75%
**Ready for Synthesis:** Yes, with caveats noted below

---

## Coverage by PRD Section

### 1. Problem Definition

| Item | Coverage | Source | Notes |
|------|----------|--------|-------|
| Current account planning process | **COVERED** | Working Session 1, Summary of Process | End-to-end walkthrough documented |
| Pain points by stage | **COVERED** | Session 2, Working Session 1 | ChatGPT inaccuracy, manual validation, no standardization |
| Time spent manual vs. strategic | **PARTIAL** | Intro Session | "70-80% manual" stated but not quantified |
| Data sources and quality | **COVERED** | All sessions | Detailed inventory: Salesforce, Crossbeam, Tableau, Gatekeeper, ZoomInfo, Built With |
| Tools currently in use | **COVERED** | Session 2, Working Session 1 | ChatGPT, Gemini Deep Research, Glean, Sales Navigator |

### 2. Stakeholder Perspectives

| Stakeholder | Coverage | Key Insights |
|-------------|----------|--------------|
| AE (Primary Users) | **COVERED** | Matt Lazar, Matt Vosberg, Chris Powers, Thomas - detailed process input |
| BDR | **PARTIAL** | Joel mentioned; division of labor discussed but not standardized |
| CSM | **COVERED** | Farsheed; critical for internal footprint, informal engagement flagged |
| Sales Engineer | **PARTIAL** | Technical blueprinting moved to opportunity stage |
| Solution Strategist | **COVERED** | Moran; technical assessment process, AE Scope tool |
| Partner Manager | **PARTIAL** | Gatekeepers to Crossbeam; no direct interview |
| Sales Leadership | **COVERED** | Steve, Rich - clear vision for 70-80% automation |
| IT/AI Team | **COVERED** | Mikki, Tyler, Rob, Tom, Justin - listening mode, ready to build |

**Conflicting Needs Surfaced:**
- Thomas: "Danger in automation if AEs just trust AI without verifying"
- Chris Powers: "Don't overload with data - keep it simple for leaders"
- Matt Vosberg: "Balance between comprehensive data and going blind staring at it"

### 3. Requirements

| Category | Coverage | Details |
|----------|----------|---------|
| **Ideal state account plan structure** | **COVERED** | Nationwide white space map = gold standard |
| **Data elements per stage** | **COVERED** | Detailed column requirements documented |
| **Automation candidates** | **COVERED** | Doc gen, QA agents, pattern recognition, partner matching |
| **Integration requirements** | **PARTIAL** | Systems identified but integration paths not scoped |
| **Performance/latency requirements** | **MISSING** | Not discussed |
| **Training/adoption requirements** | **PARTIAL** | "Upskilling" mentioned; no concrete plan |

### 4. Success Criteria

| Item | Coverage | Notes |
|------|----------|-------|
| 70-80% automation goal | **COVERED** | Stated by Steve, reinforced throughout |
| "More time with clients" | **COVERED** | Qualitative outcome clear |
| Specific metrics | **MISSING** | No time-saved targets, adoption rates defined |
| Baseline measurements | **MISSING** | Current time spent not quantified |

### 5. Scope

| Item | Coverage | Notes |
|------|----------|-------|
| In scope stages | **COVERED** | Landscape → White Space → Partner → Internal Footprint → Power Mapping → Strategic Alignment |
| Out of scope | **COVERED** | Technical Blueprinting (moved to opportunity stage) |
| Net new vs. existing customers | **COVERED** | Both; different depth but same structure |
| Which accounts | **PARTIAL** | "Top 100" mentioned; criteria not defined |

### 6. Risks

| Risk Category | Coverage | Risks Identified |
|---------------|----------|------------------|
| Data quality | **COVERED** | ZoomInfo outdated, Crossbeam incomplete, ChatGPT inaccurate |
| AI accuracy | **COVERED** | "Standard ChatGPT unreliable," deep research better |
| Adoption/training | **PARTIAL** | Flagged but no mitigation plan |
| Change management | **MISSING** | Not discussed |
| Platform selection | **MISSING** | Glean vs. Claude vs. custom not decided |

### 7. Context & Background

| Item | Coverage | Notes |
|------|----------|-------|
| ELT priority alignment | **COVERED** | Top Customer Growth (Massimo's priority) |
| Executive sponsor vision | **COVERED** | Steve clear on "AI should make us efficient" |
| Previous attempts | **PARTIAL** | EMEA mentioned (Phil's work); US varies by rep |
| Related initiatives | **PARTIAL** | Glean agents, AE Scope tool mentioned |

---

## Opportunities Flagged

### High-Value Automation Opportunities

1. **White Space Map Generation**
   - Deep Research → structured output → validation
   - "If we can get 99% from deep research and have QA agents..."
   - Estimated impact: HIGH (used for every account)

2. **Partner Matching Agent**
   - Auto-lookup against Crossbeam + partner spreadsheet
   - Slack notification to partner channel
   - Estimated impact: MEDIUM (currently manual Salesforce lookup)

3. **Internal Footprint Aggregation**
   - Surface from Salesforce, Tableau, Gatekeeper
   - Single view vs. "go to 4-5 different places"
   - Estimated impact: HIGH (data exists but fragmented)

4. **QA/Validation Agents**
   - AI validating AI output
   - Confidence scores on citations
   - Estimated impact: HIGH (addresses trust problem)

5. **Strategic Alignment Research**
   - Glean Account Navigator + Gemini Deep Research
   - 10K analysis, earnings reports, strategic priorities
   - Estimated impact: MEDIUM (already working reasonably well)

### Process Standardization Opportunities

1. **Standard White Space Template**
   - Nationwide format as gold standard
   - Add: MAPs column, front-end/hosting, current spend

2. **CSM Engagement Checklist**
   - Formal questions for internal footprint
   - Currently "Slack messages, informal conversations"

3. **AI Literacy Training**
   - "Cognitive shifts" curriculum (Charlie has this)
   - Shadow sessions with Thomas (comfortable with AI)

---

## Contradictions Surfaced

| Topic | Position A | Position B | Resolution Needed |
|-------|-----------|-----------|-------------------|
| Prompt library | Tyler: "Worth exploring" | Thomas: "Prompting is the past, just talk to AI" | Hybrid: starter library + fluency training |
| Data depth | Moran: "Need technical risk assessment" | Matt V: "Don't go blind with too many fields" | Phase approach: core fields now, enrichment later |
| Power mapping | Full org chart | C-Suite only | Decided: C-Suite for planning, full map for opportunities |
| Standardization | Steve: "One way everyone knows" | Thomas: "Should be organic, AE accountable" | Balance: standard output, flexible process |

---

## Gaps Requiring Follow-Up

### Critical (Block PRD Finalization)

1. **Technical Feasibility Review** (Session 3 - Pending)
   - What can we deliver quickly vs. what needs more work?
   - Data integration challenges?
   - Agent architecture recommendations?

2. **Data Deep Dive** (Session 4 - Pending)
   - Where does each data element live?
   - Quality/freshness of each source?
   - What integrations exist or are needed?

3. **Success Metrics Definition**
   - Baseline time spent today?
   - Target time reduction?
   - Adoption rate expectations?

### Important (Strengthen PRD)

4. **CSM/Partner Manager Input** (Session 5 - Pending)
   - Formal process for sharing account knowledge?
   - What data do they have that isn't leveraged?

5. **Platform Decision**
   - Glean (128k token limit) vs. Claude vs. custom?
   - Who decides? (Mikki/IT)

6. **Account Criteria**
   - Top 100? All enterprise? Commercial?
   - Different templates for different tiers?

---

## Stakeholder Power Map

| Stakeholder | Power | Influence | Disposition | Notes |
|-------------|-------|-----------|-------------|-------|
| Steve Letourneau | HIGH | HIGH | Champion | Driving initiative, committed ELT time |
| Massimo | HIGH | HIGH | Sponsor | ELT priority, provided resources |
| Mikki | HIGH | MEDIUM | Supportive | IT/AI team lead, enabling resources |
| Rich | MEDIUM | HIGH | Champion | Day-to-day sales leadership |
| Chris Powers | LOW | HIGH | Champion | Gold standard examples, Gemini expertise |
| Thomas | LOW | MEDIUM | Cautious | Valuable skeptic - "danger in automation" |
| Matt Vosberg | LOW | MEDIUM | Supportive | Practical process input |
| Matt Lazar | LOW | MEDIUM | Supportive | Deep Research advocate |

---

## Hypothesis Validation

| Hypothesis | Status | Evidence |
|------------|--------|----------|
| AEs spend too much time on manual data gathering | **VALIDATED** | "70-80% manual work," multiple testimonies |
| No standardized account plan format exists | **VALIDATED** | "Everyone has different way," Miro vs. Excel debate |
| ChatGPT provides unreliable research | **VALIDATED** | J&J obsolete subsidiaries, "trust but verify" |
| Deep Research significantly improves accuracy | **PARTIALLY VALIDATED** | Matt Lazar: "99% accurate," but still needs QA |
| Internal data is fragmented across systems | **VALIDATED** | Tableau, Gatekeeper, Salesforce, "4-5 places" |
| CSM knowledge is underutilized | **VALIDATED** | "Informal Slack messages," no formal process |

---

## Recommended Next Steps

1. **Immediate (This Week)**
   - Assemble gold standard template from examples
   - Schedule Technical Feasibility Review (Session 3)
   - Schedule Data Deep Dive (Session 4)

2. **Short-Term (Next 2 Weeks)**
   - Prototype white space generation agent
   - Define success metrics with Steve/Rich
   - Complete CSM/Partner Manager interviews

3. **Validation Session (Session 6)**
   - Present synthesized PRD
   - Validate priorities
   - Agree on MVP scope

---

*Generated using PuRDy v2.4 Coverage Tracker*
