# Requirements Prioritization Heuristics

## Purpose

Reference document for DISCO Convergence agents when prioritizing requirements for enterprise PRDs derived from discovery findings. Provides calibrated frameworks, scoring methods, and traceability guidance. Use these heuristics to transform unordered discovery outputs into a defensible, prioritized requirements list.

---

## 1. MoSCoW with Enterprise Calibration

Standard MoSCoW is subjective. Enterprise calibration ties each tier to concrete decision criteria rooted in sponsor behavior and organizational dynamics.

### Tier Definitions

| Tier | Label | Enterprise Calibration | Decision Test |
|------|-------|----------------------|---------------|
| **M** | Must Have | The sponsor will not approve the initiative without this requirement. Removing it breaks the core value proposition. | "If we cut this, does the sponsor still sign off?" If NO --> Must Have |
| **S** | Should Have | Delivers significant value and will be included if feasible within scope/timeline. Sponsor would be disappointed but would still approve without it. | "Would the sponsor express strong disappointment but still proceed?" If YES --> Should Have |
| **C** | Could Have | Nice to have. Provides incremental value. First items cut when scope pressure appears. | "Would the sponsor notice if this was missing at launch?" If NO --> Could Have |
| **W** | Won't Have (this time) | Explicitly out of scope for this initiative. Documented to prevent scope creep and set expectations. | "Has anyone requested this?" If YES and it's out of scope --> document as Won't Have |

### Enterprise Calibration Rules

1. **Must Haves should be 40-60% of total requirements.** If Must Haves exceed 60%, the scope is too large or calibration is too generous. Challenge each Must Have with the sponsor sign-off test.

2. **Won't Haves are not optional to document.** Every PRD must include an explicit Won't Have list. This prevents scope creep, manages expectations, and provides a backlog for future phases.

3. **Should Haves are the negotiation zone.** When timeline pressure appears, Should Haves are where trade-off conversations happen. Rank them internally by value to enable informed cuts.

4. **Could Haves exist to be cut.** If no Could Haves are cut during delivery, the initial scope was likely too conservative. They serve as a buffer.

### MoSCoW Assignment Decision Tree

```
For each requirement:
  |
  Q1: Does removing this requirement break the initiative's core value proposition?
  |-- YES --> MUST HAVE
  |
  |-- NO
      |
      Q2: Would the sponsor express strong disappointment if this were missing?
      |-- YES --> SHOULD HAVE
      |
      |-- NO
          |
          Q3: Has a stakeholder explicitly requested this?
          |-- YES --> Was it in scope during discovery?
          |   |-- YES --> COULD HAVE
          |   |-- NO  --> WON'T HAVE (this time)
          |
          |-- NO --> Omit entirely (not a real requirement)
```

---

## 2. RICE Scoring Adapted for Enterprise PRDs

RICE provides a numerical score for comparing requirements. The enterprise adaptation recalibrates each factor for internal tools and process improvements where "users" are employees and "reach" is organizational impact.

### Factor Definitions

| Factor | Definition | Scale | Enterprise Interpretation |
|--------|-----------|-------|--------------------------|
| **Reach** | How many people, processes, or systems are affected | Number of people or processes per quarter | Count affected employees, teams, or business processes. A requirement affecting 500 employees scores higher than one affecting a 5-person team. |
| **Impact** | Magnitude of change for those reached | 3 = Massive, 2 = High, 1 = Medium, 0.5 = Low, 0.25 = Minimal | Massive: eliminates a major pain point or creates a new capability. Minimal: slight convenience improvement. |
| **Confidence** | Quality of evidence from discovery | 100% = High, 80% = Medium, 50% = Low | High: multiple stakeholders confirmed, data supports it. Medium: some stakeholder input, reasonable assumption. Low: single mention, no data, or team's intuition only. |
| **Effort** | Implementation cost | Person-weeks | Include design, development, testing, deployment, and documentation. Round to nearest whole week. |

