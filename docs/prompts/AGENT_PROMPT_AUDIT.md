# Agent Prompt Audit: Finding Over-Engineered LLM Interactions

## Context

We discovered that the task extraction system was being "too clever" with its prompts - adding complex JSON schemas, detailed field descriptions, and multiple constraints that actually made the LLM perform WORSE than a simple, natural prompt would.

The fix was simple: instead of complex instructions, just ask Claude naturally: "I need you to find action items from this document..."

This pattern likely exists elsewhere in the codebase.

## Audit Prompt

Use this prompt to review the Thesis codebase for similar issues:

---

**Your Task**: Audit the Thesis multi-agent platform for over-engineered LLM prompts and interactions.

**Problem Pattern to Find**:
- Prompts that try to be "clever" with complex schemas, detailed field specifications, or multiple nested constraints
- Prompts that would work better if they just asked Claude naturally (like a human would)
- Places where structured output requirements make the LLM worse at the actual task
- Agent system instructions that are overly prescriptive about format vs. substance

**Files to Review**:
1. `/backend/system_instructions/agents/*.xml` - All agent system prompts
2. `/backend/services/task_extractor.py` - Task extraction (recently fixed)
3. `/backend/services/document_classifier.py` - Document classification prompts
4. `/backend/services/career_status_report.py` - Career report generation
5. `/backend/services/opportunity_justification.py` - AI-generated justifications
6. `/backend/services/transcript_analyzer.py` - Meeting transcript analysis
7. `/backend/agents/*.py` - Agent implementations with any embedded prompts

**What to Look For**:

1. **Complex JSON Schemas in Prompts**
   - Multiple nested fields with detailed descriptions
   - Overly specific format requirements
   - Fields that the LLM struggles to populate correctly

2. **Negative Instructions Overload**
   - Long lists of "do NOT do X"
   - Multiple constraints that confuse more than clarify

3. **Over-Specified Output Formats**
   - Asking for specific character counts
   - Requiring exact formatting that adds no value
   - Mandatory fields that often come back empty or wrong

4. **Prompts That Don't Sound Natural**
   - If you wouldn't ask a human colleague this way, don't ask Claude this way
   - Overly formal or robotic language
   - Instructions that require multiple re-reads to understand

**For Each Issue Found, Document**:
1. File and line number
2. Current prompt approach (brief summary)
3. What makes it over-engineered
4. Suggested simpler approach
5. Expected improvement

**Output Format**:
```markdown
## [File Path]

### Issue: [Brief description]
**Lines**: X-Y
**Current Approach**: [What it does now]
**Problem**: [Why it's over-engineered]
**Suggested Fix**: [Simpler approach]

---
```

**Prioritization**:
- HIGH: User-facing features where quality matters (task extraction, meeting analysis, career reports)
- MEDIUM: Internal agent instructions that affect response quality
- LOW: Edge case handling or rarely-used features

---

## Run Instructions

1. Start a new Claude Code session
2. Paste this audit prompt
3. Ask Claude to systematically review each file category
4. Collect findings into a single document
5. Prioritize fixes by user impact

## Success Criteria

The simplest test: Would the prompt work better if you just asked Claude like you'd ask a colleague?

"Hey Claude, can you find action items in this meeting transcript?"
vs.
"Extract all ACTION_ITEMs matching schema {complex_json} where each item MUST have fields A, B, C, D, E and MUST NOT include X, Y, Z..."

The first approach usually wins.
