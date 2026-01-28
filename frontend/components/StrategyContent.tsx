'use client'

/**
 * Strategy Content Component
 *
 * Displays company objectives/goals and department KPIs.
 * Used as a tab within the Intelligence page.
 */

import { useState } from 'react'
import {
  Target,
  TrendingUp,
  TrendingDown,
  Minus,
  Building2,
  ChevronDown,
  ChevronRight,
  BarChart3,
  Users,
  Sparkles,
} from 'lucide-react'

// ============================================================================
// TYPES
// ============================================================================

interface CompanyObjective {
  id: string
  title: string
  description: string
  icon: string
  target_metric: string
  current_value: number | null
  target_value: number
  unit: string
  progress_percentage: number
  status: 'on_track' | 'at_risk' | 'behind' | 'achieved'
  priority: number
  updated_at: string
}

interface DepartmentKPI {
  id: string
  department: string
  kpi_name: string
  description: string
  current_value: number | null
  target_value: number
  unit: string
  trend: 'up' | 'down' | 'flat'
  trend_percentage: number
  status: 'green' | 'yellow' | 'red'
  linked_objective_id: string | null
  updated_at: string
}

// ============================================================================
// COMPANY DATA - FY26 Company Goals (Current Measurement)
// ============================================================================

const FY26_OBJECTIVES: CompanyObjective[] = [
  {
    id: '1',
    title: 'Market Positioning',
    description: 'Re-establish Contentful as a thought leader and disruptor in the broader DXP category, with a compelling near-term value proposition, and an expansive vision around content operations that co-opts the GenAI value proposition.',
    icon: 'Target',
    target_metric: 'DXP category leadership',
    current_value: null,
    target_value: 100,
    unit: '%',
    progress_percentage: 65,
    status: 'on_track',
    priority: 1,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '2',
    title: 'Sales Productivity',
    description: 'Accelerate sales productivity to approach industry benchmarks, exceed pipeline and bookings targets, and support increased S&M investment in H2 to re-accelerate revenue growth in FY27 and FY28.',
    icon: 'TrendingUp',
    target_metric: 'Pipeline vs target',
    current_value: 113,
    target_value: 100,
    unit: '%',
    progress_percentage: 100,
    status: 'achieved',
    priority: 2,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '3',
    title: 'Product Innovation',
    description: 'Accelerate velocity of new product and feature introductions that reinforce platform/ecosystem leadership, provide differentiated expansion into DXP category, and capture net new spend categories through GenAI capabilities.',
    icon: 'Sparkles',
    target_metric: 'EXO/GenAI milestones',
    current_value: 5,
    target_value: 8,
    unit: 'milestones',
    progress_percentage: 63,
    status: 'on_track',
    priority: 3,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '4',
    title: 'Culture',
    description: 'Create a winning culture based on transparency, empowerment, risk taking and performance. Values: Relentless Customer Focus, Own It, Be Bold, Win Together.',
    icon: 'Users',
    target_metric: 'Employee retention',
    current_value: 92,
    target_value: 98,
    unit: '%',
    progress_percentage: 67,
    status: 'on_track',
    priority: 4,
    updated_at: '2026-01-22T10:00:00Z',
  },
]

// ============================================================================
// COMPANY DATA - FY27 Company Goals (Forward-Looking / Notional)
// ============================================================================

