'use client'

import { useState, useEffect } from 'react'
import { authenticatedFetch } from '@/lib/api'
import LoadingSpinner from '@/components/LoadingSpinner'

interface Agent {
  id: string
  name: string
  display_name: string
  description: string | null
  is_active: boolean
}

const AGENT_SHORT_DESCRIPTIONS: Record<string, string> = {
  facilitator: 'Meeting orchestration and synthesis',
  atlas: 'GenAI research and benchmarking',
  fortuna: 'ROI analysis and business cases',
  guardian: 'Security, compliance, IT governance',
  counselor: 'Legal, contracts, AI risks',
  oracle: 'Meeting transcript analysis',
  sage: 'Change management and adoption',
  strategist: 'Executive strategy and governance',
  architect: 'Technical architecture and integration',
  operator: 'Process optimization and automation',
  pioneer: 'Emerging tech and innovation',
  catalyst: 'Internal communications and messaging',
  scholar: 'Training and learning programs',
  echo: 'Brand voice and style analysis',
  nexus: 'Systems thinking and interconnections',
}

interface CreateMeetingModalProps {
  onClose: () => void
  onCreate: (data: {
    title: string
    description?: string
    meeting_type: string
    participant_agent_ids: string[]
  }) => void
}

export default function CreateMeetingModal({ onClose, onCreate }: CreateMeetingModalProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [meetingType, setMeetingType] = useState('collaboration')
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      const response = await authenticatedFetch('/api/agents')
      const data = await response.json()

      if (data.success) {
        // Filter to only active agents, exclude coordinator
        const activeAgents = data.agents.filter(
          (a: Agent) => a.is_active && a.name !== 'coordinator'
        )
        setAgents(activeAgents)
      }
    } catch (error) {
      console.error('Error loading agents:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleAgent = (agentId: string) => {
    setSelectedAgents(prev =>
      prev.includes(agentId)
        ? prev.filter(id => id !== agentId)
        : [...prev, agentId]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!title.trim()) {
      return
    }

    if (selectedAgents.length < 2) {
      return
    }

    setSubmitting(true)

    try {
      await onCreate({
        title: title.trim(),
        description: description.trim() || undefined,
        meeting_type: meetingType,
        participant_agent_ids: selectedAgents
      })
    } finally {
      setSubmitting(false)
    }
  }

  const getAgentColor = (name: string): string => {
    const colors: Record<string, string> = {
      facilitator: 'bg-yellow-500',
      atlas: 'bg-blue-500',
      fortuna: 'bg-green-500',
      guardian: 'bg-purple-500',
      counselor: 'bg-amber-500',
      oracle: 'bg-cyan-500',
      sage: 'bg-rose-500',
      strategist: 'bg-indigo-500',
      architect: 'bg-slate-500',
      operator: 'bg-orange-500',
      pioneer: 'bg-emerald-500',
      catalyst: 'bg-pink-500',
      scholar: 'bg-teal-500',
      echo: 'bg-violet-500',
      nexus: 'bg-sky-500'
    }
    return colors[name] || 'bg-gray-500'
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-panel rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-default">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-primary">Create Meeting Room</h2>
            <button
              onClick={onClose}
              className="text-secondary hover:text-primary"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-primary mb-2">
              Meeting Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Q1 Security Investment Discussion"
              className="w-full px-4 py-2 border border-default rounded-lg bg-panel text-primary focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-primary mb-2">
              Description (optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What will this meeting discuss?"
              rows={2}
              className="w-full px-4 py-2 border border-default rounded-lg bg-panel text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
          </div>

          {/* Meeting Type */}
          <div>
            <label className="block text-sm font-medium text-primary mb-2">
              Meeting Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setMeetingType('collaboration')}
                className={`p-4 border rounded-lg text-left transition-colors ${
                  meetingType === 'collaboration'
                    ? 'border-primary bg-primary/10'
                    : 'border-default hover:border-primary/50'
                }`}
              >
                <div className="font-medium text-primary">Collaboration</div>
                <div className="text-sm text-secondary mt-1">
                  Cross-functional discussion with multiple agents
                </div>
              </button>
              <button
                type="button"
                onClick={() => setMeetingType('meeting_prep')}
                className={`p-4 border rounded-lg text-left transition-colors ${
                  meetingType === 'meeting_prep'
                    ? 'border-primary bg-primary/10'
                    : 'border-default hover:border-primary/50'
                }`}
              >
                <div className="font-medium text-primary">Meeting Prep</div>
                <div className="text-sm text-secondary mt-1">
                  Prepare for stakeholder meetings with talking points
                </div>
              </button>
            </div>
          </div>

          {/* Agent Selection */}
          <div>
            <label className="block text-sm font-medium text-primary mb-2">
              Select Agents (minimum 2) *
            </label>
            {loading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="md" />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    type="button"
                    onClick={() => toggleAgent(agent.id)}
                    className={`p-3 border rounded-lg text-left transition-colors ${
                      selectedAgents.includes(agent.id)
                        ? 'border-primary bg-primary/10'
                        : 'border-default hover:border-primary/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full ${getAgentColor(agent.name)} flex items-center justify-center text-white font-semibold text-sm flex-shrink-0`}>
                        {agent.display_name.charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-primary text-sm">
                          {agent.display_name}
                        </div>
                        <div className="text-xs text-secondary truncate">
                          {AGENT_SHORT_DESCRIPTIONS[agent.name] || agent.description || 'AI Agent'}
                        </div>
                      </div>
                      {selectedAgents.includes(agent.id) && (
                        <svg className="w-5 h-5 text-primary flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
            {selectedAgents.length < 2 && (
              <p className="mt-2 text-sm text-amber-600">
                Select at least 2 agents to participate
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-default">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-secondary hover:text-primary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || selectedAgents.length < 2 || submitting}
              className="btn-primary px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? <LoadingSpinner size="sm" /> : 'Create Meeting'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
