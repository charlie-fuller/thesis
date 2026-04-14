/// <reference path="../pb_data/types.d.ts" />

// Task collections: project_tasks, task_candidates (leaf), then task_comments, task_history (relations).
// Two-pass: leaf first, then relations.

migrate((app) => {
  // ===== Pass 1: Leaf collections =====

  const projectTasks = new Collection({
    name: "project_tasks",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "title", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "status", type: "text" },
      { name: "priority", type: "number" },
      { name: "assignee_stakeholder_id", type: "text" },
      { name: "assignee_user_id", type: "text" },
      { name: "assignee_name", type: "text" },
      { name: "due_date", type: "date" },
      { name: "completed_at", type: "date" },
      { name: "source_type", type: "text" },
      { name: "source_transcript_id", type: "text" },
      { name: "source_conversation_id", type: "text" },
      { name: "source_research_task_id", type: "text" },
      { name: "source_project_id", type: "text" },
      { name: "source_text", type: "editor" },
      { name: "source_extracted_at", type: "date" },
      { name: "category", type: "text" },
      { name: "tags", type: "json" },
      { name: "related_stakeholder_ids", type: "json" },
      { name: "related_project_id", type: "text" },
      { name: "blocker_reason", type: "editor" },
      { name: "blocked_at", type: "date" },
      { name: "metadata", type: "json" },
      { name: "position", type: "number" },
      { name: "source_document_id", type: "text" },
      { name: "team", type: "text" },
      { name: "linked_project_id", type: "text" },
      // embedding is USER-DEFINED vector -- omitted, handled by vec sidecar
      { name: "sequence_number", type: "number" },
      { name: "depends_on", type: "json" },
      { name: "notes", type: "editor" },
      { name: "source_initiative_id", type: "text" },
      { name: "source_disco_output_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(projectTasks)

  const taskCandidates = new Collection({
    name: "task_candidates",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "source_document_id", type: "text" },
      { name: "source_document_name", type: "text" },
      { name: "source_text", type: "editor" },
      { name: "title", type: "text", required: true },
      { name: "suggested_priority", type: "number" },
      { name: "suggested_due_date", type: "date" },
      { name: "due_date_text", type: "text" },
      { name: "assignee_name", type: "text" },
      { name: "confidence", type: "text" },
      { name: "extraction_pattern", type: "text" },
      { name: "status", type: "text" },
      { name: "accepted_at", type: "date" },
      // accepted_by: uuid FK to auth -- kept as plain text per instructions
      { name: "accepted_by", type: "text" },
      { name: "created_task_id", type: "text" },
      { name: "rejected_at", type: "date" },
      // rejected_by: uuid FK to auth -- kept as plain text per instructions
      { name: "rejected_by", type: "text" },
      { name: "rejection_reason", type: "editor" },
      { name: "meeting_context", type: "editor" },
      { name: "team", type: "text" },
      { name: "stakeholder_name", type: "text" },
      { name: "value_proposition", type: "editor" },
      { name: "document_date", type: "date" },
      { name: "description", type: "editor" },
      { name: "topics", type: "json" },
      { name: "linked_project_id", type: "text" },
      { name: "source_project_id", type: "text" },
      { name: "matched_task_id", type: "text" },
      { name: "matched_candidate_id", type: "text" },
      { name: "match_confidence", type: "number" },
      { name: "match_reason", type: "editor" },
      // embedding + embedding_status -- omitted, handled by vec sidecar
      { name: "linked_project_candidate_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(taskCandidates)

  // ===== Pass 2: Collections with relations =====

  const taskComments = new Collection({
    name: "task_comments",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "task_id", type: "relation", collectionId: projectTasks.id, required: true, cascadeDelete: true, maxSelect: 1 },
      // user_id: auth ref -- skipped
      { name: "content", type: "editor" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(taskComments)

  const taskHistory = new Collection({
    name: "task_history",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "task_id", type: "relation", collectionId: projectTasks.id, required: true, cascadeDelete: true, maxSelect: 1 },
      // user_id: auth ref -- skipped
      { name: "field_name", type: "text" },
      { name: "old_value", type: "text" },
      { name: "new_value", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(taskHistory)

}, (app) => {
  const names = [
    "task_history", "task_comments",
    "task_candidates", "project_tasks",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
