'use client'

import { useState } from 'react'
import {
  Loader2,
  Zap,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Check,
  X,
} from 'lucide-react'
import { authenticatedFetch, apiPatch } from '@/lib/api'
import { Task } from './TaskKanbanBoard'

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

interface SingleTaskEvaluation {
  task_id: string
  title: string
  task_understanding?: string
  steps?: string[]
  recommendations?: string[]
  decision_gaps?: string[]
  category: 'automatable' | 'assistable' | 'manual'
  confidence: number
  confidence_breakdown?: ConfidenceBreakdown
  reasoning: string
  proposed_action: string
  estimated_quality: 'high' | 'medium' | 'low'
}

type Phase = 'idle' | 'evaluating' | 'reviewed' | 'executing' | 'done'

interface KrakenTaskPanelProps {
  task: Task
  onNotesUpdated: (newNotes: string) => void
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function KrakenTaskPanel({ task, onNotesUpdated }: KrakenTaskPanelProps) {
  const [phase, setPhase] = useState<Phase>('idle')
  const [statusText, setStatusText] = useState('')
  const [evaluation, setEvaluation] = useState<SingleTaskEvaluation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [stepsExpanded, setStepsExpanded] = useState(false)
  const [breakdownExpanded, setBreakdownExpanded] = useState(false)

  // ============================================================================
  // EVALUATE
  // ============================================================================

  const runEvaluation = async () => {
    setPhase('evaluating')
    setError(null)
    setEvaluation(null)
    setStatusText('Starting evaluation...')

    try {
      const response = await authenticatedFetch(
        `/api/tasks/${task.id}/kraken/evaluate`,
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
              i++

              if (eventType === 'status') {
                setStatusText(data)
              } else if (eventType === 'evaluation_complete') {
                try {
                  const parsed = JSON.parse(data)
                  setEvaluation(parsed.evaluation)
                  setPhase('reviewed')
                } catch {
                  setError('Failed to parse evaluation results')
                  setPhase('idle')
                }
              } else if (eventType === 'error') {
                setError(data)
                setPhase('idle')
              }
            }
          }
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Evaluation failed')
      setPhase('idle')
    }
  }

  // ============================================================================
  // ACCEPT (EXECUTE)
  // ============================================================================

