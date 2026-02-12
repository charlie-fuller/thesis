'use client'

import { useState, useEffect } from 'react'
import {
  Boxes,
  CheckCircle,
  XCircle,
  Edit3,
  GitMerge,
  Scissors,
  Loader2,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Target,
  Clock,
  Zap,
  FileText,
  Scale,
  Sparkles,
  FolderPlus,
  ExternalLink
} from 'lucide-react'
import { apiGet, apiPost, apiPatch } from '@/lib/api'

// Output type options
const OUTPUT_TYPES = [
  {
    value: 'prd',
    label: 'Product Requirements Document',
    description: 'For build/development proposed initiatives',
    icon: FileText,
  },
  {
    value: 'evaluation_framework',
    label: 'Evaluation Framework',
    description: 'For research/evaluation proposed initiatives',
    icon: Scale,
  },
  {
    value: 'decision_framework',
    label: 'Decision Framework',
    description: 'For governance decisions',
    icon: Target,
  },
]

interface Bundle {
  id: string
  initiative_id: string
  name: string
  description: string
  status: 'proposed' | 'approved' | 'rejected' | 'merged'
  impact_score: string | null
  impact_rationale: string | null
  feasibility_score: string | null
  feasibility_rationale: string | null
  urgency_score: string | null
  urgency_rationale: string | null
  complexity_tier: string | null
  complexity_rationale: string | null
  included_items: Array<{ description: string; source?: string }>
  stakeholders: Array<{ name: string; stake: string }>
  dependencies: { blocks?: string[]; requires?: string[]; conflicts?: string[] }
  bundling_rationale: string | null
  created_at: string
  approved_at: string | null
}

interface SynthesisViewProps {
  initiativeId: string
  canEdit: boolean
  onRefresh: () => void
}

const SCORE_COLORS = {
  HIGH: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  MEDIUM: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  LOW: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
}

