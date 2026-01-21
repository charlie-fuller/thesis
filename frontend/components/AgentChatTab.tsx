'use client'

import { useState, useEffect } from 'react'
import { MessageSquare, Plus, Loader2 } from 'lucide-react'
import ChatInterface from './ChatInterface'
import { apiGet } from '@/lib/api'

// Format time relative to now (e.g., "5m ago", "2h ago", "3d ago")
function formatTimeAgo(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}

interface AgentChatTabProps {
  agentId: string
  agentName: string
  displayName: string
  userId: string
  clientId?: string
}

export default function AgentChatTab({
  agentId,
  agentName,
  displayName,
  userId,
  clientId
}: AgentChatTabProps) {
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)

  // Load agent-specific conversations
  useEffect(() => {
    loadConversations()
  }, [agentId])

  async function loadConversations() {
    try {
      setLoading(true)
      const data = await apiGet<{ success: boolean; conversations: Conversation[] }>(`/api/agents/${agentId}/conversations`)
      if (data.success) {
        setConversations(data.conversations || [])
      }
    } catch (error) {
      console.error('Failed to load agent conversations:', error)
    } finally {
      setLoading(false)
    }
  }

  function handleNewChat() {
    setCurrentConversationId(null)
  }

  function handleConversationCreated(conversationId?: string) {
    // Reload conversations to include the new one
    loadConversations()
    if (conversationId) {
      setCurrentConversationId(conversationId)
    }
  }

  function handleSelectConversation(conversationId: string) {
    setCurrentConversationId(conversationId)
  }

  return (
    <div className="flex h-[calc(100vh-280px)] min-h-[500px] border border-border rounded-lg overflow-hidden bg-background">
      {/* Left: Conversation list */}
      <div className="w-72 border-r border-border flex flex-col bg-muted/30">
        {/* Header with New Chat button */}
        <div className="p-3 border-b border-border">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat with {displayName}</span>
          </button>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-center">
              <MessageSquare className="w-12 h-12 text-muted-foreground/50 mb-3" />
              <p className="text-sm text-muted-foreground">
                No conversations yet
              </p>
              <p className="text-xs text-muted-foreground/70 mt-1">
                Start a new chat with {displayName}
              </p>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv.id)}
                  className={`w-full text-left p-3 rounded-md transition-colors ${
                    currentConversationId === conv.id
                      ? 'bg-primary/10 border border-primary/30'
                      : 'hover:bg-muted'
                  }`}
                >
                  <p className="text-sm font-medium truncate">
                    {conv.title || 'New Conversation'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatTimeAgo(new Date(conv.updated_at))}
                    {conv.message_count !== undefined && (
                      <span className="ml-2">
                        {conv.message_count} message{conv.message_count !== 1 ? 's' : ''}
                      </span>
                    )}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: Chat interface */}
      <div className="flex-1 flex flex-col">
        <ChatInterface
          clientId={clientId}
          userId={userId}
          conversationId={currentConversationId || undefined}
          lockedAgentId={agentName}
          lockedAgentDisplayName={displayName}
          agentIdForConversation={agentId}
          onConversationCreated={handleConversationCreated}
        />
      </div>
    </div>
  )
}
