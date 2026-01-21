# Prompt Audit Quick Reference Checklist

## Issues Found (6 Total)

### Issue #1: Career Status Report ⚠️ HIGH
- **File**: `/backend/services/career_status_report.py` (lines 272-318)
- **Problem**: Over-specified output format with exact markers
- **Symptom**: 8 required markers, 103 lines of parsing code
- **Fix Effort**: 2 hours
- **Impact**: -50% prompt tokens, +parsing reliability
- **Recommendation**: DO THIS FIRST

### Issue #2: Opportunity Justification ⚠️ MEDIUM-HIGH
- **File**: `/backend/services/opportunity_justification.py` (lines 68-85)
- **Problem**: Rigid JSON schema with 5 fields
- **Symptom**: Overly prescriptive "exactly 3-4 sentences" constraints
- **Fix Effort**: 1 hour
- **Impact**: -40% prompt tokens, simpler parsing
- **Recommendation**: DO THIS SECOND

### Issue #3: Document Classifier 🔸 MEDIUM
- **File**: `/backend/services/document_classifier.py` (lines 307-339)
- **Problem**: Over-complex LLM fallback with full agent list
- **Symptom**: Markdown code block handling suggests brittleness
- **Fix Effort**: 2-3 hours
- **Impact**: -50% prompt tokens, faster Haiku inference
- **Recommendation**: DO THIS THIRD

### Issue #4: Task Extractor 🟢 LOW-MEDIUM
- **File**: `/backend/services/task_extractor.py` (lines 222-253)
- **Problem**: Minor over-specification of JSON fields
- **Symptom**: Already mostly fixed (commit beba18da), minor refinements possible
- **Fix Effort**: 1-2 hours
- **Impact**: +20% prompt tokens at most
- **Recommendation**: OPTIONAL - low priority, already good

### Issue #5: Oracle Agent XML 🟢 LOW
- **File**: `/backend/system_instructions/agents/oracle.xml` (lines 202-242)
- **Problem**: Over-detailed 10-section output format
- **Symptom**: Rigid structure that doesn't fit all meetings
- **Fix Effort**: 1 hour (documentation mostly)
- **Impact**: Flexibility improvement, no token savings
- **Recommendation**: LOW PRIORITY - user-facing, document only

### Issue #6: Smart Brevity Overlap 🟢 VERY LOW
- **File**: `/backend/system_instructions/agents/oracle.xml` (line 22)
- **Problem**: Potential conflict between Smart Brevity (100-150 words) and 10-section format
- **Symptom**: Documentation issue, no functional bug
- **Fix Effort**: 0.5 hours
- **Impact**: Clarity only
- **Recommendation**: SKIP - very low value

---

## By Priority

### 🚀 Immediate (This Sprint)

```
1. Career Status Report Fix
   [ ] Read current code (5 min)
   [ ] Create test file with 10-20 samples (30 min)
   [ ] Write simplified prompt (20 min)
   [ ] Write markdown parsing helpers (30 min)
   [ ] Test new version (30 min)
   [ ] Compare quality (30 min)
   [ ] Commit and document (20 min)
   Total: ~2.5 hours

2. Opportunity Justification Fix
   [ ] Read current code (5 min)
   [ ] Create test file (20 min)
   [ ] Write simplified prompt (15 min)
   [ ] Simplify parsing (15 min)
   [ ] Test (20 min)
   [ ] Commit (10 min)
   Total: ~1.5 hours
```

### 📋 Short Term (Next 1-2 Sprints)

```
3. Document Classifier Fix
   [ ] Measure current Haiku token usage (30 min)
   [ ] Create test set (30 min)
   [ ] Simplify prompt (30 min)
   [ ] Rewrite parsing (45 min)
   [ ] Test thoroughly (45 min)
   [ ] Stage and validate (30 min)
   Total: ~3 hours
```

### 📌 Optional

```
4. Task Extractor refinement
5. Oracle format flexibility review
6. Smart Brevity documentation
```

---

## Testing Checklist (For Each Fix)

```
Before Implementation:
[ ] Run current system on 20 diverse test cases
[ ] Save outputs for comparison
[ ] Note any errors or edge cases

After Implementation:
[ ] Run simplified version on same 20 test cases
[ ] Compare outputs (same/better/worse for each)
[ ] Check for parsing errors (should be 0)
[ ] Verify token reduction (target: 40-50%)
[ ] Spot check output quality (natural? useful? complete?)

Before Commit:
[ ] All tests pass (100% pass rate)
[ ] No new failure modes
[ ] Document changes in commit message
[ ] Add reference to audit findings
```

---

## Prompts to Avoid

These patterns indicate over-engineering:

