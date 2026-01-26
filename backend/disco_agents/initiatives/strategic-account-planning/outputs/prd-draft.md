# PRD: Strategic Account Planning Automation

## Document Info
- **Version:** Draft from Discovery
- **Date:** 2026-01-22
- **Author:** PuRDy Synthesis
- **Sponsor:** Steve Letourneau / Massimo (ELT)

---

## 1. Problem Statement

### 1.1 Background
Contentful has committed to an ELT priority of driving top customer growth. This requires strategic account planning for the top 100 customers—a process that involves understanding company landscape, identifying whitespace opportunities, mapping partner relationships, auditing internal footprint, identifying key contacts, and aligning to customer strategic priorities.

Currently, this process is manual, inconsistent, and time-consuming. Each AE approaches it differently, data is scattered across 70-80 sources, and there's no standard template or process.

### 1.2 Current State
AEs building strategic account plans today:
- Use ChatGPT/Gemini for research (with varying prompts and modes)
- Manually search SEC filings, company websites, BuiltWith, ZoomInfo, Crunchbase
- Request partner data from Partner Managers (no direct Crossbeam access)
- Ask CSMs for internal footprint info via informal Slack/email
- Use LinkedIn Sales Navigator for contact identification
- Create ad-hoc spreadsheets with no standard template
- Spend hours per account gathering and organizing data

### 1.3 Problem Definition
**AEs spend too much time on manual data gathering and not enough time on strategic client engagement.**

The information needed for account planning exists but is fragmented across dozens of systems with no unified view. Each AE reinvents the process, leading to inconsistent quality and no ability for leadership to easily understand account status across the portfolio.

### 1.4 Impact of Problem

| Impact Area | Quantification |
|-------------|----------------|
| Time spent per account plan | Hours (estimated 4-8 hours per strategic account) |
| AE time not with clients | 20-30% of time on internal data work |
| Leadership visibility | No consistent view across accounts |
| Data accuracy | Variable; verification required |
| Knowledge loss | CSM/PM knowledge trapped in conversations |

*Note: Baseline measurements need validation with Sales Ops*

---

## 2. Goals & Success Criteria

### 2.1 Goals
1. **Standardize** the account planning process with consistent templates and workflows
2. **Automate** 70-80% of manual data gathering work
3. **Enable** AEs to spend 70-80% of their time on client engagement
4. **Provide** leadership with consistent visibility into strategic accounts

### 2.2 Success Metrics

| Metric | Current Baseline | Target | Measurement Method |
|--------|-----------------|--------|-------------------|
| Time per account plan | TBD (estimate 4-8 hrs) | <2 hours | AE self-report survey |
| AE time with clients | TBD | 70-80% | Activity tracking |
| Template adoption rate | 0% (no standard) | 100% of strategic accounts | Audit |
| Agent/tool usage | TBD | 80%+ AEs using weekly | Glean analytics |
| Account plan completeness | Variable | 100% of required fields | Audit |

*Note: Baselines need measurement before implementation*

### 2.3 Non-Goals
- Replacing AE judgment on strategy and account approach
- Automating relationship building or client conversations
- Full automation of every edge case
- Technical blueprinting (moved to opportunity stage)

---

## 3. User & Stakeholder Analysis

### 3.1 Primary Users

| User Type | Needs | Pain Points | Success Criteria |
|-----------|-------|-------------|------------------|
| Account Executives | Consolidated data, standard templates, automation | Manual gathering, scattered data, no standard process | Dramatically reduced time on data work |
| BDRs | Ability to contribute to landscape definition | Unclear role, no access to tools | Clear division with AE, can execute first step |

### 3.2 Secondary Stakeholders

| Stakeholder | Role | Needs |
|-------------|------|-------|
| CSMs | Internal footprint knowledge source | Standardized request process, clear expectations |
| Partner Managers | Partner data source | Formal intelligence request process |
| Sales Engineers | Technical blueprint recipients | Clear handoff point, structured data |
| Sales Leadership | Visibility, consistency | Standard templates, ELT-ready views |
| Value Engineering | IVP document creation | Quality strategic alignment input |
| IT/AI Team | Build and maintain tools | Clear requirements, feedback loops |

---

## 4. Requirements

### 4.1 Functional Requirements

#### Must Have
| ID | Requirement | Rationale | Source |
|----|-------------|-----------|--------|
| F1 | Standard whitespace template based on Nationwide format | Workshop consensus on gold standard | Chris Powers, workshop |
| F2 | Landscape definition automation via Deep Research or agents | Reduce manual research time | Matt Lazar, workshop |
| F3 | Whitespace mapping support (BU-organized, standard status values) | Consistency across accounts | Workshop consensus |
| F4 | Partner data aggregation (Crossbeam + BuiltWith + PM input) | Address data fragmentation | Matt Vosberg, workshop |
| F5 | Internal footprint brief process (for existing customers) | Capture CSM knowledge | Workshop discussion |
| F6 | Simplified power mapping (C-Suite baseline) | Workshop decision to simplify | Workshop consensus |
| F7 | Strategic alignment research automation | Enable 3 Whys / IVP workflow | Workshop discussion |

