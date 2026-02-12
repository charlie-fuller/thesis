# DISCO Process Guide

**Discovery - Intelligence - Synthesis - Convergence - Operationalize**

This document describes the complete DISCO workflow from initiative creation through operationalization. It corresponds to the visual process maps available in the DISCO section of the application (Workflow Map and Operationalize Map tabs).

---

## Overview

DISCO is a structured methodology for transforming ambiguous opportunities into actionable outputs. The process moves through five stages, each with a dedicated AI agent and human checkpoint to ensure quality and alignment.

**Process Flow:**
```
Discovery → Intelligence → Synthesis → Convergence → Operationalize
    D            I            S            C              O
```

---

## Structured Framing (Optional)

Before running the DISCO pipeline, users can add structured input framing to a discovery. There are two approaches:

### Agent-Extracted Framing (Recommended)
1. Create a discovery with just a name, description, and linked documents
2. Run the **Triage** agent
3. The agent analyzes documents using Five Whys and root cause analysis, then suggests problem statements, hypotheses, gaps, KPIs, and stakeholders
4. A "Review Suggested Framing" panel appears after triage
5. Accept all, accept selectively, or dismiss

### Manual Framing
In the create or edit modal, expand "Investigation Framing":

- **Problem Statements**: What problems are we trying to solve? (auto-ID: ps-1, ps-2, ...)
- **Hypotheses**: What do we believe to be true? Types: assumption, belief, prediction (auto-ID: h-1, h-2, ...)
- **Known Gaps**: What information are we missing? Categories: data, people, process, capability (auto-ID: g-1, g-2, ...)
- **Desired Outcome State**: What does the world look like when this discovery succeeds?

When present, the throughline is injected into all 4 agent stages. Each agent references problem statements, evaluates hypotheses against evidence, and tracks gap coverage. At convergence, the Requirements Generator produces a structured **Throughline Resolution** with hypothesis status (confirmed/refuted/inconclusive), gap status (addressed/unaddressed), recommended state changes, and a "So What?" analysis.

---

## Value Alignment (Optional)

Each discovery can track alignment with organizational value streams. All fields are optional and can be populated progressively:

| Field | Purpose |
|-------|---------|
| **Target Department** | Which department this discovery serves |
| **KPIs** | Measurable outcomes this discovery supports |
| **Department Goals** | Goals this supports (free text) |
| **Company Priority** | Which company priority it aligns with |
| **Strategic Pillar** | Enable, Operationalize, or Govern |
| **Notes** | Context on how alignment was discovered |

The triage agent can suggest KPIs and department context from documents. Value alignment is validated at the Convergence stage.

---

## Stage 1: Discovery (D)

**Agent:** Discovery Guide (v1.2)

**Purpose:** Validate whether the problem is worth solving and plan how to gather the necessary information.

**What Happens:**
1. User uploads relevant documents (meeting notes, research, prior work)
2. User links existing Knowledge Base documents
3. Discovery Guide analyzes the materials and runs in one of three modes:
   - **Triage Mode:** GO/NO-GO gate - determines if the opportunity warrants further investigation. Uses Five Whys and root cause analysis. Extracts suggested framing (problem statements, hypotheses, gaps, KPIs, stakeholders) from documents.
   - **Planning Mode:** Designs discovery sessions for humans to execute (stakeholder interviews, research tasks) with gap-targeted questions
   - **Coverage Mode:** Tracks discovery completeness, identifies gaps (READY/GAPS), includes "Why This Matters" and absence reports

**Outputs:**
- Discovery plan with recommended sessions
- Stakeholder candidates identified from documents
- Project candidates surfaced from analysis
- Task candidates for follow-up work
- Framing suggestions (problem statements, hypotheses, gaps, KPIs) when throughline is sparse

**Human Checkpoint:** Review discovery findings and suggested framing. Confirm readiness to proceed to Intelligence stage.

**Status:** Discovery moves from `draft` → `triaged` → `in_discovery`

---

## Stage 2: Intelligence (I)

**Agent:** Insight Analyst