```python
# 🚫 BAD - Over-specified
prompt = """
Format your response EXACTLY as:
FIELD_NAME: [content]
ANOTHER_FIELD: [content]
...
"""

# ✅ GOOD - Natural
prompt = """
Use headers to organize your response.
Include: title, description, priority.
"""

# 🚫 BAD - Excessive constraints
prompt = """
Maximum exactly 3-4 sentences per section.
Must include all 5 required fields.
Do NOT use markdown.
"""

# ✅ GOOD - Light guidance
prompt = """
Be concise (2-3 sentences per section).
Include all key information.
Structure for readability.
"""

# 🚫 BAD - Complex JSON schema
prompt = """
Return JSON with this structure:
{
  "field1": "...",
  "field2": "...",
  ...
}
"""

# ✅ GOOD - Natural structure
prompt = """
Provide these details: title, owner, priority.
Structure clearly so they're easy to find.
"""
```

---

## Helper Functions to Reuse

Once created for Career Status Report, these can be used in other services:

```python
# In services/prompt_parsing.py (new file)

def extract_section(text: str, headers: list[str], lines: int = None) -> str:
    """Extract content under a markdown header."""
    # Used by: Career Status, Oracle analysis, etc.

def extract_score(text: str, dimension: str) -> int:
    """Extract numeric score from text."""
    # Used by: Career Status, Opportunities, etc.

def extract_list(text: str, headers: list[str]) -> list[str]:
    """Extract bulleted list."""
    # Used by: Career Status, Recommendations, etc.

def extract_by_marker(text: str, marker: str) -> str:
    """Extract text after a simple marker."""
    # Used by: Fallback for unstructured text

def cleanup_json_response(response_text: str) -> dict:
    """Handle markdown code blocks in JSON responses."""
    # Used by: Opportunity Justification, Task Extractor, etc.
```

---

## Success Metrics

After all fixes:

| Metric | Current | Target |
|--------|---------|--------|
| Career Report prompt tokens | ~300 | ~150 (-50%) |
| Career Report parsing code | 103 lines | 50 lines (-50%) |
| Opp. Justification prompt tokens | ~150 | ~90 (-40%) |
| Opp. Justification parsing code | 38 lines | 5 lines (-87%) |
| Doc Classifier prompt tokens | ~200 | ~100 (-50%) |
| Parse failure rate (all services) | <1% | 0% |
| User satisfaction | TBD | Same or +5% |

---

## Rollback Plan

If deployment causes issues:

1. **Immediate**: Revert to original prompts via feature flag
   ```
   export USE_SIMPLIFIED_PROMPTS=false
   ```

2. **Investigation**: Check error logs
   ```
   grep "parsing\|error\|failed" logs/
   ```

3. **Quick Fix**: Add test case for the failure
   ```
   # Add to test suite
   # Re-deploy with hotfix
   ```

4. **Communication**: Update team on status
   ```
   # Post to #engineering
   "Rolled back Career Report to original prompt.
    Investigating parsing edge case. ETA: 2 hours"
   ```

---

## Files to Modify

### Core Changes
- `backend/services/career_status_report.py` - Lines 272-318 (prompt), 321-424 (parsing)
- `backend/services/opportunity_justification.py` - Lines 47-85 (prompt), 88-122 (parsing)
- `backend/services/document_classifier.py` - Lines 307-339 (prompt)
- `backend/services/task_extractor.py` - Lines 222-253 (prompt) [OPTIONAL]

### Supporting Files
- `backend/services/prompt_parsing.py` - CREATE (new helper functions)
- `backend/tests/test_prompt_simplification.py` - CREATE (test suite)
- `docs/prompts/SIMPLIFICATION_IMPLEMENTATION_GUIDE.md` - REFERENCE

---

## Commit Message Template

```
refactor: simplify [service] prompts per audit findings

- Reduced prompt complexity from XXXX tokens to XXXX tokens (-XX%)
- Simplified parsing from XXX lines to XXX lines
- Removed X over-specified format constraints
- Added markdown header-based parsing (more robust)
- All tests pass with same/better output quality

Closes audit issue #X
Reference: docs/prompts/AGENT_PROMPT_AUDIT_FINDINGS.md
```

---

## Contact Points for Questions

If you need to:
- **Understand the findings**: See `AGENT_PROMPT_AUDIT_FINDINGS.md`
- **Learn implementation steps**: See `SIMPLIFICATION_IMPLEMENTATION_GUIDE.md`
- **Copy helper functions**: Look for `prompt_parsing.py`
- **See examples**: Check worked example in Implementation Guide
- **Reference patterns**: Return to this Quick Reference

---

## One-Minute Summary

**What**: 6 LLM prompts are over-engineered with unnecessary format constraints

**Where**: Career reports, Opportunity justification, Document classifier, Task extractor, Oracle agent

**Why**: Adds complexity, increases errors, wastes tokens

**Fix**: Simplify prompts, use markdown headers, reduce parsing code

**Impact**: -50% prompt tokens, better reliability, less maintenance

**Priority**: Do Issues #1 and #2 first (~3.5 hours), then #3 (~3 hours)

**Bottom Line**: Follow the examples in the Implementation Guide, test thoroughly, keep quality the same or better, commit with reference to audit findings.

---

**Status**: Ready to implement
**Estimated Total Effort**: 8-10 hours for all fixes
**Expected Benefit**: 40-50% reduction in prompt tokens, improved parsing reliability
