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
  History
} from 'lucide-react'
import { apiGet, apiPost, apiDelete } from '@/lib/api'
import DocumentUpload from '@/components/purdy/DocumentUpload'
import DocumentList from '@/components/purdy/DocumentList'
import AgentRunner from '@/components/purdy/AgentRunner'
import OutputViewer from '@/components/purdy/OutputViewer'
import InitiativeChat from '@/components/purdy/InitiativeChat'
import ShareModal from '@/components/purdy/ShareModal'

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
  content: string
  document_type: string
  version: number
  uploaded_at: string
  metadata: Record<string, any>
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
  content_structured: Record<string, any>
  created_at: string
}

// ============================================================================
// CONSTANTS
// ============================================================================

const STATUS_CONFIG: Record<string, { label: string; color: string; bgColor: string }> = {
  draft: { label: 'Draft', color: 'text-slate-600', bgColor: 'bg-slate-100 dark:bg-slate-800' },
  triaged: { label: 'Triaged', color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900/30' },
  in_discovery: { label: 'In Discovery', color: 'text-amber-600', bgColor: 'bg-amber-100 dark:bg-amber-900/30' },
  synthesized: { label: 'Synthesized', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900/30' },
  evaluated: { label: 'Evaluated', color: 'text-purple-600', bgColor: 'bg-purple-100 dark:bg-purple-900/30' },
  archived: { label: 'Archived', color: 'text-slate-500', bgColor: 'bg-slate-100 dark:bg-slate-800' },
}

type TabType = 'documents' | 'agents' | 'outputs' | 'chat'

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
        `/api/purdy/initiatives/${initiativeId}`
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

  // Load documents
  const loadDocuments = useCallback(async () => {
    try {
      const result = await apiGet<{ success: boolean; documents: Document[] }>(
        `/api/purdy/initiatives/${initiativeId}/documents`
      )
      setDocuments(result.documents || [])
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }, [initiativeId])

  // Load outputs
  const loadOutputs = useCallback(async () => {
    try {
      const result = await apiGet<{ success: boolean; outputs: Output[] }>(
        `/api/purdy/initiatives/${initiativeId}/outputs`
      )
      setOutputs(result.outputs || [])
    } catch (err) {
      console.error('Failed to load outputs:', err)
    }
  }, [initiativeId])

  useEffect(() => {
    loadInitiative()
    loadDocuments()
    loadOutputs()
  }, [loadInitiative, loadDocuments, loadOutputs])

  const handleDocumentUploaded = (doc: Document) => {
    setDocuments([doc, ...documents])
    if (initiative) {
      setInitiative({
        ...initiative,
        document_count: initiative.document_count + 1
      })
    }
  }

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
        `/api/purdy/initiatives/${initiativeId}`,
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
        `/api/purdy/initiatives/${initiativeId}/outputs`
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
    await apiDelete(`/api/purdy/initiatives/${initiativeId}/outputs/${outputId}`)
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
            onClick={() => router.push('/purdy')}
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
          onClick={() => router.push('/purdy')}
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
            <div className="flex items-center gap-4 mt-2 text-sm text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1">
                <FileText className="w-4 h-4" />
                {initiative.document_count} documents
              </span>
              <span className="flex items-center gap-1">
                <History className="w-4 h-4" />
                {outputs.length} outputs
              </span>
              {initiative.user_role !== 'owner' && (
                <span className="flex items-center gap-1">
                  <Eye className="w-4 h-4" />
                  {initiative.user_role}
                </span>
              )}
            </div>
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
      <div className="flex border-b border-slate-200 dark:border-slate-700 mb-6">
        {[
          { id: 'documents' as const, label: 'Documents', icon: FileText },
          { id: 'agents' as const, label: 'Run Agent', icon: Play },
          { id: 'outputs' as const, label: 'Outputs', icon: CheckCircle },
          { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
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
                onUploaded={handleDocumentUploaded}
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

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <InitiativeChat initiativeId={initiativeId} />
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
