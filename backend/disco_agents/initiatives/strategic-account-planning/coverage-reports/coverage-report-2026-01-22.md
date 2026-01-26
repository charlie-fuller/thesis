# Coverage Report: Strategic Account Planning

## Report Date: 2026-01-22
## Sessions Completed: 3 of 6 planned

---

## Coverage Summary

| Category | Status | Confidence |
|----------|--------|------------|
| Problem Definition | **Covered** | High |
| Stakeholder Perspectives | **Covered** | High |
| Requirements | **Partial** | Medium |
| Success Criteria | **Partial** | Low |
| Scope & Boundaries | **Covered** | High |
| Risks | **Partial** | Medium |
| Context | **Covered** | High |

---

## Detailed Coverage Assessment

### Problem Definition
**Status:** Covered
**Confidence:** High

**What we know:**
- Current process is manual and time-consuming (multiple sources: Matt Lazar, Matt Vosberg, Chris Powers)
- AEs spend significant time gathering data from 70-80 places instead of being with clients (Steve Letourneau)
- No consistency across company in account planning approach (Rich)
- Data sources are fragmented across Salesforce, Tableau, BuiltWith, ZoomInfo, ChatGPT, Glean (all workshop participants)
- ZoomInfo data is often obsolete ("nine out of ten were obsolete") - workshop discussion
- ChatGPT standard mode is unreliable; Deep Research mode ~99% accurate (Matt Lazar)
- Crossbeam data is incomplete and sometimes stale (Matt Vosberg)
- Product usage data fragmented across multiple Tableau views (workshop discussion)
- No single comprehensive view of account information exists (multiple sources)

**Gaps:**
- Quantified time currently spent on account planning (hours per account)
- Cost of current inefficiencies in dollar terms

**Source sessions:** Intro transcript, Summary of process transcript, Next steps transcript

---

### Stakeholder Perspectives
**Status:** Covered
**Confidence:** High

**What we know:**

**AEs (Primary Users):**
- Need consolidated, accurate data in one place
- Want to reduce manual verification work
- Currently use ChatGPT Deep Research, BuiltWith, Wappalyzer, ZoomInfo, Salesforce
- Prefer Outreach over Excel for power mapping
- Want gold standard templates (Nationwide whitespace doc, Amazon partner leverage)

**BDRs:**
- Should be able to execute landscape definition at AE level
- Act as resource, AE remains accountable
- Division: "AE above line, BDR below line & wide"

**CSMs:**
- Hold critical internal footprint knowledge
- Currently share via informal Slack/email
- No standardized questionnaire exists
- Best source for usage data and account health

**Sales Engineers:**
- Technical blueprinting should happen at opportunity stage, not account planning
- Need structured handoff from AEs
- AE Scope tool being developed (Michael/Matt/Neha)

