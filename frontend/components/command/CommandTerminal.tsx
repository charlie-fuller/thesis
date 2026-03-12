'use client'

import { useState, useRef, useEffect, useCallback, KeyboardEvent } from 'react'
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
const MAX_HISTORY = 100

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
  const outputRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Load history from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(HISTORY_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) {
          setHistory(parsed.slice(-MAX_HISTORY))
        }
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

  const handleSubmit = useCallback(async () => {
    const input = currentInput.trim()
    if (!input || isStreaming) return

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
  }, [currentInput, isStreaming, session, history])

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
      onClick={() => inputRef.current?.focus()}
    >
      {/* Output area */}
      <div ref={outputRef} className="flex-1 overflow-y-auto p-4 font-mono text-sm leading-relaxed">
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
            <div className={`ml-2 mt-1 whitespace-pre-wrap ${entry.isError ? 'text-red-400' : 'text-gray-100'}`}>
              {entry.output}
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
              <div className="ml-2 mt-1 text-gray-100 whitespace-pre-wrap">{streamingOutput}</div>
            )}
            {!streamingOutput && streamingToolCalls.length === 0 && (
              <div className="ml-2 mt-1 text-gray-500 animate-pulse">thinking...</div>
            )}
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="flex items-center px-4 py-3 border-t border-gray-800 bg-gray-900">
        <span className="text-green-400 mr-2 font-mono text-sm flex-shrink-0">thesis&gt;</span>
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
      </div>
    </div>
  )
}
