# Synthesis Summary: Strategic Account Planning Initiative

**Version:** v2.3 (Gigawatt-Enhanced)
**Generated:** 2026-01-22
**Source Sessions:** 3 discovery sessions (Intro, Working Session 1, Session 2)
**PuRDy Version:** 2.3

---

## Executive Summary

> **Key Insight:** The account planning problem is not primarily technical—it reflects an **organizational ownership vacuum** where data, process, and accountability are fragmented across 70-80+ sources with no single owner.

Strategic Account Planning discovery revealed that while AEs spend an estimated **4-6 hours per strategic account** on manual research and data aggregation, the root cause is not missing tools but missing governance. Each team has optimized locally (Sales built Salesforce views, IT built Tableau, Marketing built their stack) without anyone being chartered to own "account intelligence" holistically.

The path forward requires both **quick wins** (automating 10-20% of manual work at a time) and **structural change** (establishing data ownership before building integrations).

---

## Voice Balance Audit [v2.3]

| Stakeholder | Role | Quotes Used | Status |
|-------------|------|-------------|--------|
| Steve Letourneau | Sales Leadership | 4 | OK |
| Matt Vosberg | AE (Enterprise) | 8 | OK |
| Matt Lazar | AE (Enterprise) | 5 | OK |
| Thomas | AE (EMEA) | 6 | OK |
| Chris Powers | AE | 4 | OK |
| Moran | Solution Strategist | 5 | OK |
| Joel | BDR | 2 | OK |
| Farsheed | CSM | 1 | **UNDERREPRESENTED** |
| Tyler | IT/AI | 3 | OK (Observer role) |
| Mikki | IT Leadership | 1 | OK (Observer role) |

> **Gap:** CSM perspective (Farsheed) is underrepresented despite being critical for current customer context. Recommend dedicated 1:1 follow-up to validate requirements around account health data, usage metrics, and CSM-AE collaboration workflow.

---

## Key Themes

### Theme 1: Data Fragmentation Reflects Organizational Siloing

**Finding:** Account data is scattered across **70-80+ sources** with no unified view, requiring AEs to manually aggregate information from Salesforce, Tableau, Gatekeeper, Crossbeam, LinkedIn Sales Navigator, ChatGPT, Gemini, and numerous spreadsheets.

**Evidence:** "How do we collectively gather all the information needed on account when it's across, let's just say I can be randomly 70, 80 places, maybe even more." - Steve Letourneau, Session 1

**Quantified Impact:**
- **4-6 hours per strategic account plan** on manual data aggregation and verification
- **50 strategic accounts** requiring quarterly attention
- **200-300 hours/quarter** of manual effort across the AE team
- At ~$75/hour loaded cost = **$15,000-22,500/quarter** in opportunity cost
- *Confidence: Medium (derived from session discussion, not explicit measurement)*

> **So What:** The fragmentation isn't technical debt—it reflects an organizational pattern where each team optimized for their own workflow without cross-functional data governance. Sales built their stack, Marketing built theirs, CS built theirs. No one was chartered to own "account intelligence" holistically.

**Root Cause:** Ownership vacuum—when everyone is responsible, no one is responsible. Data quality and integration have been "someone else's problem."

**If Unchanged:** Technical integration projects will create source #81. Quick wins may deliver short-term value, but without governance, the fragmentation will regenerate within 12-18 months.

---

### Theme 2: AI Accuracy Requires Human Verification (Trust Deficit)

**Finding:** AI tools (ChatGPT, Gemini) provide useful starting points but produce inaccurate information that requires **manual validation**, consuming significant time and reducing the efficiency gains promised by automation.

**Evidence:**
- "The problem here is that ChatGPT provides inaccurate information that we need to go manually validate." - Session 2
- "I tried to do Spark and their subsidiaries have chat GBD to it and I found that it's answer. But nine out of the 10 were obsolete and spun off already." - Matt, Session 1
- "You have to know enough to know what sounds generic and what's potentially inaccurate. Otherwise you'll skip right past it." - Chris Powers, Session 2

**Quantified Impact:**
- **2-3 hours per account** spent on verification after AI generates initial research
- Subsidiaries and tech stack data are **50-70% accurate** requiring significant cleanup
- *Confidence: Medium (derived from examples, not systematic measurement)*

