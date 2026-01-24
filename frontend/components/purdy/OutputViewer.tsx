'use client'

import { useState } from 'react'
import {
  FileText,
  Download,
  ChevronDown,
  ChevronRight,
  Clock,
  CheckCircle,
  AlertCircle,
  Copy,
  Check,
  History,
  Target,
  Search,
  BarChart,
  Cpu
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface Output {
  id: string
  run_id: string
  agent_type: string
  version: number
  title: string | null
  recommendation: string | null
  tier_routing: string | null
  confidence_level: string | null
  executive_summary: string | null
  content_markdown: string
  content_structured: Record<string, any>
  created_at: string
}

interface OutputViewerProps {
  initiativeId: string
  outputs: Output[]
  selectedOutput: Output | null
  onSelectOutput: (output: Output | null) => void
  onRefresh: () => void
}

const AGENT_CONFIG: Record<string, { name: string; icon: typeof Target; color: string }> = {
  triage: { name: 'Triage', icon: Target, color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400' },
  discovery_planner: { name: 'Discovery Planner', icon: Search, color: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400' },
  coverage_tracker: { name: 'Coverage Tracker', icon: BarChart, color: 'text-purple-600 bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400' },
  synthesizer: { name: 'Synthesizer', icon: FileText, color: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400' },
  tech_evaluation: { name: 'Tech Evaluation', icon: Cpu, color: 'text-indigo-600 bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-400' },
}

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'Unknown date'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'Unknown date'
  return date.toLocaleString()
}

function OutputListItem({
  output,
  selected,
  onClick
}: {
  output: Output
  selected: boolean
  onClick: () => void
}) {
  const config = AGENT_CONFIG[output.agent_type] || { name: output.agent_type, icon: FileText, color: 'text-slate-600 bg-slate-100' }
  const Icon = config.icon

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-start gap-3 p-3 rounded-lg text-left transition-all ${
        selected
          ? 'bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800'
          : 'hover:bg-slate-50 dark:hover:bg-slate-800 border border-transparent'
      }`}
    >
      <div className={`p-1.5 rounded ${config.color}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-900 dark:text-white">
            {config.name}
          </span>
          <span className="text-xs text-slate-400">v{output.version}</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          {output.recommendation && (
            <span className={`px-1.5 py-0.5 text-xs rounded ${
              output.recommendation === 'GO'
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : output.recommendation === 'NO-GO'
                ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
            }`}>
              {output.recommendation}
            </span>
          )}
          {output.confidence_level && (
            <span className="text-xs text-slate-500">
              {output.confidence_level}
            </span>
          )}
        </div>
        <div className="text-xs text-slate-400 mt-1">
          {formatDate(output.created_at)}
        </div>
      </div>
    </button>
  )
}

function OutputDetail({
  output,
  onClose
}: {
  output: Output
  onClose: () => void
}) {
  const [copied, setCopied] = useState(false)
  const config = AGENT_CONFIG[output.agent_type] || { name: output.agent_type, icon: FileText, color: 'text-slate-600 bg-slate-100' }
  const Icon = config.icon

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(output.content_markdown)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = () => {
    const blob = new Blob([output.content_markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${output.agent_type}_v${output.version}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded ${config.color}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white">
              {config.name}
            </h3>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span>Version {output.version}</span>
              <span>•</span>
              <span>{formatDate(output.created_at)}</span>
            </div>
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
        </div>
      </div>

      {/* Summary badges */}
      {(output.recommendation || output.tier_routing || output.confidence_level) && (
        <div className="flex flex-wrap gap-2 px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
          {output.recommendation && (
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              output.recommendation === 'GO'
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : output.recommendation === 'NO-GO'
                ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
            }`}>
              {output.recommendation}
            </span>
          )}
          {output.tier_routing && (
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
              {output.tier_routing}
            </span>
          )}
          {output.confidence_level && (
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300">
              {output.confidence_level} Confidence
            </span>
          )}
        </div>
      )}

      {/* Executive Summary */}
      {output.executive_summary && (
        <div className="px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Executive Summary
          </h4>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {output.executive_summary}
          </p>
        </div>
      )}

      {/* Full Content */}
      <div className="p-4 max-h-[600px] overflow-y-auto">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{output.content_markdown}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}

export default function OutputViewer({
  initiativeId,
  outputs,
  selectedOutput,
  onSelectOutput,
  onRefresh
}: OutputViewerProps) {
  // Group outputs by agent type
  const outputsByType = outputs.reduce((acc, output) => {
    if (!acc[output.agent_type]) {
      acc[output.agent_type] = []
    }
    acc[output.agent_type].push(output)
    return acc
  }, {} as Record<string, Output[]>)

  if (outputs.length === 0) {
    return (
      <div className="text-center py-12 border border-dashed border-slate-300 dark:border-slate-600 rounded-lg">
        <FileText className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
        <p className="text-slate-500 dark:text-slate-400">No outputs yet</p>
        <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
          Run an agent to generate analysis outputs
        </p>
      </div>
    )
  }

  return (
    <div className="flex gap-6">
      {/* Output List */}
      <div className="w-80 flex-shrink-0">
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 space-y-4">
          {Object.entries(outputsByType).map(([agentType, typeOutputs]) => {
            const config = AGENT_CONFIG[agentType] || { name: agentType }

            return (
              <div key={agentType}>
                <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 px-2">
                  {config.name}
                </h4>
                <div className="space-y-1">
                  {typeOutputs.map((output) => (
                    <OutputListItem
                      key={output.id}
                      output={output}
                      selected={selectedOutput?.id === output.id}
                      onClick={() => onSelectOutput(output)}
                    />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Output Detail */}
      <div className="flex-1 min-w-0">
        {selectedOutput ? (
          <OutputDetail
            output={selectedOutput}
            onClose={() => onSelectOutput(null)}
          />
        ) : (
          <div className="flex items-center justify-center h-[400px] bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-lg">
            <div className="text-center text-slate-500 dark:text-slate-400">
              <FileText className="w-10 h-10 mx-auto mb-3 opacity-50" />
              <p>Select an output to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
