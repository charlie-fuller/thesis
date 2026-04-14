/// <reference path="../pb_data/types.d.ts" />

// Obsidian vault sync and graph sync collections.
// Two-pass: leaf first, then relations.

migrate((app) => {
  // ===== Pass 1: Leaf collections =====

  const obsidianVaultConfigs = new Collection({
    name: "obsidian_vault_configs",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "vault_path", type: "text", required: true },
      { name: "vault_name", type: "text" },
      { name: "is_active", type: "bool" },
      { name: "last_sync_at", type: "date" },
      { name: "last_error", type: "editor" },
      { name: "sync_options", type: "json" },
      { name: "metadata", type: "json" },
      { name: "sync_progress", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(obsidianVaultConfigs)

  const graphSyncLog = new Collection({
    name: "graph_sync_log",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "sync_type", type: "text", required: true },
      { name: "entity_type", type: "text", required: true },
      { name: "entity_id", type: "text" },
      { name: "synced_at", type: "date" },
      { name: "sync_status", type: "text", required: true },
      { name: "details", type: "json" },
      { name: "error_message", type: "editor" },
      { name: "duration_ms", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(graphSyncLog)

  const graphSyncState = new Collection({
    name: "graph_sync_state",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "entity_type", type: "text", required: true },
      { name: "last_synced_at", type: "date" },
      { name: "last_sync_status", type: "text" },
      { name: "record_count", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(graphSyncState)

  // ===== Pass 2: Collections with relations =====

  const obsidianSyncLog = new Collection({
    name: "obsidian_sync_log",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "config_id", type: "relation", collectionId: obsidianVaultConfigs.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "sync_type", type: "text", required: true },
      { name: "status", type: "text", required: true },
      { name: "trigger_source", type: "text" },
      { name: "files_scanned", type: "number" },
      { name: "files_added", type: "number" },
      { name: "files_updated", type: "number" },
      { name: "files_deleted", type: "number" },
      { name: "files_skipped", type: "number" },
      { name: "files_failed", type: "number" },
      { name: "duration_ms", type: "number" },
      { name: "error_message", type: "editor" },
      { name: "error_details", type: "json" },
      { name: "started_at", type: "date" },
      { name: "completed_at", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(obsidianSyncLog)

  const obsidianSyncState = new Collection({
    name: "obsidian_sync_state",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "config_id", type: "relation", collectionId: obsidianVaultConfigs.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "file_path", type: "text", required: true },
      { name: "document_id", type: "text" },
      { name: "file_mtime", type: "date" },
      { name: "file_hash", type: "text" },
      { name: "file_size", type: "number" },
      { name: "sync_status", type: "text" },
      { name: "last_synced_at", type: "date" },
      { name: "sync_error", type: "editor" },
      { name: "frontmatter", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(obsidianSyncState)

}, (app) => {
  const names = [
    "obsidian_sync_state", "obsidian_sync_log",
    "graph_sync_state", "graph_sync_log", "obsidian_vault_configs",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
