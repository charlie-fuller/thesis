# DISCo v4.3 Output Evaluation

Evaluate DISCo agent outputs against our quality standards and the expanded pipeline intentions.

---

## What Changed: PuRDy → DISCo

### The Expansion

PuRDy was a **discovery engine** - it analyzed transcripts and produced decision documents. DISCo extends the pipeline to **actionable PRDs**:

| Old (PuRDy) | New (DISCo) | Change |
|-------------|-------------|--------|
| Discovery → Insights → Decision Doc | Discovery → Insights → **Bundles → PRDs** | Extended output |
| "Synthesizer" | "Consolidator" | Renamed (consolidates insights) |
| N/A | "Strategist" | **NEW** - creates initiative bundles |
| N/A | "PRD Generator" | **NEW** - generates PRDs from bundles |

### The New Flow

```
Discovery Stage
  └─ Triage (GO/NO-GO)
  └─ Discovery Planner (session plans)
       ↓
Insights Stage
  └─ Coverage Tracker (READY/GAPS/CRITICAL)
  └─ Insight Extractor (patterns, pain points)
  └─ Consolidator (900-word decision document)  ← was "Synthesizer"
       ↓
Synthesis Stage [NEW]
  └─ Strategist (cluster → score → bundle)
  └─ [HUMAN CHECKPOINT: Review/edit bundles]
       ↓
Capabilities Stage [NEW]
  └─ PRD Generator (complete PRD per bundle)
  └─ [HUMAN CHECKPOINT: Approve PRDs]
```

---

## Evaluation Structure

This evaluation has two parts:

### Part A: Updated Agents (Compare to Last Run)
Grade the **renamed/unchanged** agents against prior performance:
- Triage v4.2
- Discovery Planner v4.1
- Coverage Tracker v4.1
- Insight Extractor v4.2
- Consolidator v4.2 (was Synthesizer)

### Part B: New Agents (Grade on Intention)
Grade the **new** agents against their stated purpose:
- Strategist v1.0
- PRD Generator v1.0

---

## Files to Read First

**Scoring Rubric:**
`/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/RUBRIC-v3.0.md`

**Agent Prompts:**
- `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/triage-v4.2.md`
- `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/insight-extractor-v4.2.md`
- `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/consolidator-v4.2.md`
- `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/strategist-v1.0.md`
- `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/prd-generator-v1.0.md`

---

## Data Queries

### Agent Outputs
```sql
SELECT
    po.agent_type,
    po.version,
    po.created_at,
    po.content_markdown,
    po.recommendation,
    po.confidence_level,
    pi.name as initiative_name
FROM purdy_outputs po
JOIN purdy_initiatives pi ON po.initiative_id = pi.id
WHERE po.created_at > NOW() - INTERVAL '24 hours'
ORDER BY po.agent_type, po.created_at DESC;
```

### Strategist Bundles
```sql
SELECT
    db.name,
    db.description,
    db.status,
    db.impact_score,
    db.impact_rationale,
    db.feasibility_score,
    db.feasibility_rationale,
    db.urgency_score,
    db.urgency_rationale,
    db.complexity_tier,
    db.bundling_rationale,
    db.included_items,
    db.stakeholders,
    db.dependencies,
    pi.name as initiative_name
FROM disco_bundles db
JOIN purdy_initiatives pi ON db.initiative_id = pi.id
WHERE db.created_at > NOW() - INTERVAL '24 hours'
ORDER BY db.created_at DESC;
```

### PRDs
```sql
SELECT
    dp.title,
    dp.status,
    dp.version,
    dp.content_markdown,
    dp.content_structured,
    db.name as bundle_name,
    pi.name as initiative_name
FROM disco_prds dp
JOIN disco_bundles db ON dp.bundle_id = db.id
JOIN purdy_initiatives pi ON dp.initiative_id = pi.id
WHERE dp.created_at > NOW() - INTERVAL '24 hours'
ORDER BY dp.created_at DESC;
```

---

# PART A: Updated Agents (vs. Last Run)

## Standard Tier Scoring

