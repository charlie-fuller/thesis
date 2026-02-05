'use client'

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import DocumentUpload from '@/components/DocumentUpload'
import LoadingSpinner from '@/components/LoadingSpinner'
import GoogleDrivePicker from '@/components/GoogleDrivePicker'
import { logger } from '@/lib/logger'
import {
  getGoogleDriveStatus,
  connectGoogleDrive,
  syncGoogleDriveFiles,
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
import { apiGet, apiPatch, apiPost } from '@/lib/api'
import { API_BASE_URL } from '@/lib/config'
import ConfirmModal from '@/components/ConfirmModal'

interface ObsidianStatus {
  connected: boolean
  vault_name?: string
  vault_path?: string
  document_count?: number
  last_sync?: string
  pending_changes?: number
  total_files?: number
  unsynced_count?: number
}

interface RecentFile {
  file_path: string
  document_id: string
  last_synced_at: string
  original_date?: string
}

interface KBSyncSettingsModalProps {
  isOpen: boolean
  onClose: () => void
  onDocumentsChange: () => void
}

export default function KBSyncSettingsModal({
  isOpen,
  onClose,
  onDocumentsChange
}: KBSyncSettingsModalProps) {
  const { profile } = useAuth()
  const [activeTab, setActiveTab] = useState<'vault' | 'drive' | 'notion' | 'uploads'>('vault')

  // --- Obsidian state ---
  const [obsidianStatus, setObsidianStatus] = useState<ObsidianStatus | null>(null)
  const [obsidianSyncing, setObsidianSyncing] = useState(false)
  const [obsidianSyncError, setObsidianSyncError] = useState<string | null>(null)
  const [obsidianSyncSuccess, setObsidianSyncSuccess] = useState<string | null>(null)
  const [obsidianSyncProgress, setObsidianSyncProgress] = useState<{
    synced: number
    total: number
    current_file?: string
    stage?: string
  } | null>(null)
  const [syncingRecent, setSyncingRecent] = useState(false)
  const [checkingStatus, setCheckingStatus] = useState(false)
  const [pendingFiles, setPendingFiles] = useState<{pending: Array<{file_path: string, sync_status: string, sync_error?: string}>, failed: Array<{file_path: string, sync_status: string, sync_error?: string}>} | null>(null)
  const [showPendingDetails, setShowPendingDetails] = useState(false)

  // --- Google Drive state ---
  const [driveStatus, setDriveStatus] = useState<GoogleDriveStatus | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [syncSuccess, setSyncSuccess] = useState<string | null>(null)
  const [syncFrequency, setSyncFrequency] = useState<string>('manual')
  const [nextSyncScheduled, setNextSyncScheduled] = useState<string | null>(null)
  const [driveFiles, setDriveFiles] = useState<GoogleDriveFile[]>([])
  const [driveFilesLoading, setDriveFilesLoading] = useState(false)
  const [selectedDriveFileIds, setSelectedDriveFileIds] = useState<Set<string>>(new Set())
  const [showDisconnectModal, setShowDisconnectModal] = useState(false)

  // --- Notion state ---
  const [notionStatus, setNotionStatus] = useState<NotionStatus | null>(null)
  const [notionSyncing, setNotionSyncing] = useState(false)
  const [notionSyncError, setNotionSyncError] = useState<string | null>(null)
  const [notionSyncSuccess, setNotionSyncSuccess] = useState<string | null>(null)
  const [notionPages, setNotionPages] = useState<NotionPage[]>([])
  const [notionPagesLoading, setNotionPagesLoading] = useState(false)
  const [selectedNotionPageIds, setSelectedNotionPageIds] = useState<Set<string>>(new Set())
  const [showNotionDisconnectModal, setShowNotionDisconnectModal] = useState(false)

  // --- Obsidian handlers ---
  const checkObsidianStatusFn = useCallback(async () => {
    try {
      const response = await apiGet<{
        success: boolean
        connected: boolean
        vault_name?: string
        vault_path?: string
        files_synced?: number
        pending_changes?: number
        unsynced_count?: number
        last_sync?: string
        sync_progress?: {
          is_syncing: boolean
          total_files: number
          files_processed: number
          current_file?: string
          stage?: string
        } | null
      }>('/api/obsidian/status')
      setObsidianStatus({
        connected: response.connected,
        vault_name: response.vault_name,
        vault_path: response.vault_path,
        document_count: response.files_synced,
        pending_changes: response.pending_changes,
        unsynced_count: response.unsynced_count,
        last_sync: response.last_sync
      })
      return response
    } catch (err) {
      logger.error('Error checking Obsidian status:', err)
      setObsidianStatus({ connected: false })
      return null
    }
  }, [])

  async function fetchPendingFiles() {
    try {
      const response = await apiGet<{
        success: boolean
        pending: Array<{file_path: string, sync_status: string, sync_error?: string}>
        failed: Array<{file_path: string, sync_status: string, sync_error?: string}>
        pending_count: number
        failed_count: number
      }>('/api/obsidian/files/pending')
      if (response) {
        setPendingFiles({pending: response.pending, failed: response.failed})
      }
    } catch (err) {
      logger.error('Error fetching pending files:', err)
    }
  }

  async function handleCheckForUpdates() {
    try {
      setCheckingStatus(true)
      await checkObsidianStatusFn()
    } finally {
      setCheckingStatus(false)
    }
  }

  async function handleSyncRecent() {
    try {
      setSyncingRecent(true)
      setObsidianSyncError(null)
      setObsidianSyncSuccess(null)

      await apiPost('/api/obsidian/sync/recent')

      const pollInterval = setInterval(async () => {
        const status = await checkObsidianStatusFn()
        if (status?.sync_progress?.is_syncing) {
          setObsidianSyncProgress({
            synced: status.sync_progress.files_processed,
            total: status.sync_progress.total_files,
            current_file: status.sync_progress.current_file,
            stage: status.sync_progress.stage
          })
        } else {
          clearInterval(pollInterval)
          setSyncingRecent(false)
          setObsidianSyncProgress(null)
          setObsidianSyncSuccess('Recent files synced successfully!')
          onDocumentsChange()
          setTimeout(() => setObsidianSyncSuccess(null), 5000)
        }
      }, 1000)
    } catch (err) {
      logger.error('Error syncing recent files:', err)
      setSyncingRecent(false)
      setObsidianSyncError(err instanceof Error ? err.message : 'Failed to sync recent files')
    }
  }

  async function handleObsidianFullSync() {
    try {
      setObsidianSyncing(true)
      setObsidianSyncError(null)
      setObsidianSyncSuccess(null)
      setObsidianSyncProgress(null)

      await apiPost<{ success: boolean; message: string }>('/api/obsidian/sync/full')

      let seenSyncing = false
      const pollInterval = setInterval(async () => {
        const status = await checkObsidianStatusFn()
        if (status) {
          const progress = status.sync_progress
          if (progress && progress.is_syncing) {
            seenSyncing = true
            setObsidianSyncProgress({
              synced: progress.files_processed,
              total: progress.total_files,
              current_file: progress.current_file,
              stage: progress.stage
            })
          } else if (seenSyncing && (!progress || !progress.is_syncing)) {
            clearInterval(pollInterval)
            setObsidianSyncing(false)
            setObsidianSyncProgress(null)
            const synced = status.files_synced ?? 0
            setObsidianSyncSuccess(`Sync complete! ${synced} documents synced.`)
            setTimeout(() => setObsidianSyncSuccess(null), 10000)
            onDocumentsChange()
          }
        }
      }, 1000)

      setTimeout(() => {
        clearInterval(pollInterval)
        if (obsidianSyncing) {
          setObsidianSyncing(false)
          setObsidianSyncProgress(null)
          setObsidianSyncSuccess('Sync started in background. Refresh to see updates.')
          setTimeout(() => setObsidianSyncSuccess(null), 10000)
          onDocumentsChange()
        }
      }, 600000)
    } catch (err) {
      setObsidianSyncError(err instanceof Error ? err.message : 'Sync failed')
      setObsidianSyncing(false)
      setObsidianSyncProgress(null)
    }
  }

  // --- Google Drive handlers ---
  const checkDriveStatus = useCallback(async () => {
    try {
      const status = await getGoogleDriveStatus()
      setDriveStatus(status)
      if (status.connected) {
        try {
          const data = await apiGet<{ sync_frequency: string; next_sync_scheduled: string | null }>('/api/google-drive/sync-settings')
          setSyncFrequency(data.sync_frequency || 'manual')
          setNextSyncScheduled(data.next_sync_scheduled)
        } catch (err) {
          logger.error('Error loading sync settings:', err)
        }
      }
    } catch (err) {
      logger.error('Error checking Drive status:', err)
    }
  }, [])

  async function handleConnectDrive() {
    try {
      setSyncError(null)
      await connectGoogleDrive()
      let attempts = 0
      const pollInterval = setInterval(async () => {
        attempts++
        try {
          const status = await getGoogleDriveStatus()
          if (status.connected) {
            clearInterval(pollInterval)
            setSyncSuccess('Google Drive connected successfully!')
            setDriveStatus(status)
            onDocumentsChange()
          }
        } catch { /* ignore */ }
        if (attempts >= 30) clearInterval(pollInterval)
      }, 1000)
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Failed to connect Google Drive')
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
      await syncGoogleDriveFiles(Array.from(selectedDriveFileIds))
      setSyncSuccess('File/folder sync started - documents will appear shortly')
      onDocumentsChange()
      setSelectedDriveFileIds(new Set())
      setTimeout(() => setSyncSuccess(null), 10000)
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Sync failed')
    } finally {
      setSyncing(false)
    }
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

  function toggleDriveFileSelection(fileId: string) {
    setSelectedDriveFileIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(fileId)) newSet.delete(fileId)
      else newSet.add(fileId)
      return newSet
    })
  }

  // --- Notion handlers ---
  const checkNotionStatus = useCallback(async () => {
    try {
      const status = await getNotionStatus()
      setNotionStatus(status)
    } catch (err) {
      logger.error('Error checking Notion status:', err)
    }
  }, [])

  async function handleConnectNotion() {
    try {
      setNotionSyncError(null)
      await connectNotion()
    } catch (err) {
      setNotionSyncError(err instanceof Error ? err.message : 'Failed to connect Notion')
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

  async function handleNotionSync() {
    if (selectedNotionPageIds.size === 0) {
      setNotionSyncError('Please select at least one page to sync')
      return
    }
    try {
      setNotionSyncing(true)
      setNotionSyncError(null)
      setNotionSyncSuccess(null)
      await syncNotion(Array.from(selectedNotionPageIds))
      setNotionSyncSuccess(`Sync started for ${selectedNotionPageIds.size} page(s)!`)
      setTimeout(() => onDocumentsChange(), 1500)
      setTimeout(() => setNotionSyncSuccess(null), 10000)
    } catch (err) {
      setNotionSyncError(err instanceof Error ? err.message : 'Sync failed')
    } finally {
      setNotionSyncing(false)
    }
  }

  async function handleNotionDisconnectConfirm() {
    setShowNotionDisconnectModal(false)
    try {
      setNotionSyncError(null)
      await disconnectNotion()
      setNotionSyncSuccess('Notion disconnected')
      await checkNotionStatus()
      setTimeout(() => setNotionSyncSuccess(null), 3000)
    } catch (err) {
      setNotionSyncError(err instanceof Error ? err.message : 'Failed to disconnect')
    }
  }

  function toggleNotionPageSelection(pageId: string) {
    setSelectedNotionPageIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(pageId)) newSet.delete(pageId)
      else newSet.add(pageId)
      return newSet
    })
  }

  // Load statuses when modal opens
  useEffect(() => {
    if (isOpen) {
      checkObsidianStatusFn()
      checkDriveStatus()
      checkNotionStatus()
    }
  }, [isOpen, checkObsidianStatusFn, checkDriveStatus, checkNotionStatus])

  // Load Notion pages when that tab is selected
  useEffect(() => {
    if (activeTab === 'notion' && notionStatus?.connected && notionPages.length === 0) {
      loadNotionPages()
    }
  }, [activeTab, notionStatus?.connected])

  if (!isOpen) return null

  const tabs = [
    { id: 'vault' as const, label: 'Vault' },
    { id: 'drive' as const, label: 'Drive' },
    { id: 'notion' as const, label: 'Notion' },
    { id: 'uploads' as const, label: 'Uploads' }
  ]

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
        <div className="bg-card rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-default">
            <h3 className="heading-3">Sync Settings</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <div className="border-b border-default px-4">
            <nav className="-mb-px flex gap-4">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-secondary hover:text-primary hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {/* === VAULT TAB === */}
            {activeTab === 'vault' && (
              <div className="space-y-4">
                {!obsidianStatus ? (
                  <p className="text-sm text-muted">Checking vault status...</p>
                ) : !obsidianStatus.connected ? (
                  <p className="text-sm text-muted">Vault not configured. Set DISCO_REPO_PATH in backend settings.</p>
                ) : (
                  <>
                    {/* Status */}
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
                            <button
                              onClick={() => {
                                setShowPendingDetails(!showPendingDetails)
                                if (!pendingFiles) fetchPendingFiles()
                              }}
                              className="text-amber-600 dark:text-amber-400 ml-1 hover:underline cursor-pointer"
                            >
                              ({obsidianStatus.pending_changes} pending)
                            </button>
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
                        onClick={handleCheckForUpdates}
                        disabled={checkingStatus || obsidianSyncing || syncingRecent}
                        className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Scan vault for new or changed files"
                      >
                        {checkingStatus ? 'Checking...' : 'Check for Updates'}
                      </button>
                    </div>

                    {/* Sync Options */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 border border-slate-200 dark:border-slate-700 rounded-lg">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-sm font-medium text-primary">Sync New & Changed</span>
                          {(obsidianStatus.unsynced_count ?? 0) > 0 && (
                            <span className="text-xs px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded">
                              {obsidianStatus.unsynced_count} file{obsidianStatus.unsynced_count !== 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-muted mb-2">
                          Only processes new, modified, or previously failed files. Existing documents and all project/initiative links are unchanged.
                        </p>
                        <button
                          onClick={handleSyncRecent}
                          disabled={obsidianSyncing || syncingRecent || (obsidianStatus.unsynced_count ?? 0) === 0}
                          className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                        >
                          {syncingRecent ? 'Syncing...' : (obsidianStatus.unsynced_count ?? 0) > 0
                            ? `Sync ${obsidianStatus.unsynced_count} File${obsidianStatus.unsynced_count !== 1 ? 's' : ''}`
                            : 'Everything Up to Date'}
                        </button>
                      </div>

                      <div className="p-3 border border-slate-200 dark:border-slate-700 rounded-lg">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-sm font-medium text-primary">Full Resync</span>
                        </div>
                        <p className="text-xs text-muted mb-2">
                          Mirrors the vault: syncs changes first, detects moves, then removes files no longer in the vault. All project/initiative links are preserved.
                        </p>
                        <button
                          onClick={handleObsidianFullSync}
                          disabled={obsidianSyncing || syncingRecent}
                          className="btn-secondary w-full disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                        >
                          {obsidianSyncing ? 'Syncing...' : 'Resync All Files'}
                        </button>
                      </div>
                    </div>

                    {/* Pending Files Details */}
                    {showPendingDetails && (
                      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-amber-800 dark:text-amber-200">Pending Files</span>
                          <button
                            onClick={() => setShowPendingDetails(false)}
                            className="text-amber-600 dark:text-amber-400 hover:text-amber-800 dark:hover:text-amber-200"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                        {!pendingFiles ? (
                          <div className="text-sm text-amber-700 dark:text-amber-300">Loading...</div>
                        ) : (
                          <div className="space-y-2">
                            {pendingFiles.pending.length > 0 && (
                              <div>
                                <div className="text-xs font-medium text-amber-700 dark:text-amber-300 mb-1">Pending ({pendingFiles.pending.length})</div>
                                {pendingFiles.pending.map((f, i) => (
                                  <div key={i} className="text-xs text-amber-600 dark:text-amber-400 font-mono truncate" title={f.file_path}>
                                    {f.file_path.split('/').pop()}
                                  </div>
                                ))}
                              </div>
                            )}
                            {pendingFiles.failed.length > 0 && (
                              <div>
                                <div className="text-xs font-medium text-red-700 dark:text-red-300 mb-1">Failed ({pendingFiles.failed.length})</div>
                                {pendingFiles.failed.map((f, i) => (
                                  <div key={i} className="text-xs text-red-600 dark:text-red-400 mb-1">
                                    <div className="font-mono truncate" title={f.file_path}>{f.file_path.split('/').pop()}</div>
                                    {f.sync_error && <div className="text-red-500 text-xs ml-2 truncate" title={f.sync_error}>{f.sync_error.slice(0, 80)}...</div>}
                                  </div>
                                ))}
                              </div>
                            )}
                            {pendingFiles.pending.length === 0 && pendingFiles.failed.length === 0 && (
                              <div className="text-sm text-amber-700 dark:text-amber-300">No pending or failed files found.</div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Messages */}
                    {obsidianSyncSuccess && (
                      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                        <span className="text-sm text-green-800 dark:text-green-200">{obsidianSyncSuccess}</span>
                      </div>
                    )}
                    {obsidianSyncError && (
                      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                        <span className="text-red-600 dark:text-red-400 font-bold">Error: </span>
                        <span className="text-sm text-red-800 dark:text-red-200">{obsidianSyncError}</span>
                      </div>
                    )}
                    {(obsidianSyncing || syncingRecent) && (
                      <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3">
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <LoadingSpinner size="sm" />
                            <span className="text-sm font-medium text-purple-800 dark:text-purple-200">
                              {obsidianSyncProgress ? (() => {
                                const { stage, synced, total } = obsidianSyncProgress
                                switch (stage) {
                                  case 'scanning': return 'Scanning vault for changes...'
                                  case 'syncing_changes': return `Syncing changes... ${synced} of ${total}`
                                  case 'detecting_moves': return 'Detecting moved files...'
                                  case 'cleaning_up': return 'Removing deleted files...'
                                  case 'verifying': return `Verifying... ${synced} of ${total}`
                                  default: return `Syncing... ${synced} of ${total} files`
                                }
                              })() : 'Starting sync...'}
                            </span>
                          </div>
                          {obsidianSyncProgress && obsidianSyncProgress.total > 0 && (
                            <span className="text-sm text-purple-600 dark:text-purple-300">
                              {Math.round((obsidianSyncProgress.synced / obsidianSyncProgress.total) * 100)}%
                            </span>
                          )}
                        </div>
                        {obsidianSyncProgress && obsidianSyncProgress.total > 0 && (
                          <div className="w-full bg-purple-200 dark:bg-purple-900 rounded-full h-2.5 mb-2">
                            <div
                              className="bg-purple-600 h-2.5 rounded-full transition-all duration-300"
                              style={{ width: `${Math.round((obsidianSyncProgress.synced / obsidianSyncProgress.total) * 100)}%` }}
                            />
                          </div>
                        )}
                        {obsidianSyncProgress?.current_file && (
                          <div className="text-xs text-purple-600 dark:text-purple-400 truncate" title={obsidianSyncProgress.current_file}>
                            {obsidianSyncProgress.current_file}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* === DRIVE TAB === */}
            {activeTab === 'drive' && (
              <div className="space-y-4">
                {!driveStatus ? (
                  <p className="text-sm text-muted">Checking Drive status...</p>
                ) : !driveStatus.connected ? (
                  <div className="text-center py-6">
                    <p className="text-sm text-muted mb-3">Connect Google Drive to sync documents</p>
                    <button onClick={handleConnectDrive} className="btn-primary">
                      Connect Google Drive
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm">
                        <div className="text-green-600 font-medium">Connected</div>
                        <div className="text-xs text-muted">
                          {driveStatus.document_count} documents - Last sync: {formatLastSync(driveStatus.last_sync)}
                        </div>
                      </div>
                      <button
                        onClick={() => setShowDisconnectModal(true)}
                        className="btn-secondary text-red-600 hover:bg-red-50"
                      >
                        Disconnect
                      </button>
                    </div>

                    {/* File Selection */}
                    <div className="bg-gray-50 dark:bg-gray-800 border border-default rounded-lg p-3">
                      <label className="block text-sm font-medium text-secondary mb-2">
                        Select files from Google Drive
                      </label>
                      <div className="flex gap-2 mb-3">
                        <GoogleDrivePicker
                          disabled={syncing}
                          buttonText="Browse Google Drive"
                          buttonClassName="btn-primary flex-1"
                          onFilesPicked={(files) => {
                            const newFiles: GoogleDriveFile[] = files.map(f => ({
                              id: f.id,
                              name: f.name,
                              mimeType: f.mimeType,
                              iconLink: f.iconUrl
                            }))
                            setDriveFiles(newFiles)
                            setSelectedDriveFileIds(new Set(files.map(f => f.id)))
                          }}
                        />
                      </div>

                      {driveFilesLoading ? (
                        <div className="text-sm text-muted py-4 text-center">Loading files...</div>
                      ) : driveFiles.length > 0 ? (
                        <>
                          <div className="flex items-center justify-between mb-2">
                            <label className="block text-sm font-medium text-secondary">Select Files to Sync</label>
                            <div className="flex gap-2">
                              <button onClick={() => setSelectedDriveFileIds(new Set(driveFiles.map(f => f.id)))} className="text-xs text-blue-600 hover:text-blue-800">Select All</button>
                              <button onClick={() => setSelectedDriveFileIds(new Set())} className="text-xs text-gray-600 hover:text-gray-800">Deselect All</button>
                            </div>
                          </div>
                          <div className="max-h-64 overflow-y-auto space-y-2 bg-white dark:bg-gray-900 rounded p-2">
                            {driveFiles.map(file => (
                              <label key={file.id} className="flex items-start gap-2 p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded cursor-pointer">
                                <input type="checkbox" checked={selectedDriveFileIds.has(file.id)} onChange={() => toggleDriveFileSelection(file.id)} className="mt-0.5" />
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm font-medium text-primary truncate">{file.name}</div>
                                  <div className="text-xs text-muted">{file.mimeType?.split('/').pop() || 'Unknown type'}{file.size && ` - ${Math.round(parseInt(file.size) / 1024)} KB`}</div>
                                </div>
                              </label>
                            ))}
                          </div>
                          {selectedDriveFileIds.size > 0 && (
                            <div className="mt-3 flex items-center justify-between">
                              <div className="text-xs text-muted">{selectedDriveFileIds.size} file{selectedDriveFileIds.size === 1 ? '' : 's'} selected</div>
                              <button onClick={handleDriveFilesSync} disabled={syncing} className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed">
                                {syncing ? 'Syncing...' : 'Sync Selected'}
                              </button>
                            </div>
                          )}
                        </>
                      ) : null}
                    </div>

                    {/* Sync Frequency */}
                    <div className="border-t border-default pt-4">
                      <div className="flex items-center gap-4">
                        <label className="text-sm font-medium text-secondary">Automatic Sync:</label>
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
                          <span className="text-xs text-muted">Next sync: {new Date(nextSyncScheduled).toLocaleString()}</span>
                        )}
                      </div>
                    </div>

                    {/* Messages */}
                    {syncSuccess && (
                      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                        <span className="text-sm text-green-800 dark:text-green-200">{syncSuccess}</span>
                      </div>
                    )}
                    {syncError && (
                      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                        <span className="text-red-600 dark:text-red-400 font-bold">Error: </span>
                        <span className="text-sm text-red-800 dark:text-red-200">{syncError}</span>
                      </div>
                    )}
                    {syncing && (
                      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                        <div className="flex items-center gap-2">
                          <LoadingSpinner size="sm" />
                          <span className="text-sm text-blue-800 dark:text-blue-200">Syncing documents from Google Drive...</span>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* === NOTION TAB === */}
            {activeTab === 'notion' && (
              <div className="space-y-4">
                {!notionStatus ? (
                  <p className="text-sm text-muted">Checking Notion status...</p>
                ) : !notionStatus.connected ? (
                  <div className="text-center py-6">
                    <p className="text-sm text-muted mb-3">Connect Notion to sync pages</p>
                    <button onClick={handleConnectNotion} className="btn-primary">
                      Connect Notion
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm">
                        <div className="text-green-600 font-medium">Connected</div>
                        <div className="text-xs text-muted">Workspace: {notionStatus.workspace_name || 'Unknown'}</div>
                      </div>
                      <button
                        onClick={() => setShowNotionDisconnectModal(true)}
                        className="btn-secondary text-red-600 hover:bg-red-50"
                      >
                        Disconnect
                      </button>
                    </div>

                    {/* Page Selection */}
                    <div className="bg-gray-50 dark:bg-gray-800 border border-default rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <label className="block text-sm font-medium text-secondary">Select Pages to Sync</label>
                        {notionPages.length > 0 && (
                          <div className="flex gap-2">
                            <button onClick={() => setSelectedNotionPageIds(new Set(notionPages.map(p => p.id)))} className="text-xs text-blue-600 hover:text-blue-800">Select All</button>
                            <button onClick={() => setSelectedNotionPageIds(new Set())} className="text-xs text-gray-600 hover:text-gray-800">Deselect All</button>
                          </div>
                        )}
                      </div>
                      {notionPagesLoading ? (
                        <div className="text-sm text-muted py-4 text-center">Loading pages...</div>
                      ) : notionPages.length === 0 ? (
                        <div className="text-sm text-muted py-4 text-center">No pages found. Make sure pages are shared with the integration.</div>
                      ) : (
                        <div className="max-h-64 overflow-y-auto space-y-2 bg-white dark:bg-gray-900 rounded p-2">
                          {notionPages.map(page => (
                            <label key={page.id} className="flex items-start gap-2 p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded cursor-pointer">
                              <input type="checkbox" checked={selectedNotionPageIds.has(page.id)} onChange={() => toggleNotionPageSelection(page.id)} className="mt-0.5" />
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-primary truncate">{page.title || 'Untitled'}</div>
                              </div>
                            </label>
                          ))}
                        </div>
                      )}
                      {selectedNotionPageIds.size > 0 && (
                        <div className="mt-3 flex items-center justify-between">
                          <div className="text-xs text-muted">{selectedNotionPageIds.size} page{selectedNotionPageIds.size === 1 ? '' : 's'} selected</div>
                          <button onClick={handleNotionSync} disabled={notionSyncing} className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed">
                            {notionSyncing ? 'Syncing...' : 'Sync Selected'}
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Messages */}
                    {notionSyncSuccess && (
                      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                        <span className="text-sm text-green-800 dark:text-green-200">{notionSyncSuccess}</span>
                      </div>
                    )}
                    {notionSyncError && (
                      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                        <span className="text-red-600 dark:text-red-400 font-bold">Error: </span>
                        <span className="text-sm text-red-800 dark:text-red-200">{notionSyncError}</span>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* === UPLOADS TAB === */}
            {activeTab === 'uploads' && (
              <div className="space-y-4">
                {profile?.client_id ? (
                  <DocumentUpload
                    clientId={profile.client_id}
                    apiBaseUrl={API_BASE_URL}
                    onUploadComplete={onDocumentsChange}
                    showAgentSelector={true}
                  />
                ) : (
                  <p className="text-secondary">Loading...</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Disconnect Confirmation Modals */}
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
    </>
  )
}
