'use client'

import { useState, useEffect, use } from 'react'
import { useRouter } from 'next/navigation'
import { apiGet } from '@/lib/api'

interface Attendee {
  name: string
  role: string
  organization: string
  stakeholder_id: string | null
}

interface ActionItem {
  description: string
  owner: string
  due_date: string | null
  status: string
}

interface Insight {
  id: string
  insight_type: string
  content: string
  quote: string | null
  confidence: number
  is_resolved: boolean
  stakeholder_name: string
}

interface TranscriptDetail {
  id: string
  title: string
  meeting_date: string | null
  meeting_type: string
  raw_text: string | null
  attendees: Attendee[]
  summary: string
  key_topics: string[]
  sentiment_summary: {
    overall: string
    score: number
  }
  action_items: ActionItem[]
  decisions: string[]
  open_questions: string[]
  processing_status: string
  created_at: string
}

interface InsightsResponse {
  insights: Insight[]
  total: number
}

export default function TranscriptDetailPage(props: { params: Promise<{ id: string }> }) {
  const params = use(props.params)
  const router = useRouter()
  const [transcript, setTranscript] = useState<TranscriptDetail | null>(null)
  const [insights, setInsights] = useState<Insight[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showRawText, setShowRawText] = useState(false)

  useEffect(() => {
    async function loadTranscript() {
      try {
        setLoading(true)
        setError(null)

        const [transcriptData, insightsData] = await Promise.all([
          apiGet<TranscriptDetail>(`/api/transcripts/${params.id}`),
          apiGet<InsightsResponse>(`/api/transcripts/${params.id}/insights`)
        ])

        setTranscript(transcriptData)
        setInsights(insightsData.insights || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load transcript')
      } finally {
        setLoading(false)
      }
    }

    loadTranscript()
  }, [params.id])

  function getSentimentColor(score: number) {
    if (score > 0.2) return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
    if (score < -0.2) return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
    return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
  }

  function getInsightColor(type: string) {
    switch (type) {
      case 'concern':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800'
      case 'enthusiasm':
      case 'support':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800'
      case 'commitment':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800'
      case 'objection':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800'
      case 'question':
        return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800'
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500"></div>
      </div>
    )
  }

  if (error || !transcript) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
              Error Loading Transcript
            </h2>
            <p className="text-red-700 dark:text-red-300">{error || 'Transcript not found'}</p>
            <button
              onClick={() => router.push('/transcripts')}
              className="mt-4 text-sm text-red-600 dark:text-red-400 hover:underline"
            >
              &larr; Back to transcripts
            </button>
          </div>
        </div>
      </div>
    )
  }

  const concernCount = insights.filter(i => i.insight_type === 'concern').length
  const supportCount = insights.filter(i => ['enthusiasm', 'support', 'commitment'].includes(i.insight_type)).length

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Back Button */}
        <button
          onClick={() => router.push('/transcripts')}
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mb-6 flex items-center gap-1"
        >
          &larr; Back to transcripts
        </button>

        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                {transcript.title}
              </h1>
              <div className="flex flex-wrap gap-3 text-sm">
                {transcript.meeting_date && (
                  <span className="text-gray-500 dark:text-gray-400">
                    &#128197; {transcript.meeting_date}
                  </span>
                )}
                <span className="px-2 py-0.5 bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 rounded capitalize">
                  {transcript.meeting_type}
                </span>
                <span className={`px-2 py-0.5 rounded ${getSentimentColor(transcript.sentiment_summary.score)}`}>
                  {transcript.sentiment_summary.overall} ({transcript.sentiment_summary.score.toFixed(2)})
                </span>
              </div>
            </div>
            <div className="text-right text-sm text-gray-400 dark:text-gray-500">
              <div>{transcript.attendees.length} attendees</div>
              <div>{insights.length} insights</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Summary */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Summary
              </h2>
              <p className="text-gray-600 dark:text-gray-400">{transcript.summary}</p>
            </div>

            {/* Key Topics */}
            {transcript.key_topics.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Key Topics
                </h2>
                <div className="flex flex-wrap gap-2">
                  {transcript.key_topics.map((topic, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Stakeholder Insights */}
            {insights.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Stakeholder Insights
                  </h2>
                  <div className="flex gap-3 text-sm">
                    {concernCount > 0 && (
                      <span className="text-orange-600 dark:text-orange-400">
                        {concernCount} concerns
                      </span>
                    )}
                    {supportCount > 0 && (
                      <span className="text-green-600 dark:text-green-400">
                        {supportCount} positive
                      </span>
                    )}
                  </div>
                </div>
                <div className="space-y-4">
                  {insights.map((insight) => (
                    <div
                      key={insight.id}
                      className={`p-4 rounded-lg border ${getInsightColor(insight.insight_type)}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {insight.stakeholder_name}
                          </span>
                          <span className="text-xs px-2 py-0.5 bg-white/50 dark:bg-black/20 rounded">
                            {insight.insight_type}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {Math.round(insight.confidence * 100)}% confidence
                        </span>
                      </div>
                      <p className="text-sm">{insight.content}</p>
                      {insight.quote && (
                        <p className="mt-2 text-xs italic opacity-75 border-l-2 border-current pl-2">
                          &ldquo;{insight.quote}&rdquo;
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Items */}
            {transcript.action_items.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Action Items
                </h2>
                <ul className="space-y-3">
                  {transcript.action_items.map((item, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        disabled
                        checked={item.status === 'completed'}
                        className="mt-1 rounded border-gray-300 dark:border-gray-600"
                      />
                      <div>
                        <p className="text-gray-700 dark:text-gray-300">{item.description}</p>
                        <div className="flex gap-3 text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {item.owner && <span>Owner: {item.owner}</span>}
                          {item.due_date && <span>Due: {item.due_date}</span>}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Raw Transcript */}
            {transcript.raw_text && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <button
                  onClick={() => setShowRawText(!showRawText)}
                  className="flex items-center justify-between w-full text-left"
                >
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Raw Transcript
                  </h2>
                  <span className="text-teal-600 dark:text-teal-400 text-sm">
                    {showRawText ? 'Hide' : 'Show'}
                  </span>
                </button>
                {showRawText && (
                  <pre className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap overflow-x-auto max-h-96 overflow-y-auto">
                    {transcript.raw_text}
                  </pre>
                )}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Attendees */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Attendees ({transcript.attendees.length})
              </h2>
              <div className="space-y-3">
                {transcript.attendees.map((attendee, i) => (
                  <div
                    key={i}
                    className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                  >
                    <div className="font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
                      {attendee.name}
                      {attendee.stakeholder_id && (
                        <span className="text-teal-500 text-xs" title="Linked to stakeholder database">
                          &#10003;
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {attendee.role}
                    </div>
                    <div className="text-xs text-gray-400 dark:text-gray-500">
                      {attendee.organization}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Decisions */}
            {transcript.decisions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Decisions Made
                </h2>
                <ul className="space-y-2">
                  {transcript.decisions.map((decision, i) => (
                    <li
                      key={i}
                      className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2"
                    >
                      <span className="text-teal-500 mt-0.5">&#10003;</span>
                      {decision}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Open Questions */}
            {transcript.open_questions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Open Questions
                </h2>
                <ul className="space-y-2">
                  {transcript.open_questions.map((question, i) => (
                    <li
                      key={i}
                      className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2"
                    >
                      <span className="text-purple-500">?</span>
                      {question}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
