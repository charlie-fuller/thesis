# DISCo Overview

## What Is DISCo?

DISCo (Discovery-Insights-Synthesis-Convergence) is a product discovery methodology where humans do the discovery and AI does the synthesis. Human facilitators conduct stakeholder interviews, workshops, and observation sessions. AI agents then analyze what was learned, find patterns, identify gaps, and structure findings into engineering-ready Product Requirements Documents. The process moves through four sequential phases, ensuring nothing gets lost between conversation and specification.

## Starting Inputs

Before DISCo begins, gather the raw materials that frame the problem space:

- **Problem Statement**: Initial hypothesis of what needs solving
- **Existing Research**: Market research, competitive analysis, prior studies
- **Golden Examples**: Exemplary solutions or analogous successes from other domains
- **Stakeholder Map**: Who's affected, who decides, who implements
- **Constraints**: Budget, timeline, technical limitations, regulatory requirements
- **Supporting Documents**: Emails, tickets, complaints, feature requests

These inputs give the Triage agent context for the GO/NO-GO decision and help the Discovery Planner design targeted sessions.

## The Four Phases

### Phase 1: Discovery (Intake & Validation)
Validates whether a problem is worth solving and plans how to investigate it. The Triage agent reviews starting inputs and applies four criteria (Is it real? Costly? Solvable? Ours?) to issue a GO/NO-GO decision. The Discovery Planner then creates investigation plans, interview guides, and session agendas for live human discovery sessions with stakeholders.

### Phase 2: Insights (Analysis & Consolidation)
Extracts meaning from research. The Coverage Tracker identifies gaps in discovery. The Insight Extractor finds patterns, contradictions, and hidden dynamics. The Consolidator produces a comprehensive decision document with metrics and system diagrams.

### Phase 3: Synthesis (Bundling & Initiative Definition)
Bundles insights into initiatives. The Strategist clusters related findings and scores them on Impact, Feasibility, and Urgency. Humans review proposed bundles and can approve, reject, merge, or split them.

### Phase 4: Convergence (PRD Generation)
Generates actionable outputs. The PRD Generator creates engineering-ready specifications from approved bundles. The Tech Evaluation agent provides build-vs-buy analysis and architecture recommendations.

## The Eight Agents

| Agent | Role | Key Output |
|-------|------|------------|
| Triage | GO/NO-GO decision | Problem Worth Solving assessment |
| Discovery Planner | Live session planning | Agendas, interview guides, workshop frameworks |
| Coverage Tracker | Gap analysis | Readiness status, missing areas |
| Insight Extractor | Pattern recognition | Enterprise dynamics, contradictions |
| Consolidator | Decision synthesis | Metrics dashboard, recommendations |
| Strategist | Initiative bundling | Scored bundles with dependencies |
| PRD Generator | Specification writing | Engineering-ready PRDs |
| Tech Evaluation | Architecture guidance | Build vs. buy analysis |

## The Human Discovery Process

**Discovery is fundamentally human work.** AI cannot interview stakeholders, observe users, or sense the politics in a room. DISCo's AI agents prepare humans for discovery and process what they learn, but the actual discovery happens through human conversation and observation.

**What Humans Do:**
- Conduct stakeholder interviews and workshops
- Observe users in their environment
- Ask follow-up questions based on body language and tone
- Navigate organizational dynamics and build trust
- Capture notes, recordings, and artifacts

**What AI Does:**
- Prepare session agendas and interview guides (Discovery Planner)
- Track what's been covered vs. what gaps remain (Coverage Tracker)
- Find patterns across multiple sessions (Insight Extractor)
- Synthesize findings into decisions (Consolidator)

**The Session Workflow:**
1. Discovery Planner generates session agenda and interview questions
2. Human facilitator conducts live sessions with stakeholders
3. Session notes, transcripts, and artifacts are uploaded to DISCo
4. Coverage Tracker assesses what's been learned vs. what gaps remain
5. Additional sessions are scheduled until coverage is sufficient
6. Only then does the process move to Insights phase

**What Gets Captured:**
- Pain points and workarounds
- Stakeholder priorities and constraints
- Existing workflows and systems
- Success criteria from different perspectives
- Political dynamics and organizational context

## Key Concepts

- **Human-Led Discovery**: AI prepares and processes, but humans conduct the actual discovery work
- **Human Checkpoints**: Review, approve, reject, merge, or split bundles at each stage
- **Problem Worth Solving Gate**: Four criteria - Is the problem real? Costly? Solvable? Ours to solve?
- **Complexity Tiers**: Light, Medium, Heavy - determines implementation scope
- **Bundle Scoring**: Impact, Feasibility, and Urgency dimensions
- **Smart Brevity**: Concise, decision-first communication (100-150 words)

## The Value Proposition

Transform chaotic discovery into structured initiatives. DISCo pairs human empathy and judgment in live discovery sessions with AI's ability to synthesize, pattern-match, and structure findings. No insight gets lost, every decision is documented, and engineering receives clear specifications grounded in validated stakeholder research.

---

## NotebookLM Graphic Prompt

Use this prompt when generating your graphic in NotebookLM:

```
Create an infographic explaining DISCo, a product discovery methodology where humans do the discovery and AI does the synthesis.

STRUCTURE:
- Show the flow: Starting Inputs → Discovery (human) → Insights (AI) → Synthesis → Convergence
- Emphasize that humans conduct interviews and workshops, AI processes and synthesizes
- Four phases as connected stages: D-I-S-Co
- Include the starting inputs: problem statement, research, golden examples, stakeholder map

COLOR PALETTE:
- Primary: Deep navy or slate blue (trust, expertise)
- Accent: Warm coral or amber (energy, discovery)
- Neutral: Off-white and light gray backgrounds
- Avoid: Neon, gradients, overly playful colors

VISUAL ELEMENTS:
- Human figures for discovery sessions (interviews, workshops)
- Abstract shapes or icons for AI processing
- Flow arrows showing progression through phases
- Four connected nodes representing D-I-S-Co phases
- Subtle grid or structured layout implying methodology

TYPOGRAPHY FEEL:
- Sans-serif, clean, confident
- Bold headers, light body weight
- Structured hierarchy with clear labels

MOOD:
- Strategic and thoughtful
- Human-centered but tech-enabled
- Organized complexity made simple
- The feeling of clarity emerging from chaos

AVOID:
- Cartoon characters or mascots
- Busy patterns or cluttered compositions
- Generic AI imagery (robots, brains, circuits)
- Making it look fully automated (humans are central)
```
