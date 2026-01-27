'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Search, FileText, Tag, Plus, Minus, Loader2, Check, X } from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'
import TagSelector from '@/components/TagSelector'

interface KBDocument {
  id: string
  filename: string
  title: string | null
  obsidian_file_path: string | null
  tags: string[]
}

interface TagItem {
  tag: string
  count: number
}

interface TagManagerTabProps {
  onDocumentsChange?: () => void
}

export default function TagManagerTab({ onDocumentsChange }: TagManagerTabProps) {
  // Document selection state
  const [searchQuery, setSearchQuery] = useState('')
  const [filterTags, setFilterTags] = useState<Set<string>>(new Set())
  const [documents, setDocuments] = useState<KBDocument[]>([])
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set())
  const [loadingDocs, setLoadingDocs] = useState(false)
  const [hasMoreDocs, setHasMoreDocs] = useState(false)
  const [docsOffset, setDocsOffset] = useState(0)

  // Tag management state
  const [allTags, setAllTags] = useState<TagItem[]>([])
  const [loadingTags, setLoadingTags] = useState(false)
  const [newTag, setNewTag] = useState('')
  const [tagsToAdd, setTagsToAdd] = useState<Set<string>>(new Set())
  const [tagsToRemove, setTagsToRemove] = useState<Set<string>>(new Set())

  // Operation state
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)

  const LIMIT = 50

  // Track latest request to prevent race conditions
  const latestRequestRef = useRef(0)

  // Fetch documents
  const fetchDocuments = useCallback(async (reset = true, query?: string, tags?: Set<string>) => {
    const requestId = ++latestRequestRef.current
    setLoadingDocs(true)
    try {
      const params = new URLSearchParams({
        limit: LIMIT.toString(),
        offset: reset ? '0' : docsOffset.toString()
      })
      const q = query ?? searchQuery
      const t = tags ?? filterTags
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

      // Only update state if this is still the latest request
      if (requestId !== latestRequestRef.current) {
        console.log('Ignoring stale response for request', requestId, '(latest is', latestRequestRef.current + ')')
        return
      }

      if (reset) {
        setDocuments(result.documents || [])
        setDocsOffset(LIMIT)
      } else {
        setDocuments(prev => [...prev, ...(result.documents || [])])
        setDocsOffset(prev => prev + LIMIT)
      }
      setHasMoreDocs(result.hasMore)
    } catch (err) {
      console.error('Failed to fetch documents:', err)
    } finally {
      // Only clear loading if this is still the latest request
      if (requestId === latestRequestRef.current) {
        setLoadingDocs(false)
      }
    }
  }, [docsOffset])

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

  // Fetch tags on mount
  useEffect(() => {
    fetchTags()
  }, [])

  // Search-based document loading (runs on mount and when search params change)
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDocuments(true, searchQuery, filterTags)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery, filterTags])

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

  // Select all visible
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
      fetchDocuments(true, searchQuery, filterTags)
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

  // Get tags from selected documents
  const selectedDocsTags = new Set<string>()
  documents
    .filter(d => selectedDocs.has(d.id))
    .forEach(d => d.tags?.forEach(t => selectedDocsTags.add(t)))

  return (
    <div className="flex h-full">
      {/* Left Panel - Document Selection */}
      <div className="flex-1 border-r border-default flex flex-col">
        {/* Search and Filter */}
        <div className="p-4 border-b border-default space-y-3">
          <div className="flex items-center gap-2 px-3 py-2 border border-default rounded-lg bg-card hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors">
            <Search className="w-4 h-4 text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              className="flex-1 bg-transparent outline-none text-sm text-primary placeholder:text-muted"
            />
          </div>
          <TagSelector
            selectedTags={filterTags}
            onTagsChange={setFilterTags}
            placeholder="Filter by tags..."
          />
        </div>

        {/* Selection Actions */}
        <div className="px-4 py-2 bg-subtle border-b border-default flex items-center justify-between">
          <span className="text-sm text-secondary">
            {selectedDocs.size} document(s) selected
          </span>
          <div className="flex gap-2">
            <button onClick={selectAll} className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline">
              Select all
            </button>
            <span className="text-muted">|</span>
            <button onClick={deselectAll} className="text-sm text-secondary hover:underline">
              Clear
            </button>
          </div>
        </div>

        {/* Document List */}
        <div className="flex-1 overflow-y-auto">
          {loadingDocs && documents.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
            </div>
          ) : documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-secondary">
              <FileText className="w-10 h-10 mb-3 text-muted" />
              <p>No documents found</p>
            </div>
          ) : (
            <div className="divide-y divide-default">
              {documents.map(doc => (
                <button
                  key={doc.id}
                  onClick={() => toggleDoc(doc.id)}
                  className={`w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-subtle transition-colors ${
                    selectedDocs.has(doc.id) ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''
                  }`}
                >
                  <div className={`mt-0.5 w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 ${
                    selectedDocs.has(doc.id)
                      ? 'bg-indigo-600 border-indigo-600'
                      : 'border-default'
                  }`}>
                    {selectedDocs.has(doc.id) && <Check className="w-3 h-3 text-white" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-primary truncate">
                      {doc.title || doc.filename}
                    </div>
                    {doc.tags && doc.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {doc.tags.slice(0, 4).map(tag => (
                          <span key={tag} className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs bg-subtle text-secondary rounded">
                            <Tag className="w-2.5 h-2.5" />
                            {tag}
                          </span>
                        ))}
                        {doc.tags.length > 4 && (
                          <span className="text-xs text-muted">+{doc.tags.length - 4}</span>
                        )}
                      </div>
                    )}
                  </div>
                </button>
              ))}

              {/* Load More */}
              {hasMoreDocs && (
                <button
                  onClick={() => fetchDocuments(false, searchQuery, filterTags)}
                  disabled={loadingDocs}
                  className="w-full py-3 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-subtle flex items-center justify-center gap-2"
                >
                  {loadingDocs ? (
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
      </div>

      {/* Right Panel - Tag Operations */}
      <div className="w-80 flex flex-col">
        <div className="p-4 border-b border-default">
          <h3 className="font-medium text-primary">Tag Operations</h3>
          <p className="text-sm text-secondary mt-1">
            Select documents, then add or remove tags
          </p>
        </div>

        {/* New Tag Input */}
        <div className="p-4 border-b border-default">
          <label className="block text-sm font-medium text-secondary mb-2">
            Create New Tag
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addNewTag()}
              placeholder="New tag name..."
              className="input-field flex-1 text-sm"
            />
            <button
              onClick={addNewTag}
              disabled={!newTag.trim()}
              className="p-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tags List */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-4">
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
              <h4 className="text-xs font-semibold text-secondary uppercase mb-2">
                All Tags ({allTags.length})
              </h4>
              {loadingTags ? (
                <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
              ) : allTags.length === 0 ? (
                <p className="text-sm text-muted">No tags yet</p>
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
                              : 'bg-subtle text-secondary border-default'
                          }`}
                          title="Click to add this tag"
                        >
                          <Tag className="w-3 h-3" />
                          {item.tag}
                          <span className="text-xs text-muted">({item.count})</span>
                        </button>
                        <button
                          onClick={() => toggleTagToRemove(item.tag)}
                          className={`px-1.5 rounded-r-md border-t border-r border-b transition-colors ${
                            isRemoving
                              ? 'bg-red-200 dark:bg-red-800 text-red-700 dark:text-red-300 border-red-300'
                              : 'bg-subtle text-muted hover:bg-red-50 hover:text-red-600 border-default'
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
        </div>

        {/* Apply Button */}
        <div className="p-4 border-t border-default">
          {result && (
            <div className={`mb-3 p-2 rounded-md text-sm ${
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
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {applying ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Applying...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Apply to {selectedDocs.size} Document(s)
              </>
            )}
          </button>

          {selectedDocs.size === 0 && (
            <p className="mt-2 text-xs text-secondary text-center">
              Select documents to enable tag operations
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
