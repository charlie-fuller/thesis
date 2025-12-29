'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  getProjects,
  createProject,
  updateProject,
  deleteProject,
  type Project
} from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import LoadingSpinner from '@/components/LoadingSpinner'
import ConfirmModal from '@/components/ConfirmModal'
import PageHeader from '@/components/PageHeader'
import toast from 'react-hot-toast'
import { logger } from '@/lib/logger'

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  'active': { bg: 'bg-green-100', text: 'text-green-700' },
  'archived': { bg: 'bg-gray-100', text: 'text-gray-500' },
  'complete': { bg: 'bg-blue-100', text: 'text-blue-700' },
}

export default function ProjectsPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('active')

  // Form state
  const [formTitle, setFormTitle] = useState('')
  const [formDescription, setFormDescription] = useState('')

  // Delete modal state
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

  // Track which projects are expanded to show conversations
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set())

  function toggleProjectExpanded(projectId: string) {
    setExpandedProjects(prev => {
      const next = new Set(prev)
      if (next.has(projectId)) {
        next.delete(projectId)
      } else {
        next.add(projectId)
      }
      return next
    })
  }

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [authLoading, user, router])

  useEffect(() => {
    if (user) {
      loadProjects()
    }
  }, [statusFilter, user])

  async function loadProjects() {
    try {
      setLoading(true)
      const response = await getProjects(statusFilter !== 'all' ? statusFilter : undefined)
      if (response.success) {
        setProjects(response.projects)
      }
    } catch (err) {
      logger.error('Error loading projects:', err)
      toast.error('Failed to load projects')
    } finally {
      setLoading(false)
    }
  }

  function openCreateModal() {
    setEditingProject(null)
    setFormTitle('')
    setFormDescription('')
    setShowCreateModal(true)
  }

  function openEditModal(project: Project) {
    setEditingProject(project)
    setFormTitle(project.title)
    setFormDescription(project.description || '')
    setShowCreateModal(true)
  }

  function closeModal() {
    setShowCreateModal(false)
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
        toast.success('Project updated')
      } else {
        await createProject({
          title: formTitle.trim(),
          description: formDescription.trim() || undefined
        })
        toast.success('Project created')
      }

      await loadProjects()
      closeModal()
    } catch (err) {
      logger.error('Error saving project:', err)
      toast.error('Failed to save project')
    }
  }

  function handleDeleteProject(project: Project) {
    setConfirmModal({
      open: true,
      title: 'Delete Project',
      message: `Are you sure you want to delete "${project.title}"? Conversations will be unlinked but not deleted.`,
      onConfirm: async () => {
        try {
          await deleteProject(project.id)
          toast.success('Project deleted')
          await loadProjects()
        } catch (err) {
          logger.error('Error deleting project:', err)
          toast.error('Failed to delete project')
        }
        setConfirmModal({ ...confirmModal, open: false })
      }
    })
  }

  async function handleArchiveProject(project: Project) {
    try {
      await updateProject(project.id, { status: 'archived' })
      toast.success('Project archived')
      await loadProjects()
    } catch (err) {
      logger.error('Error archiving project:', err)
      toast.error('Failed to archive project')
    }
  }

  async function handleRestoreProject(project: Project) {
    try {
      await updateProject(project.id, { status: 'active' })
      toast.success('Project restored')
      await loadProjects()
    } catch (err) {
      logger.error('Error restoring project:', err)
      toast.error('Failed to restore project')
    }
  }

  function formatDate(isoString: string) {
    if (!isoString) return 'Unknown'
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return 'Unknown'
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  // Show loading state while auth is being checked
  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-page">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-secondary mt-4">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render if not authenticated
  if (!user) {
    return null
  }

  const filteredProjects = statusFilter === 'all'
    ? projects
    : projects.filter(p => p.status === statusFilter)

  return (
    <div className="flex flex-col min-h-screen bg-page">
      {/* Consistent Header */}
      <PageHeader />

      {/* Main Content */}
      <main className="flex-1 max-w-6xl mx-auto w-full p-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-primary">Initiatives</h1>
            <p className="text-secondary mt-1">
              Organize your AI strategy work into initiatives
            </p>
          </div>
          <button
            onClick={openCreateModal}
            className="btn-primary flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Initiative
          </button>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex border-b border-border mb-6">
          {['active', 'archived', 'all'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors capitalize ${
                statusFilter === status
                  ? 'border-primary text-primary'
                  : 'border-transparent text-secondary hover:text-primary'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4 text-secondary opacity-30">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-primary mb-2">
              {statusFilter === 'active' ? 'No active initiatives' :
               statusFilter === 'archived' ? 'No archived initiatives' : 'No initiatives yet'}
            </h3>
            <p className="text-secondary mb-4">
              {statusFilter === 'active'
                ? 'Create an initiative to organize your AI strategy work'
                : 'Archived initiatives will appear here'}
            </p>
            {statusFilter === 'active' && (
              <button onClick={openCreateModal} className="btn-primary">
                Create Your First Initiative
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProjects.map((project) => {
              const statusColors = STATUS_COLORS[project.status] || STATUS_COLORS['active']
              const isArchived = project.status === 'archived'

              return (
                <div
                  key={project.id}
                  className={`card p-4 hover:shadow-md transition-shadow ${isArchived ? 'opacity-60' : ''}`}
                >
                  {/* Project Header */}
                  <div className="mb-3">
                    <h3 className="font-semibold text-primary truncate">
                      {project.title}
                    </h3>
                    {project.description && (
                      <p className="text-sm text-secondary mt-1 line-clamp-2">
                        {project.description}
                      </p>
                    )}
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-sm text-secondary mb-4">
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <span>{project.conversation_count || 0} chats</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{formatDate(project.updated_at)}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-3 border-t border-border">
                    <button
                      onClick={() => openEditModal(project)}
                      className="p-2 hover:bg-hover rounded transition-colors cursor-pointer"
                      title="Edit"
                    >
                      <svg className="w-4 h-4 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    {isArchived ? (
                      <button
                        onClick={() => handleRestoreProject(project)}
                        className="p-2 hover:bg-hover rounded transition-colors cursor-pointer"
                        title="Reactivate"
                      >
                        <svg className="w-4 h-4 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleArchiveProject(project)}
                        className="p-2 hover:bg-hover rounded transition-colors cursor-pointer"
                        title="Archive"
                      >
                        <svg className="w-4 h-4 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                        </svg>
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteProject(project)}
                      className="p-2 hover:bg-hover rounded transition-colors cursor-pointer"
                      title="Delete"
                    >
                      <svg className="w-4 h-4 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                    <div className="flex-1" />
                    <Link
                      href={`/chat?project=${project.id}`}
                      className="p-2 hover:bg-hover rounded transition-colors cursor-pointer"
                      title="Start new chat in project"
                    >
                      <svg className="w-4 h-4 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                    </Link>
                  </div>

                  {/* Expandable Conversations List */}
                  {project.conversations && project.conversations.length > 0 && (
                    <div className="mt-3 border-t border-border">
                      <button
                        onClick={() => toggleProjectExpanded(project.id)}
                        className="w-full flex items-center justify-between py-2 text-sm text-secondary hover:text-primary transition-colors"
                      >
                        <span>{project.conversations.length} conversation{project.conversations.length !== 1 ? 's' : ''}</span>
                        <svg
                          className={`w-4 h-4 transition-transform ${expandedProjects.has(project.id) ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                      {expandedProjects.has(project.id) && (
                        <div className="pb-2 space-y-1">
                          {project.conversations.map((conv) => (
                            <Link
                              key={conv.id}
                              href={`/chat?id=${conv.id}`}
                              className="block px-2 py-1.5 text-sm text-secondary hover:text-primary hover:bg-hover rounded transition-colors truncate"
                            >
                              {conv.title || 'Untitled conversation'}
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* Create/Edit Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
              <h2 className="text-xl font-semibold text-primary mb-4">
                {editingProject ? 'Edit Initiative' : 'Create Initiative'}
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="label">Initiative Name</label>
                  <input
                    type="text"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    placeholder="e.g., Finance GenAI Pilot"
                    className="input-field w-full"
                    autoFocus
                  />
                </div>

                <div>
                  <label className="label">Description (optional)</label>
                  <textarea
                    value={formDescription}
                    onChange={(e) => setFormDescription(e.target.value)}
                    placeholder="Brief description of this initiative..."
                    rows={3}
                    className="input-field w-full resize-none"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleSaveProject}
                  className="btn-primary flex-1"
                >
                  {editingProject ? 'Save Changes' : 'Create Initiative'}
                </button>
                <button
                  onClick={closeModal}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        <ConfirmModal
          open={confirmModal.open}
          title={confirmModal.title}
          message={confirmModal.message}
          onConfirm={confirmModal.onConfirm}
          onCancel={() => setConfirmModal({ ...confirmModal, open: false })}
        />
      </main>
    </div>
  )
}
