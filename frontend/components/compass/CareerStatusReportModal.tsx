'use client'

/**
 * CareerStatusReportModal Component
 *
 * Displays a career status report with:
 * - Overall score visualization
 * - Executive summary
 * - 5 dimension scores with justifications
 * - Strengths, growth opportunities, and recommended actions
 */

import { useState, useEffect } from 'react'
import {
  X,
  Trophy,
  TrendingUp,
  Target,
  Lightbulb,
  Calendar,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { apiGet } from '@/lib/api'
import ScoreDimensionCard, { type Dimension } from './ScoreDimensionCard'

// ============================================================================
// TYPES
// ============================================================================

interface CareerStatusReport {
  id: string
  report_date: string
  period_start: string | null
  period_end: string | null

  // Scores
  strategic_impact: number | null
  execution_quality: number | null
  relationship_building: number | null
  growth_mindset: number | null
  leadership_presence: number | null
  overall_score: number | null

  // AI-generated content
  executive_summary: string | null
  strategic_impact_justification: string | null
  execution_quality_justification: string | null
  relationship_building_justification: string | null
  growth_mindset_justification: string | null
  leadership_presence_justification: string | null

  // Evidence and recommendations
  areas_of_strength: string[]
  growth_opportunities: string[]
  recommended_actions: string[]

  // Metadata
  data_sources: {
    kb_documents?: number
    memories?: number
  }
  created_at: string
}

interface RubricDimension {
  key: string
  name: string
  weight: number
  description: string
  levels: Record<number, string>
}

interface CareerStatusReportModalProps {
  report: CareerStatusReport
  open: boolean
  onClose: () => void
  onRegenerate?: () => void
  regenerating?: boolean
}

// ============================================================================
// SCORE LEVEL CONFIG
// ============================================================================

const OVERALL_LEVEL_CONFIG: Record<string, { label: string; color: string; bg: string; range: string }> = {
  exceptional: {
    label: 'Exceptional Performance',
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900/30',
    range: '4.5-5.0',
  },
  strong: {
    label: 'Strong Performance',
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    range: '3.5-4.4',
  },
  solid: {
    label: 'Solid Performance',
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    range: '2.5-3.4',
  },
  developing: {
    label: 'Developing',
    color: 'text-orange-600 dark:text-orange-400',
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    range: '1.5-2.4',
  },
  foundational: {
    label: 'Foundational',
    color: 'text-slate-600 dark:text-slate-400',
    bg: 'bg-slate-100 dark:bg-slate-800',
    range: '<1.5',
  },
}

function getOverallLevel(score: number | null): typeof OVERALL_LEVEL_CONFIG.exceptional {
  if (!score) return OVERALL_LEVEL_CONFIG.foundational
  if (score >= 4.5) return OVERALL_LEVEL_CONFIG.exceptional
  if (score >= 3.5) return OVERALL_LEVEL_CONFIG.strong
  if (score >= 2.5) return OVERALL_LEVEL_CONFIG.solid
  if (score >= 1.5) return OVERALL_LEVEL_CONFIG.developing
  return OVERALL_LEVEL_CONFIG.foundational
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function CareerStatusReportModal({
  report,
  open,
  onClose,
  onRegenerate,
  regenerating = false,
}: CareerStatusReportModalProps) {
  const [rubric, setRubric] = useState<RubricDimension[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory] = useState<Array<{ id: string; report_date: string; overall_score: number | null }>>([])
  const [historyLoading, setHistoryLoading] = useState(false)

  // Fetch rubric on mount
  useEffect(() => {
    async function fetchRubric() {
      try {
        const data = await apiGet<{ dimensions: RubricDimension[] }>('/api/compass/rubric')
        setRubric(data.dimensions || [])
      } catch (err) {
        console.error('Failed to fetch rubric:', err)
      }
    }
    if (open) {
      fetchRubric()
    }
  }, [open])

  // Fetch history when expanded
  useEffect(() => {
    async function fetchHistory() {
      setHistoryLoading(true)
      try {
        const data = await apiGet<Array<{ id: string; report_date: string; overall_score: number | null }>>('/api/compass/status-reports?limit=5')
        setHistory(data || [])
      } catch (err) {
        console.error('Failed to fetch report history:', err)
      } finally {
        setHistoryLoading(false)
      }
    }
    if (showHistory && history.length === 0) {
      fetchHistory()
    }
  }, [showHistory, history.length])

  if (!open) return null

  const overallLevel = getOverallLevel(report.overall_score)

  // Map dimension keys to report fields
  const getDimensionData = (key: string): { score: number | null; justification: string | null } => {
    const scoreMap: Record<string, number | null> = {
      strategic_impact: report.strategic_impact,
      execution_quality: report.execution_quality,
      relationship_building: report.relationship_building,
      growth_mindset: report.growth_mindset,
      leadership_presence: report.leadership_presence,
    }
    const justificationMap: Record<string, string | null> = {
      strategic_impact: report.strategic_impact_justification,
      execution_quality: report.execution_quality_justification,
      relationship_building: report.relationship_building_justification,
      growth_mindset: report.growth_mindset_justification,
      leadership_presence: report.leadership_presence_justification,
    }
    return {
      score: scoreMap[key] ?? null,
      justification: justificationMap[key] ?? null,
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-card rounded-lg shadow-xl overflow-hidden flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-default">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
              <Trophy className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-primary">Career Status Report</h2>
              <p className="text-sm text-muted">
                Generated {new Date(report.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                disabled={regenerating}
                className="p-2 text-muted hover:text-primary hover:bg-hover rounded-lg transition-colors disabled:opacity-50"
                title="Regenerate report"
              >
                <RefreshCw className={`w-5 h-5 ${regenerating ? 'animate-spin' : ''}`} />
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-muted hover:text-primary hover:bg-hover rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Overall Score Summary */}
          <div className={`p-4 rounded-lg ${overallLevel.bg}`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`font-semibold ${overallLevel.color}`}>{overallLevel.label}</span>
              <span className={`text-2xl font-bold ${overallLevel.color}`}>
                {report.overall_score?.toFixed(1) ?? '-'}/5.0
              </span>
            </div>
            <p className="text-sm text-secondary">
              Based on {report.data_sources?.kb_documents || 0} documents from your Knowledge Base
            </p>
          </div>

          {/* Executive Summary */}
          {report.executive_summary && (
            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
              <h3 className="text-sm font-medium text-primary mb-2 flex items-center gap-2">
                <Target className="w-4 h-4" />
                Executive Summary
              </h3>
              <p className="text-sm text-secondary leading-relaxed">{report.executive_summary}</p>
            </div>
          )}

          {/* Dimension Scores */}
          <div className="space-y-5">
            <h3 className="text-sm font-medium text-muted uppercase tracking-wide">
              Performance Dimensions
            </h3>

            {rubric.map((dim) => {
              const { score, justification } = getDimensionData(dim.key)
              return (
                <ScoreDimensionCard
                  key={dim.key}
                  dimension={dim}
                  score={score}
                  justification={justification}
                />
              )
            })}
          </div>

          {/* Strengths */}
          {report.areas_of_strength && report.areas_of_strength.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-primary flex items-center gap-2">
                <Trophy className="w-4 h-4 text-green-500" />
                Areas of Strength
              </h3>
              <ul className="space-y-1">
                {report.areas_of_strength.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                    <span className="text-green-500 mt-0.5">+</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Growth Opportunities */}
          {report.growth_opportunities && report.growth_opportunities.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-primary flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-amber-500" />
                Growth Opportunities
              </h3>
              <ul className="space-y-1">
                {report.growth_opportunities.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                    <span className="text-amber-500 mt-0.5">*</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommended Actions */}
          {report.recommended_actions && report.recommended_actions.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-primary flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-blue-500" />
                Recommended Actions
              </h3>
              <ul className="space-y-1">
                {report.recommended_actions.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                    <span className="text-blue-500 mt-0.5">{i + 1}.</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Report History (expandable) */}
          <div className="pt-4 border-t border-default">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center gap-2 text-sm text-muted hover:text-primary transition-colors"
            >
              {showHistory ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
              <Calendar className="w-4 h-4" />
              Previous Reports
            </button>
            {showHistory && (
              <div className="mt-3 space-y-2">
                {historyLoading ? (
                  <div className="flex items-center gap-2 text-sm text-muted">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading history...
                  </div>
                ) : history.length === 0 ? (
                  <p className="text-sm text-muted">No previous reports</p>
                ) : (
                  history.map((h) => (
                    <div
                      key={h.id}
                      className={`flex items-center justify-between text-sm p-2 rounded ${
                        h.id === report.id
                          ? 'bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800'
                          : 'hover:bg-hover'
                      }`}
                    >
                      <span className={h.id === report.id ? 'text-primary font-medium' : 'text-secondary'}>
                        {new Date(h.report_date).toLocaleDateString()}
                      </span>
                      <span className="text-muted">
                        {h.overall_score?.toFixed(1) ?? '-'}/5.0
                      </span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
