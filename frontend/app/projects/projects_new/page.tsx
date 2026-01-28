'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  ChevronDown,
  ChevronRight,
  Plus,
  Filter,
  User,
  Building2,
  ExternalLink,
  LayoutGrid,
  List,
  Zap,
  ScatterChart
} from 'lucide-react'
import { apiGet, apiPatch, apiPost } from '@/lib/api'
import PageHeader from '@/components/PageHeader'
import ProjectDetailModal from '@/components/projects/ProjectDetailModal'
import ProjectScatterPlot from '@/components/projects/ProjectScatterPlot'

// ============================================================================
// TYPES
// ============================================================================

interface Opportunity {
  id: string
  opportunity_code: string
  title: string
  description: string | null
  department: string | null
  owner_stakeholder_id: string | null
  owner_name: string | null
  current_state: string | null
  desired_state: string | null
  roi_potential: number | null
  implementation_effort: number | null
  strategic_alignment: number | null
  stakeholder_readiness: number | null
  total_score: number
  tier: number
  status: string
  next_step: string | null
  blockers: string[]
  follow_up_questions: string[]
  roi_indicators: Record<string, unknown>
  created_at: string
  updated_at: string
  // Scoring confidence fields
  scoring_confidence?: number | null
  confidence_questions?: string[]
}

interface OpportunitiesByTier {
  tier_1: Opportunity[]
  tier_2: Opportunity[]
  tier_3: Opportunity[]
  tier_4: Opportunity[]
  summary: {
    tier_1_count: number
    tier_2_count: number
    tier_3_count: number
    tier_4_count: number
    total: number
  }
}

interface Stakeholder {
  id: string
  name: string
  department: string | null
}

// ============================================================================
// CONSTANTS
// ============================================================================

