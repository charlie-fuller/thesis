'use client'

import { useState } from 'react'
import {
  FileText,
  Trash2,
  Download,
  ChevronDown,
  ChevronRight,
  Clock,
  Tag,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { apiDelete } from '@/lib/api'

interface Document {
  id: string
  filename: string
  content: string
  document_type: string
  version: number
  uploaded_at: string
  metadata: Record<string, any>
}

interface DocumentListProps {
  documents: Document[]
  canDelete: boolean
  initiativeId: string
  onDeleted: (docId: string) => void
}

const DOC_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  uploaded: { label: 'Uploaded', color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' },
  triage_output: { label: 'Triage', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  discovery_output: { label: 'Discovery', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  coverage_output: { label: 'Coverage', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
  prd_output: { label: 'PRD', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  tech_eval_output: { label: 'Tech Eval', color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400' },
}

function DocumentItem({
  document,
  canDelete,
  initiativeId,
  onDeleted
}: {
  document: Document
  canDelete: boolean
  initiativeId: string
  onDeleted: (docId: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const typeConfig = DOC_TYPE_CONFIG[document.document_type] || DOC_TYPE_CONFIG.uploaded

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return
    }

    setDeleting(true)
    setError(null)

    try {
      await apiDelete(`/api/purdy/initiatives/${initiativeId}/documents/${document.id}`)
      onDeleted(document.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete')
    } finally {
      setDeleting(false)
    }
  }

  const handleDownload = () => {
    const blob = new Blob([document.content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = document.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-white dark:bg-slate-800">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          {expanded ? (
            <ChevronDown className="w-5 h-5" />
          ) : (
            <ChevronRight className="w-5 h-5" />
          )}
        </button>

        <FileText className="w-5 h-5 text-slate-400" />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-900 dark:text-white truncate">
              {document.filename}
            </span>
            <span className={`px-2 py-0.5 text-xs rounded-full ${typeConfig.color}`}>
              {typeConfig.label}
            </span>
            {document.version > 1 && (
              <span className="text-xs text-slate-500">v{document.version}</span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(document.uploaded_at).toLocaleDateString()}
            </span>
            <span>{document.content.length.toLocaleString()} chars</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDownload}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md transition-colors"
            title="Download"
          >
            <Download className="w-4 h-4" />
          </button>
          {canDelete && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="p-2 text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors disabled:opacity-50"
              title="Delete"
            >
              {deleting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Expanded Content Preview */}
      {expanded && (
        <div className="border-t border-slate-200 dark:border-slate-700 p-4 bg-slate-50 dark:bg-slate-900/50">
          <pre className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
            {document.content.slice(0, 5000)}
            {document.content.length > 5000 && (
              <span className="text-slate-400">
                {'\n\n... (truncated, {(document.content.length - 5000).toLocaleString()} more characters)'}
              </span>
            )}
          </pre>
        </div>
      )}
    </div>
  )
}

export default function DocumentList({
  documents,
  canDelete,
  initiativeId,
  onDeleted
}: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-12 border border-dashed border-slate-300 dark:border-slate-600 rounded-lg">
        <FileText className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
        <p className="text-slate-500 dark:text-slate-400">No documents yet</p>
        <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
          Upload documents to start building context for analysis
        </p>
      </div>
    )
  }

  // Group documents by type
  const uploadedDocs = documents.filter(d => d.document_type === 'uploaded')
  const outputDocs = documents.filter(d => d.document_type !== 'uploaded')

  return (
    <div className="space-y-6">
      {/* Uploaded Documents */}
      {uploadedDocs.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
            Uploaded Documents ({uploadedDocs.length})
          </h3>
          <div className="space-y-2">
            {uploadedDocs.map((doc) => (
              <DocumentItem
                key={doc.id}
                document={doc}
                canDelete={canDelete}
                initiativeId={initiativeId}
                onDeleted={onDeleted}
              />
            ))}
          </div>
        </div>
      )}

      {/* Output Documents */}
      {outputDocs.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
            Generated Outputs ({outputDocs.length})
          </h3>
          <div className="space-y-2">
            {outputDocs.map((doc) => (
              <DocumentItem
                key={doc.id}
                document={doc}
                canDelete={canDelete}
                initiativeId={initiativeId}
                onDeleted={onDeleted}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
