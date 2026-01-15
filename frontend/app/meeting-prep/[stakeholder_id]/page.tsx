'use client'

import { useState, useEffect, use } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft,
  User,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Calendar,
  MessageCircle,
  ClipboardList,
  RefreshCw,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'

// ============================================================================
// TYPES
// ============================================================================

interface StatusItem {
  area: string
  status: 'green' | 'yellow' | 'red'
  notes: string
}

interface MetricSummary {
  id: string
  metric_name: string
  current_value: string | null
  target_value: string | null
  validation_status: string
  unit: string | null
}

interface OpportunitySummary {
  id: string
  opportunity_code: string
  title: string
  total_score: number
  tier: number
  status: string
  next_step: string | null
  role: string
}

interface StakeholderData {
  id: string
  name: string
  email: string | null
  role: string | null
  department: string | null
  organization: string | null
  priority_level: string | null
  engagement_level: string
  relationship_status: string | null
  sentiment_score: number
  ai_priorities: string[]
  pain_points: string[]
  win_conditions: string[]
}

interface MeetingPrepData {
  stakeholder: StakeholderData
  status_summary: StatusItem[]
  metrics: MetricSummary[]
  opportunities: OpportunitySummary[]
  questions_to_ask: string[]
  recommended_approach: string | null
  last_contact: string | null
  days_since_contact: number | null
}

// ============================================================================
// COMPONENTS
// ============================================================================

function StatusCard({ item }: { item: StatusItem }) {
  const config = {
    green: {
      bg: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-200 dark:border-green-800',
      text: 'text-green-700 dark:text-green-300',
      icon: CheckCircle,
    },
    yellow: {
      bg: 'bg-amber-50 dark:bg-amber-900/20',
      border: 'border-amber-200 dark:border-amber-800',
      text: 'text-amber-700 dark:text-amber-300',
      icon: Clock,
    },
    red: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-700 dark:text-red-300',
      icon: AlertCircle,
    },
  }

  const c = config[item.status]
  const Icon = c.icon

  return (
    <div className={`p-4 rounded-lg border ${c.bg} ${c.border}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-5 h-5 ${c.text}`} />
        <h3 className={`font-medium ${c.text}`}>{item.area}</h3>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400">{item.notes}</p>
    </div>
  )
}

function ValidationBadge({ status }: { status: string }) {
  const config = {
    green: { icon: '🟢', label: 'Validated', color: 'text-green-600 dark:text-green-400' },
    yellow: { icon: '🟡', label: 'Partial', color: 'text-amber-600 dark:text-amber-400' },
    red: { icon: '🔴', label: 'Needs Validation', color: 'text-red-600 dark:text-red-400' },
  }
  const c = config[status as keyof typeof config] || config.red
  return (
    <span className={`text-xs ${c.color}`}>
      {c.icon} {c.label}
    </span>
  )
}

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
      Tier {tier}
    </span>
  )
}

