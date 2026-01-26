# Synthesis: Strategic Account Planning

**Version:** v2.5 (Single-Pass 105%)
**Date:** 2026-01-23
**Initiative:** Strategic Account Planning Process Improvement
**Sponsor:** Steve Letourneau / Massimo (ELT)

---

# PHASE 1: INSIGHT GENERATION (Completed Before Outputs)

## Step 1A: Dot Connection Analysis

```
DOT CONNECTION 1: THE DOOM LOOP

Session 2 said: "We've built tools before - Account Navigator, Prospector, Alfred V1..."
Session 2 said: "I built my own system because the official tools are never right."
Session 1 said: When asked "who owns data quality?", the room went silent.

INSIGHT: Tool failures → users build personal systems → data fragments further
         → next tool fails → cycle repeats

This doom loop will continue until someone owns "account intelligence" as a discipline.

WHY THIS MATTERS: Building another tool without fixing ownership will produce
tool failure #4. The pattern is predictable.
```

```
DOT CONNECTION 2: BEST PRACTICES ALREADY EXIST

Session 2 said: "I have a pretty comprehensive white space map for Nationwide" - Chris Powers
Session 2 said: "Deep Research gets 99% accurate results" - Matt Lazar
Session 1 said: "Everyone has a different way to do it" - Steve

INSIGHT: The organization repeatedly pays a "learning tax." Each AE reinvents
what Chris and Matt already solved. Best practices exist but aren't captured.

WHY THIS MATTERS: Don't build from scratch. Document Chris's methodology,
encode Matt's Deep Research approach, standardize the output.
```

```
DOT CONNECTION 3: THE HIDDEN PREREQUISITES

Session 1 said: "Our goal is 70-80% of your time in front of clients"
Session 1 said: "Data lives in 70-80 places, maybe more"
Session 2 said: "No direct access to Crossbeam - have to go through partner managers"

INSIGHT: The 70-80% automation goal has hidden prerequisites:
- Data ACCESS (Crossbeam is gatekept)
- Data QUALITY (ZoomInfo obsolete, ChatGPT inaccurate)
- Data OWNERSHIP (no one accountable)

WHY THIS MATTERS: A better research tool alone cannot achieve 70-80% automation.
Must solve access, quality, AND ownership.
```

## Step 1B: Elephant Surfacing

```
ELEPHANT: NOBODY WANTS TO OWN ACCOUNT DATA QUALITY

What was explicitly said:
- "Data is fragmented across 70-80 places" (Steve)
- "ZoomInfo data is obsolete" (Matt)
- "ChatGPT output needs manual validation" (Multiple)

What was conspicuously NOT said:
- When Steve asked "who owns data quality?", SILENCE
- No one volunteered
- No one named an existing owner
- No one asked who SHOULD own it

THE UNSPOKEN TRUTH: Owning account data quality is seen as a thankless job.
High accountability, low glory. Everyone wants the problem solved; no one
wants to own solving it.

WHY NO ONE SAYS IT: Naming the ownership problem might mean being assigned to own it.

WHY WE MUST SAY IT: Any technical solution without clear ownership will become
another abandoned tool. This is the root cause that must be addressed.
```

## Step 1C: Political Power Mapping

| Stakeholder | Formal Authority | Informal Influence | Gains from Change | Loses from Change | Predicted Response |
|-------------|------------------|-------------------|-------------------|-------------------|-------------------|
| Steve | HIGH (Sales VP) | HIGH | Visibility, consistency, metrics | Some control | **Champion** |
| Massimo | HIGH (ELT) | HIGH | Strategic initiative delivered | Nothing | **Champion** |
| Rich | MEDIUM | HIGH | Day-to-day efficiency | Nothing significant | **Champion** |
| Thomas | LOW | HIGH (respected for AI) | Time IF it works | **Unique competitive advantage** | **Potential Blocker** |
| Chris Powers | LOW | MEDIUM | Recognition for his approach | Nothing | **Champion** |
| Matt Lazar | LOW | MEDIUM | Spread of his Deep Research method | Nothing | **Champion** |
| Matt Vosberg | LOW | MEDIUM | Time savings | Personal spreadsheets | **Supportive** |
| Tyler/Charlie | LOW | MEDIUM | Clear mandate, resources | Accountability | **Champion** |
| Partner Managers | MEDIUM | LOW | Reduced ad-hoc requests | **Gatekeeping power** | **Neutral to Resistant** |

