# Agent Prompt Audit: Findings Report

**Audit Date**: January 20, 2026
**Auditor**: Claude Code
**Focus**: Finding over-engineered LLM prompts and interactions
**Baseline**: Thesis codebase as of commit 99022b30

---

## Executive Summary

Systematic audit of the Thesis codebase identified **6 key issues** where LLM prompts are over-engineered with complex formats that could be simplified. The good news: the task extraction system was already fixed (commit beba18da), demonstrating the codebase is moving in the right direction.

**Overall Pattern**: The codebase tends toward **over-specified output formats** that add complexity without necessarily improving quality. Most issues cluster in three service areas:
1. Career status report generation (most over-engineered)
2. Opportunity justification generation
3. Document classifier LLM fallback

**Estimated Impact**: Simplifying these prompts could improve:
- LLM response reliability (fewer parsing failures)
- Token efficiency (shorter prompts, faster generation)
- Output quality (natural language instead of structured formats)
- Maintenance burden (fewer regex parsers needed)

---

## ISSUE 1: Career Status Report - Excessive Format Specification (HIGH PRIORITY)

**File**: `/backend/services/career_status_report.py`
**Lines**: 272-318
**Severity**: HIGH
**Model Impact**: Claude Sonnet 4

### Current Approach

The prompt specifies exact output formatting with precise markers:
```
Format your response EXACTLY as:
EXECUTIVE_SUMMARY: [your text]
STRATEGIC_IMPACT_SCORE: [1-5]
STRATEGIC_IMPACT_JUSTIFICATION: [your text]
STRATEGIC_IMPACT_IMPROVEMENTS: [action1] | [action2] | [action3]
[repeats for 4 more dimensions...]
```

This creates:
- 8 required line markers
- Pipe-delimited lists (unusual format)
- Strict single-line constraint per section
- Complex parsing logic (lines 352-408)

### What Makes It Over-Engineered

1. **Over-specified markers**: The prompt demands exact formatting with colons, making it fragile
2. **Pipe delimiters**: Why pipes instead of natural sentence endings or markdown?
3. **Single-line constraint**: Forces actions into cramped format: `[action1] | [action2] | [action3]`
4. **Parsing complexity**: 76 lines of parsing code with multiple fallback attempts
5. **Rigid structure**: If Claude adds a single preamble line, parsing fails

### The Test: Natural Prompt Version

Instead of the current approach, Claude could naturally write:
```
Generate a career status report with:
- Overall assessment
- Scores 1-5 for each of the 5 dimensions
- Justification for each score (2-3 sentences)
- 2-3 actionable improvements for each dimension
- Key strengths
- Growth opportunities
- Next steps
```

Claude would naturally structure this with headers and clear sections. No pipe delimiters needed.

### Suggested Fix

**Simpler prompt**:
```python
def _build_assessment_prompt(context: dict) -> str:
    """Build the prompt for career status assessment."""

    # Format rubric dimensions
    rubric_text = "CAREER ASSESSMENT RUBRIC:\n\n"
    for key, dim in DEFAULT_RUBRIC.items():
        rubric_text += f"### {dim['name']} (Weight: {dim['weight']}%)\n"
        rubric_text += f"{dim['description']}\n"
        for level, desc in sorted(dim["levels"].items(), reverse=True):
            rubric_text += f"  Level {level}: {desc}\n"
        rubric_text += "\n"

    # Format KB context
    kb_context = ""
    if context.get("kb_documents"):
        kb_context = "\n\nCAREER DOCUMENTS (from Knowledge Base):\n"
        for i, doc in enumerate(context["kb_documents"], 1):
            kb_context += f"\n--- Document {i}: {doc['title']} ---\n"
            kb_context += doc["content"][:1500]
            kb_context += "\n"

    return f"""You are Compass, a career coaching agent. Generate a comprehensive career status report.

{rubric_text}{kb_context}

Assess performance across all 5 dimensions (1-5 scale). For each:
- Your score
- Why you gave that score (2-3 sentences with specific evidence)
- Concrete improvements (2-3 actions they can take this month)

Also provide:
- Overall career trajectory summary
- 2-3 key strengths
- 2-3 growth opportunities
- Top 3 priorities moving forward

Format with clear headers and natural prose."""
```

