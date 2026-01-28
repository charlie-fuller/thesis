'use client'

import { useState, useEffect, useCallback } from 'react'
import { FileText, RefreshCw, CheckCircle, Sparkles } from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'

interface SyncActivity {
  active: boolean
  current_file: string | null
  recent_files: Array<{ files_added: number; files_updated: number }>
}

interface ExtractionActivity {
  active: boolean
  job_id: string | null
  status: string | null
  files_processed: number
  opportunities_found: number
  tasks_found: number
  stakeholders_found: number
  started_at: string | null
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
  extraction_activity?: ExtractionActivity
}

interface ScanResult {
  status: string
  job_id?: string
  message?: string
}

export default function GranolaScanPanel() {
  const [status, setStatus] = useState<GranolaScanStatus | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [loading, setLoading] = useState(true)
  const [scanMessage, setScanMessage] = useState<string | null>(null)

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

  useEffect(() => {
    fetchStatus()
    // Poll more frequently when scanning/syncing is active
    const isActive = status?.sync_activity?.active || status?.extraction_activity?.active || isScanning
    const pollInterval = isActive ? 3000 : 10000  // 3s when active, 10s otherwise
    const interval = setInterval(fetchStatus, pollInterval)
    return () => clearInterval(interval)
  }, [fetchStatus, status?.sync_activity?.active, status?.extraction_activity?.active, isScanning])

  // Auto-dismiss scan message after 10 seconds
  useEffect(() => {
    if (scanMessage) {
      const timer = setTimeout(() => setScanMessage(null), 10000)
      return () => clearTimeout(timer)
    }
  }, [scanMessage])

  const handleScan = async () => {
    try {
      setIsScanning(true)
      setScanMessage(null)
      // Use background=true so scan continues even if user navigates away
      const result = await apiPost<ScanResult>('/api/pipeline/granola/scan?force_rescan=false&background=true', {})

      if (result.status === 'started') {
        setScanMessage('Scan started! You can navigate away - it will continue in the background.')
        // Poll status after a delay
        setTimeout(async () => {
          await fetchStatus()
          setIsScanning(false)
        }, 5000)
      } else {
        await fetchStatus()
        setIsScanning(false)
      }
    } catch (err) {
      console.error('Scan failed:', err)
      setScanMessage('Scan failed to start. Please try again.')
      setIsScanning(false)
    }
  }

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
    <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            status.connected ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-red-100 dark:bg-red-900/30'
          }`}>
            <FileText className={`w-5 h-5 ${
              status.connected ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
            }`} />
          </div>
          <div>
            <h3 className="font-medium text-slate-900 dark:text-white">Granola Vault</h3>
            <p className="text-xs text-slate-500">
              {status.connected
                ? `${status.scanned_files}/${status.total_files} meetings scanned`
                : (status.error && status.error.length > 100
                    ? 'Connection error. Please try again.'
                    : status.error || 'Not connected')
              }
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {status.pending_files > 0 && (
            <span className="text-xs px-2 py-1 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
              {status.pending_files} new
            </span>
          )}
          <button
            onClick={handleScan}
            disabled={isScanning || !status.connected}
            className="px-3 py-1.5 text-sm font-medium rounded-lg bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />
            {isScanning ? 'Scanning...' : 'Scan'}
          </button>
        </div>
      </div>

      {status.last_scan && (
        <p className="text-xs text-slate-400 mt-2">
          Last scan: {new Date(status.last_scan).toLocaleString()}
        </p>
      )}

      {/* Scan status message */}
      {scanMessage && (
        <div className="mt-3 flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg px-3 py-2">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{scanMessage}</span>
        </div>
      )}

      {/* Sync Activity Indicator */}
      {status.sync_activity?.active && (
        <div className="mt-3 flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg px-3 py-2">
          <RefreshCw className="w-4 h-4 animate-spin flex-shrink-0" />
          <span>Syncing: {status.sync_activity.current_file || 'processing...'}</span>
        </div>
      )}

      {/* Extraction Activity Indicator */}
      {status.extraction_activity?.active && (
        <div className="mt-3 flex items-center gap-2 text-sm text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 rounded-lg px-3 py-2">
          <Sparkles className="w-4 h-4 animate-pulse flex-shrink-0" />
          <span>
            Analyzing meetings for tasks, opportunities & stakeholders...
            {status.extraction_activity.files_processed > 0 && (
              <span className="text-purple-500 dark:text-purple-300 ml-1">
                ({status.extraction_activity.files_processed} processed)
              </span>
            )}
          </span>
        </div>
      )}

      {/* Extraction Complete Summary */}
      {status.extraction_activity && !status.extraction_activity.active && status.extraction_activity.status === 'completed' && (
        <div className="mt-3 flex items-center gap-2 text-sm text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 rounded-lg px-3 py-2">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>
            Found {status.extraction_activity.opportunities_found} opportunities, {status.extraction_activity.tasks_found} tasks, {status.extraction_activity.stakeholders_found} stakeholders
          </span>
        </div>
      )}

      {!status.sync_activity?.active && status.sync_activity?.recent_files && status.sync_activity.recent_files.length > 0 && (
        <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Just synced: {status.sync_activity.recent_files[0].files_added + status.sync_activity.recent_files[0].files_updated} file(s)
        </div>
      )}
    </div>
  )
}
