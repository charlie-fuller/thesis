'use client'

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

const AGENT_COLORS: Record<string, string> = {
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
  scholar: 'bg-teal-500'
}

const AGENT_DESCRIPTIONS: Record<string, string> = {
  atlas: 'Research & Best Practices',
  fortuna: 'Financial Analysis & ROI',
  guardian: 'Security & Governance',
  counselor: 'Legal & Compliance',
  oracle: 'Stakeholder Intelligence',
  sage: 'People & Change Management',
  strategist: 'Executive Strategy',
  architect: 'Technical Architecture',
  operator: 'Business Operations',
  pioneer: 'Innovation & R&D',
  catalyst: 'Internal Communications',
  scholar: 'Learning & Development'
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
    <div className="w-64 border-l border-default bg-panel flex-shrink-0 overflow-y-auto">
      <div className="p-4 border-b border-default">
        <h3 className="font-medium text-primary">Participants</h3>
        <p className="text-xs text-secondary mt-1">
          {participants.length} agents in this meeting
        </p>

        {/* Autonomous Discussion Progress */}
        {isAutonomous && currentRound > 0 && (
          <div className="mt-3 p-2 bg-primary/5 rounded-lg border border-primary/20">
            <div className="flex items-center justify-between text-xs">
              <span className="text-primary font-medium">Round {currentRound} of {totalRounds}</span>
              <span className="text-secondary">
                {Math.round((currentRound / totalRounds) * 100)}%
              </span>
            </div>
            <div className="mt-1.5 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
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
        <div className="p-4 border-b border-default">
          <h4 className="text-xs font-medium text-secondary mb-2 uppercase tracking-wide">
            Speaking Order
          </h4>
          <div className="flex flex-wrap gap-1">
            {sortedParticipants.map((participant, index) => {
              const isActive = activeAgent === participant.agent_display_name
              const color = AGENT_COLORS[participant.agent_name] || 'bg-gray-500'
              return (
                <div
                  key={participant.id}
                  className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
                    isActive
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-secondary'
                  }`}
                >
                  <span className="font-medium">{index + 1}.</span>
                  <div className={`w-2 h-2 rounded-full ${color}`} />
                  <span className="truncate max-w-[60px]">
                    {participant.agent_display_name.split(' ')[0]}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div className="p-4 space-y-3">
        {(isAutonomous ? sortedParticipants : participants).map((participant, index) => {
          const isActive = activeAgent === participant.agent_display_name
          const color = AGENT_COLORS[participant.agent_name] || 'bg-gray-500'
          const description = AGENT_DESCRIPTIONS[participant.agent_name] || ''

          return (
            <div
              key={participant.id}
              className={`p-3 rounded-lg transition-colors ${
                isActive ? 'bg-primary/10 border border-primary' : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div
                    className={`w-10 h-10 rounded-full ${color} flex items-center justify-center text-white font-semibold`}
                  >
                    {participant.agent_display_name.charAt(0)}
                  </div>
                  {isActive && (
                    <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white dark:border-gray-900 flex items-center justify-center">
                      <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                    </div>
                  )}
                  {isAutonomous && !isActive && (
                    <div className="absolute -top-1 -left-1 w-5 h-5 bg-gray-600 rounded-full border-2 border-white dark:border-gray-900 flex items-center justify-center text-[10px] text-white font-medium">
                      {index + 1}
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="font-medium text-primary text-sm truncate">
                    {participant.agent_display_name}
                  </div>
                  <div className="text-xs text-secondary truncate">
                    {participant.role_description || description}
                  </div>
                </div>
              </div>

              {isActive && (
                <div className="mt-2 text-xs text-primary flex items-center gap-1">
                  <span className="inline-block w-2 h-2 bg-primary rounded-full animate-pulse" />
                  Responding...
                </div>
              )}

              {participant.turns_taken > 0 && !isActive && (
                <div className="mt-2 text-xs text-tertiary">
                  {participant.turns_taken} turn{participant.turns_taken !== 1 ? 's' : ''}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-default">
        <h4 className="text-xs font-medium text-secondary mb-2 uppercase tracking-wide">
          Status
        </h4>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full" />
            <span className="text-secondary">Currently responding</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gray-300 dark:bg-gray-600 rounded-full" />
            <span className="text-secondary">Idle</span>
          </div>
        </div>
      </div>
    </div>
  )
}
