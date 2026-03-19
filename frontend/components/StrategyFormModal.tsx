'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiGet, apiPost, apiPatch } from '@/lib/api'

// Types matching the API
interface StrategicGoal {
  id: string
  level: string
  title: string
  description: string | null
  department: string | null
  owner: string | null
  target_metric: string | null
  current_value: number | null
  target_value: number | null
  unit: string | null
  status: string
  priority: number
  parent_goal_id: string | null
  fiscal_year: string
  created_at: string
  updated_at: string
}

interface DepartmentKPI {
  id: string
  department: string
  kpi_name: string
  description: string | null
  current_value: number | null
  target_value: number
  unit: string
  trend: string
  trend_percentage: number
  status: string
  linked_objective_id: string | null
  linked_goal_id: string | null
  fiscal_year: string
  sort_order: number
  created_at: string
  updated_at: string
}

type ItemType = 'company_goal' | 'team_goal' | 'kpi'

interface StrategyFormModalProps {
  open: boolean
  onClose: () => void
  onSaved: () => void
  editItem?: { type: ItemType; data: StrategicGoal | DepartmentKPI } | null
  defaultType?: ItemType
}

const FISCAL_YEARS = ['FY26', 'FY27', 'FY28']
const GOAL_STATUSES = [
  { value: 'on_track', label: 'On Track' },
  { value: 'at_risk', label: 'At Risk' },
  { value: 'behind', label: 'Behind' },
  { value: 'achieved', label: 'Achieved' },
]
const KPI_STATUSES = [
  { value: 'green', label: 'Green' },
  { value: 'yellow', label: 'Yellow' },
  { value: 'red', label: 'Red' },
]

