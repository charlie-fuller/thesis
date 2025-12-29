'use client'

import { AgentIcon, getAgentColor } from '@/components/AgentIcon'

interface Participant {
  id: string
  agent_id: string
  agent_name: string
  agent_display_name: string
  role_description: string | null
  priority: number
  turns_taken: number
  tokens_used: number
}

interface ParticipantBarProps {
  participants: Participant[]
  activeAgent: string | null
  isAutonomous?: boolean
  currentRound?: number
  totalRounds?: number
}

const AGENT_DESCRIPTIONS: Record<string, string> = {
  // Meta-Agents
  facilitator: 'Meeting Orchestration',
  reporter: 'Synthesis & Documentation',
  // Stakeholder Perspective Agents
  atlas: 'Research & Best Practices',
  fortuna: 'Financial Analysis & ROI',
  guardian: 'Security & Governance',
  counselor: 'Legal & Compliance',
  oracle: 'Stakeholder Intelligence',
  sage: 'People, Incentives & Human-Centered AI',
  // Consulting/Implementation Agents
  strategist: 'Executive Strategy',
  architect: 'Technical Architecture',
  operator: 'Business Operations',
  pioneer: 'Innovation & R&D',
  // Internal Enablement Agents
  catalyst: 'Internal Communications',
  scholar: 'Learning & Development',
  echo: 'Brand Voice & Style',
  // Systems Agent
  nexus: 'Systems Thinking'
}

export default function ParticipantBar({
  participants,
  activeAgent,
  isAutonomous = false,
  currentRound = 0,
  totalRounds = 0
}: ParticipantBarProps) {
  // Sort participants by priority for speaking order display
  const sortedParticipants = [...participants].sort((a, b) => a.priority - b.priority)

  return (
    <div className="w-64 border-l border-default bg-card flex-shrink-0 overflow-y-auto">
      <div className="px-3 py-2 border-b border-default">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-primary text-sm">Participants</h3>
          <span className="text-[10px] text-secondary">{participants.length} agents</span>
        </div>

        {/* Autonomous Discussion Progress */}
        {isAutonomous && currentRound > 0 && (
          <div className="mt-2 p-1.5 bg-primary/5 rounded border border-primary/20">
            <div className="flex items-center justify-between text-[10px]">
              <span className="text-primary font-medium">Round {currentRound}/{totalRounds}</span>
              <span className="text-secondary">
                {Math.round((currentRound / totalRounds) * 100)}%
              </span>
            </div>
            <div className="mt-1 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500"
                style={{ width: `${(currentRound / totalRounds) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Speaking Order (shown during autonomous mode) */}
      {isAutonomous && (
        <div className="px-3 py-2 border-b border-default">
          <h4 className="text-[10px] font-medium text-secondary mb-1.5 uppercase tracking-wide">
            Speaking Order
          </h4>
          <div className="flex flex-wrap gap-0.5">
            {sortedParticipants.map((participant, index) => {
              const isActive = activeAgent === participant.agent_display_name
              return (
                <div
                  key={participant.id}
                  className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] ${
                    isActive
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-secondary'
                  }`}
                >
                  <span className="font-medium">{index + 1}.</span>
                  <AgentIcon name={participant.agent_name} size="sm" className="w-3 h-3" />
                  <span className="truncate max-w-[50px]">
                    {participant.agent_display_name.split(' ')[0]}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div className="p-3 space-y-1.5">
        {(isAutonomous ? sortedParticipants : participants).map((participant, index) => {
          const isActive = activeAgent === participant.agent_display_name
          const color = getAgentColor(participant.agent_name)
          const description = AGENT_DESCRIPTIONS[participant.agent_name] || ''

          return (
            <div
              key={participant.id}
              className={`px-2 py-1.5 rounded-md transition-colors ${
                isActive ? 'bg-primary/10 border border-primary' : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <div className="relative flex-shrink-0">
                  <div
                    className={`w-7 h-7 rounded-lg ${color} flex items-center justify-center border`}
                  >
                    <AgentIcon name={participant.agent_name} size="sm" />
                  </div>
                  {isActive && (
                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border border-white dark:border-gray-900 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                    </div>
                  )}
                  {isAutonomous && !isActive && (
                    <div className="absolute -top-0.5 -left-0.5 w-4 h-4 bg-gray-600 rounded-full border border-white dark:border-gray-900 flex items-center justify-center text-[9px] text-white font-medium">
                      {index + 1}
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="font-medium text-primary text-xs truncate leading-tight">
                    {participant.agent_display_name}
                  </div>
                  <div className="text-[10px] text-secondary truncate leading-tight">
                    {participant.role_description || description}
                  </div>
                </div>

                {isActive && (
                  <span className="inline-block w-2 h-2 bg-primary rounded-full animate-pulse flex-shrink-0" />
                )}

                {participant.turns_taken > 0 && !isActive && (
                  <span className="text-[10px] text-tertiary flex-shrink-0">
                    {participant.turns_taken}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="px-3 py-2 border-t border-default">
        <div className="flex items-center gap-4 text-[10px] text-secondary">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-green-500 rounded-full" />
            <span>Responding</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-gray-300 dark:bg-gray-600 rounded-full" />
            <span>Idle</span>
          </div>
        </div>
      </div>
    </div>
  )
}
