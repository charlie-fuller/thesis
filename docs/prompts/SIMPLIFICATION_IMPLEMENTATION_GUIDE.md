# Prompt Simplification Implementation Guide

**Purpose**: Step-by-step guide for refactoring over-engineered prompts into simpler, more natural requests

**Difficulty**: Low-Medium (mostly copy-paste with validation)

---

## Template: The Simplification Process

### Step 1: Identify Over-Engineering Markers

Look for these red flags:
- `"EXACTLY as"` or `"Format your response"` phrases
- JSON schemas with 5+ required fields
- Numbered lists with strict requirements
- Multiple "MUST NOT" constraints
- Parsing code longer than 30 lines
- Regex patterns with 15+ capture groups

### Step 2: Understand the Goal

Ask: "What is Claude actually supposed to do?"

Remove everything that's not essential to the goal. For example:
- **Career Report Goal**: "Assess someone's performance across 5 dimensions with scores and justifications"
- **Unnecessary Detail**: Exact format markers, pipe delimiters, single-line constraints

### Step 3: Write the Natural Version

Pretend you're asking a human colleague. Write that request. Include:
- What you need
- Why you need it
- Quality standards (if any)

Don't include format specs yet.

### Step 4: Handle Output Parsing

**Option A: Use Markdown Headers** (Recommended)
- Ask Claude to use headers: `### Dimension Name`
- Parse by searching for headers
- More robust than regex

**Option B: Use Simple Delimiters**
- Fewer than 3 required delimiters
- Simple regex patterns (5-10 chars max)

**Option C: Use JSON But Simplified**
- Only 3-5 truly required fields
- Let Claude structure sub-fields naturally
- Store whole response as text if needed

### Step 5: Test and Validate

