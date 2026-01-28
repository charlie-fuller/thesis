'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, ChevronRight, Check, XIcon, FileText, Link2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiPost } from '@/lib/api'

interface OpportunityCandidate {
  id: string
  title: string
  description?: string
  department?: string
  source_document_id?: string
  source_document_name?: string
  source_text?: string
  suggested_roi_potential?: number
  suggested_effort?: number
  suggested_alignment?: number
  suggested_readiness?: number
  potential_impact?: string
  related_stakeholder_names?: string[]
  status: string
  confidence: string
  matched_opportunity_id?: string
  matched_candidate_id?: string
  match_confidence?: number
  match_reason?: string
  created_at: string
}

interface OpportunityCandidateReviewModalProps {
  open: boolean
  onClose: () => void
  onComplete: (stats: { accepted: number; rejected: number; linked: number }) => void
  candidates: OpportunityCandidate[]
}

const DEPARTMENT_OPTIONS = [
  'Finance',
  'Legal',
  'IT',
  'HR',
  'Operations',
  'Marketing',
  'Sales',
  'Engineering',
  'Executive',
  'Other',
]

const SCORE_OPTIONS = [
  { value: 1, label: '1 - Low' },
  { value: 2, label: '2 - Below Average' },
  { value: 3, label: '3 - Average' },
  { value: 4, label: '4 - Above Average' },
  { value: 5, label: '5 - High' },
]