**Parsing becomes trivial** with markdown headers:
```python
def _parse_assessment_response(response_text: str) -> dict:
    """Parse career status report using markdown headers."""
    result = {
        "executive_summary": extract_section(response_text, "Overall"),
        "strategic_impact": extract_score(response_text, "Strategic Impact"),
        "strategic_impact_justification": extract_section(response_text, "Strategic Impact", include_score=False),
        # ... etc
    }
```

### Expected Improvement

- **Parsing code**: From 76 lines to ~20 lines
- **Prompt clarity**: From 47 lines to ~25 lines
- **Error handling**: Fewer edge cases, better fallbacks
- **Output quality**: Claude's natural structure often better than forced formats

---

## ISSUE 2: Opportunity Justification - Over-Specified JSON Fields (MEDIUM-HIGH PRIORITY)

**File**: `/backend/services/opportunity_justification.py`
**Lines**: 68-85
**Severity**: MEDIUM-HIGH
**Model Impact**: Claude Haiku

### Current Approach

The prompt requests a very specific JSON structure with 5 fields:
```
Generate the following in a professional, concise tone. Each should be exactly 3-4 sentences:

1. OPPORTUNITY_SUMMARY: Describe what this opportunity is and its potential business impact.
2. ROI_JUSTIFICATION: Explain why this opportunity received its ROI score...
3. EFFORT_JUSTIFICATION: Explain why this opportunity received its implementation ease score...
4. ALIGNMENT_JUSTIFICATION: Explain why this opportunity received its strategic alignment score...
5. READINESS_JUSTIFICATION: Explain why this opportunity received its stakeholder readiness score...

Format your response exactly as:
OPPORTUNITY_SUMMARY: [your text]
ROI_JUSTIFICATION: [your text]
...
```

### What Makes It Over-Engineered

1. **Overly prescriptive**: "exactly 3-4 sentences" - Claude knows when sections should be brief
2. **Named sections**: Creates expectation of rigid compliance
3. **Repetitive pattern**: All 5 sections follow identical structure (dimension + score explanation)
4. **Parsing fragility**: If Claude formats differently, parsing breaks

### The Test: Natural Prompt Version

```
Generate a 3-4 sentence justification for this opportunity's scores. Cover:
- What this opportunity is and why it matters
- Why the ROI potential is [X]/5
- Why implementation effort is [X]/5
- Why it aligns with strategy at [X]/5
- Why stakeholder readiness is [X]/5

Keep professional and concise.
```

Claude will naturally use paragraphs or bullets. Either works fine.

### Suggested Fix

Instead of named sections with exact formatting:
```python
def _build_generation_prompt(opportunity: dict) -> str:
    """Build the prompt for generating justifications."""

    title = opportunity.get("title", "Untitled")
    description = opportunity.get("description") or "No description provided"
    roi = opportunity.get("roi_potential")
    effort = opportunity.get("implementation_effort")
    alignment = opportunity.get("strategic_alignment")
    readiness = opportunity.get("stakeholder_readiness")

    return f"""Generate a concise justification for this AI opportunity's scores.

**Opportunity**: {title}
**Description**: {description}

**Scores**: ROI {roi}/5 | Effort {effort}/5 | Alignment {alignment}/5 | Readiness {readiness}/5

Write 3-4 sentences covering:
1. What this opportunity is and business impact
2. Why ROI potential is {roi}/5
3. Why implementation effort is {roi}/5
4. Why strategic alignment is {alignment}/5
5. Why stakeholder readiness is {readiness}/5

Be professional and specific."""
```

**Parsing**: Just grab the response text as-is:
```python
justifications = {
    "opportunity_summary": response_text[:500],  # First part
    "all_justifications": response_text  # Store whole response
}
```

The UI can display the natural text directly.

### Expected Improvement

- **Parsing code**: From 38 lines to ~5 lines (just take the text)
- **Prompt clarity**: From 39 lines to ~20 lines
- **Flexibility**: Claude can structure output naturally
- **Token efficiency**: Shorter prompt, fewer wasted tokens on format specification

---

