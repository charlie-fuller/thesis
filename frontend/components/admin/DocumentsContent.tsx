'use client'

import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { useAuth } from '@/contexts/AuthContext'
import { apiGet, apiDelete } from '@/lib/api'
import ConfirmModal from '@/components/ConfirmModal'
import { logger } from '@/lib/logger'

interface Document {
  id: string
  filename: string
  file_type: string | null
  file_size: number
  client_id: string
  uploaded_at: string
  uploaded_by?: string
  processing_status: string
  chunk_count: number
  access_count: number
  clients?: { name: string }
  users?: { email: string }
}

interface DocumentDetails extends Document {
  client_name?: string
  uploaded_by_email?: string
  conversations?: Array<{ id: string; title: string }>
}

export default function DocumentsContent() {
  const { user, session, loading: authLoading } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState<string>('')
  const [selectedStatus, setSelectedStatus] = useState<string>('')
  const [dateRange, setDateRange] = useState<string>('all')
  const [total, setTotal] = useState(0)
  const [limit, setLimit] = useState(20)
  const [offset, setOffset] = useState(0)
  const [sortBy, setSortBy] = useState<string>('uploaded_at')
  const [sortOrder, setSortOrder] = useState<string>('desc')
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set())
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [documentDetails, setDocumentDetails] = useState<DocumentDetails | null>(null)
  const [confirmModal, setConfirmModal] = useState<{
    open: boolean
    title: string
    message: string
    onConfirm: () => void
  }>({
    open: false,
    title: '',
    message: '',
    onConfirm: () => {}
  })

  useEffect(() => {
    if (authLoading || !user || !session) return
    const timer = setTimeout(() => {
      setOffset(0)
      loadDocuments()
    }, 300)
    return () => clearTimeout(timer)
  }, [authLoading, searchQuery, selectedType, selectedStatus, dateRange, sortBy, sortOrder, user, session])

  useEffect(() => {
    if (!authLoading && user && session) {
      loadDocuments()
    }
  }, [authLoading, offset, limit, user, session])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams()
      if (searchQuery) params.set('search', searchQuery)
      if (selectedType) params.set('file_type', selectedType)
      if (selectedStatus) params.set('status', selectedStatus)
      if (sortBy) params.set('sort_by', sortBy)
      if (sortOrder) params.set('sort_order', sortOrder)
      params.set('limit', limit.toString())
      params.set('offset', offset.toString())

      if (dateRange !== 'all') {
        const now = new Date()
        const dateFrom = new Date()
        switch (dateRange) {
          case 'week':
            dateFrom.setDate(now.getDate() - 7)
            break
          case 'month':
            dateFrom.setMonth(now.getMonth() - 1)
            break
          case 'quarter':
            dateFrom.setMonth(now.getMonth() - 3)
            break
        }
        params.set('date_from', dateFrom.toISOString())
      }

      const data = await apiGet<{ documents: Document[]; total: number }>(`/api/documents?${params.toString()}`)
      setDocuments(data.documents || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectAll = () => {
    if (selectedDocuments.size === documents.length) {
      setSelectedDocuments(new Set())
    } else {
      setSelectedDocuments(new Set(documents.map(d => d.id)))
    }
  }

  const handleSelectDocument = (docId: string) => {
    const newSelected = new Set(selectedDocuments)
    if (newSelected.has(docId)) {
      newSelected.delete(docId)
    } else {
      newSelected.add(docId)
    }
    setSelectedDocuments(newSelected)
  }

  const handleDelete = (documentId: string) => {
    setConfirmModal({
      open: true,
      title: 'Delete Document',
      message: 'Are you sure you want to delete this document? This action cannot be undone.',
      onConfirm: async () => {
        await deleteDocument(documentId)
      }
    })
  }

  const deleteDocument = async (documentId: string) => {
    try {
      await apiDelete(`/api/documents/${documentId}`)
      setDocuments(prev => prev.filter(d => d.id !== documentId))
      setTotal(prev => prev - 1)
    } catch (err) {
      logger.error('Delete error:', err)
      toast.error('Failed to delete document')
      loadDocuments()
    }
  }

  const handleBulkDelete = () => {
    if (selectedDocuments.size === 0) return
    setConfirmModal({
      open: true,
      title: 'Delete Documents',
      message: `Are you sure you want to delete ${selectedDocuments.size} document(s)? This action cannot be undone.`,
      onConfirm: async () => {
        try {
          const documentIds = Array.from(selectedDocuments)
          const data = await apiDelete<{ deleted: number }>('/api/documents/bulk', { document_ids: documentIds })
          toast.success(`Successfully deleted ${data.deleted} document(s)`)
          setSelectedDocuments(new Set())
          loadDocuments()
        } catch (err) {
          logger.error('Bulk delete error:', err)
          toast.error('Failed to delete documents')
        }
      }
    })
  }

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
  }

  const handleViewDetails = async (document: Document) => {
    setSelectedDocument(document)
    setShowDetailModal(true)
    setDetailLoading(true)
    try {
      const data = await apiGet<{ document: DocumentDetails }>(`/api/documents/${document.id}/details`)
      setDocumentDetails(data.document)
    } catch (err) {
      logger.error('Error loading details:', err)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleDownload = async (documentId: string) => {
    try {
      const data = await apiGet<{ download_url: string }>(`/api/documents/${documentId}/download`)
      window.open(data.download_url, '_blank')
    } catch (err) {
      logger.error('Download error:', err)
      toast.error('Failed to download document')
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getFileTypeDisplay = (mimeType: string | null): string => {
    if (!mimeType) return 'Unknown'
    if (mimeType.includes('pdf')) return 'PDF'
    if (mimeType.includes('word') || mimeType.includes('document')) return 'DOCX'
    if (mimeType.includes('csv')) return 'CSV'
    if (mimeType.includes('text')) return 'TXT'
    return mimeType.split('/')[1]?.toUpperCase() || 'Unknown'
  }

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
      completed: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-800 dark:text-green-300', label: 'Processed' },
      processing: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-800 dark:text-blue-300', label: 'Processing' },
      pending: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-800 dark:text-yellow-300', label: 'Pending' },
      failed: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-300', label: 'Failed' },
    }
    const config = statusConfig[status] || statusConfig.pending
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    )
  }

  const currentPage = Math.floor(offset / limit) + 1
  const totalPages = Math.ceil(total / limit)

  if (loading && documents.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto mb-4"></div>
          <p className="text-muted">Loading documents...</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Filters */}
      <div className="card p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <input
            type="text"
            placeholder="Search by filename..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm"
          />
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm"
          >
            <option value="">All Types</option>
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
            <option value="csv">CSV</option>
            <option value="txt">TXT</option>
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm"
          >
            <option value="">All Statuses</option>
            <option value="completed">Processed</option>
            <option value="processing">Processing</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm"
          >
            <option value="all">All Time</option>
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="quarter">Last 90 Days</option>
          </select>
          <select
            value={limit}
            onChange={(e) => {
              setLimit(Number(e.target.value))
              setOffset(0)
            }}
            className="px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm"
          >
            <option value="20">20 per page</option>
            <option value="50">50 per page</option>
            <option value="100">100 per page</option>
          </select>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedDocuments.size > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <p className="font-medium text-blue-800 dark:text-blue-200">
              {selectedDocuments.size} document(s) selected
            </p>
            <button
              onClick={handleBulkDelete}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Delete Selected
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
          <p className="text-red-800 dark:text-red-200">Error: {error}</p>
        </div>
      )}

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-page border-b border-default">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.size === documents.length && documents.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-default"
                  />
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase text-muted cursor-pointer hover:bg-hover"
                  onClick={() => handleSort('filename')}
                >
                  Filename {sortBy === 'filename' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-muted">Type</th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase text-muted cursor-pointer hover:bg-hover"
                  onClick={() => handleSort('file_size')}
                >
                  Size {sortBy === 'file_size' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-muted">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-muted">Chunks</th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium uppercase text-muted cursor-pointer hover:bg-hover"
                  onClick={() => handleSort('uploaded_at')}
                >
                  Uploaded {sortBy === 'uploaded_at' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase text-muted">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-default">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-hover transition-colors">
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedDocuments.has(doc.id)}
                      onChange={() => handleSelectDocument(doc.id)}
                      className="rounded border-default"
                    />
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => handleViewDetails(doc)}
                      className="text-brand hover:underline font-medium text-sm truncate max-w-xs block"
                      title={doc.filename}
                    >
                      {doc.filename}
                    </button>
                  </td>
                  <td className="px-6 py-4 text-sm text-secondary">{getFileTypeDisplay(doc.file_type)}</td>
                  <td className="px-6 py-4 text-sm text-secondary">{formatFileSize(doc.file_size)}</td>
                  <td className="px-6 py-4">{getStatusBadge(doc.processing_status)}</td>
                  <td className="px-6 py-4 text-sm text-secondary">{doc.chunk_count || 0}</td>
                  <td className="px-6 py-4 text-sm text-secondary">{formatDate(doc.uploaded_at)}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleDownload(doc.id)}
                        className="p-1 text-muted hover:text-primary transition-colors"
                        title="Download"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-1 text-muted hover:text-red-600 transition-colors"
                        title="Delete"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {documents.length === 0 && !loading && (
          <div className="text-center py-12">
            <p className="text-primary font-medium">No documents found</p>
            <p className="text-muted text-sm mt-1">Try adjusting your filters</p>
          </div>
        )}

        {/* Pagination */}
        {documents.length > 0 && (
          <div className="bg-page px-6 py-4 flex items-center justify-between border-t border-default">
            <div className="text-sm text-muted">
              Showing {offset + 1}-{Math.min(offset + limit, total)} of {total} documents
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-muted">Page {currentPage} of {totalPages}</span>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={offset + limit >= total}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showDetailModal && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <div className="bg-card rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-card border-b border-default px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-primary">Document Details</h2>
              <button onClick={() => setShowDetailModal(false)} className="text-muted hover:text-primary text-2xl">
                &times;
              </button>
            </div>
            <div className="px-6 py-4">
              {detailLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand mx-auto"></div>
                </div>
              ) : documentDetails ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-medium uppercase text-muted">Filename</label>
                    <p className="text-sm text-primary mt-1">{documentDetails.filename}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-medium uppercase text-muted">Type</label>
                      <p className="text-sm text-primary mt-1">{getFileTypeDisplay(documentDetails.file_type)}</p>
                    </div>
                    <div>
                      <label className="text-xs font-medium uppercase text-muted">Size</label>
                      <p className="text-sm text-primary mt-1">{formatFileSize(documentDetails.file_size)}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-medium uppercase text-muted">Status</label>
                      <div className="mt-1">{getStatusBadge(documentDetails.processing_status)}</div>
                    </div>
                    <div>
                      <label className="text-xs font-medium uppercase text-muted">Chunks</label>
                      <p className="text-sm text-primary mt-1">{documentDetails.chunk_count || 0}</p>
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-medium uppercase text-muted">Uploaded</label>
                    <p className="text-sm text-primary mt-1">{formatDate(documentDetails.uploaded_at)}</p>
                  </div>
                </div>
              ) : null}
            </div>
            <div className="sticky bottom-0 bg-page px-6 py-4 flex items-center justify-end gap-2 border-t border-default">
              <button onClick={() => handleDownload(selectedDocument.id)} className="btn-primary">Download</button>
              <button
                onClick={() => {
                  setShowDetailModal(false)
                  handleDelete(selectedDocument.id)
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Delete
              </button>
              <button onClick={() => setShowDetailModal(false)} className="btn-secondary">Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Modal */}
      <ConfirmModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        onConfirm={confirmModal.onConfirm}
        onCancel={() => setConfirmModal({ ...confirmModal, open: false })}
      />
    </div>
  )
}