#### Should Have
| ID | Requirement | Rationale | Source |
|----|-------------|-----------|--------|
| F8 | QA/validation for AI-generated data | Trust but verify | Multiple AEs |
| F9 | BuiltWith data parsing (CMS, frontend, hosting) | Currently "just a blob" | Meron, Matt V |
| F10 | Unified account dashboard view | Address 70-80 sources problem | Vision statement |
| F11 | Training materials on AI tools and prompting | Varying AI literacy | Workshop discussion |

#### Nice to Have
| ID | Requirement | Rationale | Source |
|----|-------------|-----------|--------|
| F12 | Product usage dashboard consolidation | Fragmented Tableau views | Workshop discussion |
| F13 | Automated partner mapping agent | Future automation | Miro analysis |
| F14 | Intent data integration by subsidiary | Checkout data limitation | Joel |

### 4.2 Non-Functional Requirements

| Category | Requirement | Rationale |
|----------|-------------|-----------|
| Performance | Agent responses within 30 seconds | Usability; AEs won't wait |
| Reliability | 99% uptime during business hours | Critical tool, can't be blocker |
| Accuracy | AI outputs >90% accurate (with verification) | Trust but verify standard |
| Security | No customer PII exposed inappropriately | Compliance requirement |
| Usability | < 30 min training to basic proficiency | Adoption barrier |

### 4.3 Constraints

| Constraint | Description | Source |
|------------|-------------|--------|
| Platform TBD | Glean vs. Claude Projects vs. other not yet decided | Mikki/IT |
| No direct Crossbeam access | AEs must work through Partner Managers | Current architecture |
| Tableau fragmentation | Product usage data across multiple views | Tom Woodhouse |
| Timeline | Quick wins expected Q1; full vision 6-12 months | ELT expectation |

### 4.4 Dependencies

| Dependency | Description | Owner |
|------------|-------------|-------|
| Platform decision | Affects architecture of all solutions | Mikki/IT Leadership |
| Glean access | Required for agent development | IT |
| Sales leadership sign-off | Required for template standardization | Steve/Rich |
| CSM/PM buy-in | Required for new processes | CS/Partner Leadership |

---

## 5. Scope

### 5.1 In Scope
- Landscape definition (automation and templates)
- Whitespace mapping (standard template, data support)
- Partner leverage (process and data aggregation)
- Internal footprint audit (brief template and process)
- Power mapping (simplified C-Suite approach)
- Strategic alignment (agents and 3 Whys framework)
- Training and adoption support
- Top 100 strategic accounts (initial rollout)

### 5.2 Out of Scope
- **Technical blueprinting** - Moves to opportunity stage (workshop decision)
- **Detailed relationship mapping** - Comes at opportunity stage
- **Economic buyer/champion in whitespace** - Discussed and rejected for account planning
- **Commercial accounts** - Phase 2 after strategic accounts proven
- **Tech stack selection** - Separate downstream process
- **Salesforce modifications** - Separate initiative (Tom Woodhouse)

### 5.3 Future Considerations
- Extension to all Enterprise accounts
- Extension to Commercial accounts
- Deeper Salesforce integration
- Real-time account health alerts
- Competitive intelligence automation

---

## 6. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Platform decision delayed | Medium | High | Build platform-agnostic where possible; proceed with Glean for quick wins |
| AI output quality insufficient | Medium | High | Trust but verify approach; QA agent; training on validation |
| Adoption resistance | Medium | High | Champion network; prove value with quick wins; leadership mandate |
| Data quality issues (ZoomInfo, Crossbeam) | High | Medium | Multiple source triangulation; explicit verification steps |
| CSM/PM process adoption | Medium | Medium | Leadership buy-in; demonstrate mutual benefit |
| Scope creep | High | Medium | Explicit out-of-scope list; change control |
| Integration complexity | Medium | High | Phased delivery; start with low-integration quick wins |

---

## 7. Open Questions

| Question | Impact if Unresolved | Owner | Target Date |
|----------|---------------------|-------|-------------|
| What's the baseline time per account plan? | Can't measure improvement | Sales Ops | Week 2 |
| Platform decision (Glean vs. other)? | Affects technical architecture | Mikki | Week 4 |
| What are numeric success targets? | Can't declare success | Steve/Massimo | Week 2 |
| Who owns Tableau consolidation? | Dashboard risk | Tom Woodhouse | Week 3 |
| Value Engineering handoff process? | IVP workflow incomplete | Sean Winter | Week 4 |

---

## 8. Appendices

### 8.1 Glossary

| Term | Definition |
|------|------------|
| Whitespace | Areas where customer has need but no Contentful presence |
| IVP | Ideal Value Proposition document (3 Whys output) |
| 3 Whys | Framework: Why Now, Why Change, Why Contentful |
| MAPs | Monthly Active Profiles (product usage metric) |
| BU | Business Unit |
| Deep Research | ChatGPT mode with higher accuracy |

### 8.2 References

| Document | Location |
|----------|----------|
| Workshop transcripts (3) | /transcripts/ |
| Miro Board Gap Analysis | /outputs/ |
| Nationwide Whitespace Template | Google Sheets (Chris Powers) |
| Amazon Account Plan | Google Sheets |
| Signet Exec Brief | Google Docs |

### 8.3 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| Draft | 2026-01-22 | PuRDy | Initial synthesis from discovery |

---

*Generated using PuRDy v2.0 Synthesizer*
