'use client'

/**
 * ScoreDimensionCard Component
 *
 * Displays a single career rubric dimension with score bar,
 * level explanation, and AI-generated justification.
 */

interface Level {
  [key: number]: string
}

export interface Dimension {
  key: string
  name: string
  weight: number
  description: string
  levels: Level
}

interface ScoreDimensionCardProps {
  dimension: Dimension
  score: number | null
  justification: string | null
}

export default function ScoreDimensionCard({
  dimension,
  score,
  justification,
}: ScoreDimensionCardProps) {
  const value = score ?? 0
  const percentage = (value / 5) * 100

  // Color based on score
  const getBarColor = (score: number) => {
    if (score >= 4) return 'bg-green-500 dark:bg-green-400'
    if (score >= 3) return 'bg-amber-500 dark:bg-amber-400'
    if (score >= 2) return 'bg-orange-500 dark:bg-orange-400'
    return 'bg-gray-400 dark:bg-gray-500'
  }

  const levelExplanation = score
    ? dimension.levels[score]
    : 'Not scored'

  return (
    <div className="space-y-2">
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-primary">{dimension.name}</span>
            <span className="text-xs text-muted">({dimension.weight}%)</span>
          </div>
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
        <p className="text-sm text-secondary pl-3 border-l-2 border-amber-300 dark:border-amber-600">
          {justification}
        </p>
      )}
    </div>
  )
}
