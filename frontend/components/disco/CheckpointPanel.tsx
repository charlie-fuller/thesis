'use client'

import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  Lock,
  CheckCircle,
  AlertTriangle,
  Clock,
  Check,
  X,
  MessageSquare,
  Users,
  ClipboardCheck,
  ThumbsUp,
  FileText,
  RefreshCw
} from 'lucide-react'

export type CheckpointStatus = 'locked' | 'needs_review' | 'approved' | 'stale'

export interface ChecklistItem {
  id: string
  label: string
  completed: boolean
}

export interface Checkpoint {
  id: string
  checkpoint_number: number
  status: CheckpointStatus
  approved_at?: string
  approved_by?: string
  notes?: string
  checklist_items: ChecklistItem[]
  is_stale?: boolean
  stale_reason?: string
}

interface CheckpointPanelProps {
  checkpoint: Checkpoint
  onApprove: (notes?: string) => Promise<void>
  onReset: () => Promise<void>
  onChecklistChange: (items: ChecklistItem[]) => void
  loading?: boolean
  canEdit?: boolean
}

// Checkpoint configuration by number
const CHECKPOINT_CONFIG: Record<number, {
  title: string
  description: string
  humanAction: string
  humanDetails: string
  icon: typeof MessageSquare
  stageLabel: string
  stageColor: string
  defaultChecklist: { id: string; label: string }[]
}> = {
  1: {
    title: 'Ready to Execute Discovery?',
    description: 'Review Discovery Guide output before conducting discovery sessions',
    humanAction: 'Execute the discovery sessions',
    humanDetails: 'The Discovery Guide has created session plans and agendas. YOU must conduct these sessions with stakeholders, record them, and upload the transcripts. After completing discovery, re-run Discovery Guide in coverage mode to verify readiness.',
    icon: MessageSquare,
    stageLabel: 'Discovery',
    stageColor: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30',
    defaultChecklist: [
      { id: 'triage_go', label: 'Triage decision is GO (not NO-GO or INVESTIGATE)' },
      { id: 'sessions_planned', label: 'Discovery sessions are planned with clear agendas' },
      { id: 'participants_identified', label: 'Participants and sponsors are identified' },
      { id: 'ready_to_execute', label: 'You are ready to execute the discovery sessions' }
    ]
  },
  2: {
    title: 'Ready for Proposed Initiatives?',
    description: 'Review insights and decision document before creating proposed initiatives',
    humanAction: 'Validate insights match your understanding',
    humanDetails: 'The Insight Analyst has extracted patterns and created a decision document. Review the leverage point, key insights, and evidence. Verify these match what you heard in discovery sessions. Add any missing documents before proceeding.',
    icon: ClipboardCheck,
    stageLabel: 'Intelligence',
    stageColor: 'text-cyan-600 bg-cyan-100 dark:bg-cyan-900/30',
    defaultChecklist: [
      { id: 'decision_reviewed', label: 'Decision document reviewed and validated' },
      { id: 'leverage_point', label: 'Leverage point makes sense for the problem' },
      { id: 'evidence_supports', label: 'Evidence supports the conclusions' },
      { id: 'no_gaps', label: 'No critical gaps or contradictions identified' }
    ]
  },
  3: {
    title: 'Ready for Requirements?',
    description: 'Review and approve proposed initiatives before generating documents',
    humanAction: 'Approve or reject proposed initiatives',
    humanDetails: 'The Initiative Builder has clustered insights into scored proposed initiatives. Review each one\'s scope, scoring (impact/feasibility/urgency), and dependencies. You can merge or split them. Select which proposed initiatives should proceed to document generation.',
    icon: ThumbsUp,
    stageLabel: 'Synthesis',
    stageColor: 'text-green-600 bg-green-100 dark:bg-green-900/30',
    defaultChecklist: [
      { id: 'bundles_reviewed', label: 'All proposed initiatives reviewed' },
      { id: 'scoring_valid', label: 'Scoring (impact/feasibility/urgency) is accurate' },
      { id: 'priority_agreed', label: 'Priority order agreed upon' },
      { id: 'bundles_selected', label: 'Proposed initiatives for document generation selected' }
    ]
  },
  4: {
    title: 'Ready for Engineering Handoff?',
    description: 'Review PRD and technical recommendations before handoff',
    humanAction: 'Final review before engineering',
    humanDetails: 'The Requirements Generator has created a comprehensive PRD with technical evaluation. Review with your engineering team for feasibility. This is the final gate before execution begins.',
    icon: FileText,
    stageLabel: 'Convergence',
    stageColor: 'text-rose-600 bg-rose-100 dark:bg-rose-900/30',
    defaultChecklist: [
      { id: 'prd_complete', label: 'PRD is complete and actionable' },
      { id: 'tech_reviewed', label: 'Technical approach reviewed with engineering' },
      { id: 'estimates_valid', label: 'Cost and timeline estimates are reasonable' },
      { id: 'ready_handoff', label: 'Ready for engineering handoff' }
    ]
  }
}

