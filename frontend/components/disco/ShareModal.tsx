'use client'

import { useState, useEffect } from 'react'
import {
  X,
  Users,
  User,
  Mail,
  Trash2,
  ChevronDown,
  Loader2,
  Crown,
  Eye,
  Edit3,
  AlertCircle
} from 'lucide-react'
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api'

interface Member {
  id: string
  initiative_id: string
  user_id: string
  role: 'owner' | 'editor' | 'viewer'
  invited_at: string
  user: {
    id: string
    email: string
    name: string
  }
}

interface ShareModalProps {
  open: boolean
  onClose: () => void
  initiativeId: string
  userRole: string
}

const ROLE_CONFIG = {
  owner: { label: 'Owner', icon: Crown, color: 'text-amber-600' },
  editor: { label: 'Editor', icon: Edit3, color: 'text-blue-600' },
  viewer: { label: 'Viewer', icon: Eye, color: 'text-slate-600' },
}

export default function ShareModal({
  open,
  onClose,
  initiativeId,
  userRole
}: ShareModalProps) {
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'editor' | 'viewer'>('viewer')
  const [inviting, setInviting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canManageMembers = userRole === 'owner' || userRole === 'editor'
  const canChangeRoles = userRole === 'owner'

  // Load members
  useEffect(() => {
    if (!open) return

    const loadMembers = async () => {
      try {
        setLoading(true)
        const result = await apiGet<{ success: boolean; members: Member[] }>(
          `/api/disco/initiatives/${initiativeId}/members`
        )
        setMembers(result.members || [])
      } catch (err) {
        console.error('Failed to load members:', err)
      } finally {
        setLoading(false)
      }
    }
    loadMembers()
  }, [open, initiativeId])

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!email.trim()) return

    setInviting(true)
    setError(null)

    try {
      const result = await apiPost<{ success: boolean; member: Member }>(
        `/api/disco/initiatives/${initiativeId}/members`,
        { email: email.trim(), role }
      )

      if (result.success && result.member) {
        setMembers(prev => [...prev, result.member])
        setEmail('')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to invite member')
    } finally {
      setInviting(false)
    }
  }

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await apiPatch(`/api/disco/initiatives/${initiativeId}/members/${userId}`, {
        role: newRole
      })

      setMembers(prev =>
        prev.map(m =>
          m.user_id === userId ? { ...m, role: newRole as Member['role'] } : m
        )
      )
    } catch (err) {
      console.error('Failed to update role:', err)
    }
  }

  const handleRemove = async (userId: string) => {
    if (!confirm('Are you sure you want to remove this member?')) return

    try {
      await apiDelete(`/api/disco/initiatives/${initiativeId}/members/${userId}`)
      setMembers(prev => prev.filter(m => m.user_id !== userId))
    } catch (err) {
      console.error('Failed to remove member:', err)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-slate-500" />
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              Share Initiative
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Invite Form */}
          {canManageMembers && (
            <form onSubmit={handleInvite} className="space-y-3">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter email address"
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as 'editor' | 'viewer')}
                  className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="viewer">Viewer</option>
                  <option value="editor">Editor</option>
                </select>
                <button
                  type="submit"
                  disabled={!email.trim() || inviting}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {inviting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    'Invite'
                  )}
                </button>
              </div>

              {error && (
                <p className="text-sm text-red-600 dark:text-red-400 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {error}
                </p>
              )}
            </form>
          )}

          {/* Members List */}
          <div>
            <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Members ({members.length})
            </h3>

            {loading ? (
              <div className="flex items-center justify-center py-8 text-slate-500">
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                Loading members...
              </div>
            ) : members.length === 0 ? (
              <p className="text-center py-8 text-slate-500">No members yet</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {members.map((member) => {
                  const roleConfig = ROLE_CONFIG[member.role]
                  const RoleIcon = roleConfig.icon

                  return (
                    <div
                      key={member.id}
                      className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg"
                    >
                      <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-600 flex items-center justify-center">
                        <User className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 dark:text-white truncate">
                          {member.user.name || member.user.email}
                        </p>
                        {member.user.name && (
                          <p className="text-sm text-slate-500 dark:text-slate-400 truncate">
                            {member.user.email}
                          </p>
                        )}
                      </div>

                      {/* Role Selector or Badge */}
                      {canChangeRoles && member.role !== 'owner' ? (
                        <select
                          value={member.role}
                          onChange={(e) => handleRoleChange(member.user_id, e.target.value)}
                          className="px-2 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                        >
                          <option value="viewer">Viewer</option>
                          <option value="editor">Editor</option>
                        </select>
                      ) : (
                        <span className={`flex items-center gap-1 px-2 py-1 text-xs font-medium ${roleConfig.color}`}>
                          <RoleIcon className="w-3 h-3" />
                          {roleConfig.label}
                        </span>
                      )}

                      {/* Remove Button */}
                      {canChangeRoles && member.role !== 'owner' && (
                        <button
                          onClick={() => handleRemove(member.user_id)}
                          className="p-1 text-slate-400 hover:text-red-600 dark:hover:text-red-400 rounded transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Role Legend */}
          <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
            <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
              Role Permissions
            </h4>
            <div className="grid grid-cols-3 gap-2 text-xs text-slate-500 dark:text-slate-400">
              <div>
                <span className="font-medium text-amber-600">Owner</span>
                <p>Full access + delete</p>
              </div>
              <div>
                <span className="font-medium text-blue-600">Editor</span>
                <p>Upload + run agents</p>
              </div>
              <div>
                <span className="font-medium text-slate-600">Viewer</span>
                <p>Read only</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
