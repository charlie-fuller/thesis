# ADDIE Workflow-Aware Quick Prompts - Implementation Guide

## Overview

This implementation adds L&D workflow-aware quick prompts to Thesis, organized by the ADDIE model phases (Analysis, Design, Development, Implementation, Evaluation). The system provides contextual prompt suggestions based on conversation content and uploaded documents.

## Features Implemented

### 1. ADDIE Phase Categorization
- Prompts organized into 5 ADDIE phases + General category
- Each phase has a unique icon, color scheme, and description
- Collapsible phase sections for better organization
- 3-5 prompts per phase (configurable)

### 2. Context-Aware Suggestions
- Automatic phase detection based on conversation keywords
- Relevance scoring using contextual keyword matching
- Auto-expansion of detected phase section
- "Contextual" view mode showing most relevant prompts

### 3. Document-Aware Prompts
- Special prompt suggestions when documents are uploaded
- Document count indicator
- Quick access to document analysis prompts

### 4. Slash Commands Integration
- `/image` - Generate visuals
- `/help` - Get help
- Prominently surfaced in "General" category

## Files Modified/Created

### Backend Files

#### Created:
- `/backend/migrations/026_add_addie_categories.sql` - Database schema migration
- `/backend/seed_addie_prompts.py` - Script to populate ADDIE prompts for users

#### Modified:
- `/backend/services/quick_prompt_generator.py`
  - Added `ADDIE_PROMPT_LIBRARY` with 28 L&D-specific prompts
  - Added `generate_addie_prompts()` function
  - Added `get_contextual_prompts()` function
  - Added `get_prompts_by_phase()` function
  - Added `detect_addie_phase_from_conversation()` function

- `/backend/api/routes/quick_prompts.py`
  - Added `addie_phase` query parameter to GET endpoint
  - Added POST `/generate-addie` endpoint
  - Added POST `/contextual` endpoint
  - Added POST `/detect-phase` endpoint

### Frontend Files

#### Created:
- `/frontend/components/PromptCategory.tsx` - Component for ADDIE phase sections

#### Modified:
- `/frontend/components/QuickPromptsBar.tsx`
  - Added ADDIE phase grouping
  - Added contextual prompt fetching
  - Added phase detection
  - Added view mode toggle (All Phases / Contextual)
  - Added document upload awareness
  - Added expandable/collapsible phase sections

## Database Schema Changes

### New Columns in `user_quick_prompts` table:

```sql
-- ADDIE phase (Analysis, Design, Development, Implementation, Evaluation, General)
addie_phase VARCHAR(50)

-- Category label (e.g., "Needs Analysis", "Learning Objectives")
category VARCHAR(100)

-- Array of keywords for context detection
contextual_keywords TEXT[]
```

### Indexes Added:
- `idx_quick_prompts_addie_phase` - For efficient phase filtering
- `idx_quick_prompts_category` - For category queries

## ADDIE Prompt Library

### Analysis Phase (5 prompts)
1. What skills gap exists in this situation?
2. What's the business problem we're trying to solve?
3. Who is the target audience for this learning?
4. What are the current knowledge and skill levels?
5. What constraints or resources do we have?

### Design Phase (5 prompts)
1. Create learning objectives for this topic
2. Design an assessment strategy
3. Map learning outcomes to business goals
4. What instructional strategies should we use?
5. Design the course structure and flow

### Development Phase (5 prompts)
1. Write a detailed course outline
2. Create content modules for this topic
3. Design visuals and multimedia elements
4. Write practice activities and exercises
5. Develop assessment questions and rubrics

### Implementation Phase (5 prompts)
1. Create a facilitator guide
2. Design the delivery schedule and timeline
3. Plan the rollout strategy
4. Prepare participant materials and resources
5. Set up the learning environment and technology

### Evaluation Phase (5 prompts)
1. Design evaluation metrics and KPIs
2. Create feedback surveys and forms
3. Measure learning outcomes and ROI
4. Analyze completion and engagement data
5. Plan for continuous improvement

### General (3 prompts)
1. /image - Generate a visual for this concept
2. /help - Get help with Thesis's features
3. Summarize this document for learning design

## API Endpoints

### GET `/api/quick-prompts`
Fetch quick prompts with optional ADDIE phase filtering.

**Query Parameters:**
- `active_only` (boolean) - Only return active prompts (default: true)
- `addie_phase` (string) - Filter by phase (Analysis, Design, Development, Implementation, Evaluation, General)

**Response:**
```json
{
  "success": true,
  "count": 15,
  "prompts": [
    {
      "id": "uuid",
      "prompt_text": "What skills gap exists in this situation?",
      "addie_phase": "Analysis",
      "category": "Needs Analysis",
      "contextual_keywords": ["gap", "need", "problem"],
      "usage_count": 5,
      "active": true
    }
  ]
}
```

### POST `/api/quick-prompts/generate-addie`
Generate ADDIE-based prompts for the current user.

**Request:**
```json
{
  "phases": ["Analysis", "Design", "Development"],  // Optional, defaults to all
  "max_per_phase": 3  // Max prompts per phase (1-10)
}
```

### POST `/api/quick-prompts/contextual`
Get contextually relevant prompts based on conversation.

**Request:**
```json
{
  "conversation_text": "We need to identify the skills gap...",
  "addie_phase": "Analysis",  // Optional filter
  "limit": 5  // Max prompts to return
}
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "prompts": [
    {
      "id": "uuid",
      "prompt_text": "What skills gap exists?",
      "relevance_score": 3,  // Number of keyword matches
      "addie_phase": "Analysis",
      "category": "Needs Analysis"
    }
  ]
}
```

