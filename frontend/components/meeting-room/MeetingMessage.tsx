'use client'

import ReactMarkdown from 'react-markdown'

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
  created_at: string
}

interface MeetingMessageProps {
  message: Message
  participants: Participant[]
  isStreaming?: boolean
}

const AGENT_COLORS: Record<string, { bg: string; text: string }> = {
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
  isStreaming = false
}: MeetingMessageProps) {
  const isUser = message.role === 'user'
  const agentName = message.agent_name || ''
  const colors = AGENT_COLORS[agentName] || { bg: 'bg-gray-500', text: 'text-gray-700' }

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

  // Agent message
  return (
    <div className="flex gap-3">
      {/* Agent Avatar */}
      <div
        className={`w-10 h-10 rounded-full ${colors.bg} flex items-center justify-center text-white font-semibold text-sm flex-shrink-0`}
      >
        {message.agent_display_name?.charAt(0) || 'A'}
      </div>

      {/* Message Content */}
      <div className="flex-1 max-w-[80%]">
        {/* Agent Name */}
        <div className={`text-sm font-medium ${colors.text} mb-1`}>
          {message.agent_display_name || agentName}
          {isStreaming && (
            <span className="ml-2 inline-flex items-center">
              <span className="animate-pulse">typing</span>
              <span className="animate-bounce ml-1">...</span>
            </span>
          )}
        </div>

        {/* Message Bubble */}
        <div className="bg-panel border border-default rounded-lg px-4 py-3 prose prose-sm max-w-none text-primary">
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

        {/* Timestamp */}
        <div className="text-xs text-tertiary mt-1">
          {new Date(message.created_at).toLocaleTimeString(undefined, {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  )
}
