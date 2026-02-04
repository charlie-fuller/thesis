'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Plus,
  Folder,
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Search,
  Users,
  ChevronRight,
  Loader2,
  Map,
  GitBranch
} from 'lucide-react'
import DiscoProcessMap from '@/components/disco/DiscoProcessMap'
import DiscoOperationalizeMap from '@/components/disco/DiscoOperationalizeMap'
import { apiGet, apiPost } from '@/lib/api'

// ============================================================================
// TYPES
// ============================================================================

interface Initiative {
  id: string
  name: string
  description: string | null
  status: string
  created_at: string
  updated_at: string
  user_role: string
  document_count: number
  users?: {
    id: string
    name: string
    email: string
  }
  latest_outputs?: Record<string, {
    agent_type: string
    version: number
    created_at: string
    recommendation?: string
    confidence_level?: string
  }>
}

interface InitiativesResponse {
  success: boolean
  initiatives: Initiative[]
  total: number
}

// ============================================================================
// CONSTANTS
// ============================================================================

const STATUS_CONFIG: Record<string, { label: string; color: string; bgColor: string; icon: typeof Clock }> = {
  draft: { label: 'Draft', color: 'text-slate-600', bgColor: 'bg-slate-100 dark:bg-slate-800', icon: FileText },
  triaged: { label: 'Triaged', color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900/30', icon: CheckCircle },
  in_discovery: { label: 'Discovery', color: 'text-amber-600', bgColor: 'bg-amber-100 dark:bg-amber-900/30', icon: Clock },
  consolidated: { label: 'Intelligence', color: 'text-teal-600', bgColor: 'bg-teal-100 dark:bg-teal-900/30', icon: CheckCircle },
  synthesized: { label: 'Synthesis', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900/30', icon: CheckCircle },
  documented: { label: 'Convergence', color: 'text-indigo-600', bgColor: 'bg-indigo-100 dark:bg-indigo-900/30', icon: CheckCircle },
  archived: { label: 'Archived', color: 'text-slate-500', bgColor: 'bg-slate-100 dark:bg-slate-800', icon: AlertCircle },
}

// ============================================================================
// COMPONENTS
// ============================================================================

function InitiativeCard({ initiative, onClick }: { initiative: Initiative; onClick: () => void }) {
  const statusConfig = STATUS_CONFIG[initiative.status] || STATUS_CONFIG.draft
  const StatusIcon = statusConfig.icon

  const triageOutput = initiative.latest_outputs?.triage
  // Check for consolidator (new) or synthesizer (backwards compatibility)
  const prdOutput = initiative.latest_outputs?.consolidator || initiative.latest_outputs?.synthesizer

  return (
    <div
      onClick={onClick}
      className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-5 hover:shadow-md hover:border-indigo-300 dark:hover:border-indigo-600 transition-all cursor-pointer group"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-900 dark:text-white truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
            {initiative.name}
          </h3>
          {initiative.description && (
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
              {initiative.description}
            </p>
          )}
        </div>
        <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
          <StatusIcon className="w-3 h-3" />
          {statusConfig.label}
        </span>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
        <span className="flex items-center gap-1">
          <FileText className="w-4 h-4" />
          {initiative.document_count} docs
        </span>
        {initiative.user_role !== 'owner' && (
          <span className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            {initiative.user_role}
          </span>
        )}
      </div>

      {/* Triage recommendation badge */}
      {triageOutput?.recommendation && (
        <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700">
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
            triageOutput.recommendation === 'GO'
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
              : triageOutput.recommendation === 'NO-GO'
              ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
          }`}>
            {triageOutput.recommendation}
            {triageOutput.confidence_level && (
              <span className="opacity-75 ml-1">({triageOutput.confidence_level})</span>
            )}
          </span>
        </div>
      )}

      {/* Click hint */}
      <div className="mt-3 flex items-center justify-end gap-1 text-xs text-slate-400 group-hover:text-indigo-500 transition-colors">
        View details
        <ChevronRight className="w-3 h-3" />
      </div>
    </div>
  )
}

function CreateInitiativeModal({
  open,
  onClose,
  onCreated
}: {
  open: boolean
  onClose: () => void
  onCreated: (initiative: Initiative) => void
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!name.trim()) {
      setError('Name is required')
      return
    }

    setCreating(true)
    setError(null)

    try {
      const result = await apiPost<{ success: boolean; initiative: Initiative }>(
        '/api/disco/initiatives',
        { name: name.trim(), description: description.trim() || undefined }
      )

      if (result.success && result.initiative) {
        onCreated(result.initiative)
        setName('')
        setDescription('')
        onClose()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create initiative')
    } finally {
      setCreating(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative card rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
        <h2 className="text-lg font-semibold text-primary mb-4">
          Create New Initiative
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Customer Portal Redesign"
              className="input-field"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the initiative..."
              rows={3}
              className="textarea-field"
            />
          </div>

          {error && (
            <p className="text-sm" style={{ color: 'var(--color-error)' }}>{error}</p>
          )}
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={creating || !name.trim()}
            className="btn-primary flex items-center gap-2"
          >
            {creating && <Loader2 className="w-4 h-4 animate-spin" />}
            Create Initiative
          </button>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function DiscoInitiativesPage() {
  const router = useRouter()
  const [initiatives, setInitiatives] = useState<Initiative[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'initiatives' | 'workflow' | 'operationalize'>('initiatives')

  const loadInitiatives = async () => {
    try {
      setLoading(true)
      setError(null)

      let endpoint = '/api/disco/initiatives'
      if (statusFilter) {
        endpoint += `?status=${statusFilter}`
      }

      const result = await apiGet<InitiativesResponse>(endpoint)
      setInitiatives(result.initiatives || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load initiatives')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadInitiatives()
    // eslint-disable-next-line react-hooks/exhaustive-deps -- loadInitiatives is stable
  }, [statusFilter])

  const handleInitiativeCreated = (initiative: Initiative) => {
    setInitiatives([initiative, ...initiatives])
    router.push(`/disco/${initiative.id}`)
  }

  // Filter by search query
  const filteredInitiatives = initiatives.filter(initiative => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      initiative.name.toLowerCase().includes(query) ||
      (initiative.description?.toLowerCase().includes(query) ?? false)
    )
  })

  // Group by status for summary
  const statusCounts = initiatives.reduce((acc, init) => {
    acc[init.status] = (acc[init.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  if (loading && initiatives.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-2 text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          Loading initiatives...
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Title - Centered */}
      <div className="text-center mb-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
          DISCO
        </h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Discovery, Intelligence, Synthesis, Convergence, Operationalize
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab('initiatives')}
          className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
            activeTab === 'initiatives'
              ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          Initiatives
        </button>
        <button
          onClick={() => setActiveTab('workflow')}
          className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
            activeTab === 'workflow'
              ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          <Map className="w-4 h-4" />
          Workflow Map
        </button>
        <button
          onClick={() => setActiveTab('operationalize')}
          className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-1.5 ${
            activeTab === 'operationalize'
              ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
          }`}
        >
          <GitBranch className="w-4 h-4" />
          Operationalize Map
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'workflow' ? (
        <DiscoProcessMap />
      ) : activeTab === 'operationalize' ? (
        <DiscoOperationalizeMap />
      ) : (
        <>

      {/* Header - only show New Initiative button when there are initiatives */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
            Initiatives
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {initiatives.length} initiative{initiatives.length !== 1 ? 's' : ''} total
          </p>
        </div>
        {initiatives.length > 0 && (
          <button
            onClick={() => setCreateModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Initiative
          </button>
        )}
      </div>

      {/* Summary Cards - exclude draft and archived */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-6">
        {Object.entries(STATUS_CONFIG)
          .filter(([status]) => status !== 'draft' && status !== 'archived')
          .map(([status, config]) => {
            const count = statusCounts[status] || 0
            const StatusIcon = config.icon
            return (
              <button
                key={status}
                onClick={() => setStatusFilter(statusFilter === status ? '' : status)}
                className={`p-3 rounded-lg border transition-all ${
                  statusFilter === status
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30'
                    : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                }`}
              >
                <div className={`text-2xl font-bold ${config.color}`}>{count}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">{config.label}</div>
              </button>
            )
          })}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search initiatives..."
            className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        {statusFilter && (
          <button
            onClick={() => setStatusFilter('')}
            className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            Clear filter
          </button>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
            <AlertCircle className="w-5 h-5" />
            <p>{error}</p>
          </div>
          <button
            onClick={loadInitiatives}
            className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Initiative Grid */}
      {filteredInitiatives.length === 0 ? (
        <div className="text-center py-12">
          <Folder className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
            {searchQuery || statusFilter ? 'No matching initiatives' : 'No initiatives yet'}
          </h3>
          <p className="text-slate-500 dark:text-slate-400 mb-4">
            {searchQuery || statusFilter
              ? 'Try adjusting your search or filter'
              : 'Create your first initiative to get started with DISCO'}
          </p>
          {!searchQuery && !statusFilter && (
            <button
              onClick={() => setCreateModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              <Plus className="w-4 h-4" />
              Create Initiative
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredInitiatives.map((initiative) => (
            <InitiativeCard
              key={initiative.id}
              initiative={initiative}
              onClick={() => router.push(`/disco/${initiative.id}`)}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      <CreateInitiativeModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreated={handleInitiativeCreated}
      />
      </>
      )}
    </div>
  )
}
