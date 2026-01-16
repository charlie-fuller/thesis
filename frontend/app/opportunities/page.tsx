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
  Building2
} from 'lucide-react'
import { apiGet, apiPatch, apiPost } from '@/lib/api'
import PageHeader from '@/components/PageHeader'

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
  1: { label: 'Tier 1: Strategic Priorities', color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-200', description: 'Score 17-20 - Pursue immediately' },
  2: { label: 'Tier 2: High Impact', color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', description: 'Score 14-16 - Near-term priority' },
  3: { label: 'Tier 3: Medium Priority', color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200', description: 'Score 11-13 - Queue for later' },
  4: { label: 'Tier 4: Backlog', color: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-200', description: 'Score <11 - Track but deprioritize' },
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
      <span className="text-xs text-slate-500 w-8">{label}</span>
      <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${
            percentage >= 80 ? 'bg-green-500' : percentage >= 60 ? 'bg-amber-500' : 'bg-slate-400'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-medium w-4 text-right">{score}</span>
    </div>
  )
}

function OpportunityCard({
  opportunity,
  onStatusChange,
  onScoreUpdate,
}: {
  opportunity: Opportunity
  onStatusChange: (id: string, status: string) => void
  onScoreUpdate: (id: string, scores: Record<string, number>) => void
}) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isEditingScores, setIsEditingScores] = useState(false)
  const [editScores, setEditScores] = useState({
    roi_potential: opportunity.roi_potential ?? 3,
    implementation_effort: opportunity.implementation_effort ?? 3,
    strategic_alignment: opportunity.strategic_alignment ?? 3,
    stakeholder_readiness: opportunity.stakeholder_readiness ?? 3,
  })

  const statusConfig = STATUS_CONFIG[opportunity.status] || STATUS_CONFIG.identified
  const StatusIcon = statusConfig.icon

  const handleScoreSave = () => {
    onScoreUpdate(opportunity.id, editScores)
    setIsEditingScores(false)
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-mono font-bold text-slate-700">
              {opportunity.opportunity_code}
            </span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${statusConfig.color}`}>
              <StatusIcon className="w-3 h-3" />
              {statusConfig.label}
            </span>
          </div>
          <h3 className="font-medium text-slate-900 truncate">{opportunity.title}</h3>
          {opportunity.owner_name && (
            <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
              <User className="w-3 h-3" />
              {opportunity.owner_name}
            </p>
          )}
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-slate-900">{opportunity.total_score}</div>
          <div className="text-xs text-slate-500">/ 20</div>
        </div>
      </div>

      {/* Scores Preview */}
      <div className="mt-4 space-y-1">
        <ScoreDisplay label="ROI" value={opportunity.roi_potential} />
        <ScoreDisplay label="Efft" value={opportunity.implementation_effort} />
        <ScoreDisplay label="Strt" value={opportunity.strategic_alignment} />
        <ScoreDisplay label="Rdy" value={opportunity.stakeholder_readiness} />
      </div>

      {/* Expand/Collapse */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="mt-3 w-full flex items-center justify-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        {isExpanded ? 'Less' : 'More'}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-slate-200 space-y-4">
          {/* Description */}
          {opportunity.description && (
            <div>
              <h4 className="text-xs font-medium text-slate-500 uppercase mb-1">Description</h4>
              <p className="text-sm text-slate-700">{opportunity.description}</p>
            </div>
          )}

          {/* Current/Desired State */}
          {(opportunity.current_state || opportunity.desired_state) && (
            <div className="grid grid-cols-2 gap-4">
              {opportunity.current_state && (
                <div>
                  <h4 className="text-xs font-medium text-slate-500 uppercase mb-1">Current State</h4>
                  <p className="text-sm text-slate-700">{opportunity.current_state}</p>
                </div>
              )}
              {opportunity.desired_state && (
                <div>
                  <h4 className="text-xs font-medium text-slate-500 uppercase mb-1">Desired State</h4>
                  <p className="text-sm text-slate-700">{opportunity.desired_state}</p>
                </div>
              )}
            </div>
          )}

          {/* Next Step */}
          {opportunity.next_step && (
            <div>
              <h4 className="text-xs font-medium text-slate-500 uppercase mb-1">Next Step</h4>
              <p className="text-sm text-slate-700">{opportunity.next_step}</p>
            </div>
          )}

          {/* Blockers */}
          {opportunity.blockers.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-red-500 uppercase mb-1">Blockers</h4>
              <ul className="text-sm text-slate-700 list-disc list-inside">
                {opportunity.blockers.map((blocker, i) => (
                  <li key={i}>{blocker}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Score Editor */}
          {isEditingScores ? (
            <div className="bg-slate-50 rounded-lg p-3 space-y-3">
              <h4 className="text-xs font-medium text-slate-500 uppercase">Edit Scores (1-5)</h4>
              {(['roi_potential', 'implementation_effort', 'strategic_alignment', 'stakeholder_readiness'] as const).map((key) => (
                <div key={key} className="flex items-center gap-2">
                  <label className="text-sm text-slate-600 w-32 capitalize">{key.replace(/_/g, ' ')}</label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={editScores[key]}
                    onChange={(e) => setEditScores({ ...editScores, [key]: parseInt(e.target.value) })}
                    className="flex-1"
                  />
                  <span className="w-6 text-center font-medium">{editScores[key]}</span>
                </div>
              ))}
              <div className="flex gap-2 mt-2">
                <button
                  onClick={handleScoreSave}
                  className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                >
                  Save
                </button>
                <button
                  onClick={() => setIsEditingScores(false)}
                  className="px-3 py-1 bg-slate-200 text-slate-700 text-sm rounded hover:bg-slate-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setIsEditingScores(true)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              Edit Scores
            </button>
          )}

          {/* Status Change */}
          <div>
            <h4 className="text-xs font-medium text-slate-500 uppercase mb-2">Change Status</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                <button
                  key={status}
                  onClick={() => onStatusChange(opportunity.id, status)}
                  disabled={opportunity.status === status}
                  className={`px-2 py-1 text-xs rounded border ${
                    opportunity.status === status
                      ? 'bg-slate-100 border-slate-300 text-slate-400 cursor-not-allowed'
                      : 'border-slate-200 hover:border-slate-400 text-slate-600'
                  }`}
                >
                  {config.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TierSection({
  tier,
  opportunities,
  onStatusChange,
  onScoreUpdate,
}: {
  tier: 1 | 2 | 3 | 4
  opportunities: Opportunity[]
  onStatusChange: (id: string, status: string) => void
  onScoreUpdate: (id: string, scores: Record<string, number>) => void
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
          <p className="text-sm text-slate-500">{config.description}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-2 py-1 rounded-full text-sm font-medium ${config.bg} ${config.color}`}>
            {opportunities.length}
          </span>
          {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </div>
      </button>

      {!isCollapsed && (
        <div className="px-4 pb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {opportunities.map((opp) => (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              onStatusChange={onStatusChange}
              onScoreUpdate={onScoreUpdate}
            />
          ))}
        </div>
      )}
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

  // Filters
  const [departmentFilter, setDepartmentFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')

  async function loadData() {
    try {
      setLoading(true)
      setError(null)

      let endpoint = '/api/opportunities/by-tier'
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

  async function handleStatusChange(id: string, status: string) {
    try {
      await apiPatch(`/api/opportunities/${id}/status?status=${status}`)
      loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update status')
    }
  }

  async function handleScoreUpdate(id: string, scores: Record<string, number>) {
    try {
      await apiPatch(`/api/opportunities/${id}/scores`, scores)
      loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update scores')
    }
  }

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
            <h1 className="text-2xl font-bold text-primary">AI Opportunities</h1>
            <p className="text-muted">
              {data?.summary.total || 0} opportunities tracked
            </p>
          </div>
          <button
            onClick={() => router.push('/opportunities/new')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Add Opportunity
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {([1, 2, 3, 4] as const).map((tier) => {
            const config = TIER_CONFIG[tier]
            const count = data?.summary[`tier_${tier}_count` as keyof typeof data.summary] || 0
            return (
              <div key={tier} className={`${config.bg} ${config.border} border rounded-lg p-4`}>
                <div className={`text-3xl font-bold ${config.color}`}>{count}</div>
                <div className="text-sm text-slate-600">Tier {tier}</div>
              </div>
            )
          })}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-500">Filter:</span>
          </div>
          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="px-3 py-1.5 border border-slate-300 rounded text-sm"
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
            className="px-3 py-1.5 border border-slate-300 rounded text-sm"
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
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* Tier Sections */}
        <div className="space-y-6">
          {data && (
            <>
              <TierSection
                tier={1}
                opportunities={data.tier_1}
                onStatusChange={handleStatusChange}
                onScoreUpdate={handleScoreUpdate}
              />
              <TierSection
                tier={2}
                opportunities={data.tier_2}
                onStatusChange={handleStatusChange}
                onScoreUpdate={handleScoreUpdate}
              />
              <TierSection
                tier={3}
                opportunities={data.tier_3}
                onStatusChange={handleStatusChange}
                onScoreUpdate={handleScoreUpdate}
              />
              <TierSection
                tier={4}
                opportunities={data.tier_4}
                onStatusChange={handleStatusChange}
                onScoreUpdate={handleScoreUpdate}
              />
            </>
          )}
        </div>

        {/* Empty State */}
        {data && data.summary.total === 0 && (
          <div className="text-center py-12">
            <Target className="w-12 h-12 text-muted mx-auto mb-4" />
            <h3 className="text-lg font-medium text-primary mb-2">No opportunities yet</h3>
            <p className="text-muted mb-4">Start tracking AI implementation opportunities</p>
            <button
              onClick={() => router.push('/opportunities/new')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add First Opportunity
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
