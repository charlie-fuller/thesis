'use client'

/**
 * OpportunityDetailModal Component
 *
 * Full-featured detail modal for opportunities showing:
 * - Score justification with visual breakdown
 * - Full opportunity details (description, current/desired state, etc.)
 * - Related documents from knowledge base (sorted by relevance to scoring)
 * - Q&A chat interface with conversation history
 * - Taskmaster chat for breaking projects into tasks
 * - Edit mode for modifying scores and details
 * - Convert to Project workflow
 */

import { useState, useEffect, useRef } from 'react'
import {
  X,
  FileText,
  MessageSquare,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Send,
  Loader2,
  User,
  Building2,
  Target,
  AlertCircle,
  Eye,
  HelpCircle,
  Gauge,
  Pencil,
  Save,
  XCircle,
  Rocket,
  ListTodo,
} from 'lucide-react'
import { apiGet, apiPost, apiPatch } from '@/lib/api'
import ScoreJustification from './ScoreJustification'
import DocumentViewerModal from './DocumentViewerModal'
import ProjectNameModal from './ProjectNameModal'
import TaskmasterChatSection from './TaskmasterChatSection'

// ============================================================================
// TYPES
// ============================================================================

interface Opportunity {
  id: string
  opportunity_code: string
  title: string
  description: string | null
  department: string | null
  owner_stakeholder_id: string | null
  owner_name: string | null
  current_state: string | null
  desired_state: string | null
  roi_potential: number | null
  implementation_effort: number | null
  strategic_alignment: number | null
  stakeholder_readiness: number | null
  total_score: number
  tier: number
  status: string
  next_step: string | null
  blockers: string[]
  follow_up_questions: string[]
  roi_indicators: Record<string, unknown>
  created_at: string
  updated_at: string
  // Project fields
  project_name?: string | null
  project_description?: string | null
  // Extended justification fields
  opportunity_summary?: string | null
  roi_justification?: string | null
  effort_justification?: string | null
  alignment_justification?: string | null
  readiness_justification?: string | null
  // Scoring confidence fields
  scoring_confidence?: number | null  // 0-100 percentage
  confidence_questions?: string[]  // Questions that would raise confidence
}

// Edit form state type
interface EditFormState {
  title: string
  description: string
  department: string
  current_state: string
  desired_state: string
  next_step: string
  roi_potential: number | null
  implementation_effort: number | null
  strategic_alignment: number | null
  stakeholder_readiness: number | null
  status: string
  // Justification fields
  opportunity_summary: string
  roi_justification: string
  effort_justification: string
  alignment_justification: string
  readiness_justification: string
}

interface RelatedDocument {
  chunk_id: string
  document_id: string
  document_name: string
  relevance_score: number
  snippet: string
  metadata: {
    filename?: string
    page_number?: number
    source_type?: string
    storage_path?: string
  }
}

interface LinkedStakeholder {
  id: string
  opportunity_id: string
  stakeholder_id: string
  stakeholder_name: string | null
  stakeholder_role: string | null
  stakeholder_department: string | null
  role: string  // Link role (owner, stakeholder, etc.)
  notes: string | null
  created_at: string
}

interface Conversation {
  id: string
  question: string
  response: string
  source_documents: Array<{
    document_id: string
    document_name: string
    relevance_score: number
    snippet: string
  }>
  created_at: string
}

interface OpportunityDetailModalProps {
  opportunity: Opportunity
  open: boolean
  onClose: () => void
}

// ============================================================================
// STATUS CONFIG
// ============================================================================

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  identified: { label: 'Identified', color: 'text-slate-500' },
  scoping: { label: 'Scoping', color: 'text-blue-500' },
  pilot: { label: 'Pilot', color: 'text-amber-500' },
  scaling: { label: 'Scaling', color: 'text-green-500' },
  completed: { label: 'Completed', color: 'text-green-600' },
  blocked: { label: 'Blocked', color: 'text-red-500' },
}

const STATUS_OPTIONS = [
  { value: 'identified', label: 'Identified' },
  { value: 'scoping', label: 'Scoping' },
  { value: 'pilot', label: 'Pilot' },
  { value: 'scaling', label: 'Scaling' },
  { value: 'completed', label: 'Completed' },
  { value: 'blocked', label: 'Blocked' },
]

const DEPARTMENT_OPTIONS = [
  'Finance',
  'Legal',
  'IT',
  'Operations',
  'HR',
  'Marketing',
  'Sales',
  'Engineering',
  'Executive',
  'General',
  'Other',
]