  const handleAccept = async () => {
    if (!evaluation) return

    setPhase('executing')
    setError(null)
    setStatusText('Starting execution...')

    // Format evaluation into notes
    const evalNotes = formatEvaluationNotes(evaluation)

    try {
      const response = await authenticatedFetch(
        `/api/tasks/${task.id}/kraken/execute`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ evaluation_notes: evalNotes }),
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
                setStatusText(data)
              } else if (eventType === 'task_complete') {
                try {
                  const result = JSON.parse(data)
                  onNotesUpdated(result.notes || '')
                  setPhase('done')
                } catch {
                  setPhase('done')
                }
              } else if (eventType === 'error') {
                setError(data)
                setPhase('reviewed')
              }
            }
          }
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Execution failed')
      setPhase('reviewed')
    }
  }

  // ============================================================================
  // DECLINE
  // ============================================================================

  const handleDecline = async () => {
    if (!evaluation) return

    // Save recommendations to notes
    const recommendations = evaluation.recommendations || []
    if (recommendations.length > 0) {
      const recText = `[Kraken Recommendations]\n${recommendations.map((r, i) => `${i + 1}. ${r}`).join('\n')}`
      const existingNotes = task.notes || ''
      const separator = existingNotes ? '\n\n---\n' : ''
      const newNotes = existingNotes + separator + recText

      try {
        await apiPatch(`/api/tasks/${task.id}`, { notes: newNotes })
        onNotesUpdated(newNotes)
      } catch {
        // Silent fail for note save
      }
    }

    setPhase('idle')
    setEvaluation(null)
  }

  // ============================================================================
  // HELPERS
  // ============================================================================

  const categoryColor = (cat: string) => {
    switch (cat) {
      case 'automatable': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
      case 'assistable': return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
      default: return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
    }
  }

  const confidenceColor = (score: number) => {
    if (score >= 70) return 'text-green-600 dark:text-green-400'
    if (score >= 40) return 'text-amber-600 dark:text-amber-400'
    return 'text-red-600 dark:text-red-400'
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="border-t border-default pt-3 mt-3">
      {/* Idle: Show button */}
      {phase === 'idle' && (
        <button
          onClick={runEvaluation}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
        >
          <Zap className="w-4 h-4" />
          Release the Kraken
        </button>
      )}

      {/* Evaluating: Spinner */}
      {phase === 'evaluating' && (
        <div className="flex items-center gap-2 text-sm text-muted p-3 bg-violet-50 dark:bg-violet-900/10 rounded-lg">
          <Loader2 className="w-4 h-4 animate-spin text-violet-500" />
          {statusText}
        </div>
      )}

      {/* Reviewed: Show evaluation */}
      {phase === 'reviewed' && evaluation && (
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-medium text-primary">Kraken Evaluation</span>
            <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${categoryColor(evaluation.category)}`}>
              {evaluation.category}
            </span>
            <span className={`text-sm font-medium ${confidenceColor(evaluation.confidence)}`}>
              Confidence Score {evaluation.confidence}%
            </span>
          </div>

          {/* Understanding */}
          {evaluation.task_understanding && (
            <p className="text-sm text-secondary">{evaluation.task_understanding}</p>
          )}

          {/* Recommendations */}
          {evaluation.recommendations && evaluation.recommendations.length > 0 && (
            <div className="p-2.5 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-lg">
              <p className="text-xs font-medium text-amber-700 dark:text-amber-400 mb-1.5">
                KB gaps to address for higher confidence:
              </p>
              <ul className="space-y-1">
                {evaluation.recommendations.map((rec, i) => (
                  <li key={i} className="text-xs text-amber-600 dark:text-amber-400 flex items-start gap-1.5">
                    <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Decision gaps */}
          {evaluation.decision_gaps && evaluation.decision_gaps.length > 0 && (
            <div className="p-2.5 bg-purple-50 dark:bg-purple-900/10 border border-purple-200 dark:border-purple-800 rounded-lg">
              <p className="text-xs font-medium text-purple-700 dark:text-purple-400 mb-1.5">
                Decisions needed before execution:
              </p>
              <ul className="space-y-1">
                {evaluation.decision_gaps.map((gap, i) => (
                  <li key={i} className="text-xs text-purple-600 dark:text-purple-400 flex items-start gap-1.5">
                    <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    {gap}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Steps (collapsible) */}
          {evaluation.steps && evaluation.steps.length > 0 && (
            <div>
              <button
                onClick={() => setStepsExpanded(!stepsExpanded)}
                className="flex items-center gap-1 text-xs font-medium text-muted hover:text-primary transition-colors"
              >
                {stepsExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                {evaluation.steps.length} execution steps
              </button>
              {stepsExpanded && (
                <ol className="mt-1.5 ml-4 space-y-1 list-decimal list-outside">
                  {evaluation.steps.map((step, i) => (
                    <li key={i} className="text-xs text-secondary">{step}</li>
                  ))}
                </ol>
              )}
            </div>
          )}

          {/* Confidence Breakdown (collapsible) */}
          {evaluation.confidence_breakdown && (
            <div>
              <button
                onClick={() => setBreakdownExpanded(!breakdownExpanded)}
                className="flex items-center gap-1 text-xs font-medium text-muted hover:text-primary transition-colors"
              >
                {breakdownExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                Confidence breakdown
              </button>
              {breakdownExpanded && (
                <div className="mt-1.5 grid grid-cols-5 gap-2">
                  {Object.entries(evaluation.confidence_breakdown).map(([key, val]) => (
                    <div key={key} className="text-center">
                      <div className={`text-sm font-medium ${val >= 14 ? 'text-green-600 dark:text-green-400' : val >= 10 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}`}>
                        {val}/20
                      </div>
                      <div className="text-[10px] text-muted leading-tight">
                        {key.replace(/_/g, ' ')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Reasoning + Proposed Action */}
          <div className="space-y-1">
            <p className="text-xs text-muted">{evaluation.reasoning}</p>
            <p className="text-xs text-secondary">
              <span className="font-medium">Proposed:</span> {evaluation.proposed_action}
            </p>
          </div>

          {/* Accept / Decline buttons */}
          <div className="flex items-center gap-2 pt-1">
            <button
              onClick={handleAccept}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Check className="w-4 h-4" />
              Execute
            </button>
            <button
              onClick={handleDecline}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-default text-muted rounded-lg hover:text-primary hover:bg-hover transition-colors"
            >
              <X className="w-4 h-4" />
              Decline
            </button>
          </div>
        </div>
      )}

      {/* Executing: Spinner */}
      {phase === 'executing' && (
        <div className="flex items-center gap-2 text-sm text-muted p-3 bg-green-50 dark:bg-green-900/10 rounded-lg">
          <Loader2 className="w-4 h-4 animate-spin text-green-500" />
          {statusText}
        </div>
      )}

      {/* Done: Success */}
      {phase === 'done' && (
        <div className="flex items-center gap-2 text-sm p-3 bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-lg">
          <Check className="w-4 h-4 text-green-500" />
          <span className="text-green-700 dark:text-green-400">Task executed. Check comments for output.</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-2 p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-400">
          {error}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// FORMAT EVALUATION INTO NOTES
// ============================================================================

function formatEvaluationNotes(eval_: SingleTaskEvaluation): string {
  const lines: string[] = ['[Kraken Evaluation]']

  lines.push(`Category: ${eval_.category} | Confidence: ${eval_.confidence}%`)

  if (eval_.task_understanding) {
    lines.push(`\nUnderstanding: ${eval_.task_understanding}`)
  }

  if (eval_.steps && eval_.steps.length > 0) {
    lines.push('\nExecution Steps:')
    eval_.steps.forEach((step, i) => {
      lines.push(`  ${i + 1}. ${step}`)
    })
  }

  if (eval_.confidence_breakdown) {
    const bd = eval_.confidence_breakdown
    lines.push(`\nConfidence Breakdown: Info=${bd.information_sufficiency}/20, Clarity=${bd.output_clarity}/20, Feasibility=${bd.execution_feasibility}/20, Completeness=${bd.completeness_achievable}/20, Fit=${bd.domain_fit}/20`)
  }

  if (eval_.recommendations && eval_.recommendations.length > 0) {
    lines.push('\nKB Gaps:')
    eval_.recommendations.forEach((rec, i) => {
      lines.push(`  ${i + 1}. ${rec}`)
    })
  }

  if (eval_.decision_gaps && eval_.decision_gaps.length > 0) {
    lines.push('\nDecision Gaps:')
    eval_.decision_gaps.forEach((gap, i) => {
      lines.push(`  ${i + 1}. ${gap}`)
    })
  }

  lines.push(`\nProposed Action: ${eval_.proposed_action}`)

  return lines.join('\n')
}
