'use client'

import React, { useState } from 'react'
import { Lightbulb, X, Edit3 } from 'lucide-react'
import AspectRatioSelector from './AspectRatioSelector'

interface ImageSuggestion {
  suggested_prompt: string
  reason: string
}

interface ImageSuggestionPromptProps {
  suggestion: ImageSuggestion
  onAccept: (prompt: string, aspectRatio: string, model: string) => void
  onDecline: () => void
  isGenerating?: boolean
}

export default function ImageSuggestionPrompt({
  suggestion,
  onAccept,
  onDecline,
  isGenerating = false
}: ImageSuggestionPromptProps) {
  const [showRatioSelector, setShowRatioSelector] = useState(false)
  const [showCustomPrompt, setShowCustomPrompt] = useState(false)
  const [customPrompt, setCustomPrompt] = useState(suggestion.suggested_prompt)

  const handleYes = () => {
    setShowRatioSelector(true)
  }

  const handleCustomize = () => {
    setShowCustomPrompt(true)
    setShowRatioSelector(true)
  }

  const handleGenerate = (aspectRatio: string, model: string) => {
    const finalPrompt = showCustomPrompt ? customPrompt : suggestion.suggested_prompt
    onAccept(finalPrompt, aspectRatio, model)
  }

  const handleCancel = () => {
    setShowRatioSelector(false)
    setShowCustomPrompt(false)
    setCustomPrompt(suggestion.suggested_prompt)
  }

  if (isGenerating) {
    return (
      <div className="my-4 p-4 bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 rounded-lg">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[var(--color-primary)]"></div>
          <span className="text-[var(--color-text-primary)] text-sm">
            Generating image...
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
          <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg p-4">
            <label className="block text-[var(--color-text-primary)] font-medium mb-2">
              Customize your prompt:
            </label>
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              className="w-full p-3 bg-[var(--color-bg-page)] border border-[var(--color-border)] rounded-lg text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none resize-none"
              rows={3}
              placeholder="Describe the image you want to generate..."
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
    <div className="my-4 p-4 bg-[var(--color-primary)]/5 border border-[var(--color-primary)]/20 rounded-lg">
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <Lightbulb className="w-5 h-5 text-[var(--color-primary)]" />
        </div>

        {/* Content */}
        <div className="flex-1 space-y-3">
          {/* Suggestion Text */}
          <div className="text-[var(--color-text-primary)]">
            <p className="font-medium mb-1">
              {suggestion.reason}
            </p>
            <p className="text-sm text-[var(--color-text-secondary)]">
              Would you like me to generate an image showing{' '}
              <span className="font-medium text-[var(--color-text-primary)]">
                {suggestion.suggested_prompt}
              </span>
              ?
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleYes}
              className="px-4 py-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white rounded-lg text-sm font-medium transition-colors"
            >
              Yes, generate it
            </button>

            <button
              onClick={handleCustomize}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--color-bg-hover)] hover:bg-[var(--color-border)] text-[var(--color-text-primary)] rounded-lg text-sm font-medium transition-colors border border-[var(--color-border)]"
            >
              <Edit3 className="w-3.5 h-3.5" />
              Customize prompt
            </button>

            <button
              onClick={onDecline}
              className="px-4 py-2 bg-transparent hover:bg-[var(--color-bg-hover)] text-[var(--color-text-secondary)] rounded-lg text-sm transition-colors"
            >
              No, thanks
            </button>
          </div>
        </div>

        {/* Close Button */}
        <button
          onClick={onDecline}
          className="flex-shrink-0 p-1 hover:bg-[var(--color-bg-hover)] rounded transition-colors"
          title="Dismiss suggestion"
        >
          <X className="w-4 h-4 text-[var(--color-text-muted)]" />
        </button>
      </div>
    </div>
  )
}
