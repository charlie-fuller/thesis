'use client'

/**
 * ScoreJustification Component
 *
 * Displays the 4-dimension scoring breakdown for an opportunity with
 * visual bars and explanations of what each score level means.
 */

interface DimensionJustification {
  roi_potential?: string
  implementation_effort?: string
  strategic_alignment?: string
  stakeholder_readiness?: string
}

interface ScoreJustificationProps {
  roiPotential: number | null
  implementationEffort: number | null
  strategicAlignment: number | null
  stakeholderReadiness: number | null
  totalScore: number
  tier: number
  opportunityDescription?: string
  dimensionJustifications?: DimensionJustification
}

// Scoring dimension definitions with explanations
const DIMENSIONS = {
  roi_potential: {
    label: 'ROI Potential',
    description: 'Revenue, cost savings, or time impact potential',
    levels: {
      5: 'Transformative impact - major revenue or 50%+ cost reduction',
      4: 'High impact - significant measurable savings',
      3: 'Moderate impact - clear but limited ROI',
      2: 'Low impact - marginal improvements',
      1: 'Minimal impact - unclear business value',
    },
  },
  implementation_effort: {
    label: 'Implementation Ease',
    description: 'How easy is this to implement? (5 = easiest)',
    levels: {
      5: 'Plug-and-play - minimal integration needed',
      4: 'Low effort - standard integrations, clear path',
      3: 'Moderate effort - some custom work required',
      2: 'High effort - significant development needed',
      1: 'Very complex - major infrastructure changes',
    },
  },
  strategic_alignment: {
    label: 'Strategic Alignment',
    description: 'How well does this align with business goals?',
    levels: {
      5: 'Core priority - directly supports key initiatives',
      4: 'Strong alignment - supports multiple goals',
      3: 'Moderate alignment - supports some objectives',
      2: 'Weak alignment - tangential to strategy',
      1: 'Misaligned - not a current priority',
    },
  },
  stakeholder_readiness: {
    label: 'Stakeholder Readiness',
    description: 'Champion identified, data ready, team eager?',
    levels: {
      5: 'Fully ready - champion, data, and team aligned',
      4: 'Mostly ready - minor gaps to address',
      3: 'Partially ready - needs some preparation',
      2: 'Low readiness - significant gaps exist',
      1: 'Not ready - no champion or major blockers',
    },
  },
}

const TIER_INFO = {
  1: {
    label: 'Tier 1: Strategic Priority',
    color: 'text-rose-600 dark:text-rose-400',
    bg: 'bg-rose-100 dark:bg-rose-900/30',
    range: '17-20',
    meaning: 'Pursue immediately - high value, ready to implement',
  },
  2: {
    label: 'Tier 2: High Impact',
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    range: '14-16',
    meaning: 'Near-term priority - strong opportunity, needs some work',
  },
  3: {
    label: 'Tier 3: Medium Priority',
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    range: '11-13',
    meaning: 'Queue for later - potential value, not urgent',
  },
  4: {
    label: 'Tier 4: Backlog',
    color: 'text-slate-600 dark:text-slate-400',
    bg: 'bg-slate-100 dark:bg-slate-800',
    range: '<11',
    meaning: 'Track but deprioritize - needs more development',
  },
}

function ScoreBar({
  score,
  dimension,
  justification,
}: {
  score: number | null
  dimension: keyof typeof DIMENSIONS
  justification?: string
}) {
  const dimInfo = DIMENSIONS[dimension]
  const value = score ?? 0
  const percentage = (value / 5) * 100

  // Color based on score
  const getBarColor = (score: number) => {
    if (score >= 4) return 'bg-green-500 dark:bg-green-400'
    if (score >= 3) return 'bg-amber-500 dark:bg-amber-400'
    return 'bg-gray-400 dark:bg-gray-500'
  }

  const levelExplanation = score ? dimInfo.levels[score as keyof typeof dimInfo.levels] : 'Not scored'

  return (
    <div className="space-y-2">
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-primary">{dimInfo.label}</span>
          <span className="text-sm font-bold text-primary">{score ?? '-'}/5</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${getBarColor(value)}`}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
        <p className="text-xs text-muted">{levelExplanation}</p>
      </div>
      {justification && (
        <p className="text-sm text-secondary pl-1 border-l-2 border-gray-200 dark:border-gray-700">
          {justification}
        </p>
      )}
    </div>
  )
}

export default function ScoreJustification({
  roiPotential,
  implementationEffort,
  strategicAlignment,
  stakeholderReadiness,
  totalScore,
  tier,
  opportunityDescription,
  dimensionJustifications,
}: ScoreJustificationProps) {
  const tierInfo = TIER_INFO[tier as keyof typeof TIER_INFO] || TIER_INFO[4]

  return (
    <div className="space-y-6">
      {/* Opportunity Description */}
      {opportunityDescription && (
        <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
          <h4 className="text-sm font-medium text-primary mb-2">About This Opportunity</h4>
          <p className="text-sm text-secondary leading-relaxed">{opportunityDescription}</p>
        </div>
      )}

      {/* Tier Summary */}
      <div className={`p-4 rounded-lg ${tierInfo.bg}`}>
        <div className="flex items-center justify-between mb-2">
          <span className={`font-semibold ${tierInfo.color}`}>{tierInfo.label}</span>
          <span className={`text-2xl font-bold ${tierInfo.color}`}>{totalScore}/20</span>
        </div>
        <p className="text-sm text-secondary">{tierInfo.meaning}</p>
        <p className="text-xs text-muted mt-1">Score range: {tierInfo.range}</p>
      </div>

      {/* Individual Scores */}
      <div className="space-y-5">
        <h4 className="text-sm font-medium text-muted uppercase tracking-wide">
          Score Breakdown
        </h4>

        <ScoreBar
          score={roiPotential}
          dimension="roi_potential"
          justification={dimensionJustifications?.roi_potential}
        />
        <ScoreBar
          score={implementationEffort}
          dimension="implementation_effort"
          justification={dimensionJustifications?.implementation_effort}
        />
        <ScoreBar
          score={strategicAlignment}
          dimension="strategic_alignment"
          justification={dimensionJustifications?.strategic_alignment}
        />
        <ScoreBar
          score={stakeholderReadiness}
          dimension="stakeholder_readiness"
          justification={dimensionJustifications?.stakeholder_readiness}
        />
      </div>

      {/* Dimension Descriptions */}
      <div className="pt-4 border-t border-default">
        <details className="group">
          <summary className="text-xs text-muted cursor-pointer hover:text-primary">
            About the scoring dimensions
          </summary>
          <div className="mt-3 space-y-3 text-xs text-secondary">
            {Object.entries(DIMENSIONS).map(([key, dim]) => (
              <div key={key}>
                <span className="font-medium text-primary">{dim.label}:</span>{' '}
                {dim.description}
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  )
}