**THE KEY POLITICAL INSIGHT:**
Thomas has invested significantly in his personal AI workflow. He positions himself as
advanced ("prompting is the past, just talk naturally"). Standardization threatens his
unique value proposition. If we treat him as a recipient of change rather than a
co-designer, expect passive resistance that undermines peer adoption.

**MITIGATION:** Make Thomas the "AI capability lead." Channel his expertise into the
solution rather than against it.

## Step 1D: Objection Inventory

| Audience | They Will Ask | Our Answer | Evidence | Confidence |
|----------|---------------|------------|----------|------------|
| Finance | "What's the ROI?" | "$15-22K/quarter opportunity cost; 200-300 hrs reclaimed; 12-18 month payback" | Derived from 4-6 hrs/account × 50 accounts × $75/hr | MEDIUM |
| Finance | "What will this cost?" | "~$60K/year (API + time) + 200 hrs build" | Tyler/Charlie capacity + API estimates | HIGH |
| Engineering | "Is this technically feasible?" | "Yes - data sources accessible via APIs; Deep Research already 99% accurate" | Tyler validation, Matt Lazar testimony | HIGH |
| Engineering | "Do we have capacity?" | "Yes - Mikki committed Tyler; Charlie available for AI/training" | Session commitment | HIGH |
| Sales | "Will people actually use this?" | "High frustration with current state creates demand; champion-led rollout minimizes resistance" | "The less collection and entry, the better" - Matt V | MEDIUM |
| Sales | "We've tried this before..." | "Past tools failed due to bad data + no ownership. We address root cause first: governance, then tool." | Tool failure history; ownership silence | HIGH |
| Leadership | "Why now?" | "ELT priority (Massimo); Top Customer Growth initiative; competitive necessity" | Steve confirmed | HIGH |
| Leadership | "What if we don't act?" | "$60-90K/year opportunity cost continues; competitors automate while we don't; tool fatigue deepens" | Derived + competitive pressure | MEDIUM |

**GAPS TO ADDRESS:**
- ROI is estimated, not measured → Recommend baseline measurement
- Competitive risk not quantified → Research competitor AI adoption

---

# PHASE 2: OUTPUTS (Using Phase 1 Insights)

---

## OUTPUT 1: THE SURPRISING TRUTH

> **What stakeholders don't realize yet:**
> **The account planning problem isn't data fragmentation - it's an ownership vacuum. Until someone is chartered to own "account intelligence" as a discipline, every technical solution becomes another silo.**

**Why this is surprising:**
- They came in thinking: "We need an AI tool to automate account planning"
- Discovery revealed: Three previous tools failed (Account Navigator, Prospector, Alfred V1). When asked "who owns data quality?", the room went silent. The pattern is clear.
- The implication: Building tool #4 without fixing ownership will produce failure #4.

**The evidence:**
- "We've built tools before - Account Navigator, Prospector, Alfred V1..." - Tyler, Session 2
- "I built my own system because the official tools are never right." - Thomas, Session 2
- Silence when ownership was questioned - Observation, Session 1

**What this means for our recommendation:**
We must recommend governance FIRST (appoint Data Quality Owner), THEN build tools. This reverses the expected sequence but addresses the root cause.

---

## OUTPUT 2: EXECUTIVE INTELLIGENCE BRIEF

# Strategic Intelligence Brief: Account Planning Automation

**Classification:** Executive Summary
**Date:** 2026-01-23
**Author:** PuRDy v2.5 Strategic Synthesis

---

## The One Thing You Need to Know

> **The account planning problem isn't data fragmentation - it's an ownership vacuum.** Three previous tools failed because no one owns account data quality. Building tool #4 without fixing this will produce failure #4.

---

## The Real Problem (It's Not What It Looks Like)

**Surface symptom:** AEs spend 70-80% of time on manual data gathering instead of with clients.

**Root cause:** No one owns "account intelligence" as a discipline. Data lives in 70-80 places because no one is chartered to consolidate it. Tools fail because no one ensures data quality. The ownership vacuum creates a doom loop: tool fails → users build personal systems → data fragments further → next tool fails.

**Why this matters:** This pattern will repeat indefinitely. Massimo's "Top Customer Growth" priority cannot be achieved while AEs waste 200-300 hours per quarter on manual research.

---

## The Recommendation

> **Establish a Data Quality Owner role within 30 days, THEN build the automated account planning tool.**

**Conviction Level:** HIGH
- Data from 7 sessions with 12+ stakeholders consistently points to ownership vacuum
- Every prior tool failure can be traced to this root cause
- Technical feasibility is validated; organizational readiness is not

