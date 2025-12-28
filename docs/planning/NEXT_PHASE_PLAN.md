# Thesis - Next Phase Implementation Plan

**Created:** 2025-12-27
**Status:** Planning
**Author:** Claude (with Charlie Fuller)

---

## Executive Summary

This document outlines the next phase of work to move Thesis from "agents defined" to "agents operational." The system instructions are complete for all 12 agents, but several infrastructure pieces are needed to make them fully functional.

---

## Current State (Completed)

### Agent System Instructions (12 total)
- **Persona-Aligned (6):** Atlas, Fortuna, Guardian, Counselor, Sage, Oracle
- **Consulting/Implementation (4):** Strategist, Architect, Operator, Pioneer
- **Internal Enablement (2):** Catalyst, Scholar

### Infrastructure Completed
- Coordinator agent with routing to all 12 specialists
- XML-based externalized system instructions
- Agent instruction versioning API (create, activate, compare, delete)
- Admin UI for agent management with version history
- Neo4j graph integration for stakeholder networks

---

## Phase 1: Agent Infrastructure (Priority: High)

### 1.1 Create Python Agent Classes for New Agents

**What:** Create individual Python agent classes for the 6 new agents that only have XML system instructions.

**Files to Create:**
```
backend/agents/strategist.py
backend/agents/architect.py
backend/agents/operator.py
backend/agents/pioneer.py
backend/agents/catalyst.py
backend/agents/scholar.py
```

**Pattern to Follow:** Use existing agents (atlas.py, fortuna.py, etc.) as templates.

**Estimated Effort:** 2-3 hours

### 1.2 Database Seeding for New Agents

**What:** Add database records for the new agents so they appear in the admin UI.

**SQL to Run:**
```sql
INSERT INTO agents (name, display_name, description, is_active) VALUES
('strategist', 'Strategist', 'Executive Strategy Partner - C-suite engagement and organizational politics', true),
('architect', 'Architect', 'Technical Architecture Partner - Enterprise AI patterns and integration', true),
('operator', 'Operator', 'Business Operations Partner - Process optimization and metrics', true),
('pioneer', 'Pioneer', 'Innovation Partner - Emerging technology and hype filtering', true),
('catalyst', 'Catalyst', 'Internal Communications Partner - AI messaging and employee engagement', true),
('scholar', 'Scholar', 'L&D Partner - Training programs and champion enablement', true);
```

**Estimated Effort:** 30 minutes

### 1.3 Register New Agents with Coordinator

**What:** Update the agent factory/registry to instantiate and register the new agents.

**File to Update:** `backend/agents/__init__.py` or wherever agents are registered

**Estimated Effort:** 1 hour

### 1.4 Load XML Instructions on Agent Init

**What:** Ensure agents load their system instructions from XML files on initialization.

**Pattern:**
```python
def _get_default_instruction(self) -> str:
    xml_path = Path(__file__).parent.parent / "system_instructions/agents/strategist.xml"
    if xml_path.exists():
        return xml_path.read_text()
    return self._fallback_instruction()
```

**Estimated Effort:** 1-2 hours

---

## Phase 2: Agent Testing and Refinement (Priority: High)

### 2.1 Integration Tests for Each Agent

**What:** Create test cases that verify each agent responds appropriately to domain-specific queries.

**Test Structure:**
```python
# test_agents.py
async def test_strategist_executive_query():
    """Strategist should handle C-suite engagement questions."""
    response = await strategist.process(AgentContext(
        user_message="How do we get our CEO more engaged in AI initiatives?"
    ))
    assert "executive" in response.content.lower() or "sponsorship" in response.content.lower()
```

**Coverage:**
- Each agent handles its domain appropriately
- Coordinator routes to correct agents
- Multi-agent synthesis works for cross-domain queries

**Estimated Effort:** 4-6 hours

### 2.2 Coordinator Routing Validation

**What:** Test that the coordinator correctly routes queries to appropriate specialists.

**Test Cases:**
| Query | Expected Agent(s) |
|-------|------------------|
| "What's the ROI of this project?" | fortuna |
| "How do we communicate this to employees?" | catalyst |
| "Design a training program for AI" | scholar |
| "What emerging technologies should we watch?" | pioneer |
| "How do we get executive buy-in?" | strategist |
| "What architecture should we use?" | architect |
| "How do we optimize this process?" | operator |

**Estimated Effort:** 2-3 hours

### 2.3 Few-Shot Example Testing

**What:** Validate that agents produce responses matching their few-shot examples in quality and format.

**Estimated Effort:** 2-3 hours

---

## Phase 3: Frontend Enhancements (Priority: Medium)

### 3.1 Agent Chat Interface Updates

**What:** Ensure the chat interface works with all 12 agents and displays appropriate context.

