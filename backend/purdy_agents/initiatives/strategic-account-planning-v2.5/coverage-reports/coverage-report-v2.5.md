# Coverage Report: Strategic Account Planning

**Version:** v2.5 (Single-Pass 105%)
**Report Date:** 2026-01-23
**Sessions Completed:** 7 of 7
**Synthesis Readiness:** READY

---

## SECTION 1: INSIGHT AMMUNITION (For Synthesizer)

> **PURPOSE:** Pre-generate insights so Synthesizer doesn't start from scratch

### Dot Connections Identified

> **Connection 1: The Ownership Vacuum Creates a Doom Loop**
> - Finding A: "We've built tools before - Account Navigator, Prospector, Alfred V1..." - Tyler, Session 2
> - Finding B: "I built my own system because the official tools are never right." - Thomas, Session 2
> - Finding C: "When asked 'who owns data quality?', the room went silent" - Observation, Session 1
> - **INSIGHT:** Tool failures → users build personal systems → data fragments further → next tool fails. This doom loop will repeat until someone owns "account intelligence" as a discipline.
> - **Implication for Synthesis:** The solution isn't a better tool - it's establishing ownership FIRST, then building a tool.

> **Connection 2: Best Practices Exist But Aren't Standardized**
> - Finding A: "I have a pretty comprehensive white space map for Nationwide. It took me like 6 hours but it's really good." - Chris Powers, Session 2
> - Finding B: "Matt L gets great results with Deep Research - 99% accurate" - Multiple sources
> - Finding C: "Everyone has a different way to do it." - Steve, Session 1
> - **INSIGHT:** The organization repeatedly pays a "learning tax" - each AE reinvents what others already solved. Best practices exist in silos but aren't captured or shared.
> - **Implication for Synthesis:** Don't build from scratch - document Chris's methodology, encode it as an agent, and standardize the output format.

> **Connection 3: The 70-80% Goal Has a Hidden Prerequisite**
> - Finding A: "Our goal is that 70-80% of your time is in front of clients" - Steve, Session 1
> - Finding B: "Data lives in 70-80 places, maybe more" - Steve, Session 1
> - Finding C: "No one has direct access to Crossbeam. We have to go through partner managers." - Matt V, Session 2
> - **INSIGHT:** The 70-80% automation goal can't be achieved by building a better research tool alone. It requires solving the data access problem (Crossbeam gating, Tableau fragmentation) and the data quality problem (ZoomInfo staleness, ChatGPT inaccuracy).
> - **Implication for Synthesis:** The recommendation must address data governance AND tool building - not just tools.

### Elephant in the Room

> **The Unspoken Dynamic: Nobody Wants to Own Account Data Quality**
> - What people SAID: "The data is fragmented across 70-80 places" (Steve), "ZoomInfo data is obsolete" (Matt), "ChatGPT output needs manual validation" (Multiple)
> - What people AVOIDED: Who should own this? When Steve asked "who owns data quality?", the room went silent.
> - What the pattern SUGGESTS: Owning account data quality is seen as a thankless job. High accountability, low glory. Everyone wants the problem solved, but no one wants to own solving it.
> - **Why no one says it:** Naming the ownership problem might mean being assigned to own it.
> - **Why we must say it:** Any technical solution without clear ownership will become another abandoned tool.
> - **Implication for Synthesis:** Synthesizer MUST name this elephant explicitly and recommend a Data Quality Owner role.

### Surprising Findings

| We Expected | We Found | Implication |
|-------------|----------|-------------|
| AEs want automation | AEs want accuracy MORE than speed | Validation/QA is more important than generation |
| Tool fatigue is about too many tools | Tool fatigue is about tools with BAD DATA | Good data + fewer tools beats many tools |
| CSM input is formal | CSM engagement is "Slack messages and informal conversations" | Major process gap - quick win to fix |
| Crossbeam data is accessible | Crossbeam access is GATEKEPT through PMs | Access fix could be immediate win |
| Deep Research is experimental | Deep Research is already producing "99% accurate" results | Spread this practice, don't reinvent |

