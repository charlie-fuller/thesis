'use client'

import { useState, useCallback, DragEvent } from 'react'
import { Calendar, User, AlertCircle, FileText, MessageSquare, Search, Pencil } from 'lucide-react'
import { Task } from './TaskKanbanBoard'

interface TaskCardProps {
  task: Task
  onClick: () => void
}

// Priority colors (1=low, 5=critical)
const PRIORITY_COLORS = {
  1: 'bg-gray-200 dark:bg-gray-700',
  2: 'bg-blue-200 dark:bg-blue-700',
  3: 'bg-yellow-200 dark:bg-yellow-700',
  4: 'bg-orange-200 dark:bg-orange-700',
  5: 'bg-red-200 dark:bg-red-700',
} as const

// Source type icons
const SOURCE_ICONS = {
  transcript: FileText,
  conversation: MessageSquare,
  research: Search,
  manual: Pencil,
  project: AlertCircle,
} as const

export default function TaskCard({ task, onClick }: TaskCardProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragStart = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData('taskId', task.id)
    e.dataTransfer.effectAllowed = 'move'
    setIsDragging(true)

    // Add visual feedback
    setTimeout(() => {
      const el = e.target as HTMLElement
      el.classList.add('opacity-50')
    }, 0)
  }, [task.id])

  const handleDragEnd = useCallback((e: DragEvent<HTMLDivElement>) => {
    setIsDragging(false)
    const el = e.target as HTMLElement
    el.classList.remove('opacity-50')
  }, [])

  // Check urgency
  const now = new Date()
  const dueDate = task.due_date ? new Date(task.due_date) : null
  const isOverdue = dueDate && dueDate < now && task.status !== 'completed'

  // Check if due soon (within 3 days)
  const threeDaysFromNow = new Date(now)
  threeDaysFromNow.setDate(threeDaysFromNow.getDate() + 3)
  const isDueSoon = dueDate && !isOverdue && dueDate <= threeDaysFromNow && task.status !== 'completed'

  // Get source icon
  const SourceIcon = task.source_type ? SOURCE_ICONS[task.source_type as keyof typeof SOURCE_ICONS] : null

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onClick={onClick}
      className={`
        bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700
        p-3 cursor-pointer hover:shadow-md transition-all
        ${isDragging ? 'opacity-50 ring-2 ring-brand' : ''}
        ${task.status === 'blocked' ? 'border-l-4 border-l-orange-500' : ''}
      `}
    >
      {/* Priority indicator */}
      <div className="flex items-start gap-2 mb-2">
        <div
          className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
            PRIORITY_COLORS[task.priority as keyof typeof PRIORITY_COLORS] || PRIORITY_COLORS[3]
          }`}
          title={`Priority: ${task.priority}`}
        />
        <h4 className="text-sm font-medium text-primary line-clamp-2 flex-1">
          {task.title}
        </h4>
      </div>

      {/* Blocker reason */}
      {task.status === 'blocked' && task.blocker_reason && (
        <div className="flex items-start gap-1.5 mb-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded text-xs text-orange-700 dark:text-orange-300">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span className="line-clamp-2">{task.blocker_reason}</span>
        </div>
      )}

      {/* Metadata row */}
      <div className="flex items-center gap-3 text-xs text-muted">
        {/* Assignee */}
        {task.display_assignee && (
          <div className="flex items-center gap-1 truncate max-w-[120px]" title={task.display_assignee}>
            <User className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{task.display_assignee}</span>
          </div>
        )}

        {/* Due date */}
        {task.due_date && (
          <div
            className={`flex items-center gap-1 ${
              isOverdue
                ? 'text-red-600 dark:text-red-400 font-medium'
                : isDueSoon
                  ? 'text-amber-600 dark:text-amber-400 font-medium'
                  : ''
            }`}
            title={isOverdue ? 'Overdue!' : isDueSoon ? 'Due soon!' : `Due: ${task.due_date}`}
          >
            <Calendar className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{formatDate(task.due_date)}</span>
          </div>
        )}

        {/* Source icon */}
        {SourceIcon && (
          <div className="ml-auto" title={`Source: ${task.source_type}`}>
            <SourceIcon className="w-3.5 h-3.5" />
          </div>
        )}
      </div>

    </div>
  )
}

// Helper to format date
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  // Reset time for comparison
  today.setHours(0, 0, 0, 0)
  tomorrow.setHours(0, 0, 0, 0)
  date.setHours(0, 0, 0, 0)

  if (date.getTime() === today.getTime()) {
    return 'Today'
  } else if (date.getTime() === tomorrow.getTime()) {
    return 'Tomorrow'
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }
}
