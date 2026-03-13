'use client'

import { useState, useRef, useEffect, useCallback, KeyboardEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useAuth } from '@/contexts/AuthContext'

interface ToolCall {
  tool: string
  input: Record<string, unknown>
  result?: string
}

interface CommandEntry {
  input: string
  output: string
  toolCalls: ToolCall[]
  isError?: boolean
}

const HISTORY_KEY = 'thesis_command_history'
const MODEL_KEY = 'thesis_command_model'
const FONT_SIZE_KEY = 'thesis_command_font_size'
const MAX_HISTORY = 100

const FONT_SIZES = [
  { id: 'xs', label: 'XS', px: '11px' },
  { id: 'sm', label: 'S', px: '13px' },
  { id: 'md', label: 'M', px: '14px' },
  { id: 'lg', label: 'L', px: '16px' },
  { id: 'xl', label: 'XL', px: '18px' },
] as const

type FontSizeId = typeof FONT_SIZES[number]['id']

const MODELS = [
  { id: 'haiku', label: 'Haiku', description: 'Fast' },
  { id: 'sonnet', label: 'Sonnet', description: 'Default' },
  { id: 'opus', label: 'Opus', description: 'Powerful' },
] as const

type ModelId = typeof MODELS[number]['id']

const markdownComponents = {
  table: ({ children, ...props }: React.ComponentProps<'table'>) => (
    <table className="border-collapse my-2 text-sm w-full" {...props}>{children}</table>
  ),
  thead: ({ children, ...props }: React.ComponentProps<'thead'>) => (
    <thead className="border-b border-gray-600" {...props}>{children}</thead>
  ),
  th: ({ children, ...props }: React.ComponentProps<'th'>) => (
    <th className="text-left px-2 py-1 text-gray-300 font-semibold" {...props}>{children}</th>
  ),
  td: ({ children, ...props }: React.ComponentProps<'td'>) => (
    <td className="px-2 py-1 text-gray-200 border-t border-gray-800" {...props}>{children}</td>
  ),
  strong: ({ children, ...props }: React.ComponentProps<'strong'>) => (
    <strong className="text-white font-bold" {...props}>{children}</strong>
  ),
  code: ({ children, className, ...props }: React.ComponentProps<'code'> & { className?: string }) => {
    const isBlock = className?.includes('language-')
    if (isBlock) {
      return (
        <code className="block bg-gray-900 border border-gray-700 rounded p-3 my-2 text-sm overflow-x-auto whitespace-pre" {...props}>
          {children}
        </code>
      )
    }
    return (
      <code className="bg-gray-800 text-green-300 px-1 rounded text-sm" {...props}>{children}</code>
    )
  },
  pre: ({ children, ...props }: React.ComponentProps<'pre'>) => (
    <pre className="my-1" {...props}>{children}</pre>
  ),
  ul: ({ children, ...props }: React.ComponentProps<'ul'>) => (
    <ul className="list-disc list-inside my-1 space-y-0.5" {...props}>{children}</ul>
  ),
  ol: ({ children, ...props }: React.ComponentProps<'ol'>) => (
    <ol className="list-decimal list-inside my-1 space-y-0.5" {...props}>{children}</ol>
  ),
  h2: ({ children, ...props }: React.ComponentProps<'h2'>) => (
    <h2 className="text-white font-bold text-base mt-3 mb-1" {...props}>{children}</h2>
  ),
  h3: ({ children, ...props }: React.ComponentProps<'h3'>) => (
    <h3 className="text-white font-bold text-sm mt-2 mb-1" {...props}>{children}</h3>
  ),
  p: ({ children, ...props }: React.ComponentProps<'p'>) => (
    <p className="my-1" {...props}>{children}</p>
  ),
  hr: (props: React.ComponentProps<'hr'>) => (
    <hr className="border-gray-700 my-2" {...props} />
  ),
}

const WELCOME_MESSAGE = `Welcome to Thesis Command Center.

Type natural language commands to interact with your data.

Examples:
  list tasks                          Show all tasks
  list projects tier 1                Show strategic projects
  create task "Review Q1 budget"      Create a new task
  show dashboard summary              Get counts overview
  search documents "AI strategy"      Search knowledge base
  list stakeholders in Engineering    Filter by department

Press Ctrl+L to clear, Up/Down for history.`

type ExportStep = 'title' | 'location' | 'project' | 'initiative' | null

