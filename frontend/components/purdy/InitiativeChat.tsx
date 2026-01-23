'use client'

import { useState, useEffect, useRef } from 'react'
import {
  Send,
  User,
  Bot,
  Loader2,
  FileText,
  ExternalLink,
  Trash2
} from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'
import ReactMarkdown from 'react-markdown'

interface Source {
  type: 'document' | 'system_kb'
  id: string
  name: string
  similarity: number
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  created_at: string
}

interface Conversation {
  id: string
  messages: Message[]
}

interface InitiativeChatProps {
  initiativeId: string
}

export default function InitiativeChat({ initiativeId }: InitiativeChatProps) {
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Load conversation
  useEffect(() => {
    const loadConversation = async () => {
      try {
        setLoading(true)
        const result = await apiGet<{ success: boolean; conversation: Conversation }>(
          `/api/purdy/initiatives/${initiativeId}/chat`
        )
        if (result.success && result.conversation) {
          setConversation(result.conversation)
          setMessages(result.conversation.messages || [])
        }
      } catch (err) {
        console.error('Failed to load conversation:', err)
      } finally {
        setLoading(false)
      }
    }
    loadConversation()
  }, [initiativeId])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const question = input.trim()
    if (!question || sending) return

    setInput('')
    setSending(true)
    setError(null)

    // Optimistically add user message
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: question,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      const result = await apiPost<{
        success: boolean
        response: string
        sources: Source[]
        conversation_id: string
      }>(`/api/purdy/initiatives/${initiativeId}/chat`, {
        question,
        conversation_id: conversation?.id
      })

      if (result.success) {
        // Replace temp message with real one and add assistant response
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: result.response,
          sources: result.sources,
          created_at: new Date().toISOString()
        }
        setMessages(prev => [...prev.slice(0, -1), { ...tempUserMessage, id: `user-${Date.now()}` }, assistantMessage])

        if (!conversation) {
          setConversation({ id: result.conversation_id, messages: [] })
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
      // Remove the optimistic message on error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[400px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg">
        <div className="flex items-center gap-2 text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          Loading conversation...
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[600px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center text-slate-500 dark:text-slate-400">
            <div>
              <Bot className="w-10 h-10 mx-auto mb-3 opacity-50" />
              <p className="font-medium">Ask about this initiative</p>
              <p className="text-sm mt-1">
                I can answer questions about documents, outputs, and methodology
              </p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : ''
              }`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                </div>
              )}

              <div className={`max-w-[80%] ${
                message.role === 'user' ? 'order-first' : ''
              }`}>
                <div className={`rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-100 dark:bg-slate-700'
                }`}>
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  )}
                </div>

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {message.sources.slice(0, 3).map((source, index) => (
                      <span
                        key={`${source.id}-${index}`}
                        className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded"
                      >
                        <FileText className="w-3 h-3" />
                        {source.name}
                      </span>
                    ))}
                    {message.sources.length > 3 && (
                      <span className="text-xs text-slate-400">
                        +{message.sources.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>

              {message.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-600 flex items-center justify-center">
                  <User className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                </div>
              )}
            </div>
          ))
        )}

        {sending && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
              <Bot className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div className="bg-slate-100 dark:bg-slate-700 rounded-lg p-3">
              <div className="flex items-center gap-2 text-slate-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                Thinking...
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-sm text-red-600 dark:text-red-400 border-t border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-slate-200 dark:border-slate-700 p-4">
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about this initiative..."
            rows={1}
            className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || sending}
            className="flex items-center justify-center w-10 h-10 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {sending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
