'use client'

/**
 * ProjectDetailModal Component
 *
 * Full-featured detail modal for projects with tabbed interface:
 *
 * Tabs:
 * - Scores: Score breakdown with inline editing, AI-generated justifications
 * - Confidence: Scoring confidence meter and questions to raise confidence
 * - Details: Description, current/desired state, next step (all inline-editable)
 * - Related: Linked stakeholders and related documents from KB
 * - Chat: Q&A about the project + Taskmaster for task breakdown
 *
 * Features:
 * - Individual inline edit icons for each section (hover to reveal)
 * - Convert to Active Project workflow with project naming
 * - AI-generated justifications for scores
 */

import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useRouter } from 'next/navigation'
import {
  X,
  FileText,
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
  Compass,
  Plus,
  Trash2,
  Link,
  Unlink,
  Zap,
  AlertTriangle,
  RefreshCw,
  Download,
  Network,
} from 'lucide-react'
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import TaskDependencyGraph, { TaskGraphNode } from '@/components/tasks/TaskDependencyGraph'
import ScoreJustification from './ScoreJustification'
import DocumentViewerModal from './DocumentViewerModal'
import ProjectNameModal from './ProjectNameModal'
import GoalAlignmentSection from './GoalAlignmentSection'
import ProjectDocumentBrowser from './ProjectDocumentBrowser'
import KrakenPanel from './KrakenPanel'
import ProjectAgentPanel from './ProjectAgentPanel'

// ============================================================================
// TYPES
// ============================================================================

interface Project {
  id: string
  project_code?: string  // New naming
  opportunity_code?: string  // Legacy naming (backward compatibility)
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
  // Active project fields
  project_name?: string | null
  project_description?: string | null
  // Extended justification fields
  project_summary?: string | null
  roi_justification?: string | null
  effort_justification?: string | null
  alignment_justification?: string | null
  readiness_justification?: string | null
  // Scoring confidence fields
  scoring_confidence?: number | null  // 0-100 percentage
  confidence_questions?: string[]  // Questions that would raise confidence
  // Goal alignment fields
  goal_alignment_score?: number | null  // 0-100 alignment with IS strategic goals
  goal_alignment_details?: {
    pillar_scores: {
      customer_prospect_journey: { score: number; rationale: string }
      maximize_value: { score: number; rationale: string }
      data_first_digital_workforce: { score: number; rationale: string }
      high_trust_culture: { score: number; rationale: string }
    }
    kpi_impacts: string[]
    summary: string
    analyzed_at: string
  } | null
  // Linked initiatives
  initiative_ids?: string[]
  // Agenticity fields (Kraken)
  agenticity_score?: number | null
  agenticity_evaluated_at?: string | null
}

interface Initiative {
  id: string
  name: string
  status?: string
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
  project_summary: string
  roi_justification: string
  effort_justification: string
  alignment_justification: string
  readiness_justification: string
}

interface LinkedStakeholder {
  id: string
  project_id: string
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

interface LinkedDocument {
  id: string
  document_id: string
  document_name: string
  title: string | null
  linked_at: string
  linked_by: string | null
  notes: string | null
}

interface ProjectDetailModalProps {
  project: Project
  open: boolean
  onClose: () => void
  onProjectUpdated?: (updated: Project) => void
}

// ============================================================================
// STATUS CONFIG
// ============================================================================

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  backlog: { label: 'Backlog', color: 'text-slate-500' },
  active: { label: 'Active', color: 'text-blue-500' },
  completed: { label: 'Completed', color: 'text-green-600' },
  archived: { label: 'Archived', color: 'text-gray-500' },
}

const STATUS_OPTIONS = [
  { value: 'backlog', label: 'Backlog' },
  { value: 'active', label: 'Active' },
  { value: 'completed', label: 'Completed' },
  { value: 'archived', label: 'Archived' },
]

