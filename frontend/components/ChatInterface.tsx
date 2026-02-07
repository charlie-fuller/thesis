'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { X, AlertTriangle } from 'lucide-react'
import ChatMessage from './ChatMessage'
import LoadingSpinner from './LoadingSpinner'
import AgentSelector from './AgentSelector'
import SaveToKBModal from './SaveToKBModal'
import { AgentIcon, getAgentColor } from './AgentIcon'
import {
  authenticatedFetch,
  apiGet,
  apiPost
} from '@/lib/api'
import toast from 'react-hot-toast'
import { API_BASE_URL } from '@/lib/config'
import { logger } from '@/lib/logger'

interface Document {
  id: string
  filename: string
  mime_type?: string
}

interface Message {
  id?: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  documents?: Document[]
  metadata?: Record<string, unknown>
}

interface ChatInterfaceProps {
  clientId?: string  // Optional - backend auto-assigns default client
  userId: string
  conversationId?: string
  apiBaseUrl?: string
  initialPromptText?: string | null
  onPromptUsed?: () => void
  onConversationCreated?: ((conversationId?: string) => void)
  // Agent chat tab props
  lockedAgentId?: string  // Lock to specific agent name (hides selector)
  lockedAgentDisplayName?: string  // Display name for locked agent
  agentIdForConversation?: string  // UUID of agent (for conversation creation)
  // Context-aware chat props
  projectId?: string  // Project context for conversation
  initiativeId?: string  // Initiative context for conversation
  // Callback when conversation metadata is loaded (restores project/initiative context)
  onContextRestored?: (context: { projectId?: string | null; initiativeId?: string | null }) => void
}

