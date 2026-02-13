'use client'

import { useState } from 'react'
import { CheckSquare, Square, ChevronDown, ChevronUp, Loader2, Target } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiGet, apiPatch } from '@/lib/api'

export interface FramingProposal {
  problem_statements?: { id: string; text: string }[]
  hypotheses?: { id: string; statement: string; rationale?: string; type?: string }[]
  gaps?: { id: string; description: string; type?: string }[]
  desired_outcome_state?: string
}

interface Throughline {
  problem_statements?: { id: string; text: string }[]
  hypotheses?: { id: string; statement: string; rationale?: string; type?: string }[]
  gaps?: { id: string; description: string; type?: string }[]
  desired_outcome_state?: string
}

interface FramingProposalCardProps {
  proposal: FramingProposal
  initiativeId: string
  onFramingApplied?: () => void
}

type ItemCategory = 'problem_statements' | 'hypotheses' | 'gaps'

interface SelectableItem {
  category: ItemCategory
  index: number
}

const CATEGORY_LABELS: Record<ItemCategory, { label: string; color: string }> = {
  problem_statements: {
    label: 'Problem Statement',
    color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  },
  hypotheses: {
    label: 'Hypothesis',
    color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  },
  gaps: {
    label: 'Gap',
    color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  },
}

function itemKey(item: SelectableItem): string {
  return `${item.category}-${item.index}`
}

