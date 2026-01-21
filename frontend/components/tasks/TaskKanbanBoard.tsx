'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { Plus, Filter, RefreshCw, ListChecks, ChevronDown, ChevronUp, Loader2, Search } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiGet, apiPatch, apiPost } from '@/lib/api'
import { logger } from '@/lib/logger'
import TaskColumn from './TaskColumn'
import TaskCreateModal from './TaskCreateModal'
import TaskFilters from './TaskFilters'
import TaskCandidateReviewModal from './TaskCandidateReviewModal'
import LoadingSpinner from '@/components/LoadingSpinner'

// Task types
export interface Task {
  id: string
  client_id: string
  title: string
  description: string | null
  status: 'pending' | 'in_progress' | 'blocked' | 'completed'
  priority: number
  assignee_stakeholder_id: string | null
  assignee_user_id: string | null
  assignee_name: string | null
  display_assignee: string | null
  due_date: string | null
  completed_at: string | null
  source_type: string | null
  source_transcript_id: string | null
  category: string | null
  tags: string[]
  blocker_reason: string | null
  blocked_at: string | null
  position: number
  created_at: string
  updated_at: string
  stakeholder_name?: string | null
  stakeholder_email?: string | null
}

interface KanbanResponse {
  success: boolean
  columns: {
    pending: Task[]
    in_progress: Task[]
    blocked: Task[]
    completed: Task[]
  }
  counts: {
    pending: number
    in_progress: number
    blocked: number
    completed: number
    total: number
    overdue: number
  }
}

export interface TaskFiltersState {
  assignee_stakeholder_id: string | null
  due_date_from: string | null
  due_date_to: string | null
  priority: number[] | null
  source_type: string[] | null
  search: string | null
  include_completed: boolean
}

const COLUMN_CONFIG = [
  { id: 'pending', title: 'To Do', color: 'bg-gray-100 dark:bg-gray-800', headerColor: 'text-gray-700 dark:text-gray-300' },
  { id: 'in_progress', title: 'In Progress', color: 'bg-blue-50 dark:bg-blue-900/20', headerColor: 'text-blue-700 dark:text-blue-300' },
  { id: 'blocked', title: 'Blocked', color: 'bg-orange-50 dark:bg-orange-900/20', headerColor: 'text-orange-700 dark:text-orange-300' },
  { id: 'completed', title: 'Done', color: 'bg-green-50 dark:bg-green-900/20', headerColor: 'text-green-700 dark:text-green-300' },
] as const

