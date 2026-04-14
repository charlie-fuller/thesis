/// <reference path="../pb_data/types.d.ts" />

// PuRDy collections: 11 tables across 2 passes.
// Pass 1: leaf collections (no relations to other PuRDy tables)
// Pass 2: collections with relations to Pass 1

migrate((app) => {
  // ===== Pass 1: Leaf collections =====

  const purdyInitiatives = new Collection({
    name: "purdy_initiatives",
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
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(purdyInitiatives)

  const purdySystemKb = new Collection({
    name: "purdy_system_kb",
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
  app.save(purdySystemKb)

  const purdyConversations = new Collection({
    name: "purdy_conversations",
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
  app.save(purdyConversations)

  // ===== Pass 2: Relations to purdy_initiatives / purdy_system_kb =====

  const purdyDocuments = new Collection({
    name: "purdy_documents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "relation", collectionId: purdyInitiatives.id, cascadeDelete: true, maxSelect: 1 },
      { name: "filename", type: "text", required: true },
      { name: "content", type: "editor", required: true },
      { name: "document_type", type: "text" },
      { name: "version", type: "number" },
      { name: "source_run_id", type: "text" },
      { name: "uploaded_at", type: "date" },
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(purdyDocuments)

  const purdyInitiativeMembers = new Collection({
    name: "purdy_initiative_members",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "initiative_id", type: "relation", collectionId: purdyInitiatives.id, cascadeDelete: true, maxSelect: 1 },
      { name: "role", type: "text" },
      { name: "invited_at", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(purdyInitiativeMembers)

  const purdyMessages = new Collection({
    name: "purdy_messages",
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
  app.save(purdyMessages)

  const purdyRuns = new Collection({
    name: "purdy_runs",
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
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(purdyRuns)

  const purdyOutputs = new Collection({
    name: "purdy_outputs",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "run_id", type: "text" },
      { name: "initiative_id", type: "text", required: true },
      { name: "agent_type", type: "text", required: true },
      { name: "version", type: "number" },
      { name: "title", type: "text" },
      { name: "recommendation", type: "editor" },
      { name: "tier_routing", type: "text" },
      { name: "confidence_level", type: "text" },
      { name: "executive_summary", type: "editor" },
      { name: "content_markdown", type: "editor" },
      { name: "content_structured", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(purdyOutputs)

  const purdyDocumentChunks = new Collection({
    name: "purdy_document_chunks",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "document_id", type: "text" },
      { name: "initiative_id", type: "relation", collectionId: purdyInitiatives.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "chunk_index", type: "number" },
      { name: "content", type: "editor" },
      // embedding (vector) omitted
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(purdyDocumentChunks)

  const purdySystemKbChunks = new Collection({
    name: "purdy_system_kb_chunks",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "kb_id", type: "relation", collectionId: purdySystemKb.id, cascadeDelete: true, maxSelect: 1 },
      { name: "chunk_index", type: "number" },
      { name: "content", type: "editor" },
      // embedding (vector) omitted
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(purdySystemKbChunks)

  const purdyRunDocuments = new Collection({
    name: "purdy_run_documents",
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
  app.save(purdyRunDocuments)

}, (app) => {
  // Down migration: delete in reverse order (Pass 2, then Pass 1)
  const names = [
    // Pass 2
    "purdy_run_documents", "purdy_system_kb_chunks", "purdy_document_chunks",
    "purdy_outputs", "purdy_runs", "purdy_messages", "purdy_initiative_members",
    "purdy_documents",
    // Pass 1
    "purdy_conversations", "purdy_system_kb", "purdy_initiatives",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