**Purpose:** Extract patterns from discovery materials and consolidate findings into a decision-ready document.

**What Happens:**
1. Insight Analyst reviews all discovery documents and session transcripts
2. Extracts recurring themes with supporting evidence
3. Identifies contradictions and tensions in the data
4. Surfaces "What They Don't Realize" insights - non-obvious findings
5. Synthesizes everything into a cohesive narrative

**Outputs:**
- System patterns (leveraging the Pattern Library)
- Contradictions table highlighting conflicting information
- Key insights with evidence citations
- GO/NO-GO/CONDITIONAL recommendation with confidence level
- Explicit handoff summary for next stage

**Human Checkpoint:** Validate insights, resolve contradictions, confirm recommendation.

**Status:** Discovery moves to `consolidated`

---

## Stage 3: Synthesis (S)

**Agent:** Initiative Builder

**Purpose:** Cluster validated insights into themed proposed initiatives and score them for prioritization.

**What Happens:**
1. Initiative Builder groups related insights into coherent proposed initiatives
2. Each proposed initiative receives scores:
   - **Impact:** HIGH / MEDIUM / LOW
   - **Feasibility:** HIGH / MEDIUM / LOW
   - **Urgency:** HIGH / MEDIUM / LOW
3. Assigns complexity tier: Light / Medium / Heavy
4. Identifies dependencies and affected stakeholders
5. Documents bundling rationale
6. Notes which throughline items (problem statements, hypotheses) each proposed initiative addresses

**Outputs:**
- One or more proposed initiatives, each containing:
  - Name and description
  - Included insights with mapping
  - Impact, feasibility, urgency scores
  - Complexity tier
  - Stakeholders affected
  - Dependencies (blockers, parallel work)
  - Bundling rationale

**Human Checkpoint - Proposed Initiative Review:**
Proposed initiatives are created with status `proposed`. Users can:
- **Approve** → Proposed initiative proceeds to Convergence or direct project creation (status: `approved`)
- **Reject** → Proposed initiative stops here (status: `rejected`)
- **Merge** → Combine multiple proposed initiatives into one
- **Split** → Divide one proposed initiative into multiple

All actions are tracked in feedback for audit purposes.

**Status:** Discovery moves to `synthesized`

---

## Stage 4: Convergence (C)

**Agent:** Requirements Generator (v1.2)

**Purpose:** Transform an approved proposed initiative into a formal output document.

**What Happens:**
1. User selects an approved proposed initiative
2. User chooses the output document type:
   - **PRD (Product Requirements Document):** For build/development initiatives
   - **Evaluation Framework:** For vendor/tool comparisons and platform selection
   - **Decision Framework:** For governance, policy, and strategic decisions
3. Requirements Generator produces the document with streaming output
4. Document is parsed into structured sections automatically
5. When throughline is present, produces a structured **Throughline Resolution**

**Output Document Types:**

| Type | Best For | Key Sections |
|------|----------|--------------|
| **PRD** | Features, systems, development work | Executive Summary, Problem Statement, Goals, Requirements, User Stories, Technical Considerations, Risks, Tool/Platform Recommendations |
| **Evaluation Framework** | Tool selection, vendor comparison | Evaluation Scope, Weighted Criteria Matrix, Platform Comparison, Recommendation, Next Steps |
| **Decision Framework** | Policy, strategy, governance | Decision Context, Stakeholder Analysis, Decision Criteria, Options Analysis, Risk/Benefit Assessment, Implementation |

**All output types include:**
- Value alignment confirmation (verifies recommendation ties to KPIs)
- Tool and platform recommendations (simplest effective tool principle)
- AI risk and compliance review (data classification, EU AI Act, platform governance)
- Evaluation/QA plan

**Human Checkpoint - Document Review:**
Documents are created with status `draft`. Users can:
- **Edit** → Modify content, version is incremented
- **Approve** → Document is locked (status: `approved`), approver recorded
- **Export** → Send to external system (status: `exported`)

**Status:** Discovery moves to `documented`

---

## Stage 5: Operationalize (O)