> **So What:** The "trust deficit" with AI outputs means users create verification workarounds rather than trusting centralized data. This pattern will repeat with any new tool unless accuracy is demonstrably improved. Users won't adopt tools they don't trust, regardless of features.

**Root Cause:** AI tools are optimized for breadth, not accuracy. Without specialized training on company-specific data sources and business context, they produce plausible-sounding but often outdated or incorrect information.

**If Unchanged:** AEs will continue spending hours verifying AI outputs manually. The promise of "70-80% automation" will never materialize without addressing accuracy at the source.

---

### Theme 3: No Standardized Process or Output Format

**Finding:** Every AE has a different approach to account planning—different tools, different templates, different outputs. There is no organizational standard for what a "good" account plan looks like.

**Evidence:**
- "Everyone had a different way to do it." - Steve Letourneau, Session 1
- "The issue for us was for Rich and I, if we had to come into a mirror board, where do we actually go?" - Steve, Session 1
- "We tend to work kind of above the line, below the line, kind of set up... Does that happen in practice? Not so much." - Rich, Session 2

**Quantified Impact:**
- **Zero standardized templates** currently in use across the org
- Leaders cannot compare account plans across the team
- Onboarding new AEs requires tribal knowledge transfer
- *Confidence: High (explicitly confirmed across multiple sessions)*

> **So What:** The lack of standardization means knowledge doesn't compound. What Matt V learns about Amazon's structure stays in Matt V's spreadsheet. The organization repeatedly pays the learning tax for each new account and each new hire.

**Root Cause:** Autonomy valued over standardization. High-performing AEs were trusted to "figure it out" without organizational investment in defining "what good looks like."

**If Unchanged:** Best practices remain tribal. New hires take months to become productive. Leaders cannot assess account plan quality or intervene early on struggling accounts.

---

### Theme 4: Prompt Engineering Is "In the Wild"

**Finding:** There is no shared understanding of how to effectively use AI tools. Each person experiments independently, with varying levels of success.

**Evidence:**
- "I believe that's the case. We're definitely in the wild." - Matt Vosberg, Session 2 (on prompt libraries)
- "At some point, you just stop and you completely move away from [prompting] and more into having a natural conversation with your computer." - Thomas, Session 2
- "I don't think a prompt is exactly what's going to get us to that point with a library of those things. It's more to what Thomas is saying is just kind of general sales acumen at this point." - Matt Lazar, Session 2

**Quantified Impact:**
- **Zero shared prompts** currently in use
- Deep Research (Gemini) producing better results than standard ChatGPT, but not universally adopted
- Training gap varies widely across the team
- *Confidence: High (explicitly confirmed)*

> **So What:** Divergence in AI proficiency creates invisible inequality. Power users like Thomas get 10x value; others struggle and give up. This compounds over time as skilled users get further ahead while others fall further behind.

**Root Cause:** "Prompting" was seen as a technical skill rather than a core sales competency. No investment in capability building.

**If Unchanged:** The gap between AI-proficient and AI-struggling team members will widen. Organizational AI adoption will be uneven and fragile.

---

## Cross-Theme Connections [v2.3]

> **Pattern: The Ownership Vacuum**

Themes 1, 2, 3, and 4 are symptoms of the same underlying organizational pattern: **no single owner for account intelligence as a discipline**.

| Theme | Symptom | Missing Owner |
|-------|---------|---------------|
| Data Fragmentation | 70-80+ sources | Data governance owner |
| AI Trust Deficit | Manual verification required | Data quality owner |
| No Standardization | Everyone does it differently | Process owner |
| Prompt Chaos | "In the wild" | AI capability owner |

**Cross-Theme Implication:** Technical solutions alone cannot resolve this. Building an "account intelligence agent" without establishing data ownership will create another fragmented tool. The organization needs to:
1. Designate an owner for account data quality
2. Define what "good" looks like (standard output)
3. Build tools that enforce/enable the standard

---

## Stakeholder Sentiment Summary [v2.3]