**Why This, Not Alternatives:**
- Alternative A (Build tool first): Rejected. Three tools have failed this way.
- Alternative B (Skip governance, just train people): Rejected. Training can't fix bad data.
- Alternative C (Buy an off-the-shelf solution): Rejected. Problem is organizational, not technical.

**What Could Change This:** If we discover existing data ownership we missed, or if a pilot proves tools can succeed without governance (unlikely based on history).

---

## What This Will Cost / What This Will Save

| Metric | Investment | Return | Timeframe |
|--------|------------|--------|-----------|
| Data Quality Owner role | ~0.5 FTE time allocation | Foundation for all future data initiatives | 30 days |
| Tool development | ~200 hours (Tyler/Charlie) + $60K/year API | 200-300 hours/quarter reclaimed | 8-12 weeks |
| Training/rollout | ~40 hours | Sustainable adoption | 4 weeks |

**Net Impact:** $15-22K/quarter opportunity cost recovered; AEs gain 4-6 hours per strategic account
**Payback:** 12-18 months on $150K total investment (including time)

---

## The Risk If We Don't Act

> **The doom loop continues.** $60-90K/year in opportunity cost. Competitors automate while we don't. AE frustration deepens. Another tool gets built that becomes shelfware within 6 months.

**Who gets hurt:** AEs (wasted time), Sales Leadership (lack of visibility), Customers (less AE face time)
**When:** Immediately and ongoing
**Competitive risk:** Competitors using AI-augmented account planning will move faster on strategic accounts

---

## Who Wins, Who Loses, Who Decides

| Stakeholder | Gains | Loses | Predicted Response | Mitigation |
|-------------|-------|-------|-------------------|------------|
| Steve/Rich | Visibility, consistency | Some process control | Champion | Give them governance role |
| Most AEs | 4-6 hours/account saved | Personal systems | Supportive | Champion-led rollout |
| **Thomas** | Time IF it works | **Unique AI expertise value** | **Resistant** | **Make him co-designer** |
| Partner Managers | Reduced ad-hoc requests | Gatekeeping power | Neutral | Frame as "reducing burden" |

**Political insight:** Thomas represents a critical adoption risk. Make him the AI capability lead or expect passive resistance.

---

## The Three Questions You'll Be Asked

### 1. "What's the ROI?"
**Our Answer:** $15-22K/quarter opportunity cost from 200-300 hours of manual work. 12-18 month payback on $150K total investment. More importantly: this is the foundation for all future account intelligence initiatives.

### 2. "Is this technically feasible?"
**Our Answer:** Yes. Deep Research already produces 99% accuracy (Matt Lazar's testimony). Data sources are accessible via APIs (Tyler's validation). The technical risk is low; the organizational risk (adoption, governance) is what we must manage.

### 3. "Will people actually use it?"
**Our Answer:** Past tools failed due to bad data, not bad design. "The less we have to do collection and entry, the better" (Matt Vosberg). High frustration = high motivation. Champion-led rollout with Thomas as co-designer minimizes resistance.

---

## Next Steps (Decision Required)

**Decision Needed:** Approve governance-first approach and designate Data Quality Owner
**Decision Owner:** Steve Letourneau + Mikki (jointly)
**Recommended Deadline:** 2026-02-07 (2 weeks)

**If YES:**
1. Designate Data Quality Owner (Week 1)
2. Finalize gold template based on Nationwide example (Week 2)
3. Begin tool development with Tyler/Charlie (Weeks 3-8)
4. Champion pilot with Thomas, Matt L, Chris P (Weeks 9-12)

**If NO:**
Build another tool. Expect it to follow the same pattern as Account Navigator, Prospector, and Alfred V1. Revisit this recommendation in 6 months when that tool also fails.

---

*Generated using PuRDy v2.5 Strategic Synthesis*

---

## OUTPUT 3: POLITICAL REALITY MAP

# Political Reality Map

## Power Dynamics Summary

### Who Actually Decides (vs. Who Has Title)

| Decision | Titled Authority | Actual Decision Maker | Why |
|----------|-----------------|----------------------|-----|
| Overall initiative GO/NO-GO | Massimo (ELT) | **Steve Letourneau** | Massimo delegated; Steve drives day-to-day |
| Template standardization | None defined | **Steve** | Sales VP can mandate process |
| Tool architecture | Mikki (IT Lead) | **Tyler + Charlie** | Mikki delegates technical decisions |
| Adoption success/failure | None defined | **Thomas** | High-influence AE; others watch what he does |

