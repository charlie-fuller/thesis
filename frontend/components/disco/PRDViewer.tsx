'use client'

import { useState, useEffect } from 'react'
import {
  FileText,
  CheckCircle,
  Clock,
  Download,
  Copy,
  Check,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  ExternalLink
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { apiGet, apiPost, authenticatedFetch } from '@/lib/api'

interface PRD {
  id: string
  bundle_id: string
  initiative_id: string
  title: string
  content_markdown: string
  content_structured: {
    executive_summary?: string
    problem_statement?: string
    requirements?: string
    technical_considerations?: string
    risks?: string
  }
  status: 'draft' | 'review' | 'approved' | 'exported'
  version: number
  created_at: string
  approved_at: string | null
  disco_bundles?: {
    name: string
    status: string
  }
}

interface PRDViewerProps {
  initiativeId: string
  canEdit: boolean
  onRefresh: () => void
}

const STATUS_CONFIG = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300', icon: Clock },
  review: { label: 'In Review', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400', icon: Clock },
  approved: { label: 'Approved', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', icon: CheckCircle },
  exported: { label: 'Exported', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', icon: ExternalLink }
}

function PRDCard({
  prd,
  selected,
  onClick
}: {
  prd: PRD
  selected: boolean
  onClick: () => void
}) {
  const statusConfig = STATUS_CONFIG[prd.status]
  const StatusIcon = statusConfig.icon

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-lg border transition-all ${
        selected
          ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-300 dark:border-indigo-700'
          : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
      }`}
    >
      <div className="flex items-start gap-3">
        <FileText className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
          selected ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'
        }`} />
        <div className="flex-1 min-w-0">
          <h3 className={`font-medium truncate ${
            selected ? 'text-indigo-900 dark:text-indigo-100' : 'text-slate-900 dark:text-white'
          }`}>
            {prd.title}
          </h3>
          {prd.disco_bundles && (
            <p className="text-xs text-slate-500 mt-0.5">
              Bundle: {prd.disco_bundles.name}
            </p>
          )}
          <div className="flex items-center gap-2 mt-2">
            <span className={`px-2 py-0.5 rounded text-xs font-medium flex items-center gap-1 ${statusConfig.color}`}>
              <StatusIcon className="w-3 h-3" />
              {statusConfig.label}
            </span>
            <span className="text-xs text-slate-400">v{prd.version}</span>
          </div>
        </div>
      </div>
    </button>
  )
}

function PRDDetail({
  prd,
  canEdit,
  onApprove,
  onRefresh
}: {
  prd: PRD
  canEdit: boolean
  onApprove: () => void
  onRefresh: () => void
}) {
  const [copied, setCopied] = useState(false)
  const [approving, setApproving] = useState(false)
  const statusConfig = STATUS_CONFIG[prd.status]

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(prd.content_markdown)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = () => {
    const blob = new Blob([prd.content_markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${prd.title.replace(/\s+/g, '_')}_v${prd.version}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleApprove = async () => {
    setApproving(true)
    try {
      await onApprove()
    } finally {
      setApproving(false)
    }
  }

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <div>
          <h3 className="font-semibold text-slate-900 dark:text-white">
            {prd.title}
          </h3>
          <div className="flex items-center gap-2 text-sm text-slate-500 mt-1">
            <span>Version {prd.version}</span>
            <span>-</span>
            <span className={`px-1.5 py-0.5 rounded text-xs ${statusConfig.color}`}>
              {statusConfig.label}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-green-500" />
                Copied
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy
              </>
            )}
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md transition-colors"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          {canEdit && prd.status === 'draft' && (
            <button
              onClick={handleApprove}
              disabled={approving}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {approving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle className="w-4 h-4" />
              )}
              Approve
            </button>
          )}
        </div>
      </div>

      {/* Executive Summary Quick View */}
      {prd.content_structured?.executive_summary && (
        <div className="px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Executive Summary
          </h4>
          <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-4">
            {prd.content_structured.executive_summary}
          </p>
        </div>
      )}

      {/* Full Content */}
      <div className="p-4 max-h-[calc(100vh-350px)] min-h-[400px] overflow-y-auto">
        <div className="prose prose-sm dark:prose-invert max-w-none prose-table:border-collapse prose-table:w-full prose-th:border prose-th:border-slate-300 prose-th:dark:border-slate-600 prose-th:bg-slate-100 prose-th:dark:bg-slate-700 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-td:border prose-td:border-slate-300 prose-td:dark:border-slate-600 prose-td:px-3 prose-td:py-2">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {prd.content_markdown}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}

