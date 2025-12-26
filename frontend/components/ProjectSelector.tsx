'use client'

import { useState, useEffect } from 'react'
import {
  getProjects,
  createProject,
  updateProject,
  deleteProject,
  addConversationToProject,
  removeConversationFromProject,
  type Project
} from '@/lib/api'
import LoadingSpinner from './LoadingSpinner'
import ConfirmModal from './ConfirmModal'
import toast from 'react-hot-toast'
import { logger } from '@/lib/logger'

// Phase color configuration
const PHASE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'Analysis': { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-200' },
  'Design': { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-200' },
  'Development': { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-200' },
  'Implementation': { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-200' },
  'Evaluation': { bg: 'bg-pink-100', text: 'text-pink-700', border: 'border-pink-200' },
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  'active': { bg: 'bg-green-100', text: 'text-green-700' },
  'archived': { bg: 'bg-gray-100', text: 'text-gray-700' },
  'complete': { bg: 'bg-blue-100', text: 'text-blue-700' },
}

interface ProjectSelectorProps {
  currentConversationId?: string | null
  onProjectChange?: (projectId: string | null) => void
  className?: string
  selectedProjectId?: string | null  // Controlled selection from parent
}

export default function ProjectSelector({
  currentConversationId,
  onProjectChange,
  className = '',
  selectedProjectId: controlledSelectedId
}: ProjectSelectorProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [internalSelectedId, setInternalSelectedId] = useState<string | null>(null)

  // Use controlled value if provided, otherwise use internal state
  const selectedProjectId = controlledSelectedId !== undefined ? controlledSelectedId : internalSelectedId
  const setSelectedProjectId = (id: string | null) => {
    setInternalSelectedId(id)
    onProjectChange?.(id)
  }

  // Form state
  const [formTitle, setFormTitle] = useState('')
  const [formDescription, setFormDescription] = useState('')

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
    loadProjects()
  }, [])

  async function loadProjects() {
    try {
      setLoading(true)
      const response = await getProjects()
      if (response.success) {
        setProjects(response.projects)
      }
    } catch (err) {
      logger.error('Error loading projects:', err)
    } finally {
      setLoading(false)
    }
  }

  function handleStartCreate() {
    setShowCreateForm(true)
    setEditingProject(null)
    setFormTitle('')
    setFormDescription('')
  }

  function handleStartEdit(project: Project, e: React.MouseEvent) {
    e.stopPropagation()
    setEditingProject(project)
    setShowCreateForm(false)
    setFormTitle(project.title)
    setFormDescription(project.description || '')
  }

  function handleCancelForm() {
    setShowCreateForm(false)
    setEditingProject(null)
    setFormTitle('')
    setFormDescription('')
  }

  async function handleSaveProject() {
    if (!formTitle.trim()) {
      toast.error('Project title is required')
      return
    }

    try {
      if (editingProject) {
        await updateProject(editingProject.id, {
          title: formTitle.trim(),
          description: formDescription.trim() || undefined
        })
        toast.success('Project updated successfully')
      } else {
        await createProject({
          title: formTitle.trim(),
          description: formDescription.trim() || undefined
        })
        toast.success('Project created successfully')
      }

      await loadProjects()
      handleCancelForm()
    } catch (err) {
      logger.error('Error saving project:', err)
      toast.error('Failed to save project')
    }
  }

  async function handleDeleteProject(projectId: string, e: React.MouseEvent) {
    e.stopPropagation()

    setConfirmModal({
      open: true,
      title: 'Delete Project',
      message: 'Are you sure you want to delete this project? Conversations will be unlinked but not deleted.',
      onConfirm: async () => {
        try {
          await deleteProject(projectId)
          toast.success('Project deleted successfully')
          await loadProjects()
          if (selectedProjectId === projectId) {
            setSelectedProjectId(null)
            onProjectChange?.(null)
          }
        } catch (err) {
          logger.error('Error deleting project:', err)
          toast.error('Failed to delete project')
        }
      }
    })
  }

  async function handleAddToProject(projectId: string) {
    if (!currentConversationId) {
      toast.error('No conversation selected')
      return
    }

    try {
      await addConversationToProject(projectId, currentConversationId)
      toast.success('Conversation added to project')
      await loadProjects()
    } catch (err) {
      logger.error('Error adding conversation to project:', err)
      toast.error('Failed to add conversation to project')
    }
  }

  // handleRemoveFromProject kept for future UI implementation
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async function _handleRemoveFromProject(projectId: string) {
    if (!currentConversationId) {
      toast.error('No conversation selected')
      return
    }

    try {
      await removeConversationFromProject(projectId, currentConversationId)
      toast.success('Conversation removed from project')
      await loadProjects()
    } catch (err) {
      logger.error('Error removing conversation from project:', err)
      toast.error('Failed to remove conversation from project')
    }
  }

  function handleSelectProject(project: Project) {
    if (selectedProjectId === project.id) {
      setSelectedProjectId(null)
    } else {
      setSelectedProjectId(project.id)
    }
  }

  function formatDate(isoString: string) {
    if (!isoString) return 'Unknown'
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return 'Unknown'
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div className={`border-t border-default ${className}`}>
      {/* Header */}
      <div
        className="flex items-center justify-between w-full px-4 py-2 hover:bg-hover transition-colors cursor-pointer"
      >
        <div
          className="flex items-center gap-2 flex-1"
          onClick={() => setExpanded(!expanded)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && setExpanded(!expanded)}
        >
          <svg
            className={`w-4 h-4 text-muted transition-transform ${expanded ? 'rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-xs font-medium text-muted uppercase tracking-wide">
            Projects
          </span>
          {projects.length > 0 && (
            <span className="text-xs text-muted">({projects.length})</span>
          )}
        </div>
        <button
          onClick={() => {
            handleStartCreate()
            setExpanded(true)
          }}
          className="text-xs text-primary hover:opacity-70"
          title="Create Project"
        >
          + New
        </button>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-3 pb-3">
          {/* Create/Edit Form */}
          {(showCreateForm || editingProject) && (
            <div className="mb-3 p-3 bg-hover rounded-lg space-y-2">
              <input
                type="text"
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                placeholder="Project title..."
                className="input-field w-full px-2 py-1.5 text-sm"
                autoFocus
              />
              <textarea
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                placeholder="Description (optional)..."
                rows={2}
                className="input-field w-full px-2 py-1.5 text-sm resize-none"
              />
              <div className="flex gap-2 pt-1">
                <button
                  onClick={handleSaveProject}
                  className="btn-primary flex-1 text-xs py-1.5"
                >
                  {editingProject ? 'Update' : 'Create'}
                </button>
                <button
                  onClick={handleCancelForm}
                  className="btn-secondary flex-1 text-xs py-1.5"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading ? (
            <div className="py-4 text-center">
              <LoadingSpinner size="sm" />
            </div>
          ) : projects.length === 0 ? (
            <div className="text-xs text-muted text-center py-3">
              No projects yet. Create one to organize your conversations.
            </div>
          ) : (
            <div className="space-y-1">
              {projects.map((project) => {
                const colors = PHASE_COLORS[project.current_phase] || PHASE_COLORS['Analysis']
                // statusColors kept for future status badge display
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                const _statusColors = STATUS_COLORS[project.status] || STATUS_COLORS['active']
                const isSelected = selectedProjectId === project.id

                return (
                  <div
                    key={project.id}
                    className={`group rounded-lg transition-all cursor-pointer ${
                      isSelected ? 'bg-accent border border-brand-primary' : 'hover:bg-hover'
                    }`}
                    onClick={() => handleSelectProject(project)}
                  >
                    <div className="px-3 py-2">
                      {/* Project Title and Phase */}
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <div className="font-medium text-sm text-primary truncate flex-1">
                          {project.title}
                        </div>
                        <span className={`text-xs px-1.5 py-0.5 rounded flex-shrink-0 ${colors.bg} ${colors.text}`}>
                          {project.current_phase.charAt(0)}
                        </span>
                      </div>

                      {/* Description */}
                      {project.description && (
                        <div className="text-xs text-muted truncate mb-1">
                          {project.description}
                        </div>
                      )}

                      {/* Meta info and actions */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-xs text-muted">
                          <span>{project.conversation_count || 0} chats</span>
                          <span>·</span>
                          <span>{formatDate(project.updated_at)}</span>
                        </div>

                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          {/* Add current conversation to project */}
                          {currentConversationId && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleAddToProject(project.id)
                              }}
                              className="p-1 hover:bg-gray-200 rounded transition-colors"
                              title="Add current conversation to this project"
                            >
                              <svg className="w-3.5 h-3.5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                              </svg>
                            </button>
                          )}
                          {/* Edit */}
                          <button
                            onClick={(e) => handleStartEdit(project, e)}
                            className="p-1 hover:bg-gray-200 rounded transition-colors"
                            title="Edit project"
                          >
                            <svg className="w-3.5 h-3.5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                            </svg>
                          </button>
                          {/* Delete */}
                          <button
                            onClick={(e) => handleDeleteProject(project.id, e)}
                            className="p-1 hover:bg-gray-200 rounded transition-colors"
                            title="Delete project"
                          >
                            <svg className="w-3.5 h-3.5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>

                      {/* Expanded project details when selected */}
                      {isSelected && project.conversations && project.conversations.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-gray-200">
                          <div className="text-xs text-muted mb-1">Conversations:</div>
                          <div className="space-y-1 max-h-32 overflow-y-auto">
                            {project.conversations.map((conv) => (
                              <div
                                key={conv.id}
                                className={`text-xs px-2 py-1 rounded flex items-center justify-between ${
                                  conv.id === currentConversationId
                                    ? 'bg-brand-primary text-white'
                                    : 'bg-gray-100 text-gray-700'
                                }`}
                              >
                                <span className="truncate flex-1">{conv.title}</span>
                                {conv.addie_phase && (
                                  <span className={`ml-1 px-1 rounded text-[10px] ${
                                    conv.id === currentConversationId
                                      ? 'bg-white/20 text-white'
                                      : PHASE_COLORS[conv.addie_phase]?.bg + ' ' + PHASE_COLORS[conv.addie_phase]?.text
                                  }`}>
                                    {conv.addie_phase.charAt(0)}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

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
