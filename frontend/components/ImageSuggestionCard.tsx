'use client'

import React, { useState, memo } from 'react'
import { Lightbulb, X, Workflow, Network, BarChart3, Calendar, GitCompare, Brain } from 'lucide-react'
import AspectRatioSelector from './AspectRatioSelector'

// L&D-specific image types
export type LDImageType =
  | 'flowchart'
  | 'diagram'
  | 'infographic'
  | 'timeline'
  | 'comparison'
  | 'mindmap'

interface ImageTypeOption {
  type: LDImageType
  icon: React.ElementType
  label: string
  description: string
  promptTemplate: string
}

const IMAGE_TYPE_OPTIONS: ImageTypeOption[] = [
  {
    type: 'flowchart',
    icon: Workflow,
    label: 'Process Flowchart',
    description: 'Step-by-step procedure visualization',
    promptTemplate: 'A detailed flowchart showing the process of {subject}, with clear steps, decision points, and flow arrows'
  },
  {
    type: 'diagram',
    icon: Network,
    label: 'Concept Diagram',
    description: 'Abstract ideas and relationships',
    promptTemplate: 'An educational diagram illustrating {subject}, showing key concepts and their relationships'
  },
  {
    type: 'infographic',
    icon: BarChart3,
    label: 'Infographic',
    description: 'Data and statistics visualization',
    promptTemplate: 'A clean, professional infographic about {subject}, displaying key statistics and data points visually'
  },
  {
    type: 'timeline',
    icon: Calendar,
    label: 'Timeline',
    description: 'Chronological events and milestones',
    promptTemplate: 'A timeline visualization showing {subject}, with clear chronological progression and key milestones'
  },
  {
    type: 'comparison',
    icon: GitCompare,
    label: 'Comparison Chart',
    description: 'Side-by-side comparison',
    promptTemplate: 'A comparison chart contrasting {subject}, highlighting key differences and similarities in a clear visual format'
  },
  {
    type: 'mindmap',
    icon: Brain,
    label: 'Mind Map',
    description: 'Brainstorming and ideation',
    promptTemplate: 'A mind map exploring {subject}, with central concept and branching related ideas and connections'
  }
]

interface ImageSuggestionCardProps {
  detectedSubject: string
  suggestedType?: LDImageType
  reason: string
  onGenerate: (prompt: string, aspectRatio: string, model: string) => void
  onDismiss: () => void
  isGenerating?: boolean
}

