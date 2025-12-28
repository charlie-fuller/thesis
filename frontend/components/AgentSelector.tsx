'use client'

import { useState, useEffect, useRef } from 'react'
import { ChevronDown, X, Plus, Check } from 'lucide-react'
import { AgentIcon, getAgentColor } from './AgentIcon'

export interface Agent {
  id: string
  name: string
  display_name: string
  description?: string
}

interface AgentSelectorProps {
  selectedAgents: string[]
  onAgentsChange: (agents: string[]) => void
  maxAgents?: number
  className?: string
  disabled?: boolean
}

// Agent metadata for display
const AGENT_INFO: Record<string, { displayName: string; description: string; category: string }> = {
  // Stakeholder Perspective Agents
  atlas: {
    displayName: 'Atlas',
    description: 'GenAI research, case studies, thought leadership',
    category: 'Stakeholder',
  },
  fortuna: {
    displayName: 'Fortuna',
    description: 'ROI analysis, budget justification, business cases',
    category: 'Stakeholder',
  },
  guardian: {
    displayName: 'Guardian',
    description: 'Security, compliance, IT governance',
    category: 'Stakeholder',
  },
  counselor: {
    displayName: 'Counselor',
    description: 'Legal considerations, contracts, IP',
    category: 'Stakeholder',
  },
  oracle: {
    displayName: 'Oracle',
    description: 'Meeting transcript analysis, stakeholder insights',
    category: 'Stakeholder',
  },
  sage: {
    displayName: 'Sage',
    description: 'Change management, adoption, human factors',
    category: 'Stakeholder',
  },
  // Consulting/Implementation Agents
  strategist: {
    displayName: 'Strategist',
    description: 'Executive engagement, organizational politics',
    category: 'Consulting',
  },
  architect: {
    displayName: 'Architect',
    description: 'Technical architecture, RAG, integration patterns',
    category: 'Consulting',
  },
  operator: {
    displayName: 'Operator',
    description: 'Process optimization, automation, metrics',
    category: 'Consulting',
  },
  pioneer: {
    displayName: 'Pioneer',
    description: 'Emerging tech, innovation, maturity assessment',
    category: 'Consulting',
  },
  // Internal Enablement Agents
  catalyst: {
    displayName: 'Catalyst',
    description: 'Internal communications, AI messaging',
    category: 'Enablement',
  },
  scholar: {
    displayName: 'Scholar',
    description: 'Training programs, champion enablement',
    category: 'Enablement',
  },
  echo: {
    displayName: 'Echo',
    description: 'Brand voice analysis, style profiling',
    category: 'Enablement',
  },
  // Systems Agent
  nexus: {
    displayName: 'Nexus',
    description: 'Systems thinking, feedback loops, interconnections',
    category: 'Systems',
  },
  // Coordinator
  coordinator: {
    displayName: 'Coordinator',
    description: 'Routes to the best agent for your question',
    category: 'System',
  },
}

const AGENT_ORDER = [
  'coordinator',
  'atlas',
  'fortuna',
  'guardian',
  'counselor',
  'oracle',
  'sage',
  'strategist',
  'architect',
  'operator',
  'pioneer',
  'catalyst',
  'scholar',
  'echo',
  'nexus',
]

