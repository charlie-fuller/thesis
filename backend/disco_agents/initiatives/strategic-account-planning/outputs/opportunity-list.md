# Opportunity List: Strategic Account Planning

## Opportunity Identification Method
Opportunities identified from:
- Pain points surfaced in workshop sessions
- Gap analysis from Miro board review
- Countermeasures proposed during root cause analysis
- Technical capabilities already in development (Tyler's agents)

---

## Opportunity Summary

| # | Opportunity | Impact | Effort | Priority Index | Category |
|---|-------------|--------|--------|----------------|----------|
| 1 | Glean Account Navigator Enhancement | 4 | 2 | 16 | Quick Win |
| 2 | Standard Template Adoption (Nationwide) | 4 | 1 | 20 | Quick Win |
| 3 | Deep Research Training & Adoption | 3 | 1 | 15 | Quick Win |
| 4 | Alfred V2 Agent Deployment | 4 | 2 | 16 | Quick Win |
| 5 | BuiltWith Data Parsing Automation | 3 | 2 | 12 | Quick Win |
| 6 | CSM Brief Template & Process | 3 | 2 | 12 | Quick Win |
| 7 | Partner Intelligence Request Process | 3 | 2 | 12 | Quick Win |
| 8 | QA Agent for AI Output Validation | 4 | 3 | 12 | Strategic |
| 9 | Unified Account Dashboard | 5 | 4 | 10 | Strategic |
| 10 | Partner Mapping Agent | 3 | 3 | 9 | Backlog |
| 11 | Product Usage Dashboard Consolidation | 4 | 4 | 8 | Strategic |
| 12 | Full 70-80% Automation Goal | 5 | 5 | 5 | Major Bet |

---

## Detailed Opportunity Analysis

### Opportunity 1: Glean Account Navigator Enhancement

**Description:** Enhance existing Glean Account Navigator agent to pull more comprehensive data and format output for account planning use cases.

**Impact: 4** - High
- Affects all AEs doing account planning (~20+ people)
- Used weekly/monthly per account
- Tyler already has V1 working; enhancement builds on proven foundation
- Directly addresses "data scattered" problem

**Effort: 2** - Light
- Agent already exists; enhancement, not new build
- Tyler has expertise to execute
- 2-4 weeks estimated

**Priority Index:** 16
**Category:** Quick Win

**Dependencies:** Glean platform access
**Risks:** Glean data freshness/completeness
**Stakeholder support:** High (Tyler champion, AEs requesting)

**Recommendation:** Pursue immediately

---

### Opportunity 2: Standard Template Adoption (Nationwide)

**Description:** Adopt the Nationwide whitespace document as the official standard template, adding agreed-upon columns (MAPs, Delivery Architecture, Current Spend).

**Impact: 4** - High
- Solves "no standardized format" problem
- Enables ELT visibility across accounts
- Chris Powers already championing
- Low risk—proven template

**Effort: 1** - Minimal
- Template exists; just needs endorsement and distribution
- Add 3-4 columns as agreed in workshop
- Days to finalize, roll out via training

**Priority Index:** 20
**Category:** Quick Win

**Dependencies:** Leadership sign-off on standard
**Risks:** Adoption resistance from those with existing templates
**Stakeholder support:** High (Chris Powers champion, leadership aligned)

**Recommendation:** Pursue immediately

---

### Opportunity 3: Deep Research Training & Adoption

**Description:** Train all AEs/BDRs on using ChatGPT Deep Research mode (or equivalent) for landscape definition and strategic research. Document standard prompts.

**Impact: 3** - Moderate
- Addresses "ChatGPT unreliable" problem
- ~99% accuracy vs. standard mode
- No new tools needed—training only
- Benefits all account research activities

**Effort: 1** - Minimal
- Training materials creation: 1-2 days
- Rollout: 1 hour session + documentation
- Charlie has "Cognitive Shifts" course framework

**Priority Index:** 15
**Category:** Quick Win

**Dependencies:** None
**Risks:** Adoption inconsistency; people revert to old habits
**Stakeholder support:** High (Matt Lazar already using, willing to share)

**Recommendation:** Pursue immediately

---

### Opportunity 4: Alfred V2 Agent Deployment

**Description:** Deploy Tyler's Alfred V2 (Prospector rebranded) agent for strategic alignment research across team.

**Impact: 4** - High
- Automates strategic alignment research
- Tyler already has V1 shared; V2 in development
- Directly produces input for IVP documents
- Used for every strategic account

**Effort: 2** - Light
- Agent exists; deployment and training effort
- 2-3 weeks to finalize and roll out
- Documentation and training needed

**Priority Index:** 16
**Category:** Quick Win

**Dependencies:** Glean platform
**Risks:** Prompt tuning for accuracy
**Stakeholder support:** High (Tyler owner, AEs interested)

**Recommendation:** Pursue immediately

---

### Opportunity 5: BuiltWith Data Parsing Automation

**Description:** Automate parsing of BuiltWith "blob" data into structured fields: CMS, Frontend Framework, Commerce, Personalization, A/B Testing.

**Impact: 3** - Moderate
- Addresses "BuiltWith is just a blob" problem
- Enables technical risk assessment (Angular flag)
- Supports Vercel co-sell motion (hosting data)
- Manual parsing currently done by Matt V

**Effort: 2** - Light
- Data transformation task
- Known input format, known output fields
- 2-3 weeks engineering effort

**Priority Index:** 12
**Category:** Quick Win

**Dependencies:** Access to BuiltWith data feed
**Risks:** BuiltWith data completeness varies
**Stakeholder support:** Medium (Meron requested, Data team can own)

**Recommendation:** Pursue in first phase

---

### Opportunity 6: CSM Brief Template & Process

**Description:** Create standardized "CSM Brief" template and formal request process to replace ad-hoc Slack/email requests for internal footprint information.

**Impact: 3** - Moderate
- Addresses "informal information gathering" problem
- Captures institutional knowledge
- Reduces CSM interruption overhead
- Enables consistent internal footprint data

**Effort: 2** - Light
- Template design: 1-2 days
- Process definition: 1-2 days
- CSM buy-in and training: 1 week

**Priority Index:** 12
**Category:** Quick Win

**Dependencies:** CSM leadership buy-in
**Risks:** Adoption if perceived as "more work" for CSMs
**Stakeholder support:** Medium (Farsheed engaged, need leadership)

**Recommendation:** Pursue in first phase

---

### Opportunity 7: Partner Intelligence Request Process

**Description:** Create formal process for AEs to request partner intelligence from Partner Managers, including proactive briefings for strategic accounts.

**Impact: 3** - Moderate
- Addresses "no direct Crossbeam access" problem
- Enables proactive partner engagement
- Fills data gaps from incomplete Crossbeam
- Supports partner-led growth motion

**Effort: 2** - Light
- Process design: 1 week
- PM buy-in and training: 1-2 weeks
- No technical build required

**Priority Index:** 12
**Category:** Quick Win

**Dependencies:** Partner team buy-in
**Risks:** PM capacity constraints
**Stakeholder support:** Medium (discussed but PMs not in workshop)

**Recommendation:** Pursue in first phase

---

### Opportunity 8: QA Agent for AI Output Validation

**Description:** Build agent that validates AI-generated account data against authoritative sources (SEC filings, company websites) and flags discrepancies.

**Impact: 4** - High
- Addresses "trust but verify" problem at scale
- Reduces manual verification burden
- Increases confidence in AI outputs
- Could catch errors before they propagate

**Effort: 3** - Moderate
- New agent development
- Multiple source integrations
- 1-2 months engineering effort
- Needs accuracy tuning

**Priority Index:** 12
**Category:** Strategic

**Dependencies:** Clear validation rules defined
**Risks:** False positives create distrust; false negatives miss errors
**Stakeholder support:** High conceptually, needs design validation

**Recommendation:** Plan for Phase 2

---

### Opportunity 9: Unified Account Dashboard

**Description:** Create single view aggregating all account planning data from Salesforce, Tableau, Glean, and other sources into one dashboard.

**Impact: 5** - Transformative
- Directly addresses "70-80 places" problem
- Enables ELT visibility into any account
- Foundation for all other automation
- Changes how account planning works

**Effort: 4** - Significant
- Multiple system integrations
- Data transformation and normalization
- UI/UX design
- 3-6 months engineering effort

**Priority Index:** 10
**Category:** Strategic

**Dependencies:** Data architecture decisions, platform choice
**Risks:** Integration complexity; data freshness; scope creep
**Stakeholder support:** Very high (this is the vision)

**Recommendation:** Plan carefully, phase delivery

---

### Opportunity 10: Partner Mapping Agent

**Description:** Build agent that combines Crossbeam data, BuiltWith findings, and PM knowledge into unified partner intelligence view.

**Impact: 3** - Moderate
- Addresses partner data fragmentation
- Automates current manual aggregation
- Supports partner-led motions

**Effort: 3** - Moderate
- Multiple data source integration
- Logic for reconciling conflicting data
- 2-3 months effort

**Priority Index:** 9
**Category:** Backlog

**Dependencies:** Partner Intelligence Request process in place first
**Risks:** Crossbeam API access; data quality issues
**Stakeholder support:** Medium

**Recommendation:** Defer to Phase 2 or 3

---

### Opportunity 11: Product Usage Dashboard Consolidation

**Description:** Consolidate fragmented Tableau views into single comprehensive product usage dashboard showing account health, usage trends, and adoption metrics.

**Impact: 4** - High
- Addresses "fragmented Tableau views" problem
- Enables quick account health assessment
- Supports renewal and expansion motions
- Currently major gap for existing customers

**Effort: 4** - Significant
- Tom Woodhouse's domain
- Multiple Tableau view consolidation
- Data pipeline work
- 2-4 months effort

**Priority Index:** 8
**Category:** Strategic

**Dependencies:** Tom Woodhouse availability
**Risks:** Existing Tableau dependencies elsewhere
**Stakeholder support:** High (problem well-understood)

**Recommendation:** Plan for Phase 2, coordinate with Tom

---

### Opportunity 12: Full 70-80% Automation Goal

**Description:** Achieve the ELT-stated goal of automating 70-80% of account planning work, enabling that much more time for client engagement.

**Impact: 5** - Transformative
- The North Star of the initiative
- Fundamental change to how AEs work
- Major productivity and revenue enabler

**Effort: 5** - Major
- Requires most other opportunities completed
- Platform decisions, integrations, training, adoption
- 6-12+ months full realization

**Priority Index:** 5
**Category:** Major Bet

**Dependencies:** All above opportunities; platform decision; organizational change
**Risks:** Scope creep; adoption failure; technical blockers
**Stakeholder support:** Very high (ELT commitment)

**Recommendation:** Vision to guide all work; measure progress toward it

---

## Recommended Sequencing

### Phase 1: Quick Wins (Weeks 1-4)
1. Standard Template Adoption
2. Deep Research Training
3. Glean Account Navigator Enhancement
4. Alfred V2 Deployment

### Phase 2: Foundation (Months 2-3)
5. BuiltWith Data Parsing
6. CSM Brief Template & Process
7. Partner Intelligence Request Process
8. QA Agent development begins

### Phase 3: Strategic (Months 4-6)
9. Unified Account Dashboard (phased delivery)
10. Product Usage Dashboard Consolidation
11. Partner Mapping Agent

### Ongoing
12. Full automation goal—measured quarterly

---

## Quick Wins to Start Immediately

| Opportunity | Owner | Target Completion |
|-------------|-------|-------------------|
| Standard Template Adoption | Sales Leadership | Week 2 |
| Deep Research Training | Charlie/Tyler | Week 2 |
| Glean Account Navigator Enhancement | Tyler | Week 4 |
| Alfred V2 Deployment | Tyler | Week 4 |

These four require minimal technical effort and can demonstrate value quickly, building momentum for larger investments.

---

*Generated using PuRDy v2.0 Synthesizer*
