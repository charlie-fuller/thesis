'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { apiGet, apiPost, apiDelete } from '@/lib/api'
import { logger } from '@/lib/logger'
import LoadingSpinner from '@/components/LoadingSpinner'
import DeleteDocumentModal from '@/components/kb/DeleteDocumentModal'
import type { Document } from '@/components/kb/KBDocumentInfoModal'

interface KBFinderContentProps {
  selectedFolder: string | null
  searchQuery: string
  sourceFilter: string
  onDocumentClick: (doc: Document) => void
  onDocumentsChange: () => void
  refreshTrigger?: number
}

function parseLocalDate(dateStr: string): Date {
  if (dateStr.includes('T')) return new Date(dateStr)
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day, 12, 0, 0)
}

function formatDate(isoString: string) {
  const date = new Date(isoString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function formatLongDate(isoString: string) {
  const date = new Date(isoString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export default function KBFinderContent({
  selectedFolder,
  searchQuery,
  sourceFilter,
  onDocumentClick,
  onDocumentsChange,
  refreshTrigger = 0
}: KBFinderContentProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [offset, setOffset] = useState(0)
  const [totalCount, setTotalCount] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)
  const loadMoreRef = useRef<HTMLDivElement>(null)

  // Delete state
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [docToDelete, setDocToDelete] = useState<Document | null>(null)

  // Notification state
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Sync doc state
  const [syncingDocId, setSyncingDocId] = useState<string | null>(null)

  const LIMIT = 50

  const fetchDocuments = useCallback(async (reset = true) => {
    if (reset) {
      setLoading(true)
      setOffset(0)
    }

    try {
      const params = new URLSearchParams()
      params.set('limit', String(LIMIT))
      params.set('offset', reset ? '0' : String(offset))

      // Use folder-based search when a specific folder is selected (not __all__)
      if (selectedFolder && selectedFolder !== '__all__') {
        params.set('folder', selectedFolder)
        params.set('sort', 'name_asc')
      }

      // Add search query
      if (searchQuery.trim()) {
        params.set('q', searchQuery.trim())
      }

      // Add source filter
      if (sourceFilter !== 'all') {
        params.set('source', sourceFilter)
      }

      const result = await apiGet<{
        success: boolean
        documents: Document[]
        total_count?: number
        hasMore?: boolean
      }>(`/api/documents/search?${params}`)

      let docs = result.documents || []

      // When browsing a specific folder (not __all__), filter to direct children only
      if (selectedFolder && selectedFolder !== '__all__' && !searchQuery.trim()) {
        docs = docs.filter(doc => {
          if (!doc.obsidian_file_path) return false
          const relativePath = doc.obsidian_file_path.substring(selectedFolder.length + 1)
          return relativePath && !relativePath.includes('/')
        })
      }

      if (reset) {
        setDocuments(docs)
      } else {
        setDocuments(prev => [...prev, ...docs])
      }

      setTotalCount(result.total_count || docs.length)
      setHasMore(result.hasMore || false)
      setOffset(prev => reset ? LIMIT : prev + LIMIT)
    } catch (err) {
      logger.error('Failed to load documents:', err)
      setErrorMsg('Failed to load documents')
      setTimeout(() => setErrorMsg(null), 3000)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [selectedFolder, searchQuery, sourceFilter, offset])

  // Reload when folder, search, source, or refresh trigger changes
  useEffect(() => {
    fetchDocuments(true)
  }, [selectedFolder, searchQuery, sourceFilter, refreshTrigger])

  // Infinite scroll observer
  useEffect(() => {
    const sentinel = loadMoreRef.current
    if (!sentinel || !hasMore) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          setLoadingMore(true)
          fetchDocuments(false)
        }
      },
      { threshold: 0.1 }
    )

    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [hasMore, loadingMore, fetchDocuments])

  function handleViewDocument(doc: Document) {
    if (doc.storage_url) {
      window.open(doc.storage_url, '_blank', 'noopener,noreferrer')
    } else if (doc.external_url) {
      window.open(doc.external_url, '_blank', 'noopener,noreferrer')
    }
  }

  function handleDeleteClick(doc: Document, e: React.MouseEvent) {
    e.stopPropagation()
    setDocToDelete(doc)
    setShowDeleteModal(true)
  }

  async function handleDocumentSync(doc: Document, e: React.MouseEvent) {
    e.stopPropagation()
    if (!doc.google_drive_file_id) return

    setSyncingDocId(doc.id)
    try {
      await apiPost(`/api/google-drive/sync-document/${doc.google_drive_file_id}`)
      setSuccessMsg(`Syncing ${doc.filename}...`)
      setTimeout(() => {
        setSuccessMsg(null)
        onDocumentsChange()
      }, 2000)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to sync document')
      setTimeout(() => setErrorMsg(null), 3000)
    } finally {
      setSyncingDocId(null)
    }
  }

  function getSourceBadge(doc: Document) {
    if (doc.source_platform === 'google_drive') {
      return <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">Drive</span>
    }
    if (doc.source_platform === 'obsidian') {
      return <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">Vault</span>
    }
    if (doc.source_platform === 'notion') {
      return <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">Notion</span>
    }
    return <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">Upload</span>
  }

  // Build breadcrumb from folder path (skip for __all__)
  const breadcrumbParts = selectedFolder && selectedFolder !== '__all__' ? selectedFolder.split('/') : []

  // Empty state when no folder selected (initial state only, not when __all__ is selected)
  if (selectedFolder === null && !searchQuery.trim() && sourceFilter === 'all') {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-6 py-12">
        <svg className="w-12 h-12 text-muted mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <p className="text-secondary font-medium mb-1">Select a folder to browse</p>
        <p className="text-sm text-muted">Choose a folder from the sidebar to view its documents, or use search to find specific documents.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Breadcrumb */}
      {selectedFolder && (
        <div className="flex items-center gap-1 px-4 py-2 text-sm border-b border-default bg-subtle">
          <button
            onClick={() => {/* Could navigate up */}}
            className="text-muted hover:text-primary"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h6a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clipRule="evenodd" />
            </svg>
          </button>
          {breadcrumbParts.map((part, i) => (
            <span key={i} className="flex items-center gap-1">
              <svg className="w-3 h-3 text-muted" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              <span className={i === breadcrumbParts.length - 1 ? 'text-primary font-medium' : 'text-muted'}>
                {part}
              </span>
            </span>
          ))}
          {documents.length > 0 && (
            <span className="text-muted ml-auto text-xs">{documents.length} document{documents.length !== 1 ? 's' : ''}</span>
          )}
        </div>
      )}

      {/* All Documents header */}
      {selectedFolder === '__all__' && !searchQuery.trim() && sourceFilter === 'all' && (
        <div className="px-4 py-2 text-sm border-b border-default bg-subtle">
          <span className="text-muted">
            All Documents
            {documents.length > 0 && ` (${documents.length})`}
          </span>
        </div>
      )}

      {/* Search/filter results header */}
      {(searchQuery.trim() || sourceFilter !== 'all') && (selectedFolder === '__all__' || !selectedFolder) && (
        <div className="px-4 py-2 text-sm border-b border-default bg-subtle">
          <span className="text-muted">
            {searchQuery.trim() && `Search: "${searchQuery.trim()}"`}
            {searchQuery.trim() && sourceFilter !== 'all' && ' - '}
            {sourceFilter !== 'all' && `Source: ${sourceFilter === 'obsidian' ? 'Vault' : sourceFilter}`}
            {documents.length > 0 && ` (${documents.length} result${documents.length !== 1 ? 's' : ''})`}
          </span>
        </div>
      )}

      {/* Messages */}
      {successMsg && (
        <div className="mx-4 mt-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-2">
          <span className="text-sm text-green-800 dark:text-green-200">{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="mx-4 mt-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-2">
          <span className="text-sm text-red-800 dark:text-red-200">{errorMsg}</span>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="text-center py-12">
            <LoadingSpinner size="md" />
            <p className="mt-2 text-sm text-muted">Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12 text-muted">
            <p className="text-sm">No documents in this folder</p>
          </div>
        ) : (
          <div className="divide-y divide-default">
            {documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => onDocumentClick(doc)}
                className="flex items-center gap-3 px-4 py-2.5 hover:bg-hover transition-colors cursor-pointer group"
              >
                {/* File icon */}
                <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>

                {/* Filename */}
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-primary truncate block">
                    {doc.title || doc.filename}
                  </span>
                </div>

                {/* Processing badge */}
                {!doc.processed && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200 flex-shrink-0">
                    <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing
                  </span>
                )}
                {doc.processed && doc.processing_status === 'failed' && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-200 flex-shrink-0">
                    Failed
                  </span>
                )}

                {/* Source badge */}
                {getSourceBadge(doc)}

                {/* Date */}
                <span className="text-xs text-muted flex-shrink-0 w-16 text-right" title={formatLongDate(doc.original_date || doc.uploaded_at)}>
                  {formatDate(doc.original_date || doc.uploaded_at)}
                </span>

                {/* Action buttons (visible on hover) */}
                <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  {/* Sync button for Drive docs */}
                  {doc.source_platform === 'google_drive' && (
                    <button
                      onClick={(e) => handleDocumentSync(doc, e)}
                      disabled={syncingDocId === doc.id}
                      className="p-1 text-gray-400 hover:text-blue-600 rounded transition-colors disabled:opacity-50"
                      title="Sync from Drive"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  )}

                  {/* View button */}
                  {(doc.storage_url || doc.external_url) && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleViewDocument(doc); }}
                      className="p-1 text-gray-400 hover:text-green-600 rounded transition-colors"
                      title="View document"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                  )}

                  {/* Delete button */}
                  <button
                    onClick={(e) => handleDeleteClick(doc, e)}
                    className="p-1 text-gray-400 hover:text-red-600 rounded transition-colors"
                    title="Delete"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}

            {/* Infinite scroll sentinel */}
            {hasMore && (
              <div ref={loadMoreRef} className="h-10 flex items-center justify-center">
                {loadingMore && (
                  <div className="flex items-center gap-2 text-sm text-muted">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Loading more...
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Delete Modal */}
      <DeleteDocumentModal
        isOpen={showDeleteModal}
        documentId={docToDelete?.id || null}
        documentName={docToDelete?.filename || ''}
        onClose={() => {
          setShowDeleteModal(false)
          setDocToDelete(null)
        }}
        onDeleted={() => {
          onDocumentsChange()
          fetchDocuments(true)
        }}
      />
    </div>
  )
}
