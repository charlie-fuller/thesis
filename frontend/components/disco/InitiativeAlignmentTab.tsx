'use client'

import { useState, useEffect, useCallback } from 'react'
import { AlertTriangle, ExternalLink, Target } from 'lucide-react'
import { apiGet, apiPatch, apiPost } from '@/lib/api'
import GoalAlignmentSection from '@/components/projects/GoalAlignmentSection'
import { type GoalAlignmentDetails, getAlignmentLevel } from '@/components/projects/GoalAlignmentSection'

interface ProjectRollupItem {
  id: string
  project_code: string
  title: string
  status: string
  goal_alignment_score: number | null
  alignment_level: string | null
}

interface AlignmentRollup {
  total_projects: number
  analyzed_projects: number
  average_score: number | null
  distribution: {
    high: number
    moderate: number
    low: number
    minimal: number
  }
  projects: ProjectRollupItem[]
}

interface InitiativeAlignmentTabProps {
  initiativeId: string
  goalAlignmentScore: number | null
  goalAlignmentDetails: GoalAlignmentDetails | null
  latestOutputCreatedAt: string | null
  canEdit: boolean
  onAlignmentUpdated: (score: number, details: GoalAlignmentDetails) => void
  hasAgentOutputs: boolean
}

export default function InitiativeAlignmentTab({
  initiativeId,
  goalAlignmentScore,
  goalAlignmentDetails,
  latestOutputCreatedAt,
  canEdit,
  onAlignmentUpdated,
  hasAgentOutputs,
}: InitiativeAlignmentTabProps) {
  const [rollup, setRollup] = useState<AlignmentRollup | null>(null)
  const [loadingRollup, setLoadingRollup] = useState(true)

  // Check if analysis is stale (new outputs since last analysis)
  const isStale = (() => {
    if (!goalAlignmentDetails?.analyzed_at || !latestOutputCreatedAt) return false
    return new Date(latestOutputCreatedAt) > new Date(goalAlignmentDetails.analyzed_at)
  })()

  const loadRollup = useCallback(async () => {
    try {
      setLoadingRollup(true)
      const result = await apiGet<{ success: boolean } & AlignmentRollup>(
        `/api/disco/initiatives/${initiativeId}/alignment-rollup`
      )
      if (result.success) {
        setRollup(result)
      }
    } catch (err) {
      console.error('Failed to load alignment rollup:', err)
    } finally {
      setLoadingRollup(false)
    }
  }, [initiativeId])

  useEffect(() => {
    loadRollup()
  }, [loadRollup])

  const handleAnalyze = async () => {
    const result = await apiPost<{
      success: boolean
      goal_alignment_score: number
      goal_alignment_details: GoalAlignmentDetails
    }>(`/api/disco/initiatives/${initiativeId}/analyze-alignment`)

    if (result.success) {
      onAlignmentUpdated(result.goal_alignment_score, result.goal_alignment_details)
    }
  }

  const handleDetailsUpdated = useCallback(async (details: GoalAlignmentDetails) => {
    try {
      await apiPatch(`/api/disco/initiatives/${initiativeId}`, {
        goal_alignment_details: details,
      })
      onAlignmentUpdated(goalAlignmentScore ?? 0, details)
    } catch (err) {
      console.error('Failed to update alignment details:', err)
    }
  }, [initiativeId, goalAlignmentScore, onAlignmentUpdated])

  return (
    <div className="space-y-8">
      {/* Section A: Initiative Alignment */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-6">
        {/* Stale indicator */}
        {isStale && (
          <div className="mb-4 flex items-center gap-2 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-sm text-amber-700 dark:text-amber-400">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            New agent outputs available since last analysis. Re-analyze for updated scores.
          </div>
        )}

        {/* Empty state hint */}
        {!hasAgentOutputs && goalAlignmentScore === null && (
          <div className="mb-4 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-700 dark:text-blue-400">
            Run DISCO agents first (Triage, Strategist, Insight Analyst) for more accurate alignment
            analysis. You can still analyze with just the initiative name and description.
          </div>
        )}

        {canEdit ? (
          <GoalAlignmentSection
            projectId={initiativeId}
            goalAlignmentScore={goalAlignmentScore}
            goalAlignmentDetails={goalAlignmentDetails}
            onAnalyze={handleAnalyze}
            onDetailsUpdated={handleDetailsUpdated}
            canEdit
          />
        ) : goalAlignmentScore !== null ? (
          <GoalAlignmentSection
            projectId={initiativeId}
            goalAlignmentScore={goalAlignmentScore}
            goalAlignmentDetails={goalAlignmentDetails}
            onAnalyze={async () => {}}
          />
        ) : (
          <div className="text-center py-8 text-secondary">
            <Target className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">
              Only editors and owners can run alignment analysis.
            </p>
          </div>
        )}
      </div>

      {/* Section B: Project Roll-up */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-6">
        <h3 className="text-sm font-medium text-primary mb-4 flex items-center gap-2">
          <Target className="w-5 h-5" />
          Linked Project Alignment
        </h3>

        {loadingRollup ? (
          <div className="text-center py-8 text-muted text-sm">Loading project alignment data...</div>
        ) : !rollup || rollup.total_projects === 0 ? (
          <div className="text-center py-8 border border-dashed border-slate-300 dark:border-slate-600 rounded-lg">
            <Target className="w-10 h-10 mx-auto text-slate-400 mb-2" />
            <p className="text-sm text-muted">No projects linked to this initiative yet.</p>
            <p className="text-xs text-muted mt-1">
              Link projects from the Projects tab or create them from PRDs.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Rollup summary */}
            {rollup.analyzed_projects > 0 && (
              <div className="flex items-center gap-4 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                <div>
                  <span className="text-2xl font-bold text-primary">
                    {rollup.average_score}/100
                  </span>
                  <p className="text-xs text-muted">Average across {rollup.analyzed_projects} project{rollup.analyzed_projects !== 1 ? 's' : ''}</p>
                </div>
                <div className="flex gap-3 ml-auto text-xs">
                  {rollup.distribution.high > 0 && (
                    <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                      {rollup.distribution.high} High
                    </span>
                  )}
                  {rollup.distribution.moderate > 0 && (
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded">
                      {rollup.distribution.moderate} Moderate
                    </span>
                  )}
                  {rollup.distribution.low > 0 && (
                    <span className="px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded">
                      {rollup.distribution.low} Low
                    </span>
                  )}
                  {rollup.distribution.minimal > 0 && (
                    <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded">
                      {rollup.distribution.minimal} Minimal
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Not-analyzed notice */}
            {rollup.total_projects > rollup.analyzed_projects && (
              <p className="text-xs text-muted">
                {rollup.total_projects - rollup.analyzed_projects} of {rollup.total_projects} project{rollup.total_projects !== 1 ? 's' : ''} not yet analyzed.
              </p>
            )}

            {/* Project cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {rollup.projects.map((project) => {
                const level = getAlignmentLevel(project.goal_alignment_score)
                return (
                  <a
                    key={project.id}
                    href={`/projects?highlight=${project.id}`}
                    className="flex items-center justify-between p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-indigo-300 dark:hover:border-indigo-600 hover:shadow-sm transition-all group"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-mono text-muted">{project.project_code}</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded capitalize ${
                          project.status === 'active'
                            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                            : project.status === 'completed'
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                        }`}>
                          {project.status}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-primary truncate">{project.title}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-3 flex-shrink-0">
                      {project.goal_alignment_score !== null ? (
                        <span className={`text-sm font-semibold px-2 py-0.5 rounded ${level.bg} ${level.color}`}>
                          {project.goal_alignment_score}
                        </span>
                      ) : (
                        <span className="text-xs text-muted">Not analyzed</span>
                      )}
                      <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-500 transition-colors" />
                    </div>
                  </a>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
