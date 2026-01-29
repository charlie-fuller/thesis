'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Vault, Loader2 } from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'

interface SyncActivity {
  active: boolean
  current_file: string | null
  last_synced_file: string | null
  recent_files: Array<{ files_added: number; files_updated: number }>
}

interface GranolaScanStatus {
  connected: boolean
  vault_path: string
  total_files: number
  scanned_files: number
  pending_files: number
  last_scan: string | null
  error: string | null
  sync_activity?: SyncActivity
}

interface ScanResult {
  status: string
  job_id?: string
  message?: string
}

export default function GranolaScanPanel() {
  const [status, setStatus] = useState<GranolaScanStatus | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [isPreparing, setIsPreparing] = useState(false)  // Show during auto-scan delay
  const [loading, setLoading] = useState(true)
  const autoScanTriggeredRef = useRef(false)
  const lastPendingCountRef = useRef(0)

  const fetchStatus = useCallback(async () => {
    try {
      const result = await apiGet<GranolaScanStatus>('/api/pipeline/granola/status')
      setStatus(result)
    } catch (err) {
      console.error('Failed to fetch Granola status:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Define handleScan BEFORE the effects that use it
  const handleScan = useCallback(async () => {
    try {
      setIsScanning(true)
      // Use background=true so scan continues even if user navigates away
      const result = await apiPost<ScanResult>('/api/pipeline/granola/scan?force_rescan=false&background=true', {})

      if (result.status === 'started') {
        // Poll status until pending_files becomes 0
        const pollUntilDone = async () => {
          await fetchStatus()
          // Check if still have pending files (scan not complete)
          // Note: status state won't be updated yet, so we re-fetch
          const currentStatus = await apiGet<GranolaScanStatus>('/api/pipeline/granola/status')
          if (currentStatus.pending_files > 0) {
            setTimeout(pollUntilDone, 3000)
          } else {
            setIsScanning(false)
          }
        }
        setTimeout(pollUntilDone, 3000)
      } else {
        await fetchStatus()
        setIsScanning(false)
      }
    } catch (err) {
      console.error('Scan failed:', err)
      setIsScanning(false)
    }
  }, [fetchStatus])

  useEffect(() => {
    fetchStatus()
    // Poll more frequently when any activity is happening
    const isActive = status?.sync_activity?.active || isScanning || isPreparing
    const pollInterval = isActive ? 2000 : 5000  // 2s when active, 5s otherwise (faster default)
    const interval = setInterval(fetchStatus, pollInterval)
    return () => clearInterval(interval)
  }, [fetchStatus, status?.sync_activity?.active, isScanning, isPreparing])

  // Auto-scan when new documents are detected and sync is not active
  useEffect(() => {
    if (!status) return

    const hasPendingFiles = status.pending_files > 0
    const syncIsActive = status.sync_activity?.active
    const newFilesDetected = status.pending_files > lastPendingCountRef.current

    // Update last pending count
    lastPendingCountRef.current = status.pending_files

    // Auto-scan conditions:
    // 1. Has pending files
    // 2. Not currently scanning
    // 3. Sync is not active (wait for files to finish syncing)
    // 4. Either new files were just detected OR we haven't auto-scanned yet for current pending
    if (hasPendingFiles && !isScanning && !syncIsActive) {
      // Reset auto-scan flag when new files are detected
      if (newFilesDetected) {
        autoScanTriggeredRef.current = false
      }

      // Trigger auto-scan if not already triggered
      if (!autoScanTriggeredRef.current) {
        autoScanTriggeredRef.current = true
        setIsPreparing(true)  // Show preparing state during delay
        // Small delay to batch any rapid successive syncs
        const timer = setTimeout(() => {
          setIsPreparing(false)
          handleScan()
        }, 2000)
        return () => {
          clearTimeout(timer)
          setIsPreparing(false)
        }
      }
    }

    // Reset flag when all files are scanned
    if (!hasPendingFiles) {
      autoScanTriggeredRef.current = false
      setIsPreparing(false)
    }
  }, [status?.pending_files, status?.sync_activity?.active, isScanning, handleScan])

  if (loading) {
    return (
      <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
        <div className="animate-pulse flex items-center gap-3">
          <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-lg" />
          <div className="flex-1">
            <div className="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded mb-2" />
            <div className="h-3 w-32 bg-slate-200 dark:bg-slate-700 rounded" />
          </div>
        </div>
      </div>
    )
  }

  if (!status) return null

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            status.connected ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-red-100 dark:bg-red-900/30'
          }`}>
            <Vault className={`w-5 h-5 ${
              status.connected ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
            }`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-primary">Vault</h3>
            <p className="text-sm text-secondary">
              {status.connected
                ? `${status.scanned_files}/${status.total_files} meetings synced`
                : (status.error && status.error.length > 100
                    ? 'Connection error. Please try again.'
                    : status.error || 'Not connected')
              }
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {status.pending_files > 0 && !isScanning && (
            <span className="text-xs px-2 py-1 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
              {status.pending_files} new
            </span>
          )}
        </div>
      </div>

      {status.sync_activity?.last_synced_file && (
        <p className="text-xs text-slate-400 mt-2 truncate">
          Last synced: {status.sync_activity.last_synced_file}
        </p>
      )}


      {/* Status indicators - shows progress through sync → prepare → analyze */}
      {status.sync_activity?.active && (
        <div className="mt-3 flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded-lg px-3 py-2">
          <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
          <span>Syncing new files...</span>
        </div>
      )}
      {!status.sync_activity?.active && isPreparing && (
        <div className="mt-3 flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg px-3 py-2">
          <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
          <span>Preparing to analyze...</span>
        </div>
      )}
      {isScanning && (
        <div className="mt-3 flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg px-3 py-2">
          <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
          <span>Analyzing for tasks, projects, stakeholders...</span>
        </div>
      )}
    </div>
  )
}
