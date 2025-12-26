'use client'

import { useState, useRef } from 'react'
import { API_BASE_URL } from '@/lib/config'
import { authenticatedFetch } from '@/lib/api'

interface TranscriptUploadProps {
  onUploadComplete?: (transcriptId: string) => void
}

interface UploadStatus {
  status: 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error'
  message: string
  progress?: number
}

interface TranscriptAnalysis {
  transcript_id: string
  title: string
  meeting_date: string | null
  meeting_type: string
  attendees: Array<{
    name: string
    role: string
    organization: string
    stakeholder_id: string | null
  }>
  summary: string
  key_topics: string[]
  action_items: Array<{
    description: string
    owner: string
    due_date: string | null
  }>
  sentiment_summary: {
    overall: string
    score: number
  }
  insights: Array<{
    stakeholder_name: string
    insight_type: string
    content: string
    quote: string | null
  }>
}

export default function TranscriptUpload({
  onUploadComplete
}: TranscriptUploadProps) {
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    status: 'idle',
    message: ''
  })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [textContent, setTextContent] = useState<string>('')
  const [inputMode, setInputMode] = useState<'file' | 'paste'>('file')
  const [analysis, setAnalysis] = useState<TranscriptAnalysis | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setUploadStatus({ status: 'idle', message: '' })
      setAnalysis(null)
    }
  }

  async function handleAnalyze() {
    if (inputMode === 'file' && !selectedFile) return
    if (inputMode === 'paste' && !textContent.trim()) return

    try {
      setUploadStatus({
        status: 'uploading',
        message: 'Preparing transcript...',
        progress: 10
      })

      let response: Response

      if (inputMode === 'file' && selectedFile) {
        // Upload file
        const formData = new FormData()
        formData.append('file', selectedFile)

        setUploadStatus({
          status: 'uploading',
          message: `Uploading ${selectedFile.name}...`,
          progress: 30
        })

        response = await authenticatedFetch(`${API_BASE_URL}/api/transcripts/upload`, {
          method: 'POST',
          body: formData
        })
      } else {
        // Analyze pasted text
        setUploadStatus({
          status: 'analyzing',
          message: 'Analyzing transcript with Oracle agent...',
          progress: 40
        })

        response = await authenticatedFetch(`${API_BASE_URL}/api/transcripts/analyze`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ text: textContent })
        })
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Analysis failed: ${response.statusText}`)
      }

      setUploadStatus({
        status: 'analyzing',
        message: 'Extracting stakeholder insights...',
        progress: 70
      })

      const data = await response.json()

      setUploadStatus({
        status: 'complete',
        message: 'Analysis complete!',
        progress: 100
      })

      setAnalysis(data)

      // Clear inputs
      setSelectedFile(null)
      setTextContent('')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      // Notify parent
      if (onUploadComplete && data.transcript_id) {
        onUploadComplete(data.transcript_id)
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setUploadStatus({
        status: 'error',
        message: `Error: ${errorMessage}`,
        progress: 0
      })
    }
  }

  function resetForm() {
    setUploadStatus({ status: 'idle', message: '' })
    setAnalysis(null)
    setSelectedFile(null)
    setTextContent('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const isProcessing = uploadStatus.status === 'uploading' || uploadStatus.status === 'analyzing'
  const canSubmit = inputMode === 'file' ? !!selectedFile : !!textContent.trim()

  return (
    <div className="space-y-6">
      {/* Input Mode Toggle */}
      <div className="flex space-x-2 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setInputMode('file')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            inputMode === 'file'
              ? 'border-teal-500 text-teal-600 dark:text-teal-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          Upload File
        </button>
        <button
          onClick={() => setInputMode('paste')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            inputMode === 'paste'
              ? 'border-teal-500 text-teal-600 dark:text-teal-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          Paste Text
        </button>
      </div>

      {/* File Input */}
      {inputMode === 'file' && (
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md"
            onChange={handleFileSelect}
            disabled={isProcessing}
            className="block w-full text-sm text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer bg-gray-50 dark:bg-gray-800 focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-teal-500 file:text-white hover:file:bg-teal-600"
          />
          {selectedFile && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Selected: <span className="font-medium">{selectedFile.name}</span> ({(selectedFile.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>
      )}

      {/* Text Paste Input */}
      {inputMode === 'paste' && (
        <div>
          <textarea
            value={textContent}
            onChange={(e) => setTextContent(e.target.value)}
            disabled={isProcessing}
            placeholder="Paste your meeting transcript here...

Example format (Granola/Otter.ai):

John (Product Manager): I think we should prioritize the API integration.
Sarah (Engineering Lead): I have some concerns about the timeline..."
            className="w-full h-64 px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {textContent.length} characters
          </p>
        </div>
      )}

      {/* Analyze Button */}
      <button
        onClick={handleAnalyze}
        disabled={!canSubmit || isProcessing}
        className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {uploadStatus.status === 'uploading' ? 'Uploading...' :
         uploadStatus.status === 'analyzing' ? 'Analyzing with Oracle...' :
         'Analyze Transcript'}
      </button>

      {/* Progress Bar */}
      {isProcessing && uploadStatus.progress !== undefined && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-teal-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadStatus.progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 text-center">
            {uploadStatus.message}
          </p>
        </div>
      )}

      {/* Error Message */}
      {uploadStatus.status === 'error' && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-200">{uploadStatus.message}</p>
          <button
            onClick={resetForm}
            className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Analysis Complete
            </h3>
            <button
              onClick={resetForm}
              className="text-sm text-teal-600 dark:text-teal-400 hover:underline"
            >
              Analyze another
            </button>
          </div>

          {/* Meeting Info */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
              {analysis.title}
            </h4>
            <div className="flex flex-wrap gap-2 text-xs">
              {analysis.meeting_date && (
                <span className="px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded">
                  {analysis.meeting_date}
                </span>
              )}
              <span className="px-2 py-1 bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 rounded">
                {analysis.meeting_type}
              </span>
              <span className={`px-2 py-1 rounded ${
                analysis.sentiment_summary.score > 0.2 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
                analysis.sentiment_summary.score < -0.2 ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' :
                'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}>
                Sentiment: {analysis.sentiment_summary.overall}
              </span>
            </div>
          </div>

          {/* Summary */}
          <div>
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Summary</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">{analysis.summary}</p>
          </div>

          {/* Attendees */}
          <div>
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
              Attendees ({analysis.attendees.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {analysis.attendees.map((attendee, i) => (
                <div
                  key={i}
                  className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <div className="font-medium text-sm text-gray-900 dark:text-gray-100">
                    {attendee.name}
                    {attendee.stakeholder_id && (
                      <span className="ml-1 text-teal-500" title="Linked to stakeholder">
                        &#10003;
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {attendee.role}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Key Topics */}
          {analysis.key_topics.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Key Topics</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.key_topics.map((topic, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Insights */}
          {analysis.insights.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
                Stakeholder Insights ({analysis.insights.length})
              </h4>
              <div className="space-y-3">
                {analysis.insights.map((insight, i) => (
                  <div
                    key={i}
                    className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm text-gray-900 dark:text-gray-100">
                        {insight.stakeholder_name}
                      </span>
                      <span className={`px-2 py-0.5 text-xs rounded ${
                        insight.insight_type === 'concern' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300' :
                        insight.insight_type === 'enthusiasm' || insight.insight_type === 'support' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
                        insight.insight_type === 'commitment' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' :
                        'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}>
                        {insight.insight_type}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{insight.content}</p>
                    {insight.quote && (
                      <p className="mt-2 text-xs text-gray-500 dark:text-gray-500 italic border-l-2 border-gray-300 dark:border-gray-600 pl-2">
                        &ldquo;{insight.quote}&rdquo;
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Items */}
          {analysis.action_items.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
                Action Items ({analysis.action_items.length})
              </h4>
              <ul className="space-y-2">
                {analysis.action_items.map((item, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
                  >
                    <span className="text-teal-500 mt-0.5">&#9679;</span>
                    <div>
                      <span>{item.description}</span>
                      {item.owner && (
                        <span className="text-gray-500 dark:text-gray-500">
                          {' '}— {item.owner}
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Supported Formats */}
      {!analysis && (
        <div className="text-xs text-gray-500 dark:text-gray-400 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="font-semibold mb-1">Supported formats:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Granola exports (.txt, .md)</li>
            <li>Otter.ai transcripts (.txt)</li>
            <li>Plain text with speaker labels</li>
          </ul>
          <p className="mt-2">
            The Oracle agent will extract attendees, sentiment, concerns, and action items.
          </p>
        </div>
      )}
    </div>
  )
}
