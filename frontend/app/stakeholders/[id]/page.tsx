'use client'

import { useState, useEffect, use } from 'react'
import { useRouter } from 'next/navigation'
import {
  Check,
  FileText,
  MessageCircle,
  Target,
  ClipboardList,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  Users,
  Calendar,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { apiGet, apiPatch, apiPost } from '@/lib/api'

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
  // Project-triage fields
  priority_level: string | null
  ai_priorities: string[]
  pain_points: string[]
  win_conditions: string[]
  communication_style: string | null
  relationship_status: string | null
  open_questions: string[]
  last_contact: string | null
  reports_to_name: string | null
  team_size: number | null
}

interface StakeholderMetric {
  id: string
  metric_name: string
  metric_category: string
  unit: string | null
  current_value: string | null
  target_value: string | null
  validation_status: string
  source: string | null
  notes: string | null
  questions_to_confirm: string[]
}

interface LinkedOpportunity {
  id: string
  opportunity_code: string
  title: string
  total_score: number
  tier: number
  status: string
  role: string
}

interface Insight {
  id: string
  insight_type: string
  content: string
  quote: string | null
  confidence: number
  is_resolved: boolean
  meeting_title: string | null
  meeting_date: string | null
  created_at: string
}

const ENGAGEMENT_LEVELS = ['champion', 'supporter', 'neutral', 'skeptic', 'blocker']
const DEPARTMENTS = ['finance', 'it', 'legal', 'governance', 'hr', 'marketing', 'engineering', 'operations', 'executive']
const PRIORITY_LEVELS = [
  { value: 'tier_1', label: 'Tier 1 - Critical' },
  { value: 'tier_2', label: 'Tier 2 - Important' },
  { value: 'tier_3', label: 'Tier 3 - Standard' },
]
const RELATIONSHIP_STATUSES = ['strong', 'building', 'new', 'strained']

// Validation status badge helper
function ValidationBadge({ status }: { status: string }) {
  const config = {
    green: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', icon: '🟢', label: 'Validated' },
    yellow: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-300', icon: '🟡', label: 'Partial' },
    red: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', icon: '🔴', label: 'Needs Validation' },
  }
  const c = config[status as keyof typeof config] || config.red
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${c.bg} ${c.text}`}>
      {c.icon} {c.label}
    </span>
  )
}

// Tier badge helper
function TierBadge({ tier }: { tier: number }) {
  const config = {
    1: { bg: 'bg-rose-100 dark:bg-rose-900/30', text: 'text-rose-700 dark:text-rose-300' },
    2: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-300' },
    3: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300' },
    4: { bg: 'bg-slate-100 dark:bg-slate-700', text: 'text-slate-700 dark:text-slate-300' },
  }
  const c = config[tier as keyof typeof config] || config[4]
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${c.bg} ${c.text}`}>
      T{tier}
    </span>
  )
}

