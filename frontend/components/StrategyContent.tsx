'use client'

/**
 * Strategy Content Component
 *
 * Displays company objectives/goals and department KPIs.
 * KPIs are fetched from the database and support inline editing.
 * Used as a tab within the Intelligence page.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Target,
  TrendingUp,
  TrendingDown,
  Minus,
  Building2,
  ChevronDown,
  ChevronRight,
  BarChart3,
  Users,
  Sparkles,
  Plus,
  Trash2,
  Check,
  X,
  Pencil,
  Loader2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api'

// ============================================================================
// TYPES
// ============================================================================

interface CompanyObjective {
  id: string
  title: string
  description: string
  icon: string
  target_metric: string
  current_value: number | null
  target_value: number
  unit: string
  progress_percentage: number
  status: 'on_track' | 'at_risk' | 'behind' | 'achieved'
  priority: number
  updated_at: string
}

interface DepartmentKPI {
  id: string
  department: string
  kpi_name: string
  description: string
  current_value: number | null
  target_value: number
  unit: string
  trend: 'up' | 'down' | 'flat'
  trend_percentage: number
  status: 'green' | 'yellow' | 'red'
  linked_objective_id: string | null
  fiscal_year: string
  sort_order: number
  created_at: string
  updated_at: string
}

// ============================================================================
// COMPANY DATA - FY26 Company Goals (Completed)
// ============================================================================

const FY26_OBJECTIVES: CompanyObjective[] = [
  {
    id: '1',
    title: 'Market Positioning',
    description: 'Re-establish Contentful as a thought leader and disruptor in the broader DXP category, with a compelling near-term value proposition, and an expansive vision around content operations that co-opts the GenAI value proposition.',
    icon: 'Target',
    target_metric: 'DXP category leadership',
    current_value: null,
    target_value: 100,
    unit: '%',
    progress_percentage: 65,
    status: 'on_track',
    priority: 1,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '2',
    title: 'Sales Productivity',
    description: 'Accelerate sales productivity to approach industry benchmarks, exceed pipeline and bookings targets, and support increased S&M investment in H2 to re-accelerate revenue growth in FY27 and FY28.',
    icon: 'TrendingUp',
    target_metric: 'Pipeline vs target',
    current_value: 113,
    target_value: 100,
    unit: '%',
    progress_percentage: 100,
    status: 'achieved',
    priority: 2,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '3',
    title: 'Product Innovation',
    description: 'Accelerate velocity of new product and feature introductions that reinforce platform/ecosystem leadership, provide differentiated expansion into DXP category, and capture net new spend categories through GenAI capabilities.',
    icon: 'Sparkles',
    target_metric: 'EXO/GenAI milestones',
    current_value: 5,
    target_value: 8,
    unit: 'milestones',
    progress_percentage: 63,
    status: 'on_track',
    priority: 3,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '4',
    title: 'Culture',
    description: 'Create a winning culture based on transparency, empowerment, risk taking and performance. Values: Relentless Customer Focus, Own It, Be Bold, Win Together.',
    icon: 'Users',
    target_metric: 'Employee retention',
    current_value: 92,
    target_value: 98,
    unit: '%',
    progress_percentage: 67,
    status: 'on_track',
    priority: 4,
    updated_at: '2026-01-22T10:00:00Z',
  },
]

// ============================================================================
// COMPANY DATA - FY27 Company Goals (Current)
// ============================================================================

const FY27_OBJECTIVES: CompanyObjective[] = [
  {
    id: '1',
    title: 'Market Leadership',
    description: 'Transform perceptions of Contentful from a technical CMS tool for developers into a strategic solution partner for CMOs and CTOs. Create a differentiated narrative around our product vision that capitalizes on emerging AI disruptions and creates an aura of industry leadership.',
    icon: 'Target',
    target_metric: 'CMO/CTO perception shift',
    current_value: null,
    target_value: 100,
    unit: '%',
    progress_percentage: 0,
    status: 'on_track',
    priority: 1,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '2',
    title: 'Cost-Efficient GTM Growth',
    description: 'Build upon FY26 productivity improvements to exceed all FY top line targets, achieve a cost-to-book ratio under 2.0, and improve FY26 gross retention metrics.',
    icon: 'TrendingUp',
    target_metric: 'Cost-to-book ratio',
    current_value: null,
    target_value: 2.0,
    unit: 'ratio',
    progress_percentage: 0,
    status: 'on_track',
    priority: 2,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '3',
    title: 'Product Innovation',
    description: 'Introduce new platform and AI-powered experience orchestration capabilities that leapfrog the market. Democratize the value of experimentation, p13n, and content analytics. Develop a clear product strategy behind the agentic web.',
    icon: 'Sparkles',
    target_metric: 'EXO/Agentic Web milestones',
    current_value: null,
    target_value: 8,
    unit: 'milestones',
    progress_percentage: 0,
    status: 'on_track',
    priority: 3,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '4',
    title: 'Culture',
    description: 'Create a winning culture based on transparency, empowerment, risk taking and performance. Target: 98% employee retention.',
    icon: 'Users',
    target_metric: 'Employee retention',
    current_value: null,
    target_value: 98,
    unit: '%',
    progress_percentage: 0,
    status: 'on_track',
    priority: 4,
    updated_at: '2026-01-22T10:00:00Z',
  },
]

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Sparkles,
  Users,
  Target,
  TrendingUp,
}

function ObjectiveIcon({ name, className }: { name: string; className?: string }) {
  const Icon = ICON_MAP[name] || Target
  return <Icon className={className} />
}

function StatusBadge({ status }: { status: CompanyObjective['status'] }) {
  const config = {
    on_track: { label: 'On Track', color: 'var(--color-success)' },
    at_risk: { label: 'At Risk', color: 'var(--color-warning)' },
    behind: { label: 'Behind', color: 'var(--color-error)' },
    achieved: { label: 'Achieved', color: 'var(--color-primary)' },
  }
  const { label, color } = config[status]
  return (
    <span
      className="px-2 py-0.5 rounded-full text-xs font-medium border"
      style={{ borderColor: color, color: color }}
    >
      {label}
    </span>
  )
}

function KPIStatusDot({ status }: { status: DepartmentKPI['status'] }) {
  const colors = {
    green: 'var(--color-success)',
    yellow: 'var(--color-warning)',
    red: 'var(--color-error)',
  }
  return <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: colors[status] }} />
}

function TrendIndicator({ trend, percentage }: { trend: DepartmentKPI['trend']; percentage: number }) {
  if (trend === 'up') {
    return (
      <span className="flex items-center gap-0.5 text-xs" style={{ color: 'var(--color-success)' }}>
        <TrendingUp className="w-3 h-3" />
        {percentage}%
      </span>
    )
  }
  if (trend === 'down') {
    return (
      <span className="flex items-center gap-0.5 text-xs" style={{ color: 'var(--color-error)' }}>
        <TrendingDown className="w-3 h-3" />
        {percentage}%
      </span>
    )
  }
  return (
    <span className="flex items-center gap-0.5 text-muted text-xs">
      <Minus className="w-3 h-3" />
      {percentage}%
    </span>
  )
}

function ProgressBar({ percentage, status }: { percentage: number; status: CompanyObjective['status'] }) {
  const colors = {
    on_track: 'var(--color-success)',
    at_risk: 'var(--color-warning)',
    behind: 'var(--color-error)',
    achieved: 'var(--color-primary)',
  }
  return (
    <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-bg-hover)' }}>
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${Math.min(percentage, 100)}%`, backgroundColor: colors[status] }}
      />
    </div>
  )
}

// ============================================================================
// KPI INLINE EDITOR
// ============================================================================

interface KPIEditState {
  current_value: string
  target_value: string
  trend: 'up' | 'down' | 'flat'
  status: 'green' | 'yellow' | 'red'
}

function KPIEditRow({
  kpi,
  onSave,
  onCancel,
}: {
  kpi: DepartmentKPI
  onSave: (id: string, data: Partial<DepartmentKPI>) => Promise<void>
  onCancel: () => void
}) {
  const [form, setForm] = useState<KPIEditState>({
    current_value: kpi.current_value?.toString() ?? '',
    target_value: kpi.target_value.toString(),
    trend: kpi.trend,
    status: kpi.status,
  })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await onSave(kpi.id, {
        current_value: form.current_value ? parseFloat(form.current_value) : null,
        target_value: parseFloat(form.target_value),
        trend: form.trend,
        status: form.status,
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <tr className="border-t border-default bg-hover/50">
      <td className="px-4 py-3">
        <div>
          <span className="text-sm font-medium text-primary">{kpi.kpi_name}</span>
          <p className="text-xs text-muted mt-0.5">{kpi.description}</p>
        </div>
      </td>
      <td className="text-right px-4 py-3">
        <input
          type="number"
          value={form.current_value}
          onChange={(e) => setForm({ ...form, current_value: e.target.value })}
          className="w-20 px-2 py-1 text-sm text-right bg-card border border-default rounded"
          placeholder="--"
        />
      </td>
      <td className="text-right px-4 py-3">
        <input
          type="number"
          value={form.target_value}
          onChange={(e) => setForm({ ...form, target_value: e.target.value })}
          className="w-20 px-2 py-1 text-sm text-right bg-card border border-default rounded"
        />
      </td>
      <td className="text-center px-4 py-3">
        <select
          value={form.trend}
          onChange={(e) => setForm({ ...form, trend: e.target.value as KPIEditState['trend'] })}
          className="px-2 py-1 text-xs bg-card border border-default rounded"
        >
          <option value="up">Up</option>
          <option value="down">Down</option>
          <option value="flat">Flat</option>
        </select>
      </td>
      <td className="text-center px-4 py-3">
        <div className="flex items-center justify-center gap-1">
          <select
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value as KPIEditState['status'] })}
            className="px-2 py-1 text-xs bg-card border border-default rounded"
          >
            <option value="green">Green</option>
            <option value="yellow">Yellow</option>
            <option value="red">Red</option>
          </select>
          <button
            onClick={handleSave}
            disabled={saving}
            className="p-1 text-green-600 hover:bg-green-100 dark:hover:bg-green-900/30 rounded"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          </button>
          <button
            onClick={onCancel}
            className="p-1 text-muted hover:bg-hover rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </td>
    </tr>
  )
}

// ============================================================================
// KPI ADD FORM
// ============================================================================

interface NewKPIForm {
  kpi_name: string
  description: string
  target_value: string
  unit: string
  department: string
}

function AddKPIRow({
  department,
  onSave,
  onCancel,
}: {
  department: string
  onSave: (data: Partial<DepartmentKPI> & { department: string; kpi_name: string; target_value: number; unit: string }) => Promise<void>
  onCancel: () => void
}) {
  const [form, setForm] = useState<NewKPIForm>({
    kpi_name: '',
    description: '',
    target_value: '',
    unit: '',
    department,
  })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.kpi_name.trim() || !form.target_value || !form.unit.trim()) {
      toast.error('Name, target value, and unit are required')
      return
    }
    setSaving(true)
    try {
      await onSave({
        department: form.department,
        kpi_name: form.kpi_name.trim(),
        description: form.description.trim() || undefined,
        target_value: parseFloat(form.target_value),
        unit: form.unit.trim(),
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <tr className="border-t border-default bg-hover/50">
      <td className="px-4 py-3">
        <input
          type="text"
          value={form.kpi_name}
          onChange={(e) => setForm({ ...form, kpi_name: e.target.value })}
          placeholder="KPI name"
          className="w-full px-2 py-1 text-sm bg-card border border-default rounded mb-1"
          autoFocus
        />
        <input
          type="text"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          placeholder="Description (optional)"
          className="w-full px-2 py-1 text-xs bg-card border border-default rounded"
        />
      </td>
      <td className="text-right px-4 py-3">
        <span className="text-xs text-muted">--</span>
      </td>
      <td className="text-right px-4 py-3">
        <input
          type="number"
          value={form.target_value}
          onChange={(e) => setForm({ ...form, target_value: e.target.value })}
          placeholder="Target"
          className="w-20 px-2 py-1 text-sm text-right bg-card border border-default rounded"
        />
      </td>
      <td className="text-center px-4 py-3">
        <input
          type="text"
          value={form.unit}
          onChange={(e) => setForm({ ...form, unit: e.target.value })}
          placeholder="unit"
          className="w-20 px-2 py-1 text-xs text-center bg-card border border-default rounded"
        />
      </td>
      <td className="text-center px-4 py-3">
        <div className="flex items-center justify-center gap-1">
          <button
            onClick={handleSave}
            disabled={saving}
            className="p-1 text-green-600 hover:bg-green-100 dark:hover:bg-green-900/30 rounded"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          </button>
          <button
            onClick={onCancel}
            className="p-1 text-muted hover:bg-hover rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </td>
    </tr>
  )
}

// ============================================================================
// ADD DEPARTMENT FORM
// ============================================================================

function AddDepartmentForm({
  onSave,
  onCancel,
}: {
  onSave: (data: { department: string; kpi_name: string; target_value: number; unit: string; description?: string }) => Promise<void>
  onCancel: () => void
}) {
  const [form, setForm] = useState({
    department: '',
    kpi_name: '',
    description: '',
    target_value: '',
    unit: '',
  })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.department.trim() || !form.kpi_name.trim() || !form.target_value || !form.unit.trim()) {
      toast.error('Department, KPI name, target value, and unit are required')
      return
    }
    setSaving(true)
    try {
      await onSave({
        department: form.department.trim(),
        kpi_name: form.kpi_name.trim(),
        description: form.description.trim() || undefined,
        target_value: parseFloat(form.target_value),
        unit: form.unit.trim(),
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-card border border-default rounded-lg p-4 space-y-3">
      <h4 className="text-sm font-medium text-primary">Add New Department</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-muted mb-1">Department Name</label>
          <input
            type="text"
            value={form.department}
            onChange={(e) => setForm({ ...form, department: e.target.value })}
            placeholder="e.g. Marketing"
            className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
            autoFocus
          />
        </div>
        <div>
          <label className="block text-xs text-muted mb-1">First KPI Name</label>
          <input
            type="text"
            value={form.kpi_name}
            onChange={(e) => setForm({ ...form, kpi_name: e.target.value })}
            placeholder="e.g. Campaign ROI"
            className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
          />
        </div>
        <div>
          <label className="block text-xs text-muted mb-1">Target Value</label>
          <input
            type="number"
            value={form.target_value}
            onChange={(e) => setForm({ ...form, target_value: e.target.value })}
            placeholder="100"
            className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
          />
        </div>
        <div>
          <label className="block text-xs text-muted mb-1">Unit</label>
          <input
            type="text"
            value={form.unit}
            onChange={(e) => setForm({ ...form, unit: e.target.value })}
            placeholder="e.g. %, days, count"
            className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
          />
        </div>
        <div className="col-span-2">
          <label className="block text-xs text-muted mb-1">Description (optional)</label>
          <input
            type="text"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Brief description of this KPI"
            className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
          />
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-muted hover:bg-hover rounded"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-3 py-1.5 text-sm bg-primary text-white rounded hover:opacity-90 disabled:opacity-50 flex items-center gap-1.5"
        >
          {saving && <Loader2 className="w-3 h-3 animate-spin" />}
          Add Department
        </button>
      </div>
    </div>
  )
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function StrategyContent() {
  const [mainTab, setMainTab] = useState<'company' | 'department'>('company')
  const [fiscalYearTab, setFiscalYearTab] = useState<'fy26' | 'fy27'>('fy27')
  const [kpis, setKpis] = useState<DepartmentKPI[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedDepartments, setExpandedDepartments] = useState<Set<string>>(new Set())
  const [editingKpiId, setEditingKpiId] = useState<string | null>(null)
  const [addingToDepartment, setAddingToDepartment] = useState<string | null>(null)
  const [showAddDepartment, setShowAddDepartment] = useState(false)
  const [deletingKpiId, setDeletingKpiId] = useState<string | null>(null)

  // Select objectives based on fiscal year tab
  const objectives = fiscalYearTab === 'fy26' ? FY26_OBJECTIVES : FY27_OBJECTIVES

  // Fetch KPIs from API
  const fetchKpis = useCallback(async () => {
    try {
      setError(null)
      const data = await apiGet<DepartmentKPI[]>('/api/strategy/kpis')
      setKpis(data)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load KPIs'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchKpis()
  }, [fetchKpis])

  // Group KPIs by department
  const kpisByDepartment = kpis.reduce((acc, kpi) => {
    if (!acc[kpi.department]) {
      acc[kpi.department] = []
    }
    acc[kpi.department].push(kpi)
    return acc
  }, {} as Record<string, DepartmentKPI[]>)

  const departments = Object.keys(kpisByDepartment).sort()

  const toggleDepartment = (dept: string) => {
    setExpandedDepartments(prev => {
      const next = new Set(prev)
      if (next.has(dept)) {
        next.delete(dept)
      } else {
        next.add(dept)
      }
      return next
    })
  }

  // CRUD handlers
  const handleUpdateKpi = async (id: string, data: Partial<DepartmentKPI>) => {
    try {
      const updated = await apiPatch<DepartmentKPI>(`/api/strategy/kpis/${id}`, data)
      setKpis(prev => prev.map(k => k.id === id ? updated : k))
      setEditingKpiId(null)
      toast.success('KPI updated')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update KPI')
    }
  }

  const handleCreateKpi = async (data: Partial<DepartmentKPI> & { department: string; kpi_name: string; target_value: number; unit: string }) => {
    try {
      const created = await apiPost<DepartmentKPI>('/api/strategy/kpis', data)
      setKpis(prev => [...prev, created])
      setAddingToDepartment(null)
      setShowAddDepartment(false)
      // Auto-expand the department
      setExpandedDepartments(prev => {
        const next = new Set(prev)
        next.add(created.department)
        return next
      })
      toast.success('KPI created')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create KPI')
    }
  }

  const handleDeleteKpi = async (id: string) => {
    try {
      await apiDelete(`/api/strategy/kpis/${id}`)
      setKpis(prev => prev.filter(k => k.id !== id))
      setDeletingKpiId(null)
      toast.success('KPI deleted')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete KPI')
    }
  }

  // Calculate summary stats
  const objectiveSummary = {
    total: objectives.length,
    onTrack: objectives.filter(o => o.status === 'on_track').length,
    atRisk: objectives.filter(o => o.status === 'at_risk').length,
    behind: objectives.filter(o => o.status === 'behind').length,
    achieved: objectives.filter(o => o.status === 'achieved').length,
    avgProgress: Math.round(objectives.reduce((sum, o) => sum + o.progress_percentage, 0) / objectives.length),
  }

  const kpiSummary = {
    total: kpis.length,
    green: kpis.filter(k => k.status === 'green').length,
    yellow: kpis.filter(k => k.status === 'yellow').length,
    red: kpis.filter(k => k.status === 'red').length,
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <p className="text-muted">
          Company objectives and G&A department KPIs. Use these to align AI opportunities with
          strategic priorities and demonstrate impact in career reviews with Compass.
        </p>
      </div>

      {/* Main Tabs */}
      <div className="flex items-center gap-2 mb-6 border-b border-default">
        <button
          onClick={() => setMainTab('company')}
          className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
            mainTab === 'company'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted hover:text-secondary'
          }`}
        >
          <Target className="w-4 h-4 inline-block mr-2" />
          Company Objectives
        </button>
        <button
          onClick={() => setMainTab('department')}
          className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
            mainTab === 'department'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted hover:text-secondary'
          }`}
        >
          <BarChart3 className="w-4 h-4 inline-block mr-2" />
          Department KPIs
        </button>
      </div>

      {/* Company Objectives Tab */}
      {mainTab === 'company' && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">
                  {fiscalYearTab === 'fy26' ? 'FY26 Final' : 'FY27 Progress'}
                </span>
                <Target className="w-5 h-5 text-blue-500" />
              </div>
              <div className="mt-2">
                {fiscalYearTab === 'fy26' ? (
                  <>
                    <span className="text-2xl font-bold text-primary">{objectiveSummary.avgProgress}%</span>
                    <span className="text-sm text-muted ml-2">avg completion</span>
                  </>
                ) : (
                  <>
                    <span className="text-2xl font-bold text-primary">{objectives.length}</span>
                    <span className="text-sm text-muted ml-2">strategic goals</span>
                  </>
                )}
              </div>
              <div className="mt-2 flex gap-2 text-xs">
                {fiscalYearTab === 'fy26' ? (
                  <>
                    <span style={{ color: 'var(--color-success)' }}>{objectiveSummary.onTrack} on track</span>
                    <span style={{ color: 'var(--color-warning)' }}>{objectiveSummary.atRisk} at risk</span>
                    <span style={{ color: 'var(--color-error)' }}>{objectiveSummary.behind} behind</span>
                  </>
                ) : (
                  <span className="text-secondary">Planning targets for next fiscal year</span>
                )}
              </div>
            </div>

            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">Strategic Goals</span>
                <Sparkles className="w-5 h-5 text-amber-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">{objectives.length}</span>
                <span className="text-sm text-muted ml-2">objectives</span>
              </div>
              <div className="mt-2 text-xs text-muted">
                {fiscalYearTab === 'fy26' ? 'Current fiscal year' : 'Next fiscal year planning'}
              </div>
            </div>

            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">Achieved</span>
                <TrendingUp className="w-5 h-5 text-green-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">{objectiveSummary.achieved}</span>
                <span className="text-sm text-muted ml-2">/ {objectives.length}</span>
              </div>
              <div className="mt-2 text-xs text-muted">
                Goals completed
              </div>
            </div>
          </div>

          {/* Fiscal Year Tabs */}
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => setFiscalYearTab('fy26')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                fiscalYearTab === 'fy26'
                  ? 'bg-primary text-white'
                  : 'bg-card border border-default text-secondary hover:bg-hover'
              }`}
            >
              FY26 Goals
              <span className="ml-1.5 text-xs opacity-75">(Completed)</span>
            </button>
            <button
              onClick={() => setFiscalYearTab('fy27')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                fiscalYearTab === 'fy27'
                  ? 'bg-primary text-white'
                  : 'bg-card border border-default text-secondary hover:bg-hover'
              }`}
            >
              FY27 Goals
              <span className="ml-1.5 text-xs opacity-75">(Current)</span>
            </button>
          </div>

          <div className="space-y-4">
            {objectives
              .sort((a, b) => a.priority - b.priority)
              .map((objective) => (
                <div
                  key={objective.id}
                  className="bg-card border border-default rounded-lg p-5 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-hover flex items-center justify-center">
                      <ObjectiveIcon name={objective.icon} className="w-6 h-6 icon-primary" />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h3 className="text-base font-semibold text-primary">
                            {objective.priority}. {objective.title}
                          </h3>
                          <p className="text-sm text-muted mt-1">{objective.description}</p>
                        </div>
                        {fiscalYearTab === 'fy26' ? (
                          <StatusBadge status={objective.status} />
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-hover text-secondary">
                            Planning
                          </span>
                        )}
                      </div>

                      {/* Progress */}
                      <div className="mt-4">
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-muted">{objective.target_metric}</span>
                          <span className="font-medium text-primary">
                            {fiscalYearTab === 'fy26' ? (
                              <>
                                {objective.current_value !== null ? objective.current_value : '--'}{objective.unit} / {objective.target_value}{objective.unit}
                              </>
                            ) : (
                              <>Target: {objective.target_value}{objective.unit}</>
                            )}
                          </span>
                        </div>
                        {fiscalYearTab === 'fy26' ? (
                          <>
                            <ProgressBar percentage={objective.progress_percentage} status={objective.status} />
                            <div className="flex items-center justify-between mt-1">
                              <span className="text-xs text-muted">{objective.progress_percentage}% complete</span>
                              <span className="text-xs text-muted">
                                Updated {new Date(objective.updated_at).toLocaleDateString()}
                              </span>
                            </div>
                          </>
                        ) : (
                          <div className="h-2 bg-hover rounded-full overflow-hidden">
                            <div className="h-full w-0 rounded-full border-default" />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </>
      )}

      {/* Department KPIs Tab */}
      {mainTab === 'department' && (
        <>
          {/* Loading / Error States */}
          {loading && (
            <div className="flex items-center justify-center py-12 text-muted">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              Loading KPIs...
            </div>
          )}

          {error && (
            <div className="p-4 mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
              <button onClick={fetchKpis} className="mt-2 text-sm text-red-600 underline">
                Retry
              </button>
            </div>
          )}

          {!loading && !error && (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-card border border-default rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted">KPI Health</span>
                    <BarChart3 className="w-5 h-5 text-green-500" />
                  </div>
                  <div className="mt-2">
                    <span className="text-2xl font-bold text-primary">{kpiSummary.total}</span>
                    <span className="text-sm text-muted ml-2">tracked KPIs</span>
                  </div>
                  <div className="mt-2 flex gap-2 text-xs">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-success)' }} />
                      {kpiSummary.green} green
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-warning)' }} />
                      {kpiSummary.yellow} yellow
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-error)' }} />
                      {kpiSummary.red} red
                    </span>
                  </div>
                </div>

                <div className="bg-card border border-default rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted">Departments</span>
                    <Building2 className="w-5 h-5 text-purple-500" />
                  </div>
                  <div className="mt-2">
                    <span className="text-2xl font-bold text-primary">{departments.length}</span>
                    <span className="text-sm text-muted ml-2">with AI KPIs</span>
                  </div>
                  <div className="mt-2 text-xs text-muted">
                    {departments.slice(0, 3).join(', ')}{departments.length > 3 ? ` +${departments.length - 3} more` : ''}
                  </div>
                </div>

                <div className="bg-card border border-default rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted">At Risk</span>
                    <TrendingDown className="w-5 h-5 text-red-500" />
                  </div>
                  <div className="mt-2">
                    <span className="text-2xl font-bold text-primary">{kpiSummary.red}</span>
                    <span className="text-sm text-muted ml-2">KPIs need attention</span>
                  </div>
                  <div className="mt-2 text-xs text-muted">
                    Below target metrics
                  </div>
                </div>
              </div>

              {/* Department List */}
              <div className="space-y-3">
                {departments.map((department) => {
                  const deptKpis = kpisByDepartment[department]
                  const isExpanded = expandedDepartments.has(department)
                  const deptHealth = {
                    green: deptKpis.filter(k => k.status === 'green').length,
                    yellow: deptKpis.filter(k => k.status === 'yellow').length,
                    red: deptKpis.filter(k => k.status === 'red').length,
                  }

                  return (
                    <div key={department} className="bg-card border border-default rounded-lg overflow-hidden">
                      {/* Department Header */}
                      <button
                        onClick={() => toggleDepartment(department)}
                        className="w-full flex items-center justify-between p-4 hover:bg-hover transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          {isExpanded ? (
                            <ChevronDown className="w-5 h-5 text-muted" />
                          ) : (
                            <ChevronRight className="w-5 h-5 text-muted" />
                          )}
                          <Building2 className="w-5 h-5 text-purple-500" />
                          <span className="font-medium text-primary">{department}</span>
                          <span className="text-sm text-muted">({deptKpis.length} KPIs)</span>
                        </div>
                        <div className="flex items-center gap-3">
                          {deptHealth.green > 0 && (
                            <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-success)' }}>
                              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-success)' }} />
                              {deptHealth.green}
                            </span>
                          )}
                          {deptHealth.yellow > 0 && (
                            <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-warning)' }}>
                              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-warning)' }} />
                              {deptHealth.yellow}
                            </span>
                          )}
                          {deptHealth.red > 0 && (
                            <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-error)' }}>
                              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-error)' }} />
                              {deptHealth.red}
                            </span>
                          )}
                        </div>
                      </button>

                      {/* KPI List */}
                      {isExpanded && (
                        <div className="border-t border-default">
                          <table className="w-full">
                            <thead>
                              <tr className="bg-hover/50 text-xs text-muted uppercase">
                                <th className="text-left px-4 py-2 font-medium">KPI</th>
                                <th className="text-right px-4 py-2 font-medium">Current</th>
                                <th className="text-right px-4 py-2 font-medium">Target</th>
                                <th className="text-center px-4 py-2 font-medium">Trend</th>
                                <th className="text-center px-4 py-2 font-medium">Status</th>
                              </tr>
                            </thead>
                            <tbody>
                              {deptKpis.map((kpi) =>
                                editingKpiId === kpi.id ? (
                                  <KPIEditRow
                                    key={kpi.id}
                                    kpi={kpi}
                                    onSave={handleUpdateKpi}
                                    onCancel={() => setEditingKpiId(null)}
                                  />
                                ) : (
                                  <tr key={kpi.id} className="border-t border-default hover:bg-hover/30 group">
                                    <td className="px-4 py-3">
                                      <div>
                                        <span className="text-sm font-medium text-primary">{kpi.kpi_name}</span>
                                        <p className="text-xs text-muted mt-0.5">{kpi.description}</p>
                                      </div>
                                    </td>
                                    <td className="text-right px-4 py-3">
                                      <span className="text-sm font-medium text-primary">
                                        {kpi.current_value !== null ? kpi.current_value : '--'} {kpi.unit}
                                      </span>
                                    </td>
                                    <td className="text-right px-4 py-3">
                                      <span className="text-sm text-muted">
                                        {kpi.target_value} {kpi.unit}
                                      </span>
                                    </td>
                                    <td className="text-center px-4 py-3">
                                      <TrendIndicator trend={kpi.trend} percentage={kpi.trend_percentage} />
                                    </td>
                                    <td className="text-center px-4 py-3">
                                      <div className="flex items-center justify-center gap-2">
                                        <KPIStatusDot status={kpi.status} />
                                        <div className="hidden group-hover:flex items-center gap-1">
                                          <button
                                            onClick={() => setEditingKpiId(kpi.id)}
                                            className="p-1 text-muted hover:text-primary hover:bg-hover rounded"
                                          >
                                            <Pencil className="w-3.5 h-3.5" />
                                          </button>
                                          {deletingKpiId === kpi.id ? (
                                            <div className="flex items-center gap-1">
                                              <button
                                                onClick={() => handleDeleteKpi(kpi.id)}
                                                className="p-1 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded"
                                              >
                                                <Check className="w-3.5 h-3.5" />
                                              </button>
                                              <button
                                                onClick={() => setDeletingKpiId(null)}
                                                className="p-1 text-muted hover:bg-hover rounded"
                                              >
                                                <X className="w-3.5 h-3.5" />
                                              </button>
                                            </div>
                                          ) : (
                                            <button
                                              onClick={() => setDeletingKpiId(kpi.id)}
                                              className="p-1 text-muted hover:text-red-600 hover:bg-hover rounded"
                                            >
                                              <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                          )}
                                        </div>
                                      </div>
                                    </td>
                                  </tr>
                                )
                              )}
                              {addingToDepartment === department && (
                                <AddKPIRow
                                  department={department}
                                  onSave={handleCreateKpi}
                                  onCancel={() => setAddingToDepartment(null)}
                                />
                              )}
                            </tbody>
                          </table>
                          {addingToDepartment !== department && (
                            <div className="px-4 py-2 border-t border-default">
                              <button
                                onClick={() => setAddingToDepartment(department)}
                                className="flex items-center gap-1.5 text-xs text-muted hover:text-primary transition-colors"
                              >
                                <Plus className="w-3.5 h-3.5" />
                                Add KPI
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Add Department */}
              <div className="mt-4">
                {showAddDepartment ? (
                  <AddDepartmentForm
                    onSave={handleCreateKpi}
                    onCancel={() => setShowAddDepartment(false)}
                  />
                ) : (
                  <button
                    onClick={() => setShowAddDepartment(true)}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-muted hover:text-primary border border-dashed border-default rounded-lg hover:border-primary transition-colors w-full justify-center"
                  >
                    <Plus className="w-4 h-4" />
                    Add Department
                  </button>
                )}
              </div>
            </>
          )}
        </>
      )}

      {/* Info Banner */}
      <div className="mt-8 p-4 bg-hover border border-default rounded-lg">
        <div className="flex items-start gap-3">
          <Target className="w-5 h-5 icon-primary flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-primary">
              Aligning Opportunities with Strategy
            </h3>
            <p className="text-sm text-secondary mt-1">
              When evaluating AI opportunities, consider how they contribute to these company objectives
              and department KPIs. Opportunities that directly impact multiple strategic goals should
              receive higher priority scores.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
