'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiGet } from '@/lib/api'
import { logger } from '@/lib/logger'

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
    current.count = folder.count
  }

  return root
}

interface KBFinderSidebarProps {
  selectedFolder: string | null
  onSelectFolder: (folder: string | null) => void
  refreshTrigger?: number
}

export default function KBFinderSidebar({
  selectedFolder,
  onSelectFolder,
  refreshTrigger = 0
}: KBFinderSidebarProps) {
  const [folders, setFolders] = useState<FolderInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [totalDocCount, setTotalDocCount] = useState(0)

  const fetchFolders = useCallback(async () => {
    setLoading(true)
    try {
      const result = await apiGet<{
        success: boolean
        folders: FolderInfo[]
      }>('/api/documents/folders')
      setFolders(result.folders || [])

      // Calculate total from folder counts
      const total = (result.folders || []).reduce((sum, f) => sum + f.count, 0)
      setTotalDocCount(total)
    } catch (err) {
      logger.error('Failed to fetch folders:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchFolders()
  }, [fetchFolders, refreshTrigger])

  const tree = buildFolderTree(folders)

  const toggleFolder = (path: string) => {
    setExpandedFolders(prev => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }

  const handleFolderClick = (path: string) => {
    // Select folder and expand it
    onSelectFolder(path === selectedFolder ? null : path)
    if (!expandedFolders.has(path)) {
      setExpandedFolders(prev => new Set([...prev, path]))
    }
  }

  const renderFolderNode = (node: FolderNode, depth: number) => {
    const isExpanded = expandedFolders.has(node.path)
    const isSelected = selectedFolder === node.path
    const hasChildren = node.children.length > 0

    return (
      <div key={node.path}>
        <div
          className={`flex items-center gap-1 py-1 px-2 rounded transition-colors cursor-pointer group ${
            isSelected
              ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
              : 'hover:bg-hover text-secondary hover:text-primary'
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => handleFolderClick(node.path)}
        >
          {/* Expand/collapse toggle */}
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleFolder(node.path)
              }}
              className="p-0.5 text-muted hover:text-primary"
            >
              <svg className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            </button>
          ) : (
            <span className="w-4" />
          )}

          {/* Folder icon */}
          <svg className={`w-4 h-4 flex-shrink-0 ${isSelected ? 'text-blue-500' : 'text-amber-500'}`} fill="currentColor" viewBox="0 0 20 20">
            {isExpanded ? (
              <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v1H8a3 3 0 00-3 3v1.5a1.5 1.5 0 01-3 0V6z" />
            ) : (
              <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h6a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clipRule="evenodd" />
            )}
          </svg>

          {/* Folder name */}
          <span className="flex-1 text-sm font-medium truncate">{node.name}</span>

          {/* Document count */}
          <span className={`text-xs tabular-nums ${isSelected ? 'text-blue-500 dark:text-blue-400' : 'text-muted'}`}>
            {node.count}
          </span>
        </div>

        {/* Children */}
        {isExpanded && hasChildren && (
          <div>
            {node.children
              .sort((a, b) => a.name.localeCompare(b.name))
              .map(child => renderFolderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500 mx-auto"></div>
        <p className="text-xs text-muted mt-2">Loading folders...</p>
      </div>
    )
  }

  if (folders.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-muted">
        <p>No folders found.</p>
        <p className="text-xs mt-1">Sync your vault to see folders here.</p>
      </div>
    )
  }

  return (
    <div className="py-2">
      {/* "All Documents" root item */}
      <div
        className={`flex items-center gap-2 py-1.5 px-3 rounded transition-colors cursor-pointer mb-1 ${
          selectedFolder === null
            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
            : 'hover:bg-hover text-secondary hover:text-primary'
        }`}
        onClick={() => onSelectFolder(null)}
      >
        <svg className={`w-4 h-4 flex-shrink-0 ${selectedFolder === null ? 'text-blue-500' : 'text-slate-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <span className="text-sm font-medium flex-1">All Documents</span>
        <span className={`text-xs tabular-nums ${selectedFolder === null ? 'text-blue-500 dark:text-blue-400' : 'text-muted'}`}>
          {totalDocCount}
        </span>
      </div>

      {/* Folder tree */}
      {tree.children
        .sort((a, b) => a.name.localeCompare(b.name))
        .map(child => renderFolderNode(child, 0))}
    </div>
  )
}