export default function StakeholderDetailPage(props: { params: Promise<{ id: string }> }) {
  const params = use(props.params)
  const router = useRouter()
  const [stakeholder, setStakeholder] = useState<Stakeholder | null>(null)
  const [insights, setInsights] = useState<Insight[]>([])
  const [metrics, setMetrics] = useState<StakeholderMetric[]>([])
  const [opportunities, setOpportunities] = useState<LinkedOpportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Stakeholder>>({})
  const [saving, setSaving] = useState(false)
  const [showResolved, setShowResolved] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    metrics: true,
    opportunities: true,
    questions: true,
  })

  function toggleSection(section: string) {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  async function loadData() {
    try {
      setLoading(true)
      setError(null)

      const [stakeholderData, insightsData, metricsData, oppsData] = await Promise.all([
        apiGet<Stakeholder>(`/api/stakeholders/${params.id}`),
        apiGet<Insight[]>(`/api/stakeholders/${params.id}/insights?include_resolved=${showResolved}`),
        apiGet<StakeholderMetric[]>(`/api/stakeholder-metrics/by-stakeholder/${params.id}`).catch(() => []),
        apiGet<LinkedOpportunity[]>(`/api/stakeholders/${params.id}/opportunities`).catch(() => []),
      ])

      setStakeholder(stakeholderData)
      setInsights(insightsData || [])
      setMetrics(metricsData || [])
      setOpportunities(oppsData || [])
      setEditForm(stakeholderData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stakeholder')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [params.id, showResolved])

  async function handleSave() {
    try {
      setSaving(true)
      const updated = await apiPatch<Stakeholder>(`/api/stakeholders/${params.id}`, editForm)
      setStakeholder(updated)
      setEditing(false)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update stakeholder')
    } finally {
      setSaving(false)
    }
  }

  async function handleResolveInsight(insightId: string) {
    try {
      await apiPost(`/api/stakeholders/${params.id}/insights/${insightId}/resolve`, {})
      loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to resolve insight')
    }
  }

  function getSentimentColor(score: number) {
    if (score > 0.3) return 'text-green-600 dark:text-green-400'
    if (score < -0.3) return 'text-red-600 dark:text-red-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  function getEngagementBadge(level: string) {
    switch (level) {
      case 'champion': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      case 'supporter': return 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300'
      case 'neutral': return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
      case 'skeptic': return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
      case 'blocker': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
      default: return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
  }

  function getInsightColor(type: string) {
    switch (type) {
      case 'concern': return 'border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20'
      case 'enthusiasm':
      case 'support': return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
      case 'commitment': return 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20'
      case 'objection': return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
      case 'question': return 'border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-900/20'
      default: return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500"></div>
      </div>
    )
  }

  if (error || !stakeholder) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
              Error Loading Stakeholder
            </h2>
            <p className="text-red-700 dark:text-red-300">{error || 'Stakeholder not found'}</p>
            <button
              onClick={() => router.push('/stakeholders')}
              className="mt-4 text-sm text-red-600 dark:text-red-400 hover:underline"
            >
              &larr; Back to stakeholders
            </button>
          </div>
        </div>
      </div>
    )
  }

  const concernCount = insights.filter(i => i.insight_type === 'concern' && !i.is_resolved).length

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Back Button */}
        <button
          onClick={() => router.push('/stakeholders')}
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mb-6 flex items-center gap-1"
        >
          &larr; Back to stakeholders
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Profile */}
          <div className="lg:col-span-2 space-y-6">
            {/* Header Card */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  {editing ? (
                    <input
                      type="text"
                      value={editForm.name || ''}
                      onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
                      className="text-2xl font-bold text-gray-900 dark:text-gray-100 bg-transparent border-b border-teal-500 focus:outline-none"
                    />
                  ) : (
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {stakeholder.name}
                    </h1>
                  )}
                  <div className="flex items-center gap-2 mt-1">
                    {editing ? (
                      <input
                        type="text"
                        value={editForm.role || ''}
                        onChange={e => setEditForm(f => ({ ...f, role: e.target.value }))}
                        placeholder="Role"
                        className="text-gray-600 dark:text-gray-400 bg-transparent border-b border-gray-300 dark:border-gray-600 focus:outline-none"
                      />
                    ) : (
                      stakeholder.role && (
                        <span className="text-gray-600 dark:text-gray-400">{stakeholder.role}</span>
                      )
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {editing ? (
                    <select
                      value={editForm.engagement_level || stakeholder.engagement_level}
                      onChange={e => setEditForm(f => ({ ...f, engagement_level: e.target.value }))}
                      className={`px-3 py-1 rounded-full text-sm capitalize ${getEngagementBadge(editForm.engagement_level || stakeholder.engagement_level)}`}
                    >
                      {ENGAGEMENT_LEVELS.map(l => (
                        <option key={l} value={l}>{l}</option>
                      ))}
                    </select>
                  ) : (
                    <span className={`px-3 py-1 rounded-full text-sm capitalize ${getEngagementBadge(stakeholder.engagement_level)}`}>
                      {stakeholder.engagement_level}
                    </span>
                  )}
                </div>
              </div>

              {/* Contact Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-500 dark:text-gray-400 mb-1">Email</div>
                  {editing ? (
                    <input
                      type="email"
                      value={editForm.email || ''}
                      onChange={e => setEditForm(f => ({ ...f, email: e.target.value }))}
                      className="w-full bg-transparent border-b border-gray-300 dark:border-gray-600 focus:outline-none text-gray-900 dark:text-gray-100"
                    />
                  ) : (
                    <div className="text-gray-900 dark:text-gray-100">
                      {stakeholder.email || '-'}
                    </div>
                  )}
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400 mb-1">Phone</div>
                  {editing ? (
                    <input
                      type="tel"
                      value={editForm.phone || ''}
                      onChange={e => setEditForm(f => ({ ...f, phone: e.target.value }))}
                      className="w-full bg-transparent border-b border-gray-300 dark:border-gray-600 focus:outline-none text-gray-900 dark:text-gray-100"
                    />
                  ) : (
                    <div className="text-gray-900 dark:text-gray-100">
                      {stakeholder.phone || '-'}
                    </div>
                  )}
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400 mb-1">Department</div>
                  {editing ? (
                    <select
                      value={editForm.department || ''}
                      onChange={e => setEditForm(f => ({ ...f, department: e.target.value }))}
                      className="w-full bg-transparent border-b border-gray-300 dark:border-gray-600 focus:outline-none text-gray-900 dark:text-gray-100"
                    >
                      <option value="">Select...</option>
                      {DEPARTMENTS.map(d => (
                        <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="text-gray-900 dark:text-gray-100 capitalize">
                      {stakeholder.department || '-'}
                    </div>
                  )}
                </div>
                <div>
                  <div className="text-gray-500 dark:text-gray-400 mb-1">Organization</div>
                  {editing ? (
                    <input
                      type="text"
                      value={editForm.organization || ''}
                      onChange={e => setEditForm(f => ({ ...f, organization: e.target.value }))}
                      className="w-full bg-transparent border-b border-gray-300 dark:border-gray-600 focus:outline-none text-gray-900 dark:text-gray-100"
                    />
                  ) : (
                    <div className="text-gray-900 dark:text-gray-100">
                      {stakeholder.organization}
                    </div>
                  )}
                </div>
              </div>

              {/* Notes */}
              <div className="mt-4">
                <div className="text-gray-500 dark:text-gray-400 mb-1 text-sm">Notes</div>
                {editing ? (
                  <textarea
                    value={editForm.notes || ''}
                    onChange={e => setEditForm(f => ({ ...f, notes: e.target.value }))}
                    rows={3}
                    className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg p-2 focus:outline-none text-gray-900 dark:text-gray-100"
                  />
                ) : (
                  <div className="text-gray-700 dark:text-gray-300 text-sm">
                    {stakeholder.notes || 'No notes'}
                  </div>
                )}
              </div>

              {/* Edit Actions */}
              <div className="mt-6 flex justify-end gap-3">
                {editing ? (
                  <>
                    <button
                      onClick={() => {
                        setEditing(false)
                        setEditForm(stakeholder)
                      }}
                      className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      className="btn-primary disabled:opacity-50"
                    >
                      {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setEditing(true)}
                    className="text-sm text-teal-600 dark:text-teal-400 hover:underline"
                  >
                    Edit Profile
                  </button>
                )}
              </div>
            </div>

            {/* Insights */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Insights ({insights.length})
                  {concernCount > 0 && (
                    <span className="ml-2 text-sm text-orange-600 dark:text-orange-400">
                      {concernCount} unresolved concerns
                    </span>
                  )}
                </h2>
                <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <input
                    type="checkbox"
                    checked={showResolved}
                    onChange={e => setShowResolved(e.target.checked)}
                    className="rounded border-gray-300 dark:border-gray-600"
                  />
                  Show resolved
                </label>
              </div>

              {insights.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  No insights yet. Upload meeting transcripts to extract insights.
                </div>
              ) : (
                <div className="space-y-4">
                  {insights.map(insight => (
                    <div
                      key={insight.id}
                      className={`p-4 rounded-lg border ${getInsightColor(insight.insight_type)} ${insight.is_resolved ? 'opacity-60' : ''}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs px-2 py-0.5 bg-white/50 dark:bg-black/20 rounded capitalize">
                            {insight.insight_type}
                          </span>
                          {insight.meeting_title && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              from {insight.meeting_title}
                            </span>
                          )}
                          {insight.is_resolved && (
                            <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                              <Check className="w-3 h-3" /> Resolved
                            </span>
                          )}
                        </div>
                        {!insight.is_resolved && insight.insight_type === 'concern' && (
                          <button
                            onClick={() => handleResolveInsight(insight.id)}
                            className="text-xs text-teal-600 dark:text-teal-400 hover:underline"
                          >
                            Mark Resolved
                          </button>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{insight.content}</p>
                      {insight.quote && (
                        <p className="mt-2 text-xs italic text-gray-500 dark:text-gray-500 border-l-2 border-gray-300 dark:border-gray-600 pl-2">
                          &ldquo;{insight.quote}&rdquo;
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Stakeholder KPIs/Metrics Table */}
            {metrics.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <button
                  onClick={() => toggleSection('metrics')}
                  className="w-full flex items-center justify-between mb-4"
                >
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-teal-600" />
                    KPI Metrics ({metrics.length})
                  </h2>
                  {expandedSections.metrics ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                </button>

                {expandedSections.metrics && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left py-2 px-2 font-medium text-gray-500 dark:text-gray-400">Metric</th>
                          <th className="text-left py-2 px-2 font-medium text-gray-500 dark:text-gray-400">Current</th>
                          <th className="text-left py-2 px-2 font-medium text-gray-500 dark:text-gray-400">Target</th>
                          <th className="text-left py-2 px-2 font-medium text-gray-500 dark:text-gray-400">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.map(metric => (
                          <tr key={metric.id} className="border-b border-gray-100 dark:border-gray-700/50">
                            <td className="py-2 px-2">
                              <div className="font-medium text-gray-900 dark:text-gray-100">{metric.metric_name}</div>
                              {metric.notes && (
                                <div className="text-xs text-gray-500 dark:text-gray-400">{metric.notes}</div>
                              )}
                            </td>
                            <td className="py-2 px-2 text-gray-700 dark:text-gray-300">
                              {metric.current_value || '-'} {metric.unit || ''}
                            </td>
                            <td className="py-2 px-2 text-gray-700 dark:text-gray-300">
                              {metric.target_value || '-'} {metric.unit || ''}
                            </td>
                            <td className="py-2 px-2">
                              <ValidationBadge status={metric.validation_status} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Linked Opportunities */}
            {opportunities.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <button
                  onClick={() => toggleSection('opportunities')}
                  className="w-full flex items-center justify-between mb-4"
                >
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <Target className="w-5 h-5 text-blue-600" />
                    Linked Opportunities ({opportunities.length})
                  </h2>
                  {expandedSections.opportunities ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                </button>

                {expandedSections.opportunities && (
                  <div className="space-y-3">
                    {opportunities.map(opp => (
                      <div
                        key={opp.id}
                        onClick={() => router.push('/opportunities')}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-sm text-gray-700 dark:text-gray-300">
                              {opp.opportunity_code}
                            </span>
                            <TierBadge tier={opp.tier} />
                            <span className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-600 rounded capitalize">
                              {opp.role}
                            </span>
                          </div>
                          <div className="text-sm text-gray-900 dark:text-gray-100 mt-1">{opp.title}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-gray-900 dark:text-gray-100">{opp.total_score}</div>
                          <div className="text-xs text-gray-500 capitalize">{opp.status}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Open Questions */}
            {stakeholder.open_questions && stakeholder.open_questions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-purple-200 dark:border-purple-800 p-6">
                <button
                  onClick={() => toggleSection('questions')}
                  className="w-full flex items-center justify-between mb-4"
                >
                  <h2 className="text-lg font-semibold text-purple-700 dark:text-purple-300 flex items-center gap-2">
                    <ClipboardList className="w-5 h-5" />
                    Open Questions ({stakeholder.open_questions.length})
                  </h2>
                  {expandedSections.questions ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                </button>

                {expandedSections.questions && (
                  <ul className="space-y-2">
                    {stakeholder.open_questions.map((q, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                        <span className="text-purple-500 mt-0.5">•</span>
                        {q}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          {/* Sidebar Stats */}
          <div className="space-y-6">
            {/* Priority & Relationship */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Priority & Status
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Priority Level</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    stakeholder.priority_level === 'tier_1' ? 'bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300' :
                    stakeholder.priority_level === 'tier_2' ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300' :
                    'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  }`}>
                    {stakeholder.priority_level ? stakeholder.priority_level.replace('_', ' ').toUpperCase() : 'Not Set'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Relationship</span>
                  <span className={`px-3 py-1 rounded-full text-sm capitalize ${
                    stakeholder.relationship_status === 'strong' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
                    stakeholder.relationship_status === 'building' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' :
                    stakeholder.relationship_status === 'strained' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' :
                    'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}>
                    {stakeholder.relationship_status || 'New'}
                  </span>
                </div>
                {stakeholder.last_contact && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                      <Calendar className="w-4 h-4" /> Last Contact
                    </span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {new Date(stakeholder.last_contact).toLocaleDateString()}
                    </span>
                  </div>
                )}
                {stakeholder.team_size && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                      <Users className="w-4 h-4" /> Team Size
                    </span>
                    <span className="text-gray-900 dark:text-gray-100">{stakeholder.team_size}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Engagement Metrics */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Engagement Metrics
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Sentiment Score</span>
                  <span className={`text-xl font-bold ${getSentimentColor(stakeholder.sentiment_score)}`}>
                    {stakeholder.sentiment_score > 0 ? '+' : ''}{stakeholder.sentiment_score.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Sentiment Trend</span>
                  <span className="text-gray-900 dark:text-gray-100 capitalize">
                    {stakeholder.sentiment_trend}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Alignment Score</span>
                  <span className="text-xl font-bold text-teal-600 dark:text-teal-400">
                    {Math.round(stakeholder.alignment_score * 100)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Total Interactions</span>
                  <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
                    {stakeholder.total_interactions}
                  </span>
                </div>
                {stakeholder.last_interaction && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Last Interaction</span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {new Date(stakeholder.last_interaction).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Key Concerns */}
            {stakeholder.key_concerns.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-orange-200 dark:border-orange-800 p-6">
                <h3 className="text-lg font-semibold text-orange-700 dark:text-orange-300 mb-3">
                  Key Concerns
                </h3>
                <div className="flex flex-wrap gap-2">
                  {stakeholder.key_concerns.map((concern, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 text-sm rounded"
                    >
                      {concern}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Interests */}
            {stakeholder.interests.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-green-200 dark:border-green-800 p-6">
                <h3 className="text-lg font-semibold text-green-700 dark:text-green-300 mb-3">
                  Interests
                </h3>
                <div className="flex flex-wrap gap-2">
                  {stakeholder.interests.map((interest, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm rounded"
                    >
                      {interest}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Pain Points */}
            {stakeholder.pain_points && stakeholder.pain_points.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-red-200 dark:border-red-800 p-6">
                <h3 className="text-lg font-semibold text-red-700 dark:text-red-300 mb-3">
                  Pain Points
                </h3>
                <ul className="space-y-2">
                  {stakeholder.pain_points.map((pain, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                      <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                      {pain}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Win Conditions */}
            {stakeholder.win_conditions && stakeholder.win_conditions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-emerald-200 dark:border-emerald-800 p-6">
                <h3 className="text-lg font-semibold text-emerald-700 dark:text-emerald-300 mb-3">
                  Win Conditions
                </h3>
                <ul className="space-y-2">
                  {stakeholder.win_conditions.map((win, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                      <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                      {win}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* AI Priorities */}
            {stakeholder.ai_priorities && stakeholder.ai_priorities.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-indigo-200 dark:border-indigo-800 p-6">
                <h3 className="text-lg font-semibold text-indigo-700 dark:text-indigo-300 mb-3">
                  AI Priorities
                </h3>
                <div className="flex flex-wrap gap-2">
                  {stakeholder.ai_priorities.map((priority, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-sm rounded"
                    >
                      {priority}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Communication Style */}
            {stakeholder.communication_style && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Communication Style
                </h3>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {stakeholder.communication_style}
                </p>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Quick Actions
              </h3>
              <div className="space-y-2">
                <button
                  onClick={() => router.push(`/meeting-prep/${stakeholder.id}`)}
                  className="w-full text-left px-3 py-2 text-sm bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-900/40 rounded-lg transition-colors flex items-center gap-2 font-medium"
                >
                  <ClipboardList className="w-4 h-4" /> Prepare for Meeting
                </button>
                <button
                  onClick={() => router.push('/transcripts')}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" /> Upload Transcript
                </button>
                <button
                  onClick={() => router.push('/chat')}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <MessageCircle className="w-4 h-4" /> Chat with Agents
                </button>
                <button
                  onClick={() => router.push('/opportunities')}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <Target className="w-4 h-4" /> View Opportunities
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
