'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import PageLayout from '@/components/PageLayout'
import LoadingSpinner from '@/components/LoadingSpinner'
import TaskKanbanBoard from '@/components/tasks/TaskKanbanBoard'

export default function TasksPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [authLoading, user, router])

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
          <TaskKanbanBoard />
        </div>
      </div>
    </PageLayout>
  )
}
