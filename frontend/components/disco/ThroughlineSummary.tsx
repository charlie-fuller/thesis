'use client'

import { useState, useCallback } from 'react'
import {
  ChevronDown,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  XCircle,
  Edit3,
  Save,
  X,
  Loader2
} from 'lucide-react'
import { apiPatch } from '@/lib/api'
import type { Throughline } from './ThroughlineEditor'

// ============================================================================
// TYPES
// ============================================================================

interface HypothesisResolution {
  hypothesis_id: string
  status: string
  evidence_summary?: string
}

interface GapStatus {
  gap_id: string
  status: string
  findings?: string
}

interface StateChange {
  description: string
  owner?: string
  deadline?: string
}

interface SoWhat {
  state_change_proposed?: string
  next_human_action?: string
  kill_test?: string
}

export interface ThroughlineResolution {
  hypothesis_resolutions?: HypothesisResolution[]
  gap_statuses?: GapStatus[]
  state_changes?: StateChange[]
  so_what?: SoWhat
}

interface OverrideEntry {
  status: string
  note?: string
}

interface ResolutionAnnotations {
  hypothesis_overrides?: Record<string, OverrideEntry>
  gap_overrides?: Record<string, OverrideEntry>
}

interface ThroughlineSummaryProps {
  throughline: Throughline
  resolution?: ThroughlineResolution | null
  initiativeId?: string
  resolutionAnnotations?: ResolutionAnnotations | null
  onAnnotationsUpdated?: (annotations: ResolutionAnnotations) => void
}

// ============================================================================
// CONSTANTS
// ============================================================================

const HYPOTHESIS_STATUS_OPTIONS = [
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'refuted', label: 'Refuted' },
  { value: 'partially_confirmed', label: 'Partially confirmed' },
  { value: 'inconclusive', label: 'Inconclusive' },
]

const GAP_STATUS_OPTIONS = [
  { value: 'addressed', label: 'Addressed' },
  { value: 'partially_addressed', label: 'Partially addressed' },
  { value: 'still_open', label: 'Still open' },
  { value: 'no_longer_relevant', label: 'No longer relevant' },
]

// ============================================================================
// HELPERS
// ============================================================================

const STATUS_STYLES: Record<string, { bg: string; text: string; icon: typeof CheckCircle }> = {
  confirmed: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', icon: CheckCircle },
  addressed: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', icon: CheckCircle },
  refuted: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', icon: XCircle },
  unaddressed: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', icon: XCircle },
  still_open: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', icon: XCircle },
  no_longer_relevant: { bg: 'bg-slate-100 dark:bg-slate-800', text: 'text-slate-500 dark:text-slate-400', icon: XCircle },
  inconclusive: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400', icon: HelpCircle },
  partially_addressed: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400', icon: HelpCircle },
  partially_confirmed: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400', icon: HelpCircle },
}

