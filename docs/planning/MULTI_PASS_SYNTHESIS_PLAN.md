# Multi-Pass Synthesis Implementation Plan

**Date**: 2026-01-24
**Status**: Approved for implementation

---

## Overview

Implement a "Multi-Pass Synthesis" mode for the Synthesizer agent that:
1. Runs Sonnet 3 times with varying temperatures (0.5, 0.7, 0.85)
2. Feeds all 3 outputs to Opus for meta-synthesis
3. Produces a unified best-of-all output

### Temperature Rationale

For business documents and process analysis, lower temperatures are preferred:
- **0.5 (Conservative)**: Precise, fact-focused interpretation - anchors the synthesis
- **0.7 (Balanced)**: Standard creative-analytical balance
- **0.85 (Exploratory)**: Surfaces bolder insights without becoming unreliable

Higher temperatures (1.0+) risk hallucination and drift from source material, which is unacceptable for business-critical synthesis.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Multi-Pass Synthesis                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Pass 1       │  │ Pass 2       │  │ Pass 3       │           │
│  │ Sonnet       │  │ Sonnet       │  │ Sonnet       │           │
│  │ temp: 0.5    │  │ temp: 0.7    │  │ temp: 0.85   │           │
│  │ "Conservative"│  │ "Balanced"  │  │ "Exploratory"│           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                    │
│         └────────────────┬┴─────────────────┘                    │
│                          │                                       │
│                          ▼                                       │
│                 ┌──────────────────┐                            │
│                 │ Meta-Synthesis   │                            │
│                 │ Opus             │                            │
│                 │ temp: 0.6        │                            │
│                 │ "Best of All"    │                            │
│                 └────────┬─────────┘                            │
│                          │                                       │
│                          ▼                                       │
│                 ┌──────────────────┐                            │
│                 │ Final Output     │                            │
│                 │ Version: N       │                            │
│                 │ (multi_pass)     │                            │
│                 └──────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### Phase 1: Backend Changes

#### 1.1 Update AgentRunRequest

**File**: `/backend/api/routes/purdy.py`

```python
class AgentRunRequest(BaseModel):
    agent_type: str
    document_ids: Optional[List[str]] = None
    output_format: Optional[str] = "comprehensive"
    multi_pass: Optional[bool] = False  # NEW: Enable multi-pass synthesis
```

#### 1.2 Add Multi-Pass Configuration

**File**: `/backend/services/purdy/agent_service.py`

```python
# Multi-pass synthesis configuration
# Lower temperatures for business documents - precision over creativity
MULTI_PASS_CONFIG = {
    "passes": [
        {"model": "claude-sonnet-4-20250514", "temperature": 0.5, "label": "Conservative"},
        {"model": "claude-sonnet-4-20250514", "temperature": 0.7, "label": "Balanced"},
        {"model": "claude-sonnet-4-20250514", "temperature": 0.85, "label": "Exploratory"},
    ],
    "meta_synthesis": {
        "model": "claude-opus-4-5-20251101",
        "temperature": 0.6,  # Lower for precise combination
    },
    # Only these agents support multi-pass
    "supported_agents": ["synthesizer"]
}
```

#### 1.3 Create Meta-Synthesis Prompt

**File**: `/backend/purdy_agents/meta-synthesizer-v1.0.md`

```markdown
# Meta-Synthesizer

You are a senior strategic analyst reviewing three independent synthesis attempts of the same discovery materials. Your task is to produce a unified, best-of-all synthesis.

## Understanding Temperature Variation

These three syntheses were generated with intentionally different temperature settings. Temperature controls how deterministic vs. exploratory the model's outputs are:

| Version | Temperature | Characteristics | Validation Approach |
|---------|-------------|-----------------|---------------------|
| A (Conservative) | 0.5 | More deterministic, sticks closely to source material, precise numbers, conservative estimates | **High trust** - if A states something, it's likely directly supported by evidence |
| B (Balanced) | 0.7 | Standard balance of precision and insight, typical business analysis quality | **Medium trust** - verify against A for factual claims, consider for balanced framing |
| C (Exploratory) | 0.85 | More exploratory, may surface connections others missed, bolder hypotheses | **Verify carefully** - cross-reference with A/B before including; may contain valuable insights OR overreach |

### Key Implications for Your Synthesis

1. **When all three agree**: Very high confidence - include with strong conviction
2. **When A+B agree but C differs**: C may be overreaching OR seeing something others missed - evaluate the evidence
3. **When A states a fact that B/C embellish**: Trust A's precision, consider if B/C's framing adds value without distorting
4. **When only C surfaces an insight**: This could be the "elephant" or could be noise - look for supporting evidence in source material
5. **For numbers and estimates**: Prefer A's conservative figures unless B/C provide compelling reasoning for different values

## Your Inputs

You have received three synthesis outputs:
- **Version A (Conservative)**: Generated with temperature 0.5, precise and fact-focused
- **Version B (Balanced)**: Generated with temperature 0.7, balances precision and insight
- **Version C (Exploratory)**: Generated with temperature 0.85, surfaces bolder insights while staying grounded

## Your Task

Produce a single unified synthesis that:

1. **Selects the best insights** from each version
   - If all three agree on an insight, it's likely robust
   - If only one version surfaced an insight, evaluate if it's genuinely valuable or an outlier

2. **Resolves conflicts** between versions
   - When versions disagree, explain which interpretation is more supported by evidence
   - Note where genuine ambiguity exists

3. **Preserves unique value** from each pass
   - Version A may have more precise numbers and conservative estimates
   - Version B may have balanced framing and standard insights
   - Version C may have surfaced elephants or bolder connections others missed

4. **Maintains structural coherence**
   - Follow the standard Synthesizer v2.8 output format
   - Ensure the final output reads as one cohesive document, not a patchwork

## Output Format

Produce a complete synthesis following the v2.8 format, with one addition:

### Multi-Pass Synthesis Notes

At the end, include a brief section:

```markdown
## Multi-Pass Synthesis Notes

