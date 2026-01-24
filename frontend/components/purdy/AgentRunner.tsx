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

  const runAgent = async () => {
    if (!selectedAgent) return

    setRunning(true)
    setStreamContent('')
    setStatus('Starting...')
    setError(null)
    setCompleted(false)

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

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => {
            const Icon = AGENT_ICONS[agent.type] || Zap
            const isSelected = selectedAgent === agent.type

            return (
              <button
                key={agent.type}
                onClick={() => setSelectedAgent(agent.type)}
                disabled={running}
                className={`flex items-start gap-3 p-4 rounded-lg border text-left transition-all ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                    : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
                } ${running ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div className={`p-2 rounded-lg ${
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
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                    {agent.description}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Est. {agent.estimated_time}
                  </p>
                </div>
              </button>
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
            </div>

            {running && (
              <span className="text-xs bg-indigo-100 dark:bg-indigo-800 text-indigo-600 dark:text-indigo-300 px-2 py-1 rounded-full animate-pulse">
                Generating in real-time...
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
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>{streamContent}</ReactMarkdown>
              </div>
            ) : running ? (
              <div className="text-slate-400 dark:text-slate-500 italic">
                Waiting for agent response...
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
