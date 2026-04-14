/// <reference path="../pb_data/types.d.ts" />

// Stakeholder extras: candidates, insights, metrics.
// All leaf -- cross-migration stakeholder_id refs stored as plain text.

migrate((app) => {
  const stakeholderCandidates = new Collection({
    name: "stakeholder_candidates",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text", required: true },
      { name: "role", type: "text" },
      { name: "department", type: "text" },
      { name: "organization", type: "text" },
      { name: "email", type: "text" },
      { name: "key_concerns", type: "json" },
      { name: "interests", type: "json" },
      { name: "initial_sentiment", type: "text" },
      { name: "influence_level", type: "text" },
      { name: "source_document_id", type: "text" },
      { name: "source_document_name", type: "text" },
      { name: "source_text", type: "editor" },
      { name: "extraction_context", type: "editor" },
      { name: "related_project_ids", type: "json" },
      { name: "related_task_ids", type: "json" },
      { name: "status", type: "text" },
      { name: "confidence", type: "text" },
      { name: "potential_match_stakeholder_id", type: "text" },
      { name: "match_confidence", type: "number" },
      { name: "accepted_at", type: "date" },
      { name: "accepted_by", type: "text" },
      { name: "created_stakeholder_id", type: "text" },
      { name: "merged_into_stakeholder_id", type: "text" },
      { name: "rejection_reason", type: "editor" },
      { name: "matched_candidate_id", type: "text" },
      { name: "match_reason", type: "editor" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(stakeholderCandidates)

  const stakeholderInsights = new Collection({
    name: "stakeholder_insights",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "stakeholder_id", type: "text" },
      { name: "source_document_id", type: "text" },
      { name: "meeting_transcript_id", type: "text" },
      { name: "insight_type", type: "text", required: true },
      { name: "content", type: "editor", required: true },
      { name: "confidence", type: "number" },
      { name: "extracted_quote", type: "editor" },
      { name: "context", type: "editor" },
      { name: "is_resolved", type: "bool" },
      { name: "resolved_at", type: "date" },
      { name: "resolution_notes", type: "editor" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(stakeholderInsights)

  const stakeholderMetrics = new Collection({
    name: "stakeholder_metrics",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "stakeholder_id", type: "text" },
      { name: "metric_name", type: "text", required: true },
      { name: "metric_category", type: "text" },
      { name: "unit", type: "text" },
      { name: "current_value", type: "text" },
      { name: "target_value", type: "text" },
      { name: "validation_status", type: "text" },
      { name: "source", type: "text" },
      { name: "source_date", type: "date" },
      { name: "notes", type: "editor" },
      { name: "questions_to_confirm", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(stakeholderMetrics)

}, (app) => {
  const names = [
    "stakeholder_metrics", "stakeholder_insights", "stakeholder_candidates",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
