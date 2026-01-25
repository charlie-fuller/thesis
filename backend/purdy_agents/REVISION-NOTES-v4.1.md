# PuRDy v4.1 Revision Notes

**Created:** 2026-01-25
**Status:** PENDING - awaiting full analysis after testing

---

## Context

During v4.0 deployment, user observed that Insight Extractor and Discovery Planner ran faster than expected, raising concerns about analysis depth.

**Investigation found:** Outputs are actually exceeding word limits (1000+ words vs 350-500 targets) and quality appears solid. Speed was due to familiar context and Opus efficiency, not shallow analysis.

---

## Chain-of-Thought Enhancement (Consider for v4.1)

If future testing reveals shallow analysis, add explicit reasoning steps to agent instructions:

### Proposed Addition (for any agent)

```markdown
## ANALYSIS PROCESS (Do This First, Thoroughly)

**Before writing any output, complete this analysis internally:**

### Step 1: Read Everything
- Read every document completely - do not skim
- Note every stakeholder mentioned and their role
- Flag every number, metric, or quantification

### Step 2: Extract All Potential Insights
- List every finding, observation, or claim made
- For each, note who said it and the exact quote
- Identify which findings are supported by multiple sources

### Step 3: Identify Patterns
- Look for reinforcing loops (A causes B causes A)
- Look for contradictions between stakeholders
- Look for gaps between what people say and what they do
- Look for implicit assumptions that may be wrong

### Step 4: Assess Surprise Value
- What would stakeholders be surprised to learn?
- What do they believe that the evidence contradicts?
- What are they not seeing that the data shows?

### Step 5: Prioritize Ruthlessly
- From all insights found, select the most decision-relevant
- Discard insights that are obvious or don't affect the decision
- Keep only insights backed by direct evidence

### Step 6: Write the Output
- Now write the structured output
- Every insight must have evidence
- The output is the distillation, not the analysis

**The output is short because the thinking was thorough, not because the thinking was skipped.**
```

### Why This Might Help

1. **Forces sequential processing** - Agent must complete steps before writing
2. **Creates accountability** - Each step has specific requirements
3. **Separates analysis from output** - Thinking can be deep even if output is concise
4. **Addresses the Claude behavior** - Output length correlates with reasoning depth; this decouples them

### Why It Might Not Be Needed

1. **Current outputs are thorough** - 1000+ words with structured evidence
2. **Word limits aren't being enforced** - Agents are self-regulating to appropriate length
3. **Opus is already methodical** - May be redundant instruction

---

## Other v4.1 Candidates

### 1. Word Limit Enforcement
- Current: Agents ignore limits, output 800-1200 words
- Decision needed: Enforce strictly or let agents self-regulate?

### 2. Discovery Loop UX
- Coverage Tracker is designed for iterative use (during breaks, after sessions)
- Frontend doesn't currently surface this workflow prominently
- Consider: Visual workflow indicator showing the loop

### 3. Real Names Requirement
- Synthesizer requires real names, not role titles
- Agents may not have access to names if not in documents
- Consider: Fallback language like "[Requester to identify owner]"

---

## Testing Checklist (Before v4.1)

- [ ] Run each agent on Strategic Account Planning initiative
- [ ] Compare v3.0 vs v4.0 outputs side-by-side
- [ ] Score using SCORING-METHODOLOGY-v3.0.md
- [ ] Identify specific quality gaps (if any)
- [ ] Get user feedback on consulting quality bar
- [ ] Decide on word limit enforcement

---

## Files Modified in v4.0

- `insight-extractor-v4.0.md` - NEW agent (has partial chain-of-thought edit)
- `synthesizer-v4.0.md` - 500 words, decision first
- `discovery-planner-v4.0.md` - Human execution clarity
- `coverage-tracker-v4.0.md` - Iterative use
- `triage-v4.0.md` - Conviction language
- `tech-evaluation-v4.0.md` - Partner quality bar
- `agent_service.py` - Added insight_extractor
- `AgentRunner.tsx` - Added icon and workflow