const TIER_CONFIG = {
  1: { label: 'Tier 1: Strategic Priorities', color: 'text-rose-600 dark:text-rose-400', bg: 'bg-rose-50 dark:bg-rose-900/20', border: 'border-rose-200 dark:border-rose-800', description: 'Score 17-20 - Pursue immediately' },
  2: { label: 'Tier 2: High Impact', color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-amber-200 dark:border-amber-800', description: 'Score 14-16 - Near-term priority' },
  3: { label: 'Tier 3: Medium Priority', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-blue-200 dark:border-blue-800', description: 'Score 11-13 - Queue for later' },
  4: { label: 'Tier 4: Backlog', color: 'text-slate-600 dark:text-slate-400', bg: 'bg-slate-50 dark:bg-slate-800', border: 'border-slate-200 dark:border-slate-700', description: 'Score <11 - Track but deprioritize' },
}

const STATUS_CONFIG: Record<string, { label: string; icon: typeof CheckCircle; color: string }> = {
  identified: { label: 'Identified', icon: Target, color: 'text-slate-500' },
  scoping: { label: 'Scoping', icon: Clock, color: 'text-blue-500' },
  pilot: { label: 'Pilot', icon: TrendingUp, color: 'text-amber-500' },
  scaling: { label: 'Scaling', icon: TrendingUp, color: 'text-green-500' },
  completed: { label: 'Completed', icon: CheckCircle, color: 'text-green-600' },
  blocked: { label: 'Blocked', icon: AlertCircle, color: 'text-red-500' },
}

const DEPARTMENTS = ['finance', 'legal', 'hr', 'it', 'revops', 'marketing', 'sales', 'onboarding']

// ============================================================================
// COMPONENTS
// ============================================================================

function ScoreDisplay({ label, value, max = 5 }: { label: string; value: number | null; max?: number }) {
  const score = value ?? 0
  const percentage = (score / max) * 100

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted w-8">{label}</span>
      <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${
            percentage >= 80 ? 'bg-green-500' : percentage >= 60 ? 'bg-amber-500' : 'bg-gray-400 dark:bg-gray-500'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-medium w-4 text-right text-primary">{score}</span>
    </div>
  )
}

function OpportunityCard({
  opportunity,
  onClick,
}: {
  opportunity: Opportunity
  onClick: (opportunity: Opportunity) => void
}) {
  const statusConfig = STATUS_CONFIG[opportunity.status] || STATUS_CONFIG.identified
  const StatusIcon = statusConfig.icon

  return (
    <div
      onClick={() => onClick(opportunity)}
      className="bg-card border border-default rounded-lg p-4 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-700 transition-all cursor-pointer group"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-mono font-bold text-secondary">
              {opportunity.opportunity_code}
            </span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${statusConfig.color}`}>
              <StatusIcon className="w-3 h-3" />
              {statusConfig.label}
            </span>
          </div>
          <h3 className="font-medium text-primary truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            {opportunity.title}
          </h3>
          {opportunity.owner_name && (
            <p className="text-sm text-muted flex items-center gap-1 mt-1">
              <User className="w-3 h-3" />
              {opportunity.owner_name}
            </p>
          )}
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-primary">{opportunity.total_score}</div>
          <div className="text-xs text-muted">/ 20</div>
        </div>
      </div>

      {/* Scores Preview */}
      <div className="mt-4 space-y-1">
        <ScoreDisplay label="ROI" value={opportunity.roi_potential} />
        <ScoreDisplay label="Efft" value={opportunity.implementation_effort} />
        <ScoreDisplay label="Strt" value={opportunity.strategic_alignment} />
        <ScoreDisplay label="Rdy" value={opportunity.stakeholder_readiness} />
      </div>

      {/* Click hint */}
      <div className="mt-3 flex items-center justify-center gap-1 text-xs text-muted group-hover:text-blue-500 transition-colors">
        <ExternalLink className="w-3 h-3" />
        Click for details
      </div>
    </div>
  )
}

function TierSection({
  tier,
  opportunities,
  onOpportunityClick,
}: {
  tier: 1 | 2 | 3 | 4
  opportunities: Opportunity[]
  onOpportunityClick: (opportunity: Opportunity) => void
}) {
  const [isCollapsed, setIsCollapsed] = useState(tier === 4)
  const config = TIER_CONFIG[tier]

  if (opportunities.length === 0) return null

  return (
    <div className={`border rounded-lg ${config.border} ${config.bg}`}>
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full px-4 py-3 flex items-center justify-between text-left"
      >
        <div>
          <h2 className={`font-semibold ${config.color}`}>{config.label}</h2>
          <p className="text-sm text-muted">{config.description}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-2 py-1 rounded-full text-sm font-medium ${config.bg} ${config.color}`}>
            {opportunities.length}
          </span>
          {isCollapsed ? <ChevronRight className="w-5 h-5 text-secondary" /> : <ChevronDown className="w-5 h-5 text-secondary" />}
        </div>
      </button>

      {!isCollapsed && (
        <div className="px-4 pb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {opportunities.map((opp) => (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              onClick={onOpportunityClick}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function PriorityListView({
  opportunities,
  onOpportunityClick,
}: {
  opportunities: Opportunity[]
  onOpportunityClick: (opportunity: Opportunity) => void
}) {
  // Sort by total_score descending
  const sorted = [...opportunities].sort((a, b) => b.total_score - a.total_score)

  return (
    <div className="bg-card border border-default rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-default flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-500" />
          <h2 className="font-semibold text-primary">Priority Queue</h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-muted">
            {sorted.length}
          </span>
        </div>
        <span className="text-xs text-muted">Ranked by total score</span>
      </div>

      <div className="divide-y divide-default max-h-[720px] overflow-y-auto">
        {sorted.length === 0 ? (
          <div className="px-4 py-8 text-center text-muted">
            <Target className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No opportunities match current filters</p>
          </div>
        ) : (
          sorted.map((opp, index) => {
            const statusConfig = STATUS_CONFIG[opp.status] || STATUS_CONFIG.identified
            return (
              <div
                key={opp.id}
                className="px-4 py-3 hover:bg-hover cursor-pointer transition-colors"
                onClick={() => onOpportunityClick(opp)}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-xs font-medium text-muted">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-muted">{opp.opportunity_code}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        TIER_CONFIG[opp.tier as 1|2|3|4]?.bg || ''
                      } ${TIER_CONFIG[opp.tier as 1|2|3|4]?.color || ''}`}>
                        T{opp.tier}
                      </span>
                      <span className={`text-xs ${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                      {opp.department && (
                        <span className="text-xs text-muted">{opp.department}</span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-primary truncate">
                      {opp.title}
                    </p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted">
                      <span className="flex items-center gap-1">
                        <Zap className="w-3 h-3" />
                        Score: {opp.total_score}/20
                      </span>
                      {opp.owner_name && (
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {opp.owner_name}
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted flex-shrink-0" />
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function OpportunitiesPage() {
  const router = useRouter()
  const [data, setData] = useState<OpportunitiesByTier | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Page tab (Pipeline vs Analysis)
  const [activeTab, setActiveTab] = useState<'pipeline' | 'analysis'>('pipeline')

  // View mode (within Pipeline tab)
  const [viewMode, setViewMode] = useState<'tier' | 'priority'>('tier')

  // Filters
  const [departmentFilter, setDepartmentFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')

  // Modal state
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const handleOpportunityClick = (opportunity: Opportunity) => {
    setSelectedOpportunity(opportunity)
    setModalOpen(true)
  }

  const handleModalClose = () => {
    setModalOpen(false)
    // Refresh data in case anything was changed via the modal
    loadData()
  }

  async function loadData() {
    try {
      setLoading(true)
      setError(null)

      let endpoint = '/api/projects/by-tier'
      const params = new URLSearchParams()
      if (departmentFilter) params.append('department', departmentFilter)
      if (statusFilter) params.append('status', statusFilter)
      if (params.toString()) endpoint += `?${params.toString()}`

      const result = await apiGet<OpportunitiesByTier>(endpoint)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load opportunities')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [departmentFilter, statusFilter])

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-page flex flex-col">
        <PageHeader />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-muted">Loading opportunities...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-page flex flex-col">
        <PageHeader />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600">{error}</p>
            <button
              onClick={loadData}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-page flex flex-col">
      <PageHeader />
      <div className="flex-1 max-w-7xl mx-auto px-4 py-8 w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-primary">Opportunities</h1>
            <p className="text-muted">
              {data?.summary.total || 0} opportunities tracked
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/projects/new')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Add Opportunity
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {([1, 2, 3, 4] as const).map((tier) => {
            const config = TIER_CONFIG[tier]
            const count = data?.summary[`tier_${tier}_count` as keyof typeof data.summary] || 0
            return (
              <div key={tier} className={`${config.bg} ${config.border} border rounded-lg p-4`}>
                <div className={`text-3xl font-bold ${config.color}`}>{count}</div>
                <div className="text-sm text-muted">Tier {tier}</div>
              </div>
            )
          })}
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-default mb-6">
          <button
            onClick={() => setActiveTab('pipeline')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors relative ${
              activeTab === 'pipeline'
                ? 'text-primary'
                : 'text-muted hover:text-primary'
            }`}
          >
            <LayoutGrid className="w-4 h-4" />
            Pipeline
            {activeTab === 'pipeline' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('analysis')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors relative ${
              activeTab === 'analysis'
                ? 'text-primary'
                : 'text-muted hover:text-primary'
            }`}
          >
            <ScatterChart className="w-4 h-4" />
            Analysis
            {activeTab === 'analysis' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
            )}
          </button>
        </div>

        {/* Pipeline Tab Content */}
        {activeTab === 'pipeline' && (
          <>
            {/* Filters */}
            <div className="flex items-center gap-4 mb-6">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-muted" />
                <span className="text-sm text-muted">Filter:</span>
              </div>
              <select
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
                className="px-3 py-1.5 border border-default rounded text-sm bg-card text-primary"
              >
                <option value="">All Departments</option>
                {DEPARTMENTS.map((dept) => (
                  <option key={dept} value={dept}>
                    {dept.charAt(0).toUpperCase() + dept.slice(1)}
                  </option>
                ))}
              </select>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 border border-default rounded text-sm bg-card text-primary"
              >
                <option value="">All Statuses</option>
                {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                  <option key={status} value={status}>
                    {config.label}
                  </option>
                ))}
              </select>
              {(departmentFilter || statusFilter) && (
                <button
                  onClick={() => {
                    setDepartmentFilter('')
                    setStatusFilter('')
                  }}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                >
                  Clear filters
                </button>
              )}
              {/* View toggle */}
              <div className="ml-auto flex items-center bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('tier')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'tier'
                      ? 'bg-white dark:bg-slate-700 text-primary shadow-sm'
                      : 'text-muted hover:text-primary'
                  }`}
                >
                  <LayoutGrid className="w-4 h-4" />
                  Tiers
                </button>
                <button
                  onClick={() => setViewMode('priority')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'priority'
                      ? 'bg-white dark:bg-slate-700 text-primary shadow-sm'
                      : 'text-muted hover:text-primary'
                  }`}
                >
                  <List className="w-4 h-4" />
                  Priority
                </button>
              </div>
            </div>

            {/* Tier Sections or Priority View */}
            {viewMode === 'tier' ? (
              <div className="space-y-6">
                {data && (
                  <>
                    <TierSection
                      tier={1}
                      opportunities={data.tier_1}
                      onOpportunityClick={handleOpportunityClick}
                    />
                    <TierSection
                      tier={2}
                      opportunities={data.tier_2}
                      onOpportunityClick={handleOpportunityClick}
                    />
                    <TierSection
                      tier={3}
                      opportunities={data.tier_3}
                      onOpportunityClick={handleOpportunityClick}
                    />
                    <TierSection
                      tier={4}
                      opportunities={data.tier_4}
                      onOpportunityClick={handleOpportunityClick}
                    />
                  </>
                )}
              </div>
            ) : (
              data && (
                <PriorityListView
                  opportunities={[...data.tier_1, ...data.tier_2, ...data.tier_3, ...data.tier_4]}
                  onOpportunityClick={handleOpportunityClick}
                />
              )
            )}
          </>
        )}

        {/* Analysis Tab Content */}
        {activeTab === 'analysis' && data && (
          <ProjectScatterPlot
            projects={[...data.tier_1, ...data.tier_2, ...data.tier_3, ...data.tier_4]}
            onProjectClick={handleOpportunityClick}
          />
        )}

        {/* Empty State */}
        {data && data.summary.total === 0 && activeTab === 'pipeline' && (
          <div className="text-center py-12">
            <Target className="w-12 h-12 text-muted mx-auto mb-4" />
            <h3 className="text-lg font-medium text-primary mb-2">No opportunities yet</h3>
            <p className="text-muted mb-4">Start tracking AI implementation opportunities</p>
            <button
              onClick={() => router.push('/projects/new')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add First Opportunity
            </button>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedOpportunity && (
        <ProjectDetailModal
          project={selectedOpportunity}
          open={modalOpen}
          onClose={handleModalClose}
        />
      )}
    </div>
  )
}
