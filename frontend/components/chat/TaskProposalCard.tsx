'use client'

import { useState } from 'react'
import { CheckSquare, Square, ArrowRight, Calendar, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiPost } from '@/lib/api'

export interface TaskProposal {
  sequence: number
  title: string
  description?: string | null
  priority: number
  due_date?: string | null
  category?: string | null
  team?: string | null
  assignee_name?: string | null
  depends_on: number[]
  tags?: string[]
}

interface TaskProposalCardProps {
  proposals: TaskProposal[]
  projectId?: string | null
  conversationId?: string | null
  onTasksCreated?: (count: number, taskIds: string[]) => void
}

const PRIORITY_LABELS: Record<number, { label: string; color: string }> = {
  1: { label: 'Critical', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  2: { label: 'High', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
  3: { label: 'Medium', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
  4: { label: 'Low', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  5: { label: 'Lowest', color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
}

export default function TaskProposalCard({
  proposals,
  projectId,
  conversationId,
  onTasksCreated
}: TaskProposalCardProps) {
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(
    new Set(proposals.map((_, i) => i))
  )
  const [isExpanded, setIsExpanded] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [isCreated, setIsCreated] = useState(false)

  const toggleSelection = (index: number) => {
    setSelectedIndices(prev => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  const toggleAll = () => {
    if (selectedIndices.size === proposals.length) {
      setSelectedIndices(new Set())
    } else {
      setSelectedIndices(new Set(proposals.map((_, i) => i)))
    }
  }

  const handleCreateTasks = async () => {
    if (selectedIndices.size === 0) {
      toast.error('Select at least one task to create')
      return
    }

    setIsCreating(true)

    try {
      const selectedProposals = proposals.filter((_, i) => selectedIndices.has(i))

      // Build bulk request with depends_on_indices mapping
      const tasks = selectedProposals.map((p, idx) => ({
        title: p.title,
        description: p.description || null,
        priority: p.priority,
        due_date: p.due_date || null,
        category: p.category || null,
        tags: p.tags || [],
        team: p.team || null,
        assignee_name: p.assignee_name || null,
        sequence_number: p.sequence,
        // Map depends_on sequence numbers to indices in the selected array
        depends_on_indices: (p.depends_on || [])
          .map(depSeq => selectedProposals.findIndex(sp => sp.sequence === depSeq))
          .filter(i => i >= 0),
      }))

      const response = await apiPost<{ success: boolean; count: number; tasks: { id: string }[] }>('/api/tasks/bulk', {
        tasks,
        linked_project_id: projectId || null,
        source_conversation_id: conversationId || null,
      })

      if (response.success) {
        setIsCreated(true)
        toast.success(`Created ${response.count} task${response.count !== 1 ? 's' : ''}!`)
        if (onTasksCreated) {
          onTasksCreated(response.count, response.tasks.map(t => t.id))
        }
      } else {
        toast.error('Failed to create tasks')
      }
    } catch (err) {
      console.error('Error creating tasks:', err)
      toast.error('Failed to create tasks')
    } finally {
      setIsCreating(false)
    }
  }

  if (isCreated) {
    return (
      <div className="mt-3 border border-green-200 dark:border-green-800 rounded-lg p-3 bg-green-50 dark:bg-green-900/20">
        <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400 font-medium">
          <CheckSquare className="w-4 h-4" />
          <span>{selectedIndices.size} task{selectedIndices.size !== 1 ? 's' : ''} created on your board</span>
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
          <CheckSquare className="w-4 h-4 text-teal-600 dark:text-teal-400" />
          <span>Task Plan ({proposals.length} tasks)</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted" />
        )}
      </button>

      {isExpanded && (
        <div className="p-3">
          {/* Select all toggle */}
          <div className="flex items-center justify-between mb-2 pb-2 border-b border-default">
            <button
              onClick={toggleAll}
              className="text-xs text-muted hover:text-primary transition-colors"
            >
              {selectedIndices.size === proposals.length ? 'Deselect all' : 'Select all'}
            </button>
            <span className="text-xs text-muted">
              {selectedIndices.size} of {proposals.length} selected
            </span>
          </div>

          {/* Task list */}
          <div className="space-y-2">
            {proposals.map((proposal, index) => {
              const isSelected = selectedIndices.has(index)
              const priority = PRIORITY_LABELS[proposal.priority] || PRIORITY_LABELS[3]

              return (
                <div
                  key={index}
                  onClick={() => toggleSelection(index)}
                  className={`flex items-start gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-800'
                      : 'bg-gray-50 dark:bg-gray-800/30 border border-transparent hover:border-gray-200 dark:hover:border-gray-700'
                  }`}
                >
                  {/* Checkbox */}
                  <div className="mt-0.5 flex-shrink-0">
                    {isSelected ? (
                      <CheckSquare className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                    ) : (
                      <Square className="w-4 h-4 text-muted" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      {/* Sequence number */}
                      <span className="text-xs font-mono text-muted bg-gray-200 dark:bg-gray-700 rounded px-1.5 py-0.5">
                        #{proposal.sequence}
                      </span>
                      {/* Title */}
                      <span className="text-sm font-medium text-primary truncate">
                        {proposal.title}
                      </span>
                    </div>

                    {/* Description */}
                    {proposal.description && (
                      <p className="text-xs text-muted mt-0.5 line-clamp-2">
                        {proposal.description}
                      </p>
                    )}

                    {/* Metadata row */}
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {/* Priority badge */}
                      <span className={`text-xs px-1.5 py-0.5 rounded ${priority.color}`}>
                        {priority.label}
                      </span>

                      {/* Dependencies */}
                      {proposal.depends_on && proposal.depends_on.length > 0 && (
                        <span className="text-xs text-muted flex items-center gap-0.5">
                          <ArrowRight className="w-3 h-3" />
                          Depends on: {proposal.depends_on.map(d => `#${d}`).join(', ')}
                        </span>
                      )}

                      {/* Due date */}
                      {proposal.due_date && (
                        <span className="text-xs text-muted flex items-center gap-0.5">
                          <Calendar className="w-3 h-3" />
                          {proposal.due_date}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Create button */}
          <div className="mt-3 pt-2 border-t border-default">
            <button
              onClick={handleCreateTasks}
              disabled={isCreating || selectedIndices.size === 0}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md transition-colors"
            >
              {isCreating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Creating tasks...</span>
                </>
              ) : (
                <>
                  <CheckSquare className="w-4 h-4" />
                  <span>Create {selectedIndices.size} Task{selectedIndices.size !== 1 ? 's' : ''}</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
