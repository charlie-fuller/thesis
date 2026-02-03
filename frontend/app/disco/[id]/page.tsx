'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  ArrowLeft,
  FileText,
  Play,
  MessageSquare,
  Users,
  Download,
  Upload,
  Trash2,
  ChevronDown,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  Settings,
  Eye,
  Edit3,
  Target,
  ExternalLink
} from 'lucide-react'
import { apiGet, apiPost, apiDelete } from '@/lib/api'
import DocumentUpload from '@/components/disco/DocumentUpload'
import DocumentList from '@/components/disco/DocumentList'
import AgentRunner from '@/components/disco/AgentRunner'
import OutputViewer from '@/components/disco/OutputViewer'
import InitiativeChat from '@/components/disco/InitiativeChat'
import ShareModal from '@/components/disco/ShareModal'

// ============================================================================
// TYPES
// ============================================================================

interface Initiative {
  id: string
  name: string
  description: string | null
  status: string
  created_at: string
  updated_at: string
  user_role: string
  document_count: number
  users?: {
    id: string
    name: string
    email: string
  }
  latest_outputs?: Record<string, {
    agent_type: string
    version: number
    created_at: string
    recommendation?: string
    confidence_level?: string
  }>
}

interface Document {
  id: string
  filename: string
  title?: string | null
  uploaded_at: string
  source_platform?: string
  linked_at?: string
  linked_by?: string
  // Legacy fields for backward compatibility
  content?: string
  document_type?: string
  version?: number
  metadata?: Record<string, unknown>
}

interface Output {
  id: string
  run_id: string
  agent_type: string
  version: number
  title: string | null
  recommendation: string | null
  tier_routing: string | null
  confidence_level: string | null
  executive_summary: string | null
  content_markdown: string
  content_structured: Record<string, unknown>
  created_at: string
}

interface LinkedProject {
  id: string
  project_code: string
  title: string
  description: string | null
  status: string
  tier: number
}

// ============================================================================
// CONSTANTS
// ============================================================================