### Key Agreements (High Confidence)
- [Insights all three versions surfaced - these are robust findings]

### Resolved Conflicts
- [Where versions disagreed, which version you trusted, and why based on temperature characteristics]
- Example: "Version C suggested 40% cost savings, but A's conservative 25% estimate was better supported by the source data"

### Unique Contributions
- From Version A (Conservative): [Precise facts or conservative estimates that anchored the analysis]
- From Version B (Balanced): [Framing or synthesis that improved clarity]
- From Version C (Exploratory): [Bold insights that were validated against source material]

### Temperature-Based Validation Notes
- [Any cases where C's exploratory insight was confirmed by evidence]
- [Any cases where C's insight was excluded as unsupported]
```

## Quality Standard

The final output should be BETTER than any single version - not just a merge, but a genuine synthesis that leverages the diversity of perspectives.
```

#### 1.4 Update run_agent Function

**File**: `/backend/services/purdy/agent_service.py`

Add new function for multi-pass:

```python
async def run_agent_multi_pass(
    initiative_id: str,
    agent_type: str,
    user_id: str,
    document_ids: Optional[List[str]] = None,
    output_format: str = "comprehensive"
) -> AsyncGenerator[Dict, None]:
    """
    Execute multi-pass synthesis with 3 Sonnet runs + 1 Opus meta-synthesis.
    """
    if agent_type not in MULTI_PASS_CONFIG["supported_agents"]:
        raise ValueError(f"Multi-pass not supported for {agent_type}")

    # Build context once (shared across all passes)
    context = await build_agent_context(initiative_id, agent_type)
    agent_prompt = load_agent_prompt(agent_type)
    full_prompt = build_full_prompt(agent_type, context, output_format)

    pass_outputs = []

    # Run 3 passes with different temperatures
    for i, pass_config in enumerate(MULTI_PASS_CONFIG["passes"]):
        yield {'type': 'status', 'data': f'Pass {i+1}/3: {pass_config["label"]}...'}

        response = ""
        with anthropic_client.messages.stream(
            model=pass_config["model"],
            max_tokens=16000,
            temperature=pass_config["temperature"],
            system=agent_prompt,
            messages=[{"role": "user", "content": full_prompt}]
        ) as stream:
            for text in stream.text_stream:
                response += text
                yield {'type': 'content', 'data': f'[Pass {i+1}] '}  # Indicate which pass

        pass_outputs.append({
            "label": pass_config["label"],
            "content": response
        })

    # Meta-synthesis with Opus
    yield {'type': 'status', 'data': 'Meta-synthesis with Opus...'}

    meta_prompt = load_agent_prompt("meta_synthesizer")
    meta_input = build_meta_synthesis_input(pass_outputs)

    final_response = ""
    with anthropic_client.messages.stream(
        model=MULTI_PASS_CONFIG["meta_synthesis"]["model"],
        max_tokens=20000,
        temperature=MULTI_PASS_CONFIG["meta_synthesis"]["temperature"],
        system=meta_prompt,
        messages=[{"role": "user", "content": meta_input}]
    ) as stream:
        for text in stream.text_stream:
            final_response += text
            yield {'type': 'content', 'data': text}

    # Store final output with multi_pass flag
    # ... (storage logic with synthesis_mode='multi_pass')
```

---

### Phase 2: Frontend Changes

#### 2.1 Add Multi-Pass Toggle

**File**: `/frontend/components/purdy/AgentRunner.tsx`

Add state and UI:

```typescript
const [multiPass, setMultiPass] = useState(false)

// In the UI, after output format selector:
{selectedAgent === 'synthesizer' && (
  <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
    <label className="flex items-start gap-3 cursor-pointer">
      <input
        type="checkbox"
        checked={multiPass}
        onChange={(e) => setMultiPass(e.target.checked)}
        disabled={running}
        className="mt-1"
      />
      <div>
        <div className="font-medium text-amber-900 dark:text-amber-100">
          Multi-Pass Synthesis
        </div>
        <div className="text-xs text-amber-700 dark:text-amber-300">
          Runs 3 passes with varying creativity levels, then synthesizes the best of all.
          Takes longer but produces higher quality insights.
        </div>
        <div className="text-xs text-amber-600 dark:text-amber-400 mt-1">
          Estimated time: 45-60 minutes | Cost: ~$6-7
        </div>
      </div>
    </label>
  </div>
)}
```

#### 2.2 Update Progress Display

Show which pass is currently running:

```typescript
// In the status header, show pass progress
{running && multiPass && (
  <div className="flex items-center gap-2">
    <div className="flex gap-1">
      {[1, 2, 3, 4].map((pass) => (
        <div
          key={pass}
          className={`w-2 h-2 rounded-full ${
            currentPass >= pass
              ? 'bg-indigo-500'
              : 'bg-slate-300 dark:bg-slate-600'
          }`}
        />
      ))}
    </div>
    <span className="text-xs text-slate-500">
      {currentPass <= 3 ? `Pass ${currentPass}/3` : 'Meta-synthesis'}
    </span>
  </div>
)}
```

---

### Phase 3: Database Changes

#### 3.1 Add Synthesis Mode Column

**File**: `/database/migrations/044_multi_pass_synthesis.sql`

```sql
-- Add synthesis_mode column to track single vs multi-pass
ALTER TABLE purdy_outputs
ADD COLUMN IF NOT EXISTS synthesis_mode TEXT DEFAULT 'single';

-- Add intermediate_outputs for storing the 3 pass results
ALTER TABLE purdy_outputs
ADD COLUMN IF NOT EXISTS intermediate_outputs JSONB;

COMMENT ON COLUMN purdy_outputs.synthesis_mode IS 'single or multi_pass';
COMMENT ON COLUMN purdy_outputs.intermediate_outputs IS 'Stores 3 pass outputs for multi-pass synthesis';
```

---

## UI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ Select Agent                                                     │
├─────────────────────────────────────────────────────────────────┤
│ ○ Triage v2.6                                                   │
│ ○ Discovery Planner v2.9                                        │
│ ○ Coverage Tracker v2.7                                         │
│ ● Synthesizer v2.8  ←──────────────────────── Selected          │
│ ○ Tech Evaluation v2.7                                          │
├─────────────────────────────────────────────────────────────────┤
│ Output Format                                                    │
│ ● Comprehensive  ○ Executive  ○ Brief                           │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ☑ Multi-Pass Synthesis                                      │ │
│ │   Runs 3 passes with varying creativity levels, then        │ │
│ │   synthesizes the best of all. Takes longer but produces    │ │
│ │   higher quality insights.                                  │ │
│ │   Estimated time: 45-60 minutes | Cost: ~$6-7               │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                                        [▶ Run Agent]            │
└─────────────────────────────────────────────────────────────────┘

When running multi-pass:

┌─────────────────────────────────────────────────────────────────┐
│ Synthesizer Output                    ● ● ○ ○  Pass 2/3         │
├─────────────────────────────────────────────────────────────────┤
│ ⟳ Pass 2: Balanced...                                          │
│                                                                  │
│ [Pass 2] # The Surprising Truth...                              │
│ [Pass 2] > What stakeholders don't realize...                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estimated Effort

| Phase | Task | Effort |
|-------|------|--------|
| Backend | Update AgentRunRequest | 15 min |
| Backend | Add multi-pass config | 15 min |
| Backend | Create meta-synthesizer prompt | 30 min |
| Backend | Implement run_agent_multi_pass | 2 hrs |
| Frontend | Add multi-pass toggle | 30 min |
| Frontend | Update progress display | 30 min |
| Database | Migration | 15 min |
| Testing | End-to-end test | 1 hr |
| **Total** | | **~5 hours** |

---

## Future Enhancements

1. **Expose intermediate outputs**: Let users view all 3 pass outputs, not just the final
2. **A/B comparison view**: Side-by-side compare any two passes
3. **Selective re-run**: Re-run just one pass if it seems off
4. **Custom temperature control**: Let power users set their own temperatures
5. **Other agents**: Extend multi-pass to Discovery Planner and Tech Evaluation

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Long run time (45-60 min) | Clear progress indicator, allow background runs |
| Higher cost (~$6-7) | Show cost estimate before running |
| Meta-synthesis conflicts | Clear instructions in meta-synthesizer prompt |
| User confusion | Only show option for Synthesizer, clear UI labels |
