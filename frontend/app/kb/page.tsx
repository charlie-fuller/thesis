'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import dynamic from 'next/dynamic'

// Lazy load the heavy components
const DocumentsContent = dynamic(() => import('@/components/admin/DocumentsContent'), {
  loading: () => <div className="flex items-center justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div></div>
})

const ConversationsContent = dynamic(() => import('@/components/admin/ConversationsContent'), {
  loading: () => <div className="flex items-center justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div></div>
})

export default function KnowledgeBasePage() {
  const router = useRouter()
  const { user, session, loading: authLoading } = useAuth()
  const [activeTab, setActiveTab] = useState<'documents' | 'conversations'>('documents')

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
    <div className="flex flex-col min-h-screen bg-page">
      <PageHeader />
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
          </div>

          {/* Tab Content */}
          {activeTab === 'documents' && <DocumentsContent />}
          {activeTab === 'conversations' && <ConversationsContent />}
        </div>
      </div>
    </div>
  )
}
