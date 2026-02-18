'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  X,
  Loader2,
  FolderPlus,
  AlertCircle,
  Sparkles,
  ExternalLink,
  CheckSquare,
  Square
} from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'
import toast from 'react-hot-toast'

// ============================================================================
// TYPES
// ============================================================================

interface ExtractedField {
  value: string | null
  confidence: 'high' | 'medium' | 'low' | 'none'
}

interface ExtractedScore {
  value: number | null
  confidence: 'high' | 'medium' | 'low' | 'none'
}

interface ExtractedTask {
  title: string
  description?: string
  priority: 'low' | 'medium' | 'high'
}

interface ExtractedData {
  title: ExtractedField
  description: ExtractedField
  department: ExtractedField
  current_state: ExtractedField
  desired_state: ExtractedField
  roi_potential: ExtractedScore
  implementation_effort: ExtractedScore
  strategic_alignment: ExtractedScore
  stakeholder_readiness: ExtractedScore
}

interface ExtractionResponse {
  success: boolean
  extracted?: ExtractedData
  tasks?: ExtractedTask[]
  source_context?: string
  initiative_id?: string
  initiative_name?: string
  error?: string
}

interface CreateProjectFromChatModalProps {
  open: boolean
  onClose: () => void
  initiativeId: string
  initiativeName: string
}

// ============================================================================
// CONSTANTS
// ============================================================================

const DEPARTMENTS = [
  { value: 'finance', label: 'Finance' },
  { value: 'legal', label: 'Legal' },
  { value: 'people', label: 'People' },
  { value: 'it', label: 'IT' },
  { value: 'is', label: 'IS' },
  { value: 'revops', label: 'RevOps' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'sales', label: 'Sales' },
  { value: 'operations', label: 'Operations' },
]

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function generateProjectCode(department: string): string {
  // Generate a code like F01, L01, etc. based on department
  const prefixMap: Record<string, string> = {
    finance: 'F',
    legal: 'L',
    people: 'P',
    it: 'IT',
    revops: 'RO',
    marketing: 'M',
    sales: 'S',
    operations: 'OP',
  }
  const prefix = prefixMap[department?.toLowerCase()] || 'P'
  // Add random 2-digit number to avoid collisions
  const num = Math.floor(Math.random() * 99) + 1
  return `${prefix}${num.toString().padStart(2, '0')}`
}

function needsAttention(confidence: string): boolean {
  return confidence === 'none' || confidence === 'low'
}

// ============================================================================
// COMPONENTS
// ============================================================================

