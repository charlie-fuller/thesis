'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import { useAuth } from '@/contexts/AuthContext'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import InterfaceHealthPanel from '@/components/InterfaceHealthPanel'
import GraphStatsPanel from '@/components/GraphStatsPanel'
import GraphVisualizationPanel from '@/components/admin/GraphVisualizationPanel'

// Lazy load analytics to reduce initial bundle size
const LazyUsageAnalytics = dynamic(() => import('@/components/LazyUsageAnalytics'), {
  loading: () => <div className="flex items-center justify-center py-12"><LoadingSpinner size="lg" /></div>
})

type HomeTab = 'system' | 'knowledge-graph' | 'analytics'
type GraphSubTab = 'data' | 'visualization'

export default function HomePage() {
  const router = useRouter()
  const { user, session, loading: authLoading, isAdmin } = useAuth()
  const [activeTab, setActiveTab] = useState<HomeTab>('system')
  const [graphSubTab, setGraphSubTab] = useState<GraphSubTab>('data')

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [authLoading, user, router])

  if (authLoading) {
    return (
      <div className="min-h-screen bg-page flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-brand mb-2">Thesis</h1>
          <p className="text-muted mb-4">Loading...</p>
          <LoadingSpinner size="lg" />
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="flex flex-col min-h-screen bg-page">
      <PageHeader />

      <main className="flex-1 mx-auto w-full p-6 max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-primary">Dashboard</h1>
          <p className="text-secondary mt-1">Platform overview and insights</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-1 mb-6 border-b border-default">
          {isAdmin && (
            <>
              <button
                onClick={() => setActiveTab('system')}
                className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  activeTab === 'system'
                    ? 'border-brand text-brand'
                    : 'border-transparent text-muted hover:text-primary'
                }`}
              >
                System Health
              </button>
              <button
                onClick={() => setActiveTab('knowledge-graph')}
                className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  activeTab === 'knowledge-graph'
                    ? 'border-brand text-brand'
                    : 'border-transparent text-muted hover:text-primary'
                }`}
              >
                Knowledge Graph
              </button>
            </>
          )}
          {isAdmin && (
            <button
              onClick={() => setActiveTab('analytics')}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === 'analytics'
                  ? 'border-brand text-brand'
                  : 'border-transparent text-muted hover:text-primary'
              }`}
            >
              Analytics
            </button>
          )}
        </div>

        {/* System Health Tab */}
        {activeTab === 'system' && (
          <div className="space-y-6">
            <InterfaceHealthPanel />
          </div>
        )}

        {/* Knowledge Graph Tab */}
        {activeTab === 'knowledge-graph' && (
          <div className="space-y-6">
            {/* Sub-tab Navigation */}
            <div className="flex gap-1 bg-hover rounded-lg p-1 max-w-xs">
              <button
                onClick={() => setGraphSubTab('data')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  graphSubTab === 'data'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                Data
              </button>
              <button
                onClick={() => setGraphSubTab('visualization')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  graphSubTab === 'visualization'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                Visualization
              </button>
            </div>

            {/* Sub-tab Content */}
            {graphSubTab === 'data' && <GraphStatsPanel />}
            {graphSubTab === 'visualization' && <GraphVisualizationPanel />}
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div>
            <LazyUsageAnalytics />
          </div>
        )}
      </main>
    </div>
  )
}
