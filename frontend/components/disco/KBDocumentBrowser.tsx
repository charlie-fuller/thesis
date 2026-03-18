'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { X, Search, FileText, Check, Loader2, Eye, Tag, Link, Link2, ArrowUpDown, Filter, Folder, FolderOpen, ChevronRight, CheckSquare } from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'
import TagSelector from '@/components/TagSelector'

type SortOption = 'recent' | 'oldest' | 'name_asc' | 'name_desc'
type SourceOption = '' | 'obsidian' | 'upload'
type ViewMode = 'search' | 'folders'

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'recent', label: 'Most Recent' },
  { value: 'oldest', label: 'Oldest First' },
  { value: 'name_asc', label: 'Name (A-Z)' },
  { value: 'name_desc', label: 'Name (Z-A)' },
]

const SOURCE_OPTIONS: { value: SourceOption; label: string }[] = [
  { value: '', label: 'All Sources' },
  { value: 'obsidian', label: 'Vault' },
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

interface FolderInfo {
  path: string
  count: number
}

interface FolderNode {
  name: string
  path: string
  count: number
  children: FolderNode[]
}

function buildFolderTree(folders: FolderInfo[]): FolderNode {
  const root: FolderNode = { name: 'root', path: '', count: 0, children: [] }
  const sorted = [...folders].sort((a, b) => a.path.localeCompare(b.path))

  for (const folder of sorted) {
    const parts = folder.path.split('/')
    let current = root
    let currentPath = ''

    for (const part of parts) {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      let child = current.children.find(c => c.name === part)
      if (!child) {
        child = { name: part, path: currentPath, count: 0, children: [] }
        current.children.push(child)
      }
      current = child
    }
    // Set the count from the API data
    current.count = folder.count
  }

  return root
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
  // Search mode state
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTagsFilter, setSelectedTagsFilter] = useState<Set<string>>(new Set())
  const [sortBy, setSortBy] = useState<SortOption>('recent')
  const [sourceFilter, setSourceFilter] = useState<SourceOption>('')
  const [documents, setDocuments] = useState<KBDocument[]>([])
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [offset, setOffset] = useState(0)

  // Shared state
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set())
  const [previewDoc, setPreviewDoc] = useState<string | null>(null)
  const [previewContent, setPreviewContent] = useState<string>('')
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [linking, setLinking] = useState(false)

  // Folder mode state
  const [viewMode, setViewMode] = useState<ViewMode>('search')
  const [folders, setFolders] = useState<FolderInfo[]>([])
  const [loadingFolders, setLoadingFolders] = useState(false)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [folderDocuments, setFolderDocuments] = useState<Record<string, KBDocument[]>>({})
  const [loadingFolder, setLoadingFolder] = useState<string | null>(null)
  const [selectingFolder, setSelectingFolder] = useState<string | null>(null)

  // Linked folders state (auto-link subscriptions)
  const [linkedFolderPaths, setLinkedFolderPaths] = useState<Set<string>>(new Set())
  const [linkingFolder, setLinkingFolder] = useState<string | null>(null)

  const LIMIT = 20

  const folderTree = useMemo(() => buildFolderTree(folders), [folders])

  // Fetch documents for search mode
  const fetchDocuments = useCallback(async (
    resetOffset = true,
    query?: string,
    tags?: Set<string>,
    sort?: SortOption,
    source?: SourceOption
  ) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        limit: LIMIT.toString(),
        offset: resetOffset ? '0' : offset.toString()
      })
      const q = query ?? searchQuery
      const t = tags ?? selectedTagsFilter
      const s = sort ?? sortBy
      const src = source ?? sourceFilter

      if (q) params.append('q', q)
      if (t.size > 0) params.append('tags', Array.from(t).join(','))
      if (s) params.append('sort', s)
      if (src) params.append('source', src)

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
  }, [offset, searchQuery, selectedTagsFilter, sortBy, sourceFilter])

  // Fetch folder list
  const fetchFolders = useCallback(async () => {
    setLoadingFolders(true)
    try {
      const result = await apiGet<{
        success: boolean
        folders: FolderInfo[]
      }>('/api/documents/folders')
      setFolders(result.folders || [])
    } catch (err) {
      console.error('Failed to fetch folders:', err)
    } finally {
      setLoadingFolders(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    if (isOpen) {
      if (viewMode === 'search') {
        fetchDocuments(true, searchQuery, selectedTagsFilter, sortBy, sourceFilter)
      } else {
        fetchFolders()
      }
    }
  }, [isOpen, viewMode])

  // Fetch linked folders on open
  useEffect(() => {
    if (isOpen) {
      apiGet<{ success: boolean; folders: { folder_path: string }[] }>(
        `/api/disco/initiatives/${initiativeId}/linked-folders`
      ).then(result => {
        setLinkedFolderPaths(new Set((result.folders || []).map(f => f.folder_path)))
      }).catch(() => {})
    }
  }, [isOpen, initiativeId])

  // Re-fetch search results when filters change
  useEffect(() => {
    if (isOpen && viewMode === 'search') {
      fetchDocuments(true, searchQuery, selectedTagsFilter, sortBy, sourceFilter)
    }
  }, [searchQuery, selectedTagsFilter, sortBy, sourceFilter])

  const handleLinkFolder = async (folderPath: string) => {
    setLinkingFolder(folderPath)
    try {
      await apiPost(`/api/disco/initiatives/${initiativeId}/folders/link`, {
        folder_path: folderPath,
        recursive: true,
        backfill: true,
      })
      setLinkedFolderPaths(prev => new Set([...prev, folderPath]))
    } catch (err) {
      console.error('Failed to link folder:', err)
    } finally {
      setLinkingFolder(null)
    }
  }

  // Load documents for a specific folder
  const loadFolderDocuments = async (folderPath: string) => {
    setLoadingFolder(folderPath)
    try {
      const params = new URLSearchParams({
        folder: folderPath,
        limit: '200',
        sort: 'name_asc'
      })
      const result = await apiGet<{
        success: boolean
        documents: KBDocument[]
      }>(`/api/documents/search?${params}`)

      // Filter to only direct children (not in subfolders)
      const directDocs = (result.documents || []).filter(doc => {
        if (!doc.obsidian_file_path) return false
        const relativePath = doc.obsidian_file_path.substring(folderPath.length + 1)
        return relativePath && !relativePath.includes('/')
      })

      setFolderDocuments(prev => ({ ...prev, [folderPath]: directDocs }))
    } catch (err) {
      console.error('Failed to load folder documents:', err)
    } finally {
      setLoadingFolder(null)
    }
  }

  // Toggle folder expand/collapse
  const toggleFolder = async (folderPath: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(folderPath)) {
      newExpanded.delete(folderPath)
    } else {
      newExpanded.add(folderPath)
      if (!folderDocuments[folderPath]) {
        await loadFolderDocuments(folderPath)
      }
    }
    setExpandedFolders(newExpanded)
  }

  // Select all documents in a folder (including subfolders)
  const selectAllInFolder = async (folderPath: string) => {
    setSelectingFolder(folderPath)
    try {
      const params = new URLSearchParams({
        folder: folderPath,
        limit: '500',
        sort: 'name_asc'
      })
      const result = await apiGet<{
        success: boolean
        documents: KBDocument[]
      }>(`/api/documents/search?${params}`)

      const newSelected = new Set(selectedDocs)
      for (const doc of result.documents || []) {
        newSelected.add(doc.id)
      }
      setSelectedDocs(newSelected)
    } catch (err) {
      console.error('Failed to select folder documents:', err)
    } finally {
      setSelectingFolder(null)
    }
  }

  // Deselect all documents in a folder
  const deselectAllInFolder = async (folderPath: string) => {
    setSelectingFolder(folderPath)
    try {
      const params = new URLSearchParams({
        folder: folderPath,
        limit: '500',
        sort: 'name_asc'
      })
      const result = await apiGet<{
        success: boolean
        documents: KBDocument[]
      }>(`/api/documents/search?${params}`)

      const newSelected = new Set(selectedDocs)
      for (const doc of result.documents || []) {
        newSelected.delete(doc.id)
      }
      setSelectedDocs(newSelected)
    } catch (err) {
      console.error('Failed to deselect folder documents:', err)
    } finally {
      setSelectingFolder(null)
    }
  }

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

  // Select all visible documents (search mode)
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

  // Switch view mode
  const switchViewMode = (mode: ViewMode) => {
    setViewMode(mode)
    if (mode === 'folders' && folders.length === 0) {
      fetchFolders()
    }
  }

  // Close and reset
  const handleClose = () => {
    setSelectedDocs(new Set())
    setPreviewDoc(null)
    setPreviewContent('')
    setSearchQuery('')
    setSelectedTagsFilter(new Set())
    setSortBy('recent')
    setSourceFilter('')
    setViewMode('search')
    setExpandedFolders(new Set())
    setFolderDocuments({})
    onClose()
  }

  // Render a document row (shared between search and folder modes)
  const renderDocumentRow = (doc: KBDocument) => (
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
        {doc.obsidian_file_path && viewMode === 'search' && (
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
  )

  // Render folder tree node
  const renderFolderNode = (node: FolderNode, depth: number) => {
    const isExpanded = expandedFolders.has(node.path)
    const isLoading = loadingFolder === node.path
    const directDocs = folderDocuments[node.path] || []
    const isSelecting = selectingFolder === node.path

    // Check if all loaded docs in this folder are selected
    const allDirectSelected = directDocs.length > 0 &&
      directDocs.every(d => selectedDocs.has(d.id))

    return (
      <div key={node.path}>
        {/* Folder row */}
        <div
          className="flex items-center gap-1 py-1.5 px-2 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded transition-colors group"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {/* Expand/collapse */}
          <button
            onClick={() => toggleFolder(node.path)}
            className="p-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <ChevronRight className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
          </button>

          {/* Folder icon */}
          {isExpanded ? (
            <FolderOpen className="w-4 h-4 text-amber-500 flex-shrink-0" />
          ) : (
            <Folder className="w-4 h-4 text-amber-500 flex-shrink-0" />
          )}

          {/* Name - click to expand */}
          <button
            onClick={() => toggleFolder(node.path)}
            className="flex-1 text-left text-sm font-medium text-slate-700 dark:text-slate-200 truncate"
          >
            {node.name}
          </button>

          {/* Count badge */}
          <span className="text-xs text-slate-400 dark:text-slate-500 tabular-nums mr-1">
            {node.count}
          </span>

          {/* Select all in folder button */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              if (allDirectSelected && isExpanded) {
                deselectAllInFolder(node.path)
              } else {
                selectAllInFolder(node.path)
              }
            }}
            disabled={isSelecting}
            className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs text-slate-400 hover:text-indigo-600 dark:text-slate-500 dark:hover:text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity rounded hover:bg-indigo-50 dark:hover:bg-indigo-900/20"
            title={`Select all ${node.count} documents in ${node.name}`}
          >
            {isSelecting ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <CheckSquare className="w-3 h-3" />
            )}
            {allDirectSelected && isExpanded ? 'Deselect' : 'Select all'}
          </button>

          {/* Link folder button */}
          {linkedFolderPaths.has(node.path) ? (
            <span
              className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs text-emerald-600 dark:text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity"
              title="This folder is auto-linked"
            >
              <Link2 className="w-3 h-3" />
              Auto-linked
            </span>
          ) : (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleLinkFolder(node.path)
              }}
              disabled={linkingFolder === node.path}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs text-slate-400 hover:text-emerald-600 dark:text-slate-500 dark:hover:text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
              title={`Auto-link folder "${node.name}" — new docs will be linked automatically`}
            >
              {linkingFolder === node.path ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Link2 className="w-3 h-3" />
              )}
              Link folder
            </button>
          )}
        </div>

        {/* Expanded content */}
        {isExpanded && (
          <div>
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex items-center gap-2 py-2" style={{ paddingLeft: `${(depth + 1) * 16 + 24}px` }}>
                <Loader2 className="w-3.5 h-3.5 text-indigo-500 animate-spin" />
                <span className="text-xs text-slate-400">Loading documents...</span>
              </div>
            )}

            {/* Direct documents in this folder */}
            {directDocs.map(doc => (
              <div
                key={doc.id}
                className={`flex items-center gap-2 py-1.5 px-2 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded transition-colors ${
                  selectedDocs.has(doc.id) ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''
                } ${
                  previewDoc === doc.id ? 'bg-emerald-50/50 dark:bg-emerald-900/20' : ''
                }`}
                style={{ paddingLeft: `${(depth + 1) * 16 + 16}px` }}
              >
                <button
                  onClick={() => toggleDoc(doc.id)}
                  className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 ${
                    selectedDocs.has(doc.id)
                      ? 'bg-indigo-600 border-indigo-600'
                      : 'border-slate-300 dark:border-slate-600 hover:border-indigo-400'
                  }`}
                >
                  {selectedDocs.has(doc.id) && <Check className="w-2.5 h-2.5 text-white" />}
                </button>

                <FileText className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />

                <span className="flex-1 text-sm text-slate-700 dark:text-slate-300 truncate">
                  {doc.title || doc.filename}
                </span>

                <button
                  onClick={() => loadPreview(doc.id)}
                  className="p-1 text-slate-300 hover:text-indigo-600 dark:text-slate-600 dark:hover:text-indigo-400 rounded transition-colors"
                  title="Preview"
                >
                  <Eye className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}

            {/* Child folders */}
            {node.children
              .sort((a, b) => a.name.localeCompare(b.name))
              .map(child => renderFolderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
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

        {/* View Mode Toggle + Filters */}
        <div className="px-6 py-3 border-b border-slate-200 dark:border-slate-700 space-y-3">
          {/* View mode toggle */}
          <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-700 rounded-lg p-1 w-fit">
            <button
              onClick={() => switchViewMode('search')}
              className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-colors ${
                viewMode === 'search'
                  ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              Search
            </button>
            <button
              onClick={() => switchViewMode('folders')}
              className={`flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-colors ${
                viewMode === 'folders'
                  ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <Folder className="w-3.5 h-3.5" />
              Folders
            </button>
          </div>

          {/* Search filters (only in search mode) */}
          {viewMode === 'search' && (
            <>
              <div className="flex items-start gap-4">
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
              <div className="flex items-center gap-4">
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
                {(sortBy !== 'recent' || sourceFilter) && (
                  <button
                    onClick={() => {
                      setSortBy('recent')
                      setSourceFilter('')
                    }}
                    className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    Reset filters
                  </button>
                )}
              </div>
            </>
          )}
        </div>

        {/* Content - Split View */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Document List or Folder Tree */}
          <div className="w-2/5 overflow-y-auto border-r border-slate-200 dark:border-slate-700">
            {viewMode === 'search' ? (
              // Search mode: flat document list
              <>
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
                    {documents.map(doc => renderDocumentRow(doc))}
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
              </>
            ) : (
              // Folder mode: folder tree
              <>
                {loadingFolders ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
                  </div>
                ) : folderTree.children.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-slate-500 dark:text-slate-400">
                    <Folder className="w-10 h-10 mb-3 text-slate-300 dark:text-slate-600" />
                    <p>No vault folders found</p>
                    <p className="text-sm">Sync your local vault to browse folders</p>
                  </div>
                ) : (
                  <div className="py-2">
                    {folderTree.children
                      .sort((a, b) => a.name.localeCompare(b.name))
                      .map(node => renderFolderNode(node, 0))}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Preview Panel */}
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
            {viewMode === 'search' && (
              <button
                onClick={selectAll}
                className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                Select visible
              </button>
            )}
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
