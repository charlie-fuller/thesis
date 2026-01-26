# PRD: Strategic Account Planning v2.1

## Document Info
- **Version:** Draft from Discovery v2.1
- **Date:** 2026-01-22
- **Author:** PuRDy v2.1 Synthesis
- **Sponsor:** Steve Letourneau / Massimo (ELT)

---

## 1. Problem Statement

### 1.1 Background
Contentful's sales team is executing against an ELT-driven "Top Customer Growth" strategic priority. The top 100 accounts represent significant expansion opportunity, but the account planning process is inconsistent across the organization and heavily manual. Sales leadership committed to the ELT to improve this process, and Mikki's IT/AI team has been allocated to support.

### 1.2 Current State
Account planning data is scattered across 70-80+ sources:
- **External Research:** ChatGPT, Gemini Deep Research, Company websites, SEC 10-K filings
- **Tech Stack:** BuiltWith, Wappalyzer, Mobilizer
- **Contact Data:** LinkedIn Sales Navigator, ZoomInfo
- **Internal Systems:** Salesforce, Tableau (multiple views), Gatekeeper, Granulate
- **Partner Data:** Crossbeam (via Partner Managers only)
- **Collaboration:** Glean, Slack (informal CSM conversations)

"How do we collectively gather all the information needed on account when it's across, let's just say I can be randomly 70, 80 places, maybe even more." - Steve Letourneau

No standardized template exists. "Currently, there's no consistency across our company. So there's no kind of set template, just a place to put them in Salesforce." - Rich

### 1.3 Problem Definition
Account Executives spend excessive time on manual data gathering and verification instead of client-facing strategic work. The lack of standardization means:
1. Each AE reinvents the process
2. Leadership lacks visibility into account status
3. Data quality varies wildly
4. Knowledge isn't transferred when accounts change hands
5. Quick wins from AI automation aren't captured systematically

### 1.4 Impact of Problem
**Qualitative:**
- "The goal is that 70 to 80% of your time is in front of clients. That's where the magic happens." - Steve Letourneau
- AEs report spending significant hours per strategic account plan
- Data verification requires manual citation checking even with AI assistance

**Quantified (Gaps - needs measurement):**
- [ ] Baseline hours per account plan not measured
- [ ] Percentage of time on data gathering vs. strategy unknown
- [ ] Cost of inconsistency not calculated

---

## 2. Goals & Success Criteria

### 2.1 Goals
1. **Primary:** Automate 70-80% of the account planning process
2. **Secondary:** Standardize account plan format across the organization
3. **Tertiary:** Enable "sell more faster" through better intelligence

"AI should be making us more efficient. Productivity our goal as leaders." - Steve Letourneau

### 2.2 Success Metrics

| Metric | Current Baseline | Target | Measurement Method |
|--------|-----------------|--------|-------------------|
| % of AE time with clients | Unknown | 70-80% | Time tracking / survey |
| Hours per account plan | Unknown (estimate needed) | 50% reduction | Time tracking |
| Account plans completed per quarter | Unknown | +X% | Salesforce reporting |
| Agent adoption rate | N/A (new) | 80%+ | Glean/tool usage analytics |
| Template compliance | 0% (no template) | 100% | Salesforce field completion |

**[GAP] Baseline measurements not yet captured - recommend Sales Ops survey**

### 2.3 Non-Goals
- Fully automated "one button" solution (not feasible in near-term)
- Replacing AE judgment on strategy and prioritization
- Automating technical blueprinting (explicitly scoped out)
- Detailed relationship mapping (belongs at opportunity stage)

---

## 3. User & Stakeholder Analysis

### 3.1 Primary Users

| User Type | Needs | Pain Points | Success Criteria |
|-----------|-------|-------------|------------------|
| Account Executives | Consolidated, accurate data; time savings; flexibility | Manual data gathering; verification burden; fragmented sources | "Less time on data gathering, more time on strategy" |
| BDRs | Clear scope; ability to contribute at AE level | Undefined boundaries; variable expectations | "AE above line, BDR below line & wide" |

### 3.2 Secondary Stakeholders

| Stakeholder | Needs | Pain Points | Success Criteria |
|-------------|-------|-------------|------------------|
| Sales Leadership | Consistency; visibility; ELT reporting | No standard format; can't compare accounts | Standardized template in use |
| CSMs | Clear contribution process | Ad-hoc requests via Slack | Structured handoff |
| Partner Managers | Less fielding of basic requests | AEs can't self-serve Crossbeam | Partner agent reduces inquiries |
| IT/AI Team | Clear requirements; adoption | Building tools no one uses | High adoption rates |