export default function ChatInterface({
  clientId,
  userId,
  conversationId,
  // apiBaseUrl kept for potential future customization
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  apiBaseUrl: _apiBaseUrl = API_BASE_URL,
  initialPromptText,
  onPromptUsed,
  onConversationCreated,
  lockedAgentId,
  lockedAgentDisplayName,
  agentIdForConversation,
  projectId,
  initiativeId,
  onContextRestored
}: ChatInterfaceProps) {
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(conversationId || null)
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [uploadingFiles, setUploadingFiles] = useState(false)
  const [conversationDocumentIds, setConversationDocumentIds] = useState<string[]>([])
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- setSearchQuery kept for future search feature
  const [searchQuery, _setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<number[]>([])
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0)
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- setStreamingEnabled kept for future toggle feature
  const [streamingEnabled, _setStreamingEnabled] = useState(true) // Enable streaming by default
  // Use a ref to track when we're sending the first message - this prevents the useEffect
  // from reloading the conversation and overwriting our optimistic message update
  const isSendingFirstMessageRef = useRef(false)
  const [digDeeperLoading, setDigDeeperLoading] = useState<string | null>(null) // Track which message is being elaborated


  // Context window tracking - Claude Sonnet 4 has 200K token context
  const CLAUDE_CONTEXT_WINDOW = 200000
  const [totalTokensUsed, setTotalTokensUsed] = useState(0)
  const contextPercentage = Math.min((totalTokensUsed / CLAUDE_CONTEXT_WINDOW) * 100, 100)

  // Agent selection state - initialize with locked agent if provided, or context-specific agent
  const getInitialAgents = (): string[] => {
    if (lockedAgentId) return [lockedAgentId]
    if (projectId) return ['project_agent', 'taskmaster']
    if (initiativeId) return ['initiative_agent']
    return []
  }
  const [selectedAgents, setSelectedAgents] = useState<string[]>(getInitialAgents())

  // Update selected agents when context changes
  useEffect(() => {
    if (lockedAgentId) return // Don't change locked agents
    if (projectId) {
      setSelectedAgents(['project_agent', 'taskmaster'])
    } else if (initiativeId) {
      setSelectedAgents(['initiative_agent'])
    }
  }, [projectId, initiativeId, lockedAgentId])
  const [currentResponseAgent, setCurrentResponseAgent] = useState<{ name: string; displayName: string } | null>(null)

  // Save to KB modal state
  const [saveToKBModal, setSaveToKBModal] = useState<{
    isOpen: boolean;
    messageId: string;
    content: string;
  }>({ isOpen: false, messageId: '', content: '' })
  const [isSavingToKB, setIsSavingToKB] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const searchResultRefs = useRef<(HTMLDivElement | null)[]>([])
  const userHasScrolledUp = useRef(false)

  // Check if user is near the bottom of the scroll container
  const isNearBottom = () => {
    const container = messagesContainerRef.current
    if (!container) return true
    const threshold = 150 // pixels from bottom
    return container.scrollHeight - container.scrollTop - container.clientHeight < threshold
  }

  // Track when user scrolls up manually
  const handleScroll = () => {
    userHasScrolledUp.current = !isNearBottom()
  }

  // Auto-scroll to bottom when new messages arrive (only if user hasn't scrolled up)
  useEffect(() => {
    // Only auto-scroll if user is near bottom or hasn't scrolled up
    if (!userHasScrolledUp.current || isNearBottom()) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])


  // Handle changes to conversationId prop (e.g., when clicking "New Chat" or selecting a different conversation)
  // This also handles initial mount
  useEffect(() => {
    // Update internal state when prop changes
    setCurrentConversationId(conversationId || null)

    // Reset scroll tracking when conversation changes
    userHasScrolledUp.current = false

    // If there's a conversation ID, load it - BUT skip if we're currently sending the first message
    // (This prevents overwriting messages during streaming after creating a new conversation)
    // Using a ref here prevents the effect from re-running when the flag changes
    if (conversationId && !isSendingFirstMessageRef.current) {
      loadConversation(conversationId)
    } else if (!conversationId) {
      // No conversation ID means start fresh (new chat)
      setMessages([])
      setError(null)
      setTotalTokensUsed(0)  // Reset token count for new conversation
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally runs only on conversationId change
  }, [conversationId])

  // Handle prompt text from sidebar
  useEffect(() => {
    if (initialPromptText) {
      setInput(initialPromptText)
      onPromptUsed?.()
    }
  }, [initialPromptText, onPromptUsed])

  async function loadConversation(convId?: string) {
    const idToLoad = convId || currentConversationId
    if (!idToLoad) return

    try {
      // Fetch messages and conversation metadata in parallel
      const [data, convData] = await Promise.all([
        apiGet<{ messages: Array<{ id: string; content: string; role: string; timestamp?: string; created_at?: string; documents?: Document[]; metadata?: Record<string, unknown> }> }>(`/api/conversations/${idToLoad}/messages`),
        apiGet<{ success: boolean; conversation: { project_id?: string | null; initiative_id?: string | null; agent_id?: string | null } }>(`/api/conversations/${idToLoad}`)
      ])

      // Convert database messages to our Message format
      const loadedMessages: Message[] = data.messages.map((msg) => ({
        id: msg.id,
        content: msg.content,
        role: msg.role as 'user' | 'assistant',
        timestamp: msg.timestamp || msg.created_at || new Date().toISOString(), // Backend uses created_at
        documents: msg.documents || [],
        metadata: msg.metadata
      }))

      setMessages(loadedMessages)

      // Restore context from conversation metadata
      if (convData.success && convData.conversation) {
        const conv = convData.conversation

        // Restore project/initiative context to parent
        if (onContextRestored && (conv.project_id || conv.initiative_id)) {
          onContextRestored({
            projectId: conv.project_id,
            initiativeId: conv.initiative_id
          })
        }

        // Restore agent selection from conversation history
        // Look at the last assistant message's agent_name, or infer from context
        if (!lockedAgentId) {
          const lastAssistantMsg = [...loadedMessages].reverse().find(m => m.role === 'assistant' && m.metadata?.agent_name)
          if (lastAssistantMsg?.metadata?.agent_name) {
            // Restore the agents that were active in this conversation
            const agentName = lastAssistantMsg.metadata.agent_name as string
            // Include taskmaster if it was a project conversation
            if (conv.project_id) {
              const agents = new Set(['project_agent', 'taskmaster'])
              agents.add(agentName)
              setSelectedAgents(Array.from(agents))
            } else if (conv.initiative_id) {
              const agents = new Set(['initiative_agent'])
              agents.add(agentName)
              setSelectedAgents(Array.from(agents))
            } else {
              setSelectedAgents([agentName])
            }
          } else if (conv.project_id) {
            setSelectedAgents(['project_agent', 'taskmaster'])
          } else if (conv.initiative_id) {
            setSelectedAgents(['initiative_agent'])
          }
        }
      }

      // Estimate token count for loaded conversation (rough estimate: 1 token ≈ 4 chars)
      const estimatedTokens = loadedMessages.reduce((total, msg) => {
        return total + Math.ceil(msg.content.length / 4)
      }, 0)
      setTotalTokensUsed(estimatedTokens)
    } catch (err) {
      logger.error('Error loading conversation:', err)
      // Don't show error to user, just start with empty conversation
      setTotalTokensUsed(0)
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || [])
    setAttachedFiles(prev => [...prev, ...files])
  }

  function removeAttachment(index: number) {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }

  async function uploadAttachments() {
    if (attachedFiles.length === 0) return []

    const uploadedDocIds: string[] = []

    try {
      setUploadingFiles(true)

      for (const file of attachedFiles) {
        // Upload file
        const formData = new FormData()
        formData.append('file', file)
        // client_id auto-assigned by backend

        const uploadResponse = await authenticatedFetch('/api/documents/upload', {
          method: 'POST',
          body: formData
        })

        if (!uploadResponse.ok) throw new Error(`Failed to upload ${file.name}`)

        const uploadData = await uploadResponse.json()
        const documentId = uploadData.document_id

        // Process file
        const processResponse = await authenticatedFetch(
          `/api/documents/${documentId}/process`,
          { method: 'POST' }
        )

        if (!processResponse.ok) throw new Error(`Failed to process ${file.name}`)

        uploadedDocIds.push(documentId)
      }

      // Add uploaded document IDs to conversation context
      setConversationDocumentIds(prev => [...prev, ...uploadedDocIds])

      return uploadedDocIds
    } finally {
      setUploadingFiles(false)
    }
  }

  async function sendMessage() {
    if ((!input.trim() && attachedFiles.length === 0) || loading) return

    let messageContent = input

    // Upload attachments first if any
    let uploadedDocs: string[] = []
    let uploadedDocuments: Document[] = []
    if (attachedFiles.length > 0) {
      try {
        uploadedDocs = await uploadAttachments()
        // Create document objects for the message
        uploadedDocuments = attachedFiles.map((file, index) => ({
          id: uploadedDocs[index],
          filename: file.name,
          mime_type: file.type
        }))
        messageContent += `\n\nAttached: ${attachedFiles.map(f => f.name).join(', ')}`
      } catch {
        setError('Failed to upload attachments')
        return
      }
    }

    const userMessage: Message = {
      content: messageContent,
      role: 'user',
      timestamp: new Date().toISOString(),
      documents: uploadedDocuments
    }

    // Add user message immediately
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setAttachedFiles([])
    setLoading(true)
    setError(null)

    try {
      // Create conversation if this is the first message
      let conversationIdToUse = currentConversationId

      if (!conversationIdToUse) {
        // Mark that we're sending the first message - this prevents loadConversation
        // from overwriting our messages when the URL updates
        isSendingFirstMessageRef.current = true

        const createData = await apiPost<{ conversation_id: string }>('/api/conversations/create', {
          client_id: clientId,
          user_id: userId,
          title: 'New Conversation',
          agent_id: agentIdForConversation,  // Link conversation to specific agent (if provided)
          project_id: projectId,  // Link to project context (if provided)
          initiative_id: initiativeId  // Link to initiative context (if provided)
        })

        conversationIdToUse = createData.conversation_id
        setCurrentConversationId(conversationIdToUse)

        // Update URL to include the conversation ID (skip for agent chat tab)
        if (!lockedAgentId) {
          router.push(`/chat?id=${conversationIdToUse}`)
        }

        // Generate a title for the conversation in the background (don't await)
        // Include agent name if exactly one agent is selected
        const titlePayload: { message: string; agent_name?: string } = {
          message: userMessage.content
        }
        if (selectedAgents.length === 1) {
          titlePayload.agent_name = selectedAgents[0]
        }
        apiPost(`/api/conversations/${conversationIdToUse}/generate-title`, titlePayload)
          .then(() => {
            // Refresh the sidebar to show the new title
            onConversationCreated?.(conversationIdToUse ?? undefined)
          }).catch((err) => {
            logger.warn('Failed to generate conversation title:', err)
          })

        // Notify parent that a new conversation was created
        onConversationCreated?.(conversationIdToUse ?? undefined)
      }

      // Ensure we have a conversation ID at this point
      if (!conversationIdToUse) {
        throw new Error('Failed to create or retrieve conversation ID')
      }

      // Combine conversation documents with newly uploaded documents
      const allDocumentIds = [...new Set([...conversationDocumentIds, ...uploadedDocs])]

      // Update conversation document IDs to include new uploads
      if (uploadedDocs.length > 0) {
        setConversationDocumentIds(allDocumentIds)
      }

      if (streamingEnabled) {
        // Use streaming endpoint for better UX
        await handleStreamingResponse(userMessage.content, conversationIdToUse, allDocumentIds)
      } else {
        // Use regular endpoint for backward compatibility
        const data = await apiPost<{ message?: string; response?: string }>('/api/chat', {
          message: userMessage.content,
          client_id: clientId,
          conversation_id: conversationIdToUse,
          use_rag: true,
          document_ids: allDocumentIds.length > 0 ? allDocumentIds : undefined,
          project_id: projectId || undefined
        })

        const assistantMessage: Message = {
          content: data.message || data.response || '',
          role: 'assistant',
          timestamp: new Date().toISOString()
        }

        setMessages(prev => [...prev, assistantMessage])
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
      setLastFailedMessage(userMessage.content)
      logger.error('Chat error:', err)

      const errorMsg: Message = {
        content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
        role: 'assistant',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setLoading(false)
      isSendingFirstMessageRef.current = false // Reset after message is complete
    }
  }

  async function handleStreamingResponse(userContent: string, conversationIdToUse: string, documentIds: string[] = []) {
    // Create placeholder message for streaming content
    const placeholderMessage: Message = {
      content: '',
      role: 'assistant',
      timestamp: new Date().toISOString()
    }

    // Add placeholder immediately
    let messageIndex = -1
    setMessages(prev => {
      messageIndex = prev.length
      return [...prev, placeholderMessage]
    })

    let fullResponse = ''

    try {
      // Reset current response agent before new request
      setCurrentResponseAgent(null)

      const response = await authenticatedFetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userContent,
          client_id: clientId,
          conversation_id: conversationIdToUse,
          use_rag: true,
          document_ids: documentIds.length > 0 ? documentIds : undefined,
          agent_ids: selectedAgents.length > 0 ? selectedAgents : undefined,
          project_id: projectId || undefined
        })
      })

      if (!response.ok) {
        throw new Error(`Streaming failed: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Stream not available')
      }

      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        // Decode the chunk
        const chunk = decoder.decode(value, { stream: true })

        // Parse SSE events (format: "data: {...}\n\n")
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6))

              if (data.type === 'token') {
                // Append token to response
                fullResponse += data.content

                // Update message in place
                setMessages(prev => {
                  const updated = [...prev]
                  if (updated[messageIndex]) {
                    updated[messageIndex] = {
                      ...updated[messageIndex],
                      content: fullResponse
                    }
                  }
                  return updated
                })
              } else if (data.type === 'agent') {
                // Track which agent is responding
                setCurrentResponseAgent({
                  name: data.agent,
                  displayName: data.display_name
                })
                logger.debug(`Agent responding: ${data.display_name}`)

                // Update message metadata with agent info
                setMessages(prev => {
                  const updated = [...prev]
                  if (updated[messageIndex]) {
                    updated[messageIndex] = {
                      ...updated[messageIndex],
                      metadata: {
                        ...updated[messageIndex].metadata,
                        agent_name: data.agent,
                        agent_display_name: data.display_name
                      }
                    }
                  }
                  return updated
                })
              } else if (data.type === 'task_proposals') {
                // Taskmaster proposed tasks - store in message metadata
                logger.debug(`Received ${data.tasks?.length} task proposals`)
                setMessages(prev => {
                  const updated = [...prev]
                  if (updated[messageIndex]) {
                    updated[messageIndex] = {
                      ...updated[messageIndex],
                      metadata: {
                        ...updated[messageIndex].metadata,
                        task_proposals: data.tasks,
                        task_proposals_project_id: data.project_id,
                        task_proposals_conversation_id: data.conversation_id,
                      }
                    }
                  }
                  return updated
                })
              } else if (data.type === 'tasks_created') {
                // Tasks were created from proposals
                logger.debug(`${data.count} tasks created`)
                toast.success(`${data.count} task${data.count !== 1 ? 's' : ''} created!`)
              } else if (data.type === 'done') {
                logger.debug('Stream complete:', data.tokens)
                // Accumulate tokens for context window tracking
                if (data.tokens?.total) {
                  setTotalTokensUsed(prev => prev + data.tokens.total)
                }
                // Set the message ID from backend so dig-deeper and other features work
                if (data.message_id) {
                  setMessages(prev => {
                    const updated = [...prev]
                    if (messageIndex >= 0 && messageIndex < updated.length) {
                      updated[messageIndex] = { ...updated[messageIndex], id: data.message_id }
                    }
                    return updated
                  })
                }
              } else if (data.type === 'error') {
                throw new Error(data.error)
              } else if (data.type === 'context') {
                logger.debug(`Using ${data.count} context chunks`)
              }
            } catch (parseError) {
              logger.warn('Failed to parse SSE data:', line, parseError)
            }
          }
        }
      }
    } catch (streamError) {
      logger.error('Streaming error:', streamError)
      throw streamError
    }
  }

  function retryLastMessage() {
    if (!lastFailedMessage) return

    setInput(lastFailedMessage)
    setLastFailedMessage(null)
    setError(null)

    // Automatically send after a brief delay
    setTimeout(() => {
      sendMessage()
    }, 100)
  }

  async function handleDigDeeper(messageId: string, originalContent: string) {
    if (!currentConversationId || digDeeperLoading) return

    setDigDeeperLoading(messageId)

    // Create placeholder message for streaming content
    const placeholderMessage: Message = {
      content: '',
      role: 'assistant',
      timestamp: new Date().toISOString(),
      metadata: { dig_deeper_response: true }
    }

    // Add placeholder immediately
    let messageIndex = -1
    setMessages(prev => {
      messageIndex = prev.length
      return [...prev, placeholderMessage]
    })

    let fullResponse = ''

    try {
      const response = await authenticatedFetch('/api/chat/dig-deeper', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: currentConversationId,
          message_id: messageId,
          original_content: originalContent
        })
      })

      if (!response.ok) {
        throw new Error(`Dig deeper failed: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Stream not available')
      }

      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6))

              if (data.type === 'token') {
                fullResponse += data.content
                setMessages(prev => {
                  const updated = [...prev]
                  if (updated[messageIndex]) {
                    updated[messageIndex] = {
                      ...updated[messageIndex],
                      content: fullResponse
                    }
                  }
                  return updated
                })
              } else if (data.type === 'done') {
                logger.debug('Dig deeper complete:', data.tokens)
              } else if (data.type === 'error') {
                throw new Error(data.error)
              }
            } catch (parseError) {
              logger.warn('Failed to parse SSE data:', line, parseError)
            }
          }
        }
      }

      // Reload messages to get server-assigned IDs
      await loadConversation(currentConversationId)

    } catch (err) {
      logger.error('Dig deeper error:', err)
      toast.error('Failed to elaborate on response')
      // Remove the placeholder message on error
      setMessages(prev => prev.filter((_, i) => i !== messageIndex))
    } finally {
      setDigDeeperLoading(null)
    }
  }

  // Handle inline dig-deeper section expansion (non-streaming, returns content directly)
  async function handleDigDeeperSection(messageId: string, originalContent: string, sectionId: string): Promise<string> {
    if (!currentConversationId) {
      throw new Error('No conversation active')
    }

    try {
      const response = await apiPost<{ expanded_content?: string }>('/api/chat/dig-deeper-section', {
        conversation_id: currentConversationId,
        message_id: messageId,
        original_content: originalContent,
        section_id: sectionId
      })

      if (response.expanded_content) {
        return response.expanded_content
      }

      throw new Error('No content returned')
    } catch (err) {
      logger.error('Dig deeper section error:', err)
      toast.error('Failed to expand section')
      throw err
    }
  }

  // Handle Save to KB button click
  function handleSaveToKB(messageId: string, content: string) {
    setSaveToKBModal({ isOpen: true, messageId, content })
  }

  // Handle actual save to KB
  async function handleSaveToKBConfirm(title: string, agentIds: string[] | null) {
    try {
      setIsSavingToKB(true)

      await apiPost('/api/documents/save-from-chat', {
        title,
        content: saveToKBModal.content,
        message_id: saveToKBModal.messageId,
        conversation_id: currentConversationId,
        agent_ids: agentIds
      })

      toast.success('Saved to knowledge base')
      setSaveToKBModal({ isOpen: false, messageId: '', content: '' })
    } catch (err) {
      logger.error('Save to KB error:', err)
      toast.error('Failed to save to knowledge base')
    } finally {
      setIsSavingToKB(false)
    }
  }

  function handleKeyPress(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Search functionality
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      setCurrentSearchIndex(0)
      return
    }

    const query = searchQuery.toLowerCase()
    const results: number[] = []

    messages.forEach((msg, index) => {
      if (msg.content.toLowerCase().includes(query)) {
        results.push(index)
      }
    })

    setSearchResults(results)
    setCurrentSearchIndex(0)

    // Scroll to first result
    if (results.length > 0) {
      setTimeout(() => {
        searchResultRefs.current[results[0]]?.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        })
      }, 100)
    }
  }, [searchQuery, messages])

  return (
    <div className="flex flex-col h-full page-bg">
      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-6 py-4"
        aria-live="polite"
        aria-label="Chat messages"
      >
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-secondary text-lg font-medium">
                Start a Conversation
              </p>
            </div>
          ) : (
            messages.map((msg, index) => {
              const isCurrentSearchResult = searchResults[currentSearchIndex] === index

              return (
                <div key={`msg-${index}`}>
                  <div
                    ref={(el) => { searchResultRefs.current[index] = el }}
                    className={isCurrentSearchResult ? 'ring-2 ring-teal-500 rounded-lg' : ''}
                  >
                    <ChatMessage
                      content={msg.content}
                      role={msg.role}
                      timestamp={msg.timestamp}
                      documents={msg.documents}
                      conversationId={currentConversationId || undefined}
                      messageId={msg.id}
                      onDigDeeper={handleDigDeeper}
                      onDigDeeperSection={handleDigDeeperSection}
                      isDigDeeperLoading={digDeeperLoading === msg.id}
                      metadata={msg.metadata}
                      onSaveToKB={handleSaveToKB}
                    />
                  </div>
                </div>
              )
            })
          )}

          {/* Loading indicator */}
          {loading && (
            <div className="mb-4 flex justify-start">
              <div className="bg-hover rounded-lg px-4 py-3 max-w-[70%]">
                <LoadingSpinner type="dots" />
              </div>
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Error display with retry */}
      {error && (
        <div className="bg-red-50 border-t border-red-200 px-6 py-3">
          <div className="max-w-4xl mx-auto flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1">
              <span className="text-red-600 text-sm flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                {error}
              </span>
              {lastFailedMessage && (
                <button
                  onClick={retryLastMessage}
                  className="px-3 py-1 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
                  disabled={loading}
                >
                  Retry
                </button>
              )}
            </div>
            <button
              onClick={() => {
                setError(null)
                setLastFailedMessage(null)
              }}
              className="text-red-600 hover:opacity-70 transition-opacity"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="bg-card border-t border-default px-6 py-4 shadow-lg">
        <div className="max-w-4xl mx-auto">

          {/* Agent Selector - hidden when agent is locked */}
          {!lockedAgentId ? (
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-muted">Agent:</span>
                <AgentSelector
                  selectedAgents={selectedAgents}
                  onAgentsChange={setSelectedAgents}
                  maxAgents={3}
                  disabled={loading}
                />
              </div>
              {/* Show current responding agent during streaming */}
              {loading && currentResponseAgent && (
                <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium border ${getAgentColor(currentResponseAgent.name)}`}>
                  <AgentIcon name={currentResponseAgent.name} size="sm" />
                  <span>{currentResponseAgent.displayName} responding...</span>
                </div>
              )}
            </div>
          ) : (
            /* Locked agent badge - shown when chatting with specific agent */
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-muted">Chatting with:</span>
                <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border ${getAgentColor(lockedAgentId)}`}>
                  <AgentIcon name={lockedAgentId} size="sm" />
                  <span>{lockedAgentDisplayName || lockedAgentId}</span>
                </div>
              </div>
              {/* Show responding indicator during streaming */}
              {loading && (
                <span className="text-xs text-muted-foreground animate-pulse">responding...</span>
              )}
            </div>
          )}

          {/* Attached Files Preview */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachedFiles.map((file, index) => (
                <div key={index} className="attachment-pill">
                  <span className="text-primary">{file.name}</span>
                  <button
                    onClick={() => removeAttachment(index)}
                    className="text-muted hover:opacity-70"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex space-x-3">
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.doc,.csv,.txt,.md,.json,.xml"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />

            {/* Attach button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={loading || uploadingFiles}
              className="btn-icon"
              title="Attach files"
            >
              Attach
            </button>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={loading || uploadingFiles}
              rows={4}
              className="textarea-field flex-1"
            />

            <button
              onClick={sendMessage}
              disabled={loading || uploadingFiles || (!input.trim() && attachedFiles.length === 0)}
              className="btn-primary px-6 py-3"
            >
              {uploadingFiles ? 'Uploading...' : loading ? 'Sending...' : 'Send'}
            </button>
          </div>
          <div className="flex justify-between items-center mt-2">
            <p className="form-helper">
              Attach files for this conversation • Press Enter to send • Shift+Enter for new line
            </p>
            {/* Context window usage indicator */}
            {totalTokensUsed > 0 && (
              <p className={`text-xs ${
                contextPercentage >= 90 ? 'text-red-500 font-medium' :
                contextPercentage >= 75 ? 'text-amber-500' :
                'text-muted'
              }`}>
                {contextPercentage.toFixed(1)}% context used
                {contextPercentage >= 90 && ' - approaching limit!'}
                {contextPercentage >= 75 && contextPercentage < 90 && ' - consider starting new chat'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Save to KB Modal */}
      <SaveToKBModal
        isOpen={saveToKBModal.isOpen}
        onClose={() => setSaveToKBModal({ isOpen: false, messageId: '', content: '' })}
        onSave={handleSaveToKBConfirm}
        defaultTitle=""
        isSaving={isSavingToKB}
      />
    </div>
  )
}