const DEPARTMENT_OPTIONS = [
  'Finance',
  'Legal',
  'IT',
  'Operations',
  'People',
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

export default function ProjectDetailModal({
  project: initialProject,
  open,
  onClose,
  onProjectUpdated,
}: ProjectDetailModalProps) {
  // Local project state to allow refreshing after generation
  const [project, setProject] = useState<Project>(initialProject)

  // State
  const [linkedDocuments, setLinkedDocuments] = useState<LinkedDocument[]>([])
  const [linkedDocsLoading, setLinkedDocsLoading] = useState(false)
  const [showDocumentBrowser, setShowDocumentBrowser] = useState(false)
  const [unlinkingDocId, setUnlinkingDocId] = useState<string | null>(null)
  const [showInitiativeDocPicker, setShowInitiativeDocPicker] = useState(false)
  const [initiativeDocs, setInitiativeDocs] = useState<{ id: string; document_id: string; filename: string; title?: string }[]>([])
  const [initiativeDocsLoading, setInitiativeDocsLoading] = useState(false)
  const [selectedInitiativeDocIds, setSelectedInitiativeDocIds] = useState<string[]>([])
  const [linkingInitiativeDocs, setLinkingInitiativeDocs] = useState(false)
  const [linkedStakeholders, setLinkedStakeholders] = useState<LinkedStakeholder[]>([])
  const [stakeholdersLoading, setStakeholdersLoading] = useState(false)
  const [linkedInitiatives, setLinkedInitiatives] = useState<Initiative[]>([])
  const [availableInitiatives, setAvailableInitiatives] = useState<Initiative[]>([])
  const [initiativesLoading, setInitiativesLoading] = useState(false)
  const [editingInitiatives, setEditingInitiatives] = useState(false)
  const [selectedInitiativeIds, setSelectedInitiativeIds] = useState<string[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [conversationsLoading, setConversationsLoading] = useState(false)
  const [showConversations, setShowConversations] = useState(false)

  // Tasks state
  interface ProjectTask {
    id: string
    title: string
    status: 'pending' | 'in_progress' | 'blocked' | 'completed'
    priority: number
    due_date: string | null
    assignee_name: string | null
    assignee_user_id: string | null
    assignee_stakeholder_id: string | null
    depends_on: string[]
    sequence_number: number | null
    linked_project_id: string | null
  }
  const [projectTasks, setProjectTasks] = useState<ProjectTask[]>([])
  const [tasksLoading, setTasksLoading] = useState(false)

  // Justification generation state
  const [generating, setGenerating] = useState(false)

  // Document viewer modal state
  const [viewingDocument, setViewingDocument] = useState<{
    document_id: string
    document_name: string
  } | null>(null)

  // Edit form state (used by individual section editing)
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
    status: 'backlog',
    project_summary: '',
    roi_justification: '',
    effort_justification: '',
    alignment_justification: '',
    readiness_justification: '',
  })
  const [isSaving, setIsSaving] = useState(false)

  // Project name modal state (for activating projects)
  const [showProjectNameModal, setShowProjectNameModal] = useState(false)
  const [pendingStatus, setPendingStatus] = useState<'active' | null>(null)

  // Task generation state
  const [shouldAutoGenerateTasks, setShouldAutoGenerateTasks] = useState(false)
  const [generatingTasks, setGeneratingTasks] = useState(false)
  const [tasksGeneratedCount, setTasksGeneratedCount] = useState<number | null>(null)

  // Tab state
  const [activeTab, setActiveTab] = useState<'scores' | 'confidence' | 'alignment' | 'details' | 'tasks' | 'graph' | 'documents' | 'disco' | 'kraken-guide' | 'scoring-guide'>('details')

  const router = useRouter()
  const { profile } = useAuth()

  // Individual section editing state (replaces global edit mode)
  const [editingSection, setEditingSection] = useState<
    'header' | 'scores' | 'justifications' | 'description' | 'states' | 'next_step' | null
  >(null)

  const questionInputRef = useRef<HTMLTextAreaElement>(null)

  // Update local project when prop changes
  useEffect(() => {
    setProject(initialProject)
    // Reset editing section and auto-generate flag when project changes
    setEditingSection(null)
    setShouldAutoGenerateTasks(false)
  }, [initialProject])

  // Initialize edit form when entering any section's edit mode
  useEffect(() => {
    if (editingSection && project) {
      setEditForm({
        title: project.title || '',
        description: project.description || '',
        department: project.department || '',
        current_state: project.current_state || '',
        desired_state: project.desired_state || '',
        next_step: project.next_step || '',
        roi_potential: project.roi_potential,
        implementation_effort: project.implementation_effort,
        strategic_alignment: project.strategic_alignment,
        stakeholder_readiness: project.stakeholder_readiness,
        status: project.status || 'backlog',
        // Justification fields
        project_summary: project.project_summary || '',
        roi_justification: project.roi_justification || '',
        effort_justification: project.effort_justification || '',
        alignment_justification: project.alignment_justification || '',
        readiness_justification: project.readiness_justification || '',
      })
    }
  }, [editingSection, project])

  // Fetch related documents, stakeholders, initiatives, and tasks on open
  useEffect(() => {
    if (open && project) {
      fetchLinkedDocuments()
      fetchLinkedStakeholders()
      fetchConversations()
      fetchLinkedInitiatives()
      fetchProjectTasks()
    }
  }, [open, project?.id])

  // Focus question input when modal opens
  useEffect(() => {
    if (open && questionInputRef.current) {
      // Small delay to ensure modal is rendered
      setTimeout(() => questionInputRef.current?.focus(), 100)
    }
  }, [open])

  const fetchLinkedDocuments = async () => {
    setLinkedDocsLoading(true)
    try {
      const docs = await apiGet<LinkedDocument[]>(
        `/api/projects/${project.id}/documents`
      )
      setLinkedDocuments(docs)
    } catch (error) {
      console.error('Failed to fetch linked documents:', error)
    } finally {
      setLinkedDocsLoading(false)
    }
  }

  const handleUnlinkDocument = async (documentId: string) => {
    setUnlinkingDocId(documentId)
    try {
      await apiDelete(`/api/projects/${project.id}/documents/${documentId}`)
      setLinkedDocuments(prev => prev.filter(d => d.document_id !== documentId))
    } catch (error) {
      console.error('Failed to unlink document:', error)
    } finally {
      setUnlinkingDocId(null)
    }
  }

  const handleDocumentsLinked = () => {
    fetchLinkedDocuments()
  }

  const handleShowInitiativeDocPicker = async () => {
    const initiativeIds = project.initiative_ids || []
    if (initiativeIds.length === 0) return

    setShowInitiativeDocPicker(true)
    setInitiativeDocsLoading(true)
    setSelectedInitiativeDocIds([])
    try {
      // Fetch docs from all linked initiatives
      const allDocs: typeof initiativeDocs = []
      const alreadyLinkedIds = new Set(linkedDocuments.map(d => d.document_id))
      for (const initId of initiativeIds) {
        const result = await apiGet<{ documents: { id: string; document_id: string; filename: string; title?: string }[] }>(
          `/api/disco/initiatives/${initId}/linked-documents`
        )
        if (result.documents) {
          for (const doc of result.documents) {
            // Backend returns `id` as the document ID; normalize to `document_id`
            const docId = doc.document_id || doc.id
            if (!alreadyLinkedIds.has(docId) && !allDocs.some(d => d.document_id === docId)) {
              allDocs.push({ ...doc, document_id: docId })
            }
          }
        }
      }
      setInitiativeDocs(allDocs)
    } catch (error) {
      console.error('Failed to fetch initiative documents:', error)
    } finally {
      setInitiativeDocsLoading(false)
    }
  }

  const handleLinkSelectedInitiativeDocs = async () => {
    if (selectedInitiativeDocIds.length === 0) return
    setLinkingInitiativeDocs(true)
    try {
      await apiPost(`/api/projects/${project.id}/documents/link`, {
        document_ids: selectedInitiativeDocIds,
      })
      fetchLinkedDocuments()
      setShowInitiativeDocPicker(false)
      setSelectedInitiativeDocIds([])
      setInitiativeDocs([])
    } catch (error) {
      console.error('Failed to link initiative documents:', error)
    } finally {
      setLinkingInitiativeDocs(false)
    }
  }

  const fetchLinkedStakeholders = async () => {
    setStakeholdersLoading(true)
    try {
      const stakeholders = await apiGet<LinkedStakeholder[]>(
        `/api/projects/${project.id}/stakeholders`
      )
      setLinkedStakeholders(stakeholders)
    } catch (error) {
      console.error('Failed to fetch linked stakeholders:', error)
    } finally {
      setStakeholdersLoading(false)
    }
  }

  const fetchLinkedInitiatives = async () => {
    setInitiativesLoading(true)
    try {
      // Get list of available initiatives
      const tagsResult = await apiGet<{ success: boolean; tags: Array<{ tag: string; initiative_id: string; status: string }> }>(
        '/api/disco/initiatives/as-tags'
      )
      if (tagsResult.success && tagsResult.tags) {
        const initiatives = tagsResult.tags.map(t => ({
          id: t.initiative_id,
          name: t.tag,
          status: t.status,
        }))
        setAvailableInitiatives(initiatives)

        // Filter to get linked initiatives based on project.initiative_ids
        const linkedIds = project.initiative_ids || []
        const linked = initiatives.filter(i => linkedIds.includes(i.id))
        setLinkedInitiatives(linked)
        setSelectedInitiativeIds(linkedIds)
      }
    } catch (error) {
      console.error('Failed to fetch initiatives:', error)
    } finally {
      setInitiativesLoading(false)
    }
  }

  const handleSaveInitiatives = async () => {
    setIsSaving(true)
    try {
      await apiPatch(`/api/projects/${project.id}`, {
        initiative_ids: selectedInitiativeIds,
      })
      // Update local state
      const linked = availableInitiatives.filter(i => selectedInitiativeIds.includes(i.id))
      setLinkedInitiatives(linked)
      setProject({ ...project, initiative_ids: selectedInitiativeIds })
      setEditingInitiatives(false)
    } catch (error) {
      console.error('Failed to save initiatives:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const toggleInitiative = (initiativeId: string) => {
    setSelectedInitiativeIds(prev =>
      prev.includes(initiativeId)
        ? prev.filter(id => id !== initiativeId)
        : [...prev, initiativeId]
    )
  }

  const fetchConversations = async () => {
    setConversationsLoading(true)
    try {
      const convos = await apiGet<Conversation[]>(
        `/api/projects/${project.id}/conversations?limit=10`
      )
      setConversations(convos)
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    } finally {
      setConversationsLoading(false)
    }
  }

  const fetchProjectTasks = async () => {
    setTasksLoading(true)
    try {
      const response = await apiGet<{ success: boolean; tasks: ProjectTask[] }>(
        `/api/tasks?linked_project_id=${project.id}&limit=50`
      )
      if (response.success) {
        setProjectTasks(response.tasks || [])
      }
    } catch (error) {
      console.error('Failed to fetch project tasks:', error)
    } finally {
      setTasksLoading(false)
    }
  }

  const handleGenerateTasks = async () => {
    if (generatingTasks) return
    setGeneratingTasks(true)
    setTasksGeneratedCount(null)
    try {
      const result = await apiPost<{ response: string; tasks_created: number; task_titles: string[] }>(
        `/api/projects/${project.id}/taskmaster-chat`,
        { message: 'Break this project into actionable tasks based on its description, current state, desired state, and any blockers.' }
      )
      setTasksGeneratedCount(result.tasks_created)
      await fetchProjectTasks()
    } catch (error) {
      console.error('Failed to generate tasks:', error)
      alert('Failed to generate tasks. Make sure the project has been activated first.')
    } finally {
      setGeneratingTasks(false)
      setShouldAutoGenerateTasks(false)
    }
  }

  // Auto-generate tasks when shouldAutoGenerateTasks is set (after project activation)
  useEffect(() => {
    if (shouldAutoGenerateTasks && activeTab === 'tasks' && !generatingTasks) {
      handleGenerateTasks()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldAutoGenerateTasks, activeTab])

  const handleGenerateJustifications = async () => {
    if (generating) return

    setGenerating(true)
    try {
      await apiPost(`/api/projects/${project.id}/generate-justifications`, {})

      // Refetch project to get updated justifications
      const updated = await apiGet<Project>(`/api/projects/${project.id}`)
      setProject(updated)
    } catch (error) {
      console.error('Failed to generate justifications:', error)
      alert('Failed to generate justifications. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const handleAnalyzeGoalAlignment = async () => {
    try {
      await apiPost(`/api/projects/${project.id}/analyze-goal-alignment`, {})

      // Refetch project to get updated goal alignment data
      const updated = await apiGet<Project>(`/api/projects/${project.id}`)
      setProject(updated)
    } catch (error) {
      console.error('Failed to analyze goal alignment:', error)
      alert('Failed to analyze goal alignment. Please try again.')
      throw error // Re-throw so the component can handle loading state
    }
  }

  const handleAlignmentDetailsUpdated = async (details: import('./GoalAlignmentSection').GoalAlignmentDetails) => {
    try {
      const updated = await apiPatch<Project>(`/api/projects/${project.id}`, {
        goal_alignment_details: details,
      })
      setProject(updated)
    } catch (error) {
      console.error('Failed to update alignment details:', error)
    }
  }

  // Save individual section
  const handleSaveSection = async (section: typeof editingSection) => {
    if (isSaving || !section) return

    setIsSaving(true)
    try {
      const updateData: Record<string, unknown> = {}

      switch (section) {
        case 'header':
          if (editForm.title !== project.title) updateData.title = editForm.title
          if (editForm.status !== project.status) {
            updateData.status = editForm.status
          }
          break

        case 'scores':
          if (editForm.roi_potential !== project.roi_potential) updateData.roi_potential = editForm.roi_potential
          if (editForm.implementation_effort !== project.implementation_effort) updateData.implementation_effort = editForm.implementation_effort
          if (editForm.strategic_alignment !== project.strategic_alignment) updateData.strategic_alignment = editForm.strategic_alignment
          if (editForm.stakeholder_readiness !== project.stakeholder_readiness) updateData.stakeholder_readiness = editForm.stakeholder_readiness
          break

        case 'justifications':
          if (editForm.project_summary !== (project.project_summary || '')) updateData.project_summary = editForm.project_summary || null
          if (editForm.roi_justification !== (project.roi_justification || '')) updateData.roi_justification = editForm.roi_justification || null
          if (editForm.effort_justification !== (project.effort_justification || '')) updateData.effort_justification = editForm.effort_justification || null
          if (editForm.alignment_justification !== (project.alignment_justification || '')) updateData.alignment_justification = editForm.alignment_justification || null
          if (editForm.readiness_justification !== (project.readiness_justification || '')) updateData.readiness_justification = editForm.readiness_justification || null
          break

        case 'description':
          if (editForm.description !== (project.description || '')) updateData.description = editForm.description || null
          if (editForm.department !== (project.department || '')) updateData.department = editForm.department || null
          break

        case 'states':
          if (editForm.current_state !== (project.current_state || '')) updateData.current_state = editForm.current_state || null
          if (editForm.desired_state !== (project.desired_state || '')) updateData.desired_state = editForm.desired_state || null
          break

        case 'next_step':
          if (editForm.next_step !== (project.next_step || '')) updateData.next_step = editForm.next_step || null
          break
      }

      if (Object.keys(updateData).length === 0) {
        setEditingSection(null)
        setIsSaving(false)
        return
      }

      const updated = await apiPatch<Project>(`/api/projects/${project.id}`, updateData)
      setProject(updated)
      onProjectUpdated?.(updated)
      setEditingSection(null)
    } catch (error) {
      console.error('Failed to save project:', error)
      alert('Failed to save changes. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleProjectNameSubmit = async (projectName: string, projectDescription?: string) => {
    if (!pendingStatus) return

    try {
      // Update status with project name
      const updated = await apiPatch<Project>(`/api/projects/${project.id}/status`, {
        status: pendingStatus,
        project_name: projectName,
        project_description: projectDescription,
      })
      setProject(updated)
      onProjectUpdated?.(updated)
      setShowProjectNameModal(false)
      setPendingStatus(null)
      setEditingSection(null)

      // Switch to Tasks tab and trigger Taskmaster auto-generation
      setActiveTab('tasks')
      setShouldAutoGenerateTasks(true)
    } catch (error) {
      console.error('Failed to update status:', error)
      alert('Failed to update status. Please try again.')
    }
  }

  const handleConvertToProject = () => {
    // Trigger the project name modal for "Start as Active Project"
    setPendingStatus('active')
    setShowProjectNameModal(true)
  }

  const handleEditFormChange = (field: keyof EditFormState, value: string | number | null) => {
    setEditForm(prev => ({ ...prev, [field]: value }))
  }

  // Check if there are unsaved changes in the current editing section
  const checkForUnsavedChanges = (): boolean => {
    if (!editingSection) return false

    switch (editingSection) {
      case 'header':
        return editForm.title !== project.title || editForm.status !== project.status
      case 'scores':
        return (
          editForm.roi_potential !== project.roi_potential ||
          editForm.implementation_effort !== project.implementation_effort ||
          editForm.strategic_alignment !== project.strategic_alignment ||
          editForm.stakeholder_readiness !== project.stakeholder_readiness
        )
      case 'justifications':
        return (
          editForm.project_summary !== (project.project_summary || '') ||
          editForm.roi_justification !== (project.roi_justification || '') ||
          editForm.effort_justification !== (project.effort_justification || '') ||
          editForm.alignment_justification !== (project.alignment_justification || '') ||
          editForm.readiness_justification !== (project.readiness_justification || '')
        )
      case 'description':
        return (
          editForm.description !== (project.description || '') ||
          editForm.department !== (project.department || '')
        )
      case 'states':
        return (
          editForm.current_state !== (project.current_state || '') ||
          editForm.desired_state !== (project.desired_state || '')
        )
      case 'next_step':
        return editForm.next_step !== (project.next_step || '')
      default:
        return false
    }
  }

  // Check if justifications exist
  const hasJustifications = !!(
    project.project_summary ||
    project.roi_justification ||
    project.effort_justification ||
    project.alignment_justification ||
    project.readiness_justification
  )

  // When not open but still mounted, render invisible overlay to absorb stray clicks
  if (!open) {
    const blocker = <div className="fixed inset-0 z-50" onClick={(e) => e.stopPropagation()} />
    if (typeof document === 'undefined') return blocker
    return createPortal(blocker, document.body)
  }

  const statusConfig = STATUS_CONFIG[project.status] || STATUS_CONFIG.backlog
  const tierConfig = TIER_CONFIG[project.tier as keyof typeof TIER_CONFIG] || TIER_CONFIG[4]

  const modalContent = (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal - Fixed large size */}
      <div className="relative bg-card border border-default rounded-xl shadow-2xl w-full max-w-[1400px] h-[90vh] flex flex-col mx-4" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-default group">
          <div className="flex-1 min-w-0 mr-4 overflow-hidden">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-mono font-bold text-muted">
                {project.project_code || project.opportunity_code}
              </span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${tierConfig.color}`}>
                Tier {project.tier}
              </span>
              <select
                value={project.status}
                onChange={async (e) => {
                  const newStatus = e.target.value
                  try {
                    await apiPatch(`/api/projects/${project.id}`, { status: newStatus })
                    setProject(prev => ({ ...prev, status: newStatus }))
                    setEditForm(prev => ({ ...prev, status: newStatus }))
                    onProjectUpdated?.({ ...project, status: newStatus })
                  } catch (error) {
                    console.error('Failed to update status:', error)
                  }
                }}
                className={`px-2 py-0.5 rounded text-xs font-medium border border-transparent hover:border-default bg-transparent cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 ${statusConfig.color}`}
              >
                {STATUS_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              {project.project_name && (
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                  Active: {project.project_name}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {editingSection === 'header' ? (
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) => handleEditFormChange('title', e.target.value)}
                  className="text-xl font-semibold text-primary bg-transparent border-b border-blue-500 focus:outline-none flex-1"
                  placeholder="Project title"
                />
              ) : (
                <h2 className="text-xl font-semibold text-primary truncate flex-1">
                  {project.title}
                </h2>
              )}
              {editingSection !== 'header' && (
                <button
                  onClick={() => setEditingSection('header')}
                  className="p-1 text-muted hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Edit title and status"
                >
                  <Pencil className="w-4 h-4" />
                </button>
              )}
            </div>
            {project.owner_name && editingSection !== 'header' && (
              <p className="text-sm text-muted flex items-center gap-1 mt-1">
                <User className="w-3 h-3" />
                {project.owner_name}
                {project.department && (
                  <>
                    <span className="mx-1">|</span>
                    <Building2 className="w-3 h-3" />
                    {project.department}
                  </>
                )}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0 relative z-20">
            <button
              onClick={() => {
                onClose()
                router.push(`/chat?project_id=${project.id}`)
              }}
              className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors flex items-center gap-1.5"
              title="Chat with this Project"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Chat
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onClose(); }}
              className="p-3 text-muted hover:text-primary hover:bg-hover rounded-lg transition-colors relative z-20 cursor-pointer"
              title="Close"
              aria-label="Close modal"
            >
              <X className="w-6 h-6 pointer-events-none" />
            </button>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="flex border-b border-default px-6 bg-hover/30">
          {[
            { id: 'details' as const, label: 'Details', icon: FileText },
            { id: 'scores' as const, label: 'Scores', icon: Target },
            { id: 'confidence' as const, label: 'Confidence', icon: Gauge },
            { id: 'alignment' as const, label: 'Alignment', icon: Target },
            { id: 'tasks' as const, label: 'Tasks', icon: ListTodo },
            { id: 'graph' as const, label: 'Graph', icon: Network },
            { id: 'documents' as const, label: 'Documents', icon: Link },
            { id: 'disco' as const, label: 'DISCO', icon: Compass },
            { id: 'kraken-guide' as const, label: 'Kraken Guide', icon: Zap },
            { id: 'scoring-guide' as const, label: 'Scoring Guide', icon: Target },
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

        {/* Content - Scrollable with min height to prevent shrinking */}
        <div className="flex-1 overflow-y-auto p-6 min-h-0">
          {/* SCORES TAB */}
          {activeTab === 'scores' && (
            <div className="space-y-8">
              {/* Score Values Section */}
              <section className="group">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Scores (1-5)
                  </h3>
                  {editingSection !== 'scores' && (
                    <button
                      onClick={() => setEditingSection('scores')}
                      className="flex items-center gap-1 px-2 py-1 text-xs text-muted hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Edit scores"
                    >
                      <Pencil className="w-3 h-3" />
                      Edit
                    </button>
                  )}
                </div>

                {editingSection === 'scores' ? (
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
                ) : (
                  <ScoreJustification
                    roiPotential={project.roi_potential}
                    implementationEffort={project.implementation_effort}
                    strategicAlignment={project.strategic_alignment}
                    stakeholderReadiness={project.stakeholder_readiness}
                    totalScore={project.total_score}
                    tier={project.tier}
                    opportunityDescription={project.project_summary || undefined}
                    dimensionJustifications={{
                      roi_potential: project.roi_justification || undefined,
                      implementation_effort: project.effort_justification || undefined,
                      strategic_alignment: project.alignment_justification || undefined,
                      stakeholder_readiness: project.readiness_justification || undefined,
                    }}
                  />
                )}
              </section>

              {/* AI Readiness Section (Kraken Agenticity) */}
              <section>
                <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2 mb-3">
                  <Zap className="w-4 h-4" />
                  AI Readiness
                </h3>
                {project.agenticity_score != null ? (
                  <div className="p-4 bg-violet-50 dark:bg-violet-900/10 border border-violet-200 dark:border-violet-800 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-bold text-violet-700 dark:text-violet-400">
                            {project.agenticity_score.toFixed(0)}%
                          </span>
                          <span className="text-sm text-violet-600 dark:text-violet-400">Agenticity Score</span>
                        </div>
                        <p className="text-xs text-muted mt-1">
                          Percentage of project tasks that can be automated by AI
                        </p>
                      </div>
                      {project.agenticity_evaluated_at && (
                        <span className="text-xs text-muted">
                          Evaluated {new Date(project.agenticity_evaluated_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    {/* Progress bar */}
                    <div className="mt-3 w-full bg-violet-200 dark:bg-violet-800 rounded-full h-2">
                      <div
                        className="bg-violet-600 dark:bg-violet-400 h-2 rounded-full transition-all"
                        style={{ width: `${Math.min(100, project.agenticity_score)}%` }}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 border border-dashed border-default rounded-lg">
                    <Zap className="w-5 h-5 mx-auto text-muted mb-1" />
                    <p className="text-xs text-muted">
                      No agenticity score yet. Evaluate tasks from the Tasks tab.
                    </p>
                  </div>
                )}
              </section>

              {/* Justifications Section */}
              <section className="group">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Score Justifications
                  </h3>
                  <div className="flex items-center gap-2">
                    {editingSection !== 'justifications' && (
                      <>
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
                              {hasJustifications ? 'Regenerate' : 'Generate'} AI Analysis
                            </>
                          )}
                        </button>
                        <button
                          onClick={() => setEditingSection('justifications')}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-muted hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Edit justifications"
                        >
                          <Pencil className="w-3 h-3" />
                          Edit
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {editingSection === 'justifications' ? (
                  <div className="space-y-4">
                    <div>
                      <label className="text-xs font-medium text-muted uppercase block mb-1">
                        Opportunity Summary
                      </label>
                      <textarea
                        value={editForm.project_summary}
                        onChange={(e) => handleEditFormChange('project_summary', e.target.value)}
                        rows={3}
                        className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        placeholder="Summary of the project and its potential business impact..."
                      />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-medium text-muted uppercase block mb-1">
                          ROI Potential Justification
                        </label>
                        <textarea
                          value={editForm.roi_justification}
                          onChange={(e) => handleEditFormChange('roi_justification', e.target.value)}
                          rows={3}
                          className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                          placeholder="Why this ROI score?"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-muted uppercase block mb-1">
                          Effort Justification
                        </label>
                        <textarea
                          value={editForm.effort_justification}
                          onChange={(e) => handleEditFormChange('effort_justification', e.target.value)}
                          rows={3}
                          className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                          placeholder="Why this effort score?"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-muted uppercase block mb-1">
                          Strategic Alignment Justification
                        </label>
                        <textarea
                          value={editForm.alignment_justification}
                          onChange={(e) => handleEditFormChange('alignment_justification', e.target.value)}
                          rows={3}
                          className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                          placeholder="Why this alignment score?"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-muted uppercase block mb-1">
                          Stakeholder Readiness Justification
                        </label>
                        <textarea
                          value={editForm.readiness_justification}
                          onChange={(e) => handleEditFormChange('readiness_justification', e.target.value)}
                          rows={3}
                          className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                          placeholder="Why this readiness score?"
                        />
                      </div>
                    </div>
                  </div>
                ) : !hasJustifications ? (
                  <div className="text-center py-8 border border-dashed border-default rounded-lg">
                    <FileText className="w-8 h-8 mx-auto text-muted mb-2" />
                    <p className="text-sm text-muted">No justifications yet.</p>
                    <p className="text-xs text-muted mt-1">Click &quot;Generate AI Analysis&quot; to auto-generate, or &quot;Edit&quot; to write your own.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {project.project_summary && (
                      <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <p className="text-sm text-secondary">{project.project_summary}</p>
                      </div>
                    )}
                  </div>
                )}
              </section>
            </div>
          )}

          {/* CONFIDENCE TAB */}
          {activeTab === 'confidence' && (
            <div className="space-y-6">
              {(project.scoring_confidence !== null && project.scoring_confidence !== undefined) ? (
                <>
                  {/* Confidence Meter */}
                  <section>
                    <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4 flex items-center gap-2">
                      <Gauge className="w-4 h-4" />
                      Scoring Confidence
                    </h3>
                    <div className="bg-card border border-default rounded-lg p-6">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-lg text-secondary">Confidence Level</span>
                        <span className={`text-3xl font-bold ${
                          project.scoring_confidence >= 80 ? 'text-green-600 dark:text-green-400' :
                          project.scoring_confidence >= 60 ? 'text-blue-600 dark:text-blue-400' :
                          project.scoring_confidence >= 40 ? 'text-amber-600 dark:text-amber-400' :
                          'text-red-600 dark:text-red-400'
                        }`}>
                          {project.scoring_confidence}%
                        </span>
                      </div>
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            project.scoring_confidence >= 80 ? 'bg-green-500' :
                            project.scoring_confidence >= 60 ? 'bg-blue-500' :
                            project.scoring_confidence >= 40 ? 'bg-amber-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${project.scoring_confidence}%` }}
                        />
                      </div>
                      <p className="text-sm text-muted mt-3">
                        {project.scoring_confidence >= 80 ? 'High confidence - scores are well-supported by available information' :
                         project.scoring_confidence >= 60 ? 'Moderate confidence - some assumptions were made based on limited data' :
                         project.scoring_confidence >= 40 ? 'Low confidence - significant unknowns remain in the scoring' :
                         'Very low confidence - scores are mostly speculative due to lack of information'}
                      </p>
                    </div>
                  </section>

                  {/* Questions to Raise Confidence */}
                  {project.confidence_questions && project.confidence_questions.length > 0 && (
                    <section>
                      <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4 flex items-center gap-2">
                        <HelpCircle className="w-4 h-4" />
                        Questions to Raise Confidence
                      </h3>
                      <div className="space-y-3">
                        {project.confidence_questions.map((question, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-lg"
                          >
                            <span className="flex-shrink-0 w-6 h-6 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full flex items-center justify-center text-sm font-medium">
                              {i + 1}
                            </span>
                            <span className="text-sm text-secondary">{question}</span>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-muted mt-4">
                        Answering these questions through research, stakeholder interviews, or discovery sessions would help refine the scoring accuracy.
                      </p>
                    </section>
                  )}
                </>
              ) : (
                <div className="text-center py-12 border border-dashed border-default rounded-lg">
                  <Gauge className="w-12 h-12 mx-auto text-muted mb-3" />
                  <h3 className="text-lg font-medium text-primary mb-2">No Confidence Data</h3>
                  <p className="text-sm text-muted max-w-md mx-auto">
                    Confidence scoring has not been generated for this project yet.
                    Generate AI analysis on the Scores tab to evaluate confidence levels.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ALIGNMENT TAB */}
          {activeTab === 'alignment' && (
            <GoalAlignmentSection
              projectId={project.id}
              goalAlignmentScore={project.goal_alignment_score ?? null}
              goalAlignmentDetails={project.goal_alignment_details ?? null}
              onAnalyze={handleAnalyzeGoalAlignment}
              onDetailsUpdated={handleAlignmentDetailsUpdated}
              canEdit
            />
          )}

          {/* DETAILS TAB */}
          {activeTab === 'details' && (
            <div className="space-y-6">
              {/* Linked Initiatives */}
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                    <Compass className="w-4 h-4" />
                    Linked Initiatives
                    {linkedInitiatives.length > 0 && (
                      <span className="text-xs font-normal">({linkedInitiatives.length})</span>
                    )}
                  </h3>
                  {editingInitiatives ? (
                    <div className="flex items-center gap-1">
                      <button
                        onClick={handleSaveInitiatives}
                        disabled={isSaving}
                        className="flex items-center gap-1 px-2 py-1 text-xs text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                      >
                        {isSaving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setEditingInitiatives(false)
                          setSelectedInitiativeIds(project.initiative_ids || [])
                        }}
                        className="flex items-center gap-1 px-2 py-1 text-xs text-muted hover:bg-hover rounded"
                      >
                        <XCircle className="w-3 h-3" />
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setEditingInitiatives(true)}
                      className="flex items-center gap-1 px-2 py-1 text-xs text-muted hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                      title="Edit linked initiatives"
                    >
                      <Pencil className="w-3 h-3" />
                      Edit
                    </button>
                  )}
                </div>

                {initiativesLoading ? (
                  <div className="flex items-center gap-2 text-muted py-4">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Loading initiatives...</span>
                  </div>
                ) : editingInitiatives ? (
                  <div className="space-y-2">
                    {availableInitiatives.length === 0 ? (
                      <p className="text-sm text-muted py-4">No initiatives available.</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                        {availableInitiatives.map((initiative) => (
                          <label
                            key={initiative.id}
                            className={`flex items-center gap-2 p-2 border rounded-lg cursor-pointer transition-colors ${
                              selectedInitiativeIds.includes(initiative.id)
                                ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                                : 'border-default hover:bg-hover'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={selectedInitiativeIds.includes(initiative.id)}
                              onChange={() => toggleInitiative(initiative.id)}
                              className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                            />
                            <span className="text-sm text-primary truncate">{initiative.name}</span>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                ) : linkedInitiatives.length === 0 ? (
                  <p className="text-sm text-muted py-4">
                    No initiatives linked. Click Edit to connect this project to DISCo initiatives.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {linkedInitiatives.map((initiative) => (
                      <a
                        key={initiative.id}
                        href={`/disco/${initiative.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-sm hover:bg-indigo-200 dark:hover:bg-indigo-900/50 transition-colors"
                      >
                        <Compass className="w-3.5 h-3.5" />
                        {initiative.name}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ))}
                  </div>
                )}
              </section>

              {/* Description & Department Section */}
              <section className="group">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Description
                  </h3>
                  {editingSection !== 'description' && (
                    <button
                      onClick={() => setEditingSection('description')}
                      className="flex items-center gap-1 px-2 py-1 text-xs text-muted hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Edit description"
                    >
                      <Pencil className="w-3 h-3" />
                      Edit
                    </button>
                  )}
                </div>

                {editingSection === 'description' ? (
                  <div className="space-y-4">
                    <div>
                      <label className="text-xs font-medium text-muted uppercase block mb-1">Department</label>
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
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted uppercase block mb-1">Description</label>
                      <textarea
                        value={editForm.description}
                        onChange={(e) => handleEditFormChange('description', e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        placeholder="Describe the project..."
                      />
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {project.department && (
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-muted" />
                        <span className="text-sm text-secondary">{project.department}</span>
                      </div>
                    )}
                    {project.description ? (
                      <p className="text-sm text-secondary whitespace-pre-wrap">{project.description}</p>
                    ) : (
                      <p className="text-sm text-muted italic">No description provided. Click Edit to add one.</p>
                    )}
                  </div>
                )}
              </section>

              {/* Current/Desired State Section */}
              <section className="group">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Current vs. Desired State
                  </h3>
                  {editingSection !== 'states' && (
                    <button
                      onClick={() => setEditingSection('states')}
                      className="flex items-center gap-1 px-2 py-1 text-xs text-muted hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Edit states"
                    >
                      <Pencil className="w-3 h-3" />
                      Edit
                    </button>
                  )}
                </div>

                {editingSection === 'states' ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-medium text-muted uppercase block mb-1">Current State</label>
                      <textarea
                        value={editForm.current_state}
                        onChange={(e) => handleEditFormChange('current_state', e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        placeholder="Describe the current state..."
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted uppercase block mb-1">Desired State</label>
                      <textarea
                        value={editForm.desired_state}
                        onChange={(e) => handleEditFormChange('desired_state', e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        placeholder="Describe the desired state..."
                      />
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 bg-red-50 dark:bg-red-900/10 rounded-lg">
                      <h4 className="text-xs font-medium text-red-600 dark:text-red-400 uppercase mb-1">
                        Current State
                      </h4>
                      {project.current_state ? (
                        <p className="text-sm text-secondary">{project.current_state}</p>
                      ) : (
                        <p className="text-sm text-muted italic">Not defined</p>
                      )}
                    </div>
                    <div className="p-3 bg-green-50 dark:bg-green-900/10 rounded-lg">
                      <h4 className="text-xs font-medium text-green-600 dark:text-green-400 uppercase mb-1">
                        Desired State
                      </h4>
                      {project.desired_state ? (
                        <p className="text-sm text-secondary">{project.desired_state}</p>
                      ) : (
                        <p className="text-sm text-muted italic">Not defined</p>
                      )}
                    </div>
                  </div>
                )}
              </section>

              {/* Next Step Section */}
              <section className="group">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                    <ChevronRight className="w-4 h-4" />
                    Next Step
                  </h3>
                  {editingSection !== 'next_step' && (
                    <button
                      onClick={() => setEditingSection('next_step')}
                      className="flex items-center gap-1 px-2 py-1 text-xs text-muted hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Edit next step"
                    >
                      <Pencil className="w-3 h-3" />
                      Edit
                    </button>
                  )}
                </div>

                {editingSection === 'next_step' ? (
                  <textarea
                    value={editForm.next_step}
                    onChange={(e) => handleEditFormChange('next_step', e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    placeholder="What's the next step?"
                  />
                ) : project.next_step ? (
                  <p className="text-sm text-secondary">{project.next_step}</p>
                ) : (
                  <p className="text-sm text-muted italic">No next step defined. Click Edit to add one.</p>
                )}
              </section>

              {/* Blockers Section (read-only) */}
              {project.blockers.length > 0 && (
                <section>
                  <h3 className="text-sm font-medium text-red-500 uppercase tracking-wide mb-3 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Blockers
                  </h3>
                  <ul className="text-sm text-secondary list-disc list-inside space-y-1">
                    {project.blockers.map((blocker, i) => (
                      <li key={i}>{blocker}</li>
                    ))}
                  </ul>
                </section>
              )}

              {/* ROI Indicators Section (read-only) */}
              {Object.keys(project.roi_indicators).length > 0 && (
                <section>
                  <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-3">
                    ROI Indicators
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(project.roi_indicators).map(([key, value]) => (
                      <span
                        key={key}
                        className="px-2 py-1 bg-hover rounded text-xs text-secondary"
                      >
                        {key.replace(/_/g, ' ')}: {String(value)}
                      </span>
                    ))}
                  </div>
                </section>
              )}

            </div>
          )}

          {/* TASKS TAB */}
          {activeTab === 'tasks' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                  <ListTodo className="w-4 h-4" />
                  Project Tasks
                  {projectTasks.length > 0 && (
                    <span className="text-xs font-normal">({projectTasks.length})</span>
                  )}
                </h3>
                <div className="flex items-center gap-3">
                  {tasksGeneratedCount !== null && (
                    <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                      {tasksGeneratedCount} tasks created
                    </span>
                  )}
                  {(project.project_name || project.status === 'active') && (
                    <button
                      onClick={handleGenerateTasks}
                      disabled={generatingTasks}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-200 dark:border-amber-800 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/50 transition-colors disabled:opacity-50"
                    >
                      {generatingTasks ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Zap className="w-3.5 h-3.5" />
                      )}
                      {generatingTasks ? 'Generating...' : 'Generate Tasks'}
                    </button>
                  )}
                  <a
                    href={`/tasks?project=${project.id}`}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 transition-colors"
                  >
                    View and Edit Tasks
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>

              {tasksLoading ? (
                <div className="flex items-center gap-2 text-muted py-8">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Loading tasks...</span>
                </div>
              ) : projectTasks.length === 0 ? (
                <div className="text-center py-12 border border-dashed border-default rounded-lg">
                  <ListTodo className="w-8 h-8 mx-auto text-muted mb-2" />
                  <p className="text-sm text-muted">No tasks linked to this project yet.</p>
                  <p className="text-xs text-muted mt-1">
                    {(project.project_name || project.status === 'active')
                      ? 'Use the Generate Tasks button above to break this project into actionable tasks.'
                      : 'Activate this project first, then use Generate Tasks to create a task breakdown.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {projectTasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center gap-3 p-3 border border-default rounded-lg hover:bg-hover transition-colors"
                    >
                      {/* Status indicator */}
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        task.status === 'completed' ? 'bg-green-500' :
                        task.status === 'in_progress' ? 'bg-blue-500' :
                        task.status === 'blocked' ? 'bg-orange-500' :
                        'bg-gray-400'
                      }`} />

                      {/* Task details */}
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium truncate ${
                          task.status === 'completed' ? 'text-muted line-through' : 'text-primary'
                        }`}>
                          {task.title}
                        </p>
                        {(task.assignee_name || task.due_date) && (
                          <p className="text-xs text-muted flex items-center gap-2 mt-0.5">
                            {task.assignee_name && <span>{task.assignee_name}</span>}
                            {task.assignee_name && task.due_date && <span>•</span>}
                            {task.due_date && <span>Due {new Date(task.due_date).toLocaleDateString()}</span>}
                          </p>
                        )}
                      </div>

                      {/* Priority badge */}
                      <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${
                        task.priority >= 4 ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                        task.priority === 3 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                        'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                      }`}>
                        {task.priority >= 4 ? 'High' : task.priority === 3 ? 'Med' : 'Low'}
                      </span>

                      {/* Status badge */}
                      <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${
                        task.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                        task.status === 'in_progress' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                        task.status === 'blocked' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                        'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                      }`}>
                        {task.status === 'in_progress' ? 'In Progress' :
                         task.status.charAt(0).toUpperCase() + task.status.slice(1)}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Kraken Task Evaluator */}
              {projectTasks.length > 0 && (
                <KrakenPanel
                  projectId={project.id}
                  taskCount={projectTasks.length}
                  taskIds={projectTasks.map(t => t.id)}
                  onTasksUpdated={fetchProjectTasks}
                />
              )}
            </div>
          )}

          {/* GRAPH TAB */}
          {activeTab === 'graph' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                  <Network className="w-4 h-4" />
                  Task Dependency Graph
                </h3>
              </div>
              {tasksLoading ? (
                <div className="flex items-center gap-2 text-muted py-8">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Loading tasks...</span>
                </div>
              ) : (
                <TaskDependencyGraph
                  tasks={projectTasks as TaskGraphNode[]}
                  currentUserId={profile?.id}
                  currentUserName={profile?.name}
                  onTaskClick={(taskId) => {
                    window.open(`/tasks?project=${project.id}`, '_blank')
                  }}
                  height={450}
                  colorBy="status"
                />
              )}
            </div>
          )}

          {/* DOCUMENTS TAB */}
          {activeTab === 'documents' && (
            <div className="space-y-6">
              {/* Header with Link button */}
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-muted uppercase tracking-wide flex items-center gap-2">
                  <Link className="w-4 h-4" />
                  Linked Documents
                </h3>
                <div className="flex items-center gap-2">
                  {(project.initiative_ids?.length ?? 0) > 0 && (
                    <button
                      onClick={handleShowInitiativeDocPicker}
                      className="flex items-center gap-2 px-3 py-1.5 text-sm border border-indigo-300 dark:border-indigo-700 text-indigo-600 dark:text-indigo-400 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      Link from Initiative
                    </button>
                  )}
                  <button
                    onClick={() => setShowDocumentBrowser(true)}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    Link from KB
                  </button>
                </div>
              </div>

              {/* Initiative Document Picker */}
              {showInitiativeDocPicker && (
                <div className="border border-indigo-200 dark:border-indigo-800 rounded-lg bg-indigo-50/50 dark:bg-indigo-900/10">
                  <div className="flex items-center justify-between p-3 border-b border-indigo-200 dark:border-indigo-800">
                    <span className="text-sm font-medium text-primary">Select initiative documents to link</span>
                    <button
                      onClick={() => { setShowInitiativeDocPicker(false); setSelectedInitiativeDocIds([]) }}
                      className="p-1 text-muted hover:text-primary rounded"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  {initiativeDocsLoading ? (
                    <div className="flex items-center justify-center py-6">
                      <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
                    </div>
                  ) : initiativeDocs.length === 0 ? (
                    <div className="text-center py-6 text-sm text-muted">
                      No additional initiative documents to link. All are already linked to this project.
                    </div>
                  ) : (
                    <>
                      <div className="max-h-64 overflow-y-auto p-2 space-y-1">
                        <label className="flex items-center gap-2 px-2 py-1 text-xs text-muted cursor-pointer hover:bg-indigo-100 dark:hover:bg-indigo-900/20 rounded">
                          <input
                            type="checkbox"
                            checked={selectedInitiativeDocIds.length === initiativeDocs.length}
                            onChange={(e) => {
                              setSelectedInitiativeDocIds(e.target.checked ? initiativeDocs.map(d => d.id) : [])
                            }}
                            className="rounded border-gray-300 text-indigo-600"
                          />
                          Select all ({initiativeDocs.length})
                        </label>
                        <div className="border-t border-indigo-200 dark:border-indigo-800 my-1" />
                        {initiativeDocs.map(doc => (
                          <label
                            key={doc.id}
                            className="flex items-center gap-2 px-2 py-1.5 text-sm text-primary cursor-pointer hover:bg-indigo-100 dark:hover:bg-indigo-900/20 rounded"
                          >
                            <input
                              type="checkbox"
                              checked={selectedInitiativeDocIds.includes(doc.id)}
                              onChange={(e) => {
                                setSelectedInitiativeDocIds(prev =>
                                  e.target.checked
                                    ? [...prev, doc.id]
                                    : prev.filter(id => id !== doc.id)
                                )
                              }}
                              className="rounded border-gray-300 text-indigo-600"
                            />
                            <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                            <span className="truncate">{doc.title || doc.filename}</span>
                          </label>
                        ))}
                      </div>
                      <div className="flex items-center justify-between p-3 border-t border-indigo-200 dark:border-indigo-800">
                        <span className="text-xs text-muted">
                          {selectedInitiativeDocIds.length} of {initiativeDocs.length} selected
                        </span>
                        <button
                          onClick={handleLinkSelectedInitiativeDocs}
                          disabled={selectedInitiativeDocIds.length === 0 || linkingInitiativeDocs}
                          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                        >
                          {linkingInitiativeDocs ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Plus className="w-4 h-4" />
                          )}
                          Link Selected
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Loading state */}
              {linkedDocsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
                </div>
              ) : linkedDocuments.length === 0 ? (
                <div className="text-center py-12 border border-dashed border-slate-300 dark:border-slate-600 rounded-lg">
                  <FileText className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
                  <p className="text-sm text-muted">No documents linked yet</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Click &quot;Link from KB&quot; to attach relevant documents
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {linkedDocuments.map(doc => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <FileText className="w-5 h-5 text-slate-400 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="font-medium text-primary truncate">
                            {doc.title || doc.document_name}
                          </p>
                          <p className="text-xs text-muted">
                            Linked {new Date(doc.linked_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setViewingDocument({
                              document_id: doc.document_id,
                              document_name: doc.document_name
                            })
                          }}
                          className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors"
                          title="View document"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleUnlinkDocument(doc.document_id)}
                          disabled={unlinkingDocId === doc.document_id}
                          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors disabled:opacity-50"
                          title="Unlink document"
                        >
                          {unlinkingDocId === doc.document_id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Unlink className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Note about auto-discovered documents */}
              <p className="text-xs text-slate-400 border-t border-slate-200 dark:border-slate-700 pt-4">
                These are documents you&apos;ve manually linked to this project.
              </p>
            </div>
          )}

          {/* DISCO TAB */}
          {activeTab === 'disco' && (
            <ProjectAgentPanel projectId={project.id} />
          )}

          {/* KRAKEN GUIDE TAB */}
          {activeTab === 'kraken-guide' && (
            <div className="overflow-hidden rounded-lg border border-default" style={{ height: 'calc(100vh - 320px)' }}>
              <iframe
                src="/kraken-process-map.html"
                className="w-full h-full border-0"
                title="Kraken Task Automation Process Map"
              />
            </div>
          )}

          {/* SCORING GUIDE TAB */}
          {activeTab === 'scoring-guide' && (
            <div className="overflow-hidden rounded-lg border border-default" style={{ height: 'calc(100vh - 320px)' }}>
              <iframe
                src="/project-scoring-map.html"
                className="w-full h-full border-0"
                title="Project Scoring and Lifecycle Guide"
              />
            </div>
          )}

        </div>

        {/* Footer - shows Save/Cancel when editing */}
        {editingSection && (
          <div className="flex items-center justify-end gap-3 p-4 border-t border-default">
            <button
              onClick={() => {
                // Check if there are unsaved changes
                const hasChanges = checkForUnsavedChanges()
                if (hasChanges) {
                  if (window.confirm('You have unsaved changes. Are you sure you want to cancel?')) {
                    setEditingSection(null)
                  }
                } else {
                  setEditingSection(null)
                }
              }}
              className="px-4 py-2 text-secondary hover:text-primary hover:bg-hover rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => handleSaveSection(editingSection)}
              disabled={isSaving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Save Changes
            </button>
          </div>
        )}
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
        projectTitle={project.title}
        existingProjectName={project.project_name}
        existingProjectDescription={project.project_description || project.description}
        newStatus={pendingStatus || 'active'}
      />

      {/* Document Browser Modal */}
      <ProjectDocumentBrowser
        projectId={project.id}
        projectTitle={project.title}
        isOpen={showDocumentBrowser}
        onClose={() => setShowDocumentBrowser(false)}
        onLinked={handleDocumentsLinked}
      />
    </div>
  )

  if (typeof document === 'undefined') return modalContent
  return createPortal(modalContent, document.body)
}
