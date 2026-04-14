/// <reference path="../pb_data/types.d.ts" />

// Help collections: help_documents, help_conversations (leaf),
// then help_chunks (-> help_documents), help_messages (-> help_conversations).

migrate((app) => {
  // ===== Pass 1: Leaf collections =====

  const helpDocuments = new Collection({
    name: "help_documents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "title", type: "text", required: true },
      { name: "file_path", type: "text", required: true },
      { name: "category", type: "text", required: true },
      { name: "role_access", type: "json" },
      { name: "content", type: "editor", required: true },
      { name: "word_count", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(helpDocuments)

  const helpConversations = new Collection({
    name: "help_conversations",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "title", type: "text" },
      { name: "help_type", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(helpConversations)

  // ===== Pass 2: Collections with relations =====

  const helpChunks = new Collection({
    name: "help_chunks",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "document_id", type: "relation", collectionId: helpDocuments.id, cascadeDelete: true, maxSelect: 1 },
      { name: "content", type: "editor", required: true },
      { name: "chunk_index", type: "number", required: true },
      { name: "heading_context", type: "text" },
      { name: "role_access", type: "json" },
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(helpChunks)

  const helpMessages = new Collection({
    name: "help_messages",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "conversation_id", type: "relation", collectionId: helpConversations.id, cascadeDelete: true, maxSelect: 1 },
      { name: "role", type: "text", required: true },
      { name: "content", type: "editor", required: true },
      { name: "sources", type: "json" },
      { name: "timestamp", type: "date" },
      { name: "feedback", type: "number" },
      { name: "feedback_timestamp", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(helpMessages)

}, (app) => {
  const names = [
    "help_messages", "help_chunks",
    "help_conversations", "help_documents",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
