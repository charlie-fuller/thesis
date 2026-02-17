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
  ExternalLink,
  BarChart3,
  X,
  Plus,
  Sparkles,
  Crosshair
} from 'lucide-react'
import { apiGet, apiPost, apiPatch, apiDelete, authenticatedFetch } from '@/lib/api'
import DocumentUpload from '@/components/disco/DocumentUpload'
import DocumentList from '@/components/disco/DocumentList'
import AgentRunner from '@/components/disco/AgentRunner'
import OutputViewer from '@/components/disco/OutputViewer'
import ShareModal from '@/components/disco/ShareModal'
import InitiativeAlignmentTab from '@/components/disco/InitiativeAlignmentTab'
import ThroughlineEditor, { type Throughline } from '@/components/disco/ThroughlineEditor'
import { type GoalAlignmentDetails } from '@/components/projects/GoalAlignmentSection'
import LinkedFoldersSection from '@/components/disco/LinkedFoldersSection'
import ProjectCreateModal from '@/components/projects/ProjectCreateModal'

// ============================================================================
// TYPES
// ============================================================================

interface ValueAlignment {
  kpis?: string[]
  department_goals?: string[]
  company_priority?: string
  strategic_pillar?: 'enable' | 'operationalize' | 'govern'
  notes?: string
}

interface Initiative {
  id: string
  name: string
  description: string | null
  status: string
  created_at: string
  updated_at: string
  user_role: string
  document_count: number
  target_department?: string | null
  value_alignment?: ValueAlignment | null
  sponsor_stakeholder_id?: string | null
  stakeholder_ids?: string[]
  resolution_annotations?: Record<string, unknown> | null
  users?: {
    id: string
    name: string
    email: string
  }
  throughline?: Throughline | null
  user_corrections?: string | null
  goal_alignment_score: number | null
  goal_alignment_details: GoalAlignmentDetails | null
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

interface TriageSuggestions {
  problem_statements?: string[]
  hypotheses?: string[]
  gaps?: string[]
  kpis?: string[]
  stakeholders?: string[]
  value_alignment_notes?: string
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
  triage_suggestions?: TriageSuggestions | null
  created_at: string
}

interface LinkedProject {
  id: string
  project_code: string
  title: string
  description: string | null
  status: string
  tier: number
  source_type?: string
  source_id?: string
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

type TabType = 'framing' | 'documents' | 'agents' | 'outputs' | 'alignment' | 'projects'

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
  const [showActiveProjectsOnly, setShowActiveProjectsOnly] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [activeTab, setActiveTab] = useState<TabType>('documents')
  const [selectedOutput, setSelectedOutput] = useState<Output | null>(null)
  const [shareModalOpen, setShareModalOpen] = useState(false)

  // Linked folders state
  const [linkedFolders, setLinkedFolders] = useState<{ id: string; folder_path: string; recursive: boolean; linked_at: string }[]>([])

  // Project create modal state
  const [projectCreateOpen, setProjectCreateOpen] = useState(false)

  // Edit modal state
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editedName, setEditedName] = useState('')
  const [editedDescription, setEditedDescription] = useState('')
  const [editedDepartment, setEditedDepartment] = useState('')
  const [editedKpis, setEditedKpis] = useState<string[]>([])
  const [editedKpiInput, setEditedKpiInput] = useState('')
  const [editedStrategicPillar, setEditedStrategicPillar] = useState('')
  const [savingEdit, setSavingEdit] = useState(false)

  // Inline framing editor state
  const [inlineFraming, setInlineFraming] = useState<Throughline>({})
  const [corrections, setCorrections] = useState('')
  const [framingDirty, setFramingDirty] = useState(false)
  const [savingFraming, setSavingFraming] = useState(false)

  // Triage suggestions review panel
  const [triageReviewDismissed, setTriageReviewDismissed] = useState(false)
  const [acceptingSuggestions, setAcceptingSuggestions] = useState(false)

