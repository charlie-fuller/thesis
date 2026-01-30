'use client'

import { useState, useEffect, useRef, useCallback, useId } from 'react'
import { flushSync } from 'react-dom'
import {
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Loader2,
  Zap,
  FileText,
  Target,
  Search,
  BarChart,
  Cpu,
  Lightbulb,
  Boxes,
  Users,
  MessageSquare,
  ClipboardCheck,
  ThumbsUp
} from 'lucide-react'
import { apiGet } from '@/lib/api'
import { authenticatedFetch } from '@/lib/api'
import TagSelector from '@/components/TagSelector'
import ReactMarkdown, { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

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

// Agent config with icons and colors (matches OutputViewer for consistency)
const AGENT_CONFIG: Record<string, { icon: typeof Target; color: string }> = {
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

// Workflow guidance for each agent (v4.0 - consulting quality bar)
const AGENT_WORKFLOW: Record<string, {
  when: string
  inputs: string[]
  outputs: string
  prerequisites: string[]
}> = {
  discovery_prep: {
    when: "Pre-Triage - run when you have raw stakeholder documents (interviews, spreadsheets, meeting notes)",
    inputs: [
      "Interview transcripts or notes",
      "Spreadsheets (project lists, prioritization matrices)",
      "Meeting notes, strategy documents, email threads"
    ],
    outputs: "Meeting Prep Guide with scored project cards, assumptions, and confirmation questions - OR Context Request if insufficient input",
    prerequisites: []
  },
  triage: {
    when: "First step - run when you have initial request details",
    inputs: [
      "Request description or intake document",
      "Any context about the requester or business area"
    ],
    outputs: "GO/NO-GO/INVESTIGATE decision with conviction - 250 words max",
    prerequisites: []
  },
  discovery_planner: {
    when: "After Triage returns GO - designs discovery humans will execute",
    inputs: [
      "Triage output (auto-included)",
      "Any pre-existing documentation about the initiative"
    ],
    outputs: "Session plans with agendas, key questions, and quantification gates - 350 words max",
    prerequisites: ["Triage (GO recommendation)"]
  },
  coverage_tracker: {
    when: "Run iteratively - during workshop breaks, after each session, before synthesis",
    inputs: [
      "Discovery Planner output (auto-included)",
      "Meeting transcripts (partial or complete)",
      "Any discovery artifacts uploaded"
    ],
    outputs: "READY/GAPS/CRITICAL verdict with specific gaps and next steps - 280 words max",
    prerequisites: ["Discovery Planner", "At least one discovery session transcript"]
  },
  insight_extractor: {
    when: "After Coverage Tracker shows READY - before Synthesizer",
    inputs: [
      "All discovery transcripts and documents",
      "Coverage Tracker output (auto-included)"
    ],
    outputs: "Structured insights with evidence quotes, patterns, and surprises - 500 words max",
    prerequisites: ["Coverage Tracker (READY status)", "Discovery transcripts uploaded"]
  },
  consolidator: {
    when: "After Insight Extractor - creates the decision document",
    inputs: [
      "Insight Extractor output (auto-included)",
      "All previous outputs"
    ],
    outputs: "Decision document with leverage point, evidence, blockers, first action - 900 words max",
    prerequisites: ["Insight Extractor output"]
  },
  // NOTE: synthesizer removed (soft deprecated) - use consolidator instead
  strategist: {
    when: "After Consolidator - transforms insights into initiative bundles",
    inputs: [
      "Consolidator output (auto-included)",
      "All discovery insights and context"
    ],
    outputs: "Scored initiative bundles with clustering, dependencies, and recommendations",
    prerequisites: ["Consolidator output"]
  },
  tech_evaluation: {
    when: "After Synthesizer - when evaluating implementation options",
    inputs: [
      "Synthesizer output (auto-included)",
      "Technical constraints documentation",
      "Vendor/platform information if available"
    ],
    outputs: "Platform recommendation with architecture diagram and confidence-tagged estimates",
    prerequisites: ["Synthesizer output"]
  },
  prd_generator: {
    when: "After Strategist - transforms bundles into engineering-ready PRDs",
    inputs: [
      "Strategist bundle output (auto-included)",
      "All discovery insights and context"
    ],
    outputs: "Structured PRD with user stories, acceptance criteria, and technical requirements",
    prerequisites: ["Strategist output"]
  }
}

// Human-in-the-Loop configuration for each agent
// Defines what human action is expected AFTER running each agent
const HITL_CONFIG: Record<string, {
  stage: string
  stageColor: string
  action: string
  details: string
  icon: typeof Users
}> = {
  discovery_prep: {
    stage: 'Pre-Discovery',
    stageColor: 'text-orange-600 bg-orange-100 dark:bg-orange-900/30',
    action: 'Review prep guide or provide more context',
    details: 'If you received a Meeting Prep Guide, review the scored project cards and assumptions before your planning session. Use the confirmation questions to validate assumptions with stakeholders. If you received a Context Request, gather the requested materials and re-run.',
    icon: ClipboardCheck
  },
  triage: {
    stage: 'Discovery',
    stageColor: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30',
    action: 'Review GO/NO-GO decision',
    details: 'After Triage, review the recommendation. If GO, proceed to Discovery Planner. If NO-GO or INVESTIGATE, address the concerns before continuing. This is your first gate to avoid wasting effort on non-viable initiatives.',
    icon: ThumbsUp
  },
  discovery_planner: {
    stage: 'Discovery',
    stageColor: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30',
    action: 'Execute the discovery sessions',
    details: 'The Discovery Planner outputs interview guides and session agendas. YOU must conduct these sessions with stakeholders, record them, and upload the transcripts. The agents cannot do discovery - only humans can gather the ground truth.',
    icon: MessageSquare
  },
  coverage_tracker: {
    stage: 'Discovery',
    stageColor: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30',
    action: 'Address gaps or proceed when READY',
    details: 'Coverage Tracker tells you if discovery is complete. If GAPS, conduct more sessions targeting the missing areas. If CRITICAL, you may need to revisit assumptions. Only proceed to Insight Extractor when status is READY.',
    icon: ClipboardCheck
  },
  insight_extractor: {
    stage: 'Intelligence',
    stageColor: 'text-cyan-600 bg-cyan-100 dark:bg-cyan-900/30',
    action: 'Verify insights match your understanding',
    details: 'Review the extracted insights. Do they capture what you heard in discovery? Are any key points missing? You can add documents or re-run if critical insights are missing before proceeding to Consolidator.',
    icon: ClipboardCheck
  },
  consolidator: {
    stage: 'Intelligence',
    stageColor: 'text-cyan-600 bg-cyan-100 dark:bg-cyan-900/30',
    action: 'Validate the decision document',
    details: 'The Consolidator produces a 900-word decision document. Review the GO/NO-GO recommendation, leverage point, metrics, and first action. This document should be ready to share with stakeholders. Edit if needed before proceeding.',
    icon: ClipboardCheck
  },
  // NOTE: synthesizer removed (soft deprecated) - use consolidator instead
  strategist: {
    stage: 'Synthesis',
    stageColor: 'text-green-600 bg-green-100 dark:bg-green-900/30',
    action: 'Approve or reject initiative bundles',
    details: 'The Strategist clusters insights into initiative bundles with scores. YOU must review each bundle and decide: Approve (proceed to PRD), Reject (remove from consideration), or Merge/Split bundles. This is a critical human decision point.',
    icon: ThumbsUp
  },
  prd_generator: {
    stage: 'Capabilities',
    stageColor: 'text-rose-600 bg-rose-100 dark:bg-rose-900/30',
    action: 'Review PRD with engineering',
    details: 'The PRD Generator creates an engineering-ready document. Share with your technical team for feasibility review. They may identify constraints or alternatives that require iteration before Tech Evaluation.',
    icon: Users
  },
  tech_evaluation: {
    stage: 'Capabilities',
    stageColor: 'text-indigo-600 bg-indigo-100 dark:bg-indigo-900/30',
    action: 'Make build/buy/partner decision',
    details: 'Tech Evaluation provides platform recommendations with confidence-tagged estimates. YOU must decide the implementation approach and secure commitments from engineering and vendors. This is the final gate before execution.',
    icon: ThumbsUp
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
  const [outputFormat, setOutputFormat] = useState<'comprehensive' | 'executive' | 'brief'>('comprehensive')
  const [multiPass, setMultiPass] = useState(true)  // Default ON for synthesizer
  const [passesCompleted, setPassesCompleted] = useState(0)
  const [currentPassLabel, setCurrentPassLabel] = useState('')
  const [hitlExpanded, setHitlExpanded] = useState(false)

  // KB tag selection (for Discovery Prep)
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
      // Multi-pass consolidation/synthesis runs 4 Claude calls and needs much longer timeout
      const isMultiPass = (selectedAgent === 'consolidator' || selectedAgent === 'synthesizer') && multiPass
      const timeoutMs = isMultiPass ? 600000 : 300000 // 10 min for multi-pass, 5 min for single

      const requestBody: Record<string, unknown> = {
        agent_type: selectedAgent,
        output_format: outputFormat,
        multi_pass: isMultiPass
      }

      // Add KB tags for Discovery Prep
      if (selectedAgent === 'discovery_prep' && selectedKbTags.size > 0) {
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
              } else if (eventType === 'pass_complete') {
                // Multi-pass: a synthesis pass completed
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
      {/* HITL Guidance Panel */}
      {selectedAgent && HITL_CONFIG[selectedAgent] && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg overflow-hidden">
          <button
            onClick={() => setHitlExpanded(!hitlExpanded)}
            className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-amber-100/50 dark:hover:bg-amber-900/30 transition-colors"
          >
            <div className="p-1.5 rounded-md bg-amber-200 dark:bg-amber-800">
              <Users className="w-4 h-4 text-amber-700 dark:text-amber-300" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-amber-900 dark:text-amber-100">
                  Human-in-the-Loop Required
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${HITL_CONFIG[selectedAgent].stageColor}`}>
                  {HITL_CONFIG[selectedAgent].stage}
                </span>
              </div>
              <p className="text-sm text-amber-700 dark:text-amber-300 mt-0.5">
                After running: {HITL_CONFIG[selectedAgent].action}
              </p>
            </div>
            {hitlExpanded ? (
              <ChevronDown className="w-5 h-5 text-amber-500 flex-shrink-0" />
            ) : (
              <ChevronRight className="w-5 h-5 text-amber-500 flex-shrink-0" />
            )}
          </button>

          {hitlExpanded && (
            <div className="px-4 pb-4 pt-2 border-t border-amber-200 dark:border-amber-800">
              <div className="flex items-start gap-3">
                {(() => {
                  const HITLIcon = HITL_CONFIG[selectedAgent].icon
                  return <HITLIcon className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                })()}
                <div>
                  <p className="text-sm text-amber-800 dark:text-amber-200">
                    {HITL_CONFIG[selectedAgent].details}
                  </p>
                  <div className="mt-3 p-3 bg-white dark:bg-slate-800 rounded-md border border-amber-200 dark:border-amber-700">
                    <p className="text-xs font-medium text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1">
                      DISCo Workflow
                    </p>
                    <div className="flex items-center gap-1 text-xs">
                      <span className={selectedAgent === 'triage' || selectedAgent === 'discovery_planner' || selectedAgent === 'coverage_tracker' ? 'font-bold text-blue-600' : 'text-slate-400'}>Discovery</span>
                      <span className="text-slate-300">→</span>
                      <span className={selectedAgent === 'insight_extractor' || selectedAgent === 'consolidator' || selectedAgent === 'synthesizer' ? 'font-bold text-cyan-600' : 'text-slate-400'}>Intelligence</span>
                      <span className="text-slate-300">→</span>
                      <span className={selectedAgent === 'strategist' ? 'font-bold text-green-600' : 'text-slate-400'}>Synthesis</span>
                      <span className="text-slate-300">→</span>
                      <span className={selectedAgent === 'prd_generator' || selectedAgent === 'tech_evaluation' ? 'font-bold text-rose-600' : 'text-slate-400'}>Capabilities</span>
                      <span className="text-slate-300">→</span>
                      <span className="text-slate-400">Operationalize</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Agent Selection */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Select Agent
        </h3>

        <div className="space-y-2">
          {agents.map((agent) => {
            const config = AGENT_CONFIG[agent.type] || { icon: Zap, color: 'text-slate-600 bg-slate-100 dark:bg-slate-700 dark:text-slate-400' }
            const Icon = config.icon
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
                      ? 'bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  } ${running ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className={`p-2 rounded-lg flex-shrink-0 ${config.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-900 dark:text-white">
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

        {/* Output Format Selection */}
        {selectedAgent && (
          <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Output Format
            </h4>
            <div className="space-y-2">
              <label className={`flex items-start gap-3 cursor-pointer p-2 rounded-lg border transition-colors ${
                outputFormat === 'comprehensive'
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30'
                  : 'border-transparent hover:bg-slate-100 dark:hover:bg-slate-700/50'
              }`}>
                <input
                  type="radio"
                  name="outputFormat"
                  value="comprehensive"
                  checked={outputFormat === 'comprehensive'}
                  onChange={() => setOutputFormat('comprehensive')}
                  disabled={running}
                  className="mt-1 w-4 h-4 text-indigo-600 bg-slate-100 dark:bg-slate-700 border-slate-300 dark:border-slate-600 focus:ring-indigo-500 dark:focus:ring-indigo-600"
                />
                <div>
                  <div className="font-medium text-slate-900 dark:text-white">Comprehensive</div>
                  <div className="text-xs text-slate-500">Full detailed analysis with all sections</div>
                </div>
              </label>
              <label className={`flex items-start gap-3 cursor-pointer p-2 rounded-lg border transition-colors ${
                outputFormat === 'executive'
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30'
                  : 'border-transparent hover:bg-slate-100 dark:hover:bg-slate-700/50'
              }`}>
                <input
                  type="radio"
                  name="outputFormat"
                  value="executive"
                  checked={outputFormat === 'executive'}
                  onChange={() => setOutputFormat('executive')}
                  disabled={running}
                  className="mt-1 w-4 h-4 text-indigo-600 bg-slate-100 dark:bg-slate-700 border-slate-300 dark:border-slate-600 focus:ring-indigo-500 dark:focus:ring-indigo-600"
                />
                <div>
                  <div className="font-medium text-slate-900 dark:text-white">Executive Summary</div>
                  <div className="text-xs text-slate-500">Key findings and recommendations only (~50% shorter)</div>
                </div>
              </label>
              <label className={`flex items-start gap-3 cursor-pointer p-2 rounded-lg border transition-colors ${
                outputFormat === 'brief'
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30'
                  : 'border-transparent hover:bg-slate-100 dark:hover:bg-slate-700/50'
              }`}>
                <input
                  type="radio"
                  name="outputFormat"
                  value="brief"
                  checked={outputFormat === 'brief'}
                  onChange={() => setOutputFormat('brief')}
                  disabled={running}
                  className="mt-1 w-4 h-4 text-indigo-600 bg-slate-100 dark:bg-slate-700 border-slate-300 dark:border-slate-600 focus:ring-indigo-500 dark:focus:ring-indigo-600"
                />
                <div>
                  <div className="font-medium text-slate-900 dark:text-white">Brief</div>
                  <div className="text-xs text-slate-500">Decision and next steps only (~80% shorter)</div>
                </div>
              </label>
            </div>
          </div>
        )}

        {/* KB Tag Selection (Discovery Prep) */}
        {selectedAgent === 'discovery_prep' && (
          <div className="mt-4 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
            <h4 className="text-sm font-medium text-orange-900 dark:text-orange-100 mb-2">
              Select Knowledge Base Documents by Tags
            </h4>
            <p className="text-xs text-orange-700 dark:text-orange-300 mb-3">
              Filter KB documents by tags. Documents matching ALL selected tags will be included.
            </p>
            <TagSelector
              selectedTags={selectedKbTags}
              onTagsChange={setSelectedKbTags}
              placeholder="Search tags..."
              showInitiatives={true}
              disabled={running}
            />
            {selectedKbTags.size > 0 && (
              <p className="mt-2 text-xs text-orange-600 dark:text-orange-400">
                Documents with all {selectedKbTags.size} selected tag(s) will be analyzed
              </p>
            )}
          </div>
        )}

        {/* Multi-Pass Toggle (Consolidator/Synthesizer) */}
        {(selectedAgent === 'consolidator' || selectedAgent === 'synthesizer') && (
          <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
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
                  Multi-Pass Synthesis (Recommended)
                </div>
                <div className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                  <strong>How it works:</strong> Runs 3 independent synthesis passes with varying
                  analysis styles (Conservative → Balanced → Exploratory), then uses a senior
                  analyst model to combine the best insights from all three into a unified output.
                </div>
                <div className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                  <strong>Why it&apos;s better:</strong> Conservative pass anchors facts precisely.
                  Balanced pass provides standard framing. Exploratory pass surfaces &quot;elephants&quot;
                  and bolder connections. The meta-synthesis validates and combines them all.
                </div>
                <div className="text-xs text-amber-500 dark:text-amber-500 mt-2 flex items-center gap-2 flex-wrap">
                  <span>~4x runtime</span>
                  <span className="text-amber-400">|</span>
                  <span>~$6-7 cost</span>
                  <span className="text-amber-400">|</span>
                  <span>Higher quality insights</span>
                </div>
              </div>
            </label>
          </div>
        )}

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

              {running && elapsedTime > 0 && (
                <span className="text-sm text-slate-400 dark:text-slate-500 font-mono">
                  {formatElapsedTime(elapsedTime)}
                </span>
              )}
            </div>

            {running && (
              <div className="flex items-center gap-3">
                {/* Multi-pass progress dots */}
                {(selectedAgent === 'consolidator' || selectedAgent === 'synthesizer') && multiPass && (
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
            className="p-4 max-h-[600px] overflow-y-auto bg-slate-50 dark:bg-slate-900/50"
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
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mb-4" />
                <p className="text-lg text-slate-600 dark:text-slate-300 font-medium transition-all duration-300">
                  {status}
                </p>
                {(selectedAgent === 'consolidator' || selectedAgent === 'synthesizer') && multiPass && passesCompleted > 0 && passesCompleted < 3 && (
                  <p className="text-sm text-green-600 dark:text-green-400 mt-3">
                    Completed: {passesCompleted}/3 passes ({currentPassLabel})
                  </p>
                )}
                {(selectedAgent === 'consolidator' || selectedAgent === 'synthesizer') && multiPass && passesCompleted === 3 && (
                  <p className="text-sm text-amber-600 dark:text-amber-400 mt-3">
                    Running meta-synthesis with Opus...
                  </p>
                )}
                {elapsedTime > 20 && !((selectedAgent === 'consolidator' || selectedAgent === 'synthesizer') && multiPass) && (
                  <p className="text-sm text-slate-400 dark:text-slate-500 mt-3 max-w-md">
                    Deep analysis takes time - Opus is reading all your documents carefully
                  </p>
                )}
                {elapsedTime > 60 && (selectedAgent === 'consolidator' || selectedAgent === 'synthesizer') && multiPass && (
                  <p className="text-sm text-slate-400 dark:text-slate-500 mt-3 max-w-md">
                    Multi-pass synthesis runs 4 separate analyses for higher quality results
                  </p>
                )}
              </div>
            ) : null}
          </div>

          {/* Character count and synthesis mode */}
          {streamContent && (
            <div className="px-4 py-2 text-xs text-slate-400 dark:text-slate-500 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between">
              <span>{streamContent.length.toLocaleString()} characters generated</span>
              {(selectedAgent === 'consolidator' || selectedAgent === 'synthesizer') && multiPass && completed && (
                <span className="bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded text-xs">
                  Multi-Pass Synthesis
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
