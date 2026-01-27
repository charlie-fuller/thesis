# DISCo Process Overview

**Discovery-Insights-Synthesis-Capabilities (DISCo)** (formerly PuRDy - Product Requirements Discovery)
**Version:** 4.2
**Last Updated:** 2026-01-25

---

## What is DISCo?

DISCo is a multi-agent system that transforms raw product discovery into actionable decision documents. It bridges the gap between "someone has an idea" and "leadership can make an informed GO/NO-GO decision."

**The Core Insight:** Product discovery typically drowns in transcripts, notes, and research that never gets synthesized into something executives can act on. DISCo solves this by structuring the entire journey from intake to recommendation.

---

## The Complete Process Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DISCo PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   INTAKE              DISCOVERY                 SYNTHESIS                    │
│   ─────────────────   ──────────────────────   ─────────────────────────    │
│                                                                              │
│   ┌─────────┐         ┌──────────────────┐     ┌───────────────────────┐    │
│   │ TRIAGE  │──GO────▶│ DISCOVERY PLANNER│     │ INSIGHT EXTRACTOR     │    │
│   │ (AI)    │         │ (AI)             │     │ (AI)                  │    │
│   └────┬────┘         └────────┬─────────┘     └───────────┬───────────┘    │
│        │                       │                           │                 │
│        │ NO-GO                 ▼                           │                 │
│        │ stops          ┌──────────────┐                   ▼                 │
│        ▼                │ LIVE         │           ┌───────────────────┐    │
│   [Declined]            │ DISCOVERY    │           │ CONSOLIDATOR      │    │
│                         │ SESSIONS     │           │ (AI)              │    │
│                         │ (HUMANS)     │           └───────────────────┘    │
│                         └──────┬───────┘                   │                 │
│                                │                           ▼                 │
│                                ▼                    ┌───────────────┐        │
│                         ┌──────────────┐           │ DECISION DOC  │        │
│                         │ COVERAGE     │           │ GO / NO-GO    │        │
│                         │ TRACKER      │           └───────────────┘        │
│                         │ (AI)         │                                     │
│                         └──────┬───────┘                                     │
│                                │                                             │
│                    ┌───────────┴───────────┐                                │
│                    │                       │                                 │
│              GAPS REMAIN              READY FOR                              │
│              ↓ Back to                SYNTHESIS                              │
│              Discovery                ↑ Proceed                              │
│              Planner                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Intake (Triage)

**Agent:** Triage v4.2
**Time:** 3-5 minutes
**Input:** Initiative description, problem statement
**Output:** GO / NO-GO / INVESTIGATE recommendation

### What Happens

1. Someone submits an initiative idea (e.g., "We need AI to automate invoice processing")
2. Triage agent evaluates in <5 minutes:
   - **Problem Worth Solving Gate** (v4.2): Is the problem real, costly, solvable, and ours?
   - Strategic fit, ROI potential, effort sizing
   - Change readiness (sponsor, capacity, competing priorities)
3. Makes a conviction-based call:
   - **GO** → Proceed to Discovery Planner
   - **NO-GO** → Decline with rationale
   - **INVESTIGATE** → Need more information first

### Key Principle
> "Would you stake your reputation on this recommendation?"

Triage prevents wasted discovery effort on initiatives that shouldn't proceed.

---

## Phase 2: Discovery Planning

**Agent:** Discovery Planner v4.1
**Time:** 5-10 minutes
**Input:** Triaged initiative (GO)
**Output:** Structured discovery plan with sessions, questions, success criteria

### What Happens

1. Discovery Planner analyzes the initiative
2. Identifies the **core question** that, if answered, enables a decision
3. Designs specific discovery sessions:
   - Workshop formats (2-3 hours, multiple stakeholders)
   - Interview formats (45-60 min, deep dives)
   - Process walkthroughs (1-2 hours, current state)
4. For each session, specifies:
   - **Agenda** with time allocations
   - **Key Questions** (including quantification)
   - **Done When** criteria (specific artifact/answer)
5. Creates the **Quantification Gate** - numbers required for ROI calculation