export default function StrategyFormModal({
  open,
  onClose,
  onSaved,
  editItem,
  defaultType = 'company_goal',
}: StrategyFormModalProps) {
  const isEdit = !!editItem
  const [itemType, setItemType] = useState<ItemType>(defaultType)
  const [saving, setSaving] = useState(false)
  const [goals, setGoals] = useState<StrategicGoal[]>([])

  // Form fields -- goal
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [department, setDepartment] = useState('')
  const [owner, setOwner] = useState('')
  const [targetMetric, setTargetMetric] = useState('')
  const [currentValue, setCurrentValue] = useState('')
  const [targetValue, setTargetValue] = useState('')
  const [unit, setUnit] = useState('')
  const [status, setStatus] = useState('on_track')
  const [fiscalYear, setFiscalYear] = useState('FY27')
  const [priority, setPriority] = useState('0')
  const [parentGoalId, setParentGoalId] = useState('')

  // Form fields -- KPI-specific
  const [kpiName, setKpiName] = useState('')
  const [linkedGoalId, setLinkedGoalId] = useState('')
  const [kpiStatus, setKpiStatus] = useState('yellow')

  // Fetch goals for dropdowns
  const fetchGoals = useCallback(async () => {
    try {
      const data = await apiGet<StrategicGoal[]>('/api/strategy/goals')
      setGoals(data)
    } catch {
      // Silently fail -- dropdown just won't have options
    }
  }, [])

  useEffect(() => {
    if (open) {
      fetchGoals()
      if (editItem) {
        setItemType(editItem.type)
        populateForm(editItem.type, editItem.data)
      } else {
        setItemType(defaultType)
        resetForm()
      }
    }
  }, [open, editItem, defaultType, fetchGoals])

  function populateForm(type: ItemType, data: StrategicGoal | DepartmentKPI) {
    if (type === 'kpi') {
      const kpi = data as DepartmentKPI
      setKpiName(kpi.kpi_name)
      setDescription(kpi.description || '')
      setDepartment(kpi.department)
      setTargetValue(kpi.target_value.toString())
      setUnit(kpi.unit)
      setLinkedGoalId(kpi.linked_goal_id || '')
      setFiscalYear(kpi.fiscal_year)
      setKpiStatus(kpi.status)
    } else {
      const goal = data as StrategicGoal
      setTitle(goal.title)
      setDescription(goal.description || '')
      setDepartment(goal.department || '')
      setOwner(goal.owner || '')
      setTargetMetric(goal.target_metric || '')
      setCurrentValue(goal.current_value?.toString() || '')
      setTargetValue(goal.target_value?.toString() || '')
      setUnit(goal.unit || '')
      setStatus(goal.status)
      setFiscalYear(goal.fiscal_year)
      setPriority(goal.priority.toString())
      setParentGoalId(goal.parent_goal_id || '')
    }
  }

  function resetForm() {
    setTitle('')
    setDescription('')
    setDepartment('')
    setOwner('')
    setTargetMetric('')
    setCurrentValue('')
    setTargetValue('')
    setUnit('')
    setStatus('on_track')
    setFiscalYear('FY27')
    setPriority('0')
    setParentGoalId('')
    setKpiName('')
    setLinkedGoalId('')
    setKpiStatus('yellow')
  }

  async function handleSubmit() {
    setSaving(true)
    try {
      if (itemType === 'kpi') {
        await submitKPI()
      } else {
        await submitGoal()
      }
      onSaved()
      onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  async function submitGoal() {
    if (!title.trim()) {
      throw new Error('Title is required')
    }

    const payload: Record<string, unknown> = {
      level: itemType === 'company_goal' ? 'company' : 'team',
      title: title.trim(),
      description: description.trim() || null,
      target_metric: targetMetric.trim() || null,
      target_value: targetValue ? parseFloat(targetValue) : null,
      current_value: currentValue ? parseFloat(currentValue) : null,
      unit: unit.trim() || null,
      status,
      fiscal_year: fiscalYear,
      priority: parseInt(priority) || 0,
    }

    if (itemType === 'team_goal') {
      payload.department = department.trim() || null
      payload.owner = owner.trim() || null
      payload.parent_goal_id = parentGoalId || null
    }

    if (isEdit) {
      await apiPatch(`/api/strategy/goals/${(editItem!.data as StrategicGoal).id}`, payload)
      toast.success('Goal updated')
    } else {
      await apiPost('/api/strategy/goals', payload)
      toast.success('Goal created')
    }
  }

  async function submitKPI() {
    if (!kpiName.trim() || !targetValue || !unit.trim() || !department.trim()) {
      throw new Error('Name, department, target value, and unit are required')
    }

    const payload: Record<string, unknown> = {
      kpi_name: kpiName.trim(),
      description: description.trim() || null,
      department: department.trim(),
      target_value: parseFloat(targetValue),
      unit: unit.trim(),
      linked_goal_id: linkedGoalId || null,
      fiscal_year: fiscalYear,
      status: kpiStatus,
    }

    if (isEdit) {
      await apiPatch(`/api/strategy/kpis/${(editItem!.data as DepartmentKPI).id}`, payload)
      toast.success('KPI updated')
    } else {
      await apiPost('/api/strategy/kpis', payload)
      toast.success('KPI created')
    }
  }

  // Filter company goals for parent dropdown
  const companyGoals = goals.filter(
    (g) => g.level === 'company' && g.fiscal_year === fiscalYear
  )

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-card border border-default rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-default">
          <h2 className="text-lg font-semibold text-primary">
            {isEdit ? 'Edit' : 'Add'} {itemType === 'kpi' ? 'KPI' : 'Goal'}
          </h2>
          <button onClick={onClose} className="p-1 text-muted hover:text-primary rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <div className="p-4 space-y-4">
          {/* Type selector */}
          <div>
            <label className="block text-xs text-muted mb-1">Type</label>
            <select
              value={itemType}
              onChange={(e) => setItemType(e.target.value as ItemType)}
              disabled={isEdit}
              className="w-full px-3 py-2 text-sm bg-card border border-default rounded disabled:opacity-50"
            >
              <option value="company_goal">Company Goal</option>
              <option value="team_goal">Team Goal</option>
              <option value="kpi">KPI</option>
            </select>
          </div>

          {/* Fiscal Year */}
          <div>
            <label className="block text-xs text-muted mb-1">Fiscal Year</label>
            <select
              value={fiscalYear}
              onChange={(e) => setFiscalYear(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
            >
              {FISCAL_YEARS.map((fy) => (
                <option key={fy} value={fy}>{fy}</option>
              ))}
            </select>
          </div>

          {/* KPI fields */}
          {itemType === 'kpi' && (
            <>
              <div>
                <label className="block text-xs text-muted mb-1">KPI Name *</label>
                <input
                  type="text"
                  value={kpiName}
                  onChange={(e) => setKpiName(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                  placeholder="e.g. Contract Review Cycle Time"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Department *</label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                  placeholder="e.g. Legal"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-muted mb-1">Target Value *</label>
                  <input
                    type="number"
                    value={targetValue}
                    onChange={(e) => setTargetValue(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted mb-1">Unit *</label>
                  <input
                    type="text"
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                    placeholder="%, days, count"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Status</label>
                <select
                  value={kpiStatus}
                  onChange={(e) => setKpiStatus(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                >
                  {KPI_STATUSES.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Linked Goal (optional)</label>
                <select
                  value={linkedGoalId}
                  onChange={(e) => setLinkedGoalId(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                >
                  <option value="">None</option>
                  {goals.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.fiscal_year} - {g.title} ({g.level})
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}

          {/* Goal fields (company + team) */}
          {itemType !== 'kpi' && (
            <>
              <div>
                <label className="block text-xs text-muted mb-1">Title *</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                  placeholder="e.g. Market Leadership"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                />
              </div>

              {/* Team goal specific */}
              {itemType === 'team_goal' && (
                <>
                  <div>
                    <label className="block text-xs text-muted mb-1">Department</label>
                    <input
                      type="text"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                      placeholder="e.g. Legal"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-muted mb-1">Owner</label>
                    <input
                      type="text"
                      value={owner}
                      onChange={(e) => setOwner(e.target.value)}
                      className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                      placeholder="e.g. Ashley Adams"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-muted mb-1">Parent Goal</label>
                    <select
                      value={parentGoalId}
                      onChange={(e) => setParentGoalId(e.target.value)}
                      className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                    >
                      <option value="">None</option>
                      {companyGoals.map((g) => (
                        <option key={g.id} value={g.id}>{g.title}</option>
                      ))}
                    </select>
                  </div>
                </>
              )}

              <div>
                <label className="block text-xs text-muted mb-1">Target Metric</label>
                <input
                  type="text"
                  value={targetMetric}
                  onChange={(e) => setTargetMetric(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                  placeholder="e.g. DXP category leadership"
                />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-muted mb-1">Current</label>
                  <input
                    type="number"
                    value={currentValue}
                    onChange={(e) => setCurrentValue(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                    placeholder="--"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted mb-1">Target</label>
                  <input
                    type="number"
                    value={targetValue}
                    onChange={(e) => setTargetValue(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted mb-1">Unit</label>
                  <input
                    type="text"
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                    placeholder="%"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-muted mb-1">Status</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                  >
                    {GOAL_STATUSES.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-muted mb-1">Priority</label>
                  <input
                    type="number"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-2 text-sm bg-card border border-default rounded"
                    min="0"
                  />
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-4 border-t border-default">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-muted hover:bg-hover rounded"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-4 py-2 text-sm bg-primary text-white rounded hover:opacity-90 disabled:opacity-50 flex items-center gap-1.5"
          >
            {saving && <Loader2 className="w-3 h-3 animate-spin" />}
            {isEdit ? 'Save' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}
