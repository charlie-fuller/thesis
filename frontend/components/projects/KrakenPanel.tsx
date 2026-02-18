'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Loader2,
  Check,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Zap,
  FileText,
  Clock,
  RefreshCw,
} from 'lucide-react'
import { authenticatedFetch } from '@/lib/api'

// ============================================================================
// TYPES
// ============================================================================

interface ConfidenceBreakdown {
  information_sufficiency: number
  output_clarity: number
  execution_feasibility: number
  completeness_achievable: number
  domain_fit: number
}

interface TaskEvaluation {
  task_id: string
  title: string
  task_understanding?: string
  steps?: string[]
  recommendations?: string[]
  category: 'automatable' | 'assistable' | 'manual'
  confidence: number
  confidence_breakdown?: ConfidenceBreakdown
  reasoning: string
  proposed_action: string
  estimated_quality: 'high' | 'medium' | 'low'
}

interface EvaluationSummary {
  total: number
  automatable: number
  assistable: number
  manual: number
  agenticity_score: number
}

interface EvaluationData {
  evaluations: TaskEvaluation[]
  summary: EvaluationSummary
  agenticity_score: number
  task_hash: string
}

interface StoredEvaluation {
  agenticity_score: number | null
  evaluated_at: string | null
  evaluation: {
    evaluations: TaskEvaluation[]
    summary: EvaluationSummary
  } | null
  task_hash: string | null
  is_stale: boolean
  current_task_count: number
}

interface TaskExecutionResult {
  task_id: string
  title: string
  comment_id?: string
  doc_id?: string
  word_count?: number
  error?: string
}