### Key Principle
> "The agent PLANS discovery. Humans EXECUTE it."

Discovery Planner produces a plan that Chris (or any facilitator) can pick up and run without additional prep.

---

## Phase 3: Live Discovery Sessions (HUMANS)

**Executor:** Human facilitator (e.g., Chris, the PM)
**Time:** Variable (per session design)
**Input:** Discovery Plan from agent
**Output:** Session recordings, transcripts, notes

### What Happens

1. Human facilitator takes the Discovery Plan
2. Schedules and runs the sessions:
   - Uses the agenda as a guide
   - Asks the key questions
   - Captures quantification data
   - Notes surprises and contradictions
3. After each session:
   - Uploads transcript to DISCo (within 24 hours)
   - Runs Coverage Tracker to assess progress

### The Discovery Loop

```
Discovery Planner → [Human runs Session 1] → Coverage Tracker
       ↑                                           |
       └──────── (if GAPS REMAIN) ─────────────────┘
                 (if READY) ─────────────────────────→ Insight Extractor
```

**This is NOT one-and-done.** Expect 2-4 iterations:
- Session 1 → Coverage check → identify gaps
- Session 2 (follow-up) → Coverage check → identify remaining gaps
- Continue until "READY FOR SYNTHESIS"

### Key Principle
> "Run Coverage Tracker after EVERY session, not just at the end."

---

## Phase 4: Coverage Tracking (Iterative)

**Agent:** Coverage Tracker v4.1
**Time:** 3-5 minutes per run
**Input:** Discovery transcripts (partial or complete)
**Output:** Gap analysis, readiness assessment, next steps

### What Happens

1. After each discovery session, Coverage Tracker runs
2. Evaluates what we know vs. what we still need:
   - Root cause: Clear / Partial / Missing
   - Quantification: Clear / Partial / Missing
   - Stakeholder alignment: Clear / Partial / Missing
   - Change readiness: Clear / Partial / Missing
   - Executive sponsor: Named / Unclear / Missing
3. Returns a status:
   - **READY FOR SYNTHESIS** → Proceed to Insight Extractor
   - **GAPS REMAIN - CRITICAL** → Back to Discovery Planner for follow-up
   - **GAPS REMAIN - MINOR** → Can proceed with caveats
   - **BLOCKED - [reason]** → External dependency, action required

### When to Run Coverage Tracker

| Timing | Purpose |
|--------|---------|
| During workshop breaks | Course-correct mid-session |
| After each session | Full gap assessment |
| Before synthesis decision | Final go/no-go |

### Key Principle
> "Short because it runs multiple times. Each run should take <1 minute to read."

---

## Phase 5: Insight Extraction

**Agent:** Insight Extractor v4.2
**Time:** 5-10 minutes
**Input:** All discovery transcripts and notes
**Output:** Structured insights with evidence, patterns, surprises

### What Happens

1. Insight Extractor processes all discovery content
2. Extracts key insights:
   - Direct quotes that prove points
   - Confidence levels with evidence
   - Implications for the decision
3. Identifies patterns using the **Pattern Library** (v4.2):
   - The Governance Vacuum
   - The Data Quality Trap
   - The Adoption Gap
   - The Shadow IT Spiral
   - The Scope Creep Doom Loop
4. Surfaces contradictions between stakeholders
5. Identifies "What They Don't Realize" - surprises with high impact
6. Prepares structured handoff for Consolidator via **Handoff Protocol** (v4.2)

### Key Principle
> "Reduce 10,000 words of transcripts to 800 words of meaning."

The output is dense because the thinking was thorough.

---

## Phase 6: Consolidation (Final Decision Document)

**Agent:** Consolidator v4.2
**Time:** 10-15 minutes
**Input:** Insight Extractor output, all prior context
**Output:** 900-word decision document with GO/NO-GO/CONDITIONAL recommendation

### What Happens

