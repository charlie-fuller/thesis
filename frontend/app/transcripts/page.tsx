'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import TranscriptUpload from '@/components/TranscriptUpload'
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 py-8">
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
            <div className="text-4xl mb-4">&#128221;</div>
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
                        <span>&#128197; {transcript.meeting_date}</span>
                      )}
                      <span>&#128101; {transcript.attendee_count} attendees</span>
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
