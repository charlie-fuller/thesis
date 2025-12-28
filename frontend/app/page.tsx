'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { useAuth } from '@/contexts/AuthContext'
import { apiGet } from '@/lib/api'
import { logger } from '@/lib/logger'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import InterfaceHealthPanel from '@/components/InterfaceHealthPanel'
import GraphStatsPanel from '@/components/GraphStatsPanel'
import GraphVisualization from '@/components/admin/GraphVisualization'

// Lazy load analytics to reduce initial bundle size
const LazyUsageAnalytics = dynamic(() => import('@/components/LazyUsageAnalytics'), {
  loading: () => <div className="flex items-center justify-center py-12"><LoadingSpinner size="lg" /></div>
})

interface ResearchInsight {
  id: string
  topic: string
  focus_area: string
  result_summary: string
  completed_at: string
  web_sources?: Array<{ url: string; title: string }>
}

interface StakeholderMetrics {
  total_stakeholders: number
  average_sentiment: number
  average_alignment: number
  stakeholders_needing_attention: Array<{ id: string; name: string }>
}

type HomeTab = 'research' | 'system' | 'analytics'
type SystemSubTab = 'interfaces' | 'graph-data' | 'graph-visualization'

export default function HomePage() {
  const router = useRouter()
  const { user, session, loading: authLoading, isAdmin } = useAuth()
  const [activeTab, setActiveTab] = useState<HomeTab>('research')
  const [systemSubTab, setSystemSubTab] = useState<SystemSubTab>('interfaces')
  const [insights, setInsights] = useState<ResearchInsight[]>([])
  const [metrics, setMetrics] = useState<StakeholderMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [authLoading, user, router])

  useEffect(() => {
    if (user && session && activeTab === 'research') {
      loadData()
    }
  }, [user, session, activeTab])

  async function loadData() {
    try {
      setLoading(true)
      setError(null)

      const [insightsData, metricsData] = await Promise.all([
        apiGet<{ success: boolean; insights: ResearchInsight[] }>('/api/research/insights?limit=5').catch(() => ({ success: false, insights: [] })),
        apiGet<StakeholderMetrics>('/api/stakeholders/dashboard').catch(() => null)
      ])

      setInsights(insightsData?.insights || [])
      setMetrics(metricsData)
    } catch (err) {
      logger.error('Error loading home data:', err)
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  function formatDate(isoString: string) {
    if (!isoString) return ''
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return ''
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
  }

  function getFocusAreaLabel(area: string) {
    const labels: Record<string, string> = {
      strategic_planning: 'Strategic Planning',
      finance_roi: 'Finance & ROI',
      governance_security: 'Governance & Security',
      legal_compliance: 'Legal & Compliance',
      change_management: 'Change Management',
      technology_architecture: 'Technology',
      knowledge_gap: 'Knowledge Gap',
      manual: 'Custom Research'
    }
    return labels[area] || area
  }

  function getFocusAreaColor(area: string) {
    const colors: Record<string, string> = {
      strategic_planning: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
      finance_roi: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
      governance_security: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
      legal_compliance: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
      change_management: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
      technology_architecture: 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300',
      knowledge_gap: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
      manual: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
    return colors[area] || colors.manual
  }

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

      <main className="flex-1 max-w-5xl mx-auto w-full p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-primary">Dashboard</h1>
          <p className="text-secondary mt-1">Platform overview and insights</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-1 mb-6 border-b border-default">
          <button
            onClick={() => setActiveTab('research')}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === 'research'
                ? 'border-brand text-brand'
                : 'border-transparent text-muted hover:text-primary'
            }`}
          >
            Research
          </button>
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
                onClick={() => setActiveTab('analytics')}
                className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  activeTab === 'analytics'
                    ? 'border-brand text-brand'
                    : 'border-transparent text-muted hover:text-primary'
                }`}
              >
                Analytics
              </button>
            </>
          )}
        </div>

        {/* Quick Navigation */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Link
            href="/chat"
            className="card p-4 hover:shadow-md transition-shadow flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-lg bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-teal-600 dark:text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div className="min-w-0">
              <div className="font-semibold text-primary text-sm">Chat</div>
              <div className="text-xs text-muted truncate">Ask agents</div>
            </div>
          </Link>

          <Link
            href="/meeting-room"
            className="card p-4 hover:shadow-md transition-shadow flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div className="min-w-0">
              <div className="font-semibold text-primary text-sm">Meeting Room</div>
              <div className="text-xs text-muted truncate">Multi-agent</div>
            </div>
          </Link>

          <Link
            href="/intelligence"
            className="card p-4 hover:shadow-md transition-shadow flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="min-w-0">
              <div className="font-semibold text-primary text-sm">Intelligence</div>
              <div className="text-xs text-muted truncate">Stakeholders</div>
            </div>
          </Link>

          <Link
            href="/kb"
            className="card p-4 hover:shadow-md transition-shadow flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <div className="min-w-0">
              <div className="font-semibold text-primary text-sm">KB</div>
              <div className="text-xs text-muted truncate">Documents</div>
            </div>
          </Link>
        </div>

        {/* Tab Content */}
        {activeTab === 'research' && (
          <>
            {/* Summary Stats Row */}
            {metrics && (
              <div className="grid grid-cols-3 gap-4 mb-8">
                <div className="card p-4 text-center">
                  <div className="text-2xl font-bold text-primary">{metrics.total_stakeholders}</div>
                  <div className="text-xs text-muted">Stakeholders</div>
                </div>
                <div className="card p-4 text-center">
                  <div className={`text-2xl font-bold ${metrics.average_sentiment > 0.3 ? 'text-green-600 dark:text-green-400' : metrics.average_sentiment < -0.3 ? 'text-red-600 dark:text-red-400' : 'text-secondary'}`}>
                    {metrics.average_sentiment > 0 ? '+' : ''}{metrics.average_sentiment.toFixed(2)}
                  </div>
                  <div className="text-xs text-muted">Avg Sentiment</div>
                </div>
                <div className="card p-4 text-center">
                  <div className="text-2xl font-bold text-teal-600 dark:text-teal-400">
                    {Math.round(metrics.average_alignment * 100)}%
                  </div>
                  <div className="text-xs text-muted">Avg Alignment</div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner size="lg" />
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
                <p className="text-red-800 dark:text-red-200">{error}</p>
                <button onClick={loadData} className="mt-2 text-sm text-red-600 hover:underline">
                  Try again
                </button>
              </div>
            )}

            {/* Research Insights */}
            {!loading && !error && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-primary">Latest Research</h2>
                  <Link href="/chat" className="text-sm text-brand hover:underline">
                    Ask Atlas for more
                  </Link>
                </div>

                {insights.length > 0 ? (
                  <div className="space-y-4">
                    {insights.map(insight => (
                      <div key={insight.id} className="card p-5">
                        <div className="flex items-start justify-between gap-4 mb-3">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${getFocusAreaColor(insight.focus_area)}`}>
                              {getFocusAreaLabel(insight.focus_area)}
                            </span>
                            <span className="text-xs text-muted">
                              {formatDate(insight.completed_at)}
                            </span>
                          </div>
                        </div>
                        <h3 className="font-medium text-primary mb-2">{insight.topic}</h3>
                        <p className="text-sm text-secondary leading-relaxed">
                          {insight.result_summary}
                        </p>
                        {insight.web_sources && insight.web_sources.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-default">
                            <div className="text-xs text-muted mb-1">Sources:</div>
                            <div className="flex flex-wrap gap-2">
                              {insight.web_sources.slice(0, 3).map((source, idx) => (
                                <a
                                  key={idx}
                                  href={source.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-brand hover:underline truncate max-w-[200px]"
                                  title={source.title}
                                >
                                  {source.title || new URL(source.url).hostname}
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="card p-12 text-center">
                    <div className="flex justify-center mb-4">
                      <svg className="w-12 h-12 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-primary mb-2">No Research Yet</h3>
                    <p className="text-secondary mb-4">
                      Atlas will proactively research GenAI strategy topics.<br />
                      You can also ask Atlas directly for specific research.
                    </p>
                    <Link href="/chat" className="btn-primary inline-flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      Ask Atlas
                    </Link>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* System Health Tab */}
        {activeTab === 'system' && (
          <div className="space-y-6">
            {/* Sub-tab Navigation */}
            <div className="flex gap-1 bg-hover rounded-lg p-1">
              <button
                onClick={() => setSystemSubTab('interfaces')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  systemSubTab === 'interfaces'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                Interfaces
              </button>
              <button
                onClick={() => setSystemSubTab('graph-data')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  systemSubTab === 'graph-data'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                Graph Data
              </button>
              <button
                onClick={() => setSystemSubTab('graph-visualization')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  systemSubTab === 'graph-visualization'
                    ? 'bg-card text-primary shadow-sm'
                    : 'text-muted hover:text-primary'
                }`}
              >
                Graph Visualization
              </button>
            </div>

            {/* Sub-tab Content */}
            {systemSubTab === 'interfaces' && <InterfaceHealthPanel />}
            {systemSubTab === 'graph-data' && <GraphStatsPanel />}
            {systemSubTab === 'graph-visualization' && (
              <div className="card p-4">
                <div className="h-[500px]">
                  <GraphVisualization />
                </div>
              </div>
            )}
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
