'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { authenticatedFetch } from '@/lib/api'
import { API_BASE_URL } from '@/lib/config'
import { supabase } from '@/lib/supabase'
import LoadingSpinner from '@/components/LoadingSpinner'
import MeetingMessage from '@/components/meeting-room/MeetingMessage'
import ParticipantBar from '@/components/meeting-room/ParticipantBar'
import toast from 'react-hot-toast'

interface Participant {
  id: string
  agent_id: string
  agent_name: string
  agent_display_name: string
  role_description: string | null
  priority: number
  turns_taken: number
  tokens_used: number
}

interface MeetingRoom {
  id: string
  title: string
  description: string | null
  meeting_type: string
  status: string
  config: Record<string, unknown>
  total_tokens_used: number
  participants: Participant[]
  created_at: string
  updated_at: string
}

interface Message {
  id: string
  role: 'user' | 'agent' | 'system'
  content: string
  agent_id?: string
  agent_name?: string
  agent_display_name?: string
  turn_number?: number
  created_at: string
}

export default function MeetingRoomPage() {
  const params = useParams()
  const meetingId = params.id as string
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  const [meeting, setMeeting] = useState<MeetingRoom | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [activeAgent, setActiveAgent] = useState<string | null>(null)
  const [streamingContent, setStreamingContent] = useState<Record<string, string>>({})

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [authLoading, user, router])

  useEffect(() => {
    if (user && meetingId) {
      loadMeeting()
      loadMessages()
    }
  }, [user, meetingId])

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const loadMeeting = async () => {
    try {
      const response = await authenticatedFetch(`/api/meeting-rooms/${meetingId}`)
      const data = await response.json()

      if (data.success) {
        setMeeting(data.meeting_room)
      } else {
        throw new Error(data.detail || 'Failed to load meeting')
      }
    } catch (error) {
      console.error('Error loading meeting:', error)
      toast.error('Failed to load meeting room')
      router.push('/meeting-room')
    }
  }

  const loadMessages = async () => {
    try {
      setLoading(true)
      const response = await authenticatedFetch(`/api/meeting-rooms/${meetingId}/messages`)
      const data = await response.json()

      if (data.success) {
        setMessages(data.messages)
      }
    } catch (error) {
      console.error('Error loading messages:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() || sending) return

    const userMessage = input.trim()
    setInput('')
    setSending(true)
    setStreamingContent({})

    // Add user message to UI immediately
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      // Get auth token
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) {
        throw new Error('Not authenticated')
      }

      // Start SSE stream
      const response = await fetch(`${API_BASE_URL}/api/meeting-rooms/${meetingId}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ message: userMessage })
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let currentAgentName = ''
      const agentResponses: Record<string, string> = {}

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              switch (data.type) {
                case 'agent_turn_start':
                  currentAgentName = data.agent_name
                  setActiveAgent(data.agent_display_name)
                  agentResponses[currentAgentName] = ''
                  break

                case 'agent_token':
                  if (data.agent_name) {
                    agentResponses[data.agent_name] = (agentResponses[data.agent_name] || '') + data.content
                    setStreamingContent({ ...agentResponses })
                  }
                  break

                case 'agent_turn_end':
                  // Agent finished - add their message to the list
                  if (agentResponses[data.agent_name]) {
                    const agentMessage: Message = {
                      id: `agent-${data.agent_name}-${Date.now()}`,
                      role: 'agent',
                      content: agentResponses[data.agent_name],
                      agent_name: data.agent_name,
                      agent_display_name: meeting?.participants.find(
                        p => p.agent_name === data.agent_name
                      )?.agent_display_name || data.agent_name,
                      created_at: new Date().toISOString()
                    }
                    setMessages(prev => [...prev, agentMessage])
                  }
                  setActiveAgent(null)
                  break

                case 'round_complete':
                  // Clear streaming content
                  setStreamingContent({})
                  break

                case 'error':
                  toast.error(data.message || 'An error occurred')
                  break
              }
            } catch (e) {
              // Ignore parse errors for incomplete chunks
            }
          }
        }
      }

    } catch (error) {
      console.error('Error sending message:', error)
      toast.error('Failed to send message')
      // Remove the temp message on error
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
    } finally {
      setSending(false)
      setActiveAgent(null)
      setStreamingContent({})
      // Refresh messages to get server-assigned IDs
      loadMessages()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-page">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!meeting) {
    return null
  }

  return (
    <div className="flex flex-col h-screen bg-page">
      {/* Header */}
      <div className="bg-panel border-b border-default px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/meeting-room')}
              className="text-secondary hover:text-primary"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-lg font-semibold text-primary">{meeting.title}</h1>
              {meeting.description && (
                <p className="text-sm text-secondary">{meeting.description}</p>
              )}
            </div>
          </div>
          <div className="text-sm text-tertiary">
            {meeting.total_tokens_used.toLocaleString()} tokens used
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Messages */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && !sending && (
              <div className="text-center py-16 text-secondary">
                <p className="mb-2">Start the conversation</p>
                <p className="text-sm">
                  Ask a question and the participating agents will share their perspectives
                </p>
              </div>
            )}

            {messages.map((message) => (
              <MeetingMessage
                key={message.id}
                message={message}
                participants={meeting.participants}
              />
            ))}

            {/* Streaming messages */}
            {Object.entries(streamingContent).map(([agentName, content]) => {
              if (!content) return null
              const participant = meeting.participants.find(p => p.agent_name === agentName)
              return (
                <MeetingMessage
                  key={`streaming-${agentName}`}
                  message={{
                    id: `streaming-${agentName}`,
                    role: 'agent',
                    content,
                    agent_name: agentName,
                    agent_display_name: participant?.agent_display_name || agentName,
                    created_at: new Date().toISOString()
                  }}
                  participants={meeting.participants}
                  isStreaming
                />
              )
            })}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-default p-4">
            <div className="flex gap-3">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                className="flex-1 resize-none rounded-lg border border-default bg-panel px-4 py-3 text-primary placeholder-tertiary focus:outline-none focus:ring-2 focus:ring-primary"
                rows={2}
                disabled={sending}
              />
              <button
                onClick={handleSendMessage}
                disabled={!input.trim() || sending}
                className="btn-primary px-6 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sending ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Participants sidebar */}
        <ParticipantBar
          participants={meeting.participants}
          activeAgent={activeAgent}
        />
      </div>
    </div>
  )
}
