'use client'

/**
 * DocumentViewerModal Component
 *
 * Read-only modal for viewing document content directly without navigating
 * to the knowledge base page. Supports markdown rendering.
 */

import { useState, useEffect, useRef } from 'react'
import { X, FileText, Loader2, Download, ExternalLink } from 'lucide-react'
import { apiGet } from '@/lib/api'
import ReactMarkdown from 'react-markdown'

// ============================================================================
// TYPES
// ============================================================================

interface DocumentInfo {
  document_id: string
  document_name: string
}

interface DocumentContent {
  document: {
    id: string
    filename: string
    title: string | null
    mime_type: string | null
  }
  content: string
  chunk_count: number
}

interface DocumentViewerModalProps {
  document: DocumentInfo | null
  open: boolean
  onClose: () => void
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function DocumentViewerModal({
  document,
  open,
  onClose,
}: DocumentViewerModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [content, setContent] = useState<DocumentContent | null>(null)
  const modalRef = useRef<HTMLDivElement>(null)

  // Fetch document content when modal opens
  useEffect(() => {
    if (open && document) {
      fetchDocumentContent()
    } else {
      // Reset state when modal closes
      setContent(null)
      setError(null)
    }
  }, [open, document?.document_id])

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        onClose()
      }
    }

    if (open) {
      window.addEventListener('keydown', handleKeyDown)
      // Prevent body scroll when modal is open
      const originalOverflow = window.document.body.style.overflow
      window.document.body.style.overflow = 'hidden'

      return () => {
        window.removeEventListener('keydown', handleKeyDown)
        window.document.body.style.overflow = originalOverflow
      }
    }
  }, [open, onClose])

  const fetchDocumentContent = async () => {
    if (!document) return

    setLoading(true)
    setError(null)

    try {
      const result = await apiGet<DocumentContent>(
        `/api/documents/${document.document_id}/content`
      )
      setContent(result)
    } catch (err) {
      console.error('Failed to fetch document content:', err)
      setError('Failed to load document content. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!document) return

    try {
      const result = await apiGet<{ download_url: string }>(
        `/api/documents/${document.document_id}/download`
      )
      window.open(result.download_url, '_blank')
    } catch (err) {
      console.error('Failed to get download URL:', err)
      alert('Failed to download document. Please try again.')
    }
  }

  const openInKnowledgeBase = () => {
    if (!document) return
    const url = `/kb?doc=${document.document_id}`
    window.open(url, '_blank')
  }

  const isMarkdown = content?.document?.mime_type?.includes('markdown') ||
    content?.document?.filename?.endsWith('.md')

  if (!open) return null

  const displayTitle = content?.document?.title ||
    document?.document_name ||
    content?.document?.filename ||
    'Document'

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        ref={modalRef}
        className="relative bg-card border border-default rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col mx-4"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-default">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <FileText className="w-5 h-5 text-muted flex-shrink-0" />
            <h2 className="text-lg font-semibold text-primary truncate">
              {displayTitle}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="p-2 text-muted hover:text-primary hover:bg-hover rounded-lg transition-colors"
              title="Download document"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={openInKnowledgeBase}
              className="p-2 text-muted hover:text-primary hover:bg-hover rounded-lg transition-colors"
              title="Open in Knowledge Base"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-muted hover:text-primary hover:bg-hover rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-muted" />
              <span className="ml-2 text-muted">Loading document...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-500 mb-4">{error}</p>
              <button
                onClick={fetchDocumentContent}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          ) : content ? (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {isMarkdown ? (
                <ReactMarkdown>{content.content}</ReactMarkdown>
              ) : (
                <pre className="whitespace-pre-wrap font-sans text-sm text-secondary leading-relaxed">
                  {content.content}
                </pre>
              )}
            </div>
          ) : (
            <p className="text-muted text-center py-12">No content available</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-default">
          <span className="text-xs text-muted">
            {content?.chunk_count ? `${content.chunk_count} chunks` : ''}
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 text-secondary hover:text-primary hover:bg-hover rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