---

## 4. Requirements

### 4.1 Functional Requirements

#### Must Have

| ID | Requirement | Rationale | Source |
|----|-------------|-----------|--------|
| F1 | Standardized whitespace template with BU-organized rows, product columns, CMS/frontend/personalization fields | "We've decided on the format that we want" - Matt Vosberg | Workshop consensus |
| F2 | Template must include: Company, BU, Use Case, Website, CMS Current, Frontend Framework, Personalization, Monthly Active Profiles, Status (SOLD/Competitor/Whitespace/Unknown/N/A) | Nationwide doc as gold standard; MAPs for sizing | Chris Powers (Nationwide), Steve Letourneau (MAPs) |
| F3 | Deep Research starter prompts for landscape/whitespace research | "We only get 15-20 deep research queries per month" - need to make each one count | Tyler |
| F4 | Partner leverage tab matching Amazon example format | Partner account, use cases, stakeholders, role in account, next steps | Amazon Account Plan |
| F5 | Internal footprint brief format: healthy/not, usage up/down, key sites/use cases | CSM knowledge capture | Workshop discussion |
| F6 | Power mapping simplified to C-Suite + VP level + known champions/detractors | Full relationship mapping is opportunity-stage | Thomas, workshop consensus |

#### Should Have

| ID | Requirement | Rationale | Source |
|----|-------------|-----------|--------|
| S1 | Glean agent for internal footprint aggregation | Removes manual Tableau navigation | Tyler, Matt Vosberg |
| S2 | Unified Tableau dashboard for product usage | "No single Tableau V tells the whole story" - Tom Woodhouse | Workshop discussion |
| S3 | Delivery architecture/hosting column for Vercel co-sell | "We do have a co-sell assembly motion with Vercel" | Meron |
| S4 | CSM contribution questionnaire | Formalizes informal Slack process | Workshop discussion |

#### Nice to Have

| ID | Requirement | Rationale | Source |
|----|-------------|-----------|--------|
| N1 | AI QA agent for output validation with confidence scores | "Catch 75-80% of the problems" automatically | Workshop discussion |
| N2 | Salesforce native account plan object | Single source of truth in existing workflow | Tom Woodhouse |
| N3 | Partner intelligence agent with Crossbeam integration | Self-serve partner data | Tyler |

### 4.2 Non-Functional Requirements

| Category | Requirement | Rationale |
|----------|-------------|-----------|
| Accuracy | Deep Research outputs must be verifiable via citations | "Trust but verify" - universal requirement |
| Performance | Agent responses within 30 seconds for simple queries | AE workflow should feel responsive |
| Availability | Tools accessible from standard AE tech stack (Glean, Salesforce) | Minimize new tool adoption |
| Maintainability | Prompt library must support versioning and updates | "What works for Gemini 3 is going to look different than Gemini 5" - Tyler |

### 4.3 Constraints
- Platform decision pending (Glean vs. Claude vs. other) - "What's the platform decision timeline?" needed from Mikki
- Salesforce is the system of record - any solution must integrate
- Deep Research queries limited (15-20/month) - prompts must be optimized
- Data quality issues in underlying systems cannot be solved by AI

### 4.4 Dependencies
- Data team must expose relevant Salesforce/Tableau fields to Glean
- Partner team must provide clean Crossbeam export or alternative
- CSM leadership must endorse contribution process
- BI team must consolidate Tableau views

---

## 5. Scope

### 5.1 In Scope
- Landscape Definition
- Whitespace Mapping
- Partner Leverage
- Internal Footprint Audit (brief format)
- Power Mapping (simplified)
- Strategic Alignment (IVP handoff to Value Engineering)

### 5.2 Out of Scope
- **Technical Blueprinting** - "I think we're past planning when we get to technical blueprinting" - Matt Vosberg; unanimous workshop decision to move to opportunity stage
- **Detailed Relationship Mapping** - belongs at opportunity stage per workshop consensus
- **Economic Buyer/Champion integration in whitespace** - Microsoft example discussed but rejected as too complex for account planning stage

### 5.3 Future Considerations
- Commercial account templates (simpler, "click of a button")
- Integration with Outreach for ongoing tracking
- Automatic Salesforce field updates from agents
- Extension beyond top 100 accounts

