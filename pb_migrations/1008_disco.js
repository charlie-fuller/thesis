/// <reference path="../pb_data/types.d.ts" />

// DISCO collections: 18 tables across 3 passes.
// Pass 1: leaf collections (no relations to other DISCO tables)
// Pass 2: collections with relations to Pass 1
// Pass 3: collections with relations to Pass 2

migrate((app) => {
  // ===== Pass 1: Leaf collections =====

  const discoInitiatives = new Collection({
    name: "disco_initiatives",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "status", type: "text" },
      { name: "created_by", type: "text" },
      { name: "decided_at", type: "date" },
      { name: "launched_at", type: "date" },
      { name: "completed_at", type: "date" },
      { name: "abandoned_at", type: "date" },
      // decision_velocity_days is GENERATED ALWAYS -- omit
      { name: "goal_alignment_score", type: "number" },
      { name: "goal_alignment_details", type: "json" },
      { name: "throughline", type: "json" },
      { name: "target_department", type: "text" },
      { name: "value_alignment", type: "json" },
      { name: "sponsor_stakeholder_id", type: "text" },
      { name: "stakeholder_ids", type: "json" },
      { name: "resolution_annotations", type: "json" },
      { name: "user_corrections", type: "editor" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(discoInitiatives)

  const discoSystemKb = new Collection({
    name: "disco_system_kb",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "filename", type: "text", required: true },
      { name: "content", type: "editor", required: true },
      { name: "category", type: "text" },
      { name: "description", type: "editor" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(discoSystemKb)

  const discoConversations = new Collection({
    name: "disco_conversations",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "text" },
      { name: "user_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoConversations)

  const discoOutcomeMetrics = new Collection({
    name: "disco_outcome_metrics",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text" },
      { name: "status", type: "text" },
      { name: "decided_at", type: "date" },
      { name: "launched_at", type: "date" },
      { name: "completed_at", type: "date" },
      { name: "abandoned_at", type: "date" },
      { name: "decision_velocity_days", type: "number" },
      { name: "velocity_category", type: "text" },
      { name: "avg_stakeholder_rating", type: "number" },
      { name: "ratings_count", type: "number" },
      { name: "total_outputs", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoOutcomeMetrics)

  // ===== Pass 2: Relations to disco_initiatives / disco_system_kb =====

  const discoBundles = new Collection({
    name: "disco_bundles",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "relation", collectionId: discoInitiatives.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "name", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "status", type: "text" },
      { name: "impact_score", type: "text" },
      { name: "impact_rationale", type: "editor" },
      { name: "feasibility_score", type: "text" },
      { name: "feasibility_rationale", type: "editor" },
      { name: "urgency_score", type: "text" },
      { name: "urgency_rationale", type: "editor" },
      { name: "complexity_tier", type: "text" },
      { name: "complexity_rationale", type: "editor" },
      { name: "included_items", type: "json" },
      { name: "stakeholders", type: "json" },
      { name: "dependencies", type: "json" },
      { name: "bundling_rationale", type: "editor" },
      { name: "source_output_id", type: "text" },
      { name: "approved_at", type: "date" },
      { name: "solution_type", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(discoBundles)

  const discoCheckpoints = new Collection({
    name: "disco_checkpoints",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "relation", collectionId: discoInitiatives.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "checkpoint_number", type: "number", required: true },
      { name: "status", type: "text" },
      { name: "approved_at", type: "date" },
      { name: "notes", type: "editor" },
      { name: "checklist_items", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(discoCheckpoints)

  const discoDocuments = new Collection({
    name: "disco_documents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "relation", collectionId: discoInitiatives.id, cascadeDelete: true, maxSelect: 1 },
      { name: "filename", type: "text", required: true },
      { name: "content", type: "editor", required: true },
      { name: "document_type", type: "text" },
      { name: "version", type: "number" },
      { name: "source_run_id", type: "text" },
      { name: "uploaded_at", type: "date" },
      { name: "metadata", type: "json" },
      { name: "migrated_to_kb", type: "bool" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoDocuments)

  const discoInitiativeDocuments = new Collection({
    name: "disco_initiative_documents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "relation", collectionId: discoInitiatives.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "document_id", type: "text" },
      { name: "linked_at", type: "date" },
      { name: "linked_by", type: "text" },
      { name: "notes", type: "editor" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoInitiativeDocuments)

  const discoInitiativeFolders = new Collection({
    name: "disco_initiative_folders",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "relation", collectionId: discoInitiatives.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "folder_path", type: "text", required: true },
      { name: "recursive", type: "bool" },
      { name: "linked_at", type: "date" },
      { name: "linked_by", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoInitiativeFolders)

  const discoInitiativeMembers = new Collection({
    name: "disco_initiative_members",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "relation", collectionId: discoInitiatives.id, cascadeDelete: true, maxSelect: 1 },
      { name: "role", type: "text" },
      { name: "invited_at", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoInitiativeMembers)

  const discoMessages = new Collection({
    name: "disco_messages",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "conversation_id", type: "text" },
      { name: "role", type: "text", required: true },
      { name: "content", type: "editor", required: true },
      { name: "sources", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoMessages)

  const discoRuns = new Collection({
    name: "disco_runs",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "text" },
      { name: "agent_type", type: "text", required: true },
      { name: "run_by", type: "text" },
      { name: "started_at", type: "date" },
      { name: "completed_at", type: "date" },
      { name: "status", type: "text" },
      { name: "error_message", type: "editor" },
      { name: "token_usage", type: "json" },
      { name: "metadata", type: "json" },
      { name: "project_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoRuns)

  const discoOutputs = new Collection({
    name: "disco_outputs",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "run_id", type: "text" },
      { name: "initiative_id", type: "text" },
      { name: "agent_type", type: "text", required: true },
      { name: "version", type: "number" },
      { name: "title", type: "text" },
      { name: "recommendation", type: "editor" },
      { name: "tier_routing", type: "text" },
      { name: "confidence_level", type: "text" },
      { name: "executive_summary", type: "editor" },
      { name: "content_markdown", type: "editor" },
      { name: "content_structured", type: "json" },
      { name: "synthesis_mode", type: "text" },
      { name: "intermediate_outputs", type: "json" },
      { name: "output_format", type: "text" },
      { name: "source_outputs", type: "json" },
      { name: "synthesis_notes", type: "editor" },
      { name: "stakeholder_rating", type: "number" },
      { name: "stakeholder_feedback", type: "editor" },
      { name: "last_run_at", type: "date" },
      { name: "throughline_resolution", type: "json" },
      { name: "triage_suggestions", type: "json" },
      { name: "project_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoOutputs)

  const discoDocumentChunks = new Collection({
    name: "disco_document_chunks",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "document_id", type: "text" },
      { name: "initiative_id", type: "relation", collectionId: discoInitiatives.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "chunk_index", type: "number" },
      { name: "content", type: "editor" },
      // embedding (vector) omitted
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoDocumentChunks)

  const discoSystemKbChunks = new Collection({
    name: "disco_system_kb_chunks",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "kb_id", type: "relation", collectionId: discoSystemKb.id, cascadeDelete: true, maxSelect: 1 },
      { name: "chunk_index", type: "number" },
      { name: "content", type: "editor" },
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoSystemKbChunks)

  // ===== Pass 3: Relations to disco_bundles =====

  const discoBundleFeedback = new Collection({
    name: "disco_bundle_feedback",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "bundle_id", type: "relation", collectionId: discoBundles.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "action", type: "text", required: true },
      { name: "feedback", type: "editor" },
      { name: "changes", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoBundleFeedback)

  const discoPrds = new Collection({
    name: "disco_prds",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "bundle_id", type: "relation", collectionId: discoBundles.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "initiative_id", type: "text" },
      { name: "title", type: "text", required: true },
      { name: "content_markdown", type: "editor", required: true },
      { name: "content_structured", type: "json" },
      { name: "status", type: "text" },
      { name: "version", type: "number" },
      { name: "source_output_id", type: "text" },
      { name: "approved_at", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(discoPrds)

  const discoRunDocuments = new Collection({
    name: "disco_run_documents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "run_id", type: "text" },
      { name: "document_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(discoRunDocuments)

}, (app) => {
  // Down migration: delete in reverse order (Pass 3, then Pass 2, then Pass 1)
  const names = [
    // Pass 3
    "disco_run_documents", "disco_prds", "disco_bundle_feedback",
    // Pass 2
    "disco_system_kb_chunks", "disco_document_chunks", "disco_outputs", "disco_runs",
    "disco_messages", "disco_initiative_members", "disco_initiative_folders",
    "disco_initiative_documents", "disco_documents", "disco_checkpoints", "disco_bundles",
    // Pass 1
    "disco_outcome_metrics", "disco_conversations", "disco_system_kb", "disco_initiatives",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