function QuestionItem({
  question,
  index,
  checked,
  onToggle,
}: {
  question: string
  index: number
  checked: boolean
  onToggle: () => void
}) {
  return (
    <div
      onClick={onToggle}
      className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
        checked
          ? 'bg-green-50 dark:bg-green-900/20 line-through opacity-60'
          : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
      }`}
    >
      <div
        className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 mt-0.5 ${
          checked
            ? 'bg-green-500 text-white'
            : 'border border-gray-300 dark:border-gray-600'
        }`}
      >
        {checked && <CheckCircle className="w-4 h-4" />}
      </div>
      <span className="text-sm text-gray-700 dark:text-gray-300">{question}</span>
    </div>
  )
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function MeetingPrepPage(props: { params: Promise<{ stakeholder_id: string }> }) {
  const params = use(props.params)
  const router = useRouter()
  const [data, setData] = useState<MeetingPrepData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [checkedQuestions, setCheckedQuestions] = useState<Set<number>>(new Set())
  const [expandedSections, setExpandedSections] = useState({
    metrics: true,
    opportunities: true,
    questions: true,
    context: false,
  })

  function toggleSection(section: keyof typeof expandedSections) {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  function toggleQuestion(index: number) {
    setCheckedQuestions(prev => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  async function loadData() {
    try {
      setLoading(true)
      setError(null)
      const result = await apiGet<MeetingPrepData>(`/api/meeting-prep/${params.stakeholder_id}`)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load meeting prep data')
    } finally {
      setLoading(false)
    }
  }

  async function markContacted() {
    try {
      await apiPost(`/api/meeting-prep/${params.stakeholder_id}/mark-contacted`, {})
      loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update contact date')
    }
  }

  useEffect(() => {
    loadData()
  }, [params.stakeholder_id])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500"></div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
              Error Loading Meeting Prep
            </h2>
            <p className="text-red-700 dark:text-red-300">{error || 'Data not found'}</p>
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

  const { stakeholder, status_summary, metrics, opportunities, questions_to_ask, recommended_approach, days_since_contact } = data

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <button
              onClick={() => router.push(`/stakeholders/${stakeholder.id}`)}
              className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mb-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Profile
            </button>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
              <ClipboardList className="w-7 h-7 text-teal-600" />
              Meeting Prep: {stakeholder.name}
            </h1>
            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500 dark:text-gray-400">
              {stakeholder.role && <span>{stakeholder.role}</span>}
              {stakeholder.department && (
                <>
                  <span>•</span>
                  <span className="capitalize">{stakeholder.department}</span>
                </>
              )}
              {days_since_contact !== null && (
                <>
                  <span>•</span>
                  <span className={days_since_contact > 14 ? 'text-amber-600' : ''}>
                    {days_since_contact === 0 ? 'Contacted today' : `${days_since_contact} days since contact`}
                  </span>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadData}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            <button
              onClick={markContacted}
              className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 flex items-center gap-2"
            >
              <Calendar className="w-4 h-4" />
              Mark Contacted
            </button>
          </div>
        </div>

        {/* Status at a Glance */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Status at a Glance
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {status_summary.map((item, i) => (
              <StatusCard key={i} item={item} />
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Key Metrics */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => toggleSection('metrics')}
                className="w-full px-6 py-4 flex items-center justify-between text-left"
              >
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-teal-600" />
                  Key Metrics ({metrics.length})
                </h2>
                {expandedSections.metrics ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </button>

              {expandedSections.metrics && metrics.length > 0 && (
                <div className="px-6 pb-6">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left py-2 pr-4 font-medium text-gray-500 dark:text-gray-400">Metric</th>
                          <th className="text-left py-2 px-4 font-medium text-gray-500 dark:text-gray-400">Current</th>
                          <th className="text-left py-2 px-4 font-medium text-gray-500 dark:text-gray-400">Target</th>
                          <th className="text-left py-2 pl-4 font-medium text-gray-500 dark:text-gray-400">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.map(metric => (
                          <tr key={metric.id} className="border-b border-gray-100 dark:border-gray-700/50">
                            <td className="py-3 pr-4 font-medium text-gray-900 dark:text-gray-100">
                              {metric.metric_name}
                            </td>
                            <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                              {metric.current_value || '-'} {metric.unit || ''}
                            </td>
                            <td className="py-3 px-4 text-gray-700 dark:text-gray-300">
                              {metric.target_value || '-'} {metric.unit || ''}
                            </td>
                            <td className="py-3 pl-4">
                              <ValidationBadge status={metric.validation_status} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {expandedSections.metrics && metrics.length === 0 && (
                <div className="px-6 pb-6 text-center text-gray-500 dark:text-gray-400">
                  No metrics tracked for this stakeholder yet.
                </div>
              )}
            </div>

            {/* Active Opportunities */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => toggleSection('opportunities')}
                className="w-full px-6 py-4 flex items-center justify-between text-left"
              >
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  Active Opportunities ({opportunities.length})
                </h2>
                {expandedSections.opportunities ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </button>

              {expandedSections.opportunities && opportunities.length > 0 && (
                <div className="px-6 pb-6 space-y-3">
                  {opportunities.map(opp => (
                    <div
                      key={opp.id}
                      className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-gray-700 dark:text-gray-300">
                            {opp.opportunity_code}
                          </span>
                          <TierBadge tier={opp.tier} />
                          <span className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-600 rounded capitalize">
                            {opp.role}
                          </span>
                        </div>
                        <div className="text-right">
                          <div className="font-bold text-gray-900 dark:text-gray-100">{opp.total_score}/20</div>
                          <div className="text-xs text-gray-500 capitalize">{opp.status}</div>
                        </div>
                      </div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">{opp.title}</h3>
                      {opp.next_step && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                          <span className="font-medium">Next:</span> {opp.next_step}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {expandedSections.opportunities && opportunities.length === 0 && (
                <div className="px-6 pb-6 text-center text-gray-500 dark:text-gray-400">
                  No opportunities linked to this stakeholder yet.
                </div>
              )}
            </div>

            {/* Questions to Ask */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => toggleSection('questions')}
                className="w-full px-6 py-4 flex items-center justify-between text-left"
              >
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                  <MessageCircle className="w-5 h-5 text-purple-600" />
                  Questions to Ask ({questions_to_ask.length})
                  {checkedQuestions.size > 0 && (
                    <span className="text-sm font-normal text-gray-500">
                      ({checkedQuestions.size} checked)
                    </span>
                  )}
                </h2>
                {expandedSections.questions ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </button>

              {expandedSections.questions && questions_to_ask.length > 0 && (
                <div className="px-6 pb-6 space-y-2">
                  {questions_to_ask.map((question, i) => (
                    <QuestionItem
                      key={i}
                      question={question}
                      index={i}
                      checked={checkedQuestions.has(i)}
                      onToggle={() => toggleQuestion(i)}
                    />
                  ))}
                </div>
              )}

              {expandedSections.questions && questions_to_ask.length === 0 && (
                <div className="px-6 pb-6 text-center text-gray-500 dark:text-gray-400">
                  No pending questions for this stakeholder.
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Recommended Approach */}
            {recommended_approach && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-teal-200 dark:border-teal-800 p-6">
                <h3 className="text-lg font-semibold text-teal-700 dark:text-teal-300 mb-3">
                  Recommended Approach
                </h3>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {recommended_approach}
                </p>
              </div>
            )}

            {/* Stakeholder Context */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => toggleSection('context')}
                className="w-full px-6 py-4 flex items-center justify-between text-left"
              >
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                  <User className="w-5 h-5 text-gray-500" />
                  Stakeholder Context
                </h3>
                {expandedSections.context ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </button>

              {expandedSections.context && (
                <div className="px-6 pb-6 space-y-4">
                  {/* Priority & Engagement */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Priority</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      stakeholder.priority_level === 'tier_1' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300' :
                      stakeholder.priority_level === 'tier_2' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' :
                      'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                    }`}>
                      {stakeholder.priority_level?.replace('_', ' ').toUpperCase() || 'Not Set'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Engagement</span>
                    <span className="text-sm text-gray-900 dark:text-gray-100 capitalize">
                      {stakeholder.engagement_level}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Relationship</span>
                    <span className="text-sm text-gray-900 dark:text-gray-100 capitalize">
                      {stakeholder.relationship_status || 'New'}
                    </span>
                  </div>

                  {/* AI Priorities */}
                  {stakeholder.ai_priorities?.length > 0 && (
                    <div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">AI Priorities</div>
                      <div className="flex flex-wrap gap-1">
                        {stakeholder.ai_priorities.map((p, i) => (
                          <span key={i} className="text-xs px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded">
                            {p}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Pain Points */}
                  {stakeholder.pain_points?.length > 0 && (
                    <div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Pain Points</div>
                      <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
                        {stakeholder.pain_points.slice(0, 3).map((p, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <span className="text-red-500">•</span> {p}
                          </li>
                        ))}
                        {stakeholder.pain_points.length > 3 && (
                          <li className="text-gray-500 text-xs">+{stakeholder.pain_points.length - 3} more</li>
                        )}
                      </ul>
                    </div>
                  )}

                  {/* Win Conditions */}
                  {stakeholder.win_conditions?.length > 0 && (
                    <div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Win Conditions</div>
                      <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
                        {stakeholder.win_conditions.slice(0, 3).map((w, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <span className="text-green-500">•</span> {w}
                          </li>
                        ))}
                        {stakeholder.win_conditions.length > 3 && (
                          <li className="text-gray-500 text-xs">+{stakeholder.win_conditions.length - 3} more</li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Quick Actions
              </h3>
              <div className="space-y-2">
                <button
                  onClick={() => router.push(`/stakeholders/${stakeholder.id}`)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <User className="w-4 h-4" /> View Full Profile
                </button>
                <button
                  onClick={() => router.push('/opportunities')}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <Target className="w-4 h-4" /> View All Opportunities
                </button>
                <button
                  onClick={() => router.push('/chat')}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <MessageCircle className="w-4 h-4" /> Chat with Agents
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
