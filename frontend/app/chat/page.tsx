'use client'

import LazyUnifiedWorkspace from '@/components/LazyUnifiedWorkspace'
import LoadingSpinner from '@/components/LoadingSpinner'
import WelcomeModal from '@/components/WelcomeModal'
import PageHeader from '@/components/PageHeader'
import CreateMeetingModal from '@/components/meeting-room/CreateMeetingModal'
import { useSearchParams } from 'next/navigation'
import { Suspense, useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { supabase } from '@/lib/supabase'
import { authenticatedFetch } from '@/lib/api'

// ============================================================================
// TYPES
// ============================================================================

interface MeetingRoom {
  id: string
  title: string
  description: string | null
  meeting_type: string
  status: string
  total_tokens_used: number
  participant_count: number
  autonomous_topic: string | null
  created_at: string
  updated_at: string
}

type TabType = 'chat' | 'meetings'

// ============================================================================
// MEETING ROOMS TAB CONTENT
// ============================================================================

function MeetingRoomsContent() {
  const router = useRouter()
  const [meetings, setMeetings] = useState<MeetingRoom[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    loadMeetings()
  }, [])

  const loadMeetings = async () => {
    try {
      setLoading(true)
      const response = await authenticatedFetch('/api/meeting-rooms')
      const data = await response.json()

      if (data.success) {
        setMeetings(data.meeting_rooms)
      }
    } catch (error) {
      console.error('Error loading meetings:', error)
      toast.error('Failed to load meeting rooms')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateMeeting = async (meetingData: {
    title: string
    description?: string
    meeting_type: string
    participant_agent_ids: string[]
  }) => {
    try {
      const response = await authenticatedFetch('/api/meeting-rooms', {
        method: 'POST',
        body: JSON.stringify(meetingData)
      })

      const data = await response.json()

      if (data.success) {
        toast.success('Meeting room created')
        setShowCreateModal(false)
        router.push(`/meeting-room/${data.meeting_room.id}`)
      } else {
        throw new Error(data.detail || 'Failed to create meeting')
      }
    } catch (error) {
      console.error('Error creating meeting:', error)
      toast.error('Failed to create meeting room')
    }
  }

  const handleDeleteMeeting = async (meetingId: string) => {
    if (!confirm('Are you sure you want to delete this meeting room?')) {
      return
    }

    try {
      const response = await authenticatedFetch(`/api/meeting-rooms/${meetingId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        toast.success('Meeting room deleted')
        setMeetings(meetings.filter(m => m.id !== meetingId))
      } else {
        throw new Error('Failed to delete')
      }
    } catch (error) {
      console.error('Error deleting meeting:', error)
      toast.error('Failed to delete meeting room')
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getMeetingTypeLabel = (type: string) => {
    switch (type) {
      case 'collaboration':
        return 'Collaboration'
      case 'meeting_prep':
        return 'Meeting Prep'
      default:
        return type
    }
  }

  const getMeetingTypeColor = (type: string) => {
    switch (type) {
      case 'collaboration':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
      case 'meeting_prep':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-primary">Meeting Rooms</h2>
            <p className="text-secondary text-sm mt-1">Multi-agent collaboration spaces</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary px-4 py-2 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Meeting
          </button>
        </div>

        {meetings.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-primary mb-2">No meeting rooms yet</h3>
            <p className="text-secondary mb-6">
              Create a meeting room to have multi-agent conversations
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary px-4 py-2"
            >
              Create Your First Meeting
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {meetings.map((meeting) => (
              <div
                key={meeting.id}
                className="bg-card border border-default rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => router.push(`/meeting-room/${meeting.id}`)}
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-medium text-primary truncate flex-1">
                    {meeting.title}
                  </h3>
                  <div className="flex items-center gap-2 ml-2">
                    {meeting.autonomous_topic && (
                      <span className="text-xs px-2 py-1 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400" title={`Topic: ${meeting.autonomous_topic}`}>
                        Autonomous
                      </span>
                    )}
                    <span className={`text-xs px-2 py-1 rounded-full ${getMeetingTypeColor(meeting.meeting_type)}`}>
                      {getMeetingTypeLabel(meeting.meeting_type)}
                    </span>
                  </div>
                </div>

                {meeting.description && (
                  <p className="text-sm text-secondary mb-3 line-clamp-2">
                    {meeting.description}
                  </p>
                )}

                <div className="flex items-center justify-between text-xs text-tertiary">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {meeting.participant_count} agents
                    </span>
                    <span>{formatDate(meeting.updated_at)}</span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteMeeting(meeting.id)
                    }}
                    className="text-red-500 hover:text-red-700 p-1"
                    title="Delete meeting"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreateModal && (
        <CreateMeetingModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateMeeting}
        />
      )}
    </>
  )
}

// ============================================================================
// MAIN PAGE CONTENT
// ============================================================================

function ChatPageContent() {
  const { user, profile, loading, refreshProfile } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const conversationId = searchParams.get('id') || undefined
  const tabParam = searchParams.get('tab')
  const [activeTab, setActiveTab] = useState<TabType>(tabParam === 'meetings' ? 'meetings' : 'chat')
  // Use a separate variable for styling comparisons to avoid TypeScript narrowing issues
  const currentTab: TabType = activeTab
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

  // Sync tab with URL
  useEffect(() => {
    if (tabParam === 'meetings' && activeTab !== 'meetings') {
      setActiveTab('meetings')
    } else if (!tabParam && activeTab !== 'chat') {
      setActiveTab('chat')
    }
  }, [tabParam, activeTab])

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab)
    if (tab === 'meetings') {
      router.push('/chat?tab=meetings')
    } else {
      router.push('/chat')
    }
  }

  const handleOnboardingComplete = async (preferences?: { notificationsEnabled?: boolean; emailDigest?: boolean }) => {
    try {
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

      await refreshProfile()
      setShowWelcomeModal(false)
    } catch (err) {
      console.warn('Error skipping onboarding:', err)
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

      {activeTab === 'chat' ? (
        <LazyUnifiedWorkspace
          clientId={profile.client_id}
          userId={user!.id}
          conversationId={conversationId}
          tabSwitcher={
            <div className="flex justify-center">
              <div className="flex gap-1 bg-hover rounded-lg p-1 w-full max-w-md border border-border">
                <button
                  onClick={() => handleTabChange('chat')}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    currentTab === 'chat'
                      ? 'bg-card text-primary shadow-sm'
                      : 'text-secondary hover:text-primary'
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => handleTabChange('meetings')}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    currentTab === 'meetings'
                      ? 'bg-card text-primary shadow-sm'
                      : 'text-secondary hover:text-primary'
                  }`}
                >
                  Meeting Rooms
                </button>
              </div>
            </div>
          }
        />
      ) : (
        <div className="min-h-screen bg-page">
          <PageHeader />

          {/* Tab Switcher for Meeting Rooms view */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
            <div className="flex justify-center">
              <div className="flex gap-1 bg-hover rounded-lg p-1 w-full max-w-md border border-border">
                <button
                  onClick={() => handleTabChange('chat')}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    currentTab === 'chat'
                      ? 'bg-card text-primary shadow-sm'
                      : 'text-secondary hover:text-primary'
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => handleTabChange('meetings')}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    currentTab === 'meetings'
                      ? 'bg-card text-primary shadow-sm'
                      : 'text-secondary hover:text-primary'
                  }`}
                >
                  Meeting Rooms
                </button>
              </div>
            </div>
          </div>

          <MeetingRoomsContent />
        </div>
      )}
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