const TIER_CONFIG = {
  1: { color: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400' },
  2: { color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  3: { color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  4: { color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400' },
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function OpportunityDetailModal({
  opportunity: initialOpportunity,
  open,
  onClose,
}: OpportunityDetailModalProps) {
  // Local opportunity state to allow refreshing after generation
  const [opportunity, setOpportunity] = useState<Opportunity>(initialOpportunity)

  // State
  const [relatedDocs, setRelatedDocs] = useState<RelatedDocument[]>([])
  const [docsLoading, setDocsLoading] = useState(false)
  const [linkedStakeholders, setLinkedStakeholders] = useState<LinkedStakeholder[]>([])
  const [stakeholdersLoading, setStakeholdersLoading] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [conversationsLoading, setConversationsLoading] = useState(false)
  const [showConversations, setShowConversations] = useState(false)

  // Justification generation state
  const [generating, setGenerating] = useState(false)

  // Q&A state
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [latestResponse, setLatestResponse] = useState<{
    response: string
    sources: RelatedDocument[]
  } | null>(null)

  // Document viewer modal state
  const [viewingDocument, setViewingDocument] = useState<{
    document_id: string
    document_name: string
  } | null>(null)

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false)
  const [editForm, setEditForm] = useState<EditFormState>({
    title: '',
    description: '',
    department: '',
    current_state: '',
    desired_state: '',
    next_step: '',
    roi_potential: null,
    implementation_effort: null,
    strategic_alignment: null,
    stakeholder_readiness: null,
    status: 'identified',
    opportunity_summary: '',
    roi_justification: '',
    effort_justification: '',
    alignment_justification: '',
    readiness_justification: '',
  })
  const [isSaving, setIsSaving] = useState(false)

  // Project name modal state
  const [showProjectNameModal, setShowProjectNameModal] = useState(false)
  const [pendingStatus, setPendingStatus] = useState<'scoping' | 'pilot' | null>(null)

  // Tab state
  const [activeTab, setActiveTab] = useState<'scores' | 'details' | 'related' | 'chat'>('scores')

  const questionInputRef = useRef<HTMLTextAreaElement>(null)

  // Update local opportunity when prop changes
  useEffect(() => {
    setOpportunity(initialOpportunity)
    // Reset edit mode when opportunity changes
    setIsEditMode(false)
  }, [initialOpportunity])

  // Initialize edit form when entering edit mode
  useEffect(() => {
    if (isEditMode && opportunity) {
      setEditForm({
        title: opportunity.title || '',
        description: opportunity.description || '',
        department: opportunity.department || '',
        current_state: opportunity.current_state || '',
        desired_state: opportunity.desired_state || '',
        next_step: opportunity.next_step || '',
        roi_potential: opportunity.roi_potential,
        implementation_effort: opportunity.implementation_effort,
        strategic_alignment: opportunity.strategic_alignment,
        stakeholder_readiness: opportunity.stakeholder_readiness,
        status: opportunity.status || 'identified',
        // Justification fields
        opportunity_summary: opportunity.opportunity_summary || '',
        roi_justification: opportunity.roi_justification || '',
        effort_justification: opportunity.effort_justification || '',
        alignment_justification: opportunity.alignment_justification || '',
        readiness_justification: opportunity.readiness_justification || '',
      })
    }
  }, [isEditMode, opportunity])

  // Fetch related documents and stakeholders on open
  useEffect(() => {
    if (open && opportunity) {
      fetchRelatedDocuments()
      fetchLinkedStakeholders()
      fetchConversations()
    }
  }, [open, opportunity?.id])

  // Focus question input when modal opens
  useEffect(() => {
    if (open && questionInputRef.current) {
      // Small delay to ensure modal is rendered
      setTimeout(() => questionInputRef.current?.focus(), 100)
    }
  }, [open])

  const fetchRelatedDocuments = async () => {
    setDocsLoading(true)
    try {
      const docs = await apiGet<RelatedDocument[]>(
        `/api/opportunities/${opportunity.id}/related-documents?limit=8`
      )
      setRelatedDocs(docs)
    } catch (error) {
      console.error('Failed to fetch related documents:', error)
    } finally {
      setDocsLoading(false)
    }
  }

  const fetchLinkedStakeholders = async () => {
    setStakeholdersLoading(true)
    try {
      const stakeholders = await apiGet<LinkedStakeholder[]>(
        `/api/opportunities/${opportunity.id}/stakeholders`
      )
      setLinkedStakeholders(stakeholders)
    } catch (error) {
      console.error('Failed to fetch linked stakeholders:', error)
    } finally {
      setStakeholdersLoading(false)
    }
  }

  const fetchConversations = async () => {
    setConversationsLoading(true)
    try {
      const convos = await apiGet<Conversation[]>(
        `/api/opportunities/${opportunity.id}/conversations?limit=10`
      )
      setConversations(convos)
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    } finally {
      setConversationsLoading(false)
    }
  }

  const handleAskQuestion = async () => {
    if (!question.trim() || asking) return

    setAsking(true)
    setLatestResponse(null)

    try {
      const result = await apiPost<{
        response: string
        sources: RelatedDocument[]
      }>(`/api/opportunities/${opportunity.id}/ask`, { question: question.trim() })

      setLatestResponse(result)
      setQuestion('')

      // Refresh conversations to show the new one
      fetchConversations()
    } catch (error) {
      console.error('Failed to ask question:', error)
      alert('Failed to get an answer. Please try again.')
    } finally {
      setAsking(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAskQuestion()
    }
  }

  const openDocumentInNewTab = (doc: RelatedDocument) => {
    // For now, open KB page with document ID as param
    // In future, could open direct document URL if storage_path available
    const url = `/kb?doc=${doc.document_id}`
    window.open(url, '_blank')
  }

  const getRelevanceColor = (score: number) => {
    if (score >= 0.7) return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    if (score >= 0.5) return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
    if (score >= 0.3) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
    return 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
  }

  const getEngagementBadge = (level: string) => {
    switch (level) {
      case 'champion':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      case 'supporter':
        return 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300'
      case 'neutral':
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
      case 'skeptic':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
      case 'blocker':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
  }

  const getSupportLevelBadge = (level: string | null) => {
    switch (level) {
      case 'strong_support':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      case 'support':
        return 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300'
      case 'opposed':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
  }

  const handleGenerateJustifications = async () => {
    if (generating) return

    setGenerating(true)
    try {
      await apiPost(`/api/opportunities/${opportunity.id}/generate-justifications`, {})

      // Refetch opportunity to get updated justifications
      const updated = await apiGet<Opportunity>(`/api/opportunities/${opportunity.id}`)
      setOpportunity(updated)
    } catch (error) {
      console.error('Failed to generate justifications:', error)
      alert('Failed to generate justifications. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const handleCancelEdit = () => {
    setIsEditMode(false)
  }

  const handleSaveEdit = async () => {
    if (isSaving) return

    setIsSaving(true)
    try {
      // Build update payload - only include changed fields
      const updateData: Record<string, unknown> = {}

      if (editForm.title !== opportunity.title) updateData.title = editForm.title
      if (editForm.description !== (opportunity.description || '')) updateData.description = editForm.description || null
      if (editForm.department !== (opportunity.department || '')) updateData.department = editForm.department || null
      if (editForm.current_state !== (opportunity.current_state || '')) updateData.current_state = editForm.current_state || null
      if (editForm.desired_state !== (opportunity.desired_state || '')) updateData.desired_state = editForm.desired_state || null
      if (editForm.next_step !== (opportunity.next_step || '')) updateData.next_step = editForm.next_step || null
      if (editForm.roi_potential !== opportunity.roi_potential) updateData.roi_potential = editForm.roi_potential
      if (editForm.implementation_effort !== opportunity.implementation_effort) updateData.implementation_effort = editForm.implementation_effort
      if (editForm.strategic_alignment !== opportunity.strategic_alignment) updateData.strategic_alignment = editForm.strategic_alignment
      if (editForm.stakeholder_readiness !== opportunity.stakeholder_readiness) updateData.stakeholder_readiness = editForm.stakeholder_readiness
      // Justification fields
      if (editForm.opportunity_summary !== (opportunity.opportunity_summary || '')) updateData.opportunity_summary = editForm.opportunity_summary || null
      if (editForm.roi_justification !== (opportunity.roi_justification || '')) updateData.roi_justification = editForm.roi_justification || null
      if (editForm.effort_justification !== (opportunity.effort_justification || '')) updateData.effort_justification = editForm.effort_justification || null
      if (editForm.alignment_justification !== (opportunity.alignment_justification || '')) updateData.alignment_justification = editForm.alignment_justification || null
      if (editForm.readiness_justification !== (opportunity.readiness_justification || '')) updateData.readiness_justification = editForm.readiness_justification || null

      // Handle status changes separately (may require project name)
      if (editForm.status !== opportunity.status) {
        const requiresProjectName = ['scoping', 'pilot'].includes(editForm.status)
        const hasProjectName = !!opportunity.project_name

        if (requiresProjectName && !hasProjectName) {
          // Show project name modal
          setPendingStatus(editForm.status as 'scoping' | 'pilot')
          setShowProjectNameModal(true)
          setIsSaving(false)
          return
        }

        updateData.status = editForm.status
      }

      if (Object.keys(updateData).length === 0) {
        setIsEditMode(false)
        setIsSaving(false)
        return
      }

      const updated = await apiPatch<Opportunity>(`/api/opportunities/${opportunity.id}`, updateData)
      setOpportunity(updated)
      setIsEditMode(false)
    } catch (error) {
      console.error('Failed to save opportunity:', error)
      alert('Failed to save changes. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleProjectNameSubmit = async (projectName: string, projectDescription?: string) => {
    if (!pendingStatus) return

    try {
      // Update status with project name
      const updated = await apiPatch<Opportunity>(`/api/opportunities/${opportunity.id}/status`, {
        status: pendingStatus,
        project_name: projectName,
        project_description: projectDescription,
      })
      setOpportunity(updated)
      setShowProjectNameModal(false)
      setPendingStatus(null)
      setIsEditMode(false)
    } catch (error) {
      console.error('Failed to update status:', error)
      alert('Failed to update status. Please try again.')
    }
  }

  const handleConvertToProject = () => {
    // Trigger the project name modal for "Start as Project"
    setPendingStatus('scoping')
    setShowProjectNameModal(true)
  }

  const handleEditFormChange = (field: keyof EditFormState, value: string | number | null) => {
    setEditForm(prev => ({ ...prev, [field]: value }))
  }

  // Check if justifications exist
  const hasJustifications = !!(
    opportunity.opportunity_summary ||
    opportunity.roi_justification ||
    opportunity.effort_justification ||
    opportunity.alignment_justification ||
    opportunity.readiness_justification
  )

  if (!open) return null

  const statusConfig = STATUS_CONFIG[opportunity.status] || STATUS_CONFIG.identified
  const tierConfig = TIER_CONFIG[opportunity.tier as keyof typeof TIER_CONFIG] || TIER_CONFIG[4]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal - Larger size */}
      <div className="relative bg-card border border-default rounded-xl shadow-2xl w-full max-w-6xl max-h-[95vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-default">
          <div className="flex-1 min-w-0 pr-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-mono font-bold text-muted">
                {opportunity.opportunity_code}
              </span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${tierConfig.color}`}>
                Tier {opportunity.tier}
              </span>
              {isEditMode ? (
                <select
                  value={editForm.status}
                  onChange={(e) => handleEditFormChange('status', e.target.value)}
                  className="px-2 py-0.5 rounded text-xs font-medium border border-default bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {STATUS_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              ) : (
                <span className={`text-xs font-medium ${statusConfig.color}`}>
                  {statusConfig.label}
                </span>
              )}
              {opportunity.project_name && (
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                  Project: {opportunity.project_name}
                </span>
              )}
            </div>
            {isEditMode ? (
              <input
                type="text"
                value={editForm.title}
                onChange={(e) => handleEditFormChange('title', e.target.value)}
                className="text-xl font-semibold text-primary bg-transparent border-b border-blue-500 focus:outline-none w-full"
                placeholder="Opportunity title"
              />
            ) : (
              <h2 className="text-xl font-semibold text-primary truncate">
                {opportunity.title}
              </h2>
            )}
            {opportunity.owner_name && !isEditMode && (
              <p className="text-sm text-muted flex items-center gap-1 mt-1">
                <User className="w-3 h-3" />
                {opportunity.owner_name}
                {opportunity.department && (
                  <>
                    <span className="mx-1">|</span>
                    <Building2 className="w-3 h-3" />
                    {opportunity.department}
                  </>
                )}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!isEditMode && (
              <button
                onClick={() => setIsEditMode(true)}
                className="p-2 text-muted hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                title="Edit scores and details"
              >
                <Pencil className="w-5 h-5" />
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-muted hover:text-primary hover:bg-hover rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="flex border-b border-default px-6 bg-hover/30">
          {[
            { id: 'scores' as const, label: 'Scores', icon: Target },
            { id: 'details' as const, label: 'Details', icon: FileText },
            { id: 'related' as const, label: 'Related', icon: ExternalLink },
            { id: 'chat' as const, label: 'Chat', icon: MessageSquare },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-muted hover:text-primary hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* SCORES TAB */}
          {activeTab === 'scores' && (
            <div className="space-y-8">
          {/* Score Justification */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                <Target className="w-4 h-4" />
                Score Justification {isEditMode && <span className="text-blue-500 normal-case">(Editing)</span>}
              </h3>
              {!isEditMode && (
                <button
                  onClick={handleGenerateJustifications}
                  disabled={generating}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      {hasJustifications ? 'Regenerate' : 'Generate'} Analysis
                    </>
                  )}
                </button>
              )}
            </div>

            {isEditMode ? (
              /* Editable Justifications */
              <div className="space-y-4">
                {/* Opportunity Summary */}
                <div>
                  <label className="text-xs font-medium text-muted uppercase block mb-1">
                    Opportunity Summary
                  </label>
                  <textarea
                    value={editForm.opportunity_summary}
                    onChange={(e) => handleEditFormChange('opportunity_summary', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    placeholder="Summary of the opportunity and its potential business impact..."
                  />
                </div>

                {/* Dimension Justifications */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-muted uppercase block mb-1">
                      ROI Potential Justification (Score: {editForm.roi_potential || '-'})
                    </label>
                    <textarea
                      value={editForm.roi_justification}
                      onChange={(e) => handleEditFormChange('roi_justification', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="Why this ROI score? What value does this opportunity provide?"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted uppercase block mb-1">
                      Implementation Effort Justification (Score: {editForm.implementation_effort || '-'})
                    </label>
                    <textarea
                      value={editForm.effort_justification}
                      onChange={(e) => handleEditFormChange('effort_justification', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="Why this effort score? What resources/time are needed?"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted uppercase block mb-1">
                      Strategic Alignment Justification (Score: {editForm.strategic_alignment || '-'})
                    </label>
                    <textarea
                      value={editForm.alignment_justification}
                      onChange={(e) => handleEditFormChange('alignment_justification', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="Why this alignment score? How does it fit business strategy?"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted uppercase block mb-1">
                      Stakeholder Readiness Justification (Score: {editForm.stakeholder_readiness || '-'})
                    </label>
                    <textarea
                      value={editForm.readiness_justification}
                      onChange={(e) => handleEditFormChange('readiness_justification', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="Why this readiness score? Are stakeholders prepared for change?"
                    />
                  </div>
                </div>
              </div>
            ) : (
              <ScoreJustification
                roiPotential={opportunity.roi_potential}
                implementationEffort={opportunity.implementation_effort}
                strategicAlignment={opportunity.strategic_alignment}
                stakeholderReadiness={opportunity.stakeholder_readiness}
                totalScore={opportunity.total_score}
                tier={opportunity.tier}
                opportunityDescription={opportunity.opportunity_summary || undefined}
                dimensionJustifications={{
                  roi_potential: opportunity.roi_justification || undefined,
                  implementation_effort: opportunity.effort_justification || undefined,
                  strategic_alignment: opportunity.alignment_justification || undefined,
                  stakeholder_readiness: opportunity.readiness_justification || undefined,
                }}
              />
            )}
          </section>

          {/* Scoring Confidence */}
          {(opportunity.scoring_confidence !== null && opportunity.scoring_confidence !== undefined) && (
            <section>
              <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4 flex items-center gap-2">
                <Gauge className="w-4 h-4" />
                Scoring Confidence
              </h3>
              <div className="bg-card border border-default rounded-lg p-4 space-y-4">
                {/* Confidence Meter */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-secondary">Confidence Level</span>
                    <span className={`text-lg font-bold ${
                      opportunity.scoring_confidence >= 80 ? 'text-green-600 dark:text-green-400' :
                      opportunity.scoring_confidence >= 60 ? 'text-blue-600 dark:text-blue-400' :
                      opportunity.scoring_confidence >= 40 ? 'text-amber-600 dark:text-amber-400' :
                      'text-red-600 dark:text-red-400'
                    }`}>
                      {opportunity.scoring_confidence}%
                    </span>
                  </div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        opportunity.scoring_confidence >= 80 ? 'bg-green-500' :
                        opportunity.scoring_confidence >= 60 ? 'bg-blue-500' :
                        opportunity.scoring_confidence >= 40 ? 'bg-amber-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${opportunity.scoring_confidence}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted mt-1">
                    {opportunity.scoring_confidence >= 80 ? 'High confidence - scores are well-supported' :
                     opportunity.scoring_confidence >= 60 ? 'Moderate confidence - some assumptions made' :
                     opportunity.scoring_confidence >= 40 ? 'Low confidence - significant unknowns' :
                     'Very low confidence - mostly speculative'}
                  </p>
                </div>

                {/* Questions to Raise Confidence */}
                {opportunity.confidence_questions && opportunity.confidence_questions.length > 0 && (
                  <div>
                    <h4 className="text-xs font-medium text-muted uppercase mb-2 flex items-center gap-1">
                      <HelpCircle className="w-3 h-3" />
                      Questions to Raise Confidence
                    </h4>
                    <ul className="space-y-2">
                      {opportunity.confidence_questions.map((question, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm text-secondary bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2"
                        >
                          <span className="flex-shrink-0 w-5 h-5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full flex items-center justify-center text-xs font-medium">
                            {i + 1}
                          </span>
                          <span>{question}</span>
                        </li>
                      ))}
                    </ul>
                    <p className="text-xs text-muted mt-2">
                      Answering these questions would help refine the scoring accuracy.
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}
            </div>
          )}

          {/* DETAILS TAB */}
          {activeTab === 'details' && (
            <div className="space-y-8">
          {/* Opportunity Details */}
          <section>
            <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4">
              Opportunity Details {isEditMode && <span className="text-blue-500 normal-case">(Editing)</span>}
            </h3>
            <div className="space-y-4">
              {/* Department (edit mode only or if has value) */}
              {(isEditMode || opportunity.department) && (
                <div>
                  <h4 className="text-xs font-medium text-muted uppercase mb-1">Department</h4>
                  {isEditMode ? (
                    <select
                      value={editForm.department}
                      onChange={(e) => handleEditFormChange('department', e.target.value)}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select department...</option>
                      {DEPARTMENT_OPTIONS.map(dept => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
                    </select>
                  ) : (
                    <p className="text-sm text-secondary">{opportunity.department}</p>
                  )}
                </div>
              )}

              {/* Description */}
              {(isEditMode || opportunity.description) && (
                <div>
                  <h4 className="text-xs font-medium text-muted uppercase mb-1">Description</h4>
                  {isEditMode ? (
                    <textarea
                      value={editForm.description}
                      onChange={(e) => handleEditFormChange('description', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="Describe the opportunity..."
                    />
                  ) : (
                    <p className="text-sm text-secondary whitespace-pre-wrap">{opportunity.description}</p>
                  )}
                </div>
              )}

              {/* Current/Desired State */}
              {(isEditMode || opportunity.current_state || opportunity.desired_state) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className={`p-3 ${isEditMode ? 'border border-default' : 'bg-red-50 dark:bg-red-900/10'} rounded-lg`}>
                    <h4 className={`text-xs font-medium ${isEditMode ? 'text-muted' : 'text-red-600 dark:text-red-400'} uppercase mb-1`}>
                      Current State
                    </h4>
                    {isEditMode ? (
                      <textarea
                        value={editForm.current_state}
                        onChange={(e) => handleEditFormChange('current_state', e.target.value)}
                        rows={3}
                        className="w-full px-2 py-1 border border-default rounded bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        placeholder="Describe current state..."
                      />
                    ) : (
                      <p className="text-sm text-secondary">{opportunity.current_state}</p>
                    )}
                  </div>
                  <div className={`p-3 ${isEditMode ? 'border border-default' : 'bg-green-50 dark:bg-green-900/10'} rounded-lg`}>
                    <h4 className={`text-xs font-medium ${isEditMode ? 'text-muted' : 'text-green-600 dark:text-green-400'} uppercase mb-1`}>
                      Desired State
                    </h4>
                    {isEditMode ? (
                      <textarea
                        value={editForm.desired_state}
                        onChange={(e) => handleEditFormChange('desired_state', e.target.value)}
                        rows={3}
                        className="w-full px-2 py-1 border border-default rounded bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        placeholder="Describe desired state..."
                      />
                    ) : (
                      <p className="text-sm text-secondary">{opportunity.desired_state}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Next Step */}
              {(isEditMode || opportunity.next_step) && (
                <div>
                  <h4 className="text-xs font-medium text-muted uppercase mb-1">Next Step</h4>
                  {isEditMode ? (
                    <textarea
                      value={editForm.next_step}
                      onChange={(e) => handleEditFormChange('next_step', e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="What's the next step?"
                    />
                  ) : (
                    <p className="text-sm text-secondary">{opportunity.next_step}</p>
                  )}
                </div>
              )}

              {/* Scores (Edit Mode) */}
              {isEditMode && (
                <div>
                  <h4 className="text-xs font-medium text-muted uppercase mb-2">Scores (1-5)</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="text-xs text-muted block mb-1">ROI Potential</label>
                      <input
                        type="number"
                        min="1"
                        max="5"
                        value={editForm.roi_potential || ''}
                        onChange={(e) => handleEditFormChange('roi_potential', e.target.value ? parseInt(e.target.value) : null)}
                        className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="-"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted block mb-1">Effort</label>
                      <input
                        type="number"
                        min="1"
                        max="5"
                        value={editForm.implementation_effort || ''}
                        onChange={(e) => handleEditFormChange('implementation_effort', e.target.value ? parseInt(e.target.value) : null)}
                        className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="-"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted block mb-1">Strategic</label>
                      <input
                        type="number"
                        min="1"
                        max="5"
                        value={editForm.strategic_alignment || ''}
                        onChange={(e) => handleEditFormChange('strategic_alignment', e.target.value ? parseInt(e.target.value) : null)}
                        className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="-"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted block mb-1">Readiness</label>
                      <input
                        type="number"
                        min="1"
                        max="5"
                        value={editForm.stakeholder_readiness || ''}
                        onChange={(e) => handleEditFormChange('stakeholder_readiness', e.target.value ? parseInt(e.target.value) : null)}
                        className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="-"
                      />
                    </div>
                  </div>
                </div>
              )}

              {opportunity.blockers.length > 0 && !isEditMode && (
                <div>
                  <h4 className="text-xs font-medium text-red-500 uppercase mb-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Blockers
                  </h4>
                  <ul className="text-sm text-secondary list-disc list-inside space-y-1">
                    {opportunity.blockers.map((blocker, i) => (
                      <li key={i}>{blocker}</li>
                    ))}
                  </ul>
                </div>
              )}

              {Object.keys(opportunity.roi_indicators).length > 0 && !isEditMode && (
                <div>
                  <h4 className="text-xs font-medium text-muted uppercase mb-1">ROI Indicators</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(opportunity.roi_indicators).map(([key, value]) => (
                      <span
                        key={key}
                        className="px-2 py-1 bg-hover rounded text-xs text-secondary"
                      >
                        {key.replace(/_/g, ' ')}: {String(value)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Convert to Project CTA - Only show when status is "identified" and no project_name */}
          {!isEditMode && opportunity.status === 'identified' && !opportunity.project_name && (
            <section className="bg-gradient-to-r from-emerald-50 to-blue-50 dark:from-emerald-900/20 dark:to-blue-900/20 rounded-lg p-4 border border-emerald-200 dark:border-emerald-800">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
                    <Rocket className="w-4 h-4" />
                    Ready to move forward?
                  </h3>
                  <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1">
                    Convert this opportunity into an active project to start scoping and task planning.
                  </p>
                </div>
                <button
                  onClick={handleConvertToProject}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2 text-sm font-medium"
                >
                  <Rocket className="w-4 h-4" />
                  Start as Project
                </button>
              </div>
            </section>
          )}
            </div>
          )}

          {/* RELATED TAB */}
          {activeTab === 'related' && (
            <div className="space-y-8">
          {/* Linked Stakeholders */}
          {(linkedStakeholders.length > 0 || stakeholdersLoading) && (
            <section>
              <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4 flex items-center gap-2">
                <User className="w-4 h-4" />
                Linked Stakeholders
                {linkedStakeholders.length > 0 && (
                  <span className="text-xs font-normal">({linkedStakeholders.length})</span>
                )}
              </h3>

              {stakeholdersLoading ? (
                <div className="flex items-center gap-2 text-muted py-4">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Loading stakeholders...</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {linkedStakeholders.map((stakeholder) => (
                    <div
                      key={stakeholder.id}
                      className="border border-default rounded-lg p-3 hover:bg-hover transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4 text-muted flex-shrink-0" />
                            <span className="text-sm font-medium text-primary truncate">
                              {stakeholder.stakeholder_name || 'Unknown'}
                            </span>
                          </div>
                          {stakeholder.stakeholder_role && (
                            <p className="text-xs text-muted ml-6 truncate">
                              {stakeholder.stakeholder_role}
                              {stakeholder.stakeholder_department && ` - ${stakeholder.stakeholder_department}`}
                            </p>
                          )}
                        </div>
                        <span className="px-2 py-0.5 rounded text-xs font-medium capitalize bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                          {stakeholder.role}
                        </span>
                      </div>
                      {stakeholder.notes && (
                        <p className="text-xs text-muted mt-2 ml-6 line-clamp-2">
                          {stakeholder.notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Related Documents */}
          <section>
            <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Related Documents
              {relatedDocs.length > 0 && (
                <span className="text-xs font-normal">({relatedDocs.length})</span>
              )}
            </h3>

            {docsLoading ? (
              <div className="flex items-center gap-2 text-muted py-4">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Finding relevant documents...</span>
              </div>
            ) : relatedDocs.length === 0 ? (
              <p className="text-sm text-muted py-4">
                No related documents found in the knowledge base.
              </p>
            ) : (
              <div className="space-y-2">
                {relatedDocs.map((doc) => (
                  <div
                    key={doc.chunk_id}
                    className="border border-default rounded-lg p-3 hover:bg-hover transition-colors"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <FileText className="w-4 h-4 text-muted flex-shrink-0" />
                          <span
                            className="text-sm font-medium text-primary truncate cursor-pointer hover:underline"
                            onClick={() => setViewingDocument({
                              document_id: doc.document_id,
                              document_name: doc.document_name
                            })}
                            title={`View ${doc.document_name}`}
                          >
                            {doc.document_name}
                          </span>
                          <button
                            onClick={() => setViewingDocument({
                              document_id: doc.document_id,
                              document_name: doc.document_name
                            })}
                            className="p-1 text-muted hover:text-blue-500"
                            title="View document"
                          >
                            <Eye className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => openDocumentInNewTab(doc)}
                            className="p-1 text-muted hover:text-primary"
                            title="Open in Knowledge Base"
                          >
                            <ExternalLink className="w-3 h-3" />
                          </button>
                        </div>
                        <p className="text-xs text-muted line-clamp-2">{doc.snippet}</p>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${getRelevanceColor(
                          doc.relevance_score
                        )}`}
                        title={`Relevance: ${(doc.relevance_score * 100).toFixed(0)}%`}
                      >
                        {(doc.relevance_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
            </div>
          )}

          {/* CHAT TAB */}
          {activeTab === 'chat' && (
            <div className="space-y-8">
          {/* Q&A Section */}
          <section>
            <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Ask About This Opportunity
            </h3>

            {/* Previous Conversations */}
            {conversations.length > 0 && (
              <div className="mb-4">
                <button
                  onClick={() => setShowConversations(!showConversations)}
                  className="flex items-center gap-1 text-sm text-muted hover:text-primary mb-2"
                >
                  {showConversations ? (
                    <ChevronDown className="w-4 h-4" />
                  ) : (
                    <ChevronRight className="w-4 h-4" />
                  )}
                  Previous questions ({conversations.length})
                </button>

                {showConversations && (
                  <div className="space-y-3 max-h-60 overflow-y-auto border border-default rounded-lg p-3 bg-hover/50">
                    {conversationsLoading ? (
                      <div className="flex items-center gap-2 text-muted">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Loading...</span>
                      </div>
                    ) : (
                      conversations.map((conv) => (
                        <div key={conv.id} className="text-sm">
                          <p className="font-medium text-primary mb-1">Q: {conv.question}</p>
                          <p className="text-secondary line-clamp-3">{conv.response}</p>
                          <p className="text-xs text-muted mt-1">
                            {new Date(conv.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Question Input */}
            <div className="space-y-3">
              <div className="relative">
                <textarea
                  ref={questionInputRef}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a question about this opportunity..."
                  className="w-full px-4 py-3 pr-12 border border-default rounded-lg bg-card text-primary placeholder-muted resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  disabled={asking}
                />
                <button
                  onClick={handleAskQuestion}
                  disabled={!question.trim() || asking}
                  className="absolute right-3 bottom-3 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {asking ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-muted">
                Press Enter to send, Shift+Enter for new line
              </p>
            </div>

            {/* Latest Response */}
            {latestResponse && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg">
                <h4 className="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase mb-2">
                  Response
                </h4>
                <p className="text-sm text-secondary whitespace-pre-wrap">
                  {latestResponse.response}
                </p>

                {latestResponse.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
                    <p className="text-xs text-muted mb-2">
                      Sources ({latestResponse.sources.length}):
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {latestResponse.sources.map((source, i) => (
                        <button
                          key={source.chunk_id || i}
                          onClick={() => openDocumentInNewTab(source)}
                          className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded hover:bg-blue-200 dark:hover:bg-blue-900/50 flex items-center gap-1"
                        >
                          <FileText className="w-3 h-3" />
                          {source.document_name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* Taskmaster Section */}
          {!isEditMode && (
            opportunity.project_name ? (
              <TaskmasterChatSection
                opportunityId={opportunity.id}
                projectName={opportunity.project_name}
                opportunityTitle={opportunity.title}
              />
            ) : (
              /* Prompt to convert to project first */
              <section className="border border-dashed border-amber-300 dark:border-amber-700 rounded-lg p-4 bg-amber-50/50 dark:bg-amber-900/10">
                <div className="flex items-start gap-3">
                  <ListTodo className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-medium text-amber-800 dark:text-amber-300">
                      Break Down Tasks with Taskmaster
                    </h3>
                    <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                      Convert this opportunity to a project first to unlock Taskmaster.
                      Click &quot;Start as Project&quot; above or change the status to Scoping/Pilot to begin.
                    </p>
                  </div>
                </div>
              </section>
            )
          )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 p-4 border-t border-default">
          {isEditMode ? (
            <>
              <p className="text-xs text-muted">
                Tip: Changing status to Scoping or Pilot will prompt you to name the project.
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleCancelEdit}
                  disabled={isSaving}
                  className="px-4 py-2 text-secondary hover:text-primary hover:bg-hover rounded-lg transition-colors flex items-center gap-2"
                >
                  <XCircle className="w-4 h-4" />
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  disabled={isSaving}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                >
                  {isSaving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  Save Changes
                </button>
              </div>
            </>
          ) : (
            <>
              <div />
              <button
                onClick={onClose}
                className="px-4 py-2 text-secondary hover:text-primary hover:bg-hover rounded-lg transition-colors"
              >
                Close
              </button>
            </>
          )}
        </div>
      </div>

      {/* Document Viewer Modal */}
      <DocumentViewerModal
        document={viewingDocument}
        open={!!viewingDocument}
        onClose={() => setViewingDocument(null)}
      />

      {/* Project Name Modal */}
      <ProjectNameModal
        open={showProjectNameModal}
        onClose={() => {
          setShowProjectNameModal(false)
          setPendingStatus(null)
        }}
        onSubmit={handleProjectNameSubmit}
        opportunityTitle={opportunity.title}
        newStatus={pendingStatus || 'scoping'}
      />
    </div>
  )
}
