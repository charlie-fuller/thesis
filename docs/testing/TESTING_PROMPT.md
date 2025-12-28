# Thesis Platform - Comprehensive Testing, Review & Auto-Fix Prompt

**Version:** 2.1
**Last Updated:** 2025-12-27

---

## How to Use This Prompt

Copy the entire prompt below and paste it into a new Claude Code session to run a comprehensive code review, testing analysis, AND automated fixes of the Thesis platform.

---

## THE PROMPT

```
I need you to perform a comprehensive code review, testing analysis, AND automated fixing of the Thesis platform. This is a multi-agent GenAI strategy platform with a FastAPI backend, Next.js frontend, and PostgreSQL/Neo4j databases.

## Your Mission

You have TWO phases:

**PHASE A: ANALYZE** - Identify all issues
**PHASE B: FIX** - Automatically fix issues with high confidence

Target: Achieve a code quality score of 9/10 or higher before completing.

## Operating Principles

### Safety-First Fixing Rules

You MUST follow these rules when making fixes:

1. **NEVER remove or disable functionality** - Only improve code quality
2. **NEVER break API contracts** - Maintain all existing endpoints and response formats
3. **NEVER change database schema** - Only fix application code
4. **NEVER remove error handling** - Only improve it
5. **NEVER modify authentication/authorization logic** - Security-critical code requires manual review
6. **ALWAYS run tests after each batch of fixes** - Verify nothing broke
7. **ALWAYS preserve all imports, connections, and integrations**
8. **ALWAYS use git to track changes** - Commit after each successful fix batch

### High-Confidence Fixes (AUTO-FIX)

These issues can be fixed automatically:

| Issue Type | Fix Pattern | Confidence |
|------------|-------------|------------|
| Bare `except:` blocks | Add specific exception type | 95% |
| `datetime.utcnow()` | Replace with `datetime.now(timezone.utc)` | 99% |
| Pydantic `@validator` | Migrate to `@field_validator` | 90% |
| Print statements | Replace with `logger.info/warning/error` | 95% |
| Missing type hints | Add obvious return types | 85% |
| Trailing whitespace | Remove | 100% |
| Unused imports | Remove with verification | 80% |

### Medium-Confidence Fixes (FIX WITH VERIFICATION)

These require running tests after each fix:

| Issue Type | Approach |
|------------|----------|
| Large file refactoring | Extract one function/component at a time, test |
| Error message improvements | Update text only, preserve logic |
| Logging level adjustments | Change levels, verify behavior |

### Low-Confidence Fixes (REPORT ONLY)

These should be reported but NOT auto-fixed:

| Issue Type | Reason |
|------------|--------|
| Authentication changes | Security-critical |
| Database queries | Risk of data issues |
| API response format changes | Could break clients |
| Business logic modifications | Requires domain knowledge |
| Third-party integration code | External dependencies |

---

## PHASE A: Analysis

### Step 1: Environment Setup

```bash
cd /Users/motorthings/Documents/GitHub/thesis/backend
source venv/bin/activate
```

### Step 2: Run Baseline Tests

```bash
python -m pytest tests/ -v --tb=short 2>&1
```

**Record the baseline:**
- Number of tests passing
- Number of tests failing
- Any import errors

### Step 3: Code Quality Scan

Run these scans and record all findings:

```bash
# Bare except blocks
grep -rn "except:" . --include="*.py" | grep -v venv | grep -v ".pyc"

# Deprecated datetime
grep -rn "datetime.utcnow()" . --include="*.py" | grep -v venv

# Deprecated Pydantic validators
grep -rn "@validator\|@root_validator" . --include="*.py" | grep -v venv

# Print statements in production code
grep -rn "print(" . --include="*.py" | grep -v venv | grep -v test_ | grep -v scripts/

# TODO/FIXME comments
grep -rn "TODO\|FIXME\|XXX\|HACK" . --include="*.py" | grep -v venv

# Large files (>500 lines)
find . -name "*.py" -not -path "./venv/*" -exec wc -l {} \; | awk '$1 > 500' | sort -rn
```

### Step 4: Frontend Quality Scan

```bash
cd /Users/motorthings/Documents/GitHub/thesis/frontend

# TypeScript any types
grep -rn ": any" . --include="*.ts" --include="*.tsx" | grep -v node_modules | grep -v ".next"

# Console.log statements
grep -rn "console.log" . --include="*.ts" --include="*.tsx" | grep -v node_modules