### RICE Formula

```
RICE Score = (Reach x Impact x Confidence) / Effort
```

### Scoring Example

| Requirement | Reach | Impact | Confidence | Effort | RICE Score |
|-------------|-------|--------|------------|--------|------------|
| Auto-classify uploaded documents by topic | 200 users | 2 (High) | 80% | 6 weeks | (200 x 2 x 0.8) / 6 = **53.3** |
| Add dark mode to dashboard | 200 users | 0.25 (Minimal) | 50% | 3 weeks | (200 x 0.25 x 0.5) / 3 = **8.3** |
| Integrate with Salesforce CRM | 50 users | 3 (Massive) | 100% | 12 weeks | (50 x 3 x 1.0) / 12 = **12.5** |
| Bulk export reports to PDF | 80 users | 1 (Medium) | 80% | 2 weeks | (80 x 1 x 0.8) / 2 = **32.0** |
| Real-time collaboration on docs | 200 users | 2 (High) | 50% | 16 weeks | (200 x 2 x 0.5) / 16 = **12.5** |

**Interpretation**: Auto-classify (53.3) and bulk export (32.0) score highest. Dark mode (8.3) scores lowest despite reaching all users because impact and confidence are low. Salesforce and real-time collaboration tie at 12.5 but for different reasons (high impact/effort vs. low confidence/high effort).

### RICE Calibration Notes for Enterprise Context

- **Reach floor**: If a requirement affects fewer than 10 people, question whether it belongs in a platform-level PRD or should be handled as a team-specific configuration.
- **Confidence penalty**: Discovery-backed requirements should have confidence >= 80%. If confidence is 50% or below, consider running a validation spike before committing to the requirement.
- **Effort sanity check**: Any single requirement estimated at > 8 person-weeks should be examined for decomposition. It may be multiple requirements bundled together.

---

## 3. Kano Model for Enterprise Internal Tools

The Kano model classifies requirements by their relationship to user satisfaction. For enterprise internal tools, the distribution skews heavily toward Basic requirements.

### Category Definitions