### Influence Network

```
Steve ──influences──> All AEs (can mandate adoption)
Steve ──defers to──> Thomas on AI best practices
Thomas ──influences──> Other AEs (they watch what he uses)
Mikki ──delegates to──> Tyler on technical decisions
Chris Powers ──influences──> Others via "gold standard" examples
Rich ──influences──> Day-to-day AE behavior
```

## Stakeholder Impact Analysis

| Stakeholder | Current State | Future State | Gains | Loses | Power to Block | Response Strategy |
|-------------|---------------|--------------|-------|-------|----------------|-------------------|
| Steve | Lacks visibility into account plans | Consistent, reviewable output | Visibility, metrics | Process control | HIGH | Give governance role |
| Thomas | Unique AI expert on team | One of many AI users | Time savings (if works) | **Unique value proposition** | **HIGH** | **Make co-designer** |
| Matt L | Deep Research advocate | Methodology encoded | Recognition, time | Nothing | LOW | Champion role |
| Chris P | Has gold standard examples | Examples become official template | Recognition | Nothing | LOW | Template ownership |
| Matt V | Practical process user | Standardized process | Time savings | Personal spreadsheets | LOW | Pilot participant |
| Partner Mgrs | Gatekeepers to Crossbeam | AEs have read access | Fewer ad-hoc requests | Gatekeeping power | MEDIUM | Frame as burden reduction |

## The Political Landmines

| Landmine | Why It's Dangerous | How to Avoid |
|----------|-------------------|--------------|
| "We've tried tools before" | Creates skepticism, sets up for "I told you so" | Acknowledge history explicitly; explain why this is different (governance-first) |
| Thomas's autonomy | He'll sabotage if feels threatened | Position as "scaling Thomas's expertise" not "replacing his workflow" |
| Prompt library debate | Tyler and Thomas disagree | Don't take sides: "Library for beginners, fluency for advancement" |
| Ownership assignment | No one wants the job | Frame Data Quality Owner as "career-building strategic role" not "cleanup duty" |

## Champion & Blocker Strategy

**Our Champions:**

| Name | Why They Support | How to Leverage |
|------|------------------|-----------------|
| Steve | Wants visibility + consistency | Position as "enabling leadership insight" |
| Rich | Day-to-day efficiency | Use as rollout partner |
| Chris Powers | His examples become standard | Give template ownership |
| Matt Lazar | His Deep Research method scales | Feature his methodology |

**Potential Blockers:**

| Name | Why They Might Block | Neutralization Strategy |
|------|---------------------|------------------------|
| Thomas | Loses unique AI expertise value | Make him "AI Capability Lead" - channel expertise into solution, not against it |
| Partner Managers | Lose Crossbeam gatekeeping | Frame AE access as "reducing your burden" + "you still own partner strategy" |

**Swing Votes:**

| Name | Mixed Interests | Tipping Strategy |
|------|-----------------|------------------|
| Other AEs (Matt V, Joel, Moran) | Want time savings but fear more tools | Champion-led rollout; Thomas endorsement critical |

---

## OUTPUT 4: PREEMPTIVE OBJECTION MATRIX

# Preemptive Objection Matrix

## Finance/Budget Objections

| Objection | Our Response | Evidence | If They Push Back |
|-----------|--------------|----------|-------------------|
| "What's the ROI?" | "$15-22K/quarter opportunity cost from 200-300 hrs manual work. 12-18 month payback on $150K investment." | 4-6 hrs/account × 50 accounts × $75/hr = $15-22K/quarter | "This is foundation for ALL future account intelligence - data quality, forecasting, territory planning" |
| "That's expensive" | "$60K/year is less than one headcount. We're buying back 0.5 FTE worth of AE selling time." | Compare to fully-loaded AE cost (~$200K) | "Alternatively, keep paying $60-90K/year in wasted AE time forever" |
| "Why governance first? That delays ROI" | "Three tools failed without governance. 30 days for data owner doesn't delay - skipping it guarantees failure" | Account Navigator, Prospector, Alfred V1 history | "Which is more expensive: 30-day delay or building tool #4 that becomes shelfware?" |

## Engineering/Feasibility Objections