# Large components
find ./components -name "*.tsx" -exec wc -l {} \; | awk '$1 > 400' | sort -rn
find ./app -name "*.tsx" -exec wc -l {} \; | awk '$1 > 500' | sort -rn
```

### Step 5: Calculate Initial Score

Use this scoring rubric:

| Category | Weight | Scoring |
|----------|--------|---------|
| Tests passing | 25% | 100% pass = 10, each failure -0.5 |
| Bare excepts | 15% | 0 = 10, each occurrence -2 |
| Deprecated patterns | 15% | 0 = 10, 1-5 = 8, 6-20 = 6, 20+ = 4 |
| Print statements | 10% | 0 = 10, 1-5 = 8, 6-15 = 6, 15+ = 4 |
| Large files | 10% | 0 over 800 = 10, each -1 |
| TODO comments | 10% | 0 = 10, 1-3 = 8, 4-10 = 6, 10+ = 4 |
| Security issues | 15% | 0 = 10, any critical = 0 |

**Target Score: 9.0 or higher**

---

## PHASE B: Automated Fixes

### Fix Batch 1: Bare Except Blocks (High Confidence)

For each bare `except:` found:

1. Read the surrounding code context (10 lines before/after)
2. Identify what exceptions could realistically occur
3. Replace with specific exception type

**Common patterns:**

```python
# Pattern: Version parsing
# Before:
except:
    new_version = "1.1"
# After:
except (ValueError, IndexError):
    new_version = "1.1"

# Pattern: Storage/IO operations
# Before:
except:
    pass  # Ignore errors
# After:
except Exception as e:
    logger.warning(f"Operation failed: {e}")

# Pattern: JSON parsing
# Before:
except:
    return {}
# After:
except (json.JSONDecodeError, KeyError, TypeError) as e:
    logger.warning(f"Parse error: {e}")
    return {}
```

**After fixing, run tests:**
```bash
python -m pytest tests/ -v --tb=short
```

If tests fail, revert the change and report it as needing manual review.

### Fix Batch 2: Deprecated datetime.utcnow() (High Confidence)

Add the import at the top of each affected file:
```python
from datetime import datetime, timezone
```

Then replace all occurrences:
```python
# Before:
datetime.utcnow()

# After:
datetime.now(timezone.utc)
```

**Run tests after this batch.**

### Fix Batch 3: Print Statements to Logging (High Confidence)

For each print statement in production code (not tests/scripts):

1. Check if `logger` is already defined in the file
2. If not, add at top: `logger = logging.getLogger(__name__)`
3. Replace print with appropriate log level:

```python
# Informational prints
print(f"Processing {item}")  →  logger.info(f"Processing {item}")

# Warning prints
print("⚠️ Something unexpected")  →  logger.warning("Something unexpected")

# Error prints
print(f"Error: {e}")  →  logger.error(f"Error: {e}")

# Debug prints
print(f"Debug: {var}")  →  logger.debug(f"Debug: {var}")
```

**Run tests after this batch.**

### Fix Batch 4: Pydantic Validator Migration (Medium Confidence)

For each `@validator` decorator:

```python
# Before:
from pydantic import validator

class MyModel(BaseModel):
    title: str

    @validator('title')
    def validate_title(cls, v):
        return v.strip() if v else v

# After:
from pydantic import field_validator

class MyModel(BaseModel):
    title: str

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        return v.strip() if v else v
```

**Run tests after EACH file change in this batch.**

### Fix Batch 5: FastAPI on_event Migration (Medium Confidence)

If `@app.on_event("startup")` or `@app.on_event("shutdown")` found in main.py:

```python
# Before:
@app.on_event("startup")
async def startup():
    # startup code

@app.on_event("shutdown")
async def shutdown():
    # shutdown code

# After:
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code
    yield
    # shutdown code

app = FastAPI(lifespan=lifespan, ...)
```

**Run full test suite after this change.**

---

## PHASE C: Verification Cycle

After completing all fix batches:

### Step 1: Run Full Test Suite
```bash
cd /Users/motorthings/Documents/GitHub/thesis/backend
source venv/bin/activate
python -m pytest tests/ -v --tb=short
```

**All tests must pass. If any fail, investigate and fix or revert.**

### Step 2: Re-run Quality Scans
```bash
# Bare excepts (should be 0)
grep -rn "except:" . --include="*.py" | grep -v venv | grep -v ".pyc" | wc -l

# Deprecated datetime (should be 0 or only in tests)
grep -rn "datetime.utcnow()" . --include="*.py" | grep -v venv | grep -v test_ | wc -l

# Print statements (should be 0 in production code)
grep -rn "print(" . --include="*.py" | grep -v venv | grep -v test_ | grep -v scripts/ | wc -l
```

### Step 3: Recalculate Score

Using the same rubric from Phase A, calculate the new score.

### Step 4: Iterate if Needed

If score < 9.0:
1. Identify remaining high-confidence fixes
2. Apply them one at a time
3. Test after each
4. Recalculate score
5. Repeat until score >= 9.0 or no more high-confidence fixes remain

---

## PHASE D: Commit Changes

Once score >= 9.0 and all tests pass:

```bash
cd /Users/motorthings/Documents/GitHub/thesis

# Check what changed
git status
git diff --stat

# Stage and commit
git add -A
git commit -m "fix: automated code quality improvements