function ImageSuggestionCard({
  detectedSubject,
  suggestedType,
  reason,
  onGenerate,
  onDismiss,
  isGenerating = false
}: ImageSuggestionCardProps) {
  const [selectedType, setSelectedType] = useState<LDImageType | null>(suggestedType || null)
  const [customPrompt, setCustomPrompt] = useState('')
  const [showCustomPrompt, setShowCustomPrompt] = useState(false)
  const [showRatioSelector, setShowRatioSelector] = useState(false)

  const handleTypeSelect = (type: LDImageType) => {
    setSelectedType(type)
    const option = IMAGE_TYPE_OPTIONS.find(opt => opt.type === type)
    if (option) {
      const prompt = option.promptTemplate.replace('{subject}', detectedSubject)
      setCustomPrompt(prompt)
    }
  }

  const handleQuickGenerate = () => {
    if (!selectedType) return

    const option = IMAGE_TYPE_OPTIONS.find(opt => opt.type === selectedType)
    if (option) {
      const prompt = option.promptTemplate.replace('{subject}', detectedSubject)
      setCustomPrompt(prompt)
      setShowRatioSelector(true)
    }
  }

  const handleCustomize = () => {
    if (!selectedType) return

    const option = IMAGE_TYPE_OPTIONS.find(opt => opt.type === selectedType)
    if (option) {
      const prompt = option.promptTemplate.replace('{subject}', detectedSubject)
      setCustomPrompt(prompt)
    }
    setShowCustomPrompt(true)
    setShowRatioSelector(true)
  }

  const handleGenerate = (aspectRatio: string, model: string) => {
    onGenerate(customPrompt, aspectRatio, model)
  }

  const handleCancel = () => {
    setShowRatioSelector(false)
    setShowCustomPrompt(false)
  }

  if (isGenerating) {
    return (
      <div className="my-4 p-4 bg-teal-500/10 border border-teal-500/30 rounded-lg">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-teal-500"></div>
          <span className="text-primary text-sm">
            Generating your visual...
          </span>
        </div>
      </div>
    )
  }

  if (showRatioSelector) {
    return (
      <div className="my-4 space-y-4">
        {/* Custom Prompt Editor */}
        {showCustomPrompt && (
          <div className="bg-card border border-default rounded-lg p-4">
            <label className="block text-primary font-medium mb-2">
              Customize your prompt:
            </label>
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              className="w-full p-3 bg-page border border-default rounded-lg text-primary focus:border-teal-500 focus:outline-none resize-none"
              rows={3}
              placeholder="Describe the visual you want to generate..."
            />
          </div>
        )}

        {/* Aspect Ratio and Model Selector */}
        <AspectRatioSelector
          onSelect={handleGenerate}
          onCancel={handleCancel}
        />
      </div>
    )
  }

  return (
    <div className="my-4 p-4 bg-teal-500/5 border border-teal-500/20 rounded-lg">
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <Lightbulb className="w-5 h-5 text-teal-500" />
        </div>

        {/* Content */}
        <div className="flex-1 space-y-4">
          {/* Suggestion Text */}
          <div className="text-primary">
            <p className="font-medium mb-1">
              {reason}
            </p>
            <p className="text-sm text-secondary">
              I detected you&apos;re discussing{' '}
              <span className="font-medium text-primary">
                &quot;{detectedSubject}&quot;
              </span>
              . Select a visual type to help illustrate this concept:
            </p>
          </div>

          {/* Image Type Selection Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {IMAGE_TYPE_OPTIONS.map((option) => {
              const Icon = option.icon
              const isSelected = selectedType === option.type
              const isSuggested = suggestedType === option.type

              return (
                <button
                  key={option.type}
                  onClick={() => handleTypeSelect(option.type)}
                  className={`
                    relative p-3 rounded-lg text-left transition-all border-2
                    ${isSelected
                      ? 'bg-teal-500/20 border-teal-500 shadow-sm'
                      : 'bg-hover border-default hover:border-teal-500/50'
                    }
                  `}
                  title={option.description}
                >
                  {isSuggested && !isSelected && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-teal-500 rounded-full animate-pulse" />
                  )}
                  <div className="flex items-start gap-2">
                    <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isSelected ? 'text-teal-500' : 'text-secondary'}`} />
                    <div>
                      <div className={`text-sm font-medium ${isSelected ? 'text-teal-600 dark:text-teal-400' : 'text-primary'}`}>
                        {option.label}
                      </div>
                      <div className="text-xs text-muted mt-0.5">
                        {option.description}
                      </div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Action Buttons */}
          {selectedType && (
            <div className="flex flex-wrap gap-2 pt-2">
              <button
                onClick={handleQuickGenerate}
                className="px-4 py-2 bg-teal-500 hover:bg-teal-600 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Generate {IMAGE_TYPE_OPTIONS.find(opt => opt.type === selectedType)?.label}
              </button>

              <button
                onClick={handleCustomize}
                className="px-4 py-2 bg-hover hover:bg-default text-primary rounded-lg text-sm font-medium transition-colors border border-default"
              >
                Customize prompt
              </button>

              <button
                onClick={onDismiss}
                className="px-4 py-2 bg-transparent hover:bg-hover text-secondary rounded-lg text-sm transition-colors"
              >
                Not now
              </button>
            </div>
          )}
        </div>

        {/* Close Button */}
        <button
          onClick={onDismiss}
          className="flex-shrink-0 p-1 hover:bg-hover rounded transition-colors"
          title="Dismiss suggestion"
        >
          <X className="w-4 h-4 text-muted" />
        </button>
      </div>
    </div>
  )
}

export default memo(ImageSuggestionCard);
