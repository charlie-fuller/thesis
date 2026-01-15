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
  { value: 'opportunity', label: 'Opportunity' },
]

export default function TaskFilters({ filters, onChange, onClose }: TaskFiltersProps) {
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [searchValue, setSearchValue] = useState(filters.search || '')

  // Load stakeholders
  useEffect(() => {
    const loadStakeholders = async () => {
      try {
        const response = await apiGet<{ success: boolean; stakeholders: Stakeholder[] }>('/api/stakeholders')
        if (response.success) {
          setStakeholders(response.stakeholders)
        }
      } catch (error) {
        console.error('Failed to load stakeholders:', error)
      }
    }
    loadStakeholders()
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
    <div className="bg-card border border-default rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-primary">Filters</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={handleClearAll}
            className="text-sm text-muted hover:text-primary transition-colors"
          >
            Clear all
          </button>
          <button
            onClick={onClose}
            className="p-1 text-muted hover:text-primary rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Search</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder="Search tasks..."
              className="w-full pl-9 pr-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
            />
          </div>
        </div>

        {/* Assignee */}
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Assignee</label>
          <select
            value={filters.assignee_stakeholder_id || ''}
            onChange={(e) => onChange({ ...filters, assignee_stakeholder_id: e.target.value || null })}
            className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
          >
            <option value="">All assignees</option>
            {stakeholders.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        {/* Due Date From */}
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Due From</label>
          <input
            type="date"
            value={filters.due_date_from || ''}
            onChange={(e) => onChange({ ...filters, due_date_from: e.target.value || null })}
            className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>

        {/* Due Date To */}
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Due To</label>
          <input
            type="date"
            value={filters.due_date_to || ''}
            onChange={(e) => onChange({ ...filters, due_date_to: e.target.value || null })}
            className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>
      </div>

      {/* Priority & Source Type */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Priority */}
        <div>
          <label className="block text-sm font-medium text-secondary mb-2">Priority</label>
          <div className="flex flex-wrap gap-2">
            {PRIORITY_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => handlePriorityToggle(opt.value)}
                className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                  filters.priority?.includes(opt.value)
                    ? 'bg-brand text-white border-brand'
                    : 'border-default text-muted hover:border-brand hover:text-brand'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Source Type */}
        <div>
          <label className="block text-sm font-medium text-secondary mb-2">Source</label>
          <div className="flex flex-wrap gap-2">
            {SOURCE_TYPE_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => handleSourceToggle(opt.value)}
                className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                  filters.source_type?.includes(opt.value)
                    ? 'bg-brand text-white border-brand'
                    : 'border-default text-muted hover:border-brand hover:text-brand'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Include Completed Toggle */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="include-completed"
          checked={filters.include_completed}
          onChange={(e) => onChange({ ...filters, include_completed: e.target.checked })}
          className="w-4 h-4 rounded border-default text-brand focus:ring-brand"
        />
        <label htmlFor="include-completed" className="text-sm text-secondary">
          Show completed tasks
        </label>
      </div>
    </div>
  )
}