**Purpose:** Transform approved documents into actionable work and integrate with operational systems.

Once a document is approved in Convergence, it enters the Operationalize phase. This stage has no dedicated agent - it consists of post-processing options and destination routing.

### Post-Processing Options

**1a. Direct Project Creation (from Proposed Initiative)**
- Click "Create Project" on an approved proposed initiative (no PRD required)
- Score mapping: impact → roi_potential, feasibility → effort, urgency → alignment
- Name and description pre-filled from proposed initiative
- Quick path for simpler cases that don't need a full PRD

**1b. Project Extraction from Document (AI-Powered)**
- AI analyzes the approved document and extracts project fields:
  - Title, description, department
  - Current state and desired state
  - Scores: ROI potential, implementation effort, strategic alignment, stakeholder readiness
  - Initial task list
- Confidence indicators highlight low-confidence fields for user review
- Creates a new project in the Projects Pipeline
- Links back to source DISCO discovery for traceability
- Project status set to `identified`

**1c. Task Creation from State Changes**
- When convergence output includes throughline resolution with state changes, click "Create Tasks from State Changes"
- Select which state changes to create as tasks
- Optionally link tasks to a project
- "Next Human Action" from "So What?" section included as high-priority task option
- Tasks include `source_initiative_id` and `source_disco_output_id` for traceability

**2. Executive Summary Generation**
- Summarizes all approved bundles/documents from the initiative
- Provides prioritization recommendations
- Creates leadership-ready overview
- Useful for steering committee presentations

**3. Knowledge Base Integration**
- Promotes the approved document to the searchable Knowledge Base
- Document becomes available via initiative chat Q&A
- RAG-enabled for future queries across initiatives
- Maintains full traceability to source materials

### Destinations

**Projects Pipeline**
- Projects extracted from documents appear on the Kanban board
- Status progression: Identified → Scoping → Active → Complete
- Full task management and assignment capabilities
- Progress tracking and stakeholder visibility
- Maintains link to source DISCO initiative

**External Export**
- Export approved documents to external systems
- Integrations: Jira, Confluence, Notion
- Download as PDF or Markdown
- API webhook triggers for automation
- Audit trail maintained with `exported` status

---

## Traceability

DISCO maintains full traceability throughout the process. Every output can be traced back through the chain:

```
Task → Project → Document → Proposed Initiative → Insights → Discovery Materials → Source Documents
```

Tasks created from state changes include `source_initiative_id` and `source_disco_output_id` for direct traceability. Projects include `source_type: disco_prd` and link to parent discovery via `initiative_ids`.

This audit trail enables:
- Understanding why decisions were made
- Revisiting assumptions when circumstances change
- Demonstrating due diligence in the discovery process
- Learning from past discoveries
- Resolution annotations for correcting agent assessments as new information emerges

---

## Summary

| Stage | Agent | Key Action | Human Checkpoint | Output |
|-------|-------|------------|------------------|--------|
| **D - Discovery** | Discovery Guide (v1.2) | Validate problem, extract framing, plan discovery | Review findings + suggested framing | Discovery plan, candidates, framing suggestions |
| **I - Intelligence** | Insight Analyst | Extract patterns, consolidate | Validate insights | Decision document |
| **S - Synthesis** | Initiative Builder | Cluster into proposed initiatives, score | Approve/reject proposed initiatives | Scored proposed initiatives |
| **C - Convergence** | Requirements Generator (v1.2) | Generate output document + throughline resolution | Approve document | PRD / Evaluation / Decision + resolution |
| **O - Operationalize** | (Post-processing) | Create project, create tasks, integrate KB | N/A | Projects, tasks, KB docs, exports |

---

## Related Documentation

- [DISCO Roadmap](./DISCO_ROADMAP.md) - Future enhancements planned
- [Architecture](./ARCHITECTURE.md) - Technical implementation details
- [Agent Guardrails](./AGENT_GUARDRAILS.md) - Agent behavior rules

---

*This document corresponds to the Workflow Map and Operationalize Map visualizations in the DISCO section of the application.*
