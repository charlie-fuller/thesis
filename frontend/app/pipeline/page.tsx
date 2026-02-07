'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  Target,
  CheckSquare,
  Users,
  RefreshCw,
  AlertTriangle,
  Calendar,
  ArrowUpRight,
  ChevronRight,
  Filter,
  Building2,
  Clock,
  TrendingUp,
  Zap,
  Vault
} from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'
import PageLayout from '@/components/PageLayout'

// ============================================================================
// TYPES
// ============================================================================

interface PriorityOpportunity {
  id: string
  opportunity_code: string
  title: string
  description: string | null
  department: string | null
  roi_potential: number | null
  implementation_effort: number | null
  strategic_alignment: number | null
  stakeholder_readiness: number | null
  total_score: number | null
  tier: number | null
  status: string
  priority_score: number
  owner_name: string | null
  created_at: string
}

interface Commitment {
  id: string
  title: string
  description: string | null
  assignee_name: string | null
  due_date: string | null
  status: string
  priority: number
  source_type: string | null
  is_overdue: boolean
  days_until_due: number | null
  created_at: string
}

interface StakeholderPulse {
  id: string
  name: string
  role: string | null
  department: string | null
  engagement_level: string | null
  sentiment_score: number | null
  last_interaction: string | null
  total_interactions: number
  open_questions: string[]
}

interface PipelineOverview {
  priority_queue: PriorityOpportunity[]
  commitments: Commitment[]
  stakeholder_pulse: StakeholderPulse[]
  stats: {
    total_opportunities: number
    total_commitments: number
    overdue_commitments: number
    total_stakeholders: number
    department_filter: string | null
  }
}

interface GranolaScanStatus {
  connected: boolean
  vault_path: string
  total_files: number
  scanned_files: number
  pending_files: number
  last_scan: string | null
  error: string | null
}

// ============================================================================
// CONSTANTS
// ============================================================================

