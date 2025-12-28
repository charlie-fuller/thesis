'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import TranscriptUpload from '@/components/TranscriptUpload'
import PageHeader from '@/components/PageHeader'
import { apiGet, apiDelete } from '@/lib/api'

interface Transcript {
  id: string
  title: string
  meeting_date: string | null
  meeting_type: string
  attendee_count: number
  summary: string | null
  sentiment: string
  processing_status: string
  created_at: string
}

interface TranscriptsResponse {
  transcripts: Transcript[]
  total: number
}

export default function TranscriptsPage() {
  const router = useRouter()
  const [transcripts, setTranscripts] = useState<Transcript[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  async function loadTranscripts() {
    try {
      setLoading(true)
      setError(null)
      const data = await apiGet<TranscriptsResponse>('/api/transcripts/')
      setTranscripts(data.transcripts || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load transcripts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTranscripts()
  }, [])

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this transcript?')) return

    try {
      setDeletingId(id)
      await apiDelete(`/api/transcripts/${id}`)
      setTranscripts(prev => prev.filter(t => t.id !== id))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete transcript')
    } finally {
      setDeletingId(null)
    }
  }

  function handleUploadComplete() {
    setShowUpload(false)
    loadTranscripts()
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  function getSentimentColor(sentiment: string) {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      case 'negative':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-page">
      <PageHeader />
      <div className="max-w-6xl mx-auto px-4 py-8 w-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Meeting Transcripts
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Upload and analyze meeting transcripts with Oracle
            </p>
          </div>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="btn-primary flex items-center gap-2"
          >
            {showUpload ? (
              <>
                <span>&times;</span>
                Close
              </>
            ) : (
              <>
                <span>+</span>
                New Transcript
              </>
            )}
          </button>
        </div>

        {/* Upload Panel */}
        {showUpload && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Analyze New Transcript
            </h2>
            <TranscriptUpload onUploadComplete={handleUploadComplete} />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">{error}</p>
            <button
              onClick={loadTranscripts}
              className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
            >
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
        {!loading && !error && transcripts.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
            <div className="flex justify-center mb-4">
              <svg className="w-12 h-12 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              No transcripts yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Upload your first meeting transcript to extract stakeholder insights with Oracle.
            </p>
            <button
              onClick={() => setShowUpload(true)}
              className="btn-primary"
            >
              Upload Transcript
            </button>
          </div>
        )}

        {/* Transcripts List */}
        {!loading && transcripts.length > 0 && (
          <div className="space-y-4">
            {transcripts.map((transcript) => (
              <div
                key={transcript.id}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {transcript.title}
                      </h3>
                      {transcript.processing_status === 'completed' ? (
                        <span className={`px-2 py-0.5 text-xs rounded ${getSentimentColor(transcript.sentiment)}`}>
                          {transcript.sentiment}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded">
                          {transcript.processing_status}
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-3 text-sm text-gray-500 dark:text-gray-400 mb-3">
                      {transcript.meeting_date && (
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          {transcript.meeting_date}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        {transcript.attendee_count} attendees
                      </span>
                      <span className="capitalize">{transcript.meeting_type}</span>
                    </div>

                    {transcript.summary && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                        {transcript.summary}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => router.push(`/transcripts/${transcript.id}`)}
                      className="px-3 py-1.5 text-sm text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/20 rounded-lg transition-colors"
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleDelete(transcript.id)}
                      disabled={deletingId === transcript.id}
                      className="px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
                    >
                      {deletingId === transcript.id ? '...' : 'Delete'}
                    </button>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-400 dark:text-gray-500">
                  Uploaded {formatDate(transcript.created_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
