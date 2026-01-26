'use client'

import { useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'

interface DiscoLayoutProps {
  children: React.ReactNode
}

export default function DiscoLayout({ children }: DiscoLayoutProps) {
  const { user, profile, loading, hasDiscoAccess } = useAuth()
  const router = useRouter()

  // Check DISCo access
  useEffect(() => {
    if (!loading) {
      // Not logged in - redirect to login
      if (!user) {
        router.push('/auth/login')
        return
      }

      // No DISCo access - redirect to home
      if (profile && !hasDiscoAccess) {
        router.push('/')
        return
      }
    }
  }, [loading, user, profile, router, hasDiscoAccess])

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-page">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-muted mt-4">Loading...</p>
        </div>
      </div>
    )
  }

  // Show loading state while redirecting users without access
  if (!user || !hasDiscoAccess) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-page">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-muted mt-4">Redirecting...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen bg-page flex flex-col">
      {/* Top Navigation - using shared PageHeader */}
      <PageHeader />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