const ENGAGEMENT_COLORS: Record<string, string> = {
  champion: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  advocate: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  engaged: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  neutral: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400',
  skeptic: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  disengaged: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

const TIER_COLORS: Record<number, string> = {
  1: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400',
  2: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  3: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  4: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
}

// ============================================================================
// COMPONENTS
// ============================================================================

function PriorityQueuePanel({
  opportunities,
  onViewOpportunity
}: {
  opportunities: PriorityOpportunity[]
  onViewOpportunity: (id: string) => void
}) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-rose-500" />
          <h2 className="font-semibold text-slate-900 dark:text-white">Priority Queue</h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
            {opportunities.length}
          </span>
        </div>
        <span className="text-xs text-slate-500">Ranked by impact/effort</span>
      </div>

      <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[720px] overflow-y-auto">
        {opportunities.length === 0 ? (
          <div className="px-4 py-8 text-center text-slate-500">
            <Target className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No opportunities yet</p>
            <p className="text-xs">Scan your vault to discover projects</p>
          </div>
        ) : (
          opportunities.map((opp, index) => (
            <div
              key={opp.id}
              className="px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
              onClick={() => onViewOpportunity(opp.id)}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-xs font-medium text-slate-600 dark:text-slate-400">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-slate-500">{opp.opportunity_code}</span>
                    {opp.tier && (
                      <span className={`text-xs px-1.5 py-0.5 rounded ${TIER_COLORS[opp.tier]}`}>
                        T{opp.tier}
                      </span>
                    )}
                    {opp.department && (
                      <span className="text-xs text-slate-400">{opp.department}</span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                    {opp.title}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Score: {opp.priority_score}
                    </span>
                    {opp.owner_name && (
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {opp.owner_name}
                      </span>
                    )}
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function CommitmentsPanel({
  commitments,
  onViewTask
}: {
  commitments: Commitment[]
  onViewTask: (id: string) => void
}) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckSquare className="w-5 h-5 text-blue-500" />
          <h2 className="font-semibold text-slate-900 dark:text-white">Commitments</h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
            {commitments.length}
          </span>
        </div>
        <span className="text-xs text-slate-500">What you owe</span>
      </div>

      <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[720px] overflow-y-auto">
        {commitments.length === 0 ? (
          <div className="px-4 py-8 text-center text-slate-500">
            <CheckSquare className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No pending commitments</p>
          </div>
        ) : (
          commitments.map((task) => (
            <div
              key={task.id}
              className="px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
              onClick={() => onViewTask(task.id)}
            >
              <div className="flex items-start gap-3">
                <div className={`flex-shrink-0 w-2 h-2 mt-2 rounded-full ${
                  task.is_overdue
                    ? 'bg-red-500'
                    : task.days_until_due !== null && task.days_until_due <= 3
                      ? 'bg-amber-500'
                      : 'bg-blue-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                    {task.title}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                    {task.due_date && (
                      <span className={`flex items-center gap-1 ${
                        task.is_overdue ? 'text-red-600 dark:text-red-400 font-medium' : ''
                      }`}>
                        <Calendar className="w-3 h-3" />
                        {task.is_overdue
                          ? `${Math.abs(task.days_until_due!)} days overdue`
                          : task.days_until_due === 0
                            ? 'Due today'
                            : task.days_until_due === 1
                              ? 'Due tomorrow'
                              : `Due in ${task.days_until_due} days`
                        }
                      </span>
                    )}
                    {task.assignee_name && (
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {task.assignee_name}
                      </span>
                    )}
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function StakeholderPulsePanel({
  stakeholders,
  onViewStakeholder
}: {
  stakeholders: StakeholderPulse[]
  onViewStakeholder: (id: string) => void
}) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-emerald-500" />
          <h2 className="font-semibold text-slate-900 dark:text-white">Stakeholder Pulse</h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
            {stakeholders.length}
          </span>
        </div>
        <span className="text-xs text-slate-500">Engagement levels</span>
      </div>

      <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[720px] overflow-y-auto">
        {stakeholders.length === 0 ? (
          <div className="px-4 py-8 text-center text-slate-500">
            <Users className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No stakeholders yet</p>
            <p className="text-xs">Scan your meetings to discover stakeholders</p>
          </div>
        ) : (
          stakeholders.map((sh) => (
            <div
              key={sh.id}
              className="px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
              onClick={() => onViewStakeholder(sh.id)}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-sm font-medium text-slate-600 dark:text-slate-400">
                  {sh.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {sh.name}
                    </p>
                    {sh.engagement_level && (
                      <span className={`text-xs px-1.5 py-0.5 rounded capitalize ${
                        ENGAGEMENT_COLORS[sh.engagement_level] || ENGAGEMENT_COLORS.neutral
                      }`}>
                        {sh.engagement_level}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    {sh.role && <span>{sh.role}</span>}
                    {sh.department && (
                      <span className="flex items-center gap-1">
                        <Building2 className="w-3 h-3" />
                        {sh.department}
                      </span>
                    )}
                    {sh.total_interactions > 0 && (
                      <span>{sh.total_interactions} interactions</span>
                    )}
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function GranolaScanPanel({
  status,
  isScanning,
  onScan
}: {
  status: GranolaScanStatus | null
  isScanning: boolean
  onScan: (forceRescan: boolean) => void
}) {
  if (!status) return null

  return (
    <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            status.connected ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-red-100 dark:bg-red-900/30'
          }`}>
            <Vault className={`w-5 h-5 ${
              status.connected ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
            }`} />
          </div>
          <div>
            <h3 className="font-medium text-slate-900 dark:text-white">Vault</h3>
            <p className="text-xs text-slate-500">
              {status.connected
                ? `${status.scanned_files}/${status.total_files} meetings synced`
                : status.error || 'Not connected'
              }
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {status.pending_files > 0 && (
            <span className="text-xs px-2 py-1 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
              {status.pending_files} new
            </span>
          )}
          <button
            onClick={() => onScan(false)}
            disabled={isScanning || !status.connected}
            className="px-3 py-1.5 text-sm font-medium rounded-lg bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />
            {isScanning ? 'Scanning...' : 'Scan'}
          </button>
        </div>
      </div>

      {status.last_scan && (
        <p className="text-xs text-slate-400 mt-2">
          Last scan: {new Date(status.last_scan).toLocaleString()}
        </p>
      )}
    </div>
  )
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function PipelinePage() {
  const router = useRouter()
  const [data, setData] = useState<PipelineOverview | null>(null)
  const [granolaStatus, setGranolaStatus] = useState<GranolaScanStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [isScanning, setIsScanning] = useState(false)
  const [departmentFilter, setDepartmentFilter] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams()
      if (departmentFilter) params.set('department', departmentFilter)

      const [overviewRes, statusRes] = await Promise.all([
        apiGet<PipelineOverview>(`/api/pipeline/overview?${params}`),
        apiGet<GranolaScanStatus>('/api/pipeline/granola/status')
      ])

      setData(overviewRes)
      setGranolaStatus(statusRes)
    } catch (err) {
      console.error('Failed to fetch pipeline data:', err)
      setError('Failed to load pipeline data')
    } finally {
      setLoading(false)
    }
  }, [departmentFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleScan = async (forceRescan: boolean) => {
    try {
      setIsScanning(true)
      await apiPost(`/api/pipeline/granola/scan?force_rescan=${forceRescan}`, {})
      await fetchData()
    } catch (err) {
      console.error('Scan failed:', err)
      setError('Failed to scan vault')
    } finally {
      setIsScanning(false)
    }
  }

  const handleViewOpportunity = (id: string) => {
    router.push(`/opportunities?selected=${id}`)
  }

  const handleViewTask = (id: string) => {
    router.push(`/tasks?selected=${id}`)
  }

  const handleViewStakeholder = (id: string) => {
    router.push(`/stakeholders/${id}`)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
          <p className="text-sm text-slate-500">Loading pipeline...</p>
        </div>
      </div>
    )
  }

  return (
    <PageLayout>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 bg-slate-50 dark:bg-slate-950 min-h-full">
        {/* Page Title */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Pipeline</h1>
          <p className="text-sm text-slate-500 mt-1">
            Your action-oriented view of opportunities, commitments, and stakeholders
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
              <AlertTriangle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Granola Scan Panel */}
        <div className="mb-6">
          <GranolaScanPanel
            status={granolaStatus}
            isScanning={isScanning}
            onScan={handleScan}
          />
        </div>

        {/* Filter Bar */}
        <div className="mb-6 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-500">Filter:</span>
          </div>
          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="px-3 py-1.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
          >
            <option value="">All Departments</option>
            <option value="Legal">Legal</option>
            <option value="People">People</option>
            <option value="Finance">Finance</option>
            <option value="IT">IT</option>
            <option value="Engineering">Engineering</option>
            <option value="Marketing">Marketing</option>
            <option value="Sales">Sales</option>
          </select>

          {departmentFilter && (
            <button
              onClick={() => setDepartmentFilter('')}
              className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            >
              Clear filter
            </button>
          )}
        </div>

        {/* Stats Row */}
        {data?.stats && (
          <div className="mb-6 grid grid-cols-4 gap-4">
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4">
              <div className="flex items-center gap-2 text-slate-500 mb-1">
                <Target className="w-4 h-4" />
                <span className="text-xs uppercase tracking-wide">Opportunities</span>
              </div>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                {data.stats.total_opportunities}
              </p>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4">
              <div className="flex items-center gap-2 text-slate-500 mb-1">
                <CheckSquare className="w-4 h-4" />
                <span className="text-xs uppercase tracking-wide">Commitments</span>
              </div>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                {data.stats.total_commitments}
              </p>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4">
              <div className="flex items-center gap-2 text-red-500 mb-1">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-xs uppercase tracking-wide">Overdue</span>
              </div>
              <p className="text-2xl font-semibold text-red-600 dark:text-red-400">
                {data.stats.overdue_commitments}
              </p>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4">
              <div className="flex items-center gap-2 text-slate-500 mb-1">
                <Users className="w-4 h-4" />
                <span className="text-xs uppercase tracking-wide">Stakeholders</span>
              </div>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                {data.stats.total_stakeholders}
              </p>
            </div>
          </div>
        )}

        {/* Three Panel Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <PriorityQueuePanel
            opportunities={data?.priority_queue || []}
            onViewOpportunity={handleViewOpportunity}
          />
          <CommitmentsPanel
            commitments={data?.commitments || []}
            onViewTask={handleViewTask}
          />
          <StakeholderPulsePanel
            stakeholders={data?.stakeholder_pulse || []}
            onViewStakeholder={handleViewStakeholder}
          />
        </div>
      </main>
    </PageLayout>
  )
}