| Tier | Weight | Metrics |
|------|--------|---------|
| Tier 1: Action Enablement | 50% | Decision velocity, action clarity, stakeholder conviction |
| Tier 2: Insight Quality | 30% | Surprise rate, root cause accuracy, risk prediction |
| Tier 3: Efficiency | 20% | Time to confidence, output utilization, rework rate |

## Agent-Specific Checklists

### Triage v4.2
- [ ] Problem Worth Solving Gate present (4-criteria table)
- [ ] Gate result: PASS/PAUSE/FAIL stated
- [ ] Gate aligns with GO/NO-GO recommendation
- [ ] Each criterion has Assessment + Evidence

### Insight Extractor v4.2
- [ ] Pattern Library referenced (named pattern or "Custom")
- [ ] Handoff Protocol section present
- [ ] Status: READY FOR HANDOFF / BLOCKED / NEEDS MORE DISCOVERY
- [ ] "Key Input for Next Agent" specified

### Consolidator v4.2 (was Synthesizer)
- [ ] **Decision is LITERAL FIRST WORDS** (GO/NO-GO/CONDITIONAL)
- [ ] Metrics Dashboard with Baseline → Target → Timeline → Confidence
- [ ] "How We'll Know" observable proof
- [ ] System diagram with "Why Here" explanation
- [ ] "Alternative Considered" for intervention point
- [ ] No blocked role titles as owners
- [ ] Unknown owners use "[Requester to assign: Role]" format
- [ ] Word count ≤900

## Qualitative Assessment

| # | Question | Answer |
|---|----------|--------|
| Q1 | Can stakeholder state the decision in <5 seconds? | |
| Q2 | Can stakeholder state the leverage point in <10 seconds? | |
| Q3 | Can stakeholder state the first action in <10 seconds? | |
| Q4 | Is every action owner a real name (not role title)? | |
| Q5 | Are there measurable outcomes (baseline → target)? | |
| Q6 | Is systems thinking visible (loop + intervention point)? | |

## Override Rules

| Condition | Override | Reason |
|-----------|----------|--------|
| Decision not in first words (Consolidator) | -10 pts | Fails 30-second test |
| Role title used as owner | -5 pts per instance | Accountability gap |
| Missing "Done When" criteria | -5 pts | Can't verify completion |
| Word count >900 (Consolidator) | -5 pts | Brevity failure |
| Missing Metrics table | -10 pts | Can't track progress |
| Missing "Why Here" | -5 pts | Can't validate reasoning |
| Missing Problem Gate (Triage) | -10 pts | Skipped validation |

---

# PART B: New Agents (Grade on Intention)

## Strategist v1.0 - Intention

**Purpose:** Transform consolidated insights into initiative bundles that humans can review, prioritize, and approve.

**The agent succeeds if:**
1. Every significant insight is addressed (in a bundle or explicitly excluded)
2. Bundles are coherent (items genuinely belong together)
3. Scores are defensible (rationale supports the rating)
4. Human reviewers can make decisions without re-reading all discovery

### Strategist Checklist

**Completeness:**
- [ ] All pain points from Consolidator output addressed
- [ ] All opportunities from Consolidator output addressed
- [ ] Unbundled items have explicit reasons for exclusion

**Bundle Quality:**
- [ ] Each bundle has a clear, action-oriented name
- [ ] Description explains what the initiative delivers (not just what it fixes)
- [ ] Included items have source references (trace to discovery)

**Scoring Quality:**
| Dimension | Check |
|-----------|-------|
| Impact | [ ] Score present [ ] Rationale present [ ] Uses correct criteria (people/workflow/$) |
| Feasibility | [ ] Score present [ ] Rationale present [ ] Uses correct criteria (path/data/complexity) |
| Urgency | [ ] Score present [ ] Rationale present [ ] Uses correct criteria (deadline/competition/criticality) |

**Clustering Logic:**
- [ ] Bundles are mutually exclusive (no item in multiple bundles)
- [ ] Bundling rationale explains WHY items belong together
- [ ] Complexity tier assigned with justification

**Dependencies:**
- [ ] Cross-bundle dependencies identified
- [ ] Blocking relationships clear
- [ ] Dependency map included (mermaid or table)