**Biggest Surprise:** The problem isn't tools or technology - it's organizational. Data ownership vacuum is the root cause.
**Why Synthesizer Should Highlight This:** It reframes the entire initiative. They came thinking "build us a tool." We should say "appoint an owner first, THEN build the tool."

---

## SECTION 2: POLITICAL INTELLIGENCE (For Synthesizer)

> **PURPOSE:** Give Synthesizer the political map so outputs address power dynamics

### Power Dynamics Observed

| Stakeholder | Formal Authority | Informal Influence | Signals Observed |
|-------------|------------------|-------------------|------------------|
| Steve Letourneau | HIGH (Sales VP) | HIGH | Sets direction, commits ELT time, everyone defers to him |
| Massimo | HIGH (ELT) | HIGH | Sponsor - provided resources, made it a priority |
| Mikki | HIGH (IT Lead) | MEDIUM | Controls IT resources, Tyler reports to her |
| Rich | MEDIUM (Sales Leadership) | HIGH | Day-to-day relationships, AEs respect him |
| Thomas | LOW (AE) | HIGH | Respected for AI skills, others watch what he does |
| Chris Powers | LOW (AE) | MEDIUM | Has "gold standard" examples, Gemini Deep Research advocate |
| Matt Lazar | LOW (AE) | MEDIUM | Deep Research champion, practical process input |
| Tyler | LOW (I.S.) | MEDIUM | Will build whatever is decided; listened to on technical questions |

### Who Wins and Loses (Preliminary)

| Stakeholder | Gains from Change | Loses from Change | Predicted Response |
|-------------|-------------------|-------------------|-------------------|
| Steve/Rich (Leadership) | Visibility, consistency, metrics | Some control over process design | **Champion** |
| Most AEs (Matt L, Matt V, Chris) | Time saved, better data | Some autonomy | **Supportive** |
| Thomas | Time IF it works | **Unique competitive advantage** - his personal AI expertise becomes less differentiating | **Potential Blocker** |
| CSMs | Clear process for contributing | Nothing significant | **Supportive** |
| Partner Managers | Reduced ad-hoc requests | Gatekeeping power over Crossbeam | **Neutral to Resistant** |
| Tyler/Charlie | Clear mandate to build | Accountability for delivery | **Champion** |

### Potential Blockers to Flag

| Name | Why They Might Block | Evidence | Recommended Approach |
|------|---------------------|----------|---------------------|
| **Thomas** | Has invested heavily in personal AI workflow; standardization threatens his unique value | "At some point, you just stop prompting and have a natural conversation with your computer" (positioned himself as advanced) | Make him CO-DESIGNER, not recipient. Give him "AI capability lead" role. |
| Partner Managers | Lose gatekeeping power if AEs get Crossbeam access | Not interviewed, but access is currently gated | Frame as "reducing burden on PMs" not "taking away control" |

### Political Landmines Detected

| Landmine | Evidence | Implication for Synthesis |
|----------|----------|--------------------------|
| "We've tried tools before" | Tyler listed Account Navigator, Prospector, Alfred V1 | Acknowledge past failures explicitly. Explain why this is different. |
| Thomas's autonomy | He's built sophisticated personal workflows | Don't position this as "replacing" what Thomas does. Position as "scaling Thomas's expertise." |
| Prompt library debate | Tyler wants library, Thomas says "prompting is the past" | Don't take sides. Recommend BOTH: starter library for beginners, fluency training for advancement. |

---

## SECTION 3: OBJECTION READINESS ASSESSMENT

> **PURPOSE:** Track whether we can survive tough questions

### Can We Answer the Questions We'll Be Asked?

