'use client'

/**
 * ProjectCreateModal Component
 *
 * Modal for creating new projects directly from the Projects page.
 * Supports all required and optional fields:
 * - Project code (required)
 * - Title (required)
 * - Description
 * - Department
 * - Scores (ROI, Effort, Alignment, Readiness)
 * - Current/Desired state
 * - Status
 */

import { useState } from 'react'
import {
  X,
  Loader2,
  Target,
  FileText,
  Building2,
  Save,
} from 'lucide-react'
import { apiPost } from '@/lib/api'
import toast from 'react-hot-toast'

// ============================================================================
// TYPES
// ============================================================================

interface ProjectCreateModalProps {
  open: boolean
  onClose: () => void
  onCreated: () => void
}

interface CreateFormState {
  project_code: string
  title: string
  description: string
  department: string
  current_state: string
  desired_state: string
  roi_potential: number | null
  implementation_effort: number | null
  strategic_alignment: number | null
  stakeholder_readiness: number | null
  status: string
  next_step: string
}

// ============================================================================
// CONSTANTS
// ============================================================================

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

const STATUS_OPTIONS = [
  { value: 'backlog', label: 'Backlog' },
  { value: 'active', label: 'Active' },
]

const INITIAL_FORM_STATE: CreateFormState = {
  project_code: '',
  title: '',
  description: '',
  department: '',
  current_state: '',
  desired_state: '',
  roi_potential: null,
  implementation_effort: null,
  strategic_alignment: null,
  stakeholder_readiness: null,
  status: 'backlog',
  next_step: '',
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function ProjectCreateModal({
  open,
  onClose,
  onCreated,
}: ProjectCreateModalProps) {
  const [form, setForm] = useState<CreateFormState>(INITIAL_FORM_STATE)
  const [isSaving, setIsSaving] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleChange = (field: keyof CreateFormState, value: string | number | null) => {
    setForm(prev => ({ ...prev, [field]: value }))
    // Clear error when field is modified
    if (errors[field]) {
      setErrors(prev => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!form.project_code.trim()) {
      newErrors.project_code = 'Project code is required'
    } else if (form.project_code.length < 2 || form.project_code.length > 10) {
      newErrors.project_code = 'Code must be 2-10 characters'
    }

    if (!form.title.trim()) {
      newErrors.title = 'Title is required'
    }

    // Validate scores are 1-5 if provided
    const scoreFields: (keyof CreateFormState)[] = [
      'roi_potential',
      'implementation_effort',
      'strategic_alignment',
      'stakeholder_readiness',
    ]
    scoreFields.forEach(field => {
      const value = form[field] as number | null
      if (value !== null && (value < 1 || value > 5)) {
        newErrors[field] = 'Score must be 1-5'
      }
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return

    setIsSaving(true)
    try {
      const payload = {
        project_code: form.project_code.toUpperCase().trim(),
        title: form.title.trim(),
        description: form.description.trim() || null,
        department: form.department || null,
        current_state: form.current_state.trim() || null,
        desired_state: form.desired_state.trim() || null,
        roi_potential: form.roi_potential,
        implementation_effort: form.implementation_effort,
        strategic_alignment: form.strategic_alignment,
        stakeholder_readiness: form.stakeholder_readiness,
        status: form.status,
        next_step: form.next_step.trim() || null,
      }

      await apiPost('/api/projects/', payload)
      toast.success('Project created successfully')
      setForm(INITIAL_FORM_STATE)
      onCreated()
      onClose()
    } catch (error: unknown) {
      console.error('Failed to create project:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create project'
      toast.error(errorMessage)
    } finally {
      setIsSaving(false)
    }
  }

  const handleClose = () => {
    // Check for unsaved changes
    const hasChanges = Object.entries(form).some(([key, value]) => {
      const initial = INITIAL_FORM_STATE[key as keyof CreateFormState]
      return value !== initial
    })

    if (hasChanges) {
      if (window.confirm('You have unsaved changes. Are you sure you want to close?')) {
        setForm(INITIAL_FORM_STATE)
        setErrors({})
        onClose()
      }
    } else {
      onClose()
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-card border border-default rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-default">
          <div>
            <h2 className="text-xl font-semibold text-primary">New Project</h2>
            <p className="text-sm text-muted mt-1">Create a new AI initiative to track</p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 text-muted hover:text-primary hover:bg-hover rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Basic Info Section */}
          <section>
            <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Basic Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-medium text-muted block mb-1">
                  Project Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.project_code}
                  onChange={(e) => handleChange('project_code', e.target.value.toUpperCase())}
                  className={`w-full px-3 py-2 border rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono ${
                    errors.project_code ? 'border-red-500' : 'border-default'
                  }`}
                  placeholder="PRJ-001"
                  maxLength={10}
                />
                {errors.project_code && (
                  <p className="text-xs text-red-500 mt-1">{errors.project_code}</p>
                )}
              </div>
              <div className="md:col-span-2">
                <label className="text-xs font-medium text-muted block mb-1">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => handleChange('title', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.title ? 'border-red-500' : 'border-default'
                  }`}
                  placeholder="AI-powered Invoice Processing"
                />
                {errors.title && (
                  <p className="text-xs text-red-500 mt-1">{errors.title}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="text-xs font-medium text-muted block mb-1">Department</label>
                <select
                  value={form.department}
                  onChange={(e) => handleChange('department', e.target.value)}
                  className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select department...</option>
                  {DEPARTMENT_OPTIONS.map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-muted block mb-1">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => handleChange('status', e.target.value)}
                  className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {STATUS_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-4">
              <label className="text-xs font-medium text-muted block mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => handleChange('description', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="Describe the project and its objectives..."
              />
            </div>
          </section>

          {/* Scores Section */}
          <section>
            <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Scores (1-5)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs font-medium text-muted block mb-1">ROI Potential</label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={form.roi_potential ?? ''}
                  onChange={(e) => handleChange('roi_potential', e.target.value ? parseInt(e.target.value) : null)}
                  className={`w-full px-3 py-2 border rounded-lg bg-card text-primary text-center focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.roi_potential ? 'border-red-500' : 'border-default'
                  }`}
                  placeholder="-"
                />
                <p className="text-xs text-muted mt-1">5 = High value</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted block mb-1">Effort</label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={form.implementation_effort ?? ''}
                  onChange={(e) => handleChange('implementation_effort', e.target.value ? parseInt(e.target.value) : null)}
                  className={`w-full px-3 py-2 border rounded-lg bg-card text-primary text-center focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.implementation_effort ? 'border-red-500' : 'border-default'
                  }`}
                  placeholder="-"
                />
                <p className="text-xs text-muted mt-1">5 = Easy</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted block mb-1">Strategic</label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={form.strategic_alignment ?? ''}
                  onChange={(e) => handleChange('strategic_alignment', e.target.value ? parseInt(e.target.value) : null)}
                  className={`w-full px-3 py-2 border rounded-lg bg-card text-primary text-center focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.strategic_alignment ? 'border-red-500' : 'border-default'
                  }`}
                  placeholder="-"
                />
                <p className="text-xs text-muted mt-1">5 = Aligned</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted block mb-1">Readiness</label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={form.stakeholder_readiness ?? ''}
                  onChange={(e) => handleChange('stakeholder_readiness', e.target.value ? parseInt(e.target.value) : null)}
                  className={`w-full px-3 py-2 border rounded-lg bg-card text-primary text-center focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.stakeholder_readiness ? 'border-red-500' : 'border-default'
                  }`}
                  placeholder="-"
                />
                <p className="text-xs text-muted mt-1">5 = Ready</p>
              </div>
            </div>
          </section>

          {/* States Section */}
          <section>
            <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-4 flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              Current vs. Desired State
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-muted block mb-1">Current State</label>
                <textarea
                  value={form.current_state}
                  onChange={(e) => handleChange('current_state', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="Describe the current situation..."
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted block mb-1">Desired State</label>
                <textarea
                  value={form.desired_state}
                  onChange={(e) => handleChange('desired_state', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="Describe the target outcome..."
                />
              </div>
            </div>
          </section>

          {/* Next Step */}
          <section>
            <label className="text-xs font-medium text-muted block mb-1">Next Step</label>
            <input
              type="text"
              value={form.next_step}
              onChange={(e) => handleChange('next_step', e.target.value)}
              className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="What's the immediate next action?"
            />
          </section>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-default">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-secondary hover:text-primary hover:bg-hover rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSaving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Create Project
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