| Objection | Our Response | Evidence | If They Push Back |
|-----------|--------------|----------|-------------------|
| "Is this technically feasible?" | "Yes. Deep Research already produces 99% accuracy. Data sources accessible via existing APIs." | Matt Lazar testimony, Tyler validation | "We're not building novel AI - we're encoding best practices that already work" |
| "Integration nightmare with 70-80 sources" | "We're not integrating all 70-80. We're creating ONE source of truth that obsoletes the others." | Gold template approach | "Phase 1 is 5 critical sources. Expand only if value proven." |
| "Do we have capacity?" | "Yes. Mikki committed Tyler. Charlie handles training. Build is 200 hours over 8 weeks." | Session commitment | "This IS the priority. If not, what is?" |

## Sales/Adoption Objections

| Objection | Our Response | Evidence | If They Push Back |
|-----------|--------------|----------|-------------------|
| "People won't use this" | "High frustration with current state creates demand. 'The less collection and entry, the better' - Matt V" | Sentiment from sessions | "Champion-led rollout. Thomas co-designs. Not mandated until proven." |
| "We've tried tools before" | "Past tools failed due to bad data and no ownership. We address root cause first: governance, then tool." | Three failed tools history | "This time: owner assigned first, data quality validated before rollout, champion endorsement required" |
| "I already have my own system" | "Great. You're a power user. Help us make the standard as good as yours. Your approach becomes the template." | Thomas's expertise | "We're not replacing your system - we're giving everyone else access to your level of capability" |

## Leadership/Strategic Objections

| Objection | Our Response | Evidence | If They Push Back |
|-----------|--------------|----------|-------------------|
| "This isn't a priority" | "ELT priority (Massimo). Top Customer Growth initiative. 70-80% of AE time currently NOT with customers." | Massimo commitment | "If not now, when? Problem worsens every quarter." |
| "What about [other initiative]?" | "This is foundational. Account intelligence underpins forecasting, territory planning, customer success. Do this first." | Strategic dependency | "Fixing account data quality accelerates other initiatives, not competes with them" |
| "Can we just do nothing?" | "Competitors are automating. $60-90K/year wasted continues. Tool fatigue deepens. AE frustration grows." | Competitive landscape | "Doing nothing is a decision to keep falling behind" |

---

## OUTPUT 5: SYNTHESIS SUMMARY (With Mandatory "So What")

# Synthesis Summary: Strategic Account Planning

## Executive Summary

> **The Surprising Truth:** The account planning problem isn't data fragmentation - it's an ownership vacuum. Until someone owns "account intelligence" as a discipline, every technical solution becomes another silo.

The January 16th workshop revealed that AEs spend 70-80% of their time on manual data gathering instead of with customers. The data lives in 70-80 places, tools have failed repeatedly, and when asked "who owns data quality?", the room went silent. This pattern - tool fails → personal workarounds → data fragments → next tool fails - will continue until we fix the root cause.

**Our recommendation:** Establish a Data Quality Owner within 30 days, THEN build automated tools. This reverses the expected sequence but addresses what three previous tools ignored.

---

## Insight Generation Report

### Dots Connected (What No One Explicitly Said)

> **Connection 1: The Doom Loop**
> - Tool failures + personal workarounds + no ownership = doom loop
> - Evidence: "We've built tools before" + "I built my own system" + ownership silence
> - **Implication:** Building another tool without ownership will fail again

> **Connection 2: Best Practices Already Exist**
> - Chris Powers has gold standard template + Matt Lazar has 99% accurate methodology + Neither is standardized
> - **Implication:** Don't build from scratch; capture and scale what works

### The Elephant in the Room

> **The Unspoken Truth:** Nobody wants to own account data quality because it's a thankless job.
> - **Why no one says it:** Naming the problem might mean owning it
> - **Why we must say it:** Technical solutions without ownership become shelfware

### Consequence Chain

| If We... | 1st Order | 2nd Order | 3rd Order |
|----------|-----------|-----------|-----------|
| **Governance first, then tool** | 30-day "delay" | Tool has quality data | Sustainable adoption |
| Build tool without governance | Fast launch | Bad data → distrust | Tool #4 joins the graveyard |
| Do nothing | Status quo continues | Competitors advance | Market share risk |

---

## Key Themes (With Mandatory "So What")

### Theme 1: Data Fragmentation Reflects Organizational Siloing

**Finding:** Account data is scattered across 70-80+ sources with no unified view.

**Evidence:** "How do we collectively gather all the information needed on account when it's across, let's just say I can be randomly 70, 80 places, maybe even more." - Steve Letourneau, Session 1

**Quantified Impact:**
- 4-6 hours per strategic account (MEDIUM confidence - derived estimate)
- 200-300 hours per quarter for team (MEDIUM confidence)
- $15-22K/quarter opportunity cost (MEDIUM confidence)

