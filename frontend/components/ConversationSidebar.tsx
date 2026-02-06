'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
// Link import intentionally removed - navigation handled via router
import { useDebounce } from 'use-debounce'
import { apiGet, apiDelete, apiPost, apiPatch } from '@/lib/api'
import LoadingSpinner from './LoadingSpinner'
import ConfirmModal from './ConfirmModal'
import toast from 'react-hot-toast'
import { API_BASE_URL } from '@/lib/config'
import { logger } from '@/lib/logger'

interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count?: number
  in_knowledge_base?: boolean
  added_to_kb_at?: string | null
  archived?: boolean
  archived_at?: string | null
  project_id?: string | null
  initiative_id?: string | null
}

interface Project {
  id: string
  title: string
  project_code?: string
}

interface Initiative {
  id: string
  name: string
}

interface ConversationSidebarProps {
  clientId?: string  // Optional - backend auto-assigns default client
  userId?: string
  currentConversationId?: string | null
  apiBaseUrl?: string
  className?: string
  refreshTrigger?: number
  // Context filter props
  projectId?: string | null  // Filter by project (from URL or selection)
  initiativeId?: string | null  // Filter by initiative (from URL or selection)
  onProjectChange?: (projectId: string | null) => void
  onInitiativeChange?: (initiativeId: string | null) => void
}

