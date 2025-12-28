'use client'

import LazyUnifiedWorkspace from '@/components/LazyUnifiedWorkspace'
import LoadingSpinner from '@/components/LoadingSpinner'
import WelcomeModal from '@/components/WelcomeModal'
import { useSearchParams } from 'next/navigation'
import { Suspense, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import toast from 'react-hot-toast'
import { supabase } from '@/lib/supabase'

function ChatPageContent() {
  const { user, profile, loading, refreshProfile } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const conversationId = searchParams.get('id') || undefined
  const timestamp = searchParams.get('t') || undefined
  const [showWelcomeModal, setShowWelcomeModal] = useState(false)

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth/login')
    }
  }, [loading, user, router])

  // Check if user needs onboarding
  useEffect(() => {
    if (!loading && profile && profile.onboarded === false) {
      setShowWelcomeModal(true)
    }
  }, [loading, profile])

  const handleOnboardingComplete = async (preferences?: { notificationsEnabled?: boolean; emailDigest?: boolean }) => {
    try {
      // Get current session for authentication
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error('No valid session')
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/onboarding/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        credentials: 'include',
        body: JSON.stringify({ preferences })
      })

      if (!response.ok) {
        throw new Error('Failed to complete onboarding')
      }

      // Refresh profile to get updated onboarded status
      await refreshProfile()
      setShowWelcomeModal(false)
      toast.success('Welcome to Thesis! Let\'s get started.')
    } catch (err) {
      console.warn('Error completing onboarding:', err)
      toast.error('Failed to save onboarding preferences')
    }
  }

  const handleOnboardingSkip = async () => {
    try {
      // Get current session for authentication
      const { data: { session } } = await supabase.auth.getSession()

      if (!session?.access_token) {
        throw new Error('No valid session')
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/onboarding/skip`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        },
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Failed to skip onboarding')
      }

      // Refresh profile to get updated onboarded status
      await refreshProfile()
      setShowWelcomeModal(false)
    } catch (err) {
      console.warn('Error skipping onboarding:', err)
      // Still close modal even if API call fails
      setShowWelcomeModal(false)
    }
  }

  // Show loading state while auth is being checked
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-page">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-secondary mt-4">Loading your workspace...</p>
        </div>
      </div>
    )
  }

  // Show error if no profile
  if (!profile) {
    return (
      <div className="flex items-center justify-center h-screen bg-page">
        <div className="text-center max-w-md">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Account Setup Incomplete</h2>
            <p className="text-red-700 mb-4">
              Unable to load your profile. Please try logging in again.
            </p>
            <button
              onClick={() => router.push('/auth/login')}
              className="btn-primary px-4 py-2"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <WelcomeModal
        open={showWelcomeModal}
        userName={profile.name}
        onComplete={handleOnboardingComplete}
        onClose={handleOnboardingSkip}
        allowSkip={true}
      />

      <LazyUnifiedWorkspace
        key={conversationId || timestamp || 'new'}
        clientId={profile.client_id}  // Optional - auto-assigned by backend
        userId={user!.id}
        conversationId={conversationId}
      />
    </>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
      <ChatPageContent />
    </Suspense>
  )
}
