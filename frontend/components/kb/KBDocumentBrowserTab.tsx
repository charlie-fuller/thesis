'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Search, FileText, Tag, Plus, Minus, Loader2, Check, X, Eye, ArrowUpDown, Filter } from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'
import TagSelector from '@/components/TagSelector'

type SortOption = 'recent' | 'oldest' | 'name_asc' | 'name_desc'
type SourceOption = '' | 'obsidian' | 'google_drive' | 'notion' | 'upload'
type RightPanelView = 'preview' | 'tags'

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'recent', label: 'Most Recent' },
  { value: 'oldest', label: 'Oldest First' },
  { value: 'name_asc', label: 'Name (A-Z)' },
  { value: 'name_desc', label: 'Name (Z-A)' },
]

const SOURCE_OPTIONS: { value: SourceOption; label: string }[] = [
  { value: '', label: 'All Sources' },
  { value: 'obsidian', label: 'Vault' },
  { value: 'google_drive', label: 'Google Drive' },
  { value: 'notion', label: 'Notion' },
  { value: 'upload', label: 'Uploaded' },
]

interface KBDocument {
  id: string
  filename: string
  title: string | null
  obsidian_file_path: string | null
  uploaded_at: string
  tags: string[]
}

interface TagItem {
  tag: string
  count: number
}

interface KBDocumentBrowserTabProps {
  onDocumentsChange?: () => void
}