1. Generate 10-20 test cases with new prompt
2. Check: Do all parse correctly?
3. Check: Is quality same or better?
4. Check: Are tokens reduced?
5. If any fail, add specific guidance to prompt (don't add constraints)

---

## Worked Example: Career Status Report Fix

### BEFORE: Over-Engineered Version

```python
# Current prompt (lines 272-318 of career_status_report.py)
prompt = f"""You are Compass, a career coaching agent. Generate a comprehensive career status report based on the rubric and available context.

{rubric_text}
{kb_context}
{memory_context}

Based on the available information, assess career performance across all 5 dimensions...

Generate the following:

1. EXECUTIVE_SUMMARY: A 2-3 sentence overall assessment...

2. For each dimension, provide:
   - SCORE (1-5 based on rubric levels)
   - JUSTIFICATION (2-3 sentences explaining the score...)
   - IMPROVEMENT_ACTIONS: 2-3 concrete, actionable steps...

Format your response EXACTLY as:
EXECUTIVE_SUMMARY: [your text]

STRATEGIC_IMPACT_SCORE: [1-5]
STRATEGIC_IMPACT_JUSTIFICATION: [your text]
STRATEGIC_IMPACT_IMPROVEMENTS: [action1] | [action2] | [action3]

EXECUTION_QUALITY_SCORE: [1-5]
EXECUTION_QUALITY_JUSTIFICATION: [your text]
EXECUTION_QUALITY_IMPROVEMENTS: [action1] | [action2] | [action3]

RELATIONSHIP_BUILDING_SCORE: [1-5]
RELATIONSHIP_BUILDING_JUSTIFICATION: [your text]
RELATIONSHIP_BUILDING_IMPROVEMENTS: [action1] | [action2] | [action3]

GROWTH_MINDSET_SCORE: [1-5]
GROWTH_MINDSET_JUSTIFICATION: [your text]
GROWTH_MINDSET_IMPROVEMENTS: [action1] | [action2] | [action3]

LEADERSHIP_PRESENCE_SCORE: [1-5]
LEADERSHIP_PRESENCE_JUSTIFICATION: [your text]
LEADERSHIP_PRESENCE_IMPROVEMENTS: [action1] | [action2] | [action3]

AREAS_OF_STRENGTH: [item1] | [item2] | [item3]
GROWTH_OPPORTUNITIES: [item1] | [item2] | [item3]
RECOMMENDED_ACTIONS: [item1] | [item2] | [item3]"""

# Parsing (lines 321-424)
def _parse_assessment_response(response_text: str) -> dict:
    """Parse the Claude response into structured fields."""
    result = {
        "executive_summary": None,
        "strategic_impact": None,
        # ... 11 more fields
    }

    # Parse text fields
    text_sections = {
        "EXECUTIVE_SUMMARY:": "executive_summary",
        "STRATEGIC_IMPACT_JUSTIFICATION:": "strategic_impact_justification",
        # ... 5 more fields
    }

    # Parse scores
    score_sections = {
        "STRATEGIC_IMPACT_SCORE:": "strategic_impact",
        "EXECUTION_QUALITY_SCORE:": "execution_quality",
        # ... 3 more fields
    }

    # Parse list fields
    list_sections = {
        "AREAS_OF_STRENGTH:": "areas_of_strength",
        "GROWTH_OPPORTUNITIES:": "growth_opportunities",
        "RECOMMENDED_ACTIONS:": "recommended_actions",
    }

    # Parse improvement actions per dimension
    improvement_sections = {
        "STRATEGIC_IMPACT_IMPROVEMENTS:": "strategic_impact",
        # ... 4 more fields
    }

    lines = response_text.split("\n")
    for line in lines:
        line = line.strip()

        # Check score sections
        for marker, field in score_sections.items():
            if line.startswith(marker):
                try:
                    score_str = line[len(marker) :].strip()
                    score = int(score_str.split()[0])
                    if 1 <= score <= 5:
                        result[field] = score
                except (ValueError, IndexError):
                    pass

        # ... more parsing code ...

    return result
```

**Issues**:
- 47 lines of prompt instruction + format spec
- 103 lines of parsing code
- 8 required markers
- Pipe delimiters for lists
- Multiple fallback attempts

### AFTER: Simplified Version

```python
# New prompt (simplified)
prompt = f"""You are Compass, a career coaching agent. Assess this person's career performance across 5 dimensions.

{rubric_text}
{kb_context}

Generate a comprehensive career status report:

1. Overall assessment (2-3 sentences about their trajectory)
2. For each dimension, provide:
   - Your score (1-5)
   - Why you gave that score (2-3 sentences with specific evidence)
   - 2-3 concrete actions they can take this month
3. Top 3-4 key strengths
4. Top 3-4 growth opportunities
5. Top 3 priorities to focus on

Use clear headers to organize sections (e.g., "### Strategic Impact"). Write naturally."""

# Parsing (simplified)
def _parse_assessment_response(response_text: str) -> dict:
    """Parse career assessment from markdown headers."""
    result = {
        "executive_summary": extract_section(response_text, ["Overall", "Summary", "Assessment"]),
        "strategic_impact": extract_score(response_text, "Strategic Impact"),
        "execution_quality": extract_score(response_text, "Execution Quality"),
        "relationship_building": extract_score(response_text, "Relationship Building"),
        "growth_mindset": extract_score(response_text, "Growth Mindset"),
        "leadership_presence": extract_score(response_text, "Leadership Presence"),
        "areas_of_strength": extract_list(response_text, "Strengths"),
        "growth_opportunities": extract_list(response_text, "Opportunities|Growth"),
        "recommended_actions": extract_list(response_text, ["Priorities", "Actions", "Focus"]),
    }

    # Extract justifications from sections
    result["strategic_impact_justification"] = extract_section(response_text, "Strategic Impact", lines=2)
    # ... similar for other dimensions

    # Calculate overall score
    scores = [
        result.get("strategic_impact"),
        result.get("execution_quality"),
        result.get("relationship_building"),
        result.get("growth_mindset"),
        result.get("leadership_presence"),
    ]
    valid_scores = [s for s in scores if s is not None]
    if valid_scores:
        result["overall_score"] = round(sum(valid_scores) / len(valid_scores), 2)

    return result


# Helper functions
def extract_section(text: str, headers: list | str, lines: int = 3) -> str:
    """Extract content under a header."""
    if isinstance(headers, str):
        headers = [headers]

    for header in headers:
        pattern = rf"### {header}.*?\n((?:.*?\n){{0,{lines}}})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_score(text: str, dimension: str) -> int:
    """Extract score from text."""
    pattern = rf"### {dimension}.*?(?:score|rated|assessment)[:=\s]+(\d+)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return None


def extract_list(text: str, headers: list | str) -> list:
    """Extract bulleted list."""
    if isinstance(headers, str):
        headers = [headers]

    for header in headers:
        pattern = rf"### {header}.*?\n((?:\s*[-*]\s.*\n)*)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            items = re.findall(r"[-*]\s+(.*?)(?=\n|$)", match.group(1))
            return [item.strip() for item in items if item.strip()]
    return []
```

**Improvements**:
- Prompt: 47 lines → 23 lines (51% reduction)
- Parsing: 103 lines → ~50 lines (helper functions reusable)
- Markers: 8 required → 0 required (uses natural headers)
- Error recovery: Better (markdown headers are more stable)

---

## Implementation Checklist

### For Each Simplification

- [ ] **Read the current code** (prompt + parsing)
- [ ] **Identify the over-engineering** (use markers from Step 1)
- [ ] **Identify the true goal** (1-2 sentences)
- [ ] **Write natural version** (as if asking a colleague)
- [ ] **Design parsing strategy** (markdown/delimiters/JSON)
- [ ] **Write helper functions** (extract_section, extract_list, etc.)
- [ ] **Create test file** (10-20 test cases)
- [ ] **Generate test data** (run current system on test set)
- [ ] **Implement new prompt** (in staging)
- [ ] **Test new prompt** (same test set)
- [ ] **Compare results** (quality, parsing errors, tokens)
- [ ] **Document changes** (what was simplified, why)
- [ ] **Commit** (conventional commit: `refactor: simplify [service] prompts`)

---

## Common Parsing Strategies

### Strategy 1: Markdown Headers (Recommended)

**Best for**: Multi-section reports, assessments, analysis

**Prompt instruction**:
```
Use clear section headers (### Section Name) to organize your response.
```

**Parsing**:
```python
import re

def extract_section(text: str, section_name: str) -> str:
    """Extract content under a markdown header."""
    pattern = rf"^### {section_name}.*?$\n(.*?)(?=^### |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None
```

**Advantages**:
- Flexible (Claude can add content before/after)
- Natural (matches how humans structure)
- Robust (works even if content varies)
- Reusable (one helper for all headers)

**Disadvantages**:
- Requires Claude to use consistent header names
- May miss content not under headers

### Strategy 2: Simple Delimiters

**Best for**: Extracting 2-3 specific pieces

**Prompt instruction**:
```
Separate your response into sections with clear labels.
```

**Parsing**:
```python
def extract_by_marker(text: str, marker: str) -> str:
    """Extract text after a marker."""
    pattern = rf"{marker}[:\s]+(.*?)(?=\n[A-Z]|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None
```

**Advantages**:
- Simple
- Works for unstructured text

**Disadvantages**:
- Brittle (if marker changes, parsing fails)
- Hard to scale to many sections

### Strategy 3: JSON (When Truly Needed)

**Best for**: Structured data that truly needs structure

**Prompt instruction**:
```
Return a JSON object with these fields: title, description, priority.
```

**Parsing**:
```python
import json

def extract_json(response_text: str) -> dict:
    """Extract JSON from response, handling markdown code blocks."""
    # Remove markdown code blocks if present
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    return json.loads(response_text.strip())
```

**Advantages**:
- Precise
- Easy to validate

**Disadvantages**:
- Brittle (parsing fails if Claude varies format)
- Slower (JSON encode/decode overhead)
- Less natural for text

---

## Testing Template

### Test File Structure

```python
# tests/test_[service]_simplification.py

import pytest
from backend.services.[service] import [function]

class TestSimplifiedPrompt:
    """Test the simplified prompt version."""

    TEST_CASES = [
        {
            "input": "...",
            "expected_fields": ["field1", "field2"],
            "description": "Basic case"
        },
        # ... more test cases
    ]

    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_parsing(self, test_case):
        """Test that output parses correctly."""
        response = test_case["input"]
        result = parse_response(response)

        for field in test_case["expected_fields"]:
            assert result[field] is not None, f"Missing field: {field}"

    def test_no_errors(self):
        """Test that parsing doesn't raise exceptions."""
        # Run 20 times with varied inputs
        for i in range(20):
            response = generate_test_response(i)
            try:
                parse_response(response)
            except Exception as e:
                pytest.fail(f"Parsing failed on test {i}: {e}")
```

### Validation Checklist

```
Before → After Comparison:

OLD PROMPT:
  - Lines: [count]
  - Tokens: [estimate]
  - Required markers: [count]
  - Format constraints: [list]

NEW PROMPT:
  - Lines: [count] (target: 50% reduction)
  - Tokens: [estimate] (target: 40-50% reduction)
  - Required markers: 0
  - Format constraints: 0

PARSING:
  - OLD: [lines] lines of code
  - NEW: [lines] lines of code (target: 50% reduction)
  - Test pass rate: 100% (0 failures)
  - Error types: None new

QUALITY:
  - Sample 1: [same/better/worse]
  - Sample 2: [same/better/worse]
  - Overall: [same/improved]
```

---

## Gotchas and Fallbacks

### Problem: Claude Ignores Format Request

**Symptom**: Claude responds but not with the requested format

**Solution**:
1. Be more explicit about structure: "Use headers like ### Dimension Name"
2. Add example: "For example: ### Strategic Impact\nScore: 4\nReason: ..."
3. Reference natural language: "Structure your response like a memo"

### Problem: Parsing Catches Some But Not All Cases

**Symptom**: 90% of outputs parse, but 10% fail

**Solution**:
1. Make helper functions more forgiving
2. Add fallback patterns
3. Log unparseable responses for manual review

```python
def extract_section_forgiving(text: str, section: str) -> Optional[str]:
    """Try multiple patterns to find section."""
    patterns = [
        rf"^### {section}",           # Markdown header
        rf"^## {section}",             # Level 2 header
        rf"^{section}:",               # Plain colon
        rf"^{section}",                # Just the word
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            # Extract text until next marker
            start = match.end()
            end = re.search(r"\n^[#*-]|\n^[A-Z][a-z]+:", text[start:], re.MULTILINE)
            if end:
                return text[start:start+end.start()].strip()
            return text[start:].strip()

    return None
```

### Problem: New Prompt Loses Information

**Symptom**: Quality goes down because Claude provides less detail

**Solution**:
1. Check if prompt actually asks for the detail
2. If so, add it explicitly: "Include specific examples"
3. Provide KB context if available
4. Consider using Sonnet instead of Haiku

---

## Implementation Priority

### HIGH (Do First)
1. **Career Status Report** (Issue #1)
   - Biggest improvement potential
   - Highest impact on quality
   - Clearest simplification

2. **Opportunity Justification** (Issue #2)
   - Quick win (1-2 hours)
   - Clear improvement
   - Good for building momentum

### MEDIUM (Do Next)
3. **Document Classifier** (Issue #3)
   - Good scaling benefit
   - Medium effort
   - Performance improvement

### LOW (Do If Time)
4. **Task Extractor** (Issue #4)
   - Already mostly good
   - Low ROI
   - Safe to leave

---

## Rollback Strategy

If something goes wrong after deploying:

1. **Revert prompt**: Switch back to original
2. **Keep parsing logic**: New parsing might be better anyway
3. **Investigate**: What went wrong?
4. **Add test case**: Ensure it doesn't happen again
5. **Try again**: Usually just needs fine-tuning

```python
# Easy rollback pattern
USE_SIMPLIFIED_PROMPT = os.getenv("USE_SIMPLIFIED_PROMPTS", "false").lower() == "true"

def build_career_prompt(context):
    if USE_SIMPLIFIED_PROMPT:
        return build_simplified_prompt(context)
    return build_original_prompt(context)
```

---

## Metrics to Track

After deployment, measure:

1. **Prompt efficiency**: Tokens per request (track reduction)
2. **Parsing reliability**: Errors per 1000 requests (should be 0)
3. **Quality**: User satisfaction scores (should stay same or improve)
4. **Latency**: Response time (should improve)
5. **Cost**: Token cost per request (should decrease)

---

End of Implementation Guide
