'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Save, Target, AlertCircle } from 'lucide-react'
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
}

// ============================================================================
// CONSTANTS
// ============================================================================

const DEPARTMENTS = [
  { value: 'finance', label: 'Finance' },
  { value: 'legal', label: 'Legal' },
  { value: 'hr', label: 'HR' },
  { value: 'it', label: 'IT' },
  { value: 'revops', label: 'RevOps' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'sales', label: 'Sales' },
  { value: 'onboarding', label: 'Onboarding' },
]

const STATUS_OPTIONS = [
  { value: 'identified', label: 'Identified', description: 'Opportunity recognized but not yet scoped' },
  { value: 'scoping', label: 'Scoping', description: 'Actively defining requirements and approach' },
  { value: 'pilot', label: 'Pilot', description: 'Running a limited proof of concept' },
  { value: 'scaling', label: 'Scaling', description: 'Expanding from pilot to broader deployment' },
  { value: 'completed', label: 'Completed', description: 'Fully implemented' },
  { value: 'blocked', label: 'Blocked', description: 'Progress halted due to blockers' },
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
    if (v >= 4) return 'text-green-600'
    if (v >= 3) return 'text-amber-600'
    return 'text-slate-500'
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <label className="font-medium text-slate-700">{label}</label>
          <p className="text-sm text-slate-500">{description}</p>
        </div>
        <span className={`text-2xl font-bold ${getScoreColor(value)}`}>{value}</span>
      </div>
      <input
        type="range"
        min="1"
        max="5"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
      />
      <div className="flex justify-between text-xs text-slate-400">
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
      <label className="block font-medium text-slate-700">{label}</label>
      <div className="flex gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAdd())}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          type="button"
          onClick={handleAdd}
          className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200"
        >
          Add
        </button>
      </div>
      {values.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {values.map((val, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm"
            >
              {val}
              <button
                type="button"
                onClick={() => handleRemove(i)}
                className="ml-1 text-slate-400 hover:text-slate-600"
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
    status: 'identified',
    next_step: '',
    blockers: [],
    follow_up_questions: [],
  })

  // Load stakeholders for owner selection
  useEffect(() => {
    async function loadStakeholders() {
      try {
        const data = await apiGet<{ stakeholders: Stakeholder[] }>('/api/stakeholders/')
        setStakeholders(data.stakeholders || [])
      } catch (err) {
        console.error('Failed to load stakeholders:', err)
      }
    }
    loadStakeholders()
  }, [])

  // Calculate total score
  const totalScore =
    (form.roi_potential || 0) +
    (form.implementation_effort || 0) +
    (form.strategic_alignment || 0) +
    (form.stakeholder_readiness || 0)

  // Calculate tier
  const getTier = (score: number) => {
    if (score >= 17) return { tier: 1, label: 'Tier 1: Strategic Priority', color: 'text-rose-600 bg-rose-50' }
    if (score >= 14) return { tier: 2, label: 'Tier 2: High Impact', color: 'text-amber-600 bg-amber-50' }
    if (score >= 11) return { tier: 3, label: 'Tier 3: Medium Priority', color: 'text-blue-600 bg-blue-50' }
    return { tier: 4, label: 'Tier 4: Backlog', color: 'text-slate-600 bg-slate-50' }
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
      await apiPost('/api/opportunities/', payload)
      router.push('/opportunities')
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
            onClick={() => router.push('/opportunities')}
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
              <p className="text-slate-500">Track and score a new AI implementation opportunity</p>
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-red-800">Error</h3>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Basic Info */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Basic Information</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block font-medium text-slate-700 mb-1">
                  Opportunity Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.opportunity_code}
                  onChange={(e) => setForm({ ...form, opportunity_code: e.target.value.toUpperCase() })}
                  placeholder="e.g., F01, L03, HR02"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                />
                <p className="text-xs text-slate-500 mt-1">Department prefix + number (e.g., F01 = Finance #1)</p>
              </div>
              <div>
                <label className="block font-medium text-slate-700 mb-1">Department</label>
                <select
                  value={form.department}
                  onChange={(e) => setForm({ ...form, department: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                <label className="block font-medium text-slate-700 mb-1">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="e.g., AP Invoice Automation"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block font-medium text-slate-700 mb-1">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  placeholder="Brief description of the opportunity..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-medium text-slate-700 mb-1">Owner</label>
                <select
                  value={form.owner_stakeholder_id}
                  onChange={(e) => setForm({ ...form, owner_stakeholder_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                <label className="block font-medium text-slate-700 mb-1">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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

          {/* Current/Desired State */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Problem Statement</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Current State</label>
                <textarea
                  value={form.current_state}
                  onChange={(e) => setForm({ ...form, current_state: e.target.value })}
                  rows={3}
                  placeholder="What is the current process? What are the pain points?"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block font-medium text-slate-700 mb-1">Desired State</label>
                <textarea
                  value={form.desired_state}
                  onChange={(e) => setForm({ ...form, desired_state: e.target.value })}
                  rows={3}
                  placeholder="What does success look like? What's the target outcome?"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Scoring */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Opportunity Scoring</h2>
                <p className="text-sm text-slate-500">Rate each dimension from 1-5</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-slate-900">{totalScore}/20</div>
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
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Tracking</h2>
            <div className="space-y-4">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Next Step</label>
                <input
                  type="text"
                  value={form.next_step}
                  onChange={(e) => setForm({ ...form, next_step: e.target.value })}
                  placeholder="What's the next action to advance this opportunity?"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              onClick={() => router.push('/opportunities')}
              className="px-6 py-2 text-slate-600 hover:text-slate-800"
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
