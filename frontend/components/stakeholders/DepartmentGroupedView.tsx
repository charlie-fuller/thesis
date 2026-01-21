'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import {
  ChevronDown,
  ChevronRight,
  Building2,
  Users,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react'

// ============================================================================
// TYPES
// ============================================================================

interface Stakeholder {
  id: string
  name: string
  email: string | null
  role: string | null
  department: string | null
  organization: string
  sentiment_score: number
  sentiment_trend: string
  engagement_level: string
  alignment_score: number
  total_interactions: number
  last_interaction: string | null
  key_concerns: string[]
  interests: string[]
}

interface DepartmentGroupedViewProps {
  stakeholders: Stakeholder[]
  onDelete: (id: string, name: string) => void
}

// ============================================================================
// SENIORITY INFERENCE
// ============================================================================

// Order matters - earlier patterns are higher seniority
const SENIORITY_PATTERNS = [
  { pattern: /\b(ceo|chief executive)\b/i, level: 1 },
  { pattern: /\b(cfo|cto|coo|cmo|cio|cpo|chief)\b/i, level: 2 },
  { pattern: /\b(president)\b/i, level: 3 },
  { pattern: /\b(evp|executive vice president)\b/i, level: 4 },
  { pattern: /\b(svp|senior vice president)\b/i, level: 5 },
  { pattern: /\b(vp|vice president)\b/i, level: 6 },
  { pattern: /\b(head of|head,)\b/i, level: 7 },
  { pattern: /\b(senior director)\b/i, level: 8 },
  { pattern: /\b(director)\b/i, level: 9 },
  { pattern: /\b(senior manager)\b/i, level: 10 },
  { pattern: /\b(manager)\b/i, level: 11 },
  { pattern: /\b(lead|principal)\b/i, level: 12 },
  { pattern: /\b(senior)\b/i, level: 13 },
  { pattern: /\b(specialist|analyst|coordinator|associate)\b/i, level: 14 },
]

