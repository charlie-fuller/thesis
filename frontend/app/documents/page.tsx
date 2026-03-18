'use client'

import { useState, useEffect, useCallback, Suspense } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import DocumentUpload from '@/components/DocumentUpload'
import LoadingSpinner from '@/components/LoadingSpinner'
import ConfirmModal from '@/components/ConfirmModal'
import StorageIndicator from '@/components/StorageIndicator'
import PageHeader from '@/components/PageHeader'
import { logger } from '@/lib/logger'
import { apiGet, apiDelete } from '@/lib/api'
import { API_BASE_URL } from '@/lib/config'

interface Document {
  id: string
  filename: string
  uploaded_at: string
  processed: boolean
  processing_status?: string
  processing_error?: string
  storage_url: string
  source_platform?: string
  external_url?: string
  sync_cadence?: string
  file_size?: number
  is_core_document?: boolean
}

function DocumentsContent() {
  const { profile } = useAuth()

  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Document actions state
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null)
  const [showInfoModal, setShowInfoModal] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [docToDelete, setDocToDelete] = useState<Document | null>(null)

  // General document notifications
  const [generalSuccess, setGeneralSuccess] = useState<string | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)

  // Storage refresh trigger
  const [storageRefreshTrigger, setStorageRefreshTrigger] = useState<number>(0)

  // Upload and Documents section state
  const [uploadExpanded, setUploadExpanded] = useState<boolean>(false)
  const [documentsExpanded, setDocumentsExpanded] = useState<boolean>(false)
  const [coreDocumentsExpanded, setCoreDocumentsExpanded] = useState<boolean>(false)


  // Define functions first with useCallback
  const loadDocuments = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true)
      }
      // Use new user-based endpoint - users only see their own documents
      const data = await apiGet<{ documents: Document[] }>(`/api/users/me/documents`)
      setDocuments(data.documents || [])
      setError(null)
    } catch (err) {
      logger.error('Error loading documents:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      if (showLoading) {
        setLoading(false)
      }
    }
  }, [])

  const handleDocumentsChange = useCallback(async () => {
    await loadDocuments()
    setStorageRefreshTrigger(prev => prev + 1)  // Refresh storage indicator
  }, [loadDocuments])

  // Now use the functions in useEffect hooks
  useEffect(() => {
    loadDocuments()

    // Intentionally run only on mount - including function dependencies would cause infinite re-fetch loops
  }, [])

  // Auto-refresh when there are unprocessed documents
  useEffect(() => {
    const hasUnprocessedDocs = documents.some(doc => !doc.processed)

    if (hasUnprocessedDocs) {
      // Poll every 2 seconds to check for processing completion
      // Use showLoading=false to avoid UI flashing during background polling
      const intervalId = setInterval(() => {
        loadDocuments(false)
      }, 2000)

      return () => clearInterval(intervalId)
    }
  }, [documents, loadDocuments])

  function formatDate(isoString: string) {
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  function formatFileSize(bytes?: number): string {
    if (!bytes) return 'Unknown'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }

  // Document action handlers
  function handleDocumentInfo(doc: Document) {
    setSelectedDoc(doc)
    setShowInfoModal(true)
  }

  function handleDeleteClick(doc: Document) {
    setDocToDelete(doc)
    setShowDeleteModal(true)
  }

  async function handleDeleteConfirm() {
    if (!docToDelete) return

    setShowDeleteModal(false)
    setDeletingDocId(docToDelete.id)

    try {
      await apiDelete(`/api/documents/${docToDelete.id}`)
      setGeneralSuccess(`Deleted ${docToDelete.filename}`)
      await loadDocuments()
      setStorageRefreshTrigger(prev => prev + 1)  // Refresh storage indicator
      setTimeout(() => setGeneralSuccess(null), 3000)
    } catch (err) {
      setGeneralError(err instanceof Error ? err.message : 'Failed to delete document')
      setTimeout(() => setGeneralError(null), 3000)
    } finally {
      setDeletingDocId(null)
      setDocToDelete(null)
    }
  }

  return (
    <div className="min-h-screen bg-page">
      <PageHeader />

      {/* Storage Indicator */}
      <div className="max-w-7xl mx-auto px-6 pt-3">
        <StorageIndicator
          apiBaseUrl={API_BASE_URL}
          refreshTrigger={storageRefreshTrigger}
          onStorageUpdate={(data) => {
            // Optional: Can add logic here if needed when storage updates
          }}
        />
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 pt-3 pb-8">
        {/* Upload Section */}
        <div className={`card mb-3 ${uploadExpanded ? 'p-6' : 'p-2'}`}>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1">
              <button
                onClick={() => setUploadExpanded(!uploadExpanded)}
                className="text-secondary hover:text-primary transition-colors"
              >
                {uploadExpanded ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
              <h3 className="heading-3">Upload</h3>
            </div>
          </div>

          {uploadExpanded && (
            <div className="mt-4">
              {profile?.client_id ? (
                <DocumentUpload
                  clientId={profile.client_id}
                  apiBaseUrl={API_BASE_URL}
                  onUploadComplete={handleDocumentsChange}
                />
              ) : (
                <p className="text-secondary">Loading...</p>
              )}
            </div>
          )}
        </div>

        {/* Documents List */}
        <div className={`card mb-3 ${documentsExpanded ? 'p-6' : 'p-2'}`}>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1">
              <button
                onClick={() => setDocumentsExpanded(!documentsExpanded)}
                className="text-secondary hover:text-primary transition-colors"
              >
                {documentsExpanded ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
              <h2 className="heading-3">Documents</h2>
            </div>
          </div>

          {documentsExpanded && (
            <div className="mt-4">

            {/* General Document Notifications */}
            {generalSuccess && (
              <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-3">
                <div className="flex items-center gap-2">
                    <span className="text-sm text-green-800">{generalSuccess}</span>
                </div>
              </div>
            )}

            {generalError && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <span className="text-red-600 font-bold">Error:</span>
                  <span className="text-sm text-red-800">{generalError}</span>
                </div>
              </div>
            )}

            {loading ? (
              <div className="text-center py-8 text-muted">
                <LoadingSpinner size="md" />
                <p className="mt-2">Loading documents...</p>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg text-sm">
                Error: {error}
              </div>
            ) : documents.filter(doc => !doc.is_core_document).length === 0 ? (
              <div className="text-center py-8 text-muted">
                <p>No documents uploaded yet</p>
                <p className="text-sm mt-2">Upload your first document to get started!</p>
              </div>
            ) : (
              <div className="space-y-3">
                {documents.filter(doc => !doc.is_core_document).map((doc) => (
                  <div
                    key={doc.id}
                    className={`border rounded-lg p-2 transition-colors ${
                      doc.is_core_document
                        ? 'border-gray-200 dark:border-green-700 bg-[#F1FEF4] dark:bg-green-900/20 hover:bg-[#E5F9E9] dark:hover:bg-green-900/30'
                        : 'border-default hover:bg-hover'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-2 mb-1">
                          <h3 className="font-medium text-primary break-words">{doc.filename}</h3>
                          {/* Core Document Badge */}
                          {doc.is_core_document && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300 flex-shrink-0" title="Core document - cannot be deleted">
                              Core
                            </span>
                          )}
                          {/* Status Badges */}
                          {!doc.processed && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 flex-shrink-0" title="Document is being processed">
                              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              Processing
                            </span>
                          )}
                          {doc.processed && doc.processing_status === 'failed' && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 flex-shrink-0" title={`Processing failed: ${doc.processing_error || 'Unknown error'}`}>
                              Failed
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {/* Action Buttons */}
                        <div className="flex items-center gap-1">
                          {/* Info Button */}
                          <button
                            onClick={() => handleDocumentInfo(doc)}
                            className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                            title="Document info"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </button>

                          {/* Delete Button - hidden for core documents */}
                          {!doc.is_core_document && (
                            <button
                              onClick={() => handleDeleteClick(doc)}
                              disabled={deletingDocId === doc.id}
                              className="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              title="Delete document"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            </div>
          )}
        </div>

        {/* Core Documents List */}
        <div className={`card ${coreDocumentsExpanded ? 'p-6' : 'p-2'}`}>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1">
              <button
                onClick={() => setCoreDocumentsExpanded(!coreDocumentsExpanded)}
                className="text-secondary hover:text-primary transition-colors"
              >
                {coreDocumentsExpanded ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
              <h2 className="heading-3 text-teal-600">Core Documents</h2>
            </div>
          </div>

          {coreDocumentsExpanded && (
            <div className="mt-4">
            {loading ? (
              <div className="text-center py-8 text-muted">
                <LoadingSpinner size="md" />
                <p className="mt-2">Loading documents...</p>
              </div>
            ) : documents.filter(doc => doc.is_core_document).length === 0 ? (
              <div className="text-center py-8 text-muted">
                <p>No core documents</p>
              </div>
            ) : (
              <div className="space-y-3">
                {documents.filter(doc => doc.is_core_document).map((doc) => (
                  <div
                    key={doc.id}
                    className="border border-default bg-card hover:bg-hover rounded-lg py-1.5 px-3 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-primary break-words text-sm">{doc.filename}</h3>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {/* Info Button */}
                        <button
                          onClick={() => handleDocumentInfo(doc)}
                          className="p-1 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="Document info"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            </div>
          )}
        </div>

      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        open={showDeleteModal}
        title="Delete Document"
        message={`Are you sure you want to delete "${docToDelete?.filename}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmVariant="danger"
        onConfirm={handleDeleteConfirm}
        onCancel={() => {
          setShowDeleteModal(false)
          setDocToDelete(null)
        }}
      />

      {/* Document Info Modal */}
      {showInfoModal && selectedDoc && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowInfoModal(false)}>
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="heading-3">Document Information</h3>
              <button
                onClick={() => setShowInfoModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-secondary">Filename</label>
                <p className="text-sm text-primary mt-1">{selectedDoc.filename}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-secondary">Document ID</label>
                <p className="text-xs text-muted font-mono mt-1">{selectedDoc.id}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-secondary">Source</label>
                <p className="text-sm text-primary mt-1">
                  {selectedDoc.source_platform === 'obsidian' ? 'Obsidian' : 'Direct Upload'}
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-secondary">Uploaded</label>
                <p className="text-sm text-primary mt-1">{formatDate(selectedDoc.uploaded_at)}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-secondary">File Size</label>
                <p className="text-sm text-primary mt-1">{formatFileSize(selectedDoc.file_size)}</p>
              </div>

              {selectedDoc.external_url && (
                <div>
                  <label className="text-sm font-medium text-secondary">External Link</label>
                  <a
                    href={selectedDoc.external_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline mt-1 inline-block"
                  >
                    View source →
                  </a>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setShowInfoModal(false)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function DocumentsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-page flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    }>
      <DocumentsContent />
    </Suspense>
  )
}