### POST `/api/quick-prompts/detect-phase`
Detect ADDIE phase from conversation text.

**Request:**
```json
{
  "conversation_text": "We need to create learning objectives and design assessments..."
}
```

**Response:**
```json
{
  "success": true,
  "detected_phase": "Design"
}
```

## Deployment Steps

### 1. Run Database Migration

```bash
cd /Users/motorthings/Documents/GitHub/thesis/backend
python apply_migration.py migrations/026_add_addie_categories.sql
```

### 2. Seed ADDIE Prompts for Existing Users

```bash
# Seed for all users
python seed_addie_prompts.py

# Or seed for specific user
python seed_addie_prompts.py <user_id>
```

### 3. Deploy Backend Changes

The backend changes are backward compatible - existing prompts will continue to work.

### 4. Deploy Frontend Changes

The frontend gracefully handles both legacy prompts (without ADDIE phase) and new ADDIE-categorized prompts.

## Usage Examples

### For New Users
When new users complete onboarding, call the ADDIE generation endpoint:

```typescript
await apiPost('/api/quick-prompts/generate-addie', {
  phases: null,  // All phases
  max_per_phase: 3
});
```

### For Existing Users
Run the seed script or manually trigger generation via the API.

### Contextual Prompts in Chat
The QuickPromptsBar component automatically:
1. Detects conversation context every 50+ characters
2. Fetches relevant prompts based on keywords
3. Highlights detected ADDIE phase
4. Shows contextual prompts in separate view

### Document Upload Integration
When users upload documents, QuickPromptsBar shows:
```
Analyze uploaded document for L&D (1 file)
```

Clicking this sends: `"Summarize this document for learning design"`

## Component Props

### QuickPromptsBar

```typescript
interface QuickPromptsBarProps {
  onPromptClick: (promptText: string) => void;
  conversationText?: string;  // Recent conversation for context
  uploadedDocuments?: number; // Count of uploaded docs
}
```

### PromptCategory

```typescript
interface PromptCategoryProps {
  phase: string;  // ADDIE phase name
  prompts: QuickPrompt[];
  onPromptClick: (promptText: string) => void;
  isActive?: boolean;  // Highlight if detected
  onToggleExpanded?: () => void;
  isExpanded?: boolean;
}
```

## Phase Detection Algorithm

The system uses keyword matching to detect ADDIE phases:

- **Analysis**: gap, need, problem, challenge, audience, learner, baseline, skills
- **Design**: objective, outcome, goal, assessment, strategy, structure, align
- **Development**: content, module, material, create, write, develop, activity
- **Implementation**: deliver, rollout, launch, facilitator, schedule, deployment, LMS
- **Evaluation**: measure, metric, KPI, feedback, survey, ROI, impact, analytics

Each keyword match adds 1 to the phase score. The phase with the highest score is selected.

## Styling & Design

### Phase Colors
- **Analysis**: Blue (`text-blue-700`, `bg-blue-50`)
- **Design**: Purple (`text-purple-700`, `bg-purple-50`)
- **Development**: Green (`text-green-700`, `bg-green-50`)
- **Implementation**: Orange (`text-orange-700`, `bg-orange-50`)
- **Evaluation**: Pink (`text-pink-700`, `bg-pink-50`)
- **General**: Gray (`text-gray-700`, `bg-gray-50`)

### Icons (in UI)
- Analysis: Search icon
- Design: Ruler icon
- Development: Tools icon
- Implementation: Rocket icon
- Evaluation: Chart icon
- General: Lightning icon

## Testing

### Backend Tests

```bash
# Test prompt generation
curl -X POST http://localhost:8000/api/quick-prompts/generate-addie \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"max_per_phase": 3}'

# Test contextual prompts
curl -X POST http://localhost:8000/api/quick-prompts/contextual \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"conversation_text": "We need to identify skills gaps", "limit": 5}'

# Test phase detection
curl -X POST http://localhost:8000/api/quick-prompts/detect-phase \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"conversation_text": "Create learning objectives and design assessments"}'
```

### Frontend Tests

1. Load chat interface
2. Start conversation with L&D terms (e.g., "learning objectives")
3. Verify phase detection and highlighting
4. Upload a document
5. Verify document prompt appears
6. Click contextual view
7. Verify relevant prompts show with scores

## Troubleshooting

### Prompts Not Showing
- Check user has prompts in database: `SELECT * FROM user_quick_prompts WHERE user_id = '<id>'`
- Run seed script: `python seed_addie_prompts.py <user_id>`

### Phase Detection Not Working
- Ensure conversation text is > 50 characters
- Check network tab for API calls to `/detect-phase`
- Verify keywords in conversation match phase definitions

### TypeScript Errors
- Run `npx tsc --noEmit` to check for type errors
- Existing errors in ChatInterface.tsx are unrelated to this implementation

## Future Enhancements

1. **Machine Learning Phase Detection** - Use Claude API to detect phases more intelligently
2. **Custom Prompt Builder** - UI for users to create custom ADDIE prompts
3. **Prompt Analytics** - Track which prompts are most effective
4. **Team Sharing** - Share prompts across team members
5. **Smart Ordering** - Reorder prompts based on usage frequency
6. **Multi-language Support** - Translate prompts to other languages
7. **Integration with LMS** - Sync prompts with external LMS systems

## Support

For questions or issues:
- Check logs: `backend/backend.log`
- Review API responses in browser DevTools
- Contact development team

---

**Last Updated:** December 18, 2025
**Version:** 1.0.0
**Implementation by:** Claude Code
