'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { flushSync } from 'react-dom'
import {
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  Loader2,
  Zap,
  FileText,
  Target,
  Search,
  BarChart,
  Cpu
} from 'lucide-react'
import { apiGet } from '@/lib/api'
import { authenticatedFetch } from '@/lib/api'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Document {
  id: string
  filename: string
  document_type: string
}

interface AgentType {
  type: string
  name: string
  version: string
  description: string
  estimated_time: string
  output_type: string
}

interface AgentRunnerProps {
  initiativeId: string
  canRun: boolean
  documents: Document[]
  onComplete: (output: any) => void
}

const AGENT_ICONS: Record<string, typeof Target> = {
  triage: Target,
  discovery_planner: Search,
  coverage_tracker: BarChart,
  synthesizer: FileText,
  tech_evaluation: Cpu,
}

// Fun status messages to show while waiting
const FUN_STATUS_MESSAGES = [
  "Cooking up insights...",
  "Flibbergibberting the data...",
  "Consulting the oracle...",
  "Percolating ideas...",
  "Wrangling requirements...",
  "Synthesizing brilliance...",
  "Channeling product wisdom...",
  "Contemplating the universe...",
  "Herding stakeholder cats...",
  "Brewing analysis...",
  "Crunching the numbers...",
  "Pondering deeply...",
  "Summoning insights...",
  "Marinating thoughts...",
  "Distilling knowledge...",
  "Calibrating genius...",
  "Making coffee...",
  "Cracking knuckles...",
  "Sighing deeply...",
  "Gazing out the window at the mountains...",
  "Getting a snack...",
  "Popping a wheelie...",
  "Looking casually over my shoulder...",
]

// Workflow guidance for each agent
const AGENT_WORKFLOW: Record<string, {
  when: string
  inputs: string[]
  outputs: string
  prerequisites: string[]
}> = {
  triage: {
    when: "First step - run this when you have initial request details",
    inputs: [
      "Request description or intake document",
      "Any context about the requester or business area"
    ],
    outputs: "GO/NO-GO recommendation with tier routing (ELT/Solutions/Self-Serve) and confidence-tagged ROI",
    prerequisites: []
  },
  discovery_planner: {
    when: "After Triage returns GO - before conducting discovery meetings",
    inputs: [
      "Triage output (auto-included)",
      "Any pre-existing documentation about the initiative"
    ],
    outputs: "Structured discovery plan with type-specific questions, quantification gates, and meeting agenda",
    prerequisites: ["Triage (GO recommendation)"]
  },
  coverage_tracker: {
    when: "After discovery meetings - before synthesis",
    inputs: [
      "Discovery Planner output (auto-included)",
      "Meeting transcripts and notes (upload to Documents)",
      "Interview summaries, stakeholder feedback"
    ],
    outputs: "Gap analysis with RED/YELLOW/GREEN flags, contradiction map, and 3M waste diagnosis",
    prerequisites: ["Triage", "Discovery Planner", "Discovery meeting notes uploaded"]
  },
  synthesizer: {
    when: "After Coverage Tracker shows GREEN (no blocking red flags)",
    inputs: [
      "All previous outputs (auto-included)",
      "All discovery documents"
    ],
    outputs: "Complete PRD with persona-specific briefs (Finance, Engineering, Sales, Executive)",
    prerequisites: ["Triage", "Discovery Planner", "Coverage Tracker (GREEN status)"]
  },
  tech_evaluation: {
    when: "After synthesis - when evaluating implementation options",
    inputs: [
      "Synthesizer output (auto-included)",
      "Technical constraints documentation",
      "Vendor/platform information if available"
    ],
    outputs: "Platform recommendations with confidence-tagged effort estimates and build vs. buy analysis",
    prerequisites: ["Synthesizer output"]
  }
}

