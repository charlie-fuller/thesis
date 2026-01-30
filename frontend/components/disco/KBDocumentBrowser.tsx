'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, Search, FileText, Check, Loader2, Eye, Tag, Link } from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'
import TagSelector from '@/components/TagSelector'

interface KBDocument {
  id: string
  filename: string
  title: string | null
  obsidian_file_path: string | null
  uploaded_at: string
  tags: string[]
}

interface KBDocumentBrowserProps {
  initiativeId: string
  initiativeName: string
  isOpen: boolean
  onClose: () => void
  onLinked: (documentIds: string[]) => void
}

export default function KBDocumentBrowser({
  initiativeId,
  initiativeName,
  isOpen,
  onClose,
  onLinked
}: KBDocumentBrowserProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTagsFilter, setSelectedTagsFilter] = useState<Set<string>>(new Set())
  const [documents, setDocuments] = useState<KBDocument[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set())
  const [previewDoc, setPreviewDoc] = useState<string | null>(null)
  const [previewContent, setPreviewContent] = useState<string>('')
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [linking, setLinking] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [offset, setOffset] = useState(0)

  const LIMIT = 20

  // Fetch documents when search or tags change
  const fetchDocuments = useCallback(async (resetOffset = true, query?: string, tags?: Set<string>) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        limit: LIMIT.toString(),
        offset: resetOffset ? '0' : offset.toString()
      })
      // Use passed values or fall back to state
      const q = query ?? searchQuery
      const t = tags ?? selectedTagsFilter
      if (q) {
        params.append('q', q)
      }
      if (t.size > 0) {
        params.append('tags', Array.from(t).join(','))
      }

      const result = await apiGet<{
        success: boolean
        documents: KBDocument[]
        hasMore: boolean
      }>(`/api/documents/search?${params}`)

      if (resetOffset) {
        setDocuments(result.documents || [])
        setOffset(LIMIT)
      } else {
        setDocuments(prev => [...prev, ...(result.documents || [])])
        setOffset(prev => prev + LIMIT)
      }
      setHasMore(result.hasMore)
    } catch (err) {
      console.error('Failed to fetch documents:', err)
    } finally {
      setLoading(false)
    }
  }, [offset])

  // Initial load and search/filter changes
  useEffect(() => {
    if (isOpen) {
      fetchDocuments(true, searchQuery, selectedTagsFilter)
    }
  }, [isOpen, searchQuery, selectedTagsFilter])

  // Load document preview
  const loadPreview = async (docId: string) => {
    setPreviewDoc(docId)
    setLoadingPreview(true)
    try {
      const result = await apiGet<{
        success: boolean
        content: string
      }>(`/api/documents/${docId}/content`)
      setPreviewContent(result.content || 'No content available')
    } catch (err) {
      setPreviewContent('Failed to load preview')
    } finally {
      setLoadingPreview(false)
    }
  }

  // Toggle document selection
  const toggleDoc = (docId: string) => {
    const newSelected = new Set(selectedDocs)
    if (newSelected.has(docId)) {
      newSelected.delete(docId)
    } else {
      newSelected.add(docId)
    }
    setSelectedDocs(newSelected)
  }

  // Select all visible documents
  const selectAll = () => {
    const newSelected = new Set(selectedDocs)
    documents.forEach(doc => newSelected.add(doc.id))
    setSelectedDocs(newSelected)
  }

  // Deselect all
  const deselectAll = () => {
    setSelectedDocs(new Set())
  }

  // Link selected documents to initiative
  const linkDocuments = async () => {
    if (selectedDocs.size === 0) return

    setLinking(true)
    try {
      const result = await apiPost<{
        success: boolean
        linked_count: number
        documents: Array<{ id: string; filename: string }>
        errors?: Array<{ document_id: string; error: string }>
      }>(`/api/disco/initiatives/${initiativeId}/documents/link`, {
        document_ids: Array.from(selectedDocs)
      })

      if (result.success) {
        onLinked(Array.from(selectedDocs))
        onClose()
      }
    } catch (err) {
      console.error('Failed to link documents:', err)
    } finally {
      setLinking(false)
    }
  }

  // Close and reset
  const handleClose = () => {
    setSelectedDocs(new Set())
    setPreviewDoc(null)
    setPreviewContent('')
    setSearchQuery('')
    setSelectedTagsFilter(new Set())
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-6xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              Link Documents from Knowledge Base
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Link existing KB documents to &quot;{initiativeName}&quot;
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Search and Filter */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-start gap-4">
            {/* Text Search - 50% width */}
            <div className="relative w-1/2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by filename or title..."
                className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Tag Filter - 60% width */}
            <div className="flex-1">
              <TagSelector
                selectedTags={selectedTagsFilter}
                onTagsChange={setSelectedTagsFilter}
                placeholder="Filter by tags..."
                showInitiatives={false}
                size="base"
              />
            </div>
          </div>
        </div>

        {/* Content - Split View */}
        <div className="flex-1 flex overflow-hidden">
          {/* Document List - 40% width */}
          <div className="w-2/5 overflow-y-auto border-r border-slate-200 dark:border-slate-700">
            {loading && documents.length === 0 ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
              </div>
            ) : documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-500 dark:text-slate-400">
                <FileText className="w-10 h-10 mb-3 text-slate-300 dark:text-slate-600" />
                <p>No documents found</p>
                <p className="text-sm">Try adjusting your search or filters</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-700">
                {documents.map(doc => (
                  <div
                    key={doc.id}
                    className={`flex items-start gap-3 px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${
                      selectedDocs.has(doc.id) ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''
                    } ${
                      previewDoc === doc.id ? 'border-r-4 border-r-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/20' : ''
                    }`}
                  >
                    <button
                      onClick={() => toggleDoc(doc.id)}
                      className={`mt-1 w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 ${
                        selectedDocs.has(doc.id)
                          ? 'bg-indigo-600 border-indigo-600'
                          : 'border-slate-300 dark:border-slate-600 hover:border-indigo-400'
                      }`}
                    >
                      {selectedDocs.has(doc.id) && <Check className="w-3 h-3 text-white" />}
                    </button>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                        <span className="font-medium text-slate-900 dark:text-white truncate">
                          {doc.title || doc.filename}
                        </span>
                      </div>
                      {doc.obsidian_file_path && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                          {doc.obsidian_file_path}
                        </p>
                      )}
                      {doc.tags && doc.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {doc.tags.slice(0, 3).map(tag => (
                            <span
                              key={tag}
                              className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded"
                            >
                              <Tag className="w-2.5 h-2.5" />
                              {tag}
                            </span>
                          ))}
                          {doc.tags.length > 3 && (
                            <span className="text-xs text-slate-400">+{doc.tags.length - 3}</span>
                          )}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => loadPreview(doc.id)}
                      className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors"
                      title="Preview"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                ))}

                {/* Load More */}
                {hasMore && (
                  <button
                    onClick={() => fetchDocuments(false, searchQuery, selectedTagsFilter)}
                    disabled={loading}
                    className="w-full py-3 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      'Load more'
                    )}
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Preview Panel - 60% width */}
          <div className="w-3/5 overflow-y-auto bg-slate-50 dark:bg-slate-900/50">
            {previewDoc ? (
              <div className="p-4">
                <h3 className="text-sm font-medium text-slate-900 dark:text-white mb-3">
                  Preview
                </h3>
                {loadingPreview ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
                  </div>
                ) : (
                  <div className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                    {previewContent.slice(0, 2000)}
                    {previewContent.length > 2000 && (
                      <span className="text-slate-400">... (truncated)</span>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 p-4">
                <Eye className="w-8 h-8 mb-2" />
                <p className="text-sm text-center">Click the eye icon to preview a document</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600 dark:text-slate-400">
              {selectedDocs.size} selected
            </span>
            <button
              onClick={selectAll}
              className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Select visible
            </button>
            <button
              onClick={deselectAll}
              className="text-sm text-slate-500 dark:text-slate-400 hover:underline"
            >
              Clear
            </button>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={linkDocuments}
              disabled={selectedDocs.size === 0 || linking}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {linking ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Linking...
                </>
              ) : (
                <>
                  <Link className="w-4 h-4" />
                  Link {selectedDocs.size} Document{selectedDocs.size !== 1 ? 's' : ''}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
