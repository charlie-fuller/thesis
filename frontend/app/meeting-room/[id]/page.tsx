'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { authenticatedFetch } from '@/lib/api'
import { API_BASE_URL } from '@/lib/config'
import { supabase } from '@/lib/supabase'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import MeetingMessage from '@/components/meeting-room/MeetingMessage'
import ParticipantBar from '@/components/meeting-room/ParticipantBar'
import AutonomousDiscussionPanel from '@/components/meeting-room/AutonomousDiscussionPanel'
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

  // Autonomous discussion state
  const [isAutonomous, setIsAutonomous] = useState(false)
  const [autonomousRound, setAutonomousRound] = useState(0)
  const [autonomousTotalRounds, setAutonomousTotalRounds] = useState(0)
  const [autonomousTopic, setAutonomousTopic] = useState<string | null>(null)
  const [autonomousPaused, setAutonomousPaused] = useState(false)

  // Title editing state
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [editedTitle, setEditedTitle] = useState('')

  // Export state
  const [exporting, setExporting] = useState(false)

  // Context sources state - maps message ID to its context sources
  // The context sources are associated with the first agent message after a user message
  const [messageContextSources, setMessageContextSources] = useState<Record<string, ContextSources>>({})
  // Current pending context sources (received before any agent messages in current turn)
  const [pendingContextSources, setPendingContextSources] = useState<ContextSources | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const titleInputRef = useRef<HTMLInputElement>(null)

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

  const handleStartEditingTitle = () => {
    if (meeting) {
      setEditedTitle(meeting.title)
      setIsEditingTitle(true)
      // Focus the input after state update
      setTimeout(() => titleInputRef.current?.focus(), 0)
    }
  }

  const handleSaveTitle = async () => {
    if (!editedTitle.trim() || !meeting) return

    const newTitle = editedTitle.trim()
    if (newTitle === meeting.title) {
      setIsEditingTitle(false)
      return
    }

    try {
      const response = await authenticatedFetch(`/api/meeting-rooms/${meetingId}`, {
        method: 'PATCH',
        body: JSON.stringify({ title: newTitle })
      })

      const data = await response.json()

      if (data.success) {
        setMeeting({ ...meeting, title: newTitle })
        toast.success('Title updated')
      } else {
        throw new Error(data.detail || 'Failed to update title')
      }
    } catch (error) {
      console.error('Error updating title:', error)
      toast.error('Failed to update title')
    } finally {
      setIsEditingTitle(false)
    }
  }

  const handleTitleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSaveTitle()
    } else if (e.key === 'Escape') {
      setIsEditingTitle(false)
    }
  }

  const handleExportConversation = async () => {
    if (exporting || messages.length === 0) return

    setExporting(true)
    try {
      // Build markdown content from all messages
      const participantNames = meeting?.participants.map(p => p.agent_display_name).join(', ') || 'Agents'
      const dateStr = new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })

      let markdownContent = `## Meeting Details\n\n`
      markdownContent += `- **Title:** ${meeting?.title}\n`
      markdownContent += `- **Date:** ${dateStr}\n`
      markdownContent += `- **Participants:** ${participantNames}\n`
      if (meeting?.description) {
        markdownContent += `- **Description:** ${meeting.description}\n`
      }
      markdownContent += `\n---\n\n## Conversation\n\n`

      for (const msg of messages) {
        const time = new Date(msg.created_at).toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit'
        })

        if (msg.role === 'user') {
          markdownContent += `### User (${time})\n\n${msg.content}\n\n`
        } else {
          const agentName = msg.agent_display_name || msg.agent_name || 'Agent'
          markdownContent += `### ${agentName} (${time})\n\n${msg.content}\n\n`
        }
      }

      const response = await authenticatedFetch('/api/documents/save-from-chat', {
        method: 'POST',
        body: JSON.stringify({
          title: `Meeting Transcript - ${meeting?.title}`,
          content: markdownContent,
          agent_ids: [] // Global document
        })
      })

      const data = await response.json()

      if (data.success) {
        toast.success('Meeting exported to Knowledge Base')
      } else {
        throw new Error(data.detail || 'Failed to export')
      }
    } catch (error) {
      console.error('Error exporting conversation:', error)
      toast.error('Failed to export conversation')
    } finally {
      setExporting(false)
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
      // Track pending context sources to associate with first agent message
      let pendingContextForTurn: ContextSources | null = null
      let firstAgentMessageId: string | null = null

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
                case 'context_sources':
                  // Store KB and Graph context sources as pending
                  // These will be associated with the first agent message
                  pendingContextForTurn = {
                    kb_sources: data.kb_sources || [],
                    graph_sources: data.graph_sources || {
                      stakeholders: [],
                      concerns: [],
                      roi_opportunities: [],
                      relationships: []
                    }
                  }
                  break

                case 'facilitator_turn_start':
                  currentAgentName = 'facilitator'
                  setActiveAgent('Facilitator')
                  agentResponses['facilitator'] = ''
                  break

                case 'facilitator_token':
                  agentResponses['facilitator'] = (agentResponses['facilitator'] || '') + data.content
                  setStreamingContent({ ...agentResponses })
                  break

                case 'facilitator_turn_end':
                  // Facilitator finished - add their message to the list
                  if (agentResponses['facilitator']) {
                    const messageId = `agent-facilitator-${Date.now()}`
                    const facilitatorMessage: Message = {
                      id: messageId,
                      role: 'agent',
                      content: agentResponses['facilitator'],
                      agent_name: 'facilitator',
                      agent_display_name: 'Facilitator',
                      created_at: new Date().toISOString()
                    }
                    // Associate pending context with first agent message
                    if (pendingContextForTurn && !firstAgentMessageId) {
                      firstAgentMessageId = messageId
                      setMessageContextSources(prev => ({
                        ...prev,
                        [messageId]: pendingContextForTurn!
                      }))
                    }
                    // Clear streaming content BEFORE adding message to prevent duplicate display
                    delete agentResponses['facilitator']
                    setStreamingContent({ ...agentResponses })
                    setMessages(prev => [...prev, facilitatorMessage])
                  }
                  setActiveAgent(null)
                  break

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
                    const messageId = `agent-${data.agent_name}-${Date.now()}`
                    const agentMessage: Message = {
                      id: messageId,
                      role: 'agent',
                      content: agentResponses[data.agent_name],
                      agent_name: data.agent_name,
                      agent_display_name: meeting?.participants.find(
                        p => p.agent_name === data.agent_name
                      )?.agent_display_name || data.agent_name,
                      created_at: new Date().toISOString()
                    }
                    // Associate pending context with first agent message (if not already set by facilitator)
                    if (pendingContextForTurn && !firstAgentMessageId) {
                      firstAgentMessageId = messageId
                      setMessageContextSources(prev => ({
                        ...prev,
                        [messageId]: pendingContextForTurn!
                      }))
                    }
                    // Clear streaming content BEFORE adding message to prevent duplicate display
                    delete agentResponses[data.agent_name]
                    setStreamingContent({ ...agentResponses })
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
      // NOTE: We don't reload messages here anymore to prevent flickering.
      // The local state is already accurate from streaming events.
      // Server-assigned IDs will be fetched on next page load.
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // Autonomous discussion handlers
  const handleStartAutonomousDiscussion = async (topic: string, rounds: number) => {
    setSending(true)
    setIsAutonomous(true)
    setAutonomousTopic(topic)
    setAutonomousTotalRounds(rounds)
    setAutonomousRound(1)
    setAutonomousPaused(false)
    setStreamingContent({})

    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) {
        throw new Error('Not authenticated')
      }

      const response = await fetch(`${API_BASE_URL}/api/meeting-rooms/${meetingId}/autonomous/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ topic, rounds, speaking_order: 'priority' })
      })

      if (!response.ok) {
        throw new Error('Failed to start autonomous discussion')
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      const agentResponses: Record<string, string> = {}
      // Track pending context sources per round
      let pendingContextForRound: ContextSources | null = null
      let firstAgentInRoundId: string | null = null

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
                case 'context_sources':
                  // Store KB and Graph context sources as pending for this round
                  pendingContextForRound = {
                    kb_sources: data.kb_sources || [],
                    graph_sources: data.graph_sources || {
                      stakeholders: [],
                      concerns: [],
                      roi_opportunities: [],
                      relationships: []
                    }
                  }
                  // Reset first agent tracker for new context
                  firstAgentInRoundId = null
                  break

                case 'discussion_round_start':
                  setAutonomousRound(data.round_number)
                  setAutonomousTotalRounds(data.total_rounds)
                  break

                case 'agent_turn_start':
                  setActiveAgent(data.agent_display_name)
                  agentResponses[data.agent_name] = ''
                  break

                case 'agent_token':
                  if (data.agent_name) {
                    agentResponses[data.agent_name] = (agentResponses[data.agent_name] || '') + data.content
                    setStreamingContent({ ...agentResponses })
                  }
                  break

                case 'agent_turn_end':
                  if (agentResponses[data.agent_name]) {
                    const messageId = `agent-${data.agent_name}-${Date.now()}`
                    const agentMessage: Message = {
                      id: messageId,
                      role: 'agent',
                      content: agentResponses[data.agent_name],
                      agent_name: data.agent_name,
                      agent_display_name: meeting?.participants.find(
                        p => p.agent_name === data.agent_name
                      )?.agent_display_name || data.agent_name,
                      discussion_round: autonomousRound,
                      metadata: { autonomous: true },
                      created_at: new Date().toISOString()
                    }
                    // Associate pending context with first agent message in this round
                    if (pendingContextForRound && !firstAgentInRoundId) {
                      firstAgentInRoundId = messageId
                      setMessageContextSources(prev => ({
                        ...prev,
                        [messageId]: pendingContextForRound!
                      }))
                    }
                    // Clear streaming content BEFORE adding message to prevent duplicate display
                    delete agentResponses[data.agent_name]
                    setStreamingContent({ ...agentResponses })
                    setMessages(prev => [...prev, agentMessage])
                  }
                  setActiveAgent(null)
                  break

                case 'discussion_round_end':
                  // Round complete
                  break

                case 'discussion_complete':
                  setIsAutonomous(false)
                  setAutonomousRound(0)
                  setAutonomousTopic(null)
                  toast.success('Discussion complete')
                  break

                case 'discussion_paused':
                  setIsAutonomous(false)
                  setAutonomousPaused(true)
                  if (data.reason === 'user_interjection') {
                    toast('Discussion paused for your input')
                  }
                  break

                case 'error':
                  toast.error(data.message || 'An error occurred')
                  break
              }
            } catch {
              // Ignore parse errors for incomplete chunks
            }
          }
        }
      }

    } catch (error) {
      console.error('Error in autonomous discussion:', error)
      toast.error('Failed to start autonomous discussion')
      setIsAutonomous(false)
    } finally {
      setSending(false)
      setActiveAgent(null)
      setStreamingContent({})
      // NOTE: We don't reload messages here to prevent flickering.
      // The local state is already accurate from streaming events.
    }
  }

  const handleStopAutonomousDiscussion = async () => {
    try {
      await authenticatedFetch(`/api/meeting-rooms/${meetingId}/autonomous/stop`, {
        method: 'POST'
      })
      setIsAutonomous(false)
      setAutonomousPaused(true)
      toast('Discussion stopped')
    } catch (error) {
      console.error('Error stopping discussion:', error)
      toast.error('Failed to stop discussion')
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
      {/* Top Navigation */}
      <PageHeader />

      {/* Meeting Header */}
      <div className="bg-card border-b border-default px-6 py-3">
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
            <div className="flex-1 min-w-0">
              {isEditingTitle ? (
                <input
                  ref={titleInputRef}
                  type="text"
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  onBlur={handleSaveTitle}
                  onKeyDown={handleTitleKeyDown}
                  className="text-lg font-semibold text-primary bg-transparent border-b-2 border-primary focus:outline-none w-full max-w-md"
                />
              ) : (
                <h1
                  className="text-lg font-semibold text-primary cursor-pointer hover:text-primary/80 inline-flex items-center gap-2 group"
                  onClick={handleStartEditingTitle}
                  title="Click to edit title"
                >
                  {meeting.title}
                  <svg
                    className="w-4 h-4 opacity-0 group-hover:opacity-50 transition-opacity"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </h1>
              )}
              {meeting.description && (
                <p className="text-sm text-secondary">{meeting.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleExportConversation}
              disabled={exporting || messages.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-secondary hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Export conversation to Knowledge Base"
            >
              {exporting ? (
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              )}
              <span>Export to KB</span>
            </button>
            <span className="text-sm text-tertiary">
              {meeting.total_tokens_used.toLocaleString()} tokens used
            </span>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Messages */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {/* Autonomous Discussion Panel */}
            <AutonomousDiscussionPanel
              meetingId={meetingId}
              isActive={isAutonomous}
              isPaused={autonomousPaused}
              currentRound={autonomousRound}
              totalRounds={autonomousTotalRounds}
              topic={autonomousTopic}
              onStart={handleStartAutonomousDiscussion}
              onStop={handleStopAutonomousDiscussion}
              disabled={sending}
            />

            {messages.length === 0 && !sending && !isAutonomous && (
              <div className="text-center py-16 text-secondary">
                <p className="mb-2">Start the conversation</p>
                <p className="text-sm">
                  Ask a question or start an autonomous discussion to have agents share their perspectives
                </p>
              </div>
            )}

            {messages.map((message) => (
              <MeetingMessage
                key={message.id}
                message={message}
                participants={meeting.participants}
                meetingTitle={meeting.title}
                contextSources={messageContextSources[message.id]}
              />
            ))}

            {/* Streaming messages */}
            {Object.entries(streamingContent).map(([agentName, content]) => {
              if (!content) return null
              // Handle Facilitator specially since it's not in participants list
              const isFacilitator = agentName === 'facilitator'
              const participant = meeting.participants.find(p => p.agent_name === agentName)
              const displayName = isFacilitator ? 'Facilitator' : (participant?.agent_display_name || agentName)
              return (
                <MeetingMessage
                  key={`streaming-${agentName}`}
                  message={{
                    id: `streaming-${agentName}`,
                    role: 'agent',
                    content,
                    agent_name: agentName,
                    agent_display_name: displayName,
                    created_at: new Date().toISOString()
                  }}
                  participants={meeting.participants}
                  meetingTitle={meeting.title}
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
                placeholder={sending ? "Agents responding... type your next message" : "Type your message..."}
                className="flex-1 resize-none rounded-lg border border-default bg-card px-4 py-3 text-primary placeholder-tertiary focus:outline-none focus:ring-2 focus:ring-primary"
                rows={2}
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
          isAutonomous={isAutonomous}
          currentRound={autonomousRound}
          totalRounds={autonomousTotalRounds}
        />
      </div>
    </div>
  )
}
