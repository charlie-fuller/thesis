'use client'

import { useState } from 'react'
import {
  FileText,
  Unlink,
  ExternalLink,
  Clock,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { apiDelete } from '@/lib/api'

interface Document {
  id: string
  filename: string
  title?: string | null
  uploaded_at: string
  source_platform?: string
  linked_at?: string
}

interface DocumentListProps {
  documents: Document[]
  canDelete: boolean
  initiativeId: string
  onDeleted: (docId: string) => void
}

function DocumentItem({
  document: doc,
  canDelete,
  initiativeId,
  onDeleted
}: {
  document: Document
  canDelete: boolean
  initiativeId: string
  onDeleted: (docId: string) => void
}) {
  const [unlinking, setUnlinking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const displayName = doc.title || doc.filename

  const handleUnlink = async () => {
    if (!confirm('Unlink this document from the initiative? The document will remain in the Knowledge Base.')) {
      return
    }

    setUnlinking(true)
    setError(null)

    try {
      await apiDelete(`/api/disco/initiatives/${initiativeId}/linked-documents/${doc.id}`)
      onDeleted(doc.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unlink')
    } finally {
      setUnlinking(false)
    }
  }

  const getSourceIcon = () => {
    switch (doc.source_platform) {
      case 'obsidian':
        return <span className="text-purple-500 text-xs">Vault</span>
      case 'google_drive':
        return <span className="text-blue-500 text-xs">Drive</span>
      default:
        return <span className="text-slate-400 text-xs">Uploaded</span>
    }
  }

  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-slate-300 dark:hover:border-slate-600 transition-colors">
      <FileText className="w-5 h-5 text-slate-400 flex-shrink-0" />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-900 dark:text-white truncate">
            {displayName}
          </span>
          {getSourceIcon()}
        </div>
        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {doc.linked_at
              ? `Linked ${new Date(doc.linked_at).toLocaleDateString()}`
              : new Date(doc.uploaded_at).toLocaleDateString()
            }
          </span>
          {doc.title && doc.filename !== doc.title && (
            <span className="truncate max-w-[200px]" title={doc.filename}>
              {doc.filename}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* View in KB link */}
        <a
          href={`/kb?doc=${doc.id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md transition-colors"
          title="View in Knowledge Base"
        >
          <ExternalLink className="w-4 h-4" />
        </a>

        {/* Unlink button */}
        {canDelete && (
          <button
            onClick={handleUnlink}
            disabled={unlinking}
            className="p-2 text-slate-400 hover:text-orange-600 dark:hover:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-md transition-colors disabled:opacity-50"
            title="Unlink from initiative"
          >
            {unlinking ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Unlink className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="absolute inset-x-0 bottom-0 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-sm text-red-600 dark:text-red-400 rounded-b-lg">
          <AlertCircle className="w-4 h-4 inline mr-1" />
          {error}
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
        <p className="text-slate-500 dark:text-slate-400">No documents linked</p>
        <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
          Link documents from the Knowledge Base to build context for analysis
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
        Linked Documents ({documents.length})
      </h3>
      {documents.map((doc) => (
        <DocumentItem
          key={doc.id}
          document={doc}
          canDelete={canDelete}
          initiativeId={initiativeId}
          onDeleted={onDeleted}
        />
      ))}
    </div>
  )
}
