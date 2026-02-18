'use client'

import { useState } from 'react'
import { CheckSquare, ChevronDown, ChevronUp, Loader2, Settings } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiPatch } from '@/lib/api'

export interface ProjectUpdate {
  project_id: string
  status?: string
  next_step?: string
  blockers?: string[]
  description?: string
  current_state?: string
  desired_state?: string
  roi_potential?: number
  implementation_effort?: number
  strategic_alignment?: number
  stakeholder_readiness?: number
}

interface ProjectUpdateCardProps {
  updates: ProjectUpdate
  onUpdateApplied?: () => void
}

const SCORE_FIELDS = ['roi_potential', 'implementation_effort', 'strategic_alignment', 'stakeholder_readiness']

function fieldLabel(key: string): string {
  const labels: Record<string, string> = {
    status: 'Status',
    next_step: 'Next Step',
    blockers: 'Blockers',
    description: 'Description',
    current_state: 'Current State',
    desired_state: 'Desired State',
    roi_potential: 'ROI Potential',
    implementation_effort: 'Implementation Effort',
    strategic_alignment: 'Strategic Alignment',
    stakeholder_readiness: 'Stakeholder Readiness',
  }
  return labels[key] || key
}

function formatValue(key: string, value: unknown): string {
  if (Array.isArray(value)) return value.join(', ') || 'None'
  if (SCORE_FIELDS.includes(key) && typeof value === 'number') return `${value}/5`
  if (value === null || value === undefined) return 'None'
  return String(value)
}

export default function ProjectUpdateCard({
  updates,
  onUpdateApplied,
}: ProjectUpdateCardProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [isApplying, setIsApplying] = useState(false)
  const [isApplied, setIsApplied] = useState(false)

  // Extract changed fields (excluding project_id)
  const changedFields: { key: string; value: unknown }[] = []
  const scoreUpdates: Record<string, number> = {}
  const fieldUpdates: Record<string, unknown> = {}

  for (const [k, v] of Object.entries(updates)) {
    if (k === 'project_id') continue
    changedFields.push({ key: k, value: v })
    if (SCORE_FIELDS.includes(k) && typeof v === 'number') {
      scoreUpdates[k] = v
    } else {
      fieldUpdates[k] = v
    }
  }

  const handleApplyUpdate = async () => {
    setIsApplying(true)

    try {
      // Apply score updates via scores endpoint if any
      if (Object.keys(scoreUpdates).length > 0) {
        await apiPatch(`/api/projects/${updates.project_id}/scores`, scoreUpdates)
      }

      // Apply field updates via main patch endpoint if any
      if (Object.keys(fieldUpdates).length > 0) {
        await apiPatch(`/api/projects/${updates.project_id}`, fieldUpdates)
      }

      setIsApplied(true)
      toast.success('Project updated')
      onUpdateApplied?.()
    } catch (err) {
      console.error('Error applying project update:', err)
      toast.error('Failed to update project')
    } finally {
      setIsApplying(false)
    }
  }

  if (isApplied) {
    return (
      <div className="mt-3 border border-green-200 dark:border-green-800 rounded-lg p-3 bg-green-50 dark:bg-green-900/20">
        <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400 font-medium">
          <CheckSquare className="w-4 h-4" />
          <span>Project updated ({changedFields.length} field{changedFields.length !== 1 ? 's' : ''})</span>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-3 border border-default rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800/50 text-sm font-medium text-primary hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 text-purple-600 dark:text-purple-400" />
          <span>Project Update ({changedFields.length} field{changedFields.length !== 1 ? 's' : ''})</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted" />
        )}
      </button>

      {isExpanded && (
        <div className="p-3">
          {/* Field changes */}
          <div className="space-y-2">
            {changedFields.map(({ key, value }) => (
              <div
                key={key}
                className="flex items-start gap-2 p-2 rounded-md bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800"
              >
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-muted">{fieldLabel(key)}</div>
                  <div className="text-sm text-primary mt-0.5">
                    {SCORE_FIELDS.includes(key) ? (
                      <div className="flex items-center gap-1">
                        <span className="font-medium">{formatValue(key, value)}</span>
                        {typeof value === 'number' && (
                          <div className="flex gap-0.5 ml-1">
                            {[1, 2, 3, 4, 5].map(n => (
                              <div
                                key={n}
                                className={`w-2 h-2 rounded-full ${
                                  n <= (value as number)
                                    ? 'bg-purple-500 dark:bg-purple-400'
                                    : 'bg-gray-200 dark:bg-gray-700'
                                }`}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      formatValue(key, value)
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Apply button */}
          <div className="mt-3 pt-2 border-t border-default">
            <button
              onClick={handleApplyUpdate}
              disabled={isApplying}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md transition-colors"
            >
              {isApplying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Applying update...</span>
                </>
              ) : (
                <>
                  <Settings className="w-4 h-4" />
                  <span>Apply Project Update</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
