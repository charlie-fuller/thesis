'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import PageLayout from '@/components/PageLayout'
import LoadingSpinner from '@/components/LoadingSpinner'
import dynamic from 'next/dynamic'

// Lazy load the heavy components
const KBDocumentsContent = dynamic(() => import('@/components/kb/KBDocumentsContent'), {
  loading: () => <div className="flex items-center justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div></div>
})

const ConversationsContent = dynamic(() => import('@/components/admin/ConversationsContent'), {
  loading: () => <div className="flex items-center justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div></div>
})

const KBDataMap = dynamic(() => import('@/components/kb/KBDataMap'), {
  loading: () => <div className="flex items-center justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div></div>
})

export default function KnowledgeBasePage() {
  const router = useRouter()
  const { user, session, loading: authLoading } = useAuth()
  const [activeTab, setActiveTab] = useState<'documents' | 'conversations' | 'datamap'>('documents')

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
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-primary mb-6">Knowledge Base</h1>

          {/* Tabs */}
          <div className="flex gap-1 mb-6 border-b border-default">
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === 'documents'
                  ? 'border-brand text-brand'
                  : 'border-transparent text-muted hover:text-primary'
              }`}
            >
              Documents
            </button>
            <button
              onClick={() => setActiveTab('conversations')}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === 'conversations'
                  ? 'border-brand text-brand'
                  : 'border-transparent text-muted hover:text-primary'
              }`}
            >
              Conversations
            </button>
            <button
              onClick={() => setActiveTab('datamap')}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === 'datamap'
                  ? 'border-brand text-brand'
                  : 'border-transparent text-muted hover:text-primary'
              }`}
            >
              Data Map
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'documents' && (
            <Suspense fallback={<div className="flex items-center justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div></div>}>
              <KBDocumentsContent />
            </Suspense>
          )}
          {activeTab === 'conversations' && <ConversationsContent />}
          {activeTab === 'datamap' && (
            <Suspense fallback={<div className="flex items-center justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div></div>}>
              <KBDataMap />
            </Suspense>
          )}
        </div>
      </div>
    </PageLayout>
  )
}