export default function FramingProposalCard({
  proposal,
  initiativeId,
  onFramingApplied,
}: FramingProposalCardProps) {
  // Build flat list of all selectable items
  const allItems: SelectableItem[] = []
  const categories: ItemCategory[] = ['problem_statements', 'hypotheses', 'gaps']
  for (const cat of categories) {
    const items = proposal[cat]
    if (items) {
      items.forEach((_, i) => allItems.push({ category: cat, index: i }))
    }
  }

  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(
    new Set(allItems.map(itemKey))
  )
  const [isExpanded, setIsExpanded] = useState(true)
  const [isApplying, setIsApplying] = useState(false)
  const [isApplied, setIsApplied] = useState(false)

  // Include desired_outcome_state toggle
  const hasOutcome = !!proposal.desired_outcome_state
  const [includeOutcome, setIncludeOutcome] = useState(hasOutcome)

  const toggleSelection = (item: SelectableItem) => {
    const key = itemKey(item)
    setSelectedKeys(prev => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const toggleAll = () => {
    if (selectedKeys.size === allItems.length) {
      setSelectedKeys(new Set())
      setIncludeOutcome(false)
    } else {
      setSelectedKeys(new Set(allItems.map(itemKey)))
      if (hasOutcome) setIncludeOutcome(true)
    }
  }

  const totalSelected = selectedKeys.size + (includeOutcome ? 1 : 0)
  const totalItems = allItems.length + (hasOutcome ? 1 : 0)

  const handleApply = async () => {
    if (totalSelected === 0) {
      toast.error('Select at least one item to apply')
      return
    }

    setIsApplying(true)

    try {
      // Fetch current initiative to get existing throughline
      const initiative = await apiGet<{ throughline?: Throughline }>(
        `/api/disco/initiatives/${initiativeId}`
      )
      const existing: Throughline = initiative?.throughline || {}

      // Merge selected proposals into existing throughline
      const merged: Throughline = { ...existing }

      // Merge problem statements
      if (proposal.problem_statements) {
        const selected = proposal.problem_statements.filter((_, i) =>
          selectedKeys.has(itemKey({ category: 'problem_statements', index: i }))
        )
        if (selected.length > 0) {
          merged.problem_statements = [...(merged.problem_statements || []), ...selected]
        }
      }

      // Merge hypotheses
      if (proposal.hypotheses) {
        const selected = proposal.hypotheses.filter((_, i) =>
          selectedKeys.has(itemKey({ category: 'hypotheses', index: i }))
        )
        if (selected.length > 0) {
          merged.hypotheses = [...(merged.hypotheses || []), ...selected]
        }
      }

      // Merge gaps
      if (proposal.gaps) {
        const selected = proposal.gaps.filter((_, i) =>
          selectedKeys.has(itemKey({ category: 'gaps', index: i }))
        )
        if (selected.length > 0) {
          merged.gaps = [...(merged.gaps || []), ...selected]
        }
      }

      if (includeOutcome && proposal.desired_outcome_state) {
        merged.desired_outcome_state = proposal.desired_outcome_state
      }

      // PATCH the initiative with merged throughline
      await apiPatch(`/api/disco/initiatives/${initiativeId}`, {
        throughline: merged,
      })

      setIsApplied(true)
      toast.success('Framing applied to discovery')
      onFramingApplied?.()
    } catch (err) {
      console.error('Error applying framing:', err)
      toast.error('Failed to apply framing')
    } finally {
      setIsApplying(false)
    }
  }

  if (isApplied) {
    return (
      <div className="mt-3 border border-green-200 dark:border-green-800 rounded-lg p-3 bg-green-50 dark:bg-green-900/20">
        <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400 font-medium">
          <CheckSquare className="w-4 h-4" />
          <span>Framing applied to discovery</span>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-3 border border-default rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800/50 text-sm font-medium text-primary hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-purple-600 dark:text-purple-400" />
          <span>Framing Proposal ({totalItems} items)</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted" />
        )}
      </button>

      {isExpanded && (
        <div className="p-3">
          {/* Select all toggle */}
          <div className="flex items-center justify-between mb-2 pb-2 border-b border-default">
            <button
              onClick={toggleAll}
              className="text-xs text-muted hover:text-primary transition-colors"
            >
              {totalSelected === totalItems ? 'Deselect all' : 'Select all'}
            </button>
            <span className="text-xs text-muted">
              {totalSelected} of {totalItems} selected
            </span>
          </div>

          {/* Items by category */}
          <div className="space-y-2">
            {categories.map(cat => {
              const items = proposal[cat]
              if (!items || items.length === 0) return null
              const catMeta = CATEGORY_LABELS[cat]

              return items.map((item, index) => {
                const key = itemKey({ category: cat, index })
                const isSelected = selectedKeys.has(key)

                // Get display text based on category
                let displayText = ''
                let subText = ''
                if (cat === 'problem_statements') {
                  displayText = (item as { text: string }).text
                } else if (cat === 'hypotheses') {
                  const h = item as { statement: string; rationale?: string; type?: string }
                  displayText = h.statement
                  subText = h.rationale || ''
                } else if (cat === 'gaps') {
                  displayText = (item as { description: string }).description
                }

                const itemId = (item as { id: string }).id

                return (
                  <div
                    key={key}
                    onClick={() => toggleSelection({ category: cat, index })}
                    className={`flex items-start gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800'
                        : 'bg-gray-50 dark:bg-gray-800/30 border border-transparent hover:border-gray-200 dark:hover:border-gray-700'
                    }`}
                  >
                    <div className="mt-0.5 flex-shrink-0">
                      {isSelected ? (
                        <CheckSquare className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                      ) : (
                        <Square className="w-4 h-4 text-muted" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-mono text-muted bg-gray-200 dark:bg-gray-700 rounded px-1.5 py-0.5">
                          {itemId}
                        </span>
                        <span className={`text-xs px-1.5 py-0.5 rounded ${catMeta.color}`}>
                          {catMeta.label}
                        </span>
                      </div>
                      <p className="text-sm text-primary mt-1">{displayText}</p>
                      {subText && (
                        <p className="text-xs text-muted mt-0.5">{subText}</p>
                      )}
                    </div>
                  </div>
                )
              })
            })}

            {/* Desired outcome state */}
            {hasOutcome && (
              <div
                onClick={() => setIncludeOutcome(!includeOutcome)}
                className={`flex items-start gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                  includeOutcome
                    ? 'bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800'
                    : 'bg-gray-50 dark:bg-gray-800/30 border border-transparent hover:border-gray-200 dark:hover:border-gray-700'
                }`}
              >
                <div className="mt-0.5 flex-shrink-0">
                  {includeOutcome ? (
                    <CheckSquare className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  ) : (
                    <Square className="w-4 h-4 text-muted" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    Desired Outcome
                  </span>
                  <p className="text-sm text-primary mt-1">{proposal.desired_outcome_state}</p>
                </div>
              </div>
            )}
          </div>

          {/* Apply button */}
          <div className="mt-3 pt-2 border-t border-default">
            <button
              onClick={handleApply}
              disabled={isApplying || totalSelected === 0}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md transition-colors"
            >
              {isApplying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Applying framing...</span>
                </>
              ) : (
                <>
                  <Target className="w-4 h-4" />
                  <span>Apply to Discovery</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