**Considerations:**
- Agent-specific colors/icons in chat
- Display which specialist(s) contributed to response
- Show confidence/routing reasoning (optional, for admin)

**Estimated Effort:** 3-4 hours

### 3.2 Agent Detail Page Enhancements

**What:** Improve the agent detail page in admin to show:
- Agent description and persona alignment
- Recent conversations handled by this agent
- Success metrics (if available)
- Quick test interface

**Estimated Effort:** 4-6 hours

### 3.3 Bulk Import of XML Instructions

**What:** Create admin capability to:
- Upload new XML system instruction
- Preview changes before applying
- Bulk update multiple agents

**Estimated Effort:** 4-6 hours

---

## Phase 4: Memory and Learning (Priority: Medium)

### 4.1 Agent-Specific Memory

**What:** Configure Mem0 to maintain separate memory contexts per agent.

**Pattern:**
```python
# When saving memory
metadata = {
    "repo": "thesis",
    "agent": "strategist",
    "type": "insight"
}
```

**Estimated Effort:** 2-3 hours

### 4.2 Cross-Agent Memory Sharing

**What:** Determine which memories should be shared across agents vs. agent-specific.

**Categories:**
- **Shared:** Client context, stakeholder information, decisions made
- **Agent-Specific:** Domain-specific learnings, patterns discovered

**Estimated Effort:** 2-3 hours

### 4.3 Memory Search in Agent Context

**What:** Before responding, agents should search relevant memories to provide context-aware responses.

**Estimated Effort:** 2-3 hours

---

## Phase 5: Advanced Features (Priority: Low)

### 5.1 Agent Performance Analytics

**What:** Track and display:
- Query volume per agent
- Response quality metrics (user feedback)
- Routing accuracy
- Average response time

**Estimated Effort:** 6-8 hours

### 5.2 A/B Testing for Agent Instructions

**What:** Allow running two versions of an agent's instructions to compare effectiveness.

**Estimated Effort:** 8-10 hours

### 5.3 Agent Specialization Tuning

**What:** Fine-tune routing keywords and LLM classification based on actual usage patterns.

**Estimated Effort:** 4-6 hours

---

## Phase 6: Persona Alignment for New Agents (Priority: Ongoing)

### 6.1 Interview Subject Identification

As new interviews are conducted at Contentful or other enterprises, align new agents to interview subjects:

| Agent | Ideal Interview Subject |
|-------|------------------------|
| Strategist | CTO, Chief Strategy Officer, COO |
| Architect | VP Engineering, Solutions Architect |
| Operator | Operations Director, Process Excellence Lead |
| Pioneer | Head of Innovation, R&D Director |
| Catalyst | Head of Internal Comms, Employee Experience |
| Scholar | L&D Director, Training Manager |

### 6.2 Persona Update Process

When interview subject is identified:
1. Analyze interview transcript
2. Update agent XML with persona_alignment section
3. Add specific concerns, language patterns, anti-patterns
4. Update few-shot examples to match persona voice
5. Create new version in instruction versioning system

---

## Recommended Execution Order

### Week 1: Foundation
1. Create Python agent classes (Phase 1.1)
2. Database seeding (Phase 1.2)
3. Register with coordinator (Phase 1.3)
4. XML loading (Phase 1.4)

### Week 2: Validation
1. Integration tests (Phase 2.1)
2. Routing validation (Phase 2.2)
3. Few-shot testing (Phase 2.3)

### Week 3: Polish
1. Chat interface updates (Phase 3.1)
2. Agent detail page (Phase 3.2)
3. Memory integration (Phase 4.1-4.3)

### Ongoing
- Persona alignment as interviews happen
- Analytics and A/B testing
- Routing optimization

---

## Success Criteria

### Phase 1 Complete When:
- All 12 agents appear in admin UI
- All agents can process queries
- Coordinator routes to all agents correctly

### Phase 2 Complete When:
- All integration tests pass
- Routing accuracy > 90%
- Response quality matches few-shot examples

### Phase 3 Complete When:
- Chat shows agent attribution
- Admin can manage all agents
- Bulk operations work

### Full MVP When:
- All 12 agents operational
- Memory integration working
- Basic analytics available
- At least 2-3 new agents have persona alignment

---

## Dependencies and Blockers

### External Dependencies
- Interview subjects for persona alignment (user-dependent)
- Contentful stakeholder access for testing (user-dependent)

### Technical Dependencies
- Supabase database access
- Neo4j for graph features (optional)
- Anthropic API for agent responses

### Blockers
- None identified - all work can proceed with current infrastructure

---

## Notes

This plan focuses on **making what exists work** rather than adding new capabilities. The 12 agent system instructions are comprehensive - the priority is infrastructure to make them operational.

Future phases (customer-facing agents, engineering perspectives, external comms) should wait until this foundation is solid.