interface ExportData {
  title: string
  location: string
  projectId: string
  initiativeId: string
}

export default function CommandTerminal() {
  const { session } = useAuth()
  const [history, setHistory] = useState<CommandEntry[]>([])
  const [currentInput, setCurrentInput] = useState('')
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingOutput, setStreamingOutput] = useState('')
  const [streamingToolCalls, setStreamingToolCalls] = useState<ToolCall[]>([])
  const [model, setModel] = useState<ModelId>('sonnet')
  const [fontSize, setFontSize] = useState<FontSizeId>('sm')
  const [exportStep, setExportStep] = useState<ExportStep>(null)
  const exportDataRef = useRef<ExportData>({ title: '', location: '', projectId: '', initiativeId: '' })
  const outputRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Load history and model from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(HISTORY_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) {
          setHistory(parsed.slice(-MAX_HISTORY))
        }
      }
      const savedModel = localStorage.getItem(MODEL_KEY)
      if (savedModel && MODELS.some(m => m.id === savedModel)) {
        setModel(savedModel as ModelId)
      }
      const savedFontSize = localStorage.getItem(FONT_SIZE_KEY)
      if (savedFontSize && FONT_SIZES.some(f => f.id === savedFontSize)) {
        setFontSize(savedFontSize as FontSizeId)
      }
    } catch {
      // Ignore parse errors
    }
  }, [])

  // Save history to localStorage
  useEffect(() => {
    if (history.length > 0) {
      try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-MAX_HISTORY)))
      } catch {
        // Ignore storage errors
      }
    }
  }, [history])

  // Auto-scroll to bottom
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [history, streamingOutput, streamingToolCalls])

  // Focus input on mount and click
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // --- Fuzzy matching ---
  // Score how well `query` matches `target` (higher = better, 0 = no match)
  const fuzzyScore = (query: string, target: string): number => {
    const q = query.toLowerCase().trim()
    const t = target.toLowerCase().trim()
    if (!q || !t) return 0
    // Exact match
    if (q === t) return 100
    // Target contains query as substring
    if (t.includes(q)) return 80 + (q.length / t.length) * 15
    // Query contains target as substring (user typed more than needed)
    if (q.includes(t)) return 70
    // Word-level matching: how many query words appear in target
    const qWords = q.split(/\s+/)
    const tWords = t.split(/\s+/)
    let wordHits = 0
    for (const qw of qWords) {
      if (tWords.some(tw => tw.includes(qw) || qw.includes(tw))) wordHits++
      // Partial word match (handles typos by checking if start matches)
      else if (tWords.some(tw => tw.startsWith(qw.slice(0, 3)) || qw.startsWith(tw.slice(0, 3)))) wordHits += 0.5
    }
    if (wordHits > 0) return 30 + (wordHits / qWords.length) * 40
    // Character overlap ratio (handles typos)
    const qChars = new Set(q.replace(/\s/g, '').split(''))
    const tChars = new Set(t.replace(/\s/g, '').split(''))
    let overlap = 0
    for (const c of qChars) { if (tChars.has(c)) overlap++ }
    const ratio = overlap / Math.max(qChars.size, tChars.size)
    return ratio > 0.5 ? ratio * 30 : 0
  }

  const fuzzyMatch = (query: string, items: Array<{ id: string; name: string }>): { id: string; name: string; score: number } | null => {
    if (!query.trim() || items.length === 0) return null
    // Check for number selection first
    const num = parseInt(query.trim(), 10)
    if (!isNaN(num) && num >= 1 && num <= items.length) {
      return { ...items[num - 1], score: 100 }
    }
    let best: { id: string; name: string; score: number } | null = null
    for (const item of items) {
      const score = fuzzyScore(query, item.name)
      if (score > 0 && (!best || score > best.score)) {
        best = { ...item, score }
      }
    }
    return best && best.score >= 20 ? best : null
  }

  const fuzzyMatchLocation = (query: string, folders: string[]): string | null => {
    if (!query.trim() || folders.length === 0) return null
    let best: { path: string; score: number } | null = null
    for (const folder of folders) {
      // Also match against the last segment of the path
      const segments = folder.split('/')
      const lastSegment = segments[segments.length - 1]
      const fullScore = fuzzyScore(query, folder)
      const segScore = fuzzyScore(query, lastSegment)
      const score = Math.max(fullScore, segScore)
      if (score > 0 && (!best || score > best.score)) {
        best = { path: folder, score }
      }
    }
    return best && best.score >= 20 ? best.path : null
  }

  // --- Export state refs ---
  const projectsRef = useRef<Array<{ id: string; name: string }>>([])
  const initiativesRef = useRef<Array<{ id: string; name: string }>>([])
  const foldersRef = useRef<string[]>([])
  const resolvedProjectRef = useRef<{ id: string; name: string } | null>(null)
  const resolvedInitiativeRef = useRef<{ id: string; name: string } | null>(null)
  const resolvedLocationRef = useRef<string>('')

  const fetchOptions = useCallback(async () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const headers: Record<string, string> = { Authorization: `Bearer ${session?.access_token}` }
    try {
      const [projRes, initRes, folderRes] = await Promise.all([
        fetch(`${apiUrl}/api/projects/`, { headers }),
        fetch(`${apiUrl}/api/disco/initiatives`, { headers }),
        fetch(`${apiUrl}/api/documents/folders`, { headers }),
      ])
      if (projRes.ok) {
        const projects = await projRes.json()
        projectsRef.current = projects
          .filter((p: { status?: string }) => p.status !== 'archived' && p.status !== 'cancelled')
          .map((p: { id: string; name: string }) => ({ id: p.id, name: p.name }))
      }
      if (initRes.ok) {
        const initiatives = await initRes.json()
        initiativesRef.current = (Array.isArray(initiatives) ? initiatives : initiatives.data || [])
          .filter((i: { status?: string }) => i.status !== 'archived' && i.status !== 'cancelled')
          .map((i: { id: string; name: string }) => ({ id: i.id, name: i.name }))
      }
      if (folderRes.ok) {
        const data = await folderRes.json()
        foldersRef.current = (data.folders || []).map((f: { path: string }) => f.path)
      }
    } catch {
      // Continue with empty lists
    }
  }, [session])

  const formatProjectList = () => {
    if (projectsRef.current.length === 0) return '**Link to project?** No active projects found. Press Enter to skip.'
    const list = projectsRef.current.map((p, i) => `  ${i + 1}. ${p.name}`).join('\n')
    return `**Link to project?** Type a name (or number) to match, or Enter to skip.\n\n${list}`
  }

  const formatInitiativeList = () => {
    if (initiativesRef.current.length === 0) return '**Link to initiative?** No active initiatives found. Press Enter to skip.'
    const list = initiativesRef.current.map((i, idx) => `  ${idx + 1}. ${i.name}`).join('\n')
    return `**Link to initiative?** Type a name (or number) to match, or Enter to skip.\n\n${list}`
  }

  const formatLocationPrompt = () => {
    let prompt = '**Location/category** — where should this be filed?'
    if (foldersRef.current.length > 0) {
      const list = foldersRef.current.slice(0, 15).map((f, i) => `  ${i + 1}. ${f}`).join('\n')
      prompt += ` Type a name to match, or Enter to skip.\n\n${list}`
    } else {
      prompt += ' Type a folder name (e.g. `research`, `meeting-notes`), or Enter to skip.'
    }
    return prompt
  }

  const submitExport = useCallback(async () => {
    const { title } = exportDataRef.current
    const location = resolvedLocationRef.current
    const project = resolvedProjectRef.current
    const initiative = resolvedInitiativeRef.current

    if (history.length === 0) {
      setHistory(prev => [...prev, { input: '(saving...)', output: 'Nothing to export — conversation is empty.', toolCalls: [], isError: true }])
      return
    }

    const displayTitle = title || `Command Session ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`

    // Build markdown from conversation history (exclude export wizard entries)
    const lines = [`# ${displayTitle}\n`, `*Exported: ${new Date().toISOString().slice(0, 16).replace('T', ' ')}*\n`]
    for (const entry of history.filter(e => !e.input.startsWith('/export') && !e.input.startsWith('export:'))) {
      lines.push(`---\n## User\n\n${entry.input}\n`)
      if (entry.output) {
        lines.push(`## Assistant\n\n${entry.output}\n`)
      }
    }
    const content = lines.join('\n')

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const body: Record<string, unknown> = { title: displayTitle, content }
      if (location) body.location = location
      if (project) body.project_id = project.id
      if (initiative) body.initiative_id = initiative.id

      const res = await fetch(`${apiUrl}/api/documents/export-to-kb`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify(body),
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Export failed')

      // Build summary with resolved names
      const parts = [`Saved **${displayTitle}**`]
      if (location) parts[0] += ` @ \`${location}\``
      if (project) parts.push(`Linked to project: **${project.name}**`)
      if (initiative) parts.push(`Linked to initiative: **${initiative.name}**`)
      parts.push(`Document ID: \`${data.document_id}\``)

      setHistory(prev => [...prev, { input: 'export: saving...', output: parts.join('\n'), toolCalls: [] }])
    } catch (err) {
      setHistory(prev => [...prev, {
        input: 'export: saving...',
        output: `Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`,
        toolCalls: [],
        isError: true,
      }])
    }
  }, [history, session])

  const handleExportStep = useCallback((input: string) => {
    const value = input.trim()

    switch (exportStep) {
      case 'title': {
        exportDataRef.current.title = value
        setHistory(prev => [...prev, { input: value || '(default)', output: formatLocationPrompt(), toolCalls: [] }])
        setExportStep('location')
        break
      }
      case 'location': {
        if (value) {
          const matched = fuzzyMatchLocation(value, foldersRef.current)
          if (matched) {
            resolvedLocationRef.current = matched
            setHistory(prev => [...prev, { input: value, output: `Matched location: **${matched}**\n\n${formatProjectList()}`, toolCalls: [] }])
          } else {
            // Use the raw input as a new location
            resolvedLocationRef.current = value
            setHistory(prev => [...prev, { input: value, output: `New location: **${value}**\n\n${formatProjectList()}`, toolCalls: [] }])
          }
        } else {
          resolvedLocationRef.current = ''
          setHistory(prev => [...prev, { input: '(skip)', output: formatProjectList(), toolCalls: [] }])
        }
        setExportStep('project')
        break
      }
      case 'project': {
        if (value) {
          const match = fuzzyMatch(value, projectsRef.current)
          if (match) {
            resolvedProjectRef.current = { id: match.id, name: match.name }
            setHistory(prev => [...prev, { input: value, output: `Matched project: **${match.name}**\n\n${formatInitiativeList()}`, toolCalls: [] }])
          } else {
            resolvedProjectRef.current = null
            setHistory(prev => [...prev, { input: value, output: `No matching project found for "${value}". Skipping.\n\n${formatInitiativeList()}`, toolCalls: [], isError: true }])
          }
        } else {
          resolvedProjectRef.current = null
          setHistory(prev => [...prev, { input: '(skip)', output: formatInitiativeList(), toolCalls: [] }])
        }
        setExportStep('initiative')
        break
      }
      case 'initiative': {
        if (value) {
          const match = fuzzyMatch(value, initiativesRef.current)
          if (match) {
            resolvedInitiativeRef.current = { id: match.id, name: match.name }
            setHistory(prev => [...prev, { input: value, output: `Matched initiative: **${match.name}**\n\nExporting...`, toolCalls: [] }])
          } else {
            resolvedInitiativeRef.current = null
            setHistory(prev => [...prev, { input: value, output: `No matching initiative found for "${value}". Skipping.\n\nExporting...`, toolCalls: [], isError: true }])
          }
        } else {
          resolvedInitiativeRef.current = null
          setHistory(prev => [...prev, { input: '(skip)', output: 'Exporting...', toolCalls: [] }])
        }
        setExportStep(null)
        submitExport()
        break
      }
    }
  }, [exportStep, submitExport])

  const startExport = useCallback(async () => {
    if (history.length === 0) {
      setHistory(prev => [...prev, { input: '/export', output: 'Nothing to export — conversation is empty.', toolCalls: [], isError: true }])
      return
    }
    exportDataRef.current = { title: '', location: '', projectId: '', initiativeId: '' }
    resolvedProjectRef.current = null
    resolvedInitiativeRef.current = null
    resolvedLocationRef.current = ''
    await fetchOptions()
    setHistory(prev => [...prev, { input: '/export', output: '**Filename/title** for this export? Press Enter for default.', toolCalls: [] }])
    setExportStep('title')
  }, [history, fetchOptions])

  const handleSubmit = useCallback(async () => {
    const input = currentInput.trim()
    if (!input && !exportStep) return
    if (isStreaming) return

    // Handle export wizard steps
    if (exportStep) {
      setCurrentInput('')
      handleExportStep(input)
      return
    }

    if (!input) return

    // Handle client-side slash commands
    if (input.startsWith('/export')) {
      setCurrentInput('')
      setHistoryIndex(-1)
      startExport()
      return
    }

    if (input === '/clear') {
      setCurrentInput('')
      setHistoryIndex(-1)
      setHistory([])
      localStorage.removeItem(HISTORY_KEY)
      return
    }

    if (input === '/help') {
      setCurrentInput('')
      setHistoryIndex(-1)
      setHistory(prev => [...prev, {
        input: '/help',
        output: [
          '**Available commands:**',
          '- `/export` — Save this conversation to the Knowledge Base',
          '  Walks you through: title, location, project link, initiative link',
          '  Uses fuzzy matching — type naturally, it will find the best match',
          '- `/clear` — Clear conversation history',
          '- `/help` — Show this help',
          '',
          'Or type any question to query the database via AI.',
        ].join('\n'),
        toolCalls: [],
      }])
      return
    }

    setCurrentInput('')
    setHistoryIndex(-1)
    setIsStreaming(true)
    setStreamingOutput('')
    setStreamingToolCalls([])

    const controller = new AbortController()
    abortRef.current = controller

    let fullOutput = ''
    const toolCalls: ToolCall[] = []
    let isError = false

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify({
          message: input,
          model,
          history: history.slice(-10).flatMap(h => [
            { role: 'user', content: h.input },
            { role: 'assistant', content: h.output },
          ]),
        }),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('Stream not available')

      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.substring(6))

            if (data.type === 'token') {
              fullOutput += data.content
              setStreamingOutput(fullOutput)
            } else if (data.type === 'tool_call') {
              const tc: ToolCall = { tool: data.tool, input: data.input }
              toolCalls.push(tc)
              setStreamingToolCalls([...toolCalls])
            } else if (data.type === 'tool_result') {
              // Update the last tool call with result
              if (toolCalls.length > 0) {
                toolCalls[toolCalls.length - 1].result = data.result
                setStreamingToolCalls([...toolCalls])
              }
            } else if (data.type === 'error') {
              fullOutput += data.error
              isError = true
              setStreamingOutput(fullOutput)
            }
          } catch {
            // Skip malformed JSON lines
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        fullOutput += '\n[aborted]'
      } else {
        fullOutput += `Error: ${err instanceof Error ? err.message : 'Unknown error'}`
        isError = true
      }
    } finally {
      setHistory(prev => [...prev, { input, output: fullOutput, toolCalls, isError }])
      setIsStreaming(false)
      setStreamingOutput('')
      setStreamingToolCalls([])
      abortRef.current = null
      // Re-focus input after command completes
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [currentInput, isStreaming, session, history, model, exportStep, handleExportStep, startExport])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleSubmit()
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        const inputs = history.map(h => h.input)
        if (inputs.length === 0) return
        const newIndex = historyIndex === -1 ? inputs.length - 1 : Math.max(0, historyIndex - 1)
        setHistoryIndex(newIndex)
        setCurrentInput(inputs[newIndex])
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        const inputs = history.map(h => h.input)
        if (historyIndex === -1) return
        const newIndex = historyIndex + 1
        if (newIndex >= inputs.length) {
          setHistoryIndex(-1)
          setCurrentInput('')
        } else {
          setHistoryIndex(newIndex)
          setCurrentInput(inputs[newIndex])
        }
      } else if (e.key === 'c' && e.ctrlKey) {
        if (isStreaming && abortRef.current) {
          abortRef.current.abort()
        }
      } else if (e.key === 'l' && e.ctrlKey) {
        e.preventDefault()
        setHistory([])
        localStorage.removeItem(HISTORY_KEY)
      }
    },
    [handleSubmit, history, historyIndex, isStreaming]
  )

  return (
    <div
      className="flex flex-col h-full bg-gray-950 rounded-lg overflow-hidden border border-gray-800"
      onClick={() => {
        // Only refocus input if user hasn't selected text
        const selection = window.getSelection()
        if (!selection || selection.isCollapsed) {
          inputRef.current?.focus()
        }
      }}
    >
      {/* Output area */}
      <div ref={outputRef} className="flex-1 overflow-y-auto p-4 font-mono leading-relaxed" style={{ fontSize: FONT_SIZES.find(f => f.id === fontSize)?.px || '13px' }}>
        {/* Welcome message (only when no history) */}
        {history.length === 0 && !isStreaming && (
          <pre className="text-gray-500 whitespace-pre-wrap mb-4">{WELCOME_MESSAGE}</pre>
        )}

        {/* Command history */}
        {history.map((entry, i) => (
          <div key={i} className="mb-3">
            <div className="flex">
              <span className="text-green-400 mr-2 flex-shrink-0">thesis&gt;</span>
              <span className="text-gray-100">{entry.input}</span>
            </div>
            {entry.toolCalls.length > 0 && (
              <div className="ml-2 mt-1">
                {entry.toolCalls.map((tc, j) => (
                  <div key={j} className="text-yellow-500/70 text-xs">
                    [{tc.tool}] {tc.result || '...'}
                  </div>
                ))}
              </div>
            )}
            <div className={`ml-2 mt-1 ${entry.isError ? 'text-red-400' : 'text-gray-100'} command-markdown`}>
              {entry.isError ? (
                <pre className="whitespace-pre-wrap">{entry.output}</pre>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{entry.output}</ReactMarkdown>
              )}
            </div>
          </div>
        ))}

        {/* Currently streaming */}
        {isStreaming && (
          <div className="mb-3">
            <div className="flex">
              <span className="text-green-400 mr-2 flex-shrink-0">thesis&gt;</span>
              <span className="text-gray-100">{currentInput || history[history.length - 1]?.input}</span>
            </div>
            {streamingToolCalls.length > 0 && (
              <div className="ml-2 mt-1">
                {streamingToolCalls.map((tc, j) => (
                  <div key={j} className="text-yellow-500/70 text-xs">
                    [{tc.tool}] {tc.result || 'executing...'}
                  </div>
                ))}
              </div>
            )}
            {streamingOutput && (
              <div className="ml-2 mt-1 text-gray-100 command-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{streamingOutput}</ReactMarkdown>
              </div>
            )}
            {!streamingOutput && streamingToolCalls.length === 0 && (
              <div className="ml-2 mt-1 text-gray-500 animate-pulse">thinking...</div>
            )}
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="flex items-center px-4 py-3 border-t border-gray-800 bg-gray-900 gap-2">
        <span className="text-green-400 mr-1 font-mono text-sm flex-shrink-0">thesis&gt;</span>
        <input
          ref={inputRef}
          type="text"
          value={currentInput}
          onChange={e => setCurrentInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          className="flex-1 bg-transparent text-gray-100 font-mono text-sm outline-none placeholder-gray-600 disabled:opacity-50"
          placeholder={isStreaming ? 'Processing...' : exportStep ? `Enter ${exportStep} (or press Enter to skip)...` : 'Type a command...'}
          autoComplete="off"
          spellCheck={false}
        />
        <select
          value={model}
          onChange={e => {
            const val = e.target.value as ModelId
            setModel(val)
            localStorage.setItem(MODEL_KEY, val)
          }}
          onClick={e => e.stopPropagation()}
          onMouseDown={e => e.stopPropagation()}
          className="bg-gray-800 text-gray-400 text-xs font-mono border border-gray-700 rounded px-2 py-1 outline-none focus:border-gray-500 cursor-pointer"
        >
          {MODELS.map(m => (
            <option key={m.id} value={m.id}>
              {m.label}
            </option>
          ))}
        </select>
        <select
          value={fontSize}
          onChange={e => {
            const val = e.target.value as FontSizeId
            setFontSize(val)
            localStorage.setItem(FONT_SIZE_KEY, val)
          }}
          onClick={e => e.stopPropagation()}
          onMouseDown={e => e.stopPropagation()}
          className="bg-gray-800 text-gray-400 text-xs font-mono border border-gray-700 rounded px-2 py-1 outline-none focus:border-gray-500 cursor-pointer"
          title="Font size"
        >
          {FONT_SIZES.map(f => (
            <option key={f.id} value={f.id}>
              {f.label}
            </option>
          ))}
        </select>
      </div>
      {/* Hint bar */}
      <div className="flex items-center justify-between px-4 py-1 border-t border-gray-800/50 bg-gray-900/80 text-gray-600 text-[10px] font-mono">
        <span><span className="text-gray-500">/help</span> commands · <span className="text-gray-500">/export</span> save to KB · <span className="text-gray-500">↑↓</span> history</span>
        <span><span className="text-gray-500">/clear</span> reset</span>
      </div>
    </div>
  )
}