const FY27_OBJECTIVES: CompanyObjective[] = [
  {
    id: '1',
    title: 'Market Leadership',
    description: 'Transform perceptions of Contentful from a technical CMS tool for developers into a strategic solution partner for CMOs and CTOs. Create a differentiated narrative around our product vision that capitalizes on emerging AI disruptions and creates an aura of industry leadership.',
    icon: 'Target',
    target_metric: 'CMO/CTO perception shift',
    current_value: null,
    target_value: 100,
    unit: '%',
    progress_percentage: 0,
    status: 'on_track',
    priority: 1,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '2',
    title: 'Cost-Efficient GTM Growth',
    description: 'Build upon FY26 productivity improvements to exceed all FY top line targets, achieve a cost-to-book ratio under 2.0, and improve FY26 gross retention metrics.',
    icon: 'TrendingUp',
    target_metric: 'Cost-to-book ratio',
    current_value: null,
    target_value: 2.0,
    unit: 'ratio',
    progress_percentage: 0,
    status: 'on_track',
    priority: 2,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '3',
    title: 'Product Innovation',
    description: 'Introduce new platform and AI-powered experience orchestration capabilities that leapfrog the market. Democratize the value of experimentation, p13n, and content analytics. Develop a clear product strategy behind the agentic web.',
    icon: 'Sparkles',
    target_metric: 'EXO/Agentic Web milestones',
    current_value: null,
    target_value: 8,
    unit: 'milestones',
    progress_percentage: 0,
    status: 'on_track',
    priority: 3,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '4',
    title: 'Culture',
    description: 'Create a winning culture based on transparency, empowerment, risk taking and performance. Target: 98% employee retention.',
    icon: 'Users',
    target_metric: 'Employee retention',
    current_value: null,
    target_value: 98,
    unit: '%',
    progress_percentage: 0,
    status: 'on_track',
    priority: 4,
    updated_at: '2026-01-22T10:00:00Z',
  },
]

const MOCK_KPIS: DepartmentKPI[] = [
  // Legal
  {
    id: 'legal-1',
    department: 'Legal',
    kpi_name: 'Contract Review Cycle Time',
    description: 'Days from contract submission to completion (target: 90% reduction).',
    current_value: 19,
    target_value: 2,
    unit: 'days',
    trend: 'down',
    trend_percentage: 10,
    status: 'red',
    linked_objective_id: '2',
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'legal-2',
    department: 'Legal',
    kpi_name: 'Attorney Strategic Work Time',
    description: 'Time on high-value strategic work vs. admin.',
    current_value: 20,
    target_value: 40,
    unit: '%',
    trend: 'up',
    trend_percentage: 5,
    status: 'yellow',
    linked_objective_id: '3',
    updated_at: '2026-01-22T10:00:00Z',
  },
  // Finance
  {
    id: 'fin-1',
    department: 'Finance',
    kpi_name: 'Monthly Close Cycle',
    description: 'Days to complete monthly financial close.',
    current_value: 15,
    target_value: 8,
    unit: 'days',
    trend: 'down',
    trend_percentage: 10,
    status: 'yellow',
    linked_objective_id: '2',
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'fin-2',
    department: 'Finance',
    kpi_name: 'Invoice Processing Time',
    description: 'Minutes per invoice via AI OCR.',
    current_value: 15,
    target_value: 3,
    unit: 'min/invoice',
    trend: 'down',
    trend_percentage: 15,
    status: 'yellow',
    linked_objective_id: '3',
    updated_at: '2026-01-22T10:00:00Z',
  },
  // HR/People
  {
    id: 'hr-1',
    department: 'HR/People',
    kpi_name: 'Employee Retention Rate',
    description: 'Annual employee retention (target: 98%).',
    current_value: 92,
    target_value: 98,
    unit: '%',
    trend: 'up',
    trend_percentage: 2,
    status: 'yellow',
    linked_objective_id: '4',
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'hr-2',
    department: 'HR/People',
    kpi_name: 'HR Ticket Deflection',
    description: 'Questions resolved via AI chatbot.',
    current_value: 10,
    target_value: 40,
    unit: '%',
    trend: 'up',
    trend_percentage: 5,
    status: 'yellow',
    linked_objective_id: '3',
    updated_at: '2026-01-22T10:00:00Z',
  },
  // IT
  {
    id: 'it-1',
    department: 'IT',
    kpi_name: 'AI Agent Success Rate',
    description: 'Built agents reaching production.',
    current_value: 4,
    target_value: 80,
    unit: '%',
    trend: 'up',
    trend_percentage: 5,
    status: 'red',
    linked_objective_id: '3',
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'it-2',
    department: 'IT',
    kpi_name: 'Production Agents',
    description: 'AI agents deployed to production.',
    current_value: 15,
    target_value: 50,
    unit: 'agents',
    trend: 'up',
    trend_percentage: 10,
    status: 'yellow',
    linked_objective_id: '3',
    updated_at: '2026-01-22T10:00:00Z',
  },
  // Revenue Ops
  {
    id: 'revops-1',
    department: 'Revenue Ops',
    kpi_name: 'Ticket Escalation Rate',
    description: 'Sales questions requiring human escalation.',
    current_value: 75,
    target_value: 25,
    unit: '%',
    trend: 'down',
    trend_percentage: 5,
    status: 'red',
    linked_objective_id: '2',
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'revops-2',
    department: 'Revenue Ops',
    kpi_name: 'MEDDIC Field Completion',
    description: 'Opportunities with complete MEDDIC data.',
    current_value: 60,
    target_value: 90,
    unit: '%',
    trend: 'up',
    trend_percentage: 10,
    status: 'yellow',
    linked_objective_id: '1',
    updated_at: '2026-01-22T10:00:00Z',
  },
]

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Sparkles,
  Users,
  Target,
  TrendingUp,
}