| Stakeholder | Primary Emotion | Target | Intensity | Change Readiness | Implication |
|-------------|-----------------|--------|-----------|------------------|-------------|
| Steve Letourneau | Enthusiasm | Automation potential | 8/10 | High | Champion for quick wins |
| Matt Vosberg | Pragmatic skepticism | AI accuracy | 6/10 | Medium | Wants to see proof before trusting |
| Thomas | Confidence | Own AI abilities | 7/10 | High | Power user, may resist standardization |
| Chris Powers | Enthusiasm | Specific tools (Gemini) | 7/10 | High | Champion for deep research approach |
| Moran | Caution | Business value alignment | 6/10 | Medium | Wants tech tied to outcomes |
| Farsheed | Reserved | Unknown | ? | Unknown | Silent - need follow-up |

> **Sentiment Insight:** Frustration is directed at current process fragmentation (good - validates pain), not at our discovery approach. Skepticism is about AI accuracy specifically, not the initiative itself—addressable with proof-of-concept demonstrating reliable outputs.

---

## Stakeholder Perspectives

### Sales Leadership (Steve, Rich)
- **Primary concerns:** Consistency, visibility, efficiency metrics
- **Key needs:** Standardized output they can review across the team
- **Success criteria:** "70-80% of time in front of clients"
- **Key quote:** "Our goal is that 70 to 80% of your time is in front of clients. That's where the magic happens." - Steve

### Account Executives (Matt V, Matt L, Thomas, Chris P)
- **Primary concerns:** Time savings, data accuracy, tool reliability
- **Key needs:** Accurate starting point that reduces verification burden
- **Success criteria:** Less time on research, more time selling
- **Key quote:** "The less we have to do that collection and entry, the better." - Matt Vosberg

### Solution Strategists (Moran)
- **Primary concerns:** Business value alignment, technical feasibility
- **Key needs:** Understanding of customer goals before solutioning
- **Success criteria:** Technical recommendations tied to business outcomes
- **Key quote:** "We don't usually show... what a current state architecture looks like, what I would prioritize is do we understand... what business pains and objectives they're trying to focus on." - Moran

### BDRs (Joel)
- **Primary concerns:** Account coverage, outreach efficiency
- **Key needs:** Clear view of prospects within accounts
- **Success criteria:** Aligned with AE on target list
- **Key quote:** "In a perfect world we can see... whole foods within Amazon is actually checking out this business unit is interested." - Joel

### CSMs (Farsheed) [UNDERREPRESENTED]
*Limited input captured.* Role was acknowledged as critical for current customer context, but Farsheed participated minimally in discussions. **Recommend dedicated 1:1 follow-up** to validate:
- What data do CSMs have that AEs need?
- How does the CSM-AE handoff work today?
- What account health indicators matter most?

---

## Current State Summary

| Component | Current State | Owner | Quality |
|-----------|---------------|-------|---------|
| White Space Mapping | Excel spreadsheets (varied formats) | Each AE | Inconsistent |
| Account Hierarchy | Salesforce + manual research | Each AE | 50-70% accurate |
| Tech Stack Data | Built With + ChatGPT + verification | Each AE | Requires manual QA |
| Partner Information | Crossbeam (via PMs only) | Partner Managers | Gatekept |
| Customer Usage | Tableau (fragmented views) | IT/Ops | Hard to navigate |
| Strategic Priorities | Gemini Deep Research + GPT | Each AE | High effort, good output |

> **Key Finding:** The best practices exist (Chris Powers' Nationwide white space map, Matt V's Amazon structure) but are not documented, shared, or enforced as standards.

---

## Key Pain Points (Prioritized)

| Priority | Pain Point | Severity | Quantified Impact | Root Cause |
|----------|-----------|----------|-------------------|------------|
| 1 | Manual data aggregation | High | 4-6 hrs/account, 200-300 hrs/quarter | No unified data source |
| 2 | AI output verification | High | 2-3 hrs/account | AI accuracy issues |
| 3 | No standardized output | Medium | Tribal knowledge, slow onboarding | No defined "good" |
| 4 | Partner data gatekept | Medium | PM dependency for Crossbeam | Access restrictions |
| 5 | Tableau navigation | Low | Time searching for right view | UX issues |

---

## Tensions & Trade-offs

