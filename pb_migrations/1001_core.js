/// <reference path="../pb_data/types.d.ts" />

// Core collections: agents, agent helpers, projects, stakeholders, goals.
// Two-pass: leaf first, then relations.

migrate((app) => {
  // ===== Pass 1: Leaf collections =====

  const agents = new Collection({
    name: "agents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text", required: true },
      { name: "display_name", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "system_instruction", type: "editor" },
      { name: "is_active", type: "bool" },
      { name: "config", type: "json" },
      { name: "capabilities", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(agents)

  const agentTopicMapping = new Collection({
    name: "agent_topic_mapping",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "topic_keyword", type: "text", required: true },
      { name: "agent_name", type: "text", required: true },
      { name: "relevance_score", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(agentTopicMapping)

  const aiProjects = new Collection({
    name: "ai_projects",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "project_code", type: "text", required: true },
      { name: "title", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "department", type: "text" },
      { name: "owner_stakeholder_id", type: "text" },
      { name: "current_state", type: "editor" },
      { name: "desired_state", type: "editor" },
      { name: "roi_potential", type: "number" },
      { name: "implementation_effort", type: "number" },
      { name: "strategic_alignment", type: "number" },
      { name: "stakeholder_readiness", type: "number" },
      // total_score and tier are GENERATED -- computed in app code
      { name: "status", type: "text" },
      { name: "next_step", type: "editor" },
      { name: "blockers", type: "json" },
      { name: "follow_up_questions", type: "json" },
      { name: "roi_indicators", type: "json" },
      { name: "source_type", type: "text" },
      { name: "source_id", type: "text" },
      { name: "source_notes", type: "editor" },
      { name: "metadata", type: "json" },
      { name: "project_summary", type: "editor" },
      { name: "roi_justification", type: "editor" },
      { name: "effort_justification", type: "editor" },
      { name: "alignment_justification", type: "editor" },
      { name: "readiness_justification", type: "editor" },
      { name: "project_name", type: "text" },
      { name: "project_description", type: "editor" },
      { name: "scoring_confidence", type: "number" },
      { name: "confidence_questions", type: "json" },
      { name: "goal_alignment_score", type: "number" },
      { name: "goal_alignment_details", type: "json" },
      { name: "initiative_ids", type: "json" },
      { name: "agenticity_score", type: "number" },
      { name: "agenticity_evaluated_at", type: "date" },
      { name: "agenticity_evaluation", type: "json" },
      { name: "agenticity_task_hash", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(aiProjects)

  const stakeholders = new Collection({
    name: "stakeholders",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text", required: true },
      { name: "email", type: "text" },
      { name: "phone", type: "text" },
      { name: "role", type: "text" },
      { name: "department", type: "text" },
      { name: "organization", type: "text" },
      { name: "sentiment_score", type: "number" },
      { name: "sentiment_trend", type: "text" },
      { name: "engagement_level", type: "text" },
      { name: "alignment_score", type: "number" },
      { name: "first_interaction", type: "date" },
      { name: "last_interaction", type: "date" },
      { name: "total_interactions", type: "number" },
      { name: "communication_preferences", type: "json" },
      { name: "key_concerns", type: "json" },
      { name: "interests", type: "json" },
      { name: "notes", type: "editor" },
      { name: "reports_to", type: "text" },
      { name: "influences", type: "json" },
      { name: "metadata", type: "json" },
      { name: "last_engagement_calculated", type: "date" },
      { name: "priority_level", type: "text" },
      { name: "ai_priorities", type: "json" },
      { name: "pain_points", type: "json" },
      { name: "win_conditions", type: "json" },
      { name: "communication_style", type: "editor" },
      { name: "relationship_status", type: "text" },
      { name: "open_questions", type: "json" },
      { name: "last_contact", type: "date" },
      { name: "reports_to_name", type: "text" },
      { name: "team_size", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(stakeholders)

  const strategicGoals = new Collection({
    name: "strategic_goals",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "level", type: "text", required: true },
      { name: "title", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "department", type: "text" },
      { name: "owner", type: "text" },
      { name: "target_metric", type: "text" },
      { name: "current_value", type: "number" },
      { name: "target_value", type: "number" },
      { name: "unit", type: "text" },
      { name: "status", type: "text" },
      { name: "priority", type: "number" },
      { name: "parent_goal_id", type: "text" },
      { name: "fiscal_year", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(strategicGoals)

  // ===== Pass 2: Collections with relations =====

  const agentHandoffs = new Collection({
    name: "agent_handoffs",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "conversation_id", type: "text", required: true },
      { name: "from_agent_id", type: "relation", collectionId: agents.id, maxSelect: 1 },
      { name: "to_agent_id", type: "relation", collectionId: agents.id, maxSelect: 1 },
      { name: "reason", type: "editor" },
      { name: "context", type: "json" },
      { name: "initiated_at", type: "date" },
      { name: "accepted_at", type: "date" },
      { name: "status", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(agentHandoffs)

  const agentInstructionVersions = new Collection({
    name: "agent_instruction_versions",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "agent_id", type: "relation", collectionId: agents.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "version_number", type: "text", required: true },
      { name: "instructions", type: "editor", required: true },
      { name: "description", type: "editor" },
      { name: "is_active", type: "bool" },
      { name: "created_by", type: "text" },
      { name: "activated_at", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(agentInstructionVersions)

  const agentKnowledgeBase = new Collection({
    name: "agent_knowledge_base",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "agent_id", type: "relation", collectionId: agents.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "document_id", type: "text", required: true },
      { name: "added_by", type: "text" },
      { name: "notes", type: "editor" },
      { name: "priority", type: "number" },
      { name: "relevance_score", type: "number" },
      { name: "classification_source", type: "text" },
      { name: "classification_confidence", type: "number" },
      { name: "classification_reason", type: "editor" },
      { name: "user_confirmed", type: "bool" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(agentKnowledgeBase)

}, (app) => {
  const names = [
    "agent_knowledge_base", "agent_instruction_versions", "agent_handoffs",
    "strategic_goals", "stakeholders", "ai_projects", "agent_topic_mapping", "agents",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
