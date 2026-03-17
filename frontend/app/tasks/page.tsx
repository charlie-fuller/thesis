'use client'

import { Suspense, useEffect, useState, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { LayoutGrid, Network } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { apiGet } from '@/lib/api'
import PageLayout from '@/components/PageLayout'
import LoadingSpinner from '@/components/LoadingSpinner'
import TaskKanbanBoard from '@/components/tasks/TaskKanbanBoard'
import TaskDependencyGraph, { TaskGraphNode } from '@/components/tasks/TaskDependencyGraph'
import type { Task } from '@/components/tasks/TaskKanbanBoard'

function TasksContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, profile, loading: authLoading } = useAuth()
  const [viewMode, setViewMode] = useState<'kanban' | 'graph'>('kanban')
  const [graphTasks, setGraphTasks] = useState<TaskGraphNode[]>([])
  const [graphLoading, setGraphLoading] = useState(false)

  // Get initial project filter from URL
  const initialProjectId = searchParams.get('project')

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [authLoading, user, router])

  // Fetch tasks for graph view
  const fetchGraphTasks = useCallback(async () => {
    setGraphLoading(true)
    try {
      const response = await apiGet<{ success: boolean; tasks: Task[] }>(
        '/api/tasks?status=backlog&status=pending&status=in_progress&status=blocked&limit=500'
      )
      if (response.success && response.tasks) {
        setGraphTasks(response.tasks as TaskGraphNode[])
      }
    } catch (err) {
      console.error('Failed to fetch tasks for graph:', err)
    } finally {
      setGraphLoading(false)
    }
  }, [])

  useEffect(() => {
    if (viewMode === 'graph' && graphTasks.length === 0) {
      fetchGraphTasks()
    }
  }, [viewMode, graphTasks.length, fetchGraphTasks])

  // Show loading state while auth is initializing
  if (authLoading) {
    return (
      <div className="min-h-screen bg-page flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // Don't render if not authenticated
  if (!user) {
    return null
  }

  return (
    <PageLayout>
      <div className="flex-1 p-6">
        <div className="max-w-[1600px] mx-auto">
          {/* View mode toggle */}
          <div className="flex items-center justify-between mb-4">
            <div />
            <div className="flex items-center gap-1 bg-hover rounded-lg p-1">
              <button
                onClick={() => setViewMode('kanban')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  viewMode === 'kanban'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                <LayoutGrid className="w-3.5 h-3.5" />
                Kanban
              </button>
              <button
                onClick={() => setViewMode('graph')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  viewMode === 'graph'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                <Network className="w-3.5 h-3.5" />
                Graph
              </button>
            </div>
          </div>

          {viewMode === 'kanban' ? (
            <TaskKanbanBoard initialProjectId={initialProjectId} />
          ) : graphLoading ? (
            <div className="flex items-center justify-center py-24">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <TaskDependencyGraph
              tasks={graphTasks}
              currentUserId={profile?.id}
              currentUserName={profile?.name}
              highlightMode="mine"
              colorBy="project"
              height={700}
            />
          )}
        </div>
      </div>
    </PageLayout>
  )
}

export default function TasksPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-page flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    }>
      <TasksContent />
    </Suspense>
  )
}