function ObjectiveIcon({ name, className }: { name: string; className?: string }) {
  const Icon = ICON_MAP[name] || Target
  return <Icon className={className} />
}

function StatusBadge({ status }: { status: CompanyObjective['status'] }) {
  const config = {
    on_track: { label: 'On Track', color: 'var(--color-success)' },
    at_risk: { label: 'At Risk', color: 'var(--color-warning)' },
    behind: { label: 'Behind', color: 'var(--color-error)' },
    achieved: { label: 'Achieved', color: 'var(--color-primary)' },
  }
  const { label, color } = config[status]
  return (
    <span
      className="px-2 py-0.5 rounded-full text-xs font-medium border"
      style={{ borderColor: color, color: color }}
    >
      {label}
    </span>
  )
}

function KPIStatusDot({ status }: { status: DepartmentKPI['status'] }) {
  const colors = {
    green: 'var(--color-success)',
    yellow: 'var(--color-warning)',
    red: 'var(--color-error)',
  }
  return <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: colors[status] }} />
}

function TrendIndicator({ trend, percentage }: { trend: DepartmentKPI['trend']; percentage: number }) {
  if (trend === 'up') {
    return (
      <span className="flex items-center gap-0.5 text-xs" style={{ color: 'var(--color-success)' }}>
        <TrendingUp className="w-3 h-3" />
        {percentage}%
      </span>
    )
  }
  if (trend === 'down') {
    return (
      <span className="flex items-center gap-0.5 text-xs" style={{ color: 'var(--color-error)' }}>
        <TrendingDown className="w-3 h-3" />
        {percentage}%
      </span>
    )
  }
  return (
    <span className="flex items-center gap-0.5 text-muted text-xs">
      <Minus className="w-3 h-3" />
      {percentage}%
    </span>
  )
}