| Category | User Reaction When Present | User Reaction When Absent | Enterprise Internal Tool Frequency |
|----------|--------------------------|--------------------------|-----------------------------------|
| **Basic** | No praise; taken for granted | Complaints, frustration, workarounds | 60-70% of requirements |
| **Performance** | Satisfaction increases linearly with quality | Satisfaction decreases linearly | 20-30% of requirements |
| **Excitement** | Delight, surprise, "I didn't know I needed this" | No reaction (they didn't know it was possible) | 5-10% of requirements |

### Enterprise Internal Tool Kano Distribution

Most internal tool requirements are Basic. Users expect the tool to work correctly, be available, handle their data safely, and integrate with existing systems. These generate no praise when delivered but cause significant friction when missing.

**Common Basic requirements for enterprise tools:**
- SSO/authentication works reliably
- Data is not lost or corrupted
- Performance is acceptable (sub-3-second page loads)
- Permissions respect organizational hierarchy
- Export/import of data in standard formats
- Audit trail for compliance-sensitive actions
- Mobile-responsive (if users are mobile)

**Common Performance requirements:**
- Search speed and relevance (more is better)
- Report generation time (faster is better)
- Number of integrations supported (more is better)
- Customization depth (more flexibility is better)

**Common Excitement requirements (rare for internal tools):**
- AI-powered suggestions that save significant manual work
- Automated detection of anomalies or opportunities
- Natural language interfaces that replace complex query builders
- Proactive notifications that prevent problems before they occur

### Kano Prioritization Rule

```
Priority order:
  1. ALL Basic requirements first (these are table stakes)
  2. Performance requirements ranked by RICE score
  3. Excitement requirements only if Basic and top Performance are covered

Exception: If an Excitement requirement has a very high RICE score
and low effort, it may be promoted to demonstrate innovation value
to sponsors. But never at the expense of undelivered Basic requirements.
```

### Kano Classification Decision Tree

```
For each requirement:
  |
  Q1: Would users actively complain or create workarounds if this were missing?
  |-- YES --> BASIC (must deliver; no praise expected)
  |
  |-- NO
      |
      Q2: Does "more/better" of this directly increase user satisfaction?
      |-- YES --> PERFORMANCE (invest proportionally to RICE score)
      |
      |-- NO
          |
          Q3: Would this surprise and delight users?
          |-- YES --> EXCITEMENT (include only if basics are covered)
          |
          |-- NO --> Reconsider whether this is a real requirement
```

---

## 4. Leading vs. Lagging Indicators

Every requirement should have associated success metrics. Distinguish between leading indicators (predictive, actionable early) and lagging indicators (outcome-based, measured after delivery).

### Indicator Mapping Table for Common Enterprise Scenarios

| Requirement Domain | Leading Indicator | Lagging Indicator | Measurement Timing |
|-------------------|-------------------|-------------------|-------------------|
| **Process automation** | Number of processes mapped for automation; automation script completion rate | Reduction in manual hours per process; error rate reduction | Leading: during build. Lagging: 30-90 days post-launch |
| **Search/discovery** | Search index coverage; query response time in staging | Search usage frequency; time-to-find-document reduction | Leading: during build. Lagging: 30 days post-launch |
| **Reporting/analytics** | Number of report templates built; data source connections established | Report generation frequency; reduction in ad-hoc data requests | Leading: during build. Lagging: 60 days post-launch |
| **Integration** | API endpoints implemented; test coverage of integration paths | Data sync accuracy; reduction in manual data entry | Leading: during build. Lagging: 30 days post-launch |
| **User adoption** | Training completion rate; beta user feedback scores | Daily active users; feature utilization rate | Leading: pre-launch. Lagging: 60-90 days post-launch |
| **Compliance/governance** | Audit controls implemented; policy rules encoded | Audit pass rate; compliance incident reduction | Leading: during build. Lagging: next audit cycle |
| **Content management** | Content types modeled; workflow stages configured | Publishing cycle time; content reuse rate | Leading: during build. Lagging: 60 days post-launch |
| **Knowledge management** | Documents indexed; taxonomy categories defined | Knowledge retrieval success rate; duplicate content reduction | Leading: during build. Lagging: 90 days post-launch |

### Indicator Assignment Rules

1. **Every Must Have requirement needs at least one lagging indicator.** This is how you prove the requirement delivered its intended value.
2. **Every requirement estimated at > 4 person-weeks needs a leading indicator.** This enables early course correction during delivery.
3. **Leading indicators should be measurable during development**, not after launch. They serve as progress signals.
4. **Lagging indicators should be baselined before development begins.** If you cannot measure the current state, you cannot prove improvement.

---

## 5. Requirements Traceability

Every requirement in the PRD must trace back to at least one discovery finding. Untraceable requirements are either scope creep or indicate a gap in discovery documentation.

### Traceability Matrix Template

| Req ID | Requirement | Discovery Source | Finding ID | Stakeholder | Evidence Type |
|--------|------------|-----------------|------------|-------------|--------------|
| R-001 | Auto-classify documents by topic | Stakeholder interview: Content Ops lead | D-014 | Sarah M. (Content Ops) | Direct request + pain point observation |
| R-002 | Bulk export to PDF | Stakeholder interview: Finance Director | D-022 | James T. (Finance) | Workaround documented (manual copy-paste to Word) |
| R-003 | SSO integration | Security policy review | D-031 | IT Security team | Compliance requirement (non-negotiable) |
| R-004 | AI-powered search suggestions | Synthesis: pattern across 4 interviews | D-008, D-015, D-023, D-029 | Multiple | Synthesized from repeated "search is painful" theme |
| R-005 | Dark mode | No discovery source identified | -- | -- | **FLAG: No traceability. Challenge inclusion.** |

### Traceability Rules

1. **1:1 minimum**: Every requirement must map to at least one discovery finding.
2. **Many:1 is strong**: A requirement supported by multiple findings has stronger justification. Note this in confidence scoring.
3. **1:many is expected**: A single finding may generate multiple requirements (e.g., "search is broken" may yield requirements for indexing, relevance tuning, and UI improvements).
4. **0:1 is a red flag**: A requirement with no discovery source should be challenged. Either the discovery was incomplete (go back and validate) or the requirement is scope creep.
5. **Trace to Won't Haves too**: Document which findings were addressed by Won't Have items, so future phases can pick them up with context.

---

## 6. Technical Debt Assessment

Discovery often uncovers technical debt that, while not a "feature," directly impacts the feasibility or success of new requirements. The PRD must address this explicitly.

### When to Include Technical Debt in PRD

| Scenario | Include in PRD? | Rationale |
|----------|----------------|-----------|
| Debt directly blocks a Must Have requirement | **Yes, as a Must Have prerequisite** | Cannot deliver the feature without addressing the debt |
| Debt degrades performance of a Should Have requirement | **Yes, as a Should Have** | Addressing it significantly improves the requirement's impact |
| Debt is unrelated to any PRD requirement but was discovered | **No, route to engineering backlog** | Out of scope; document separately for tech lead awareness |
| Debt affects system reliability broadly | **Yes, as Foundation work** | Impacts all requirements; include as platform-level prerequisite |
| Debt is speculative ("this might cause problems someday") | **No** | Not evidence-based; does not meet traceability standard |

### Technical Debt Scoring

When tech debt items are included, score them using a modified RICE:

| Factor | Adaptation for Tech Debt |
|--------|------------------------|
| **Reach** | Number of requirements or features affected by this debt |
| **Impact** | Severity if debt is not addressed: 3 = blocks features, 2 = degrades performance, 1 = increases maintenance cost, 0.5 = cosmetic/minor |
| **Confidence** | How certain are we this debt is real? 100% = measured/observed, 80% = engineering team consensus, 50% = one engineer's concern |
| **Effort** | Person-weeks to remediate |

### Tech Debt Classification

| Type | Description | Example | Typical Priority |
|------|------------|---------|-----------------|
| **Blocking debt** | Prevents new feature delivery | Database schema incompatible with new data model | Must Have (prerequisite) |
| **Degrading debt** | Reduces quality of new features | Slow API that will get slower with new load | Should Have |
| **Drag debt** | Slows development velocity | No automated tests; every change requires manual QA | Should Have (for large initiatives) |
| **Latent debt** | No current impact but growing risk | Deprecated library still in use | Could Have or backlog |

---

## 7. Scalability Assessment

Requirements should be evaluated for future-proofing, but over-engineering is equally dangerous. Use the "3x rule" and explicit horizon planning.

### The 3x Rule

Design for 3x current scale. Not 10x. Not 100x. Three times.

| Dimension | Current State | Design For (3x) | Do Not Design For |
|-----------|--------------|-----------------|-------------------|
| **Users** | 200 employees | 600 employees | 10,000 employees (unless M&A is imminent) |
| **Data volume** | 10,000 documents | 30,000 documents | 1 million documents |
| **Integrations** | 3 systems | 9 systems | "any system in the world" |
| **Concurrent users** | 20 peak | 60 peak | 1,000 concurrent |

### Scalability Decision Tree

```
For each requirement:
  |
  Q1: Is there a known growth event in the next 12 months?
      (M&A, new market, org restructuring, major product launch)
  |-- YES --> Design for the post-event scale specifically
  |
  |-- NO
      |
      Q2: Is the requirement's architecture easy to change later?
      |-- YES --> Design for current needs only (YAGNI principle)
      |           Document the scaling path for future reference
      |
      |-- NO (hard to change: data models, API contracts, auth architecture)
          |
          Apply the 3x rule for this requirement.
          Document the scaling assumption explicitly.
```

### Scalability Assessment Table Template

| Requirement | Current Scale | 3x Scale | Scaling Approach | Effort to Scale Later | Decision |
|-------------|--------------|----------|------------------|-----------------------|----------|
| Document search | 10K docs | 30K docs | Add search index (Elasticsearch) | Medium (4 weeks) | Design for 30K now; index architecture supports 100K+ |
| User permissions | 200 users, 5 roles | 600 users, 15 roles | Role-based, not user-based | Low (config change) | Current RBAC design sufficient; no extra work needed |
| Report generation | 50 reports/day | 150 reports/day | Queue-based processing | High (8 weeks to retrofit) | Build with queue from start; hard to retrofit |
| API rate limits | 100 req/min | 300 req/min | Rate limiter config | Low (config change) | Set at 300 now; trivial to adjust |

### Over-Engineering Warning Signs

| Signal | What It Looks Like | Correction |
|--------|-------------------|------------|
| "What if we need to support..." | Designing for hypothetical scenarios with no evidence | Ask: "Is there a discovery finding that supports this scale?" If no, defer. |
| Generic abstraction layers | Building a "platform" when you need a "feature" | Build the specific thing. Abstract only when the second use case appears. |
| Microservices for < 5 developers | Distributed architecture for a small team | Monolith-first. Decompose when team size or deployment frequency demands it. |
| Multi-tenant from day one | Building tenant isolation for a single-tenant tool | Single-tenant. Add tenancy only if there's a concrete multi-tenant requirement. |

---

## 8. Prioritization Process: Step-by-Step

For DISCO agents executing the convergence phase:

1. **List all candidate requirements** from synthesis output with their discovery traceability (Section 5).
2. **Classify each requirement using Kano** (Section 3). Ensure all Basic requirements are identified.
3. **Assign MoSCoW tier** using the enterprise-calibrated decision tree (Section 1). Validate that Must Haves are 40-60% of total.
4. **Score all Should Have and Could Have requirements with RICE** (Section 2). Must Haves do not need RICE (they are non-negotiable). Won't Haves do not need RICE (they are out of scope).
5. **Assess technical debt** (Section 6). Add blocking debt as Must Have prerequisites. Score degrading/drag debt with modified RICE.
6. **Run scalability assessment** (Section 7) on Must Have and top-scoring Should Have requirements.
7. **Assign leading and lagging indicators** (Section 4) to all Must Haves and high-effort requirements.
8. **Validate traceability** (Section 5). Flag any requirement without a discovery source.
9. **Produce the final prioritized list** ordered by: Must Have (all) > Should Have (by RICE) > Could Have (by RICE) > Won't Have (documented for future reference).

### Final Output Format

| Priority | Req ID | Requirement | MoSCoW | Kano | RICE | Discovery Source | Indicators |
|----------|--------|-------------|--------|------|------|-----------------|------------|
| 1 | R-003 | SSO integration | Must | Basic | -- | D-031 | Lagging: auth success rate |
| 2 | R-001 | Auto-classify documents | Must | Performance | -- | D-014 | Leading: model accuracy in staging. Lagging: classification accuracy at 30d |
| 3 | R-004 | AI-powered search | Should | Excitement | 53.3 | D-008, D-015, D-023, D-029 | Leading: index coverage. Lagging: search usage frequency |
| 4 | R-002 | Bulk export to PDF | Should | Basic | 32.0 | D-022 | Lagging: export usage, manual workaround elimination |
| 5 | R-006 | Custom report builder | Could | Performance | 18.7 | D-019 | Lagging: report generation frequency |
| -- | R-005 | Dark mode | Won't | Performance | 8.3 | None | -- |
