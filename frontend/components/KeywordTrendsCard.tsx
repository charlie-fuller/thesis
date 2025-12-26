'use client'

import { useState, useEffect, useCallback, memo } from 'react'
import { apiGet } from '@/lib/api'
import LoadingSpinner from './LoadingSpinner'

interface Keyword {
  word: string
  count: number
  is_domain_keyword: boolean
  category: string
}

interface Question {
  text: string
  timestamp: string
}

interface FaqSuggestion {
  topic: string
  count: number
  suggestion: string
}

interface KeywordTrendsData {
  keywords: Keyword[]
  questions: Question[]
  message_count: number
  date_range: string
  domain_keyword_count: number
  suggested_faqs: FaqSuggestion[]
}

function KeywordTrendsCard() {
  const [data, setData] = useState<KeywordTrendsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(30)
  const [showQuestions, setShowQuestions] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await apiGet<KeywordTrendsData>(`/api/admin/analytics/keyword-trends?days=${days}`)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load keyword trends')
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  if (loading) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-primary mb-4">Keyword Trends</h3>
        <div className="flex justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-primary mb-4">Keyword Trends</h3>
        <div className="text-red-600 text-sm">{error}</div>
        <button onClick={fetchData} className="btn-secondary mt-2 text-sm">Retry</button>
      </div>
    )
  }

  if (!data) return null

  const maxCount = data.keywords.length > 0 ? data.keywords[0].count : 1

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-primary">Keyword Trends</h3>
          <p className="text-xs text-secondary mt-1">
            {data.message_count} messages analyzed &bull; {data.date_range}
          </p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="text-sm border border-border rounded px-2 py-1 bg-card"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Domain Keywords Summary */}
      {data.domain_keyword_count > 0 && (
        <div className="mb-4 p-3 rounded-lg bg-teal-50 border border-teal-200">
          <div className="flex items-center gap-2">
            <span className="text-teal-600 font-semibold">{data.domain_keyword_count}</span>
            <span className="text-sm text-teal-700">L&D domain keywords detected</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-border mb-4">
        <button
          onClick={() => setShowQuestions(false)}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            !showQuestions
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Keywords ({data.keywords.length})
        </button>
        <button
          onClick={() => setShowQuestions(true)}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            showQuestions
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Questions ({data.questions.length})
        </button>
      </div>

      {!showQuestions ? (
        <>
          {/* Keywords List */}
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {data.keywords.slice(0, 20).map((keyword, idx) => (
              <div key={keyword.word} className="flex items-center gap-3">
                <span className="text-xs text-secondary w-5 text-right">{idx + 1}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${keyword.is_domain_keyword ? 'text-teal-700' : 'text-primary'}`}>
                      {keyword.word}
                    </span>
                    {keyword.is_domain_keyword && (
                      <span className="text-xs px-1.5 py-0.5 bg-teal-100 text-teal-700 rounded">L&D</span>
                    )}
                  </div>
                  <div className="mt-1 h-2 bg-hover rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${keyword.is_domain_keyword ? 'bg-teal-500' : 'bg-blue-500'}`}
                      style={{ width: `${(keyword.count / maxCount) * 100}%` }}
                    />
                  </div>
                </div>
                <span className="text-sm text-secondary font-mono">{keyword.count}</span>
              </div>
            ))}
          </div>

        </>
      ) : (
        /* Questions List */
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {data.questions.length === 0 ? (
            <p className="text-sm text-secondary text-center py-4">No questions found</p>
          ) : (
            data.questions.map((question, idx) => (
              <div
                key={idx}
                className="p-3 bg-hover border border-default rounded-lg"
              >
                <p className="text-sm text-primary">{question.text}</p>
                <p className="text-xs text-secondary mt-1">{formatDate(question.timestamp)}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default memo(KeywordTrendsCard);
