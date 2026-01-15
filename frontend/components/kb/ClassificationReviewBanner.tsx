'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiGet, apiPost } from '@/lib/api'
import { AlertTriangle, Check, X, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'

interface Agent {
  id: string
  name: string
  display_name: string
}

interface PendingReview {
  document_id: string
  filename: string
  detected_type: string | null
  review_reason: string | null
  suggested_agents: Record<string, number>  // {agent_name: confidence}
  created_at: string
}

interface ClassificationReviewBannerProps {
  onReviewComplete?: () => void
  refreshTrigger?: number
}

export default function ClassificationReviewBanner({
  onReviewComplete,
  refreshTrigger = 0
}: ClassificationReviewBannerProps) {
  const [pendingReviews, setPendingReviews] = useState<PendingReview[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(false)
  const [confirmingId, setConfirmingId] = useState<string | null>(null)
  const [selectedAgents, setSelectedAgents] = useState<Record<string, Set<string>>>({})

  // Load agents for selection
  const loadAgents = useCallback(async () => {
    try {
      const data = await apiGet<{ agents: Agent[] }>('/api/agents?include_inactive=false')
      setAgents(data.agents || [])
    } catch (err) {
      console.error('Failed to load agents:', err)
    }
  }, [])

  // Load pending reviews
  const loadPendingReviews = useCallback(async () => {
    try {
      setLoading(true)
      const data = await apiGet<{ pending_reviews: PendingReview[] }>('/api/documents/pending-reviews')
      setPendingReviews(data.pending_reviews || [])

      // Initialize selected agents from suggestions
      const initialSelections: Record<string, Set<string>> = {}
      for (const review of data.pending_reviews || []) {
        const suggestedAgentNames = Object.entries(review.suggested_agents || {})
          .filter(([, confidence]) => confidence >= 0.4)
          .map(([name]) => name)

        // Find agent IDs for suggested names
        const suggestedIds = new Set<string>()
        for (const name of suggestedAgentNames) {
          const agent = agents.find(a => a.name === name)
          if (agent) {
            suggestedIds.add(agent.id)
          }
        }
        initialSelections[review.document_id] = suggestedIds
      }
      setSelectedAgents(initialSelections)
    } catch (err) {
      console.error('Failed to load pending reviews:', err)
    } finally {
      setLoading(false)
    }
  }, [agents])

  useEffect(() => {
    loadAgents()
  }, [loadAgents])

  useEffect(() => {
    if (agents.length > 0) {
      loadPendingReviews()
    }
  }, [agents, loadPendingReviews, refreshTrigger])

  const toggleAgentSelection = (documentId: string, agentId: string) => {
    setSelectedAgents(prev => {
      const docSelections = new Set(prev[documentId] || [])
      if (docSelections.has(agentId)) {
        docSelections.delete(agentId)
      } else {
        docSelections.add(agentId)
      }
      return { ...prev, [documentId]: docSelections }
    })
  }

  const confirmClassification = async (documentId: string) => {
    try {
      setConfirmingId(documentId)
      const agentIds = Array.from(selectedAgents[documentId] || [])

      await apiPost(`/api/documents/${documentId}/classification/confirm`, {
        agent_ids: agentIds
      })

      // Remove from pending reviews
      setPendingReviews(prev => prev.filter(r => r.document_id !== documentId))

      if (onReviewComplete) {
        onReviewComplete()
      }
    } catch (err) {
      console.error('Failed to confirm classification:', err)
    } finally {
      setConfirmingId(null)
    }
  }

  const dismissReview = async (documentId: string) => {
    // Confirm with empty array (make document global)
    try {
      setConfirmingId(documentId)
      await apiPost(`/api/documents/${documentId}/classification/confirm`, {
        agent_ids: []
      })
      setPendingReviews(prev => prev.filter(r => r.document_id !== documentId))
      if (onReviewComplete) {
        onReviewComplete()
      }
    } catch (err) {
      console.error('Failed to dismiss classification:', err)
    } finally {
      setConfirmingId(null)
    }
  }

  // Get agent display name and confidence for a document
  const getAgentInfo = (review: PendingReview, agentId: string) => {
    const agent = agents.find(a => a.id === agentId)
    if (!agent) return null
    const confidence = review.suggested_agents[agent.name] || 0
    return { agent, confidence }
  }

  if (loading || pendingReviews.length === 0) {
    return null
  }

  return (
    <div className="mb-4 rounded-lg border border-amber-500/50 bg-amber-50 dark:bg-amber-900/20">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-left"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-600 dark:text-amber-400" />
          <span className="font-medium text-amber-800 dark:text-amber-200">
            {pendingReviews.length} document{pendingReviews.length !== 1 ? 's' : ''} need classification review
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-amber-600 dark:text-amber-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-amber-600 dark:text-amber-400" />
        )}
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-3 pb-3 space-y-3">
          <p className="text-sm text-amber-700 dark:text-amber-300">
            These documents were auto-analyzed but need your confirmation on which agents should have access.
          </p>

          {pendingReviews.map(review => (
            <div
              key={review.document_id}
              className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-amber-200 dark:border-amber-800"
            >
              {/* Document Info */}
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-medium text-primary">{review.filename}</p>
                  {review.detected_type && (
                    <p className="text-xs text-muted">Detected type: {review.detected_type}</p>
                  )}
                  {review.review_reason && (
                    <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1 mt-1">
                      <AlertTriangle className="w-3 h-3" />
                      {review.review_reason}
                    </p>
                  )}
                </div>
              </div>

              {/* Suggested Agents */}
              <div className="mb-3">
                <p className="text-xs text-muted mb-2">Suggested agents (click to toggle):</p>
                <div className="flex flex-wrap gap-2">
                  {agents
                    .filter(agent =>
                      // Show suggested agents first, then others
                      Object.keys(review.suggested_agents).includes(agent.name) ||
                      (selectedAgents[review.document_id]?.has(agent.id))
                    )
                    .sort((a, b) => {
                      const confA = review.suggested_agents[a.name] || 0
                      const confB = review.suggested_agents[b.name] || 0
                      return confB - confA
                    })
                    .map(agent => {
                      const isSelected = selectedAgents[review.document_id]?.has(agent.id)
                      const confidence = review.suggested_agents[agent.name] || 0
                      const confidencePercent = Math.round(confidence * 100)

                      return (
                        <button
                          key={agent.id}
                          onClick={() => toggleAgentSelection(review.document_id, agent.id)}
                          className={`
                            px-2 py-1 text-xs rounded-full border transition-colors
                            ${isSelected
                              ? 'bg-brand/20 border-brand text-brand'
                              : 'bg-tertiary border-default text-secondary hover:border-brand/50'
                            }
                          `}
                        >
                          {agent.display_name}
                          {confidence > 0 && (
                            <span className="ml-1 opacity-60">({confidencePercent}%)</span>
                          )}
                        </button>
                      )
                    })}

                  {/* Show "Add more..." button if not all agents shown */}
                  {agents.filter(a => !Object.keys(review.suggested_agents).includes(a.name)).length > 0 && (
                    <button
                      onClick={() => {
                        // Show all agents (toggle behavior could be added)
                      }}
                      className="px-2 py-1 text-xs rounded-full border border-dashed border-default text-muted hover:border-brand/50"
                    >
                      + more agents
                    </button>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => confirmClassification(review.document_id)}
                  disabled={confirmingId === review.document_id}
                  className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-sm bg-brand text-white rounded-md hover:bg-brand/90 disabled:opacity-50"
                >
                  {confirmingId === review.document_id ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      Confirm
                    </>
                  )}
                </button>
                <button
                  onClick={() => dismissReview(review.document_id)}
                  disabled={confirmingId === review.document_id}
                  className="flex items-center justify-center gap-1 px-3 py-1.5 text-sm border border-default rounded-md hover:bg-tertiary disabled:opacity-50"
                  title="Make document global (available to all agents)"
                >
                  <X className="w-4 h-4" />
                  Make Global
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