function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.inconclusive
  const Icon = style.icon
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text}`}>
      <Icon className="w-3 h-3" />
      {status.replace(/_/g, ' ')}
    </span>
  )
}

function UserOverrideBadge({ status, note }: { status: string; note?: string }) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-400"
      title={note || undefined}
    >
      (You: {status.replace(/_/g, ' ')})
    </span>
  )
}

// ============================================================================
// INLINE OVERRIDE EDITOR
// ============================================================================

function OverrideEditor({
  itemId,
  statusOptions,
  currentOverride,
  onSave,
  onCancel,
  saving,
}: {
  itemId: string
  statusOptions: { value: string; label: string }[]
  currentOverride?: OverrideEntry | null
  onSave: (itemId: string, status: string, note: string) => void
  onCancel: () => void
  saving: boolean
}) {
  const [status, setStatus] = useState(currentOverride?.status || statusOptions[0].value)
  const [note, setNote] = useState(currentOverride?.note || '')

  return (
    <div className="mt-2 p-2.5 bg-violet-50 dark:bg-violet-900/10 border border-violet-200 dark:border-violet-800 rounded-lg space-y-2">
      <div className="flex items-center gap-2">
        <label className="text-xs font-medium text-violet-700 dark:text-violet-300 whitespace-nowrap">
          Your override:
        </label>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="flex-1 text-xs px-2 py-1 border border-violet-300 dark:border-violet-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
        >
          {statusOptions.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
      <input
        type="text"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Add a note (optional)..."
        className="w-full text-xs px-2 py-1 border border-violet-300 dark:border-violet-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400"
      />
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => onSave(itemId, status, note)}
          disabled={saving}
          className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-white bg-violet-600 rounded hover:bg-violet-700 disabled:opacity-50 transition-colors"
        >
          {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
          Save
        </button>
        <button
          onClick={onCancel}
          disabled={saving}
          className="inline-flex items-center gap-1 px-2 py-1 text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
        >
          <X className="w-3 h-3" />
          Cancel
        </button>
      </div>
    </div>
  )
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ThroughlineSummary({
  throughline,
  resolution,
  initiativeId,
  resolutionAnnotations,
  onAnnotationsUpdated,
}: ThroughlineSummaryProps) {
  const [expanded, setExpanded] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const problemCount = throughline.problem_statements?.length || 0
  const hypothesisCount = throughline.hypotheses?.length || 0
  const gapCount = throughline.gaps?.length || 0
  const totalItems = problemCount + hypothesisCount + gapCount

  if (totalItems === 0 && !throughline.desired_outcome_state) return null

  // Build resolution lookup maps
  const hypResMap = new Map(
    (resolution?.hypothesis_resolutions || []).map(hr => [hr.hypothesis_id, hr])
  )
  const gapResMap = new Map(
    (resolution?.gap_statuses || []).map(gs => [gs.gap_id, gs])
  )

  // Build annotation lookup
  const hypOverrides = resolutionAnnotations?.hypothesis_overrides || {}
  const gapOverrides = resolutionAnnotations?.gap_overrides || {}

  const handleSaveOverride = useCallback(async (
    itemId: string,
    status: string,
    note: string,
    type: 'hypothesis' | 'gap',
  ) => {
    if (!initiativeId) return
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {}
      const overrideEntry: OverrideEntry = { status }
      if (note.trim()) overrideEntry.note = note.trim()

      if (type === 'hypothesis') {
        payload.hypothesis_overrides = { [itemId]: overrideEntry }
      } else {
        payload.gap_overrides = { [itemId]: overrideEntry }
      }

      const result = await apiPatch<{ success: boolean; initiative: { resolution_annotations?: ResolutionAnnotations } }>(
        `/api/disco/initiatives/${initiativeId}/resolution-annotations`,
        payload,
      )

      if (result.success && result.initiative?.resolution_annotations && onAnnotationsUpdated) {
        onAnnotationsUpdated(result.initiative.resolution_annotations)
      }
      setEditingId(null)
    } catch (err) {
      console.error('Failed to save resolution override:', err)
    } finally {
      setSaving(false)
    }
  }, [initiativeId, onAnnotationsUpdated])

  const canEdit = !!initiativeId

  return (
    <div className="mt-2">
      {/* Compact pills + toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
      >
        {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        <span className="flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 text-indigo-500" />
          <span className="font-medium">Throughline:</span>
          {problemCount > 0 && (
            <span className="px-1.5 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded">
              {problemCount} problem{problemCount !== 1 ? 's' : ''}
            </span>
          )}
          {hypothesisCount > 0 && (
            <span className="px-1.5 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded">
              {hypothesisCount} hypothes{hypothesisCount !== 1 ? 'es' : 'is'}
            </span>
          )}
          {gapCount > 0 && (
            <span className="px-1.5 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded">
              {gapCount} gap{gapCount !== 1 ? 's' : ''}
            </span>
          )}
          {resolution && (
            <span className="px-1.5 py-0.5 text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded font-medium">
              resolved
            </span>
          )}
        </span>
      </button>

      {/* Expanded detail view */}
      {expanded && (
        <div className="mt-3 p-4 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-lg space-y-4 text-sm">
          {/* Problem Statements */}
          {problemCount > 0 && (
            <div>
              <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1.5">Problem Statements</h4>
              <ul className="space-y-1">
                {throughline.problem_statements!.map((ps, i) => (
                  <li key={i} className="flex items-start gap-2 text-slate-600 dark:text-slate-400">
                    <span className="font-mono text-xs text-slate-400 mt-0.5">{ps.id || `ps-${i + 1}`}</span>
                    <span>{ps.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Hypotheses */}
          {hypothesisCount > 0 && (
            <div>
              <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1.5">Hypotheses</h4>
              <ul className="space-y-1.5">
                {throughline.hypotheses!.map((h, i) => {
                  const hId = h.id || `h-${i + 1}`
                  const res = hypResMap.get(hId)
                  const override = hypOverrides[hId]
                  const isEditing = editingId === `hyp-${hId}`
                  return (
                    <li key={i} className="flex items-start gap-2">
                      <span className="font-mono text-xs text-slate-400 mt-0.5">{hId}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-600 dark:text-slate-400">{h.statement}</span>
                          <span className="text-xs text-slate-400">({h.type || 'assumption'})</span>
                          {res && <StatusBadge status={res.status} />}
                          {override && <UserOverrideBadge status={override.status} note={override.note} />}
                          {canEdit && !isEditing && (
                            <button
                              onClick={() => setEditingId(`hyp-${hId}`)}
                              className="p-0.5 text-slate-400 hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
                              title="Override resolution"
                            >
                              <Edit3 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                        {h.rationale && (
                          <p className="text-xs text-slate-400 mt-0.5">Rationale: {h.rationale}</p>
                        )}
                        {res?.evidence_summary && (
                          <p className="text-xs text-slate-500 mt-0.5 italic">Evidence: {res.evidence_summary}</p>
                        )}
                        {override?.note && !isEditing && (
                          <p className="text-xs text-violet-600 dark:text-violet-400 mt-0.5 italic">Note: {override.note}</p>
                        )}
                        {isEditing && (
                          <OverrideEditor
                            itemId={hId}
                            statusOptions={HYPOTHESIS_STATUS_OPTIONS}
                            currentOverride={override}
                            onSave={(id, status, note) => handleSaveOverride(id, status, note, 'hypothesis')}
                            onCancel={() => setEditingId(null)}
                            saving={saving}
                          />
                        )}
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}

          {/* Gaps */}
          {gapCount > 0 && (
            <div>
              <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1.5">Known Gaps</h4>
              <ul className="space-y-1.5">
                {throughline.gaps!.map((g, i) => {
                  const gId = g.id || `g-${i + 1}`
                  const res = gapResMap.get(gId)
                  const override = gapOverrides[gId]
                  const isEditing = editingId === `gap-${gId}`
                  return (
                    <li key={i} className="flex items-start gap-2">
                      <span className="font-mono text-xs text-slate-400 mt-0.5">{gId}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-600 dark:text-slate-400">{g.description}</span>
                          <span className="text-xs px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded">{g.type || 'data'}</span>
                          {res && <StatusBadge status={res.status} />}
                          {override && <UserOverrideBadge status={override.status} note={override.note} />}
                          {canEdit && !isEditing && (
                            <button
                              onClick={() => setEditingId(`gap-${gId}`)}
                              className="p-0.5 text-slate-400 hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
                              title="Override resolution"
                            >
                              <Edit3 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                        {res?.findings && (
                          <p className="text-xs text-slate-500 mt-0.5 italic">Findings: {res.findings}</p>
                        )}
                        {override?.note && !isEditing && (
                          <p className="text-xs text-violet-600 dark:text-violet-400 mt-0.5 italic">Note: {override.note}</p>
                        )}
                        {isEditing && (
                          <OverrideEditor
                            itemId={gId}
                            statusOptions={GAP_STATUS_OPTIONS}
                            currentOverride={override}
                            onSave={(id, status, note) => handleSaveOverride(id, status, note, 'gap')}
                            onCancel={() => setEditingId(null)}
                            saving={saving}
                          />
                        )}
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}

          {/* Desired Outcome State */}
          {throughline.desired_outcome_state && (
            <div>
              <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1">Desired Outcome State</h4>
              <p className="text-slate-600 dark:text-slate-400">{throughline.desired_outcome_state}</p>
            </div>
          )}

          {/* Resolution: So What? */}
          {resolution?.so_what && (
            <div className="p-3 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg">
              <h4 className="font-medium text-indigo-700 dark:text-indigo-300 mb-2">So What?</h4>
              {resolution.so_what.state_change_proposed && (
                <p className="text-sm text-indigo-600 dark:text-indigo-400 mb-1">
                  <span className="font-medium">State Change:</span> {resolution.so_what.state_change_proposed}
                </p>
              )}
              {resolution.so_what.next_human_action && (
                <p className="text-sm text-indigo-600 dark:text-indigo-400 mb-1">
                  <span className="font-medium">Next Action:</span> {resolution.so_what.next_human_action}
                </p>
              )}
              {resolution.so_what.kill_test && (
                <p className="text-sm text-red-600 dark:text-red-400">
                  <span className="font-medium">Kill Test:</span> {resolution.so_what.kill_test}
                </p>
              )}
            </div>
          )}

          {/* Resolution: State Changes */}
          {resolution?.state_changes && resolution.state_changes.length > 0 && (
            <div>
              <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1.5">Recommended State Changes</h4>
              <ul className="space-y-1">
                {resolution.state_changes.map((sc, i) => (
                  <li key={i} className="text-slate-600 dark:text-slate-400">
                    <span>{sc.description}</span>
                    {sc.owner && <span className="text-xs text-slate-400 ml-2">Owner: {sc.owner}</span>}
                    {sc.deadline && <span className="text-xs text-slate-400 ml-2">By: {sc.deadline}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
