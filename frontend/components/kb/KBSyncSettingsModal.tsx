'use client'

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import DocumentUpload from '@/components/DocumentUpload'
import LoadingSpinner from '@/components/LoadingSpinner'
import { logger } from '@/lib/logger'
import { formatLastSync } from '@/lib/formatters'
import { apiGet, apiPost } from '@/lib/api'
import { API_BASE_URL } from '@/lib/config'

interface ObsidianStatus {
  connected: boolean
  vault_name?: string
  vault_path?: string
  document_count?: number
  last_sync?: string
  pending_changes?: number
  total_files?: number
  unsynced_count?: number
  agent_active?: boolean
  agent_last_upload?: string | null
  agent_uploads_count?: number
  agent_sync_current?: number | null
  agent_sync_total?: number | null
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
  const [activeTab, setActiveTab] = useState<'vault' | 'uploads'>('vault')

  // --- Vault path editing ---
  const [editingVaultPath, setEditingVaultPath] = useState(false)
  const [vaultPathInput, setVaultPathInput] = useState('')
  const [vaultPathSaving, setVaultPathSaving] = useState(false)

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
        agent_active?: boolean
        agent_last_upload?: string | null
        agent_uploads_count?: number
        agent_sync_current?: number | null
        agent_sync_total?: number | null
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
        last_sync: response.last_sync,
        agent_active: response.agent_active,
        agent_last_upload: response.agent_last_upload,
        agent_uploads_count: response.agent_uploads_count,
        agent_sync_current: response.agent_sync_current,
        agent_sync_total: response.agent_sync_total,
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

  async function handleSaveVaultPath() {
    if (!vaultPathInput.trim()) return
    try {
      setVaultPathSaving(true)
      setObsidianSyncError(null)
      await apiPost('/api/obsidian/configure', { vault_path: vaultPathInput.trim() })
      setEditingVaultPath(false)
      setObsidianSyncSuccess('Vault location updated')
      setTimeout(() => setObsidianSyncSuccess(null), 3000)
      await checkObsidianStatusFn()
    } catch (err) {
      setObsidianSyncError(err instanceof Error ? err.message : 'Failed to update vault location')
    } finally {
      setVaultPathSaving(false)
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

  // Load status when modal opens
  useEffect(() => {
    if (isOpen) {
      checkObsidianStatusFn()
    }
  }, [isOpen, checkObsidianStatusFn])

  // Auto-refresh while agent is actively syncing
  useEffect(() => {
    if (!isOpen || !obsidianStatus?.agent_active) return
    const interval = setInterval(() => {
      checkObsidianStatusFn()
    }, 5000)
    return () => clearInterval(interval)
  }, [isOpen, obsidianStatus?.agent_active, checkObsidianStatusFn])

  if (!isOpen) return null

  const tabs = [
    { id: 'vault' as const, label: 'Vault' },
    { id: 'uploads' as const, label: 'Uploads' }
  ]

  return (
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
                <div className="space-y-3">
                  <p className="text-sm text-muted">No vault configured. Enter the absolute path to your Obsidian vault.</p>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={vaultPathInput}
                      onChange={(e) => setVaultPathInput(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleSaveVaultPath() }}
                      className="flex-1 text-sm font-mono px-3 py-2 border border-default rounded bg-white dark:bg-gray-900 text-primary"
                      placeholder="/Users/you/Vault"
                    />
                    <button onClick={handleSaveVaultPath} disabled={vaultPathSaving || !vaultPathInput.trim()} className="btn-primary disabled:opacity-50">
                      {vaultPathSaving ? 'Saving...' : 'Configure'}
                    </button>
                  </div>
                  {obsidianSyncError && (
                    <div className="text-sm text-red-600">{obsidianSyncError}</div>
                  )}
                </div>
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
                        {(() => {
                          const lastSync = obsidianStatus.agent_last_upload || obsidianStatus.last_sync
                          return lastSync ? <> - Last sync: {formatLastSync(lastSync)}</> : null
                        })()}
                      </div>
                      {obsidianStatus.vault_path && !editingVaultPath && (
                        <button
                          onClick={() => { setVaultPathInput(obsidianStatus.vault_path || ''); setEditingVaultPath(true) }}
                          className="text-xs text-muted font-mono truncate max-w-md hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer text-left"
                          title="Click to change vault location"
                        >
                          {obsidianStatus.vault_path}
                        </button>
                      )}
                      {editingVaultPath && (
                        <div className="flex items-center gap-2 mt-1">
                          <input
                            type="text"
                            value={vaultPathInput}
                            onChange={(e) => setVaultPathInput(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter') handleSaveVaultPath(); if (e.key === 'Escape') setEditingVaultPath(false) }}
                            className="flex-1 text-xs font-mono px-2 py-1 border border-default rounded bg-white dark:bg-gray-900 text-primary"
                            placeholder="/path/to/vault"
                            autoFocus
                          />
                          <button onClick={handleSaveVaultPath} disabled={vaultPathSaving} className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
                            {vaultPathSaving ? '...' : 'Save'}
                          </button>
                          <button onClick={() => setEditingVaultPath(false)} className="text-xs px-2 py-1 text-muted hover:text-primary">
                            Cancel
                          </button>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={handleCheckForUpdates}
                      disabled={checkingStatus || obsidianSyncing || syncingRecent}
                      className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Refresh sync status and document count"
                    >
                      {checkingStatus ? 'Refreshing...' : 'Refresh Status'}
                    </button>
                  </div>

                  {/* Local Sync Agent Status */}
                  {obsidianStatus.agent_active && (
                    <div className="px-3 py-2.5 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className="relative flex h-2.5 w-2.5 flex-shrink-0">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
                        </span>
                        <div className="flex-1 min-w-0">
                          <span className="text-sm font-medium text-green-800 dark:text-green-200">
                            Sync agent running
                          </span>
                          {obsidianStatus.agent_sync_current != null && obsidianStatus.agent_sync_total != null ? (
                            <span className="text-xs text-green-600 dark:text-green-400 ml-2">
                              {obsidianStatus.agent_sync_current} of {obsidianStatus.agent_sync_total} files
                              {obsidianStatus.agent_sync_total - obsidianStatus.agent_sync_current > 0 && (
                                <> ({obsidianStatus.agent_sync_total - obsidianStatus.agent_sync_current} remaining)</>
                              )}
                            </span>
                          ) : (
                            <span className="text-xs text-green-600 dark:text-green-400 ml-2">
                              {obsidianStatus.agent_uploads_count} file{obsidianStatus.agent_uploads_count !== 1 ? 's' : ''} uploaded this session
                            </span>
                          )}
                        </div>
                      </div>
                      {obsidianStatus.agent_sync_current != null && obsidianStatus.agent_sync_total != null && obsidianStatus.agent_sync_total > 0 && (
                        <div className="mt-2 w-full bg-green-200 dark:bg-green-900 rounded-full h-1.5">
                          <div
                            className="bg-green-500 h-1.5 rounded-full transition-all duration-500"
                            style={{ width: `${Math.round((obsidianStatus.agent_sync_current / obsidianStatus.agent_sync_total) * 100)}%` }}
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {/* Sync Options */}
                  {!obsidianStatus.agent_active && (
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
                          Uploads new and modified files from the vault. Use this if files were added while the sync agent was stopped.
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
                          Re-processes all vault files and removes documents for deleted files. Use if the KB seems out of sync with your vault.
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
                  )}

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
  )
}
