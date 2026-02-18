'use client'

import { useState } from 'react'
import { CheckSquare, ChevronDown, ChevronUp, Loader2, Pencil } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiPatch } from '@/lib/api'

export interface TaskUpdate {
  task_id: string
  title?: string
  status?: string
  priority?: number
  assignee_name?: string | null
  due_date?: string | null
  description?: string
  blocker_reason?: string | null
  notes?: string
  // Display-only fields injected by SSE or metadata for diffing
  _current_title?: string
  _current_status?: string
  _current_priority?: number
}

interface TaskUpdateCardProps {
  updates: TaskUpdate[]
  projectId?: string | null
  onUpdatesApplied?: (count: number) => void
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'To Do',
  in_progress: 'In Progress',
  blocked: 'Blocked',
  completed: 'Done',
}

const PRIORITY_LABELS: Record<number, string> = {
  1: 'Critical',
  2: 'High',
  3: 'Medium',
  4: 'Low',
  5: 'Lowest',
}

function formatField(key: string, value: unknown): string {
  if (key === 'status' && typeof value === 'string') return STATUS_LABELS[value] || value
  if (key === 'priority' && typeof value === 'number') return PRIORITY_LABELS[value] || String(value)
  if (value === null || value === undefined) return 'None'
  return String(value)
}

function fieldLabel(key: string): string {
  const labels: Record<string, string> = {
    title: 'Title',
    status: 'Status',
    priority: 'Priority',
    assignee_name: 'Assignee',
    due_date: 'Due Date',
    description: 'Description',
    blocker_reason: 'Blocker',
    notes: 'Notes',
  }
  return labels[key] || key
}

export default function TaskUpdateCard({
  updates,
  projectId,
  onUpdatesApplied,
}: TaskUpdateCardProps) {
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(
    new Set(updates.map((_, i) => i))
  )
  const [isExpanded, setIsExpanded] = useState(true)
  const [isApplying, setIsApplying] = useState(false)
  const [isApplied, setIsApplied] = useState(false)

  const toggleSelection = (index: number) => {
    setSelectedIndices(prev => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  const handleApplyUpdates = async () => {
    if (selectedIndices.size === 0) {
      toast.error('Select at least one update to apply')
      return
    }

    setIsApplying(true)
    let successCount = 0

    try {
      const selected = updates.filter((_, i) => selectedIndices.has(i))

      for (const update of selected) {
        const { task_id, _current_title, _current_status, _current_priority, ...fields } = update
        // Remove any internal display fields
        const patchData: Record<string, unknown> = {}
        for (const [k, v] of Object.entries(fields)) {
          if (!k.startsWith('_') && k !== 'task_id') {
            patchData[k] = v
          }
        }

        try {
          await apiPatch(`/api/tasks/${task_id}`, patchData)
          successCount++
        } catch (err) {
          console.error(`Failed to update task ${task_id}:`, err)
        }
      }

      if (successCount > 0) {
        setIsApplied(true)
        toast.success(`Updated ${successCount} task${successCount !== 1 ? 's' : ''}`)
        onUpdatesApplied?.(successCount)
      } else {
        toast.error('Failed to apply updates')
      }
    } catch (err) {
      console.error('Error applying task updates:', err)
      toast.error('Failed to apply updates')
    } finally {
      setIsApplying(false)
    }
  }

  if (isApplied) {
    return (
      <div className="mt-3 border border-green-200 dark:border-green-800 rounded-lg p-3 bg-green-50 dark:bg-green-900/20">
        <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400 font-medium">
          <CheckSquare className="w-4 h-4" />
          <span>{selectedIndices.size} task{selectedIndices.size !== 1 ? 's' : ''} updated</span>
        </div>
      </div>
    )
  }

  // Extract the changed fields for each update (excluding task_id and _current_ fields)
  const getChangedFields = (update: TaskUpdate) => {
    const changed: { key: string; value: unknown }[] = []
    for (const [k, v] of Object.entries(update)) {
      if (k === 'task_id' || k.startsWith('_')) continue
      changed.push({ key: k, value: v })
    }
    return changed
  }

  return (
    <div className="mt-3 border border-default rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800/50 text-sm font-medium text-primary hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Pencil className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span>Task Updates ({updates.length} change{updates.length !== 1 ? 's' : ''})</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted" />
        )}
      </button>

      {isExpanded && (
        <div className="p-3">
          {/* Update list */}
          <div className="space-y-2">
            {updates.map((update, index) => {
              const isSelected = selectedIndices.has(index)
              const changedFields = getChangedFields(update)
              const taskTitle = update._current_title || update.title || update.task_id.slice(0, 8)

              return (
                <div
                  key={index}
                  onClick={() => toggleSelection(index)}
                  className={`flex items-start gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                      : 'bg-gray-50 dark:bg-gray-800/30 border border-transparent hover:border-gray-200 dark:hover:border-gray-700'
                  }`}
                >
                  {/* Checkbox */}
                  <div className="mt-0.5 flex-shrink-0">
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    ) : (
                      <div className="w-4 h-4 border border-gray-300 dark:border-gray-600 rounded" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-primary truncate">
                      {taskTitle}
                    </div>
                    <div className="mt-1 space-y-0.5">
                      {changedFields.map(({ key, value }) => (
                        <div key={key} className="flex items-center gap-1 text-xs text-muted">
                          <span className="font-medium">{fieldLabel(key)}:</span>
                          <span className="text-primary">{formatField(key, value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Apply button */}
          <div className="mt-3 pt-2 border-t border-default">
            <button
              onClick={handleApplyUpdates}
              disabled={isApplying || selectedIndices.size === 0}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md transition-colors"
            >
              {isApplying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Applying updates...</span>
                </>
              ) : (
                <>
                  <Pencil className="w-4 h-4" />
                  <span>Apply {selectedIndices.size} Update{selectedIndices.size !== 1 ? 's' : ''}</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