| Audience | Question | Answer Ready? | Evidence | Gap Action |
|----------|----------|---------------|----------|------------|
| Finance | "What's the ROI?" | **Partial** | "200-300 hrs/quarter manual effort" - derived; no baseline measurement | Need Steve to validate baseline |
| Finance | "What will this cost?" | **Yes** | Tyler/Charlie time + API costs (~$60K/year); Mikki committed resources | Ready |
| Engineering | "Is this technically feasible?" | **Yes** | Tyler confirmed data sources accessible via APIs; Deep Research already working | Ready |
| Engineering | "Do we have capacity?" | **Yes** | Mikki allocated Tyler + Charlie; Charlie has cognitive shifts training ready | Ready |
| Sales/Users | "Will people actually use this?" | **Partial** | High frustration with current state (good); but tool fatigue is real (risk) | Champion-led rollout strategy |
| Sales/Users | "We've tried this before..." | **Yes** | Past tools failed due to bad data + no ownership. This addresses root cause first. | Ready |
| Leadership | "Why now?" | **Yes** | ELT priority (Top Customer Growth), Massimo commitment | Ready |
| Leadership | "What if we don't act?" | **Partial** | Qualitative risk clear; quantified cost of inaction not stated | Add: "Competitors automate while we don't" |

### Objection Ammunition Collected

| Objection | Best Evidence | Quote |
|-----------|---------------|-------|
| "What's the ROI?" | 200-300 hrs/quarter at $75/hr = $15-22K/quarter opportunity cost | "4-6 hours per strategic account plan on manual data aggregation" - derived from sessions |
| "Is this feasible?" | Deep Research already produces 99% accuracy | "Deep Research, you could probably get it 99% of the time" - Matt Lazar |
| "Will people use it?" | High pain = high motivation | "The less we have to do that collection and entry, the better" - Matt Vosberg |
| "We tried before" | Previous tools had bad data | "The problem is ChatGPT provides inaccurate information" - Session 2 |
| "Why governance first?" | Silence on ownership | When asked "who owns data quality?", the room went silent |

### Objection Gaps (Critical for Next Sessions)

| Question We Can't Answer | Why It Matters | How to Close |
|-------------------------|----------------|--------------|
| Baseline time measurement | ROI calculation is estimated, not measured | Ask Steve to survey 3 AEs this week |
| Competitive risk quantified | "What if we don't act?" needs teeth | Research what competitors are doing with AI |

---

## SECTION 4: HYPOTHESIS TRACKING

| Hypothesis | Status | Key Evidence | Confidence |
|------------|--------|--------------|------------|
| H1: Data fragmentation is the core problem | **Confirmed** | "70-80 places, maybe more" - Steve; fragmentation across Salesforce, Tableau, Gatekeeper, Crossbeam confirmed | HIGH |
| H2: An automated tool is the solution | **Revised** | "It's not tools, it's ownership" - implied by failure of Account Navigator, Alfred V1; Thomas's skepticism | MEDIUM |
| H3: Adoption will be difficult | **Confirmed** | "We tried three tools already" - implied; Thomas has built personal workflow; tool fatigue mentioned | HIGH |
| H4: No one owns account intelligence | **Strongly Confirmed** | Silence when ownership questioned; everyone blames "the data" but no one owns fixing it | HIGH |

### Hypothesis Detail: H2 Revised

**Original Hypothesis:** An automated data aggregation tool is the solution direction.

**What We Found:**
- Tools have been built before (Account Navigator, Prospector, Alfred V1) and didn't stick
- Thomas explicitly said "prompting is the past" - skeptical of another tool approach
- Multiple references to data QUALITY being the issue, not data ACCESS
- Deep Research already works well - it's about spreading best practices, not building new tech

**Revised Hypothesis:** An automated tool PLUS clear data ownership PLUS standardized best practices is the solution. Tool alone will fail (again).

**Implication for Synthesis:** Recommend governance-first approach: appoint Data Quality Owner, THEN build tools.

---

## SECTION 5: CONTRADICTION LOG

> **PURPOSE:** Surface disagreements explicitly - don't smooth them over

### Explicit Contradictions

