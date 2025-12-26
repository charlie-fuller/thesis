'use client'

import React from 'react'
import { Workflow, Network, BarChart3, Calendar, GitCompare, Brain, Sparkles } from 'lucide-react'

interface VisualQuickAction {
  type: string
  icon: React.ElementType
  label: string
  description: string
  chatPrompt: string  // The message to insert into chat
}

const VISUAL_ACTIONS: VisualQuickAction[] = [
  {
    type: 'flowchart',
    icon: Workflow,
    label: 'Flowchart',
    description: 'Process or workflow',
    chatPrompt: 'Create a flowchart based on what we have discussed.'
  },
  {
    type: 'diagram',
    icon: Network,
    label: 'Diagram',
    description: 'Concepts & relationships',
    chatPrompt: 'Create a diagram showing the concepts and relationships we have discussed.'
  },
  {
    type: 'infographic',
    icon: BarChart3,
    label: 'Infographic',
    description: 'Data visualization',
    chatPrompt: 'Create an infographic visualizing the key points from our conversation.'
  },
  {
    type: 'timeline',
    icon: Calendar,
    label: 'Timeline',
    description: 'Chronological events',
    chatPrompt: 'Create a timeline based on what we have discussed.'
  },
  {
    type: 'comparison',
    icon: GitCompare,
    label: 'Comparison',
    description: 'Side-by-side analysis',
    chatPrompt: 'Create a comparison chart based on what we have discussed.'
  },
  {
    type: 'mindmap',
    icon: Brain,
    label: 'Mind Map',
    description: 'Brainstorming ideas',
    chatPrompt: 'Create a mind map exploring the ideas we have discussed.'
  }
]

interface VisualQuickActionsProps {
  onActionSelect: (prompt: string) => void
}

export default function VisualQuickActions({ onActionSelect }: VisualQuickActionsProps) {
  const handleActionClick = (action: VisualQuickAction) => {
    // Simply pass the chat prompt to be inserted into the chat input
    onActionSelect(action.chatPrompt)
  }

  return (
    <div className="bg-card border border-default rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-5 h-5 text-teal-500" />
        <h3 className="text-sm font-semibold text-primary">Generate Visual</h3>
      </div>

      {/* Action Grid */}
      <div className="grid grid-cols-3 gap-2">
        {VISUAL_ACTIONS.map((action) => {
          const Icon = action.icon

          return (
            <button
              key={action.type}
              onClick={() => handleActionClick(action)}
              className="p-2 bg-hover hover:bg-default border border-default hover:border-teal-500/50 rounded-lg text-left transition-all group"
              title={action.description}
            >
              <div className="flex flex-col items-center gap-1 text-center">
                <Icon className="w-4 h-4 text-secondary group-hover:text-teal-500 transition-colors flex-shrink-0" />
                <div className="text-xs font-medium text-primary group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors truncate w-full">
                  {action.label}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      <p className="text-xs text-muted mt-3">
        Click to start creating a visual in the chat
      </p>
    </div>
  )
}