function getSeniorityLevel(role: string | null): number {
  if (!role) return 99 // Unknown roles go to the end

  for (const { pattern, level } of SENIORITY_PATTERNS) {
    if (pattern.test(role)) {
      return level
    }
  }

  return 50 // Default for unmatched roles
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function getEngagementBadge(level: string): string {
  switch (level) {
    case 'champion':
      return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
    case 'supporter':
      return 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300'
    case 'neutral':
      return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    case 'skeptic':
      return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
    case 'blocker':
      return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
    default:
      return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
  }
}

function getSentimentColor(score: number): string {
  if (score > 0.3) return 'text-green-600 dark:text-green-400'
  if (score < -0.3) return 'text-red-600 dark:text-red-400'
  return 'text-slate-500'
}

function formatDepartmentName(dept: string): string {
  return dept.charAt(0).toUpperCase() + dept.slice(1)
}

// ============================================================================
// DEPARTMENT PANEL COMPONENT
// ============================================================================

function DepartmentPanel({
  department,
  stakeholders,
  isExpanded,
  onToggle,
  onViewStakeholder,
  onDeleteStakeholder
}: {
  department: string
  stakeholders: Stakeholder[]
  isExpanded: boolean
  onToggle: () => void
  onViewStakeholder: (id: string) => void
  onDeleteStakeholder: (id: string, name: string) => void
}) {
  // Calculate department stats
  const avgSentiment = stakeholders.length > 0
    ? stakeholders.reduce((sum, s) => sum + s.sentiment_score, 0) / stakeholders.length
    : 0

  const championCount = stakeholders.filter(s => s.engagement_level === 'champion').length
  const skepticCount = stakeholders.filter(s => ['skeptic', 'blocker'].includes(s.engagement_level)).length

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      {/* Header - Always visible */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-slate-400" />
          )}
          <Building2 className="w-5 h-5 text-slate-500" />
          <span className="font-semibold text-slate-900 dark:text-white">
            {formatDepartmentName(department)}
          </span>
          <span className="text-sm text-slate-500">
            ({stakeholders.length})
          </span>
        </div>

        {/* Quick stats */}
        <div className="flex items-center gap-4 text-sm">
          {championCount > 0 && (
            <span className="text-green-600 dark:text-green-400">
              {championCount} champion{championCount !== 1 ? 's' : ''}
            </span>
          )}
          {skepticCount > 0 && (
            <span className="text-orange-600 dark:text-orange-400">
              {skepticCount} skeptic{skepticCount !== 1 ? 's' : ''}
            </span>
          )}
          <span className={getSentimentColor(avgSentiment)}>
            Avg: {avgSentiment > 0 ? '+' : ''}{avgSentiment.toFixed(1)}
          </span>
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-slate-200 dark:border-slate-800">
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {stakeholders.map((stakeholder) => (
              <div
                key={stakeholder.id}
                className="px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    {/* Avatar */}
                    <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-sm font-medium text-slate-600 dark:text-slate-400 flex-shrink-0">
                      {stakeholder.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </div>

                    {/* Name and role */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-900 dark:text-white truncate">
                          {stakeholder.name}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${getEngagementBadge(stakeholder.engagement_level)}`}>
                          {stakeholder.engagement_level}
                        </span>
                      </div>
                      {stakeholder.role && (
                        <p className="text-sm text-slate-500 truncate">
                          {stakeholder.role}
                        </p>
                      )}
                    </div>

                    {/* Metrics */}
                    <div className="flex items-center gap-6 text-sm flex-shrink-0">
                      <div className="text-center">
                        <div className={`font-medium ${getSentimentColor(stakeholder.sentiment_score)}`}>
                          {stakeholder.sentiment_score > 0 ? '+' : ''}{stakeholder.sentiment_score.toFixed(1)}
                        </div>
                        <div className="text-xs text-slate-400 flex items-center gap-1">
                          Sentiment
                          {stakeholder.sentiment_trend === 'improving' && <TrendingUp className="w-3 h-3 text-green-500" />}
                          {stakeholder.sentiment_trend === 'declining' && <TrendingDown className="w-3 h-3 text-red-500" />}
                          {stakeholder.sentiment_trend === 'stable' && <Minus className="w-3 h-3 text-slate-400" />}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium text-teal-600 dark:text-teal-400">
                          {Math.round(stakeholder.alignment_score * 100)}%
                        </div>
                        <div className="text-xs text-slate-400">Alignment</div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium text-slate-600 dark:text-slate-300">
                          {stakeholder.total_interactions}
                        </div>
                        <div className="text-xs text-slate-400">Meetings</div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => onViewStakeholder(stakeholder.id)}
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      View
                    </button>
                    <button
                      onClick={() => onDeleteStakeholder(stakeholder.id, stakeholder.name)}
                      className="text-sm text-red-600 dark:text-red-400 hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {/* Key concerns */}
                {stakeholder.key_concerns.length > 0 && (
                  <div className="mt-2 ml-14 flex flex-wrap gap-1">
                    {stakeholder.key_concerns.slice(0, 3).map((concern, i) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-0.5 bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300 rounded"
                      >
                        {concern}
                      </span>
                    ))}
                    {stakeholder.key_concerns.length > 3 && (
                      <span className="text-xs text-slate-400">
                        +{stakeholder.key_concerns.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DepartmentGroupedView({
  stakeholders,
  onDelete
}: DepartmentGroupedViewProps) {
  const router = useRouter()
  const [expandedDepartments, setExpandedDepartments] = useState<Set<string>>(new Set())

  // Group stakeholders by department and sort by seniority
  const groupedStakeholders = useMemo(() => {
    const groups: Record<string, Stakeholder[]> = {}

    for (const stakeholder of stakeholders) {
      const dept = stakeholder.department || 'unassigned'
      if (!groups[dept]) {
        groups[dept] = []
      }
      groups[dept].push(stakeholder)
    }

    // Sort each group by seniority (most senior first)
    for (const dept of Object.keys(groups)) {
      groups[dept].sort((a, b) => {
        const seniorityA = getSeniorityLevel(a.role)
        const seniorityB = getSeniorityLevel(b.role)
        return seniorityA - seniorityB
      })
    }

    // Sort departments alphabetically, but put 'unassigned' last
    const sortedDepts = Object.keys(groups).sort((a, b) => {
      if (a === 'unassigned') return 1
      if (b === 'unassigned') return -1
      return a.localeCompare(b)
    })

    return sortedDepts.map(dept => ({
      department: dept,
      stakeholders: groups[dept]
    }))
  }, [stakeholders])

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

  const expandAll = () => {
    setExpandedDepartments(new Set(groupedStakeholders.map(g => g.department)))
  }

  const collapseAll = () => {
    setExpandedDepartments(new Set())
  }

  if (stakeholders.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-12 text-center">
        <Users className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
          No stakeholders yet
        </h3>
        <p className="text-slate-500">
          Add stakeholders manually or upload transcripts to auto-populate.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Users className="w-4 h-4" />
          {stakeholders.length} stakeholder{stakeholders.length !== 1 ? 's' : ''} across {groupedStakeholders.length} department{groupedStakeholders.length !== 1 ? 's' : ''}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={expandAll}
            className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          >
            Expand all
          </button>
          <span className="text-slate-300 dark:text-slate-600">|</span>
          <button
            onClick={collapseAll}
            className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          >
            Collapse all
          </button>
        </div>
      </div>

      {/* Department panels */}
      {groupedStakeholders.map(({ department, stakeholders: deptStakeholders }) => (
        <DepartmentPanel
          key={department}
          department={department}
          stakeholders={deptStakeholders}
          isExpanded={expandedDepartments.has(department)}
          onToggle={() => toggleDepartment(department)}
          onViewStakeholder={(id) => router.push(`/stakeholders/${id}`)}
          onDeleteStakeholder={onDelete}
        />
      ))}
    </div>
  )
}
