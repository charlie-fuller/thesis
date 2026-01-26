# Initiative Risk Framework

## Purpose
Identify and assess risks that commonly derail strategic initiatives. Use during synthesis (Agent 3) to flag risks in PRDs and during discovery to ensure risk topics are covered.

---

## Risk Categories

### 1. Scope & Requirements Risks

| Risk Pattern | Warning Signs | Mitigation |
|--------------|---------------|------------|
| **Scope creep** | Stakeholders keep adding "one more thing"; no clear boundary | Define explicit out-of-scope list; change control process |
| **Unclear requirements** | Different stakeholders describe different solutions; vague success criteria | Validate requirements with multiple stakeholders; document assumptions |
| **Moving target** | Business context changing; strategy shifts mid-initiative | Short iteration cycles; regular stakeholder check-ins |
| **Gold plating** | Push for perfection over progress; features no one asked for | MVP mindset; prioritized backlog; "good enough" thresholds |

### 2. Stakeholder & Organizational Risks

| Risk Pattern | Warning Signs | Mitigation |
|--------------|---------------|------------|
| **Misaligned sponsors** | Different executives have different visions | Explicit alignment session; documented decision rights |
| **Missing champions** | No one advocating for adoption; passive support only | Identify and empower champions early; create ownership |
| **Resistance to change** | "We've always done it this way"; active pushback | Change management plan; involve resisters in design |
| **Competing priorities** | Key people overcommitted; initiative keeps slipping | Executive prioritization; dedicated resources |
| **Knowledge silos** | Critical info in one person's head; no documentation | Knowledge transfer sessions; documentation requirements |

### 3. Technical & Integration Risks

| Risk Pattern | Warning Signs | Mitigation |
|--------------|---------------|------------|
| **Data quality issues** | Inconsistent data; missing fields; manual workarounds | Data audit early; data cleanup as prerequisite |
| **Integration complexity** | Multiple systems; unclear APIs; legacy constraints | Technical spike; integration architect involvement |
| **Performance unknowns** | Scale requirements unclear; no load testing plan | Define SLAs early; performance testing in scope |
| **Security/compliance gaps** | Sensitive data; regulatory requirements; access control | Security review early; compliance checklist |
| **Technical debt** | Building on shaky foundation; known issues deferred | Assess foundation health; include remediation |

### 4. Execution & Delivery Risks

| Risk Pattern | Warning Signs | Mitigation |
|--------------|---------------|------------|
| **Resource constraints** | Team understaffed; key skills missing | Realistic resourcing; skill gap plan |
| **Dependency delays** | Blocked by other teams/initiatives; external vendors | Dependency mapping; buffer time; escalation paths |
| **Unrealistic timeline** | Pressure to deliver fast; insufficient analysis time | Evidence-based estimates; scope negotiation |
| **Quality shortcuts** | Rushing to meet dates; testing skipped | Quality gates; acceptance criteria defined |

### 5. Adoption & Value Risks

| Risk Pattern | Warning Signs | Mitigation |
|--------------|---------------|------------|
| **Build it and they won't come** | No adoption plan; assumes users will just use it | User research; adoption metrics; training plan |
| **Solving wrong problem** | Solution doesn't address root cause; symptoms treated | Root cause analysis; problem validation |
| **Value hard to measure** | Success criteria vague; no baseline | Define metrics early; establish baselines |
| **Sustainability concerns** | Who maintains this? No operational plan | Operations team involvement; handoff plan |

---

## Risk Assessment Matrix

### Likelihood Scale
| Level | Description |
|-------|-------------|
| **High** | Very likely to occur; has happened before |
| **Medium** | Could occur; some warning signs present |
| **Low** | Unlikely but possible; mitigations in place |

### Impact Scale
| Level | Description |
|-------|-------------|
| **High** | Would significantly delay or derail initiative |
| **Medium** | Would cause notable setback; recoverable |
| **Low** | Minor inconvenience; easily managed |

### Priority Matrix
```
              │  Low Impact  │ Med Impact  │ High Impact
──────────────┼──────────────┼─────────────┼─────────────
High          │   Monitor    │   Mitigate  │  🚨 Critical
Likelihood    │              │   Actively  │
──────────────┼──────────────┼─────────────┼─────────────
Medium        │   Accept     │   Monitor   │   Mitigate
Likelihood    │              │   Closely   │   Actively
──────────────┼──────────────┼─────────────┼─────────────
Low           │   Accept     │   Accept    │   Monitor
Likelihood    │              │             │
```

---

## Risk Discovery Questions

Use these during discovery to surface risks:

### For Sponsors/Leadership
- What keeps you up at night about this initiative?
- What would cause you to consider this a failure?
- What's been tried before? What happened?
- Who might resist this change?

### For Process Owners
- What workarounds exist today?
- Where does data quality break down?
- What happens when [key person] is unavailable?
- What systems are most fragile?

### For Technical Teams
- What technical unknowns concern you?
- What integrations are most complex?
- What's the technical debt situation?
- What would you prototype first to reduce risk?

### For End Users
- What would stop you from using this?
- What's happened with past changes?
- What training would you need?
- What would make you a champion for this?

---

## Risk Documentation Template

For each identified risk in a PRD:

```markdown
### Risk: [Name]

**Category:** [Scope/Stakeholder/Technical/Execution/Adoption]
**Likelihood:** [High/Medium/Low]
**Impact:** [High/Medium/Low]
**Priority:** [Critical/Mitigate/Monitor/Accept]

**Description:**
[What is the risk? How might it manifest?]

**Warning Signs:**
- [Early indicator 1]
- [Early indicator 2]

**Mitigation Plan:**
- [Action 1]
- [Action 2]

**Owner:** [Who is responsible for monitoring/mitigating]
**Review Frequency:** [How often to reassess]
```

---

## Common Risk Patterns by Initiative Type

### Process Improvement Initiatives
- Change resistance from current process owners
- Data quality issues in existing systems
- Scope creep as more inefficiencies surface
- Adoption failure if training inadequate

### New Capability Initiatives
- Requirements unclear until users see something
- Integration complexity underestimated
- Competing priorities delay resourcing
- Value measurement difficult

### System Replacement Initiatives
- Data migration complexity
- Feature parity expectations
- User attachment to old system
- Parallel running costs

### Cross-Functional Initiatives
- Stakeholder alignment challenges
- Competing departmental priorities
- Handoff/boundary confusion
- Governance unclear

---

## Risk Review Checkpoints

| Phase | Risk Focus |
|-------|------------|
| **Discovery** | Identify risks; ensure coverage in sessions |
| **PRD Draft** | Document known risks; assign owners |
| **PRD Review** | Validate risk assessment; challenge assumptions |
| **Execution** | Monitor warning signs; update mitigations |
| **Retrospective** | Review what materialized; capture learnings |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-22 | Initial framework |