| Topic | Stakeholder A Says | Stakeholder B Says | Stakes | Resolution Needed From |
|-------|-------------------|-------------------|--------|----------------------|
| Prompt library | "Worth exploring a library of prompts" - Tyler | "Prompting is the past, just talk to AI naturally" - Thomas | Determines training vs. tooling investment | Steve (can mandate approach) |
| Standardization | "Need consistency so leadership can review" - Steve | "I like my own system, it works for me" - Thomas | Affects adoption and autonomy | Steve (can mandate template) |
| Data depth | "Need comprehensive view with all details" - Moran | "Don't go blind staring at too many fields" - Matt V | Template design | Phased approach: core now, enrich later |

### Tension Analysis

**Tension 1: Standardization vs. Autonomy**

- **Perspective A (held by Steve, Rich, Leadership):**
  - Position: "We need consistency so leadership can review and compare accounts."
  - Evidence: "If we had to come into a mirror board, where do we actually go?" - Steve
  - Underlying interest: Visibility, accountability, ability to help struggling AEs

- **Perspective B (held by Thomas, some AEs):**
  - Position: "My personal system works. Standardization means lowest common denominator."
  - Evidence: "At some point, you just stop [prompting] and have a natural conversation" - Thomas (implies his approach is advanced)
  - Underlying interest: Autonomy, recognition for individual expertise

- **Why They Disagree:** Leadership optimizes for visibility and scalability; power users optimize for personal effectiveness. Both are rational from their position.
- **Stakes:** If unresolved: Either leadership lacks visibility OR AEs resist adoption
- **Who Has Power to Resolve:** Steve (Sales VP) can mandate standards
- **Recommended Resolution:** **Standardize OUTPUT, not process.** Define what the end artifact must contain, but let people create it their way. This preserves autonomy while enabling visibility.

**Tension 2: Tool-First vs. Governance-First**

- **Perspective A (implied by initiative framing):**
  - Position: Build an AI tool to automate account planning
  - Underlying interest: Quick tangible progress

- **Perspective B (implied by discovery findings):**
  - Position: Fix data ownership before building tools
  - Evidence: Multiple tool failures; silence on ownership; "ChatGPT provides inaccurate information"
  - Underlying interest: Sustainable solution

- **Why This Tension Exists:** Building a tool is visible and exciting. Fixing governance is invisible and thankless.
- **Stakes:** If unresolved: Build another tool that becomes shelfware
- **Who Has Power to Resolve:** Mikki/Steve jointly
- **Recommended Resolution:** **Governance-first with parallel quick wins.** Appoint Data Quality Owner (30 days) while running 10% automation wins to show value.

---

## SECTION 6: COVERAGE ASSESSMENT

| Category | Status | Confidence | Evidence Strength |
|----------|--------|------------|-------------------|
| Problem Definition | **Covered** | HIGH | Strong - multiple sources, quantified |
| Stakeholder Perspectives | **Covered** | HIGH | Strong - AEs, Leadership, IT all heard |
| Requirements | **Covered** | MEDIUM | Moderate - gold standard exists, details need validation |
| Success Criteria | **Partial** | LOW | Weak - "70-80%" stated but not measured |
| Scope & Boundaries | **Covered** | HIGH | Strong - clear in/out decisions made |
| Risks | **Partial** | MEDIUM | Moderate - adoption risk clear, technical risk unclear |
| Context | **Covered** | HIGH | Strong - ELT priority, strategic alignment clear |
| Quantified Impact | **Partial** | MEDIUM | Moderate - estimates derived, not measured |
| Adoption Indicators | **Covered** | HIGH | Strong - sentiment captured, champions identified |

### Hidden Signals (What Wasn't Said)

| Topic | Expected Because | Who Was Silent | Interpretation |
|-------|------------------|----------------|----------------|
| Budget | Every project has constraints | Mikki, Steve | Either unlimited (unlikely) or not yet considered (risk) |
| Previous failures in detail | Change management 101 | Leadership | May be avoiding acknowledging specific past mistakes |
| Who owns data quality | Core to solution | **Everyone** | The elephant - no one wants the job |

**Dog That Didn't Bark: Data Engineering Consultation**
> Data integration is the core problem, yet no Data Engineering stakeholders were in the room. Five sessions on data fragmentation, zero sessions with people who manage the data infrastructure. This suggests either: (a) Data Eng doesn't exist as a function, (b) they weren't invited, or (c) the problem is seen as "Sales' problem" not "Data's problem."
> **Recommendation:** Before implementation, consult with whoever manages Salesforce, Tableau, and integration infrastructure.