export default function KBDocumentBrowserTab({ onDocumentsChange }: KBDocumentBrowserTabProps) {
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTagsFilter, setSelectedTagsFilter] = useState<Set<string>>(new Set())
  const [sortBy, setSortBy] = useState<SortOption>('recent')
  const [sourceFilter, setSourceFilter] = useState<SourceOption>('')

  // Document state
  const [documents, setDocuments] = useState<KBDocument[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set())
  const [hasMore, setHasMore] = useState(false)
  const [offset, setOffset] = useState(0)

  // Preview state
  const [previewDoc, setPreviewDoc] = useState<string | null>(null)
  const [previewContent, setPreviewContent] = useState<string>('')
  const [loadingPreview, setLoadingPreview] = useState(false)

  // Right panel view state
  const [rightPanelView, setRightPanelView] = useState<RightPanelView>('tags')

  // Tag management state
  const [allTags, setAllTags] = useState<TagItem[]>([])
  const [loadingTags, setLoadingTags] = useState(false)
  const [newTag, setNewTag] = useState('')
  const [tagsToAdd, setTagsToAdd] = useState<Set<string>>(new Set())
  const [tagsToRemove, setTagsToRemove] = useState<Set<string>>(new Set())

  // Operation state
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)

  const LIMIT = 20

  // Track latest request to prevent race conditions
  const latestRequestRef = useRef(0)

  // Fetch documents when search, tags, sort, or source change
  const fetchDocuments = useCallback(async (
    resetOffset = true,
    query?: string,
    tags?: Set<string>,
    sort?: SortOption,
    source?: SourceOption
  ) => {
    const requestId = ++latestRequestRef.current
    setLoading(true)
    try {
      const params = new URLSearchParams({
        limit: LIMIT.toString(),
        offset: resetOffset ? '0' : offset.toString()
      })
      // Use passed values or fall back to state
      const q = query ?? searchQuery
      const t = tags ?? selectedTagsFilter
      const s = sort ?? sortBy
      const src = source ?? sourceFilter

      if (q) {
        params.append('q', q)
      }
      if (t.size > 0) {
        params.append('tags', Array.from(t).join(','))
      }
      if (s) {
        params.append('sort', s)
      }
      if (src) {
        params.append('source', src)
      }

      const result = await apiGet<{
        success: boolean
        documents: KBDocument[]
        hasMore: boolean
      }>(`/api/documents/search?${params}`)

      // Only update state if this is still the latest request
      if (requestId !== latestRequestRef.current) {
        return
      }

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
      if (requestId === latestRequestRef.current) {
        setLoading(false)
      }
    }
  }, [offset, searchQuery, selectedTagsFilter, sortBy, sourceFilter])

  // Fetch all tags
  const fetchTags = useCallback(async () => {
    setLoadingTags(true)
    try {
      const result = await apiGet<{
        success: boolean
        tags: TagItem[]
        hasMore: boolean
      }>('/api/documents/tags?limit=500')
      setAllTags(result.tags || [])
    } catch (err) {
      console.error('Failed to fetch tags:', err)
    } finally {
      setLoadingTags(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    fetchDocuments(true, searchQuery, selectedTagsFilter, sortBy, sourceFilter)
    fetchTags()
  }, [])

  // Debounced search/filter changes
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDocuments(true, searchQuery, selectedTagsFilter, sortBy, sourceFilter)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery, selectedTagsFilter, sortBy, sourceFilter])

  // Load document preview
  const loadPreview = async (docId: string) => {
    setPreviewDoc(docId)
    setRightPanelView('preview')
    setLoadingPreview(true)
    try {
      const result = await apiGet<{
        success: boolean
        content: string
      }>(`/api/documents/${docId}/content`)
      setPreviewContent(result.content || 'No content available')
    } catch {
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

  // Add new tag to list
  const addNewTag = () => {
    if (!newTag.trim()) return
    const tag = newTag.trim()
    if (!allTags.find(t => t.tag === tag)) {
      setAllTags(prev => [...prev, { tag, count: 0 }].sort((a, b) => a.tag.localeCompare(b.tag)))
    }
    setTagsToAdd(prev => new Set(prev).add(tag))
    setNewTag('')
  }

  // Toggle tag to add
  const toggleTagToAdd = (tag: string) => {
    const newTags = new Set(tagsToAdd)
    if (newTags.has(tag)) {
      newTags.delete(tag)
    } else {
      newTags.add(tag)
      // Remove from tagsToRemove if present
      const newRemove = new Set(tagsToRemove)
      newRemove.delete(tag)
      setTagsToRemove(newRemove)
    }
    setTagsToAdd(newTags)
  }

  // Toggle tag to remove
  const toggleTagToRemove = (tag: string) => {
    const newTags = new Set(tagsToRemove)
    if (newTags.has(tag)) {
      newTags.delete(tag)
    } else {
      newTags.add(tag)
      // Remove from tagsToAdd if present
      const newAdd = new Set(tagsToAdd)
      newAdd.delete(tag)
      setTagsToAdd(newAdd)
    }
    setTagsToRemove(newTags)
  }

  // Apply tag operations
  const applyTags = async () => {
    if (selectedDocs.size === 0) return
    if (tagsToAdd.size === 0 && tagsToRemove.size === 0) return

    setApplying(true)
    setResult(null)

    try {
      const results: string[] = []
      let hasFailures = false

      // Add tags
      if (tagsToAdd.size > 0) {
        const addResult = await apiPost<{
          success: boolean
          results: { success: number; failed: number; errors?: Array<{ document_id: string; error: string }> }
        }>('/api/documents/bulk-tags', {
          document_ids: Array.from(selectedDocs),
          tags: Array.from(tagsToAdd),
          operation: 'add'
        })
        if (addResult.results.failed > 0) {
          hasFailures = true
          results.push(`Added tags to ${addResult.results.success}/${selectedDocs.size} docs (${addResult.results.failed} failed)`)
        } else {
          results.push(`Added ${tagsToAdd.size} tag(s) to ${addResult.results.success} document(s)`)
        }
      }

      // Remove tags
      if (tagsToRemove.size > 0) {
        const removeResult = await apiPost<{
          success: boolean
          results: { success: number; failed: number; errors?: Array<{ document_id: string; error: string }> }
        }>('/api/documents/bulk-tags', {
          document_ids: Array.from(selectedDocs),
          tags: Array.from(tagsToRemove),
          operation: 'remove'
        })
        if (removeResult.results.failed > 0) {
          hasFailures = true
          results.push(`Removed tags from ${removeResult.results.success}/${selectedDocs.size} docs (${removeResult.results.failed} failed)`)
        } else {
          results.push(`Removed ${tagsToRemove.size} tag(s) from ${removeResult.results.success} document(s)`)
        }
      }

      setResult({ success: !hasFailures, message: results.join('. ') })

      // Reset and refresh
      setTagsToAdd(new Set())
      setTagsToRemove(new Set())
      fetchDocuments(true, searchQuery, selectedTagsFilter, sortBy, sourceFilter)
      fetchTags()
      onDocumentsChange?.()
    } catch (err) {
      console.error('Failed to apply tags:', err)
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setResult({ success: false, message: `Failed to apply tags: ${errorMessage}` })
    } finally {
      setApplying(false)
    }
  }

  // Reset filters
  const resetFilters = () => {
    setSortBy('recent')
    setSourceFilter('')
    setSelectedTagsFilter(new Set())
    setSearchQuery('')
  }

  // Get tags from selected documents
  const selectedDocsTags = new Set<string>()
  documents
    .filter(d => selectedDocs.has(d.id))
    .forEach(d => d.tags?.forEach(t => selectedDocsTags.add(t)))

  const hasActiveFilters = sortBy !== 'recent' || sourceFilter !== '' || selectedTagsFilter.size > 0 || searchQuery !== ''

  return (
    <div className="flex flex-col h-[calc(100vh-280px)] bg-white dark:bg-slate-800 rounded-lg border border-default">
      {/* Search and Filter */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 space-y-3">
        {/* First Row: Search and Tags */}
        <div className="flex items-start gap-4">
          {/* Text Search - 60% width */}
          <div className="relative w-3/5">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by filename or title..."
              className="w-full pl-10 pr-4 py-2 border border-default rounded-lg bg-card text-primary placeholder:text-muted focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Tag Filter - 40% width */}
          <div className="w-2/5">
            <TagSelector
              selectedTags={selectedTagsFilter}
              onTagsChange={setSelectedTagsFilter}
              placeholder="Filter by tags..."
              showInitiatives={false}
              size="base"
            />
          </div>
        </div>

        {/* Second Row: Sort and Source Filter */}
        <div className="flex items-center gap-4">
          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="px-3 py-1.5 text-sm border border-default rounded-lg bg-card text-primary focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {SORT_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Source Filter Dropdown */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value as SourceOption)}
              className="px-3 py-1.5 text-sm border border-default rounded-lg bg-card text-primary focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {SOURCE_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Active filters indicator */}
          {hasActiveFilters && (
            <button
              onClick={resetFilters}
              className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Reset filters
            </button>
          )}
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
                  onClick={() => fetchDocuments(false, searchQuery, selectedTagsFilter, sortBy, sourceFilter)}
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

        {/* Right Panel - 60% width */}
        <div className="w-3/5 flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-900/50">
          {/* Panel Toggle */}
          <div className="flex border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
            <button
              onClick={() => setRightPanelView('tags')}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                rightPanelView === 'tags'
                  ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-500'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Tag className="w-4 h-4 inline-block mr-1.5 -mt-0.5" />
              Manage Tags
            </button>
            <button
              onClick={() => setRightPanelView('preview')}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                rightPanelView === 'preview'
                  ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-500'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Eye className="w-4 h-4 inline-block mr-1.5 -mt-0.5" />
              Preview
            </button>
          </div>

          {/* Panel Content */}
          <div className="flex-1 overflow-y-auto">
            {rightPanelView === 'preview' ? (
              // Preview Panel
              <div className="p-4">
                {previewDoc ? (
                  <>
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
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                    <Eye className="w-8 h-8 mb-2" />
                    <p className="text-sm text-center">Click the eye icon to preview a document</p>
                  </div>
                )}
              </div>
            ) : (
              // Tag Management Panel
              <div className="p-4 space-y-4">
                {/* Create New Tag */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Create New Tag
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && addNewTag()}
                      placeholder="New tag name..."
                      className="flex-1 px-3 py-2 text-sm border border-default rounded-lg bg-card text-primary placeholder:text-muted focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <button
                      onClick={addNewTag}
                      disabled={!newTag.trim()}
                      className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Tags to Add */}
                {tagsToAdd.size > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-green-600 dark:text-green-400 uppercase mb-2">
                      Will Add ({tagsToAdd.size})
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {Array.from(tagsToAdd).map(tag => (
                        <button
                          key={`add-${tag}`}
                          onClick={() => toggleTagToAdd(tag)}
                          className="inline-flex items-center gap-1 px-2 py-1 text-sm bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-md hover:bg-green-200"
                        >
                          <Plus className="w-3 h-3" />
                          {tag}
                          <X className="w-3 h-3 ml-1" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tags to Remove */}
                {tagsToRemove.size > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-red-600 dark:text-red-400 uppercase mb-2">
                      Will Remove ({tagsToRemove.size})
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {Array.from(tagsToRemove).map(tag => (
                        <button
                          key={`remove-${tag}`}
                          onClick={() => toggleTagToRemove(tag)}
                          className="inline-flex items-center gap-1 px-2 py-1 text-sm bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-md hover:bg-red-200"
                        >
                          <Minus className="w-3 h-3" />
                          {tag}
                          <X className="w-3 h-3 ml-1" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* All Tags */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-2">
                    All Tags ({allTags.length})
                  </h4>
                  {loadingTags ? (
                    <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
                  ) : allTags.length === 0 ? (
                    <p className="text-sm text-slate-400">No tags yet</p>
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {allTags.map(item => {
                        const isAdding = tagsToAdd.has(item.tag)
                        const isRemoving = tagsToRemove.has(item.tag)
                        const isOnSelected = selectedDocsTags.has(item.tag)

                        return (
                          <div key={item.tag} className="inline-flex">
                            <button
                              onClick={() => toggleTagToAdd(item.tag)}
                              className={`inline-flex items-center gap-1 px-2 py-1 text-sm rounded-l-md border transition-colors ${
                                isAdding
                                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300'
                                  : isRemoving
                                  ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-300'
                                  : isOnSelected
                                  ? 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 border-indigo-200'
                                  : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-600'
                              }`}
                              title="Click to add this tag"
                            >
                              <Tag className="w-3 h-3" />
                              {item.tag}
                              <span className="text-xs text-slate-400">({item.count})</span>
                            </button>
                            <button
                              onClick={() => toggleTagToRemove(item.tag)}
                              className={`px-1.5 rounded-r-md border-t border-r border-b transition-colors ${
                                isRemoving
                                  ? 'bg-red-200 dark:bg-red-800 text-red-700 dark:text-red-300 border-red-300'
                                  : 'bg-slate-100 dark:bg-slate-700 text-slate-400 hover:bg-red-50 hover:text-red-600 border-slate-200 dark:border-slate-600'
                              }`}
                              title="Click to remove this tag"
                            >
                              <Minus className="w-3 h-3" />
                            </button>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between bg-white dark:bg-slate-800">
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
          {result && (
            <div className={`px-3 py-1.5 rounded-md text-sm ${
              result.success
                ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
            }`}>
              {result.message}
            </div>
          )}
          <button
            onClick={applyTags}
            disabled={selectedDocs.size === 0 || (tagsToAdd.size === 0 && tagsToRemove.size === 0) || applying}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {applying ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Applying...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Apply Tag Changes
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