const STATUS_CONFIG: Record<string, { label: string; color: string; bgColor: string }> = {
  draft: { label: 'Draft', color: 'text-slate-600', bgColor: 'bg-slate-100 dark:bg-slate-800' },
  triaged: { label: 'Triaged', color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900/30' },
  in_discovery: { label: 'In Discovery', color: 'text-amber-600', bgColor: 'bg-amber-100 dark:bg-amber-900/30' },
  consolidated: { label: 'Consolidated', color: 'text-teal-600', bgColor: 'bg-teal-100 dark:bg-teal-900/30' },
  synthesized: { label: 'Synthesized', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900/30' },
  documented: { label: 'PRD Generated', color: 'text-indigo-600', bgColor: 'bg-indigo-100 dark:bg-indigo-900/30' },
  evaluated: { label: 'Evaluated', color: 'text-purple-600', bgColor: 'bg-purple-100 dark:bg-purple-900/30' },
  archived: { label: 'Archived', color: 'text-slate-500', bgColor: 'bg-slate-100 dark:bg-slate-800' },
}

type TabType = 'documents' | 'agents' | 'outputs' | 'projects' | 'chat'

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function InitiativeDetailPage() {
  const params = useParams()
  const router = useRouter()
  const initiativeId = params.id as string

  const [initiative, setInitiative] = useState<Initiative | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [outputs, setOutputs] = useState<Output[]>([])
  const [linkedProjects, setLinkedProjects] = useState<LinkedProject[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [activeTab, setActiveTab] = useState<TabType>('documents')
  const [selectedOutput, setSelectedOutput] = useState<Output | null>(null)
  const [shareModalOpen, setShareModalOpen] = useState(false)

  // Edit mode for initiative details
  const [editingDescription, setEditingDescription] = useState(false)
  const [editedDescription, setEditedDescription] = useState('')
  const [savingDescription, setSavingDescription] = useState(false)

  const canEdit = initiative?.user_role === 'owner' || initiative?.user_role === 'editor'

  // Load initiative data
  const loadInitiative = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const result = await apiGet<{ success: boolean; initiative: Initiative }>(
        `/api/disco/initiatives/${initiativeId}`
      )

      if (result.success && result.initiative) {
        setInitiative(result.initiative)
      } else {
        setError('Initiative not found')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load initiative')
    } finally {
      setLoading(false)
    }
  }, [initiativeId])

  // Load linked KB documents
  const loadDocuments = useCallback(async () => {
    try {
      const result = await apiGet<{ success: boolean; documents: Document[] }>(
        `/api/disco/initiatives/${initiativeId}/linked-documents`
      )
      setDocuments(result.documents || [])
    } catch (err) {
      console.error('Failed to load linked documents:', err)
    }
  }, [initiativeId])

  // Load outputs
  const loadOutputs = useCallback(async () => {
    try {
      const result = await apiGet<{ success: boolean; outputs: Output[] }>(
        `/api/disco/initiatives/${initiativeId}/outputs`
      )
      setOutputs(result.outputs || [])
    } catch (err) {
      console.error('Failed to load outputs:', err)
    }
  }, [initiativeId])

  // Load linked projects
  const loadLinkedProjects = useCallback(async () => {
    try {
      // API returns array directly, not wrapped in { projects: [...] }
      const result = await apiGet<LinkedProject[]>(
        `/api/projects?initiative_id=${initiativeId}`
      )
      setLinkedProjects(result || [])
    } catch (err) {
      console.error('Failed to load linked projects:', err)
    }
  }, [initiativeId])

  useEffect(() => {
    loadInitiative()
    loadDocuments()
    loadOutputs()
    loadLinkedProjects()
  }, [loadInitiative, loadDocuments, loadOutputs, loadLinkedProjects])

  const handleDocumentDeleted = (docId: string) => {
    setDocuments(documents.filter(d => d.id !== docId))
    if (initiative) {
      setInitiative({
        ...initiative,
        document_count: Math.max(0, initiative.document_count - 1)
      })
    }
  }

  const handleEditDescription = () => {
    setEditedDescription(initiative?.description || '')
    setEditingDescription(true)
  }

  const handleSaveDescription = async () => {
    if (!initiative) return

    setSavingDescription(true)
    try {
      const result = await apiPost<{ success: boolean; initiative: Initiative }>(
        `/api/disco/initiatives/${initiativeId}`,
        { description: editedDescription }
      )
      if (result.success && result.initiative) {
        setInitiative(result.initiative)
      }
      setEditingDescription(false)
    } catch (err) {
      console.error('Failed to save description:', err)
    } finally {
      setSavingDescription(false)
    }
  }

  const handleCancelEdit = () => {
    setEditingDescription(false)
    setEditedDescription('')
  }

  const handleAgentComplete = async () => {
    // Reload full outputs list to get complete data
    try {
      const result = await apiGet<{ success: boolean; outputs: Output[] }>(
        `/api/disco/initiatives/${initiativeId}/outputs`
      )
      const newOutputs = result.outputs || []
      setOutputs(newOutputs)
      // Select the newest output (first in list since sorted by created_at desc)
      if (newOutputs.length > 0) {
        setSelectedOutput(newOutputs[0])
      }
    } catch (err) {
      console.error('Failed to reload outputs:', err)
    }
    setActiveTab('outputs')
    loadInitiative() // Refresh status
  }

  const handleDeleteOutput = async (outputId: string) => {
    await apiDelete(`/api/disco/initiatives/${initiativeId}/outputs/${outputId}`)
    // Remove from local state
    setOutputs(outputs.filter(o => o.id !== outputId))
    // Clear selection if deleted
    if (selectedOutput?.id === outputId) {
      const remaining = outputs.filter(o => o.id !== outputId)
      setSelectedOutput(remaining.length > 0 ? remaining[0] : null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-2 text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          Loading initiative...
        </div>
      </div>
    )
  }

  if (error || !initiative) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
            {error || 'Initiative not found'}
          </h2>
          <button
            onClick={() => router.push('/disco')}
            className="mt-4 inline-flex items-center gap-2 px-4 py-2 text-sm text-indigo-600 hover:underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to initiatives
          </button>
        </div>
      </div>
    )
  }

  const statusConfig = STATUS_CONFIG[initiative.status] || STATUS_CONFIG.draft

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push('/disco')}
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to initiatives
        </button>

        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                {initiative.name}
              </h1>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
            {editingDescription ? (
              <div className="flex items-start gap-2 max-w-2xl">
                <textarea
                  value={editedDescription}
                  onChange={(e) => setEditedDescription(e.target.value)}
                  placeholder="Add a description for this initiative..."
                  rows={3}
                  className="flex-1 px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  autoFocus
                />
                <div className="flex flex-col gap-1">
                  <button
                    onClick={handleSaveDescription}
                    disabled={savingDescription}
                    className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {savingDescription ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    disabled={savingDescription}
                    className="px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-2 group">
                {initiative.description ? (
                  <p className="text-slate-500 dark:text-slate-400 max-w-2xl">
                    {initiative.description}
                  </p>
                ) : canEdit ? (
                  <p className="text-slate-400 dark:text-slate-500 italic">
                    No description
                  </p>
                ) : null}
                {canEdit && (
                  <button
                    onClick={handleEditDescription}
                    className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Edit description"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
            {/* Show linked projects or user role if applicable */}
            {(linkedProjects.length > 0 || initiative.user_role !== 'owner') && (
              <div className="flex items-center gap-4 mt-2 text-sm text-slate-500 dark:text-slate-400">
                {linkedProjects.length > 0 && (
                  <a
                    href={`/projects?initiative=${initiativeId}`}
                    className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    <Target className="w-4 h-4" />
                    {linkedProjects.length} project{linkedProjects.length !== 1 ? 's' : ''}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
                {initiative.user_role !== 'owner' && (
                  <span className="flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    {initiative.user_role}
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShareModalOpen(true)}
              className="flex items-center gap-2 px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              <Users className="w-4 h-4" />
              Share
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-700 mb-6 overflow-x-auto">
        {[
          { id: 'documents' as const, label: 'Documents', icon: FileText },
          { id: 'agents' as const, label: 'Run Agents', icon: Play },
          { id: 'outputs' as const, label: 'Outputs', icon: CheckCircle },
          { id: 'projects' as const, label: 'Projects', icon: Target },
          { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
            {tab.id === 'documents' && (
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded">
                {documents.length}
              </span>
            )}
            {tab.id === 'outputs' && (
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded">
                {outputs.length}
              </span>
            )}
            {tab.id === 'projects' && (
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded">
                {linkedProjects.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="space-y-6">
            {canEdit && (
              <DocumentUpload
                initiativeId={initiativeId}
                initiativeName={initiative?.name}
                onDocumentsLinked={loadDocuments}
              />
            )}
            <DocumentList
              documents={documents}
              canDelete={canEdit}
              initiativeId={initiativeId}
              onDeleted={handleDocumentDeleted}
            />
          </div>
        )}

        {/* Agents Tab */}
        {activeTab === 'agents' && (
          <AgentRunner
            initiativeId={initiativeId}
            canRun={canEdit}
            documents={documents}
            outputs={outputs}
            onComplete={handleAgentComplete}
          />
        )}

        {/* Outputs Tab */}
        {activeTab === 'outputs' && (
          <OutputViewer
            initiativeId={initiativeId}
            outputs={outputs}
            selectedOutput={selectedOutput}
            onSelectOutput={setSelectedOutput}
            onRefresh={loadOutputs}
            onDelete={canEdit ? handleDeleteOutput : undefined}
          />
        )}

        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <div className="space-y-4">
            {linkedProjects.length === 0 ? (
              <div className="text-center py-12 border border-dashed border-slate-300 dark:border-slate-600 rounded-lg">
                <Target className="w-12 h-12 mx-auto text-slate-400 mb-3" />
                <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
                  No Linked Projects
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                  Projects can be linked to this initiative from the Projects page.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {linkedProjects.map((project) => (
                  <a
                    key={project.id}
                    href={`/projects?highlight=${project.id}`}
                    className="block p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-indigo-300 dark:hover:border-indigo-600 hover:shadow-md transition-all group"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                          {project.project_code}
                        </span>
                        <span className={`text-xs px-1.5 py-0.5 rounded capitalize ${
                          project.status === 'active'
                            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                            : project.status === 'completed'
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                        }`}>
                          {project.status}
                        </span>
                      </div>
                      <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-colors" />
                    </div>
                    <h4 className="font-medium text-slate-900 dark:text-white mb-1 line-clamp-2">
                      {project.title}
                    </h4>
                    {project.description && (
                      <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">
                        {project.description}
                      </p>
                    )}
                  </a>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <InitiativeChat initiativeId={initiativeId} initiativeName={initiative?.name} />
        )}
      </div>

      {/* Share Modal */}
      <ShareModal
        open={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        initiativeId={initiativeId}
        userRole={initiative.user_role}
      />
    </div>
  )
}
