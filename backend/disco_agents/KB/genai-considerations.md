# GenAI Considerations

Guidance for scoping and building AI/agent projects at Contentful.

---

## When to Use AI

### Good Fit for AI
- High volume, repetitive tasks
- Pattern recognition in unstructured data
- Summarization and synthesis
- Q&A over large document sets
- Draft generation (with human review)
- Classification and routing

### Poor Fit for AI
- Decisions requiring accountability
- Highly regulated outputs (without human review)
- Tasks requiring real-time accuracy
- Small volume, high stakes decisions
- Anything where "close enough" isn't acceptable

---

## Tool Selection

### Glean (Self-Serve Tier)
**Best for**:
- Enterprise Q&A
- Simple team agents
- Document lookup
- "What does our policy say about X?"

**Limitations**:
- 128k token context
- No complex multi-step reasoning
- Limited customization

**Guidance**: If it can be a Glean agent, it should be. Don't overbuild.

### Claude / ChatGPT / Gemini (Complex Problems)
**Best for**:
- Large context analysis (200k+ tokens)
- Multi-step reasoning
- Code generation
- Complex document processing
- Custom agent builds

**When to choose**:
- Problem exceeds Glean's context window
- Need custom logic/workflows
- Requires integration with multiple systems

### Claude Projects (Team Collaboration)
**Best for**:
- Shared methodology (like PuRDy)
- Team-specific knowledge bases
- Consistent outputs across users

### Custom Builds (Agent Development)
**Best for**:
- Production workflows
- System integrations
- Automated pipelines
- User-facing tools

---

## Prompt Engineering Principles

### Structure Matters
```
[ROLE] - Who is the AI acting as?
[CONTEXT] - What background info is needed?
[TASK] - What specifically should it do?
[FORMAT] - How should output be structured?
[CONSTRAINTS] - What should it NOT do?
```

### Key Principles

1. **Be specific**: Vague prompts → vague outputs
2. **Provide examples**: Show, don't just tell
3. **Break down complex tasks**: Chain of thought
4. **Set constraints**: What to avoid, word limits, format
5. **Iterate**: First prompt is rarely the best prompt

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| "Summarize this" | "Summarize in 3 bullet points focusing on action items" |
| "Write something good" | "Write a professional email declining the request, keeping positive tone" |
| "Analyze this data" | "Identify the top 3 trends and explain why they matter" |
| Dump raw data | Structure data, highlight what to focus on |

---

## Data Considerations

### What Data Can Be Used?

| Data Type | Glean | Claude/ChatGPT | Custom Build |
|-----------|-------|----------------|---------------|
| Public docs | ✅ | ✅ | ✅ |
| Internal policies | ✅ | ⚠️ Check | ✅ with controls |
| Customer names/accounts | ⚠️ Limited | ❌ External | ✅ Internal only |
| PII (employee/customer) | ❌ | ❌ | ⚠️ Requires approval |
| Financial data | ⚠️ Aggregate only | ❌ | ⚠️ Requires approval |
| Legal/contracts | ⚠️ Internal only | ❌ | ⚠️ Requires approval |

### Questions to Ask

1. What data does this need access to?
2. Where does that data live?
3. Who currently has access?
4. What happens if the AI gets it wrong?
5. Is there audit trail requirements?

---

## Guardrails & Safety

### Output Validation

- **Human-in-the-loop**: Required for customer-facing, financial, legal outputs
- **Confidence thresholds**: When to escalate vs. proceed
- **Audit trails**: Log inputs, outputs, decisions

### Common Failure Modes

| Failure | Mitigation |
|---------|------------|
| Hallucination | Ground in source docs, add citations |
| Inconsistency | Use structured prompts, examples |
| Over-confidence | Add uncertainty language, confidence scores |
| Prompt injection | Input sanitization, output validation |
| Drift over time | Regular testing, version prompts |

### Testing Checklist

- [ ] Test with edge cases
- [ ] Test with adversarial inputs
- [ ] Test with empty/null inputs
- [ ] Verify outputs against known good examples
- [ ] Check for PII leakage
- [ ] Validate citations/sources

---

## Build Checklist

### Before Building

- [ ] Is AI the right solution? (vs. rules, workflow, human)
- [ ] What's the simplest version that delivers value?
- [ ] Who reviews outputs before they go anywhere?
- [ ] What data access is required?
- [ ] What happens when it fails?

### During Build

- [ ] Start with prompts, not code
- [ ] Test with real examples
- [ ] Get user feedback early
- [ ] Document the prompt/approach
- [ ] Plan for iteration

### After Launch

- [ ] Monitor for failures/edge cases
- [ ] Collect user feedback
- [ ] Track adoption metrics
- [ ] Schedule prompt reviews
- [ ] Plan v2 improvements

---

## ROI Estimation for AI Projects

### Formula
```
Value = (Time saved per task × Frequency × People affected) - (Build cost + Maintenance)
```

### Quick Estimates

| Task Type | Typical Time Saved | AI Confidence |
|-----------|-------------------|---------------|
| Q&A lookup | 5-15 min → instant | High |
| Document summary | 30 min → 2 min | High |
| Draft generation | 1 hour → 10 min | Medium |
| Data extraction | 20 min → 2 min | Medium |
| Complex analysis | 2 hours → 30 min | Low-Medium |

### Red Flags for ROI

- Low volume (< 10x/week)
- High accuracy requirements (AI isn't reliable enough)
- Requires extensive human review anyway
- Data access is the hard part, not the analysis
- Users won't adopt (change management problem)