## ISSUE 3: Document Classifier - Over-Complex LLM Fallback Prompt (MEDIUM PRIORITY)

**File**: `/backend/services/document_classifier.py`
**Lines**: 307-339
**Severity**: MEDIUM
**Model Impact**: Claude Haiku

### Current Approach

When keyword scoring is ambiguous, the classifier asks Claude Haiku to score documents against 15 agents with a very specific JSON schema:

```json
{
  "agents": [
    {"name": "agent_name", "confidence": 0.0, "reason": "brief explanation"}
  ],
  "document_type": "brief description of document type"
}
```

The prompt includes:
- Full agent list (50+ lines)
- Detailed rules ("Include only agents with confidence >= 0.4")
- Multiple constraints ("Maximum 3 agents per document")
- Document sample (3000 chars)

### What Makes It Over-Engineered

1. **Full agent list**: Forcing Haiku to process 15 agent descriptions every time (wasteful)
2. **JSON schema requirement**: Creating parsing complexity unnecessarily
3. **Multiple constraints**: "Include only..." "Order by..." "Maximum 3..." - could be simpler
4. **Markdown code block handling**: Lines 367-370 handle Claude wrapping in ```json, indicating prompt brittleness

### The Test: Natural Prompt Version

```
Read this document sample and list which of these agents would find it useful:
- atlas: Research, case studies, best practices
- capital: ROI, budgets, financial planning
- guardian: Security, compliance, governance
[etc - brief descriptions only]

List agents you think would use this (top 3, with confidence 0-1.0).
```

Claude will naturally return something like:
```
capital (0.85) - Financial analysis focused on ROI
operator (0.72) - Business process optimization
architect (0.65) - Technical implementation concerns
```

### Suggested Fix

```python
def _build_llm_prompt(self, sample_text: str) -> str:
    """Build the LLM classification prompt."""

    # Just the brief descriptions, not full agent list
    agents_brief = "capital (ROI, budgets), guardian (security, compliance), operator (processes)"

    return f"""Which Thesis agents would find this document most useful?

The agents are: atlas (research), capital (finance), guardian (security), counselor (legal),
oracle (meetings), sage (people), strategist (executive), architect (technical), operator (ops),
pioneer (innovation), catalyst (comms), scholar (learning), echo (brand voice), nexus (systems),
manual (platform help)

Document sample:
{sample_text[:2000]}

List the top 3 agents who'd use this, with confidence (0-1.0). Keep it concise."""
```

**Parsing natural response**:
```python
def _parse_llm_response(response_text: str) -> dict[str, float]:
    """Parse agent recommendations from natural language."""
    scores = {}
    lines = response_text.split('\n')
    for line in lines:
        # Look for "agent_name (0.xx)" patterns
        match = re.search(r'(\w+)\s*\((\d\.?\d*)\)', line)
        if match:
            agent = match.group(1).lower()
            confidence = float(match.group(2))
            if agent in self.AGENT_KEYWORDS:
                scores[agent] = confidence
    return scores
```

### Expected Improvement

- **Prompt tokens**: From ~200 tokens to ~100 tokens (50% reduction)
- **Parsing code**: Simpler, more robust
- **Latency**: Faster Haiku response
- **Error rate**: Less fragile JSON parsing

---

## ISSUE 4: Task Extractor LLM - Improved But Still Formatful (LOW-MEDIUM PRIORITY)

**File**: `/backend/services/task_extractor.py`
**Lines**: 222-253
**Severity**: LOW-MEDIUM (Already Much Better)
**Model Impact**: Claude Sonnet 4

### Current Status

This one is MUCH better than before (commit beba18da improved it significantly). The prompt is now natural:

```
I need you to find action items{user_str} from this document...

A task is:
- A specific deliverable someone agreed to complete
- Something with a clear owner (explicit or implied)
- An action that requires work AFTER this document was created

NOT a task:
[clear negatives...]

