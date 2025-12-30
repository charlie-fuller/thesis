'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { authenticatedFetch } from '@/lib/api'
import toast from 'react-hot-toast'
import { AgentIcon, getAgentColor } from '@/components/AgentIcon'

interface Participant {
  agent_name: string
  agent_display_name: string
}

interface Message {
  id: string
  role: 'user' | 'agent' | 'system'
  content: string
  agent_name?: string
  agent_display_name?: string
  discussion_round?: number
  responding_to_agent?: string
  metadata?: Record<string, unknown>
  created_at: string
}

interface KBSource {
  document_id: string | null
  similarity: number
  source_type: string
  title: string
}

interface GraphSources {
  stakeholders: { name: string; role: string; sentiment: number | null }[]
  concerns: { content: string; severity: string }[]
  roi_opportunities: { name: string; status: string }[]
  relationships: { from: string; to: string; type: string }[]
}

interface ContextSources {
  kb_sources: KBSource[]
  graph_sources: GraphSources
}

interface MeetingMessageProps {
  message: Message
  participants: Participant[]
  isStreaming?: boolean
  meetingTitle?: string
  contextSources?: ContextSources | null
}


export default function MeetingMessage({
  message,
  participants: _participants,
  isStreaming = false,
  meetingTitle = 'Meeting',
  contextSources
}: MeetingMessageProps) {
  const [saving, setSaving] = useState(false)
  const [showActions, setShowActions] = useState(false)
  const [showContextSources, setShowContextSources] = useState(false)

  // Check if this message has context sources to display
  const hasContextSources = contextSources && (
    contextSources.kb_sources.length > 0 ||
    contextSources.graph_sources.stakeholders.length > 0 ||
    contextSources.graph_sources.concerns.length > 0 ||
    contextSources.graph_sources.roi_opportunities.length > 0
  )

  const isUser = message.role === 'user'
  const agentName = message.agent_name || ''
  const color = getAgentColor(agentName)

  const handleSaveToKB = async () => {
    if (saving) return

    setSaving(true)
    try {
      const title = `${message.agent_display_name || 'Agent'} - ${meetingTitle}`
      const response = await authenticatedFetch('/api/documents/save-from-chat', {
        method: 'POST',
        body: JSON.stringify({
          title,
          content: message.content,
          message_id: message.id,
          agent_ids: [] // Global document
        })
      })

      const data = await response.json()

      if (data.success) {
        toast.success('Saved to Knowledge Base')
      } else {
        throw new Error(data.detail || 'Failed to save')
      }
    } catch (error) {
      console.error('Error saving to KB:', error)
      toast.error('Failed to save to Knowledge Base')
    } finally {
      setSaving(false)
    }
  }

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%]">
          <div className="bg-primary text-white rounded-lg px-4 py-3 prose prose-sm prose-invert max-w-none">
            <ReactMarkdown>
              {message.content}
            </ReactMarkdown>
          </div>
          <div className="text-xs text-tertiary mt-1 text-right">
            {new Date(message.created_at).toLocaleTimeString(undefined, {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        </div>
      </div>
    )
  }

  const isAutonomous = message.metadata?.autonomous === true || message.discussion_round !== undefined

  // Agent message
  return (
    <div
      className="flex gap-3 group"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* Agent Avatar */}
      <div className="relative flex-shrink-0">
        <div
          className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center border`}
        >
          <AgentIcon name={agentName} size="md" />
        </div>
        {/* Round indicator badge */}
        {isAutonomous && message.discussion_round && (
          <div className="absolute -top-1 -right-1 w-5 h-5 bg-indigo-600 rounded-full border-2 border-white flex items-center justify-center text-[10px] text-white font-medium">
            R{message.discussion_round}
          </div>
        )}
      </div>

      {/* Message Content */}
      <div className="flex-1 max-w-[80%]">
        {/* Agent Name + Autonomous Badge */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium text-primary">
            {message.agent_display_name || agentName}
          </span>
          {isAutonomous && (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-indigo-100 text-indigo-700">
              Autonomous
            </span>
          )}
          {isStreaming && (
            <span className="inline-flex items-center">
              <span className="animate-pulse text-sm text-secondary">typing</span>
              <span className="animate-bounce ml-1 text-secondary">...</span>
            </span>
          )}
        </div>

        {/* Responding to indicator */}
        {message.responding_to_agent && (
          <div className="text-xs text-secondary mb-1 flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            Responding to {message.responding_to_agent}
          </div>
        )}

        {/* Message Bubble */}
        <div className="bg-card border border-default rounded-lg px-4 py-3 prose prose-sm max-w-none text-primary">
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
              li: ({ children }) => <li className="mb-1">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              code: ({ children }) => (
                <code className="bg-gray-100 px-1 rounded text-sm">{children}</code>
              ),
              pre: ({ children }) => (
                <pre className="bg-gray-100 p-3 rounded-lg overflow-x-auto my-2">{children}</pre>
              )
            }}
          >
            {message.content || ' '}
          </ReactMarkdown>

          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1" />
          )}
        </div>

        {/* Timestamp and Actions */}
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-tertiary">
            {new Date(message.created_at).toLocaleTimeString(undefined, {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>

          {/* Save to KB button - shows on hover */}
          {!isStreaming && showActions && (
            <button
              onClick={handleSaveToKB}
              disabled={saving}
              className="flex items-center gap-1 px-2 py-0.5 text-xs text-secondary hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
              title="Save to Knowledge Base"
            >
              {saving ? (
                <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
              )}
              <span>Save to KB</span>
            </button>
          )}

          {/* Context Sources button - shows on hover when sources exist */}
          {!isStreaming && hasContextSources && showActions && (
            <button
              onClick={() => setShowContextSources(!showContextSources)}
              className="flex items-center gap-1 px-2 py-0.5 text-xs text-secondary hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              title="View context sources"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Sources</span>
              <svg
                className={`w-3 h-3 transition-transform ${showContextSources ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          )}
        </div>

        {/* Context Sources Panel - collapsible */}
        {!isStreaming && hasContextSources && showContextSources && contextSources && (
          <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-default">
            {/* KB Sources */}
            {contextSources.kb_sources.length > 0 && (
              <div className="mb-2">
                <h4 className="text-[10px] font-medium text-tertiary uppercase tracking-wide mb-1">
                  Knowledge Base
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {contextSources.kb_sources.map((source, idx) => (
                    <div
                      key={idx}
                      className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-[10px]"
                      title={`Similarity: ${(source.similarity * 100).toFixed(0)}%`}
                    >
                      <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className="truncate max-w-[120px]">{source.title}</span>
                      <span className="text-blue-500 dark:text-blue-400">
                        {(source.similarity * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Graph Sources */}
            {(contextSources.graph_sources.stakeholders.length > 0 ||
              contextSources.graph_sources.concerns.length > 0 ||
              contextSources.graph_sources.roi_opportunities.length > 0) && (
              <div>
                <h4 className="text-[10px] font-medium text-tertiary uppercase tracking-wide mb-1">
                  Stakeholder Context
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {contextSources.graph_sources.stakeholders.map((s, idx) => (
                    <div
                      key={`stakeholder-${idx}`}
                      className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-[10px]"
                    >
                      <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <span>{s.name}</span>
                      {s.role && <span className="text-purple-500">({s.role})</span>}
                    </div>
                  ))}
                  {contextSources.graph_sources.concerns.map((c, idx) => (
                    <div
                      key={`concern-${idx}`}
                      className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded text-[10px]"
                      title={c.content}
                    >
                      <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <span className="truncate max-w-[100px]">{c.content}</span>
                    </div>
                  ))}
                  {contextSources.graph_sources.roi_opportunities.map((r, idx) => (
                    <div
                      key={`roi-${idx}`}
                      className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-[10px]"
                    >
                      <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{r.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
