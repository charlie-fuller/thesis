'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import { useAuth } from '@/contexts/AuthContext'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageLayout from '@/components/PageLayout'
import InterfaceHealthPanel from '@/components/InterfaceHealthPanel'
import UnifiedDiscoveryPanel from '@/components/discovery/UnifiedDiscoveryPanel'
import GraphStatsPanel from '@/components/GraphStatsPanel'
import GraphVisualizationPanel from '@/components/admin/GraphVisualizationPanel'
import ProcessMapPanel from '@/components/ProcessMapPanel'

// Lazy load analytics to reduce initial bundle size
const LazyUsageAnalytics = dynamic(() => import('@/components/LazyUsageAnalytics'), {
  loading: () => <div className="flex items-center justify-center py-12"><LoadingSpinner size="lg" /></div>
})

const LazyManifestoCompliancePanel = dynamic(() => import('@/components/ManifestoCompliancePanel'), {
  loading: () => <div className="flex items-center justify-center py-12"><LoadingSpinner size="lg" /></div>
})

type HomeTab = 'system' | 'knowledge-graph' | 'analytics' | 'process-map'
type GraphSubTab = 'data' | 'visualization' | 'what-is-this'
type AnalyticsSubTab = 'agent-usage' | 'activity' | 'compliance'

