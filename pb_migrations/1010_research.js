/// <reference path="../pb_data/types.d.ts" />

// Research collections: research_tasks, research_sources, research_schedule.
// All leaf -- single pass, no relations.

migrate((app) => {
  const researchTasks = new Collection({
    name: "research_tasks",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "topic", type: "text", required: true },
      { name: "query", type: "editor", required: true },
      { name: "focus_area", type: "text" },
      { name: "research_type", type: "text" },
      { name: "status", type: "text" },
      { name: "priority", type: "number" },
      { name: "context", type: "json" },
      { name: "result_content", type: "editor" },
      { name: "result_document_id", type: "text" },
      { name: "result_summary", type: "editor" },
      { name: "web_sources", type: "json" },
      { name: "started_at", type: "date" },
      { name: "completed_at", type: "date" },
      { name: "error_message", type: "editor" },
      { name: "retry_count", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(researchTasks)

  const researchSources = new Collection({
    name: "research_sources",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "domain", type: "text", required: true },
      { name: "name", type: "text" },
      { name: "credibility_tier", type: "number" },
      { name: "source_type", type: "text" },
      { name: "topics", type: "json" },
      { name: "times_cited", type: "number" },
      { name: "last_cited_at", type: "date" },
      { name: "is_blocked", type: "bool" },
      { name: "notes", type: "editor" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(researchSources)

  const researchSchedule = new Collection({
    name: "research_schedule",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "day_of_week", type: "number" },
      { name: "hour_utc", type: "number" },
      { name: "focus_area", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "query_template", type: "editor" },
      { name: "is_active", type: "bool" },
      { name: "priority", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(researchSchedule)

}, (app) => {
  const names = [
    "research_schedule", "research_sources", "research_tasks",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
