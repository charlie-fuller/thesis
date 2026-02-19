'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { apiGet, apiPost, apiDelete } from '@/lib/api'
import { logger } from '@/lib/logger'
import PageLayout from '@/components/PageLayout'
import LoadingSpinner from '@/components/LoadingSpinner'
import { AgentIcon, getAgentColor } from '@/components/AgentIcon'
import dynamic from 'next/dynamic'

// Lazy load the chart component to avoid SSR issues with recharts
const EngagementTrendsChart = dynamic(
  () => import('@/components/EngagementTrendsChart'),
  { ssr: false, loading: () => <LoadingSpinner /> }
)

// Lazy load the department grouped view
const DepartmentGroupedView = dynamic(
  () => import('@/components/stakeholders/DepartmentGroupedView'),
  { ssr: false, loading: () => <LoadingSpinner /> }
)

// Lazy load Strategy content
const StrategyContent = dynamic(
  () => import('@/components/StrategyContent'),
  { ssr: false, loading: () => <LoadingSpinner /> }
)

// Tab type
type TabType = 'strategy' | 'stakeholders' | 'engagement' | 'agents' | 'stakeholder-guide' | 'agent-tree'

// Stakeholder view mode
type StakeholderViewMode = 'grid' | 'department'

// Agent interface
interface Agent {
  id: string
  name: string
  display_name: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  instruction_versions_count: number
  kb_documents_count: number
  conversations_count: number
  meeting_rooms_count: number
}

// Stakeholder types
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
const DEPARTMENTS = ['finance', 'it', 'is', 'legal', 'governance', 'hr', 'marketing', 'engineering', 'operations', 'executive']

function IntelligencePageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, session, loading: authLoading } = useAuth()
  const tabParam = searchParams.get('tab')
  const [activeTab, setActiveTab] = useState<TabType>(
    tabParam === 'stakeholders' ? 'stakeholders' :
    tabParam === 'engagement' ? 'engagement' :
    tabParam === 'agents' ? 'agents' : 'strategy'
  )

  // Stakeholder state
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [stakeholderLoading, setStakeholderLoading] = useState(true)
  const [stakeholderError, setStakeholderError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [filterDepartment, setFilterDepartment] = useState<string>('')
  const [filterEngagement, setFilterEngagement] = useState<string>('')
  const [stakeholderViewMode, setStakeholderViewMode] = useState<StakeholderViewMode>('department')
  const [createForm, setCreateForm] = useState<StakeholderCreateForm>({
    name: '',
    email: '',
    role: '',
    department: '',
    organization: 'Contentful',
    notes: ''
  })
  const [creating, setCreating] = useState(false)

  // Agent state
  const [agents, setAgents] = useState<Agent[]>([])
  const [agentsLoading, setAgentsLoading] = useState(true)
  const [agentsError, setAgentsError] = useState<string | null>(null)

  // Load agent data
  async function loadAgentData() {
    try {
      setAgentsLoading(true)
      setAgentsError(null)
      const data = await apiGet<{ agents: Agent[] }>('/api/agents?include_inactive=true')
      setAgents(data.agents || [])
    } catch (err) {
      logger.error('Failed to fetch agents:', err)
      setAgentsError('Failed to load agents')
    } finally {
      setAgentsLoading(false)
    }
  }

  // Load stakeholder data
  async function loadStakeholderData() {
    try {
      setStakeholderLoading(true)
      setStakeholderError(null)

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
      setStakeholderError(err instanceof Error ? err.message : 'Failed to load stakeholders')
    } finally {
      setStakeholderLoading(false)
    }
  }

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [authLoading, user, router])

  // Load data when authenticated and auth is fully ready
  useEffect(() => {
    if (!authLoading && user && session) {
      loadStakeholderData()
      loadAgentData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- loadStakeholderData and loadAgentData are stable
  }, [authLoading, user, session])

  useEffect(() => {
    if (!authLoading && user && session && activeTab === 'stakeholders') {
      loadStakeholderData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- loadStakeholderData is stable, activeTab intentionally omitted
  }, [authLoading, filterDepartment, filterEngagement, user, session])

  async function handleCreateStakeholder(e: React.FormEvent) {
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
      loadStakeholderData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create stakeholder')
    } finally {
      setCreating(false)
    }
  }

  async function handleDeleteStakeholder(id: string, name: string) {
    if (!confirm(`Delete stakeholder "${name}"? This cannot be undone.`)) return

    try {
      await apiDelete(`/api/stakeholders/${id}`)
      loadStakeholderData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete stakeholder')
    }
  }

  function getSentimentColor(score: number) {
    if (score > 0.3) return 'text-green-600 dark:text-green-400'
    if (score < -0.3) return 'text-red-600 dark:text-red-400'
    return 'text-muted'
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
      case 'improving':
        return (
          <svg className="w-3 h-3 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l5-5 5 5" />
          </svg>
        )
      case 'declining':
        return (
          <svg className="w-3 h-3 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-5 5-5-5" />
          </svg>
        )
      default:
        return (
          <svg className="w-3 h-3 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
          </svg>
        )
    }
  }

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
      <div className="max-w-7xl mx-auto px-4 py-8 w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-primary">
              Intelligence
            </h1>
            <p className="text-secondary mt-1">
              Manage stakeholders and AI agents
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-default">
          <button
            onClick={() => setActiveTab('strategy')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'strategy'
                ? 'border-brand text-brand'
                : 'border-transparent text-secondary hover:text-primary'
            }`}
          >
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Strategy
            </div>
          </button>
          <button
            onClick={() => setActiveTab('stakeholders')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'stakeholders'
                ? 'border-brand text-brand'
                : 'border-transparent text-secondary hover:text-primary'
            }`}
          >
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Stakeholders
            </div>
          </button>
          <button
            onClick={() => setActiveTab('engagement')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'engagement'
                ? 'border-brand text-brand'
                : 'border-transparent text-secondary hover:text-primary'
            }`}
          >
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Engagement
            </div>
          </button>
          <button
            onClick={() => setActiveTab('agents')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'agents'
                ? 'border-brand text-brand'
                : 'border-transparent text-secondary hover:text-primary'
            }`}
          >
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Agents
            </div>
          </button>
          <button
            onClick={() => setActiveTab('stakeholder-guide')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'stakeholder-guide'
                ? 'border-brand text-brand'
                : 'border-transparent text-secondary hover:text-primary'
            }`}
          >
            Stakeholder Guide
          </button>
          <button
            onClick={() => setActiveTab('agent-tree')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'agent-tree'
                ? 'border-brand text-brand'
                : 'border-transparent text-secondary hover:text-primary'
            }`}
          >
            Agent Selection Tree
          </button>
        </div>

        {/* Stakeholders Tab */}
        {activeTab === 'stakeholders' && (
          <div>
            {/* Add Stakeholder Button */}
            <div className="flex justify-end mb-6">
              <button
                onClick={() => setShowCreateForm(!showCreateForm)}
                className="btn-primary flex items-center gap-2"
              >
                {showCreateForm ? (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Close
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add Stakeholder
                  </>
                )}
              </button>
            </div>

            {/* Create Form */}
            {showCreateForm && (
              <div className="card p-6 mb-8">
                <h3 className="text-lg font-semibold text-primary mb-4">
                  Add New Stakeholder
                </h3>
                <form onSubmit={handleCreateStakeholder} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-secondary mb-1">
                      Name *
                    </label>
                    <input
                      type="text"
                      value={createForm.name}
                      onChange={e => setCreateForm(f => ({ ...f, name: e.target.value }))}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-secondary mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      value={createForm.email}
                      onChange={e => setCreateForm(f => ({ ...f, email: e.target.value }))}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-secondary mb-1">
                      Role
                    </label>
                    <input
                      type="text"
                      value={createForm.role}
                      onChange={e => setCreateForm(f => ({ ...f, role: e.target.value }))}
                      placeholder="e.g., VP of Engineering"
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-secondary mb-1">
                      Department
                    </label>
                    <select
                      value={createForm.department}
                      onChange={e => setCreateForm(f => ({ ...f, department: e.target.value }))}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary"
                    >
                      <option value="">Select department...</option>
                      {DEPARTMENTS.map(d => (
                        <option key={d} value={d}>{d.length <= 2 ? d.toUpperCase() : d.charAt(0).toUpperCase() + d.slice(1)}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-secondary mb-1">
                      Organization
                    </label>
                    <input
                      type="text"
                      value={createForm.organization}
                      onChange={e => setCreateForm(f => ({ ...f, organization: e.target.value }))}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-secondary mb-1">
                      Notes
                    </label>
                    <input
                      type="text"
                      value={createForm.notes}
                      onChange={e => setCreateForm(f => ({ ...f, notes: e.target.value }))}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary"
                    />
                  </div>
                  <div className="md:col-span-2 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="px-4 py-2 text-secondary hover:text-primary"
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

            {/* Filters and View Toggle */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex gap-4">
                <select
                  value={filterDepartment}
                  onChange={e => setFilterDepartment(e.target.value)}
                  className="px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm"
                >
                  <option value="">All Departments</option>
                  {DEPARTMENTS.map(d => (
                    <option key={d} value={d}>{d.length <= 2 ? d.toUpperCase() : d.charAt(0).toUpperCase() + d.slice(1)}</option>
                  ))}
                </select>
                <select
                  value={filterEngagement}
                  onChange={e => setFilterEngagement(e.target.value)}
                  className="px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm"
                >
                  <option value="">All Engagement Levels</option>
                  {ENGAGEMENT_LEVELS.map(l => (
                    <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>
                  ))}
                </select>
              </div>

              {/* View Toggle */}
              <div className="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg">
                <button
                  onClick={() => setStakeholderViewMode('department')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    stakeholderViewMode === 'department'
                      ? 'bg-white dark:bg-slate-700 text-primary shadow-sm'
                      : 'text-secondary hover:text-primary'
                  }`}
                >
                  By Team
                </button>
                <button
                  onClick={() => setStakeholderViewMode('grid')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    stakeholderViewMode === 'grid'
                      ? 'bg-white dark:bg-slate-700 text-primary shadow-sm'
                      : 'text-secondary hover:text-primary'
                  }`}
                >
                  Grid
                </button>
              </div>
            </div>

            {/* Error State */}
            {stakeholderError && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
                <p className="text-red-800 dark:text-red-200">{stakeholderError}</p>
                <button onClick={loadStakeholderData} className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline">
                  Try again
                </button>
              </div>
            )}

            {/* Loading State */}
            {stakeholderLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
              </div>
            )}

            {/* Empty State */}
            {!stakeholderLoading && !stakeholderError && stakeholders.length === 0 && (
              <div className="card p-12 text-center">
                <div className="flex justify-center mb-4">
                  <svg className="w-12 h-12 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-primary mb-2">
                  No stakeholders yet
                </h3>
                <p className="text-secondary mb-4">
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

            {/* Stakeholders Display - Department Grouped View */}
            {!stakeholderLoading && stakeholders.length > 0 && stakeholderViewMode === 'department' && (
              <DepartmentGroupedView
                stakeholders={stakeholders}
                onDelete={handleDeleteStakeholder}
              />
            )}

            {/* Stakeholders Display - Grid View */}
            {!stakeholderLoading && stakeholders.length > 0 && stakeholderViewMode === 'grid' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {stakeholders.map(stakeholder => (
                  <div
                    key={stakeholder.id}
                    className="card p-6 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-primary">
                          {stakeholder.name}
                        </h3>
                        {stakeholder.role && (
                          <p className="text-sm text-muted">{stakeholder.role}</p>
                        )}
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full capitalize ${getEngagementBadge(stakeholder.engagement_level)}`}>
                        {stakeholder.engagement_level}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm">
                      {stakeholder.department && (
                        <div className="flex items-center gap-2 text-secondary">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                          </svg>
                          <span className="capitalize">{stakeholder.department}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2 text-secondary">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <span>{stakeholder.organization}</span>
                      </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-default grid grid-cols-3 gap-2 text-center">
                      <div>
                        <div className={`text-lg font-semibold ${getSentimentColor(stakeholder.sentiment_score)}`}>
                          {stakeholder.sentiment_score > 0 ? '+' : ''}{stakeholder.sentiment_score.toFixed(1)}
                        </div>
                        <div className="text-xs text-muted flex items-center justify-center gap-1">
                          Sentiment {getTrendIcon(stakeholder.sentiment_trend)}
                        </div>
                      </div>
                      <div>
                        <div className="text-lg font-semibold text-teal-600 dark:text-teal-400">
                          {Math.round(stakeholder.alignment_score * 100)}%
                        </div>
                        <div className="text-xs text-muted">Alignment</div>
                      </div>
                      <div>
                        <div className="text-lg font-semibold text-secondary">
                          {stakeholder.total_interactions}
                        </div>
                        <div className="text-xs text-muted">Meetings</div>
                      </div>
                    </div>

                    {stakeholder.key_concerns.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-default">
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
                        className="text-sm text-brand hover:underline"
                      >
                        View
                      </button>
                      <button
                        onClick={() => handleDeleteStakeholder(stakeholder.id, stakeholder.name)}
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
        )}

        {/* Strategy Tab */}
        {activeTab === 'strategy' && (
          <StrategyContent />
        )}

        {/* Engagement Tab */}
        {activeTab === 'engagement' && (
          <div>
            {/* Dashboard Metrics */}
            {metrics && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="card p-6">
                  <div className="text-3xl font-bold text-primary">
                    {metrics.total_stakeholders}
                  </div>
                  <div className="text-sm text-muted">Total Stakeholders</div>
                </div>
                <div className="card p-6">
                  <div className={`text-3xl font-bold ${getSentimentColor(metrics.average_sentiment)}`}>
                    {metrics.average_sentiment > 0 ? '+' : ''}{metrics.average_sentiment.toFixed(2)}
                  </div>
                  <div className="text-sm text-muted">Avg Sentiment</div>
                </div>
                <div className="card p-6">
                  <div className="text-3xl font-bold text-teal-600 dark:text-teal-400">
                    {Math.round(metrics.average_alignment * 100)}%
                  </div>
                  <div className="text-sm text-muted">Avg Alignment</div>
                </div>
                <div className="card p-6">
                  <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                    {metrics.stakeholders_needing_attention.length}
                  </div>
                  <div className="text-sm text-muted">Need Attention</div>
                </div>
              </div>
            )}

            {/* Engagement Distribution */}
            {metrics && Object.keys(metrics.engagement_distribution).length > 0 && (
              <div className="card p-6 mb-8">
                <h3 className="text-lg font-semibold text-primary mb-4">
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
                        <span className="text-secondary">
                          {count} ({percentage}%)
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Engagement Trends Analytics */}
            <div className="mb-8">
              <EngagementTrendsChart />
            </div>

            {/* Recent Concerns */}
            {metrics && metrics.recent_concerns.length > 0 && (
              <div className="card border-orange-200 dark:border-orange-800 p-6">
                <h3 className="text-lg font-semibold text-orange-700 dark:text-orange-300 mb-4">
                  Recent Unresolved Concerns
                </h3>
                <div className="space-y-3">
                  {metrics.recent_concerns.slice(0, 5).map(concern => (
                    <div key={concern.id} className="flex items-start gap-3 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                      <svg className="w-5 h-5 text-orange-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <div>
                        <span className="font-medium text-primary">
                          {concern.stakeholder_name}:
                        </span>
                        <span className="text-secondary ml-2">
                          {concern.content}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state when no metrics */}
            {!metrics && !stakeholderLoading && (
              <div className="card p-12 text-center">
                <div className="flex justify-center mb-4">
                  <svg className="w-12 h-12 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-primary mb-2">
                  No engagement data yet
                </h3>
                <p className="text-secondary">
                  Add stakeholders to start tracking engagement metrics.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Agents Tab */}
        {activeTab === 'agents' && (
          <div>
            {/* Loading State */}
            {agentsLoading && (
              <div className="flex items-center justify-center py-20">
                <LoadingSpinner size="lg" />
              </div>
            )}

            {/* Error State */}
            {agentsError && (
              <div className="text-center py-20">
                <p className="text-red-400">{agentsError}</p>
                <button
                  onClick={loadAgentData}
                  className="mt-4 btn-primary"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Agent Grid */}
            {!agentsLoading && !agentsError && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {agents.map((agent) => (
                    <Link
                      key={agent.id}
                      href={`/admin/agents/${agent.id}`}
                      className="card p-6 hover:border-primary/50 transition-all group"
                    >
                      {/* Agent Header */}
                      <div className="flex items-start gap-4 mb-4">
                        <div className={`w-12 h-12 rounded-lg flex items-center justify-center border ${getAgentColor(agent.name)}`}>
                          <AgentIcon name={agent.name} size="lg" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-primary group-hover:text-blue-400 transition-colors">
                            {agent.display_name}
                          </h3>
                          <p className="text-sm text-secondary">
                            {agent.name}
                          </p>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${
                          agent.is_active
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-gray-500/20 text-gray-400'
                        }`}>
                          {agent.is_active ? 'Active' : 'Inactive'}
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-sm text-secondary mb-4 line-clamp-2">
                        {agent.description || 'No description configured'}
                      </p>

                      {/* Stats */}
                      <div className="grid grid-cols-4 gap-3 pt-4 border-t border-border">
                        <div className="text-center">
                          <div className="text-lg font-semibold text-primary">
                            {agent.instruction_versions_count}
                          </div>
                          <div className="text-xs text-secondary">Versions</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-semibold text-primary">
                            {agent.kb_documents_count}
                          </div>
                          <div className="text-xs text-secondary">KB Docs</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-semibold text-primary">
                            {agent.conversations_count ?? 0}
                          </div>
                          <div className="text-xs text-secondary">Chats</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-semibold text-primary">
                            {agent.meeting_rooms_count ?? 0}
                          </div>
                          <div className="text-xs text-secondary">Meetings</div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>

                {agents.length === 0 && (
                  <div className="text-center py-20 card">
                    <p className="text-secondary">No agents configured yet</p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'stakeholder-guide' && (
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
            <iframe
              src="/stakeholder-workflow.html"
              className="w-full h-full border-0"
              title="Stakeholder Engagement Workflow"
            />
          </div>
        )}

        {activeTab === 'agent-tree' && (
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
            <iframe
              src="/agent-selection-tree.html"
              className="w-full h-full border-0"
              title="Agent Selection Tree"
            />
          </div>
        )}
      </div>
    </PageLayout>
  )
}

export default function IntelligencePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-page flex items-center justify-center"><LoadingSpinner size="lg" /></div>}>
      <IntelligencePageContent />
    </Suspense>
  )
}
