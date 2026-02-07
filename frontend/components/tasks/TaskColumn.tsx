'use client'

import { useState, useCallback, useMemo, useEffect, useRef, DragEvent } from 'react'
import { Plus, ArrowUpDown } from 'lucide-react'
import { Task } from './TaskKanbanBoard'
import TaskCard from './TaskCard'

type SortOption = 'priority-desc' | 'priority-asc' | 'due-asc' | 'due-desc' | 'created-desc' | 'created-asc' | 'alpha' | 'sequence'

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'sequence', label: 'Sequence (#01, #02...)' },
  { value: 'priority-desc', label: 'Priority (High \u2192 Low)' },
  { value: 'priority-asc', label: 'Priority (Low \u2192 High)' },
  { value: 'due-asc', label: 'Due Date (Soonest)' },
  { value: 'due-desc', label: 'Due Date (Latest)' },
  { value: 'created-desc', label: 'Created (Newest)' },
  { value: 'created-asc', label: 'Created (Oldest)' },
  { value: 'alpha', label: 'Alphabetical' },
]

interface Stakeholder {
  id: string
  name: string
  role: string | null
}

interface TaskColumnProps {
  id: string
  title: string
  tasks: Task[]
  count: number
  color: string
  headerColor: string
  onDrop: (taskId: string, newStatus: Task['status'], position?: number) => void
  onTaskClick: (task: Task) => void
  onAddTask: (status: Task['status']) => void
  stakeholders?: Stakeholder[]
  onAssigneeChange?: (taskId: string, stakeholderId: string | null) => void
}

export default function TaskColumn({
  id,
  title,
  tasks,
  count,
  color,
  headerColor,
  onDrop,
  onTaskClick,
  onAddTask,
  stakeholders = [],
  onAssigneeChange,
}: TaskColumnProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [sortBy, setSortBy] = useState<SortOption>('priority-desc')
  const [showSortMenu, setShowSortMenu] = useState(false)
  const sortMenuRef = useRef<HTMLDivElement>(null)

  // Close sort menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (sortMenuRef.current && !sortMenuRef.current.contains(e.target as Node)) {
        setShowSortMenu(false)
      }
    }
    if (showSortMenu) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showSortMenu])

  // Sort tasks based on selected option
  const sortedTasks = useMemo(() => {
    const sorted = [...tasks]
    switch (sortBy) {
      case 'sequence':
        return sorted.sort((a, b) => {
          if (a.sequence_number == null && b.sequence_number == null) return 0
          if (a.sequence_number == null) return 1
          if (b.sequence_number == null) return -1
          return a.sequence_number - b.sequence_number
        })
      case 'priority-desc':
        return sorted.sort((a, b) => (b.priority || 0) - (a.priority || 0))
      case 'priority-asc':
        return sorted.sort((a, b) => (a.priority || 0) - (b.priority || 0))
      case 'due-asc':
        return sorted.sort((a, b) => {
          if (!a.due_date && !b.due_date) return 0
          if (!a.due_date) return 1
          if (!b.due_date) return -1
          return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
        })
      case 'due-desc':
        return sorted.sort((a, b) => {
          if (!a.due_date && !b.due_date) return 0
          if (!a.due_date) return 1
          if (!b.due_date) return -1
          return new Date(b.due_date).getTime() - new Date(a.due_date).getTime()
        })
      case 'created-desc':
        return sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      case 'created-asc':
        return sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      case 'alpha':
        return sorted.sort((a, b) => a.title.localeCompare(b.title))
      default:
        return sorted
    }
  }, [tasks, sortBy])

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    // Only set to false if we're actually leaving the column, not entering a child
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragOver(false)
    }
  }, [])

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)

    const taskId = e.dataTransfer.getData('taskId')
    if (taskId) {
      // Calculate position based on where dropped
      const position = tasks.length // Add to end for now
      onDrop(taskId, id as Task['status'], position)
    }
  }, [id, tasks.length, onDrop])

  return (
    <div
      className={`flex flex-col w-80 min-w-80 rounded-lg ${color} ${
        isDragOver ? 'ring-2 ring-brand ring-offset-2' : ''
      } transition-all`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Column Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <h3 className={`font-semibold ${headerColor}`}>{title}</h3>
          <button
            onClick={() => onAddTask(id as Task['status'])}
            className={`p-1 rounded hover:bg-white/50 dark:hover:bg-black/20 transition-colors ${headerColor}`}
            title={`Add task to ${title}`}
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center gap-2">
          {/* Sort Dropdown */}
          <div className="relative" ref={sortMenuRef}>
            <button
              onClick={() => setShowSortMenu(!showSortMenu)}
              className={`p-1 rounded hover:bg-white/50 dark:hover:bg-black/20 transition-colors ${headerColor}`}
              title="Sort tasks"
            >
              <ArrowUpDown className="w-4 h-4" />
            </button>
            {showSortMenu && (
              <div className="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                {SORT_OPTIONS.map(option => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setSortBy(option.value)
                      setShowSortMenu(false)
                    }}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg ${
                      sortBy === option.value ? 'bg-gray-100 dark:bg-gray-700 font-medium' : ''
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <span className={`px-2 py-0.5 text-sm font-medium rounded-full ${headerColor} bg-white/50 dark:bg-black/20`}>
            {count}
          </span>
        </div>
      </div>

      {/* Task List */}
      <div className="flex-1 p-2 space-y-2 min-h-[200px] max-h-[calc(100vh-280px)] overflow-y-auto">
        {sortedTasks.length === 0 ? (
          <div className="flex items-center justify-center h-24 text-muted text-sm">
            No tasks
          </div>
        ) : (
          sortedTasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              onClick={() => onTaskClick(task)}
              stakeholders={stakeholders}
              onAssigneeChange={onAssigneeChange}
            />
          ))
        )}
      </div>
    </div>
  )
}
