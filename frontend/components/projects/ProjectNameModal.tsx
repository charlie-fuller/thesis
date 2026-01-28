'use client'

import { useState, useEffect } from 'react'
import { X, Rocket } from 'lucide-react'

interface ProjectNameModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (projectName: string, projectDescription?: string) => void
  opportunityTitle?: string
  newStatus: 'scoping' | 'pilot'
}

export default function ProjectNameModal({
  open,
  onClose,
  onSubmit,
  opportunityTitle,
  newStatus,
}: ProjectNameModalProps) {
  const [projectName, setProjectName] = useState('')
  const [projectDescription, setProjectDescription] = useState('')

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setProjectName('')
      setProjectDescription('')
    }
  }, [open])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (projectName.trim()) {
      onSubmit(projectName.trim(), projectDescription.trim() || undefined)
    }
  }

  if (!open) return null

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-card rounded-lg shadow-xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-default">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10">
              <Rocket className="w-5 h-5 text-emerald-500" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-primary">
                Name This Project
              </h2>
              <p className="text-sm text-secondary">
                Moving to {newStatus === 'scoping' ? 'Scoping' : 'Pilot'} phase
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-muted hover:text-primary rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {opportunityTitle && (
            <div className="text-sm text-secondary bg-page p-3 rounded-lg border border-default">
              <span className="font-medium">Opportunity:</span> {opportunityTitle}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Project Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g., Contract Analysis Initiative"
              className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-emerald-500"
              autoFocus
              required
            />
            <p className="text-xs text-muted mt-1">
              Give this project a memorable name for tracking
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Project Description
            </label>
            <textarea
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              placeholder="Brief description of project scope..."
              rows={3}
              className="w-full px-3 py-2 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none text-sm"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-secondary hover:text-primary transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!projectName.trim()}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              Continue to {newStatus === 'scoping' ? 'Scoping' : 'Pilot'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
