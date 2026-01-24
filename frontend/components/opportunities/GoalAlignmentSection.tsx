'use client'

/**
 * GoalAlignmentSection Component
 *
 * Displays goal alignment analysis for an opportunity against IS team FY27 strategic goals.
 * Shows overall score (0-100) and breakdown across 4 strategic pillars.
 */

import { useState } from 'react'
import { Target, RefreshCw, TrendingUp, Database, Users, Building2 } from 'lucide-react'

interface PillarScore {
  score: number
  rationale: string
}

interface GoalAlignmentDetails {
  pillar_scores: {
    customer_prospect_journey: PillarScore
    maximize_value: PillarScore
    data_first_digital_workforce: PillarScore
    high_trust_culture: PillarScore
  }
  kpi_impacts: string[]
  summary: string
  analyzed_at: string
}

interface GoalAlignmentSectionProps {
  opportunityId: string
  goalAlignmentScore: number | null
  goalAlignmentDetails: GoalAlignmentDetails | null
  onAnalyze: () => Promise<void>
}

// Pillar definitions with icons and colors (FY27 IS Priorities)
const PILLARS = {
  customer_prospect_journey: {
    key: 'customer_prospect_journey',
    label: 'Customer and Prospect Journey',
    shortLabel: 'Customer Journey',
    icon: TrendingUp,
    description: 'Decision-ready first touch to churn, connected backbone for GTM/Product/Finance',
    kpis: ['100% customers trackable', '2+ GTM motions with insights'],
    color: 'rose',
  },
  maximize_value: {
    key: 'maximize_value',
    label: 'Maximize Value from Core Systems & AI',
    shortLabel: 'Maximize Value',
    icon: Building2,
    description: 'Portfolio driving measurable value: productivity, spend, experience',
    kpis: ['v5 P&P launched', 'Contract entitlements integrated'],
    color: 'amber',
  },
  data_first_digital_workforce: {
    key: 'data_first_digital_workforce',
    label: 'Data First Digital Workforce',
    shortLabel: 'Digital Workforce',
    icon: Database,
    description: 'Insight 360, automation, AI reducing friction and providing decision-ready insights',
    kpis: ['100% sources in Insight 360', '50%+ lifecycle automated', 'AI ROI on 2+ projects'],
    color: 'blue',
  },
  high_trust_culture: {
    key: 'high_trust_culture',
    label: 'High-Trust IS Culture',
    shortLabel: 'High-Trust Culture',
    icon: Users,
    description: 'Strategic partner: easy to work with, transparent, career growth',
    kpis: ['Stakeholder sentiment improving', 'Development plans in place'],
    color: 'emerald',
  },
} as const

type PillarKey = keyof typeof PILLARS

// Get alignment level info based on score
function getAlignmentLevel(score: number | null): {
  label: string
  color: string
  bg: string
  description: string
} {
  if (score === null) {
    return {
      label: 'Not Analyzed',
      color: 'text-gray-500',
      bg: 'bg-gray-100 dark:bg-gray-800',
      description: 'Click "Analyze" to evaluate strategic alignment',
    }
  }
  if (score >= 80) {
    return {
      label: 'High Alignment',
      color: 'text-green-600 dark:text-green-400',
      bg: 'bg-green-100 dark:bg-green-900/30',
      description: 'Directly advances strategic goals',
    }
  }
  if (score >= 60) {
    return {
      label: 'Moderate Alignment',
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      description: 'Strong indirect support for strategy',
    }
  }
  if (score >= 40) {
    return {
      label: 'Low Alignment',
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-100 dark:bg-amber-900/30',
      description: 'Tangential connection to strategy',
    }
  }
  return {
    label: 'Minimal Alignment',
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900/30',
    description: 'Limited strategic value',
  }
}

// Get color classes for pillar based on score
function getPillarScoreColor(score: number): string {
  if (score >= 20) return 'bg-green-500 dark:bg-green-400'
  if (score >= 15) return 'bg-blue-500 dark:bg-blue-400'
  if (score >= 10) return 'bg-amber-500 dark:bg-amber-400'
  return 'bg-gray-400 dark:bg-gray-500'
}