export default function AgentRunner({
  initiativeId,
  canRun,
  documents,
  onComplete
}: AgentRunnerProps) {
  const [agents, setAgents] = useState<AgentType[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [streamContent, setStreamContent] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [completed, setCompleted] = useState(false)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [startTime, setStartTime] = useState<number | null>(null)
  const [funMessageIndex, setFunMessageIndex] = useState(0)

  const contentRef = useRef<HTMLDivElement>(null)

  // Load available agents
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const result = await apiGet<{ success: boolean; agents: AgentType[] }>('/api/purdy/agents')
        setAgents(result.agents || [])
      } catch (err) {
        console.error('Failed to load agents:', err)
      }
    }
    loadAgents()
  }, [])

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

  // Rotate fun messages while waiting for content
  useEffect(() => {
    if (!running || streamContent) return

    const interval = setInterval(() => {
      setFunMessageIndex(prev => (prev + 1) % FUN_STATUS_MESSAGES.length)
    }, 3000)

    return () => clearInterval(interval)
  }, [running, streamContent])

  const formatElapsedTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
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
    setFunMessageIndex(Math.floor(Math.random() * FUN_STATUS_MESSAGES.length))

    try {
      const response = await authenticatedFetch(
        `/api/purdy/initiatives/${initiativeId}/runs`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_type: selectedAgent
          }),
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

        // Track indices of data lines that belong to typed events (to skip them)
        const skipIndices = new Set<number>()

        // First pass: find all event: lines and mark their data lines
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].startsWith('event: ')) {
            // The next line should be the data for this event
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

            // Get the next data line
            if (i + 1 < lines.length && lines[i + 1].startsWith('data: ')) {
              const data = lines[i + 1].slice(6)

              if (eventType === 'status') {
                flushSync(() => setStatus(data))
              } else if (eventType === 'complete') {
                try {
                  const result = JSON.parse(data)
                  flushSync(() => {
                    setCompleted(true)
                    setStatus('Complete!')
                  })
                  // Signal completion - parent will reload full outputs list
                  onComplete(result)
                } catch (e) {
                  console.error('Failed to parse complete event:', e)
                }
              } else if (eventType === 'error') {
                flushSync(() => setError(data))
              }
            }
          } else if (line.startsWith('data: ') && !skipIndices.has(i)) {
            // Regular content (not part of a typed event) - use flushSync for immediate rendering
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

  const selectedAgentInfo = agents.find(a => a.type === selectedAgent)

  return (
    <div className="space-y-6">
      {/* Agent Selection */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Select Agent
        </h3>

        <div className="space-y-2">
          {agents.map((agent) => {
            const Icon = AGENT_ICONS[agent.type] || Zap
            const isSelected = selectedAgent === agent.type
            const workflow = AGENT_WORKFLOW[agent.type]

            return (
              <div key={agent.type} className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
                {/* Agent Header - Clickable */}
                <button
                  onClick={() => setSelectedAgent(isSelected ? null : agent.type)}
                  disabled={running}
                  className={`w-full flex items-center gap-3 p-4 text-left transition-all ${
                    isSelected
                      ? 'bg-indigo-50 dark:bg-indigo-900/20 border-b border-indigo-200 dark:border-indigo-800'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  } ${running ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className={`p-2 rounded-lg flex-shrink-0 ${
                    isSelected
                      ? 'bg-indigo-100 dark:bg-indigo-900/40'
                      : 'bg-slate-100 dark:bg-slate-700'
                  }`}>
                    <Icon className={`w-5 h-5 ${
                      isSelected
                        ? 'text-indigo-600 dark:text-indigo-400'
                        : 'text-slate-500 dark:text-slate-400'
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`font-medium ${
                        isSelected
                          ? 'text-indigo-900 dark:text-indigo-100'
                          : 'text-slate-900 dark:text-white'
                      }`}>
                        {agent.name}
                      </span>
                      <span className="text-xs text-slate-400">{agent.version}</span>
                      <span className="text-xs text-slate-400 ml-auto">
                        Est. {agent.estimated_time}
                      </span>
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                      {agent.description}
                    </p>
                  </div>
                  <ChevronDown className={`w-5 h-5 text-slate-400 flex-shrink-0 transition-transform ${
                    isSelected ? 'rotate-180' : ''
                  }`} />
                </button>

                {/* Expanded Workflow Details */}
                {isSelected && workflow && (
                  <div className="p-4 bg-slate-50 dark:bg-slate-900/50">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                          When to Run
                        </h4>
                        <p className="text-sm text-slate-700 dark:text-slate-300">
                          {workflow.when}
                        </p>
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                          Output
                        </h4>
                        <p className="text-sm text-slate-700 dark:text-slate-300">
                          {workflow.outputs}
                        </p>
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                          Required Inputs
                        </h4>
                        <ul className="text-sm text-slate-700 dark:text-slate-300 list-disc list-inside space-y-0.5">
                          {workflow.inputs.map((input, i) => (
                            <li key={i}>{input}</li>
                          ))}
                        </ul>
                      </div>
                      {workflow.prerequisites.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                            Prerequisites
                          </h4>
                          <ul className="text-sm text-slate-700 dark:text-slate-300 list-disc list-inside space-y-0.5">
                            {workflow.prerequisites.map((prereq, i) => (
                              <li key={i}>{prereq}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Run Button */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
          <div className="text-sm text-slate-500 dark:text-slate-400">
            {documents.length === 0 ? (
              <span className="text-amber-600 dark:text-amber-400">
                Upload documents first for better analysis
              </span>
            ) : (
              <span>Using {documents.length} document(s) as context</span>
            )}
          </div>

          <button
            onClick={runAgent}
            disabled={!canRun || !selectedAgent || running}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {running ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Running...
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
          <p className="text-sm text-amber-600 dark:text-amber-400 mt-2">
            You need editor access to run agents
          </p>
        )}
      </div>

      {/* Output Stream - Shows during and after agent run */}
      {(running || streamContent || error) && (
        <div className="bg-white dark:bg-slate-800 border-2 border-indigo-200 dark:border-indigo-800 rounded-lg overflow-hidden shadow-lg">
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
                {selectedAgentInfo?.name || 'Agent'} Output
              </span>

              <span className="text-sm text-slate-500 dark:text-slate-400">
                {status}
              </span>

              {running && elapsedTime > 0 && (
                <span className="text-sm text-slate-400 dark:text-slate-500 font-mono">
                  {formatElapsedTime(elapsedTime)}
                </span>
              )}
            </div>

            {running && (
              <span className="text-xs bg-indigo-100 dark:bg-indigo-800 text-indigo-600 dark:text-indigo-300 px-3 py-1 rounded-full">
                {streamContent ? 'Streaming...' : FUN_STATUS_MESSAGES[funMessageIndex]}
              </span>
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
            className="p-4 max-h-[600px] overflow-y-auto bg-slate-50 dark:bg-slate-900/50"
          >
            {streamContent ? (
              <div className="prose prose-sm dark:prose-invert max-w-none prose-table:border-collapse prose-table:w-full prose-th:border prose-th:border-slate-300 prose-th:dark:border-slate-600 prose-th:bg-slate-100 prose-th:dark:bg-slate-700 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-td:border prose-td:border-slate-300 prose-td:dark:border-slate-600 prose-td:px-3 prose-td:py-2">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamContent}</ReactMarkdown>
              </div>
            ) : running ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mb-4" />
                <p className="text-lg text-slate-600 dark:text-slate-300 font-medium transition-all duration-300">
                  {FUN_STATUS_MESSAGES[funMessageIndex]}
                </p>
                {elapsedTime > 20 && (
                  <p className="text-sm text-slate-400 dark:text-slate-500 mt-3 max-w-md">
                    Deep analysis takes time - Opus is reading all your documents carefully
                  </p>
                )}
              </div>
            ) : null}
          </div>

          {/* Character count for debugging */}
          {streamContent && (
            <div className="px-4 py-2 text-xs text-slate-400 dark:text-slate-500 border-t border-slate-200 dark:border-slate-700">
              {streamContent.length.toLocaleString()} characters generated
            </div>
          )}
        </div>
      )}
    </div>
  )
}
