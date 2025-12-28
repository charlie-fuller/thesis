'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api'
import PageHeader from '@/components/PageHeader'

interface Stakeholder {
  id: string
  name: string
  email: string | null
  phone: string | null
  role: string | null
  department: string | null
  organization: string
  sentiment_score: number
  sentiment_trend: string
  engagement_level: string
  alignment_score: number
  total_interactions: number
  last_interaction: string | null
  key_concerns: string[]
  interests: string[]
  notes: string | null
  created_at: string
}

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
  stakeholders_needing_attention: Stakeholder[]
}

interface StakeholderCreateForm {
  name: string
  email: string
  role: string
  department: string
  organization: string
  notes: string
}

const ENGAGEMENT_LEVELS = ['champion', 'supporter', 'neutral', 'skeptic', 'blocker']
const DEPARTMENTS = ['finance', 'it', 'legal', 'governance', 'hr', 'marketing', 'engineering', 'operations', 'executive']

export default function StakeholdersPage() {
  const router = useRouter()
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [filterDepartment, setFilterDepartment] = useState<string>('')
  const [filterEngagement, setFilterEngagement] = useState<string>('')
  const [createForm, setCreateForm] = useState<StakeholderCreateForm>({
    name: '',
    email: '',
    role: '',
    department: '',
    organization: 'Contentful',
    notes: ''
  })
  const [creating, setCreating] = useState(false)

  async function loadData() {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams()
      if (filterDepartment) params.append('department', filterDepartment)
      if (filterEngagement) params.append('engagement_level', filterEngagement)

      const [stakeholderData, metricsData] = await Promise.all([
        apiGet<Stakeholder[]>(`/api/stakeholders/?${params.toString()}`),
        apiGet<DashboardMetrics>('/api/stakeholders/dashboard')
      ])

      setStakeholders(stakeholderData || [])
      setMetrics(metricsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stakeholders')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [filterDepartment, filterEngagement])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!createForm.name.trim()) return

    try {
      setCreating(true)
      await apiPost('/api/stakeholders/', createForm)
      setShowCreateForm(false)
      setCreateForm({
        name: '',
        email: '',
        role: '',
        department: '',
        organization: 'Contentful',
        notes: ''
      })
      loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create stakeholder')
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete stakeholder "${name}"? This cannot be undone.`)) return

    try {
      await apiDelete(`/api/stakeholders/${id}`)
      loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete stakeholder')
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

  function getTrendIcon(trend: string) {
    switch (trend) {
      case 'improving': return '&#8599;'
      case 'declining': return '&#8600;'
      default: return '&#8594;'
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-page">
      <PageHeader />
      <div className="max-w-7xl mx-auto px-4 py-8 w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Stakeholder Intelligence
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Track sentiment, engagement, and alignment across your stakeholders
            </p>
          </div>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn-primary flex items-center gap-2"
          >
            {showCreateForm ? <>&times; Close</> : <>+ Add Stakeholder</>}
          </button>
        </div>

        {/* Dashboard Metrics */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
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

        {/* Engagement Distribution */}
        {metrics && Object.keys(metrics.engagement_distribution).length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Engagement Distribution
            </h3>
            <div className="flex gap-4 flex-wrap">
              {ENGAGEMENT_LEVELS.map(level => {
                const count = metrics.engagement_distribution[level] || 0
                const percentage = metrics.total_stakeholders > 0
                  ? Math.round((count / metrics.total_stakeholders) * 100)
                  : 0
                return (
                  <div key={level} className="flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-sm capitalize ${getEngagementBadge(level)}`}>
                      {level}
                    </span>
                    <span className="text-gray-600 dark:text-gray-400">
                      {count} ({percentage}%)
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Create Form */}
        {showCreateForm && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Add New Stakeholder
            </h3>
            <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={e => setCreateForm(f => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={createForm.email}
                  onChange={e => setCreateForm(f => ({ ...f, email: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Role
                </label>
                <input
                  type="text"
                  value={createForm.role}
                  onChange={e => setCreateForm(f => ({ ...f, role: e.target.value }))}
                  placeholder="e.g., VP of Engineering"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Department
                </label>
                <select
                  value={createForm.department}
                  onChange={e => setCreateForm(f => ({ ...f, department: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Select department...</option>
                  {DEPARTMENTS.map(d => (
                    <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Organization
                </label>
                <input
                  type="text"
                  value={createForm.organization}
                  onChange={e => setCreateForm(f => ({ ...f, organization: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Notes
                </label>
                <input
                  type="text"
                  value={createForm.notes}
                  onChange={e => setCreateForm(f => ({ ...f, notes: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                />
              </div>
              <div className="md:col-span-2 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !createForm.name.trim()}
                  className="btn-primary disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Stakeholder'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Recent Concerns */}
        {metrics && metrics.recent_concerns.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-orange-200 dark:border-orange-800 p-6 mb-8">
            <h3 className="text-lg font-semibold text-orange-700 dark:text-orange-300 mb-4">
              Recent Unresolved Concerns
            </h3>
            <div className="space-y-3">
              {metrics.recent_concerns.slice(0, 5).map(concern => (
                <div key={concern.id} className="flex items-start gap-3 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                  <span className="text-orange-500 mt-0.5">&#9888;</span>
                  <div>
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {concern.stakeholder_name}:
                    </span>
                    <span className="text-gray-600 dark:text-gray-400 ml-2">
                      {concern.content}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-4 mb-6">
          <select
            value={filterDepartment}
            onChange={e => setFilterDepartment(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
          >
            <option value="">All Departments</option>
            {DEPARTMENTS.map(d => (
              <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
            ))}
          </select>
          <select
            value={filterEngagement}
            onChange={e => setFilterEngagement(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
          >
            <option value="">All Engagement Levels</option>
            {ENGAGEMENT_LEVELS.map(l => (
              <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>
            ))}
          </select>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">{error}</p>
            <button onClick={loadData} className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline">
              Try again
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500"></div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && stakeholders.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
            <div className="text-4xl mb-4">&#128101;</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              No stakeholders yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Add stakeholders manually or upload transcripts to auto-populate.
            </p>
            <div className="flex justify-center gap-4">
              <button onClick={() => setShowCreateForm(true)} className="btn-primary">
                Add Stakeholder
              </button>
              <button onClick={() => router.push('/transcripts')} className="btn-secondary">
                Upload Transcript
              </button>
            </div>
          </div>
        )}

        {/* Stakeholders Grid */}
        {!loading && stakeholders.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stakeholders.map(stakeholder => (
              <div
                key={stakeholder.id}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                      {stakeholder.name}
                    </h3>
                    {stakeholder.role && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">{stakeholder.role}</p>
                    )}
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full capitalize ${getEngagementBadge(stakeholder.engagement_level)}`}>
                    {stakeholder.engagement_level}
                  </span>
                </div>

                <div className="space-y-2 text-sm">
                  {stakeholder.department && (
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <span>&#127970;</span>
                      <span className="capitalize">{stakeholder.department}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                    <span>&#127965;</span>
                    <span>{stakeholder.organization}</span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700 grid grid-cols-3 gap-2 text-center">
                  <div>
                    <div className={`text-lg font-semibold ${getSentimentColor(stakeholder.sentiment_score)}`}>
                      {stakeholder.sentiment_score > 0 ? '+' : ''}{stakeholder.sentiment_score.toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      Sentiment <span dangerouslySetInnerHTML={{ __html: getTrendIcon(stakeholder.sentiment_trend) }} />
                    </div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-teal-600 dark:text-teal-400">
                      {Math.round(stakeholder.alignment_score * 100)}%
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Alignment</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-gray-700 dark:text-gray-300">
                      {stakeholder.total_interactions}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Meetings</div>
                  </div>
                </div>

                {stakeholder.key_concerns.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                    <div className="text-xs text-orange-600 dark:text-orange-400 font-medium mb-1">
                      Key Concerns
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {stakeholder.key_concerns.slice(0, 3).map((concern, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300 rounded">
                          {concern}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-4 flex justify-end gap-2">
                  <button
                    onClick={() => router.push(`/stakeholders/${stakeholder.id}`)}
                    className="text-sm text-teal-600 dark:text-teal-400 hover:underline"
                  >
                    View
                  </button>
                  <button
                    onClick={() => handleDelete(stakeholder.id, stakeholder.name)}
                    className="text-sm text-red-600 dark:text-red-400 hover:underline"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