export default function HomePage() {
  const router = useRouter()
  const { user, session, loading: authLoading, isAdmin } = useAuth()
  const [activeTab, setActiveTab] = useState<HomeTab>('analytics')
  const [graphSubTab, setGraphSubTab] = useState<GraphSubTab>('data')
  const [analyticsSubTab, setAnalyticsSubTab] = useState<AnalyticsSubTab>('agent-usage')

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
    <PageLayout>
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
                onClick={() => setActiveTab('analytics')}
                className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  activeTab === 'analytics'
                    ? 'border-brand text-brand'
                    : 'border-transparent text-muted hover:text-primary'
                }`}
              >
                Analytics
              </button>
              <button
                onClick={() => setActiveTab('system')}
                className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  activeTab === 'system'
                    ? 'border-brand text-brand'
                    : 'border-transparent text-muted hover:text-primary'
                }`}
              >
                Discovery Inbox
              </button>
              <button
                onClick={() => setActiveTab('process-map')}
                className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  activeTab === 'process-map'
                    ? 'border-brand text-brand'
                    : 'border-transparent text-muted hover:text-primary'
                }`}
              >
                Process Map
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
        </div>

        {/* Discovery Inbox Tab */}
        {activeTab === 'system' && (
          <div className="space-y-6">
            <UnifiedDiscoveryPanel />
          </div>
        )}

        {/* Knowledge Graph Tab */}
        {activeTab === 'knowledge-graph' && (
          <div className="space-y-6">
            {/* Sub-tab Navigation */}
            <div className="flex gap-1 bg-hover rounded-lg p-1 max-w-md">
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
              <button
                onClick={() => setGraphSubTab('what-is-this')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  graphSubTab === 'what-is-this'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                What is this?
              </button>
            </div>

            {/* Sub-tab Content */}
            {graphSubTab === 'data' && <GraphStatsPanel />}
            {graphSubTab === 'visualization' && <GraphVisualizationPanel />}
            {graphSubTab === 'what-is-this' && (
              <div className="max-w-3xl space-y-6">
                <div className="card p-6">
                  <h2 className="text-lg font-semibold text-primary mb-3">What is a Knowledge Graph?</h2>
                  <p className="text-secondary leading-relaxed">
                    A knowledge graph is a structured representation of information that captures
                    entities (nodes) and the relationships between them (edges). Unlike traditional
                    databases that store data in isolated tables, a knowledge graph connects
                    information in a way that mirrors how concepts relate in the real world.
                  </p>
                </div>

                <div className="card p-6">
                  <h2 className="text-lg font-semibold text-primary mb-3">Why is it Important?</h2>
                  <p className="text-secondary leading-relaxed mb-3">
                    Knowledge graphs enable AI systems to understand context and connections
                    that would otherwise be invisible. When your agents analyze documents,
                    stakeholders, projects, and meetings, the knowledge graph captures how
                    all these elements relate to each other.
                  </p>
                  <ul className="list-disc list-inside space-y-2 text-secondary ml-2">
                    <li><strong className="text-primary">Contextual Understanding:</strong> Agents can see that a document was discussed in a meeting, relates to a project, and involves specific stakeholders</li>
                    <li><strong className="text-primary">Discovery:</strong> Surface hidden connections between people, topics, and initiatives across your organization</li>
                    <li><strong className="text-primary">Memory:</strong> Maintain persistent knowledge that grows over time, not just single conversations</li>
                  </ul>
                </div>

                <div className="card p-6">
                  <h2 className="text-lg font-semibold text-primary mb-3">How Does it Add Value?</h2>
                  <div className="grid gap-4">
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-purple-400 font-medium">1</span>
                      </div>
                      <div>
                        <h3 className="font-medium text-primary">Smarter Agent Responses</h3>
                        <p className="text-secondary text-sm">Agents pull in relevant context from connected entities, providing more informed answers.</p>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-blue-400 font-medium">2</span>
                      </div>
                      <div>
                        <h3 className="font-medium text-primary">Cross-Domain Insights</h3>
                        <p className="text-secondary text-sm">Discover connections between stakeholders, documents, and projects across your organization.</p>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-green-400 font-medium">3</span>
                      </div>
                      <div>
                        <h3 className="font-medium text-primary">Institutional Knowledge</h3>
                        <p className="text-secondary text-sm">Build a growing repository of organizational knowledge that persists beyond individual conversations.</p>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-amber-400 font-medium">4</span>
                      </div>
                      <div>
                        <h3 className="font-medium text-primary">Impact Analysis</h3>
                        <p className="text-secondary text-sm">Understand how changes to one area might affect connected stakeholders, projects, or initiatives.</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card p-6">
                  <h2 className="text-lg font-semibold text-primary mb-3">How is it Used in Thesis?</h2>
                  <p className="text-secondary leading-relaxed mb-3">
                    The knowledge graph automatically syncs data from across the platform:
                  </p>
                  <ul className="list-disc list-inside space-y-2 text-secondary ml-2">
                    <li><strong className="text-primary">Documents</strong> from your Knowledge Base with their topics and categories</li>
                    <li><strong className="text-primary">Stakeholders</strong> and their relationships to projects and initiatives</li>
                    <li><strong className="text-primary">Projects</strong> and their connected documents and team members</li>
                    <li><strong className="text-primary">Meeting Notes</strong> linked to attendees, action items, and discussed topics</li>
                    <li><strong className="text-primary">Tasks</strong> connected to their assignees and related projects</li>
                  </ul>
                  <p className="text-secondary leading-relaxed mt-3">
                    When agents process your queries, they traverse these connections to provide
                    comprehensive answers that consider the full context of your organization&apos;s
                    knowledge and relationships.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {/* Sub-tab Navigation */}
            <div className="flex gap-1 bg-hover rounded-lg p-1 max-w-lg">
              <button
                onClick={() => setAnalyticsSubTab('agent-usage')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  analyticsSubTab === 'agent-usage'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                Agent Usage
              </button>
              <button
                onClick={() => setAnalyticsSubTab('activity')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  analyticsSubTab === 'activity'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                Activity
              </button>
              <button
                onClick={() => setAnalyticsSubTab('compliance')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  analyticsSubTab === 'compliance'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                Compliance
              </button>
            </div>

            {/* Sub-tab Content */}
            {analyticsSubTab === 'agent-usage' && <LazyUsageAnalytics view="agents" />}
            {analyticsSubTab === 'activity' && (
              <>
                <LazyUsageAnalytics view="activity" />
                <InterfaceHealthPanel />
              </>
            )}
            {analyticsSubTab === 'compliance' && <LazyManifestoCompliancePanel />}
          </div>
        )}

        {/* Process Map Tab */}
        {activeTab === 'process-map' && (
          <div>
            <ProcessMapPanel />
          </div>
        )}

      </main>
    </PageLayout>
  )
}
