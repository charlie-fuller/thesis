'use client'

import { useState, useMemo } from 'react'
import type { PortfolioProject } from './PortfolioContent'

interface PortfolioTableProps {
  projects: PortfolioProject[]
}

type SortField =
  | 'name'
  | 'department'
  | 'owner'
  | 'status'
  | 'effort'
  | 'investment'
  | 'business_value'
  | 'tools_platform'
  | 'category'
  | 'start_date'

type SortDirection = 'asc' | 'desc'

const STATUS_DISPLAY: Record<string, string> = {
  planned: 'Planned',
  in_progress: 'In Progress',
  completed: 'Completed',
}

const STATUS_BADGE_CLASSES: Record<string, string> = {
  planned: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-800 dark:text-blue-300',
  completed: 'bg-green-100 text-green-700 dark:bg-green-800 dark:text-green-300',
}

// For sorting ordinal values
const EFFORT_ORDER: Record<string, number> = { low: 1, medium: 2, high: 3 }
const VALUE_ORDER: Record<string, number> = { low: 1, medium: 2, high: 3, critical: 4 }
const INVESTMENT_ORDER: Record<string, number> = {
  '0-1k': 1,
  '1k-5k': 2,
  '5k-15k': 3,
  '15k-25k': 4,
  '25k+': 5,
}

function capitalize(val: string | null): string {
  if (!val) return '--'
  return val.charAt(0).toUpperCase() + val.slice(1)
}

function formatDate(val: string | null): string {
  if (!val) return '--'
  try {
    return new Date(val).toLocaleDateString()
  } catch {
    return val
  }
}

const COLUMNS: { key: SortField; label: string }[] = [
  { key: 'name', label: 'Name' },
  { key: 'department', label: 'Department' },
  { key: 'owner', label: 'Owner' },
  { key: 'status', label: 'Status' },
  { key: 'effort', label: 'Effort' },
  { key: 'investment', label: 'Investment' },
  { key: 'business_value', label: 'Value' },
  { key: 'tools_platform', label: 'Tools' },
  { key: 'category', label: 'Category' },
  { key: 'start_date', label: 'Start Date' },
]

export default function PortfolioTable({ projects }: PortfolioTableProps) {
  const [sortField, setSortField] = useState<SortField>('name')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedProjects = useMemo(() => {
    const sorted = [...projects]
    sorted.sort((a, b) => {
      let aVal: string | number | null = null
      let bVal: string | number | null = null

      switch (sortField) {
        case 'effort':
          aVal = EFFORT_ORDER[a.effort?.toLowerCase() ?? ''] ?? 0
          bVal = EFFORT_ORDER[b.effort?.toLowerCase() ?? ''] ?? 0
          break
        case 'business_value':
          aVal = VALUE_ORDER[a.business_value?.toLowerCase() ?? ''] ?? 0
          bVal = VALUE_ORDER[b.business_value?.toLowerCase() ?? ''] ?? 0
          break
        case 'investment':
          aVal = INVESTMENT_ORDER[a.investment?.toLowerCase() ?? ''] ?? 0
          bVal = INVESTMENT_ORDER[b.investment?.toLowerCase() ?? ''] ?? 0
          break
        case 'start_date':
          aVal = a.start_date ? new Date(a.start_date).getTime() : 0
          bVal = b.start_date ? new Date(b.start_date).getTime() : 0
          break
        default:
          aVal = (a[sortField] ?? '').toString().toLowerCase()
          bVal = (b[sortField] ?? '').toString().toLowerCase()
          break
      }

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
      }

      const aStr = String(aVal)
      const bStr = String(bVal)
      const cmp = aStr.localeCompare(bStr)
      return sortDirection === 'asc' ? cmp : -cmp
    })
    return sorted
  }, [projects, sortField, sortDirection])

  if (projects.length === 0) {
    return (
      <div className="bg-card border border-default rounded-lg p-8 text-center">
        <h3 className="text-lg font-medium text-primary mb-2">No projects found</h3>
        <p className="text-muted text-sm">
          Adjust your filters or import a CSV to get started.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-card border border-default rounded-lg overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                className="bg-hover text-muted text-xs font-medium uppercase tracking-wider px-4 py-3 text-left cursor-pointer select-none hover:text-primary transition-colors whitespace-nowrap"
              >
                <span className="inline-flex items-center gap-1">
                  {col.label}
                  {sortField === col.key && (
                    <span className="text-primary">
                      {sortDirection === 'asc' ? '\u2191' : '\u2193'}
                    </span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedProjects.map((project) => (
            <tr
              key={project.id}
              className="hover:bg-hover transition-colors border-t border-default"
            >
              <td className="px-4 py-3 font-medium text-primary whitespace-nowrap">
                {project.name}
              </td>
              <td className="px-4 py-3 text-muted whitespace-nowrap">
                {project.department}
              </td>
              <td className="px-4 py-3 text-muted whitespace-nowrap">
                {project.owner ?? '--'}
              </td>
              <td className="px-4 py-3 whitespace-nowrap">
                <span
                  className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                    STATUS_BADGE_CLASSES[project.status] ?? ''
                  }`}
                >
                  {STATUS_DISPLAY[project.status] ?? project.status}
                </span>
              </td>
              <td className="px-4 py-3 text-muted whitespace-nowrap">
                {capitalize(project.effort)}
              </td>
              <td className="px-4 py-3 text-muted whitespace-nowrap">
                {project.investment ?? '--'}
              </td>
              <td className="px-4 py-3 text-muted whitespace-nowrap">
                {capitalize(project.business_value)}
              </td>
              <td className="px-4 py-3 text-muted whitespace-nowrap">
                {project.tools_platform ?? '--'}
              </td>
              <td className="px-4 py-3 text-muted whitespace-nowrap">
                {project.category ?? '--'}
              </td>
              <td className="px-4 py-3 text-muted whitespace-nowrap">
                {formatDate(project.start_date)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
