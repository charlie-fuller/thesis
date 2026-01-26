# Opportunity List: Strategic Account Planning v2.1

## Opportunity Identification Method

Opportunities were identified from pain points surfaced across 6 discovery sessions (intro workshop, working sessions, process summary, AI standardization, next steps). Each opportunity maps to a specific step in the account planning process where manual effort or data gaps were documented.

## Opportunity Summary

| # | Opportunity | Impact | Effort | Priority Index | Category |
|---|-------------|--------|--------|----------------|----------|
| 1 | Deep Research Starter Prompt Library | 4 | 1 | 4.0 | Quick Win |
| 2 | Internal Footprint Agent (Usage/Health) | 5 | 3 | 1.7 | Strategic |
| 3 | Unified Tableau Dashboard for Product Usage | 4 | 3 | 1.3 | Strategic |
| 4 | Partner Intelligence Agent | 4 | 3 | 1.3 | Strategic |
| 5 | CSM Contribution Questionnaire/Process | 3 | 1 | 3.0 | Quick Win |
| 6 | Whitespace Template Standardization | 4 | 2 | 2.0 | Quick Win |
| 7 | AI QA/Validation Agent | 5 | 4 | 1.25 | Major Bet |
| 8 | Salesforce Account Plan Object | 4 | 4 | 1.0 | Major Bet |
| 9 | AE AI Fluency Training | 3 | 2 | 1.5 | Strategic |

---

## Detailed Opportunity Analysis

### Opportunity 1: Deep Research Starter Prompt Library

**Description:** Create a curated library of starter prompts for Deep Research (ChatGPT and Gemini) optimized for strategic account planning use cases.

**Impact: 4** - High
- Enables immediate improvement in research quality for all AEs
- "We only get 15-20 deep research queries per month. So people can't really experiment." - Tyler
- Reduces learning curve for less AI-fluent team members
- Sharing what works creates rising tide effect