**Human Readiness:**
- [ ] Recommendations section with prioritization
- [ ] Decision points for stakeholders are yes/no questions
- [ ] Suggested phasing is actionable

### Strategist Scoring

| Criterion | Weight | Score | Notes |
|-----------|--------|-------|-------|
| Completeness (all insights addressed) | 25% | /25 | |
| Bundle coherence (items belong together) | 25% | /25 | |
| Score quality (defensible ratings) | 20% | /20 | |
| Dependency clarity | 15% | /15 | |
| Human readiness (decision-ready) | 15% | /15 | |
| **Total** | 100% | /100 | |

### Strategist Anti-Patterns

| Pattern | Penalty | Why It's Bad |
|---------|---------|--------------|
| Catch-all bundle ("Misc Improvements") | -10 pts | Too vague to act on |
| Single-item bundle | -5 pts | Overhead not justified |
| Score inflation (all HIGH/HIGH/HIGH) | -10 pts | No honest prioritization |
| Missing rationale on any score | -5 pts per instance | Can't validate assessment |
| Generic bundle name ("Process Improvement") | -5 pts per instance | Not actionable |
| Items appear in multiple bundles | -10 pts | Confuses scope |

---

## PRD Generator v1.0 - Intention

**Purpose:** Transform an approved bundle into a complete PRD that engineering can implement.

**The agent succeeds if:**
1. Engineering could start planning from this document alone
2. Every requirement traces to a discovery finding
3. Success is measurable (baseline → target)
4. Scope is unambiguous (in/out clearly defined)

### PRD Section Checklist

| Section | Required Elements | Present | Quality (1-5) |
|---------|-------------------|---------|---------------|
| Executive Summary | What, Why, Who, Scope, Success Criteria | | |
| Problem Statement | Current State, Impact table, Root Causes | | |
| Goals & Success Metrics | Primary Goals, Metrics table with baseline/target/timeline, Definition of Done | | |
| Stakeholders | Role, Name/Group, Interest, Involvement table | | |
| Functional Requirements | ID, Requirement, Priority, Source, Acceptance Criteria table | | |
| Non-Functional Requirements | ID, Category, Requirement, Priority table | | |
| Out of Scope | Explicit exclusions list | | |
| Technical Considerations | Data Requirements table, Integration Points, Technology Options, Recommended Approach | | |
| Risks & Dependencies | Risks table (likelihood/impact/mitigation), Dependencies, Assumptions | | |
| Timeline Considerations | Phasing, Milestones, Decision Points | | |
| Appendix | Source Documents links, Change Log | | |

### PRD Quality Criteria

**Traceability:**
- [ ] Every Functional Requirement has a Source reference
- [ ] Source references link to actual discovery findings
- [ ] Stakeholders match those in the bundle

**Testability:**
- [ ] Every requirement has Acceptance Criteria
- [ ] Success metrics have measurement method
- [ ] Definition of Done is checkable

**Measurability:**
- [ ] Metrics have Baseline (current state)
- [ ] Metrics have Target (goal)
- [ ] Metrics have Timeline (by when)

**Scope Clarity:**
- [ ] Out of Scope section is populated
- [ ] Explicit about deferred items
- [ ] No ambiguous "nice to haves"

**Engineering Readiness:**
- [ ] Requirements are specific enough to estimate
- [ ] Technical options presented (not mandated)
- [ ] Dependencies won't surprise implementation team

### PRD Scoring

| Criterion | Weight | Score | Notes |
|-----------|--------|-------|-------|
| Section completeness | 20% | /20 | |
| Traceability (requirements → discovery) | 25% | /25 | |
| Testability (acceptance criteria) | 20% | /20 | |
| Measurability (baseline → target) | 15% | /15 | |
| Scope clarity | 10% | /10 | |
| Engineering readiness | 10% | /10 | |
| **Total** | 100% | /100 | |

### PRD Anti-Patterns

