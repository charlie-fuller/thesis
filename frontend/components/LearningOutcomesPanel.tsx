'use client'

import { useState, useEffect } from 'react'
import {
  getProjectOutcomes,
  createOutcome,
  updateOutcome,
  recordOutcomeMeasurement,
  deleteOutcome,
  getMetricTypes,
  type LearningOutcome,
  type MetricType
} from '@/lib/api'
import LoadingSpinner from './LoadingSpinner'
import ConfirmModal from './ConfirmModal'
import toast from 'react-hot-toast'
import { logger } from '@/lib/logger'

// Status badge colors
const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  'pending': { bg: 'bg-gray-100', text: 'text-gray-700' },
  'in_progress': { bg: 'bg-blue-100', text: 'text-blue-700' },
  'achieved': { bg: 'bg-green-100', text: 'text-green-700' },
  'missed': { bg: 'bg-red-100', text: 'text-red-700' },
  'partial': { bg: 'bg-yellow-100', text: 'text-yellow-700' },
}

interface LearningOutcomesPanelProps {
  projectId: string
  projectTitle?: string
  className?: string
}

export default function LearningOutcomesPanel({
  projectId,
  // projectTitle kept for future use in panel header
  projectTitle: _projectTitle,
  className = ''
}: LearningOutcomesPanelProps) {
  const [outcomes, setOutcomes] = useState<LearningOutcome[]>([])
  const [summary, setSummary] = useState<{
    total: number
    achieved: number
    in_progress: number
    pending: number
    achievement_rate: number
  } | null>(null)
  const [metricTypes, setMetricTypes] = useState<MetricType[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingOutcome, setEditingOutcome] = useState<LearningOutcome | null>(null)
  const [recordingMeasurement, setRecordingMeasurement] = useState<LearningOutcome | null>(null)

  // Form state
  const [formTitle, setFormTitle] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [formMetricType, setFormMetricType] = useState('completion_rate')
  const [formBaseline, setFormBaseline] = useState('')
  const [formTarget, setFormTarget] = useState('')
  const [formUnit, setFormUnit] = useState('%')
  const [formTargetDate, setFormTargetDate] = useState('')
  const [formNotes, setFormNotes] = useState('')

  // Measurement form
  const [measurementValue, setMeasurementValue] = useState('')
  const [measurementNotes, setMeasurementNotes] = useState('')

  // Modal state
  const [confirmModal, setConfirmModal] = useState<{
    open: boolean
    title: string
    message: string
    onConfirm: () => void
  }>({
    open: false,
    title: '',
    message: '',
    onConfirm: () => {}
  })

  useEffect(() => {
    loadOutcomes()
    loadMetricTypes()
  }, [projectId])

  async function loadOutcomes() {
    try {
      setLoading(true)
      const response = await getProjectOutcomes(projectId)
      if (response.success) {
        setOutcomes(response.outcomes)
        setSummary(response.summary)
      }
    } catch (err) {
      logger.error('Error loading outcomes:', err)
    } finally {
      setLoading(false)
    }
  }

  async function loadMetricTypes() {
    try {
      const response = await getMetricTypes()
      if (response.success) {
        setMetricTypes(response.metric_types)
      }
    } catch (err) {
      logger.error('Error loading metric types:', err)
    }
  }

  function handleStartCreate() {
    setShowCreateForm(true)
    setEditingOutcome(null)
    resetForm()
  }

  function handleStartEdit(outcome: LearningOutcome) {
    setEditingOutcome(outcome)
    setShowCreateForm(false)
    setFormTitle(outcome.title)
    setFormDescription(outcome.description || '')
    setFormMetricType(outcome.metric_type)
    setFormBaseline(outcome.baseline_value?.toString() || '')
    setFormTarget(outcome.target_value?.toString() || '')
    setFormUnit(outcome.unit || '%')
    setFormTargetDate(outcome.target_date || '')
    setFormNotes(outcome.notes || '')
  }

  function resetForm() {
    setFormTitle('')
    setFormDescription('')
    setFormMetricType('completion_rate')
    setFormBaseline('')
    setFormTarget('')
    setFormUnit('%')
    setFormTargetDate('')
    setFormNotes('')
  }

  function handleCancelForm() {
    setShowCreateForm(false)
    setEditingOutcome(null)
    resetForm()
  }

  async function handleSaveOutcome() {
    if (!formTitle.trim()) {
      toast.error('Outcome title is required')
      return
    }

    try {
      if (editingOutcome) {
        await updateOutcome(editingOutcome.id, {
          title: formTitle.trim(),
          description: formDescription.trim() || undefined,
          baseline_value: formBaseline ? parseFloat(formBaseline) : undefined,
          target_value: formTarget ? parseFloat(formTarget) : undefined,
          unit: formUnit || undefined,
          target_date: formTargetDate || undefined,
          notes: formNotes.trim() || undefined
        })
        toast.success('Outcome updated successfully')
      } else {
        await createOutcome({
          project_id: projectId,
          title: formTitle.trim(),
          description: formDescription.trim() || undefined,
          metric_type: formMetricType,
          baseline_value: formBaseline ? parseFloat(formBaseline) : undefined,
          target_value: formTarget ? parseFloat(formTarget) : undefined,
          unit: formUnit || undefined,
          target_date: formTargetDate || undefined,
          notes: formNotes.trim() || undefined
        })
        toast.success('Outcome created successfully')
      }

      await loadOutcomes()
      handleCancelForm()
    } catch (err) {
      logger.error('Error saving outcome:', err)
      toast.error('Failed to save outcome')
    }
  }

  function handleStartMeasurement(outcome: LearningOutcome) {
    setRecordingMeasurement(outcome)
    setMeasurementValue(outcome.actual_value?.toString() || '')
    setMeasurementNotes('')
  }

  function handleCancelMeasurement() {
    setRecordingMeasurement(null)
    setMeasurementValue('')
    setMeasurementNotes('')
  }

  async function handleRecordMeasurement() {
    if (!recordingMeasurement) return
    if (!measurementValue) {
      toast.error('Please enter a measurement value')
      return
    }

    try {
      const response = await recordOutcomeMeasurement(recordingMeasurement.id, {
        actual_value: parseFloat(measurementValue),
        notes: measurementNotes.trim() || undefined
      })

      toast.success(`Measurement recorded - Status: ${response.status}`)
      await loadOutcomes()
      handleCancelMeasurement()
    } catch (err) {
      logger.error('Error recording measurement:', err)
      toast.error('Failed to record measurement')
    }
  }

  async function handleDeleteOutcome(outcomeId: string) {
    setConfirmModal({
      open: true,
      title: 'Delete Outcome',
      message: 'Are you sure you want to delete this learning outcome? This action cannot be undone.',
      onConfirm: async () => {
        try {
          await deleteOutcome(outcomeId)
          toast.success('Outcome deleted successfully')
          await loadOutcomes()
        } catch (err) {
          logger.error('Error deleting outcome:', err)
          toast.error('Failed to delete outcome')
        }
      }
    })
  }

  function calculateProgress(outcome: LearningOutcome): number {
    if (outcome.baseline_value === undefined || outcome.target_value === undefined) return 0
    if (outcome.actual_value === undefined) return 0
    if (outcome.target_value === outcome.baseline_value) return 100

    const progress = ((outcome.actual_value - outcome.baseline_value) / (outcome.target_value - outcome.baseline_value)) * 100
    return Math.min(100, Math.max(0, progress))
  }

  const selectedMetric = metricTypes.find(m => m.id === formMetricType)

  if (loading) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      </div>
    )
  }

  return (
    <div className={`${className}`}>
      {/* Header with Summary */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-primary">Learning Outcomes</h3>
          {summary && summary.total > 0 && (
            <p className="text-sm text-muted mt-1">
              {summary.achieved} of {summary.total} achieved ({summary.achievement_rate}%)
            </p>
          )}
        </div>
        <button
          onClick={handleStartCreate}
          className="btn-primary text-sm px-3 py-1.5"
        >
          + Add Outcome
        </button>
      </div>

      {/* Summary Stats */}
      {summary && summary.total > 0 && (
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-gray-700">{summary.total}</div>
            <div className="text-xs text-muted">Total</div>
          </div>
          <div className="bg-green-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-700">{summary.achieved}</div>
            <div className="text-xs text-green-600">Achieved</div>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-700">{summary.in_progress}</div>
            <div className="text-xs text-blue-600">In Progress</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-gray-500">{summary.pending}</div>
            <div className="text-xs text-muted">Pending</div>
          </div>
        </div>
      )}

      {/* Create/Edit Form */}
      {(showCreateForm || editingOutcome) && (
        <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-3">
          <h4 className="font-medium text-primary">
            {editingOutcome ? 'Edit Outcome' : 'New Learning Outcome'}
          </h4>

          <div>
            <label className="block text-xs text-muted mb-1">Title *</label>
            <input
              type="text"
              value={formTitle}
              onChange={(e) => setFormTitle(e.target.value)}
              placeholder="e.g., Course Completion Rate"
              className="input-field w-full text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-muted mb-1">Description</label>
            <textarea
              value={formDescription}
              onChange={(e) => setFormDescription(e.target.value)}
              placeholder="Describe what this outcome measures..."
              rows={2}
              className="input-field w-full text-sm resize-none"
            />
          </div>

          {!editingOutcome && (
            <div>
              <label className="block text-xs text-muted mb-1">Metric Type</label>
              <select
                value={formMetricType}
                onChange={(e) => {
                  setFormMetricType(e.target.value)
                  const metric = metricTypes.find(m => m.id === e.target.value)
                  if (metric) setFormUnit(metric.unit)
                }}
                className="input-field w-full text-sm"
              >
                {metricTypes.map((type) => (
                  <option key={type.id} value={type.id}>{type.name}</option>
                ))}
              </select>
              {selectedMetric && (
                <p className="text-xs text-muted mt-1 italic">{selectedMetric.example}</p>
              )}
            </div>
          )}

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-muted mb-1">Baseline</label>
              <input
                type="number"
                value={formBaseline}
                onChange={(e) => setFormBaseline(e.target.value)}
                placeholder="0"
                className="input-field w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1">Target</label>
              <input
                type="number"
                value={formTarget}
                onChange={(e) => setFormTarget(e.target.value)}
                placeholder="100"
                className="input-field w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1">Unit</label>
              <input
                type="text"
                value={formUnit}
                onChange={(e) => setFormUnit(e.target.value)}
                placeholder="%"
                className="input-field w-full text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-muted mb-1">Target Date</label>
            <input
              type="date"
              value={formTargetDate}
              onChange={(e) => setFormTargetDate(e.target.value)}
              className="input-field w-full text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-muted mb-1">Notes</label>
            <textarea
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              placeholder="Any additional notes..."
              rows={2}
              className="input-field w-full text-sm resize-none"
            />
          </div>

          <div className="flex gap-2 pt-2">
            <button onClick={handleSaveOutcome} className="btn-primary text-sm px-4 py-1.5">
              {editingOutcome ? 'Update' : 'Create'}
            </button>
            <button onClick={handleCancelForm} className="btn-secondary text-sm px-4 py-1.5">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Measurement Recording Form */}
      {recordingMeasurement && (
        <div className="bg-blue-50 rounded-lg p-4 mb-4 space-y-3">
          <h4 className="font-medium text-blue-800">
            Record Measurement: {recordingMeasurement.title}
          </h4>
          <p className="text-sm text-blue-600">
            Target: {recordingMeasurement.target_value} {recordingMeasurement.unit}
            {recordingMeasurement.baseline_value !== undefined && (
              <> | Baseline: {recordingMeasurement.baseline_value} {recordingMeasurement.unit}</>
            )}
          </p>

          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-xs text-blue-700 mb-1">Actual Value</label>
              <input
                type="number"
                value={measurementValue}
                onChange={(e) => setMeasurementValue(e.target.value)}
                placeholder={`Enter value in ${recordingMeasurement.unit || 'units'}`}
                className="input-field w-full text-sm"
                autoFocus
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-blue-700 mb-1">Notes (optional)</label>
            <input
              type="text"
              value={measurementNotes}
              onChange={(e) => setMeasurementNotes(e.target.value)}
              placeholder="Add measurement notes..."
              className="input-field w-full text-sm"
            />
          </div>

          <div className="flex gap-2">
            <button onClick={handleRecordMeasurement} className="btn-primary text-sm px-4 py-1.5">
              Record
            </button>
            <button onClick={handleCancelMeasurement} className="btn-secondary text-sm px-4 py-1.5">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Outcomes List */}
      {outcomes.length === 0 ? (
        <div className="text-center py-8 text-muted">
          <p className="mb-2">No learning outcomes defined yet.</p>
          <p className="text-sm">Add outcomes to track the impact of your training.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {outcomes.map((outcome) => {
            const progress = calculateProgress(outcome)
            const colors = STATUS_COLORS[outcome.status] || STATUS_COLORS['pending']

            return (
              <div key={outcome.id} className="bg-white border border-gray-200 rounded-lg p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-medium text-primary">{outcome.title}</h4>
                    {outcome.description && (
                      <p className="text-sm text-muted mt-1">{outcome.description}</p>
                    )}
                  </div>
                  <span className={`text-xs px-2 py-1 rounded ${colors.bg} ${colors.text} capitalize ml-2`}>
                    {outcome.status.replace('_', ' ')}
                  </span>
                </div>

                {/* Progress Bar */}
                {outcome.target_value !== undefined && (
                  <div className="mb-3">
                    <div className="flex justify-between text-xs text-muted mb-1">
                      <span>
                        {outcome.baseline_value !== undefined ? `${outcome.baseline_value}` : '0'} {outcome.unit}
                      </span>
                      <span>
                        {outcome.actual_value !== undefined && (
                          <span className="font-medium text-primary mr-2">
                            Current: {outcome.actual_value} {outcome.unit}
                          </span>
                        )}
                        Target: {outcome.target_value} {outcome.unit}
                      </span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          outcome.status === 'achieved' ? 'bg-green-500' :
                          outcome.status === 'missed' ? 'bg-red-400' :
                          'bg-blue-500'
                        }`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Meta info */}
                <div className="flex items-center justify-between text-xs text-muted">
                  <div className="flex items-center gap-3">
                    <span className="capitalize">{outcome.metric_type.replace('_', ' ')}</span>
                    {outcome.target_date && (
                      <span>Due: {new Date(outcome.target_date).toLocaleDateString()}</span>
                    )}
                    {outcome.measured_at && (
                      <span>Measured: {new Date(outcome.measured_at).toLocaleDateString()}</span>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleStartMeasurement(outcome)}
                      className="text-blue-600 hover:text-blue-800 transition-colors"
                      title="Record measurement"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleStartEdit(outcome)}
                      className="text-gray-500 hover:text-gray-700 transition-colors"
                      title="Edit"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleDeleteOutcome(outcome.id)}
                      className="text-gray-500 hover:text-red-600 transition-colors"
                      title="Delete"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Notes */}
                {outcome.notes && (
                  <div className="mt-2 text-xs text-muted bg-gray-50 rounded p-2">
                    {outcome.notes}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Confirm Modal */}
      <ConfirmModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        onConfirm={confirmModal.onConfirm}
        onCancel={() => setConfirmModal({ ...confirmModal, open: false })}
      />
    </div>
  )
}