function ProgressBar({ percentage, status }: { percentage: number; status: CompanyObjective['status'] }) {
  const colors = {
    on_track: 'var(--color-success)',
    at_risk: 'var(--color-warning)',
    behind: 'var(--color-error)',
    achieved: 'var(--color-primary)',
  }
  return (
    <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-bg-hover)' }}>
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${Math.min(percentage, 100)}%`, backgroundColor: colors[status] }}
      />
    </div>
  )
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function StrategyContent() {
  const [mainTab, setMainTab] = useState<'company' | 'department'>('company')
  const [fiscalYearTab, setFiscalYearTab] = useState<'fy26' | 'fy27'>('fy26')
  const [kpis] = useState<DepartmentKPI[]>(MOCK_KPIS)
  const [expandedDepartments, setExpandedDepartments] = useState<Set<string>>(new Set())

  // Select objectives based on fiscal year tab
  const objectives = fiscalYearTab === 'fy26' ? FY26_OBJECTIVES : FY27_OBJECTIVES

  // Group KPIs by department
  const kpisByDepartment = kpis.reduce((acc, kpi) => {
    if (!acc[kpi.department]) {
      acc[kpi.department] = []
    }
    acc[kpi.department].push(kpi)
    return acc
  }, {} as Record<string, DepartmentKPI[]>)

  const departments = Object.keys(kpisByDepartment).sort()

  const toggleDepartment = (dept: string) => {
    setExpandedDepartments(prev => {
      const next = new Set(prev)
      if (next.has(dept)) {
        next.delete(dept)
      } else {
        next.add(dept)
      }
      return next
    })
  }

  // Calculate summary stats
  const objectiveSummary = {
    total: objectives.length,
    onTrack: objectives.filter(o => o.status === 'on_track').length,
    atRisk: objectives.filter(o => o.status === 'at_risk').length,
    behind: objectives.filter(o => o.status === 'behind').length,
    achieved: objectives.filter(o => o.status === 'achieved').length,
    avgProgress: Math.round(objectives.reduce((sum, o) => sum + o.progress_percentage, 0) / objectives.length),
  }

  const kpiSummary = {
    total: kpis.length,
    green: kpis.filter(k => k.status === 'green').length,
    yellow: kpis.filter(k => k.status === 'yellow').length,
    red: kpis.filter(k => k.status === 'red').length,
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <p className="text-muted">
          Company objectives and G&A department KPIs. Use these to align AI opportunities with
          strategic priorities and demonstrate impact in career reviews with Compass.
        </p>
      </div>

      {/* Main Tabs */}
      <div className="flex items-center gap-2 mb-6 border-b border-default">
        <button
          onClick={() => setMainTab('company')}
          className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
            mainTab === 'company'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted hover:text-secondary'
          }`}
        >
          <Target className="w-4 h-4 inline-block mr-2" />
          Company Objectives
        </button>
        <button
          onClick={() => setMainTab('department')}
          className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
            mainTab === 'department'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted hover:text-secondary'
          }`}
        >
          <BarChart3 className="w-4 h-4 inline-block mr-2" />
          Department KPIs
        </button>
      </div>

      {/* Company Objectives Tab */}
      {mainTab === 'company' && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">
                  {fiscalYearTab === 'fy26' ? 'FY26 Progress' : 'FY27 Targets'}
                </span>
                <Target className="w-5 h-5 text-blue-500" />
              </div>
              <div className="mt-2">
                {fiscalYearTab === 'fy26' ? (
                  <>
                    <span className="text-2xl font-bold text-primary">{objectiveSummary.avgProgress}%</span>
                    <span className="text-sm text-muted ml-2">avg completion</span>
                  </>
                ) : (
                  <>
                    <span className="text-2xl font-bold text-primary">{objectives.length}</span>
                    <span className="text-sm text-muted ml-2">strategic goals</span>
                  </>
                )}
              </div>
              <div className="mt-2 flex gap-2 text-xs">
                {fiscalYearTab === 'fy26' ? (
                  <>
                    <span style={{ color: 'var(--color-success)' }}>{objectiveSummary.onTrack} on track</span>
                    <span style={{ color: 'var(--color-warning)' }}>{objectiveSummary.atRisk} at risk</span>
                    <span style={{ color: 'var(--color-error)' }}>{objectiveSummary.behind} behind</span>
                  </>
                ) : (
                  <span className="text-secondary">Planning targets for next fiscal year</span>
                )}
              </div>
            </div>

            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">Strategic Goals</span>
                <Sparkles className="w-5 h-5 text-amber-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">{objectives.length}</span>
                <span className="text-sm text-muted ml-2">objectives</span>
              </div>
              <div className="mt-2 text-xs text-muted">
                {fiscalYearTab === 'fy26' ? 'Current fiscal year' : 'Next fiscal year planning'}
              </div>
            </div>

            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">Achieved</span>
                <TrendingUp className="w-5 h-5 text-green-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">{objectiveSummary.achieved}</span>
                <span className="text-sm text-muted ml-2">/ {objectives.length}</span>
              </div>
              <div className="mt-2 text-xs text-muted">
                Goals completed
              </div>
            </div>
          </div>

          {/* Fiscal Year Tabs */}
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => setFiscalYearTab('fy26')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                fiscalYearTab === 'fy26'
                  ? 'bg-primary text-white'
                  : 'bg-card border border-default text-secondary hover:bg-hover'
              }`}
            >
              FY26 Goals
              <span className="ml-1.5 text-xs opacity-75">(Current)</span>
            </button>
            <button
              onClick={() => setFiscalYearTab('fy27')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                fiscalYearTab === 'fy27'
                  ? 'bg-primary text-white'
                  : 'bg-card border border-default text-secondary hover:bg-hover'
              }`}
            >
              FY27 Goals
              <span className="ml-1.5 text-xs opacity-75">(Notional)</span>
            </button>
            {fiscalYearTab === 'fy27' && (
              <span
                className="ml-2 text-xs px-2 py-1 rounded border"
                style={{ borderColor: 'var(--color-warning)', color: 'var(--color-warning)' }}
              >
                Forward-looking targets - measure progress against FY26
              </span>
            )}
          </div>

          <div className="space-y-4">
            {objectives
              .sort((a, b) => a.priority - b.priority)
              .map((objective) => (
                <div
                  key={objective.id}
                  className="bg-card border border-default rounded-lg p-5 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-hover flex items-center justify-center">
                      <ObjectiveIcon name={objective.icon} className="w-6 h-6 icon-primary" />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h3 className="text-base font-semibold text-primary">
                            {objective.priority}. {objective.title}
                          </h3>
                          <p className="text-sm text-muted mt-1">{objective.description}</p>
                        </div>
                        {fiscalYearTab === 'fy26' ? (
                          <StatusBadge status={objective.status} />
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-hover text-secondary">
                            Planning
                          </span>
                        )}
                      </div>

                      {/* Progress */}
                      <div className="mt-4">
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-muted">{objective.target_metric}</span>
                          <span className="font-medium text-primary">
                            {fiscalYearTab === 'fy26' ? (
                              <>
                                {objective.current_value !== null ? objective.current_value : '—'}{objective.unit} / {objective.target_value}{objective.unit}
                              </>
                            ) : (
                              <>Target: {objective.target_value}{objective.unit}</>
                            )}
                          </span>
                        </div>
                        {fiscalYearTab === 'fy26' ? (
                          <>
                            <ProgressBar percentage={objective.progress_percentage} status={objective.status} />
                            <div className="flex items-center justify-between mt-1">
                              <span className="text-xs text-muted">{objective.progress_percentage}% complete</span>
                              <span className="text-xs text-muted">
                                Updated {new Date(objective.updated_at).toLocaleDateString()}
                              </span>
                            </div>
                          </>
                        ) : (
                          <div className="h-2 bg-hover rounded-full overflow-hidden">
                            <div className="h-full w-0 rounded-full border-default" />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </>
      )}

      {/* Department KPIs Tab */}
      {mainTab === 'department' && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">KPI Health</span>
                <BarChart3 className="w-5 h-5 text-green-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">{kpiSummary.total}</span>
                <span className="text-sm text-muted ml-2">tracked KPIs</span>
              </div>
              <div className="mt-2 flex gap-2 text-xs">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-success)' }} />
                  {kpiSummary.green} green
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-warning)' }} />
                  {kpiSummary.yellow} yellow
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-error)' }} />
                  {kpiSummary.red} red
                </span>
              </div>
            </div>

            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">Departments</span>
                <Building2 className="w-5 h-5 text-purple-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">{departments.length}</span>
                <span className="text-sm text-muted ml-2">with AI KPIs</span>
              </div>
              <div className="mt-2 text-xs text-muted">
                {departments.slice(0, 3).join(', ')}{departments.length > 3 ? ` +${departments.length - 3} more` : ''}
              </div>
            </div>

            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">At Risk</span>
                <TrendingDown className="w-5 h-5 text-red-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">{kpiSummary.red}</span>
                <span className="text-sm text-muted ml-2">KPIs need attention</span>
              </div>
              <div className="mt-2 text-xs text-muted">
                Below target metrics
              </div>
            </div>
          </div>

          <div className="space-y-3">
            {departments.map((department) => {
              const deptKpis = kpisByDepartment[department]
              const isExpanded = expandedDepartments.has(department)
              const deptHealth = {
                green: deptKpis.filter(k => k.status === 'green').length,
                yellow: deptKpis.filter(k => k.status === 'yellow').length,
                red: deptKpis.filter(k => k.status === 'red').length,
              }

              return (
                <div key={department} className="bg-card border border-default rounded-lg overflow-hidden">
                  {/* Department Header */}
                  <button
                    onClick={() => toggleDepartment(department)}
                    className="w-full flex items-center justify-between p-4 hover:bg-hover transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {isExpanded ? (
                        <ChevronDown className="w-5 h-5 text-muted" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-muted" />
                      )}
                      <Building2 className="w-5 h-5 text-purple-500" />
                      <span className="font-medium text-primary">{department}</span>
                      <span className="text-sm text-muted">({deptKpis.length} KPIs)</span>
                    </div>
                    <div className="flex items-center gap-3">
                      {deptHealth.green > 0 && (
                        <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-success)' }}>
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-success)' }} />
                          {deptHealth.green}
                        </span>
                      )}
                      {deptHealth.yellow > 0 && (
                        <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-warning)' }}>
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-warning)' }} />
                          {deptHealth.yellow}
                        </span>
                      )}
                      {deptHealth.red > 0 && (
                        <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-error)' }}>
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-error)' }} />
                          {deptHealth.red}
                        </span>
                      )}
                    </div>
                  </button>

                  {/* KPI List */}
                  {isExpanded && (
                    <div className="border-t border-default">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-hover/50 text-xs text-muted uppercase">
                            <th className="text-left px-4 py-2 font-medium">KPI</th>
                            <th className="text-right px-4 py-2 font-medium">Current</th>
                            <th className="text-right px-4 py-2 font-medium">Target</th>
                            <th className="text-center px-4 py-2 font-medium">Trend</th>
                            <th className="text-center px-4 py-2 font-medium">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {deptKpis.map((kpi) => (
                            <tr key={kpi.id} className="border-t border-default hover:bg-hover/30">
                              <td className="px-4 py-3">
                                <div>
                                  <span className="text-sm font-medium text-primary">{kpi.kpi_name}</span>
                                  <p className="text-xs text-muted mt-0.5">{kpi.description}</p>
                                </div>
                              </td>
                              <td className="text-right px-4 py-3">
                                <span className="text-sm font-medium text-primary">
                                  {kpi.current_value !== null ? kpi.current_value : '—'} {kpi.unit}
                                </span>
                              </td>
                              <td className="text-right px-4 py-3">
                                <span className="text-sm text-muted">
                                  {kpi.target_value} {kpi.unit}
                                </span>
                              </td>
                              <td className="text-center px-4 py-3">
                                <TrendIndicator trend={kpi.trend} percentage={kpi.trend_percentage} />
                              </td>
                              <td className="text-center px-4 py-3">
                                <div className="flex justify-center">
                                  <KPIStatusDot status={kpi.status} />
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* Info Banner */}
      <div className="mt-8 p-4 bg-hover border border-default rounded-lg">
        <div className="flex items-start gap-3">
          <Target className="w-5 h-5 icon-primary flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-primary">
              Aligning Opportunities with Strategy
            </h3>
            <p className="text-sm text-secondary mt-1">
              When evaluating AI opportunities, consider how they contribute to these company objectives
              and department KPIs. Opportunities that directly impact multiple strategic goals should
              receive higher priority scores.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