interface KrakenPanelProps {
  projectId: string
  taskCount: number
  onTasksUpdated?: () => void
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function KrakenPanel({ projectId, taskCount, onTasksUpdated }: KrakenPanelProps) {
  // Evaluation state
  const [evaluating, setEvaluating] = useState(false)
  const [evaluationData, setEvaluationData] = useState<EvaluationData | null>(null)
  const [storedEvaluation, setStoredEvaluation] = useState<StoredEvaluation | null>(null)
  const [evaluationStatus, setEvaluationStatus] = useState<string>('')

  // Execution state
  const [executing, setExecuting] = useState(false)
  const [executionStatus, setExecutionStatus] = useState<string>('')
  const [executionResults, setExecutionResults] = useState<TaskExecutionResult[]>([])
  const [selectedTaskIds, setSelectedTaskIds] = useState<Set<string>>(new Set())

  // UI state
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['automatable', 'assistable', 'manual']))
  const [error, setError] = useState<string | null>(null)

  // Load stored evaluation on mount
  const loadStoredEvaluation = useCallback(async () => {
    try {
      const response = await authenticatedFetch(`/api/projects/${projectId}/kraken/evaluation`)
      if (response.ok) {
        const data = await response.json()
        if (data.evaluation) {
          setStoredEvaluation(data)
          // Restore evaluation data from stored
          setEvaluationData({
            evaluations: data.evaluation.evaluations,
            summary: data.evaluation.summary,
            agenticity_score: data.agenticity_score,
            task_hash: data.task_hash,
          })
          // Pre-select automatable tasks
          const automatableTasks = new Set<string>(
            data.evaluation.evaluations
              .filter((e: TaskEvaluation) => e.category === 'automatable')
              .map((e: TaskEvaluation) => e.task_id)
          )
          setSelectedTaskIds(automatableTasks)
        }
      }
    } catch {
      // No stored evaluation, that's fine
    }
  }, [projectId])

  useEffect(() => {
    loadStoredEvaluation()
  }, [loadStoredEvaluation])

  // ============================================================================
  // EVALUATE
  // ============================================================================

  const runEvaluation = async () => {
    setEvaluating(true)
    setError(null)
    setEvaluationData(null)
    setEvaluationStatus('Starting evaluation...')
    setExecutionResults([])

    try {
      const response = await authenticatedFetch(
        `/api/projects/${projectId}/kraken/evaluate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          timeout: 120000,
        }
      )

      if (!response.ok) {
        throw new Error('Failed to start evaluation')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i]

          if (line.startsWith('event: ')) {
            const eventType = line.slice(7).trim()
            if (i + 1 < lines.length && lines[i + 1].startsWith('data: ')) {
              const data = lines[i + 1].slice(6)
              i++ // skip the data line

              if (eventType === 'status') {
                setEvaluationStatus(data)
              } else if (eventType === 'evaluation_complete') {
                try {
                  const evalData = JSON.parse(data) as EvaluationData
                  setEvaluationData(evalData)
                  // Pre-select automatable tasks
                  const automatableTasks = new Set<string>(
                    evalData.evaluations
                      .filter(e => e.category === 'automatable')
                      .map(e => e.task_id)
                  )
                  setSelectedTaskIds(automatableTasks)
                  // Update stored evaluation
                  setStoredEvaluation({
                    agenticity_score: evalData.agenticity_score,
                    evaluated_at: new Date().toISOString(),
                    evaluation: {
                      evaluations: evalData.evaluations,
                      summary: evalData.summary,
                    },
                    task_hash: evalData.task_hash,
                    is_stale: false,
                    current_task_count: evalData.summary.total,
                  })
                } catch {
                  setError('Failed to parse evaluation results')
                }
              } else if (eventType === 'error') {
                setError(data)
              }
            }
          }
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Evaluation failed')
    } finally {
      setEvaluating(false)
      setEvaluationStatus('')
    }
  }

  // ============================================================================
  // EXECUTE
  // ============================================================================

  const runExecution = async () => {
    if (selectedTaskIds.size === 0) return

    setExecuting(true)
    setError(null)
    setExecutionResults([])
    setExecutionStatus('Starting execution...')

    try {
      const response = await authenticatedFetch(
        `/api/projects/${projectId}/kraken/execute`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task_ids: Array.from(selectedTaskIds) }),
          timeout: 300000,
        }
      )

      if (!response.ok) {
        throw new Error('Failed to start execution')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i]

          if (line.startsWith('event: ')) {
            const eventType = line.slice(7).trim()
            if (i + 1 < lines.length && lines[i + 1].startsWith('data: ')) {
              const data = lines[i + 1].slice(6)
              i++

              if (eventType === 'status') {
                setExecutionStatus(data)
              } else if (eventType === 'task_started') {
                try {
                  const taskData = JSON.parse(data)
                  setExecutionStatus(`Working on: ${taskData.title}`)
                } catch { /* ignore */ }
              } else if (eventType === 'task_complete') {
                try {
                  const result = JSON.parse(data) as TaskExecutionResult
                  setExecutionResults(prev => [...prev, result])
                } catch { /* ignore */ }
              } else if (eventType === 'task_error') {
                try {
                  const result = JSON.parse(data) as TaskExecutionResult
                  setExecutionResults(prev => [...prev, result])
                } catch { /* ignore */ }
              } else if (eventType === 'all_complete') {
                try {
                  const summary = JSON.parse(data)
                  setExecutionStatus(
                    `Done! ${summary.tasks_completed} tasks completed, ${summary.docs_created} KB docs created.`
                  )
                } catch { /* ignore */ }
              } else if (eventType === 'error') {
                setError(data)
              }
            }
          }
        }
      }

      // Refresh parent task list
      onTasksUpdated?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Execution failed')
    } finally {
      setExecuting(false)
    }
  }

  // ============================================================================
  // HELPERS
  // ============================================================================

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }

  const toggleTask = (taskId: string) => {
    setSelectedTaskIds(prev => {
      const next = new Set(prev)
      if (next.has(taskId)) {
        next.delete(taskId)
      } else {
        next.add(taskId)
      }
      return next
    })
  }

  const evaluations = evaluationData?.evaluations || []
  const automatableTasks = evaluations.filter(e => e.category === 'automatable')
  const assistableTasks = evaluations.filter(e => e.category === 'assistable')
  const manualTasks = evaluations.filter(e => e.category === 'manual')

  const hasEvaluation = evaluations.length > 0
  const isStale = storedEvaluation?.is_stale || false

  // ============================================================================
  // RENDER
  // ============================================================================

  // No tasks = nothing to show
  if (taskCount === 0) return null

  return (
    <div className="space-y-4">
      {/* Header with button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Kraken Task Evaluator
          </h4>
          {hasEvaluation && evaluationData?.agenticity_score != null && (
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400">
              {evaluationData.agenticity_score.toFixed(0)}% Automatable
            </span>
          )}
          {isStale && hasEvaluation && (
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Stale
            </span>
          )}
        </div>
        <button
          onClick={runEvaluation}
          disabled={evaluating || executing}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {evaluating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Evaluating...
            </>
          ) : hasEvaluation && !isStale ? (
            <>
              <RefreshCw className="w-4 h-4" />
              Re-evaluate
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              Release the Kraken
            </>
          )}
        </button>
      </div>

      {/* Status message */}
      {evaluating && evaluationStatus && (
        <div className="flex items-center gap-2 text-sm text-muted p-3 bg-violet-50 dark:bg-violet-900/10 rounded-lg">
          <Loader2 className="w-4 h-4 animate-spin text-violet-500" />
          {evaluationStatus}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Evaluation Results */}
      {hasEvaluation && !evaluating && (
        <div className="space-y-3">
          {/* Summary bar */}
          <div className="flex items-center gap-4 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg text-xs">
            <span className="text-muted">{evaluationData?.summary.total} tasks evaluated:</span>
            <span className="text-green-600 dark:text-green-400 font-medium">
              {evaluationData?.summary.automatable} automatable
            </span>
            <span className="text-amber-600 dark:text-amber-400 font-medium">
              {evaluationData?.summary.assistable} assistable
            </span>
            <span className="text-slate-500 font-medium">
              {evaluationData?.summary.manual} manual
            </span>
            {storedEvaluation?.evaluated_at && (
              <span className="text-muted ml-auto flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(storedEvaluation.evaluated_at).toLocaleString()}
              </span>
            )}
          </div>

          {/* Automatable tasks */}
          {automatableTasks.length > 0 && (
            <CategorySection
              label="Automatable"
              color="green"
              tasks={automatableTasks}
              expanded={expandedCategories.has('automatable')}
              onToggle={() => toggleCategory('automatable')}
              selectable
              selectedIds={selectedTaskIds}
              onToggleTask={toggleTask}
              executing={executing}
              executionResults={executionResults}
            />
          )}

          {/* Assistable tasks */}
          {assistableTasks.length > 0 && (
            <CategorySection
              label="Assistable"
              color="amber"
              tasks={assistableTasks}
              expanded={expandedCategories.has('assistable')}
              onToggle={() => toggleCategory('assistable')}
              selectable
              selectedIds={selectedTaskIds}
              onToggleTask={toggleTask}
              executing={executing}
              executionResults={executionResults}
            />
          )}

          {/* Manual tasks */}
          {manualTasks.length > 0 && (
            <CategorySection
              label="Manual"
              color="slate"
              tasks={manualTasks}
              expanded={expandedCategories.has('manual')}
              onToggle={() => toggleCategory('manual')}
              selectable={false}
              selectedIds={selectedTaskIds}
              onToggleTask={toggleTask}
              executing={executing}
              executionResults={executionResults}
            />
          )}

          {/* Execute button */}
          {selectedTaskIds.size > 0 && !executing && (
            <div className="flex items-center justify-between pt-2 border-t border-default">
              <span className="text-sm text-muted">
                {selectedTaskIds.size} task{selectedTaskIds.size !== 1 ? 's' : ''} selected for execution
              </span>
              <button
                onClick={runExecution}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                <Zap className="w-4 h-4" />
                Execute {selectedTaskIds.size} Task{selectedTaskIds.size !== 1 ? 's' : ''}
              </button>
            </div>
          )}

          {/* Execution progress */}
          {executing && executionStatus && (
            <div className="flex items-center gap-2 text-sm text-muted p-3 bg-green-50 dark:bg-green-900/10 rounded-lg">
              <Loader2 className="w-4 h-4 animate-spin text-green-500" />
              {executionStatus}
            </div>
          )}

          {/* Execution results summary */}
          {!executing && executionResults.length > 0 && (
            <div className="p-3 bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-lg text-sm">
              <p className="font-medium text-green-700 dark:text-green-400 mb-2">
                Execution Complete
              </p>
              <ul className="space-y-1">
                {executionResults.map(result => (
                  <li key={result.task_id} className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    {result.error ? (
                      <AlertTriangle className="w-3 h-3 text-red-500 flex-shrink-0" />
                    ) : (
                      <Check className="w-3 h-3 flex-shrink-0" />
                    )}
                    <span className={result.error ? 'text-red-600 dark:text-red-400' : ''}>
                      {result.title}
                      {result.doc_id && (
                        <span className="text-muted ml-1 flex items-center gap-1 inline-flex">
                          <FileText className="w-3 h-3" />
                          KB doc created
                        </span>
                      )}
                      {result.error && ` - Error: ${result.error}`}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* No evaluation yet prompt */}
      {!hasEvaluation && !evaluating && (
        <div className="text-center py-6 border border-dashed border-default rounded-lg">
          <Zap className="w-6 h-6 mx-auto text-violet-400 mb-2" />
          <p className="text-sm text-muted">
            Click &quot;Release the Kraken&quot; to evaluate which tasks can be automated.
          </p>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// CATEGORY SECTION COMPONENT
// ============================================================================

interface CategorySectionProps {
  label: string
  color: 'green' | 'amber' | 'slate'
  tasks: TaskEvaluation[]
  expanded: boolean
  onToggle: () => void
  selectable: boolean
  selectedIds: Set<string>
  onToggleTask: (id: string) => void
  executing: boolean
  executionResults: TaskExecutionResult[]
}

function CategorySection({
  label,
  color,
  tasks,
  expanded,
  onToggle,
  selectable,
  selectedIds,
  onToggleTask,
  executing,
  executionResults,
}: CategorySectionProps) {
  const colorClasses = {
    green: {
      border: 'border-green-200 dark:border-green-800',
      bg: 'bg-green-50 dark:bg-green-900/10',
      text: 'text-green-700 dark:text-green-400',
      badge: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    },
    amber: {
      border: 'border-amber-200 dark:border-amber-800',
      bg: 'bg-amber-50 dark:bg-amber-900/10',
      text: 'text-amber-700 dark:text-amber-400',
      badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    },
    slate: {
      border: 'border-slate-200 dark:border-slate-700',
      bg: 'bg-slate-50 dark:bg-slate-800/50',
      text: 'text-slate-600 dark:text-slate-400',
      badge: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
    },
  }

  const c = colorClasses[color]

  return (
    <div className={`border ${c.border} rounded-lg overflow-hidden`}>
      <button
        onClick={onToggle}
        className={`w-full flex items-center justify-between p-3 ${c.bg} hover:opacity-90 transition-opacity`}
      >
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          <span className={`text-sm font-medium ${c.text}`}>{label}</span>
          <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${c.badge}`}>
            {tasks.length}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="divide-y divide-default">
          {tasks.map(task => (
            <TaskEvaluationCard
              key={task.task_id}
              task={task}
              colorClasses={c}
              selectable={selectable}
              selectedIds={selectedIds}
              onToggleTask={onToggleTask}
              executing={executing}
              executionResults={executionResults}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// TASK EVALUATION CARD (enhanced display with new fields)
// ============================================================================

interface TaskEvaluationCardProps {
  task: TaskEvaluation
  colorClasses: { border: string; bg: string; text: string; badge: string }
  selectable: boolean
  selectedIds: Set<string>
  onToggleTask: (id: string) => void
  executing: boolean
  executionResults: TaskExecutionResult[]
}

function TaskEvaluationCard({
  task,
  colorClasses: c,
  selectable,
  selectedIds,
  onToggleTask,
  executing,
  executionResults,
}: TaskEvaluationCardProps) {
  const [stepsExpanded, setStepsExpanded] = useState(false)
  const [breakdownExpanded, setBreakdownExpanded] = useState(false)

  const executionResult = executionResults.find(r => r.task_id === task.task_id)
  const isExecuting = executing && selectedIds.has(task.task_id) && !executionResult

  return (
    <div className="p-3 space-y-1.5">
      <div className="flex items-start gap-2">
        {selectable && (
          <input
            type="checkbox"
            checked={selectedIds.has(task.task_id)}
            onChange={() => onToggleTask(task.task_id)}
            disabled={executing}
            className="mt-1 rounded border-default text-violet-600 focus:ring-violet-500"
          />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-primary truncate">
              {task.title}
            </span>
            <span className={`px-1.5 py-0.5 rounded text-xs font-medium flex-shrink-0 ${c.badge}`}>
              {task.confidence}%
            </span>
            {executionResult && !executionResult.error && (
              <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
            )}
            {executionResult?.error && (
              <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />
            )}
            {isExecuting && (
              <Loader2 className="w-4 h-4 animate-spin text-green-500 flex-shrink-0" />
            )}
          </div>

          {/* Understanding */}
          {task.task_understanding && (
            <p className="text-xs text-secondary mt-1">{task.task_understanding}</p>
          )}

          {/* Recommendations callout */}
          {task.recommendations && task.recommendations.length > 0 && (
            <div className="mt-1.5 p-2 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded text-xs">
              <p className="font-medium text-amber-700 dark:text-amber-400 mb-1">KB gaps:</p>
              <ul className="space-y-0.5">
                {task.recommendations.map((rec, i) => (
                  <li key={i} className="text-amber-600 dark:text-amber-400 flex items-start gap-1">
                    <span className="flex-shrink-0">-</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Steps (collapsible) */}
          {task.steps && task.steps.length > 0 && (
            <div className="mt-1">
              <button
                onClick={() => setStepsExpanded(!stepsExpanded)}
                className="flex items-center gap-1 text-xs text-muted hover:text-primary transition-colors"
              >
                {stepsExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                {task.steps.length} steps
              </button>
              {stepsExpanded && (
                <ol className="mt-1 ml-4 space-y-0.5 list-decimal list-outside text-xs text-secondary">
                  {task.steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              )}
            </div>
          )}

          {/* Confidence breakdown (collapsible) */}
          {task.confidence_breakdown && (
            <div className="mt-1">
              <button
                onClick={() => setBreakdownExpanded(!breakdownExpanded)}
                className="flex items-center gap-1 text-xs text-muted hover:text-primary transition-colors"
              >
                {breakdownExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                Confidence breakdown
              </button>
              {breakdownExpanded && (
                <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs">
                  {Object.entries(task.confidence_breakdown).map(([key, val]) => (
                    <span key={key} className="text-muted">
                      <span className={`font-medium ${val >= 14 ? 'text-green-600 dark:text-green-400' : val >= 10 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}`}>
                        {val}/20
                      </span>
                      {' '}{key.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          <p className="text-xs text-muted mt-1">{task.reasoning}</p>
          <p className="text-xs text-secondary mt-0.5">
            <span className="font-medium">Proposed:</span> {task.proposed_action}
          </p>
        </div>
      </div>
    </div>
  )
}