const STATUS_CONFIG = {
  proposed: { label: 'Proposed', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', icon: Clock },
  approved: { label: 'Approved', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', icon: CheckCircle },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', icon: XCircle },
  merged: { label: 'Merged', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400', icon: GitMerge }
}

function ScoreBadge({ score, rationale }: { score: string | null; rationale?: string | null }) {
  if (!score) return <span className="text-slate-400 text-xs">-</span>
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium ${SCORE_COLORS[score as keyof typeof SCORE_COLORS] || 'bg-slate-100'}`}
      title={rationale || undefined}
    >
      {score}
    </span>
  )
}

function BundleCard({
  bundle,
  canEdit,
  onApprove,
  onReject,
  onEdit,
  onCreateProject,
  creatingProject,
  createdProjectId
}: {
  bundle: Bundle
  canEdit: boolean
  onApprove: () => void
  onReject: () => void
  onEdit: () => void
  onCreateProject?: () => void
  creatingProject?: boolean
  createdProjectId?: string | null
}) {
  const [expanded, setExpanded] = useState(false)
  const statusConfig = STATUS_CONFIG[bundle.status]
  const StatusIcon = statusConfig.icon

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-slate-900 dark:text-white">
              {bundle.name}
            </h3>
            <span className={`px-2 py-0.5 rounded text-xs font-medium flex items-center gap-1 ${statusConfig.color}`}>
              <StatusIcon className="w-3 h-3" />
              {statusConfig.label}
            </span>
            {bundle.complexity_tier && (
              <span className="px-2 py-0.5 rounded text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                {bundle.complexity_tier}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">
            {bundle.description}
          </p>

          {/* Score summary */}
          <div className="flex items-center gap-4 mt-2">
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-500">Impact:</span>
              <ScoreBadge score={bundle.impact_score} rationale={bundle.impact_rationale} />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-500">Feasibility:</span>
              <ScoreBadge score={bundle.feasibility_score} rationale={bundle.feasibility_rationale} />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-500">Urgency:</span>
              <ScoreBadge score={bundle.urgency_score} rationale={bundle.urgency_rationale} />
            </div>
          </div>
        </div>

        {/* Item count */}
        <span className="text-sm text-slate-400 flex-shrink-0">
          {bundle.included_items?.length || 0} items
        </span>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-slate-200 dark:border-slate-700">
          {/* Included items */}
          {bundle.included_items && bundle.included_items.length > 0 && (
            <div className="p-4 border-b border-slate-200 dark:border-slate-700">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Included Items
              </h4>
              <ul className="space-y-1.5">
                {bundle.included_items.map((item, i) => (
                  <li key={i} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                    <span className="text-slate-400">-</span>
                    <span>{item.description}</span>
                    {item.source && (
                      <span className="text-xs text-slate-400 italic">({item.source})</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Stakeholders */}
          {bundle.stakeholders && bundle.stakeholders.length > 0 && (
            <div className="p-4 border-b border-slate-200 dark:border-slate-700">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Affected Stakeholders
              </h4>
              <div className="flex flex-wrap gap-2">
                {bundle.stakeholders.map((s, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-xs text-slate-600 dark:text-slate-300"
                    title={s.stake}
                  >
                    {s.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Rationale */}
          {bundle.bundling_rationale && (
            <div className="p-4 border-b border-slate-200 dark:border-slate-700">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Grouping Rationale
              </h4>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {bundle.bundling_rationale}
              </p>
            </div>
          )}

          {/* Actions */}
          {canEdit && bundle.status === 'proposed' && (
            <div className="p-4 flex items-center gap-2 bg-slate-50 dark:bg-slate-900/50">
              <button
                onClick={onApprove}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
              >
                <CheckCircle className="w-4 h-4" />
                Approve
              </button>
              <button
                onClick={onReject}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
              >
                <XCircle className="w-4 h-4" />
                Reject
              </button>
              <button
                onClick={onEdit}
                className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 text-sm rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              >
                <Edit3 className="w-4 h-4" />
                Edit
              </button>
            </div>
          )}

          {/* Create Project action for approved bundles */}
          {bundle.status === 'approved' && onCreateProject && (
            <div className="p-4 flex items-center gap-2 bg-slate-50 dark:bg-slate-900/50">
              {createdProjectId ? (
                <a
                  href={`/projects/${createdProjectId}`}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Project
                </a>
              ) : (
                <button
                  onClick={onCreateProject}
                  disabled={creatingProject}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {creatingProject ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <FolderPlus className="w-4 h-4" />
                  )}
                  {creatingProject ? 'Creating...' : 'Create Project'}
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function SynthesisView({ initiativeId, canEdit, onRefresh }: SynthesisViewProps) {
  const [bundles, setBundles] = useState<Bundle[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [rejectFeedback, setRejectFeedback] = useState('')
  const [rejectingBundle, setRejectingBundle] = useState<string | null>(null)

  // Approval modal state
  const [approvingBundle, setApprovingBundle] = useState<string | null>(null)
  const [selectedOutputType, setSelectedOutputType] = useState('prd')
  const [suggestedOutputType, setSuggestedOutputType] = useState<string | null>(null)
  const [suggestionRationale, setSuggestionRationale] = useState<string | null>(null)
  const [suggestionLoading, setSuggestionLoading] = useState(false)

  // Create project state
  const [creatingProjectBundle, setCreatingProjectBundle] = useState<string | null>(null)
  const [createdProjects, setCreatedProjects] = useState<Record<string, string>>({})
  const [projectSuccessMessage, setProjectSuccessMessage] = useState<string | null>(null)

  // Load bundles
  useEffect(() => {
    loadBundles()
  }, [initiativeId])

  async function loadBundles() {
    try {
      setLoading(true)
      setError(null)
      const result = await apiGet<{ success: boolean; bundles: Bundle[] }>(
        `/api/disco/initiatives/${initiativeId}/bundles`
      )
      setBundles(result.bundles || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bundles')
    } finally {
      setLoading(false)
    }
  }

  // Load output type suggestion when approval modal opens
  async function loadOutputTypeSuggestion(bundleId: string) {
    setSuggestionLoading(true)
    try {
      const result = await apiGet<{
        success: boolean
        suggested_type: string
        confidence: string
        rationale: string
      }>(`/api/disco/initiatives/${initiativeId}/bundles/${bundleId}/suggest-output-type`)

      if (result.success) {
        setSuggestedOutputType(result.suggested_type)
        setSuggestionRationale(result.rationale)
        setSelectedOutputType(result.suggested_type)
      }
    } catch (err) {
      console.error('Failed to get output type suggestion:', err)
    } finally {
      setSuggestionLoading(false)
    }
  }

  function openApprovalModal(bundleId: string) {
    setApprovingBundle(bundleId)
    setSelectedOutputType('prd')
    setSuggestedOutputType(null)
    setSuggestionRationale(null)
    loadOutputTypeSuggestion(bundleId)
  }

  async function handleApprove(bundleId: string, outputType: string) {
    try {
      setActionLoading(bundleId)
      await apiPost(`/api/disco/initiatives/${initiativeId}/bundles/${bundleId}/approve`, {
        output_type: outputType,
      })
      setApprovingBundle(null)
      await loadBundles()
      onRefresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve bundle')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleReject(bundleId: string, feedback: string) {
    try {
      setActionLoading(bundleId)
      await apiPost(`/api/disco/initiatives/${initiativeId}/bundles/${bundleId}/reject`, { feedback })
      setRejectingBundle(null)
      setRejectFeedback('')
      await loadBundles()
      onRefresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject bundle')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleCreateProject(bundleId: string) {
    try {
      setCreatingProjectBundle(bundleId)
      setError(null)
      const result = await apiPost<{ success: boolean; project: { id: string; title: string; project_code: string } }>(
        `/api/disco/initiatives/${initiativeId}/bundles/${bundleId}/create-project`
      )
      if (result.success && result.project) {
        setCreatedProjects(prev => ({ ...prev, [bundleId]: result.project.id }))
        setProjectSuccessMessage(`Project "${result.project.title}" (${result.project.project_code}) created successfully.`)
        // Auto-dismiss success message after 5 seconds
        setTimeout(() => setProjectSuccessMessage(null), 5000)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project')
    } finally {
      setCreatingProjectBundle(null)
    }
  }

  // Group bundles by status
  const proposedBundles = bundles.filter(b => b.status === 'proposed')
  const approvedBundles = bundles.filter(b => b.status === 'approved')
  const rejectedBundles = bundles.filter(b => b.status === 'rejected')

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
        <span className="ml-2 text-slate-500">Loading proposed initiatives...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      </div>
    )
  }

  if (bundles.length === 0) {
    return (
      <div className="text-center py-12 border border-dashed border-slate-300 dark:border-slate-600 rounded-lg">
        <Boxes className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
        <p className="text-slate-500 dark:text-slate-400">No proposed initiatives yet</p>
        <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
          Run the Synthesis agent to generate proposed initiatives
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {proposedBundles.length}
          </div>
          <div className="text-sm text-blue-600 dark:text-blue-400">Proposed</div>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {approvedBundles.length}
          </div>
          <div className="text-sm text-green-600 dark:text-green-400">Approved</div>
        </div>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">
            {rejectedBundles.length}
          </div>
          <div className="text-sm text-red-600 dark:text-red-400">Rejected</div>
        </div>
      </div>

      {/* Proposed bundles (primary focus) */}
      {proposedBundles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-500" />
            Pending Review ({proposedBundles.length})
          </h3>
          <div className="space-y-3">
            {proposedBundles.map(bundle => (
              <BundleCard
                key={bundle.id}
                bundle={bundle}
                canEdit={canEdit}
                onApprove={() => openApprovalModal(bundle.id)}
                onReject={() => setRejectingBundle(bundle.id)}
                onEdit={() => {/* TODO: Edit modal */}}
              />
            ))}
          </div>
        </div>
      )}

      {/* Project creation success message */}
      {projectSuccessMessage && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" />
          <span className="text-sm text-green-700 dark:text-green-300">{projectSuccessMessage}</span>
          <button
            onClick={() => setProjectSuccessMessage(null)}
            className="ml-auto text-green-500 hover:text-green-700 dark:hover:text-green-300"
          >
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Approved bundles */}
      {approvedBundles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Approved ({approvedBundles.length})
          </h3>
          <div className="space-y-3">
            {approvedBundles.map(bundle => (
              <BundleCard
                key={bundle.id}
                bundle={bundle}
                canEdit={false}
                onApprove={() => {}}
                onReject={() => {}}
                onEdit={() => {}}
                onCreateProject={() => handleCreateProject(bundle.id)}
                creatingProject={creatingProjectBundle === bundle.id}
                createdProjectId={createdProjects[bundle.id] || null}
              />
            ))}
          </div>
        </div>
      )}

      {/* Rejected bundles */}
      {rejectedBundles.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-500" />
            Rejected ({rejectedBundles.length})
          </h3>
          <div className="space-y-3 opacity-60">
            {rejectedBundles.map(bundle => (
              <BundleCard
                key={bundle.id}
                bundle={bundle}
                canEdit={false}
                onApprove={() => {}}
                onReject={() => {}}
                onEdit={() => {}}
              />
            ))}
          </div>
        </div>
      )}

      {/* Reject modal */}
      {rejectingBundle && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Reject Proposed Initiative
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Please provide feedback explaining why this proposed initiative is being rejected.
            </p>
            <textarea
              value={rejectFeedback}
              onChange={(e) => setRejectFeedback(e.target.value)}
              placeholder="Feedback required..."
              className="w-full p-3 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white resize-none"
              rows={3}
            />
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => {
                  setRejectingBundle(null)
                  setRejectFeedback('')
                }}
                className="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleReject(rejectingBundle, rejectFeedback)}
                disabled={!rejectFeedback.trim() || actionLoading === rejectingBundle}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {actionLoading === rejectingBundle ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  'Reject'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Approval modal with output type selection */}
      {approvingBundle && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Approve Proposed Initiative
            </h3>

            {/* AI Suggestion */}
            {suggestionLoading ? (
              <div className="flex items-center gap-2 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg mb-4">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  Analyzing proposed initiative to suggest output type...
                </span>
              </div>
            ) : suggestedOutputType && (
              <div className="p-3 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg mb-4">
                <div className="flex items-center gap-2 mb-1">
                  <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <span className="text-sm font-medium text-indigo-900 dark:text-indigo-200">
                    AI suggests: {OUTPUT_TYPES.find(t => t.value === suggestedOutputType)?.label}
                  </span>
                </div>
                {suggestionRationale && (
                  <p className="text-xs text-indigo-700 dark:text-indigo-300 ml-6">
                    {suggestionRationale}
                  </p>
                )}
              </div>
            )}

            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Select the document type to generate after approval:
            </p>

            {/* Output type selection */}
            <div className="space-y-2 mb-6">
              {OUTPUT_TYPES.map((type) => {
                const TypeIcon = type.icon
                const isSelected = selectedOutputType === type.value
                const isSuggested = suggestedOutputType === type.value

                return (
                  <button
                    key={type.value}
                    onClick={() => setSelectedOutputType(type.value)}
                    className={`w-full flex items-start gap-3 p-3 rounded-lg border transition-colors text-left ${
                      isSelected
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'
                    }`}
                  >
                    <TypeIcon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                      isSelected ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`font-medium text-sm ${
                          isSelected ? 'text-indigo-900 dark:text-indigo-100' : 'text-slate-900 dark:text-slate-100'
                        }`}>
                          {type.label}
                        </span>
                        {isSuggested && (
                          <span className="text-xs px-1.5 py-0.5 bg-indigo-100 dark:bg-indigo-800 text-indigo-700 dark:text-indigo-300 rounded">
                            Suggested
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {type.description}
                      </p>
                    </div>
                    <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                      isSelected
                        ? 'border-indigo-500 bg-indigo-500'
                        : 'border-slate-300 dark:border-slate-500'
                    }`}>
                      {isSelected && (
                        <CheckCircle className="w-3 h-3 text-white" />
                      )}
                    </div>
                  </button>
                )
              })}
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setApprovingBundle(null)
                  setSelectedOutputType('prd')
                  setSuggestedOutputType(null)
                  setSuggestionRationale(null)
                }}
                className="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleApprove(approvingBundle, selectedOutputType)}
                disabled={actionLoading === approvingBundle}
                className="flex items-center gap-1.5 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {actionLoading === approvingBundle ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Approve & Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
