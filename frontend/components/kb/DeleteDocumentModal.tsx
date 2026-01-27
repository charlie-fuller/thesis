'use client'

import { useState, useEffect } from 'react'
import { X, AlertTriangle, Loader2, Trash2 } from 'lucide-react'
import { apiGet, apiDelete } from '@/lib/api'

interface Initiative {
  id: string
  name: string
  status: string
}

interface DeleteDocumentModalProps {
  isOpen: boolean
  documentId: string | null
  documentName: string
  onClose: () => void
  onDeleted: () => void
}

export default function DeleteDocumentModal({
  isOpen,
  documentId,
  documentName,
  onClose,
  onDeleted
}: DeleteDocumentModalProps) {
  const [loading, setLoading] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [initiatives, setInitiatives] = useState<Initiative[]>([])
  const [error, setError] = useState<string | null>(null)

  // Check for initiative links when modal opens
  useEffect(() => {
    if (!isOpen || !documentId) {
      setInitiatives([])
      setError(null)
      return
    }

    const checkInitiativeLinks = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await apiGet<{
          success: boolean
          initiatives: Initiative[]
        }>(`/api/documents/${documentId}/initiative-links`)
        setInitiatives(result.initiatives || [])
      } catch (err) {
        console.error('Failed to check initiative links:', err)
        // If we can't check, allow deletion with warning
        setInitiatives([])
      } finally {
        setLoading(false)
      }
    }

    checkInitiativeLinks()
  }, [isOpen, documentId])

  const handleDelete = async () => {
    if (!documentId) return

    setDeleting(true)
    setError(null)
    try {
      // Use force=true if there are linked initiatives
      const url = initiatives.length > 0
        ? `/api/documents/${documentId}?force=true`
        : `/api/documents/${documentId}`

      await apiDelete(url)
      onDeleted()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document')
    } finally {
      setDeleting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
              <Trash2 className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              Delete Document
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
            </div>
          ) : (
            <>
              <p className="text-slate-700 dark:text-slate-300 mb-4">
                Are you sure you want to delete <strong>&quot;{documentName}&quot;</strong>?
              </p>

              {initiatives.length > 0 && (
                <div className="mb-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-amber-800 dark:text-amber-300 mb-2">
                        This document is linked to {initiatives.length} initiative{initiatives.length !== 1 ? 's' : ''}
                      </p>
                      <p className="text-sm text-amber-700 dark:text-amber-400 mb-2">
                        Deleting it will remove it from:
                      </p>
                      <ul className="text-sm text-amber-700 dark:text-amber-400 list-disc list-inside space-y-1">
                        {initiatives.map(initiative => (
                          <li key={initiative.id}>
                            {initiative.name}
                            <span className="text-amber-500 dark:text-amber-500 text-xs ml-2">
                              ({initiative.status})
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              <p className="text-sm text-slate-500 dark:text-slate-400">
                This action cannot be undone.
              </p>

              {error && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
                  {error}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={deleting}
            className="px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={loading || deleting}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {deleting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="w-4 h-4" />
                Delete{initiatives.length > 0 ? ' Anyway' : ''}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