export default function PRDViewer({ initiativeId, canEdit, onRefresh }: PRDViewerProps) {
  const [prds, setPrds] = useState<PRD[]>([])
  const [selectedPRD, setSelectedPRD] = useState<PRD | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [generationStatus, setGenerationStatus] = useState('')

  // Load PRDs
  useEffect(() => {
    loadPRDs()
  }, [initiativeId])

  async function loadPRDs() {
    try {
      setLoading(true)
      setError(null)
      const result = await apiGet<{ success: boolean; prds: PRD[] }>(
        `/api/disco/initiatives/${initiativeId}/prds`
      )
      setPrds(result.prds || [])
      // Select first PRD if available
      if (result.prds?.length > 0 && !selectedPRD) {
        setSelectedPRD(result.prds[0])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load PRDs')
    } finally {
      setLoading(false)
    }
  }

  async function handleApprove(prdId: string) {
    try {
      await apiPost(`/api/disco/initiatives/${initiativeId}/prds/${prdId}/approve`, {})
      await loadPRDs()
      onRefresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve PRD')
    }
  }

  async function handleGenerateSummary() {
    setGenerating(true)
    setGenerationStatus('Starting executive summary generation...')

    try {
      const response = await authenticatedFetch(
        `/api/disco/initiatives/${initiativeId}/generate-summary`,
        { method: 'POST' }
      )

      if (!response.ok) {
        throw new Error('Failed to start generation')
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response stream')

      const decoder = new TextDecoder()
      let buffer = ''
      let content = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: status')) {
            const dataLine = lines[lines.indexOf(line) + 1]
            if (dataLine?.startsWith('data: ')) {
              setGenerationStatus(dataLine.slice(6))
            }
          } else if (line.startsWith('data: ') && !line.startsWith('data: {')) {
            content += line.slice(6)
          } else if (line.startsWith('event: complete')) {
            setGenerationStatus('Complete!')
            // Could display the summary in a modal here
            setTimeout(() => {
              setGenerating(false)
              setGenerationStatus('')
              loadPRDs()
              onRefresh()
            }, 1000)
          } else if (line.startsWith('event: error')) {
            const dataLine = lines[lines.indexOf(line) + 1]
            throw new Error(dataLine?.slice(6) || 'Unknown error')
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed')
      setGenerating(false)
      setGenerationStatus('')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
        <span className="ml-2 text-slate-500">Loading PRDs...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      </div>
    )
  }

  if (prds.length === 0) {
    return (
      <div className="text-center py-12 border border-dashed border-slate-300 dark:border-slate-600 rounded-lg">
        <FileText className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
        <p className="text-slate-500 dark:text-slate-400">No PRDs generated yet</p>
        <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
          Approve bundles in the Synthesis tab, then generate PRDs
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Actions bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">
            {prds.length} PRD{prds.length !== 1 ? 's' : ''} generated
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadPRDs}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          {canEdit && prds.some(p => p.status === 'approved') && (
            <button
              onClick={handleGenerateSummary}
              disabled={generating}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {generationStatus || 'Generating...'}
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  Executive Summary
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* PRD list and detail */}
      <div className="flex gap-6">
        {/* PRD List */}
        <div className="w-72 flex-shrink-0 space-y-2">
          {prds.map(prd => (
            <PRDCard
              key={prd.id}
              prd={prd}
              selected={selectedPRD?.id === prd.id}
              onClick={() => setSelectedPRD(prd)}
            />
          ))}
        </div>

        {/* PRD Detail */}
        <div className="flex-1 min-w-0">
          {selectedPRD ? (
            <PRDDetail
              prd={selectedPRD}
              canEdit={canEdit}
              onApprove={() => handleApprove(selectedPRD.id)}
              onRefresh={loadPRDs}
            />
          ) : (
            <div className="flex items-center justify-center min-h-[400px] bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-lg">
              <div className="text-center text-slate-500 dark:text-slate-400">
                <FileText className="w-10 h-10 mx-auto mb-3 opacity-50" />
                <p>Select a PRD to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