  // Check if suggestions have already been accepted into the throughline
  const areSuggestionsAlreadyAccepted = (suggestions: TriageSuggestions): boolean => {
    const throughline = initiative?.throughline
    if (!throughline) return false
    const existingPS = new Set((throughline.problem_statements || []).map(p => p.text))
    const existingH = new Set((throughline.hypotheses || []).map(h => h.statement))
    const existingG = new Set((throughline.gaps || []).map(g => g.description))
    const newPS = (suggestions.problem_statements || []).filter(ps => {
      const text = typeof ps === 'string' ? ps : (ps as { text?: string }).text
      return text && !existingPS.has(text)
    })
    const newH = (suggestions.hypotheses || []).filter(h => {
      const stmt = typeof h === 'string' ? h : (h as { statement?: string }).statement
      return stmt && !existingH.has(stmt)
    })
    const newG = (suggestions.gaps || []).filter(g => {
      const desc = typeof g === 'string' ? g : (g as { description?: string }).description
      return desc && !existingG.has(desc)
    })
    return newPS.length === 0 && newH.length === 0 && newG.length === 0
  }

  // Generate framing state
  const [generatingFraming, setGeneratingFraming] = useState(false)
  const [framingGenerationStatus, setFramingGenerationStatus] = useState('')
  const [framingGenerationError, setFramingGenerationError] = useState<string | null>(null)