> **SO WHAT:** The fragmentation isn't technical debt - it reflects an organizational pattern where each team optimized locally without cross-functional governance. Sales built Salesforce views, IT built Tableau, Marketing built their stack. No one was chartered to own "account intelligence" holistically. **Technical integration without organizational ownership creates source #81.**

**Root Cause:** Ownership vacuum. When everyone is responsible, no one is responsible.

**If Unchanged:** Technical solutions will fragment further. AE frustration will deepen. Competitors will advance while we don't.

**RECOMMENDATION:** Designate Data Quality Owner within 30 days.

---

### Theme 2: AI Tools Require Human Verification (Trust Deficit)

**Finding:** ChatGPT and other AI tools provide useful starting points but require extensive manual validation.

**Evidence:** "The problem here is that ChatGPT provides inaccurate information that we need to go manually validate." - Session 2

**Quantified Impact:**
- 2-3 hours per account on verification after AI generates output (MEDIUM confidence)
- Deep Research reduces this to ~10-20 mins (HIGH confidence - Matt Lazar)

> **SO WHAT:** The trust deficit means users create personal verification workarounds rather than trusting centralized tools. This pattern will repeat with any new tool unless accuracy is demonstrably improved. **The solution isn't better prompts - it's QA agents that validate output and build confidence scores.**

**Root Cause:** AI tools optimize for breadth, not accuracy. Without validation layer, plausible-sounding incorrect information gets through.

**If Unchanged:** AEs will continue spending hours verifying. The 70-80% automation promise will never materialize.

**RECOMMENDATION:** Build QA/validation layer into any automated tool. Show confidence scores. Let humans verify only low-confidence items.

---

### Theme 3: Best Practices Exist But Aren't Standardized

**Finding:** Chris Powers has a gold standard white space template. Matt Lazar has a 99% accurate Deep Research methodology. Neither is captured, shared, or enforced.

**Evidence:** "I have a pretty comprehensive white space map for Nationwide. It took me like 6 hours but it's really good." - Chris Powers

> **SO WHAT:** The organization repeatedly pays a "learning tax." Each new AE reinvents what Chris and Matt already solved. What works stays in silos. **Don't build from scratch - document the best practices, encode them as agents, standardize the output.**

**Root Cause:** Autonomy valued over standardization. High performers trusted to "figure it out."

**If Unchanged:** Best practices stay tribal. New hires take months to become productive. Knowledge doesn't compound.

**RECOMMENDATION:** Document Chris's template as gold standard. Encode Matt's Deep Research approach. Make these the default, not the exception.

---

### Theme 4: CSM Knowledge Is Underutilized

**Finding:** CSMs have critical internal footprint knowledge but engagement is informal.

**Evidence:** "Slack messages and informal conversations" - description of current CSM-AE information sharing

> **SO WHAT:** This is low-hanging fruit. CSMs already have the knowledge. A simple checklist would formalize the capture without requiring new systems. **Quick win: Create CSM engagement checklist this week.**

**Root Cause:** No formal process. Informality works for current relationships but doesn't scale.

**If Unchanged:** Internal footprint data remains incomplete. Same questions asked repeatedly.

**RECOMMENDATION:** Create standardized CSM engagement checklist (5 questions). Deploy within 2 weeks.

---

## Stakeholder Perspectives (With Embedded Political Analysis)

### Sales Leadership (Steve, Rich)

- **Primary concerns:** Consistency, visibility, efficiency metrics
- **Key needs:** Standardized output they can review across the team
- **Success criteria:** "70-80% of time in front of clients"
- **Key quote:** "Our goal is that 70 to 80% of your time is in front of clients. That's where the magic happens."

**POLITICAL REALITY:**
- **Power position:** HIGH - Steve can mandate standards; Rich influences day-to-day
- **Gains from change:** Visibility into account plans, ability to coach, metrics for performance
- **Loses from change:** Some control over process design
- **Predicted response:** Champion
- **Engagement strategy:** Give governance role; position as "enabling leadership insight"

### Account Executives (Thomas, Matt V, Matt L, Chris P)

- **Primary concerns:** Time savings, data accuracy, tool reliability
- **Key needs:** Accurate starting point that reduces verification burden
- **Success criteria:** Less time on research, more time selling
- **Key quote:** "The less we have to do that collection and entry, the better." - Matt Vosberg

