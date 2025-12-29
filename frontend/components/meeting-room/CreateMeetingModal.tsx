'use client'

import { useState, useEffect } from 'react'
import { authenticatedFetch } from '@/lib/api'
import LoadingSpinner from '@/components/LoadingSpinner'
import { AgentIcon, getAgentColor } from '@/components/AgentIcon'

interface Agent {
  id: string
  name: string
  display_name: string
  description: string | null
  is_active: boolean
}

// Meta-agents that always attend meetings
const META_AGENTS = ['facilitator', 'reporter']

const AGENT_SHORT_DESCRIPTIONS: Record<string, string> = {
  // Meta-Agents
  facilitator: 'Meeting orchestration',
  reporter: 'Synthesis and documentation',
  // Stakeholder Perspective Agents
  atlas: 'GenAI research and benchmarking',
  fortuna: 'ROI analysis and business cases',
  guardian: 'Security, compliance, IT governance',
  counselor: 'Legal, contracts, AI risks',
  oracle: 'Meeting transcript analysis',
  sage: 'Change management and adoption',
  // Consulting/Implementation Agents
  strategist: 'Executive strategy and governance',
  architect: 'Technical architecture and integration',
  operator: 'Process optimization and automation',
  pioneer: 'Emerging tech and innovation',
  // Internal Enablement Agents
  catalyst: 'Internal communications and messaging',
  scholar: 'Training and learning programs',
  echo: 'Brand voice and style analysis',
  // Systems Agent
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
  const [metaAgents, setMetaAgents] = useState<Agent[]>([])
  const [selectableAgents, setSelectableAgents] = useState<Agent[]>([])
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

        // Separate meta-agents from selectable agents
        const meta = activeAgents.filter((a: Agent) => META_AGENTS.includes(a.name))
        const selectable = activeAgents.filter((a: Agent) => !META_AGENTS.includes(a.name))

        setMetaAgents(meta)
        setSelectableAgents(selectable)
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
      // Include meta-agents (always attending) plus selected agents
      const metaAgentIds = metaAgents.map(a => a.id)
      const allParticipantIds = [...metaAgentIds, ...selectedAgents]

      await onCreate({
        title: title.trim(),
        description: description.trim() || undefined,
        meeting_type: meetingType,
        participant_agent_ids: allParticipantIds
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="px-4 py-3 border-b border-default">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-primary">Create Meeting Room</h2>
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

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-primary mb-1">
              Meeting Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Q1 Security Investment Discussion"
              className="w-full px-3 py-1.5 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-primary text-sm"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-primary mb-1">
              Description (optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What will this meeting discuss?"
              rows={1}
              className="w-full px-3 py-1.5 border border-default rounded-lg bg-card text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none text-sm"
            />
          </div>

          {/* Meeting Type */}
          <div>
            <label className="block text-sm font-medium text-primary mb-1">
              Meeting Type
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMeetingType('collaboration')}
                className={`flex-1 px-3 py-2 border rounded-lg text-left transition-colors ${
                  meetingType === 'collaboration'
                    ? 'border-primary bg-primary/10'
                    : 'border-default hover:border-primary/50'
                }`}
              >
                <div className="font-medium text-primary text-sm">Collaboration</div>
                <div className="text-xs text-secondary">Cross-functional discussion</div>
              </button>
              <button
                type="button"
                onClick={() => setMeetingType('meeting_prep')}
                className={`flex-1 px-3 py-2 border rounded-lg text-left transition-colors ${
                  meetingType === 'meeting_prep'
                    ? 'border-primary bg-primary/10'
                    : 'border-default hover:border-primary/50'
                }`}
              >
                <div className="font-medium text-primary text-sm">Meeting Prep</div>
                <div className="text-xs text-secondary">Prepare talking points</div>
              </button>
            </div>
          </div>

          {/* Agent Selection */}
          <div>
            <label className="block text-sm font-medium text-primary mb-1">
              Select Agents (minimum 2) *
            </label>
            {loading ? (
              <div className="flex justify-center py-4">
                <LoadingSpinner size="md" />
              </div>
            ) : (
              <div className="space-y-3">
                {/* Meta-Agents - Always Attending */}
                {metaAgents.length > 0 && (
                  <div>
                    <div className="text-xs font-medium text-secondary uppercase tracking-wide mb-1">
                      Always Attending
                    </div>
                    <div className="grid grid-cols-3 gap-1.5">
                      {metaAgents.map((agent) => (
                        <div
                          key={agent.id}
                          className="p-1.5 border rounded-lg border-primary/30 bg-primary/5"
                        >
                          <div className="flex items-center gap-1.5">
                            <div className={`w-5 h-5 rounded-md ${getAgentColor(agent.name)} flex items-center justify-center flex-shrink-0 border`}>
                              <AgentIcon name={agent.name} size="sm" className="w-3 h-3" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-primary text-xs truncate">
                                {agent.display_name}
                              </div>
                              <div className="text-[10px] text-secondary truncate">
                                {AGENT_SHORT_DESCRIPTIONS[agent.name] || ''}
                              </div>
                            </div>
                            <svg className="w-3.5 h-3.5 text-primary flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Selectable Agents */}
                <div>
                  <div className="text-xs font-medium text-secondary uppercase tracking-wide mb-1">
                    Select Additional Agents
                  </div>
                  <div className="grid grid-cols-3 gap-1.5">
                    {selectableAgents.map((agent) => (
                      <button
                        key={agent.id}
                        type="button"
                        onClick={() => toggleAgent(agent.id)}
                        className={`p-1.5 border rounded-lg text-left transition-colors ${
                          selectedAgents.includes(agent.id)
                            ? 'border-primary bg-primary/10'
                            : 'border-default hover:border-primary/50'
                        }`}
                      >
                        <div className="flex items-center gap-1.5">
                          <div className={`w-5 h-5 rounded-md ${getAgentColor(agent.name)} flex items-center justify-center flex-shrink-0 border`}>
                            <AgentIcon name={agent.name} size="sm" className="w-3 h-3" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-primary text-xs truncate">
                              {agent.display_name}
                            </div>
                            <div className="text-[10px] text-secondary truncate">
                              {AGENT_SHORT_DESCRIPTIONS[agent.name] || ''}
                            </div>
                          </div>
                          {selectedAgents.includes(agent.id) && (
                            <svg className="w-3.5 h-3.5 text-primary flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {selectedAgents.length < 2 && (
              <p className="mt-1.5 text-xs text-amber-600">
                Select at least 2 agents to participate
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-3 border-t border-default">
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