  const canEdit = !!initiative

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
        setInlineFraming(result.initiative.throughline || {})
        setCorrections(result.initiative.user_corrections || '')
        setFramingDirty(false)
      } else {
        setError('Discovery not found')
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

  // Load linked folders
  const loadLinkedFolders = useCallback(async () => {
    try {
      const result = await apiGet<{ success: boolean; folders: typeof linkedFolders }>(
        `/api/disco/initiatives/${initiativeId}/linked-folders`
      )
      setLinkedFolders(result.folders || [])
    } catch (err) {
      console.error('Failed to load linked folders:', err)
    }
  }, [initiativeId])

  // Load linked projects
  const loadLinkedProjects = useCallback(async () => {
    try {
      // Use the dedicated initiative projects endpoint
      const result = await apiGet<{ success: boolean; projects: LinkedProject[]; count: number }>(
        `/api/disco/initiatives/${initiativeId}/projects`
      )
      if (result.success) {
        setLinkedProjects(result.projects || [])
      }
    } catch (err) {
      console.error('Failed to load linked projects:', err)
    }
  }, [initiativeId])

  useEffect(() => {
    loadInitiative()
    loadDocuments()
    loadOutputs()
    loadLinkedFolders()
    loadLinkedProjects()
  }, [loadInitiative, loadDocuments, loadOutputs, loadLinkedFolders, loadLinkedProjects])

  const handleDocumentDeleted = (docId: string) => {
    setDocuments(documents.filter(d => d.id !== docId))
    if (initiative) {
      setInitiative({
        ...initiative,
        document_count: Math.max(0, initiative.document_count - 1)
      })
    }
  }

  const handleOpenEditModal = () => {
    setEditedName(initiative?.name || '')
    setEditedDescription(initiative?.description || '')
    setEditedDepartment(initiative?.target_department || '')
    setEditedKpis(initiative?.value_alignment?.kpis || [])
    setEditedKpiInput('')
    setEditedStrategicPillar(initiative?.value_alignment?.strategic_pillar || '')
    setEditModalOpen(true)
  }

  const handleSaveEdit = async () => {
    if (!initiative) return

    setSavingEdit(true)
    try {
      const result = await apiPatch<{ success: boolean; initiative: Initiative }>(
        `/api/disco/initiatives/${initiativeId}`,
        {
          name: editedName,
          description: editedDescription,
          target_department: editedDepartment || null,
          value_alignment: editedKpis.length > 0 || editedStrategicPillar
            ? { kpis: editedKpis.length > 0 ? editedKpis : undefined, strategic_pillar: editedStrategicPillar || undefined }
            : null,
        }
      )
      if (result.success && result.initiative) {
        setInitiative(result.initiative)
      }
      setEditModalOpen(false)
    } catch (err) {
      console.error('Failed to save initiative:', err)
    } finally {
      setSavingEdit(false)
    }
  }

  const handleCloseEditModal = () => {
    setEditModalOpen(false)
    setEditedName('')
    setEditedDescription('')
  }

  const handleInlineFramingChange = (updated: Throughline) => {
    setInlineFraming(updated)
    setFramingDirty(true)
  }

  const handleSaveFraming = async () => {
    if (!initiative) return
    setSavingFraming(true)
    try {
      const result = await apiPatch<{ success: boolean; initiative: Initiative }>(
        `/api/disco/initiatives/${initiativeId}`,
        { throughline: inlineFraming, user_corrections: corrections || null }
      )
      if (result.success && result.initiative) {
        setInitiative(result.initiative)
        setInlineFraming(result.initiative.throughline || {})
        setCorrections(result.initiative.user_corrections || '')
      }
      setFramingDirty(false)
    } catch (err) {
      console.error('Failed to save framing:', err)
    } finally {
      setSavingFraming(false)
    }
  }

  const handleAcceptSuggestions = async (suggestions: TriageSuggestions) => {
    if (!initiative) return
    setAcceptingSuggestions(true)
    try {
      // Build throughline from suggestions, deduplicating against existing items
      const existingPS = new Set((initiative.throughline?.problem_statements || []).map(p => p.text))
      const existingH = new Set((initiative.throughline?.hypotheses || []).map(h => h.statement))
      const existingG = new Set((initiative.throughline?.gaps || []).map(g => g.description))

      const newPS = (suggestions.problem_statements || [])
        .map(ps => {
          if (typeof ps === 'object' && ps !== null) return ps as { id: string; text: string }
          return { id: `ps-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, text: ps as string }
        })
        .filter(ps => ps.text && !existingPS.has(ps.text))

      const newH = (suggestions.hypotheses || [])
        .map(h => {
          if (typeof h === 'object' && h !== null) return h as { id: string; statement: string }
          return { id: `h-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, statement: h as string }
        })
        .filter(h => h.statement && !existingH.has(h.statement))

      const newG = (suggestions.gaps || [])
        .map(g => {
          if (typeof g === 'object' && g !== null) return g as { id: string; description: string; type: 'data' }
          return { id: `g-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, description: g as string, type: 'data' as const }
        })
        .filter(g => g.description && !existingG.has(g.description))

      const throughline: Throughline = {
        ...(initiative.throughline || {}),
        problem_statements: [...(initiative.throughline?.problem_statements || []), ...newPS],
        hypotheses: [...(initiative.throughline?.hypotheses || []), ...newH],
        gaps: [...(initiative.throughline?.gaps || []), ...newG],
      }

      // Build value alignment from suggestions
      const valueAlignment: ValueAlignment = {
        ...(initiative.value_alignment || {}),
        kpis: [...new Set([...(initiative.value_alignment?.kpis || []), ...(suggestions.kpis || [])])],
        notes: suggestions.value_alignment_notes || initiative.value_alignment?.notes || undefined,
      }

      const result = await apiPatch<{ success: boolean; initiative: Initiative }>(
        `/api/disco/initiatives/${initiativeId}`,
        {
          throughline,
          value_alignment: valueAlignment.kpis?.length || valueAlignment.notes ? valueAlignment : null,
        }
      )
      if (result.success && result.initiative) {
        setInitiative(result.initiative)
        setInlineFraming(result.initiative.throughline || {})
        setFramingDirty(false)
      }
      setTriageReviewDismissed(true)
    } catch (err) {
      console.error('Failed to accept suggestions:', err)
    } finally {
      setAcceptingSuggestions(false)
    }
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
      // Show triage review panel if suggestions are available and throughline is sparse
      if (newOutputs.length > 0 && newOutputs[0].triage_suggestions) {
        setTriageReviewDismissed(false)
      }
    } catch (err) {
      console.error('Failed to reload outputs:', err)
    }
    setActiveTab('outputs')
    loadInitiative() // Refresh status
  }

  const handleGenerateFraming = async () => {
    setGeneratingFraming(true)
    setFramingGenerationStatus('Starting Discovery Guide...')
    setFramingGenerationError(null)

    try {
      const response = await authenticatedFetch(
        `/api/disco/initiatives/${initiativeId}/runs`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ agent_type: 'discovery_guide', output_format: 'markdown' }),
          timeout: 300000,
        }
      )

      if (!response.ok) {
        throw new Error('Failed to start Discovery Guide')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) throw new Error('No response body')

      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: status')) continue
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data.startsWith('{')) {
              try {
                const parsed = JSON.parse(data)
                if (parsed.status) setFramingGenerationStatus(parsed.status)
              } catch { /* ignore parse errors */ }
            }
          }
        }
      }

      // Reload outputs to get triage suggestions
      const result = await apiGet<{ success: boolean; outputs: Output[] }>(
        `/api/disco/initiatives/${initiativeId}/outputs`
      )
      const newOutputs = result.outputs || []
      setOutputs(newOutputs)
      if (newOutputs.length > 0 && newOutputs[0].triage_suggestions) {
        setTriageReviewDismissed(false)
      }
      loadInitiative()
      setFramingGenerationStatus('')
    } catch (err) {
      setFramingGenerationError(err instanceof Error ? err.message : 'Failed to generate framing')
      setFramingGenerationStatus('')
    } finally {
      setGeneratingFraming(false)
    }
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
          Loading discovery...
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
            {error || 'Discovery not found'}
          </h2>
          <button
            onClick={() => router.push('/disco')}
            className="mt-4 inline-flex items-center gap-2 px-4 py-2 text-sm text-indigo-600 hover:underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to discoveries
          </button>
        </div>
      </div>
    )
  }

  const statusConfig = STATUS_CONFIG[initiative.status] || STATUS_CONFIG.draft

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push('/disco')}
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to discoveries
        </button>

        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                {initiative.name}
              </h1>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
                {statusConfig.label}
              </span>
              {canEdit && (
                <button
                  onClick={handleOpenEditModal}
                  className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 opacity-0 hover:opacity-100 transition-opacity"
                  title="Edit discovery details"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
              )}
            </div>
            {/* Description + Tags row */}
            <div className="mt-0.5 space-y-1.5">
              {initiative.description ? (
                <p className="text-sm text-slate-500 dark:text-slate-400 whitespace-pre-line line-clamp-3 max-w-4xl">
                  {initiative.description}
                </p>
              ) : canEdit ? (
                <button
                  onClick={handleOpenEditModal}
                  className="text-sm text-slate-400 dark:text-slate-500 italic hover:text-slate-600 dark:hover:text-slate-300"
                >
                  Add description...
                </button>
              ) : null}
              {(initiative.target_department || initiative.value_alignment?.kpis?.length || initiative.value_alignment?.strategic_pillar) && (
                <div className="flex items-center gap-1.5 flex-wrap">
                  {initiative.target_department && (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                      {initiative.target_department}
                    </span>
                  )}
                  {initiative.value_alignment?.kpis?.map((kpi, i) => (
                    <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400 group">
                      {kpi}
                      {canEdit && (
                        <button
                          onClick={async (e) => {
                            e.stopPropagation()
                            const updatedKpis = initiative.value_alignment?.kpis?.filter((_, j) => j !== i) || []
                            try {
                              const result = await apiPatch<{ success: boolean; initiative: Initiative }>(
                                `/api/disco/initiatives/${initiativeId}`,
                                { value_alignment: { ...initiative.value_alignment, kpis: updatedKpis.length > 0 ? updatedKpis : undefined } }
                              )
                              if (result.success && result.initiative) setInitiative(result.initiative)
                            } catch (err) { console.error('Failed to remove KPI:', err) }
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-600 dark:hover:text-red-400 -mr-0.5"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </span>
                  ))}
                  {initiative.value_alignment?.strategic_pillar && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 capitalize group">
                      {initiative.value_alignment.strategic_pillar}
                      {canEdit && (
                        <button
                          onClick={async (e) => {
                            e.stopPropagation()
                            try {
                              const result = await apiPatch<{ success: boolean; initiative: Initiative }>(
                                `/api/disco/initiatives/${initiativeId}`,
                                { value_alignment: { ...initiative.value_alignment, strategic_pillar: undefined } }
                              )
                              if (result.success && result.initiative) setInitiative(result.initiative)
                            } catch (err) { console.error('Failed to remove pillar:', err) }
                          }}
                          className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-600 dark:hover:text-red-400 -mr-0.5"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </span>
                  )}
                </div>
              )}
            </div>


            {/* Show linked projects or user role if applicable */}
            {(linkedProjects.length > 0 || initiative.user_role !== 'owner') && (
              <div className="flex items-center gap-4 mt-2 text-sm text-slate-500 dark:text-slate-400">
                {linkedProjects.length > 0 && (
                  <a
                    href={linkedProjects.length === 1 ? `/projects?project=${linkedProjects[0].id}` : `/projects?initiative=${initiativeId}`}
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
              onClick={() => router.push(`/chat?initiative_id=${initiativeId}`)}
              className="flex items-center gap-2 px-3 py-2 text-sm text-indigo-600 dark:text-indigo-400 border border-indigo-300 dark:border-indigo-600 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors"
              title="Chat with this Discovery"
            >
              <MessageSquare className="w-4 h-4" />
              Chat
            </button>
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

      {/* Post-Discovery Guide Framing Review Panel - show above tabs when not on framing tab */}
      {activeTab !== 'framing' && (() => {
        // Only check the LATEST discovery_guide output for suggestions
        const latestDiscoveryGuide = outputs
          .filter(o => o.agent_type === 'discovery_guide')
          .sort((a, b) => (b.version || 0) - (a.version || 0))[0]
        const suggestions = latestDiscoveryGuide?.triage_suggestions
        const hasSuggestionContent = suggestions && (
          (suggestions.problem_statements?.length ?? 0) > 0 ||
          (suggestions.hypotheses?.length ?? 0) > 0 ||
          (suggestions.gaps?.length ?? 0) > 0 ||
          (suggestions.kpis?.length ?? 0) > 0
        )

        if (hasSuggestionContent && !triageReviewDismissed && !areSuggestionsAlreadyAccepted(suggestions)) {
          return (
            <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4 mb-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                  <h3 className="font-medium text-indigo-900 dark:text-indigo-200">
                    Review Suggested Framing
                  </h3>
                </div>
                <button
                  onClick={() => setTriageReviewDismissed(true)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <p className="text-sm text-indigo-700 dark:text-indigo-300 mb-3">
                The Discovery Guide extracted framing from your documents. Accept to enable hypothesis resolution and state change tracking.
              </p>
              <div className="space-y-2 text-sm">
                {suggestions.problem_statements && suggestions.problem_statements.length > 0 && (
                  <div>
                    <span className="font-medium text-slate-700 dark:text-slate-300">Problem Statements:</span>
                    <ul className="ml-4 mt-1 space-y-0.5">
                      {suggestions.problem_statements.map((ps, i) => (
                        <li key={i} className="text-slate-600 dark:text-slate-400">- {typeof ps === 'string' ? ps : (ps as { text?: string }).text || JSON.stringify(ps)}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {suggestions.hypotheses && suggestions.hypotheses.length > 0 && (
                  <div>
                    <span className="font-medium text-slate-700 dark:text-slate-300">Hypotheses:</span>
                    <ul className="ml-4 mt-1 space-y-0.5">
                      {suggestions.hypotheses.map((h, i) => (
                        <li key={i} className="text-slate-600 dark:text-slate-400">- {typeof h === 'string' ? h : (h as { statement?: string }).statement || JSON.stringify(h)}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {suggestions.gaps && suggestions.gaps.length > 0 && (
                  <div>
                    <span className="font-medium text-slate-700 dark:text-slate-300">Gaps:</span>
                    <ul className="ml-4 mt-1 space-y-0.5">
                      {suggestions.gaps.map((g, i) => (
                        <li key={i} className="text-slate-600 dark:text-slate-400">- {typeof g === 'string' ? g : (g as { description?: string }).description || JSON.stringify(g)}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {suggestions.kpis && suggestions.kpis.length > 0 && (
                  <div>
                    <span className="font-medium text-slate-700 dark:text-slate-300">KPIs:</span>
                    <span className="ml-2 text-slate-600 dark:text-slate-400">{suggestions.kpis.join(', ')}</span>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2 mt-4">
                <button
                  onClick={() => handleAcceptSuggestions(suggestions)}
                  disabled={acceptingSuggestions}
                  className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {acceptingSuggestions ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <CheckCircle className="w-3.5 h-3.5" />
                  )}
                  Accept All
                </button>
                <button
                  onClick={() => setTriageReviewDismissed(true)}
                  className="px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )
        }
        return null
      })()}

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-700 mb-6 overflow-x-auto">
        {[
          { id: 'documents' as const, label: 'Documents', icon: FileText },
          { id: 'framing' as const, label: 'Framing', icon: Crosshair },
          { id: 'alignment' as const, label: 'Alignment', icon: BarChart3 },
          { id: 'projects' as const, label: 'Projects', icon: Target },
          { id: 'agents' as const, label: 'Run Agents', icon: Play },
          { id: 'outputs' as const, label: 'Outputs', icon: CheckCircle },
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
                {showActiveProjectsOnly
                  ? linkedProjects.filter(p => p.status !== 'archived').length
                  : linkedProjects.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {/* Framing Tab */}
        {activeTab === 'framing' && (
          <div className="space-y-6">
            {/* Action buttons */}
            {canEdit && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleGenerateFraming}
                  disabled={generatingFraming}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {generatingFraming ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5" />
                  )}
                  {generatingFraming
                    ? framingGenerationStatus || 'Generating...'
                    : (initiative.throughline?.problem_statements?.length || initiative.throughline?.hypotheses?.length || initiative.throughline?.gaps?.length)
                      ? 'Regenerate from Documents'
                      : 'Generate from Documents'}
                </button>
                {framingDirty && (
                  <button
                    onClick={handleSaveFraming}
                    disabled={savingFraming}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                  >
                    {savingFraming ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <CheckCircle className="w-3.5 h-3.5" />
                    )}
                    {savingFraming ? 'Saving...' : 'Save Framing'}
                  </button>
                )}
              </div>
            )}
            {framingGenerationError && (
              <p className="text-sm text-red-500">{framingGenerationError}</p>
            )}

            {/* Review panel for suggestions - only check latest output */}
            {(() => {
              const latestDG = outputs
                .filter(o => o.agent_type === 'discovery_guide')
                .sort((a, b) => (b.version || 0) - (a.version || 0))[0]
              const suggestions = latestDG?.triage_suggestions
              const hasSuggestionContent = suggestions && (
                (suggestions.problem_statements?.length ?? 0) > 0 ||
                (suggestions.hypotheses?.length ?? 0) > 0 ||
                (suggestions.gaps?.length ?? 0) > 0 ||
                (suggestions.kpis?.length ?? 0) > 0
              )

              if (hasSuggestionContent && !triageReviewDismissed && !areSuggestionsAlreadyAccepted(suggestions)) {
                return (
                  <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Target className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                        <h3 className="font-medium text-indigo-900 dark:text-indigo-200">
                          Review Suggested Framing
                        </h3>
                      </div>
                      <button
                        onClick={() => setTriageReviewDismissed(true)}
                        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    <p className="text-sm text-indigo-700 dark:text-indigo-300 mb-3">
                      The Discovery Guide extracted framing from your documents. Accept to populate the throughline.
                    </p>
                    <div className="space-y-2 text-sm">
                      {suggestions.problem_statements && suggestions.problem_statements.length > 0 && (
                        <div>
                          <span className="font-medium text-slate-700 dark:text-slate-300">Problem Statements:</span>
                          <ul className="ml-4 mt-1 space-y-0.5">
                            {suggestions.problem_statements.map((ps, i) => (
                              <li key={i} className="text-slate-600 dark:text-slate-400">- {typeof ps === 'string' ? ps : (ps as { text?: string }).text || JSON.stringify(ps)}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {suggestions.hypotheses && suggestions.hypotheses.length > 0 && (
                        <div>
                          <span className="font-medium text-slate-700 dark:text-slate-300">Hypotheses:</span>
                          <ul className="ml-4 mt-1 space-y-0.5">
                            {suggestions.hypotheses.map((h, i) => (
                              <li key={i} className="text-slate-600 dark:text-slate-400">- {typeof h === 'string' ? h : (h as { statement?: string }).statement || JSON.stringify(h)}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {suggestions.gaps && suggestions.gaps.length > 0 && (
                        <div>
                          <span className="font-medium text-slate-700 dark:text-slate-300">Gaps:</span>
                          <ul className="ml-4 mt-1 space-y-0.5">
                            {suggestions.gaps.map((g, i) => (
                              <li key={i} className="text-slate-600 dark:text-slate-400">- {typeof g === 'string' ? g : (g as { description?: string }).description || JSON.stringify(g)}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {suggestions.kpis && suggestions.kpis.length > 0 && (
                        <div>
                          <span className="font-medium text-slate-700 dark:text-slate-300">KPIs:</span>
                          <span className="ml-2 text-slate-600 dark:text-slate-400">{suggestions.kpis.join(', ')}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-4">
                      <button
                        onClick={() => handleAcceptSuggestions(suggestions)}
                        disabled={acceptingSuggestions}
                        className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                      >
                        {acceptingSuggestions ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <CheckCircle className="w-3.5 h-3.5" />
                        )}
                        Accept All
                      </button>
                      <button
                        onClick={() => setTriageReviewDismissed(true)}
                        className="px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                )
              }
              return null
            })()}

            {/* Inline framing editor */}
            <ThroughlineEditor
              throughline={inlineFraming}
              onChange={handleInlineFramingChange}
              corrections={corrections}
              onCorrectionsChange={(val) => { setCorrections(val); setFramingDirty(true) }}
            />
          </div>
        )}

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="space-y-6">
            {linkedFolders.length > 0 && (
              <LinkedFoldersSection
                initiativeId={initiativeId}
                folders={linkedFolders}
                canEdit={canEdit}
                onUnlinked={loadLinkedFolders}
              />
            )}
            {canEdit && (
              <DocumentUpload
                initiativeId={initiativeId}
                initiativeName={initiative?.name}
                onDocumentsLinked={() => { loadDocuments(); loadLinkedFolders() }}
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

        {/* Alignment Tab */}
        {activeTab === 'alignment' && (
          <InitiativeAlignmentTab
            initiativeId={initiativeId}
            goalAlignmentScore={initiative.goal_alignment_score}
            goalAlignmentDetails={initiative.goal_alignment_details}
            latestOutputCreatedAt={
              outputs.length > 0
                ? outputs.reduce((latest, o) =>
                    new Date(o.created_at) > new Date(latest) ? o.created_at : latest,
                    outputs[0].created_at
                  )
                : null
            }
            canEdit={canEdit}
            onAlignmentUpdated={(score, details) => {
              if (initiative) {
                setInitiative({
                  ...initiative,
                  goal_alignment_score: score,
                  goal_alignment_details: details,
                })
              }
            }}
            hasAgentOutputs={outputs.length > 0}
          />
        )}

        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <div className="space-y-4">
            {/* Header: Create + Active Only Toggle */}
            <div className="flex items-center justify-between">
              {canEdit && (
                <button
                  onClick={() => setProjectCreateOpen(true)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-indigo-600 dark:text-indigo-400 border border-indigo-300 dark:border-indigo-600 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Create Project
                </button>
              )}
              <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 ml-auto">
                <input
                  type="checkbox"
                  checked={showActiveProjectsOnly}
                  onChange={(e) => setShowActiveProjectsOnly(e.target.checked)}
                  className="rounded border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500"
                />
                Active only
              </label>
            </div>
            {(() => {
              const filteredProjects = showActiveProjectsOnly
                ? linkedProjects.filter(p => p.status !== 'archived')
                : linkedProjects

              return filteredProjects.length === 0 ? (
                <div className="text-center py-12 border border-dashed border-slate-300 dark:border-slate-600 rounded-lg">
                  <Target className="w-12 h-12 mx-auto text-slate-400 mb-3" />
                  <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
                    {showActiveProjectsOnly && linkedProjects.length > 0
                      ? 'No Active Projects'
                      : 'No Linked Projects'}
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-3">
                    {showActiveProjectsOnly && linkedProjects.length > 0
                      ? 'All linked projects are archived. Uncheck "Active only" to see them.'
                      : 'Create a project from this discovery, or link existing projects from the Projects page.'}
                  </p>
                  {canEdit && !(showActiveProjectsOnly && linkedProjects.length > 0) && (
                    <button
                      onClick={() => setProjectCreateOpen(true)}
                      className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                      Create Project
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredProjects.map((project) => (
                  <a
                    key={project.id}
                    href={`/projects?project=${project.id}`}
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
                        {project.source_type === 'disco_prd' && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
                            From PRD
                          </span>
                        )}
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
              )
            })()}
          </div>
        )}

      </div>

      {/* Share Modal */}
      <ShareModal
        open={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        initiativeId={initiativeId}
        userRole={initiative.user_role}
      />

      {/* Project Create Modal */}
      <ProjectCreateModal
        open={projectCreateOpen}
        onClose={() => setProjectCreateOpen(false)}
        onCreated={() => {
          setProjectCreateOpen(false)
          loadLinkedProjects()
        }}
        initiativeId={initiativeId}
      />

      {/* Edit Discovery Modal */}
      {editModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleCloseEditModal}
          />
          <div
            className="relative w-full max-w-4xl mx-4 bg-white dark:bg-slate-900 rounded-xl shadow-xl max-h-[90vh] flex flex-col"
            onKeyDown={(e) => {
              if (e.key === 'Escape') handleCloseEditModal()
            }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 shrink-0">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Edit Discovery Details
              </h2>
              <button
                onClick={handleCloseEditModal}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="px-6 py-4 space-y-4 overflow-y-auto">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={editedName}
                  onChange={(e) => setEditedName(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  value={editedDescription}
                  onChange={(e) => setEditedDescription(e.target.value)}
                  placeholder="Add a description for this discovery..."
                  rows={3}
                  className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              {/* Value Alignment */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Target Department
                  </label>
                  <select
                    value={editedDepartment}
                    onChange={(e) => setEditedDepartment(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="">Select department...</option>
                    {['Engineering', 'Product', 'Sales', 'Marketing', 'Customer Success', 'People', 'Finance', 'Legal', 'IT', 'Operations', 'Leadership', 'Cross-functional'].map(dept => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Strategic Pillar
                  </label>
                  <select
                    value={editedStrategicPillar}
                    onChange={(e) => setEditedStrategicPillar(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="">None</option>
                    <option value="enable">Enable</option>
                    <option value="operationalize">Operationalize</option>
                    <option value="govern">Govern</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  KPIs
                </label>
                <div className="flex gap-1">
                  <input
                    type="text"
                    value={editedKpiInput}
                    onChange={(e) => setEditedKpiInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && editedKpiInput.trim()) {
                        e.preventDefault()
                        setEditedKpis([...editedKpis, editedKpiInput.trim()])
                        setEditedKpiInput('')
                      }
                    }}
                    placeholder="Add a KPI and press Enter..."
                    className="flex-1 px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      if (editedKpiInput.trim()) {
                        setEditedKpis([...editedKpis, editedKpiInput.trim()])
                        setEditedKpiInput('')
                      }
                    }}
                    className="px-3 py-2 text-xs bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600"
                  >
                    Add
                  </button>
                </div>
                {editedKpis.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {editedKpis.map((kpi, i) => (
                      <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded text-xs">
                        {kpi}
                        <button onClick={() => setEditedKpis(editedKpis.filter((_, j) => j !== i))} className="hover:text-red-500">&times;</button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-slate-200 dark:border-slate-700">
              <button
                onClick={handleCloseEditModal}
                disabled={savingEdit}
                className="px-4 py-2 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={savingEdit || !editedName.trim()}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {savingEdit ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