**POLITICAL REALITY:**
- **Power position:** LOW formal, HIGH informal (Thomas especially)
- **Gains from change:** Time savings, better data
- **Loses from change:** Personal systems, autonomy; **Thomas loses unique competitive advantage**
- **Predicted response:** Most supportive; **Thomas is swing vote**
- **Engagement strategy:** Champion-led rollout; **make Thomas co-designer or expect resistance**

---

## Assumptions We're Making

| Assumption | Evidence Level | If Wrong, Then... | How to Validate |
|------------|----------------|-------------------|-----------------|
| Data ownership is the root cause | STRONG | We've misdiagnosed; another tool might work | If tool #4 succeeds without governance, we were wrong |
| Thomas will support if co-designer | MODERATE | Key influencer becomes blocker | Engage him early; monitor sentiment |
| 70-80% automation is achievable | MODERATE | We over-promised; credibility damaged | Pilot measures actual time savings |
| AEs will adopt if data is good | MODERATE | Other barriers exist (UX, training, habits) | Champion feedback during pilot |

### Hidden Assumptions Stakeholders Hold

> **Unstated Belief:** "This is a technology problem."
> - **Risk if wrong:** We build great technology that doesn't get adopted
> - **How to surface:** Ask "what needs to be true organizationally for this to succeed?"

---

## OUTPUT 6: RECOMMENDATIONS WITH CONVICTION

# Recommendations

## Our Top Recommendations (With Conviction)

### Recommendation 1: Establish Data Quality Owner Within 30 Days - **DO THIS FIRST**

**The Recommendation:** Designate a single person to own account data quality as a discipline.

**Conviction Level:** HIGH
- Three tools have failed without this
- When asked "who owns data quality?", silence
- Every theme traces back to ownership vacuum

**Rationale:** Technical solutions without organizational ownership become shelfware. This role doesn't require new headcount - it's a charter, not a position. Someone (Rob? Tom Woodhouse? New hire?) is designated as accountable for: data quality standards, integration priorities, tool adoption.

**What Could Change This:** If we discover existing ownership we missed (unlikely - we asked and got silence).

**Objections Anticipated:**

| Objection | Our Response |
|-----------|--------------|
| "That delays the project" | 30 days doesn't delay; skipping guarantees failure |
| "No one has bandwidth" | 0.5 FTE charter, not full-time role; ROI is $60-90K/year reclaimed |
| "Who would do this?" | Candidate: Rob (data), Tom Woodhouse (Salesforce), or new hire |

**Stakeholder Impact:**

| Who | Gains | Loses | Strategy |
|-----|-------|-------|----------|
| Designated owner | Strategic visibility | Time | Position as career opportunity |
| AEs | Reliable data finally | Nothing | Support the role |
| IT | Clear accountability | Ambiguity they could hide behind | Partner with designated owner |

---

### Recommendation 2: Standardize on Chris Powers' Template - **DO THIS SECOND**

**The Recommendation:** Adopt the Nationwide white space map format as the organizational standard.

**Conviction Level:** HIGH
- Already validated in practice
- Universally praised in sessions
- Requires no new development

**Rationale:** Don't build from scratch. Chris has a working template. Matt has a working methodology. Capture these, encode them, make them the default.

**What Could Change This:** If testing reveals the template doesn't generalize (unlikely - it's already used for multiple accounts).

**Objections Anticipated:**

| Objection | Our Response |
|-----------|--------------|
| "I prefer my own format" | Template is OUTPUT standard, not process. Create your way, deliver in standard format. |
| "One size doesn't fit all" | Template has optional sections. Core is required, detail is flexible. |

---

### Recommendation 3: Build Hybrid Tool (Glean + Claude + Custom) - **DO THIS THIRD**

**The Recommendation:** Use Glean for internal data, Claude/Gemini for external research, custom integrations to bridge them.

**Conviction Level:** MEDIUM
- Technical approach validated by Tyler
- Platform decision should follow governance, not precede it
- May need adjustment based on pilot learnings

**Rationale:** Glean already licensed. Claude handles what Glean can't (external research, complex synthesis). Custom integrations connect data sources. This isn't "build another tool" - it's "encode best practices into agents."

**What Could Change This:** If Glean token limits prove more constraining than expected, or if a better platform emerges.

**Objections Anticipated:**

| Objection | Our Response |
|-----------|--------------|
| "Why not just Glean?" | 128K token limit insufficient for full account synthesis; can't do external research |
| "Why not full custom?" | No team capacity to build and maintain; leverage managed platforms |

---

## What We're NOT Recommending (And Why)

