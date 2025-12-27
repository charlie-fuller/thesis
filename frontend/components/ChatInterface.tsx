'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import ChatMessage from './ChatMessage'
import LoadingSpinner from './LoadingSpinner'
import {
  authenticatedFetch,
  apiGet,
  apiPost,
  getProjects,
  addConversationToProject,
  removeConversationFromProject,
  type Project
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
  onConversationCreated?: () => void
  initialProjectId?: string | null  // Auto-assign new conversations to this project
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
  initialProjectId
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
  const [isSendingFirstMessage, setIsSendingFirstMessage] = useState(false) // Track when creating new conversation

  // Project assignment state
  const [projects, setProjects] = useState<Project[]>([])
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)
  const [showProjectDropdown, setShowProjectDropdown] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- loadingProjects kept for future loading state UI
  const [_loadingProjects, setLoadingProjects] = useState(false)

  // Context window tracking - Claude Sonnet 4 has 200K token context
  const CLAUDE_CONTEXT_WINDOW = 200000
  const [totalTokensUsed, setTotalTokensUsed] = useState(0)
  const contextPercentage = Math.min((totalTokensUsed / CLAUDE_CONTEXT_WINDOW) * 100, 100)

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
    if (conversationId && !isSendingFirstMessage) {
      loadConversation(conversationId)
    } else if (!conversationId) {
      // No conversation ID means start fresh (new chat)
      setMessages([])
      setError(null)
    }
  }, [conversationId, isSendingFirstMessage]) // Run when conversationId prop changes

  // Handle prompt text from sidebar
  useEffect(() => {
    if (initialPromptText) {
      setInput(initialPromptText)
      onPromptUsed?.()
    }
  }, [initialPromptText, onPromptUsed])

  // Load projects for assignment dropdown
  useEffect(() => {
    loadProjects()
  }, [])

  // Load conversation's current project when conversation changes
  useEffect(() => {
    if (currentConversationId) {
      loadConversationProject(currentConversationId)
    } else {
      setCurrentProjectId(null)
    }
  }, [currentConversationId])

  async function loadProjects() {
    try {
      setLoadingProjects(true)
      const response = await getProjects('active')
      if (response.success) {
        setProjects(response.projects)
      }
    } catch (err) {
      logger.error('Error loading projects:', err)
    } finally {
      setLoadingProjects(false)
    }
  }

  async function loadConversationProject(convId: string) {
    try {
      const data = await apiGet<{ project_id?: string | null }>(`/api/conversations/${convId}`)
      setCurrentProjectId(data.project_id || null)
    } catch (err) {
      logger.error('Error loading conversation project:', err)
    }
  }

  async function handleAssignToProject(projectId: string | null) {
    if (!currentConversationId) {
      toast.error('Save the conversation first by sending a message')
      return
    }

    try {
      if (projectId) {
        await addConversationToProject(projectId, currentConversationId)
        const project = projects.find(p => p.id === projectId)
        toast.success(`Added to "${project?.title || 'project'}"`)
      } else if (currentProjectId) {
        await removeConversationFromProject(currentProjectId, currentConversationId)
        toast.success('Removed from project')
      }
      setCurrentProjectId(projectId)
      setShowProjectDropdown(false)
    } catch (err) {
      logger.error('Error updating project assignment:', err)
      toast.error('Failed to update project')
    }
  }

  async function loadConversation(convId?: string) {
    const idToLoad = convId || currentConversationId
    if (!idToLoad) return

    try {

      const data = await apiGet<{ messages: Array<{ id: string; content: string; role: string; timestamp?: string; created_at?: string; documents?: Document[]; metadata?: Record<string, unknown> }> }>(`/api/conversations/${idToLoad}/messages`)

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
    } catch (err) {
      logger.error('Error loading conversation:', err)
      // Don't show error to user, just start with empty conversation
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
        setIsSendingFirstMessage(true)

        const createData = await apiPost<{ conversation_id: string }>('/api/conversations/create', {
          client_id: clientId,
          user_id: userId,
          title: 'New Conversation'
        })

        conversationIdToUse = createData.conversation_id
        setCurrentConversationId(conversationIdToUse)

        // Update URL to include the conversation ID
        router.push(`/chat?id=${conversationIdToUse}`)

        // Auto-assign to project if initialProjectId was provided
        if (initialProjectId) {
          try {
            await addConversationToProject(initialProjectId, conversationIdToUse)
            setCurrentProjectId(initialProjectId)
          } catch (err) {
            logger.error('Failed to auto-assign conversation to project:', err)
            // Don't fail the whole operation, just log the error
          }
        }

        // Notify parent that a new conversation was created
        onConversationCreated?.()
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
          document_ids: allDocumentIds.length > 0 ? allDocumentIds : undefined
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
      setIsSendingFirstMessage(false) // Reset after message is complete
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
          document_ids: documentIds.length > 0 ? documentIds : undefined
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
              } else if (data.type === 'done') {
                logger.debug('Stream complete:', data.tokens)
                // Update total tokens used for context window tracking
                if (data.tokens?.input) {
                  setTotalTokensUsed(data.tokens.input)
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

  const currentProject = projects.find(p => p.id === currentProjectId)

  return (
    <div className="flex flex-col h-full page-bg">
      {/* Project assignment bar - only show when there's a conversation */}
      {currentConversationId && (
        <div className="border-b border-default px-4 py-2 flex items-center justify-between bg-card">
          <div className="relative">
            <button
              onClick={() => setShowProjectDropdown(!showProjectDropdown)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md hover:bg-hover transition-colors"
            >
              <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              {currentProject ? (
                <span className="text-primary font-medium">{currentProject.title}</span>
              ) : (
                <span className="text-muted">Add to project...</span>
              )}
              <svg className="w-3 h-3 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Dropdown */}
            {showProjectDropdown && (
              <div className="absolute top-full left-0 mt-1 w-64 bg-card border border-default rounded-lg shadow-lg z-50">
                <div className="py-1">
                  {currentProjectId && (
                    <button
                      onClick={() => handleAssignToProject(null)}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-hover flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      Remove from project
                    </button>
                  )}
                  {projects.length === 0 ? (
                    <div className="px-4 py-3 text-sm text-muted">
                      No projects yet. Create one from the Projects page.
                    </div>
                  ) : (
                    projects.map(project => (
                      <button
                        key={project.id}
                        onClick={() => handleAssignToProject(project.id)}
                        className={`w-full text-left px-4 py-2 text-sm hover:bg-hover flex items-center justify-between ${
                          project.id === currentProjectId ? 'bg-accent' : ''
                        }`}
                      >
                        <span className="text-primary truncate">{project.title}</span>
                        {project.id === currentProjectId && (
                          <svg className="w-4 h-4 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

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
              <span className="text-red-600 text-sm">⚠ {error}</span>
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
              className="text-red-600 hover:opacity-70 transition-opacity font-bold"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="bg-card border-t border-default px-6 py-4 shadow-lg">
        <div className="max-w-4xl mx-auto">

          {/* Attached Files Preview */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachedFiles.map((file, index) => (
                <div key={index} className="attachment-pill">
                  <span className="text-primary">{file.name}</span>
                  <button
                    onClick={() => removeAttachment(index)}
                    className="text-xs text-muted hover:opacity-70"
                  >
                    ✕
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
    </div>
  )
}
