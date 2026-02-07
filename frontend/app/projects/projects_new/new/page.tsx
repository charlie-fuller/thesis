'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Save, Target, AlertCircle, Compass } from 'lucide-react'
import { apiGet, apiPost } from '@/lib/api'
import PageHeader from '@/components/PageHeader'

// ============================================================================
// TYPES
// ============================================================================

interface Stakeholder {
  id: string
  name: string
  department: string | null
  role: string | null
}

interface Initiative {
  id: string
  name: string
  status?: string
}

interface OpportunityCreate {
  opportunity_code: string
  title: string
  description?: string
  department?: string
  owner_stakeholder_id?: string
  current_state?: string
  desired_state?: string
  roi_potential?: number
  implementation_effort?: number
  strategic_alignment?: number
  stakeholder_readiness?: number
  status?: string
  next_step?: string
  blockers?: string[]
  follow_up_questions?: string[]
  initiative_ids?: string[]
}

// ============================================================================
// CONSTANTS
// ============================================================================

const DEPARTMENTS = [
  { value: 'finance', label: 'Finance' },
  { value: 'legal', label: 'Legal' },
  { value: 'people', label: 'People' },
  { value: 'it', label: 'IT' },
  { value: 'revops', label: 'RevOps' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'sales', label: 'Sales' },
  { value: 'onboarding', label: 'Onboarding' },
]

const STATUS_OPTIONS = [
  { value: 'backlog', label: 'Backlog', description: 'Identified but not yet started' },
  { value: 'active', label: 'Active', description: 'Currently being worked on' },
  { value: 'completed', label: 'Completed', description: 'Successfully implemented' },
  { value: 'archived', label: 'Archived', description: 'Dropped or no longer relevant' },
]

// ============================================================================
// COMPONENTS
// ============================================================================

function ScoreSlider({
  label,
  description,
  value,
  onChange,
}: {
  label: string
  description: string
  value: number
  onChange: (val: number) => void
}) {
  const getScoreColor = (v: number) => {
    if (v >= 4) return 'text-green-600 dark:text-green-400'
    if (v >= 3) return 'text-amber-600 dark:text-amber-400'
    return 'text-muted'
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <label className="font-medium text-secondary">{label}</label>
          <p className="text-sm text-muted">{description}</p>
        </div>
        <span className={`text-2xl font-bold ${getScoreColor(value)}`}>{value}</span>
      </div>
      <input
        type="range"
        min="1"
        max="5"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
      />
      <div className="flex justify-between text-xs text-muted">
        <span>Low (1)</span>
        <span>High (5)</span>
      </div>
    </div>
  )
}

