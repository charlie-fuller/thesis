/// <reference path="../pb_data/types.d.ts" />

// Miscellaneous leaf collections: API logs, compass reports, department KPIs,
// engagement history, Glean connectors, knowledge gaps, theme settings, quick prompts.

migrate((app) => {

  const apiUsageLogs = new Collection({
    name: "api_usage_logs",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "endpoint", type: "text" },
      { name: "method", type: "text" },
      { name: "operation", type: "text" },
      { name: "model", type: "text" },
      { name: "tokens_used", type: "number" },
      { name: "input_tokens", type: "number" },
      { name: "output_tokens", type: "number" },
      { name: "estimated_cost", type: "number" },
      { name: "cost_usd", type: "number" },
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(apiUsageLogs)

  const compassStatusReports = new Collection({
    name: "compass_status_reports",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "report_date", type: "date", required: true },
      { name: "period_start", type: "date" },
      { name: "period_end", type: "date" },
      { name: "strategic_impact", type: "number" },
      { name: "execution_quality", type: "number" },
      { name: "relationship_building", type: "number" },
      { name: "growth_mindset", type: "number" },
      { name: "leadership_presence", type: "number" },
      { name: "overall_score", type: "number" },
      { name: "executive_summary", type: "editor" },
      { name: "strategic_impact_justification", type: "editor" },
      { name: "execution_quality_justification", type: "editor" },
      { name: "relationship_building_justification", type: "editor" },
      { name: "growth_mindset_justification", type: "editor" },
      { name: "leadership_presence_justification", type: "editor" },
      { name: "wins_referenced", type: "json" },
      { name: "areas_of_strength", type: "json" },
      { name: "growth_opportunities", type: "json" },
      { name: "recommended_actions", type: "json" },
      { name: "data_sources", type: "json" },
      { name: "improvement_actions", type: "json" },
      { name: "generation_model", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(compassStatusReports)

  const departmentKpis = new Collection({
    name: "department_kpis",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "department", type: "text", required: true },
      { name: "kpi_name", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "current_value", type: "number" },
      { name: "target_value", type: "number" },
      { name: "unit", type: "text", required: true },
      { name: "trend", type: "text" },
      { name: "trend_percentage", type: "number" },
      { name: "status", type: "text" },
      { name: "linked_objective_id", type: "text" },
      { name: "linked_goal_id", type: "text" },
      { name: "fiscal_year", type: "text" },
      { name: "sort_order", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(departmentKpis)

  const engagementLevelHistory = new Collection({
    name: "engagement_level_history",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "stakeholder_id", type: "text" },
      { name: "engagement_level", type: "text", required: true },
      { name: "previous_level", type: "text" },
      { name: "calculation_reason", type: "editor" },
      { name: "signals", type: "json" },
      { name: "calculated_at", type: "date" },
      { name: "calculation_type", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(engagementLevelHistory)

  const gleanConnectors = new Collection({
    name: "glean_connectors",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text", required: true },
      { name: "display_name", type: "text", required: true },
      { name: "connector_type", type: "text" },
      { name: "status", type: "text" },
      { name: "contentful_status", type: "text" },
      { name: "category", type: "text" },
      { name: "description", type: "editor" },
      { name: "documentation_url", type: "text" },
      { name: "developed_by", type: "text" },
      { name: "development_date", type: "date" },
      { name: "glean_tier", type: "text" },
      { name: "setup_complexity", type: "text" },
      { name: "connector_subtype", type: "text" },
      { name: "notes", type: "editor" },
      { name: "contentful_enabled_date", type: "date" },
      { name: "disco_score", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(gleanConnectors)

  const gleanConnectorGaps = new Collection({
    name: "glean_connector_gaps",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "connector_name", type: "text" },
      { name: "request_count", type: "number" },
      { name: "priority", type: "text" },
      { name: "status", type: "text" },
      { name: "use_cases", type: "editor" },
      { name: "requesters", type: "editor" },
      { name: "first_requested", type: "date" },
      { name: "last_requested", type: "date" },
    ],
  })
  app.save(gleanConnectorGaps)

  const gleanConnectorRequests = new Collection({
    name: "glean_connector_requests",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "connector_name", type: "text", required: true },
      { name: "requested_by", type: "text" },
      { name: "request_source", type: "editor" },
      { name: "use_case", type: "editor" },
      { name: "business_justification", type: "editor" },
      { name: "priority", type: "text" },
      { name: "request_count", type: "number" },
      { name: "status", type: "text" },
      { name: "connector_id", type: "text" },
      { name: "resolved_at", type: "date" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(gleanConnectorRequests)

  const gleanConnectorSummary = new Collection({
    name: "glean_connector_summary",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "contentful_status", type: "text" },
      { name: "disco_score", type: "number" },
      { name: "connector_count", type: "number" },
      { name: "connectors", type: "editor" },
    ],
  })
  app.save(gleanConnectorSummary)

  const gleanDiscoIntegrationMatrix = new Collection({
    name: "glean_disco_integration_matrix",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "name", type: "text" },
      { name: "display_name", type: "text" },
      { name: "connector_type", type: "text" },
      { name: "connector_subtype", type: "text" },
      { name: "contentful_status", type: "text" },
      { name: "contentful_enabled_date", type: "date" },
      { name: "disco_score", type: "number" },
      { name: "disco_rating", type: "text" },
    ],
  })
  app.save(gleanDiscoIntegrationMatrix)

  const knowledgeGaps = new Collection({
    name: "knowledge_gaps",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "topic", type: "text", required: true },
      { name: "question", type: "editor", required: true },
      { name: "source_agent", type: "text" },
      { name: "source_conversation_id", type: "text" },
      { name: "resolution_task_id", type: "text" },
      { name: "uncertainty_signals", type: "json" },
      { name: "gap_type", type: "text" },
      { name: "status", type: "text" },
      { name: "resolved_at", type: "date" },
      { name: "occurrence_count", type: "number" },
      { name: "priority", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(knowledgeGaps)

  const themeSettings = new Collection({
    name: "theme_settings",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "color_primary", type: "text" },
      { name: "color_primary_hover", type: "text" },
      { name: "color_secondary", type: "text" },
      { name: "color_bg_page", type: "text" },
      { name: "color_bg_card", type: "text" },
      { name: "color_bg_hover", type: "text" },
      { name: "color_text_primary", type: "text" },
      { name: "color_text_secondary", type: "text" },
      { name: "color_text_muted", type: "text" },
      { name: "color_text_on_primary", type: "text" },
      { name: "color_text_on_secondary", type: "text" },
      { name: "color_border", type: "text" },
      { name: "color_border_focus", type: "text" },
      { name: "color_success", type: "text" },
      { name: "color_warning", type: "text" },
      { name: "color_error", type: "text" },
      { name: "font_family_heading", type: "text" },
      { name: "font_family_body", type: "text" },
      { name: "font_size_base", type: "text" },
      { name: "font_weight_heading", type: "text" },
      { name: "font_weight_body", type: "text" },
      { name: "border_radius_sm", type: "text" },
      { name: "border_radius_md", type: "text" },
      { name: "border_radius_lg", type: "text" },
      { name: "panel_border_width", type: "text" },
      { name: "panel_border_color", type: "text" },
      { name: "panel_shadow_size", type: "text" },
      { name: "panel_shadow_color", type: "text" },
      { name: "header_logo_url", type: "text" },
      { name: "header_bg_color", type: "text" },
      { name: "header_text_color", type: "text" },
      { name: "header_title_color", type: "text" },
      { name: "header_nav_color", type: "text" },
      { name: "header_nav_active_color", type: "text" },
      { name: "header_font_size", type: "text" },
      { name: "header_height", type: "text" },
      { name: "page_title_font_size", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(themeSettings)

  const userQuickPrompts = new Collection({
    name: "user_quick_prompts",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "title", type: "text", required: true },
      { name: "prompt_text", type: "editor", required: true },
      { name: "display_order", type: "number" },
      { name: "is_auto_generated", type: "bool" },
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(userQuickPrompts)

}, (app) => {
  const names = [
    "user_quick_prompts",
    "theme_settings",
    "knowledge_gaps",
    "glean_disco_integration_matrix",
    "glean_connector_summary",
    "glean_connector_requests",
    "glean_connector_gaps",
    "glean_connectors",
    "engagement_level_history",
    "department_kpis",
    "compass_status_reports",
    "api_usage_logs",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
