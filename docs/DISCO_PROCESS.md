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

Before running the DISCO pipeline, users can add structured input framing to an initiative via the "Structured Framing" section in the create or edit modal:

- **Problem Statements**: What problems are we trying to solve? (auto-ID: ps-1, ps-2, ...)
- **Hypotheses**: What do we believe to be true? Types: assumption, belief, prediction (auto-ID: h-1, h-2, ...)
- **Known Gaps**: What information are we missing? Categories: data, people, process, capability (auto-ID: g-1, g-2, ...)
- **Desired Outcome State**: What does the world look like when this initiative succeeds?

When present, the throughline is injected into all 4 agent stages. Each agent references problem statements, evaluates hypotheses against evidence, and tracks gap coverage. At convergence, the Requirements Generator produces a structured **Throughline Resolution** with hypothesis status (confirmed/refuted/inconclusive), gap status (addressed/unaddressed), recommended state changes, and a "So What?" analysis.

---

## Stage 1: Discovery (D)

**Agent:** Discovery Guide

**Purpose:** Validate whether the problem is worth solving and plan how to gather the necessary information.

**What Happens:**
1. User uploads relevant documents (meeting notes, research, prior work)
2. User links existing Knowledge Base documents
3. Discovery Guide analyzes the materials and runs in one of three modes:
   - **Triage Mode:** GO/NO-GO gate - determines if the opportunity warrants further investigation
   - **Planning Mode:** Designs discovery sessions for humans to execute (stakeholder interviews, research tasks)
   - **Coverage Mode:** Tracks discovery completeness and identifies gaps

**Outputs:**
- Discovery plan with recommended sessions
- Stakeholder candidates identified from documents
- Project candidates surfaced from analysis
- Task candidates for follow-up work

**Human Checkpoint:** Review discovery findings and confirm readiness to proceed to Intelligence stage.

**Status:** Initiative moves from `draft` → `triaged` → `in_discovery`

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

**Status:** Initiative moves to `consolidated`

---

## Stage 3: Synthesis (S)

**Agent:** Initiative Builder

**Purpose:** Cluster validated insights into themed initiative bundles and score them for prioritization.

**What Happens:**
1. Initiative Builder groups related insights into coherent bundles
2. Each bundle receives scores:
   - **Impact:** HIGH / MEDIUM / LOW
   - **Feasibility:** HIGH / MEDIUM / LOW
   - **Urgency:** HIGH / MEDIUM / LOW
3. Assigns complexity tier: Light / Medium / Heavy
4. Identifies dependencies and affected stakeholders
5. Documents bundling rationale

**Outputs:**
- One or more initiative bundles, each containing:
  - Name and description
  - Included insights with mapping
  - Impact, feasibility, urgency scores
  - Complexity tier
  - Stakeholders affected
  - Dependencies (blockers, parallel work)
  - Bundling rationale

**Human Checkpoint - Bundle Review:**
Bundles are created with status `proposed`. Users can:
- **Approve** → Bundle proceeds to Convergence (status: `approved`)
- **Reject** → Bundle stops here (status: `rejected`)
- **Merge** → Combine multiple bundles into one
- **Split** → Divide one bundle into multiple bundles

All actions are tracked in bundle feedback for audit purposes.

**Status:** Initiative moves to `synthesized`

---

## Stage 4: Convergence (C)

**Agent:** Requirements Generator

**Purpose:** Transform an approved bundle into a formal output document.

**What Happens:**
1. User selects an approved bundle
2. User chooses the output document type:
   - **PRD (Product Requirements Document):** For build/development initiatives
   - **Evaluation Framework:** For vendor/tool comparisons and platform selection
   - **Decision Framework:** For governance, policy, and strategic decisions
3. Requirements Generator produces the document with streaming output
4. Document is parsed into structured sections automatically

**Output Document Types:**

| Type | Best For | Key Sections |
|------|----------|--------------|
| **PRD** | Features, systems, development work | Executive Summary, Problem Statement, Goals, Requirements, User Stories, Technical Considerations, Risks |
| **Evaluation Framework** | Tool selection, vendor comparison | Evaluation Scope, Weighted Criteria Matrix, Platform Comparison, Recommendation, Next Steps |
| **Decision Framework** | Policy, strategy, governance | Decision Context, Stakeholder Analysis, Decision Criteria, Options Analysis, Risk/Benefit Assessment, Implementation |

**Human Checkpoint - Document Review:**
Documents are created with status `draft`. Users can:
- **Edit** → Modify content, version is incremented
- **Approve** → Document is locked (status: `approved`), approver recorded
- **Export** → Send to external system (status: `exported`)

**Status:** Initiative moves to `documented`

---

## Stage 5: Operationalize (O)

**Purpose:** Transform approved documents into actionable work and integrate with operational systems.

Once a document is approved in Convergence, it enters the Operationalize phase. This stage has no dedicated agent - it consists of post-processing options and destination routing.

### Post-Processing Options

**1. Project Extraction (AI-Powered)**
- AI analyzes the approved document and extracts project fields:
  - Title, description, department
  - Current state and desired state
  - Scores: ROI potential, implementation effort, strategic alignment, stakeholder readiness
  - Initial task list
- Creates a new project in the Projects Pipeline
- Links back to source DISCO initiative for traceability
- Project status set to `identified`

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
Project → Document → Bundle → Insights → Discovery Materials → Source Documents
```

This audit trail enables:
- Understanding why decisions were made
- Revisiting assumptions when circumstances change
- Demonstrating due diligence in the discovery process
- Learning from past initiatives

---

## Summary

| Stage | Agent | Key Action | Human Checkpoint | Output |
|-------|-------|------------|------------------|--------|
| **D - Discovery** | Discovery Guide | Validate problem, plan discovery | Review findings | Discovery plan, candidates |
| **I - Intelligence** | Insight Analyst | Extract patterns, consolidate | Validate insights | Decision document |
| **S - Synthesis** | Initiative Builder | Cluster into bundles, score | Approve/reject bundles | Scored bundles |
| **C - Convergence** | Requirements Generator | Generate output document | Approve document | PRD / Evaluation / Decision |
| **O - Operationalize** | (Post-processing) | Extract project, integrate KB | N/A | Projects, KB docs, exports |

---

## Related Documentation

- [DISCO Roadmap](./DISCO_ROADMAP.md) - Future enhancements planned
- [Architecture](./ARCHITECTURE.md) - Technical implementation details
- [Agent Guardrails](./AGENT_GUARDRAILS.md) - Agent behavior rules

---

*This document corresponds to the Workflow Map and Operationalize Map visualizations in the DISCO section of the application.*
