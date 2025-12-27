'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { apiGet } from '@/lib/api'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'

interface DashboardMetrics {
  total_stakeholders: number
  engagement_distribution: Record<string, number>
  average_sentiment: number
  average_alignment: number
  recent_concerns: Array<{
    id: string
    stakeholder_name: string
    content: string
    created_at: string
  }>
  stakeholders_needing_attention: Array<{
    id: string
    name: string
    sentiment_score: number
    sentiment_trend: string
    engagement_level: string
    key_concerns: string[]
  }>
}

interface RecentTranscript {
  id: string
  title: string
  meeting_date: string
  stakeholder_count: number
  processed_at: string
}

const ENGAGEMENT_LEVELS = ['champion', 'supporter', 'neutral', 'skeptic', 'blocker']

export default function ThesisDashboard() {
  const router = useRouter()
  const { user, loading: authLoading, effectiveRole } = useAuth()
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [recentTranscripts, setRecentTranscripts] = useState<RecentTranscript[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    } else if (!authLoading && effectiveRole === 'admin') {
      router.push('/admin')
    }
  }, [authLoading, user, effectiveRole, router])

  useEffect(() => {
    if (user && effectiveRole !== 'admin') {
      loadDashboardData()
    }
  }, [user, effectiveRole])

  async function loadDashboardData() {
    try {
      setLoading(true)
      setError(null)

      const [metricsData, transcriptsData] = await Promise.all([
        apiGet<DashboardMetrics>('/api/stakeholders/dashboard').catch(() => null),
        apiGet<{ transcripts: RecentTranscript[] }>('/api/transcripts/?limit=5').catch(() => ({ transcripts: [] }))
      ])

      setMetrics(metricsData)
      setRecentTranscripts(transcriptsData?.transcripts || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  function getSentimentColor(score: number) {
    if (score > 0.3) return 'text-green-600 dark:text-green-400'
    if (score < -0.3) return 'text-red-600 dark:text-red-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  function getEngagementBadge(level: string) {
    switch (level) {
      case 'champion':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      case 'supporter':
        return 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300'
      case 'neutral':
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
      case 'skeptic':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
      case 'blocker':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
  }

  function formatDate(isoString: string) {
    if (!isoString) return ''
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return ''
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // Show loading while auth is being checked
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

  // Don't render if not authenticated or if admin (they get redirected)
  if (!user || effectiveRole === 'admin') {
    return null
  }

  return (
    <div className="flex flex-col min-h-screen bg-page">
      <PageHeader />

      <main className="flex-1 max-w-7xl mx-auto w-full p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-primary">
            Morning Briefing
          </h1>
          <p className="text-secondary mt-1">
            Your GenAI strategy intelligence at a glance
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">{error}</p>
            <button onClick={loadDashboardData} className="mt-2 text-sm text-red-600 hover:underline">
              Try again
            </button>
          </div>
        ) : (
          <>
            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <Link
                href="/chat"
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow flex items-center gap-4"
              >
                <div className="w-12 h-12 rounded-lg bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center">
                  <svg className="w-6 h-6 text-teal-600 dark:text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Chat with Agents</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Ask Atlas, Fortuna, or other specialists</p>
                </div>
              </Link>

              <Link
                href="/transcripts"
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow flex items-center gap-4"
              >
                <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">Upload Transcript</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Analyze meetings with Oracle</p>
                </div>
              </Link>

              <Link
                href="/stakeholders"
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow flex items-center gap-4"
              >
                <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100">View Stakeholders</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Track sentiment and alignment</p>
                </div>
              </Link>
            </div>

            {/* Metrics Row */}
            {metrics && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {metrics.total_stakeholders}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Total Stakeholders</div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                  <div className={`text-3xl font-bold ${getSentimentColor(metrics.average_sentiment)}`}>
                    {metrics.average_sentiment > 0 ? '+' : ''}{metrics.average_sentiment.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Avg Sentiment</div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                  <div className="text-3xl font-bold text-teal-600 dark:text-teal-400">
                    {Math.round(metrics.average_alignment * 100)}%
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Avg Alignment</div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                  <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                    {metrics.stakeholders_needing_attention.length}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Need Attention</div>
                </div>
              </div>
            )}

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Stakeholders Needing Attention */}
              {metrics && metrics.stakeholders_needing_attention.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-orange-200 dark:border-orange-800 p-6">
                  <h3 className="text-lg font-semibold text-orange-700 dark:text-orange-300 mb-4">
                    Stakeholders Needing Attention
                  </h3>
                  <div className="space-y-3">
                    {metrics.stakeholders_needing_attention.slice(0, 5).map(stakeholder => (
                      <Link
                        key={stakeholder.id}
                        href={`/stakeholders/${stakeholder.id}`}
                        className="flex items-center justify-between p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-colors"
                      >
                        <div>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {stakeholder.name}
                          </span>
                          {stakeholder.key_concerns.length > 0 && (
                            <p className="text-sm text-orange-600 dark:text-orange-400 mt-0.5">
                              {stakeholder.key_concerns[0]}
                            </p>
                          )}
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full capitalize ${getEngagementBadge(stakeholder.engagement_level)}`}>
                          {stakeholder.engagement_level}
                        </span>
                      </Link>
                    ))}
                  </div>
                  <Link
                    href="/stakeholders"
                    className="block mt-4 text-sm text-orange-600 dark:text-orange-400 hover:underline text-center"
                  >
                    View all stakeholders
                  </Link>
                </div>
              )}

              {/* Engagement Distribution */}
              {metrics && Object.keys(metrics.engagement_distribution).length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Engagement Distribution
                  </h3>
                  <div className="space-y-3">
                    {ENGAGEMENT_LEVELS.map(level => {
                      const count = metrics.engagement_distribution[level] || 0
                      const percentage = metrics.total_stakeholders > 0
                        ? Math.round((count / metrics.total_stakeholders) * 100)
                        : 0
                      return (
                        <div key={level} className="flex items-center gap-3">
                          <span className={`w-24 px-2 py-1 rounded text-xs text-center capitalize ${getEngagementBadge(level)}`}>
                            {level}
                          </span>
                          <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${level === 'champion' || level === 'supporter' ? 'bg-teal-500' : level === 'neutral' ? 'bg-gray-400' : 'bg-orange-500'}`}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600 dark:text-gray-400 w-16 text-right">
                            {count} ({percentage}%)
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Recent Concerns */}
              {metrics && metrics.recent_concerns.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-red-200 dark:border-red-800 p-6">
                  <h3 className="text-lg font-semibold text-red-700 dark:text-red-300 mb-4">
                    Unresolved Concerns
                  </h3>
                  <div className="space-y-3">
                    {metrics.recent_concerns.slice(0, 5).map(concern => (
                      <div key={concern.id} className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {concern.stakeholder_name}:
                        </span>
                        <span className="text-gray-600 dark:text-gray-400 ml-2">
                          {concern.content}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Transcripts */}
              {recentTranscripts.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Recent Transcripts
                  </h3>
                  <div className="space-y-3">
                    {recentTranscripts.map(transcript => (
                      <Link
                        key={transcript.id}
                        href={`/transcripts/${transcript.id}`}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {transcript.title}
                          </span>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {transcript.stakeholder_count || 0} stakeholders identified
                          </p>
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(transcript.meeting_date || transcript.processed_at)}
                        </span>
                      </Link>
                    ))}
                  </div>
                  <Link
                    href="/transcripts"
                    className="block mt-4 text-sm text-teal-600 dark:text-teal-400 hover:underline text-center"
                  >
                    View all transcripts
                  </Link>
                </div>
              )}
            </div>

            {/* Empty State */}
            {(!metrics || metrics.total_stakeholders === 0) && recentTranscripts.length === 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
                <div className="text-5xl mb-4">🚀</div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Welcome to Thesis
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
                  Your GenAI strategy command center. Start by uploading a meeting transcript
                  or chatting with your specialized agents.
                </p>
                <div className="flex justify-center gap-4">
                  <Link href="/transcripts" className="btn-primary">
                    Upload Transcript
                  </Link>
                  <Link href="/chat" className="btn-secondary">
                    Chat with Agents
                  </Link>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
