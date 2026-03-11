'use client'

import { useState, useEffect, useRef } from 'react'
import { flushSync } from 'react-dom'
import {
  Play,
  CheckCircle,
  Loader2,
  FileText,
  Search,
  Lightbulb,
  Boxes,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  RefreshCw,
  Clock,
  Map,
  LayoutGrid,
  TreeDeciduous,
  BookOpen,
} from 'lucide-react'
import { apiGet, authenticatedFetch } from '@/lib/api'
import ReactMarkdown, { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

// ============================================================================
// TYPES
// ============================================================================

interface AgentOutput {
  id: string
  agent_type: string
  version: number
  title?: string
  recommendation?: string
  confidence_level?: string
  executive_summary?: string
  content_markdown: string
  created_at: string
}

interface ProjectAgentPanelProps {
  projectId: string
}

// ============================================================================
// AGENT CONFIG
// ============================================================================

const PROJECT_AGENTS: Record<string, {
  icon: typeof Search
  color: string
  name: string
  description: string
  order: number
}> = {
  discovery_guide: {
    icon: Search,
    color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400',
    name: 'Discovery Guide',
    description: 'Analyzes current vs desired state, identifies knowledge gaps',
    order: 1,
  },
  insight_analyst: {
    icon: Lightbulb,
    color: 'text-cyan-600 bg-cyan-100 dark:bg-cyan-900/30 dark:text-cyan-400',
    name: 'Insight Analyst',
    description: 'Extracts patterns and creates decision document',
    order: 2,
  },
  initiative_builder: {
    icon: Boxes,
    color: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400',
    name: 'Initiative Builder',
    description: 'Evaluates solution approaches, scores options',
    order: 3,
  },
  requirements_generator: {
    icon: FileText,
    color: 'text-rose-600 bg-rose-100 dark:bg-rose-900/30 dark:text-rose-400',
    name: 'Requirements Generator',
    description: 'Produces PRD with technical recommendations',
    order: 4,
  },
}

const AGENT_ORDER = ['discovery_guide', 'insight_analyst', 'initiative_builder', 'requirements_generator']

// ============================================================================
// COMPONENT
// ============================================================================

export default function ProjectAgentPanel({ projectId }: ProjectAgentPanelProps) {
  const [outputs, setOutputs] = useState<AgentOutput[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [streamContent, setStreamContent] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [completed, setCompleted] = useState(false)
  const [expandedOutputs, setExpandedOutputs] = useState<Set<string>>(new Set())
  const [activeGuide, setActiveGuide] = useState<string | null>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  // Auto-scroll during streaming
  useEffect(() => {
    if (running && streamContent && contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight
    }
  }, [streamContent, running])

  // Load existing outputs
  const loadOutputs = async () => {
    try {
      const result = await apiGet<{ success: boolean; outputs: AgentOutput[] }>(
        `/api/projects/${projectId}/agents/outputs`
      )
      if (result.success) {
        setOutputs(result.outputs || [])
      }
    } catch (err) {
      console.error('Failed to load agent outputs:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOutputs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  // Get latest output for an agent type
  const getLatestOutput = (agentType: string): AgentOutput | null => {
    const agentOutputs = outputs.filter(o => o.agent_type === agentType)
    if (agentOutputs.length === 0) return null
    return agentOutputs.sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0]
  }

  // Get all outputs for an agent type (for version history)
  const getOutputVersions = (agentType: string): AgentOutput[] => {
    return outputs
      .filter(o => o.agent_type === agentType)
      .sort((a, b) => b.version - a.version)
  }

  // Run an agent
  const handleRunAgent = async (agentType: string) => {
    setSelectedAgent(agentType)
    setRunning(true)
    setStreamContent('')
    setStatus('Starting...')
    setError(null)
    setCompleted(false)

    try {
      const response = await authenticatedFetch(
        `/api/projects/${projectId}/agents/run`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ agent_type: agentType }),
          timeout: 300000,
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

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        // Track indices of data lines that belong to typed events
        const skipIndices = new Set<number>()
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].startsWith('event: ')) {
            if (i + 1 < lines.length && lines[i + 1].startsWith('data: ')) {
              skipIndices.add(i + 1)
            }
          }
        }

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i]

          if (line.startsWith('event: ')) {
            const eventType = line.slice(7).trim()

            if (i + 1 < lines.length && lines[i + 1].startsWith('data: ')) {
              const data = lines[i + 1].slice(6)

              if (eventType === 'status') {
                flushSync(() => setStatus(data))
              } else if (eventType === 'complete') {
                try {
                  JSON.parse(data)
                  flushSync(() => {
                    setCompleted(true)
                    setStatus('Complete!')
                  })
                  // Reload outputs to get the new one
                  await loadOutputs()
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
    }
  }

  const toggleOutputExpanded = (agentType: string) => {
    setExpandedOutputs(prev => {
      const next = new Set(prev)
      if (next.has(agentType)) {
        next.delete(agentType)
      } else {
        next.add(agentType)
      }
      return next
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        <span className="ml-2 text-sm text-slate-500">Loading agent outputs...</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Guidance */}
      <div className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 rounded-lg px-3 py-2">
        For best results: Discovery Guide → Insight Analyst → Initiative Builder → Requirements Generator (PRD).
        Each agent automatically sees prior outputs when run in sequence.
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 gap-3">
        {AGENT_ORDER.map((agentType) => {
          const config = PROJECT_AGENTS[agentType]
          const Icon = config.icon
          const latestOutput = getLatestOutput(agentType)
          const versions = getOutputVersions(agentType)
          const isRunningThis = running && selectedAgent === agentType
          const isExpanded = expandedOutputs.has(agentType)

          return (
            <div
              key={agentType}
              className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden"
            >
              {/* Agent Card Header */}
              <div className="p-3">
                <div className="flex items-start gap-2.5">
                  <div className={`p-1.5 rounded-md ${config.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <h4 className="text-sm font-medium text-slate-900 dark:text-white truncate">
                        {config.name}
                      </h4>
                      {latestOutput && (
                        <CheckCircle className="w-3.5 h-3.5 text-green-500 shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
                      {config.description}
                    </p>
                  </div>
                </div>

                {/* Run button and version info */}
                <div className="flex items-center justify-between mt-2.5">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleRunAgent(agentType)}
                      disabled={running}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                        running
                          ? 'bg-slate-100 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                          : 'bg-indigo-600 text-white hover:bg-indigo-700'
                      }`}
                    >
                      {isRunningThis ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Play className="w-3 h-3" />
                      )}
                      {isRunningThis ? 'Running...' : latestOutput ? 'Re-run' : 'Run'}
                    </button>

                    {latestOutput && (
                      <span className="text-xs text-slate-400">
                        v{latestOutput.version}
                      </span>
                    )}
                  </div>

                  {/* Expand/collapse output */}
                  {latestOutput && (
                    <button
                      onClick={() => toggleOutputExpanded(agentType)}
                      className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 flex items-center gap-0.5"
                    >
                      {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      Output
                    </button>
                  )}
                </div>
              </div>

              {/* Expanded Output View */}
              {isExpanded && latestOutput && (
                <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-3 max-h-64 overflow-y-auto">
                  {/* Version selector if multiple */}
                  {versions.length > 1 && (
                    <div className="flex items-center gap-1 mb-2 text-xs text-slate-400">
                      <Clock className="w-3 h-3" />
                      {versions.length} versions
                    </div>
                  )}
                  {latestOutput.recommendation && (
                    <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium mb-2 ${
                      latestOutput.recommendation === 'GO'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : latestOutput.recommendation === 'NO-GO'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                    }`}>
                      {latestOutput.recommendation}
                    </div>
                  )}
                  <div className="prose prose-xs dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {latestOutput.content_markdown.slice(0, 2000) + (latestOutput.content_markdown.length > 2000 ? '\n\n...' : '')}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Streaming Output Area */}
      {(running || streamContent || error) && selectedAgent && (
        <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
          <div className="bg-slate-50 dark:bg-slate-800/50 px-4 py-2 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {running && <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />}
              {completed && <CheckCircle className="w-4 h-4 text-green-500" />}
              {error && <AlertCircle className="w-4 h-4 text-red-500" />}
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {PROJECT_AGENTS[selectedAgent]?.name || selectedAgent}
              </span>
            </div>
            {running && (
              <span className="text-xs text-slate-400">{status}</span>
            )}
          </div>

          <div ref={contentRef} className="p-4 max-h-96 overflow-y-auto">
            {error ? (
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            ) : streamContent ? (
              <div className="prose prose-sm dark:prose-invert max-w-none prose-table:border-collapse prose-table:w-full prose-th:border prose-th:border-slate-300 prose-th:dark:border-slate-600 prose-th:bg-slate-100 prose-th:dark:bg-slate-700 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-td:border prose-td:border-slate-300 prose-td:dark:border-slate-600 prose-td:px-3 prose-td:py-2">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ className, children, ...props }) {
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
                <p className="text-sm text-slate-600 dark:text-slate-300">{status}</p>
              </div>
            ) : null}
          </div>

          {streamContent && (
            <div className="bg-slate-50 dark:bg-slate-800/50 px-4 py-2 border-t border-slate-200 dark:border-slate-700 text-xs text-slate-400">
              {streamContent.length.toLocaleString()} characters generated
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {outputs.length === 0 && !running && !streamContent && (
        <div className="text-center py-6 text-sm text-slate-500 dark:text-slate-400">
          No agent outputs yet. Run an agent above to analyze this project.
        </div>
      )}

      {/* Guides Section */}
      <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
        <button
          onClick={() => setActiveGuide(activeGuide ? null : 'workflow')}
          className="flex items-center justify-between w-full px-4 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
        >
          <span className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            Maps and Guides
          </span>
          {activeGuide ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>

        {activeGuide && (
          <div className="border-t border-slate-200 dark:border-slate-700">
            {/* Guide Selector Pills */}
            <div className="flex flex-wrap gap-1.5 px-4 py-2.5 bg-slate-50 dark:bg-slate-800/50">
              {([
                { key: 'workflow', label: 'Workflow Map', icon: Map },
                { key: 'lifecycle', label: 'Discovery to Delivery', icon: ChevronRight },
                { key: 'platform-map', label: 'Platform Map', icon: LayoutGrid },
                { key: 'platform-tree', label: 'Decision Tree', icon: TreeDeciduous },
              ] as const).map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveGuide(key)}
                  className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full border transition-colors ${
                    activeGuide === key
                      ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 border-indigo-200 dark:border-indigo-700'
                      : 'bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
                  }`}
                >
                  <Icon className="w-3 h-3" />
                  {label}
                </button>
              ))}
            </div>

            {/* Guide Content */}
            <div className="bg-white dark:bg-slate-800 overflow-hidden" style={{ height: '400px' }}>
              {activeGuide === 'workflow' && (
                <iframe
                  src="/disco-process-map.html"
                  className="w-full h-full border-0"
                  title="DISCO Workflow Map"
                />
              )}
              {activeGuide === 'lifecycle' && (
                <iframe
                  src="/discovery-to-delivery.html"
                  className="w-full h-full border-0"
                  title="Discovery to Delivery Lifecycle"
                />
              )}
              {activeGuide === 'platform-map' && (
                <iframe
                  src="/platform-process-map.html"
                  className="w-full h-full border-0"
                  title="AI Platform Selection Process Map"
                />
              )}
              {activeGuide === 'platform-tree' && (
                <iframe
                  src="/platform-decision-tree.html"
                  className="w-full h-full border-0"
                  title="AI Platform Selection Decision Tree"
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
