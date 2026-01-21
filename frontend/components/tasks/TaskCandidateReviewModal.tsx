'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, ChevronRight, ChevronLeft, Check, XIcon, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiPost, apiGet } from '@/lib/api'

interface TaskCandidate {
  id: string
  title: string
  source_document_name: string
  source_text?: string
  suggested_priority: number
  suggested_due_date?: string
  due_date_text?: string
  assignee_name?: string
  confidence: string
  // Rich context fields
  description?: string
  meeting_context?: string
  team?: string
  stakeholder_name?: string
  value_proposition?: string
  document_date?: string
  topics?: string[]
}

interface TaskCandidateReviewModalProps {
  open: boolean
  onClose: () => void
  onComplete: (stats: { accepted: number; rejected: number }) => void
  candidates: TaskCandidate[]
}

const STATUS_OPTIONS = [
  { value: 'pending', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'completed', label: 'Done' },
]

const PRIORITY_OPTIONS = [
  { value: 1, label: 'Low' },
  { value: 2, label: 'Medium-Low' },
  { value: 3, label: 'Medium' },
  { value: 4, label: 'High' },
  { value: 5, label: 'Critical' },
]

export default function TaskCandidateReviewModal({
  open,
  onClose,
  onComplete,
  candidates: initialCandidates,
}: TaskCandidateReviewModalProps) {
  const [candidates, setCandidates] = useState<TaskCandidate[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [saving, setSaving] = useState(false)
  const [stats, setStats] = useState({ accepted: 0, rejected: 0 })

  // Form state for current candidate
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState('pending')
  const [priority, setPriority] = useState(3)
  const [dueDate, setDueDate] = useState('')
  const [assigneeName, setAssigneeName] = useState('')
  const [category, setCategory] = useState('')
  const [tags, setTags] = useState('')
  const [blockerReason, setBlockerReason] = useState('')

  // Initialize candidates when modal opens
  useEffect(() => {
    if (open && initialCandidates.length > 0) {
      setCandidates(initialCandidates)
      setCurrentIndex(0)
      setStats({ accepted: 0, rejected: 0 })
      loadCandidate(initialCandidates[0])
    }
  }, [open, initialCandidates])

  // Load candidate data into form
  const loadCandidate = useCallback((candidate: TaskCandidate) => {
    setTitle(candidate.title || '')
    // Use rich description if available, otherwise fall back to source_text
    setDescription(candidate.description || candidate.source_text || '')
    setStatus('pending')  // Always start as pending
    setPriority(candidate.suggested_priority || 3)
    setDueDate(candidate.suggested_due_date || '')
    setAssigneeName(candidate.assignee_name || '')
    setCategory('meeting_action')  // Default for document-extracted tasks
    setTags(candidate.topics?.join(', ') || '')
    setBlockerReason('')
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

  // Accept current candidate
  const handleAccept = useCallback(async () => {
    const candidate = candidates[currentIndex]
    if (!candidate) return

    setSaving(true)
    try {
      await apiPost(`/api/tasks/candidates/${candidate.id}/accept`, {
        overrides: {
          title: title.trim(),
          description: description.trim() || null,
          status,
          priority,
          due_date: dueDate || null,
          assignee_name: assigneeName.trim() || null,
          category: category.trim() || null,
          tags: tags.split(',').map(t => t.trim()).filter(Boolean),
          blocker_reason: status === 'blocked' ? blockerReason.trim() || null : null,
        }
      })
      toast.success('Task created')
      setStats(prev => ({ ...prev, accepted: prev.accepted + 1 }))
      moveToNext()
    } catch (error) {
      console.error('Failed to accept candidate:', error)
      toast.error('Failed to create task')
    } finally {
      setSaving(false)
    }
  }, [candidates, currentIndex, title, description, status, priority, dueDate, assigneeName, category, tags, blockerReason, moveToNext])

  // Reject current candidate (skip without creating)
  const handleReject = useCallback(async () => {
    const candidate = candidates[currentIndex]
    if (!candidate) return

    setSaving(true)
    try {
      await apiPost(`/api/tasks/candidates/${candidate.id}/reject`, {
        reason: 'Skipped during review'
      })
      setStats(prev => ({ ...prev, rejected: prev.rejected + 1 }))
      moveToNext()
    } catch (error) {
      console.error('Failed to reject candidate:', error)
      toast.error('Failed to skip task')
    } finally {
      setSaving(false)
    }
  }, [candidates, currentIndex, moveToNext])

  if (!open || candidates.length === 0) return null

  const currentCandidate = candidates[currentIndex]
  const isLast = currentIndex === candidates.length - 1
  const progress = ((currentIndex + 1) / candidates.length) * 100

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
              Review Task Candidates
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
            className="h-full bg-amber-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Source info with rich context */}
        <div className="px-4 py-3 bg-page border-b border-default">
          <div className="flex items-center gap-2 text-sm text-secondary mb-2">
            <FileText className="w-4 h-4" />
            <span className="font-medium">From: {currentCandidate.source_document_name}</span>
            {currentCandidate.document_date && (
              <span className="text-muted">
                ({new Date(currentCandidate.document_date).toLocaleDateString()})
              </span>
            )}
            <span className={`ml-auto px-2 py-0.5 rounded text-xs font-medium ${
              currentCandidate.confidence === 'high'
                ? 'bg-green-500/20 text-green-400'
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {currentCandidate.confidence} confidence
            </span>
          </div>

          {/* Rich context badges */}
          <div className="flex flex-wrap gap-2">
            {currentCandidate.team && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-500/20 text-blue-400">
                Team: {currentCandidate.team}
              </span>
            )}
            {currentCandidate.stakeholder_name && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-purple-500/20 text-purple-400">
                Stakeholder: {currentCandidate.stakeholder_name}
              </span>
            )}
            {currentCandidate.topics?.map((topic) => (
              <span key={topic} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-500/20 text-gray-400">
                {topic}
              </span>
            ))}
          </div>

          {/* Meeting context if available */}
          {currentCandidate.meeting_context && (
            <div className="mt-2 text-xs text-muted italic border-l-2 border-amber-500/50 pl-2">
              {currentCandidate.meeting_context}
            </div>
          )}

          {/* Value proposition if available */}
          {currentCandidate.value_proposition && (
            <div className="mt-2 text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded">
              Value: {currentCandidate.value_proposition}
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
              placeholder="What needs to be done?"
              className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-amber-500"
              autoFocus
            />
          </div>

          {/* Description / Context */}
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Additional details and context..."
              rows={10}
              className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none text-sm"
            />
          </div>

          {/* Source text quote (read-only reference) */}
          {currentCandidate.source_text && currentCandidate.source_text !== description && (
            <div className="text-xs text-muted bg-page p-2 rounded border border-default">
              <span className="font-medium">Source quote:</span>
              <span className="italic ml-1">&ldquo;{currentCandidate.source_text}&rdquo;</span>
            </div>
          )}

          {/* Status & Priority Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                {STATUS_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                {PRIORITY_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Blocker Reason (conditional) */}
          {status === 'blocked' && (
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Blocker Reason
              </label>
              <input
                type="text"
                value={blockerReason}
                onChange={(e) => setBlockerReason(e.target.value)}
                placeholder="What's blocking this task?"
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
          )}

          {/* Assignee & Due Date Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Assignee
              </label>
              <input
                type="text"
                value={assigneeName}
                onChange={(e) => setAssigneeName(e.target.value)}
                placeholder="Who is responsible?"
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Due Date {currentCandidate.due_date_text && (
                  <span className="font-normal text-muted">({currentCandidate.due_date_text})</span>
                )}
              </label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
          </div>

          {/* Category & Tags Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Category
              </label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g., meeting_action"
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Tags
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="tag1, tag2, tag3"
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
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
            Skip (Not a Task)
          </button>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">
              {stats.accepted} accepted, {stats.rejected} skipped
            </span>
            <button
              type="button"
              onClick={handleAccept}
              disabled={saving || !title.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 transition-colors"
            >
              <Check className="w-4 h-4" />
              {isLast ? 'Create Task & Finish' : 'Create Task & Next'}
              {!isLast && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