export default function ConversationSidebar({
  clientId,
  userId,
  currentConversationId,
  apiBaseUrl: _apiBaseUrl = API_BASE_URL,
  className = '',
  refreshTrigger,
  projectId: externalProjectId,
  initiativeId: externalInitiativeId,
  onProjectChange,
  onInitiativeChange,
}: ConversationSidebarProps) {
  const router = useRouter()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [renamingConversationId, setRenamingConversationId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [processingKBId, setProcessingKBId] = useState<string | null>(null)

  // Archive and search state
  const [showArchived, setShowArchived] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearchQuery] = useDebounce(searchQuery, 500) // 500ms delay
  const [isSearching, setIsSearching] = useState(false)

  // Context filter state
  const [projects, setProjects] = useState<Project[]>([])
  const [initiatives, setInitiatives] = useState<Initiative[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(externalProjectId || null)
  const [selectedInitiativeId, setSelectedInitiativeId] = useState<string | null>(externalInitiativeId || null)
  const [loadingFilters, setLoadingFilters] = useState(true)

  // Sync external props with internal state
  useEffect(() => {
    setSelectedProjectId(externalProjectId || null)
  }, [externalProjectId])

  useEffect(() => {
    setSelectedInitiativeId(externalInitiativeId || null)
  }, [externalInitiativeId])

  // Load projects and initiatives for dropdowns
  useEffect(() => {
    async function loadFilterOptions() {
      try {
        setLoadingFilters(true)
        const [projectsRes, initiativesRes] = await Promise.all([
          apiGet<Project[]>('/api/projects?limit=100'),
          apiGet<{ initiatives: Initiative[] }>('/api/disco/initiatives?limit=100'),
        ])
        setProjects(Array.isArray(projectsRes) ? projectsRes : [])
        setInitiatives(initiativesRes.initiatives || [])
      } catch (err) {
        logger.error('Error loading filter options:', err)
      } finally {
        setLoadingFilters(false)
      }
    }
    loadFilterOptions()
  }, [])

  // Modal state
  const [confirmModal, setConfirmModal] = useState<{
    open: boolean
    title: string
    message: string
    onConfirm: () => void
  }>({
    open: false,
    title: '',
    message: '',
    onConfirm: () => {}
  })

  useEffect(() => {
    loadConversations()
    // eslint-disable-next-line react-hooks/exhaustive-deps -- loadConversations is stable
  }, [clientId, showArchived, debouncedSearchQuery, refreshTrigger, selectedProjectId, selectedInitiativeId])

  async function loadConversations() {
    // Skip loading if no clientId (shouldn't happen in normal use)
    if (!clientId) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setIsSearching(!!debouncedSearchQuery)

      let data: { success: boolean; conversations: Conversation[] }

      // Build query params for context filtering
      const params = new URLSearchParams()
      if (selectedProjectId) params.append('project_id', selectedProjectId)
      if (selectedInitiativeId) params.append('initiative_id', selectedInitiativeId)
      params.append('include_archived', showArchived ? 'true' : 'false')

      if (debouncedSearchQuery) {
        // Use search endpoint when there's a query (debounced to avoid excessive API calls)
        params.append('query', debouncedSearchQuery)
        params.append('limit', '50')
        data = await apiGet<{ success: boolean; conversations: Conversation[] }>(`/api/conversations/search?${params.toString()}`)
      } else {
        // Use regular endpoint for listing conversations
        params.append('client_id', clientId)
        data = await apiGet<{ success: boolean; conversations: Conversation[] }>(`/api/conversations?${params.toString()}`)
      }

      if (data.success && data.conversations) {
        setConversations(data.conversations)
      } else {
        setConversations([])
      }
    } catch (err) {
      logger.error('Error loading conversations:', err)
      setConversations([])
    } finally {
      setLoading(false)
      setIsSearching(false)
    }
  }

  function handleNewConversation() {
    // Build URL with context params if filters are set
    const params = new URLSearchParams()
    params.append('t', Date.now().toString())
    if (selectedProjectId) params.append('project_id', selectedProjectId)
    if (selectedInitiativeId) params.append('initiative_id', selectedInitiativeId)
    router.push(`/chat?${params.toString()}`)
  }

  function handleSelectConversation(conversationId: string) {
    router.push(`/chat?id=${conversationId}`)
  }

  function formatDate(isoString: string) {
    if (!isoString) return 'Unknown'

    const date = new Date(isoString)

    // Check if date is invalid
    if (isNaN(date.getTime())) return 'Unknown'

    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  async function handleDeleteConversation(conversationId: string, e: React.MouseEvent) {
    e.stopPropagation()

    setConfirmModal({
      open: true,
      title: 'Delete Conversation',
      message: 'Are you sure you want to delete this conversation? This action cannot be undone.',
      onConfirm: async () => {
        await deleteConversation(conversationId)
      }
    })
  }

  async function deleteConversation(conversationId: string) {
    try {
      await apiDelete(`/api/conversations/${conversationId}`)

      // Refresh conversations list
      await loadConversations()

      // If we deleted the current conversation, redirect to new chat
      if (conversationId === currentConversationId) {
        router.push('/chat')
      }
    } catch (err) {
      logger.error('Error deleting conversation:', err)
      toast.error('Failed to delete conversation. Please try again.')
    }
  }

  function handleStartRename(conversation: Conversation, e: React.MouseEvent) {
    e.stopPropagation()
    setRenamingConversationId(conversation.id)
    setRenameValue(conversation.title)
  }

  async function handleSaveRename(conversationId: string) {
    if (!renameValue.trim()) {
      toast.error('Title cannot be empty')
      handleCancelRename()
      return
    }

    try {
      await apiPatch(`/api/conversations/${conversationId}`, {
        title: renameValue.trim()
      })

      // Refresh conversations list
      await loadConversations()

      // Clear rename state
      setRenamingConversationId(null)
      setRenameValue('')
    } catch (err) {
      logger.error('Error renaming conversation:', err)
      toast.error('Failed to rename conversation. Please try again.')
      // Cancel rename mode to prevent error loop
      handleCancelRename()
    }
  }

  function handleCancelRename() {
    setRenamingConversationId(null)
    setRenameValue('')
  }

  async function handleToggleKnowledgeBase(conversationId: string, currentStatus: boolean, e: React.MouseEvent) {
    e.stopPropagation()

    // Prevent double-clicks while processing
    if (processingKBId) return

    const action = currentStatus ? 'remove-from-kb' : 'add-to-kb'
    const actionText = currentStatus ? 'remove from' : 'add to'

    setConfirmModal({
      open: true,
      title: currentStatus ? 'Remove from Knowledge Base' : 'Add to Knowledge Base',
      message: `Are you sure you want to ${actionText} your knowledge base?`,
      onConfirm: async () => {
        await toggleKnowledgeBase(conversationId, currentStatus, action)
      }
    })
  }

async function toggleKnowledgeBase(conversationId: string, currentStatus: boolean, action: string) {
    const actionText = action === 'add-to-kb' ? 'add to' : 'remove from'

    // Set loading state
    setProcessingKBId(conversationId)

    try {
      const data = await apiPost<{ message?: string; data?: { embedding_cost_usd?: number } }>(`/api/conversations/${conversationId}/${action}`, {})

      // Show success toast with cost info if available
      let successMessage = data.message || `Successfully ${actionText === 'add to' ? 'added' : 'removed'}`
      if (data.data?.embedding_cost_usd && actionText === 'add to') {
        successMessage += ` (Cost: $${data.data.embedding_cost_usd.toFixed(4)})`
      }
      toast.success(successMessage)

      // Refresh conversations to show updated status
      await loadConversations()
    } catch (err) {
      logger.error(`Error toggling KB status:`, err)
      toast.error(`Failed to ${actionText} knowledge base. Please try again.`)
    } finally{
      // Clear loading state
      setProcessingKBId(null)
    }
  }

  async function handleArchiveConversation(conversationId: string, e: React.MouseEvent) {
    e.stopPropagation()

    setConfirmModal({
      open: true,
      title: 'Archive Conversation',
      message: 'Are you sure you want to archive this conversation? You can restore it later from the archived view.',
      onConfirm: async () => {
        await archiveConversation(conversationId)
      }
    })
  }

  async function archiveConversation(conversationId: string) {
    try {
      await apiPost(`/api/conversations/${conversationId}/archive`, {})

      toast.success('Conversation archived successfully')

      // Refresh conversations list
      await loadConversations()

      // If we archived the current conversation, redirect to new chat
      if (conversationId === currentConversationId) {
        router.push('/chat')
      }
    } catch (err) {
      logger.error('Error archiving conversation:', err)
      toast.error('Failed to archive conversation. Please try again.')
    }
  }

  async function handleRestoreConversation(conversationId: string, e: React.MouseEvent) {
    e.stopPropagation()

    try {
      await apiPost(`/api/conversations/${conversationId}/restore`, {})

      toast.success('Conversation restored successfully')

      // Refresh conversations list
      await loadConversations()
    } catch (err) {
      logger.error('Error restoring conversation:', err)
      toast.error('Failed to restore conversation. Please try again.')
    }
  }

  return (
    <div className={`flex flex-col h-full bg-card border-r border-default ${className}`}>
      {/* Header */}
      <div className="border-b border-default">
        <div className="px-4 py-2">
          <button
            onClick={handleNewConversation}
            className="btn-primary w-full flex items-center justify-center gap-2 !py-1.5"
          >
            <span className="text-lg">+</span> New Chat
          </button>
        </div>

        {/* Context Filters */}
        <div className="px-4 pb-2 space-y-2">
          {/* Project Filter */}
          <div>
            <label className="text-xs text-muted block mb-1">Project:</label>
            <select
              value={selectedProjectId || ''}
              onChange={(e) => {
                const value = e.target.value || null
                setSelectedProjectId(value)
                onProjectChange?.(value)
              }}
              className="input-field w-full text-sm py-1.5"
              disabled={loadingFilters}
            >
              <option value="">None</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.project_code ? `${project.project_code}: ` : ''}{project.title}
                </option>
              ))}
            </select>
          </div>

          {/* Initiative Filter */}
          <div>
            <label className="text-xs text-muted block mb-1">Initiative:</label>
            <select
              value={selectedInitiativeId || ''}
              onChange={(e) => {
                const value = e.target.value || null
                setSelectedInitiativeId(value)
                onInitiativeChange?.(value)
              }}
              className="input-field w-full text-sm py-1.5"
              disabled={loadingFilters}
            >
              <option value="">None</option>
              {initiatives.map((initiative) => (
                <option key={initiative.id} value={initiative.id}>
                  {initiative.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Search Input */}
        <div className="px-4 pb-2">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search conversations..."
              className="input-field w-full pl-3 pr-8 py-1.5 text-sm"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted hover:text-primary"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Archive Toggle */}
        <div className="px-4 pb-2">
          <button
            onClick={() => setShowArchived(!showArchived)}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              showArchived
                ? 'bg-primary text-white'
                : 'bg-hover text-muted hover:bg-gray-200'
            }`}
          >
            {showArchived ? 'Hide Archived' : 'Show Archived'}
          </button>
        </div>
      </div>

      {/* Main Content - split into conversations and quick prompts */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-4 text-center text-muted">
              <div className="flex justify-center mb-2">
                <LoadingSpinner size="sm" />
              </div>
              Loading...
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted">
              No conversations yet
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className="relative group"
                >
                  {renamingConversationId === conv.id ? (
                    // Rename mode
                    <div className="px-3 py-3 rounded-lg bg-hover">
                      <input
                        type="text"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleSaveRename(conv.id)
                          } else if (e.key === 'Escape') {
                            handleCancelRename()
                          }
                        }}
                        onBlur={handleCancelRename}
                        autoFocus
                        className="input-field w-full px-2 py-1 text-sm"
                      />
                    </div>
                  ) : (
                    // Normal mode
                    <div
                      className={`px-3 py-2.5 rounded-lg transition-all cursor-pointer ${
                        conv.id === currentConversationId
                          ? 'sidebar-item-active'
                          : 'sidebar-item'
                      }`}
                      onClick={() => handleSelectConversation(conv.id)}
                    >
                      {/* First line: Title with status badges */}
                      <div className="flex items-start gap-2 mb-1">
                        <div className="font-medium text-sm flex-1 min-w-0">
                          {conv.title}
                        </div>
                        {/* Context badge - show project or initiative name */}
                        {conv.project_id && !selectedProjectId && (
                          <span
                            className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded flex-shrink-0 truncate max-w-[80px]"
                            title={`Project: ${projects.find(p => p.id === conv.project_id)?.title || 'Unknown'}`}
                          >
                            {projects.find(p => p.id === conv.project_id)?.project_code || 'Proj'}
                          </span>
                        )}
                        {conv.initiative_id && !selectedInitiativeId && (
                          <span
                            className="text-xs px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded flex-shrink-0 truncate max-w-[80px]"
                            title={`Initiative: ${initiatives.find(i => i.id === conv.initiative_id)?.name || 'Unknown'}`}
                          >
                            Init
                          </span>
                        )}
                        {/* KB status indicator */}
                        {conv.in_knowledge_base && (
                          <span
                            className="text-xs px-1.5 py-0.5 bg-teal-100 text-teal-700 rounded flex-shrink-0"
                            title="In Knowledge Base"
                          >
                            KB
                          </span>
                        )}
                        {/* Archived status indicator */}
                        {conv.archived && (
                          <span
                            className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-700 rounded flex-shrink-0"
                            title="Archived"
                          >
                            Archived
                          </span>
                        )}
                      </div>

                      {/* Second line: Date on left, icons on right */}
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-xs text-muted flex-shrink-0">
                          {formatDate(conv.updated_at)}
                        </div>

                        {/* Action icons */}
                        <div className="flex items-center gap-1">
                        {processingKBId === conv.id ? (
                          <div className="p-1" title="Processing...">
                            <LoadingSpinner size="sm" />
                          </div>
                        ) : (
                          <button
                            onClick={(e) => handleToggleKnowledgeBase(conv.id, !!conv.in_knowledge_base, e)}
                            className="hover:opacity-70 p-1 opacity-60 hover:opacity-100 transition-opacity"
                            title={conv.in_knowledge_base ? 'Remove from KB' : 'Add to KB'}
                          >
                            {conv.in_knowledge_base ? (
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" className="text-teal-600">
                                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
                              </svg>
                            ) : (
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="icon-muted">
                                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
                              </svg>
                            )}
                          </button>
                        )}
                        <button
                          onClick={(e) => handleStartRename(conv, e)}
                          className="hover:opacity-70 p-1 icon-muted opacity-60 hover:opacity-100 transition-opacity"
                          title="Rename"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                          </svg>
                        </button>
                        {conv.archived ? (
                          <button
                            onClick={(e) => handleRestoreConversation(conv.id, e)}
                            className="hover:opacity-70 p-1 icon-muted opacity-60 hover:opacity-100 transition-opacity"
                            title="Reactivate"
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                              <polyline points="9 22 9 12 15 12 15 22"></polyline>
                            </svg>
                          </button>
                        ) : (
                          <>
                            <button
                              onClick={(e) => handleArchiveConversation(conv.id, e)}
                              className="hover:opacity-70 p-1 icon-muted opacity-60 hover:opacity-100 transition-opacity"
                              title="Archive"
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="21 8 21 21 3 21 3 8"></polyline>
                                <rect x="1" y="3" width="22" height="5"></rect>
                                <line x1="10" y1="12" x2="14" y2="12"></line>
                              </svg>
                            </button>
                            <button
                              onClick={(e) => handleDeleteConversation(conv.id, e)}
                              className="hover:opacity-70 p-1 icon-muted opacity-60 hover:opacity-100 transition-opacity"
                              title="Delete"
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                              </svg>
                            </button>
                          </>
                        )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>


      </div>

      {/* Confirm Modal */}
      <ConfirmModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        onConfirm={confirmModal.onConfirm}
        onCancel={() => setConfirmModal({ ...confirmModal, open: false })}
      />
    </div>
  )
}
