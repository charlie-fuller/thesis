/// <reference path="../pb_data/types.d.ts" />

// Project collections: projects, portfolio_projects, roi_opportunities,
// project_candidates, project_conversations, project_documents,
// project_folders, project_stakeholder_link.
// All leaf -- cross-migration FK refs stored as plain text.

migrate((app) => {

  const projects = new Collection({
    name: "projects",
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
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(projects)

  const portfolioProjects = new Collection({
    name: "portfolio_projects",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text", required: true },
      { name: "department", type: "text" },
      { name: "owner", type: "text" },
      { name: "status", type: "text" },
      { name: "start_date", type: "date" },
      { name: "effort", type: "text" },
      { name: "investment", type: "text" },
      { name: "business_value", type: "text" },
      { name: "tools_platform", type: "editor" },
      { name: "category", type: "text" },
      { name: "description", type: "editor" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(portfolioProjects)

  const roiOpportunities = new Collection({
    name: "roi_opportunities",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "title", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "department", type: "text" },
      { name: "estimated_value_usd", type: "number" },
      { name: "estimated_hours_saved", type: "number" },
      { name: "confidence_level", type: "text" },
      { name: "status", type: "text" },
      { name: "priority", type: "text" },
      { name: "stakeholder_alignment", type: "json" },
      { name: "source_type", type: "text" },
      { name: "source_id", type: "text" },
      { name: "actual_value_usd", type: "number" },
      { name: "actual_hours_saved", type: "number" },
      { name: "completed_at", type: "date" },
      { name: "outcome_notes", type: "editor" },
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(roiOpportunities)

  const projectCandidates = new Collection({
    name: "project_candidates",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "title", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "department", type: "text" },
      { name: "source_document_id", type: "text" },
      { name: "source_document_name", type: "text" },
      { name: "source_text", type: "editor" },
      { name: "suggested_roi_potential", type: "number" },
      { name: "suggested_effort", type: "number" },
      { name: "suggested_alignment", type: "number" },
      { name: "suggested_readiness", type: "number" },
      { name: "potential_impact", type: "editor" },
      { name: "related_stakeholder_names", type: "json" },
      { name: "status", type: "text" },
      { name: "confidence", type: "text" },
      { name: "matched_project_id", type: "text" },
      { name: "match_confidence", type: "number" },
      { name: "match_reason", type: "editor" },
      { name: "accepted_at", type: "date" },
      { name: "accepted_by", type: "text" },
      { name: "created_project_id", type: "text" },
      { name: "rejected_at", type: "date" },
      { name: "rejected_by", type: "text" },
      { name: "rejection_reason", type: "editor" },
      { name: "matched_candidate_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(projectCandidates)

  const projectConversations = new Collection({
    name: "project_conversations",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "project_id", type: "text" },
      { name: "question", type: "editor" },
      { name: "response", type: "editor" },
      { name: "source_documents", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(projectConversations)

  const projectDocuments = new Collection({
    name: "project_documents",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "project_id", type: "text" },
      { name: "document_id", type: "text" },
      { name: "linked_at", type: "date" },
      { name: "linked_by", type: "text" },
      { name: "notes", type: "editor" },
    ],
  })
  app.save(projectDocuments)

  const projectFolders = new Collection({
    name: "project_folders",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "project_id", type: "text" },
      { name: "folder_path", type: "text" },
      { name: "recursive", type: "bool" },
      { name: "linked_at", type: "date" },
      { name: "linked_by", type: "text" },
    ],
  })
  app.save(projectFolders)

  const projectStakeholderLink = new Collection({
    name: "project_stakeholder_link",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "project_id", type: "text" },
      { name: "stakeholder_id", type: "text" },
      { name: "role", type: "text" },
      { name: "notes", type: "editor" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(projectStakeholderLink)

}, (app) => {
  const names = [
    "project_stakeholder_link", "project_folders", "project_documents",
    "project_conversations", "project_candidates", "roi_opportunities",
    "portfolio_projects", "projects",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
