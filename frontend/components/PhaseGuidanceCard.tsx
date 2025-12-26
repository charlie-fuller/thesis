'use client'

import { useState, useEffect, memo } from 'react'
import { getPhaseGuidance, type PhaseGuidanceResponse } from '@/lib/api'

interface PhaseGuidanceCardProps {
  conversationId: string | null
  onPromptClick?: (prompt: string) => void
  refreshTrigger?: number
}

// Phase color configuration
const PHASE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'Analysis': { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-200' },
  'Design': { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-200' },
  'Development': { bg: 'bg-purple-50', text: 'text-purple-800', border: 'border-purple-200' },
  'Implementation': { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-200' },
  'Evaluation': { bg: 'bg-pink-50', text: 'text-pink-800', border: 'border-pink-200' },
  'General': { bg: 'bg-gray-50', text: 'text-gray-800', border: 'border-gray-200' },
}

function PhaseGuidanceCard({
  conversationId,
  onPromptClick,
  refreshTrigger
}: PhaseGuidanceCardProps) {
  const [guidance, setGuidance] = useState<PhaseGuidanceResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    if (!conversationId) {
      setGuidance(null)
      return
    }

    const fetchGuidance = async () => {
      setLoading(true)
      try {
        const result = await getPhaseGuidance({
          conversation_id: conversationId,
          include_prompts: true
        })
        if (result.success) {
          setGuidance(result)
        }
      } catch (error) {
        console.error('Failed to fetch phase guidance:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchGuidance()
  }, [conversationId, refreshTrigger])

  // Don't render if no guidance or conversation
  if (!conversationId || loading) {
    return null
  }

  if (!guidance) {
    return null
  }

  // Don't show if 100% complete
  if (guidance.completeness === 100) {
    return null
  }

  const colors = PHASE_COLORS[guidance.phase] || PHASE_COLORS['General']

  return (
    <div className={`border rounded-lg ${colors.border} ${colors.bg} mb-4 overflow-hidden`}>
      {/* Header - Always visible */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-opacity-75 transition-colors"
      >
        <div className="flex items-center gap-3">
          {/* Progress indicator */}
          <div className="relative w-10 h-10 flex-shrink-0">
            <svg className="w-10 h-10 transform -rotate-90" viewBox="0 0 36 36">
              <circle
                cx="18"
                cy="18"
                r="15"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                className="text-gray-200"
              />
              <circle
                cx="18"
                cy="18"
                r="15"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeDasharray={`${guidance.completeness}, 100`}
                className={colors.text}
              />
            </svg>
            <span className={`absolute inset-0 flex items-center justify-center text-xs font-semibold ${colors.text}`}>
              {guidance.completeness}%
            </span>
          </div>

          <div className="text-left">
            <span className={`text-sm font-medium ${colors.text}`}>
              {guidance.phase} Phase
            </span>
            {guidance.missing_required.length > 0 && (
              <span className="text-xs text-gray-500 ml-2">
                ({guidance.missing_required.length} items to address)
              </span>
            )}
          </div>
        </div>

        {/* Collapse icon */}
        <svg
          className={`w-5 h-5 ${colors.text} transition-transform ${collapsed ? '' : 'rotate-180'}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Content - Collapsible */}
      {!collapsed && (
        <div className="px-4 pb-4 border-t border-opacity-50">
          {/* Suggestion */}
          <p className={`text-sm mt-3 ${colors.text}`}>
            {guidance.suggestion}
          </p>

          {/* Missing required elements */}
          {guidance.missing_required.length > 0 && (
            <div className="mt-3">
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                Consider addressing:
              </h4>
              <div className="flex flex-wrap gap-1">
                {guidance.missing_required.map((item, index) => (
                  <span
                    key={index}
                    className={`text-xs px-2 py-1 rounded ${colors.bg} ${colors.text} border ${colors.border}`}
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Suggested prompts */}
          {guidance.suggested_prompts.length > 0 && (
            <div className="mt-4">
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                Try asking:
              </h4>
              <div className="space-y-2">
                {guidance.suggested_prompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => onPromptClick?.(prompt)}
                    className="block w-full text-left text-sm px-3 py-2 rounded-lg bg-white hover:bg-gray-50 border border-gray-200 text-gray-700 transition-colors"
                  >
                    &quot;{prompt}&quot;
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default memo(PhaseGuidanceCard);
