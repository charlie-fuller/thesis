/// <reference path="../pb_data/types.d.ts" />

// Chat collections: conversations, messages, message_documents.
// Three-pass: conversations (leaf), messages (relation), message_documents (relation).

migrate((app) => {
  // ===== Pass 1: Leaf collection =====

  const conversations = new Collection({
    name: "conversations",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "title", type: "text" },
      { name: "archived", type: "bool" },
      { name: "archived_at", type: "date" },
      { name: "in_knowledge_base", type: "bool" },
      { name: "added_to_kb_at", type: "date" },
      { name: "project_id", type: "text" },
      { name: "agent_id", type: "text" },
      { name: "agent_instruction_version_id", type: "text" },
      { name: "initiative_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(conversations)

  // ===== Pass 2: Messages (relation to conversations) =====

  const messages = new Collection({
    name: "messages",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "conversation_id", type: "relation", collectionId: conversations.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "topic", type: "text" },
      { name: "role", type: "text" },
      { name: "content", type: "editor" },
      { name: "extension", type: "editor" },
      { name: "payload", type: "json" },
      { name: "event", type: "text" },
      { name: "metadata", type: "json" },
      { name: "private", type: "bool" },
      { name: "inserted_at", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(messages)

  // ===== Pass 3: Message documents (relation to messages) =====

  const messageDocuments = new Collection({
    name: "message_documents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "message_id", type: "relation", collectionId: messages.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "document_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(messageDocuments)

}, (app) => {
  const names = [
    "message_documents", "messages", "conversations",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
