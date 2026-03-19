'use client'

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { apiGet, authenticatedFetch } from '@/lib/api'
import LoadingSpinner from '@/components/LoadingSpinner'
import PortfolioScatterPlot from '@/components/PortfolioScatterPlot'
import PortfolioTable from '@/components/PortfolioTable'

export interface PortfolioProject {
  id: string
  client_id: string
  name: string
  department: string
  owner: string | null
  status: string
  start_date: string | null
  effort: string | null
  investment: string | null
  business_value: string | null
  tools_platform: string | null
  category: string | null
  description: string | null
  created_at: string
  updated_at: string
}

export default function PortfolioContent() {
  const [projects, setProjects] = useState<PortfolioProject[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [departmentFilter, setDepartmentFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchProjects = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiGet<PortfolioProject[]>('/api/portfolio/projects')
      setProjects(data)
    } catch (err) {
      console.error('Failed to fetch portfolio projects:', err)
      setError(err instanceof Error ? err.message : 'Failed to load portfolio projects')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      if (departmentFilter && p.department !== departmentFilter) return false
      if (statusFilter && p.status !== statusFilter) return false
      return true
    })
  }, [projects, departmentFilter, statusFilter])

  const departments = useMemo(() => {
    const depts = [...new Set(projects.map((p) => p.department).filter(Boolean))]
    return depts.sort()
  }, [projects])

  const statusCounts = useMemo(() => {
    return {
      total: filteredProjects.length,
      planned: filteredProjects.filter((p) => p.status === 'planned').length,
      in_progress: filteredProjects.filter((p) => p.status === 'in_progress').length,
      completed: filteredProjects.filter((p) => p.status === 'completed').length,
    }
  }, [filteredProjects])

  const handleImportCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await authenticatedFetch('/api/portfolio/projects/import', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Import failed')
      }

      const result = await response.json()
      alert(`Successfully imported ${result.imported} projects.`)
      fetchProjects()
    } catch (err) {
      console.error('CSV import failed:', err)
      alert(err instanceof Error ? err.message : 'Failed to import CSV')
    } finally {
      // Reset file input so the same file can be re-selected
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleExportCSV = async () => {
    try {
      const params = new URLSearchParams()
      if (departmentFilter) params.set('department', departmentFilter)
      if (statusFilter) params.set('status', statusFilter)

      const queryString = params.toString()
      const url = `/api/portfolio/projects/export${queryString ? `?${queryString}` : ''}`

      const response = await authenticatedFetch(url)

      if (!response.ok) {
        throw new Error('Export failed')
      }

      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `portfolio-export-${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      console.error('CSV export failed:', err)
      alert(err instanceof Error ? err.message : 'Failed to export CSV')
    }
  }

  if (loading) {
    return (
      <div className="flex-1 p-6 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 p-6">
        <div className="max-w-[1600px] mx-auto">
          <div className="bg-card border border-default rounded-lg p-8 text-center">
            <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
            <button
              onClick={fetchProjects}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-6">
      <div className="max-w-[1600px] mx-auto space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-card border border-default rounded-lg p-4">
            <p className="text-xs font-medium text-muted uppercase tracking-wider">Total Projects</p>
            <p className="text-2xl font-bold text-primary mt-1">{statusCounts.total}</p>
          </div>
          <div className="bg-card border border-default rounded-lg p-4">
            <p className="text-xs font-medium text-muted uppercase tracking-wider">Planned</p>
            <p className="text-2xl font-bold text-slate-600 dark:text-slate-400 mt-1">{statusCounts.planned}</p>
          </div>
          <div className="bg-card border border-default rounded-lg p-4">
            <p className="text-xs font-medium text-muted uppercase tracking-wider">In Progress</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{statusCounts.in_progress}</p>
          </div>
          <div className="bg-card border border-default rounded-lg p-4">
            <p className="text-xs font-medium text-muted uppercase tracking-wider">Completed</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{statusCounts.completed}</p>
          </div>
        </div>

        {/* Filter Row */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="bg-card border border-default rounded-lg px-3 py-2 text-sm text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Departments</option>
            {departments.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-card border border-default rounded-lg px-3 py-2 text-sm text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="planned">Planned</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>

          <div className="ml-auto flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleImportCSV}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-card border border-default rounded-lg text-sm text-primary hover:bg-hover transition-colors"
            >
              Import CSV
            </button>
            <button
              onClick={handleExportCSV}
              className="px-4 py-2 bg-card border border-default rounded-lg text-sm text-primary hover:bg-hover transition-colors"
            >
              Export CSV
            </button>
          </div>
        </div>

        {/* Scatter Plot */}
        <PortfolioScatterPlot projects={filteredProjects} />

        {/* Table */}
        <PortfolioTable projects={filteredProjects} />
      </div>
    </div>
  )
}