export default function OpportunityCandidateReviewModal({
  open,
  onClose,
  onComplete,
  candidates: initialCandidates,
}: OpportunityCandidateReviewModalProps) {
  const [candidates, setCandidates] = useState<OpportunityCandidate[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [saving, setSaving] = useState(false)
  const [stats, setStats] = useState({ accepted: 0, rejected: 0, linked: 0 })

  // Form state for current candidate
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [department, setDepartment] = useState('')
  const [roiPotential, setRoiPotential] = useState(3)
  const [effort, setEffort] = useState(3)
  const [alignment, setAlignment] = useState(3)
  const [readiness, setReadiness] = useState(3)

  // Initialize candidates when modal opens
  useEffect(() => {
    if (open && initialCandidates.length > 0) {
      setCandidates(initialCandidates)
      setCurrentIndex(0)
      setStats({ accepted: 0, rejected: 0, linked: 0 })
      loadCandidate(initialCandidates[0])
    }
  }, [open, initialCandidates])

  // Load candidate data into form
  const loadCandidate = useCallback((candidate: OpportunityCandidate) => {
    setTitle(candidate.title || '')
    setDescription(candidate.description || '')
    setDepartment(candidate.department || '')
    setRoiPotential(candidate.suggested_roi_potential || 3)
    setEffort(candidate.suggested_effort || 3)
    setAlignment(candidate.suggested_alignment || 3)
    setReadiness(candidate.suggested_readiness || 3)
  }, [])

  // Move to next candidate or finish
  const moveToNext = useCallback(() => {
    if (currentIndex < candidates.length - 1) {
      const nextIndex = currentIndex + 1
      setCurrentIndex(nextIndex)
      loadCandidate(candidates[nextIndex])
    } else {
      // All candidates reviewed
      onComplete(stats)
    }
  }, [currentIndex, candidates, stats, loadCandidate, onComplete])

  // Accept current candidate and create opportunity
  const handleAccept = useCallback(async () => {
    const candidate = candidates[currentIndex]
    if (!candidate) return

    setSaving(true)
    try {
      await apiPost(`/api/opportunities/candidates/${candidate.id}/accept`, {
        title: title.trim(),
        description: description.trim() || null,
        department: department || null,
        roi_potential: roiPotential,
        implementation_effort: effort,
        strategic_alignment: alignment,
        stakeholder_readiness: readiness,
        link_to_existing: false,
      })
      toast.success('Opportunity created')
      setStats(prev => ({ ...prev, accepted: prev.accepted + 1 }))
      moveToNext()
    } catch (error) {
      console.error('Failed to accept candidate:', error)
      toast.error('Failed to create opportunity')
    } finally {
      setSaving(false)
    }
  }, [candidates, currentIndex, title, description, department, roiPotential, effort, alignment, readiness, moveToNext])

  // Link to existing opportunity (when duplicate detected)
  const handleLinkToExisting = useCallback(async () => {
    const candidate = candidates[currentIndex]
    if (!candidate || !candidate.matched_opportunity_id) return

    setSaving(true)
    try {
      await apiPost(`/api/opportunities/candidates/${candidate.id}/accept`, {
        link_to_existing: true,
      })
      toast.success('Linked to existing opportunity')
      setStats(prev => ({ ...prev, linked: prev.linked + 1 }))
      moveToNext()
    } catch (error) {
      console.error('Failed to link candidate:', error)
      toast.error('Failed to link to existing opportunity')
    } finally {
      setSaving(false)
    }
  }, [candidates, currentIndex, moveToNext])

  // Reject current candidate (skip without creating)
  const handleReject = useCallback(async () => {
    const candidate = candidates[currentIndex]
    if (!candidate) return

    setSaving(true)
    try {
      await apiPost(`/api/opportunities/candidates/${candidate.id}/reject`, {
        reason: 'Skipped during review'
      })
      setStats(prev => ({ ...prev, rejected: prev.rejected + 1 }))
      moveToNext()
    } catch (error) {
      console.error('Failed to reject candidate:', error)
      toast.error('Failed to skip opportunity')
    } finally {
      setSaving(false)
    }
  }, [candidates, currentIndex, moveToNext])

  if (!open || candidates.length === 0) return null

  const currentCandidate = candidates[currentIndex]
  const isLast = currentIndex === candidates.length - 1
  const progress = ((currentIndex + 1) / candidates.length) * 100
  const hasPotentialMatch = !!currentCandidate.matched_opportunity_id || !!currentCandidate.matched_candidate_id

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-card rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-default">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-primary">
              Review Opportunity Candidates
            </h2>
            <span className="text-sm text-secondary">
              {currentIndex + 1} of {candidates.length}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-muted hover:text-primary rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full bg-emerald-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Potential match warning */}
        {hasPotentialMatch && (
          <div className="px-4 py-3 bg-amber-500/10 border-b border-amber-500/30">
            <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
              <Link2 className="w-4 h-4" />
              <span className="font-medium">Potential match found</span>
            </div>
            <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
              {currentCandidate.match_reason}
            </p>
            <button
              onClick={handleLinkToExisting}
              disabled={saving}
              className="mt-2 text-sm text-amber-600 dark:text-amber-400 underline hover:no-underline"
            >
              Link to existing opportunity instead
            </button>
          </div>
        )}

        {/* Source info */}
        <div className="px-4 py-3 bg-page border-b border-default">
          <div className="flex items-center gap-2 text-sm text-secondary">
            <FileText className="w-4 h-4" />
            <span className="font-medium">From: {currentCandidate.source_document_name || 'Unknown document'}</span>
            <span className={`ml-auto px-2 py-0.5 rounded text-xs font-medium ${
              currentCandidate.confidence === 'high'
                ? 'bg-green-500/20 text-green-400'
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {currentCandidate.confidence} confidence
            </span>
          </div>

          {/* Source quote */}
          {currentCandidate.source_text && (
            <div className="mt-2 text-xs text-muted italic border-l-2 border-emerald-500/50 pl-2">
              &ldquo;{currentCandidate.source_text}&rdquo;
            </div>
          )}

          {/* Related stakeholders */}
          {currentCandidate.related_stakeholder_names && currentCandidate.related_stakeholder_names.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {currentCandidate.related_stakeholder_names.map((name, i) => (
                <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-purple-500/20 text-purple-400">
                  {name}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Form */}
        <div className="p-4 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What is this opportunity?"
              className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-emerald-500"
              autoFocus
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Additional details about this opportunity..."
              rows={3}
              className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none text-sm"
            />
          </div>

          {/* Department */}
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Department
            </label>
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">Select department...</option>
              {DEPARTMENT_OPTIONS.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>

          {/* Scores Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                ROI Potential
              </label>
              <select
                value={roiPotential}
                onChange={(e) => setRoiPotential(Number(e.target.value))}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {SCORE_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Implementation Effort
              </label>
              <select
                value={effort}
                onChange={(e) => setEffort(Number(e.target.value))}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {SCORE_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Strategic Alignment
              </label>
              <select
                value={alignment}
                onChange={(e) => setAlignment(Number(e.target.value))}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {SCORE_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Stakeholder Readiness
              </label>
              <select
                value={readiness}
                onChange={(e) => setReadiness(Number(e.target.value))}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {SCORE_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between p-4 border-t border-default bg-page">
          <button
            type="button"
            onClick={handleReject}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
          >
            <XIcon className="w-4 h-4" />
            Skip (Not Valid)
          </button>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">
              {stats.accepted} created, {stats.linked} linked, {stats.rejected} skipped
            </span>
            <button
              type="button"
              onClick={handleAccept}
              disabled={saving || !title.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              <Check className="w-4 h-4" />
              {isLast ? 'Create & Finish' : 'Create & Next'}
              {!isLast && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
