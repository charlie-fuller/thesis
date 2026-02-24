'use client'

import { useState, useEffect, useRef, useId } from 'react'
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
  Cpu,
  Trash2,
  Minimize2,
  Loader2,
  ListChecks,
  ExternalLink,
  Square,
  CheckSquare
} from 'lucide-react'
import ReactMarkdown, { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { apiDelete, apiPost } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'

// Mermaid diagram component for rendering diagrams
function MermaidDiagram({ chart }: { chart: string }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const uniqueId = useId().replace(/:/g, '-')
  const [error, setError] = useState<string | null>(null)
  const [rendered, setRendered] = useState(false)

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current || rendered) return

      try {
        // Dynamic import to avoid SSR issues
        const mermaid = (await import('mermaid')).default

        mermaid.initialize({
          startOnLoad: false,
          theme: 'neutral',
          securityLevel: 'loose',
        })

        const { svg } = await mermaid.render(`mermaid-${uniqueId}`, chart)
        if (containerRef.current) {
          containerRef.current.innerHTML = svg
          setRendered(true)
        }
      } catch (err) {
        console.error('Mermaid rendering failed:', err)
        setError(err instanceof Error ? err.message : 'Failed to render diagram')
      }
    }

    renderDiagram()
  }, [chart, uniqueId, rendered])

  if (error) {
    return (
      <div className="my-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <p className="text-sm text-red-600 dark:text-red-400">Diagram error: {error}</p>
        <pre className="mt-2 text-xs text-slate-600 dark:text-slate-400 overflow-x-auto">{chart}</pre>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="my-4 flex justify-center overflow-x-auto"
    />
  )
}

interface ThroughlineResolution {
  hypothesis_resolutions?: Array<{ hypothesis_id: string; status: string; evidence_summary?: string }>
  gap_statuses?: Array<{ gap_id: string; status: string; findings?: string }>
  state_changes?: Array<{ description: string; owner?: string; deadline?: string; priority?: string }>
  so_what?: { state_change_proposed?: string; next_human_action?: string; kill_test?: string }
}

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
  content_structured: Record<string, unknown>
  created_at: string
  output_format?: string
  synthesis_mode?: string
  synthesis_notes?: string | null
  source_outputs?: Array<{ agent_type: string; version: number; id: string }>
  throughline_resolution?: ThroughlineResolution | null
}

interface OutputViewerProps {
  initiativeId: string
  initiativeTitle?: string
  outputs: Output[]
  selectedOutput: Output | null
  onSelectOutput: (output: Output | null) => void
  onRefresh: () => void
  onDelete?: (outputId: string) => Promise<void>
}

// Define the DISCo workflow order for sidebar display (base agents only)
// Executive/condensed variants are grouped with their parent agent
// NOTE: synthesizer removed - outputs grouped under consolidator
const AGENT_ORDER = [
  'discovery_prep',
  'triage',
  'discovery_planner',
  'coverage_tracker',
  'insight_extractor',
  'consolidator',
  'strategist',
  'prd_generator',
  'tech_evaluation',
]

// Deprecated agent mappings (old outputs display under new agent name)
const AGENT_ALIASES: Record<string, string> = {
  'synthesizer': 'consolidator',
  'synthesizer_executive': 'consolidator_executive',
  'synthesizer_condensed': 'consolidator_condensed',
}

// Helper to get the display agent type (maps deprecated names to current names)
function getDisplayAgentType(agentType: string): string {
  return AGENT_ALIASES[agentType] || agentType
}

// Helper to get base agent type (strips _executive, _condensed suffixes, maps deprecated agents)
function getBaseAgentType(agentType: string): string {
  // First, map any deprecated agent names to their current equivalents
  const mappedType = getDisplayAgentType(agentType)
  // Then strip variant suffixes
  return mappedType.replace(/_executive$/, '').replace(/_condensed$/, '')
}

