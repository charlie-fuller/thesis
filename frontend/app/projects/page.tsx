'use client'

import { useState, useEffect, useCallback, useMemo, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  Target,
  Filter,
  RefreshCw,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  Building2,
  Users,
  Zap,
  TrendingUp,
  AlertTriangle,
  Plus,
  ArrowUpDown,
  LayoutGrid,
  Layers
} from 'lucide-react'
import { apiGet, apiPatch } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageLayout from '@/components/PageLayout'
import ProjectDetailModal from '@/components/projects/ProjectDetailModal'
import toast from 'react-hot-toast'

// ============================================================================
// TYPES
// ============================================================================

interface Project {
  id: string
  project_code: string
  opportunity_code?: string  // Legacy field for backward compatibility
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
  project_summary: string | null
  scoring_confidence: number | null
  goal_alignment_score: number | null
  display_order: number
  // Extended fields for detail modal
  project_name?: string | null
  project_description?: string | null
  roi_justification?: string | null
  effort_justification?: string | null
  alignment_justification?: string | null
  readiness_justification?: string | null
  confidence_questions?: string[]
  goal_alignment_details?: {
    pillar_scores: {
      customer_prospect_journey: { score: number; rationale: string }
      maximize_value: { score: number; rationale: string }
      data_first_digital_workforce: { score: number; rationale: string }
      high_trust_culture: { score: number; rationale: string }
    }
    kpi_impacts: string[]
    summary: string
    analyzed_at: string
  } | null
  initiative_ids?: string[]
}

// ============================================================================
// CONSTANTS
// ============================================================================

const TIER_COLORS: Record<number, string> = {
  1: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400',
  2: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  3: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  4: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
}

const STATUS_COLORS: Record<string, string> = {
  backlog: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
  active: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  archived: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500',
}

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'backlog', label: 'Backlog' },
  { value: 'active', label: 'Active' },
  { value: 'completed', label: 'Completed' },
  { value: 'archived', label: 'Archived' },
]

const DEPARTMENT_OPTIONS = [
  { value: '', label: 'All Departments' },
  { value: 'Legal', label: 'Legal' },
  { value: 'HR', label: 'HR' },
  { value: 'Finance', label: 'Finance' },
  { value: 'IT', label: 'IT' },
  { value: 'Engineering', label: 'Engineering' },
  { value: 'Marketing', label: 'Marketing' },
  { value: 'Sales', label: 'Sales' },
  { value: 'Operations', label: 'Operations' },
]

const SORT_OPTIONS = [
  { value: 'manual', label: 'Manual Order' },
  { value: 'score-desc', label: 'Score (High → Low)' },
  { value: 'score-asc', label: 'Score (Low → High)' },
  { value: 'created-desc', label: 'Created (Newest)' },
  { value: 'created-asc', label: 'Created (Oldest)' },
  { value: 'alpha', label: 'Alphabetical' },
  { value: 'roi-desc', label: 'ROI (High → Low)' },
  { value: 'effort-asc', label: 'Effort (Low → High)' },
]

// ============================================================================
// COMPONENTS
// ============================================================================

function ScoreBar({ value, max = 5, color = 'bg-brand' }: { value: number | null; max?: number; color?: string }) {
  if (value === null) return <span className="text-xs text-muted">--</span>
  const percentage = (value / max) * 100
  return (
    <div className="w-16 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
      <div className={`h-full ${color} rounded-full`} style={{ width: `${percentage}%` }} />
    </div>
  )
}

interface ProjectCardProps {
  project: Project
  onClick: () => void
  onMoveUp?: () => void
  onMoveDown?: () => void
  isFirst?: boolean
  isLast?: boolean
  showTier?: boolean
}