1. Consolidator produces the final decision document
2. Structure (v4.2):
   - **Decision (FIRST WORDS):** GO/NO-GO/CONDITIONAL with owner and deadline
   - **Leverage Point:** Single intervention that creates the most change
   - **System Diagram:** Mermaid visualization with "Why Here" reasoning
   - **Metrics Dashboard** (v4.2): Baseline → Target → Timeline with confidence
   - **Evidence Table:** 3 best quotes that convince a skeptic
   - **Blockers Table:** Top 3 risks with owners
   - **First Action:** Monday morning step with "Done When" criteria
   - **Stakes:** Cost of delay, risk of inaction

### Key Principles

**For Chris (accountability):**
- Real names, not role titles
- Role Title Blocklist: "Discovery Lead" → "[Requester to assign: Discovery Lead]"
- Measurable outcomes with timeline

**For Mikki (systems thinking):**
- "Why Here" explains intervention point reasoning
- "Alternative Considered" shows intentional problem definition

### The 30-Second Test

After reading the synthesis, a stakeholder can:
1. State the decision (5 sec)
2. State the leverage point (5 sec)
3. State the first action (5 sec)
4. Explain why we should act now (5 sec)
5. State how we'll measure success (5 sec)

---

## Optional: Tech Evaluation

**Agent:** Tech Evaluation v4.1
**Time:** 10-15 minutes
**Input:** Synthesized initiative (if technical decisions needed)
**Output:** Platform/architecture recommendation with confidence-tagged estimates

### When to Use

Run Tech Evaluation when the initiative requires:
- Platform selection (build vs. buy)
- Architecture decisions
- Integration design
- Technical feasibility assessment

---

## Agent Routing Summary

| Current State | Next Agent | Condition |
|---------------|------------|-----------|
| New initiative | Triage | Always start here |
| Triage → GO | Discovery Planner | Proceed with discovery |
| Triage → NO-GO | None | Declined |
| Triage → INVESTIGATE | None | Human action needed |
| Discovery Planner | Human execution | Plan complete |
| Human session | Coverage Tracker | After each session |
| Coverage → READY | Insight Extractor | Proceed to synthesis |
| Coverage → GAPS CRITICAL | Discovery Planner | Plan follow-up session |
| Coverage → GAPS MINOR | Insight Extractor | Proceed with caveats |
| Coverage → BLOCKED | None | External action needed |
| Insight Extractor | Consolidator | Insights extracted |
| Consolidator | Strategist | Decision doc complete |
| Strategist | PRD Generator | Initiative bundles approved |
| PRD Generator | (Optional) Tech Evaluation | If technical decisions needed |

---

## v4.2 Persona Alignment

### For Chris Baumgartner (Staff PM)
- **Metrics Dashboard:** Baseline → Target → Timeline (STAR format)
- **Role Title Blocklist:** Forces real names or explicit gaps
- **Accountability Language:** "I did" not "we did"

### For Tyler Stitt (AI Ops)
- **Pattern Library:** 5 reusable enterprise loop templates
- **Handoff Protocol:** Explicit agent-to-agent communication
- **Structured Frameworks:** Documentation he can learn and reuse

### For Mikki Hurt (Head of G&A)
- **Problem Worth Solving Gate:** 4-criteria validation before GO
- **"Why Here" Reasoning:** Explains intervention point logic
- **"Alternative Considered":** Shows intentional problem definition

---

## Success Metrics

| Metric | Target | How DISCo Helps |
|--------|--------|-----------------|
| Decision Velocity | <7 days | Structured handoffs, clear next steps |
| 30-Second Clarity | 100% | Decision-first format, brevity enforcement |
| Stakeholder Conviction | ≥4/5 | Evidence-backed, metrics-driven |
| Recommendation Adoption | ≥60% | Problem validation, real names |
| Blocker Resolution | ≥50% | Clear ownership, Done When criteria |

---

## Quick Start

1. **Submit initiative** → Triage runs automatically
2. **If GO** → Discovery Planner creates session plan
3. **Run sessions** → Upload transcripts after each
4. **Run Coverage Tracker** → Check readiness
5. **Repeat until READY** → Then run Insight Extractor
6. **Generate Synthesis** → Final decision document
7. **Present to leadership** → GO/NO-GO in 30 seconds

---

*DISCo v4.2 - From idea to decision in days, not months*