export default function TaskKanbanBoard() {
  const [columns, setColumns] = useState<KanbanResponse['columns']>({
    pending: [],
    in_progress: [],
    blocked: [],
    completed: [],
  })
  const [counts, setCounts] = useState<KanbanResponse['counts']>({
    pending: 0,
    in_progress: 0,
    blocked: 0,
    completed: 0,
    total: 0,
    overdue: 0,
  })
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editTask, setEditTask] = useState<Task | null>(null)
  const [defaultStatus, setDefaultStatus] = useState<Task['status']>('pending')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState<TaskFiltersState>({
    assignee_stakeholder_id: null,
    due_date_from: null,
    due_date_to: null,
    priority: null,
    source_type: null,
    search: null,
    include_completed: true,
  })

  // Task candidates state
  interface TaskCandidate {
    id: string
    title: string
    source_document_name: string
    source_text?: string
    suggested_priority: number
    suggested_due_date?: string
    due_date_text?: string
    assignee_name?: string
    confidence: string
    description?: string
    meeting_context?: string
    team?: string
    stakeholder_name?: string
    value_proposition?: string
    document_date?: string
    topics?: string[]
  }
  const [candidates, setCandidates] = useState<TaskCandidate[]>([])
  const [candidatesCount, setCandidatesCount] = useState(0)
  const [showCandidateReview, setShowCandidateReview] = useState(false)

  // Task discovery panel state
  const [discoveryExpanded, setDiscoveryExpanded] = useState(false)
  const [scanLoading, setScanLoading] = useState(false)
  const [scanLimit, setScanLimit] = useState(5)
  const [sinceDays, setSinceDays] = useState(30)
  const [forceRescan, setForceRescan] = useState(false)
  interface ScanStats {
    total_documents: number
    recent_documents_30d: number
    pending_candidates: number
    last_scan_at: string | null
    documents_scanned_ever: number
  }
  const [scanStats, setScanStats] = useState<ScanStats | null>(null)

  // Build query string from filters
  const buildQueryString = useCallback((f: TaskFiltersState) => {
    const params = new URLSearchParams()
    if (f.assignee_stakeholder_id) params.append('assignee_stakeholder_id', f.assignee_stakeholder_id)
    if (f.due_date_from) params.append('due_date_from', f.due_date_from)
    if (f.due_date_to) params.append('due_date_to', f.due_date_to)
    if (f.priority && f.priority.length > 0) {
      f.priority.forEach(p => params.append('priority', p.toString()))
    }
    if (f.source_type && f.source_type.length > 0) {
      f.source_type.forEach(s => params.append('source_type', s))
    }
    if (f.search) params.append('search', f.search)
    params.append('include_completed', f.include_completed.toString())
    return params.toString()
  }, [])

  // Fetch kanban data
  const fetchKanban = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) setLoading(true)
      else setRefreshing(true)

      const queryString = buildQueryString(filters)
      const response = await apiGet<KanbanResponse>(`/api/tasks/kanban?${queryString}`)

      if (response.success) {
        setColumns(response.columns)
        setCounts(response.counts)
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
      toast.error('Failed to load tasks')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [filters, buildQueryString])

  // Fetch task candidates
  const fetchCandidates = useCallback(async () => {
    try {
      const response = await apiGet<{ success: boolean; candidates: TaskCandidate[]; count: number }>(
        '/api/tasks/candidates?status=pending&limit=50'
      )
      if (response.success) {
        setCandidates(response.candidates || [])
        setCandidatesCount(response.count || 0)
      }
    } catch (err) {
      logger.error('Error fetching task candidates:', err)
    }
  }, [])

  // Fetch scan stats
  const fetchScanStats = useCallback(async () => {
    try {
      const stats = await apiGet<ScanStats>('/api/tasks/scan-stats')
      setScanStats(stats)
    } catch (err) {
      logger.error('Error fetching scan stats:', err)
    }
  }, [])

  // Scan documents for tasks
  const handleScanDocuments = useCallback(async () => {
    try {
      setScanLoading(true)

      const params = new URLSearchParams({
        limit: scanLimit.toString(),
        ...(sinceDays > 0 && { since_days: sinceDays.toString() }),
        ...(forceRescan && { force_rescan: 'true' })
      })

      interface ScanApiResponse {
        success: boolean
        documents_scanned: number
        total_tasks_found: number
        total_tasks_stored: number
        message: string
      }

      // Use longer timeout for LLM-based task extraction (120s for Sonnet quality)
      const scanResponse = await apiPost<ScanApiResponse>(
        `/api/tasks/scan-documents?${params}`,
        {},
        { timeout: 120000 }
      )

      // Refresh candidates and stats
      await Promise.all([fetchCandidates(), fetchScanStats()])

      if (scanResponse.total_tasks_found > 0) {
        setShowCandidateReview(true)
        toast.success(`Found ${scanResponse.total_tasks_found} potential tasks from ${scanResponse.documents_scanned} documents`)
      } else {
        toast.success(`Scanned ${scanResponse.documents_scanned} documents - no new tasks found`)
      }
    } catch (err) {
      logger.error('Failed to scan documents:', err)
      toast.error('Failed to scan documents for tasks')
    } finally {
      setScanLoading(false)
    }
  }, [scanLimit, sinceDays, forceRescan, fetchCandidates, fetchScanStats])

  // Initial load
  useEffect(() => {
    fetchKanban()
    fetchCandidates()
    fetchScanStats()
  }, [fetchKanban, fetchCandidates, fetchScanStats])

  // Handle drag and drop
  const handleDrop = useCallback(async (taskId: string, newStatus: Task['status'], newPosition?: number) => {
    // Find the task in current columns
    let task: Task | undefined
    let oldStatus: Task['status'] | undefined

    for (const [status, tasks] of Object.entries(columns)) {
      const found = tasks.find(t => t.id === taskId)
      if (found) {
        task = found
        oldStatus = status as Task['status']
        break
      }
    }

    if (!task || !oldStatus) return

    // Optimistic update
    setColumns(prev => {
      const newColumns = { ...prev }

      // Remove from old column
      newColumns[oldStatus!] = prev[oldStatus!].filter(t => t.id !== taskId)

      // Add to new column
      const updatedTask = { ...task!, status: newStatus, position: newPosition ?? 0 }
      newColumns[newStatus] = [...prev[newStatus], updatedTask].sort((a, b) => a.position - b.position)

      return newColumns
    })

    // API call
    try {
      await apiPatch(`/api/tasks/${taskId}/status`, {
        status: newStatus,
        position: newPosition,
      })
      toast.success(`Task moved to ${newStatus.replace('_', ' ')}`)
    } catch (error) {
      console.error('Failed to update task status:', error)
      toast.error('Failed to move task')
      // Revert on error
      fetchKanban(false)
    }
  }, [columns, fetchKanban])

  // Handle task click (open edit modal)
  const handleTaskClick = useCallback((task: Task) => {
    setEditTask(task)
    setDefaultStatus(task.status)
    setShowCreateModal(true)
  }, [])

  // Handle add task from column
  const handleAddTaskFromColumn = useCallback((status: Task['status']) => {
    setEditTask(null)
    setDefaultStatus(status)
    setShowCreateModal(true)
  }, [])

  // Handle modal close
  const handleModalClose = useCallback(() => {
    setShowCreateModal(false)
    setEditTask(null)
  }, [])

  // Handle task saved
  const handleTaskSaved = useCallback(() => {
    handleModalClose()
    fetchKanban(false)
  }, [handleModalClose, fetchKanban])

  // Handle candidate review complete
  const handleCandidateReviewComplete = useCallback((stats: { accepted: number; rejected: number }) => {
    setShowCandidateReview(false)
    if (stats.accepted > 0) {
      toast.success(`Created ${stats.accepted} task${stats.accepted !== 1 ? 's' : ''}`)
      fetchKanban(false)
    }
    fetchCandidates()
    fetchScanStats()
  }, [fetchKanban, fetchCandidates, fetchScanStats])

  // Active filters count
  const activeFiltersCount = useMemo(() => {
    let count = 0
    if (filters.assignee_stakeholder_id) count++
    if (filters.due_date_from || filters.due_date_to) count++
    if (filters.priority && filters.priority.length > 0) count++
    if (filters.source_type && filters.source_type.length > 0) count++
    if (filters.search) count++
    if (!filters.include_completed) count++
    return count
  }, [filters])

  // Calculate due soon count (within 3 days, not overdue, not completed)
  const dueSoonCount = useMemo(() => {
    const now = new Date()
    const threeDaysFromNow = new Date(now)
    threeDaysFromNow.setDate(threeDaysFromNow.getDate() + 3)

    const allTasks = [...columns.pending, ...columns.in_progress, ...columns.blocked]
    return allTasks.filter(task => {
      if (!task.due_date) return false
      const dueDate = new Date(task.due_date)
      return dueDate >= now && dueDate <= threeDaysFromNow
    }).length
  }, [columns])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary">Tasks</h1>
          <p className="text-sm text-muted mt-1">
            {counts.total} total tasks
            {counts.overdue > 0 && (
              <span className="text-red-600 dark:text-red-400 ml-2">
                ({counts.overdue} overdue)
              </span>
            )}
            {dueSoonCount > 0 && (
              <span className="text-amber-600 dark:text-amber-400 ml-2">
                ({dueSoonCount} due soon)
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchKanban(false)}
            disabled={refreshing}
            className="p-2 text-muted hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
              showFilters || activeFiltersCount > 0
                ? 'bg-brand/10 text-brand'
                : 'text-muted hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            <Filter className="w-5 h-5" />
            <span className="text-sm font-medium">Filters</span>
            {activeFiltersCount > 0 && (
              <span className="w-5 h-5 flex items-center justify-center bg-brand text-white text-xs rounded-full">
                {activeFiltersCount}
              </span>
            )}
          </button>
          <button
            onClick={() => {
              setEditTask(null)
              setDefaultStatus('pending')
              setShowCreateModal(true)
            }}
            className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span className="font-medium">Add Task</span>
          </button>
        </div>
      </div>

      {/* Task Discovery Panel - matches kanban board width: 4 columns * 320px + 3 gaps * 16px */}
      <div className="card" style={{ maxWidth: 'calc(4 * 320px + 3 * 16px)' }}>
        {/* Header */}
        <button
          onClick={() => setDiscoveryExpanded(!discoveryExpanded)}
          className="w-full p-4 flex items-center justify-between hover:bg-page/50 transition-colors rounded-lg"
        >
          <div className="flex items-center gap-2">
            <ListChecks className="w-5 h-5 text-amber-500" />
            <span className="font-semibold text-primary">Task Discovery</span>
            {candidatesCount > 0 && (
              <span className="px-2 py-0.5 text-xs bg-amber-500/20 text-amber-500 rounded-full font-medium">
                {candidatesCount} pending
              </span>
            )}
          </div>
          {discoveryExpanded ? (
            <ChevronUp className="w-5 h-5 text-secondary" />
          ) : (
            <ChevronDown className="w-5 h-5 text-secondary" />
          )}
        </button>

        {/* Expanded Content */}
        {discoveryExpanded && (
          <div className="px-4 pb-4 border-t border-border">
            <p className="text-secondary text-sm my-4">
              Scan your Knowledge Base documents (meetings, transcripts, notes) for potential tasks.
              Found tasks are saved as candidates for you to review, accept, or reject.
            </p>

            {/* Scan Settings - inline */}
            <div className="flex flex-wrap items-center gap-4 mb-4">
              <div className="flex items-center gap-2">
                <label htmlFor="scanLimit" className="text-sm text-secondary">Documents:</label>
                <select
                  id="scanLimit"
                  value={scanLimit}
                  onChange={(e) => setScanLimit(Number(e.target.value))}
                  className="px-2 py-1.5 text-sm bg-page border border-border rounded-md text-primary"
                >
                  <option value={5}>5</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label htmlFor="sinceDays" className="text-sm text-secondary">Time range:</label>
                <select
                  id="sinceDays"
                  value={sinceDays}
                  onChange={(e) => setSinceDays(Number(e.target.value))}
                  className="px-2 py-1.5 text-sm bg-page border border-border rounded-md text-primary"
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 90 days</option>
                  <option value={365}>Last year</option>
                  <option value={0}>All time</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label htmlFor="forceRescan" className="text-sm text-secondary">Rescan:</label>
                <button
                  id="forceRescan"
                  onClick={() => setForceRescan(!forceRescan)}
                  className={`px-3 py-1 text-sm rounded-md border transition-colors ${
                    forceRescan
                      ? 'bg-amber-600/20 border-amber-500/50 text-amber-500'
                      : 'bg-page border-border text-muted hover:text-primary'
                  }`}
                >
                  {forceRescan ? 'On' : 'Off'}
                </button>
              </div>
            </div>

            {/* Scan Button */}
            <button
              onClick={handleScanDocuments}
              disabled={scanLoading}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors disabled:opacity-50 font-medium"
            >
              {scanLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Scanning {scanLimit} Documents...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Scan Documents
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <TaskFilters
          filters={filters}
          onChange={setFilters}
          onClose={() => setShowFilters(false)}
        />
      )}

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {COLUMN_CONFIG.map(column => (
          <TaskColumn
            key={column.id}
            id={column.id}
            title={column.title}
            tasks={columns[column.id as keyof typeof columns]}
            count={counts[column.id as keyof typeof counts] as number}
            color={column.color}
            headerColor={column.headerColor}
            onDrop={handleDrop}
            onTaskClick={handleTaskClick}
            onAddTask={handleAddTaskFromColumn}
          />
        ))}
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <TaskCreateModal
          open={showCreateModal}
          onClose={handleModalClose}
          onSaved={handleTaskSaved}
          editTask={editTask}
          defaultStatus={defaultStatus}
        />
      )}

      {/* Candidate Review Modal */}
      {showCandidateReview && (
        <TaskCandidateReviewModal
          open={showCandidateReview}
          onClose={() => setShowCandidateReview(false)}
          onComplete={handleCandidateReviewComplete}
          candidates={candidates}
        />
      )}
    </div>
  )
}