// Check if an agent type is a variant (executive/condensed)
function isVariant(agentType: string): boolean {
  return agentType.endsWith('_executive') || agentType.endsWith('_condensed')
}

const AGENT_CONFIG: Record<string, { name: string; reportLabel: string; icon: typeof Target; color: string }> = {
  // Consolidated agents (v2.0)
  discovery_guide: { name: 'Discovery Guide', reportLabel: 'Discovery Agent Report', icon: Search, color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400' },
  insight_analyst: { name: 'Insight Analyst', reportLabel: 'Insight Analysis Report', icon: Target, color: 'text-cyan-600 bg-cyan-100 dark:bg-cyan-900/30 dark:text-cyan-400' },
  initiative_builder: { name: 'Initiative Builder', reportLabel: 'Initiative Builder Report', icon: FileText, color: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400' },
  requirements_generator: { name: 'Requirements Generator', reportLabel: 'Requirements Report', icon: ListChecks, color: 'text-rose-600 bg-rose-100 dark:bg-rose-900/30 dark:text-rose-400' },
  // Legacy agents
  discovery_prep: { name: 'Discovery Prep', reportLabel: 'Discovery Prep Report', icon: FileText, color: 'text-orange-600 bg-orange-100 dark:bg-orange-900/30 dark:text-orange-400' },
  triage: { name: 'Triage', reportLabel: 'Triage Report', icon: Target, color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400' },
  discovery_planner: { name: 'Discovery Planner', reportLabel: 'Discovery Planner Report', icon: Search, color: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400' },
  coverage_tracker: { name: 'Coverage Tracker', reportLabel: 'Coverage Report', icon: BarChart, color: 'text-purple-600 bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400' },
  insight_extractor: { name: 'Insight Extractor', reportLabel: 'Insight Extraction Report', icon: Target, color: 'text-cyan-600 bg-cyan-100 dark:bg-cyan-900/30 dark:text-cyan-400' },
  consolidator: { name: 'Consolidator', reportLabel: 'Consolidation Report', icon: FileText, color: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400' },
  synthesizer: { name: 'Synthesizer', reportLabel: 'Synthesis Report', icon: FileText, color: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400' },
  strategist: { name: 'Strategist', reportLabel: 'Strategy Report', icon: Target, color: 'text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400' },
  prd_generator: { name: 'PRD Generator', reportLabel: 'PRD Report', icon: FileText, color: 'text-rose-600 bg-rose-100 dark:bg-rose-900/30 dark:text-rose-400' },
  tech_evaluation: { name: 'Tech Evaluation', reportLabel: 'Tech Evaluation Report', icon: Cpu, color: 'text-indigo-600 bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-400' },
  // Executive Summary variants (v3.0 - extracts decision-forcing elements)
  triage_executive: { name: 'Triage (Executive)', reportLabel: 'Triage Executive Summary', icon: Minimize2, color: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400' },
  discovery_planner_executive: { name: 'Discovery (Executive)', reportLabel: 'Discovery Executive Summary', icon: Minimize2, color: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-400' },
  coverage_tracker_executive: { name: 'Coverage (Executive)', reportLabel: 'Coverage Executive Summary', icon: Minimize2, color: 'text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-400' },
  insight_extractor_executive: { name: 'Insight (Executive)', reportLabel: 'Insight Executive Summary', icon: Minimize2, color: 'text-cyan-600 bg-cyan-50 dark:bg-cyan-900/20 dark:text-cyan-400' },
  consolidator_executive: { name: 'Consolidator (Executive)', reportLabel: 'Consolidation Executive Summary', icon: Minimize2, color: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400' },
  synthesizer_executive: { name: 'Synthesizer (Executive)', reportLabel: 'Synthesis Executive Summary', icon: Minimize2, color: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400' },
  tech_evaluation_executive: { name: 'Tech Eval (Executive)', reportLabel: 'Tech Eval Executive Summary', icon: Minimize2, color: 'text-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 dark:text-indigo-400' },
  // Legacy condensed variants (for backwards compatibility)
  triage_condensed: { name: 'Triage (Condensed)', reportLabel: 'Triage Condensed Summary', icon: Minimize2, color: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400' },
  discovery_planner_condensed: { name: 'Discovery (Condensed)', reportLabel: 'Discovery Condensed Summary', icon: Minimize2, color: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-400' },
  coverage_tracker_condensed: { name: 'Coverage (Condensed)', reportLabel: 'Coverage Condensed Summary', icon: Minimize2, color: 'text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-400' },
  insight_extractor_condensed: { name: 'Insight (Condensed)', reportLabel: 'Insight Condensed Summary', icon: Minimize2, color: 'text-cyan-600 bg-cyan-50 dark:bg-cyan-900/20 dark:text-cyan-400' },
  consolidator_condensed: { name: 'Consolidator (Condensed)', reportLabel: 'Consolidation Condensed Summary', icon: Minimize2, color: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400' },
  synthesizer_condensed: { name: 'Synthesizer (Condensed)', reportLabel: 'Synthesis Condensed Summary', icon: Minimize2, color: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400' },
  tech_evaluation_condensed: { name: 'Tech Eval (Condensed)', reportLabel: 'Tech Eval Condensed Summary', icon: Minimize2, color: 'text-indigo-600 bg-indigo-50 dark:bg-indigo-900/20 dark:text-indigo-400' },
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
  const displayType = getDisplayAgentType(output.agent_type)
  const config = AGENT_CONFIG[displayType] || { name: displayType, reportLabel: `${displayType} Report`, icon: FileText, color: 'text-slate-600 bg-slate-100' }
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
          {output.synthesis_mode === 'multi_pass' && (
            <span className="px-1.5 py-0.5 text-xs rounded bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
              Multi-Pass
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
  onClose,
  onDelete,
  initiativeId,
  initiativeTitle,
  onRefresh
}: {
  output: Output
  onClose: () => void
  onDelete?: (outputId: string) => Promise<void>
  initiativeId: string
  initiativeTitle?: string
  onRefresh: () => void
}) {
  const { session } = useAuth()
  const contentRef = useRef<HTMLDivElement>(null)
  const [copied, setCopied] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [generatingSummary, setGeneratingSummary] = useState(false)
  const [summaryStatus, setSummaryStatus] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'output' | 'notes'>('output')
  // Create Tasks state
  const [showCreateTasks, setShowCreateTasks] = useState(false)
  const [selectedTaskIndices, setSelectedTaskIndices] = useState<Set<number>>(new Set())
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [linkedProjects, setLinkedProjects] = useState<Array<{ id: string; title: string }>>([])
  const [creatingTasks, setCreatingTasks] = useState(false)
  const [createTasksResult, setCreateTasksResult] = useState<{ count: number } | null>(null)
  const displayType = getDisplayAgentType(output.agent_type)
  const config = AGENT_CONFIG[displayType] || { name: displayType, reportLabel: `${displayType} Report`, icon: FileText, color: 'text-slate-600 bg-slate-100' }
  const Icon = config.icon
  const hasNotes = output.synthesis_mode === 'multi_pass' && output.synthesis_notes
  const isExecutiveSummary = displayType?.endsWith('_executive') || displayType?.endsWith('_condensed')

  const handleDelete = async () => {
    if (!onDelete) return
    if (!confirm(`Delete this ${config.name} output (v${output.version})? This cannot be undone.`)) return

    setDeleting(true)
    try {
      await onDelete(output.id)
    } catch (err) {
      console.error('Failed to delete output:', err)
      alert('Failed to delete output')
    } finally {
      setDeleting(false)
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(output.content_markdown)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const docTitle = initiativeTitle
    ? `${initiativeTitle} - ${config.reportLabel}`
    : output.title || config.reportLabel

  const handleDownload = () => {
    const blob = new Blob([output.content_markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const filename = docTitle.replace(/[^a-zA-Z0-9-_ ]/g, '').replace(/\s+/g, '-')
    a.download = `${filename}_v${output.version}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleDownloadPDF = () => {
    const contentEl = contentRef.current
    if (!contentEl) return

    const title = `${docTitle} v${output.version}`
    const date = new Date(output.created_at).toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric'
    })

    const printWindow = window.open('', '_blank')
    if (!printWindow) return

    printWindow.document.write(`<!DOCTYPE html>
<html>
<head>
  <title>${title}</title>
  <style>
    @page { margin: 1in; size: letter; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      color: #1e293b;
      line-height: 1.6;
      max-width: 100%;
      padding: 0;
      margin: 0;
    }
    .header {
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 12px;
      margin-bottom: 24px;
    }
    .header h1 { font-size: 22px; margin: 0 0 4px 0; color: #0f172a; }
    .header .meta { font-size: 12px; color: #64748b; }
    h1 { font-size: 20px; margin: 24px 0 12px; }
    h2 { font-size: 17px; margin: 20px 0 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
    h3 { font-size: 14px; margin: 16px 0 8px; }
    p { margin: 8px 0; font-size: 13px; }
    ul, ol { margin: 8px 0; padding-left: 24px; font-size: 13px; }
    li { margin: 4px 0; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 12px; }
    th, td { border: 1px solid #cbd5e1; padding: 6px 10px; text-align: left; }
    th { background: #f1f5f9; font-weight: 600; }
    tr:nth-child(even) { background: #f8fafc; }
    code { background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
    pre { background: #f1f5f9; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; }
    pre code { background: none; padding: 0; }
    blockquote { border-left: 3px solid #cbd5e1; margin: 12px 0; padding: 4px 16px; color: #475569; }
    strong { color: #0f172a; }
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 16px 0; }
    .mermaid-placeholder { display: none; }
    @media print {
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>${title}</h1>
    <div class="meta">${date}</div>
  </div>
  ${contentEl.innerHTML}
</body>
</html>`)
    printWindow.document.close()

    // Wait for content to render, then trigger print once
    let printed = false
    printWindow.onload = () => {
      if (!printed) {
        printed = true
        printWindow.print()
      }
    }
    // Fallback for browsers that don't fire onload reliably
    setTimeout(() => {
      if (!printed) {
        printed = true
        printWindow.print()
      }
    }, 500)
  }

  const handleExecutiveSummary = async () => {
    setGeneratingSummary(true)
    setSummaryStatus('Extracting decision-forcing elements...')

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/disco/initiatives/${initiativeId}/outputs/${output.id}/condense`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session?.access_token}`,
          },
        }
      )

      if (!response.ok) {
        throw new Error(`Executive summary generation failed: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response stream')

      const decoder = new TextDecoder()
      let buffer = ''

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
              setSummaryStatus(dataLine.slice(6))
            }
          } else if (line.startsWith('event: complete')) {
            setSummaryStatus('Executive summary complete!')
            setTimeout(() => {
              setGeneratingSummary(false)
              setSummaryStatus(null)
              onRefresh()
            }, 1000)
          } else if (line.startsWith('event: error')) {
            const dataLine = lines[lines.indexOf(line) + 1]
            throw new Error(dataLine?.slice(6) || 'Unknown error')
          }
        }
      }
    } catch (err) {
      console.error('Executive summary failed:', err)
      setSummaryStatus(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
      setTimeout(() => {
        setGeneratingSummary(false)
        setSummaryStatus(null)
      }, 3000)
    }
  }

  // Determine if this output has taskable items
  const stateChanges = output.throughline_resolution?.state_changes || []
  const nextAction = output.throughline_resolution?.so_what?.next_human_action
  const hasTaskableItems = stateChanges.length > 0 || !!nextAction

  const handleOpenCreateTasks = async () => {
    // Initialize all indices as selected
    const allIndices = new Set<number>()
    stateChanges.forEach((_, i) => allIndices.add(i))
    if (nextAction) allIndices.add(stateChanges.length) // next_human_action gets index after state_changes
    setSelectedTaskIndices(allIndices)
    setCreateTasksResult(null)
    setShowCreateTasks(true)

    // Fetch initiative projects
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/disco/initiatives/${initiativeId}/projects`,
        {
          headers: {
            'Authorization': `Bearer ${session?.access_token}`,
          },
        }
      )
      if (response.ok) {
        const data = await response.json()
        setLinkedProjects(data.projects || [])
      }
    } catch {
      // Projects are optional - continue without them
    }
  }

  const toggleTaskIndex = (index: number) => {
    setSelectedTaskIndices(prev => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  const handleCreateTasks = async () => {
    setCreatingTasks(true)
    try {
      const result = await apiPost<{ success: boolean; count: number; tasks: unknown[] }>(
        `/api/disco/initiatives/${initiativeId}/create-tasks-from-resolution`,
        {
          output_id: output.id,
          project_id: selectedProjectId || undefined,
          selected_indices: Array.from(selectedTaskIndices).sort(),
        }
      )
      setCreateTasksResult({ count: result.count })
    } catch (err) {
      console.error('Failed to create tasks:', err)
      alert('Failed to create tasks. Please try again.')
    } finally {
      setCreatingTasks(false)
    }
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
              {docTitle}
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
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              onBlur={() => setTimeout(() => setShowExportMenu(false), 150)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md transition-colors"
            >
              <Download className="w-4 h-4" />
              Export
              <ChevronDown className="w-3 h-3" />
            </button>
            {showExportMenu && (
              <div className="absolute right-0 top-full mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg py-1 z-50 min-w-[140px]">
                <button
                  onClick={() => { handleDownload(); setShowExportMenu(false) }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <FileText className="w-4 h-4" />
                  Markdown (.md)
                </button>
                <button
                  onClick={() => { handleDownloadPDF(); setShowExportMenu(false) }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  PDF (.pdf)
                </button>
              </div>
            )}
          </div>
          {!isExecutiveSummary && (
            <button
              onClick={handleExecutiveSummary}
              disabled={generatingSummary}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-md transition-colors disabled:opacity-50"
              title="Extract decision-forcing elements: leverage point, feedback loop, decision, first action, blocker"
            >
              {generatingSummary ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {summaryStatus || 'Generating...'}
                </>
              ) : (
                <>
                  <Minimize2 className="w-4 h-4" />
                  Executive Summary
                </>
              )}
            </button>
          )}
          {onDelete && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          )}
        </div>
      </div>

      {/* Summary badges */}
      {(output.recommendation || output.tier_routing || output.confidence_level || (output.output_format && output.output_format !== 'comprehensive')) && (
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
      {output.executive_summary && activeTab === 'output' && (
        <div className="px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Executive Summary
          </h4>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {output.executive_summary}
          </p>
        </div>
      )}

      {/* Throughline Resolution Panel */}
      {output.throughline_resolution && activeTab === 'output' && (
        <div className="px-4 py-3 bg-indigo-50/50 dark:bg-indigo-900/10 border-b border-indigo-200 dark:border-indigo-800/50">
          <h4 className="text-sm font-semibold text-indigo-700 dark:text-indigo-300 mb-3">
            Throughline Resolution
          </h4>

          {/* Hypothesis Resolutions */}
          {output.throughline_resolution.hypothesis_resolutions && output.throughline_resolution.hypothesis_resolutions.length > 0 && (
            <div className="mb-3">
              <h5 className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5 uppercase tracking-wide">Hypotheses</h5>
              <div className="space-y-1">
                {output.throughline_resolution.hypothesis_resolutions.map((hr, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="font-mono text-xs text-slate-400 w-8">{hr.hypothesis_id}</span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      hr.status === 'confirmed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                      hr.status === 'refuted' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                      'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                    }`}>
                      {hr.status}
                    </span>
                    {hr.evidence_summary && (
                      <span className="text-xs text-slate-500 dark:text-slate-400 truncate">{hr.evidence_summary}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gap Statuses */}
          {output.throughline_resolution.gap_statuses && output.throughline_resolution.gap_statuses.length > 0 && (
            <div className="mb-3">
              <h5 className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5 uppercase tracking-wide">Gaps</h5>
              <div className="space-y-1">
                {output.throughline_resolution.gap_statuses.map((gs, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="font-mono text-xs text-slate-400 w-8">{gs.gap_id}</span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      gs.status === 'addressed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                      gs.status === 'unaddressed' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                      'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                    }`}>
                      {gs.status.replace('_', ' ')}
                    </span>
                    {gs.findings && (
                      <span className="text-xs text-slate-500 dark:text-slate-400 truncate">{gs.findings}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* So What? */}
          {output.throughline_resolution.so_what && (
            <div className="p-2.5 bg-white/50 dark:bg-slate-800/50 rounded-lg border border-indigo-200 dark:border-indigo-800/50">
              <h5 className="text-xs font-medium text-indigo-600 dark:text-indigo-400 mb-1.5">So What?</h5>
              {output.throughline_resolution.so_what.state_change_proposed && (
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">
                  <span className="font-medium">State Change:</span> {output.throughline_resolution.so_what.state_change_proposed}
                </p>
              )}
              {output.throughline_resolution.so_what.next_human_action && (
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">
                  <span className="font-medium">Next Action:</span> {output.throughline_resolution.so_what.next_human_action}
                </p>
              )}
              {output.throughline_resolution.so_what.kill_test && (
                <p className="text-xs text-red-600 dark:text-red-400">
                  <span className="font-medium">Kill Test:</span> {output.throughline_resolution.so_what.kill_test}
                </p>
              )}
            </div>
          )}

          {/* Create Tasks from State Changes */}
          {hasTaskableItems && (
            <div className="mt-3">
              {!showCreateTasks && !createTasksResult && (
                <button
                  onClick={handleOpenCreateTasks}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 rounded-md transition-colors"
                >
                  <ListChecks className="w-3.5 h-3.5" />
                  Create Tasks from State Changes
                </button>
              )}

              {showCreateTasks && !createTasksResult && (
                <div className="p-3 bg-white/70 dark:bg-slate-800/70 rounded-lg border border-indigo-200 dark:border-indigo-800/50">
                  <h5 className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Select items to create as tasks:
                  </h5>
                  <div className="space-y-1.5 mb-3">
                    {stateChanges.map((sc, i) => (
                      <label key={i} className="flex items-start gap-2 cursor-pointer group">
                        <button
                          onClick={() => toggleTaskIndex(i)}
                          className="mt-0.5 flex-shrink-0 text-indigo-500 dark:text-indigo-400"
                        >
                          {selectedTaskIndices.has(i) ? (
                            <CheckSquare className="w-4 h-4" />
                          ) : (
                            <Square className="w-4 h-4 text-slate-400" />
                          )}
                        </button>
                        <div className="flex-1 min-w-0">
                          <span className="text-xs text-slate-700 dark:text-slate-300 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                            {sc.description}
                          </span>
                          {(sc.owner || sc.deadline) && (
                            <span className="text-xs text-slate-400 ml-1">
                              {sc.owner && `(${sc.owner})`}
                              {sc.deadline && ` due ${sc.deadline}`}
                            </span>
                          )}
                        </div>
                      </label>
                    ))}
                    {nextAction && (
                      <label className="flex items-start gap-2 cursor-pointer group">
                        <button
                          onClick={() => toggleTaskIndex(stateChanges.length)}
                          className="mt-0.5 flex-shrink-0 text-indigo-500 dark:text-indigo-400"
                        >
                          {selectedTaskIndices.has(stateChanges.length) ? (
                            <CheckSquare className="w-4 h-4" />
                          ) : (
                            <Square className="w-4 h-4 text-slate-400" />
                          )}
                        </button>
                        <div className="flex-1 min-w-0">
                          <span className="text-xs text-slate-700 dark:text-slate-300 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                            {nextAction}
                          </span>
                          <span className="ml-1 px-1.5 py-0.5 text-[10px] rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                            Next Action
                          </span>
                        </div>
                      </label>
                    )}
                  </div>

                  {/* Optional project selector */}
                  {linkedProjects.length > 0 && (
                    <div className="mb-3">
                      <label className="text-xs text-slate-500 dark:text-slate-400 block mb-1">
                        Link to project (optional):
                      </label>
                      <select
                        value={selectedProjectId}
                        onChange={(e) => setSelectedProjectId(e.target.value)}
                        className="w-full text-xs px-2 py-1.5 rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300"
                      >
                        <option value="">No project</option>
                        {linkedProjects.map((p) => (
                          <option key={p.id} value={p.id}>{p.title}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleCreateTasks}
                      disabled={creatingTasks || selectedTaskIndices.size === 0}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {creatingTasks ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          Creating...
                        </>
                      ) : (
                        <>
                          <ListChecks className="w-3.5 h-3.5" />
                          Create {selectedTaskIndices.size} Task{selectedTaskIndices.size !== 1 ? 's' : ''}
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => setShowCreateTasks(false)}
                      className="px-3 py-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {createTasksResult && (
                <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800/50">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                    <span className="text-xs font-medium text-green-700 dark:text-green-400">
                      Created {createTasksResult.count} task{createTasksResult.count !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <a
                    href="/tasks"
                    className="inline-flex items-center gap-1 mt-1.5 text-xs text-green-600 dark:text-green-400 hover:underline"
                  >
                    View in Tasks
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Source Outputs - show what previous outputs were used */}
      {output.source_outputs && output.source_outputs.length > 0 && activeTab === 'output' && (
        <div className="px-4 py-2 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Built on:{' '}
            {output.source_outputs.map((src, i) => (
              <span key={src.id}>
                {i > 0 && ', '}
                <span className="font-medium">{AGENT_CONFIG[src.agent_type]?.name || src.agent_type}</span>
                <span className="text-slate-400"> v{src.version}</span>
              </span>
            ))}
          </span>
        </div>
      )}

      {/* Tabs for multi-pass outputs */}
      {hasNotes && (
        <div className="flex border-b border-slate-200 dark:border-slate-700">
          <button
            onClick={() => setActiveTab('output')}
            className={`px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === 'output'
                ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400 -mb-px'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            Output
          </button>
          <button
            onClick={() => setActiveTab('notes')}
            className={`px-4 py-2.5 text-sm font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'notes'
                ? 'text-amber-600 dark:text-amber-400 border-b-2 border-amber-600 dark:border-amber-400 -mb-px'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            Synthesis Notes
            <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
              Multi-Pass
            </span>
          </button>
        </div>
      )}

      {/* Full Content */}
      <div className="p-4 max-h-[calc(100vh-350px)] min-h-[400px] overflow-y-auto">
        {activeTab === 'output' ? (
          <div ref={contentRef} className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  const language = match ? match[1] : ''
                  const content = String(children).replace(/\n$/, '')

                  // Handle mermaid diagrams
                  if (language === 'mermaid') {
                    return <MermaidDiagram chart={content} />
                  }

                  // Regular code block
                  const isInline = !className
                  return isInline ? (
                    <code className={className} {...props}>{children}</code>
                  ) : (
                    <pre className="bg-slate-100 dark:bg-slate-800 p-4 rounded overflow-x-auto">
                      <code className={className} {...props}>{children}</code>
                    </pre>
                  )
                }
              } as Components}
            >
              {output.content_markdown}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
              <p className="text-sm text-amber-800 dark:text-amber-200">
                <strong>About this report:</strong> This synthesis was created using multi-pass analysis
                (3 Sonnet passes at different temperatures + Opus meta-synthesis). The notes below explain
                which pass contributed what insights and why.
              </p>
            </div>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  const language = match ? match[1] : ''
                  const content = String(children).replace(/\n$/, '')

                  if (language === 'mermaid') {
                    return <MermaidDiagram chart={content} />
                  }

                  const isInline = !className
                  return isInline ? (
                    <code className={className} {...props}>{children}</code>
                  ) : (
                    <pre className="bg-slate-100 dark:bg-slate-800 p-4 rounded overflow-x-auto">
                      <code className={className} {...props}>{children}</code>
                    </pre>
                  )
                }
              } as Components}
            >
              {output.synthesis_notes || ''}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

export default function OutputViewer({
  initiativeId,
  initiativeTitle,
  outputs,
  selectedOutput,
  onSelectOutput,
  onRefresh,
  onDelete
}: OutputViewerProps) {
  // Track which agent sections are expanded (default: all collapsed)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({})

  const toggleSection = (agentType: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [agentType]: !prev[agentType]
    }))
  }

  // Group outputs by BASE agent type (executive/condensed variants grouped with parent)
  const outputsByType = outputs.reduce((acc, output) => {
    const agentType = output.agent_type || 'unknown'
    const baseType = getBaseAgentType(agentType)
    if (!acc[baseType]) {
      acc[baseType] = []
    }
    acc[baseType].push(output)
    return acc
  }, {} as Record<string, Output[]>)

  // Sort agent types by workflow order
  const sortedAgentTypes = Object.keys(outputsByType).sort((a, b) => {
    const indexA = AGENT_ORDER.indexOf(a)
    const indexB = AGENT_ORDER.indexOf(b)
    // Unknown agents go to the end
    if (indexA === -1 && indexB === -1) return a.localeCompare(b)
    if (indexA === -1) return 1
    if (indexB === -1) return -1
    return indexA - indexB
  })

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
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 space-y-1">
          {sortedAgentTypes.map((agentType) => {
            const typeOutputs = outputsByType[agentType]
            const config = AGENT_CONFIG[agentType] || { name: agentType, icon: FileText, color: 'text-slate-600 bg-slate-100' }
            const Icon = config.icon
            const isExpanded = expandedSections[agentType] || false
            const latestOutput = typeOutputs[0] // Most recent (already sorted by created_at desc)

            return (
              <div key={agentType} className="border-b border-slate-100 dark:border-slate-700 last:border-b-0 pb-1 last:pb-0">
                <button
                  onClick={() => toggleSection(agentType)}
                  className="w-full flex items-center gap-2 px-2 py-2 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-md transition-colors"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                  <div className={`p-1 rounded ${config.color}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300 flex-1 text-left">
                    {config.name}
                  </span>
                  <span className="text-xs text-slate-400 dark:text-slate-500">
                    {typeOutputs.length} {typeOutputs.length === 1 ? 'output' : 'outputs'}
                  </span>
                  {latestOutput?.recommendation && (
                    <span className={`px-1.5 py-0.5 text-xs rounded ${
                      latestOutput.recommendation === 'GO'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : latestOutput.recommendation === 'NO-GO'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                    }`}>
                      {latestOutput.recommendation}
                    </span>
                  )}
                </button>
                {isExpanded && (
                  <div className="ml-6 space-y-1 mt-1">
                    {typeOutputs.map((output) => (
                      <OutputListItem
                        key={output.id}
                        output={output}
                        selected={selectedOutput?.id === output.id}
                        onClick={() => onSelectOutput(output)}
                      />
                    ))}
                  </div>
                )}
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
            onDelete={onDelete}
            initiativeId={initiativeId}
            initiativeTitle={initiativeTitle}
            onRefresh={onRefresh}
          />
        ) : (
          <div className="flex items-center justify-center min-h-[400px] h-[calc(100vh-350px)] bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-lg">
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
