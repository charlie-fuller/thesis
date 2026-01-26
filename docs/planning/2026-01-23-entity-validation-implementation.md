# Entity Validation System - Implementation Plan

**Created:** 2026-01-23
**Status:** In Progress
**Scope:** PuRDy Discovery Process (not Thesis core)

## Problem
Transcription services (Granola, Otter, Zoom) make errors in names and company names. These errors propagate through the extraction pipeline and get stored permanently. Examples:
- "Charlie" → "Charley"
- "Contentful" → "Content Full"
- "Sarah Chen" → "Sara Chen"

## Solution Overview
Add a validation layer that compares extracted entities against ground truth registries, suggests corrections, and learns from user feedback.

## Architecture

```
Document → Extractor (Claude) → Entity Validator → Candidates → User Review
                                      ↓                            ↓
                              Registries (names,          Correction Learning
                              organizations)                   ↓
                                      ↑___________________________|
```

---

## Database Changes

### Migration: `039_entity_validation.sql`

**New Tables:**
1. `organization_registry` - Ground truth for company names with aliases
2. `person_name_registry` - Known names with phonetic codes and aliases
3. `entity_corrections` - User correction history for learning
4. `entity_validation_results` - Validation audit trail

**Extend `stakeholder_candidates`:**
- `name_validation_status` (validated/suggested_correction/new/potential_error)
- `name_suggested_correction`
- `name_validation_confidence` (0-1)
- `org_validation_status`
- `org_suggested_correction`
- `org_validation_confidence`

---

## Backend Services

### 1. `/backend/services/entity_validator.py` (NEW)
Core validation logic:
- Exact match against registry canonical names
- Alias match (known variations/misspellings)
- Fuzzy match (Levenshtein/Jaro-Winkler, threshold 0.85)
- Phonetic match (Double Metaphone for names)
- Optional LLM assist for uncertain cases (confidence < 0.7)

```python
@dataclass
class ValidationResult:
    original_value: str
    status: str  # exact_match, alias_match, fuzzy_match, new_entity, potential_error
    suggested_value: Optional[str]
    confidence: float
    match_reason: str

class EntityValidator:
    async def validate_person_name(name, client_id, context) -> ValidationResult
    async def validate_organization(org_name, client_id) -> ValidationResult
```

### 2. `/backend/services/entity_registry_manager.py` (NEW)
Registry CRUD and learning:
- `bootstrap_from_stakeholders()` - Populate from existing data
- `add_organization()` / `add_person()` - Manual registry entries
- `learn_from_correction()` - Add original as alias when user corrects

### 3. `/backend/services/phonetic_matcher.py` (NEW)
Name comparison using Double Metaphone:
- Particularly effective for transcription errors ("Charley" sounds like "Charlie")
- Store metaphone codes in registry for fast lookup

### 4. Modify `/backend/services/stakeholder_extractor.py`
Add optional `entity_validator` and `client_id` parameters:
- After LLM extraction, validate each name/organization
- Attach `ValidationResult` to `ExtractedStakeholder`

### 5. Modify `/backend/services/stakeholder_scanner.py`
Store validation results in candidate records.

### 6. Modify `/backend/services/granola_scanner.py`
Validate extracted stakeholders before creating candidates.

---

## API Endpoints

### `/backend/api/routes/entity_registry.py` (NEW)
```
GET  /api/entity-registry/organizations     # List orgs
POST /api/entity-registry/organizations     # Add org
PUT  /api/entity-registry/organizations/:id # Update (add aliases)
GET  /api/entity-registry/persons           # List names
POST /api/entity-registry/bootstrap         # Bootstrap from existing data
```

### `/backend/api/routes/entity_corrections.py` (NEW)
```
POST /api/entity-corrections                # Record correction
GET  /api/entity-corrections/history        # View history
POST /api/entity-corrections/batch-apply    # Apply to historical data
```

### Modify `/api/stakeholders/candidates/:id/accept`
- Accept `apply_name_suggestion`, `apply_org_suggestion` flags
- When user accepts suggestion or provides custom correction, call `learn_from_correction()`

---

## Frontend Changes

### 1. `/frontend/components/validation/ValidationIndicator.tsx` (NEW)
Visual status indicator:
- Green checkmark: Validated against registry
- Amber warning: Suggested correction available
- Blue badge: New entity (not in registry)
- Red warning: Potential transcription error

### 2. Modify `/frontend/components/stakeholders/StakeholderCandidateCard.tsx`
Add correction UI when validation suggests a fix:

```tsx
{candidate.name_suggested_correction && (
  <div className="bg-amber-50 border border-amber-200 rounded p-3">
    <span>Did you mean: <strong>{candidate.name_suggested_correction}</strong>?</span>
    <span className="text-muted">({Math.round(confidence * 100)}% match)</span>
    <button onClick={() => acceptWithCorrection('name')}>Use suggestion</button>
    <button onClick={() => acceptOriginal()}>Keep original</button>
  </div>
)}
```

### 3. Modify `/frontend/components/discovery/UnifiedDiscoveryPanel.tsx`
Show validation warnings inline in carousel view.

### 4. `/frontend/app/admin/entity-registry/page.tsx` (NEW - Optional)
Admin page for managing registries:
- View/edit organizations and person names
- Add aliases manually
- View correction history
- Bootstrap button

---

## Critical Files to Modify

| File | Change |
|------|--------|
| `/backend/services/stakeholder_extractor.py` | Add validator integration |
| `/backend/services/stakeholder_scanner.py` | Store validation results |
| `/backend/services/granola_scanner.py` | Validate before creating candidates |
| `/backend/api/routes/stakeholders.py` | Handle correction learning on accept |
| `/frontend/components/stakeholders/StakeholderCandidateCard.tsx` | Add correction UI |
| `/database/migrations/` | Add `039_entity_validation.sql` |

---

## Implementation Sequence

1. **Database migration** - Create registry tables and extend candidates
2. **PhoneticMatcher service** - Double Metaphone implementation
3. **EntityValidator service** - Core validation logic
4. **RegistryManager service** - Bootstrap and CRUD
5. **Integrate into extractors** - StakeholderExtractor, GranolaScanner
6. **API endpoints** - Registry management, corrections
7. **Frontend** - ValidationIndicator, update CandidateCard
8. **Bootstrap existing data** - Run bootstrap script
9. **Admin page** (optional) - Registry management UI

---

## Verification

### Unit Tests
```bash
# From the repo root:
cd backend
uv run pytest tests/test_entity_validator.py -v
```

### Integration Test
1. Add known stakeholder "Charlie Fuller" to registry
2. Create test document with "Charley Fuller"
3. Run Granola scanner
4. Verify candidate shows suggested correction "Charlie Fuller"
5. Accept with suggestion
6. Verify correction recorded in `entity_corrections`
7. Verify "Charley" added as alias to "Charlie Fuller" in registry

### Manual Test
1. Bootstrap registries: `POST /api/entity-registry/bootstrap`
2. Upload meeting transcript with misspelled name
3. Check Discovery Inbox - should show amber warning with suggestion
4. Accept suggestion and verify learning

---

## Dependencies
- `metaphone` Python package for Double Metaphone (install via `uv add metaphone`)
- No new frontend dependencies

---

## Future Enhancements (Out of Scope)
- ML model trained on correction history
- Cross-client shared knowledge (common company names)
- Real-time validation as user types
- Bulk correction UI for historical cleanup