function ArrayInput({
  label,
  placeholder,
  values,
  onChange,
}: {
  label: string
  placeholder: string
  values: string[]
  onChange: (vals: string[]) => void
}) {
  const [inputValue, setInputValue] = useState('')

  const handleAdd = () => {
    if (inputValue.trim()) {
      onChange([...values, inputValue.trim()])
      setInputValue('')
    }
  }

  const handleRemove = (index: number) => {
    onChange(values.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-2">
      <label className="block font-medium text-secondary">{label}</label>
      <div className="flex gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAdd())}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          type="button"
          onClick={handleAdd}
          className="px-4 py-2 bg-hover text-secondary rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
        >
          Add
        </button>
      </div>
      {values.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {values.map((val, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-3 py-1 bg-hover text-secondary rounded-full text-sm"
            >
              {val}
              <button
                type="button"
                onClick={() => handleRemove(i)}
                className="ml-1 text-muted hover:text-primary"
              >
                &times;
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function NewOpportunityPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [initiatives, setInitiatives] = useState<Initiative[]>([])

  // Form state
  const [form, setForm] = useState<OpportunityCreate>({
    opportunity_code: '',
    title: '',
    description: '',
    department: '',
    owner_stakeholder_id: '',
    current_state: '',
    desired_state: '',
    roi_potential: 3,
    implementation_effort: 3,
    strategic_alignment: 3,
    stakeholder_readiness: 3,
    status: 'backlog',
    next_step: '',
    blockers: [],
    follow_up_questions: [],
    initiative_ids: [],
  })

  // Load stakeholders and initiatives
  useEffect(() => {
    async function loadData() {
      try {
        const [stakeholdersData, initiativesData] = await Promise.all([
          apiGet<{ stakeholders: Stakeholder[] }>('/api/stakeholders/'),
          apiGet<{ success: boolean; tags: Array<{ tag: string; initiative_id: string; status: string }> }>('/api/disco/initiatives/as-tags'),
        ])
        setStakeholders(stakeholdersData.stakeholders || [])
        if (initiativesData.success && initiativesData.tags) {
          setInitiatives(initiativesData.tags.map(t => ({
            id: t.initiative_id,
            name: t.tag,
            status: t.status,
          })))
        }
      } catch (err) {
        console.error('Failed to load data:', err)
      }
    }
    loadData()
  }, [])

  const toggleInitiative = (initiativeId: string) => {
    setForm(prev => ({
      ...prev,
      initiative_ids: prev.initiative_ids?.includes(initiativeId)
        ? prev.initiative_ids.filter(id => id !== initiativeId)
        : [...(prev.initiative_ids || []), initiativeId],
    }))
  }

  // Calculate total score
  const totalScore =
    (form.roi_potential || 0) +
    (form.implementation_effort || 0) +
    (form.strategic_alignment || 0) +
    (form.stakeholder_readiness || 0)

  // Calculate tier
  const getTier = (score: number) => {
    if (score >= 17) return { tier: 1, label: 'Tier 1: Strategic Priority', color: 'text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/20' }
    if (score >= 14) return { tier: 2, label: 'Tier 2: High Impact', color: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20' }
    if (score >= 11) return { tier: 3, label: 'Tier 3: Medium Priority', color: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20' }
    return { tier: 4, label: 'Tier 4: Backlog', color: 'text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800' }
  }

  const tierInfo = getTier(totalScore)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    // Validation
    if (!form.opportunity_code.trim()) {
      setError('Opportunity code is required (e.g., F01, L03)')
      return
    }
    if (!form.title.trim()) {
      setError('Title is required')
      return
    }

    try {
      setLoading(true)
      const payload = {
        ...form,
        owner_stakeholder_id: form.owner_stakeholder_id || undefined,
      }
      await apiPost('/api/projects/', payload)
      router.push('/projects')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create opportunity')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-page flex flex-col">
      <PageHeader />
      <div className="flex-1 max-w-4xl mx-auto px-4 py-8 w-full">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/projects')}
            className="flex items-center gap-2 text-muted hover:text-primary mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Opportunities
          </button>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <Target className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-primary">New AI Opportunity</h1>
              <p className="text-muted">Track and score a new AI implementation opportunity</p>
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-red-800 dark:text-red-200">Error</h3>
              <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Basic Info */}
          <div className="bg-card rounded-xl border border-default p-6">
            <h2 className="text-lg font-semibold text-primary mb-4">Basic Information</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block font-medium text-secondary mb-1">
                  Opportunity Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.opportunity_code}
                  onChange={(e) => setForm({ ...form, opportunity_code: e.target.value.toUpperCase() })}
                  placeholder="e.g., F01, L03, HR02"
                  className="w-full px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                />
                <p className="text-xs text-muted mt-1">Department prefix + number (e.g., F01 = Finance #1)</p>
              </div>
              <div>
                <label className="block font-medium text-secondary mb-1">Department</label>
                <select
                  value={form.department}
                  onChange={(e) => setForm({ ...form, department: e.target.value })}
                  className="w-full px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select department...</option>
                  {DEPARTMENTS.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block font-medium text-secondary mb-1">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="e.g., AP Invoice Automation"
                  className="w-full px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block font-medium text-secondary mb-1">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  placeholder="Brief description of the opportunity..."
                  className="w-full px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-medium text-secondary mb-1">Owner</label>
                <select
                  value={form.owner_stakeholder_id}
                  onChange={(e) => setForm({ ...form, owner_stakeholder_id: e.target.value })}
                  className="w-full px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select owner...</option>
                  {stakeholders.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} {s.role ? `(${s.role})` : ''} {s.department ? `- ${s.department}` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-medium text-secondary mb-1">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Linked Initiatives */}
          {initiatives.length > 0 && (
            <div className="bg-card rounded-xl border border-default p-6">
              <div className="flex items-center gap-2 mb-4">
                <Compass className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-semibold text-primary">Linked Initiatives (Optional)</h2>
              </div>
              <p className="text-sm text-muted mb-4">
                Connect this project to DISCo initiatives for context tracking.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {initiatives.map((initiative) => (
                  <label
                    key={initiative.id}
                    className={`flex items-center gap-2 p-2 border rounded-lg cursor-pointer transition-colors ${
                      form.initiative_ids?.includes(initiative.id)
                        ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-default hover:bg-hover'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={form.initiative_ids?.includes(initiative.id) || false}
                      onChange={() => toggleInitiative(initiative.id)}
                      className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-primary truncate">{initiative.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Current/Desired State */}
          <div className="bg-card rounded-xl border border-default p-6">
            <h2 className="text-lg font-semibold text-primary mb-4">Problem Statement</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block font-medium text-secondary mb-1">Current State</label>
                <textarea
                  value={form.current_state}
                  onChange={(e) => setForm({ ...form, current_state: e.target.value })}
                  rows={3}
                  placeholder="What is the current process? What are the pain points?"
                  className="w-full px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-medium text-secondary mb-1">Desired State</label>
                <textarea
                  value={form.desired_state}
                  onChange={(e) => setForm({ ...form, desired_state: e.target.value })}
                  rows={3}
                  placeholder="What does success look like? What's the target outcome?"
                  className="w-full px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Scoring */}
          <div className="bg-card rounded-xl border border-default p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-primary">Opportunity Scoring</h2>
                <p className="text-sm text-muted">Rate each dimension from 1-5</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-primary">{totalScore}/20</div>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${tierInfo.color}`}>
                  {tierInfo.label}
                </span>
              </div>
            </div>

            <div className="space-y-6">
              <ScoreSlider
                label="ROI Potential"
                description="Expected return on investment and value generation"
                value={form.roi_potential || 3}
                onChange={(v) => setForm({ ...form, roi_potential: v })}
              />
              <ScoreSlider
                label="Implementation Effort"
                description="Ease of implementation (5 = easy, 1 = very complex)"
                value={form.implementation_effort || 3}
                onChange={(v) => setForm({ ...form, implementation_effort: v })}
              />
              <ScoreSlider
                label="Strategic Alignment"
                description="Alignment with organizational priorities and goals"
                value={form.strategic_alignment || 3}
                onChange={(v) => setForm({ ...form, strategic_alignment: v })}
              />
              <ScoreSlider
                label="Stakeholder Readiness"
                description="Stakeholder buy-in and change readiness"
                value={form.stakeholder_readiness || 3}
                onChange={(v) => setForm({ ...form, stakeholder_readiness: v })}
              />
            </div>
          </div>

          {/* Next Steps & Tracking */}
          <div className="bg-card rounded-xl border border-default p-6">
            <h2 className="text-lg font-semibold text-primary mb-4">Tracking</h2>
            <div className="space-y-4">
              <div>
                <label className="block font-medium text-secondary mb-1">Next Step</label>
                <input
                  type="text"
                  value={form.next_step}
                  onChange={(e) => setForm({ ...form, next_step: e.target.value })}
                  placeholder="What's the next action to advance this opportunity?"
                  className="w-full px-3 py-2 border border-default bg-card text-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <ArrayInput
                label="Blockers"
                placeholder="Add a blocker..."
                values={form.blockers || []}
                onChange={(vals) => setForm({ ...form, blockers: vals })}
              />
              <ArrayInput
                label="Follow-up Questions"
                placeholder="Add a question to explore..."
                values={form.follow_up_questions || []}
                onChange={(vals) => setForm({ ...form, follow_up_questions: vals })}
              />
            </div>
          </div>

          {/* Submit */}
          <div className="flex items-center justify-end gap-4">
            <button
              type="button"
              onClick={() => router.push('/projects')}
              className="px-6 py-2 text-muted hover:text-primary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {loading ? 'Creating...' : 'Create Opportunity'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
