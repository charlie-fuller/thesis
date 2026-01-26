# Synthesis Summary: Strategic Account Planning

## Executive Summary

Strategic Account Planning is an ELT-driven initiative to standardize and automate the account planning process for Contentful's top customers. Currently, AEs spend significant time manually gathering data from 70-80 different sources across fragmented systems, leaving less time for client-facing strategic work.

The discovery process revealed a clear picture: **the data exists but is scattered, the processes are known but inconsistent, and the tools are available but underutilized.** The path forward is not about creating new data or inventing new processes—it's about integrating what exists, standardizing on proven approaches (like the Nationwide whitespace template), and using AI to automate the 70-80% of work that's currently manual.

Key workshop decisions simplified the scope: Technical blueprinting moves to opportunity stage, power mapping starts simple (C-Suite baseline), and the focus stays on enabling AEs to spend more time with clients, not less time at their desks.

---

## Key Themes

### Theme 1: Data Fragmentation is the Core Problem
**Finding:** Account planning data exists across Salesforce, Tableau, BuiltWith, ZoomInfo, Crossbeam, Glean, ChatGPT, SEC filings, company websites, and CSM/PM knowledge—but there's no unified view.

**Evidence:**
- Steve Letourneau: "Information is across 70-80 places"
- Workshop: "No single comprehensive view" of product usage
- Miro analysis: Data sources listed separately for each stage with no integration

**Implications:**
- Solution should aggregate, not recreate data
- Integration architecture is the primary technical challenge
- "Single pane of glass" mentality for account view

---

### Theme 2: AI Amplifies, Humans Verify
**Finding:** AI tools (especially ChatGPT Deep Research, Glean agents) can do the heavy lifting of data gathering and synthesis, but output must be verified. The magic is "trust but verify."

**Evidence:**
- Matt Lazar: Deep Research is "~99% accurate" vs. standard ChatGPT being unreliable
- Matt Vosberg: "Verify what GPT/Gemini are finding... enriching all of that"
- Multiple mentions of manual verification steps

**Implications:**
- Build validation into automated workflows
- Train users on verification techniques
- Don't promise 100% automation—promise better starting points

---

### Theme 3: Gold Standards Exist, Just Not Adopted
**Finding:** High-performing individuals have created excellent templates and processes. The opportunity is standardization and adoption, not invention.

**Evidence:**
- Chris Powers' Nationwide whitespace doc designated "gold standard"
- Amazon Account Plan tabs for partner leverage and contacts
- Signet Exec Brief for IVP output
- Tyler's existing agents (Alfred V1/V2, Account Navigator)

**Implications:**
- Standardize on what works rather than designing from scratch
- Leverage existing champions to drive adoption
- Focus engineering on automation, not template design

---

### Theme 4: Simplify to Accelerate
**Finding:** Workshop consistently chose simpler approaches over comprehensive ones when trade-offs arose.

**Evidence:**
- Technical blueprinting: "Move out of account planning" (unanimous)
- Power mapping: "Start with C-Suite, let investigations lead"
- Economic buyer in whitespace: Discussed but rejected
- Internal footprint: "Keep it brief—healthy? Usage up/down? Move on"

**Implications:**
- MVP mindset will accelerate delivery
- Resist scope creep from "wouldn't it be nice" requests
- Build expandable foundations, not complete systems

---

## Stakeholder Perspectives

### Account Executives (Primary Users)
- **Primary concerns:** Too much time gathering data, not enough with clients
- **Key needs:** Consolidated data view, accurate AI outputs, standard templates, automation of manual steps
- **Success criteria:** Significantly reduced time per account plan; more strategic conversations with leadership

### BDRs (Supporting Role)
- **Primary concerns:** Being able to contribute without overstepping
- **Key needs:** Clear division of responsibility, ability to execute landscape definition
- **Success criteria:** AE above line, BDR below line & wide; clear collaboration model

### CSMs (Internal Knowledge Holders)
- **Primary concerns:** Ad-hoc requests for information, no standard process
- **Key needs:** Standardized "CSM Brief" format, clear expectations
- **Success criteria:** Formal process replaces Slack messages; knowledge documented

### Sales Engineers
- **Primary concerns:** Getting involved too early without context; BuiltWith data as "blob"
- **Key needs:** Clear handoff from account planning to opportunity; structured data
- **Success criteria:** Technical blueprinting at right time with right information

### Partner Managers
- **Primary concerns:** No direct AE access to Crossbeam; reactive rather than proactive
- **Key needs:** Partner Intelligence Request process; proactive contribution model
- **Success criteria:** Strategic accounts get proactive partner intel

### Sales Leadership
- **Primary concerns:** Inconsistency across team; no visibility into accounts
- **Key needs:** Standard templates, consistent process, ELT-ready views
- **Success criteria:** Any account can be understood at a glance by any leader

### IT/AI Team
- **Primary concerns:** Building the right thing; technical feasibility
- **Key needs:** Clear requirements, user feedback, iteration opportunities
- **Success criteria:** Tools adopted and valued; measurable productivity gains

---

## Current State Summary

The strategic account planning process today consists of six stages, each with manual data gathering:

1. **Landscape Definition:** AEs use ChatGPT Deep Research to identify subsidiaries, business units, and company structure. Validated against SEC 10-K filings. ZoomInfo data often outdated.

2. **Whitespace Mapping:** AEs manually populate spreadsheets with business units, current CMS, competitor presence, and opportunities. BuiltWith and Wappalyzer used for tech stack. Manual site inspection required.

3. **Partner Leverage:** AEs request Crossbeam data from Partner Managers (no direct access). Data is incomplete. BuiltWith supplements gaps.

4. **Internal Footprint:** For existing customers, CSMs provide account health info via informal Slack/email. Product usage data fragmented across multiple Tableau views.

5. **Power Mapping:** LinkedIn Sales Navigator and ZoomInfo used to identify executives. Currently varies from comprehensive mapping to basic C-Suite list.

6. **Strategic Alignment:** Glean agents and Deep Research identify company initiatives. Output feeds Value Engineering for IVP document creation using 3 Whys framework.

---

## Key Pain Points (Prioritized)

### Critical
1. **Data scattered across 70-80 sources** - Impact: Every AE rebuilds the same picture manually
2. **No standard templates/process** - Impact: Inconsistent quality, no ELT visibility
3. **AI output requires heavy verification** - Impact: Trust issues, duplicate effort

### High
4. **CSM knowledge trapped in conversations** - Impact: Lost institutional knowledge
5. **Partner data incomplete (Crossbeam gaps)** - Impact: Missed partnership opportunities
6. **Product usage view fragmented** - Impact: Can't quickly assess account health

### Medium
7. **Power mapping approaches vary wildly** - Impact: Some accounts over-mapped, others under-mapped
8. **No clear handoff to opportunity stage** - Impact: Work repeated or dropped
9. **AI literacy varies across team** - Impact: Uneven productivity gains

---

## Tensions & Trade-offs

| Tension | Perspective A | Perspective B | Recommended Resolution |
|---------|---------------|---------------|------------------------|
| Automation vs. Judgment | AEs want automated data, own strategy | Leadership wants consistency | Automate data gathering; AE owns synthesis and strategy |
| Comprehensive vs. Fast | Gold standards have many fields | Need to move quickly | Define required vs. optional fields; phase enhancements |
| Net New vs. Existing | Same process should work for both | Available data differs significantly | Graceful degradation—show what's available, flag gaps |
| Training vs. Tooling | Build better tools | Upskill users on AI | Both—tools AND training; lower floor AND raise ceiling |

---

*Generated using PuRDy v2.0 Synthesizer*
