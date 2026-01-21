'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiPost, apiPatch, apiDelete, apiGet } from '@/lib/api'
import { Task } from './TaskKanbanBoard'
import ConfirmModal from '@/components/ConfirmModal'

interface TaskCreateModalProps {
  open: boolean
  onClose: () => void
  onSaved: () => void
  editTask: Task | null
  defaultStatus?: Task['status']
}

interface Stakeholder {
  id: string
  name: string
  email: string
  department?: string
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

const TEAM_OPTIONS = [
  { value: '', label: 'None' },
  { value: 'Finance', label: 'Finance' },
  { value: 'Legal', label: 'Legal' },
  { value: 'IT', label: 'IT' },
  { value: 'Operations', label: 'Operations' },
  { value: 'HR', label: 'HR' },
  { value: 'Marketing', label: 'Marketing' },
  { value: 'Sales', label: 'Sales' },
  { value: 'Engineering', label: 'Engineering' },
  { value: 'Executive', label: 'Executive' },
  { value: 'Other', label: 'Other' },
]

export default function TaskCreateModal({
  open,
  onClose,
  onSaved,
  editTask,
  defaultStatus = 'pending',
}: TaskCreateModalProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState<string>('pending')
  const [priority, setPriority] = useState<number>(3)
  const [assigneeStakeholderId, setAssigneeStakeholderId] = useState<string>('')
  const [assigneeName, setAssigneeName] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [category, setCategory] = useState('')
  const [tags, setTags] = useState('')
  const [team, setTeam] = useState('')
  const [blockerReason, setBlockerReason] = useState('')

  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [saving, setSaving] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Load stakeholders for dropdown
  useEffect(() => {
    const loadStakeholders = async () => {
      try {
        const response = await apiGet<{ success: boolean; stakeholders: Stakeholder[] }>('/api/stakeholders')
        if (response.success) {
          setStakeholders(response.stakeholders)
        }
      } catch (error) {
        console.error('Failed to load stakeholders:', error)
      }
    }
    loadStakeholders()
  }, [])

  // Populate form when editing
  useEffect(() => {
    if (editTask) {
      setTitle(editTask.title)
      setDescription(editTask.description || '')
      setStatus(editTask.status)
      setPriority(editTask.priority)
      setAssigneeStakeholderId(editTask.assignee_stakeholder_id || '')
      setAssigneeName(editTask.assignee_name || '')
      setDueDate(editTask.due_date || '')
      setCategory(editTask.category || '')
      setTags(editTask.tags?.join(', ') || '')
      setTeam(editTask.team || '')
      setBlockerReason(editTask.blocker_reason || '')
    } else {
      // Reset form for new task
      setTitle('')
      setDescription('')
      setStatus(defaultStatus)
      setPriority(3)
      setAssigneeStakeholderId('')
      setAssigneeName('')
      setDueDate('')
      setCategory('')
      setTags('')
      setTeam('')
      setBlockerReason('')
    }
  }, [editTask, defaultStatus])

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()

    if (!title.trim()) {
      toast.error('Title is required')
      return
    }

    setSaving(true)

    try {
      const taskData = {
        title: title.trim(),
        description: description.trim() || null,
        status,
        priority,
        assignee_stakeholder_id: assigneeStakeholderId || null,
        assignee_name: assigneeName.trim() || null,
        due_date: dueDate || null,
        category: category.trim() || null,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
        team: team || null,
        blocker_reason: status === 'blocked' ? blockerReason.trim() || null : null,
      }

      if (editTask) {
        await apiPatch(`/api/tasks/${editTask.id}`, taskData)
        toast.success('Task updated')
      } else {
        await apiPost('/api/tasks', taskData)
        toast.success('Task created')
      }

      onSaved()
    } catch (error) {
      console.error('Failed to save task:', error)
      toast.error(editTask ? 'Failed to update task' : 'Failed to create task')
    } finally {
      setSaving(false)
    }
  }, [title, description, status, priority, assigneeStakeholderId, assigneeName, dueDate, category, tags, team, blockerReason, editTask, onSaved])

  const handleDelete = useCallback(async () => {
    if (!editTask) return

    setDeleting(true)
    try {
      await apiDelete(`/api/tasks/${editTask.id}`)
      toast.success('Task deleted')
      onSaved()
    } catch (error) {
      console.error('Failed to delete task:', error)
      toast.error('Failed to delete task')
    } finally {
      setDeleting(false)
      setShowDeleteConfirm(false)
    }
  }, [editTask, onSaved])

  if (!open) return null

  return (
    <>
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
            <h2 className="text-lg font-semibold text-primary">
              {editTask ? 'Edit Task' : 'New Task'}
            </h2>
            <button
              onClick={onClose}
              className="p-1 text-muted hover:text-primary rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
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
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
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
                placeholder="Add more details..."
                rows={15}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand resize-none"
              />
            </div>

            {/* Status & Priority Row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary mb-1">
                  Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
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
                  className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
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
                  className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
                />
              </div>
            )}

            {/* Assignee */}
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Assignee
              </label>
              <select
                value={assigneeStakeholderId}
                onChange={(e) => {
                  setAssigneeStakeholderId(e.target.value)
                  // Clear manual name when selecting from dropdown
                  if (e.target.value) {
                    const stakeholder = stakeholders.find(s => s.id === e.target.value)
                    setAssigneeName(stakeholder?.name || '')
                  }
                }}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
              >
                <option value="">Select a stakeholder...</option>
                {stakeholders.map(s => (
                  <option key={s.id} value={s.id}>
                    {s.name} {s.department ? `(${s.department})` : ''}
                  </option>
                ))}
              </select>
              {!assigneeStakeholderId && (
                <input
                  type="text"
                  value={assigneeName}
                  onChange={(e) => setAssigneeName(e.target.value)}
                  placeholder="Or enter a name manually"
                  className="w-full mt-2 px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
                />
              )}
            </div>

            {/* Due Date */}
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Due Date
              </label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
              />
            </div>

            {/* Team */}
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Team
              </label>
              <select
                value={team}
                onChange={(e) => setTeam(e.target.value)}
                className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
              >
                {TEAM_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
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
                  className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
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
                  className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-brand"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-default">
              {editTask ? (
                <button
                  type="button"
                  onClick={() => setShowDeleteConfirm(true)}
                  disabled={deleting}
                  className="flex items-center gap-2 px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              ) : (
                <div />
              )}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-muted hover:text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand/90 disabled:opacity-50 transition-colors"
                >
                  {saving ? 'Saving...' : editTask ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Delete Confirmation */}
      <ConfirmModal
        open={showDeleteConfirm}
        title="Delete Task"
        message="Are you sure you want to delete this task? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        confirmVariant="danger"
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </>
  )
}