function ScoreInput({
  label,
  description,
  value,
  onChange,
  highlight,
}: {
  label: string
  description: string
  value: number
  onChange: (val: number) => void
  highlight?: boolean
}) {
  const getScoreColor = (v: number) => {
    if (v >= 4) return 'text-green-600 dark:text-green-400'
    if (v >= 3) return 'text-amber-600 dark:text-amber-400'
    return 'text-slate-500'
  }

  return (
    <div className={`p-3 rounded-lg ${highlight ? 'bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700' : 'bg-slate-50 dark:bg-slate-800/50'}`}>
      <div className="flex items-center justify-between mb-2">
        <div>
          <label className="font-medium text-sm text-slate-900 dark:text-slate-100">{label}</label>
          {highlight && (
            <span className="ml-2 text-xs text-amber-600 dark:text-amber-400">(needs input)</span>
          )}
        </div>
        <span className={`text-lg font-bold ${getScoreColor(value)}`}>{value}</span>
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">{description}</p>
      <input
        type="range"
        min="1"
        max="5"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
      />
      <div className="flex justify-between text-xs text-slate-400 mt-1">
        <span>1</span>
        <span>5</span>
      </div>
    </div>
  )
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function CreateProjectFromChatModal({
  open,
  onClose,
  initiativeId,
  initiativeName,
}: CreateProjectFromChatModalProps) {
  const router = useRouter()

  // Loading states
  const [extracting, setExtracting] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Extracted data tracking
  const [extractedConfidence, setExtractedConfidence] = useState<ExtractedData | null>(null)
  const [sourceContext, setSourceContext] = useState('')
  const [extractedTasks, setExtractedTasks] = useState<ExtractedTask[]>([])
  const [selectedTaskIndices, setSelectedTaskIndices] = useState<Set<number>>(new Set())

  // Form state
  const [projectCode, setProjectCode] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [department, setDepartment] = useState('')
  const [currentState, setCurrentState] = useState('')
  const [desiredState, setDesiredState] = useState('')
  const [roiPotential, setRoiPotential] = useState(3)
  const [implementationEffort, setImplementationEffort] = useState(3)
  const [strategicAlignment, setStrategicAlignment] = useState(3)
  const [stakeholderReadiness, setStakeholderReadiness] = useState(3)

  // Extract project data when modal opens
  useEffect(() => {
    if (!open) return

    const extractProject = async () => {
      setExtracting(true)
      setError(null)

      try {
        const result = await apiPost<ExtractionResponse>(
          `/api/disco/initiatives/${initiativeId}/extract-project`,
          {}
        )

        if (result.success && result.extracted) {
          const extracted = result.extracted
          setExtractedConfidence(extracted)
          setSourceContext(result.source_context || '')

          // Pre-fill form with extracted values
          if (extracted.title.value) setTitle(extracted.title.value)
          if (extracted.description.value) setDescription(extracted.description.value)
          if (extracted.department.value) setDepartment(extracted.department.value.toLowerCase())
          if (extracted.current_state.value) setCurrentState(extracted.current_state.value)
          if (extracted.desired_state.value) setDesiredState(extracted.desired_state.value)
          if (extracted.roi_potential.value) setRoiPotential(extracted.roi_potential.value)
          if (extracted.implementation_effort.value) setImplementationEffort(extracted.implementation_effort.value)
          if (extracted.strategic_alignment.value) setStrategicAlignment(extracted.strategic_alignment.value)
          if (extracted.stakeholder_readiness.value) setStakeholderReadiness(extracted.stakeholder_readiness.value)

          // Generate project code based on department
          const dept = extracted.department.value?.toLowerCase() || 'general'
          setProjectCode(generateProjectCode(dept))

          // Handle extracted tasks
          if (result.tasks && result.tasks.length > 0) {
            setExtractedTasks(result.tasks)
            // Select all tasks by default
            setSelectedTaskIndices(new Set(result.tasks.map((_, i) => i)))
          }
        } else {
          setError(result.error || 'Failed to extract project information')
        }
      } catch (err) {
        console.error('Failed to extract project:', err)
        setError(err instanceof Error ? err.message : 'Failed to analyze conversation')
      } finally {
        setExtracting(false)
      }
    }

    extractProject()
  }, [open, initiativeId])

  // Update project code when department changes
  useEffect(() => {
    if (department && !projectCode) {
      setProjectCode(generateProjectCode(department))
    }
  }, [department, projectCode])

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()

    // Validation
    if (!projectCode.trim()) {
      setError('Project code is required')
      return
    }
    if (!title.trim()) {
      setError('Title is required')
      return
    }
    if (!department) {
      setError('Department is required')
      return
    }

    setCreating(true)
    setError(null)

    try {
      const projectData = {
        project_code: projectCode.toUpperCase(),
        title: title.trim(),
        description: description.trim() || null,
        department,
        current_state: currentState.trim() || null,
        desired_state: desiredState.trim() || null,
        roi_potential: roiPotential,
        implementation_effort: implementationEffort,
        strategic_alignment: strategicAlignment,
        stakeholder_readiness: stakeholderReadiness,
        status: 'identified',
        source_type: 'initiative_chat',
        source_id: initiativeId,
        source_notes: sourceContext,
        initiative_ids: [initiativeId],  // Link to the source initiative
      }

      const result = await apiPost<{ id: string; project_code: string }>('/api/projects/', projectData)

      // Create selected tasks linked to the new project
      const tasksToCreate = extractedTasks.filter((_, i) => selectedTaskIndices.has(i))
      let tasksCreated = 0

      for (const task of tasksToCreate) {
        try {
          const priorityMap: Record<string, number> = { low: 2, medium: 3, high: 4 }
          await apiPost('/api/tasks', {
            title: task.title,
            description: task.description || null,
            priority: priorityMap[task.priority] || 3,
            related_project_id: result.id,
            status: 'pending',
          })
          tasksCreated++
        } catch (taskErr) {
          console.error('Failed to create task:', task.title, taskErr)
        }
      }

      const taskMessage = tasksCreated > 0 ? ` with ${tasksCreated} task${tasksCreated > 1 ? 's' : ''}` : ''
      toast.success(
        <div className="flex items-center gap-2">
          <span>Project {result.project_code} created{taskMessage}</span>
          <button
            onClick={() => router.push(`/projects?highlight=${result.id}`)}
            className="text-indigo-600 hover:text-indigo-700 underline"
          >
            View
          </button>
        </div>
      )
      onClose()
    } catch (err) {
      console.error('Failed to create project:', err)
      const errorMessage = err instanceof Error ? err.message : 'Failed to create project'
      if (errorMessage.includes('already exists')) {
        // Regenerate code and show error
        setProjectCode(generateProjectCode(department))
        setError('Project code already exists. A new code has been generated.')
      } else {
        setError(errorMessage)
      }
    } finally {
      setCreating(false)
    }
  }, [projectCode, title, description, department, currentState, desiredState, roiPotential, implementationEffort, strategicAlignment, stakeholderReadiness, initiativeId, sourceContext, extractedTasks, selectedTaskIndices, onClose, router])

  // Reset form when modal closes
  useEffect(() => {
    if (!open) {
      setProjectCode('')
      setTitle('')
      setDescription('')
      setDepartment('')
      setCurrentState('')
      setDesiredState('')
      setRoiPotential(3)
      setImplementationEffort(3)
      setStrategicAlignment(3)
      setStakeholderReadiness(3)
      setExtractedConfidence(null)
      setSourceContext('')
      setExtractedTasks([])
      setSelectedTaskIndices(new Set())
      setError(null)
    }
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2">
            <FolderPlus className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Create Project from Chat</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {extracting ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mb-4" />
              <p className="text-slate-600 dark:text-slate-400">Analyzing conversation...</p>
              <p className="text-sm text-slate-500 dark:text-slate-500 mt-1">
                Extracting project details from your chat
              </p>
            </div>
          ) : error && !extractedConfidence ? (
            <div className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="w-8 h-8 text-red-500 mb-4" />
              <p className="text-red-600 dark:text-red-400">{error}</p>
              <button
                onClick={onClose}
                className="mt-4 px-4 py-2 text-sm text-slate-600 hover:text-slate-800"
              >
                Close
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* AI Extraction Notice */}
              <div className="flex items-start gap-2 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg text-sm">
                <Sparkles className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-indigo-900 dark:text-indigo-200">
                    Fields have been pre-filled based on your conversation.
                  </p>
                  <p className="text-indigo-700 dark:text-indigo-300 mt-1">
                    Fields highlighted in yellow need your attention.
                  </p>
                </div>
              </div>

              {/* Error display */}
              {error && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                </div>
              )}

              {/* Project Code & Title */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-slate-900 dark:text-slate-100">
                    Project Code <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={projectCode}
                    onChange={(e) => setProjectCode(e.target.value.toUpperCase())}
                    placeholder="e.g., F01"
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-mono"
                    maxLength={10}
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-1 text-slate-900 dark:text-slate-100">
                    Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Project title"
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 ${
                      extractedConfidence && needsAttention(extractedConfidence.title.confidence)
                        ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/20'
                        : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700'
                    }`}
                  />
                </div>
              </div>

              {/* Department */}
              <div>
                <label className="block text-sm font-medium mb-1 text-slate-900 dark:text-slate-100">
                  Department <span className="text-red-500">*</span>
                </label>
                <select
                  value={department}
                  onChange={(e) => {
                    setDepartment(e.target.value)
                    if (!projectCode || projectCode === generateProjectCode(department)) {
                      setProjectCode(generateProjectCode(e.target.value))
                    }
                  }}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-slate-900 dark:text-slate-100 ${
                    extractedConfidence && needsAttention(extractedConfidence.department.confidence)
                      ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/20'
                      : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700'
                  }`}
                >
                  <option value="">Select department...</option>
                  {DEPARTMENTS.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium mb-1 text-slate-900 dark:text-slate-100">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What does this project aim to accomplish?"
                  rows={3}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 ${
                    extractedConfidence && needsAttention(extractedConfidence.description.confidence)
                      ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/20'
                      : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700'
                  }`}
                />
              </div>

              {/* Current & Desired State */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-slate-900 dark:text-slate-100">Current State</label>
                  <textarea
                    value={currentState}
                    onChange={(e) => setCurrentState(e.target.value)}
                    placeholder="Current situation/pain point"
                    rows={2}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 ${
                      extractedConfidence && needsAttention(extractedConfidence.current_state.confidence)
                        ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/20'
                        : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700'
                    }`}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-slate-900 dark:text-slate-100">Desired State</label>
                  <textarea
                    value={desiredState}
                    onChange={(e) => setDesiredState(e.target.value)}
                    placeholder="Target outcome/goal"
                    rows={2}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 ${
                      extractedConfidence && needsAttention(extractedConfidence.desired_state.confidence)
                        ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/20'
                        : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700'
                    }`}
                  />
                </div>
              </div>

              {/* Scores */}
              <div>
                <h3 className="text-sm font-medium mb-3 text-slate-900 dark:text-slate-100">Scoring (1-5)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <ScoreInput
                    label="ROI Potential"
                    description="Potential return on investment"
                    value={roiPotential}
                    onChange={setRoiPotential}
                    highlight={extractedConfidence ? needsAttention(extractedConfidence.roi_potential.confidence) : false}
                  />
                  <ScoreInput
                    label="Implementation Effort"
                    description="Ease of implementation (5 = easiest)"
                    value={implementationEffort}
                    onChange={setImplementationEffort}
                    highlight={extractedConfidence ? needsAttention(extractedConfidence.implementation_effort.confidence) : false}
                  />
                  <ScoreInput
                    label="Strategic Alignment"
                    description="Alignment with business goals"
                    value={strategicAlignment}
                    onChange={setStrategicAlignment}
                    highlight={extractedConfidence ? needsAttention(extractedConfidence.strategic_alignment.confidence) : false}
                  />
                  <ScoreInput
                    label="Stakeholder Readiness"
                    description="Stakeholder buy-in and readiness"
                    value={stakeholderReadiness}
                    onChange={setStakeholderReadiness}
                    highlight={extractedConfidence ? needsAttention(extractedConfidence.stakeholder_readiness.confidence) : false}
                  />
                </div>
              </div>

              {/* Extracted Tasks */}
              {extractedTasks.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium mb-3 text-slate-900 dark:text-slate-100">
                    Suggested Tasks ({selectedTaskIndices.size} of {extractedTasks.length} selected)
                  </h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {extractedTasks.map((task, index) => (
                      <label
                        key={index}
                        className="flex items-start gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer"
                      >
                        <button
                          type="button"
                          onClick={() => {
                            const newSet = new Set(selectedTaskIndices)
                            if (newSet.has(index)) {
                              newSet.delete(index)
                            } else {
                              newSet.add(index)
                            }
                            setSelectedTaskIndices(newSet)
                          }}
                          className="mt-0.5 flex-shrink-0"
                        >
                          {selectedTaskIndices.has(index) ? (
                            <CheckSquare className="w-5 h-5 text-indigo-600" />
                          ) : (
                            <Square className="w-5 h-5 text-slate-400" />
                          )}
                        </button>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-slate-900 dark:text-slate-100">{task.title}</p>
                          {task.description && (
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">
                              {task.description}
                            </p>
                          )}
                        </div>
                        <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${
                          task.priority === 'high'
                            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                            : task.priority === 'medium'
                            ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                            : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400'
                        }`}>
                          {task.priority}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Source Context */}
              <div className="text-xs text-slate-500 dark:text-slate-400 border-t border-slate-200 dark:border-slate-700 pt-4">
                <p>
                  <strong>Source:</strong> DISCo Initiative &ldquo;{initiativeName}&rdquo;
                </p>
                {sourceContext && (
                  <p className="mt-1 line-clamp-2">{sourceContext}</p>
                )}
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        {!extracting && extractedConfidence && (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={creating}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {creating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <FolderPlus className="w-4 h-4" />
                  Create Project
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