- Replace bare except blocks with specific exception types
- Migrate datetime.utcnow() to timezone-aware datetime.now(timezone.utc)
- Replace print statements with proper logging
- Migrate Pydantic validators to V2 field_validator pattern

Code quality score: [BEFORE] → [AFTER]
All tests passing: [COUNT]

🤖 Generated with Claude Code
"
```

---

## PHASE E: Generate Report

Save the final report to a markdown file in the docs/testing directory with today's date:

**Filename format:** `docs/testing/CODE_REVIEW_YYYY-MM-DD.md`

Example: `docs/testing/CODE_REVIEW_2025-12-27.md`

The report file should contain:
1. The complete Pre-Fix Assessment
2. All Fixes Applied (table format)
3. Post-Fix Assessment with final score
4. Issues Requiring Manual Review
5. Safety Checklist results
6. Git commit hash for the changes

This creates a permanent record of each code review session for tracking quality improvements over time.

---

## Output Format

Provide a structured report:

### Pre-Fix Assessment
```
Initial Code Quality Score: X.X/10

Issues Found:
- Bare except blocks: N
- Deprecated datetime: N
- Print statements: N
- Pydantic v1 validators: N
- Large files (>500 lines): N
- TODO comments: N

Test Baseline:
- Passing: N
- Failing: N
- Errors: N
```

### Fixes Applied
```
| File | Issue | Fix Applied | Tests After |
|------|-------|-------------|-------------|
| path/file.py:123 | bare except | Added ValueError | ✅ Pass |
| path/file.py:456 | utcnow() | timezone.utc | ✅ Pass |
```

### Post-Fix Assessment
```
Final Code Quality Score: X.X/10

Remaining Issues:
- [List any issues that couldn't be auto-fixed]

Test Results:
- Passing: N
- Failing: N
- Errors: N

Changes Summary:
- Files modified: N
- Lines changed: +N / -N
```

### Issues Requiring Manual Review
```
| File | Issue | Reason Cannot Auto-Fix |
|------|-------|----------------------|
| path/file.py | Complex refactor | Requires architectural decision |
```

---

## Safety Checklist

Before completing, verify:

- [ ] All tests pass (same or more than baseline)
- [ ] No functionality was removed
- [ ] No API endpoints were changed
- [ ] No database operations were modified
- [ ] No authentication code was changed
- [ ] Application still starts without errors
- [ ] No new import errors introduced

---

## Rollback Procedure

If something goes wrong:

```bash
# See what changed
git diff

# Revert all changes
git checkout -- .

# Or revert specific file
git checkout -- path/to/file.py
```

---

## Remember

- **Safety first**: Better to leave an issue unfixed than break functionality
- **Test constantly**: Run tests after every batch of changes
- **Be conservative**: When in doubt, report rather than fix
- **Preserve intent**: Don't change what the code does, only how it's written
- **Document everything**: Clear commit messages and reports
- **Iterate**: Keep improving until you hit the target score
```

---

## Quick Reference: Safe Fix Patterns

### Bare Except → Specific Exception
```python
# IO/File operations
except: → except (IOError, OSError) as e:

# JSON parsing
except: → except (json.JSONDecodeError, KeyError, TypeError) as e:

# String/Number parsing
except: → except (ValueError, IndexError) as e:

# Generic with logging
except: → except Exception as e:
    logger.exception("Unexpected error")
```

### datetime.utcnow() → timezone-aware
```python
# Add import
from datetime import datetime, timezone

# Replace
datetime.utcnow() → datetime.now(timezone.utc)
datetime.utcnow().isoformat() → datetime.now(timezone.utc).isoformat()
```

### print() → logging
```python
# Add if not present
import logging
logger = logging.getLogger(__name__)

# Replace based on context
print(f"Info: {x}") → logger.info(f"Info: {x}")
print(f"Warning: {x}") → logger.warning(f"Warning: {x}")
print(f"Error: {x}") → logger.error(f"Error: {x}")
print(f"Debug: {x}") → logger.debug(f"Debug: {x}")
```

### Pydantic @validator → @field_validator
```python
# Change import
from pydantic import validator → from pydantic import field_validator

# Update decorator and add @classmethod
@validator('field')
def validate(cls, v):
→
@field_validator('field')
@classmethod
def validate(cls, v):
```

---

## Metrics Targets

| Metric | Starting | Target | Ideal |
|--------|----------|--------|-------|
| Code Quality Score | 7.0 | 9.0 | 9.5+ |
| Bare except blocks | 2 | 0 | 0 |
| Deprecated patterns | 60+ | 0 | 0 |
| Print statements | 25+ | 0 | 0 |
| Test pass rate | 100% | 100% | 100% |
| Test count | 55 | 75+ | 150+ |

---

## Changelog

- **2025-12-27 v2.1**: Added Phase E for generating dated report files in docs/testing/
- **2025-12-27 v2.0**: Added automated fix capabilities, safety checks, iterative improvement cycle
- **2025-12-27 v1.0**: Initial version (analysis only)