**Partner Managers:**
- Required for Crossbeam access (AEs don't have direct access)
- Should contribute proactively to strategic accounts
- Partner Intelligence Request process needed

**Sales Leadership:**
- Want standardization across team
- Goal: 70-80% of time in front of clients
- Need consistency for ELT visibility into accounts

**IT/AI Team:**
- Here to listen and build what sales needs
- Focus on ideal state, not current limitations
- Can deliver quick wins while building toward full vision

**Gaps:**
- Value Engineering team perspective on IVP document process
- Sales Ops perspective on measurement/tracking

**Source sessions:** All three transcripts, Miro Gap Analysis

---

### Requirements
**Status:** Partial
**Confidence:** Medium

**What we know:**

**Functional Requirements:**
- Landscape Definition: Company structure, subsidiaries, digital maturity, industry, end customer type
- Whitespace Mapping: BU-organized (not domain), product columns, status (SOLD/Competitor/Whitespace/Unknown/N/A), CMS current, frontend framework, delivery architecture
- Partner Leverage: Partner account, use cases, stakeholders, role in account, next steps
- Internal Footprint: Brief format - healthy/not, usage up/down, key sites/use cases
- Power Mapping: Simplified - C-Suite + VP level + known champions/detractors, use Outreach not Excel
- Strategic Alignment: 3 Whys framework (Why Now, Why Change, Why Contentful), IVP document output

**Gold Standard Examples Identified:**
- Nationwide Whitespace Doc (whitespace)
- Amazon Account Plan - Partner Leverage tab (partners)
- Amazon Account Plan - Contacts tab (power mapping)
- Signet Exec Brief (IVP/strategic alignment)

**Data Sources by Stage:**
- Landscape: Company About Us, SEC 10-K, D&B, Crunchbase, Deep Research
- Whitespace: BuiltWith, Wappalyzer, manual site inspection
- Partners: Salesforce (RSI/ISV data), Crossbeam (via PMs), BuiltWith
- Internal Footprint: Salesforce, Glean Account Navigator, Gatekeeper, Granulate, CSM input
- Power Mapping: LinkedIn Sales Navigator, ZoomInfo, Outreach
- Strategic Alignment: Deep Research, Glean agents (Account Navigator, Prospector/Alfred V2)

**Gaps:**
- Integration requirements with existing systems not detailed
- Performance requirements (how fast should agents respond?)
- Security/compliance requirements for data handling
- Specific field-level requirements for each template

**Source sessions:** Summary of process transcript, Miro Gap Analysis

---

### Success Criteria
**Status:** Partial
**Confidence:** Low

**What we know:**
- Goal: 70-80% automation of account planning process (Steve Letourneau)
- Goal: 70-80% of AE time in front of clients (Steve Letourneau)
- Qualitative: Less time on data gathering, more time on strategy and action (Rich)
- Qualitative: "Sell more faster" (Mikki)

**Gaps:**
- No baseline measurement of current time spent
- No specific numeric targets for time saved
- No adoption metrics defined
- No timeline for when value should appear
- No measurement method for "time in front of clients"

**Source sessions:** Intro transcript

---

### Scope & Boundaries
**Status:** Covered
**Confidence:** High

**What we know:**

**In Scope:**
- Landscape Definition
- Whitespace Mapping
- Partner Leverage
- Internal Footprint Audit
- Power Mapping (simplified)
- Strategic Alignment

**Out of Scope (Explicitly):**
- Technical Blueprinting (unanimous workshop decision - belongs at opportunity stage)
- Detailed relationship mapping (comes at opportunity stage)
- Economic Buyer/Champion integration in whitespace (Microsoft example discussed but rejected)

**Scope Clarifications:**
- Applies to top 100 accounts initially (ELT commitment)
- Should work for both net new and existing customers (with different data available)
- Commercial accounts should also benefit (even single brand unit = "click of a button")

**Gaps:**
- Exact account criteria for "strategic" designation
- Rollout plan beyond top 100

**Source sessions:** Intro transcript, Summary of process transcript, Miro Gap Analysis

---

### Risks
**Status:** Partial
**Confidence:** Medium

**What we know:**

**Data Quality Risks:**
- ZoomInfo data often outdated
- Crossbeam incomplete (not everyone uses it)
- ChatGPT standard mode unreliable (Deep Research required)
- BuiltWith data is "just a blob" needing parsing

**Adoption Risks:**
- Varying comfort with AI across team
- Need for upskilling/training
- Different people have different processes today

**Technical Risks:**
- Tableau views fragmented (no unified product usage view)
- No direct AE access to Crossbeam
- Platform decision not yet made (Glean vs. Claude vs. other)

**Gaps:**
- Change management approach not discussed
- Political/organizational risks not surfaced
- Fallback plan if automation fails

**Source sessions:** All transcripts, Miro Gap Analysis

---

### Context & Background
**Status:** Covered
**Confidence:** High

**What we know:**
- Initiative is ELT-driven (Massimo brought to ELT, Mikki partnered)
- Aligns to Top Customer Growth strategic priority
- IT/AI team resources allocated to support
- Tyler has existing work (Alfred V1/V2, Account Navigator, Prospector)
- Some teams (West) have been doing this well individually
- This is about standardizing what's been organic/ad-hoc

**Historical Context:**
- Chris Powers had good examples
- Multiple different approaches existed across team
- No previous failed attempts mentioned (this is new initiative)

**Gaps:**
- None significant

**Source sessions:** Intro transcript, Next steps transcript

---

## Emerging Themes

### Theme 1: Trust but Verify
**Finding:** AI tools (ChatGPT, Glean) can do heavy lifting, but output must be verified
**Evidence:** Matt Lazar, Matt Vosberg repeatedly mentioned verification steps; Deep Research improves accuracy to ~99% but still needs citation checking
**Implications:** Automation should include validation steps; training on verification is critical

### Theme 2: Standardization Without Rigidity
**Finding:** Team wants standard templates and processes but needs flexibility for account differences
**Evidence:** "Keep organic" for AE/BDR split; different data availability for net new vs. existing; Outreach preference over rigid Excel
**Implications:** Design for configurability; don't over-engineer rigid workflows

### Theme 3: Data is Scattered but Exists
**Finding:** Most needed data exists somewhere, but is fragmented across many systems
**Evidence:** 70-80 places mentioned; Salesforce, Tableau, BuiltWith, ZoomInfo, Glean, etc. all have pieces
**Implications:** Integration/aggregation is the challenge, not data creation

### Theme 4: Quick Wins Exist
**Finding:** Some improvements can be delivered fast while building toward full vision
**Evidence:** Tyler's existing agents, Starter Prompt Library POC built during meeting, Deep Research adoption is training-only
**Implications:** Phased approach - deliver value early while building comprehensive solution

---

## Tensions & Conflicts

### Tension 1: Automation vs. Human Judgment
- **Perspective A (AEs):** Want data gathered automatically but want to own strategy
- **Perspective B (Leadership):** Want consistency and visibility into accounts
- **Resolution needed:** Define which parts are automated data vs. AE judgment calls

### Tension 2: Comprehensive vs. Fast
- **Perspective A:** Gold standard templates have many fields
- **Perspective B:** Need to move quickly, not spend hours per account
- **Resolution needed:** Define minimum viable fields vs. nice-to-have

### Tension 3: Net New vs. Existing Customers
- **Perspective A:** Process should work for both
- **Perspective B:** Available data is very different (no internal footprint for net new)
- **Resolution needed:** Define variant workflows or handle gracefully

---

## Follow-Up Questions

1. What's the baseline time currently spent per account plan? - Ask Sales Ops
2. What are the specific metrics for success (adoption %, time saved %)? - Ask Steve/Massimo
3. What's the platform decision timeline (Glean vs. other)? - Ask Mikki
4. What training resources already exist we can leverage? - Ask Charlie/Tyler
5. How does Value Engineering want to receive handoff for IVP docs? - Ask Sean Winter

---

## Recommended Next Steps

### Additional Sessions Needed

| Session | Purpose | Attendees | Priority |
|---------|---------|-----------|----------|
| Technical Feasibility Review | Assess what can be automated, build roadmap | Tyler, Rob, Tom, Justin, Charlie | High |
| Data Deep Dive | Inventory data sources, assess quality | Data team, Sales Ops | High |
| Success Metrics Definition | Define baseline, targets, measurement | Steve, Sales Ops | Medium |
| CSM/PM Input | Formalize contribution processes | CSM leadership, Partner team | Medium |

### Specific Follow-Ups
- [ ] Request access to Nationwide Whitespace Doc for template review
- [ ] Get usage stats on existing Glean agents (Account Navigator, Prospector)
- [ ] Clarify timeline for platform decision from Mikki
- [ ] Document current time-per-account-plan baseline (estimate from AEs if no data)

---

## Readiness Assessment

**Ready for synthesis:** Almost

**Rationale:**
- Problem definition is solid
- Stakeholder perspectives well-captured
- Scope is clear
- Requirements are mostly known but need technical validation
- Success criteria need strengthening (metrics)
- Some tensions need resolution decisions

**Estimated sessions remaining:** 2-3 (Technical Feasibility, Success Metrics, Validation)

**Recommendation:** Proceed with draft synthesis, flag areas needing confirmation. Use synthesis draft to structure remaining sessions.

---

*Generated using PuRDy v2.0 Coverage Tracker*
