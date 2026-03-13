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

  const handleExport = useCallback(async (args: string) => {
    // Parse args: /export <title> [location:<path>] [project:<id>] [initiative:<id>]
    const tokens = args.trim().split(/\s+/)
    const kwargs: Record<string, string> = {}
    const positional: string[] = []

    for (const token of tokens) {
      if (token.includes(':') && !token.startsWith('/')) {
        const [k, ...rest] = token.split(':')
        kwargs[k] = rest.join(':')
      } else {
        positional.push(token)
      }
    }

    const title = positional.join(' ') || `Command Session ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`
    const location = kwargs.location || kwargs.loc || undefined
    const projectId = kwargs.project || kwargs.proj || undefined
    const initiativeId = kwargs.initiative || kwargs.init || undefined

    const cmdStr = `/export ${args}`.trim()

    if (history.length === 0) {
      setHistory(prev => [...prev, { input: cmdStr, output: 'Nothing to export — conversation is empty.', toolCalls: [], isError: true }])
      return
    }

    // Build markdown from conversation history
    const lines = [`# ${title}\n`, `*Exported: ${new Date().toISOString().slice(0, 16).replace('T', ' ')}*\n`]
    for (const entry of history) {
      lines.push(`---\n## User\n\n${entry.input}\n`)
      if (entry.output) {
        lines.push(`## Assistant\n\n${entry.output}\n`)
      }
    }
    const content = lines.join('\n')

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const body: Record<string, unknown> = { title, content }
      if (location) body.location = location
      if (projectId) body.project_id = projectId
      if (initiativeId) body.initiative_id = initiativeId

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

      const parts = [`Saved to KB: **${title}**`, `Document ID: \`${data.document_id}\``]
      if (data.linked_project) parts.push(`Linked to project: \`${data.linked_project}\``)
      if (data.linked_initiative) parts.push(`Linked to initiative: \`${data.linked_initiative}\``)

      setHistory(prev => [...prev, { input: cmdStr, output: parts.join('\n'), toolCalls: [] }])
    } catch (err) {
      setHistory(prev => [...prev, {
        input: cmdStr,
        output: `Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`,
        toolCalls: [],
        isError: true,
      }])
    }
  }, [history, session])

  const handleSubmit = useCallback(async () => {
    const input = currentInput.trim()
    if (!input || isStreaming) return

    // Handle client-side slash commands
    if (input.startsWith('/export')) {
      setCurrentInput('')
      setHistoryIndex(-1)
      handleExport(input.slice(7))
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
          '- `/export <title> [project:<id>] [initiative:<id>] [location:<path>]`',
          '  Save this conversation to the Knowledge Base, optionally linked to a project and/or initiative',
          '- `/clear` — Clear conversation history',
          '- `/help` — Show this help',
          '',
          '**Export examples:**',
          '- `/export Debug Session` — save with title',
          '- `/export Sprint Review project:abc-123` — save and link to project',
          '- `/export Discovery Notes init:def-456` — save and link to initiative',
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
  }, [currentInput, isStreaming, session, history, model])

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
          placeholder={isStreaming ? 'Processing...' : 'Type a command...'}
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
