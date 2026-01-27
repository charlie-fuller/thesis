'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useSearchParams } from 'next/navigation'
import Image from 'next/image'
import DocumentUpload from '@/components/DocumentUpload'
import ClassificationReviewBanner from '@/components/kb/ClassificationReviewBanner'
import LoadingSpinner from '@/components/LoadingSpinner'
import ConfirmModal from '@/components/ConfirmModal'
import StorageIndicator from '@/components/StorageIndicator'
import GoogleDrivePicker from '@/components/GoogleDrivePicker'
import TagManagerTab from '@/components/kb/TagManagerTab'
import DeleteDocumentModal from '@/components/kb/DeleteDocumentModal'
import { logger } from '@/lib/logger'
import {
  getGoogleDriveStatus,
  connectGoogleDrive,
  syncGoogleDrive,
  syncGoogleDriveFiles,
  listFolderFiles,
  disconnectGoogleDrive,
  formatLastSync,
  type GoogleDriveStatus,
  type GoogleDriveFile
} from '@/lib/googleDrive'
import {
  getNotionStatus,
  connectNotion,
  syncNotion,
  disconnectNotion,
  getNotionPages,
  type NotionStatus,
  type NotionPage
} from '@/lib/notion'
import { apiGet, apiPatch, apiPost, apiPut, apiDelete } from '@/lib/api'
import { API_BASE_URL } from '@/lib/config'

interface DocumentTag {
  tag: string
  source: 'path' | 'frontmatter' | 'manual'
}

interface Document {
  id: string
  title?: string
  filename: string
  uploaded_at: string
  original_date?: string  // Actual document date (e.g., meeting date for transcripts)
  processed: boolean
  processing_status?: string
  processing_error?: string
  storage_url: string
  source_platform?: string
  external_url?: string
  google_drive_file_id?: string
  notion_page_id?: string
  sync_cadence?: string
  file_size?: number
  obsidian_vault_path?: string
  obsidian_file_path?: string
  tags?: DocumentTag[]
}

