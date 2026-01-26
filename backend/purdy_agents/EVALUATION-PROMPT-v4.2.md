# PuRDy v4.2 Output Evaluation

I need you to evaluate PuRDy agent outputs using our established scoring methodology.

## Files to Read First

1. **Scoring Rubric** (read completely - defines all criteria):
   `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/RUBRIC-v3.0.md`

2. **Revision Notes** (context on v4.2 changes):
   `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/REVISION-NOTES-v4.2.md`

3. **v4.2 Agent Prompts** (to understand expected outputs):
   - `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/synthesizer-v4.2.md`
   - `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/insight-extractor-v4.2.md`
   - `/Users/charlie.fuller/vaults/Contentful/thesis/backend/purdy_agents/triage-v4.2.md`

## Data to Query

Run this query via Supabase to get the outputs:

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

---

## Your Task

### 1. Score Each Agent Output

Apply all three tiers from RUBRIC-v3.0.md:

| Tier | Weight | Metrics |
|------|--------|---------|
| Tier 1: Action Enablement | 50% | Decision velocity, action clarity, stakeholder conviction, recommendation adoption, blocker resolution |
| Tier 2: Insight Quality | 30% | Surprise rate, root cause accuracy, risk prediction |
| Tier 3: Efficiency | 20% | Time to confidence, output utilization, rework rate, process improvements |

### 2. v4.2-Specific Checks

For **Triage v4.2**, verify:
- [ ] Problem Worth Solving Gate present (4-criteria table)
- [ ] Gate result stated (PASS/PAUSE/FAIL)
- [ ] Gate result aligns with GO/NO-GO decision
- [ ] Each criterion has Assessment AND Evidence

For **Insight Extractor v4.2**, verify:
- [ ] Pattern Library referenced (match name or "Custom")
- [ ] Handoff Protocol section present
- [ ] Status field (READY FOR HANDOFF / BLOCKED / NEEDS MORE DISCOVERY)
- [ ] "Key Input for Next Agent" specified

For **Synthesizer v4.2**, verify:
- [ ] Metrics Dashboard present (baseline/target/timeline table)
- [ ] "How We'll Know" observable proof included
- [ ] System diagram has "Why Here" explanation
- [ ] "Alternative Considered" included
- [ ] No blocked role titles used as owners (check against blocklist)
- [ ] Unknown owners use "[Requester to assign: Role]" format

### 3. Qualitative Assessment (Q1-Q8)

| # | Question | Answer |
|---|----------|--------|
| Q1 | Can stakeholder state the decision in <5 seconds? | |
| Q2 | Can stakeholder state the leverage point in <10 seconds? | |
| Q3 | Can stakeholder state the first action in <10 seconds? | |
| Q4 | Is every action owner a real name (not role title)? | |
| Q5 | Are there measurable outcomes (baseline → target)? | |
| Q6 | Is systems thinking visible (loop + intervention point)? | |
| Q7 | Would Chris see STAR-format accountability? | |
| Q8 | Would Mikki see intentional problem definition? | |

### 4. North Star Alignment (N1-N5)

| # | Metric | Target | Actual | Pass? |
|---|--------|--------|--------|-------|
| N1 | Decision Velocity | <7 days | | |
| N2 | 30-Second Clarity | 100% | | |
| N3 | Stakeholder Conviction | ≥4/5 | | |
| N4 | Recommendation Adoption | ≥60% | | |
| N5 | Blocker Resolution | ≥50% | | |

### 5. Override Rules

Apply these overrides regardless of score:

| Condition | Override | Reason |
|-----------|----------|--------|
| Decision not in first sentence | -10 pts | Fails 30-second test |
| Role title used as owner | -5 pts per instance | Accountability gap |
| Missing "Done When" criteria | -5 pts | Can't verify completion |
| Word count >900 (Synthesizer) | -5 pts | Brevity failure |
| Missing Metrics table (v4.2) | -10 pts | Chris can't see outcomes |
| Missing "Why Here" (v4.2) | -5 pts | Mikki can't see reasoning |
| Missing Problem Gate (v4.2) | -10 pts | Skipped validation |

---

## Output Format

### Per Agent Evaluation

```markdown
## [Agent Name] v4.2 Evaluation

**Initiative:** [Name]
**Created:** [Timestamp]

### Tier Scores
| Tier | Score | Notes |
|------|-------|-------|
| Tier 1: Action Enablement | /25 | |
| Tier 2: Insight Quality | /15 | |
| Tier 3: Efficiency | /20 | |
| **Raw Total** | /60 | |
| Override Adjustments | | |
| **Final Score** | /100 | |

### v4.2 Feature Compliance
| Feature | Present | Quality (1-5) | Notes |
|---------|---------|---------------|-------|
| [Feature] | Yes/No | | |

### Key Observations
- Strength 1
- Strength 2
- Gap 1
- Gap 2

### Improvement Recommendations
1. [Specific recommendation]
2. [Specific recommendation]

### Verdict: [ADOPT / REVIEW / ITERATE / REJECT]
```

### Overall v4.2 Assessment

After evaluating all agents, provide:

```markdown
## v4.2 Overall Assessment

### Comparison: v4.1 → v4.2
| Agent | v4.1 Avg | v4.2 Avg | Delta | Trend |
|-------|----------|----------|-------|-------|
| Triage | | | | ↑/↓/→ |
| Insight Extractor | | | | ↑/↓/→ |
| Synthesizer | | | | ↑/↓/→ |

### New Feature Impact

**Metrics Dashboard (Synthesizer):**
- Adding value? [Yes/No/Partial]
- Evidence: [What you observed]

**Pattern Library (Insight Extractor):**
- Adding value? [Yes/No/Partial]
- Evidence: [What you observed]

**Problem Worth Solving Gate (Triage):**
- Adding value? [Yes/No/Partial]
- Evidence: [What you observed]

**Handoff Protocol:**
- Improving agent flow? [Yes/No/Partial]
- Evidence: [What you observed]

### Persona Alignment Check

| Persona | What They Want | v4.2 Delivers? | Evidence |
|---------|---------------|----------------|----------|
| Chris | Metrics, STAR accountability | | |
| Tyler | Structured frameworks | | |
| Mikki | Systems thinking, intentional problem definition | | |

### Recommended Changes for v4.3

1. [High priority change]
2. [Medium priority change]
3. [Low priority change]

### Final Verdict

**v4.2 Status:** [SHIP / ITERATE / ROLLBACK]

**Rationale:** [1-2 sentences]
```

---

## Scoring Reference

| Score Range | Rating | Action |
|-------------|--------|--------|
| 90-100 | Excellent | ADOPT - Ship as-is |
| 75-89 | Good | REVIEW - Minor tweaks, can ship |
| 60-74 | Adequate | ITERATE - Address gaps before shipping |
| 40-59 | Needs Work | ITERATE - Significant changes needed |
| <40 | Poor | REJECT - Rollback to previous version |

---

*Evaluation Prompt v4.2 - Persona-aligned scoring*