For each genuine task found, return JSON:
{ "title": "...", "description": "...", ... }
```

This is actually pretty good. However, there's still one over-specification:

### Minor Issue: Field Over-Specification

The JSON structure has 8 fields:
```json
{
  "title": "Action verb + specific deliverable",
  "description": "2-3 sentences with FULL CONTEXT",
  "assignee": "Who owns this",
  "priority": "high/medium/low",
  "source_text": "The exact quote",
  "due_date_text": "Any mentioned deadline",
  "meeting_context": "What was this meeting about?",
  "stakeholder_name": "Who requested this?",
  "topics": ["relevant", "tags"]
}
```

### Suggested Refinement

Claude naturally returns what's needed. Could simplify to:
```
For each task, provide:
- Title (action verb + deliverable)
- Who should do it
- Any deadline mentioned
- Why it matters (context/stakeholder)
- Relevant tags/topics
```

Return as JSON if the parser can handle it, or natural text formatted as:
```
Task: [title]
Owner: [name]
Due: [date if mentioned]
Context: [why it matters]
```

### Expected Improvement

- **Parsing code**: Could eliminate JSON parsing, use simple regex
- **Flexibility**: Claude might include additional context naturally
- **Robustness**: No JSON decode errors

---

## ISSUE 5: Oracle Agent System Instruction - Over-Detailed Output Format (LOW PRIORITY)

**File**: `/backend/system_instructions/agents/oracle.xml`
**Lines**: 202-242
**Severity**: LOW
**Model Impact**: User-facing quality, not token efficiency

### Current Approach

The Oracle instruction specifies a 10-section output format:
```
1. Meeting Summary - 2-3 sentence overview
2. Meeting Metadata - Date, type, duration
3. Attendees - Name, role, org, engagement
4. Sentiment Analysis by Speaker - Multiple fields per speaker
5. Key Topics Discussed - Listed in order
6. Action Items - Description, owner, due date, dependencies
7. Decisions Made - Both explicit and implicit
8. Open Questions - Unresolved topics
9. Stakeholder Insights - Name, type, content, quote, confidence
10. Strategic Recommendations - Specific follow-up actions
```

This is 10 required sections with strict field specifications.

### What Makes It Over-Engineered

1. **Prescriptive structure**: Forces a standard format that might not fit the meeting
2. **Too many required sections**: Some meetings don't need all 10
3. **Field specificity**: Requires exact field names and types
4. **Parsing expectation**: The output format makes it seem like it needs to be parsed, but it's actually user-facing

### Why It's LOW Priority

This isn't actually hurting performance - Oracle is a user-facing agent, and having clear structure is good. But it's worth noting that the specification is **overly rigid**.

### Suggested Approach

Instead of mandating 10 sections, give Oracle guidance:
```
Analyze this meeting and provide what's most relevant. Typical outputs include:
- Meeting summary (1-2 sentences)
- Who attended (and their roles/interests)
- Key sentiment/positions by speaker
- Action items and decisions
- Open questions or risks
- Specific engagement recommendations

