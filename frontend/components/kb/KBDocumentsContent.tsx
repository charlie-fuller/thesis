'use client'

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import ClassificationReviewBanner from '@/components/kb/ClassificationReviewBanner'
import KBDocumentBrowserTab from '@/components/kb/KBDocumentBrowserTab'
import KBFinderSidebar from '@/components/kb/KBFinderSidebar'
import KBFinderContent from '@/components/kb/KBFinderContent'
import KBDocumentInfoModal from '@/components/kb/KBDocumentInfoModal'
import KBSyncSettingsModal from '@/components/kb/KBSyncSettingsModal'
import TagSelector from '@/components/TagSelector'
import { apiGet } from '@/lib/api'
import { logger } from '@/lib/logger'
import { formatLastSync } from '@/lib/googleDrive'
import type { Document } from '@/components/kb/KBDocumentInfoModal'

interface ObsidianStatus {
  connected: boolean
  vault_name?: string
  document_count?: number
  last_sync?: string
  pending_changes?: number
  unsynced_count?: number
}

export default function KBDocumentsContent() {
  const searchParams = useSearchParams()

  // Core UI state
  const [activeTab, setActiveTab] = useState<'documents' | 'tags'>('documents')
  const [selectedFolder, setSelectedFolder] = useState<string | null>('__all__')  // Default to showing all docs
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('all')
  const [sortOrder, setSortOrder] = useState<string>('recent')
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set())

  // Modal state
  const [showSyncSettings, setShowSyncSettings] = useState(false)
  const [showInfoModal, setShowInfoModal] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)

  // Refresh trigger for child components
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  // Obsidian status for toolbar badge
  const [obsidianStatus, setObsidianStatus] = useState<ObsidianStatus | null>(null)

  // Check obsidian status for toolbar sync badge
  const checkObsidianStatus = useCallback(async () => {
    try {
      const response = await apiGet<{
        connected: boolean
        vault_name?: string
        files_synced?: number
        pending_changes?: number
        unsynced_count?: number
        last_sync?: string
      }>('/api/obsidian/status')
      setObsidianStatus({
        connected: response.connected,
        vault_name: response.vault_name,
        document_count: response.files_synced,
        pending_changes: response.pending_changes,
        unsynced_count: response.unsynced_count,
        last_sync: response.last_sync
      })
    } catch (err) {
      logger.error('Error checking Obsidian status:', err)
    }
  }, [])

  // Initial load: check status
  /* eslint-disable react-hooks/set-state-in-effect -- initial data fetch on mount */
  useEffect(() => {
    checkObsidianStatus()
  }, [checkObsidianStatus])
  /* eslint-enable react-hooks/set-state-in-effect */

  const handleDocumentsChange = useCallback(() => {
    setRefreshTrigger(prev => prev + 1)
    checkObsidianStatus()
  }, [checkObsidianStatus])

  // Handle OAuth callbacks from search params
  /* eslint-disable react-hooks/set-state-in-effect -- one-time OAuth callback on mount */
  useEffect(() => {
    const driveParam = searchParams?.get('google_drive')
    const notionParam = searchParams?.get('notion')

    if (driveParam === 'connected' || driveParam === 'error' ||
        notionParam === 'connected' || notionParam === 'error') {
      // Handle popup window case
      if (window.opener) {
        try {
          if (driveParam === 'connected') {
            window.opener.postMessage({ type: 'google_drive_connected' }, window.location.origin)
          } else if (driveParam === 'error') {
            window.opener.postMessage({ type: 'google_drive_error', message: searchParams?.get('message') || 'Failed' }, window.location.origin)
          } else if (notionParam === 'connected') {
            window.opener.postMessage({ type: 'notion_connected' }, window.location.origin)
          } else if (notionParam === 'error') {
            window.opener.postMessage({ type: 'notion_error', message: searchParams?.get('message') || 'Failed' }, window.location.origin)
          }
          setTimeout(() => window.close(), 100)
        } catch (e) {
          logger.error('Failed to close popup:', e)
          window.close()
        }
      } else {
        // Main window - clear URL and refresh
        window.history.replaceState({}, '', '/kb')
        handleDocumentsChange()
      }
    }
  }, [])
  /* eslint-enable react-hooks/set-state-in-effect */

  // Listen for OAuth messages from popups
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || ''
      const allowedOrigins = [window.location.origin, backendUrl, 'null']
      if (!allowedOrigins.some(origin => event.origin === origin || event.origin.startsWith(origin))) return

      if (event.data.type === 'google_drive_connected' ||
          event.data.type === 'notion_connected') {
        handleDocumentsChange()
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [])

  // Listen for Notion OAuth completion custom event
  useEffect(() => {
    const handleNotionOAuth = () => {
      setTimeout(() => handleDocumentsChange(), 1000)
    }
    window.addEventListener('notion-oauth-complete', handleNotionOAuth)
    return () => window.removeEventListener('notion-oauth-complete', handleNotionOAuth)
  }, [])

  function handleDocumentClick(doc: Document) {
    setSelectedDoc(doc)
    setShowInfoModal(true)
  }

  function handleDocumentUpdate(updatedDoc: Document) {
    // Trigger refresh so content pane reloads
    setRefreshTrigger(prev => prev + 1)
  }

  // Sync status text for toolbar
  const syncStatusText = obsidianStatus?.connected
    ? obsidianStatus.last_sync
      ? `Synced ${formatLastSync(obsidianStatus.last_sync)}`
      : 'Connected'
    : null

  const pendingCount = (obsidianStatus?.unsynced_count ?? 0) + (obsidianStatus?.pending_changes ?? 0)

  return (
    <div className="flex flex-col h-full">
      {/* Classification Review Banner */}
      <ClassificationReviewBanner
        onReviewComplete={handleDocumentsChange}
        refreshTrigger={refreshTrigger}
      />

      {/* Tab Navigation */}
      <div className="mb-4 border-b border-default">
        <nav className="-mb-px flex gap-4">
          <button
            onClick={() => setActiveTab('documents')}
            className={`py-2 px-1 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'documents'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-secondary hover:text-primary hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            Documents
          </button>
          <button
            onClick={() => setActiveTab('tags')}
            className={`py-2 px-1 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'tags'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-secondary hover:text-primary hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            Tag Manager
          </button>
        </nav>
      </div>

      {/* Tag Manager Tab */}
      {activeTab === 'tags' && (
        <KBDocumentBrowserTab onDocumentsChange={handleDocumentsChange} />
      )}

      {/* Documents Tab - Finder Layout */}
      {activeTab === 'documents' && (
        <div className="flex flex-col flex-1 min-h-0">
          {/* Toolbar */}
          <div className="flex items-center gap-3 mb-3">
            {/* Search */}
            <div className="relative flex-1">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-default rounded-lg text-sm bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-primary"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>

            {/* Tag Filter */}
            <div className="w-48">
              <TagSelector
                selectedTags={selectedTags}
                onTagsChange={setSelectedTags}
                placeholder="Filter by tags..."
                showInitiatives={false}
                size="sm"
              />
            </div>

            {/* Source Filter */}
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="px-3 py-2 border border-default rounded-lg text-sm bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Sources</option>
              <option value="obsidian">Vault</option>
              <option value="google_drive">Google Drive</option>
              <option value="notion">Notion</option>
              <option value="upload">Uploaded</option>
            </select>

            {/* Sort Order */}
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="px-3 py-2 border border-default rounded-lg text-sm bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="recent">Most Recent</option>
              <option value="oldest">Oldest First</option>
              <option value="name_asc">Name (A-Z)</option>
              <option value="name_desc">Name (Z-A)</option>
            </select>

            {/* Sync Status Badge */}
            {syncStatusText && (
              <span className="text-xs text-muted whitespace-nowrap hidden sm:inline">
                {syncStatusText}
              </span>
            )}
            {pendingCount > 0 && (
              <span className="text-xs px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded whitespace-nowrap">
                {pendingCount} pending
              </span>
            )}

            {/* Gear icon for sync settings */}
            <button
              onClick={() => setShowSyncSettings(true)}
              className="p-2 text-secondary hover:text-primary hover:bg-hover rounded-lg transition-colors"
              title="Sync settings"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>

          {/* Finder: Sidebar + Content */}
          <div className="flex flex-1 min-h-0 border border-default rounded-lg overflow-hidden bg-card">
            {/* Sidebar */}
            <div className="w-64 border-r border-default overflow-y-auto bg-subtle flex-shrink-0">
              <KBFinderSidebar
                selectedFolder={selectedFolder}
                onSelectFolder={setSelectedFolder}
                refreshTrigger={refreshTrigger}
              />
            </div>

            {/* Content pane */}
            <div className="flex-1 min-w-0 overflow-hidden">
              <KBFinderContent
                selectedFolder={selectedFolder}
                searchQuery={searchQuery}
                sourceFilter={sourceFilter}
                sortOrder={sortOrder}
                selectedTags={selectedTags}
                onDocumentClick={handleDocumentClick}
                onDocumentsChange={handleDocumentsChange}
                refreshTrigger={refreshTrigger}
              />
            </div>
          </div>
        </div>
      )}

      {/* Sync Settings Modal */}
      <KBSyncSettingsModal
        isOpen={showSyncSettings}
        onClose={() => setShowSyncSettings(false)}
        onDocumentsChange={handleDocumentsChange}
      />

      {/* Document Info Modal */}
      <KBDocumentInfoModal
        isOpen={showInfoModal}
        document={selectedDoc}
        onClose={() => {
          setShowInfoModal(false)
          setSelectedDoc(null)
        }}
        onSave={() => {
          setRefreshTrigger(prev => prev + 1)
        }}
        onDocumentUpdate={handleDocumentUpdate}
      />
    </div>
  )
}
