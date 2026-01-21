'use client'

import { useState, useEffect, useCallback } from 'react'
import { FileText, RefreshCw } from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'

interface GranolaScanStatus {
  connected: boolean
  vault_path: string
  total_files: number
  scanned_files: number
  pending_files: number
  last_scan: string | null
  error: string | null
}

export default function GranolaScanPanel() {
  const [status, setStatus] = useState<GranolaScanStatus | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [loading, setLoading] = useState(true)

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
  }, [fetchStatus])

  const handleScan = async () => {
    try {
      setIsScanning(true)
      await apiPost('/api/pipeline/granola/scan?force_rescan=false', {})
      await fetchStatus()
    } catch (err) {
      console.error('Scan failed:', err)
    } finally {
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
                : status.error || 'Not connected'
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
    </div>
  )
}