| Pattern | Penalty | Why It's Bad |
|---------|---------|--------------|
| Missing Executive Summary | -10 pts | Leadership can't scan |
| Missing Requirements table | -10 pts | Engineering can't scope |
| Vague requirement ("Improve performance") | -5 pts per instance | Not testable |
| Missing acceptance criteria | -5 pts per requirement | Can't verify done |
| No quantified metrics | -10 pts | Can't measure success |
| Technical mandates (not options) | -5 pts | Constrains solutions |
| Empty Out of Scope | -5 pts | Scope creep guaranteed |
| No source references | -10 pts | Can't validate requirements |

---

# Output Format

## Part A Summary

```markdown
## Part A: Updated Agents Evaluation

### Comparison to Last Run

| Agent | Last Score | This Score | Delta | Trend |
|-------|------------|------------|-------|-------|
| Triage v4.2 | | | | ↑/↓/→ |
| Discovery Planner v4.1 | | | | ↑/↓/→ |
| Coverage Tracker v4.1 | | | | ↑/↓/→ |
| Insight Extractor v4.2 | | | | ↑/↓/→ |
| Consolidator v4.2 | | | | ↑/↓/→ |

### Key Observations
- [What improved]
- [What regressed]
- [What stayed the same]

### Part A Verdict: [IMPROVED / STABLE / REGRESSED]
```

## Part B Summary

```markdown
## Part B: New Agents Evaluation

### Strategist v1.0

**Initiative:** [Name]
**Bundles Created:** [N]

**Intention Achievement:**
| Intention | Achieved? | Evidence |
|-----------|-----------|----------|
| Every insight addressed | Yes/Partial/No | |
| Bundles are coherent | Yes/Partial/No | |
| Scores are defensible | Yes/Partial/No | |
| Humans can decide without re-reading | Yes/Partial/No | |

**Score:** /100

**Verdict:** [MEETS INTENTION / PARTIAL / FAILS INTENTION]

---

### PRD Generator v1.0

**Bundle:** [Name]
**PRD Title:** [Title]

**Intention Achievement:**
| Intention | Achieved? | Evidence |
|-----------|-----------|----------|
| Engineering could start from this | Yes/Partial/No | |
| Requirements trace to discovery | Yes/Partial/No | |
| Success is measurable | Yes/Partial/No | |
| Scope is unambiguous | Yes/Partial/No | |

**Score:** /100

**Verdict:** [MEETS INTENTION / PARTIAL / FAILS INTENTION]
```

## Overall DISCo Assessment

```markdown
## DISCo Pipeline Assessment

### End-to-End Flow

| Stage | Agent(s) | Output Quality | Flow to Next |
|-------|----------|----------------|--------------|
| Discovery | Triage, Planner | /100 | Smooth/Gaps |
| Insights | Coverage, Extractor, Consolidator | /100 | Smooth/Gaps |
| Synthesis | Strategist | /100 | Smooth/Gaps |
| Convergence | PRD Generator | /100 | N/A |

### The Big Question

**Did DISCo deliver on the expansion promise?**

| Promise | Delivered? | Evidence |
|---------|------------|----------|
| Goes beyond decision docs to actionable PRDs | | |
| Human checkpoints enable course correction | | |
| Bundles are coherent initiative definitions | | |
| PRDs are engineering-ready | | |

### Recommended Changes

**For Updated Agents:**
1. [Change based on regression or opportunity]

**For Strategist:**
1. [Change based on intention gaps]

**For PRD Generator:**
1. [Change based on intention gaps]

### Final Verdict

**DISCo v4.3 Status:** [SHIP / ITERATE / ROLLBACK]

**Rationale:** [2-3 sentences on whether the expansion delivered value]
```

---

## Scoring Reference

| Score Range | Rating | Action |
|-------------|--------|--------|
| 90-100 | Excellent | ADOPT - Ship as-is |
| 75-89 | Good | REVIEW - Minor tweaks |
| 60-74 | Adequate | ITERATE - Address gaps |
| 40-59 | Needs Work | ITERATE - Significant changes |
| <40 | Poor | REJECT - Rethink approach |

---

*Evaluation Prompt v4.3 - DISCo pipeline with Strategist + PRD Generator*
*Grades updated agents vs. last run, new agents vs. intention*