export default function KBDocumentsContent() {
  const { profile } = useAuth()
  const searchParams = useSearchParams()

  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Google Drive state
  const [driveStatus, setDriveStatus] = useState<GoogleDriveStatus | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [syncSuccess, setSyncSuccess] = useState<string | null>(null)
  const [syncFrequency, setSyncFrequency] = useState<string>('manual')
  const [nextSyncScheduled, setNextSyncScheduled] = useState<string | null>(null)
  const [driveExpanded, setDriveExpanded] = useState<boolean>(false)
  const [showDisconnectModal, setShowDisconnectModal] = useState(false)
  const [selectedFolderId, setSelectedFolderId] = useState<string>('')
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- setter kept for picker callback
  const [_selectedFolderName, setSelectedFolderName] = useState<string>('')
  const [driveFiles, setDriveFiles] = useState<GoogleDriveFile[]>([])
  const [driveFilesLoading, setDriveFilesLoading] = useState(false)
  const [selectedDriveFileIds, setSelectedDriveFileIds] = useState<Set<string>>(new Set())
  const [isFileUrl, setIsFileUrl] = useState<boolean>(false)

  // Notion state
  const [notionStatus, setNotionStatus] = useState<NotionStatus | null>(null)
  const [notionSyncing, setNotionSyncing] = useState(false)
  const [, setNotionSyncError] = useState<string | null>(null)
  const [, setNotionSyncSuccess] = useState<string | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- kept for future Notion UI section
  const [_notionExpanded, setNotionExpanded] = useState<boolean>(false)
  const [showNotionDisconnectModal, setShowNotionDisconnectModal] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- kept for future Notion feature
  const [, _setNotionPageIds] = useState<string>('')
  const [, setNotionSyncFrequency] = useState<string>('manual')
  const [, setNotionNextSyncScheduled] = useState<string | null>(null)
  const [notionPages, setNotionPages] = useState<NotionPage[]>([])
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- kept for future Notion feature
  const [_notionPagesLoading, setNotionPagesLoading] = useState(false)
  const [selectedNotionPageIds, setSelectedNotionPageIds] = useState<Set<string>>(new Set())

  // Obsidian state
  interface ObsidianStatus {
    connected: boolean
    vault_name?: string
    vault_path?: string
    document_count?: number
    last_sync?: string
    pending_changes?: number
    total_files?: number
  }
  const [obsidianStatus, setObsidianStatus] = useState<ObsidianStatus | null>(null)
  const [obsidianExpanded, setObsidianExpanded] = useState<boolean>(false)
  const [obsidianSyncing, setObsidianSyncing] = useState(false)
  const [obsidianSyncError, setObsidianSyncError] = useState<string | null>(null)
  const [obsidianSyncSuccess, setObsidianSyncSuccess] = useState<string | null>(null)
  const [obsidianSyncProgress, setObsidianSyncProgress] = useState<{ synced: number; total: number } | null>(null)

  // Document actions state
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null)
  const [syncingDocId, setSyncingDocId] = useState<string | null>(null)
  const [showInfoModal, setShowInfoModal] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [docToDelete, setDocToDelete] = useState<Document | null>(null)
  const [docSyncCadence, setDocSyncCadence] = useState<string>('manual')
  const [tempSyncCadence, setTempSyncCadence] = useState<string>('manual')

  // Original date state for document info modal
  const [tempOriginalDate, setTempOriginalDate] = useState<string>('')
  const [savingOriginalDate, setSavingOriginalDate] = useState(false)

  // Agent assignment state for document info modal
  interface Agent {
    id: string
    name: string
    display_name: string
  }
  const [allAgents, setAllAgents] = useState<Agent[]>([])
  const [docIsGlobal, setDocIsGlobal] = useState<boolean>(true)
  const [docLinkedAgentIds, setDocLinkedAgentIds] = useState<Set<string>>(new Set())
  const [loadingAgentAssignments, setLoadingAgentAssignments] = useState(false)
  const [savingAgentAssignments, setSavingAgentAssignments] = useState(false)

  // Tag management state for document info modal
  const [newTagInput, setNewTagInput] = useState<string>('')
  const [addingTag, setAddingTag] = useState(false)
  const [removingTag, setRemovingTag] = useState<string | null>(null)

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('all') // 'all', 'upload', 'google_drive', 'obsidian'
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set())

  // Tab state for Documents vs Tag Manager
  const [activeTab, setActiveTab] = useState<'documents' | 'tags'>('documents')

  // Compute all unique tags from documents (sorted by frequency, then alphabetically)
  const allTags = useMemo(() => {
    const tagCounts: Record<string, number> = {}
    documents.forEach(doc => {
      (doc.tags || []).forEach(t => {
        tagCounts[t.tag] = (tagCounts[t.tag] || 0) + 1
      })
    })
    // Sort by frequency (descending), then alphabetically
    return Object.entries(tagCounts)
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([tag]) => tag)
  }, [documents])

  // Toggle a tag in the filter
  const toggleTagFilter = (tag: string) => {
    setSelectedTags(prev => {
      const next = new Set(prev)
      if (next.has(tag)) {
        next.delete(tag)
      } else {
        next.add(tag)
      }
      return next
    })
  }

  // Clear all tag filters
  const clearTagFilters = () => {
    setSelectedTags(new Set())
  }

  // Filtered documents based on search query, source filter, and tag filter
  const filteredDocuments = useMemo(() => {
    return documents.filter(doc => {
      // Search filter - match filename or title
      const matchesSearch = searchQuery.trim() === '' ||
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (doc.title && doc.title.toLowerCase().includes(searchQuery.toLowerCase()))

      // Source filter
      let matchesSource = true
      if (sourceFilter === 'upload') {
        matchesSource = !doc.source_platform
      } else if (sourceFilter !== 'all') {
        matchesSource = doc.source_platform === sourceFilter
      }

      // Tag filter - document must have ALL selected tags (AND logic)
      let matchesTags = true
      if (selectedTags.size > 0) {
        const docTags = new Set((doc.tags || []).map(t => t.tag))
        matchesTags = Array.from(selectedTags).every(tag => docTags.has(tag))
      }

      return matchesSearch && matchesSource && matchesTags
    })
  }, [documents, searchQuery, sourceFilter, selectedTags])

  // Helper to extract top-level folder from Obsidian file path
  const getTopLevelFolder = (filePath: string | undefined): string => {
    if (!filePath) return ''
    const parts = filePath.split('/')
    return parts.length > 1 ? parts[0] : ''
  }

  // Group ALL Obsidian documents by top-level folder (for Obsidian panel vault structure)
  const obsidianFolders = useMemo(() => {
    const folders: Record<string, Document[]> = {}

    documents.forEach(doc => {
      if (doc.source_platform === 'obsidian' && doc.obsidian_file_path) {
        const folder = getTopLevelFolder(doc.obsidian_file_path) || '(root)'
        if (!folders[folder]) folders[folder] = []
        folders[folder].push(doc)
      }
    })

    // Sort folders alphabetically
    const sortedFolders: Record<string, Document[]> = {}
    Object.keys(folders).sort().forEach(key => {
      sortedFolders[key] = folders[key]
    })

    return sortedFolders
  }, [documents])

  // Get directly uploaded documents (not from Drive, Notion, or Obsidian)
  const uploadedDocuments = useMemo(() => {
    return documents.filter(doc =>
      !doc.source_platform || doc.source_platform === 'upload'
    )
  }, [documents])

  // Track which folders are collapsed (default all collapsed)
  const [collapsedFolders, setCollapsedFolders] = useState<Set<string>>(new Set())
  const [foldersInitialized, setFoldersInitialized] = useState(false)

  // Initialize all folders as collapsed when they first load
  useEffect(() => {
    const folderKeys = Object.keys(obsidianFolders)
    if (folderKeys.length > 0 && !foldersInitialized) {
      setCollapsedFolders(new Set(folderKeys))
      setFoldersInitialized(true)
    }
  }, [obsidianFolders, foldersInitialized])

  const toggleFolderCollapse = (folder: string) => {
    setCollapsedFolders(prev => {
      const next = new Set(prev)
      if (next.has(folder)) {
        next.delete(folder)
      } else {
        next.add(folder)
      }
      return next
    })
  }

  // General document notifications (separate from Drive/Notion specific ones)
  const [generalSuccess, setGeneralSuccess] = useState<string | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)

  // Storage refresh trigger
  const [storageRefreshTrigger, setStorageRefreshTrigger] = useState<number>(0)

  // Upload and Documents section state
  const [uploadExpanded, setUploadExpanded] = useState<boolean>(false)
  const [documentsExpanded, setDocumentsExpanded] = useState<boolean>(false)


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

  const loadSyncSettings = useCallback(async () => {
    try {
      const data = await apiGet<{ sync_frequency: string; next_sync_scheduled: string | null }>('/api/google-drive/sync-settings')
      setSyncFrequency(data.sync_frequency || 'manual')
      setNextSyncScheduled(data.next_sync_scheduled)
    } catch (err) {
      logger.error('Error loading sync settings:', err)
    }
  }, [])

  const checkDriveStatus = useCallback(async () => {
    try {
      const status = await getGoogleDriveStatus()
      setDriveStatus(status)

      // Load sync settings if connected
      if (status.connected) {
        loadSyncSettings()
      }
    } catch (err) {
      logger.error('Error checking Drive status:', err)
    }
  }, [loadSyncSettings])

  // Notion status check function (not memoized to avoid TypeScript confusion)
  async function checkNotionStatusFn() {
    try {
      const status = await getNotionStatus()
      setNotionStatus(status)
    } catch (err) {
      logger.error('Error checking Notion status:', err)
    }
  }

  // Obsidian status check function
  async function checkObsidianStatusFn() {
    try {
      const response = await apiGet<{
        success: boolean
        connected: boolean
        vault_name?: string
        vault_path?: string
        files_synced?: number
        pending_changes?: number
        last_sync?: string
      }>('/api/obsidian/status')
      setObsidianStatus({
        connected: response.connected,
        vault_name: response.vault_name,
        vault_path: response.vault_path,
        document_count: response.files_synced,
        pending_changes: response.pending_changes,
        last_sync: response.last_sync
      })
      return response
    } catch (err) {
      logger.error('Error checking Obsidian status:', err)
      setObsidianStatus({ connected: false })
      return null
    }
  }

  // Obsidian full sync handler with progress polling
  async function handleObsidianFullSync() {
    try {
      setObsidianSyncing(true)
      setObsidianSyncError(null)
      setObsidianSyncSuccess(null)
      setObsidianSyncProgress(null)

      // Get initial count before sync
      const initialStatus = await checkObsidianStatusFn()
      const initialSynced = initialStatus?.files_synced ?? 0

      await apiPost<{ success: boolean; message: string }>('/api/obsidian/sync/full')

      // Poll for progress every 2 seconds
      const pollInterval = setInterval(async () => {
        const status = await checkObsidianStatusFn()
        if (status) {
          const currentSynced = status.files_synced ?? 0
          const pending = status.pending_changes ?? 0
          const total = currentSynced + pending

          if (total > 0) {
            setObsidianSyncProgress({ synced: currentSynced, total })
          }

          // Stop polling when no more pending changes
          if (pending === 0 && currentSynced > initialSynced) {
            clearInterval(pollInterval)
            setObsidianSyncing(false)
            setObsidianSyncProgress(null)
            setObsidianSyncSuccess(`Sync complete! ${currentSynced} documents synced.`)
            setTimeout(() => setObsidianSyncSuccess(null), 10000)
            loadDocuments(false)
          }
        }
      }, 2000)

      // Safety timeout after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval)
        if (obsidianSyncing) {
          setObsidianSyncing(false)
          setObsidianSyncProgress(null)
          setObsidianSyncSuccess('Sync started in background. Refresh to see updates.')
          setTimeout(() => setObsidianSyncSuccess(null), 10000)
          loadDocuments(false)
        }
      }, 300000)

    } catch (err) {
      setObsidianSyncError(err instanceof Error ? err.message : 'Sync failed')
      setObsidianSyncing(false)
      setObsidianSyncProgress(null)
    }
  }

  // Now use the functions in useEffect hooks
  useEffect(() => {
    loadDocuments()
    checkDriveStatus()
    checkNotionStatusFn()
    checkObsidianStatusFn()

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

  // Listen for messages from OAuth popup
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Accept messages from same origin or from backend (for OAuth callbacks)
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || ''
      const allowedOrigins = [window.location.origin, backendUrl, 'null'] // 'null' for about:blank popups
      if (!allowedOrigins.some(origin => event.origin === origin || event.origin.startsWith(origin))) {
        return
      }

      if (event.data.type === 'google_drive_connected') {
        setSyncSuccess('Google Drive connected successfully!')
        setDriveExpanded(true) // Auto-expand the Google Drive accordion
        checkDriveStatus()
        loadDocuments()
      } else if (event.data.type === 'google_drive_error') {
        setSyncError(event.data.message || 'Failed to connect Google Drive')
      } else if (event.data.type === 'notion_connected') {
        setNotionSyncSuccess('Notion connected successfully!')
        checkNotionStatusFn()
        loadDocuments()
        loadNotionPages()
      } else if (event.data.type === 'notion_error') {
        setNotionSyncError(event.data.message || 'Failed to connect Notion')
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)

    // Event listener setup - only needs to run once on mount, handler uses current state via closures
  }, [])

  // Listen for Notion OAuth completion (for when popup loses window.opener)
  useEffect(() => {
    const handleNotionOAuthComplete = () => {
      // Wait a moment for the backend to process
      setTimeout(async () => {
        try {
          const status = await getNotionStatus()

          if (status.connected) {
            setNotionSyncSuccess('Notion connected successfully!')
            setNotionStatus(status)  // IMPORTANT: Update the state
            loadDocuments()
            loadNotionPages()
          } else {
            logger.warn('Notion not connected yet, retrying in 2 seconds...')
            // Try again after a longer delay
            setTimeout(async () => {
              const retryStatus = await getNotionStatus()

              if (retryStatus.connected) {
                setNotionSyncSuccess('Notion connected successfully!')
                setNotionStatus(retryStatus)  // IMPORTANT: Update the state
                loadDocuments()
                loadNotionPages()
              } else {
                logger.error('Notion still not connected after retry')
                setNotionSyncError('Connection succeeded but unable to detect status. Please refresh the page.')
              }
            }, 2000)
          }
        } catch (err) {
          logger.error('Error checking Notion status after OAuth:', err)
          setNotionSyncError('Failed to verify connection. Please refresh the page.')
        }
      }, 1000)
    }

    window.addEventListener('notion-oauth-complete', handleNotionOAuthComplete)
    return () => window.removeEventListener('notion-oauth-complete', handleNotionOAuthComplete)

    // Custom event listener setup - only needs to run once on mount
  }, [])

  // Load Notion pages when connected and expanded
  useEffect(() => {
    if (notionStatus?.connected && _notionExpanded && notionPages.length === 0) {
      loadNotionPages()
    }

    // Only depend on connection status and expanded state - loadNotionPages is stable and notionPages is checked inline
  }, [notionStatus?.connected, _notionExpanded])

  // Check for OAuth callback
  useEffect(() => {
    const driveParam = searchParams?.get('google_drive')
    if (driveParam === 'connected') {
      // Check if this is a popup window (opened by window.open)
      if (window.opener) {
        // This is a popup - close it and notify parent
        try {
          window.opener.postMessage({ type: 'google_drive_connected' }, window.location.origin)
          window.close()
        } catch (e) {
          logger.error('Failed to close popup:', e)
        }
      } else {
        // This is the main window - show success message
        setSyncSuccess('Google Drive connected successfully!')
        checkDriveStatus()
        // Clear URL parameter
        window.history.replaceState({}, '', '/kb')
      }
    } else if (driveParam === 'error') {
      const message = searchParams?.get('message') || 'Failed to connect Google Drive'

      // Check if this is a popup window
      if (window.opener) {
        // Notify parent and close
        try {
          window.opener.postMessage({
            type: 'google_drive_error',
            message
          }, window.location.origin)
          window.close()
        } catch (e) {
          logger.error('Failed to close popup:', e)
        }
      } else {
        // Show error in main window
        setSyncError(message)
        window.history.replaceState({}, '', '/kb')
      }
    }

    // Check for Notion OAuth callback
    const notionParam = searchParams?.get('notion')
    if (notionParam === 'connected') {
      if (window.opener) {
        try {
          window.opener.postMessage({ type: 'notion_connected' }, window.location.origin)
          // Give parent time to receive message, then close
          setTimeout(() => window.close(), 100)
        } catch (e) {
          logger.error('Failed to communicate with parent window:', e)
          // Close anyway - parent will detect closure and check status
          window.close()
        }
      } else {
        // This is the main window (not a popup)
        setNotionSyncSuccess('Notion connected successfully!')
        checkNotionStatusFn()
        loadNotionPages()
        window.history.replaceState({}, '', '/kb')
      }
    } else if (notionParam === 'error') {
      const message = searchParams?.get('message') || 'Failed to connect Notion'
      if (window.opener) {
        try {
          window.opener.postMessage({
            type: 'notion_error',
            message
          }, window.location.origin)
          setTimeout(() => window.close(), 100)
        } catch (e) {
          logger.error('Failed to communicate with parent window:', e)
          window.close()
        }
      } else{
        setNotionSyncError(message)
        window.history.replaceState({}, '', '/kb')
      }
    }

    // OAuth redirect check - only needs to run once on mount to check URL params, uses searchParams from props
  }, [])

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

  async function handleSyncFrequencyChange(newFrequency: string) {
    try {
      setSyncError(null)

      const data = await apiPatch<{ sync_frequency: string; next_sync_scheduled: string | null }>('/api/google-drive/sync-settings', {
        sync_frequency: newFrequency,
        default_folder_id: driveStatus?.folder_id,
        default_folder_name: driveStatus?.folder_name
      })

      setSyncFrequency(data.sync_frequency)
      setNextSyncScheduled(data.next_sync_scheduled)
      setSyncSuccess('Sync settings updated successfully')
      setTimeout(() => setSyncSuccess(null), 3000)
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Failed to update settings')
    }
  }

  async function handleConnectDrive() {
    try {
      setSyncError(null)
      await connectGoogleDrive()

      // Poll for connection status as fallback (in case postMessage doesn't work)
      let attempts = 0
      const maxAttempts = 30 // 30 seconds max
      const pollInterval = setInterval(async () => {
        attempts++
        try {
          const status = await getGoogleDriveStatus()
          if (status.connected) {
            clearInterval(pollInterval)
            setSyncSuccess('Google Drive connected successfully!')
            setDriveExpanded(true)
            setDriveStatus(status)
            loadDocuments()
          }
        } catch {
          // Ignore errors during polling
        }
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval)
        }
      }, 1000)
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Failed to connect Google Drive')
    }
  }

  async function handleSync() {
    // Check if folder ID is empty - require it
    if (!selectedFolderId || selectedFolderId.trim() === '') {
      setSyncError('Please enter a Google Drive folder ID')
      return
    }

    // Proceed with sync
    await performSync()
  }

  async function performSync() {
    try {
      setSyncing(true)
      setSyncError(null)
      setSyncSuccess(null)

      // Pass folder ID and name (required)
      const result = await syncGoogleDrive(
        selectedFolderId,
        _selectedFolderName || null
      )

      // Sync now returns immediately with status "started"
      setSyncSuccess(
        'Sync started! Documents are being downloaded and will appear below with a "Processing" tag. The tag will disappear when each document is ready.'
      )

      // Immediately refresh document list to show any quick syncs
      loadDocuments()

      // Auto-hide success message after 10 seconds
      setTimeout(() => setSyncSuccess(null), 10000)
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  async function loadDriveFiles() {
    if (!selectedFolderId) return

    try {
      setDriveFilesLoading(true)
      setSyncError(null)
      const files = await listFolderFiles(selectedFolderId)
      setDriveFiles(files)
    } catch (err) {
      logger.error('Failed to load Google Drive files:', err)
      setSyncError(err instanceof Error ? err.message : 'Failed to load files')
      setDriveFiles([])
    } finally {
      setDriveFilesLoading(false)
    }
  }

  async function handleDriveFilesSync() {
    if (selectedDriveFileIds.size === 0) {
      setSyncError('Please select at least one file to sync')
      return
    }

    try {
      setSyncing(true)
      setSyncError(null)
      setSyncSuccess(null)

      const fileIdArray = Array.from(selectedDriveFileIds)

      await syncGoogleDriveFiles(fileIdArray)

      setSyncSuccess('File/folder sync started - Check the Documents section below for details')

      // Immediately refresh document list to show placeholder documents
      await loadDocuments(false)

      // Clear selection
      setSelectedDriveFileIds(new Set())

      setTimeout(() => setSyncSuccess(null), 10000)
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  async function handleSyncSingleFile(fileId: string) {
    try {
      setSyncing(true)
      setSyncError(null)
      setSyncSuccess(null)

      await syncGoogleDriveFiles([fileId])

      setSyncSuccess('File/folder sync started - Check the Documents section below for details')

      // Immediately refresh document list to show placeholder document
      await loadDocuments(false)

      // Clear the input field and reset file flag
      setSelectedFolderId('')
      setIsFileUrl(false)

      setTimeout(() => setSyncSuccess(null), 10000)
    } catch (err) {
      logger.error('Error syncing file:', err)
      setSyncError(err instanceof Error ? err.message : 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  function toggleDriveFileSelection(fileId: string) {
    setSelectedDriveFileIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(fileId)) {
        newSet.delete(fileId)
      } else {
        newSet.add(fileId)
      }
      return newSet
    })
  }

  function selectAllDriveFiles() {
    setSelectedDriveFileIds(new Set(driveFiles.map(f => f.id)))
  }

  function deselectAllDriveFiles() {
    setSelectedDriveFileIds(new Set())
  }

  function handleDisconnectClick() {
    setShowDisconnectModal(true)
  }

  async function handleDisconnectConfirm() {
    setShowDisconnectModal(false)

    try {
      setSyncError(null)
      await disconnectGoogleDrive()
      setSyncSuccess('Google Drive disconnected')
      await checkDriveStatus()

      setTimeout(() => setSyncSuccess(null), 3000)
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Failed to disconnect')
    }
  }

  // Notion handler functions
  async function handleConnectNotion() {
    try {
      setNotionSyncError(null)
      await connectNotion()
      // The OAuth flow will redirect back to this page
    } catch (err) {
      setNotionSyncError(err instanceof Error ? err.message : 'Failed to connect Notion')
    }
  }

  async function handleNotionSync() {
    if (selectedNotionPageIds.size === 0) {
      setNotionSyncError('Please select at least one page to sync')
      return
    }

    try {
      setNotionSyncing(true)
      setNotionSyncError(null)
      setNotionSyncSuccess(null)

      const pageIdArray = Array.from(selectedNotionPageIds)

      await syncNotion(pageIdArray)

      setNotionSyncSuccess(
        `Sync started for ${pageIdArray.length} page(s)! Pages are being downloaded and will appear below with a "Processing" tag. The tag will disappear when each page is ready.`
      )

      // Wait a moment for background task to create initial records, then refresh
      setTimeout(async () => {
        await loadDocuments(false)
      }, 1500)

      setTimeout(() => setNotionSyncSuccess(null), 10000)
    } catch (err) {
      setNotionSyncError(err instanceof Error ? err.message : 'Sync failed')
    } finally {
      setNotionSyncing(false)
    }
  }

  async function loadNotionPages() {
    try {
      setNotionPagesLoading(true)
      const response = await getNotionPages()
      setNotionPages(response.pages)
    } catch (err) {
      logger.error('Failed to load Notion pages:', err)
      setNotionSyncError(err instanceof Error ? err.message : 'Failed to load pages')
    } finally {
      setNotionPagesLoading(false)
    }
  }

  function toggleNotionPageSelection(pageId: string) {
    setSelectedNotionPageIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(pageId)) {
        newSet.delete(pageId)
      } else {
        newSet.add(pageId)
      }
      return newSet
    })
  }

  function selectAllNotionPages() {
    setSelectedNotionPageIds(new Set(notionPages.map(p => p.id)))
  }

  function deselectAllNotionPages() {
    setSelectedNotionPageIds(new Set())
  }

  function handleNotionDisconnectClick() {
    setShowNotionDisconnectModal(true)
  }

  async function handleNotionDisconnectConfirm() {
    setShowNotionDisconnectModal(false)

    try {
      setNotionSyncError(null)
      await disconnectNotion()
      setNotionSyncSuccess('Notion disconnected')
      await checkNotionStatusFn()

      setTimeout(() => setNotionSyncSuccess(null), 3000)
    } catch (err) {
      setNotionSyncError(err instanceof Error ? err.message : 'Failed to disconnect')
    }
  }

  async function handleNotionSyncFrequencyChange(newFrequency: string) {
    try {
      setNotionSyncError(null)

      const data = await apiPatch<{ sync_frequency: string; next_sync_scheduled: string | null }>('/api/notion/sync-settings', {
        sync_frequency: newFrequency
      })

      setNotionSyncFrequency(data.sync_frequency)
      setNotionNextSyncScheduled(data.next_sync_scheduled)
      setNotionSyncSuccess('Sync settings updated successfully')
      setTimeout(() => setNotionSyncSuccess(null), 3000)
    } catch (err) {
      setNotionSyncError(err instanceof Error ? err.message : 'Failed to update settings')
    }
  }

  // Load all agents (for agent assignment selector)
  async function loadAllAgents() {
    try {
      const data = await apiGet<{ agents: Agent[] }>('/api/agents?include_inactive=false')
      setAllAgents(data.agents || [])
    } catch (err) {
      logger.error('Failed to load agents:', err)
    }
  }

  // Load document's current agent assignments
  async function loadDocumentAgentAssignments(documentId: string) {
    try {
      setLoadingAgentAssignments(true)
      const data = await apiGet<{
        is_global: boolean
        linked_agents: Array<{ id: string; name: string; display_name: string }>
      }>(`/api/documents/${documentId}/agents`)

      setDocIsGlobal(data.is_global)
      setDocLinkedAgentIds(new Set(data.linked_agents.map(a => a.id)))
    } catch (err) {
      logger.error('Failed to load document agent assignments:', err)
      // Default to global if we can't load
      setDocIsGlobal(true)
      setDocLinkedAgentIds(new Set())
    } finally {
      setLoadingAgentAssignments(false)
    }
  }

  // Document action handlers
  async function handleDocumentInfo(doc: Document) {
    setSelectedDoc(doc)
    // Load actual sync cadence from document, default to 'manual'
    const currentCadence = doc.sync_cadence || 'manual'
    setDocSyncCadence(currentCadence)
    setTempSyncCadence(currentCadence)
    // Load original date (for meeting transcripts etc.)
    setTempOriginalDate(doc.original_date || '')
    setShowInfoModal(true)

    // Load agents list if not already loaded
    if (allAgents.length === 0) {
      loadAllAgents()
    }

    // Load this document's agent assignments
    loadDocumentAgentAssignments(doc.id)
  }

  function toggleDocAgentSelection(agentId: string) {
    setDocLinkedAgentIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(agentId)) {
        newSet.delete(agentId)
      } else {
        newSet.add(agentId)
      }
      return newSet
    })
  }

  async function handleSaveDocumentInfo() {
    if (!selectedDoc) return

    try {
      let hasChanges = false

      // Save sync cadence if changed
      if (tempSyncCadence !== docSyncCadence) {
        await apiPatch(`/api/documents/${selectedDoc.id}/sync-cadence`, {
          sync_cadence: tempSyncCadence
        })

        setDocSyncCadence(tempSyncCadence)
        setDocuments(prevDocs =>
          prevDocs.map(doc =>
            doc.id === selectedDoc.id
              ? { ...doc, sync_cadence: tempSyncCadence }
              : doc
          )
        )
        hasChanges = true
      }

      // Save original date if changed
      const currentOriginalDate = selectedDoc.original_date || ''
      if (tempOriginalDate !== currentOriginalDate) {
        await apiPatch(`/api/documents/${selectedDoc.id}/original-date`, {
          original_date: tempOriginalDate || null
        })

        setDocuments(prevDocs =>
          prevDocs.map(doc =>
            doc.id === selectedDoc.id
              ? { ...doc, original_date: tempOriginalDate || undefined }
              : doc
          )
        )
        hasChanges = true
      }

      // Save agent assignments
      setSavingAgentAssignments(true)
      const newAgentIds = docIsGlobal ? [] : Array.from(docLinkedAgentIds)

      await apiPut(`/api/documents/${selectedDoc.id}/agents`, {
        agent_ids: newAgentIds
      })
      hasChanges = true

      if (hasChanges) {
        const agentMsg = docIsGlobal
          ? 'Available to all agents'
          : `Linked to ${newAgentIds.length} agent(s)`
        setGeneralSuccess(`Document updated: ${agentMsg}`)
        setTimeout(() => setGeneralSuccess(null), 3000)
      }

      setShowInfoModal(false)
    } catch (err) {
      setGeneralError(err instanceof Error ? err.message : 'Failed to update document')
      setTimeout(() => setGeneralError(null), 3000)
    } finally {
      setSavingAgentAssignments(false)
    }
  }

  // Tag management functions
  async function handleAddTag() {
    if (!selectedDoc || !newTagInput.trim()) return

    const tag = newTagInput.trim()
    if (tag.length > 100) {
      setGeneralError('Tag must be 100 characters or less')
      setTimeout(() => setGeneralError(null), 3000)
      return
    }

    setAddingTag(true)
    try {
      await apiPost(`/api/documents/${selectedDoc.id}/tags`, { tag })

      // Update local state
      const newTag: DocumentTag = { tag, source: 'manual' }
      setSelectedDoc(prev => prev ? {
        ...prev,
        tags: [...(prev.tags || []), newTag]
      } : prev)

      // Update in documents list
      setDocuments(prevDocs =>
        prevDocs.map(doc =>
          doc.id === selectedDoc.id
            ? { ...doc, tags: [...(doc.tags || []), newTag] }
            : doc
        )
      )

      setNewTagInput('')
    } catch (err) {
      setGeneralError(err instanceof Error ? err.message : 'Failed to add tag')
      setTimeout(() => setGeneralError(null), 3000)
    } finally {
      setAddingTag(false)
    }
  }

  async function handleRemoveTag(tag: string) {
    if (!selectedDoc) return

    setRemovingTag(tag)
    try {
      await apiDelete(`/api/documents/${selectedDoc.id}/tags/${encodeURIComponent(tag)}`)

      // Update local state
      setSelectedDoc(prev => prev ? {
        ...prev,
        tags: (prev.tags || []).filter(t => t.tag !== tag)
      } : prev)

      // Update in documents list
      setDocuments(prevDocs =>
        prevDocs.map(doc =>
          doc.id === selectedDoc.id
            ? { ...doc, tags: (doc.tags || []).filter(t => t.tag !== tag) }
            : doc
        )
      )
    } catch (err) {
      setGeneralError(err instanceof Error ? err.message : 'Failed to remove tag')
      setTimeout(() => setGeneralError(null), 3000)
    } finally {
      setRemovingTag(null)
    }
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

  async function handleDocumentSync(doc: Document) {
    if (!doc.google_drive_file_id) {
      setSyncError('Only Google Drive documents can be synced')
      setTimeout(() => setSyncError(null), 3000)
      return
    }

    setSyncingDocId(doc.id)

    try {
      // Trigger re-sync of the specific document
      await apiPost(`/api/google-drive/sync-document/${doc.google_drive_file_id}`)
      setSyncSuccess(`Syncing ${doc.filename}...`)
      setTimeout(() => {
        setSyncSuccess(null)
        handleDocumentsChange()
      }, 2000)
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Failed to sync document')
    } finally {
      setSyncingDocId(null)
    }
  }

  return (
    <div>
      {/* Storage Indicator */}
      <div className="mb-4">
        <StorageIndicator
          apiBaseUrl={API_BASE_URL}
          refreshTrigger={storageRefreshTrigger}
          onStorageUpdate={(data) => {
            // Optional: Can add logic here if needed when storage updates
          }}
        />
      </div>

      {/* Classification Review Banner */}
      <ClassificationReviewBanner
        onReviewComplete={handleDocumentsChange}
        refreshTrigger={storageRefreshTrigger}
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

      {/* Tag Manager Tab Content */}
      {activeTab === 'tags' && (
        <TagManagerTab onDocumentsChange={handleDocumentsChange} />
      )}

      {/* Documents Tab Content */}
      {activeTab === 'documents' && (
      <>
      {/* Google Drive Integration Section */}
      <div className={`card mb-3 ${driveExpanded && driveStatus?.connected ? 'p-6' : 'p-2'}`}>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <button
              onClick={() => setDriveExpanded(!driveExpanded)}
              className="text-secondary hover:text-primary transition-colors"
            >
              {driveExpanded ? (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
            <h3 className="heading-3">Drive</h3>
          </div>
          {driveStatus && !driveStatus.connected && driveExpanded && (
            <button
              onClick={handleConnectDrive}
              className="btn-primary"
            >
              Connect Google Drive
            </button>
          )}
        </div>

        {driveExpanded && driveStatus?.connected && (
          <>
            <div className="mt-4 space-y-3">
              {/* Status and Actions */}
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm">
                  <div className="text-green-600 font-medium">Connected</div>
                  <div className="text-xs text-muted">
                    {driveStatus.document_count} documents - Last sync: {formatLastSync(driveStatus.last_sync)}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleDisconnectClick}
                    className="btn-secondary text-red-600 hover:bg-red-50"
                  >
                    Disconnect
                  </button>
                </div>
              </div>

              {/* File Selection */}
              <div className="bg-gray-50 dark:bg-gray-800 border border-default rounded-lg p-3">
                <label className="block text-sm font-medium text-secondary mb-2">
                  Select files from Google Drive
                </label>

                {/* Google Drive Picker Button */}
                <div className="flex gap-2 mb-3">
                  <GoogleDrivePicker
                    disabled={syncing}
                    buttonText="Browse Google Drive"
                    buttonClassName="btn-primary flex-1"
                    onFilesPicked={(files) => {
                      // Convert picker files to our format and add to selection
                      const newFiles: GoogleDriveFile[] = files.map(f => ({
                        id: f.id,
                        name: f.name,
                        mimeType: f.mimeType,
                        iconLink: f.iconUrl
                      }))
                      setDriveFiles(newFiles)
                      setSelectedDriveFileIds(new Set(files.map(f => f.id)))
                      setSelectedFolderId('') // Clear any manual URL input
                      setIsFileUrl(false)
                    }}
                  />
                </div>

                {/* File Picker */}
                {driveFilesLoading ? (
                  <div className="text-sm text-muted py-4 text-center">
                    Loading files...
                  </div>
                ) : driveFiles.length > 0 ? (
                  <>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium text-secondary">
                        Select Files to Sync
                      </label>
                      <div className="flex gap-2">
                        <button
                          onClick={selectAllDriveFiles}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          Select All
                        </button>
                        <button
                          onClick={deselectAllDriveFiles}
                          className="text-xs text-gray-600 hover:text-gray-800"
                        >
                          Deselect All
                        </button>
                      </div>
                    </div>

                    <div className="max-h-64 overflow-y-auto space-y-2 bg-white dark:bg-gray-900 rounded p-2">
                      {driveFiles.map(file => (
                        <label
                          key={file.id}
                          className="flex items-start gap-2 p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedDriveFileIds.has(file.id)}
                            onChange={() => toggleDriveFileSelection(file.id)}
                            className="mt-0.5"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-primary truncate">
                              {file.name}
                            </div>
                            <div className="text-xs text-muted">
                              {file.mimeType?.split('/').pop() || 'Unknown type'}
                              {file.size && ` - ${Math.round(parseInt(file.size) / 1024)} KB`}
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>

                    {selectedDriveFileIds.size > 0 && (
                      <div className="mt-3 flex items-center justify-between">
                        <div className="text-xs text-muted">
                          {selectedDriveFileIds.size} file{selectedDriveFileIds.size === 1 ? '' : 's'} selected
                        </div>
                        <button
                          onClick={handleDriveFilesSync}
                          disabled={syncing}
                          className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {syncing ? 'Syncing...' : 'Sync Selected'}
                        </button>
                      </div>
                    )}
                  </>
                ) : selectedFolderId && !isFileUrl && !driveFilesLoading ? (
                  <div className="text-sm text-muted py-4 text-center">
                    Click &quot;Load Files&quot; to see files in this folder
                  </div>
                ) : null}
              </div>
            </div>

        {/* Sync Frequency Settings */}
        <div className="mt-4 border-t border-default pt-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-secondary">
                Automatic Sync:
              </label>
              <select
                value={syncFrequency}
                onChange={(e) => handleSyncFrequencyChange(e.target.value)}
                className="px-3 py-1.5 border border-default rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-card text-primary"
              >
                <option value="manual">Manual Only</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
              {nextSyncScheduled && syncFrequency !== 'manual' && (
                <span className="text-xs text-muted">
                  Next sync: {new Date(nextSyncScheduled).toLocaleString()}
                </span>
              )}
            </div>
          </div>

        {/* Success Message */}
        {syncSuccess && (
          <div className="mt-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-green-800 dark:text-green-200">{syncSuccess}</span>
            </div>
          </div>
        )}

        {/* Error Message */}
        {syncError && (
          <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <span className="text-red-600 dark:text-red-400 font-bold">Error:</span>
              <span className="text-sm text-red-800 dark:text-red-200">{syncError}</span>
            </div>
          </div>
        )}

        {/* Syncing Progress */}
        {syncing && (
          <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <LoadingSpinner size="sm" />
              <span className="text-sm text-blue-800 dark:text-blue-200">Syncing documents from Google Drive...</span>
            </div>
          </div>
        )}
        </>
        )}
      </div>

      {/* Obsidian Vault Section */}
      <div className={`card mb-3 ${obsidianExpanded && obsidianStatus?.connected ? 'p-6' : 'p-2'}`}>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <button
              onClick={() => setObsidianExpanded(!obsidianExpanded)}
              className="text-secondary hover:text-primary transition-colors"
            >
              {obsidianExpanded ? (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
            <h3 className="heading-3">Obsidian</h3>
          </div>
          {obsidianStatus && !obsidianStatus.connected && obsidianExpanded && (
            <span className="text-sm text-muted">Not configured - run watcher script to connect</span>
          )}
        </div>

        {obsidianExpanded && obsidianStatus?.connected && (
          <>
            <div className="mt-4 space-y-3">
              {/* Status and Actions */}
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm">
                  <div className="text-purple-600 font-medium flex items-center gap-2">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                    {obsidianStatus.vault_name || 'Connected'}
                  </div>
                  <div className="text-xs text-muted mt-1">
                    {obsidianStatus.document_count ?? 0} documents synced
                    {(obsidianStatus.pending_changes ?? 0) > 0 && (
                      <span className="text-amber-600 dark:text-amber-400 ml-1">
                        ({obsidianStatus.pending_changes} pending)
                      </span>
                    )}
                    {obsidianStatus.last_sync && (
                      <> - Last sync: {formatLastSync(obsidianStatus.last_sync)}</>
                    )}
                  </div>
                  {obsidianStatus.vault_path && (
                    <div className="text-xs text-muted font-mono truncate max-w-md" title={obsidianStatus.vault_path}>
                      {obsidianStatus.vault_path}
                    </div>
                  )}
                </div>
                <button
                  onClick={handleObsidianFullSync}
                  disabled={obsidianSyncing}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {obsidianSyncing ? 'Syncing...' : 'Full Resync'}
                </button>
              </div>
            </div>

            {/* Success Message */}
            {obsidianSyncSuccess && (
              <div className="mt-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-green-800 dark:text-green-200">{obsidianSyncSuccess}</span>
                </div>
              </div>
            )}

            {/* Error Message */}
            {obsidianSyncError && (
              <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <span className="text-red-600 dark:text-red-400 font-bold">Error:</span>
                  <span className="text-sm text-red-800 dark:text-red-200">{obsidianSyncError}</span>
                </div>
              </div>
            )}

            {/* Syncing Progress */}
            {obsidianSyncing && (
              <div className="mt-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2">
                  <LoadingSpinner size="sm" />
                  <span className="text-sm text-purple-800 dark:text-purple-200">
                    {obsidianSyncProgress
                      ? `Syncing... ${obsidianSyncProgress.synced} of ${obsidianSyncProgress.total} files`
                      : 'Starting sync...'}
                  </span>
                </div>
                {obsidianSyncProgress && obsidianSyncProgress.total > 0 && (
                  <div className="w-full bg-purple-200 dark:bg-purple-900 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${Math.round((obsidianSyncProgress.synced / obsidianSyncProgress.total) * 100)}%` }}
                    />
                  </div>
                )}
              </div>
            )}

            {/* Vault Folder Structure */}
            {Object.keys(obsidianFolders).length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-secondary mb-2">Vault Structure</h4>
                <div className="space-y-1">
                  {Object.entries(obsidianFolders).map(([folder, docs]) => (
                    <div key={folder}>
                      {/* Folder header */}
                      <button
                        onClick={() => toggleFolderCollapse(folder)}
                        className="w-full flex items-center gap-2 px-2 py-1.5 text-sm font-medium text-primary hover:bg-hover rounded transition-colors"
                      >
                        <svg className={`w-4 h-4 text-secondary transition-transform ${collapsedFolders.has(folder) ? '' : 'rotate-90'}`} fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                        <svg className="w-4 h-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h6a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clipRule="evenodd" />
                        </svg>
                        <span>{folder}</span>
                        <span className="text-xs text-muted ml-auto">{docs.length}</span>
                      </button>

                      {/* Folder contents */}
                      {!collapsedFolders.has(folder) && (
                        <div className="ml-6 space-y-0.5 mt-0.5">
                          {docs.map((doc) => (
                            <div
                              key={doc.id}
                              onClick={() => handleDocumentInfo(doc)}
                              className="flex items-center gap-2 px-2 py-1 text-sm text-secondary hover:text-primary hover:bg-hover rounded cursor-pointer transition-colors"
                            >
                              <svg className="w-3.5 h-3.5 text-purple-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                              <span className="truncate">{doc.filename}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

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
            <h3 className="heading-3">Uploads</h3>
          </div>
        </div>

        {uploadExpanded && (
          <div className="mt-4">
            {profile?.client_id ? (
              <DocumentUpload
                clientId={profile.client_id}
                apiBaseUrl={API_BASE_URL}
                onUploadComplete={handleDocumentsChange}
                showAgentSelector={true}
              />
            ) : (
              <p className="text-secondary">Loading...</p>
            )}

            {/* Uploaded files list */}
            {uploadedDocuments.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-secondary mb-2">Uploaded Files ({uploadedDocuments.length})</h4>
                <div className="space-y-1">
                  {uploadedDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      onClick={() => handleDocumentInfo(doc)}
                      className="flex items-center justify-between gap-2 px-2 py-1.5 text-sm text-secondary hover:text-primary hover:bg-hover rounded cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <svg className="w-4 h-4 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span className="truncate">{doc.filename}</span>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeleteClick(doc); }}
                        disabled={deletingDocId === doc.id}
                        className="p-1 text-gray-400 hover:text-red-500 rounded transition-colors flex-shrink-0"
                        title="Delete"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
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
            <h2 className="heading-3">KB Navigator</h2>
            <span className="text-sm text-muted">
              {searchQuery || sourceFilter !== 'all' || selectedTags.size > 0
                ? `(${filteredDocuments.length} of ${documents.length})`
                : `(${documents.length})`}
            </span>
          </div>
        </div>

        {documentsExpanded && (
          <div className="mt-4">

          {/* General Document Notifications */}
          {generalSuccess && (
            <div className="mb-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
              <div className="flex items-center gap-2">
                  <span className="text-sm text-green-800 dark:text-green-200">{generalSuccess}</span>
              </div>
            </div>
          )}

          {generalError && (
            <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <span className="text-red-600 dark:text-red-400 font-bold">Error:</span>
                <span className="text-sm text-red-800 dark:text-red-200">{generalError}</span>
              </div>
            </div>
          )}

          {/* Search and Filter Bar */}
          {documents.length > 0 && (
            <div className="mb-4 flex flex-col sm:flex-row gap-3">
              {/* Search Input */}
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

              {/* Source Filter */}
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="px-3 py-2 border border-default rounded-lg text-sm bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Sources</option>
                <option value="google_drive">Google Drive</option>
                <option value="obsidian">Obsidian</option>
                <option value="upload">Uploads</option>
              </select>

              {/* Tag Filter Dropdown */}
              <select
                value={selectedTags.size === 1 ? Array.from(selectedTags)[0] : ''}
                onChange={(e) => {
                  const tag = e.target.value
                  if (tag === '') {
                    setSelectedTags(new Set())
                  } else {
                    setSelectedTags(new Set([tag]))
                  }
                }}
                className="px-3 py-2 border border-default rounded-lg text-sm bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Tags{allTags.length > 0 ? ` (${allTags.length})` : ''}</option>
                {allTags.slice(0, 50).map(tag => (
                  <option key={tag} value={tag}>{tag}</option>
                ))}
              </select>
            </div>
          )}

          {loading ? (
            <div className="text-center py-8 text-muted">
              <LoadingSpinner size="md" />
              <p className="mt-2">Loading documents...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 p-4 rounded-lg text-sm">
              Error: {error}
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-8 text-muted">
              <p>No documents uploaded yet</p>
              <p className="text-sm mt-2">Upload your first document or connect Google Drive to get started!</p>
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-8 text-muted">
              <p>No documents match your search</p>
              <button
                onClick={() => { setSearchQuery(''); setSourceFilter('all'); setSelectedTags(new Set()); }}
                className="text-sm text-blue-600 hover:underline mt-2"
              >
                Clear filters
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Show sync progress indicators */}
              {syncing && (
                <div className="border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <LoadingSpinner size="sm" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">Syncing from Google Drive:</p>
                      <div className="space-y-1">
                        {documents.filter(doc => !doc.processed && doc.source_platform === 'google_drive').map(doc => (
                          <div key={doc.id} className="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-200">
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200">
                              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              Processing
                            </span>
                            <span className="truncate">{doc.filename}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {notionSyncing && (
                <div className="border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <LoadingSpinner size="sm" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Syncing from Notion:</p>
                      <div className="space-y-1">
                        {documents.filter(doc => !doc.processed && doc.source_platform === 'notion').map(doc => (
                          <div key={doc.id} className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200">
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200">
                              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              Processing
                            </span>
                            <span className="truncate">{doc.filename}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* All documents - flat list */}
              {filteredDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="border rounded-lg p-2 transition-colors border-default hover:bg-hover"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-2 mb-1">
                        <h3 className="font-medium text-primary break-words">{doc.filename}</h3>
                        {/* Status Badges */}
                        {!doc.processed && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200 flex-shrink-0" title="Document is being processed">
                            <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Processing
                          </span>
                        )}
                        {doc.processed && doc.processing_status === 'failed' && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-200 flex-shrink-0" title={`Processing failed: ${doc.processing_error || 'Unknown error'}`}>
                            Failed
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {/* Action Buttons */}
                      <div className="flex items-center gap-1">
                        {/* Sync Button - only for Google Drive docs */}
                        {doc.source_platform === 'google_drive' && (
                          <button
                            onClick={() => handleDocumentSync(doc)}
                            disabled={syncingDocId === doc.id}
                            className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Sync this document from Google Drive"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                          </button>
                        )}

                        {/* Info Button */}
                        <button
                          onClick={() => handleDocumentInfo(doc)}
                          className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                          title="Document info"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </button>

                        {/* Delete Button */}
                        <button
                          onClick={() => handleDeleteClick(doc)}
                          disabled={deletingDocId === doc.id}
                          className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Delete document"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
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
      </>
      )}

      {/* Disconnect Confirmation Modal */}
      <ConfirmModal
        open={showDisconnectModal}
        title="Disconnect Google Drive"
        message="Are you sure you want to disconnect Google Drive? Synced documents will remain in your knowledge base."
        confirmText="Disconnect"
        cancelText="Cancel"
        confirmVariant="danger"
        onConfirm={handleDisconnectConfirm}
        onCancel={() => setShowDisconnectModal(false)}
      />

      {/* Notion Disconnect Confirmation Modal */}
      <ConfirmModal
        open={showNotionDisconnectModal}
        title="Disconnect Notion"
        message="Are you sure you want to disconnect Notion? Synced pages will remain in your knowledge base."
        confirmText="Disconnect"
        cancelText="Cancel"
        confirmVariant="danger"
        onConfirm={handleNotionDisconnectConfirm}
        onCancel={() => setShowNotionDisconnectModal(false)}
      />

      {/* Delete Confirmation Modal with Initiative Warnings */}
      <DeleteDocumentModal
        isOpen={showDeleteModal}
        documentId={docToDelete?.id || null}
        documentName={docToDelete?.filename || ''}
        onClose={() => {
          setShowDeleteModal(false)
          setDocToDelete(null)
        }}
        onDeleted={() => {
          handleDocumentsChange()
          setStorageRefreshTrigger(prev => prev + 1)
        }}
      />

      {/* Document Info Modal */}
      {showInfoModal && selectedDoc && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowInfoModal(false)}>
          <div className="bg-card rounded-lg shadow-xl max-w-lg w-full mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="heading-3">Document Information</h3>
              <button
                onClick={() => setShowInfoModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
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
                  {selectedDoc.source_platform === 'google_drive' ? 'Google Drive' : selectedDoc.source_platform === 'notion' ? 'Notion' : 'Direct Upload'}
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-secondary">Uploaded</label>
                <p className="text-sm text-primary mt-1">{formatDate(selectedDoc.uploaded_at)}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-secondary">Original Document Date</label>
                <p className="text-xs text-muted mb-1">For meeting transcripts, enter the actual meeting date</p>
                <input
                  type="date"
                  value={tempOriginalDate}
                  onChange={(e) => setTempOriginalDate(e.target.value)}
                  className="w-full px-3 py-1.5 text-sm border border-default rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-card text-primary"
                />
                {tempOriginalDate && (
                  <button
                    type="button"
                    onClick={() => setTempOriginalDate('')}
                    className="mt-1 text-xs text-muted hover:text-primary"
                  >
                    Clear date
                  </button>
                )}
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
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline mt-1 inline-block"
                  >
                    View in Google Drive
                  </a>
                </div>
              )}

              {/* Obsidian file path */}
              {selectedDoc.obsidian_file_path && (
                <div>
                  <label className="text-sm font-medium text-secondary">Vault Path</label>
                  <p className="text-sm text-primary mt-1 font-mono">{selectedDoc.obsidian_file_path}</p>
                </div>
              )}

              {/* Tags Section */}
              <div className="border-t border-default pt-3 mt-3">
                <label className="text-sm font-medium text-secondary block mb-2">Tags</label>

                {/* Existing tags */}
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {(selectedDoc.tags || []).length === 0 ? (
                    <span className="text-sm text-muted">No tags</span>
                  ) : (
                    selectedDoc.tags?.map((t) => (
                      <span
                        key={t.tag}
                        className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded ${
                          t.source === 'path'
                            ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                            : t.source === 'frontmatter'
                              ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                              : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                        }`}
                      >
                        {t.tag}
                        {t.source === 'path' || t.source === 'frontmatter' ? (
                          <span title={t.source === 'path' ? 'From folder path (read-only)' : 'From Obsidian frontmatter (read-only)'}>
                            <svg className="w-3 h-3 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                            </svg>
                          </span>
                        ) : (
                          <button
                            onClick={() => handleRemoveTag(t.tag)}
                            disabled={removingTag === t.tag}
                            className="hover:text-red-600 dark:hover:text-red-400 transition-colors disabled:opacity-50"
                            title="Remove tag"
                          >
                            {removingTag === t.tag ? (
                              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                            ) : (
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            )}
                          </button>
                        )}
                      </span>
                    ))
                  )}
                </div>

                {/* Add new tag */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => setNewTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleAddTag()
                      }
                    }}
                    placeholder="Add a tag..."
                    className="flex-1 px-3 py-1.5 text-sm border border-default rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-card text-primary"
                    maxLength={100}
                  />
                  <button
                    onClick={handleAddTag}
                    disabled={addingTag || !newTagInput.trim()}
                    className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {addingTag ? 'Adding...' : 'Add'}
                  </button>
                </div>
                <p className="text-xs text-muted mt-1">
                  Amber tags are from folder path. Purple tags are from frontmatter. Blue tags are manually added.
                </p>
              </div>

              {/* Sync Cadence Setting - for Google Drive and Notion documents */}
              {(selectedDoc.source_platform === 'google_drive' || selectedDoc.source_platform === 'notion') && (
                <div className="border-t border-default pt-3 mt-3">
                  <label className="text-sm font-medium text-secondary block mb-2">
                    Automatic Sync Cadence
                  </label>
                  <select
                    value={tempSyncCadence}
                    onChange={(e) => setTempSyncCadence(e.target.value)}
                    className="w-full px-3 py-2 border border-default rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-card text-primary"
                  >
                    <option value="manual">Manual Only</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                  <p className="text-xs text-muted mt-1">
                    Set how often this document should automatically sync from {selectedDoc.source_platform === 'google_drive' ? 'Google Drive' : 'Notion'}
                  </p>
                </div>
              )}

              {/* Agent Assignment Section */}
              <div className="border-t border-default pt-3 mt-3">
                <label className="text-sm font-medium text-secondary block mb-2">
                  Agent Visibility
                </label>

                {loadingAgentAssignments ? (
                  <div className="flex items-center gap-2 text-sm text-muted py-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    Loading...
                  </div>
                ) : (
                  <>
                    {/* Global vs Agent-specific toggle */}
                    <div className="flex gap-4 mb-3">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="docScope"
                          checked={docIsGlobal}
                          onChange={() => setDocIsGlobal(true)}
                          className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-primary">Global (all agents)</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="docScope"
                          checked={!docIsGlobal}
                          onChange={() => setDocIsGlobal(false)}
                          className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-primary">Agent-specific</span>
                      </label>
                    </div>

                    {/* Agent selection grid (only shown when agent-specific is selected) */}
                    {!docIsGlobal && (
                      <div className="mt-2">
                        <p className="text-xs text-muted mb-2">Select which agents can access this document:</p>
                        {allAgents.length === 0 ? (
                          <p className="text-sm text-muted">Loading agents...</p>
                        ) : (
                          <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                            {allAgents.map(agent => (
                              <label
                                key={agent.id}
                                className={`flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors ${
                                  docLinkedAgentIds.has(agent.id)
                                    ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500'
                                    : 'bg-gray-50 dark:bg-gray-800 border-default hover:border-blue-300'
                                }`}
                              >
                                <input
                                  type="checkbox"
                                  checked={docLinkedAgentIds.has(agent.id)}
                                  onChange={() => toggleDocAgentSelection(agent.id)}
                                  className="w-4 h-4 text-blue-600 focus:ring-blue-500 rounded"
                                />
                                <span className="text-sm text-primary truncate">{agent.display_name}</span>
                              </label>
                            ))}
                          </div>
                        )}
                        {!docIsGlobal && docLinkedAgentIds.size === 0 && allAgents.length > 0 && (
                          <p className="text-xs text-amber-600 mt-2">
                            Select at least one agent, or choose &quot;Global&quot; to make available to all.
                          </p>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setShowInfoModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveDocumentInfo}
                disabled={savingAgentAssignments || (!docIsGlobal && docLinkedAgentIds.size === 0)}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {savingAgentAssignments ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