export default function AgentSelector({
  selectedAgents,
  onAgentsChange,
  maxAgents = 3,
  className = '',
  disabled = false,
}: AgentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggleAgent = (agentName: string) => {
    if (selectedAgents.includes(agentName)) {
      // Remove agent
      onAgentsChange(selectedAgents.filter(a => a !== agentName))
    } else if (selectedAgents.length < maxAgents) {
      // Add agent
      onAgentsChange([...selectedAgents, agentName])
    }
  }

  const removeAgent = (agentName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onAgentsChange(selectedAgents.filter(a => a !== agentName))
  }

  const clearAllAgents = (e: React.MouseEvent) => {
    e.stopPropagation()
    onAgentsChange([])
  }

  // Get display text for the selector button
  const getButtonText = () => {
    if (selectedAgents.length === 0) {
      return 'Auto (Coordinator)'
    }
    if (selectedAgents.length === 1) {
      const info = AGENT_INFO[selectedAgents[0]]
      return info?.displayName || selectedAgents[0]
    }
    return `${selectedAgents.length} agents`
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Selected agents chips + dropdown trigger */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Selected agent chips */}
        {selectedAgents.map(agent => {
          const info = AGENT_INFO[agent]
          return (
            <div
              key={agent}
              className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium border ${getAgentColor(agent)}`}
            >
              <AgentIcon name={agent} size="sm" />
              <span>{info?.displayName || agent}</span>
              {!disabled && (
                <button
                  onClick={(e) => removeAgent(agent, e)}
                  className="ml-0.5 hover:opacity-70 transition-opacity"
                  aria-label={`Remove ${info?.displayName || agent}`}
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          )
        })}

        {/* Add agent button / dropdown trigger */}
        <button
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className={`
            inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
            border border-neutral-700 bg-neutral-800 text-neutral-300
            hover:bg-neutral-700 hover:border-neutral-600 transition-colors
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {selectedAgents.length === 0 ? (
            <>
              <AgentIcon name="coordinator" size="sm" />
              <span>Auto</span>
            </>
          ) : selectedAgents.length < maxAgents ? (
            <>
              <Plus className="w-3 h-3" />
              <span>Add</span>
            </>
          ) : null}
          <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? '' : 'rotate-180'}`} />
        </button>

        {/* Clear all button */}
        {selectedAgents.length > 0 && !disabled && (
          <button
            onClick={clearAllAgents}
            className="text-xs text-neutral-500 hover:text-neutral-300 transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Dropdown menu - opens upward */}
      {isOpen && (
        <div className="absolute z-50 bottom-full mb-2 w-80 rounded-lg border border-neutral-700 bg-neutral-800 shadow-xl">
          <div className="p-1.5">
            <div className="text-xs font-medium text-neutral-500 px-2 py-0.5 mb-0.5">
              Select agents (max {maxAgents})
            </div>

            {/* Auto/Coordinator option */}
            <button
              onClick={() => {
                onAgentsChange([])
                setIsOpen(false)
              }}
              className={`
                w-full flex items-center gap-2 px-2 py-1 rounded-md text-left
                hover:bg-neutral-700 transition-colors
                ${selectedAgents.length === 0 ? 'bg-neutral-700/50' : ''}
              `}
            >
              <div className={`p-1 rounded-md ${getAgentColor('coordinator')}`}>
                <AgentIcon name="coordinator" size="sm" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-neutral-200 leading-tight">
                  Auto (Coordinator)
                </div>
                <div className="text-xs text-neutral-500 truncate leading-tight">
                  Automatically routes to the best agent
                </div>
              </div>
              {selectedAgents.length === 0 && (
                <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
              )}
            </button>

            <div className="border-t border-neutral-700 my-1" />

            {/* Agent list grouped by category */}
            {['Stakeholder', 'Consulting', 'Enablement', 'Systems'].map(category => {
              const categoryAgents = AGENT_ORDER.filter(
                agent => agent !== 'coordinator' && AGENT_INFO[agent]?.category === category
              )
              if (categoryAgents.length === 0) return null

              return (
                <div key={category} className="mb-1">
                  <div className="text-xs font-medium text-neutral-500 px-2 py-0.5">
                    {category}
                  </div>
                  {categoryAgents.map(agent => {
                    const info = AGENT_INFO[agent]
                    const isSelected = selectedAgents.includes(agent)
                    const isDisabled = !isSelected && selectedAgents.length >= maxAgents

                    return (
                      <button
                        key={agent}
                        onClick={() => !isDisabled && toggleAgent(agent)}
                        disabled={isDisabled}
                        className={`
                          w-full flex items-center gap-2 px-2 py-1 rounded-md text-left
                          transition-colors
                          ${isSelected ? 'bg-neutral-700/50' : 'hover:bg-neutral-700'}
                          ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
                        `}
                      >
                        <div className={`p-1 rounded-md ${getAgentColor(agent)}`}>
                          <AgentIcon name={agent} size="sm" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-neutral-200 leading-tight">
                            {info?.displayName || agent}
                          </div>
                          <div className="text-xs text-neutral-500 truncate leading-tight">
                            {info?.description || ''}
                          </div>
                        </div>
                        {isSelected && (
                          <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
                        )}
                      </button>
                    )
                  })}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// Export agent info for use elsewhere
export { AGENT_INFO, AGENT_ORDER }
