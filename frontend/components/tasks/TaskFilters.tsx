'use client'

import { useState, useEffect } from 'react'
import { X, Search } from 'lucide-react'
import { apiGet } from '@/lib/api'
import { TaskFiltersState } from './TaskKanbanBoard'

interface TaskFiltersProps {
  filters: TaskFiltersState
  onChange: (filters: TaskFiltersState) => void
  onClose: () => void
}

interface Stakeholder {
  id: string
  name: string
  email: string
  department?: string
}

interface Project {
  id: string
  title: string
  project_name: string | null
  project_code: string
}

const TEAM_OPTIONS = [
  'Finance',
  'Legal',
  'IT',
  'HR',
  'Operations',
  'Marketing',
  'Sales',
  'Engineering',
  'Executive',
  'Other',
]

const PRIORITY_OPTIONS = [
  { value: 1, label: 'Low' },
  { value: 2, label: 'Medium-Low' },
  { value: 3, label: 'Medium' },
  { value: 4, label: 'High' },
  { value: 5, label: 'Critical' },
]

const SOURCE_TYPE_OPTIONS = [
  { value: 'transcript', label: 'Transcript' },
  { value: 'conversation', label: 'Conversation' },
  { value: 'research', label: 'Research' },
  { value: 'manual', label: 'Manual' },
  { value: 'project', label: 'Project' },
]

export default function TaskFilters({ filters, onChange, onClose }: TaskFiltersProps) {
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [projectsList, setProjectsList] = useState<Project[]>([])
  const [searchValue, setSearchValue] = useState(filters.search || '')

  // Load stakeholders and projects
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load stakeholders
        const stakeholderResponse = await apiGet<{ success: boolean; stakeholders: Stakeholder[] }>('/api/stakeholders')
        if (stakeholderResponse.success) {
          setStakeholders(stakeholderResponse.stakeholders)
        }

        // Load projects for project filter
        const projResponse = await apiGet<Project[]>('/api/projects')
        if (Array.isArray(projResponse)) {
          setProjectsList(projResponse)
        }
      } catch (error) {
        console.error('Failed to load filter data:', error)
      }
    }
    loadData()
  }, [])

  // Debounced search
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (searchValue !== filters.search) {
        onChange({ ...filters, search: searchValue || null })
      }
    }, 300)
    return () => clearTimeout(timeout)
  }, [searchValue, filters, onChange])

  const handleClearAll = () => {
    setSearchValue('')
    onChange({
      assignee_stakeholder_id: null,
      due_date_from: null,
      due_date_to: null,
      priority: null,
      source_type: null,
      team: null,
      linked_project_id: null,
      search: null,
      include_completed: true,
    })
  }

  const handlePriorityToggle = (value: number) => {
    const current = filters.priority || []
    const newPriority = current.includes(value)
      ? current.filter(p => p !== value)
      : [...current, value]
    onChange({ ...filters, priority: newPriority.length > 0 ? newPriority : null })
  }

  const handleSourceToggle = (value: string) => {
    const current = filters.source_type || []
    const newSource = current.includes(value)
      ? current.filter(s => s !== value)
      : [...current, value]
    onChange({ ...filters, source_type: newSource.length > 0 ? newSource : null })
  }

  return (
    <div className="bg-card border border-default rounded-lg px-3 py-2">
      {/* Row 1: Search + Dropdowns */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Search..."
            className="w-40 pl-8 pr-2 py-1.5 text-sm border border-default rounded-md bg-card text-primary focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>

        {/* Assignee */}
        <select
          value={filters.assignee_stakeholder_id || ''}
          onChange={(e) => onChange({ ...filters, assignee_stakeholder_id: e.target.value || null })}
          className="px-2 py-1.5 text-sm border border-default rounded-md bg-card text-primary focus:outline-none focus:ring-1 focus:ring-brand"
        >
          <option value="">Assignee</option>
          {stakeholders.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        {/* Team */}
        <select
          value={filters.team || ''}
          onChange={(e) => onChange({ ...filters, team: e.target.value || null })}
          className="px-2 py-1.5 text-sm border border-default rounded-md bg-card text-primary focus:outline-none focus:ring-1 focus:ring-brand"
        >
          <option value="">Team</option>
          {TEAM_OPTIONS.map(team => (
            <option key={team} value={team}>{team}</option>
          ))}
        </select>

        {/* Project */}
        <select
          value={filters.linked_project_id || ''}
          onChange={(e) => onChange({ ...filters, linked_project_id: e.target.value || null })}
          className="px-2 py-1.5 text-sm border border-default rounded-md bg-card text-primary focus:outline-none focus:ring-1 focus:ring-brand max-w-[140px]"
        >
          <option value="">Project</option>
          {projectsList.map(proj => (
            <option key={proj.id} value={proj.id}>
              {proj.project_code}
            </option>
          ))}
        </select>

        {/* Due From */}
        <div className="flex items-center gap-1">
          <span className="text-xs text-muted">Due:</span>
          <input
            type="date"
            value={filters.due_date_from || ''}
            onChange={(e) => onChange({ ...filters, due_date_from: e.target.value || null })}
            className="px-2 py-1.5 text-sm border border-default rounded-md bg-card text-primary focus:outline-none focus:ring-1 focus:ring-brand"
          />
          <span className="text-xs text-muted">to</span>
          <input
            type="date"
            value={filters.due_date_to || ''}
            onChange={(e) => onChange({ ...filters, due_date_to: e.target.value || null })}
            className="px-2 py-1.5 text-sm border border-default rounded-md bg-card text-primary focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Clear + Close */}
        <button
          onClick={handleClearAll}
          className="text-xs text-muted hover:text-primary transition-colors"
        >
          Clear
        </button>
        <button
          onClick={onClose}
          className="p-1 text-muted hover:text-primary rounded transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Row 2: Priority + Source + Completed */}
      <div className="flex flex-wrap items-center gap-2 mt-2 pt-2 border-t border-default">
        {/* Priority */}
        <span className="text-xs text-muted">Priority:</span>
        <div className="flex gap-1">
          {PRIORITY_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => handlePriorityToggle(opt.value)}
              className={`px-2 py-0.5 text-xs rounded-full border transition-colors ${
                filters.priority?.includes(opt.value)
                  ? 'bg-brand text-white border-brand'
                  : 'border-default text-muted hover:border-brand hover:text-brand'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <span className="text-default">|</span>

        {/* Source Type */}
        <span className="text-xs text-muted">Source:</span>
        <div className="flex gap-1">
          {SOURCE_TYPE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => handleSourceToggle(opt.value)}
              className={`px-2 py-0.5 text-xs rounded-full border transition-colors ${
                filters.source_type?.includes(opt.value)
                  ? 'bg-brand text-white border-brand'
                  : 'border-default text-muted hover:border-brand hover:text-brand'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <span className="text-default">|</span>

        {/* Include Completed Toggle */}
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.include_completed}
            onChange={(e) => onChange({ ...filters, include_completed: e.target.checked })}
            className="w-3.5 h-3.5 rounded border-default text-brand focus:ring-brand"
          />
          <span className="text-xs text-secondary">Show completed</span>
        </label>
      </div>
    </div>
  )
}
