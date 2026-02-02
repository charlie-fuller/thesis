'use client'

import { useState, useEffect, useRef, useCallback, useId } from 'react'
import { flushSync } from 'react-dom'
import {
  Play,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  Loader2,
  FileText,
  Target,
  Search,
  BarChart,
  Cpu,
  Lightbulb,
  Boxes,
  Lock,
  AlertTriangle,
  RefreshCw
} from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'
import { authenticatedFetch } from '@/lib/api'
import TagSelector from '@/components/TagSelector'
import ReactMarkdown, { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CheckpointPanel, { Checkpoint, ChecklistItem } from './CheckpointPanel'

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

interface Document {
  id: string
  filename: string
  title?: string | null
  document_type?: string
  source_platform?: string
  created_at?: string
}

interface AgentType {
  type: string
  name: string
  version: string
  description: string
  estimated_time: string
  output_type: string
}

interface AgentOutput {
  id: string
  agent_type: string
  version: number
  created_at: string
}

interface AgentRunnerProps {
  initiativeId: string
  canRun: boolean
  documents: Document[]
  outputs?: AgentOutput[]
  onComplete: (output: any) => void
}

// Consolidated agent config (4 agents with checkpoints)
const CONSOLIDATED_AGENTS: Record<string, {
  icon: typeof Target
  color: string
  name: string
  description: string
  checkpointBefore?: number // Which checkpoint must be approved before running
  checkpointAfter: number // Which checkpoint to show after running
}> = {
  discovery_guide: {
    icon: Search,
    color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400',
    name: 'Discovery Guide',
    description: 'Validates problem, plans discovery sessions, tracks coverage',
    checkpointAfter: 1
  },
  insight_analyst: {
    icon: Lightbulb,
    color: 'text-cyan-600 bg-cyan-100 dark:bg-cyan-900/30 dark:text-cyan-400',
    name: 'Insight Analyst',
    description: 'Extracts patterns and creates decision document',
    checkpointBefore: 1,
    checkpointAfter: 2
  },
  initiative_builder: {
    icon: Boxes,
    color: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400',
    name: 'Initiative Builder',
    description: 'Clusters insights into scored initiative bundles',
    checkpointBefore: 2,
    checkpointAfter: 3
  },
  requirements_generator: {
    icon: FileText,
    color: 'text-rose-600 bg-rose-100 dark:bg-rose-900/30 dark:text-rose-400',
    name: 'Requirements Generator',
    description: 'Produces PRD with technical recommendations',
    checkpointBefore: 3,
    checkpointAfter: 4
  }
}

// Ordered list of consolidated agents
const AGENT_ORDER = ['discovery_guide', 'insight_analyst', 'initiative_builder', 'requirements_generator']

// Legacy agent config (for backwards compatibility)
const LEGACY_AGENT_CONFIG: Record<string, { icon: typeof Target; color: string }> = {
  discovery_prep: { icon: FileText, color: 'text-orange-600 bg-orange-100 dark:bg-orange-900/30 dark:text-orange-400' },
  triage: { icon: Target, color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400' },
  discovery_planner: { icon: Search, color: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400' },
  coverage_tracker: { icon: BarChart, color: 'text-purple-600 bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400' },
  insight_extractor: { icon: Lightbulb, color: 'text-cyan-600 bg-cyan-100 dark:bg-cyan-900/30 dark:text-cyan-400' },
  consolidator: { icon: FileText, color: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400' },
  strategist: { icon: Boxes, color: 'text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400' },
  prd_generator: { icon: FileText, color: 'text-rose-600 bg-rose-100 dark:bg-rose-900/30 dark:text-rose-400' },
  tech_evaluation: { icon: Cpu, color: 'text-indigo-600 bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-400' },
}

export default function AgentRunner({
  initiativeId,
  canRun,
  documents,
  outputs = [],
  onComplete
}: AgentRunnerProps) {
  const [agents, setAgents] = useState<AgentType[]>([])
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [streamContent, setStreamContent] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [completed, setCompleted] = useState(false)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [startTime, setStartTime] = useState<number | null>(null)
  const [outputFormat, setOutputFormat] = useState<'comprehensive' | 'executive' | 'brief'>('comprehensive')
  const [multiPass, setMultiPass] = useState(true)
  const [passesCompleted, setPassesCompleted] = useState(0)
  const [currentPassLabel, setCurrentPassLabel] = useState('')
  const [checkpointLoading, setCheckpointLoading] = useState<number | null>(null)

  // KB tag selection (for Discovery Guide)
  const [selectedKbTags, setSelectedKbTags] = useState<Set<string>>(new Set())

  const contentRef = useRef<HTMLDivElement>(null)

  // Load available agents
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const result = await apiGet<{ success: boolean; agents: AgentType[] }>('/api/disco/agents')
        setAgents(result.agents || [])
      } catch (err) {
        console.error('Failed to load agents:', err)
      }
    }
    loadAgents()
  }, [])

  // Load checkpoints
  const loadCheckpoints = useCallback(async () => {
    try {
      const result = await apiGet<{ success: boolean; checkpoints: Checkpoint[] }>(
        `/api/disco/initiatives/${initiativeId}/checkpoints`
      )
      setCheckpoints(result.checkpoints || [])
    } catch (err) {
      console.error('Failed to load checkpoints:', err)
    }
  }, [initiativeId])

  useEffect(() => {
    loadCheckpoints()
  }, [loadCheckpoints])

  // Auto-scroll to bottom of content
  useEffect(() => {
    if (contentRef.current && running) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight
    }
  }, [streamContent, running])

  // Elapsed time timer
  useEffect(() => {
    if (!running || !startTime) return

    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(interval)
  }, [running, startTime])

  const formatElapsedTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }

  // Default checkpoint data for when API hasn't returned yet
  const getDefaultCheckpoint = (num: number): Checkpoint => ({
    id: `default-${num}`,
    checkpoint_number: num,
    status: num === 1 ? 'locked' : 'locked', // First checkpoint starts locked until agent runs
    checklist_items: []
  })

  // Get checkpoint by number - always returns a checkpoint (API data or default)
  const getCheckpoint = (num: number): Checkpoint => {
    const apiCheckpoint = checkpoints.find(c => c.checkpoint_number === num)
    return apiCheckpoint || getDefaultCheckpoint(num)
  }

  // Check if agent is runnable (checkpoint approved)
  const isAgentRunnable = (agentType: string): boolean => {
    const config = CONSOLIDATED_AGENTS[agentType]
    if (!config) return true // Legacy agents always runnable
    if (!config.checkpointBefore) return true // First agent always runnable

    const checkpoint = getCheckpoint(config.checkpointBefore)
    return checkpoint?.status === 'approved'
  }

  // Get agent status info
  const getAgentStatus = (agentType: string): { hasOutput: boolean; version: number; isStale: boolean; staleCount: number } => {
    const agentOutputs = outputs.filter(o => o.agent_type === agentType)
    const latestOutput = agentOutputs.sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0]

    if (!latestOutput) {
      return { hasOutput: false, version: 0, isStale: false, staleCount: 0 }
    }

    // Check for staleness (new docs since last run)
    const outputTime = new Date(latestOutput.created_at).getTime()
    const newDocs = documents.filter(d =>
      d.created_at && new Date(d.created_at).getTime() > outputTime
    )

    return {
      hasOutput: true,
      version: latestOutput.version,
      isStale: newDocs.length > 0,
      staleCount: newDocs.length
    }
  }

  // Approve checkpoint
  const handleApproveCheckpoint = async (checkpointNum: number, notes?: string) => {
    setCheckpointLoading(checkpointNum)
    try {
      const checkpoint = getCheckpoint(checkpointNum)
      const checklistItems = checkpoint?.checklist_items || []

      await apiPost(`/api/disco/initiatives/${initiativeId}/checkpoints/${checkpointNum}/approve`, {
        notes,
        checklist_items: checklistItems
      })
      await loadCheckpoints()
    } catch (err) {
      console.error('Failed to approve checkpoint:', err)
    } finally {
      setCheckpointLoading(null)
    }
  }

  // Reset checkpoint
  const handleResetCheckpoint = async (checkpointNum: number) => {
    setCheckpointLoading(checkpointNum)
    try {
      await apiPost(`/api/disco/initiatives/${initiativeId}/checkpoints/${checkpointNum}/reset`, {})
      await loadCheckpoints()
    } catch (err) {
      console.error('Failed to reset checkpoint:', err)
    } finally {
      setCheckpointLoading(null)
    }
  }

  // Update checklist items
  const handleChecklistChange = (checkpointNum: number, items: ChecklistItem[]) => {
    setCheckpoints(prev => prev.map(c =>
      c.checkpoint_number === checkpointNum
        ? { ...c, checklist_items: items }
        : c
    ))
  }

  const runAgent = async () => {
    if (!selectedAgent) return

    setRunning(true)
    setStreamContent('')
    setStatus('Starting...')
    setError(null)
    setCompleted(false)
    setElapsedTime(0)
    setStartTime(Date.now())
    setPassesCompleted(0)
    setCurrentPassLabel('')

    try {
      // Multi-pass runs need longer timeout
      const isMultiPassAgent = selectedAgent === 'insight_analyst' || selectedAgent === 'initiative_builder'
      const timeoutMs = isMultiPassAgent && multiPass ? 600000 : 300000

      const requestBody: Record<string, unknown> = {
        agent_type: selectedAgent,
        output_format: outputFormat,
        multi_pass: isMultiPassAgent && multiPass
      }

      // Add KB tags for Discovery Guide
      if (selectedAgent === 'discovery_guide' && selectedKbTags.size > 0) {
        requestBody.kb_tags = Array.from(selectedKbTags)
      }

      const response = await authenticatedFetch(
        `/api/disco/initiatives/${initiativeId}/runs`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
          timeout: timeoutMs,
        }
      )

      if (!response.ok) {
        throw new Error('Failed to start agent run')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process SSE events
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        // Track indices of data lines that belong to typed events
        const skipIndices = new Set<number>()

        // First pass: find all event: lines and mark their data lines
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].startsWith('event: ')) {
            if (i + 1 < lines.length && lines[i + 1].startsWith('data: ')) {
              skipIndices.add(i + 1)
            }
          }
        }

        // Second pass: process all lines
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i]

          if (line.startsWith('event: ')) {
            const eventType = line.slice(7).trim()

            if (i + 1 < lines.length && lines[i + 1].startsWith('data: ')) {
              const data = lines[i + 1].slice(6)

              if (eventType === 'status') {
                flushSync(() => setStatus(data))
              } else if (eventType === 'pass_complete') {
                try {
                  const passData = JSON.parse(data)
                  flushSync(() => {
                    setPassesCompleted(passData.pass_number)
                    setCurrentPassLabel(passData.label)
                  })
                } catch (e) {
                  console.error('Failed to parse pass_complete event:', e)
                }
              } else if (eventType === 'complete') {
                try {
                  const result = JSON.parse(data)
                  flushSync(() => {
                    setCompleted(true)
                    setStatus('Complete!')
                  })
                  // Signal completion and reload checkpoints
                  onComplete(result)
                  loadCheckpoints()
                } catch (e) {
                  console.error('Failed to parse complete event:', e)
                }
              } else if (eventType === 'error') {
                flushSync(() => setError(data))
              }
            }
          } else if (line.startsWith('data: ') && !skipIndices.has(i)) {
            const content = line.slice(6)
            flushSync(() => setStreamContent(prev => prev + content))
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Run failed')
    } finally {
      setRunning(false)
      setStartTime(null)
    }
  }

  return (
    <div className="space-y-4">
      {/* Agent Cards with Checkpoint Panels */}
      {AGENT_ORDER.map((agentType, index) => {
        const agent = agents.find(a => a.type === agentType)
        const config = CONSOLIDATED_AGENTS[agentType]
        if (!config || !agent) return null

        const Icon = config.icon
        const isSelected = selectedAgent === agentType
        const canRunAgent = isAgentRunnable(agentType)
        const agentStatus = getAgentStatus(agentType)
        const checkpointAfter = getCheckpoint(config.checkpointAfter)

        return (
          <div key={agentType}>
            {/* Agent Card */}
            <div className={`rounded-lg border-2 overflow-hidden transition-all ${
              !canRunAgent
                ? 'border-slate-200 dark:border-slate-700 opacity-60'
                : isSelected
                ? 'border-indigo-300 dark:border-indigo-700 shadow-md'
                : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
            }`}>
              {/* Agent Header */}
              <button
                onClick={() => canRunAgent && setSelectedAgent(isSelected ? null : agentType)}
                disabled={running || !canRunAgent}
                className={`w-full flex items-center gap-3 p-4 text-left transition-all ${
                  isSelected
                    ? 'bg-indigo-50 dark:bg-indigo-900/20'
                    : 'bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/80'
                } ${!canRunAgent || running ? 'cursor-not-allowed' : 'cursor-pointer'}`}
              >
                {/* Agent number */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  agentStatus.hasOutput
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                    : canRunAgent
                    ? 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500'
                }`}>
                  {agentStatus.hasOutput ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : !canRunAgent ? (
                    <Lock className="w-4 h-4" />
                  ) : (
                    index + 1
                  )}
                </div>

                {/* Icon */}
                <div className={`p-2 rounded-lg flex-shrink-0 ${config.color}`}>
                  <Icon className="w-5 h-5" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900 dark:text-white">
                      {config.name}
                    </span>
                    <span className="text-xs text-slate-400">{agent.version}</span>
                    {agentStatus.hasOutput && (
                      <span className="text-xs text-green-600 dark:text-green-400">
                        v{agentStatus.version}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                    {config.description}
                  </p>
                </div>

                {/* Status indicators */}
                <div className="flex items-center gap-2">
                  {agentStatus.isStale && (
                    <span className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 px-2 py-1 rounded">
                      <AlertTriangle className="w-3 h-3" />
                      {agentStatus.staleCount} new doc{agentStatus.staleCount > 1 ? 's' : ''}
                    </span>
                  )}
                  {!canRunAgent && (
                    <span className="text-xs text-slate-400 px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded">
                      Waiting for checkpoint
                    </span>
                  )}
                </div>

                <ChevronDown className={`w-5 h-5 text-slate-400 flex-shrink-0 transition-transform ${
                  isSelected ? 'rotate-180' : ''
                }`} />
              </button>

              {/* Expanded Agent Panel */}
              {isSelected && (
                <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 p-4 space-y-4">
                  {/* Output Format Selection */}
                  <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                    <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                      Output Format
                    </h4>
                    <div className="flex gap-2 flex-wrap">
                      {(['comprehensive', 'executive', 'brief'] as const).map(format => (
                        <label key={format} className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors ${
                          outputFormat === format
                            ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30'
                            : 'border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700/50'
                        }`}>
                          <input
                            type="radio"
                            name="outputFormat"
                            value={format}
                            checked={outputFormat === format}
                            onChange={() => setOutputFormat(format)}
                            disabled={running}
                            className="w-4 h-4 text-indigo-600"
                          />
                          <span className="text-sm font-medium text-slate-900 dark:text-white capitalize">
                            {format}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* KB Tag Selection (Discovery Guide) */}
                  {selectedAgent === 'discovery_guide' && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                      <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                        Include Knowledge Base Documents
                      </h4>
                      <p className="text-xs text-blue-700 dark:text-blue-300 mb-3">
                        Filter KB documents by tags to include additional context.
                      </p>
                      <TagSelector
                        selectedTags={selectedKbTags}
                        onTagsChange={setSelectedKbTags}
                        placeholder="Search tags..."
                        showInitiatives={true}
                        disabled={running}
                      />
                    </div>
                  )}

                  {/* Multi-Pass Toggle (Insight Analyst, Initiative Builder) */}
                  {(selectedAgent === 'insight_analyst' || selectedAgent === 'initiative_builder') && (
                    <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={multiPass}
                          onChange={(e) => setMultiPass(e.target.checked)}
                          disabled={running}
                          className="mt-1 w-4 h-4 text-amber-600 rounded focus:ring-amber-500"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-amber-900 dark:text-amber-100">
                            Multi-Pass Analysis (Recommended)
                          </div>
                          <div className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                            Runs 3 independent passes (Conservative, Balanced, Exploratory) then combines the best insights.
                          </div>
                          <div className="text-xs text-amber-500 mt-2 flex items-center gap-2 flex-wrap">
                            <span>~4x runtime</span>
                            <span className="text-amber-400">|</span>
                            <span>Higher quality</span>
                          </div>
                        </div>
                      </label>
                    </div>
                  )}

                  {/* Run Button */}
                  <div className="flex items-center justify-between pt-2">
                    <div className="text-sm text-slate-500 dark:text-slate-400">
                      {documents.length === 0 ? (
                        <span className="text-amber-600 dark:text-amber-400">
                          Upload documents first
                        </span>
                      ) : (
                        <span>Using {documents.length} document(s)</span>
                      )}
                    </div>

                    <button
                      onClick={runAgent}
                      disabled={!canRun || running}
                      className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {running ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Running...
                        </>
                      ) : agentStatus.hasOutput ? (
                        <>
                          <RefreshCw className="w-4 h-4" />
                          Re-run Agent
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4" />
                          Run Agent
                        </>
                      )}
                    </button>
                  </div>

                  {!canRun && (
                    <p className="text-sm text-amber-600 dark:text-amber-400">
                      You need editor access to run agents
                    </p>
                  )}

                  {/* Output Stream - Shows within selected agent when running or has output */}
                  {(running || streamContent || error) && (
                    <div className="mt-4 bg-white dark:bg-slate-800 border-2 border-indigo-200 dark:border-indigo-800 rounded-lg overflow-hidden shadow-lg">
                      {/* Status Header */}
                      <div className="flex items-center justify-between gap-3 px-4 py-3 bg-indigo-50 dark:bg-indigo-900/20 border-b border-indigo-200 dark:border-indigo-800">
                        <div className="flex items-center gap-3">
                          {running ? (
                            <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
                          ) : completed ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : error ? (
                            <AlertCircle className="w-5 h-5 text-red-500" />
                          ) : null}

                          <span className="font-medium text-slate-900 dark:text-white">
                            {config.name} Output
                          </span>

                          {running && elapsedTime > 0 && (
                            <span className="text-sm text-slate-400 dark:text-slate-500 font-mono">
                              {formatElapsedTime(elapsedTime)}
                            </span>
                          )}
                        </div>

                        {running && (
                          <div className="flex items-center gap-3">
                            {/* Multi-pass progress dots */}
                            {(agentType === 'insight_analyst' || agentType === 'initiative_builder') && multiPass && (
                              <div className="flex items-center gap-1.5">
                                {[1, 2, 3, 4].map((step) => (
                                  <div
                                    key={step}
                                    className={`w-2.5 h-2.5 rounded-full transition-colors ${
                                      step <= passesCompleted
                                        ? 'bg-green-500'
                                        : step === passesCompleted + 1 && !streamContent
                                        ? 'bg-amber-400 animate-pulse'
                                        : step === 4 && streamContent
                                        ? 'bg-indigo-500 animate-pulse'
                                        : 'bg-slate-300 dark:bg-slate-600'
                                    }`}
                                    title={step <= 3 ? `Pass ${step}` : 'Meta-synthesis'}
                                  />
                                ))}
                                <span className="text-xs text-slate-500 ml-1">
                                  {passesCompleted < 3 ? `Pass ${passesCompleted + 1}/3` : 'Meta-synthesis'}
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Error */}
                      {error && (
                        <div className="px-4 py-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
                          {error}
                        </div>
                      )}

                      {/* Content - Real-time streaming output */}
                      <div
                        ref={contentRef}
                        className="p-4 max-h-[500px] overflow-y-auto bg-slate-50 dark:bg-slate-900/50"
                      >
                        {streamContent ? (
                          <div className="prose prose-sm dark:prose-invert max-w-none prose-table:border-collapse prose-table:w-full prose-th:border prose-th:border-slate-300 prose-th:dark:border-slate-600 prose-th:bg-slate-100 prose-th:dark:bg-slate-700 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-td:border prose-td:border-slate-300 prose-td:dark:border-slate-600 prose-td:px-3 prose-td:py-2">
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
                              {streamContent}
                            </ReactMarkdown>
                          </div>
                        ) : running ? (
                          <div className="flex flex-col items-center justify-center py-8 text-center">
                            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mb-3" />
                            <p className="text-base text-slate-600 dark:text-slate-300 font-medium">
                              {status}
                            </p>
                            {(agentType === 'insight_analyst' || agentType === 'initiative_builder') && multiPass && passesCompleted > 0 && passesCompleted < 3 && (
                              <p className="text-sm text-green-600 dark:text-green-400 mt-2">
                                Completed: {passesCompleted}/3 passes ({currentPassLabel})
                              </p>
                            )}
                            {(agentType === 'insight_analyst' || agentType === 'initiative_builder') && multiPass && passesCompleted === 3 && (
                              <p className="text-sm text-amber-600 dark:text-amber-400 mt-2">
                                Running meta-synthesis...
                              </p>
                            )}
                          </div>
                        ) : null}
                      </div>

                      {/* Character count */}
                      {streamContent && (
                        <div className="px-4 py-2 text-xs text-slate-400 dark:text-slate-500 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between">
                          <span>{streamContent.length.toLocaleString()} characters generated</span>
                          {(agentType === 'insight_analyst' || agentType === 'initiative_builder') && multiPass && completed && (
                            <span className="bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded text-xs">
                              Multi-Pass Synthesis
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Checkpoint Panel (after agent) - Always visible */}
            <div className="my-4 ml-4 border-l-2 border-slate-200 dark:border-slate-700 pl-4">
              <CheckpointPanel
                checkpoint={checkpointAfter}
                onApprove={(notes) => handleApproveCheckpoint(config.checkpointAfter, notes)}
                onReset={() => handleResetCheckpoint(config.checkpointAfter)}
                onChecklistChange={(items) => handleChecklistChange(config.checkpointAfter, items)}
                loading={checkpointLoading === config.checkpointAfter}
                canEdit={canRun}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