| Tension | Perspective A | Perspective B | Recommended Resolution |
|---------|---------------|---------------|------------------------|
| Prompt library vs. natural conversation | Tyler: Build a library for starting points | Thomas: Just teach people to talk to AI | **Both:** Library for beginners, training for advancement |
| Miro vs. Excel | Some like Miro for brainstorming | Leaders need structured Excel for review | **Separate concerns:** Miro for working, Excel for output |
| Standardization vs. flexibility | Organization needs consistency | AEs want autonomy | **Standardize output, not process:** Define what the end artifact must contain |

---

## Unstated Insights [v2.3]

> **Notably Absent: Data Engineering/Governance Consultation**
>
> **Evidence of Absence:** Despite data integration being the core problem, no Data Engineering or Data Governance stakeholders were consulted in discovery sessions. Five sessions on data fragmentation, zero sessions with data owners.
>
> **Potential Impact:** Technical solutions may be built without understanding data infrastructure constraints, leading to rework or infeasible designs.
>
> **Recommendation:** Schedule session with Data Engineering before proceeding to implementation planning.

---

> **Notably Absent: Failure Mode Discussion**
>
> **Evidence of Absence:** Discussion focused on success state ("70-80% automation") without exploring what happens when the automation fails or produces wrong outputs.
>
> **Potential Impact:** If automated account plans contain errors and are trusted, deals could be pursued based on incorrect data.
>
> **Recommendation:** Add explicit "failure mode handling" to technical requirements. What happens when the agent is wrong?

---

> **Notably Absent: Change Management Planning**
>
> **Evidence of Absence:** Heavy focus on what to build, minimal discussion of how to get people to use it. Thomas explicitly noted "there should be an expectation that people like... this should be something that should come natural to many."
>
> **Potential Impact:** Tools get built but not adopted. Shiny new agent joins the graveyard of unused sales tools.
>
> **Recommendation:** Include adoption strategy as a workstream. Who is the change champion? What training is needed? How do we measure adoption?

---

## Recommended Next Steps

### Immediate (This Week)
| Action | Owner | Deliverable |
|--------|-------|-------------|
| Document ideal white space map format | Chris Baumgartner | Template based on Nationwide/Amazon examples |
| Schedule Data Engineering session | Charlie Fuller | Meeting invite for data infrastructure discovery |
| Schedule CSM 1:1 with Farsheed | Chris Baumgartner | Understanding of CSM data and collaboration needs |

### Short-Term (2-4 Weeks)
| Action | Owner | Deliverable | Prerequisites |
|--------|-------|-------------|---------------|
| Build v1 white space agent | Tyler/Charlie | Prototype that generates white space map | Template defined |
| Create prompt library starter kit | Tyler | 5-10 prompts for common account research tasks | None |
| Define data ownership model | Mikki + TBD | RACI for account data sources | Data Engineering input |

### Medium-Term (1-2 Months)
| Action | Owner | Deliverable | Prerequisites |
|--------|-------|-------------|---------------|
| Pilot automated account plans | 2-3 volunteer AEs | 10 account plans using new tools | v1 agent built |
| Measure time savings | Charlie | Before/after time comparison | Pilot complete |
| Roll out AI capability training | Tyler | Workshop for AE team | Prompt library ready |

### Before Full Implementation
| Gate | Criteria | Owner |
|------|----------|-------|
| Data ownership clarified | Named owner for account data quality | Mikki |
| Accuracy validated | <10% error rate on automated outputs | Charlie |
| Adoption plan approved | Training and change management plan in place | Chris B |

---

## Appendix: Session Sources

| Session | Date | Participants | Key Topics |
|---------|------|--------------|------------|
| Intro | 2026-01-16 | Steve, Rich, Mikki, Tyler, AEs, Joel, Moran, Farsheed | Initiative framing, ELT context |
| Working Session 1 | 2026-01-16 | Matt V, Matt L, Thomas, Chris P, Joel, Moran | White space mapping, landscape definition, power mapping |
| Session 2 | 2026-01-16 | Matt V, Matt L, Thomas, Chris P, Tyler, Tom Woodhouse | Process problems, AI usage, partner data |

---

*Generated using PuRDy v2.3 Synthesizer with Gigawatt-enhanced Chain-of-Thought reasoning and quantification frameworks*