function PillarCard({
  pillarKey,
  pillarScore,
}: {
  pillarKey: PillarKey
  pillarScore: PillarScore | undefined
}) {
  const pillar = PILLARS[pillarKey]
  const Icon = pillar.icon
  const score = pillarScore?.score ?? 0
  const rationale = pillarScore?.rationale ?? 'Not analyzed'
  const percentage = (score / 25) * 100

  return (
    <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg space-y-3">
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg bg-${pillar.color}-100 dark:bg-${pillar.color}-900/30`}>
          <Icon className={`w-4 h-4 text-${pillar.color}-600 dark:text-${pillar.color}-400`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-sm font-medium text-primary truncate">{pillar.shortLabel}</h4>
            <span className="text-sm font-bold text-primary flex-shrink-0">{score}/25</span>
          </div>
          <p className="text-xs text-muted mt-0.5">{pillar.description}</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${getPillarScoreColor(score)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Rationale */}
      <p className="text-sm text-secondary">{rationale}</p>

      {/* KPIs */}
      <div className="flex flex-wrap gap-1">
        {pillar.kpis.map((kpi) => (
          <span
            key={kpi}
            className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-muted rounded"
          >
            {kpi}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function GoalAlignmentSection({
  opportunityId,
  goalAlignmentScore,
  goalAlignmentDetails,
  onAnalyze,
}: GoalAlignmentSectionProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const alignmentLevel = getAlignmentLevel(goalAlignmentScore)
  const hasBeenAnalyzed = goalAlignmentScore !== null

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    try {
      await onAnalyze()
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header with Analyze Button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-medium text-primary">IS Strategic Goal Alignment</h3>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
          {hasBeenAnalyzed ? 'Regenerate' : 'Analyze'}
        </button>
      </div>

      {/* Overall Score */}
      <div className={`p-4 rounded-lg ${alignmentLevel.bg}`}>
        <div className="flex items-center justify-between mb-2">
          <span className={`font-semibold ${alignmentLevel.color}`}>{alignmentLevel.label}</span>
          <span className={`text-2xl font-bold ${alignmentLevel.color}`}>
            {goalAlignmentScore ?? '-'}/100
          </span>
        </div>
        <p className="text-sm text-secondary">{alignmentLevel.description}</p>

        {/* Progress bar */}
        {hasBeenAnalyzed && (
          <div className="mt-3 h-3 bg-white/50 dark:bg-gray-800/50 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                goalAlignmentScore! >= 80
                  ? 'bg-green-500'
                  : goalAlignmentScore! >= 60
                    ? 'bg-blue-500'
                    : goalAlignmentScore! >= 40
                      ? 'bg-amber-500'
                      : 'bg-red-500'
              }`}
              style={{ width: `${goalAlignmentScore}%` }}
            />
          </div>
        )}
      </div>

      {/* Summary */}
      {goalAlignmentDetails?.summary && (
        <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
          <h4 className="text-sm font-medium text-primary mb-2">Analysis Summary</h4>
          <p className="text-sm text-secondary leading-relaxed">{goalAlignmentDetails.summary}</p>
        </div>
      )}

      {/* KPI Impacts */}
      {goalAlignmentDetails?.kpi_impacts && goalAlignmentDetails.kpi_impacts.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-muted uppercase tracking-wide mb-2">
            Impacted KPIs
          </h4>
          <div className="flex flex-wrap gap-2">
            {goalAlignmentDetails.kpi_impacts.map((kpi) => (
              <span
                key={kpi}
                className="px-3 py-1 text-sm bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded-full"
              >
                {kpi}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Pillar Breakdown */}
      {hasBeenAnalyzed && goalAlignmentDetails?.pillar_scores && (
        <div className="space-y-4">
          <h4 className="text-xs font-medium text-muted uppercase tracking-wide">
            Strategic Pillar Breakdown
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(Object.keys(PILLARS) as PillarKey[]).map((key) => (
              <PillarCard
                key={key}
                pillarKey={key}
                pillarScore={goalAlignmentDetails.pillar_scores[key]}
              />
            ))}
          </div>
        </div>
      )}

      {/* Not Analyzed State */}
      {!hasBeenAnalyzed && (
        <div className="text-center py-8 text-secondary">
          <Target className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">
            Click &quot;Analyze&quot; to evaluate how this opportunity aligns with IS team FY27
            strategic goals.
          </p>
        </div>
      )}

      {/* Last Analyzed Timestamp */}
      {goalAlignmentDetails?.analyzed_at && (
        <p className="text-xs text-muted text-right">
          Last analyzed: {new Date(goalAlignmentDetails.analyzed_at).toLocaleString()}
        </p>
      )}
    </div>
  )
}
