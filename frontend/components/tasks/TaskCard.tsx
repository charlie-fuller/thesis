'use client'

import { useState, useCallback, useRef, useEffect, DragEvent, MouseEvent } from 'react'
import { Calendar, User, AlertCircle, FileText, MessageSquare, Search, Pencil, ChevronDown, GitBranch, FolderOpen } from 'lucide-react'
import { Task } from './TaskKanbanBoard'

interface Stakeholder {
  id: string
  name: string
  role: string | null
}

interface TaskCardProps {
  task: Task
  onClick: () => void
  stakeholders?: Stakeholder[]
  onAssigneeChange?: (taskId: string, stakeholderId: string | null) => void
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

export default function TaskCard({ task, onClick, stakeholders = [], onAssigneeChange }: TaskCardProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [showAssigneeDropdown, setShowAssigneeDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: Event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowAssigneeDropdown(false)
      }
    }
    if (showAssigneeDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showAssigneeDropdown])

  const handleAssigneeClick = (e: MouseEvent) => {
    e.stopPropagation() // Prevent card click
    if (onAssigneeChange && stakeholders.length > 0) {
      setShowAssigneeDropdown(!showAssigneeDropdown)
    }
  }

  const handleSelectAssignee = (stakeholderId: string | null) => {
    if (onAssigneeChange) {
      onAssigneeChange(task.id, stakeholderId)
    }
    setShowAssigneeDropdown(false)
  }

  const handleDragStart = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData('taskId', task.id)
    e.dataTransfer.setData('sourceStatus', task.status)
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
      {/* Priority indicator + Title */}
      <div className="flex items-start gap-2 mb-2">
        <div
          className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
            PRIORITY_COLORS[task.priority as keyof typeof PRIORITY_COLORS] || PRIORITY_COLORS[3]
          }`}
          title={`Priority: ${task.priority}`}
        />
        <h4 className="text-sm font-medium text-primary line-clamp-2 flex-1">
          {task.sequence_number != null && (
            <span className="font-mono text-muted">{String(task.sequence_number).padStart(2, '0')} — </span>
          )}
          {task.title}
        </h4>
      </div>

      {/* Linked project */}
      {task.project_code && (
        <div className="flex items-center gap-1.5 mb-2 text-xs text-blue-600 dark:text-blue-400">
          <FolderOpen className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate" title={task.project_title || task.project_code}>
            {task.project_code}{task.project_title ? ` — ${task.project_title}` : ''}
          </span>
        </div>
      )}

      {/* Blocker reason */}
      {task.status === 'blocked' && task.blocker_reason && (
        <div className="flex items-start gap-1.5 mb-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded text-xs text-orange-700 dark:text-orange-300">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span className="line-clamp-2">{task.blocker_reason}</span>
        </div>
      )}

      {/* Metadata row */}
      <div className="flex items-center gap-3 text-xs text-muted">
        {/* Assignee with dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={handleAssigneeClick}
            className={`flex items-center gap-1 truncate max-w-[140px] rounded px-1 py-0.5 -ml-1 transition-colors ${
              onAssigneeChange && stakeholders.length > 0
                ? 'hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer'
                : ''
            }`}
            title={task.display_assignee || 'Unassigned'}
          >
            <User className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{task.display_assignee || 'Unassigned'}</span>
            {onAssigneeChange && stakeholders.length > 0 && (
              <ChevronDown className="w-3 h-3 flex-shrink-0" />
            )}
          </button>
          {showAssigneeDropdown && (
            <div className="absolute left-0 top-full mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50 max-h-48 overflow-y-auto">
              <button
                onClick={() => handleSelectAssignee(null)}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                  !task.assignee_stakeholder_id ? 'bg-gray-100 dark:bg-gray-700 font-medium' : ''
                }`}
              >
                Unassigned
              </button>
              {stakeholders.map(s => (
                <button
                  key={s.id}
                  onClick={() => handleSelectAssignee(s.id)}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                    task.assignee_stakeholder_id === s.id ? 'bg-gray-100 dark:bg-gray-700 font-medium' : ''
                  }`}
                >
                  {s.name}
                  {s.role && <span className="text-muted ml-1">({s.role})</span>}
                </button>
              ))}
            </div>
          )}
        </div>

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

        {/* Dependency indicator */}
        {task.depends_on && task.depends_on.length > 0 && (
          <div className="flex items-center gap-1 text-purple-600 dark:text-purple-400" title={`Depends on ${task.depends_on.length} task${task.depends_on.length !== 1 ? 's' : ''}`}>
            <GitBranch className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{task.depends_on.length}</span>
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
