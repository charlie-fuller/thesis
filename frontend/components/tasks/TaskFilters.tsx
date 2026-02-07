'use client'

import { useState, useEffect, useRef, useMemo } from 'react'
import { X, Search } from 'lucide-react'
import { apiGet } from '@/lib/api'
import { Task, TaskFiltersState } from './TaskKanbanBoard'

interface TaskFiltersProps {
  filters: TaskFiltersState
  onChange: (filters: TaskFiltersState) => void
  onClose: () => void
  tasks?: Task[]  // Current tasks for cascading filter context
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
  department: string | null
  owner_name?: string | null
}

const TEAM_OPTIONS = [
  'Finance',
  'Legal',
  'IT',
  'People',
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

export default function TaskFilters({ filters, onChange, onClose, tasks = [] }: TaskFiltersProps) {
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [projectsList, setProjectsList] = useState<Project[]>([])
  const [searchValue, setSearchValue] = useState(filters.search || '')

  // Load stakeholders and projects
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load stakeholders
        const stakeholderResponse = await apiGet<Stakeholder[]>('/api/stakeholders')
        if (Array.isArray(stakeholderResponse)) {
          setStakeholders(stakeholderResponse)
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

  // Debounced search - only trigger when searchValue actually changes
  const prevSearchRef = useRef(searchValue)
  useEffect(() => {
    if (prevSearchRef.current === searchValue) return
    prevSearchRef.current = searchValue

    const timeout = setTimeout(() => {
      onChange({ ...filters, search: searchValue || null })
    }, 300)
    return () => clearTimeout(timeout)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchValue])

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

  // Map team filter values to project department values (case-insensitive match)
  const TEAM_TO_DEPARTMENT: Record<string, string[]> = {
    'Finance': ['finance', 'Finance'],
    'Legal': ['legal', 'Legal'],
    'IT': ['it', 'IT', 'technology', 'Technology'],
    'People': ['people', 'People', 'hr', 'HR', 'human resources', 'Human Resources'],
    'Operations': ['operations', 'Operations'],
    'Marketing': ['marketing', 'Marketing'],
    'Sales': ['sales', 'Sales'],
    'Engineering': ['engineering', 'Engineering'],
    'Executive': ['executive', 'Executive', 'leadership', 'Leadership'],
    'Other': [],
  }

  // Filter assignees: when team or project is selected, only show assignees from matching tasks
  const filteredStakeholders = useMemo(() => {
    if (!filters.team && !filters.linked_project_id) return stakeholders

    // Get assignee IDs from tasks that match the current team/project filters
    const matchingTasks = tasks.filter(t => {
      if (filters.team && t.team !== filters.team) return false
      if (filters.linked_project_id && t.linked_project_id !== filters.linked_project_id) return false
      return true
    })

    const assigneeIds = new Set(
      matchingTasks
        .map(t => t.assignee_stakeholder_id)
        .filter((id): id is string => id != null)
    )

    // If no tasks match yet (empty set), show all stakeholders so user can still pick
    if (assigneeIds.size === 0) return stakeholders

    return stakeholders.filter(s => assigneeIds.has(s.id))
  }, [stakeholders, tasks, filters.team, filters.linked_project_id])

  // Filter projects by selected team
  const filteredProjects = filters.team
    ? projectsList.filter(proj => {
        if (!proj.department) return false
        const deptVariants = TEAM_TO_DEPARTMENT[filters.team!] || []
        return deptVariants.some(d => proj.department?.toLowerCase() === d.toLowerCase())
      })
    : projectsList

  return (
    <div className="bg-card border border-default rounded-lg px-3 py-2">
      {/* Row 1: Search + Dropdowns */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative flex-1 min-w-[160px] max-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Search tasks..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Assignee */}
        <select
          value={filters.assignee_stakeholder_id || ''}
          onChange={(e) => onChange({ ...filters, assignee_stakeholder_id: e.target.value || null })}
          className="px-3 py-2 text-sm border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Assignee{filters.team || filters.linked_project_id ? ` (${filteredStakeholders.length})` : ''}</option>
          {filteredStakeholders.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        {/* Team */}
        <select
          value={filters.team || ''}
          onChange={(e) => {
            const newTeam = e.target.value || null
            // Clear project and assignee selections if they won't match the new team filter
            const updates: Partial<TaskFiltersState> = { team: newTeam }
            if (newTeam && filters.linked_project_id) {
              const proj = projectsList.find(p => p.id === filters.linked_project_id)
              const deptVariants = TEAM_TO_DEPARTMENT[newTeam] || []
              const projectMatchesTeam = proj?.department && deptVariants.some(d => proj.department?.toLowerCase() === d.toLowerCase())
              if (!projectMatchesTeam) {
                updates.linked_project_id = null
              }
            }
            // Clear assignee if it won't be in the new filtered set
            if (filters.assignee_stakeholder_id) {
              updates.assignee_stakeholder_id = null
            }
            onChange({ ...filters, ...updates })
          }}
          className="px-3 py-2 text-sm border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          className="px-3 py-2 text-sm border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[200px] max-w-[320px]"
        >
          <option value="">Project{filters.team ? ` (${filters.team})` : ''}</option>
          {filteredProjects.map(proj => (
            <option key={proj.id} value={proj.id}>
              {proj.project_code} — {proj.title}
            </option>
          ))}
        </select>

        {/* Due From */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted">Due:</span>
          <input
            type="date"
            value={filters.due_date_from || ''}
            onChange={(e) => onChange({ ...filters, due_date_from: e.target.value || null })}
            className="px-3 py-2 text-sm border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-xs text-muted">to</span>
          <input
            type="date"
            value={filters.due_date_to || ''}
            onChange={(e) => onChange({ ...filters, due_date_to: e.target.value || null })}
            className="px-3 py-2 text-sm border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
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
      <div className="flex flex-wrap items-center gap-3 mt-2 pt-2 border-t border-default">
        {/* Priority */}
        <span className="text-sm text-muted">Priority:</span>
        <div className="flex gap-1.5">
          {PRIORITY_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => handlePriorityToggle(opt.value)}
              className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
                filters.priority?.includes(opt.value)
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'border-default bg-card text-muted hover:border-blue-300 hover:text-blue-600'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Source Type */}
        <span className="text-sm text-muted ml-2">Source:</span>
        <div className="flex gap-1.5">
          {SOURCE_TYPE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => handleSourceToggle(opt.value)}
              className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
                filters.source_type?.includes(opt.value)
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'border-default bg-card text-muted hover:border-blue-300 hover:text-blue-600'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Include Completed Toggle */}
        <label className="flex items-center gap-2 cursor-pointer ml-2">
          <input
            type="checkbox"
            checked={filters.include_completed}
            onChange={(e) => onChange({ ...filters, include_completed: e.target.checked })}
            className="w-4 h-4 rounded border-default text-blue-500 focus:ring-blue-500"
          />
          <span className="text-sm text-secondary">Show completed</span>
        </label>
      </div>
    </div>
  )
}