---

## SECTION 7: SYNTHESIZER HANDOFF (Critical for 105%)

### Synthesis Readiness

**Decision:** READY
**Rationale:** Problem definition is solid, stakeholder perspectives well-captured, scope is clear. Success metrics are thin but can be flagged. The key insight (ownership vacuum) is clear and actionable.

### Insight Ammunition Summary (Copy-Paste Ready)

**The Surprising Truth (Candidate):**
> "The account planning problem isn't data fragmentation - it's an ownership vacuum. Until someone is chartered to own 'account intelligence' as a discipline, every technical solution becomes another silo. This is why three previous tools failed and why the next one will too - unless we fix the governance first."

**Dot Connections for Synthesis:**
1. Tool failures + personal workarounds + no ownership = doom loop that will repeat
2. Best practices exist (Chris, Matt L) but aren't standardized = organization pays learning tax repeatedly
3. 70-80% goal has hidden prerequisites (data access, data quality) that tools alone can't solve

**The Elephant:**
> Nobody wants to own account data quality because it's a thankless job. High accountability, low glory. This ownership vacuum is more consequential than any technical gap.

### Political Intelligence Summary (Copy-Paste Ready)

**Key Champions:** Steve, Rich (want visibility), Chris Powers (has gold standard), Matt Lazar (Deep Research advocate)
**Key Blockers:** Thomas (loses unique value), Partner Managers (lose gatekeeping power)
**Neutralization:** Make Thomas co-designer; frame Crossbeam access as "reducing PM burden"
**The Political Insight:** Thomas has invested significantly in his personal AI workflow. Standardization threatens his unique value proposition. Engage him as co-designer or expect resistance.

### Objection Handling Summary (Copy-Paste Ready)

| Objection | Best Response | Best Evidence |
|-----------|---------------|---------------|
| ROI | "$15-22K/quarter opportunity cost; 200-300 hrs reclaimed" | Derived from "4-6 hrs per account, 50 accounts" |
| Feasibility | "Data sources accessible via APIs; Deep Research already 99% accurate" | Tyler validation, Matt Lazar testimony |
| Adoption | "High frustration with current state; champion-led rollout" | "The less we have to do collection and entry, the better" - Matt V |
| Priority | "ELT priority (Massimo); Top Customer Growth initiative" | Steve confirmed |
| Tried before | "Past tools failed due to bad data and no ownership; this addresses root cause" | Tool failure history, ownership silence |

### Contradictions Requiring Resolution

| Contradiction | Synthesizer Should | Recommended Position |
|---------------|-------------------|---------------------|
| Prompt library vs. natural AI | Propose hybrid | "Library for beginners, fluency training for advancement" |
| Standardization vs. autonomy | Take position | "Standardize OUTPUT, not process" |
| Tool-first vs. governance-first | **Take strong position** | "Governance first, then tool" |

### Thin Areas to Caveat

| Area | Why It's Thin | Synthesizer Should |
|------|---------------|-------------------|
| Baseline time measurement | Estimated, not measured | Flag as assumption; recommend measurement |
| Success metrics | "70-80%" stated but not defined | Propose specific metrics in PRD |
| Budget constraints | Never discussed | Flag as open question |

### Hypothesis Results Summary

| Hypothesis | Result | Key Insight for Synthesis |
|------------|--------|--------------------------|
| H1: Data fragmentation is core problem | Confirmed | Yes, but it's a symptom of ownership vacuum |
| H2: Automated tool is the solution | **Revised** | Tool + ownership + best practices needed |
| H3: Adoption will be difficult | Confirmed | Thomas is key swing vote |
| H4: No one owns account intelligence | **Strongly Confirmed** | This is the elephant to name |

**Biggest Surprise:** The problem is organizational, not technical. Name it.

---

*Generated using PuRDy v2.5 Coverage Tracker with real-time insight capture*