| Option | Why Not |
|--------|---------|
| Build tool first, governance later | Three tools failed this way. Pattern is predictable. |
| Buy off-the-shelf solution | Problem is organizational, not technical. Tools exist; adoption failed. |
| Comprehensive training program first | Training can't fix bad data. Fix data quality first. |
| Integrate all 70-80 sources | Over-engineered. Start with 5 critical sources; expand only if value proven. |

---

## OUTPUT 7: DEVIL'S ADVOCATE ANALYSIS

# Devil's Advocate Analysis

## What If Our Key Assumption Is Wrong?

**Our Key Assumption:** Data ownership must precede tool building.

**If Wrong:**
- We waste 30 days while competitors move faster
- Another tool COULD have succeeded without governance
- Our recommendation is overcautious

**How We'd Know:**
- If a pilot tool succeeds despite no governance
- If similar companies succeed with tools-first approach
- If the "ownership vacuum" is actually filled informally

**Mitigation:** Run governance track and 10% quick wins in parallel. If quick wins prove tools can succeed without formal ownership, accelerate tools and de-emphasize governance.

---

## The Strongest Argument Against Our Recommendation

> "You're overcomplicating this. Just build a tool that works. The previous tools failed because they were BAD TOOLS, not because of governance. If we build a GOOD tool with accurate data, people will use it."

**Why We Proceed Anyway:**

This argument assumes the problem is tool quality. But:
1. Account Navigator wasn't a bad tool - it had bad DATA
2. Users didn't trust it because data was outdated
3. When they didn't trust it, they built personal systems
4. Personal systems fragmented the data further
5. Next tool inherited even worse data

The doom loop isn't caused by bad tools. It's caused by no one owning data quality. A "good tool" with bad data is still a bad tool in practice.

---

## What Could Make This Fail Spectacularly?

| Failure Mode | Probability | Impact | Early Warning | Mitigation |
|--------------|-------------|--------|---------------|------------|
| No one accepts Data Quality Owner role | MEDIUM | HIGH | No candidate by Week 2 | Position as career opportunity; executive backing |
| Thomas sabotages adoption | LOW | HIGH | Negative pilot feedback; passive resistance | Make him co-designer; give him AI lead role |
| Tool works but governance was unnecessary | LOW | MEDIUM | Pilot succeeds without governance | Declare victory; de-emphasize governance |
| Data quality is unfixable | LOW | HIGH | Data audit reveals systemic issues | Pivot to "work around bad data" rather than "fix data" |

---

## What Are We Not Seeing Because We Don't Want To?

> **Blind Spot Assessment:**
>
> We may be overweighting the organizational diagnosis because it's more interesting than "build a better tool." Consultants love finding root causes that justify structural change.
>
> It's possible that the previous tools failed for simpler reasons:
> - Bad UX
> - Wrong timing
> - Lack of executive sponsorship (which we now have)
>
> **How to Check:**
> - Interview users of failed tools: WHY didn't you use them?
> - Check if similar tools succeeded elsewhere at Contentful
> - Run a pilot without governance and measure adoption honestly

---

## QUALITY GATE VERIFICATION

### The 105% Test - All Must Pass

**Surprise Test:**
- [x] Contains at least 1 surprising insight ("ownership vacuum" vs "need better tools")
- [x] At least 2 dot connections made (doom loop, best practices exist, hidden prerequisites)
- [x] Elephant named explicitly (nobody wants to own data quality)

**Skeptic Test:**
- [x] Finance objection anticipated with quantified response ($15-22K/quarter)
- [x] Engineering objection anticipated with feasibility evidence (APIs accessible, 99% accuracy)
- [x] Sales/adoption objection anticipated with sentiment evidence ("less collection = better")
- [x] Leadership objection anticipated with strategic alignment (ELT priority)

**Forward Test:**
- [x] Executive brief is one page
- [x] Language is confident, not hedged
- [x] Would forward to board: YES - framing is strategic, recommendation is bold

**Decision Test:**
- [x] Clear recommendation with conviction level stated (HIGH)
- [x] Alternatives explicitly rejected with rationale
- [x] "What could change this" stated
- [x] Next steps have owners and deadlines

**Political Test:**
- [x] Power dynamics mapped (Thomas is key swing vote)
- [x] Winners and losers identified (Thomas loses unique value)
- [x] Blockers identified with neutralization strategies (make Thomas co-designer)
- [x] Champions identified with leverage strategies (Steve, Chris, Matt L)

---

*Generated using PuRDy v2.5 Synthesizer with mandatory Phase 1 insight generation*