---

## 6. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data quality issues undermine AI outputs | High | High | Include validation steps; surface confidence scores; "trust but verify" training |
| ZoomInfo/Crossbeam data often stale | High | Medium | Use Deep Research as primary; ZoomInfo as supplement; partner team for Crossbeam |
| Varying AI fluency across team | Medium | Medium | Provide starter prompts; optional training; pair advanced with learning users |
| Adoption resistance ("I have my own process") | Medium | Medium | Show time savings; make tools genuinely useful; don't mandate rigid workflows |
| Platform decision delayed | Medium | High | Build platform-agnostic where possible; start with Glean given existing investment |
| Scope creep (adding technical blueprint back) | Low | Medium | Document decision; refer back when raised |

---

## 7. Open Questions

| Question | Impact if Unresolved | Owner | Target Date |
|----------|---------------------|-------|-------------|
| What's the baseline time per account plan? | Can't measure improvement | Sales Ops | Week 2 |
| Platform decision (Glean primary?) | Architecture uncertainty | Mikki | Week 2 |
| What specific Tableau fields needed? | Can't build unified dashboard | AEs + BI team | Week 3 |
| How does Value Engineering want IVP handoff? | May build wrong output | Sean Winter | Week 3 |
| Which accounts qualify as "strategic"? | Unclear rollout scope | Steve/Rich | Week 2 |

---

## 8. Appendices

### 8.1 Glossary

| Term | Definition |
|------|------------|
| MAPs | Monthly Active Profiles - metric for personalization sizing |
| IVP | Initial Value Proposition - document for executive engagement |
| BU | Business Unit - organizational subdivision of large accounts |
| Deep Research | Advanced AI research mode in ChatGPT/Gemini that crawls multiple sources |
| Whitespace | Identified opportunities where Contentful is not currently deployed |

### 8.2 References

| Document | Location | Purpose |
|----------|----------|---------|
| Nationwide Whitespace Doc | Google Sheets (Chris Powers) | Gold standard template |
| Amazon Account Plan FY'27 | Google Sheets | Partner Leverage, Contacts tabs |
| Signet Exec Brief | Google Docs | IVP/3 Whys example |
| Workshop Miro Board | Miro | Process mapping outputs |

### 8.3 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v2.1 Draft | 2026-01-22 | PuRDy v2.1 | Initial synthesis with enhanced specificity, decision evolution tracking |

### 8.4 Decision Evolution Log

| Decision | Initial View | Final View | What Changed |
|----------|--------------|------------|--------------|
| Prompt Library | "No prompt library - train people instead" (Thomas: "I don't think there's any prompts myself") | Build centralized prompt library with starter prompts | "We only get 15-20 deep research queries per month. People can't really experiment." - Tyler; Compromise: library for getting started, but advanced users can freestyle |
| Technical Blueprinting | Included in original scope | OUT OF SCOPE - opportunity stage | "I think we're past planning when we get to technical blueprinting" - Matt Vosberg; SE involvement comes later |
| Power Mapping Depth | Full relationship mapping proposed | Simplified to C-Suite + VP + known champions | "For a lot of the account planning that we're talking about? Making educated guesses about what we know" - Matt Vosberg; detailed mapping at opportunity stage |
| Crossbeam Access | AEs should have direct access | Keep PM gatekeeping, build workaround agent | Data quality issues mean raw access wouldn't help; need curated intelligence |

### 8.5 What Was NOT Adopted

| Alternative | Why Considered | Why Rejected | Who Rejected |
|-------------|----------------|--------------|--------------|
| Microsoft Whitespace Report format | Shows Economic Buyer/Champion integration | Too complex for account planning stage; conflates opportunity-level detail | Workshop consensus |
| Miro as primary tool | Johannes uses it successfully; good for brainstorming | "Really hard for someone to actually use the data" - Rich; not standardizable | Steve, Rich |
| Comprehensive relationship mapping at account stage | Provides full picture | "That's the dynamic of if we don't have a relationship, we're making educated decisions" - Matt Vosberg; comes at opportunity stage | Workshop consensus |
| One-button automation | Vision: "70-80% by a button" | "That's not going to happen until you break off 10% of it at a time" - Tyler; need phased approach | IT/AI team |

---

*Generated using PuRDy v2.1 Synthesizer with enhanced specificity requirements*
