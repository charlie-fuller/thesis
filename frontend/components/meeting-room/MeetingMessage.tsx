'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { authenticatedFetch } from '@/lib/api'
import toast from 'react-hot-toast'
import { AgentIcon } from '@/components/AgentIcon'

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

interface MeetingMessageProps {
  message: Message
  participants: Participant[]
  isStreaming?: boolean
  meetingTitle?: string
}

const AGENT_COLORS: Record<string, { bg: string; text: string }> = {
  // Meta-Agents
  facilitator: { bg: 'bg-yellow-500', text: 'text-yellow-700' },
  reporter: { bg: 'bg-lime-600', text: 'text-lime-700' },
  // Stakeholder Perspective Agents
  atlas: { bg: 'bg-blue-500', text: 'text-blue-700' },
  fortuna: { bg: 'bg-green-500', text: 'text-green-700' },
  guardian: { bg: 'bg-purple-500', text: 'text-purple-700' },
  counselor: { bg: 'bg-amber-500', text: 'text-amber-700' },
  oracle: { bg: 'bg-cyan-500', text: 'text-cyan-700' },
  sage: { bg: 'bg-rose-500', text: 'text-rose-700' },
  // Consulting/Implementation Agents
  strategist: { bg: 'bg-indigo-500', text: 'text-indigo-700' },
  architect: { bg: 'bg-slate-500', text: 'text-slate-700' },
  operator: { bg: 'bg-orange-500', text: 'text-orange-700' },
  pioneer: { bg: 'bg-emerald-500', text: 'text-emerald-700' },
  // Internal Enablement Agents
  catalyst: { bg: 'bg-pink-500', text: 'text-pink-700' },
  scholar: { bg: 'bg-teal-500', text: 'text-teal-700' },
  echo: { bg: 'bg-violet-500', text: 'text-violet-700' },
  // Systems/Coordination Agents
  nexus: { bg: 'bg-sky-500', text: 'text-sky-700' },
  coordinator: { bg: 'bg-gray-600', text: 'text-gray-700' }
}

export default function MeetingMessage({
  message,
  participants: _participants,
  isStreaming = false,
  meetingTitle = 'Meeting'
}: MeetingMessageProps) {
  const [saving, setSaving] = useState(false)
  const [showActions, setShowActions] = useState(false)

  const isUser = message.role === 'user'
  const agentName = message.agent_name || ''
  const colors = AGENT_COLORS[agentName] || { bg: 'bg-gray-500', text: 'text-gray-700' }

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
          className={`w-10 h-10 rounded-full ${colors.bg} flex items-center justify-center`}
        >
          <AgentIcon name={agentName} size="md" className="text-white" />
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
          <span className={`text-sm font-medium ${colors.text}`}>
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
        </div>
      </div>
    </div>
  )
}