Structure for clarity, but adapt format to the meeting content.
```

This gives flexibility while maintaining quality.

---

## ISSUE 6: Smart Brevity Inclusion - Potential Redundancy (VERY LOW PRIORITY)

**File**: `/backend/system_instructions/agents/oracle.xml`
**Line**: 22
**Severity**: VERY LOW
**Model Impact**: None (optimization question)

### Current

The Oracle instruction includes:
```xml
<!-- Include Smart Brevity formatting directive -->
<include file="shared/smart_brevity.xml" />
```

This is good practice for code reuse. However, this means:
- Smart Brevity rules are applied PLUS
- Oracle's custom format specification (10 sections) is applied
- Potential conflict between "100-150 word max" and "10 required sections"

### Suggested Clarification

Document the interaction clearly:
```xml
<!-- Include Smart Brevity formatting directive (100-150 word limit applies) -->
<!-- Note: This may require condensing the standard 10-section format for conciseness -->
<include file="shared/smart_brevity.xml" />
```

This is really a documentation issue, not a logic issue.

---

## SUMMARY TABLE: Issues by Severity and Effort

| # | File | Issue | Severity | Effort | Token Savings | Quality Impact |
|---|------|-------|----------|--------|---------------|----------------|
| 1 | career_status_report.py | Over-specified format markers | HIGH | Medium | ~50% prompt | +High |
| 2 | opportunity_justification.py | Rigid JSON schema | MEDIUM-HIGH | Low | ~40% prompt | +Medium |
| 3 | document_classifier.py | Over-complex LLM fallback | MEDIUM | Medium | ~50% prompt | +Medium |
| 4 | task_extractor.py | Field over-specification | LOW-MEDIUM | Low | ~20% prompt | +Low |
| 5 | oracle.xml | Over-detailed output format | LOW | Low | None | Neutral |
| 6 | smart_brevity.xml | Potential rule conflicts | VERY LOW | Low | None | Neutral |

---

## Recommendations by Priority

### Immediate (Next Sprint)
1. **Simplify Career Status Report** (Issue #1)
   - Reduce parsing complexity from 76 to ~20 lines
   - Improve LLM reliability significantly
   - Estimated effort: 2 hours

2. **Simplify Opportunity Justification** (Issue #2)
   - Remove JSON requirement, accept natural text
   - Reduce parsing from 38 to ~5 lines
   - Estimated effort: 1 hour

### Short Term (1-2 Sprints)
3. **Refactor Document Classifier LLM Fallback** (Issue #3)
   - Reduce prompt size by ~50%
   - Improve Haiku efficiency
   - Estimated effort: 2-3 hours

4. **Refactor Task Extractor JSON** (Issue #4)
   - Optional: currently working well, low ROI
   - Consider after bigger issues
   - Estimated effort: 1-2 hours

### Optional/Documentation
5. Document Oracle format interaction with Smart Brevity (Issue #6)
6. Consider making Oracle format more flexible (Issue #5)

---

## Testing Approach for Fixes

When implementing these changes:

1. **Generate test set**: Run 10 documents/tasks through current system, save outputs
2. **Implement simpler prompt**: Deploy new version
3. **Compare results**: Check for parsing failures, quality changes
4. **Validate parsing**: Ensure new regex/parsing handles all cases
5. **Performance check**: Verify token count reduction

### Success Criteria

- All test cases produce same or better quality results
- No parsing failures (zero regex errors)
- Prompt tokens reduced by estimated amount
- No regressions in user-facing quality

---

## Notes for Implementation

### Key Principle

When simplifying, remember: **Claude is good at understanding intent**. You don't need to specify every detail. A natural language request often produces better results than rigid format requirements.

### Pattern to Apply Everywhere

**Before**:
```
"Format your response EXACTLY as: SECTION_NAME: [content]"
```

**After**:
```
"Format with clear headers for readability"
```

Claude knows how to structure responses. Trust it.

### Verify Against These Anti-Patterns

These are signs over-engineering is happening:
- Prompt includes phrase "EXACTLY as"
- More than 3 "MUST" statements about format
- Response parsing code is longer than prompt itself
- Format spec takes more lines than the actual task description
- Fields are defined with very specific character limits

---

## Related Context

This audit follows the earlier fix in commit beba18da (task extraction simplified from complex JSON schema to natural language request). That successful simplification validates the approach of moving toward more natural prompts.

The codebase is already trending in the right direction. These findings accelerate that improvement.

---

## Appendix: Files Reviewed

- `/backend/services/career_status_report.py` - Career status generation
- `/backend/services/opportunity_justification.py` - Opportunity scoring justifications
- `/backend/services/document_classifier.py` - Document agent relevance classification
- `/backend/services/task_extractor.py` - Task extraction (already mostly fixed)
- `/backend/system_instructions/agents/oracle.xml` - Meeting analysis agent instruction
- `/backend/system_instructions/shared/smart_brevity.xml` - Response format directive
- Git history: commits beba18da (task extraction fix) and 99022b30 (current)

---

## Questions for Further Exploration

If you want to go deeper on any of these:

1. **How do parsing failures currently manifest?** (Any error logs?)
2. **What's the token usage breakdown?** (Prompt vs response vs overhead?)
3. **Have users complained about output format?** (Is the rigid format necessary?)
4. **What's the regex parsing error rate in production?** (How often does format vary?)
5. **Are there other services with similar patterns?** (Worth auditing more?)

---

**End of Audit Report**

*This report was generated as part of code quality improvement work on the Thesis platform. All findings are recommendations for enhancement, not critical bugs.*
