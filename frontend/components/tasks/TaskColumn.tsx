'use client'

import { useState, useCallback, DragEvent } from 'react'
import { Plus } from 'lucide-react'
import { Task } from './TaskKanbanBoard'
import TaskCard from './TaskCard'

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
}: TaskColumnProps) {
  const [isDragOver, setIsDragOver] = useState(false)

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
        <span className={`px-2 py-0.5 text-sm font-medium rounded-full ${headerColor} bg-white/50 dark:bg-black/20`}>
          {count}
        </span>
      </div>

      {/* Task List */}
      <div className="flex-1 p-2 space-y-2 min-h-[200px] max-h-[calc(100vh-280px)] overflow-y-auto">
        {tasks.length === 0 ? (
          <div className="flex items-center justify-center h-24 text-muted text-sm">
            No tasks
          </div>
        ) : (
          tasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              onClick={() => onTaskClick(task)}
            />
          ))
        )}
      </div>
    </div>
  )
}