**Effort: 1** - Very Low
- Tyler built POC prompt library app in 15 minutes during meeting
- Content exists in individual AE workflows (Chris Powers' Gemini gem, etc.)
- No infrastructure changes required
- "If we have some curated ones with that, we don't have to do education and training." - Tyler

**Priority Index:** 4.0
**Category:** Quick Win

**Dependencies:** None
**Risks:** May become stale as models evolve; needs maintenance process
**Stakeholder support:**
- Champions: Tyler (built POC), Chris Powers (has working prompts)
- Potential resistance: Thomas ("I think it should be organic... prompting is the past")

**Recommendation:** Pursue immediately

---

### Opportunity 2: Internal Footprint Agent (Usage/Health)

**Description:** Glean agent that aggregates internal customer data from Salesforce, Tableau, and other sources to produce a standardized internal footprint brief.

**Impact: 5** - Very High
- "This is all stuff that we should know because it's our internal footprint. So I would hope that we can kind of standardize and easily surface a lot of the details we're looking for here." - Matt Vosberg
- Directly addresses fragmented data problem
- High frequency use case across all account plans

**Effort: 3** - Medium
- Requires data team involvement to ensure proper field exposure to Glean
- "If we want to say this is your usage finder Agent. That's the one that goes through and it specifically goes to tableau..." - Tyler
- Needs validation that underlying data is accurate and accessible

**Priority Index:** 1.7
**Category:** Strategic

**Dependencies:**
- Data team must ensure Tableau/Salesforce fields are Glean-accessible
- Requires clarity on which fields constitute "usage" and "health"
**Risks:**
- Data quality issues ("we can't go back and fix all the garbage that has been put into Salesforce" - Tyler)
- May expose data gaps that need separate remediation
**Stakeholder support:**
- Champions: Matt Vosberg, Tyler
- Required: Data team (Rob, Justin), Tom Woodhouse

**Recommendation:** Pursue - high strategic value, moderate complexity

---

### Opportunity 3: Unified Tableau Dashboard for Product Usage

**Description:** Consolidate fragmented Tableau views into a single comprehensive product usage dashboard accessible from Salesforce.

**Impact: 4** - High
- "It seems to be split up into multiple views. Which some views have 80% information, and then you got to go to at least one or two other views." - Tom Woodhouse
- "Tableau overall kind of navigation, get through a tableau or to figure out everything you potentially look at is just not the greatest UI." - Tom Woodhouse

**Effort: 3** - Medium
- Requires BI team involvement
- May require understanding what "complete" looks like (currently undefined)
- "I don't think there's one Tableau V that tells the whole story." - Tom Woodhouse

**Priority Index:** 1.3
**Category:** Strategic

**Dependencies:** Clear requirements from AEs on what fields they need
**Risks:** Scope creep; may surface underlying data quality issues
**Stakeholder support:**
- Required: BI team, Sales Ops

**Recommendation:** Pursue - foundational enabler for other improvements

---

### Opportunity 4: Partner Intelligence Agent

**Description:** Agent that pulls partner mapping data from Crossbeam export (or internal sheet) and provides partner recommendations for strategic accounts.

**Impact: 4** - High
- Removes dependency on Partner Managers for basic partner lookups
- "Different areas where we can get that detail." - Matt Vosberg on current fragmented approach
- Could integrate with Dean's work to make "AI friendly, concise Google sheet" - Tyler

**Effort: 3** - Medium
- Crossbeam data quality issues need workaround
- "If I work with Dean to make it so it's a much more AI friendly, concise Google sheet that is always in an agent to identify partners." - Tyler
- Requires partner team buy-in

**Priority Index:** 1.3
**Category:** Strategic

**Dependencies:** Partner team cooperation; clean data export
**Risks:** Crossbeam data staleness; not all partners use it
**Stakeholder support:**
- Required: Partner team, Dean

**Recommendation:** Pursue - good value, requires partnership

---

### Opportunity 5: CSM Contribution Questionnaire/Process

**Description:** Standardized questionnaire and process for CSMs to contribute internal footprint knowledge to account plans.

**Impact: 3** - Medium
- Currently "Slack messages. Stand in meetings that we already have. Emails." - Matt Vosberg on CSM engagement
- Formalizes critical knowledge transfer
- Could feed directly into account plan template

**Effort: 1** - Very Low
- Just requires defining questions and process
- No technology build required
- "I don't think the formal submission necessarily solves the detail. I think it's more wrapped data and expectations of where to find it." - Matt Vosberg

**Priority Index:** 3.0
**Category:** Quick Win

**Dependencies:** CSM leadership buy-in
**Risks:** Adoption may be spotty without enforcement
**Stakeholder support:**
- Required: CSM leadership, Farsheed

**Recommendation:** Pursue immediately - low effort, decent value

---

### Opportunity 6: Whitespace Template Standardization

**Description:** Publish the Nationwide Whitespace Doc format as the gold standard template with clear column definitions and instructions.

**Impact: 4** - High
- "Is it fair, Matt, to say, in the limited time that we have, if we put this in as the standard for both landscape definition and white space mapping...?" - Workshop discussion
- Provides clear target for automation outputs
- Enables comparison across accounts

**Effort: 2** - Low
- Template exists; needs documentation and socialization
- "We've decided on the format that we want." - Matt Vosberg
- Add columns: Monthly Active Profiles (for personalization sizing), Hosting/Delivery Architecture (Vercel co-sell)

**Priority Index:** 2.0
**Category:** Quick Win

**Dependencies:** Final review from Chris Powers (owner of Nationwide doc)
**Risks:** May need variants for different account types
**Stakeholder support:**
- Champions: Chris Powers, Matt Vosberg
- Suggested additions: Steve Letourneau (MAPs column), Meron (delivery architecture column)

**Recommendation:** Pursue immediately

---

### Opportunity 7: AI QA/Validation Agent

**Description:** Agent that cross-references AI research outputs against multiple sources and provides confidence scores for each data point.

**Impact: 5** - Very High
- Directly addresses "trust but verify" problem at scale
- "The more we can do automatically to run QA and run a different model or run a different algorithm to validate the results that are coming in. Then we're going to catch maybe 75, 80% of the things that are problems." - Workshop discussion
- Would dramatically reduce manual verification time

**Effort: 4** - High
- Complex technical challenge
- Requires access to multiple validation data sources
- "That sounds amazing and terrifying." - AE reaction

**Priority Index:** 1.25
**Category:** Major Bet

**Dependencies:** Clear definition of what "validated" means; access to authoritative data sources
**Risks:** May surface that validation is impossible for some data points; false confidence if not calibrated well
**Stakeholder support:**
- Champion: IT/AI team
- Skeptics: Some AEs concerned about over-automation

**Recommendation:** Evaluate - high value but high complexity; start with scoped prototype

---

### Opportunity 8: Salesforce Account Plan Object

**Description:** Native Salesforce object or Lightning component that serves as the single source of truth for strategic account plans, pulling data from various sources.

**Impact: 4** - High
- "Salesforce is the only thing for them. It's the only thing internally." - Tyler summarizing AE perspective
- "Salesforce has been doing a lot with account plans like they've been providing objects that you publicly into." - Tom Woodhouse

**Effort: 4** - High
- Significant Salesforce development
- Integration complexity with multiple data sources
- Change management for adoption

**Priority Index:** 1.0
**Category:** Major Bet

**Dependencies:** All data integrations working; clear template finalized
**Risks:** Scope creep; may become dumping ground; adoption challenges
**Stakeholder support:**
- Champion: Tom Woodhouse (business platform)
- Required: Sales Ops, Data team

**Recommendation:** Defer - important but dependent on other pieces being in place first

---

### Opportunity 9: AE AI Fluency Training

**Description:** Training program to upskill AEs on effective AI interaction, moving beyond "prompting" to natural conversation and verification skills.

**Impact: 3** - Medium
- "I think if you're next, really curious, right? Then you get a very good sense of how to talk to your AI." - Thomas
- Some AEs highly fluent (Thomas, Chris Powers), others less so
- "There should be an expectation that people like, I mean, good salespeople are naturally curious." - Thomas

**Effort: 2** - Low
- Chris has curriculum ready ("cognitive shifts course")
- "Ashley and Tricia were just like, oh, my God, come into legal, do that for us." - Interest exists
- Can be delivered incrementally

**Priority Index:** 1.5
**Category:** Strategic

**Dependencies:** None
**Risks:** May be seen as remedial; time away from selling
**Stakeholder support:**
- Champion: Chris B (has curriculum), Tyler
- Potential resistance: Sales leadership (time commitment)

**Recommendation:** Pursue - enables better adoption of all AI tools

---

## Recommended Sequencing

```
Phase 1 (Immediate - Week 1-2):
├── Prompt Library (Opp #1)
├── Whitespace Template (Opp #6)
└── CSM Questionnaire (Opp #5)

Phase 2 (Short-Term - Weeks 3-6):
├── Internal Footprint Agent (Opp #2)
├── Unified Tableau Dashboard (Opp #3)
└── AI Fluency Training (Opp #9)

Phase 3 (Medium-Term - Weeks 7-12):
├── Partner Intelligence Agent (Opp #4)
└── AI QA Agent Prototype (Opp #7)

Phase 4 (Longer-Term):
└── Salesforce Account Plan Object (Opp #8)
```

## Quick Wins to Start

1. **Prompt Library** - Tyler has POC ready; Chris Powers has working prompts; can deploy in days
2. **Whitespace Template** - Document exists (Nationwide); needs publishing and minor additions
3. **CSM Questionnaire** - Pure process; no technology needed

---

*Generated using PuRDy v2.1 Synthesizer with enhanced specificity requirements*