function ProjectCard({ project, onClick, onMoveUp, onMoveDown, isFirst, isLast, showTier = false }: ProjectCardProps) {
  const tierColor = TIER_COLORS[project.tier] || TIER_COLORS[4]
  const statusColor = STATUS_COLORS[project.status] || STATUS_COLORS.backlog

  return (
    <div className="bg-card rounded-lg border border-default p-4 hover:shadow-md hover:border-brand/30 transition-all group relative">
      {/* Reorder buttons */}
      <div className="absolute right-2 top-2 flex flex-col gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => { e.stopPropagation(); onMoveUp?.() }}
          disabled={isFirst}
          className={`p-1 rounded hover:bg-hover ${isFirst ? 'opacity-30 cursor-not-allowed' : ''}`}
          title="Move up"
        >
          <ChevronUp className="w-3 h-3 text-muted" />
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onMoveDown?.() }}
          disabled={isLast}
          className={`p-1 rounded hover:bg-hover ${isLast ? 'opacity-30 cursor-not-allowed' : ''}`}
          title="Move down"
        >
          <ChevronDown className="w-3 h-3 text-muted" />
        </button>
      </div>

      {/* Clickable area */}
      <div onClick={onClick} className="cursor-pointer">
        {/* Header */}
        <div className="flex items-start justify-between mb-3 pr-6">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-muted">{project.project_code}</span>
            {showTier && (
              <span className={`text-xs px-1.5 py-0.5 rounded ${tierColor}`}>
                T{project.tier}
              </span>
            )}
            <span className={`text-xs px-1.5 py-0.5 rounded capitalize ${statusColor}`}>
              {project.status}
            </span>
          </div>
          <ChevronRight className="w-4 h-4 text-muted flex-shrink-0" />
        </div>

      {/* Title */}
      <h3 className="font-semibold text-primary mb-2 line-clamp-2">
        {project.title}
      </h3>

      {/* Description */}
      {project.description && (
        <p className="text-sm text-secondary mb-3 line-clamp-2">
          {project.description}
        </p>
      )}

      {/* Scores - vertical layout */}
      <div className="space-y-1.5 mb-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-muted">ROI</span>
          <ScoreBar value={project.roi_potential} color="bg-emerald-500" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">Effort</span>
          <ScoreBar value={project.implementation_effort} color="bg-amber-500" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">Alignment</span>
          <ScoreBar value={project.strategic_alignment} color="bg-blue-500" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted">Readiness</span>
          <ScoreBar value={project.stakeholder_readiness} color="bg-purple-500" />
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center gap-3 pt-3 border-t border-default text-xs text-muted">
        <div className="flex items-center gap-1">
          <Zap className="w-3 h-3" />
          <span>Score: {project.total_score}</span>
        </div>
        {project.department && (
          <div className="flex items-center gap-1">
            <Building2 className="w-3 h-3" />
            <span>{project.department}</span>
          </div>
        )}
        {project.owner_name && (
          <div className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            <span>{project.owner_name}</span>
          </div>
        )}
      </div>

      {/* Confidence indicator */}
      {project.scoring_confidence !== null && (
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                project.scoring_confidence >= 70 ? 'bg-emerald-500' :
                project.scoring_confidence >= 40 ? 'bg-amber-500' : 'bg-red-500'
              }`}
              style={{ width: `${project.scoring_confidence}%` }}
            />
          </div>
          <span className="text-xs text-muted">{project.scoring_confidence}% confident</span>
        </div>
      )}
      </div>
    </div>
  )
}

// ============================================================================
// MAIN PAGE
// ============================================================================

function ProjectsPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, loading: authLoading } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)

  // Get initiative filter from URL
  const initiativeFilter = searchParams.get('initiative') || ''

  // Filters
  const [departmentFilter, setDepartmentFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [tierFilter, setTierFilter] = useState<number | ''>('')
  const [sortBy, setSortBy] = useState('manual')
  const [activeOnly, setActiveOnly] = useState(true)
  const [viewMode, setViewMode] = useState<'list' | 'tier'>('list')

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [authLoading, user, router])

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams()
      if (departmentFilter) params.set('department', departmentFilter)
      if (statusFilter) params.set('status', statusFilter)
      if (tierFilter) params.set('tier', tierFilter.toString())
      if (initiativeFilter) params.set('initiative_id', initiativeFilter)

      const data = await apiGet<Project[]>(`/api/projects/?${params}`)
      setProjects(data)
    } catch (err) {
      console.error('Failed to fetch projects:', err)
      setError('Failed to load projects')
      toast.error('Failed to load projects')
    } finally {
      setLoading(false)
    }
  }, [departmentFilter, statusFilter, tierFilter, initiativeFilter])

  useEffect(() => {
    if (user) {
      fetchProjects()
    }
  }, [user, fetchProjects])

  const handleViewProject = (project: Project) => {
    setSelectedProject(project)
  }

  // Move project up or down within its tier
  const moveProject = useCallback(async (projectId: string, direction: 'up' | 'down') => {
    const projectIndex = projects.findIndex(p => p.id === projectId)
    if (projectIndex === -1) return

    const project = projects[projectIndex]
    const tierProjects = projects.filter(p => p.tier === project.tier)
      .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))

    const tierIndex = tierProjects.findIndex(p => p.id === projectId)
    if (tierIndex === -1) return

    // Can't move up if first, can't move down if last
    if (direction === 'up' && tierIndex === 0) return
    if (direction === 'down' && tierIndex === tierProjects.length - 1) return

    const swapIndex = direction === 'up' ? tierIndex - 1 : tierIndex + 1
    const swapProject = tierProjects[swapIndex]

    // Swap display orders
    const newOrder = swapProject.display_order || swapIndex
    const oldOrder = project.display_order || tierIndex

    // Update locally first for instant feedback
    setProjects(prev => prev.map(p => {
      if (p.id === projectId) return { ...p, display_order: newOrder }
      if (p.id === swapProject.id) return { ...p, display_order: oldOrder }
      return p
    }))

    // Persist to backend
    try {
      await Promise.all([
        apiPatch(`/api/projects/${projectId}`, { display_order: newOrder }),
        apiPatch(`/api/projects/${swapProject.id}`, { display_order: oldOrder })
      ])
    } catch (err) {
      console.error('Failed to update project order:', err)
      toast.error('Failed to save order')
      // Revert on error
      fetchProjects()
    }
  }, [projects, fetchProjects])

  // Sort and filter projects
  const sortedProjects = useMemo(() => {
    // Filter by active status first if toggle is on
    const filtered = activeOnly
      ? projects.filter(p => p.status === 'active')
      : projects

    const sorted = [...filtered]
    switch (sortBy) {
      case 'manual':
        return sorted.sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
      case 'score-desc':
        return sorted.sort((a, b) => (b.total_score || 0) - (a.total_score || 0))
      case 'score-asc':
        return sorted.sort((a, b) => (a.total_score || 0) - (b.total_score || 0))
      case 'created-desc':
        return sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      case 'created-asc':
        return sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      case 'alpha':
        return sorted.sort((a, b) => a.title.localeCompare(b.title))
      case 'roi-desc':
        return sorted.sort((a, b) => (b.roi_potential || 0) - (a.roi_potential || 0))
      case 'effort-asc':
        return sorted.sort((a, b) => (a.implementation_effort || 0) - (b.implementation_effort || 0))
      default:
        return sorted
    }
  }, [projects, sortBy, activeOnly])


  // Show loading state while auth is being checked
  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-page">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-secondary mt-4">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render if not authenticated
  if (!user) {
    return null
  }

  return (
    <PageLayout>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-primary">Projects</h1>
            <p className="text-sm text-secondary mt-1">
              AI implementation opportunities ranked by impact and effort
            </p>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
              <AlertTriangle className="w-5 h-5" />
              <span>{error}</span>
              <button onClick={fetchProjects} className="ml-auto text-sm underline">
                Retry
              </button>
            </div>
          </div>
        )}

        {/* View Toggle */}
        <div className="mb-6 flex items-center">
          <div className="ml-auto flex items-center gap-1 bg-hover rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'list'
                  ? 'bg-card shadow-sm text-primary'
                  : 'text-muted hover:text-primary'
              }`}
              title="List View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('tier')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'tier'
                  ? 'bg-card shadow-sm text-primary'
                  : 'text-muted hover:text-primary'
              }`}
              title="Tier View"
            >
              <Layers className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted" />
            <span className="text-sm text-muted">Filters:</span>
          </div>

          {/* Initiative Filter Indicator */}
          {initiativeFilter && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-lg text-sm">
              <span>Filtered by initiative</span>
              <button
                onClick={() => router.push('/projects')}
                className="hover:text-indigo-900 dark:hover:text-indigo-100"
                title="Clear filter"
              >
                &times;
              </button>
            </div>
          )}

          {/* Active Only Toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <div className="relative">
              <input
                type="checkbox"
                checked={activeOnly}
                onChange={(e) => setActiveOnly(e.target.checked)}
                className="sr-only"
              />
              <div className={`w-10 h-5 rounded-full transition-colors ${
                activeOnly ? 'bg-brand' : 'bg-gray-300 dark:bg-gray-600'
              }`} />
              <div className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                activeOnly ? 'translate-x-5' : 'translate-x-0'
              }`} />
            </div>
            <span className={`text-sm font-medium ${activeOnly ? 'text-brand' : 'text-muted'}`}>
              Active Only
            </span>
            {activeOnly && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-brand/10 text-brand">
                {projects.filter(p => p.status === 'active').length}
              </span>
            )}
          </label>

          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="w-auto bg-hover border border-default rounded-md text-sm py-1.5 px-3 text-primary"
          >
            {DEPARTMENT_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-auto bg-hover border border-default rounded-md text-sm py-1.5 px-3 text-primary"
          >
            {STATUS_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value ? parseInt(e.target.value) : '')}
            className="w-auto bg-hover border border-default rounded-md text-sm py-1.5 px-3 text-primary"
          >
            <option value="">All Tiers</option>
            <option value="1">Tier 1 (Quick Wins)</option>
            <option value="2">Tier 2 (Strategic)</option>
            <option value="3">Tier 3 (Long-term)</option>
            <option value="4">Tier 4 (Low Priority)</option>
          </select>

          <div className="flex items-center gap-2 ml-4 pl-4 border-l border-default">
            <ArrowUpDown className="w-4 h-4 text-muted" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-auto bg-hover border border-default rounded-md text-sm py-1.5 px-3 text-primary"
            >
              {SORT_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {(departmentFilter || statusFilter || tierFilter || activeOnly) && (
            <button
              onClick={() => {
                setDepartmentFilter('')
                setStatusFilter('')
                setTierFilter('')
                setActiveOnly(false)
              }}
              className="text-sm text-muted hover:text-primary"
            >
              Clear filters
            </button>
          )}

          <button
            onClick={fetchProjects}
            className="ml-auto p-2 hover:bg-hover rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 text-muted ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-secondary opacity-30 mb-4">
              <Target className="w-16 h-16 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-primary mb-2">No projects found</h3>
            <p className="text-secondary mb-4">
              {departmentFilter || statusFilter || tierFilter
                ? 'Try adjusting your filters'
                : 'Scan your vault to discover AI implementation opportunities'}
            </p>
            <button
              onClick={() => router.push('/pipeline')}
              className="btn-primary"
            >
              Go to Pipeline
            </button>
          </div>
        ) : viewMode === 'list' ? (
          /* List View - Flat grid without tier grouping */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {sortedProjects.map((project, idx) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => handleViewProject(project)}
                onMoveUp={() => moveProject(project.id, 'up')}
                onMoveDown={() => moveProject(project.id, 'down')}
                isFirst={idx === 0}
                isLast={idx === sortedProjects.length - 1}
                showTier={false}
              />
            ))}
          </div>
        ) : (
          /* Tier View - Grouped by tier */
          <div className="space-y-8">
            {[
              { tier: 1, label: 'Quick Wins' },
              { tier: 2, label: 'Strategic' },
              { tier: 3, label: 'Long-term' },
              { tier: 4, label: 'Low Priority' },
            ].map(({ tier, label }) => {
              const tierProjects = sortedProjects.filter(p => p.tier === tier)
              return (
                <div key={tier}>
                  <div className="flex items-center gap-2 pb-3 mb-4 border-b border-default">
                    <span className={`text-xs px-2 py-1 rounded font-medium ${TIER_COLORS[tier]}`}>T{tier}</span>
                    <span className="text-sm font-medium text-primary">{label}</span>
                    <span className="text-xs text-muted ml-auto">
                      {tierProjects.length} projects
                    </span>
                  </div>
                  {tierProjects.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {tierProjects.map((project, idx) => (
                        <ProjectCard
                          key={project.id}
                          project={project}
                          onClick={() => handleViewProject(project)}
                          onMoveUp={() => moveProject(project.id, 'up')}
                          onMoveDown={() => moveProject(project.id, 'down')}
                          isFirst={idx === 0}
                          isLast={idx === tierProjects.length - 1}
                          showTier={true}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted py-4">No T{tier} projects</p>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </main>

      {/* Project Detail Modal */}
      {selectedProject && (
        <ProjectDetailModal
          project={selectedProject}
          open={true}
          onClose={() => setSelectedProject(null)}
        />
      )}
    </PageLayout>
  )
}

// Wrap in Suspense for useSearchParams
export default function ProjectsPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <ProjectsPageContent />
    </Suspense>
  )
}
