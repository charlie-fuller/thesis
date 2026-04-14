/// <reference path="../pb_data/types.d.ts" />

// Document collections: documents, document_chunks, document_classifications, document_tags.
// Two-pass: documents (leaf), then chunks/classifications/tags (relations).

migrate((app) => {
  // ===== Pass 1: Leaf collection =====

  const documents = new Collection({
    name: "documents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "filename", type: "text" },
      { name: "file_type", type: "text" },
      { name: "mime_type", type: "text" },
      { name: "file_size", type: "number" },
      { name: "storage_url", type: "editor" },
      { name: "processing_status", type: "text" },
      { name: "processing_error", type: "editor" },
      { name: "chunk_count", type: "number" },
      { name: "access_count", type: "number" },
      { name: "is_core_document", type: "bool" },
      { name: "source_platform", type: "text" },
      { name: "external_url", type: "text" },
      { name: "google_drive_file_id", type: "text" },
      { name: "notion_page_id", type: "text" },
      { name: "sync_cadence", type: "text" },
      { name: "last_synced_at", type: "date" },
      { name: "uploaded_at", type: "date" },
      { name: "processed", type: "bool" },
      { name: "storage_path", type: "text" },
      { name: "external_id", type: "text" },
      { name: "title", type: "text" },
      { name: "obsidian_vault_path", type: "text" },
      { name: "obsidian_file_path", type: "text" },
      { name: "original_date", type: "date" },
      { name: "document_type", type: "text" },
      { name: "primary_use_case", type: "text" },
      { name: "classification_confidence", type: "number" },
      { name: "classification_method", type: "text" },
      { name: "tasks_scanned_at", type: "date" },
      { name: "stakeholders_scanned_at", type: "date" },
      { name: "granola_id", type: "text" },
      { name: "granola_scanned_at", type: "date" },
      { name: "projects_scanned_at", type: "date" },
      { name: "tags_cache", type: "json" },
      { name: "needs_reverse_sync", type: "bool" },
      { name: "reverse_synced_at", type: "date" },
      { name: "digest", type: "editor" },
      { name: "digest_generated_at", type: "date" },
      { name: "related_document_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(documents)

  // ===== Pass 2: Collections with relations to documents =====

  const documentChunks = new Collection({
    name: "document_chunks",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "document_id", type: "relation", collectionId: documents.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "chunk_index", type: "number" },
      { name: "content", type: "editor" },
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(documentChunks)

  const documentClassifications = new Collection({
    name: "document_classifications",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "document_id", type: "relation", collectionId: documents.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "detected_type", type: "text" },
      { name: "classification_method", type: "text" },
      { name: "model_used", type: "text" },
      { name: "tokens_used", type: "number" },
      { name: "processing_time_ms", type: "number" },
      { name: "raw_scores", type: "json" },
      { name: "sample_chunks_used", type: "number" },
      { name: "status", type: "text" },
      { name: "requires_user_review", type: "bool" },
      { name: "review_reason", type: "editor" },
      { name: "reviewed_at", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(documentClassifications)

  const documentTags = new Collection({
    name: "document_tags",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "document_id", type: "relation", collectionId: documents.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "tag", type: "text" },
      { name: "source", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(documentTags)

}, (app) => {
  const names = [
    "document_tags", "document_classifications", "document_chunks", "documents",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