// Status styling
const STATUS_STYLES: Record<CheckpointStatus, {
  bg: string
  border: string
  icon: typeof Lock
  iconColor: string
  label: string
}> = {
  locked: {
    bg: 'bg-slate-50 dark:bg-slate-900/50',
    border: 'border-slate-200 dark:border-slate-700',
    icon: Lock,
    iconColor: 'text-slate-400',
    label: 'Locked'
  },
  needs_review: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-300 dark:border-amber-700',
    icon: Clock,
    iconColor: 'text-amber-500',
    label: 'Needs Review'
  },
  approved: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-300 dark:border-green-700',
    icon: CheckCircle,
    iconColor: 'text-green-500',
    label: 'Approved'
  },
  stale: {
    bg: 'bg-orange-50 dark:bg-orange-900/20',
    border: 'border-orange-300 dark:border-orange-700',
    icon: AlertTriangle,
    iconColor: 'text-orange-500',
    label: 'Stale'
  }
}

export default function CheckpointPanel({
  checkpoint,
  onApprove,
  onReset,
  onChecklistChange,
  loading = false,
  canEdit = true
}: CheckpointPanelProps) {
  const [expanded, setExpanded] = useState(checkpoint.status === 'needs_review')
  const [notes, setNotes] = useState(checkpoint.notes || '')
  const [localChecklist, setLocalChecklist] = useState<ChecklistItem[]>(
    checkpoint.checklist_items.length > 0
      ? checkpoint.checklist_items
      : CHECKPOINT_CONFIG[checkpoint.checkpoint_number]?.defaultChecklist.map(item => ({
          ...item,
          completed: false
        })) || []
  )

  const config = CHECKPOINT_CONFIG[checkpoint.checkpoint_number]
  const statusStyle = STATUS_STYLES[checkpoint.status]
  const StatusIcon = statusStyle.icon
  const HumanIcon = config?.icon || Users

  // Check if all checklist items are complete
  const allChecked = localChecklist.every(item => item.completed)

  const handleChecklistToggle = (itemId: string) => {
    const newChecklist = localChecklist.map(item =>
      item.id === itemId ? { ...item, completed: !item.completed } : item
    )
    setLocalChecklist(newChecklist)
    onChecklistChange(newChecklist)
  }

  const handleApprove = async () => {
    await onApprove(notes || undefined)
  }

  if (!config) {
    return null
  }

  // Locked state - minimal collapsed view
  if (checkpoint.status === 'locked') {
    return (
      <div className={`rounded-lg border-2 ${statusStyle.border} ${statusStyle.bg} opacity-60`}>
        <div className="flex items-center gap-3 px-4 py-3">
          <Lock className="w-5 h-5 text-slate-400" />
          <div className="flex-1">
            <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
              Checkpoint {checkpoint.checkpoint_number}: {config.title}
            </span>
          </div>
          <span className="text-xs text-slate-400 px-2 py-1 bg-slate-200 dark:bg-slate-700 rounded">
            Waiting for previous stage
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className={`rounded-lg border-2 ${statusStyle.border} ${statusStyle.bg} overflow-hidden transition-all`}>
      {/* Header - Always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
      >
        <StatusIcon className={`w-5 h-5 ${statusStyle.iconColor}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-900 dark:text-white">
              Checkpoint {checkpoint.checkpoint_number}: {config.title}
            </span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${config.stageColor}`}>
              {config.stageLabel}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            {config.description}
          </p>
        </div>

        {/* Status badge */}
        <span className={`text-xs px-2 py-1 rounded font-medium ${
          checkpoint.status === 'approved'
            ? 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200'
            : checkpoint.status === 'needs_review'
            ? 'bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200'
            : checkpoint.status === 'stale'
            ? 'bg-orange-200 dark:bg-orange-800 text-orange-800 dark:text-orange-200'
            : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
        }`}>
          {statusStyle.label}
        </span>

        {expanded ? (
          <ChevronDown className="w-5 h-5 text-slate-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0" />
        )}
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="border-t border-slate-200 dark:border-slate-700">
          {/* Stale Warning */}
          {checkpoint.status === 'stale' && checkpoint.stale_reason && (
            <div className="px-4 py-3 bg-orange-100 dark:bg-orange-900/40 border-b border-orange-200 dark:border-orange-800">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-600 dark:text-orange-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-orange-800 dark:text-orange-200">
                    Checkpoint is stale
                  </p>
                  <p className="text-xs text-orange-700 dark:text-orange-300 mt-0.5">
                    {checkpoint.stale_reason}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Human Action Reminder */}
          <div className="px-4 py-3 bg-white/50 dark:bg-slate-800/50">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-amber-200 dark:bg-amber-800">
                <HumanIcon className="w-4 h-4 text-amber-700 dark:text-amber-300" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  {checkpoint.status === 'approved' ? 'You approved this checkpoint' : config.humanAction}
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  {config.humanDetails}
                </p>
              </div>
            </div>
          </div>

          {/* Checklist (only for needs_review or stale) */}
          {(checkpoint.status === 'needs_review' || checkpoint.status === 'stale') && canEdit && (
            <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-700">
              <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Before Approving
              </h4>
              <div className="space-y-2">
                {localChecklist.map(item => (
                  <label
                    key={item.id}
                    className="flex items-start gap-3 cursor-pointer group"
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      <input
                        type="checkbox"
                        checked={item.completed}
                        onChange={() => handleChecklistToggle(item.id)}
                        className="w-4 h-4 rounded border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>
                    <span className={`text-sm ${
                      item.completed
                        ? 'text-slate-500 dark:text-slate-400 line-through'
                        : 'text-slate-700 dark:text-slate-300'
                    }`}>
                      {item.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          {(checkpoint.status === 'needs_review' || checkpoint.status === 'stale') && canEdit && (
            <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-700">
              <label className="block">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Notes (optional)
                </span>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add any notes about this approval..."
                  className="mt-1 w-full px-3 py-2 text-sm border border-slate-200 dark:border-slate-600 rounded-md bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  rows={2}
                />
              </label>
            </div>
          )}

          {/* Approval info (for approved checkpoints) */}
          {checkpoint.status === 'approved' && checkpoint.approved_at && (
            <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span>
                  Approved {new Date(checkpoint.approved_at).toLocaleDateString()} at{' '}
                  {new Date(checkpoint.approved_at).toLocaleTimeString()}
                </span>
              </div>
              {checkpoint.notes && (
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 pl-6">
                  {checkpoint.notes}
                </p>
              )}
            </div>
          )}

          {/* Action Buttons */}
          {canEdit && (
            <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
              <div className="flex items-center justify-end gap-3">
                {/* Reset button for approved/stale */}
                {(checkpoint.status === 'approved' || checkpoint.status === 'stale') && (
                  <button
                    onClick={onReset}
                    disabled={loading}
                    className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Reset Checkpoint
                  </button>
                )}

                {/* Approve button for needs_review/stale */}
                {(checkpoint.status === 'needs_review' || checkpoint.status === 'stale') && (
                  <button
                    onClick={handleApprove}
                    disabled={loading || !allChecked}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Check className="w-4 h-4" />
                    )}
                    Approve & Continue
                  </button>
                )}
              </div>

              {(checkpoint.status === 'needs_review' || checkpoint.status === 'stale') && !allChecked && (
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-2 text-right">
                  Complete all checklist items to approve
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
