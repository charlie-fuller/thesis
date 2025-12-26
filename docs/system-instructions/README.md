# Thesis - L&D Strategist & Learning Coach

**Version:** 1.0 (In Development)
**Purpose:** Standalone L&D assistant for UX/dashboard testing
**Owner:** Paige Bradbury, The Bradbury Group

---

## Project Overview

Thesis is a sophisticated AI assistant specialized in Learning & Development (L&D) strategy, instructional design, and learning science. This standalone version is being prepared for external user testing to validate UX and dashboard functionality before integration into the SuperAssistant platform.

### Core Philosophy

**Thesis teaches you HOW to design work, not just DOES the work for you.**

Many L&D professionals don't understand prompting or agentic workflows. Thesis's purpose is to gently build that capability through:
- Teaching prompting frameworks (GRACE, etc.)
- Explaining workflow design principles
- Showing how AI can augment (not replace) their expertise
- Building independence, not dependency

### Key Differentiators

- **Bradbury Architecture Method** - Proprietary learning design approach
- **P-DOM Framework** - Product-Driven Operating Model for L&D
- **LTEM Methodology** - Advanced evaluation framework (black-boxed for INTERNAL use)
- **Dual Identity** - Both learning coach (primary) and L&D developer (secondary)
- **Capability Builder** - Teaches users to design agentic workflows and prompt effectively

---

## Folder Structure

```
thesis-assistant/
├── system_instructions/     # System Instruction versions
│   ├── thesis_v2.0.txt     # Current internal version (from Paige)
│   └── thesis_v1.0.txt     # Hardened public-ready version (TBD)
├── docs/                    # Documentation & planning
│   ├── thesis_v1.0_hardening_plan.md  # Master hardening plan
│   ├── bradbury-architecture-method.md (TBD)
│   ├── p-dom-framework.md (TBD)
│   └── user-cheat-sheet.md (TBD)
├── prompts/                 # Externalized prompts (if needed)
├── test-data/              # Test scenarios & sample outputs
└── README.md               # This file
```

---

## Current Status

### Completed
- [x] Project folder structure created
- [x] Thesis v2.0 SI received and analyzed
- [x] Comprehensive hardening plan created
- [x] Identified enhancements from Gideon v2.0 and Gigawatt EVAL

### In Progress
- [ ] Awaiting Paige's decisions on key questions (see hardening plan)
- [ ] Draft Thesis v1.0 SI with Phase 1 enhancements
- [ ] Create user cheat sheet for command shortcuts
- [ ] Define dashboard data capture requirements

### Planned
- [ ] Test scenarios for UX validation
- [ ] Knowledge base preparation (AI Playbook, Bradbury Method, P-DOM)
- [ ] Integration with Charlie's dashboard testing
- [ ] Documentation for external users

---

## Key Features (v1.0 Target)

### Core Capabilities
1. **Learning Coach Mode** - Socratic questioning, strategic guidance
2. **L&D Developer Mode** - Generate curricula, assessments, job aids
3. **Data Analyst Mode** - ROI calculations, performance metrics
4. **Strategic Advisor Mode** - L&D strategy, tool selection

### Generative Functions
- Curriculum synthesis from unstructured content
- LTEM-aligned assessment generation
- Facilitator guides & delivery assets
- System Instructions for other AI assistants
- Visual learning journey maps (Mermaid)

### Command Shortcuts
- `/visualize` - Create tables, flowcharts, maps
- `/artifact` - Generate copy-paste-ready assets
- `/assess` - Create assessment questions
- `/roi` - Calculate learning initiative ROI
- `/coach` - Switch to Socratic coaching mode
- `/prompt` - Generate tool-specific prompts

### Unique Features
- **Prompting Coach** - Teaches GRACE framework and other prompting methods
- **Tool-Specific Output** - Optimized for Storyline, Rise, Canva, Gamma, etc.
- **LTEM Black-Boxing** - Uses proprietary framework internally, outputs standard ROI/KPI language
- **Content Integrity Engine** - Bias scanning, accessibility checks, instructional gap analysis

---

## Key Decisions Needed

See `docs/thesis_v1.0_hardening_plan.md` Part 4 for full list:

1. Persona profile integration level?
2. Priority tool list for v1.0?
3. GRACE framework primacy in AI Playbook?
4. Guardrail personality tone (professional → sassy scale)?
5. Configuration complexity for UX testing?

---

## Integration with SuperAssistant

### Current Scope
Thesis v1.0 is **standalone** for testing purposes. The UX and dashboard learnings will inform:
- Solomon Engine enhancements
- Dashboard data capture requirements
- User onboarding flow improvements

### Future Integration
- Thesis's knowledge base structure → inform SuperAssistant's document integration strategy
- Dashboard metrics → feed back into LTEM/ROI tracking for all assistants
- Prompting coach capability → potentially add to SuperAssistant platform

---

## Intellectual Property

**Proprietary Frameworks:**
- Bradbury Architecture Method
- P-DOM (Product-Driven Operating Model)
- LTEM Methodology (Learning-Transfer-Engagement-Measurement)

**Protection Strategy:**
- LTEM used internally, outputs use standard ROI/KPI language
- Never reveal "secret sauce" or framework weighting
- Multi-layer prompt injection defense
- Copyright footer on all generated assets

---

## Testing Plan (with Charlie)

### UX Validation Goals
1. Test operating mode switching (coach vs. developer)
2. Validate command shortcuts usability
3. Test proactive production offers
4. Evaluate output formatting (tables, BLUF, visual-first)

### Dashboard Requirements
- Track mode usage patterns
- Capture command shortcut frequency
- Log generated asset types
- Measure user satisfaction scores
- ROI calculation usage

### Success Criteria
- Users can easily switch between coach and developer modes
- Command shortcuts reduce friction in common tasks
- Visual-first formatting improves scan-reading
- Prompting coach feature gets used (teaching, not just doing)

---

## Contact & Collaboration

**Project Lead:** Paige Bradbury
**Technical Partner:** Charlie (SuperAssistant MVP)
**AI Assistant:** Claude (this session)

---

## Version History

- **v2.0** (Oct 7, 2025) - Internal version with full generative capabilities
- **v1.0** (Target: Dec 2025) - Hardened for external testing

---

**Last Updated:** November 29, 2025
**Next Review:** After Paige's feedback on hardening plan
